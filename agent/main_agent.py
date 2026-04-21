import asyncio
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, TypedDict

import yaml
from dotenv import load_dotenv
from workers.policy_tool import run as policy_run
from workers.retrieval import run as retrieval_run
from workers.synthesis import run as synthesis_run

load_dotenv(override=True)

# --- CONTRACT COMPLIANT TYPES ---
RouteName = Literal["retrieval_worker", "policy_tool_worker", "human_review"]


class AgentState(TypedDict):
    task: str
    supervisor_route: RouteName
    route_reason: str
    risk_high: bool
    needs_tool: bool
    retrieved_chunks: List[Dict[str, Any]]
    retrieved_sources: List[str]
    policy_result: Dict[str, Any]
    mcp_tools_used: List[Dict[str, Any]]
    final_answer: str
    sources: List[str]
    confidence: float
    history: List[str]
    workers_called: List[str]
    worker_io_logs: List[Dict[str, Any]]
    run_id: str
    timestamp: str
    llm_profiles: Dict[str, Any]
    retrieval_top_k: int


def save_trace(state: AgentState, output_dir: Optional[str] = None) -> str:
    output_dir = output_dir or os.getenv("TRACE_OUTPUT_DIR", "./artifacts/traces")
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"{state['run_id']}.json")
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(state, file, ensure_ascii=False, indent=2)
    return filename


class MainAgent:
    def __init__(self):
        self.name = "ExpertSupervisorAgent-v4"
        self.contract_path = Path("contracts/worker_contracts.yaml")
        self.routing_rules = self._load_routing_rules()

    def _load_routing_rules(self) -> List[Dict]:
        if not self.contract_path.exists():
            return []
        with open(self.contract_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("supervisor", {}).get("routing_rules", [])

    def supervisor_node(self, state: AgentState) -> AgentState:
        task_lower = state["task"].lower()
        selected_route = "retrieval_worker"
        reason = "Default route"

        for rule in self.routing_rules:
            condition = rule.get("condition", "").lower()
            clean_condition = condition.replace("task chứa", "").replace("'", "").replace('"', "")
            keywords = [k.strip() for k in clean_condition.split(",") if k.strip()]

            matched = [k for k in keywords if k in task_lower]
            if matched:
                selected_route = rule.get("route")
                reason = f"Matched YAML rules: {matched}"
                break

        state["supervisor_route"] = selected_route
        state["route_reason"] = reason
        state["needs_tool"] = selected_route == "policy_tool_worker"
        state["risk_high"] = any(k in task_lower for k in ["p1", "khẩn cấp"])
        return state

    async def query(self, question: str) -> Dict[str, Any]:
        profiles = self._get_llm_profiles()
        state: AgentState = {
            "task": question,
            "supervisor_route": "retrieval_worker",
            "route_reason": "",
            "risk_high": False,
            "needs_tool": False,
            "retrieved_chunks": [],
            "retrieved_sources": [],
            "policy_result": {},
            "mcp_tools_used": [],
            "final_answer": "",
            "sources": [],
            "confidence": 0.0,
            "history": [],
            "workers_called": [],
            "worker_io_logs": [],
            "run_id": f"run_{int(time.time() * 1000)}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "llm_profiles": profiles,
            "retrieval_top_k": int(os.getenv("RETRIEVAL_TOP_K", "5")),
        }

        state = self.supervisor_node(state)

        # 1. Retrieval
        state = await retrieval_run(state)

        # 2. Policy
        if state["supervisor_route"] == "policy_tool_worker":
            state = await policy_run(state)

        # 3. Synthesis
        state = await synthesis_run(state)

        # 4. Save Trace
        save_trace(state)

        return {
            "answer": state["final_answer"],
            "contexts": [c["text"] for c in state["retrieved_chunks"]],
            "retrieved_ids": [c.get("id", "") for c in state["retrieved_chunks"]],
            "metadata": {
                "run_id": state["run_id"],
                "route": state["supervisor_route"],
                "reason": state["route_reason"],
                "profiles": profiles,
            },
        }

    def _get_llm_profiles(self) -> dict:
        """SỬA LỖI: Lấy đúng provider và model cho từng role từ .env."""
        roles = ["supervisor", "retrieval", "synthesis", "policy"]
        profiles = {}
        for role in roles:
            provider = os.getenv(f"{role.upper()}_PROVIDER")
            model = os.getenv(f"{role.upper()}_MODEL")

            # Fallback nếu thiếu cấu hình
            if not provider or not model:
                if role == "retrieval":
                    provider, model = "openai", "text-embedding-3-small"
                else:
                    provider, model = "openai", "gpt-4o-mini"

            profiles[role] = {"provider": provider, "model": model}
        return profiles


if __name__ == "__main__":
    agent = MainAgent()

    async def main():
        resp = await agent.query("Chính sách hoàn tiền Flash Sale?")
        print(f"Result: {resp['answer']}")

    asyncio.run(main())
