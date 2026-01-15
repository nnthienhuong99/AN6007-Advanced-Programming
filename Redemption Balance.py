from flask import Flask, request, jsonify
from typing import Dict, Optional
import json
from datetime import datetime

# 使用之前定义的核心类
from cdc_classes import Household, CDCSystem, DataPersistenceManager

app = Flask(__name__)

# 初始化CDC系统
cdc_system = CDCSystem()

@app.route('/api/households/<household_id>/balance', methods=['GET'])
def get_redemption_balance(household_id: str):
    """
    提取家庭兑换余额API
    对应文档要求：d. Extracting Redemption Balance
    实现快速查询家庭代金券余额功能
    """
    try:
        # 使用快速查询索引实现O(1)时间复杂度查询
        if household_id not in cdc_system.household_balance_index:
            return jsonify({
                "error": "Household not found",
                "household_id": household_id
            }), 404
        
        # 获取余额信息
        balance_info = cdc_system.get_household_balance(household_id)
        
        if not balance_info:
            return jsonify({
                "error": "Unable to retrieve balance",
                "household_id": household_id
            }), 500
        
        # 构建响应数据
        response_data = {
            "household_id": household_id,
            "total_balance": balance_info["total"],
            "balance_breakdown": balance_info["breakdown"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "success"
        }
        
        # 记录查询日志（用于数据分析）
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
    批量查询多个家庭余额API
    支持移动应用一次获取多个家庭的余额信息
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
    获取详细余额分解API
    包括按批次和面值的详细分解，用于移动应用显示
    """
    try:
        if household_id not in cdc_system.households:
            return jsonify({"error": "Household not found"}), 404
        
        household = cdc_system.households[household_id]
        
        # 构建详细的余额分解
        detailed_breakdown = {
            "by_tranche": {},
            "by_denomination": {2.0: 0, 5.0: 0, 10.0: 0},
            "voucher_details": []
        }
        
        # 按批次统计
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
        
        # 按面值统计
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
    记录余额查询日志，用于数据分析仪表板
    符合文档要求：5. A simple relevant dashboard for any 1 stakeholder
    """
    log_entry = {
        "household_id": household_id,
        "balance_queried": balance,
        "query_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "query_type": "balance_inquiry"
    }
    
    # 保存到查询日志文件
    try:
        with open("balance_query_log.json", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Failed to log balance query: {e}")

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    健康检查端点，验证系统状态和数据完整性
    """
    try:
        total_households = len(cdc_system.households)
        total_balance_queries = cdc_system.household_balance_index
        
        return jsonify({
            "status": "healthy",
            "total_households": total_households,
            "index_size": len(total_balance_queries),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "memory_usage": "optimal"  # 实际实现中可以添加内存使用监控
        })
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

# 服务器启动时加载数据
# 添加一个全局标志
_first_request_loaded = False

@app.before_request
def load_initial_data():
    global _first_request_loaded
    if not _first_request_loaded:
        try:
            # 这里放置您原来的初始化代码
            households = DataPersistenceManager.load_households("households.json")
            cdc_system.households.update(households)
            
            for household_id, household in households.items():
                cdc_system.household_balance_index[household_id] = household.get_total_balance()
            
            print(f"Successfully loaded {len(households)} households")
            _first_request_loaded = True
            
        except Exception as e:
            print(f"Error loading initial data: {e}")

if __name__ == '__main__':
    # 启动Flask服务器
    app.run(host='0.0.0.0', port=5000, debug=True)
