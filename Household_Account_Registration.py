'''
Household Registration System (Flask)
- Data persistence using JSON file
- In-memory dictionary for fast lookup (O(1))
- Simple web interface
'''

from flask import Flask, request
import json
import os
from datetime import datetime
import re

app = Flask(__name__)

# ===== Config =====
DATA_FILE = "households.json"

# In-memory storage
households = {}   # household_id -> household object


# ===== Helper Functions =====

def validate_nric(nric):
    """NRIC format: S/T/F/G + 7 digits + 1 letter"""
    return bool(re.match(r'^[STFG]\d{7}[A-Z]$', nric.upper()))

def validate_postal(postal):
    """Postal code: 6 digits"""
    return bool(re.match(r'^\d{6}$', postal))

def generate_household_id(postal, nric):
    digits = ''.join(filter(str.isdigit, nric))
    return f"H{postal}{digits}"

def save_to_file():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(households, f, indent=2)

def load_from_file():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            households.update(json.load(f))


# ===== Routes =====

@app.route("/")
def index():
    return """
    <html>
    <head>
        <meta http-equiv="refresh" content="0; url=/household">
    </head>
    </html>
    """


@app.route("/household")
def main_page():
    return f"""
<!DOCTYPE html>
<html>
<head>
<title>Household Registration</title>
<style>
body {{ font-family: Arial; max-width: 700px; margin: 40px auto; }}
input {{ width: 100%; padding: 8px; margin: 6px 0; }}
button {{ padding: 10px 25px; background: #3498db; color: white; border: none; }}
</style>
</head>
<body>

<h2>🏠 Household Registration System</h2>
<p>Total households: <b>{len(households)}</b></p>

<h3>Register Household</h3>
<form action="/register" method="post">
Family Members (comma separated NRICs)<br>
<input name="members" required>

Postal Code<br>
<input name="postal" required>

Address<br>
<input name="address" required>

<button type="submit">Register</button>
</form>

<hr>

<h3>Search Household</h3>
<form action="/search" method="get">
Household ID<br>
<input name="hid">

OR NRIC<br>
<input name="nric">

<button type="submit">Search</button>
</form>

<hr>

<form action="/list">
<button>View All Households</button>
</form>

</body>
</html>
"""


@app.route("/register", methods=["POST"])
def register():
    members_raw = request.form.get("members")
    postal = request.form.get("postal")
    address = request.form.get("address")

    members = [m.strip().upper() for m in members_raw.split(",")]

    # Validation
    for m in members:
        if not validate_nric(m):
            return f"Invalid NRIC: {m} <br><a href='/household'>Back</a>"

    if not validate_postal(postal):
        return "Invalid postal code <br><a href='/household'>Back</a>"

    hid = generate_household_id(postal, members[0])

    if hid in households:
        return f"Household already exists: {hid} <br><a href='/household'>Back</a>"

    household = {
        "household_id": hid,
        "members": members,
        "postal_code": postal,
        "address": address,
        "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    households[hid] = household
    save_to_file()

    return f"""
    <h2>Registration Successful</h2>
    Household ID: <b>{hid}</b><br>
    Members: {", ".join(members)}<br>
    Postal: {postal}<br>
    Address: {address}<br><br>
    <a href="/household">Back</a>
    """


@app.route("/search")
def search():
    hid = request.args.get("hid", "")
    nric = request.args.get("nric", "").upper()

    result = None

    if hid:
        result = households.get(hid)

    elif nric:
        for h in households.values():
            if nric in h["members"]:
                result = h
                break

    if not result:
        return "No result found <br><a href='/household'>Back</a>"

    return f"""
    <h2>Search Result</h2>
    Household ID: {result['household_id']}<br>
    Members: {", ".join(result['members'])}<br>
    Postal: {result['postal_code']}<br>
    Address: {result['address']}<br>
    Registered At: {result['registered_at']}<br><br>
    <a href="/household">Back</a>
    """


@app.route("/list")
def list_all():
    html = "<h2>All Households</h2>"

    for h in households.values():
        html += f"""
        <hr>
        {h['household_id']}<br>
        {", ".join(h['members'])}<br>
        {h['postal_code']}<br>
        {h['address']}<br>
        """

    html += "<br><a href='/household'>Back</a>"
    return html


# ===== Run =====
if __name__ == "__main__":
    load_from_file()
    app.run(port=5000, debug=False)
