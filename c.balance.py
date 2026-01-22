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
        
        formatted_breakdown = [
            {"denomination": float(denom), "count": count}
            for denom, count in balance_info["breakdown"].items()
        ]

        # 构建响应数据
        response_data = {
            "household_id": household_id,
            "total_balance": balance_info["total"],
            "balance_breakdown": formatted_breakdown,
            "date": datetime.now().strftime("%Y-%m-%d"),       # 输出示例: 2026-01-15
            "hour": datetime.now().strftime("%H:00"),
            "status": "success"
        }
        
        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "household_id": household_id
        }), 500



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
