# services2.py
import csv
import os
import json
import random
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from data_structure2 import store, Household, Merchant, Voucher, Transaction

# -------- Persistence Logic --------

DATA_DIR = "data"
STATE_FILE = os.path.join(DATA_DIR, "system_state.json")

def save_state():
    """Saves the entire in-memory store to a JSON file for persistence"""
    os.makedirs(DATA_DIR, exist_ok=True)
    data = {
        "households": {
            hid: {
                "household_id": hh.household_id,
                "num_people": hh.num_people,
                "postal_code": hh.postal_code,
                "registration_date": hh.registration_date,
                "nric": hh.nric,
                "full_names": hh.full_names,
                "vouchers": {
                    tranche: [v.__dict__ for v in v_list] 
                    for tranche, v_list in hh.vouchers.items()
                }
            } for hid, hh in store.households.items()
        },
        "merchants": {
            mid: m.__dict__ for mid, m in store.merchants.items()
        }
    }
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_state():
    """Loads data from JSON and reconstructs Python objects into the store"""
    if not os.path.exists(STATE_FILE):
        return
    with open(STATE_FILE, "r") as f:
        data = json.load(f)
        for hid, h_data in data["households"].items():
            hh = Household(
                h_data["household_id"], 
                h_data["num_people"], 
                h_data["postal_code"],
                h_data["registration_date"],
                {}, h_data["nric"], h_data["full_names"]
            )
            for tranche, v_list in h_data["vouchers"].items():
                hh.vouchers[tranche] = [Voucher(**v) for v in v_list]
            store.households[hid] = hh
        for mid, m_data in data["merchants"].items():
            store.merchants[mid] = Merchant(**m_data)

# -------- Core Business Logic --------

def redeem(tx: Transaction, tranche: str, denominations: Dict[str, int]):
    """
    Executes redemption: Deducts vouchers based on the denomination dictionary 
    sent by the mobile app (e.g., {"10": 1, "5": 2} means 1x$10 and 2x$5).
    """
    if tx.household_id not in store.households:
        raise ValueError("Household not found.")
    
    hh = store.households[tx.household_id]
    if tranche not in hh.vouchers:
        raise ValueError(f"No vouchers found for tranche {tranche}.")

    vouchers_to_redeem = []
    total_amount = 0

    # 1. Validate availability and find suitable vouchers
    for denom_str, count in denominations.items():
        denom = int(denom_str)
        count = int(count)
        # Filter active vouchers matching the denomination within the specified tranche
        available = [v for v in hh.vouchers[tranche] if v.status == "active" and v.denomination == denom]
        
        if len(available) < count:
            raise ValueError(f"Insufficient ${denom} vouchers. Need {count}, have {len(available)}.")
        
        # Select the required number of vouchers
        selected = available[:count]
        vouchers_to_redeem.extend(selected)
        total_amount += denom * count

    # 2. Update voucher status and record in transaction
    for v in vouchers_to_redeem:
        v.status = "redeemed"
        v.redemption_date = tx.datetime_iso
        tx.vouchers_used.append(v)
    
    tx.amount = total_amount
    
    # 3. Save to store indexed by hour for CSV export requirements
    hour_key = datetime.now().strftime("%Y%m%d%H")
    if hour_key not in store.redemptions_by_hour:
        store.redemptions_by_hour[hour_key] = []
    store.redemptions_by_hour[hour_key].append(tx)

    # 4. Trigger Persistence
    save_state()
    # Export to CSV immediately to satisfy real-time audit requirements
    export_redemptions_to_csv(hour_key) 
    return True

def export_redemptions_to_csv(hour_key: str):
    """
    Project Requirement: Generate RedeemYYYYMMDDHH.csv file
    """
    transactions = store.redemptions_by_hour.get(hour_key, [])
    if not transactions:
        return

    filename = f"Redeem{hour_key}.csv"
    filepath = os.path.join(DATA_DIR, filename)
    
    keys = ["transaction_id", "household_id", "merchant_id", "amount", "datetime_iso"]
    
    with open(filepath, "w", newline="") as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        for tx in transactions:
            # Export only basic fields for financial reconciliation
            dict_writer.writerow({
                "transaction_id": tx.transaction_id,
                "household_id": tx.household_id,
                "merchant_id": tx.merchant_id,
                "amount": tx.amount,
                "datetime_iso": tx.datetime_iso
            })

# -------- Helper Functions --------

def _new_voucher_id():
    """Generates a random unique ID for vouchers"""
    return f"V-{random.randint(1000000, 9999999)}"

def register_household(household_id, num_people, postal_code="", nrics=None, names=None):
    """Registers a new household and persists state"""
    if household_id in store.households:
        raise ValueError("Household ID already exists.")
    hh = Household(household_id, num_people, postal_code)
    if nrics: hh.nric = nrics
    if names: hh.full_names = names
    store.households[household_id] = hh
    save_state()
    return hh

def claim_tranche(household_id: str, tranche_name: str):
    """Allocates vouchers for a specific tranche based on project distribution rules"""
    if household_id not in store.households:
        raise ValueError("Household ID not found.")
    hh = store.households[household_id]
    if tranche_name in hh.vouchers:
        raise ValueError(f"Tranche {tranche_name} already claimed.")
    
    hh.vouchers[tranche_name] = []
    # Assign denominations based on project requirements (2025 vs others)
    dist = {2: 50, 5: 40, 10: 20} if "2025" in tranche_name else {2: 50, 5: 20, 10: 10}
    expiry = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    
    for denom, count in dist.items():
        for _ in range(count):
            v = Voucher(_new_voucher_id(), denom, tranche_name, expiry, "active", household_id)
            hh.vouchers[tranche_name].append(v)
            
    save_state()
    return serialize_household(hh)

def serialize_household(hh: Household):
    """Helper to convert household object to a dictionary for API responses"""
    return {
        "household_id": hh.household_id,
        "balances": {t: hh.get_balance_by_tranche(t) for t in hh.vouchers.keys()}
    }