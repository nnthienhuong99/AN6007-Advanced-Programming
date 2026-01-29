# services.py
import csv
import os
import random
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from data_structure import (
    store, Household, Merchant, Voucher, Transaction, QRData, 
    VoucherAllocation, HouseholdIndex
)
import qrcode
from io import BytesIO
import base64


# -------- Voucher Generation Service --------

class VoucherGenerator:
    """Service for generating and managing vouchers"""
    
    @staticmethod
    def generate_vouchers_for_tranche(household_id: str, tranche: str) -> List[Voucher]:
        """Generate vouchers according to tranche allocation"""
        if tranche == "May2025":
            allocation = VoucherAllocation.get_may2025_allocation()
        elif tranche == "Jan2026":
            allocation = VoucherAllocation.get_jan2026_allocation()
        else:
            raise ValueError(f"Unknown tranche: {tranche}")
        
        vouchers = []
        for denomination, count in allocation.denominations.items():
            for i in range(count):
                voucher_id = f"V{random.randint(1000000, 9999999)}"
                voucher = Voucher(
                    voucher_id=voucher_id,
                    denomination=denomination,
                    tranche=tranche
                )
                vouchers.append(voucher)
                store.voucher_index.add_voucher(household_id, voucher)
        
        return vouchers
    
    @staticmethod
    def calculate_optimal_redemption(household_id: str, amount: int) -> List[Voucher]:
        """Calculate optimal vouchers to use for redemption amount"""
        return store.voucher_index.find_vouchers_for_redemption(household_id, amount)


# -------- Registration Services --------

def register_household(
    household_id: str,
    postal_code: str,
    num_people: int = 1,
    nric_members: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Register a new household"""
    if household_id in store.households:
        return {"error": "Household already registered"}
    
    household = Household(
        household_id=household_id,
        postal_code=postal_code,
        registered_date=datetime.now().strftime("%Y-%m-%d"),
        num_people=num_people,
        nric_members=nric_members or {},
        district=None
    )
    
    # Calculate district from postal code
    household.district = household.calculate_district()
    
    store.households[household_id] = household
    store.save_all()
    
    return {
        "success": True,
        "household_id": household_id,
        "district": household.district,
        "message": "Household registered successfully"
    }


def register_merchant_from_csv_row(row: Dict[str, str]) -> Dict[str, Any]:
    """Register merchant from CSV data (as per project spec)"""
    merchant_id = row.get("Merchant_ID", "").strip()
    
    if merchant_id in store.merchants:
        return {"error": "Merchant already registered"}
    
    merchant = Merchant(
        merchant_id=merchant_id,
        merchant_name=row.get("Merchant_Name", "").strip(),
        uen=row.get("UEN", "").strip(),
        bank_name=row.get("Bank_Name", "").strip(),
        bank_code=row.get("Bank_Code", "").strip(),
        branch_code=row.get("Branch_Code", "").strip(),
        account_number=row.get("Account_Number", "").strip(),
        account_holder_name=row.get("Account_Holder_Name", "").strip(),
        registration_date=row.get("Registration_Date", datetime.now().strftime("%Y-%m-%d")).strip(),
        status=row.get("Status", "Active").strip()
    )
    
    store.merchants[merchant_id] = merchant
    
    # Save to flat file as required
    with open("data/merchants.txt", "a") as f:
        f.write(json.dumps(merchant.__dict__) + "\n")
    
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
    vouchers = VoucherGenerator.generate_vouchers_for_tranche(household_id, tranche)
    household.claimed_tranches.add(tranche)
    
    # Update persistence
    store.save_all()
    
    return {
        "success": True,
        "household_id": household_id,
        "tranche": tranche,
        "vouchers_claimed": len(vouchers),
        "total_value": sum(v.denomination for v in vouchers),
        "balance": store.voucher_index.get_household_balance(household_id)
    }


# -------- Redemption Service --------

def redeem_vouchers(
    household_id: str,
    merchant_id: str,
    amount: float,
    method: str = "optimal"  # "optimal" or "specific"
) -> Dict[str, Any]:
    """Redeem vouchers for payment"""
    if household_id not in store.households:
        return {"error": "Household not found"}
    
    if merchant_id not in store.merchants:
        return {"error": "Merchant not found"}
    
    # Check if household has sufficient balance
    balance = store.voucher_index.get_household_balance(household_id)
    total_balance = sum(denom * count for denom, count in balance.items())
    
    if total_balance < amount:
        return {"error": "Insufficient voucher balance"}
    
    # Get vouchers to redeem
    if method == "optimal":
        vouchers_to_redeem = VoucherGenerator.calculate_optimal_redemption(household_id, int(amount))
    else:
        # For specific denominations, implement as needed
        vouchers_to_redeem = []
    
    if not vouchers_to_redeem:
        return {"error": "Could not find suitable vouchers"}
    
    # Create transaction
    transaction_id = f"TX{random.randint(100000, 999999)}"
    transaction_datetime = datetime.now().strftime("%Y%m%d%H%M%S")
    
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
        
        # Remove from index
        store.voucher_index.remove_voucher(voucher.voucher_id)
    
    # Create transaction rows with Remarks as per specification
    remark_counter = 1
    for denom, count in denomination_counts.items():
        amount_redeemed = denom * count
        
        for i in range(count):
            if i == count - 1:
                remarks = "Final denomination used"
            else:
                remarks = str(remark_counter)
                remark_counter += 1
            
            voucher_id = f"V{random.randint(1000000, 9999999)}"  # In practice, get actual voucher IDs
            
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
            redemption_rows.append(transaction.__dict__)
    
    # Generate QR code data
    qr_data = QRData(
        transaction_id=transaction_id,
        household_id=household_id,
        merchant_id=merchant_id,
        amount=amount,
        denominations=[(denom, count) for denom, count in denomination_counts.items()],
        timestamp=transaction_datetime
    )
    
    store.qr_codes[transaction_id] = qr_data
    
    # Save redemption to hourly CSV file as required
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
        "new_balance": store.voucher_index.get_household_balance(household_id),
        "qr_data": generate_qr_code(qr_data)
    }


def save_redemption_to_hourly_csv(rows: List[Dict], datetime_str: str):
    """Save redemption data to hourly CSV file as per specification"""
    # Extract date and hour from datetime (YYYYMMDDHHMMSS)
    date_str = datetime_str[:8]  # YYYYMMDD
    hour_str = datetime_str[8:10]  # HH
    
    filename = f"output/Redeem{date_str}{hour_str}.csv"
    
    # Define fieldnames as per specification
    fieldnames = [
        "Transaction_ID", "Household_ID", "Merchant_ID", 
        "Transaction_Date_Time", "Voucher_Code", "Denomination_Used",
        "Amount_Redeemed", "Payment_Status", "Remarks"
    ]
    
    # Prepare data for CSV
    csv_data = []
    for row in rows:
        csv_row = {
            "Transaction_ID": row["transaction_id"],
            "Household_ID": row["household_id"],
            "Merchant_ID": row["merchant_id"],
            "Transaction_Date_Time": row["transaction_datetime"],
            "Voucher_Code": row["voucher_code"],
            "Denomination_Used": f"${row['denomination_used']:.2f}",
            "Amount_Redeemed": f"${row['amount_redeemed']:.2f}",
            "Payment_Status": row["payment_status"],
            "Remarks": row["remarks"]
        }
        csv_data.append(csv_row)
    
    # Write to CSV
    file_exists = os.path.exists(filename)
    
    with open(filename, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        for row in csv_data:
            writer.writerow(row)


# -------- QR Code Service --------

def generate_qr_code(qr_data: QRData) -> Dict[str, Any]:
    """Generate QR code for transaction"""
    # Prepare data for QR code
    qr_info = {
        "transaction_id": qr_data.transaction_id,
        "household_id": qr_data.household_id,
        "merchant_id": qr_data.merchant_id,
        "amount": qr_data.amount,
        "denominations": qr_data.denominations,
        "timestamp": qr_data.timestamp
    }
    
    # Generate QR code
    qr = qrcode.make(json.dumps(qr_info))
    
    # Save to BytesIO
    buffered = BytesIO()
    qr.save(buffered, format="PNG")
    
    # Convert to base64 for API response
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return {
        "qr_code_base64": img_str,
        "transaction_data": qr_info
    }


# -------- Analytics and Dashboard Services --------

def get_system_analytics() -> Dict[str, Any]:
    """Get analytics data for dashboard"""
    total_households = len(store.households)
    total_merchants = len(store.merchants)
    total_transactions = len(store.transactions)
    
    # Calculate total vouchers issued and redeemed
    total_vouchers_issued = 0
    total_vouchers_redeemed = 0
    total_value_issued = 0
    total_value_redeemed = 0
    
    for household in store.households.values():
        balance = store.voucher_index.get_household_balance(household.household_id)
        total_vouchers_issued += sum(balance.values())
        total_value_issued += sum(denom * count for denom, count in balance.items())
    
    # Calculate from transactions
    for transaction in store.transactions:
        total_vouchers_redeemed += 1
        total_value_redeemed += transaction.amount_redeemed
    
    # District-wise distribution
    district_stats = {}
    for household in store.households.values():
        district = household.district or "Unknown"
        if district not in district_stats:
            district_stats[district] = {
                "households": 0,
                "total_balance": 0
            }
        district_stats[district]["households"] += 1
        
        balance = store.voucher_index.get_household_balance(household.household_id)
        district_stats[district]["total_balance"] += sum(denom * count for denom, count in balance.items())
    
    return {
        "total_households": total_households,
        "total_merchants": total_merchants,
        "total_transactions": total_transactions,
        "vouchers_issued": total_vouchers_issued,
        "vouchers_redeemed": total_vouchers_redeemed,
        "value_issued": total_value_issued,
        "value_redeemed": total_value_redeemed,
        "value_remaining": total_value_issued - total_value_redeemed,
        "district_stats": district_stats,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def get_household_balance(household_id: str) -> Dict[str, Any]:
    """Get detailed balance for a household"""
    if household_id not in store.households:
        return {"error": "Household not found"}
    
    household = store.households[household_id]
    balance = store.voucher_index.get_household_balance(household_id)
    
    # Calculate breakdown by tranche (simplified)
    tranche_breakdown = {}
    total_value = 0
    
    for denom, count in balance.items():
        total_value += denom * count
        # Simplified: assume equal distribution between tranches
        tranche_breakdown[denom] = {
            "May2025": count // 2,
            "Jan2026": count // 2,
            "count": count
        }
    
    return {
        "household_id": household_id,
        "postal_code": household.postal_code,
        "district": household.district,
        "claimed_tranches": list(household.claimed_tranches),
        "balance_by_denomination": balance,
        "total_vouchers": sum(balance.values()),
        "total_value": total_value,
        "tranche_breakdown": tranche_breakdown
    }


# -------- Balance Export Service --------

def export_balance_snapshot(date_str: str, hour_str: str) -> Dict[str, Any]:
    """Export balance snapshot to CSV file"""
    filename = f"output/RedemptionBalance{date_str}{hour_str}.csv"
    
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = [
            "Household_ID", "District", "Denomination_$2", 
            "Denomination_$5", "Denomination_$10", "Total_Vouchers", 
            "Total_Value", "Snapshot_Date", "Snapshot_Hour"
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for household_id, household in store.households.items():
            balance = store.voucher_index.get_household_balance(household_id)
            
            row = {
                "Household_ID": household_id,
                "District": household.district or "Unknown",
                "Denomination_$2": balance.get(2, 0),
                "Denomination_$5": balance.get(5, 0),
                "Denomination_$10": balance.get(10, 0),
                "Total_Vouchers": sum(balance.values()),
                "Total_Value": sum(denom * count for denom, count in balance.items()),
                "Snapshot_Date": date_str,
                "Snapshot_Hour": hour_str
            }
            
            writer.writerow(row)
    
    return {
        "success": True,
        "filename": filename,
        "records_exported": len(store.households),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


# -------- Initialization --------

def initialize_system():
    """Initialize system by loading data from files"""
    store.load_all()
    print("System initialized. Data loaded from files.")
    
    # Create sample data if none exists
    if not store.households:
        print("No data found. Creating sample data...")
        create_sample_data()


def create_sample_data():
    """Create sample data for testing"""
    # Sample households
    sample_households = [
        ("H001", "123456", 4),
        ("H002", "234567", 2),
        ("H003", "345678", 3),
        ("H004", "456789", 5),
        ("H005", "567890", 1)
    ]
    
    for hid, postal, people in sample_households:
        register_household(hid, postal, people)
        claim_vouchers(hid, "May2025")
        claim_vouchers(hid, "Jan2026")
    
    print(f"Created {len(sample_households)} sample households with vouchers.")