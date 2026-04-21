import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent
import uvicorn
import json
from datetime import datetime
from pathlib import Path

# Cấu hình đường dẫn dựa trên cấu trúc thực tế của Lab 14
BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "data" / "docs"
DATA_DIR = BASE_DIR / "data" / "mcp"
MOCK_TICKETS_FILE = DATA_DIR / "mock_tickets.json"
ACCESS_RULES_FILE = DATA_DIR / "access_rules.json"

def load_json(file_path: Path) -> dict:
    if not file_path.exists():
        print(f"Warning: {file_path} not found. Using empty mock data.")
        return {}
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

MOCK_TICKETS = load_json(MOCK_TICKETS_FILE)
ACCESS_RULES = load_json(ACCESS_RULES_FILE)

server = Server("lab14-mcp-server")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_kb",
            description="Tìm kiếm Knowledge Base nội bộ.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "default": 3},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_ticket_info",
            description="Tra cứu thông tin ticket Jira/Incident.",
            inputSchema={
                "type": "object",
                "properties": {"ticket_id": {"type": "string"}},
                "required": ["ticket_id"],
            },
        ),
        Tool(
            name="check_access_permission",
            description="Kiểm tra quyền truy cập hệ thống theo SOP.",
            inputSchema={
                "type": "object",
                "properties": {
                    "access_level": {"type": "integer"},
                    "requester_role": {"type": "string"},
                    "is_emergency": {"type": "boolean", "default": False},
                },
                "required": ["access_level", "requester_role"],
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent]:
    if not arguments:
        arguments = {}
        
    try:
        if name == "search_kb":
            query = arguments.get("query", "")
            top_k = arguments.get("top_k", 3)
            # Mock search logic
            query_terms = [term for term in query.lower().split() if len(term) > 2]
            scored_chunks = []

            if DOCS_DIR.exists():
                for file_path in DOCS_DIR.glob("*.txt"):
                    text = file_path.read_text(encoding="utf-8")
                    hits = sum(text.lower().count(term) for term in query_terms)
                    if hits > 0:
                        scored_chunks.append({
                            "text": text[:700],
                            "source": file_path.name,
                            "score": min(0.99, 0.3 + hits * 0.1)
                        })

            scored_chunks.sort(key=lambda x: x["score"], reverse=True)
            result = {"chunks": scored_chunks[:top_k], "total": len(scored_chunks)}
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        elif name == "get_ticket_info":
            ticket_id = str(arguments.get("ticket_id", "")).upper()
            ticket = MOCK_TICKETS.get(ticket_id)
            result = ticket if ticket else {"error": f"Ticket {ticket_id} không tồn tại."}
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        elif name == "check_access_permission":
            level = str(arguments.get("access_level"))
            is_emergency = arguments.get("is_emergency", False)
            rule = ACCESS_RULES.get(level)
            
            if not rule:
                result = {"error": "Level không hợp lệ"}
            else:
                can_grant = True
                if is_emergency and not rule.get("emergency_can_bypass", False):
                    if int(level) >= 3: can_grant = False
                
                result = {
                    "can_grant": can_grant,
                    "approvers": rule.get("required_approvers", []),
                    "notes": rule.get("emergency_bypass_note", "") if is_emergency else ""
                }
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

sse = SseServerTransport("/messages")
app = FastAPI(title="MCP Server Lab 14")

@app.get("/sse")
async def handle_sse(request):
    from starlette.requests import Request
    req = Request(request.scope, request.receive)
    async with sse.connect_sse(req.scope, req.receive, req._send) as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())

@app.post("/messages")
async def handle_messages(request):
    from starlette.requests import Request
    req = Request(request.scope, request.receive)
    await sse.handle_post_message(req.scope, req.receive, req._send)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
