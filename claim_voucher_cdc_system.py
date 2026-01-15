"""
CDC Voucher Management System
Contains: Business logic + Web routes + HTML template + Startup code
"""

# ============ PART 1: Import Libraries ============
from flask import Flask, request, jsonify, render_template_string
import json
import os
from datetime import datetime

# ============ PART 2: Flask App Initialization ============
app = Flask(__name__)

# ============ PART 3: Core Business Logic ============
class VoucherClaimService:
    """Voucher Claim Service - Business Logic"""
    
    # Voucher batch configuration
    VOUCHER_CONFIG = {
        "May2025": {
            "total_value": 500,
            "distribution": {"2": 50, "5": 20, "10": 30}
        },
        "Jan2026": {
            "total_value": 300,
            "distribution": {"2": 30, "5": 12, "10": 15}
        }
    }
    
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.households_file = os.path.join(data_dir, "households.json")
        self.transactions_file = os.path.join(data_dir, "voucher_transactions.json")
        self._initialize_files()
    
    def _initialize_files(self):
        """Initialize data files"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        if not os.path.exists(self.households_file):
            initial_data = {"households": {}}
            with open(self.households_file, 'w') as f:
                json.dump(initial_data, f, indent=2)
        
        if not os.path.exists(self.transactions_file):
            initial_transactions = {"claims": []}
            with open(self.transactions_file, 'w') as f:
                json.dump(initial_transactions, f, indent=2)
    
    def create_test_household(self, household_id):
        """Create a test household (for demo purposes)"""
        data = self.load_households()
        
        if household_id not in data["households"]:
            data["households"][household_id] = {
                "address": "Test Address, Singapore",
                "members": ["Test User"],
                "vouchers": {
                    "May2025": {
                        "claimed": False,
                        "details": {"2": 0, "5": 0, "10": 0}
                    },
                    "Jan2026": {
                        "claimed": False,
                        "details": {"2": 0, "5": 0, "10": 0}
                    }
                },
                "total_balance": 0
            }
            self.save_households(data)
            print(f"✅ Created test household {household_id}")
            return True
        return False
    
    def load_households(self):
        """Load household data"""
        with open(self.households_file, 'r') as f:
            return json.load(f)
    
    def save_households(self, data):
        """Save household data"""
        with open(self.households_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def claim_vouchers(self, household_id, tranche):
        """Claim vouchers for a household"""
        # Check if tranche is valid
        if tranche not in self.VOUCHER_CONFIG:
            return False, f"Invalid tranche: {tranche}", None
        
        # Load household data
        data = self.load_households()
        
        # Check if household exists
        if household_id not in data["households"]:
            return False, "Household does not exist", None
        
        household = data["households"][household_id]
        
        # Check if already claimed
        if household["vouchers"][tranche]["claimed"]:
            return False, f"You have already claimed the {tranche} batch vouchers", None
        
        # Distribute vouchers
        distribution = self.VOUCHER_CONFIG[tranche]["distribution"]
        
        for denomination, quantity in distribution.items():
            household["vouchers"][tranche]["details"][denomination] += quantity
        
        # Mark as claimed
        household["vouchers"][tranche]["claimed"] = True
        
        # Update total balance
        self._update_total_balance(household)
        
        # Save data
        data["households"][household_id] = household
        self.save_households(data)
        
        # Prepare success message
        voucher_details = self.VOUCHER_CONFIG[tranche]["distribution"]
        total_value = self.VOUCHER_CONFIG[tranche]["total_value"]
        message = f"""
        Successfully claimed {tranche} batch vouchers!
        
        Claim Details:
        - $2 vouchers: {voucher_details['2']} pieces
        - $5 vouchers: {voucher_details['5']} pieces
        - $10 vouchers: {voucher_details['10']} pieces
        - Total value: ${total_value}
        
        Current total balance: ${household['total_balance']}
        """
        
        return True, message, household['total_balance']
    
    def _update_total_balance(self, household):
        """Update household's total balance"""
        total = 0
        for tranche in ["May2025", "Jan2026"]:
            details = household["vouchers"][tranche]["details"]
            total += (details["2"] * 2 + details["5"] * 5 + details["10"] * 10)
        household["total_balance"] = total
    
    def get_voucher_status(self, household_id):
        """Get voucher status for a household"""
        data = self.load_households()
        
        if household_id not in data["households"]:
            return None
        
        household = data["households"][household_id]
        
        status = {
            "household_id": household_id,
            "total_balance": household["total_balance"],
            "vouchers": {}
        }
        
        for tranche in ["May2025", "Jan2026"]:
            status["vouchers"][tranche] = {
                "claimed": household["vouchers"][tranche]["claimed"],
                "details": household["vouchers"][tranche]["details"].copy(),
                "total_value": (
                    household["vouchers"][tranche]["details"]["2"] * 2 +
                    household["vouchers"][tranche]["details"]["5"] * 5 +
                    household["vouchers"][tranche]["details"]["10"] * 10
                )
            }
        
        return status

# ============ PART 4: Create Service Instance ============
service = VoucherClaimService()

# ============ PART 5: Web Routes ============

@app.route('/')
def home():
    """Home page"""
    return '''
    <h1>🏠 CDC Voucher Management System</h1>
    <p>Welcome to the CDC Voucher Claim System</p>
    <hr>
    <h3>Test Links:</h3>
    <ul>
        <li><a href="/dashboard/H001">📱 View vouchers for Household H001</a></li>
        <li><a href="/dashboard/H002">📱 View vouchers for Household H002</a></li>
        <li><a href="/api/status/H001">📊 API: Check status for H001</a></li>
    </ul>
    <p><strong>Tip:</strong> If a household doesn't exist, the system will create a test household automatically.</p>
    '''

@app.route('/dashboard/<household_id>')
def voucher_dashboard(household_id):
    """Voucher management dashboard"""
    # Create test household if it doesn't exist
    service.create_test_household(household_id)
    
    # Get status
    status = service.get_voucher_status(household_id)
    
    if status is None:
        return "Household not found", 404
    
    # Return HTML page
    return render_template_string(HTML_TEMPLATE_EN, 
                                household_id=household_id,
                                status=status)

@app.route('/api/claim', methods=['POST'])
def api_claim_vouchers():
    """API endpoint: Claim vouchers"""
    try:
        data = request.json
        household_id = data.get('household_id')
        tranche = data.get('tranche')
        
        if not household_id or not tranche:
            return jsonify({
                "success": False,
                "message": "Missing required parameters: household_id and tranche"
            }), 400
        
        success, message, new_balance = service.claim_vouchers(household_id, tranche)
        
        if success:
            return jsonify({
                "success": True,
                "message": message,
                "new_balance": new_balance
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": message
            }), 400
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"System error: {str(e)}"
        }), 500

@app.route('/api/status/<household_id>', methods=['GET'])
def api_voucher_status(household_id):
    """API endpoint: Get voucher status"""
    try:
        status = service.get_voucher_status(household_id)
        
        if status is None:
            return jsonify({
                "success": False,
                "message": "Household not found"
            }), 404
        
        return jsonify({
            "success": True,
            "status": status
        }), 200
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"System error: {str(e)}"
        }), 500

# ============ PART 6: HTML Template (as string) ============
HTML_TEMPLATE_EN = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CDC Voucher Claim System</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f5f5f5; }
        .container { background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; }
        .balance-box { background-color: #3498db; color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 30px; }
        .balance-amount { font-size: 36px; font-weight: bold; }
        .voucher-section { margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
        .claimed { background-color: #d4edda; border-color: #c3e6cb; }
        .not-claimed { background-color: #fff3cd; border-color: #ffeaa7; }
        .voucher-details { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 15px; }
        .voucher-card { text-align: center; padding: 15px; background-color: #f8f9fa; border-radius: 5px; }
        .denomination { font-size: 24px; color: #27ae60; font-weight: bold; }
        .btn { display: block; width: 100%; padding: 12px; background-color: #2ecc71; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; margin-top: 10px; }
        .btn:hover { background-color: #27ae60; }
        .btn:disabled { background-color: #95a5a6; cursor: not-allowed; }
        .message { padding: 10px; border-radius: 5px; margin-top: 20px; display: none; }
        .success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    </style>
</head>
<body>
    <div class="container">
        <h1>CDC Voucher Management System</h1>
        
        <div class="balance-box">
            <h2>Current Total Balance</h2>
            <div class="balance-amount">${{ status.total_balance }}</div>
            <p>Household ID: {{ household_id }}</p>
        </div>
        
        <!-- May 2025 Batch -->
        <div class="voucher-section {% if status.vouchers.May2025.claimed %}claimed{% else %}not-claimed{% endif %}">
            <h2>May 2025 Batch Vouchers</h2>
            <p><strong>Total value: $500</strong></p>
            
            <div class="voucher-details">
                <div class="voucher-card">
                    <div class="denomination">$2</div>
                    <div>{{ status.vouchers.May2025.details.2 }} pieces</div>
                    <div>Total ${{ status.vouchers.May2025.details.2 * 2 }}</div>
                </div>
                <div class="voucher-card">
                    <div class="denomination">$5</div>
                    <div>{{ status.vouchers.May2025.details.5 }} pieces</div>
                    <div>Total ${{ status.vouchers.May2025.details.5 * 5 }}</div>
                </div>
                <div class="voucher-card">
                    <div class="denomination">$10</div>
                    <div>{{ status.vouchers.May2025.details.10 }} pieces</div>
                    <div>Total ${{ status.vouchers.May2025.details.10 * 10 }}</div>
                </div>
            </div>
            
            {% if not status.vouchers.May2025.claimed %}
            <button class="btn" onclick="claimVoucher('May2025')">
                Claim This Batch Vouchers
            </button>
            {% else %}
            <button class="btn" disabled>
                Already Claimed ✓
            </button>
            {% endif %}
        </div>
        
        <!-- January 2026 Batch -->
        <div class="voucher-section {% if status.vouchers.Jan2026.claimed %}claimed{% else %}not-claimed{% endif %}">
            <h2>January 2026 Batch Vouchers</h2>
            <p><strong>Total value: $300</strong></p>
            
            <div class="voucher-details">
                <div class="voucher-card">
                    <div class="denomination">$2</div>
                    <div>{{ status.vouchers.Jan2026.details.2 }} pieces</div>
                    <div>Total ${{ status.vouchers.Jan2026.details.2 * 2 }}</div>
                </div>
                <div class="voucher-card">
                    <div class="denomination">$5</div>
                    <div>{{ status.vouchers.Jan2026.details.5 }} pieces</div>
                    <div>Total ${{ status.vouchers.Jan2026.details.5 * 5 }}</div>
                </div>
                <div class="voucher-card">
                    <div class="denomination">$10</div>
                    <div>{{ status.vouchers.Jan2026.details.10 }} pieces</div>
                    <div>Total ${{ status.vouchers.Jan2026.details.10 * 10 }}</div>
                </div>
            </div>
            
            {% if not status.vouchers.Jan2026.claimed %}
            <button class="btn" onclick="claimVoucher('Jan2026')">
                Claim This Batch Vouchers
            </button>
            {% else %}
            <button class="btn" disabled>
                Already Claimed ✓
            </button>
            {% endif %}
        </div>
        
        <!-- Message Display Area -->
        <div id="messageBox" class="message"></div>
    </div>
    
    <script>
        function claimVoucher(tranche) {
            const householdId = "{{ household_id }}";
            const messageBox = document.getElementById('messageBox');
            
            // Show loading state
            const button = event.target;
            const originalText = button.textContent;
            button.textContent = 'Processing...';
            button.disabled = true;
            
            // Send API request
            fetch('/api/claim', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    household_id: householdId,
                    tranche: tranche
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show success message
                    messageBox.className = 'message success';
                    messageBox.innerHTML = `
                        <h3>✓ Claim Successful!</h3>
                        <p>${data.message.replace(/\n/g, '<br>')}</p>
                    `;
                    messageBox.style.display = 'block';
                    
                    // Refresh page after 3 seconds
                    setTimeout(() => {
                        window.location.reload();
                    }, 3000);
                } else {
                    // Show error message
                    messageBox.className = 'message error';
                    messageBox.innerHTML = `
                        <h3>✗ Claim Failed</h3>
                        <p>${data.message}</p>
                    `;
                    messageBox.style.display = 'block';
                    
                    // Restore button state
                    button.textContent = originalText;
                    button.disabled = false;
                }
            })
            .catch(error => {
                // Show error message
                messageBox.className = 'message error';
                messageBox.innerHTML = `
                    <h3>✗ Network Error</h3>
                    <p>Please check your connection and try again</p>
                `;
                messageBox.style.display = 'block';
                
                // Restore button state
                button.textContent = originalText;
                button.disabled = false;
            });
        }
        
        // Auto-hide message box
        setTimeout(() => {
            const messageBox = document.getElementById('messageBox');
            if (messageBox.style.display === 'block') {
                messageBox.style.display = 'none';
            }
        }, 5000);
    </script>
</body>
</html>
'''

# ============ PART 7: Startup Code ============
if __name__ == '__main__':
    print("🎯 CDC Voucher Management System Starting...")
    print("📁 Data files will be stored in: data/ folder")
    print("🌐 Please visit: http://localhost:5000")
    print("🔧 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Create some test households
    service.create_test_household("H001")
    service.create_test_household("H002")
    
    # Start Flask server

    app.run(debug=True, port=5000)
