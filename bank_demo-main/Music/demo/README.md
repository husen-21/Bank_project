# NexaBank — Python Banking Web Demo

A responsive Flask frontend for a beginner-friendly banking management project.

## Requirements
- Python 3.10+
- pip

## Run in VS Code (Windows)
Open this folder in VS Code, then in its terminal run:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open the local address shown in the terminal, usually http://127.0.0.1:5000.

## Features
- Demo account creation
- Dashboard with balance and quick actions
- Deposit and withdrawal with PIN check
- Recent transaction history
- Loan application form and estimated EMI
- Change account PIN
- Separate locker PIN setup and unlock
- Responsive desktop/mobile styling

## Important limitations
This is an educational demo only. Account records are held in Python memory and disappear when the server restarts. PINs are stored as plain text, there is no persistent database, no real authentication/session hardening, and no real banking integration. Do not use real credentials or real money. Before any real deployment, add a database, password hashing, CSRF protection, rate limits, secure cookie settings, validation, audit logging and proper authentication.
