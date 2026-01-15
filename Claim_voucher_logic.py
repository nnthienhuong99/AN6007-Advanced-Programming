'''
Calculate balance, check status. The business logic for "how to claim coupons" is defined, such as checking eligibility, allocating coupons, and updating the balance.
'''
import json
import os
from datetime import datetime

# Voucher Batch Configuration
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

class VoucherClaimService:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.households_file = os.path.join(data_dir, "households.json")
        self.transactions_file = os.path.join(data_dir, "voucher_transactions.json")
        
        # Ensure data file exists
        self._initialize_files()
    
    def _initialize_files(self):
        """Initialize data file; create it if it doesn’t exist."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # Initialize family data file
        if not os.path.exists(self.households_file):
            initial_data = {"households": {}}
            with open(self.households_file, 'w') as f:
                json.dump(initial_data, f, indent=2)
        
        # Initialize transaction log file
        if not os.path.exists(self.transactions_file):
            initial_transactions = {"claims": []}
            with open(self.transactions_file, 'w') as f:
                json.dump(initial_transactions, f, indent=2)
    
    def load_households(self):
        """Load family data"""
        with open(self.households_file, 'r') as f:
            return json.load(f)
    
    def save_households(self, data):
        """Store family data"""
        with open(self.households_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def record_transaction(self, household_id, tranche, success, error_msg=None):
        """Record coupon redemption process"""
        with open(self.transactions_file, 'r') as f:
            transactions = json.load(f)
        
        transaction = {
            "transaction_id": f"VC{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "household_id": household_id,
            "tranche": tranche,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "error_message": error_msg
        }
        
        transactions["claims"].append(transaction)
        
        with open(self.transactions_file, 'w') as f:
            json.dump(transactions, f, indent=2)
    
    def claim_vouchers(self, household_id, tranche):
        """
        Collect designated batches of vouchers for families
        
        parameter:
            household_id: familyID
            tranche: batch ("May2025" or "Jan2026")
        
        return:
            (success, message, new_balance)
        """
        # Check if batch is valid
        if tranche not in VOUCHER_CONFIG:
            self.record_transaction(household_id, tranche, False, "Invalid batch")
            return False, f"Invalid batch: {tranche}", None
        
        # Load family data
        data = self.load_households()
        
        # Check if family exists
        if household_id not in data["households"]:
            self.record_transaction(household_id, tranche, False, "Family does not exist")
            return False, "Family does not exist", None
        
        household = data["households"][household_id]
        
        # Check if batch has been claimed.
        if household["vouchers"][tranche]["claimed"]:
            self.record_transaction(household_id, tranche, False, "This batch has been claimed.")
            return False, f"You have claimed{tranche}batch of vouchers", None
        
        # Distribute vouchers
        distribution = VOUCHER_CONFIG[tranche]["distribution"]
        
        # Update voucher balance
        for denomination, quantity in distribution.items():
            household["vouchers"][tranche]["details"][denomination] += quantity
        
        # Marked as received
        household["vouchers"][tranche]["claimed"] = True
        
        # Calculate and update total balance
        self._update_total_balance(household)
        
        # Save data
        data["households"][household_id] = household
        self.save_households(data)
        
        # Record successful transactions
        self.record_transaction(household_id, tranche, True)
        
        # Prepare success message
        voucher_details = VOUCHER_CONFIG[tranche]["distribution"]
        total_value = VOUCHER_CONFIG[tranche]["total_value"]
        message = f"""
        Successfully received{tranche}batch of vouchers！
        
        Claim Details:
        - 2$ coupon: {voucher_details['2']}
        - 5$ coupon: {voucher_details['5']}
        - 10$ coupon: {voucher_details['10']}
        - Total value: ${total_value}
        
        Current total balance: ${household['total_balance']}
        """
        
        return True, message, household['total_balance']
    
    def _update_total_balance(self, household):
        """Update total household balance"""
        total = 0
        
        for tranche in ["May2025", "Jan2026"]:
            details = household["vouchers"][tranche]["details"]
            total += (
                details["2"] * 2 +
                details["5"] * 5 +
                details["10"] * 10
            )
        
        household["total_balance"] = total
    
    def get_voucher_status(self, household_id):
        """Get status of family's vouchers"""
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

