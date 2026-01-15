import json
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

@dataclass
class Voucher:
    """Voucher class - represents a single voucher"""
    voucher_code: str
    denomination: float  # Denomination: 2.0, 5.0, 10.0
    tranche: str        # Batch: "2025-05" or "2026-01"
    status: str = "active"  # active, used, expired
    household_id: Optional[str] = None
    redemption_date: Optional[str] = None
    
    def use_voucher(self, redemption_date: str):
        """Mark voucher as used"""
        self.status = "used"
        self.redemption_date = redemption_date

@dataclass
class Household:
    """Household account class - core business entity"""
    household_id: str
    family_members: List[str]
    postal_code: str
    registration_date: str
    vouchers: Dict[str, List[Voucher]]  # Store vouchers by batch
    
    def get_balance(self) -> Dict[float, int]:
        """Get current balance (categorized by denomination)"""
        balance = {2.0: 0, 5.0: 0, 10.0: 0}
        for tranche_vouchers in self.vouchers.values():
            for voucher in tranche_vouchers:
                if voucher.status == "active":
                    balance[voucher.denomination] += 1
        return balance
    
    def get_total_balance(self) -> float:
        """Get total balance"""
        balance = self.get_balance()
        return sum(denom * count for denom, count in balance.items())
    
    def claim_vouchers(self, tranche: str, denominations: Dict[float, int]):
        """Claim vouchers for specified batch"""
        if tranche not in self.vouchers:
            self.vouchers[tranche] = []
        
        for denomination, count in denominations.items():
            for i in range(count):
                voucher_code = f"V{self.household_id[-6:]}{tranche.replace('-','')}{int(denomination)}{i:03d}"
                voucher = Voucher(
                    voucher_code=voucher_code,
                    denomination=denomination,
                    tranche=tranche,
                    household_id=self.household_id
                )
                self.vouchers[tranche].append(voucher)

@dataclass
class Merchant:
    """Merchant account class"""
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
class RedemptionTransaction:
    """Voucher redemption transaction class"""
    transaction_id: str
    household_id: str
    merchant_id: str
    transaction_datetime: str
    vouchers_used: List[Voucher]
    total_amount: float
    payment_status: str = "Pending"
    
    def get_remarks(self) -> str:
        """Generate transaction remarks (as per document requirements)"""
        if len(self.vouchers_used) == 1:
            return "Final denomination used"
        else:
            remarks = []
            for i, voucher in enumerate(self.vouchers_used, 1):
                if i == len(self.vouchers_used):
                    remarks.append(f"{i},Final denomination used")
                else:
                    remarks.append(str(i))
            return ",".join(remarks)

class CDCSystem:
    """CDC system main class - manages all business logic and in-memory data structures"""
    
    def __init__(self):
        # In-memory data structures - support fast queries
        self.households: Dict[str, Household] = {}  # Household ID -> Household object
        self.merchants: Dict[str, Merchant] = {}    # Merchant ID -> Merchant object
        self.transactions: Dict[str, RedemptionTransaction] = {}  # Transaction ID -> Transaction object
        
        # Fast query index
        self.household_balance_index: Dict[str, float] = {}  # Household ID -> total balance (O(1) query)
        
        # Voucher batch configuration (as per document table)
        self.tranche_config = {
            "2025-05": {2.0: 50, 5.0: 20, 10.0: 30},  # 500 SGD
            "2026-01": {2.0: 30, 5.0: 12, 10.0: 15}   # 300 SGD
        }
    
    def register_household(self, household_id: str, family_members: List[str], postal_code: str) -> Household:
        """Register household account"""
        household = Household(
            household_id=household_id,
            family_members=family_members,
            postal_code=postal_code,
            registration_date=datetime.now().strftime("%Y-%m-%d"),
            vouchers={}
        )
        self.households[household_id] = household
        self.household_balance_index[household_id] = 0.0
        return household
    
    def register_merchant(self, merchant_data: Dict) -> Merchant:
        """Register merchant account"""
        merchant = Merchant(**merchant_data)
        self.merchants[merchant.merchant_id] = merchant
        return merchant
    
    def claim_vouchers(self, household_id: str, tranche: str) -> bool:
        """Household claims vouchers"""
        if household_id not in self.households:
            return False
        
        if tranche not in self.tranche_config:
            return False
        
        household = self.households[household_id]
        household.claim_vouchers(tranche, self.tranche_config[tranche])
        
        # Update fast query index
        self.household_balance_index[household_id] = household.get_total_balance()
        return True
    
    def get_household_balance(self, household_id: str) -> Optional[Dict]:
        """Quickly query household balance - O(1) time complexity"""
        if household_id not in self.households:
            return None
        
        household = self.households[household_id]
        return {
            "total": self.household_balance_index[household_id],
            "breakdown": household.get_balance(),
            "household_id": household_id
        }
    
    def redeem_vouchers(self, household_id: str, merchant_id: str, denominations: Dict[float, int]) -> Optional[RedemptionTransaction]:
        """Redeem vouchers"""
        if household_id not in self.households or merchant_id not in self.merchants:
            return None
        
        household = self.households[household_id]
        available_balance = household.get_balance()
        
        # Check if balance is sufficient
        for denom, count in denominations.items():
            if available_balance.get(denom, 0) < count:
                return None
        
        # Find and mark vouchers to be used
        vouchers_used = []
        total_amount = 0
        
        for denom, count in denominations.items():
            vouchers_found = 0
            for tranche, tranche_vouchers in household.vouchers.items():
                for voucher in tranche_vouchers:
                    if voucher.denomination == denom and voucher.status == "active" and vouchers_found < count:
                        voucher.use_voucher(datetime.now().strftime("%Y%m%d%H%M%S"))
                        vouchers_used.append(voucher)
                        total_amount += denom
                        vouchers_found += 1
                        if vouchers_found == count:
                            break
                if vouchers_found == count:
                    break
        
        # Create transaction record
        transaction_id = f"TX{datetime.now().strftime('%Y%m%d%H%M%S')}"
        transaction = RedemptionTransaction(
            transaction_id=transaction_id,
            household_id=household_id,
            merchant_id=merchant_id,
            transaction_datetime=datetime.now().strftime("%Y%m%d%H%M%S"),
            vouchers_used=vouchers_used,
            total_amount=total_amount,
            payment_status="Completed"
        )
        
        self.transactions[transaction_id] = transaction
        self.household_balance_index[household_id] = household.get_total_balance()
        
        return transaction

# Data persistence management class
class DataPersistenceManager:
    """Data persistence management class - handles file storage and loading"""
    
    @staticmethod
    def save_households(households: Dict[str, Household], filename: str):
        """Save household data to file"""
        data = {hid: asdict(hh) for hid, hh in households.items()}
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    @staticmethod
    def load_households(filename: str) -> Dict[str, Household]:
        """Load household data from file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            households = {}
            for hid, hh_data in data.items():
                # Convert vouchers data
                vouchers_dict = {}
                for tranche, voucher_list in hh_data['vouchers'].items():
                    vouchers_dict[tranche] = [Voucher(**v) for v in voucher_list]
                hh_data['vouchers'] = vouchers_dict
                households[hid] = Household(**hh_data)
            return households
        except FileNotFoundError:
            return {}
    
    @staticmethod
    def save_redemption_transaction(transaction: RedemptionTransaction):
        """Save redemption transaction record (as per document format requirements)"""
        filename = f"Redeem{datetime.now().strftime('%Y%m%d%H')}.csv"
        # Implement CSV format saving logic
        pass
