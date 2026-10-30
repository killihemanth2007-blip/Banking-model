# BankKeyWatch prototype

BankKeyWatch is a local, fictional banking demo that monitors a bank-to-gateway API credential. A simulated transfer creates a demo payment record, then the backend calls a mock gateway. If the fault option is selected, the backend changes a fake credential before the call. The mock gateway returns HTTP 401, and the monitor displays the issue with safe fingerprints. Restoring the fake credential retries the rejected request.

## Run locally in VS Code on Windows

Requires Python 3.10 or newer.

1. Open the bankkeywatch folder in VS Code.
2. Choose Terminal → New Terminal.
3. Create a project environment:
   
       py -m venv .venv

4. Install Flask:
   
       .\.venv\Scripts\python.exe -m pip install -r requirements.txt

5. Run the site:
   
       .\.venv\Scripts\python.exe app.py

6. Open http://127.0.0.1:5002. Keep the terminal open. Stop with Ctrl+C.

## Expo demo

1. Leave “Simulate a backend credential change for this request” unchecked and send a demo payment. Show the mock gateway accepting the request.
2. Select the fault option and send another demo payment.
3. Show the HTTP 401 alert and the expected versus active fingerprints. The secret itself is never displayed.
4. Select “Restore credential & retry.” Show the retry succeed.
5. Explain that the app records only demo data and does not move money.

## Scope and safety

- This is a local simulation. It does not connect to a bank, real payment gateway, or external API.
- All beneficiary names, payment references, and credentials are fake. No money moves.
- The credential fault is deliberate fault injection for demonstration.
- The monitor detects a mismatch and an authentication failure in this mock integration. It does not detect every cyberattack or protect bank accounts.
- The checks are deterministic rules, not machine learning. Never place real credentials in frontend code or logs.
- Payments and event history are held in memory and reset when the server stops.
