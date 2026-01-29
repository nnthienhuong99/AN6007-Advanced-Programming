# data_structure.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import date


# -------- Domain Classes --------

@dataclass
class Voucher:
    voucher_id: str
    denomination: int


@dataclass
class Household:
    household_id: str
    # Keep these optional so the API can register a household with only household_id.
    num_people: int
    nric: Dict[str, str] = field(default_factory=dict)
    full_names: Dict[str, str] = field(default_factory=dict)


@dataclass
class Merchant:
    merchant_id: str
    merchant_name: str
    # Optional metadata (aligns with the project PDF), defaulted for minimal registration.
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
    transaction_id: str
    household_id: str
    merchant_id: str
    amount: float
    # ISO datetime string (e.g., 2025-11-02T08:15:32)
    datetime_iso: str


# -------- In-Memory Store --------

class InMemoryStore:
    def __init__(self):
        self.households: Dict[str, Household] = {}
        self.merchants: Dict[str, Merchant] = {}
        self.redemptions_by_hour: Dict[str, List[dict]] = {}


store = InMemoryStore()
