import json
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

@dataclass
class Voucher:
    """代金券类 - 表示单张代金券"""
    voucher_code: str
    expiry_date: datetime
    denomination: float  # 面值：2.0, 5.0, 10.0
    tranche: str        # 批次："2025-05" 或 "2026-01"
    status: str = "active"  # active, used, expired
    household_id: Optional[str] = None
    redemption_date: Optional[str] = None
    
    
    def use_voucher(self, redemption_date: str):
        """标记代金券为已使用"""
        self.status = "used"
        self.redemption_date = redemption_date
    
    def check_expiry(self) -> bool:
        """检查并更新券的过期状态"""
        if self.status == "used":
            return False
            
        # 获取当前日期 (YYYY-MM-DD)
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # 如果当前日期大于过期日期，强制转为 expired
        if current_date > self.expiry_date:
            self.status = "expired"
            return True
        return False

@dataclass
class Household:
    """家庭账户类 - 核心业务实体"""
    household_id: str
    family_members: List[str]
    postal_code: str
    registration_date: str
    vouchers: Dict[str, List[Voucher]]  # 按批次存储代金券
    
    def get_balance(self) -> Dict[float, int]:
        """获取当前余额（按面值分类统计）"""
        balance = {2.0: 0, 5.0: 0, 10.0: 0}
        for tranche_vouchers in self.vouchers.values():
            for voucher in tranche_vouchers:
                if voucher.status == "active":
                    balance[voucher.denomination] += 1
        return balance
    
    def get_total_balance(self) -> float:
        """获取总余额"""
        balance = self.get_balance()
        return sum(denom * count for denom, count in balance.items())
    
    def claim_vouchers(self, tranche: str, denominations: Dict[float, int]):
        """领取指定批次的代金券"""
        if tranche not in self.vouchers:
            self.vouchers[tranche] = []
        
          # 根据批次确定到期日期
        if tranche == "2025-05":
            expiry_date = datetime(2025, 12, 31)  # 2025年12月31日
        elif tranche == "2026-01":
            expiry_date = datetime(2026, 12, 31)  # 2026年12月31日
        else:
            # 如果是其他批次，默认为批次年份的12月31日
            year = int(tranche.split('-')[0])  # 提取年份
            expiry_date = datetime(year, 12, 31)

        for denomination, count in allocation.items():
            for _ in range(count):
                # 生成唯一的券代码
                voucher_code = f"CDC_{tranche}_{denomination}_{len(self.vouchers[tranche])+1:04d}"
                
                # 创建Voucher对象，传入expiry_date参数
                voucher = Voucher(
                    voucher_code=voucher_code,
                    amount=float(denomination),  # 确保转换为浮点数
                    tranche=tranche,
                    expiry_date=expiry_date,  # 设置到期日期
                    status="active"
                )
                self.vouchers[tranche].append(voucher)
        
        return True

@dataclass
class Merchant:
    """商户账户类"""
    merchant_id: str
    merchant_name: str
    uen: str
    bank_name: str
    bank_code: str
    branch_code: str
    account_number: str
    account_holder_name: str
    registration_date: str
    status: str = "Active"

@dataclass
class RedemptionTransaction:
    """代金券兑换交易类"""
    transaction_id: str
    household_id: str
    merchant_id: str
    transaction_datetime: str
    vouchers_used: List[Voucher]
    total_amount: float
    payment_status: str = "Pending"
    
    def get_remarks(self) -> str:
        """生成交易备注（按文档要求的格式）"""
        if len(self.vouchers_used) == 1:
            return "Final denomination used"
        else:
            remarks = []
            for i, voucher in enumerate(self.vouchers_used, 1):
                if i == len(self.vouchers_used):
                    remarks.append(f"{i},Final denomination used")
                else:
                    remarks.append(str(i))
            return ",".join(remarks)

class CDCSystem:
    """CDC系统主类 - 管理所有业务逻辑和内存数据结构"""
    
    def __init__(self):
        # 内存数据结构 - 支持快速查询
        self.households: Dict[str, Household] = {}  # 家庭ID -> Household对象
        self.merchants: Dict[str, Merchant] = {}    # 商户ID -> Merchant对象
        self.transactions: Dict[str, RedemptionTransaction] = {}  # 交易ID -> Transaction对象
        
        # 快速查询索引
        self.household_balance_index: Dict[str, float] = {}  # 家庭ID -> 总余额（O(1)查询）
        
        # 代金券批次配置（根据文档中的表格）
        self.tranche_config = {
            "2025-05": {2.0: 50, 5.0: 20, 10.0: 30},  # 500新元
            "2026-01": {2.0: 30, 5.0: 12, 10.0: 15}   # 300新元
        }
    
    def register_household(self, household_id: str, family_members: List[str], postal_code: str) -> Household:
        """注册家庭账户"""
        household = Household(
            household_id=household_id,
            family_members=family_members,
            postal_code=postal_code,
            registration_date=datetime.now().strftime("%Y-%m-%d"),
            vouchers={}
        )
        self.households[household_id] = household
        self.household_balance_index[household_id] = 0.0
        return household
    
    def register_merchant(self, merchant_data: Dict) -> Merchant:
        """注册商户账户"""
        merchant = Merchant(**merchant_data)
        self.merchants[merchant.merchant_id] = merchant
        return merchant
    
    def claim_vouchers(self, household_id: str, tranche: str) -> bool:
        """家庭领取代金券"""
        if household_id not in self.households:
            return False
        
        if tranche not in self.tranche_config:
            return False
        
        household = self.households[household_id]
        household.claim_vouchers(tranche, self.tranche_config[tranche])
        
        # 更新快速查询索引
        self.household_balance_index[household_id] = household.get_total_balance()
        return True
    
    def refresh_vouchers_status(self):
        """遍历所有家庭的所有券，自动标记过期"""
        expired_count = 0
        for household in self.households.values():
            for tranche in household.vouchers.values():
                for voucher in tranche:
                    if voucher.check_expiry():
                        expired_count += 1
        if expired_count > 0:
            print(f"系统已自动清理 {expired_count} 张过期代金券。")

    def get_household_balance(self, household_id: str) -> Optional[Dict]:
        """快速查询家庭余额 - O(1)时间复杂度"""
        if household_id not in self.households:
            return None
        
        household = self.households[household_id]
        return {
            "total": self.household_balance_index[household_id],
            "breakdown": household.get_balance(),
            "household_id": household_id
        }
    
    def redeem_vouchers(self, household_id: str, merchant_id: str, denominations: Dict[float, int]) -> Optional[RedemptionTransaction]:
        """代金券兑换"""
        if household_id not in self.households or merchant_id not in self.merchants:
            return None
        
        household = self.households[household_id]
        available_balance = household.get_balance()
        
        # 检查余额是否足够
        for denom, count in denominations.items():
            if available_balance.get(denom, 0) < count:
                return None
        
        # 查找并标记使用的代金券
        vouchers_used = []
        total_amount = 0
        
        for denom, count in denominations.items():
            vouchers_found = 0
            for tranche, tranche_vouchers in household.vouchers.items():
                for voucher in tranche_vouchers:
                    if voucher.is_expired():
                        continue 
             
                    if voucher.denomination == denom and voucher.status == "active" and vouchers_found < count:
                        voucher.use_voucher(datetime.now().strftime("%Y%m%d%H%M%S"))
                        vouchers_used.append(voucher)
                        total_amount += denom
                        vouchers_found += 1
                        if vouchers_found == count:
                            break
                if vouchers_found == count:
                    break
        
        # 创建交易记录
        transaction_id = f"TX{datetime.now().strftime('%Y%m%d%H%M%S')}"
        transaction = RedemptionTransaction(
            transaction_id=transaction_id,
            household_id=household_id,
            merchant_id=merchant_id,
            transaction_datetime=datetime.now().strftime("%Y%m%d%H%M%S"),
            vouchers_used=vouchers_used,
            total_amount=total_amount,
            payment_status="Completed"
        )
        
        self.transactions[transaction_id] = transaction
        self.household_balance_index[household_id] = household.get_total_balance()
    
    def export_hourly_summary_csv(self):
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        hour_str = now.strftime("%H")
        filename = f"Redeem{now.strftime('%Y%m%d%H')}.csv"
        
        # 1. 预处理：刷新所有券的过期状态，确保“当前总额”准确
        for hh in self.households.values():
            for tranche in hh.vouchers.values():
                for v in tranche:
                    v.is_expired() # 调用之前写的过期检查方法

        current_hour_prefix = now.strftime("%Y%m%d%H")
        
        # 2. 构造数据：这里我们遍历所有有变动的家庭
        # 如果需要监控所有家庭，则遍历 self.households.values()
        summary_data = defaultdict(lambda: defaultdict(int)) # {hid: {denom: count}}
        
        for tx in self.transactions.values():
            if tx.transaction_datetime.startswith(current_hour_prefix):
                for v in tx.vouchers_used:
                    summary_data[tx.household_id][v.denomination] += 1

        fields = ["HouseholdID", "Denomination", "Count", "Date", "Hour", "Initial_Total_Value", "Current_Total_Value"]
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                
                # 遍历所有家庭（确保即使没消费，余额也能被核查）
                for hid, household in self.households.items():
                    # 计算初始总额和当前余额
                    initial_total = sum(v.denomination for v_list in household.vouchers.values() for v in v_list)
                    current_balance = household.get_total_balance()
                    
                    # 获取该小时内的变动（如果有的话）
                    changes = summary_data.get(hid, {})
                    
                    # 如果该小时有消费，记录消费面额；如果没消费，记录一条 Count 为 0 的记录或跳过
                    # 通常核查要求记录变动：
                    if changes:
                        for denom, count in changes.items():
                            writer.writerow({
                                "HouseholdID": hid, "Denomination": denom, "Count": count,
                                "Date": date_str, "Hour": hour_str,
                                "Initial_Total_Value": initial_total,
                                "Current_Total_Value": current_balance
                            })
                    else:
                        # 可选：记录无变动的余额快照（对于核查非常有用）
                        writer.writerow({
                            "HouseholdID": hid, "Denomination": "-", "Count": 0,
                            "Date": date_str, "Hour": hour_str,
                            "Initial_Total_Value": initial_total,
                            "Current_Total_Value": current_balance
                        })
            return filename
        except Exception as e:
            print(f"Error: {e}")
            return None
# 数据持久化管理类
class DataPersistenceManager:
    """数据持久化管理类 - 处理文件存储和加载"""
    
    @staticmethod
    def save_households(households: Dict[str, Household], filename: str):
        """保存家庭数据到文件"""
        data = {hid: asdict(hh) for hid, hh in households.items()}
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    @staticmethod
    def load_households(filename: str) -> Dict[str, Household]:
        """从文件加载家庭数据"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            households = {}
            for hid, hh_data in data.items():
                # 转换vouchers数据
                vouchers_dict = {}
                for tranche, voucher_list in hh_data['vouchers'].items():
                    vouchers_dict[tranche] = [Voucher(**v) for v in voucher_list]
                hh_data['vouchers'] = vouchers_dict
                households[hid] = Household(**hh_data)
            return households
        except FileNotFoundError:
            return {}
    
    @staticmethod
    def save_redemption_transaction(transaction: RedemptionTransaction):
        """保存兑换交易记录（按文档要求的格式）"""
        filename = f"Redeem{datetime.now().strftime('%Y%m%d%H')}.csv"
        # 实现CSV格式保存逻辑
        pass