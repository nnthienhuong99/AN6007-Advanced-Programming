import json
import csv
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict

@dataclass
class Voucher:
    """Voucher Class - Represents a single CDC voucher"""
    voucher_code: str
    expiry_date: datetime
    denomination: float  # Denomination: 2.0, 5.0, 10.0
    tranche: str        # Tranche: "2025-05" or "2026-01"
    status: str = "active"  # Status: active, used, expired
    household_id: Optional[str] = None
    redemption_date: Optional[str] = None
    
    def use_voucher(self, redemption_date: str):
        """Mark the voucher as used"""
        self.status = "used"
        self.redemption_date = redemption_date
    
    def check_expiry(self) -> bool:
        """Check and update the expiry status of the voucher"""
        if self.status == "used":
            return False
            
        # Get current date (YYYY-MM-DD)
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Compare current date with expiry date
        expiry_str = self.expiry_date.strftime("%Y-%m-%d")
        if current_date > expiry_str:
            self.status = "expired"
            return True
        return False

@dataclass
class Household:
    """Household Class - Core business entity for accounts"""
    household_id: str
    family_members: List[str]
    postal_code: str
    registration_date: str
    vouchers: Dict[str, List[Voucher]]  # Vouchers stored by tranche
    
    def get_balance(self) -> Dict[float, int]:
        """Get current balance categorized by denomination"""
        balance = {2.0: 0, 5.0: 0, 10.0: 0}
        for tranche_vouchers in self.vouchers.values():
            for voucher in tranche_vouchers:
                if voucher.status == "active":
                    # Ensure denomination matches dictionary keys
                    denom = float(voucher.denomination)
                    if denom in balance:
                        balance[denom] += 1
        return balance
    
    def get_total_balance(self) -> float:
        """Get the total dollar value of active vouchers"""
        balance = self.get_balance()
        return sum(denom * count for denom, count in balance.items())
    
    def claim_vouchers(self, tranche: str, denominations: Dict[float, int]):
        """Claim vouchers for a specific tranche and update the records"""
        if tranche not in self.vouchers:
            self.vouchers[tranche] = []
        
        # Determine expiry date based on tranche
        if tranche == "2025-05":
            expiry_date = datetime(2025, 12, 31)
        elif tranche == "2026-01":
            expiry_date = datetime(2026, 12, 31)
        else:
            # Default to Dec 31st of the tranche year
            try:
                year = int(tranche.split('-')[0])
                expiry_date = datetime(year, 12, 31)
            except:
                expiry_date = datetime(2026, 12, 31)

        # FIXED: Changed 'allocation' to 'denominations' to resolve the bug
        for denomination, count in denominations.items():
            for _ in range(count):
                # Generate unique voucher code
                voucher_code = f"CDC_{tranche}_{denomination}_{len(self.vouchers[tranche])+1:04d}"
                
                voucher = Voucher(
                    voucher_code=voucher_code,
                    denomination=float(denomination),
                    tranche=tranche,
                    expiry_date=expiry_date,
                    status="active",
                    household_id=self.household_id
                )
                self.vouchers[tranche].append(voucher)
        
        return True

@dataclass
class Merchant:
    """Merchant Account Class"""
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
    """Voucher Redemption Transaction Class"""
    transaction_id: str
    household_id: str
    merchant_id: str
    transaction_datetime: str
    vouchers_used: List[Voucher]
    total_amount: float
    payment_status: str = "Pending"
    
    def get_remarks(self) -> str:
        """Generate transaction remarks per project documentation requirements"""
        if len(self.vouchers_used) == 1:
            return "Final denomination used"
        else:
            remarks = []
            for i, _ in enumerate(self.vouchers_used, 1):
                if i == len(self.vouchers_used):
                    remarks.append(f"{i},Final denomination used")
                else:
                    remarks.append(str(i))
            return ",".join(remarks)

class CDCSystem:
    """Main CDC System Class - Manages business logic and in-memory data"""
    
    def __init__(self):
        # In-memory structures for O(1) lookups
        self.households: Dict[str, Household] = {}
        self.merchants: Dict[str, Merchant] = {}
        self.transactions: Dict[str, RedemptionTransaction] = {}
        
        # Fast query index for household balances
        self.household_balance_index: Dict[str, float] = {}
        
        # Tranche configurations per project requirements
        self.tranche_config = {
            "2025-05": {2.0: 50, 5.0: 20, 10.0: 30},  # Total $500
            "2026-01": {2.0: 30, 5.0: 12, 10.0: 15}   # Total $300
        }
    
    def register_household(self, household_id: str, family_members: List[str], postal_code: str) -> Household:
        """Register a new household account"""
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
        """Register a new merchant account"""
        merchant = Merchant(**merchant_data)
        self.merchants[merchant.merchant_id] = merchant
        return merchant
    
    def claim_vouchers(self, household_id: str, tranche: str) -> bool:
        """Process voucher claims for a household"""
        if household_id not in self.households:
            return False
        
        if tranche not in self.tranche_config:
            return False
        
        household = self.households[household_id]
        household.claim_vouchers(tranche, self.tranche_config[tranche])
        
        # Update fast-lookup balance index
        self.household_balance_index[household_id] = household.get_total_balance()
        return True
    
    def refresh_vouchers_status(self):
        """Automatically mark expired vouchers across all households"""
        expired_count = 0
        for household in self.households.values():
            for tranche in household.vouchers.values():
                for voucher in tranche:
                    if voucher.check_expiry():
                        expired_count += 1
        if expired_count > 0:
            print(f"System: {expired_count} expired vouchers have been updated.")

    def get_household_balance(self, household_id: str) -> Optional[Dict]:
        """Retrieve household balance with O(1) complexity"""
        if household_id not in self.households:
            return None
        
        household = self.households[household_id]
        return {
            "total": self.household_balance_index.get(household_id, 0.0),
            "breakdown": household.get_balance(),
            "household_id": household_id
        }
    
    def redeem_vouchers(self, household_id: str, merchant_id: str, denominations: Dict[float, int]) -> Optional[RedemptionTransaction]:
        """Handle the redemption of vouchers"""
        if household_id not in self.households or merchant_id not in self.merchants:
            return None
        
        household = self.households[household_id]
        available_balance = household.get_balance()
        
        # Validate if the household has enough vouchers
        for denom, count in denominations.items():
            if available_balance.get(denom, 0) < count:
                return None
        
        vouchers_used = []
        total_amount = 0
        
        # Select active vouchers to fulfill redemption
        for denom, count in denominations.items():
            vouchers_found = 0
            for tranche_vouchers in household.vouchers.values():
                for voucher in tranche_vouchers:
                    if voucher.status == "active" and voucher.denomination == denom:
                        voucher.use_voucher(datetime.now().strftime("%Y%m%d%H%M%S"))
                        vouchers_used.append(voucher)
                        total_amount += denom
                        vouchers_found += 1
                        if vouchers_found == count:
                            break
                if vouchers_found == count:
                    break
        
        # Create and store transaction record
        tx_id = f"TX{datetime.now().strftime('%Y%m%d%H%M%S')}"
        transaction = RedemptionTransaction(
            transaction_id=tx_id,
            household_id=household_id,
            merchant_id=merchant_id,
            transaction_datetime=datetime.now().strftime("%Y%m%d%H%M%S"),
            vouchers_used=vouchers_used,
            total_amount=total_amount,
            payment_status="Completed"
        )
        
        self.transactions[tx_id] = transaction
        self.household_balance_index[household_id] = household.get_total_balance()
        return transaction

    def export_hourly_summary_csv(self):
        """Export hourly summary for audit purposes"""
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        hour_str = now.strftime("%H")
        filename = f"Redeem{now.strftime('%Y%m%d%H')}.csv"
        
        # Update expiry status before export
        self.refresh_vouchers_status()

        current_hour_prefix = now.strftime("%Y%m%d%H")
        summary_data = defaultdict(lambda: defaultdict(int))
        
        for tx in self.transactions.values():
            if tx.transaction_datetime.startswith(current_hour_prefix):
                for v in tx.vouchers_used:
                    summary_data[tx.household_id][v.denomination] += 1

        fields = ["HouseholdID", "Denomination", "Count", "Date", "Hour", "Initial_Total_Value", "Current_Total_Value"]
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                
                for hid, household in self.households.items():
                    # Calculate values for audit
                    initial_total = sum(v.denomination for v_list in household.vouchers.values() for v in v_list)
                    current_balance = household.get_total_balance()
                    
                    changes = summary_data.get(hid, {})
                    if changes:
                        for denom, count in changes.items():
                            writer.writerow({
                                "HouseholdID": hid, "Denomination": denom, "Count": count,
                                "Date": date_str, "Hour": hour_str,
                                "Initial_Total_Value": initial_total,
                                "Current_Total_Value": current_balance
                            })
                    else:
                        # Record a snapshot for households with no changes
                        writer.writerow({
                            "HouseholdID": hid, "Denomination": "-", "Count": 0,
                            "Date": date_str, "Hour": hour_str,
                            "Initial_Total_Value": initial_total,
                            "Current_Total_Value": current_balance
                        })
            return filename
        except Exception as e:
            print(f"Error exporting CSV: {e}")
            return None

class DataPersistenceManager:
    """Persistence Manager - Handles saving and loading data to flat files"""
    
    @staticmethod
    def save_households(households: Dict[str, Household], filename: str):
        """Save household data to JSON"""
        data = {hid: asdict(hh) for hid, hh in households.items()}
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    @staticmethod
    def load_households(filename: str) -> Dict[str, Household]:
        """Load household data from JSON and restore objects"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            households = {}
            for hid, hh_data in data.items():
                vouchers_dict = {}
                for tranche, voucher_list in hh_data['vouchers'].items():
                    vouchers_dict[tranche] = [Voucher(**v) for v in voucher_list]
                hh_data['vouchers'] = vouchers_dict
                households[hid] = Household(**hh_data)
            return households
        except FileNotFoundError:
            return {}
