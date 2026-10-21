from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import os
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))

# Demo-only in-memory data. Data resets when the server restarts.
accounts = {}
next_account_number = 12345
loan_rates = {
    "Personal Loan": 12.0,
    "Car Loan": 9.0,
    "Home Loan": 8.5,
    "Agricultural Loan": 7.0,
}


def current_account():
    account_no = session.get("account_number")
    return accounts.get(account_no) if account_no else None


def record(account, kind, amount=0, note=""):
    account["transactions"].insert(0, {
        "date": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "type": kind,
        "amount": float(amount),
        "balance": account["balance"],
        "note": note,
    })
    del account["transactions"][20:]


def login_required():
    account = current_account()
    if not account:
        flash("Please create an account or sign in first.", "warning")
        return None
    return account


def emi(principal, annual_rate, years):
    months = years * 12
    monthly_rate = annual_rate / 1200
    if monthly_rate == 0:
        return principal / months
    factor = (1 + monthly_rate) ** months
    return principal * monthly_rate * factor / (factor - 1)


@app.route("/")
def index():
    account = current_account()
    if account:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/create-account", methods=["GET", "POST"])
def create_account():
    global next_account_number
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        pin = request.form.get("pin", "").strip()
        if not name:
            flash("Please enter your full name.", "error")
        elif len(pin) != 4 or not pin.isdigit():
            flash("PIN must contain exactly 4 digits.", "error")
        else:
            account_no = str(next_account_number)
            next_account_number += 1
            accounts[account_no] = {
                "name": name,
                "pin": pin,
                "balance": 0.0,
                "locker_pin": None,
                "transactions": [],
                "loans": [],
            }
            record(accounts[account_no], "Account opened", 0)
            session["account_number"] = account_no
            flash("Your demo account has been created.", "success")
            return redirect(url_for("dashboard"))
    return render_template("create_account.html")


@app.route("/dashboard")
def dashboard():
    account = login_required()
    if not account:
        return redirect(url_for("index"))
    total_loans = sum(item["amount"] for item in account["loans"])
    return render_template("dashboard.html", account=account, total_loans=total_loans, now=datetime.now().strftime("%A, %d %B %Y"))


@app.route("/transaction/<action>", methods=["GET", "POST"])
def transaction(action):
    account = login_required()
    if not account:
        return redirect(url_for("index"))
    if action not in ("deposit", "withdraw"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        entered_pin = request.form.get("pin", "")
        try:
            amount = float(request.form.get("amount", "0"))
        except ValueError:
            amount = 0

        if entered_pin != account["pin"]:
            flash("Incorrect account PIN.", "error")
        elif amount <= 0:
            flash("Enter an amount greater than zero.", "error")
        elif action == "withdraw" and amount > account["balance"]:
            flash("Insufficient balance.", "error")
        else:
            if action == "deposit":
                account["balance"] += amount
                record(account, "Deposit", amount)
                flash(f"₹{amount:,.2f} deposited successfully.", "success")
            else:
                account["balance"] -= amount
                record(account, "Withdrawal", amount)
                flash(f"₹{amount:,.2f} withdrawn successfully.", "success")
            return redirect(url_for("dashboard"))

    return render_template("transaction.html", account=account, action=action)


@app.route("/transactions")
def transactions():
    account = login_required()
    if not account:
        return redirect(url_for("index"))
    return render_template("transactions.html", account=account)


@app.route("/loans", methods=["GET", "POST"])
def loans():
    account = login_required()
    if not account:
        return redirect(url_for("index"))
    if request.method == "POST":
        if request.form.get("pin", "") != account["pin"]:
            flash("Incorrect account PIN.", "error")
            return redirect(url_for("loans"))
        loan_type = request.form.get("loan_type", "")
        try:
            amount = float(request.form.get("amount", "0"))
            years = int(request.form.get("years", "0"))
        except ValueError:
            amount, years = 0, 0

        if loan_type not in loan_rates:
            flash("Please select a valid loan type.", "error")
        elif amount <= 0:
            flash("Loan amount must be greater than zero.", "error")
        elif not 1 <= years <= 30:
            flash("Choose a repayment period between 1 and 30 years.", "error")
        else:
            rate = loan_rates[loan_type]
            account["loans"].insert(0, {
                "type": loan_type,
                "amount": amount,
                "years": years,
                "rate": rate,
                "emi": emi(amount, rate, years),
                "status": "Pending review",
                "date": datetime.now().strftime("%d %b %Y"),
            })
            flash("Loan application submitted for demo review.", "success")
            return redirect(url_for("loans"))
    return render_template("loans.html", account=account, loan_rates=loan_rates)


@app.route("/security", methods=["GET", "POST"])
def security():
    account = login_required()
    if not account:
        return redirect(url_for("index"))
    if request.method == "POST":
        old_pin = request.form.get("old_pin", "")
        new_pin = request.form.get("new_pin", "")
        confirm_pin = request.form.get("confirm_pin", "")
        if old_pin != account["pin"]:
            flash("Current PIN is incorrect.", "error")
        elif len(new_pin) != 4 or not new_pin.isdigit():
            flash("New PIN must contain exactly 4 digits.", "error")
        elif new_pin != confirm_pin:
            flash("New PINs do not match.", "error")
        else:
            account["pin"] = new_pin
            flash("Account PIN updated.", "success")
            return redirect(url_for("security"))
    return render_template("security.html", account=account)


@app.route("/locker", methods=["GET", "POST"])
def locker():
    account = login_required()
    if not account:
        return redirect(url_for("index"))
    unlocked = session.get("locker_unlocked", False)
    if request.method == "POST":
        action = request.form.get("action")
        if action == "setup":
            if request.form.get("account_pin", "") != account["pin"]:
                flash("Incorrect account PIN.", "error")
            else:
                new_pin = request.form.get("locker_pin", "")
                confirm_pin = request.form.get("confirm_pin", "")
                if len(new_pin) != 4 or not new_pin.isdigit():
                    flash("Locker PIN must contain exactly 4 digits.", "error")
                elif new_pin != confirm_pin:
                    flash("Locker PINs do not match.", "error")
                else:
                    account["locker_pin"] = new_pin
                    flash("Locker PIN created.", "success")
        elif action == "unlock":
            if account["locker_pin"] and request.form.get("locker_pin", "") == account["locker_pin"]:
                session["locker_unlocked"] = True
                flash("Demo locker unlocked.", "success")
                return redirect(url_for("locker"))
            flash("Locker access denied.", "error")
        elif action == "lock":
            session.pop("locker_unlocked", None)
            flash("Locker locked.", "success")
            return redirect(url_for("locker"))
        return redirect(url_for("locker"))
    return render_template("locker.html", account=account, unlocked=unlocked)


@app.route("/logout")
def logout():
    session.clear()
    flash("You have signed out of this demo session.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
