# data_structure.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import date


# -------- Domain Classes --------

@dataclass
class Voucher:
    voucher_id: str
    denomination: int
    grant_date: date
    expiry_date: date
    redemption_date: date

@dataclass
class Household:
    household_id: str
    # Keep these optional so the API can register a household with only household_id.
    num_people: int
    nric: Dict[str, str]
    full_names: Dict[str, str]
    postal_code: int
    unit_number: str

@dataclass
class Merchant:
    merchant_id: str
    merchant_name: str
    uen: str
    bank_name: str
    bank_code: int
    branch_code: int
    account_number: int
    account_holder_name: str
    registration_date: Optional[date] = None
    status: str = "Active"


@dataclass
class Transaction:
    transaction_id: str
    household_id: str
    merchant_id: str
    amount: float
    datetime_iso: str # ISO datetime string (e.g., 2025-11-02T08:15:32)


# -------- In-Memory Store --------

class InMemoryStore:
    def __init__(self):
        self.households: Dict[str, Household] = {}
        self.merchants: Dict[str, Merchant] = {}
        self.redemptions_by_hour: Dict[str, List[dict]] = {}


store = InMemoryStore()
