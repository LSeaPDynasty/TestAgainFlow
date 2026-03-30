"""
AI辅助测试结果分析服务
"""
import logging
from typing import Optional, Dict, Any
from .ai_service import get_ai_service

logger = logging.getLogger(__name__)


class TestAnalysisService:
    """测试结果分析服务"""
    
    def __init__(self):
        self.ai_service = get_ai_service()
    
    async def analyze_failure(
        self,
        run_history_id: int,
        failure_info: dict,
        logs: list[str],
        context: Optional[dict] = None
    ) -> dict:
        """
        分析测试失败原因
        
        Args:
            run_history_id: 执行记录ID
            failure_info: 失败信息
            logs: 执行日志
            context: 额外上下文
        
        Returns:
            分析结果
        """
        # 先用规则引擎处理常见问题（免费）
        rule_result = self._check_common_patterns(failure_info, logs)
        if rule_result:
            logger.info(f"Rule engine matched: {rule_result['category']}")
            return rule_result
        
        # 构建AI prompt
        prompt = self._build_analysis_prompt(failure_info, logs, context)
        
        try:
            response = await self.ai_service.call(
                prompt=prompt,
                max_tokens=500,
                temperature=0.3
            )
            
            # 解析AI响应
            result = self._parse_ai_response(response)
            logger.info(f"AI analysis completed for run {run_history_id}")
            return result
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            # 降级：返回基础分析
            return self._generate_basic_analysis(failure_info, logs)
    
    def _check_common_patterns(self, failure_info: dict, logs: list[str]) -> Optional[dict]:
        """规则引擎：检查常见模式"""
        error_msg = failure_info.get('error', '').lower()
        
        # 常见模式1：超时
        if 'timeout' in error_msg or '超时' in error_msg:
            return {
                'category': 'timeout',
                'reason': '操作超时',
                'suggestions': [
                    '检查网络连接是否稳定',
                    '增加等待时间（wait_time）',
                    '检查页面是否加载完成',
                    '验证元素定位符是否正确'
                ],
                'confidence': 'high'
            }
        
        # 常见模式2：元素未找到
        if 'not found' in error_msg or '找不到元素' in error_msg or '元素未找到' in error_msg:
            return {
                'category': 'element_not_found',
                'reason': '元素未找到',
                'suggestions': [
                    '使用uiautomator2 dump检查页面结构',
                    '尝试其他定位符（resource-id → text → xpath）',
                    '检查元素是否在iframe或弹窗中',
                    '确认页面已完全加载'
                ],
                'confidence': 'high'
            }
        
        # 常见模式3：断言失败
        if 'assert' in error_msg or '断言' in error_msg:
            return {
                'category': 'assertion_failed',
                'reason': '断言失败',
                'suggestions': [
                    '检查预期值是否正确',
                    '验证实际值是否符合预期',
                    '增加等待时间确保状态稳定',
                    '检查是否有多个匹配元素'
                ],
                'confidence': 'high'
            }
        
        # 常见模式4：设备离线
        if 'device' in error_msg and ('offline' in error_msg or 'disconnected' in error_msg):
            return {
                'category': 'device_offline',
                'reason': '设备离线或断开连接',
                'suggestions': [
                    '检查USB连接',
                    '执行 adb devices 确认设备状态',
                    '重启adb服务：adb kill-server && adb start-server',
                    '检查设备是否开启USB调试'
                ],
                'confidence': 'high'
            }
        
        return None
    
    def _build_analysis_prompt(self, failure_info: dict, logs: list[str], context: Optional[dict]) -> str:
        """构建AI分析prompt"""
        # 只使用最后50条日志（控制token消耗）
        recent_logs = logs[-50:] if logs else []
        
        prompt = f"""分析以下Android自动化测试失败情况：

失败信息：
{str(failure_info)}

执行日志（最后50条）：
{chr(10).join(recent_logs)}

请分析：
1. 失败原因分类（超时/元素未找到/断言失败/设备问题/其他）
2. 最可能的根本原因（1-2句话）
3. 具体的排查步骤（3-5条，每条15字以内）

请以JSON格式返回：
{{
  "category": "失败分类",
  "reason": "根本原因",
  "suggestions": ["步骤1", "步骤2", "步骤3"],
  "confidence": "high/medium/low"
}}

只返回JSON，不要其他内容。"""
        
        return prompt
    
    def _parse_ai_response(self, response: str) -> dict:
        """解析AI响应"""
        import json
        
        try:
            # 尝试解析JSON
            result = json.loads(response.strip())
            return result
        except json.JSONDecodeError:
            # 解析失败，返回基础结构
            return {
                'category': 'unknown',
                'reason': response[:100],
                'suggestions': ['请检查日志获取更多信息'],
                'confidence': 'low'
            }
    
    def _generate_basic_analysis(self, failure_info: dict, logs: list[str]) -> dict:
        """降级方案：生成基础分析"""
        error_msg = failure_info.get('error', '未知错误')
        
        return {
            'category': 'unknown',
            'reason': f'测试失败: {error_msg}',
            'suggestions': [
                '查看完整日志了解详情',
                '在设备上手动复现问题',
                '检查元素定位符是否变化',
                '确认测试环境是否正常'
            ],
            'confidence': 'low',
            'note': 'AI服务暂时不可用，以上为通用建议'
        }
    
    async def batch_analyze(
        self,
        failures: list[dict]
    ) -> dict[int, dict]:
        """
        批量分析失败（去重，节省成本）
        
        Args:
            failures: 失败列表
        
        Returns:
            run_id到分析结果的映射
        """
        results = {}
        
        # 按错误类型分组
        groups = {}
        for failure in failures:
            error_key = failure.get('error', '')[:100]  # 用错误前100字符作为key
            if error_key not in groups:
                groups[error_key] = []
            groups[error_key].append(failure)
        
        # 每组只分析一次
        for error_key, group in groups.items():
            try:
                # 分析第一个
                first = group[0]
                analysis = await self.analyze_failure(
                    run_history_id=first['id'],
                    failure_info=first,
                    logs=first.get('logs', [])
                )
                
                # 应用到组内所有
                for item in group:
                    results[item['id']] = analysis
                    
            except Exception as e:
                logger.error(f"Batch analysis failed for {error_key}: {e}")
        
        return results


# 全局实例
test_analysis_service = TestAnalysisService()
