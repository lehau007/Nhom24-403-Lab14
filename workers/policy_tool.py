import re
import asyncio
import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any

WORKER_NAME = "policy_tool_worker"

async def _call_mcp_tool(tool_name: str, tool_input: dict) -> dict:
    try:
        from mcp.client.sse import sse_client
        from mcp.client.session import ClientSession
        async with sse_client("http://127.0.0.1:8000/sse") as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=tool_input)
                return {
                    "tool": tool_name,
                    "input": tool_input,
                    "output": json.loads(result.content[0].text) if not result.isError else None,
                    "error": result.content[0].text if result.isError else None,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
    except Exception as e:
        return {
            "tool": tool_name, "input": tool_input, "output": None,
            "error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()
        }

def analyze_policy(task: str, chunks: list) -> dict:
    task_lower = task.lower()
    context_text = " ".join(chunk.get("text", "") for chunk in chunks).lower()
    exceptions_found = []

    # Detect exceptions defined in Contract
    if "flash sale" in task_lower or "flash sale" in context_text:
        exceptions_found.append({
            "type": "flash_sale_exception",
            "rule": "Đơn hàng Flash Sale không được hoàn tiền (Điều 3, chính sách v4).",
            "source": "policy_refund_v4.txt"
        })

    if any(kw in task_lower or kw in context_text for kw in ["license", "digital", "subscription", "kỹ thuật số"]):
        exceptions_found.append({
            "type": "digital_product_exception",
            "rule": "Sản phẩm kỹ thuật số hoặc subscription không được hoàn tiền (Điều 3).",
            "source": "policy_refund_v4.txt"
        })

    if any(kw in task_lower or kw in context_text for kw in ["đã kích hoạt", "activated", "đã sử dụng"]):
        exceptions_found.append({
            "type": "activated_product_exception",
            "rule": "Sản phẩm đã kích hoạt hoặc đã sử dụng không được hoàn tiền (Điều 3).",
            "source": "policy_refund_v4.txt"
        })

    return {
        "policy_applies": len(exceptions_found) == 0,
        "policy_name": "refund_policy_v4",
        "exceptions_found": exceptions_found,
        "policy_version_note": "Sử dụng phiên bản v4 hiệu lực từ 2026-02-01."
    }

async def run(state: dict) -> dict:
    task = state.get("task", "")
    chunks = state.get("retrieved_chunks", [])
    
    state.setdefault("workers_called", [])
    state.setdefault("worker_io_logs", [])
    state.setdefault("mcp_tools_used", [])
    state["workers_called"].append(WORKER_NAME)

    # 1. Core Policy Analysis
    policy_result = analyze_policy(task, chunks)
    state["policy_result"] = policy_result

    # 2. MCP Tool Integration (as required by Contract)
    task_lower = task.lower()
    if re.search(r"(it-\d+|p1-latest)", task_lower):
        mcp_res = await _call_mcp_tool("get_ticket_info", {"ticket_id": re.search(r"(it-\d+|p1-latest)", task_lower).group(0).upper()})
        state["mcp_tools_used"].append(mcp_res)

    if re.search(r"level\s*(\d)", task_lower):
        mcp_res = await _call_mcp_tool("check_access_permission", {
            "access_level": int(re.search(r"level\s*(\d)", task_lower).group(1)),
            "requester_role": "employee", "is_emergency": "emergency" in task_lower
        })
        state["mcp_tools_used"].append(mcp_res)

    # 3. Log I/O
    state["worker_io_logs"].append({
        "worker": WORKER_NAME,
        "input": {"task": task, "chunks_count": len(chunks)},
        "output": {
            "policy_applies": policy_result["policy_applies"],
            "exceptions_count": len(policy_result["exceptions_found"]),
            "mcp_tools_count": len(state["mcp_tools_used"])
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return state
