from datetime import datetime
import hashlib
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

# Fictional local demo values only. Never use or display a real secret this way.
EXPECTED_GATEWAY_KEY = "fake-bank-gateway-key-v1"
ACTIVE_GATEWAY_KEY = EXPECTED_GATEWAY_KEY
NEXT_PAYMENT_ID = 7001
PAYMENTS = []
EVENTS = []

BENEFICIARIES = [
    "Campus Bookstore Demo",
    "Electricity Board Demo",
    "Riya Demo Account",
]

def fingerprint(secret):
    """A short identifier for the demo UI; never return the secret itself."""
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()[:8].upper()

def mock_gateway(payment):
    """Local stand-in for a payment gateway; this makes no network calls."""
    if ACTIVE_GATEWAY_KEY != EXPECTED_GATEWAY_KEY:
        return 401, {"error": "Unauthorized: gateway credential rejected"}
    return 202, {"accepted": True, "gateway_reference": "GW-" + payment["reference"]}

def check_gateway(payment):
    status, response = mock_gateway(payment)
    mismatch = ACTIVE_GATEWAY_KEY != EXPECTED_GATEWAY_KEY
    detected = mismatch or status in (401, 403)
    event = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "payment_id": payment["id"],
        "http_status": status,
        "detected": detected,
        "expected_fingerprint": fingerprint(EXPECTED_GATEWAY_KEY),
        "active_fingerprint": fingerprint(ACTIVE_GATEWAY_KEY),
        "message": (
            "Credential mismatch detected. Gateway rejected the payment request."
            if detected else "Credential accepted. Gateway acknowledged the payment request."
        ),
    }
    EVENTS.insert(0, event)
    payment["gateway_status"] = "Rejected — needs review" if detected else "Accepted by mock gateway"
    payment["http_status"] = status
    return event, response

@app.get("/")
def home():
    return render_template_string(PAGE, beneficiaries=BENEFICIARIES)

@app.get("/api/status")
def status():
    return jsonify({
        "credential_status": "mismatch" if ACTIVE_GATEWAY_KEY != EXPECTED_GATEWAY_KEY else "ready",
        "expected_fingerprint": fingerprint(EXPECTED_GATEWAY_KEY),
        "active_fingerprint": fingerprint(ACTIVE_GATEWAY_KEY),
        "latest_event": EVENTS[0] if EVENTS else None,
        "events": EVENTS[:8],
        "payments": PAYMENTS[:8],
    })

@app.post("/api/payments")
def create_payment():
    global NEXT_PAYMENT_ID, ACTIVE_GATEWAY_KEY
    data = request.get_json(silent=True) or {}
    beneficiary = data.get("beneficiary", "")
    try:
        amount = int(data.get("amount", 0))
    except (TypeError, ValueError):
        amount = 0
    if beneficiary not in BENEFICIARIES:
        return jsonify({"error": "Choose a listed demo beneficiary."}), 400
    if amount < 1 or amount > 100000:
        return jsonify({"error": "Enter a demo amount between ₹1 and ₹100,000."}), 400

    payment = {
        "id": NEXT_PAYMENT_ID,
        "reference": "BK-" + str(NEXT_PAYMENT_ID),
        "beneficiary": beneficiary,
        "amount": amount,
        "created": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "status": "Recorded in demo ledger — no funds moved",
    }
    NEXT_PAYMENT_ID += 1
    PAYMENTS.insert(0, payment)

    # Fault injection emulates an unexpected backend credential change.
    # The bank records a pending demo request, then its mock gateway rejects it.
    if bool(data.get("simulate_key_change", False)):
        ACTIVE_GATEWAY_KEY = "fake-bank-gateway-key-changed"

    event, gateway_response = check_gateway(payment)
    return jsonify({
        "payment": payment,
        "event": event,
        "gateway_response": gateway_response,
        "message": "Simulation only: no real money was transferred.",
    })

@app.post("/api/repair")
def repair_and_retry():
    global ACTIVE_GATEWAY_KEY
    ACTIVE_GATEWAY_KEY = EXPECTED_GATEWAY_KEY
    pending = next((payment for payment in PAYMENTS if payment.get("http_status") in (401, 403)), None)
    event = None
    if pending:
        event, _ = check_gateway(pending)
    return jsonify({
        "status": "ready",
        "event": event,
        "message": "Fake demo credential restored. The latest rejected request was retried.",
    })

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BankKeyWatch | Credential Monitor Demo</title>
<style>
:root{--navy:#10283d;--ink:#1d3041;--muted:#6d7b88;--line:#e1e8ed;--bg:#f3f6f8;--blue:#2372a2;--red:#b63843;--green:#177650;--gold:#f5c85f}*{box-sizing:border-box}body{margin:0;background:var(--bg);font:14px/1.5 Inter,system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--ink)}button,input,select{font:inherit}.top{background:var(--navy);color:white;padding:14px max(22px,calc((100% - 1080px)/2));display:flex;justify-content:space-between;align-items:center;gap:12px}.brand{font-size:20px;font-weight:850;letter-spacing:-.4px}.brand em{font-style:normal;color:#66d4bd}.local{font-size:10px;letter-spacing:.08em;color:#d6e4eb;border:1px solid #577083;padding:5px 8px;border-radius:99px}.wrap{max-width:1080px;margin:24px auto;padding:0 22px}.hero{background:linear-gradient(110deg,#e2f2f2,#f8fbfc 65%,#e6effa);border:1px solid #dce8eb;border-radius:14px;padding:23px 25px;display:flex;justify-content:space-between;align-items:center;gap:14px}.eyebrow{font-size:10px;font-weight:850;letter-spacing:.13em;color:var(--blue);text-transform:uppercase}.hero h1{font-size:26px;letter-spacing:-.6px;margin:5px 0}.hero p{color:var(--muted);margin:0}.icon{font-size:38px}.status{margin-top:15px;background:white;border:1px solid var(--line);border-radius:11px;padding:12px 15px;display:flex;justify-content:space-between;align-items:center;gap:12px}.statusleft{display:flex;align-items:center;gap:10px}.dot{height:11px;width:11px;border-radius:50%;background:var(--green)}.status.bad .dot{background:var(--red)}.status strong{display:block}.status small{color:var(--muted)}.badge{font-size:10px;font-weight:850;padding:5px 9px;border-radius:99px;background:#e6f5ed;color:var(--green)}.status.bad .badge{background:#fff0ef;color:var(--red)}.grid{display:grid;grid-template-columns:1fr 1fr;gap:15px;margin-top:15px}.panel{background:white;border:1px solid var(--line);border-radius:11px;padding:17px}.panel h2{font-size:16px;margin:0 0 10px}.balance{font-size:25px;font-weight:850;letter-spacing:-.4px}.caption{font-size:11px;color:var(--muted)}.field{display:block;font-weight:750;font-size:12px;margin:12px 0 5px}.input{width:100%;padding:9px 10px;border:1px solid #d4dee5;border-radius:7px;background:white}.submit{margin-top:14px;width:100%;border:0;border-radius:7px;background:var(--gold);padding:10px;font-weight:850}.submit:disabled{opacity:.6}.inject{display:flex;gap:8px;align-items:flex-start;font-size:11px;color:#5d6d7b;margin-top:12px}.inject input{margin-top:3px}.transaction{border-top:1px solid var(--line);padding:10px 0;display:flex;justify-content:space-between;gap:10px}.transaction b{display:block}.transaction small{display:block;color:var(--muted);font-size:11px}.amount{font-weight:850;white-space:nowrap}.section{margin-top:15px;background:white;border:1px solid var(--line);border-radius:11px;padding:17px}.sectionhead{display:flex;justify-content:space-between;align-items:start;gap:10px}.section h2{font-size:16px;margin:0}.section p{font-size:11px;color:var(--muted);margin:3px 0 12px}.repair{border:0;background:var(--blue);color:white;border-radius:7px;padding:9px 11px;font-weight:750;white-space:nowrap}.repair:disabled{opacity:.6}.notice{margin-top:10px;padding:12px;border-radius:8px;font-size:12px}.notice.bad{background:#fff0ef;color:#96313a;border:1px solid #f1cfcc}.notice.good{background:#eaf7f1;color:#176947;border:1px solid #cde6d9}.notice.neutral{background:#f3f6f8;color:#526374;border:1px solid var(--line)}.details{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:10px}.detail{padding:9px;background:#f6f8fa;border:1px solid var(--line);border-radius:7px}.detail small{display:block;color:var(--muted);font-size:9px;text-transform:uppercase;letter-spacing:.06em}.detail b{display:block;font-size:12px;margin-top:3px}.log{border-top:1px solid var(--line);padding:9px 0;font-size:11px;display:flex;justify-content:space-between;gap:10px}.log small{color:var(--muted)}.foot{text-align:center;font-size:10px;color:var(--muted);margin:18px 0 26px}.toast{position:fixed;bottom:18px;left:50%;transform:translateX(-50%);background:var(--navy);color:white;border-radius:8px;padding:10px 14px;display:none;box-shadow:0 4px 18px #0003}@media(max-width:740px){.grid{grid-template-columns:1fr}.top{align-items:flex-start;flex-direction:column}.hero h1{font-size:22px}.details{grid-template-columns:1fr}.sectionhead{flex-direction:column}}
</style></head><body>
<header class="top"><div class="brand">Bank<em>Key</em>Watch</div><span class="local">FICTIONAL BANK · LOCAL DEMO ONLY</span></header>
<main class="wrap"><section class="hero"><div><div class="eyebrow">Backend integration credential monitor</div><h1>Watch the bank-to-gateway connection</h1><p>Simulate a payment request, trigger a fake credential fault, and see the monitor detect it.</p></div><div class="icon">🔐</div></section>
<section id="status" class="status"><div class="statusleft"><span class="dot"></span><div><strong>Mock gateway credential</strong><small id="statusline">No credential issue detected yet.</small></div></div><span id="badge" class="badge">READY</span></section>
<div class="grid"><section class="panel"><h2>Demo transfer</h2><div class="balance">₹25,000</div><div class="caption">Fictional available balance · does not change</div><label class="field" for="beneficiary">Send to</label><select id="beneficiary" class="input">{% for b in beneficiaries %}<option>{{ b }}</option>{% endfor %}</select><label class="field" for="amount">Amount</label><input id="amount" class="input" type="number" min="1" max="100000" value="650" placeholder="Enter amount"><label class="inject"><input type="checkbox" id="inject"> Simulate a backend credential change for this request</label><button id="send" class="submit" onclick="sendPayment()">Send simulated payment</button><div class="caption" style="margin-top:9px">No money moves. The app creates a fictional payment record and calls its local mock gateway.</div></section>
<section class="panel"><h2>Recent demo requests</h2><div id="payments"><div class="caption">No demo payments yet.</div></div></section></div>
<section class="section"><div class="sectionhead"><div><h2>Credential incident monitor</h2><p>The secret stays on the server. The page displays only a short fingerprint and the mock gateway response.</p></div><button id="repair" class="repair" onclick="repair()" hidden>Restore credential & retry</button></div><div id="latest" class="notice neutral">Send a simulated payment to check the gateway connection.</div><div class="details"><div class="detail"><small>Expected fingerprint</small><b id="expected">—</b></div><div class="detail"><small>Active fingerprint</small><b id="active">—</b></div><div class="detail"><small>Latest gateway response</small><b id="http">—</b></div></div><h2 style="margin-top:17px">Incident history</h2><div id="events"><div class="caption">No events yet.</div></div></section>
<div class="foot">BankKeyWatch · Student prototype · Fake accounts and credentials · No real payment, bank, or external API connection.</div></main><div class="toast" id="toast"></div>
<script>
function money(n){return '₹'+Number(n).toLocaleString('en-IN')}
function toast(s){let t=document.getElementById('toast');t.textContent=s;t.style.display='block';setTimeout(()=>t.style.display='none',2600)}
function renderEvent(e){let bad=e.detected,bar=document.getElementById('status');bar.classList.toggle('bad',bad);document.getElementById('badge').textContent=bad?'ISSUE DETECTED':'CONNECTED';document.getElementById('statusline').textContent=bad?'Mock gateway rejected the request with HTTP '+e.http_status+'.':'Mock gateway accepted the request with HTTP '+e.http_status+'.';document.getElementById('latest').className='notice '+(bad?'bad':'good');document.getElementById('latest').innerHTML='<b>'+(bad?'Credential mismatch detected':'Gateway request succeeded')+'</b><br>Demo payment #'+e.payment_id+' · '+e.message;document.getElementById('expected').textContent=e.expected_fingerprint;document.getElementById('active').textContent=e.active_fingerprint;document.getElementById('http').textContent='HTTP '+e.http_status;document.getElementById('repair').hidden=!bad}
async function sendPayment(){let amount=Number(document.getElementById('amount').value);if(!Number.isInteger(amount)||amount<1||amount>100000){toast('Enter a demo amount from ₹1 to ₹100,000.');return}let b=document.getElementById('send');b.disabled=true;b.textContent='Sending demo request…';try{let r=await fetch('/api/payments',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({beneficiary:document.getElementById('beneficiary').value,amount:amount,simulate_key_change:document.getElementById('inject').checked})});let d=await r.json();if(!r.ok)throw new Error(d.error||'Request failed');renderEvent(d.event);loadStatus();toast('Demo request recorded. No money moved.')}catch(e){toast(e.message)}finally{b.disabled=false;b.textContent='Send simulated payment'}}
async function repair(){let b=document.getElementById('repair');b.disabled=true;b.textContent='Restoring & retrying…';try{let r=await fetch('/api/repair',{method:'POST'}),d=await r.json();if(d.event)renderEvent(d.event);loadStatus();toast(d.message)}finally{b.disabled=false;b.textContent='Restore credential & retry'}}
async function loadStatus(){let r=await fetch('/api/status'),d=await r.json();let list=document.getElementById('payments');list.innerHTML=d.payments.length?d.payments.map(p=>'<div class="transaction"><div><b>Payment #'+p.id+' · '+p.beneficiary+'</b><small>'+p.reference+' · '+p.created+' · '+p.status+'</small></div><span class="amount">'+money(p.amount)+'</span></div>').join(''):'<div class="caption">No demo payments yet.</div>';let events=document.getElementById('events');events.innerHTML=d.events.length?d.events.map(e=>'<div class="log"><span>'+e.time+' · Request #'+e.payment_id+'</span><span>HTTP '+e.http_status+' · '+(e.detected?'Credential issue':'Accepted')+'</span></div>').join(''):'<div class="caption">No events yet.</div>';if(d.latest_event)renderEvent(d.latest_event);else{document.getElementById('expected').textContent=d.expected_fingerprint;document.getElementById('active').textContent=d.active_fingerprint}}
loadStatus();
</script></body></html>"""

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002, debug=False)
