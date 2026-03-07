import logging

class TokenManager:
    """针对 AI 接口调用的 Token 计数与预算管理"""
    def __init__(self, daily_budget=5.0):
        self.daily_budget = daily_budget
        self.current_usage = 0.0

    def can_consume(self, estimated_cost=0.01):
        """检查今日 Token 余额是否足以支持本次 AI 识别"""
        if self.current_usage + estimated_cost <= self.daily_budget:
            return True
        logging.error("❌ Token 预算不足，已触发安全熔断")
        return False

    def record_usage(self, tokens, model="gpt-4o-mini"):
        """记录 Token 消耗并折算金额"""
        # 简化计算逻辑：每 1000 tokens 约 0.015 美元
        cost = (tokens / 1000) * 0.015
        self.current_usage += cost
        logging.info(f"📊 AI 识别成功，当前累计消耗: ${self.current_usage:.4f}")