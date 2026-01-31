# data_structure.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json
import os
import random
import string
from datetime import datetime


# -------- Domain Classes --------

@dataclass
class Voucher:
    """Voucher class representing individual vouchers"""
    voucher_id: str
    denomination: int
    tranche: str  # "May2025" or "Jan2026"
    is_redeemed: bool = False
    redemption_date: Optional[str] = None
    merchant_id: Optional[str] = None


@dataclass
class Household:
    """Household class with all required attributes"""
    household_id: str
    postal_code: str
    registered_date: str
    num_people: int
    district: Optional[str] = None
    nric_members: Dict[str, str] = field(default_factory=dict)
    claimed_tranches: List[str] = field(default_factory=list)


@dataclass
class Merchant:
    """Merchant class"""
    merchant_id: str
    merchant_name: str
    uen: str = ""
    bank_name: str = ""
    bank_code: str = ""
    branch_code: str = ""
    account_number: str = ""
    account_holder_name: str = ""
    registration_date: str = ""
    status: str = "Active"


@dataclass
class Transaction:
    """Transaction class for voucher redemptions"""
    transaction_id: str
    household_id: str
    merchant_id: str
    transaction_datetime: str
    voucher_code: str
    denomination_used: float
    amount_redeemed: float
    payment_status: str = "Pending"
    remarks: str = ""


# -------- Helper Functions --------

def generate_random_string(length: int = 20) -> str:
    """Generate random alphanumeric string"""
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for _ in range(length))


def object_to_dict(obj):
    """Convert object to dictionary"""
    if hasattr(obj, '__dict__'):
        result = {}
        for key, value in obj.__dict__.items():
            result[key] = object_to_dict(value)
        return result
    elif isinstance(obj, list):
        return [object_to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: object_to_dict(v) for k, v in obj.items()}
    else:
        return obj


# -------- In-Memory Store --------

class InMemoryStore:
    """Main data store with file persistence"""
    def __init__(self):
        self.households: Dict[str, Household] = {}
        self.merchants: Dict[str, Merchant] = {}
        self.transactions: List[Transaction] = []
        
        # Voucher management
        self.vouchers_by_household: Dict[str, List[Voucher]] = {}
        self.voucher_map: Dict[str, Voucher] = {}
        
        # File paths
        self.data_dir = "data"
        self.households_file = f"{self.data_dir}/households.json"
        self.merchants_file = f"{self.data_dir}/merchants.json"
        self.transactions_file = f"{self.data_dir}/transactions.json"
        self.vouchers_file = f"{self.data_dir}/vouchers.json"
        
        # Create directories
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs("output", exist_ok=True)
    
    def save_to_file(self, filename: str, data):
        """Save data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_from_file(self, filename: str, default):
        """Load data from JSON file"""
        if not os.path.exists(filename):
            return default
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:  # null file
                    return default
                return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"Warning: JSON file {filename} format error: {e}")
            print("Default data will be used...")
            # Backup corrupted files
            backup_file = filename + ".backup"
            if not os.path.exists(backup_file):
                os.rename(filename, backup_file)
                print(f"Corrupt files have been backed up to: {backup_file}")
            return default
    
    def save_all(self):
        """Save all data to files"""
        print("Saving data...")
        
        # Convert objects to simple dictionaries
        households_dict = {}
        for household_id, household in self.households.items():
            households_dict[household_id] = {
                'household_id': household.household_id,
                'postal_code': household.postal_code,
                'registered_date': household.registered_date,
                'num_people': household.num_people,
                'district': household.district,
                'nric_members': household.nric_members,
                'claimed_tranches': household.claimed_tranches
            }
        
        merchants_dict = {}
        for merchant_id, merchant in self.merchants.items():
            merchants_dict[merchant_id] = {
                'merchant_id': merchant.merchant_id,
                'merchant_name': merchant.merchant_name,
                'uen': merchant.uen,
                'bank_name': merchant.bank_name,
                'bank_code': merchant.bank_code,
                'branch_code': merchant.branch_code,
                'account_number': merchant.account_number,
                'account_holder_name': merchant.account_holder_name,
                'registration_date': merchant.registration_date,
                'status': merchant.status
            }
        
        transactions_list = []
        for transaction in self.transactions:
            transactions_list.append({
                'transaction_id': transaction.transaction_id,
                'household_id': transaction.household_id,
                'merchant_id': transaction.merchant_id,
                'transaction_datetime': transaction.transaction_datetime,
                'voucher_code': transaction.voucher_code,
                'denomination_used': transaction.denomination_used,
                'amount_redeemed': transaction.amount_redeemed,
                'payment_status': transaction.payment_status,
                'remarks': transaction.remarks
            })
        
        # Save vouchers
        vouchers_list = []
        for household_id, vouchers in self.vouchers_by_household.items():
            for voucher in vouchers:
                vouchers_list.append({
                    'voucher_id': voucher.voucher_id,
                    'denomination': voucher.denomination,
                    'tranche': voucher.tranche,
                    'is_redeemed': voucher.is_redeemed,
                    'redemption_date': voucher.redemption_date,
                    'merchant_id': voucher.merchant_id,
                    'household_id': household_id  # Add household ID association
                })
        
        # Save to files
        self.save_to_file(self.households_file, households_dict)
        self.save_to_file(self.merchants_file, merchants_dict)
        self.save_to_file(self.transactions_file, transactions_list)
        self.save_to_file(self.vouchers_file, vouchers_list)
        
        print(f"Data saving completed: {len(self.households)} household, {len(self.merchants)} merchant")
    
    def load_all(self):
        """Load all data from files"""
        print("Loading data...")
        
        # Load households
        households_data = self.load_from_file(self.households_file, {})
        for hid, data in households_data.items():
            try:
                self.households[hid] = Household(
                    household_id=data.get('household_id', hid),
                    postal_code=data.get('postal_code', ''),
                    registered_date=data.get('registered_date', ''),
                    num_people=data.get('num_people', 1),
                    district=data.get('district', ''),
                    nric_members=data.get('nric_members', {}),
                    claimed_tranches=data.get('claimed_tranches', [])
                )
            except Exception as e:
                print(f"Warning: Loading household {hid} issue: {e}")
        
        # Load merchants
        merchants_data = self.load_from_file(self.merchants_file, {})
        for mid, data in merchants_data.items():
            try:
                self.merchants[mid] = Merchant(
                    merchant_id=data.get('merchant_id', mid),
                    merchant_name=data.get('merchant_name', ''),
                    uen=data.get('uen', ''),
                    bank_name=data.get('bank_name', ''),
                    bank_code=data.get('bank_code', ''),
                    branch_code=data.get('branch_code', ''),
                    account_number=data.get('account_number', ''),
                    account_holder_name=data.get('account_holder_name', ''),
                    registration_date=data.get('registration_date', ''),
                    status=data.get('status', 'Active')
                )
            except Exception as e:
                print(f"Warning: Loading marchant {mid} issue: {e}")
        
        # Load transactions
        transactions_data = self.load_from_file(self.transactions_file, [])
        for data in transactions_data:
            try:
                self.transactions.append(Transaction(
                    transaction_id=data.get('transaction_id', ''),
                    household_id=data.get('household_id', ''),
                    merchant_id=data.get('merchant_id', ''),
                    transaction_datetime=data.get('transaction_datetime', ''),
                    voucher_code=data.get('voucher_code', ''),
                    denomination_used=data.get('denomination_used', 0.0),
                    amount_redeemed=data.get('amount_redeemed', 0.0),
                    payment_status=data.get('payment_status', 'Pending'),
                    remarks=data.get('remarks', '')
                ))
            except Exception as e:
                print(f"Warning: Loading transaction issue: {e}")
        
        # Load vouchers
        vouchers_data = self.load_from_file(self.vouchers_file, [])
        for data in vouchers_data:
            try:
                voucher = Voucher(
                    voucher_id=data.get('voucher_id', ''),
                    denomination=data.get('denomination', 0),
                    tranche=data.get('tranche', ''),
                    is_redeemed=data.get('is_redeemed', False),
                    redemption_date=data.get('redemption_date'),
                    merchant_id=data.get('merchant_id')
                )
                
                household_id = data.get('household_id')
                if household_id:
                    if household_id not in self.vouchers_by_household:
                        self.vouchers_by_household[household_id] = []
                    self.vouchers_by_household[household_id].append(voucher)
                    self.voucher_map[voucher.voucher_id] = voucher
            except Exception as e:
                print(f"Warning: Loading voucher issue: {e}")
        
        print(f"Data loading completed: {len(self.households)} household, {len(self.merchants)} merchant")
    
    def get_household_balance(self, household_id: str) -> Dict[int, int]:
        """Get voucher balance for household"""
        balance = {2: 0, 5: 0, 10: 0}
        
        if household_id in self.vouchers_by_household:
            for voucher in self.vouchers_by_household[household_id]:
                if not voucher.is_redeemed:
                    denom = voucher.denomination
                    balance[denom] = balance.get(denom, 0) + 1
        
        return balance


# Global store instance
store = InMemoryStore()