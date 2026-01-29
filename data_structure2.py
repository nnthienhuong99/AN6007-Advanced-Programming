# data_structure.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import date, datetime

# -------- Domain Classes --------

@dataclass
class Voucher:
    """Voucher Class - Represents a single CDC Voucher"""
    voucher_id: str
    denomination: int
    tranche: str            # e.g., "MAY2025" or "JAN2026"
    expiry_date: str        # Recommended ISO format string (YYYY-MM-DD)
    status: str = "active"  # Status: active, redeemed, expired
    household_id: Optional[str] = None
    redemption_date: Optional[str] = None

@dataclass
class Household:
    """Household Class - Core business entity"""
    household_id: str
    num_people: int
    postal_code: str = ""
    registration_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    # Vouchers stored by tranche: {"MAY2025": [Voucher1, Voucher2], ...}
    vouchers: Dict[str, List[Voucher]] = field(default_factory=dict)
    nric: Dict[str, str] = field(default_factory=dict)
    full_names: Dict[str, str] = field(default_factory=dict)

    def get_balance_by_tranche(self, tranche: str) -> int:
        """Calculates the remaining balance for a specific tranche"""
        if tranche not in self.vouchers:
            return 0
        return sum(v.denomination for v in self.vouchers[tranche] if v.status == "active")

@dataclass
class Merchant:
    """Merchant Class - Merchant entity"""
    merchant_id: str
    merchant_name: str
    uen: str = ""
    bank_name: str = ""
    bank_code: str = ""
    branch_code: str = ""
    account_number: str = ""
    account_holder_name: str = ""
    registration_date: Optional[date] = None
    status: str = "Active"

@dataclass
class Transaction:
    """Transaction Class - Records redemption activity logs"""
    transaction_id: str
    household_id: str
    merchant_id: str
    amount: float
    datetime_iso: str  # Format: 2025-11-02T08:15:32
    vouchers_used: List[Voucher] = field(default_factory=list)
    payment_status: str = "Completed"

# -------- In-Memory Store --------

class InMemoryStore:
    """
    In-memory data center.
    Project requirement: System should be able to restore from this structure upon reboot.
    """
    def __init__(self):
        self.households: Dict[str, Household] = {}
        self.merchants: Dict[str, Merchant] = {}
        
        # Transactions: indexed by hour to facilitate CSV generation (RedeemYYYYMMDDHH.csv)
        self.redemptions_by_hour: Dict[str, List[Transaction]] = {}
        
        # Global voucher index (Optional: used for fast voucher lookup by ID)
        self.all_vouchers: Dict[str, Voucher] = {}

    def add_transaction(self, tx: Transaction):
        """Stores a transaction into the hour-indexed dictionary"""
        # Extract date and hour as the key (e.g., "2025052014")
        dt = datetime.fromisoformat(tx.datetime_iso)
        hour_key = dt.strftime("%Y%m%d%H")
        
        if hour_key not in self.redemptions_by_hour:
            self.redemptions_by_hour[hour_key] = []
        self.redemptions_by_hour[hour_key].append(tx)

# Global singleton object for access by services.py and server.py
store = InMemoryStore()