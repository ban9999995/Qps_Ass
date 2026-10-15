"""四个角色化 Agent 的确定性演示实现。"""

from typing import Any, Protocol


class Agent(Protocol):
    """结构化 Agent 的统一执行协议。"""

    async def generate(self, context: dict[str, Any]) -> dict[str, Any]: ...


class DiagnosisAgent:
    """根据商品和竞品上下文生成诊断结果。"""

    async def generate(self, context: dict[str, Any]) -> dict[str, Any]:
        """返回目标客群、卖点、卡点和优化方向。"""
        product = context.get("product", {})
        return {
            "target_audience": ["注重防晒与透气性的城市户外人群"],
            "price_band_analysis": {"current": product.get("price", 0), "suggestion": "保持中端价格并强化面料价值"},
            "selling_point_matrix": [
                {"point": "凉感透气", "evidence": "轻薄面料", "priority": "high"},
                {"point": "防晒防护", "evidence": "UPF 场景表达", "priority": "high"},
                {"point": "通勤易搭", "evidence": "多场景穿搭", "priority": "medium"},
            ],
            "conversion_blockers": ["详情页缺少透气性对比证据", "首屏防晒指数表达不够明确"],
            "optimization_directions": ["增加面料特写", "补充户外实测对比"],
            "competitor_reference": context.get("competitors", []),
        }


class CreativeAgent:
    """根据诊断结果生成主图方案和视频脚本。"""

    async def generate(self, context: dict[str, Any]) -> dict[str, Any]:
        """返回至少三组可编辑主图和视频脚本。"""
        directions = ["凉感透气", "户外防晒", "通勤轻薄"]
        plans = [
            {"version": index + 1, "title": f"{direction}主图方案", "layout": "人物半身+面料特写", "copy": f"一件搞定{direction}", "selling_point": direction, "visual_advice": "高亮自然光与轻盈动势"}
            for index, direction in enumerate(directions)
        ]
        scripts = [
            {"version": index + 1, "title": f"{direction}短视频脚本", "hook_3s": f"3秒展示{direction}", "shots": ["户外阳光", "面料近景", "穿搭转场"], "voiceover": f"穿上即刻感受{direction}", "conversion_copy": "现在下单享受清爽出行", "duration_seconds": 15}
            for index, direction in enumerate(directions)
        ]
        return {"image_plans": plans, "video_scripts": scripts, "editable": True}


class AdStrategyAgent:
    """根据已确认内容生成投放建议。"""

    async def generate(self, context: dict[str, Any]) -> dict[str, Any]:
        """返回人群、预算、出价、素材组合和预期指标。"""
        return {
            "audience": ["户外运动", "城市通勤", "防晒需求人群"],
            "budget": context.get("budget", 3000),
            "bid": context.get("bid", 1.2),
            "period_days": context.get("period_days", 7),
            "asset_mix": ["主图方案1", "视频脚本1"],
            "ab_test": ["凉感透气文案", "户外防晒文案"],
            "expected_metrics": {"ctr": 0.035, "conversion_rate": 0.025, "roi": 2.5},
        }


class ReviewAgent:
    """根据目标和经营指标生成复盘报告。"""

    async def generate(self, context: dict[str, Any]) -> dict[str, Any]:
        """返回目标实际对比、归因和下一轮行动项。"""
        metrics = context.get("metrics", {})
        return {
            "comparison": {"target": context.get("target", {}), "actual": metrics},
            "trend": "CTR 表现稳定，详情页跳失率仍需优化",
            "attribution": ["首屏卖点清晰带来点击", "面料证据不足影响详情页转化"],
            "problems": ["详情页跳失率偏高"],
            "action_items": ["补充面料特写和透气性说明", "下一轮测试户外场景首图"],
            "markdown": "## 经营复盘\n\nCTR 表现稳定，建议补充面料特写和透气性说明。",
        }
