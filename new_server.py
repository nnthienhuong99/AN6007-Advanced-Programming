# server.py
from flask import Flask, jsonify, render_template_string, request, send_file
from flask_cors import CORS
import os
from datetime import datetime
from typing import List

from data_structure import store
import services

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize system
services.initialize_system()


# -------- HTML Templates for Dashboard --------

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CDC Voucher System Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background-color: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%);
            color: white;
            padding: 30px 0;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 30px;
        }
        
        h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        
        .subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .stats-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1a73e8;
            margin: 10px 0;
        }
        
        .stat-label {
            font-size: 0.9rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .section {
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
        }
        
        .section-title {
            font-size: 1.5rem;
            margin-bottom: 20px;
            color: #333;
            border-bottom: 2px solid #1a73e8;
            padding-bottom: 10px;
        }
        
        .api-list {
            list-style: none;
        }
        
        .api-item {
            padding: 15px;
            background: #f8f9fa;
            margin-bottom: 10px;
            border-left: 4px solid #1a73e8;
            border-radius: 5px;
        }
        
        .api-method {
            display: inline-block;
            padding: 5px 10px;
            background: #1a73e8;
            color: white;
            border-radius: 3px;
            font-size: 0.8rem;
            font-weight: bold;
            margin-right: 10px;
        }
        
        .api-get { background: #34a853; }
        .api-post { background: #1a73e8; }
        .api-put { background: #fbbc05; }
        .api-delete { background: #ea4335; }
        
        .api-endpoint {
            font-family: 'Courier New', monospace;
            font-size: 1rem;
        }
        
        .api-desc {
            margin-top: 5px;
            color: #666;
            font-size: 0.9rem;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #444;
        }
        
        input, select, textarea {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 1rem;
            transition: border-color 0.3s;
        }
        
        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #1a73e8;
            box-shadow: 0 0 0 3px rgba(26, 115, 232, 0.1);
        }
        
        button {
            background: #1a73e8;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 5px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s;
        }
        
        button:hover {
            background: #0d47a1;
        }
        
        .response-box {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-top: 20px;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
            white-space: pre-wrap;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .tab-container {
            margin-bottom: 20px;
        }
        
        .tabs {
            display: flex;
            border-bottom: 1px solid #ddd;
            margin-bottom: 20px;
        }
        
        .tab {
            padding: 15px 30px;
            cursor: pointer;
            background: #f8f9fa;
            border: 1px solid #ddd;
            border-bottom: none;
            margin-right: 5px;
            border-radius: 5px 5px 0 0;
            transition: background 0.3s;
        }
        
        .tab:hover {
            background: #e9ecef;
        }
        
        .tab.active {
            background: white;
            border-bottom: 1px solid white;
            margin-bottom: -1px;
            font-weight: bold;
            color: #1a73e8;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .refresh-btn {
            background: #34a853;
            margin-left: 10px;
        }
        
        .refresh-btn:hover {
            background: #2e8b47;
        }
        
        @media (max-width: 768px) {
            .header-content {
                flex-direction: column;
                text-align: center;
            }
            
            h1 {
                font-size: 2rem;
            }
            
            .stats-container {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <header>
        <div class="header-content">
            <div>
                <h1>CDC Voucher System Dashboard</h1>
                <p class="subtitle">Administrative Dashboard for Voucher Management and Analytics</p>
            </div>
            <div>
                <p>Last updated: <span id="current-time">Loading...</span></p>
                <button onclick="refreshDashboard()" class="refresh-btn">🔄 Refresh Data</button>
            </div>
        </div>
    </header>
    
    <div class="container">
        <div class="stats-container" id="stats-container">
            <!-- Stats will be loaded dynamically -->
            <div class="stat-card">
                <div class="stat-label">Total Households</div>
                <div class="stat-value" id="total-households">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Merchants</div>
                <div class="stat-value" id="total-merchants">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Vouchers Issued</div>
                <div class="stat-value" id="vouchers-issued">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Value Redeemed</div>
                <div class="stat-value" id="value-redeemed">$0</div>
            </div>
        </div>
        
        <div class="tab-container">
            <div class="tabs">
                <div class="tab active" onclick="switchTab('api')">API Documentation</div>
                <div class="tab" onclick="switchTab('household')">Household Management</div>
                <div class="tab" onclick="switchTab('merchant')">Merchant Management</div>
                <div class="tab" onclick="switchTab('redemption')">Redemption</div>
                <div class="tab" onclick="switchTab('analytics')">Analytics</div>
            </div>
            
            <!-- API Documentation Tab -->
            <div id="api-tab" class="tab-content active">
                <div class="section">
                    <h2 class="section-title">API Documentation</h2>
                    <p>This system provides RESTful APIs for managing CDC vouchers. All responses are in JSON format.</p>
                    
                    <h3 style="margin: 20px 0 10px 0;">Household APIs</h3>
                    <ul class="api-list">
                        <li class="api-item">
                            <span class="api-method api-post">POST</span>
                            <span class="api-endpoint">/api/households</span>
                            <p class="api-desc">Register a new household</p>
                        </li>
                        <li class="api-item">
                            <span class="api-method api-get">GET</span>
                            <span class="api-endpoint">/api/households</span>
                            <p class="api-desc">Get all registered households</p>
                        </li>
                        <li class="api-item">
                            <span class="api-method api-get">GET</span>
                            <span class="api-endpoint">/api/households/&lt;household_id&gt;</span>
                            <p class="api-desc">Get household details and balance</p>
                        </li>
                        <li class="api-item">
                            <span class="api-method api-post">POST</span>
                            <span class="api-endpoint">/api/households/&lt;household_id&gt;/claim</span>
                            <p class="api-desc">Claim vouchers for a tranche</p>
                        </li>
                    </ul>
                    
                    <h3 style="margin: 20px 0 10px 0;">Merchant APIs</h3>
                    <ul class="api-list">
                        <li class="api-item">
                            <span class="api-method api-post">POST</span>
                            <span class="api-endpoint">/api/merchants</span>
                            <p class="api-desc">Register a new merchant</p>
                        </li>
                        <li class="api-item">
                            <span class="api-method api-get">GET</span>
                            <span class="api-endpoint">/api/merchants</span>
                            <p class="api-desc">Get all registered merchants</p>
                        </li>
                    </ul>
                    
                    <h3 style="margin: 20px 0 10px 0;">Redemption APIs</h3>
                    <ul class="api-list">
                        <li class="api-item">
                            <span class="api-method api-post">POST</span>
                            <span class="api-endpoint">/api/redemptions</span>
                            <p class="api-desc">Redeem vouchers</p>
                        </li>
                        <li class="api-item">
                            <span class="api-method api-get">GET</span>
                            <span class="api-endpoint">/api/analytics</span>
                            <p class="api-desc">Get system analytics</p>
                        </li>
                        <li class="api-item">
                            <span class="api-method api-get">GET</span>
                            <span class="api-endpoint">/api/balances/export</span>
                            <p class="api-desc">Export balance snapshot</p>
                        </li>
                    </ul>
                </div>
            </div>
            
            <!-- Household Management Tab -->
            <div id="household-tab" class="tab-content">
                <div class="section">
                    <h2 class="section-title">Register New Household</h2>
                    <form id="household-form">
                        <div class="form-group">
                            <label for="household-id">Household ID</label>
                            <input type="text" id="household-id" placeholder="e.g., H001" required>
                        </div>
                        <div class="form-group">
                            <label for="postal-code">Postal Code</label>
                            <input type="text" id="postal-code" placeholder="e.g., 123456" required>
                        </div>
                        <div class="form-group">
                            <label for="num-people">Number of People</label>
                            <input type="number" id="num-people" value="1" min="1" max="20">
                        </div>
                        <button type="button" onclick="registerHousehold()">Register Household</button>
                    </form>
                    <div id="household-response" class="response-box"></div>
                </div>
                
                <div class="section">
                    <h2 class="section-title">Claim Vouchers</h2>
                    <form id="claim-form">
                        <div class="form-group">
                            <label for="claim-household-id">Household ID</label>
                            <input type="text" id="claim-household-id" placeholder="e.g., H001" required>
                        </div>
                        <div class="form-group">
                            <label for="tranche">Tranche</label>
                            <select id="tranche">
                                <option value="May2025">May 2025 ($500)</option>
                                <option value="Jan2026">January 2026 ($300)</option>
                            </select>
                        </div>
                        <button type="button" onclick="claimVouchers()">Claim Vouchers</button>
                    </form>
                    <div id="claim-response" class="response-box"></div>
                </div>
                
                <div class="section">
                    <h2 class="section-title">Household Balance Check</h2>
                    <form id="balance-form">
                        <div class="form-group">
                            <label for="balance-household-id">Household ID</label>
                            <input type="text" id="balance-household-id" placeholder="e.g., H001" required>
                        </div>
                        <button type="button" onclick="checkBalance()">Check Balance</button>
                    </form>
                    <div id="balance-response" class="response-box"></div>
                </div>
            </div>
            
            <!-- Merchant Management Tab -->
            <div id="merchant-tab" class="tab-content">
                <div class="section">
                    <h2 class="section-title">Register New Merchant</h2>
                    <p>Use the form below to register a new merchant. All fields are required.</p>
                    <form id="merchant-form">
                        <div class="form-group">
                            <label for="merchant-id">Merchant ID</label>
                            <input type="text" id="merchant-id" placeholder="e.g., M001" required>
                        </div>
                        <div class="form-group">
                            <label for="merchant-name">Merchant Name</label>
                            <input type="text" id="merchant-name" placeholder="e.g., ABC Minimart" required>
                        </div>
                        <div class="form-group">
                            <label for="uen">UEN</label>
                            <input type="text" id="uen" placeholder="e.g., 201234567A" required>
                        </div>
                        <div class="form-group">
                            <label for="bank-name">Bank Name</label>
                            <input type="text" id="bank-name" placeholder="e.g., DBS Bank Ltd" required>
                        </div>
                        <button type="button" onclick="registerMerchant()">Register Merchant</button>
                    </form>
                    <div id="merchant-response" class="response-box"></div>
                </div>
            </div>
            
            <!-- Redemption Tab -->
            <div id="redemption-tab" class="tab-content">
                <div class="section">
                    <h2 class="section-title">Redeem Vouchers</h2>
                    <p>Redeem vouchers for a household at a merchant.</p>
                    <form id="redemption-form">
                        <div class="form-group">
                            <label for="redeem-household-id">Household ID</label>
                            <input type="text" id="redeem-household-id" placeholder="e.g., H001" required>
                        </div>
                        <div class="form-group">
                            <label for="redeem-merchant-id">Merchant ID</label>
                            <input type="text" id="redeem-merchant-id" placeholder="e.g., M001" required>
                        </div>
                        <div class="form-group">
                            <label for="redeem-amount">Amount to Redeem ($)</label>
                            <input type="number" id="redeem-amount" placeholder="e.g., 50" min="2" step="1" required>
                        </div>
                        <div class="form-group">
                            <label for="redeem-method">Redemption Method</label>
                            <select id="redeem-method">
                                <option value="optimal">Optimal (Use fewest vouchers)</option>
                                <option value="specific">Specific Denominations</option>
                            </select>
                        </div>
                        <button type="button" onclick="redeemVouchers()">Redeem Vouchers</button>
                    </form>
                    <div id="redemption-response" class="response-box"></div>
                </div>
            </div>
            
            <!-- Analytics Tab -->
            <div id="analytics-tab" class="tab-content">
                <div class="section">
                    <h2 class="section-title">System Analytics</h2>
                    <button onclick="loadAnalytics()" style="margin-bottom: 20px;">📊 Load Analytics</button>
                    <div id="analytics-response" class="response-box"></div>
                </div>
                
                <div class="section">
                    <h2 class="section-title">Export Balance Snapshot</h2>
                    <p>Export current balances to CSV file for a specific date and hour.</p>
                    <form id="export-form">
                        <div class="form-group">
                            <label for="export-date">Date (YYYYMMDD)</label>
                            <input type="text" id="export-date" placeholder="e.g., 20251102" required>
                        </div>
                        <div class="form-group">
                            <label for="export-hour">Hour (HH)</label>
                            <input type="text" id="export-hour" placeholder="e.g., 08" required>
                        </div>
                        <button type="button" onclick="exportBalances()">Export Balances</button>
                    </form>
                    <div id="export-response" class="response-box"></div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Update current time
        function updateTime() {
            const now = new Date();
            document.getElementById('current-time').textContent = 
                now.toLocaleDateString() + ' ' + now.toLocaleTimeString();
        }
        setInterval(updateTime, 1000);
        updateTime();
        
        // Tab switching
        function switchTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(tabName + '-tab').classList.add('active');
            event.target.classList.add('active');
        }
        
        // Load dashboard stats
        async function loadStats() {
            try {
                const response = await fetch('/api/analytics');
                const data = await response.json();
                
                document.getElementById('total-households').textContent = data.total_households || 0;
                document.getElementById('total-merchants').textContent = data.total_merchants || 0;
                document.getElementById('vouchers-issued').textContent = data.vouchers_issued || 0;
                document.getElementById('value-redeemed').textContent = '$' + (data.value_redeemed || 0);
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }
        
        // Refresh dashboard
        function refreshDashboard() {
            loadStats();
            updateTime();
        }
        
        // API Calls
        async function registerHousehold() {
            const householdId = document.getElementById('household-id').value;
            const postalCode = document.getElementById('postal-code').value;
            const numPeople = document.getElementById('num-people').value;
            
            const response = await fetch('/api/households', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    household_id: householdId,
                    postal_code: postalCode,
                    num_people: parseInt(numPeople)
                })
            });
            
            const data = await response.json();
            document.getElementById('household-response').textContent = JSON.stringify(data, null, 2);
            loadStats(); // Refresh stats
        }
        
        async function claimVouchers() {
            const householdId = document.getElementById('claim-household-id').value;
            const tranche = document.getElementById('tranche').value;
            
            const response = await fetch(`/api/households/${householdId}/claim`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ tranche: tranche })
            });
            
            const data = await response.json();
            document.getElementById('claim-response').textContent = JSON.stringify(data, null, 2);
            loadStats();
        }
        
        async function checkBalance() {
            const householdId = document.getElementById('balance-household-id').value;
            
            const response = await fetch(`/api/households/${householdId}`);
            const data = await response.json();
            document.getElementById('balance-response').textContent = JSON.stringify(data, null, 2);
        }
        
        async function registerMerchant() {
            const merchantId = document.getElementById('merchant-id').value;
            const merchantName = document.getElementById('merchant-name').value;
            const uen = document.getElementById('uen').value;
            const bankName = document.getElementById('bank-name').value;
            
            const response = await fetch('/api/merchants', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    merchant_id: merchantId,
                    merchant_name: merchantName,
                    uen: uen,
                    bank_name: bankName
                })
            });
            
            const data = await response.json();
            document.getElementById('merchant-response').textContent = JSON.stringify(data, null, 2);
            loadStats();
        }
        
        async function redeemVouchers() {
            const householdId = document.getElementById('redeem-household-id').value;
            const merchantId = document.getElementById('redeem-merchant-id').value;
            const amount = document.getElementById('redeem-amount').value;
            const method = document.getElementById('redeem-method').value;
            
            const response = await fetch('/api/redemptions', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    household_id: householdId,
                    merchant_id: merchantId,
                    amount: parseFloat(amount),
                    method: method
                })
            });
            
            const data = await response.json();
            document.getElementById('redemption-response').textContent = JSON.stringify(data, null, 2);
            loadStats();
        }
        
        async function loadAnalytics() {
            const response = await fetch('/api/analytics');
            const data = await response.json();
            document.getElementById('analytics-response').textContent = JSON.stringify(data, null, 2);
        }
        
        async function exportBalances() {
            const date = document.getElementById('export-date').value;
            const hour = document.getElementById('export-hour').value;
            
            const response = await fetch(`/api/balances/export?date=${date}&hour=${hour}`);
            const data = await response.json();
            document.getElementById('export-response').textContent = JSON.stringify(data, null, 2);
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            loadStats();
        });
    </script>
</body>
</html>
"""

# -------- API Routes --------

@app.route("/")
def home():
    """Dashboard homepage"""
    return render_template_string(DASHBOARD_HTML)


@app.route("/api/households", methods=["POST"])
def api_create_household():
    """Register a new household"""
    data = request.get_json()
    if not data or "household_id" not in data or "postal_code" not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    result = services.register_household(
        household_id=data["household_id"],
        postal_code=data["postal_code"],
        num_people=data.get("num_people", 1),
        nric_members=data.get("nric_members", {})
    )
    
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result), 201


@app.route("/api/households", methods=["GET"])
def api_list_households():
    """Get all registered households"""
    households = []
    for household_id, household in store.households.items():
        balance = store.voucher_index.get_household_balance(household_id)
        households.append({
            "household_id": household_id,
            "postal_code": household.postal_code,
            "district": household.district,
            "num_people": household.num_people,
            "registered_date": household.registered_date,
            "claimed_tranches": list(household.claimed_tranches),
            "balance": balance,
            "total_balance": sum(denom * count for denom, count in balance.items())
        })
    
    return jsonify({
        "success": True,
        "count": len(households),
        "households": households
    })


@app.route("/api/households/<household_id>", methods=["GET"])
def api_get_household(household_id: str):
    """Get household details and balance"""
    result = services.get_household_balance(household_id)
    
    if "error" in result:
        return jsonify(result), 404
    return jsonify(result)


@app.route("/api/households/<household_id>/claim", methods=["POST"])
def api_claim_vouchers(household_id: str):
    """Claim vouchers for a tranche"""
    data = request.get_json()
    if not data or "tranche" not in data:
        return jsonify({"error": "Missing tranche"}), 400
    
    tranche = data["tranche"]
    if tranche not in ["May2025", "Jan2026"]:
        return jsonify({"error": "Invalid tranche. Must be 'May2025' or 'Jan2026'"}), 400
    
    result = services.claim_vouchers(household_id, tranche)
    
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@app.route("/api/merchants", methods=["POST"])
def api_create_merchant():
    """Register a new merchant"""
    data = request.get_json()
    if not data or "merchant_id" not in data or "merchant_name" not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    # Create row data as per CSV format
    row = {
        "Merchant_ID": data["merchant_id"],
        "Merchant_Name": data["merchant_name"],
        "UEN": data.get("uen", ""),
        "Bank_Name": data.get("bank_name", ""),
        "Bank_Code": data.get("bank_code", ""),
        "Branch_Code": data.get("branch_code", ""),
        "Account_Number": data.get("account_number", ""),
        "Account_Holder_Name": data.get("account_holder_name", ""),
        "Registration_Date": data.get("registration_date", datetime.now().strftime("%Y-%m-%d")),
        "Status": data.get("status", "Active")
    }
    
    result = services.register_merchant_from_csv_row(row)
    
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result), 201


@app.route("/api/merchants", methods=["GET"])
def api_list_merchants():
    """Get all registered merchants"""
    merchants = []
    for merchant_id, merchant in store.merchants.items():
        merchants.append({
            "merchant_id": merchant_id,
            "merchant_name": merchant.merchant_name,
            "uen": merchant.uen,
            "bank_name": merchant.bank_name,
            "status": merchant.status,
            "registration_date": merchant.registration_date
        })
    
    return jsonify({
        "success": True,
        "count": len(merchants),
        "merchants": merchants
    })


@app.route("/api/redemptions", methods=["POST"])
def api_redeem():
    """Redeem vouchers"""
    data = request.get_json()
    if not data or "household_id" not in data or "merchant_id" not in data or "amount" not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    result = services.redeem_vouchers(
        household_id=data["household_id"],
        merchant_id=data["merchant_id"],
        amount=float(data["amount"]),
        method=data.get("method", "optimal")
    )
    
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@app.route("/api/analytics", methods=["GET"])
def api_get_analytics():
    """Get system analytics for dashboard"""
    result = services.get_system_analytics()
    return jsonify(result)


@app.route("/api/balances/export", methods=["GET"])
def api_export_balances():
    """Export balance snapshot"""
    date = request.args.get("date", datetime.now().strftime("%Y%m%d"))
    hour = request.args.get("hour", datetime.now().strftime("%H"))
    
    if len(date) != 8 or len(hour) != 2:
        return jsonify({"error": "Invalid date or hour format. Use YYYYMMDD and HH"}), 400
    
    result = services.export_balance_snapshot(date, hour)
    
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@app.route("/api/qr/<transaction_id>", methods=["GET"])
def api_get_qr(transaction_id: str):
    """Get QR code for transaction"""
    if transaction_id not in store.qr_codes:
        return jsonify({"error": "Transaction not found"}), 404
    
    qr_data = store.qr_codes[transaction_id]
    qr_info = services.generate_qr_code(qr_data)
    return jsonify(qr_info)


# -------- Health and System Routes --------

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "memory_usage": {
            "households": len(store.households),
            "merchants": len(store.merchants),
            "transactions": len(store.transactions),
            "vouchers": len(store.voucher_index.voucher_map)
        }
    })


@app.route("/api/system/reset", methods=["POST"])
def system_reset():
    """Reset system (for testing only)"""
    # Clear all data
    store.households.clear()
    store.merchants.clear()
    store.transactions.clear()
    store.voucher_index = services.HouseholdIndex()
    store.qr_codes.clear()
    
    # Remove data files
    for file in ["households.json", "merchants.json", "transactions.json", "vouchers.json"]:
        filepath = os.path.join("data", file)
        if os.path.exists(filepath):
            os.remove(filepath)
    
    # Create sample data
    services.create_sample_data()
    
    return jsonify({
        "success": True,
        "message": "System reset and sample data created"
    })


# -------- Error Handlers --------

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "Resource not found"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": "Internal server error"
    }), 500


if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("data", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    
    # Run the server
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )