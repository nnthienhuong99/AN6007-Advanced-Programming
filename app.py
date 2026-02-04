# app.py - Flask API backend
from flask import Flask, jsonify, request, session
from flask_cors import CORS
import os
import json
from datetime import datetime, date
import random
import calendar
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
CORS(app)  # Allows cross-domain requests for use by Flet applications

# Data class definition

@dataclass
class Voucher:
    voucher_id: str
    denomination: int
    grant_date: str
    expiry_date: str
    tranche_id: str = ""  # T1: May 2025, T2: Jan 2026
    is_redeemed: bool = False
    redemption_date: Optional[str] = None

@dataclass
class Household:
    household_id: str
    name: str = ""
    nric: str = ""
    email: str = ""
    postal_code: str = ""
    unit_number: str = ""
    district: str = ""
    num_people: int = 0
    registered_date: str = ""
    claimed_tranches: List[str] = field(default_factory=list)
    balance_2: int = 0
    balance_5: int = 0
    balance_10: int = 0

@dataclass
class Merchant:
    merchant_id: str
    merchant_name: str
    uen: str
    bank_code: str
    branch_code: str
    account_number: str
    account_holder_name: str
    bank_name: str = ""
    branch_name: str = ""
    registration_date: str = ""
    status: str = "Active"

@dataclass
class Transaction:
    transaction_id: str
    household_id: str
    merchant_id: str
    amount: float
    datetime_iso: str
    voucher_ids: List[str] = field(default_factory=list)
    status: str = "Completed"

# Memory storage

class InMemoryStore:
    def __init__(self):
        self.households: Dict[str, Household] = {}
        self.merchants: Dict[str, Merchant] = {}
        self.transactions: Dict[str, Transaction] = {}
        self.vouchers: Dict[str, Voucher] = {}
        self.household_vouchers: Dict[str, List[str]] = {}  # household_id -> [voucher_ids]
        self.voucher_to_household: Dict[str, str] = {}  # voucher_id -> household_id
        
        # Statistical data
        self.stats = {
            "total_households": 0,
            "total_merchants": 0,
            "total_transactions": 0,
            "total_amount_redeemed": 0.0,
            "vouchers_claimed_2025": 0,
            "vouchers_claimed_2026": 0
        }
        
        # Load sample data
        self._load_sample_data()
    
    def _load_sample_data(self):
        """Load sample data"""
        # Sample household
        h1 = Household(
            household_id="H001",
            name="John Tan",
            nric="S1234567A",
            email="john@example.com",
            postal_code="123456",
            unit_number="10-123",
            district="12",
            num_people=4,
            registered_date="2024-01-01",
            claimed_tranches=["T1"],
            balance_2=50,
            balance_5=20,
            balance_10=30
        )
        self.households["H001"] = h1
        
        # Sample merchant
        m1 = Merchant(
            merchant_id="M001",
            merchant_name="ABC Minimart",
            uen="201234567A",
            bank_code="7171",
            branch_code="001",
            account_number="1234567890",
            account_holder_name="ABC Minimart Pte Ltd",
            bank_name="DBS Bank Ltd",
            branch_name="Main Branch",
            registration_date="2024-01-01"
        )
        self.merchants["M001"] = m1
        
        m2 = Merchant(
            merchant_id="M002",
            merchant_name="XYZ Bakery",
            uen="201234568B",
            bank_code="7171",
            branch_code="001",
            account_number="9876543210",
            account_holder_name="XYZ Bakery LLP",
            bank_name="DBS Bank Ltd",
            branch_name="Main Branch",
            registration_date="2024-01-01"
        )
        self.merchants["M002"] = m2
        
        # Update statistics
        self.stats["total_households"] = len(self.households)
        self.stats["total_merchants"] = len(self.merchants)
    
    def get_household_balance(self, household_id: str) -> Dict[str, int]:
        """Get household balance"""
        if household_id not in self.households:
            return {"2": 0, "5": 0, "10": 0}
        
        h = self.households[household_id]
        return {
            "2": h.balance_2,
            "5": h.balance_5,
            "10": h.balance_10
        }
    
    def add_vouchers(self, household_id: str, tranche_id: str) -> Dict[str, int]:
        """Add vouchers to household"""
        if household_id not in self.households:
            return {"error": "Household not found"}
        
        household = self.households[household_id]
        
        # Check if this batch has already been claimed
        if tranche_id in household.claimed_tranches:
            return {"error": f"Tranche {tranche_id} already claimed"}
        
        # Vouchers are allocated according to batches
        if tranche_id == "T1":  # May 2025
            added_2, added_5, added_10 = 50, 20, 30
        elif tranche_id == "T2":  # Jan 2026
            added_2, added_5, added_10 = 30, 12, 18
        else:
            return {"error": "Invalid tranche ID"}
        
        # Update balance
        household.balance_2 += added_2
        household.balance_5 += added_5
        household.balance_10 += added_10
        household.claimed_tranches.append(tranche_id)
        
        # Update statistics
        if tranche_id == "T1":
            self.stats["vouchers_claimed_2025"] += 1
        elif tranche_id == "T2":
            self.stats["vouchers_claimed_2026"] += 1
        
        return {
            "2": added_2,
            "5": added_5,
            "10": added_10,
            "total_value": added_2 * 2 + added_5 * 5 + added_10 * 10
        }
    
    def redeem_vouchers(self, household_id: str, merchant_id: str, 
                       vouchers_2: int, vouchers_5: int, vouchers_10: int) -> Dict:
        """Redeem vouchers"""
        if household_id not in self.households:
            return {"error": "Household not found"}
        
        if merchant_id not in self.merchants:
            return {"error": "Merchant not found"}
        
        household = self.households[household_id]
        
        # Check if balance is sufficient
        if (household.balance_2 < vouchers_2 or 
            household.balance_5 < vouchers_5 or 
            household.balance_10 < vouchers_10):
            return {"error": "Insufficient voucher balance"}
        
        # Calculate total amount
        total_amount = (vouchers_2 * 2) + (vouchers_5 * 5) + (vouchers_10 * 10)
        
        # Update balance
        household.balance_2 -= vouchers_2
        household.balance_5 -= vouchers_5
        household.balance_10 -= vouchers_10
        
        # Create transaction record
        transaction_id = f"TX{datetime.now().strftime('%Y%m%d%H%M%S')}"
        transaction = Transaction(
            transaction_id=transaction_id,
            household_id=household_id,
            merchant_id=merchant_id,
            amount=total_amount,
            datetime_iso=datetime.now().isoformat(),
            status="Completed"
        )
        
        self.transactions[transaction_id] = transaction
        self.stats["total_transactions"] += 1
        self.stats["total_amount_redeemed"] += total_amount
        
        return {
            "transaction_id": transaction_id,
            "household_id": household_id,
            "merchant_id": merchant_id,
            "amount": total_amount,
            "vouchers_2": vouchers_2,
            "vouchers_5": vouchers_5,
            "vouchers_10": vouchers_10,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_system_stats(self) -> Dict:
        """Get system statistics"""
        return self.stats

store = InMemoryStore()

# API Route

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

# Household-related APIs

@app.route('/api/households', methods=['GET'])
def get_all_households():
    """Get all households"""
    households = []
    for hid, household in store.households.items():
        households.append({
            "household_id": hid,
            "name": household.name,
            "email": household.email,
            "postal_code": household.postal_code,
            "unit_number": household.unit_number,
            "registered_date": household.registered_date,
            "claimed_tranches": household.claimed_tranches,
            "balance": store.get_household_balance(hid)
        })
    
    return jsonify({
        "status": "success",
        "count": len(households),
        "households": households
    })

@app.route('/api/households/<household_id>', methods=['GET'])
def get_household(household_id):
    """Get specific household information"""
    if household_id not in store.households:
        return jsonify({
            "status": "error",
            "message": "Household not found"
        }), 404
    
    household = store.households[household_id]
    balance = store.get_household_balance(household_id)
    total_value = balance["2"] * 2 + balance["5"] * 5 + balance["10"] * 10
    
    return jsonify({
        "status": "success",
        "household": {
            "household_id": household_id,
            "name": household.name,
            "nric": household.nric,
            "email": household.email,
            "postal_code": household.postal_code,
            "unit_number": household.unit_number,
            "district": household.district,
            "num_people": household.num_people,
            "registered_date": household.registered_date,
            "claimed_tranches": household.claimed_tranches,
            "balance": balance,
            "total_value": total_value
        }
    })

@app.route('/api/households/register', methods=['POST'])
def register_household():
    """Register new household"""
    data = request.json
    
    # Validate necessary fields
    required_fields = ["name", "nric", "email", "postal_code", "unit_number"]
    for field in required_fields:
        if field not in data:
            return jsonify({
                "status": "error",
                "message": f"Missing required field: {field}"
            }), 400
    
    # Generate household ID
    household_id = f"H{len(store.households) + 1:03d}"
    
    # Create household object
    household = Household(
        household_id=household_id,
        name=data["name"],
        nric=data["nric"],
        email=data["email"],
        postal_code=data["postal_code"],
        unit_number=data["unit_number"],
        district=data.get("district", ""),
        num_people=int(data.get("num_people", 1)),
        registered_date=datetime.now().strftime("%Y-%m-%d")
    )
    
    # Save to storage
    store.households[household_id] = household
    store.stats["total_households"] += 1
    
    return jsonify({
        "status": "success",
        "message": "Household registered successfully",
        "household_id": household_id,
        "household": {
            "household_id": household_id,
            "name": household.name,
            "email": household.email,
            "registered_date": household.registered_date
        }
    })

@app.route('/api/households/<household_id>/balance', methods=['GET'])
def get_balance(household_id):
    """Get household balance"""
    if household_id not in store.households:
        return jsonify({
            "status": "error",
            "message": "Household not found"
        }), 404
    
    balance = store.get_household_balance(household_id)
    total_value = balance["2"] * 2 + balance["5"] * 5 + balance["10"] * 10
    
    return jsonify({
        "status": "success",
        "household_id": household_id,
        "balance": balance,
        "total_value": total_value
    })

# Vouchers-related API

@app.route('/api/vouchers/claim', methods=['POST'])
def claim_vouchers():
    """voucher collection batches"""
    data = request.json
    
    # Validate necessary fields
    if "household_id" not in data:
        return jsonify({
            "status": "error",
            "message": "Missing household_id"
        }), 400
    
    if "tranche_id" not in data:
        return jsonify({
            "status": "error",
            "message": "Missing tranche_id"
        }), 400
    
    household_id = data["household_id"]
    tranche_id = data["tranche_id"]
    
    result = store.add_vouchers(household_id, tranche_id)
    
    if "error" in result:
        return jsonify({
            "status": "error",
            "message": result["error"]
        }), 400
    
    return jsonify({
        "status": "success",
        "message": f"Vouchers from tranche {tranche_id} claimed successfully",
        "household_id": household_id,
        "tranche_id": tranche_id,
        "vouchers_added": {
            "$2": result["2"],
            "$5": result["5"],
            "$10": result["10"]
        },
        "total_value": result["total_value"]
    })

# Merchant-related API

@app.route('/api/merchants', methods=['GET'])
def get_all_merchants():
    """Get all merchants"""
    merchants = []
    for mid, merchant in store.merchants.items():
        merchants.append({
            "merchant_id": mid,
            "merchant_name": merchant.merchant_name,
            "uen": merchant.uen,
            "bank_name": merchant.bank_name,
            "branch_name": merchant.branch_name,
            "status": merchant.status
        })
    
    return jsonify({
        "status": "success",
        "count": len(merchants),
        "merchants": merchants
    })

@app.route('/api/merchants/register', methods=['POST'])
def register_merchant():
    """Register new merchant"""
    data = request.json
    
    # Validate necessary fields
    required_fields = ["merchant_name", "uen", "bank_code", "branch_code", 
                      "account_number", "account_holder_name"]
    for field in required_fields:
        if field not in data:
            return jsonify({
                "status": "error",
                "message": f"Missing required field: {field}"
            }), 400
    
    # Generate merchant ID
    merchant_id = f"M{len(store.merchants) + 1:03d}"
    
    # Create merchant object
    merchant = Merchant(
        merchant_id=merchant_id,
        merchant_name=data["merchant_name"],
        uen=data["uen"],
        bank_code=data["bank_code"],
        branch_code=data["branch_code"],
        account_number=data["account_number"],
        account_holder_name=data["account_holder_name"],
        bank_name=data.get("bank_name", ""),
        branch_name=data.get("branch_name", ""),
        registration_date=datetime.now().strftime("%Y-%m-%d")
    )
    
    # Save to storage
    store.merchants[merchant_id] = merchant
    store.stats["total_merchants"] += 1
    
    return jsonify({
        "status": "success",
        "message": "Merchant registered successfully",
        "merchant_id": merchant_id,
        "merchant": {
            "merchant_id": merchant_id,
            "merchant_name": merchant.merchant_name,
            "uen": merchant.uen,
            "registration_date": merchant.registration_date
        }
    })

# Transaction-related API

@app.route('/api/transactions', methods=['GET'])
def get_all_transactions():
    """Get all transactions"""
    transactions = []
    for tid, transaction in store.transactions.items():
        transactions.append({
            "transaction_id": tid,
            "household_id": transaction.household_id,
            "merchant_id": transaction.merchant_id,
            "amount": transaction.amount,
            "datetime": transaction.datetime_iso,
            "status": transaction.status
        })
    
    return jsonify({
        "status": "success",
        "count": len(transactions),
        "transactions": transactions
    })

@app.route('/api/transactions/redeem', methods=['POST'])
def redeem_transaction():
    """voucher redemption transactions"""
    data = request.json
    
    # Validate necessary fields
    required_fields = ["household_id", "merchant_id", "vouchers_2", "vouchers_5", "vouchers_10"]
    for field in required_fields:
        if field not in data:
            return jsonify({
                "status": "error",
                "message": f"Missing required field: {field}"
            }), 400
    
    result = store.redeem_vouchers(
        household_id=data["household_id"],
        merchant_id=data["merchant_id"],
        vouchers_2=int(data["vouchers_2"]),
        vouchers_5=int(data["vouchers_5"]),
        vouchers_10=int(data["vouchers_10"])
    )
    
    if "error" in result:
        return jsonify({
            "status": "error",
            "message": result["error"]
        }), 400
    
    return jsonify({
        "status": "success",
        "message": "Vouchers redeemed successfully",
        "transaction": result
    })

# System Statistics API

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    stats = store.get_system_stats()
    
    # Calculate total balance
    total_balance = 0
    for household in store.households.values():
        balance = store.get_household_balance(household.household_id)
        total_balance += balance["2"] * 2 + balance["5"] * 5 + balance["10"] * 10
    
    stats["total_balance"] = total_balance
    stats["timestamp"] = datetime.now().isoformat()
    
    return jsonify({
        "status": "success",
        "stats": stats
    })

# Bank Data API

@app.route('/api/banks', methods=['GET'])
def get_banks():
    """Get bank list"""
    banks = [
        {
            "bank_code": "7171",
            "bank_name": "DBS Bank Ltd",
            "swift_code": "DBSSSGSG",
            "remarks": "FAST/GIRO Enabled"
        },
        {
            "bank_code": "7339",
            "bank_name": "OCBC Bank",
            "swift_code": "OCBCSGSG",
            "remarks": "FAST/GIRO Enabled"
        },
        {
            "bank_code": "7761",
            "bank_name": "UOB Bank",
            "swift_code": "UOVBSGSG",
            "remarks": "FAST/GIRO Enabled"
        },
        {
            "bank_code": "7091",
            "bank_name": "Maybank Singapore",
            "swift_code": "MBBESGSG",
            "remarks": "FAST/GIRO Enabled"
        },
        {
            "bank_code": "7302",
            "bank_name": "Standard Chartered Bank",
            "swift_code": "SCBLSGSG",
            "remarks": "FAST/GIRO Enabled"
        },
        {
            "bank_code": "7375",
            "bank_name": "HSBC Singapore",
            "swift_code": "HSBCSGSG",
            "remarks": "FAST/GIRO Enabled"
        }
    ]
    
    return jsonify({
        "status": "success",
        "banks": banks
    })

@app.route('/api/banks/<bank_code>/branches', methods=['GET'])
def get_branches(bank_code):
    """Get list of branches of specific banks"""
    branches = []
    
    # Return different branches based on bank code
    if bank_code == "7171":  # DBS
        branches = [
            {"branch_code": "001", "branch_name": "Main Branch"},
            {"branch_code": "081", "branch_name": "Toa Payoh Branch"},
            {"branch_code": "101", "branch_name": "Orchard Branch"}
        ]
    elif bank_code == "7339":  # OCBC
        branches = [
            {"branch_code": "501", "branch_name": "Tampines Branch"},
            {"branch_code": "502", "branch_name": "Jurong Branch"}
        ]
    elif bank_code == "7375":  # HSBC
        branches = [
            {"branch_code": "146", "branch_name": "Orchard Branch"},
            {"branch_code": "147", "branch_name": "Raffles Place Branch"}
        ]
    else:
        # Default value returns a single line break
        branches = [
            {"branch_code": "001", "branch_name": "Main Branch"}
        ]
    
    return jsonify({
        "status": "success",
        "bank_code": bank_code,
        "branches": branches
    })

# Administrator functions

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """Administrator Login"""
    data = request.json
    
    if "password" not in data:
        return jsonify({
            "status": "error",
            "message": "Password required"
        }), 400
    
    # Simple password verification
    if data["password"] == "Admin123":
        session['admin_logged_in'] = True
        session['admin_login_time'] = datetime.now().isoformat()
        
        return jsonify({
            "status": "success",
            "message": "Login successful",
            "token": "admin_token_123"  
        })
    else:
        return jsonify({
            "status": "error",
            "message": "Invalid password"
        }), 401

@app.route('/api/admin/dashboard', methods=['GET'])
def admin_dashboard():
    """Administrator Dashboard Data"""
    # Check if administrator is logged in
    if not session.get('admin_logged_in'):
        return jsonify({
            "status": "error",
            "message": "Unauthorized"
        }), 401
    
    stats = store.get_system_stats()
    
    # Add more statistics
    stats["total_balance"] = sum(
        store.get_household_balance(hid)["2"] * 2 + 
        store.get_household_balance(hid)["5"] * 5 + 
        store.get_household_balance(hid)["10"] * 10
        for hid in store.households.keys()
    )
    
    # Get recent transactions
    recent_transactions = []
    for tid, transaction in list(store.transactions.items())[-10:]:
        recent_transactions.append({
            "transaction_id": tid,
            "household_id": transaction.household_id,
            "merchant_id": transaction.merchant_id,
            "amount": transaction.amount,
            "datetime": transaction.datetime_iso
        })
    
    return jsonify({
        "status": "success",
        "dashboard": {
            "stats": stats,
            "recent_transactions": recent_transactions,
            "total_households": len(store.households),
            "total_merchants": len(store.merchants),
            "timestamp": datetime.now().isoformat()
        }
    })

# Homepage

@app.route('/')
def index():
    """API documentation page"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>CDC Vouchers API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            h1 { color: #333; }
            .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-left: 4px solid #007bff; }
            .method { font-weight: bold; color: #007bff; }
            .url { font-family: monospace; }
        </style>
    </head>
    <body>
        <h1>CDC Vouchers API</h1>
        <p>Backend API for CDC Vouchers System</p>
        
        <h2>Available Endpoints:</h2>
        
        <div class="endpoint">
            <span class="method">GET</span> <span class="url">/api/health</span>
            <p>Health check endpoint</p>
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <span class="url">/api/households</span>
            <p>Get all households</p>
        </div>
        
        <div class="endpoint">
            <span class="method">POST</span> <span class="url">/api/households/register</span>
            <p>Register new household</p>
        </div>
        
        <div class="endpoint">
            <span class="method">POST</span> <span class="url">/api/vouchers/claim</span>
            <p>Claim voucher tranche</p>
        </div>
        
        <div class="endpoint">
            <span class="method">POST</span> <span class="url">/api/transactions/redeem</span>
            <p>Redeem vouchers</p>
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <span class="url">/api/stats</span>
            <p>Get system statistics</p>
        </div>
        
        <h2>Frontend:</h2>
        <p>Run the Flet mobile app separately: <code>python mobile_app.py</code></p>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("=" * 60)
    print("CDC Vouchers API Server")
    print("=" * 60)
    print("\nAPI Endpoints available at:")
    print("• http://localhost:5000/")
    print("• http://localhost:5000/api/health")
    print("\nFlet mobile app should connect to this API.")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)