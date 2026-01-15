from flask import Blueprint, request, jsonify, render_template
from .logic import VoucherClaimService

# Establish Blueprint
bp = Blueprint('claim_voucher', __name__, url_prefix='/voucher')
service = VoucherClaimService()

@bp.route('/claim', methods=['POST'])
def claim_vouchers():
    """API Interface: Claiming Coupons"""
    try:
        data = request.json
        household_id = data.get('household_id')
        tranche = data.get('tranche')  # "May2025" or "Jan2026"
        
        if not household_id or not tranche:
            return jsonify({
                "success": False,
                "message": "Missing necessary parameters: household_id and tranche"
            }), 400
        
        success, message, new_balance = service.claim_vouchers(household_id, tranche)
        
        if success:
            return jsonify({
                "success": True,
                "message": message,
                "new_balance": new_balance
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": message
            }), 400
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"System error: {str(e)}"
        }), 500

@bp.route('/status/<household_id>', methods=['GET'])
def get_voucher_status(household_id):
    """API Interface: Get Voucher Status"""
    try:
        status = service.get_voucher_status(household_id)
        
        if status is None:
            return jsonify({
                "success": False,
                "message": "Family does not exist"
            }), 404
        
        return jsonify({
            "success": True,
            "status": status
        }), 200
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"System error: {str(e)}"
        }), 500

@bp.route('/dashboard/<household_id>')
def voucher_dashboard(household_id):
    """Web page: Voucher Management Panel"""
    status = service.get_voucher_status(household_id)
    
    if status is None:
        return "Family does not exist", 404
    
    return render_template('claim_voucher.html', 
                         household_id=household_id,
                         status=status)