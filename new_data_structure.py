# data_structure.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from datetime import date, datetime
import json
import os


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
    nric_members: Dict[str, str] = field(default_factory=dict)  # NRIC -> Name
    claimed_tranches: Set[str] = field(default_factory=set)
    
    def calculate_district(self) -> str:
        """Calculate district from postal code (first 2 digits)"""
        if len(self.postal_code) >= 2:
            sector = int(self.postal_code[:2])
            # Simplified district mapping (based on project PDF)
            if sector in [1, 2, 3, 4, 5, 6]:
                return "Central"
            elif sector in [7, 8]:
                return "Downtown Core"
            elif sector in [9, 10]:
                return "Queenstown/Tiong Bahru"
            elif sector in [11, 12, 13, 14, 15, 16]:
                return "South"
            elif sector in [17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28]:
                return "North/East/West"
        return "Unknown"


@dataclass
class Merchant:
    """Merchant class with all attributes from the project specification"""
    merchant_id: str
    merchant_name: str
    uen: str
    bank_name: str
    bank_code: str
    branch_code: str
    account_number: str
    account_holder_name: str
    registration_date: str
    status: str = "Active"


@dataclass
class Transaction:
    """Transaction class for voucher redemptions"""
    transaction_id: str
    household_id: str
    merchant_id: str
    transaction_datetime: str  # YYYYMMDDhhmmss format
    voucher_code: str
    denomination_used: float
    amount_redeemed: float
    payment_status: str = "Pending"
    remarks: str = ""


@dataclass
class QRData:
    """Class for QR code generation"""
    transaction_id: str
    household_id: str
    merchant_id: str
    amount: float
    denominations: List[Tuple[int, int]]  # (denomination, count)
    timestamp: str


# -------- Voucher Allocation Classes --------

@dataclass
class VoucherAllocation:
    """Class to define voucher allocation per tranche"""
    tranche_name: str
    total_value: int
    denominations: Dict[int, int]  # denomination -> count
    
    @classmethod
    def get_may2025_allocation(cls) -> 'VoucherAllocation':
        return cls(
            tranche_name="May2025",
            total_value=500,
            denominations={2: 50, 5: 20, 10: 30}  # 50*2 + 20*5 + 30*10 = 500
        )
    
    @classmethod
    def get_jan2026_allocation(cls) -> 'VoucherAllocation':
        return cls(
            tranche_name="Jan2026",
            total_value=300,
            denominations={2: 30, 5: 12, 10: 15}  # 30*2 + 12*5 + 15*10 = 300
        )


# -------- Advanced Data Structures for Performance --------

class HouseholdIndex:
    """Optimized index for quick household balance retrieval"""
    def __init__(self):
        self.household_vouchers: Dict[str, Dict[int, List[Voucher]]] = {}  # household_id -> {denomination -> [vouchers]}
        self.voucher_map: Dict[str, Voucher] = {}  # voucher_id -> Voucher object
        self.household_balances: Dict[str, Dict[int, int]] = {}  # household_id -> {denomination -> count}
    
    def add_voucher(self, household_id: str, voucher: Voucher):
        """Add voucher to index"""
        if household_id not in self.household_vouchers:
            self.household_vouchers[household_id] = {2: [], 5: [], 10: []}
            self.household_balances[household_id] = {2: 0, 5: 0, 10: 0}
        
        denom = voucher.denomination
        self.household_vouchers[household_id][denom].append(voucher)
        self.voucher_map[voucher.voucher_id] = voucher
        self.household_balances[household_id][denom] += 1
    
    def remove_voucher(self, voucher_id: str) -> Optional[Voucher]:
        """Remove voucher from index"""
        if voucher_id not in self.voucher_map:
            return None
        
        voucher = self.voucher_map[voucher_id]
        household_id = self.get_voucher_household(voucher_id)
        
        if household_id and household_id in self.household_vouchers:
            denom = voucher.denomination
            # Remove from list
            vouchers_list = self.household_vouchers[household_id][denom]
            for i, v in enumerate(vouchers_list):
                if v.voucher_id == voucher_id:
                    vouchers_list.pop(i)
                    break
            
            # Update balance
            self.household_balances[household_id][denom] = max(0, self.household_balances[household_id][denom] - 1)
            
        del self.voucher_map[voucher_id]
        return voucher
    
    def get_household_balance(self, household_id: str) -> Dict[int, int]:
        """Get balance for household (optimized O(1) retrieval)"""
        return self.household_balances.get(household_id, {2: 0, 5: 0, 10: 0})
    
    def get_voucher_household(self, voucher_id: str) -> Optional[str]:
        """Find which household owns a voucher"""
        for household_id, denom_dict in self.household_vouchers.items():
            for denom_list in denom_dict.values():
                for v in denom_list:
                    if v.voucher_id == voucher_id:
                        return household_id
        return None
    
    def find_vouchers_for_redemption(self, household_id: str, amount: int) -> List[Voucher]:
        """Find optimal vouchers for redemption (greedy algorithm)"""
        result = []
        remaining = amount
        denominations = [10, 5, 2]  # Try to use larger denominations first
        
        for denom in denominations:
            available = self.household_vouchers.get(household_id, {}).get(denom, [])
            count_needed = min(len(available), remaining // denom)
            
            if count_needed > 0:
                result.extend(available[:count_needed])
                remaining -= count_needed * denom
            
            if remaining == 0:
                break
        
        return result


# -------- Main In-Memory Store with Persistence --------

class InMemoryStore:
    """Main data store with file persistence"""
    def __init__(self):
        self.households: Dict[str, Household] = {}
        self.merchants: Dict[str, Merchant] = {}
        self.transactions: List[Transaction] = []
        self.voucher_index = HouseholdIndex()
        self.qr_codes: Dict[str, QRData] = {}  # transaction_id -> QRData
        
        # File paths for persistence
        self.households_file = "data/households.json"
        self.merchants_file = "data/merchants.json"
        self.transactions_file = "data/transactions.json"
        self.vouchers_file = "data/vouchers.json"
        
        # Create data directory if not exists
        os.makedirs("data", exist_ok=True)
        os.makedirs("output", exist_ok=True)
    
    def save_to_file(self, filename: str, data):
        """Save data to JSON file"""
        with open(filename, 'w') as f:
            if isinstance(data, dict):
                json.dump({k: self._serialize(v) for k, v in data.items()}, f, indent=2)
            elif isinstance(data, list):
                json.dump([self._serialize(item) for item in data], f, indent=2)
    
    def load_from_file(self, filename: str, default):
        """Load data from JSON file"""
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
                return data
        return default
    
    def _serialize(self, obj):
        """Helper method to serialize objects"""
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return obj
    
    def save_all(self):
        """Save all data to files"""
        # Convert objects to dictionaries
        households_dict = {k: v.__dict__ for k, v in self.households.items()}
        merchants_dict = {k: v.__dict__ for k, v in self.merchants.items()}
        transactions_list = [t.__dict__ for t in self.transactions]
        
        # Save vouchers (need special handling for Voucher objects in index)
        vouchers_data = []
        for voucher in self.voucher_index.voucher_map.values():
            vouchers_data.append({
                'voucher_id': voucher.voucher_id,
                'denomination': voucher.denomination,
                'tranche': voucher.tranche,
                'is_redeemed': voucher.is_redeemed,
                'redemption_date': voucher.redemption_date,
                'merchant_id': voucher.merchant_id
            })
        
        self.save_to_file(self.households_file, households_dict)
        self.save_to_file(self.merchants_file, merchants_dict)
        self.save_to_file(self.transactions_file, transactions_list)
        self.save_to_file(self.vouchers_file, vouchers_data)
    
    def load_all(self):
        """Load all data from files"""
        # Load households
        households_data = self.load_from_file(self.households_file, {})
        for hid, data in households_data.items():
            self.households[hid] = Household(**data)
        
        # Load merchants
        merchants_data = self.load_from_file(self.merchants_file, {})
        for mid, data in merchants_data.items():
            self.merchants[mid] = Merchant(**data)
        
        # Load transactions
        transactions_data = self.load_from_file(self.transactions_file, [])
        for data in transactions_data:
            self.transactions.append(Transaction(**data))
        
        # Load vouchers and rebuild index
        vouchers_data = self.load_from_file(self.vouchers_file, [])
        for data in vouchers_data:
            voucher = Voucher(**data)
            # Find household for this voucher
            household_id = self._find_household_for_voucher(voucher.voucher_id)
            if household_id:
                self.voucher_index.add_voucher(household_id, voucher)
    
    def _find_household_for_voucher(self, voucher_id: str) -> Optional[str]:
        """Helper to find household ID for a voucher (simplified - in real app would store mapping)"""
        # This is a simplified version. In production, you would store household_id with each voucher
        for household in self.households.values():
            # Check if household has claimed tranches
            if "May2025" in household.claimed_tranches or "Jan2026" in household.claimed_tranches:
                return household.household_id
        return None


# Global store instance
store = InMemoryStore()