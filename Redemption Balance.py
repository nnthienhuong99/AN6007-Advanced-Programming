from flask import Flask, request, jsonify
from typing import Dict, Optional
import json
from datetime import datetime

# Use the previously defined core classes
from cdc_classes import Household, CDCSystem, DataPersistenceManager

app = Flask(__name__)

# Initialize CDC system
cdc_system = CDCSystem()

@app.route('/api/households/<household_id>/balance', methods=['GET'])
def get_redemption_balance(household_id: str):
    """
    API for retrieving household redemption balance
    Corresponds to document requirement: d. Extracting Redemption Balance
    Implements fast query for household voucher balance functionality
    """
    try:
        # Use fast query index to achieve O(1) time complexity query
        if household_id not in cdc_system.household_balance_index:
            return jsonify({
                "error": "Household not found",
                "household_id": household_id
            }), 404
        
        # Get balance information
        balance_info = cdc_system.get_household_balance(household_id)
        
        if not balance_info:
            return jsonify({
                "error": "Unable to retrieve balance",
                "household_id": household_id
            }), 500
        
        # Construct response data
        response_data = {
            "household_id": household_id,
            "total_balance": balance_info["total"],
            "balance_breakdown": balance_info["breakdown"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "success"
        }
        
        # Log query (for data analysis)
        log_balance_query(household_id, balance_info["total"])
        
        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "household_id": household_id
        }), 500

@app.route('/api/households/balance/batch', methods=['POST'])
def get_batch_balances():
    """
    Batch query API for multiple household balances
    Supports mobile applications retrieving balances for multiple households at once
    """
    try:
        data = request.get_json()
        household_ids = data.get('household_ids', [])
        
        if not household_ids:
            return jsonify({"error": "No household IDs provided"}), 400
        
        results = []
        for hid in household_ids:
            if hid in cdc_system.household_balance_index:
                balance_info = cdc_system.get_household_balance(hid)
                if balance_info:
                    results.append({
                        "household_id": hid,
                        "total_balance": balance_info["total"],
                        "balance_breakdown": balance_info["breakdown"]
                    })
        
        return jsonify({
            "results": results,
            "total_queried": len(household_ids),
            "total_found": len(results),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/households/<household_id>/balance/breakdown', methods=['GET'])
def get_detailed_balance(household_id: str):
    """
    API for retrieving detailed balance breakdown
    Includes detailed breakdown by batch and denomination, for mobile application display
    """
    try:
        if household_id not in cdc_system.households:
            return jsonify({"error": "Household not found"}), 404
        
        household = cdc_system.households[household_id]
        
        # Build detailed balance breakdown
        detailed_breakdown = {
            "by_tranche": {},
            "by_denomination": {2.0: 0, 5.0: 0, 10.0: 0},
            "voucher_details": []
        }
        
        # Statistics by batch
        for tranche, vouchers in household.vouchers.items():
            active_vouchers = [v for v in vouchers if v.status == "active"]
            if active_vouchers:
                detailed_breakdown["by_tranche"][tranche] = {
                    "total_value": sum(v.denomination for v in active_vouchers),
                    "voucher_count": len(active_vouchers),
                    "denomination_breakdown": {
                        2.0: len([v for v in active_vouchers if v.denomination == 2.0]),
                        5.0: len([v for v in active_vouchers if v.denomination == 5.0]),
                        10.0: len([v for v in active_vouchers if v.denomination == 10.0])
                    }
                }
        
        # Statistics by denomination
        for tranche_vouchers in household.vouchers.values():
            for voucher in tranche_vouchers:
                if voucher.status == "active":
                    detailed_breakdown["by_denomination"][voucher.denomination] += 1
                    detailed_breakdown["voucher_details"].append({
                        "voucher_code": voucher.voucher_code,
                        "denomination": voucher.denomination,
                        "tranche": voucher.tranche,
                        "status": voucher.status
                    })
        
        response_data = {
            "household_id": household_id,
            "total_balance": household.get_total_balance(),
            "detailed_breakdown": detailed_breakdown,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def log_balance_query(household_id: str, balance: float):
    """
    Log balance queries for data analysis dashboard
    Complies with document requirement: 5. A simple relevant dashboard for any 1 stakeholder
    """
    log_entry = {
        "household_id": household_id,
        "balance_queried": balance,
        "query_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "query_type": "balance_inquiry"
    }
    
    # Save to query log file
    try:
        with open("balance_query_log.json", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Failed to log balance query: {e}")

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint, verifies system status and data integrity
    """
    try:
        total_households = len(cdc_system.households)
        total_balance_queries = cdc_system.household_balance_index
        
        return jsonify({
            "status": "healthy",
            "total_households": total_households,
            "index_size": len(total_balance_queries),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "memory_usage": "optimal"  # Actual implementation could add memory usage monitoring
        })
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

# Load data when server starts
# Add a global flag
_first_request_loaded = False

@app.before_request
def load_initial_data():
    global _first_request_loaded
    if not _first_request_loaded:
        try:
            # Place your original initialization code here
            households = DataPersistenceManager.load_households("households.json")
            cdc_system.households.update(households)
            
            for household_id, household in households.items():
                cdc_system.household_balance_index[household_id] = household.get_total_balance()
            
            print(f"Successfully loaded {len(households)} households")
            _first_request_loaded = True
            
        except Exception as e:
            print(f"Error loading initial data: {e}")

if __name__ == '__main__':
    # Start Flask server
    app.run(host='0.0.0.0', port=5000, debug=True)
