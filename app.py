# app.py - Flask API backend for CDC Vouchers System
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import csv

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
CORS(app)  # Allows cross-domain requests for use by Flet applications

# Flat-file persistence

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_BASE_DIR, "data")
_HOUSEHOLDS_CSV = os.path.join(_DATA_DIR, "households.csv")
_MERCHANTS_CSV = os.path.join(_DATA_DIR, "merchants.csv")
_TRANSACTIONS_CSV = os.path.join(_DATA_DIR, "transactions.csv")

def _norm_unit(unit: str) -> str:
    return (unit or "").strip().upper()

def _norm_uen(uen: str) -> str:
    return (uen or "").strip().upper()

def _ensure_data_dir():
    """Ensure data directory exists"""
    os.makedirs(_DATA_DIR, exist_ok=True)

def _ensure_flat_files():
    """Ensure CSV files exist with proper headers"""
    _ensure_data_dir()
    
    # Households csv
    if not os.path.exists(_HOUSEHOLDS_CSV):
        with open(_HOUSEHOLDS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "household_id",
                "name",
                "nric",
                "email",
                "postal_code",
                "unit_number",
                "district",
                "num_people",
                "registered_date",
                "balance_2",
                "balance_5",
                "balance_10",
                "claimed_tranches"
            ])
    
    # Merchants csv
    if not os.path.exists(_MERCHANTS_CSV):
        with open(_MERCHANTS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "merchant_id",
                "merchant_name",
                "uen",
                "bank_code",
                "branch_code",
                "account_number",
                "account_holder_name",
                "bank_name",
                "branch_name",
                "registration_date",
                "status"
            ])
    
    # Transactions csv (for backup, separate from hourly CSV)
    if not os.path.exists(_TRANSACTIONS_CSV):
        with open(_TRANSACTIONS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "transaction_id",
                "household_id",
                "merchant_id",
                "amount",
                "datetime_iso",
                "vouchers_2",
                "vouchers_5",
                "vouchers_10",
                "status",
                "payment_status"
            ])

def _save_household_to_csv(household):
    """Save or update household in CSV"""
    _ensure_flat_files()
    
    # Read existing households
    households = []
    household_exists = False
    
    if os.path.exists(_HOUSEHOLDS_CSV):
        with open(_HOUSEHOLDS_CSV, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["household_id"] == household.household_id:
                    # Update existing household
                    households.append({
                        "household_id": household.household_id,
                        "name": household.name,
                        "nric": household.nric,
                        "email": household.email,
                        "postal_code": household.postal_code,
                        "unit_number": household.unit_number,
                        "district": household.district,
                        "num_people": household.num_people,
                        "registered_date": household.registered_date,
                        "balance_2": household.balance_2,
                        "balance_5": household.balance_5,
                        "balance_10": household.balance_10,
                        "claimed_tranches": json.dumps(household.claimed_tranches)
                    })
                    household_exists = True
                else:
                    households.append(row)
    
    # Add new household if not exists
    if not household_exists:
        households.append({
            "household_id": household.household_id,
            "name": household.name,
            "nric": household.nric,
            "email": household.email,
            "postal_code": household.postal_code,
            "unit_number": household.unit_number,
            "district": household.district,
            "num_people": household.num_people,
            "registered_date": household.registered_date,
            "balance_2": household.balance_2,
            "balance_5": household.balance_5,
            "balance_10": household.balance_10,
            "claimed_tranches": json.dumps(household.claimed_tranches)
        })
    
    # Write back to csv
    with open(_HOUSEHOLDS_CSV, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "household_id", "name", "nric", "email", "postal_code", "unit_number",
            "district", "num_people", "registered_date", "balance_2", "balance_5",
            "balance_10", "claimed_tranches"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(households)

def _save_merchant_to_csv(merchant):
    """Save or update merchant in CSV"""
    _ensure_flat_files()
    
    # Read existing merchants
    merchants = []
    merchant_exists = False
    
    if os.path.exists(_MERCHANTS_CSV):
        with open(_MERCHANTS_CSV, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["merchant_id"] == merchant.merchant_id:
                    # Update existing merchant
                    merchants.append({
                        "merchant_id": merchant.merchant_id,
                        "merchant_name": merchant.merchant_name,
                        "uen": merchant.uen,
                        "bank_code": merchant.bank_code,
                        "branch_code": merchant.branch_code,
                        "account_number": merchant.account_number,
                        "account_holder_name": merchant.account_holder_name,
                        "bank_name": merchant.bank_name,
                        "branch_name": merchant.branch_name,
                        "registration_date": merchant.registration_date,
                        "status": merchant.status
                    })
                    merchant_exists = True
                else:
                    merchants.append(row)
    
    # Add new merchant if not exists
    if not merchant_exists:
        merchants.append({
            "merchant_id": merchant.merchant_id,
            "merchant_name": merchant.merchant_name,
            "uen": merchant.uen,
            "bank_code": merchant.bank_code,
            "branch_code": merchant.branch_code,
            "account_number": merchant.account_number,
            "account_holder_name": merchant.account_holder_name,
            "bank_name": merchant.bank_name,
            "branch_name": merchant.branch_name,
            "registration_date": merchant.registration_date,
            "status": merchant.status
        })
    
    # Write back to CSV
    with open(_MERCHANTS_CSV, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "merchant_id", "merchant_name", "uen", "bank_code", "branch_code",
            "account_number", "account_holder_name", "bank_name", "branch_name",
            "registration_date", "status"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merchants)

def _save_transaction_to_csv(transaction):
    """Save transaction to CSV"""
    _ensure_flat_files()
    
    with open(_TRANSACTIONS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            transaction.transaction_id,
            transaction.household_id,
            transaction.merchant_id,
            transaction.amount,
            transaction.datetime_iso,
            getattr(transaction, 'vouchers_2', 0),
            getattr(transaction, 'vouchers_5', 0),
            getattr(transaction, 'vouchers_10', 0),
            transaction.status,
            getattr(transaction, 'payment_status', 'Completed')
        ])

def _load_data_from_csv():
    """Load all data from CSV files into memory"""
    _ensure_flat_files()
    
    households = {}
    merchants = {}
    transactions = {}
    total_amount_redeemed = 0.0
    
    # Load households
    if os.path.exists(_HOUSEHOLDS_CSV):
        with open(_HOUSEHOLDS_CSV, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                household = Household(
                    household_id=row["household_id"],
                    name=row["name"],
                    nric=row["nric"],
                    email=row["email"],
                    postal_code=row["postal_code"],
                    unit_number=row["unit_number"],
                    district=row["district"],
                    num_people=int(row["num_people"]),
                    registered_date=row["registered_date"],
                    claimed_tranches=json.loads(row.get("claimed_tranches", "[]")),
                    balance_2=int(row.get("balance_2", 0)),
                    balance_5=int(row.get("balance_5", 0)),
                    balance_10=int(row.get("balance_10", 0))
                )
                households[row["household_id"]] = household
    
    # Load merchants
    if os.path.exists(_MERCHANTS_CSV):
        with open(_MERCHANTS_CSV, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                merchant = Merchant(
                    merchant_id=row["merchant_id"],
                    merchant_name=row["merchant_name"],
                    uen=row["uen"],
                    bank_code=row["bank_code"],
                    branch_code=row["branch_code"],
                    account_number=row["account_number"],
                    account_holder_name=row["account_holder_name"],
                    bank_name=row.get("bank_name", ""),
                    branch_name=row.get("branch_name", ""),
                    registration_date=row["registration_date"],
                    status=row.get("status", "Active")
                )
                merchants[row["merchant_id"]] = merchant
    
    # Load transactions
    if os.path.exists(_TRANSACTIONS_CSV):
        with open(_TRANSACTIONS_CSV, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                transaction = Transaction(
                    transaction_id=row["transaction_id"],
                    household_id=row["household_id"],
                    merchant_id=row["merchant_id"],
                    amount=float(row["amount"]),
                    datetime_iso=row["datetime_iso"],
                    vouchers_2=int(row.get("vouchers_2", 0)),
                    vouchers_5=int(row.get("vouchers_5", 0)),
                    vouchers_10=int(row.get("vouchers_10", 0)),
                    status=row.get("status", "Completed"),
                    payment_status=row.get("payment_status", "Completed")
                )
                transactions[row["transaction_id"]] = transaction
                total_amount_redeemed += float(row["amount"])
    
    return households, merchants, transactions, total_amount_redeemed

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
    voucher_code: str = ""  # Unique voucher code

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
    vouchers_2: int = 0
    vouchers_5: int = 0
    vouchers_10: int = 0
    voucher_details: List[Dict] = field(default_factory=list)  # Store individual voucher details
    status: str = "Completed"
    payment_status: str = "Completed"  # For CSV report

# Memory storage

class InMemoryStore:
    def __init__(self):
        # Load data from CSV files
        self.households, self.merchants, self.transactions, total_amount_redeemed = _load_data_from_csv()
        
        # If no data loaded, use sample data
        if not self.households and not self.merchants:
            self._load_sample_data()
        
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
        
        # Update statistics
        self._update_stats()
        
        # Set total amount redeemed from loaded transactions
        self.stats["total_amount_redeemed"] = total_amount_redeemed
    
    def _update_stats(self):
        """Update statistics"""
        self.stats["total_households"] = len(self.households)
        self.stats["total_merchants"] = len(self.merchants)
        self.stats["total_transactions"] = len(self.transactions)
        
        # Calculate vouchers claimed per tranche
        vouchers_2025 = 0
        vouchers_2026 = 0
        for household in self.households.values():
            for tranche in household.claimed_tranches:
                if tranche == "T1":
                    vouchers_2025 += 1
                elif tranche == "T2":
                    vouchers_2026 += 1
        self.stats["vouchers_claimed_2025"] = vouchers_2025
        self.stats["vouchers_claimed_2026"] = vouchers_2026
    
    def _load_sample_data(self):
        """Load sample data if no csv data exists"""
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
        
        # Save sample data to csv
        _save_household_to_csv(h1)
        _save_merchant_to_csv(m1)
        _save_merchant_to_csv(m2)
    
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
        
        # Save to csv
        _save_household_to_csv(household)
        
        return {
            "2": added_2,
            "5": added_5,
            "10": added_10,
            "total_value": added_2 * 2 + added_5 * 5 + added_10 * 10
        }
    
    def _generate_voucher_codes(self, count: int, denomination: int, transaction_id: str) -> List[str]:
        """Generate unique voucher codes"""
        import uuid
        codes = []
        for i in range(1, count + 1):
            # Generate unique code based on transaction ID, denomination, and sequence
            code = f"{transaction_id[:8]}{denomination:02d}{i:03d}{uuid.uuid4().hex[:4].upper()}"
            codes.append(code)
        return codes
    
    def _append_to_hourly_csv(self, transaction: Transaction, voucher_details: List[Dict]):
        """Append transaction to hourly CSV file - auto generated"""
        # Get transaction datetime
        trans_dt = datetime.fromisoformat(transaction.datetime_iso.replace('Z', '+00:00'))
        
        # Format: RedeemYYYYMMDDHH.csv
        csv_filename = f"Redeem{trans_dt.strftime('%Y%m%d%H')}.csv"
        
        # Check if file exists
        file_exists = os.path.exists(csv_filename)
        
        # Open file in append mode
        with open(csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header if file doesn't exist
            if not file_exists:
                writer.writerow([
                    "Transaction_ID",
                    "Household_ID",
                    "Merchant_ID",
                    "Transaction_Date_Time",
                    "Voucher_Code",
                    "Denomination_Used",
                    "Amount_Redeemed",
                    "Payment_Status",
                    "Remarks"
                ])
            
            # Write each voucher as a separate row
            total_vouchers = len(voucher_details)
            for i, voucher in enumerate(voucher_details, 1):
                # Determine remarks
                if i == total_vouchers:
                    remarks = "Final denomination used"
                else:
                    remarks = str(i)
                
                # Format transaction datetime as YYYYMMDDhhmmss
                trans_datetime_str = trans_dt.strftime('%Y%m%d%H%M%S')
                
                writer.writerow([
                    transaction.transaction_id,
                    transaction.household_id,
                    transaction.merchant_id,
                    trans_datetime_str,
                    voucher['voucher_code'],
                    voucher['denomination'],
                    voucher['denomination'],  # Individual voucher amount
                    transaction.payment_status,
                    remarks
                ])
        
        print(f"✓ Transaction recorded in CSV: {csv_filename}")
    
    def redeem_vouchers(self, household_id: str, merchant_id: str, 
                       vouchers_2: int, vouchers_5: int, vouchers_10: int) -> Dict:
        """Redeem vouchers - auto generated"""
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
        
        # Generate voucher details
        voucher_details = []
        
        # Generate voucher codes for $2 vouchers
        voucher_2_codes = self._generate_voucher_codes(vouchers_2, 2, transaction_id)
        for code in voucher_2_codes:
            voucher_details.append({
                "voucher_code": code,
                "denomination": 2
            })
        
        # Generate voucher codes for $5 vouchers
        voucher_5_codes = self._generate_voucher_codes(vouchers_5, 5, transaction_id)
        for code in voucher_5_codes:
            voucher_details.append({
                "voucher_code": code,
                "denomination": 5
            })
        
        # Generate voucher codes for $10 vouchers
        voucher_10_codes = self._generate_voucher_codes(vouchers_10, 10, transaction_id)
        for code in voucher_10_codes:
            voucher_details.append({
                "voucher_code": code,
                "denomination": 10
            })
        
        # Create transaction
        transaction = Transaction(
            transaction_id=transaction_id,
            household_id=household_id,
            merchant_id=merchant_id,
            amount=total_amount,
            datetime_iso=datetime.now().isoformat(),
            vouchers_2=vouchers_2,
            vouchers_5=vouchers_5,
            vouchers_10=vouchers_10,
            voucher_details=voucher_details,
            status="Completed",
            payment_status="Completed"
        )
        
        # Add to memory
        self.transactions[transaction_id] = transaction
        
        # Update household in CSV
        _save_household_to_csv(household)
        
        # Save transaction to backup CSV
        _save_transaction_to_csv(transaction)
        
        # Update statistics
        self.stats["total_transactions"] = len(self.transactions)
        self.stats["total_amount_redeemed"] += total_amount
        
        # Append to hourly CSV file - auto generated
        self._append_to_hourly_csv(transaction, voucher_details)
        
        return {
            "transaction_id": transaction_id,
            "household_id": household_id,
            "merchant_id": merchant_id,
            "amount": total_amount,
            "vouchers_2": vouchers_2,
            "vouchers_5": vouchers_5,
            "vouchers_10": vouchers_10,
            "voucher_details": voucher_details,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_system_stats(self) -> Dict:
        """Get system statistics"""
        return self.stats

store = InMemoryStore()

# API Route

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
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
    
    # Save to csv
    _save_household_to_csv(household)
    
    # Update statistics
    store.stats["total_households"] = len(store.households)
    
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
    """Claim voucher batches"""
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
    
    # Save to csv
    _save_merchant_to_csv(merchant)
    
    # Update statistics
    store.stats["total_merchants"] = len(store.merchants)
    
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
            "status": transaction.status,
            "vouchers_2": transaction.vouchers_2,
            "vouchers_5": transaction.vouchers_5,
            "vouchers_10": transaction.vouchers_10
        })
    
    return jsonify({
        "status": "success",
        "count": len(transactions),
        "transactions": transactions
    })

@app.route('/api/transactions/redeem', methods=['POST'])
def redeem_transaction():
    """Redeem vouchers - auto generated"""
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

# Bank data API

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
            .info-box { background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <h1>CDC Vouchers API</h1>
        <p>Backend API for CDC Vouchers System</p>
        
        <div class="info-box">
            <h3>📊 Automatic CSV Generation</h3>
            <p>Every transaction automatically generates CSV records in <code>RedeemYYYYMMDDHH.csv</code> files.</p>
            <p>Example: <code>Redeem2026020418.csv</code> contains all transactions on Feb 4, 2026, hour 18 (6 PM).</p>
        </div>
        
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
            <p>Redeem vouchers (automatically generates CSV)</p>
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <span class="url">/api/stats</span>
            <p>Get system statistics</p>
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <span class="url">/api/merchants</span>
            <p>Get all merchants</p>
        </div>
        
        <div class="endpoint">
            <span class="method">POST</span> <span class="url">/api/merchants/register</span>
            <p>Register new merchant</p>
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <span class="url">/api/banks</span>
            <p>Get bank list for merchant registration</p>
        </div>
        
        <h2>Data Persistence:</h2>
        <ul>
            <li>Household data: <code>data/households.csv</code></li>
            <li>Merchant data: <code>data/merchants.csv</code></li>
            <li>Transaction backup: <code>data/transactions.csv</code></li>
            <li>Hourly transaction CSV: <code>RedeemYYYYMMDDHH.csv</code> (automatically generated)</li>
        </ul>
        
        <h2>Frontend:</h2>
        <p>Run the Flet mobile app separately: <code>python mobile_app.py</code></p>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("=" * 60)
    print("CDC Vouchers API Server")
    print("=" * 60)
    print("\n📊 Automatic CSV Generation:")
    print("• Every transaction automatically generates CSV records")
    print("• Files named: RedeemYYYYMMDDHH.csv")
    print("• Example: Redeem2026020418.csv for transactions on Feb 4, 2026, 6 PM")
    print("\nAPI Endpoints available at:")
    print("• http://localhost:5000/")
    print("• http://localhost:5000/api/health")
    print("\nFlet mobile app should connect to this API.")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)