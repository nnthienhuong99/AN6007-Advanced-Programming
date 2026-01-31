# server.py
from flask import Flask, jsonify, request, render_template_string
import os
import random
import string
from datetime import datetime
import json

app = Flask(__name__)



# Data structure
data = {
    "households": {},  # {household_id: {details}}
    "merchants": {},   # {merchant_id: {details}}
    "vouchers": {},    # {household_id: {2: count, 5: count, 10: count}}
    "transactions": [], # transaction records
    "redemption_codes": {}  # {code: {transaction_details}}
}

# Data file
DATA_FILE = "data/system_data.json"

def generate_voucher_id():
    """Generate voucher ID"""
    return f"V{random.randint(1000000, 9999999)}"

def generate_redemption_code():
    """Generate 20-digit random redemption code"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(20))

def save_data():
    """Save data to file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_data():
    """Load data from file"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            global data
            data = json.load(f)

# Load data on initialization
os.makedirs("data", exist_ok=True)
os.makedirs("output", exist_ok=True)
load_data()

def create_sample_data():
    """Create sample data for testing"""
    global data
    
    # Clear existing data
    data = {
        "households": {},
        "merchants": {},
        "vouchers": {},
        "transactions": [],
        "redemption_codes": {}
    }
    
    # Sample households
    households = [
        ("H001", "123456", 4),
        ("H002", "234567", 2),
        ("H003", "345678", 3)
    ]
    
    for hid, postal, people in households:
        # Calculate district
        district = "Central"
        if postal and len(postal) >= 2:
            try:
                sector = int(postal[:2])
                if 1 <= sector <= 6:
                    district = "Central"
                elif 7 <= sector <= 8:
                    district = "Downtown Core"
                elif 9 <= sector <= 10:
                    district = "Queenstown/Tiong Bahru"
                elif 11 <= sector <= 16:
                    district = "South"
                elif 17 <= sector <= 28:
                    district = "North/East/West"
            except:
                pass
        
        data["households"][hid] = {
            "household_id": hid,
            "postal_code": postal,
            "district": district,
            "num_people": people,
            "registered_date": datetime.now().strftime("%Y-%m-%d"),
            "claimed_tranches": ["May2025"]
        }
        # May2025 allocation: 50*2 + 20*5 + 30*10 = $500
        data["vouchers"][hid] = {"2": 50, "5": 20, "10": 30}
    
    # Sample merchants
    merchants = [
        ("M001", "ABC Supermarket"),
        ("M002", "XYZ Bakery"),
        ("M003", "Happy Mart")
    ]
    
    for mid, name in merchants:
        data["merchants"][mid] = {
            "merchant_id": mid,
            "merchant_name": name,
            "registration_date": datetime.now().strftime("%Y-%m-%d"),
            "status": "Active"
        }
    
    save_data()
    return True

# ========== HTML Template ==========

HOME_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>CDC Voucher System</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1, h2, h3 {
            color: #333;
        }
        .section {
            border: 1px solid #ddd;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
            background: #fafafa;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input, select, button {
            padding: 10px;
            margin: 5px 0;
            width: 300px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        button {
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
            font-weight: bold;
        }
        button:hover {
            background-color: #45a049;
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            background: #e8f5e9;
            border: 1px solid #4CAF50;
            border-radius: 4px;
            white-space: pre-wrap;
            font-family: monospace;
        }
        .error {
            background: #ffebee;
            border-color: #f44336;
            color: #d32f2f;
        }
        .success {
            background: #e8f5e9;
            border-color: #4CAF50;
            color: #2e7d32;
        }
        .code-display {
            font-size: 18px;
            font-weight: bold;
            color: #1976d2;
            background: #e3f2fd;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
            text-align: center;
        }
        .balance-display {
            display: flex;
            gap: 20px;
            margin: 10px 0;
        }
        .balance-item {
            text-align: center;
            padding: 10px;
            background: #e8f5e9;
            border-radius: 4px;
            min-width: 100px;
        }
        .nav {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            background: #f0f0f0;
            padding: 10px;
            border-radius: 4px;
        }
        .nav button {
            width: auto;
            padding: 10px 20px;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏠 CDC Voucher System</h1>
        
        <div class="nav">
            <button onclick="showTab('household')">Household User</button>
            <button onclick="showTab('merchant')">Merchant User</button>
            <button onclick="showTab('admin')">System Admin</button>
        </div>
        
        <!-- Household User Tab -->
        <div id="household-tab" class="tab-content active">
            <h2>👨‍👩‍👧‍👦 Household Operations</h2>
            
            <!-- Register Household -->
            <div class="section">
                <h3>📝 Register New Household</h3>
                <div class="form-group">
                    <label for="hh-id">Household ID:</label>
                    <input type="text" id="hh-id" placeholder="e.g. H001">
                </div>
                <div class="form-group">
                    <label for="postal">Postal Code:</label>
                    <input type="text" id="postal" placeholder="e.g. 123456">
                </div>
                <div class="form-group">
                    <label for="people">Number of People:</label>
                    <input type="number" id="people" value="1" min="1">
                </div>
                <button onclick="registerHousehold()">Register Household</button>
                <div id="register-result" class="result"></div>
            </div>
            
            <!-- Claim Vouchers -->
            <div class="section">
                <h3>🎫 Claim Vouchers</h3>
                <div class="form-group">
                    <label for="claim-hh-id">Household ID:</label>
                    <input type="text" id="claim-hh-id" placeholder="e.g. H001">
                </div>
                <div class="form-group">
                    <label for="tranche">Select Tranche:</label>
                    <select id="tranche">
                        <option value="May2025">May 2025 Tranche ($500)</option>
                        <option value="Jan2026">January 2026 Tranche ($300)</option>
                    </select>
                </div>
                <button onclick="claimVouchers()">Claim Vouchers</button>
                <div id="claim-result" class="result"></div>
            </div>
            
            <!-- Check Balance -->
            <div class="section">
                <h3>💰 Check Balance</h3>
                <div class="form-group">
                    <label for="balance-hh-id">Household ID:</label>
                    <input type="text" id="balance-hh-id" placeholder="e.g. H001">
                </div>
                <button onclick="checkBalance()">Check Balance</button>
                <div id="balance-result" class="result"></div>
            </div>
            
            <!-- Generate Redemption Code -->
            <div class="section">
                <h3>🛒 Generate Redemption Code</h3>
                <div class="form-group">
                    <label for="redeem-hh-id">Household ID:</label>
                    <input type="text" id="redeem-hh-id" placeholder="e.g. H001">
                </div>
                <div class="form-group">
                    <label for="redeem-merchant-id">Merchant ID:</label>
                    <input type="text" id="redeem-merchant-id" placeholder="e.g. M001">
                </div>
                <div class="form-group">
                    <label for="amount">Redemption Amount ($):</label>
                    <input type="number" id="amount" placeholder="e.g. 50" min="2">
                </div>
                <button onclick="generateRedemptionCode()">Generate Redemption Code</button>
                <div id="redeem-result" class="result"></div>
            </div>
        </div>
        
        <!-- Merchant User Tab -->
        <div id="merchant-tab" class="tab-content">
            <h2>🏪 Merchant Operations</h2>
            
            <!-- Register Merchant -->
            <div class="section">
                <h3>📝 Register New Merchant</h3>
                <div class="form-group">
                    <label for="merchant-id">Merchant ID:</label>
                    <input type="text" id="merchant-id" placeholder="e.g. M001">
                </div>
                <div class="form-group">
                    <label for="merchant-name">Merchant Name:</label>
                    <input type="text" id="merchant-name" placeholder="e.g. ABC Supermarket">
                </div>
                <button onclick="registerMerchant()">Register Merchant</button>
                <div id="merchant-register-result" class="result"></div>
            </div>
            
            <!-- Verify Redemption Code -->
            <div class="section">
                <h3>✅ Verify Redemption Code</h3>
                <div class="form-group">
                    <label for="verify-merchant-id">Merchant ID:</label>
                    <input type="text" id="verify-merchant-id" placeholder="e.g. M001">
                </div>
                <div class="form-group">
                    <label for="redemption-code">Redemption Code:</label>
                    <input type="text" id="redemption-code" placeholder="Enter 20-digit code">
                </div>
                <button onclick="verifyRedemptionCode()">Verify Redemption Code</button>
                <div id="verify-result" class="result"></div>
            </div>
        </div>
        
        <!-- System Admin Tab -->
        <div id="admin-tab" class="tab-content">
            <h2>⚙️ System Administration</h2>
            
            <div class="section">
                <h3>📊 System Statistics</h3>
                <button onclick="getSystemStats()">View System Statistics</button>
                <div id="stats-result" class="result"></div>
            </div>
            
            <div class="section">
                <h3>📁 Export Data</h3>
                <div class="form-group">
                    <label for="export-date">Date (YYYYMMDD):</label>
                    <input type="text" id="export-date" value="{{ today_date }}">
                </div>
                <div class="form-group">
                    <label for="export-hour">Hour (HH):</label>
                    <input type="text" id="export-hour" value="{{ current_hour }}">
                </div>
                <button onclick="exportData()">Export Data</button>
                <div id="export-result" class="result"></div>
            </div>
            
            <div class="section">
                <h3>🔄 Reset System</h3>
                <p>Warning: This will clear all data!</p>
                <button onclick="resetSystem()" style="background-color: #f44336;">Reset System</button>
            </div>
        </div>
    </div>
    
    <script>
        // Tab switching
        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            // Show selected tab
            document.getElementById(tabName + '-tab').classList.add('active');
        }
        
        // Household Registration
        async function registerHousehold() {
            const householdId = document.getElementById('hh-id').value;
            const postalCode = document.getElementById('postal').value;
            const numPeople = document.getElementById('people').value;
            
            const response = await fetch('/api/households/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    household_id: householdId,
                    postal_code: postalCode,
                    num_people: parseInt(numPeople)
                })
            });
            
            const result = await response.json();
            const resultDiv = document.getElementById('register-result');
            resultDiv.innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
            resultDiv.className = result.success ? 'result success' : 'result error';
        }
        
        // Claim Vouchers
        async function claimVouchers() {
            const householdId = document.getElementById('claim-hh-id').value;
            const tranche = document.getElementById('tranche').value;
            
            const response = await fetch('/api/households/claim', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    household_id: householdId,
                    tranche: tranche
                })
            });
            
            const result = await response.json();
            const resultDiv = document.getElementById('claim-result');
            
            if (result.success) {
                let html = `<div class="success">✅ Claim Successful!</div>`;
                html += `<div class="balance-display">`;
                html += `<div class="balance-item"><div>$2 Vouchers</div><div><strong>${result.balance[2] || 0}</strong></div></div>`;
                html += `<div class="balance-item"><div>$5 Vouchers</div><div><strong>${result.balance[5] || 0}</strong></div></div>`;
                html += `<div class="balance-item"><div>$10 Vouchers</div><div><strong>${result.balance[10] || 0}</strong></div></div>`;
                html += `</div>`;
                html += `<div>Total Value: $${result.total_value}</div>`;
                resultDiv.innerHTML = html;
            } else {
                resultDiv.innerHTML = `<div class="error">❌ ${result.error}</div>`;
            }
        }
        
        // Check Balance
        async function checkBalance() {
            const householdId = document.getElementById('balance-hh-id').value;
            
            const response = await fetch(`/api/households/${householdId}/balance`);
            const result = await response.json();
            const resultDiv = document.getElementById('balance-result');
            
            if (result.success) {
                let html = `<div class="success">💰 Balance Information</div>`;
                html += `<div><strong>Household ID:</strong> ${householdId}</div>`;
                html += `<div><strong>Postal Code:</strong> ${result.postal_code}</div>`;
                html += `<div class="balance-display">`;
                html += `<div class="balance-item"><div>$2 Vouchers</div><div><strong>${result.balance[2] || 0}</strong></div></div>`;
                html += `<div class="balance-item"><div>$5 Vouchers</div><div><strong>${result.balance[5] || 0}</strong></div></div>`;
                html += `<div class="balance-item"><div>$10 Vouchers</div><div><strong>${result.balance[10] || 0}</strong></div></div>`;
                html += `</div>`;
                html += `<div><strong>Total Vouchers:</strong> ${result.total_vouchers}</div>`;
                html += `<div><strong>Total Value:</strong> $${result.total_value}</div>`;
                html += `<div><strong>Claimed Tranches:</strong> ${result.claimed_tranches.join(', ')}</div>`;
                resultDiv.innerHTML = html;
            } else {
                resultDiv.innerHTML = `<div class="error">❌ ${result.error}</div>`;
            }
        }
        
        // Generate Redemption Code
        async function generateRedemptionCode() {
            const householdId = document.getElementById('redeem-hh-id').value;
            const merchantId = document.getElementById('redeem-merchant-id').value;
            const amount = document.getElementById('amount').value;
            
            const response = await fetch('/api/redemptions/create', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    household_id: householdId,
                    merchant_id: merchantId,
                    amount: parseFloat(amount)
                })
            });
            
            const result = await response.json();
            const resultDiv = document.getElementById('redeem-result');
            
            if (result.success) {
                let html = `<div class="success">✅ Redemption Code Generated!</div>`;
                html += `<div class="code-display">${result.redemption_code}</div>`;
                html += `<div><strong>Give this code to the merchant</strong></div>`;
                html += `<div><small>Household ID: ${householdId}</small></div>`;
                html += `<div><small>Merchant ID: ${merchantId}</small></div>`;
                html += `<div><small>Amount: $${amount}</small></div>`;
                html += `<div><small>Generated: ${result.timestamp}</small></div>`;
                resultDiv.innerHTML = html;
            } else {
                resultDiv.innerHTML = `<div class="error">❌ ${result.error}</div>`;
            }
        }
        
        // Register Merchant
        async function registerMerchant() {
            const merchantId = document.getElementById('merchant-id').value;
            const merchantName = document.getElementById('merchant-name').value;
            
            const response = await fetch('/api/merchants/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    merchant_id: merchantId,
                    merchant_name: merchantName
                })
            });
            
            const result = await response.json();
            const resultDiv = document.getElementById('merchant-register-result');
            resultDiv.innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
            resultDiv.className = result.success ? 'result success' : 'result error';
        }
        
        // Verify Redemption Code
        async function verifyRedemptionCode() {
            const merchantId = document.getElementById('verify-merchant-id').value;
            const redemptionCode = document.getElementById('redemption-code').value;
            
            const response = await fetch('/api/redemptions/verify', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    merchant_id: merchantId,
                    redemption_code: redemptionCode
                })
            });
            
            const result = await response.json();
            const resultDiv = document.getElementById('verify-result');
            
            if (result.success) {
                let html = `<div class="success">✅ Verification Successful!</div>`;
                html += `<div><strong>Transaction ID:</strong> ${result.transaction_id}</div>`;
                html += `<div><strong>Household ID:</strong> ${result.household_id}</div>`;
                html += `<div><strong>Merchant ID:</strong> ${result.merchant_id}</div>`;
                html += `<div><strong>Amount:</strong> $${result.amount}</div>`;
                html += `<div><strong>Verified at:</strong> ${result.timestamp}</div>`;
                resultDiv.innerHTML = html;
            } else {
                resultDiv.innerHTML = `<div class="error">❌ ${result.error}</div>`;
            }
        }
        
        // System Statistics
        async function getSystemStats() {
            const response = await fetch('/api/system/stats');
            const result = await response.json();
            const resultDiv = document.getElementById('stats-result');
            resultDiv.innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
        }
        
        // Export Data
        async function exportData() {
            const date = document.getElementById('export-date').value;
            const hour = document.getElementById('export-hour').value;
            
            const response = await fetch(`/api/export/balance?date=${date}&hour=${hour}`);
            const result = await response.json();
            const resultDiv = document.getElementById('export-result');
            
            if (result.success) {
                resultDiv.innerHTML = `<div class="success">✅ Data Exported Successfully!</div><pre>${JSON.stringify(result, null, 2)}</pre>`;
            } else {
                resultDiv.innerHTML = `<div class="error">❌ ${result.error}</div>`;
            }
        }
        
        // Reset System
        async function resetSystem() {
            if (confirm('Are you sure you want to reset the system? This will clear all data!')) {
                const response = await fetch('/api/system/reset', {method: 'POST'});
                const result = await response.json();
                alert(result.message);
                location.reload();
            }
        }
    </script>
</body>
</html>
"""

# ========== API Routes ==========

@app.route("/")
def home():
    """Home page - display web interface"""
    today = datetime.now().strftime("%Y%m%d")
    current_hour = datetime.now().strftime("%H")
    return render_template_string(HOME_TEMPLATE, today_date=today, current_hour=current_hour)

@app.route("/api/households/register", methods=["POST"])
def register_household():
    """Register a household"""
    request_data = request.get_json()
    
    if not request_data or "household_id" not in request_data or "postal_code" not in request_data:
        return jsonify({"success": False, "error": "Missing required fields"})
    
    household_id = request_data["household_id"]
    
    if household_id in data["households"]:
        return jsonify({"success": False, "error": "Household already exists"})
    
    # Calculate district
    postal_code = request_data["postal_code"]
    district = "Unknown"
    if postal_code and len(postal_code) >= 2:
        try:
            sector = int(postal_code[:2])
            if 1 <= sector <= 6:
                district = "Central"
            elif 7 <= sector <= 8:
                district = "Downtown Core"
            elif 9 <= sector <= 10:
                district = "Queenstown/Tiong Bahru"
            elif 11 <= sector <= 16:
                district = "South"
            elif 17 <= sector <= 28:
                district = "North/East/West"
        except:
            pass
    
    # Save household information
    data["households"][household_id] = {
        "household_id": household_id,
        "postal_code": postal_code,
        "district": district,
        "num_people": request_data.get("num_people", 1),
        "registered_date": datetime.now().strftime("%Y-%m-%d"),
        "claimed_tranches": []
    }
    
    # Initialize voucher balance
    data["vouchers"][household_id] = {"2": 0, "5": 0, "10": 0}
    
    save_data()
    
    return jsonify({
        "success": True,
        "message": "Household registered successfully",
        "household_id": household_id,
        "district": district
    })

@app.route("/api/households/claim", methods=["POST"])
def claim_vouchers():
    """Claim vouchers"""
    request_data = request.get_json()
    
    if not request_data or "household_id" not in request_data or "tranche" not in request_data:
        return jsonify({"success": False, "error": "Missing required fields"})
    
    household_id = request_data["household_id"]
    tranche = request_data["tranche"]
    
    if household_id not in data["households"]:
        return jsonify({"success": False, "error": "Household does not exist"})
    
    household = data["households"][household_id]
    
    # Check if tranche already claimed
    if tranche in household["claimed_tranches"]:
        return jsonify({"success": False, "error": f"Already claimed {tranche} tranche"})
    
    # Allocate vouchers based on tranche
    if tranche == "May2025":
        # $500: 50*$2 + 20*$5 + 30*$10 = $500
        allocation = {"2": 50, "5": 20, "10": 30}
    elif tranche == "Jan2026":
        # $300: 30*$2 + 12*$5 + 15*$10 = $300
        allocation = {"2": 30, "5": 12, "10": 15}
    else:
        return jsonify({"success": False, "error": "Invalid tranche"})
    
    # Update balance
    for denom, count in allocation.items():
        data["vouchers"][household_id][denom] += count
    
    # Mark as claimed
    household["claimed_tranches"].append(tranche)
    
    save_data()
    
    return jsonify({
        "success": True,
        "message": "Vouchers claimed successfully",
        "household_id": household_id,
        "tranche": tranche,
        "balance": data["vouchers"][household_id],
        "total_value": sum(int(k)*v for k, v in data["vouchers"][household_id].items())
    })

@app.route("/api/households/<household_id>/balance")
def get_balance(household_id):
    """Get household balance"""
    if household_id not in data["households"]:
        return jsonify({"success": False, "error": "Household does not exist"})
    
    household = data["households"][household_id]
    balance = data["vouchers"].get(household_id, {"2": 0, "5": 0, "10": 0})
    
    total_vouchers = sum(balance.values())
    total_value = sum(int(k)*v for k, v in balance.items())
    
    return jsonify({
        "success": True,
        "household_id": household_id,
        "postal_code": household["postal_code"],
        "district": household["district"],
        "balance": balance,
        "total_vouchers": total_vouchers,
        "total_value": total_value,
        "claimed_tranches": household["claimed_tranches"]
    })

@app.route("/api/merchants/register", methods=["POST"])
def register_merchant():
    """Register a merchant"""
    request_data = request.get_json()
    
    if not request_data or "merchant_id" not in request_data or "merchant_name" not in request_data:
        return jsonify({"success": False, "error": "Missing required fields"})
    
    merchant_id = request_data["merchant_id"]
    
    if merchant_id in data["merchants"]:
        return jsonify({"success": False, "error": "Merchant already exists"})
    
    # Save merchant information
    data["merchants"][merchant_id] = {
        "merchant_id": merchant_id,
        "merchant_name": request_data["merchant_name"],
        "registration_date": datetime.now().strftime("%Y-%m-%d"),
        "status": "Active"
    }
    
    save_data()
    
    return jsonify({
        "success": True,
        "message": "Merchant registered successfully",
        "merchant_id": merchant_id
    })

@app.route("/api/redemptions/create", methods=["POST"])
def create_redemption():
    """Create redemption (generate redemption code)"""
    request_data = request.get_json()
    
    if not request_data or "household_id" not in request_data or "merchant_id" not in request_data or "amount" not in request_data:
        return jsonify({"success": False, "error": "Missing required fields"})
    
    household_id = request_data["household_id"]
    merchant_id = request_data["merchant_id"]
    amount = float(request_data["amount"])
    
    if household_id not in data["households"]:
        return jsonify({"success": False, "error": "Household does not exist"})
    
    if merchant_id not in data["merchants"]:
        return jsonify({"success": False, "error": "Merchant does not exist"})
    
    # Check if balance is sufficient
    balance = data["vouchers"].get(household_id, {"2": 0, "5": 0, "10": 0})
    total_balance = sum(int(k)*v for k, v in balance.items())
    
    if total_balance < amount:
        return jsonify({"success": False, "error": "Insufficient balance"})
    
    # Calculate optimal redemption combination (greedy algorithm)
    denominations = [10, 5, 2]
    remaining = amount
    redemption_details = {}
    
    for denom in denominations:
        denom_str = str(denom)
        available = balance.get(denom_str, 0)
        needed = min(available, remaining // denom)
        
        if needed > 0:
            redemption_details[denom_str] = needed
            remaining -= needed * denom
    
    # Check if exact amount can be redeemed
    if remaining != 0:
        return jsonify({"success": False, "error": "Cannot redeem exact amount with available denominations"})
    
    # Generate redemption code
    redemption_code = generate_redemption_code()
    transaction_id = f"TX{random.randint(100000, 999999)}"
    
    # Save transaction record (pending verification)
    transaction = {
        "transaction_id": transaction_id,
        "household_id": household_id,
        "merchant_id": merchant_id,
        "amount": amount,
        "redemption_code": redemption_code,
        "status": "pending",  # pending verification
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "redemption_details": redemption_details
    }
    
    data["transactions"].append(transaction)
    data["redemption_codes"][redemption_code] = transaction
    
    save_data()
    
    return jsonify({
        "success": True,
        "message": "Redemption code generated successfully",
        "transaction_id": transaction_id,
        "household_id": household_id,
        "merchant_id": merchant_id,
        "amount": amount,
        "redemption_code": redemption_code,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "instructions": "Give this redemption code to the merchant for verification"
    })

@app.route("/api/redemptions/verify", methods=["POST"])
def verify_redemption():
    """Verify redemption code"""
    request_data = request.get_json()
    
    if not request_data or "merchant_id" not in request_data or "redemption_code" not in request_data:
        return jsonify({"success": False, "error": "Missing required fields"})
    
    merchant_id = request_data["merchant_id"]
    redemption_code = request_data["redemption_code"]
    
    if merchant_id not in data["merchants"]:
        return jsonify({"success": False, "error": "Merchant does not exist"})
    
    if redemption_code not in data["redemption_codes"]:
        return jsonify({"success": False, "error": "Invalid redemption code"})
    
    transaction = data["redemption_codes"][redemption_code]
    
    if transaction["status"] != "pending":
        return jsonify({"success": False, "error": "Redemption code already used or expired"})
    
    if transaction["merchant_id"] != merchant_id:
        return jsonify({"success": False, "error": "This redemption code does not belong to this merchant"})
    
    # Check if household balance is sufficient (prevent concurrency issues)
    household_id = transaction["household_id"]
    balance = data["vouchers"].get(household_id, {"2": 0, "5": 0, "10": 0})
    
    # Deduct vouchers
    redemption_details = transaction["redemption_details"]
    for denom_str, count in redemption_details.items():
        if balance.get(denom_str, 0) < count:
            return jsonify({"success": False, "error": "Household balance insufficient, cannot complete verification"})
        
        balance[denom_str] -= count
    
    # Update balance
    data["vouchers"][household_id] = balance
    
    # Update transaction status
    transaction["status"] = "completed"
    transaction["verified_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Save to CSV file
    save_to_csv(transaction)
    
    save_data()
    
    return jsonify({
        "success": True,
        "message": "Verification successful",
        "transaction_id": transaction["transaction_id"],
        "household_id": household_id,
        "merchant_id": merchant_id,
        "amount": transaction["amount"],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

def save_to_csv(transaction):
    """Save transaction record to CSV file"""
    date_str = datetime.now().strftime("%Y%m%d")
    hour_str = datetime.now().strftime("%H")
    filename = f"output/Redeem{date_str}{hour_str}.csv"
    
    # Prepare data rows
    rows = []
    redemption_details = transaction["redemption_details"]
    
    for denom_str, count in redemption_details.items():
        for i in range(count):
            row = {
                "Transaction_ID": transaction["transaction_id"],
                "Household_ID": transaction["household_id"],
                "Merchant_ID": transaction["merchant_id"],
                "Transaction_Date_Time": transaction["created_at"].replace("-", "").replace(":", "").replace(" ", ""),
                "Voucher_Code": generate_voucher_id(),
                "Denomination_Used": f"${denom_str}.00",
                "Amount_Redeemed": f"${int(denom_str) * count}.00",
                "Payment_Status": "Completed",
                "Remarks": "Final denomination used" if i == count-1 else str(i+1)
            }
            rows.append(row)
    
    # Write to CSV
    import csv
    file_exists = os.path.exists(filename)
    
    with open(filename, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ["Transaction_ID", "Household_ID", "Merchant_ID", "Transaction_Date_Time", 
                     "Voucher_Code", "Denomination_Used", "Amount_Redeemed", "Payment_Status", "Remarks"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        for row in rows:
            writer.writerow(row)

@app.route("/api/system/stats")
def system_stats():
    """System statistics"""
    total_households = len(data["households"])
    total_merchants = len(data["merchants"])
    total_transactions = len([t for t in data["transactions"] if t["status"] == "completed"])
    pending_transactions = len([t for t in data["transactions"] if t["status"] == "pending"])
    
    # Calculate total issued and total redeemed
    total_issued = 0
    total_redeemed = 0
    
    for household_id, vouchers in data["vouchers"].items():
        for denom_str, count in vouchers.items():
            total_issued += int(denom_str) * count
    
    for transaction in data["transactions"]:
        if transaction["status"] == "completed":
            total_redeemed += transaction["amount"]
    
    return jsonify({
        "success": True,
        "total_households": total_households,
        "total_merchants": total_merchants,
        "total_transactions": total_transactions,
        "pending_transactions": pending_transactions,
        "total_vouchers_issued": total_issued,
        "total_vouchers_redeemed": total_redeemed,
        "remaining_balance": total_issued - total_redeemed,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route("/api/export/balance")
def export_balance():
    """Export balance data"""
    date = request.args.get("date", datetime.now().strftime("%Y%m%d"))
    hour = request.args.get("hour", datetime.now().strftime("%H"))
    
    filename = f"output/RedemptionBalance{date}{hour}.csv"
    
    # Write to CSV
    import csv
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ["Household_ID", "Postal_Code", "District", "Denomination_$2", 
                     "Denomination_$5", "Denomination_$10", "Total_Vouchers", "Total_Value"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for household_id, household in data["households"].items():
            balance = data["vouchers"].get(household_id, {"2": 0, "5": 0, "10": 0})
            total_vouchers = sum(balance.values())
            total_value = sum(int(k)*v for k, v in balance.items())
            
            row = {
                "Household_ID": household_id,
                "Postal_Code": household["postal_code"],
                "District": household["district"],
                "Denomination_$2": balance.get("2", 0),
                "Denomination_$5": balance.get("5", 0),
                "Denomination_$10": balance.get("10", 0),
                "Total_Vouchers": total_vouchers,
                "Total_Value": total_value
            }
            writer.writerow(row)
    
    return jsonify({
        "success": True,
        "message": "Data exported successfully",
        "filename": filename,
        "records_exported": len(data["households"])
    })

@app.route("/api/system/reset", methods=["POST"])
def reset_system():
    """Reset system (API endpoint)"""
    if create_sample_data():
        return jsonify({
            "success": True,
            "message": "System reset successfully, sample data created"
        })
    else:
        return jsonify({
            "success": False,
            "error": "Failed to reset system"
        })

@app.route("/api/health")
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "data_summary": {
            "households": len(data["households"]),
            "merchants": len(data["merchants"]),
            "transactions": len(data["transactions"])
        }
    })

if __name__ == "__main__":
    print("=" * 50)
    print("CDC Voucher System starting...")
    print(f"Access URL: http://127.0.0.1:5000")
    print("=" * 50)
    
    # If no data exists, create sample data
    if not data["households"]:
        print("Creating sample data...")
        create_sample_data()
        print("Sample data created successfully.")
    
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )