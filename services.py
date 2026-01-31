# services.py
import csv
import os
import random
from datetime import datetime
from typing import Dict, List, Optional, Any

from data_structure import store, Household, Merchant, Voucher, Transaction, generate_random_string


# -------- Voucher Generation --------

def generate_vouchers_for_tranche(household_id: str, tranche: str) -> List[Voucher]:
    """Generate vouchers according to tranche allocation"""
    if tranche == "May2025":
        # $500: 50*2 + 20*5 + 30*10 = 500
        denominations = {2: 50, 5: 20, 10: 30}
    elif tranche == "Jan2026":
        # $300: 30*2 + 12*5 + 15*10 = 300
        denominations = {2: 30, 5: 12, 10: 15}
    else:
        raise ValueError(f"Unknown tranche: {tranche}")
    
    vouchers = []
    for denomination, count in denominations.items():
        for i in range(count):
            voucher_id = f"V{random.randint(1000000, 9999999)}"
            voucher = Voucher(
                voucher_id=voucher_id,
                denomination=denomination,
                tranche=tranche
            )
            vouchers.append(voucher)
            
            # Add to store
            if household_id not in store.vouchers_by_household:
                store.vouchers_by_household[household_id] = []
            store.vouchers_by_household[household_id].append(voucher)
            store.voucher_map[voucher_id] = voucher
    
    return vouchers


# -------- Registration Services --------

def register_household(
    household_id: str,
    postal_code: str,
    num_people: int = 1
) -> Dict[str, Any]:
    """Register a new household"""
    if household_id in store.households:
        return {"error": "Household already registered"}
    
    # Calculate district from postal code
    district = "Unknown"
    if postal_code and len(postal_code) >= 2:
        try:
            sector = int(postal_code[:2])
            if 1 <= sector <= 6:
                district = "Central"
            elif 7 <= sector <= 8:
                district = "Downtown Core"
            elif 9 <= sector <= 10:
                district = "Queenstown/Tiong Bahru"
            elif 11 <= sector <= 16:
                district = "South"
            elif 17 <= sector <= 28:
                district = "North/East/West"
        except ValueError:
            pass
    
    household = Household(
        household_id=household_id,
        postal_code=postal_code,
        registered_date=datetime.now().strftime("%Y-%m-%d"),
        num_people=num_people,
        district=district
    )
    
    store.households[household_id] = household
    store.save_all()
    
    return {
        "success": True,
        "household_id": household_id,
        "district": district,
        "message": "Household registered successfully"
    }


def register_merchant(
    merchant_id: str,
    merchant_name: str,
    uen: str = ""
) -> Dict[str, Any]:
    """Register a new merchant"""
    if merchant_id in store.merchants:
        return {"error": "Merchant already registered"}
    
    merchant = Merchant(
        merchant_id=merchant_id,
        merchant_name=merchant_name,
        uen=uen,
        registration_date=datetime.now().strftime("%Y-%m-%d")
    )
    
    store.merchants[merchant_id] = merchant
    store.save_all()
    
    return {
        "success": True,
        "merchant_id": merchant_id,
        "message": "Merchant registered successfully"
    }


# -------- Voucher Claim Service --------

def claim_vouchers(household_id: str, tranche: str) -> Dict[str, Any]:
    """Claim vouchers for a specific tranche"""
    if household_id not in store.households:
        return {"error": "Household not found"}
    
    household = store.households[household_id]
    
    if tranche in household.claimed_tranches:
        return {"error": f"Tranche {tranche} already claimed"}
    
    # Generate vouchers
    vouchers = generate_vouchers_for_tranche(household_id, tranche)
    household.claimed_tranches.append(tranche)
    
    # Update persistence
    store.save_all()
    
    balance = store.get_household_balance(household_id)
    
    return {
        "success": True,
        "household_id": household_id,
        "tranche": tranche,
        "vouchers_claimed": len(vouchers),
        "total_value": sum(v.denomination for v in vouchers),
        "balance": balance
    }


# -------- Redemption Service --------

def find_vouchers_for_redemption(household_id: str, amount: int) -> List[Voucher]:
    """Find optimal vouchers for redemption (greedy algorithm)"""
    result = []
    remaining = amount
    
    if household_id not in store.vouchers_by_household:
        return result
    
    # Get available vouchers that are not redeemed
    available_vouchers = [v for v in store.vouchers_by_household[household_id] if not v.is_redeemed]
    
    # Sort by denomination descending
    available_vouchers.sort(key=lambda v: v.denomination, reverse=True)
    
    for voucher in available_vouchers:
        if remaining >= voucher.denomination:
            result.append(voucher)
            remaining -= voucher.denomination
        
        if remaining == 0:
            break
    
    # If we couldn't make exact amount, return empty
    if remaining != 0:
        return []
    
    return result


def redeem_vouchers(
    household_id: str,
    merchant_id: str,
    amount: float
) -> Dict[str, Any]:
    """Redeem vouchers for payment"""
    if household_id not in store.households:
        return {"error": "Household not found"}
    
    if merchant_id not in store.merchants:
        return {"error": "Merchant not found"}
    
    # Check if household has sufficient balance
    balance = store.get_household_balance(household_id)
    total_balance = sum(denom * count for denom, count in balance.items())
    
    if total_balance < amount:
        return {"error": "Insufficient voucher balance"}
    
    # Get vouchers to redeem
    vouchers_to_redeem = find_vouchers_for_redemption(household_id, int(amount))
    
    if not vouchers_to_redeem:
        return {"error": "Could not find suitable vouchers"}
    
    # Create transaction
    transaction_id = f"TX{random.randint(100000, 999999)}"
    transaction_datetime = datetime.now().strftime("%Y%m%d%H%M%S")
    redemption_code = generate_random_string(20)
    
    # Create redemption records
    redemption_rows = []
    denomination_counts = {}
    
    for voucher in vouchers_to_redeem:
        denom = voucher.denomination
        denomination_counts[denom] = denomination_counts.get(denom, 0) + 1
        
        # Mark voucher as redeemed
        voucher.is_redeemed = True
        voucher.redemption_date = transaction_datetime
        voucher.merchant_id = merchant_id
    
    # Create transaction rows
    remark_counter = 1
    for denom, count in denomination_counts.items():
        amount_redeemed = denom * count
        
        for i in range(count):
            if i == count - 1:
                remarks = "Final denomination used"
            else:
                remarks = str(remark_counter)
                remark_counter += 1
            
            # Find a voucher with this denomination
            voucher = next((v for v in vouchers_to_redeem if v.denomination == denom and v.voucher_id not in [r.get('voucher_code') for r in redemption_rows]), None)
            voucher_id = voucher.voucher_id if voucher else f"V{random.randint(1000000, 9999999)}"
            
            transaction = Transaction(
                transaction_id=transaction_id,
                household_id=household_id,
                merchant_id=merchant_id,
                transaction_datetime=transaction_datetime,
                voucher_code=voucher_id,
                denomination_used=float(denom),
                amount_redeemed=float(amount_redeemed),
                payment_status="Completed",
                remarks=remarks
            )
            
            store.transactions.append(transaction)
            redemption_rows.append({
                'transaction_id': transaction_id,
                'household_id': household_id,
                'merchant_id': merchant_id,
                'transaction_datetime': transaction_datetime,
                'voucher_code': voucher_id,
                'denomination_used': float(denom),
                'amount_redeemed': float(amount_redeemed),
                'payment_status': "Completed",
                'remarks': remarks
            })
    
    # Save redemption to hourly CSV file
    save_redemption_to_hourly_csv(redemption_rows, transaction_datetime)
    
    # Update persistence
    store.save_all()
    
    return {
        "success": True,
        "transaction_id": transaction_id,
        "household_id": household_id,
        "merchant_id": merchant_id,
        "amount_redeemed": amount,
        "vouchers_used": len(vouchers_to_redeem),
        "new_balance": store.get_household_balance(household_id),
        "redemption_code": redemption_code,
        "denominations_used": denomination_counts
    }


def save_redemption_to_hourly_csv(rows: List[Dict], datetime_str: str):
    """Save redemption data to hourly CSV file"""
    # Extract date and hour
    date_str = datetime_str[:8]  # YYYYMMDD
    hour_str = datetime_str[8:10]  # HH
    
    filename = f"output/Redeem{date_str}{hour_str}.csv"
    
    fieldnames = [
        "Transaction_ID", "Household_ID", "Merchant_ID", 
        "Transaction_Date_Time", "Voucher_Code", "Denomination_Used",
        "Amount_Redeemed", "Payment_Status", "Remarks"
    ]
    
    # Write to CSV
    file_exists = os.path.exists(filename)
    
    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        for row in rows:
            # Format currency values
            formatted_row = row.copy()
            formatted_row['Denomination_Used'] = f"${row['denomination_used']:.2f}"
            formatted_row['Amount_Redeemed'] = f"${row['amount_redeemed']:.2f}"
            writer.writerow(formatted_row)


# -------- Analytics Services --------

def get_system_analytics() -> Dict[str, Any]:
    """Get analytics data"""
    total_households = len(store.households)
    total_merchants = len(store.merchants)
    total_transactions = len(store.transactions)
    
    # Calculate totals
    total_vouchers_issued = 0
    total_value_issued = 0
    total_vouchers_redeemed = 0
    total_value_redeemed = 0
    
    for household_id, household in store.households.items():
        balance = store.get_household_balance(household_id)
        total_vouchers_issued += sum(balance.values())
        total_value_issued += sum(denom * count for denom, count in balance.items())
    
    for transaction in store.transactions:
        total_vouchers_redeemed += 1
        total_value_redeemed += transaction.amount_redeemed
    
    return {
        "total_households": total_households,
        "total_merchants": total_merchants,
        "total_transactions": total_transactions,
        "vouchers_issued": total_vouchers_issued,
        "vouchers_redeemed": total_vouchers_redeemed,
        "value_issued": total_value_issued,
        "value_redeemed": total_value_redeemed,
        "value_remaining": total_value_issued - total_value_redeemed,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def get_household_balance(household_id: str) -> Dict[str, Any]:
    """Get detailed balance for a household"""
    if household_id not in store.households:
        return {"error": "Household not found"}
    
    household = store.households[household_id]
    balance = store.get_household_balance(household_id)
    
    total_vouchers = sum(balance.values())
    total_value = sum(denom * count for denom, count in balance.items())
    
    return {
        "household_id": household_id,
        "postal_code": household.postal_code,
        "district": household.district,
        "claimed_tranches": household.claimed_tranches,
        "balance_by_denomination": balance,
        "total_vouchers": total_vouchers,
        "total_value": total_value
    }


# -------- Initialization --------

def initialize_system():
    """Initialize system by loading data from files"""
    store.load_all()
    print("System initialization completed.")
    
    # Create sample data if none exists
    if not store.households:
        print("No data found, create sample data...")
        create_sample_data()


def create_sample_data():
    """Create sample data for testing"""
    # Sample households
    sample_households = [
        ("H001", "123456", 4),
        ("H002", "234567", 2),
        ("H003", "345678", 3)
    ]
    
    for hid, postal, people in sample_households:
        register_household(hid, postal, people)
        claim_vouchers(hid, "May2025")
    
    # Sample merchants
    sample_merchants = [
        ("M001", "ABC Supermarket", "201234567A"),
        ("M002", "XYZ Bakery", "201234568B"),
        ("M003", "Happy Mart", "201234569C")
    ]
    
    for mid, name, uen in sample_merchants:
        register_merchant(mid, name, uen)
    
    print(f"Create {len(sample_households)} sample households and {len(sample_merchants)} sample merchants.")