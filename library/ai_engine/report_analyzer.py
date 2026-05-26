import json
import os
from typing import Dict, List, Optional

import requests


class ReportAnalyzer:
    """Analyze task logs and steps, with an optional OpenAI-compatible endpoint."""

    def __init__(self):
        self.endpoint = os.environ.get("OTEST_AI_ENDPOINT")
        self.api_key = os.environ.get("OTEST_AI_API_KEY")
        self.model = os.environ.get("OTEST_AI_MODEL", "gpt-4o-mini")

    def analyze(self, task, log_text: Optional[str], step_text: Optional[str]) -> Dict[str, object]:
        log_text = log_text or ""
        step_text = step_text or ""
        local_result = self._local_analyze(task, log_text, step_text)

        if not self.endpoint or not self.api_key:
            return local_result

        try:
            ai_result = self._remote_analyze(task, log_text, step_text, local_result)
            if ai_result:
                local_result["ai_summary"] = ai_result
                local_result["analyzer"] = "remote"
        except Exception as exc:
            local_result["ai_error"] = str(exc)

        return local_result

    def _local_analyze(self, task, log_text: str, step_text: str) -> Dict[str, object]:
        text = "\n".join([log_text, step_text]).lower()
        findings = []

        rules = [
            ("元素定位失败", ("pocotargettimeout", "targetnotfounderror", "waiting timeout", "找不到元素")),
            ("设备连接异常", ("connect", "wdaerror", "adb", "连接设备失败")),
            ("应用启动或停止异常", ("start_app", "stop_app", "package", "activity")),
            ("脚本断言失败", ("assert", "assertionerror", "断言")),
            ("运行时异常", ("traceback", "exception", "error")),
        ]

        for title, keywords in rules:
            if any(keyword in text for keyword in keywords):
                findings.append({
                    "type": title,
                    "evidence": self._first_matching_line(log_text + "\n" + step_text, keywords),
                    "suggestion": self._suggestion_for(title),
                })

        if not findings:
            findings.append({
                "type": "未发现明显失败特征",
                "evidence": "",
                "suggestion": "请结合截图、设备状态和业务断言继续排查。",
            })

        return {
            "task_id": getattr(task, "task_id", None),
            "task_name": getattr(task, "name", None),
            "status": getattr(task, "status", None),
            "analyzer": "local",
            "summary": self._build_summary(findings),
            "findings": findings,
        }

    def _remote_analyze(self, task, log_text: str, step_text: str, local_result: Dict[str, object]) -> Optional[str]:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是移动端自动化测试专家，请用中文分析失败原因并给出简洁修复建议。",
                },
                {
                    "role": "user",
                    "content": json.dumps({
                        "task": {
                            "id": getattr(task, "task_id", None),
                            "name": getattr(task, "name", None),
                            "status": getattr(task, "status", None),
                        },
                        "local_analysis": local_result,
                        "logs": log_text[-6000:],
                        "steps": step_text[-6000:],
                    }, ensure_ascii=False),
                },
            ],
            "temperature": 0.2,
        }
        response = requests.post(
            self.endpoint,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            return None
        message = choices[0].get("message") or {}
        return message.get("content")

    @staticmethod
    def _first_matching_line(text: str, keywords) -> str:
        for line in text.splitlines():
            lowered = line.lower()
            if any(keyword in lowered for keyword in keywords):
                return line[:300]
        return ""

    @staticmethod
    def _suggestion_for(title: str) -> str:
        suggestions = {
            "元素定位失败": "优先检查 Poco/Airtest 定位表达式、页面加载时机和截图中的目标元素是否变化。",
            "设备连接异常": "检查设备在线状态、端口、WDA/PocoService、ADB 连接和授权状态。",
            "应用启动或停止异常": "确认包名、activity、安装状态和设备权限是否正确。",
            "脚本断言失败": "核对断言预期与当前业务状态，必要时补充等待或测试数据准备。",
            "运行时异常": "查看 traceback 首个业务栈帧，优先修复脚本参数、空值和环境依赖。",
        }
        return suggestions.get(title, "请结合日志和截图继续排查。")

    @staticmethod
    def _build_summary(findings: List[Dict[str, str]]) -> str:
        first = findings[0]
        if first["type"] == "未发现明显失败特征":
            return first["suggestion"]
        return "初步判断为{0}。{1}".format(first["type"], first["suggestion"])
