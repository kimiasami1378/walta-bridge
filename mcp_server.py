#!/usr/bin/env python3
"""
Walta MCP Server - Model Context Protocol for AI Agent Communication
"""

import asyncio
import json
import uuid
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import websockets
from websockets.server import WebSocketServerProtocol

from walta_core import Walta


@dataclass
class MCPRequest:
    """MCP protocol request."""
    jsonrpc: str
    id: str
    method: str
    params: Dict[str, Any]


@dataclass
class MCPResponse:
    """MCP protocol response."""
    jsonrpc: str
    id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class WaltaMCPServer:
    """MCP server for Walta agent communication."""
    
    def __init__(self, walta: Walta, host: str = "localhost", port: int = 8765):
        self.walta = walta
        self.host = host
        self.port = port
        self.connected_agents: Dict[str, WebSocketServerProtocol] = {}
        self.agent_sessions: Dict[str, str] = {}  # websocket_id -> agent_did
    
    async def handle_request(self, websocket: WebSocketServerProtocol, request: MCPRequest) -> MCPResponse:
        """Handle incoming MCP requests."""
        
        try:
            if request.method == "walta.register":
                return await self.handle_register(websocket, request)
            elif request.method == "walta.verify_identity":
                return await self.handle_verify_identity(request)
            elif request.method == "walta.request_service":
                return await self.handle_request_service(websocket, request)
            elif request.method == "walta.accept_service":
                return await self.handle_accept_service(request)
            elif request.method == "walta.get_balance":
                return await self.handle_get_balance(request)
            else:
                return MCPResponse(
                    jsonrpc="2.0",
                    id=request.id,
                    error={"code": -32601, "message": f"Method not found: {request.method}"}
                )
        except Exception as e:
            return MCPResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32603, "message": f"Internal error: {str(e)}"}
            )
    
    async def handle_register(self, websocket: WebSocketServerProtocol, request: MCPRequest) -> MCPResponse:
        """Register agent and create identity."""
        agent_name = request.params.get("agent_name")
        if not agent_name:
            return MCPResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "Missing agent_name"}
            )
        
        # Create agent identity in Walta
        agent_did = self.walta.authenticate(agent_name)
        
        # Register websocket connection
        self.connected_agents[agent_did] = websocket
        self.agent_sessions[id(websocket)] = agent_did
        
        return MCPResponse(
            jsonrpc="2.0",
            id=request.id,
            result={"agent_did": agent_did, "status": "registered"}
        )
    
    async def handle_verify_identity(self, request: MCPRequest) -> MCPResponse:
        """Handle identity verification."""
        target_did = request.params.get("target_did")
        if not target_did:
            return MCPResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "Missing target_did"}
            )
        
        verified = self.walta.verify(target_did)
        identity = self.walta.get_identity(target_did) if verified else None
        
        return MCPResponse(
            jsonrpc="2.0",
            id=request.id,
            result={
                "verified": verified,
                "identity": identity.to_dict() if identity else None
            }
        )
    
    async def handle_request_service(self, websocket: WebSocketServerProtocol, request: MCPRequest) -> MCPResponse:
        """Handle service requests."""
        params = request.params
        provider_did = params.get("provider_did")
        service_name = params.get("service_name")
        offered_amount = params.get("offered_amount")
        
        if not all([provider_did, service_name, offered_amount]):
            return MCPResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "Missing parameters"}
            )
        
        # Determine requester DID from the websocket session
        requester_did = self.agent_sessions.get(id(websocket))
        success = self.walta.send_mcp_message(
            requester_did,
            provider_did,
            "service_request",
            {"service_name": service_name, "offered_amount": offered_amount}
        )
        
        return MCPResponse(
            jsonrpc="2.0",
            id=request.id,
            result={"service_requested": success}
        )
    
    async def handle_accept_service(self, request: MCPRequest) -> MCPResponse:
        """Handle service acceptance and payment."""
        params = request.params
        provider_did = params.get("provider_did")
        requester_did = params.get("requester_did")
        service_name = params.get("service_name")
        amount = params.get("amount")
        
        if not all([provider_did, requester_did, service_name, amount]):
            return MCPResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "Missing parameters"}
            )
        
        try:
            # Process payment
            transfer_result = self.walta.transfer_between_agents(
                requester_did, provider_did, amount, f"Payment for {service_name}"
            )
            
            return MCPResponse(
                jsonrpc="2.0",
                id=request.id,
                result={"payment_processed": True, "transfer_result": transfer_result}
            )
        except Exception as e:
            return MCPResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32603, "message": f"Payment failed: {str(e)}"}
            )
    
    async def handle_get_balance(self, request: MCPRequest) -> MCPResponse:
        """Handle balance requests."""
        agent_did = request.params.get("agent_did")
        if not agent_did:
            return MCPResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32602, "message": "Missing agent_did"}
            )
        
        try:
            balance = self.walta.get_balance(agent_did)
            return MCPResponse(
                jsonrpc="2.0",
                id=request.id,
                result={"balance": balance}
            )
        except Exception as e:
            return MCPResponse(
                jsonrpc="2.0",
                id=request.id,
                error={"code": -32603, "message": f"Balance query failed: {str(e)}"}
            )
    
    async def handle_client(self, websocket: WebSocketServerProtocol):
        """Handle websocket client connections."""
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    request = MCPRequest(**data)
                    response = await self.handle_request(websocket, request)
                    await websocket.send(json.dumps(asdict(response)))
                except json.JSONDecodeError:
                    error_response = MCPResponse(
                        jsonrpc="2.0",
                        id="",
                        error={"code": -32700, "message": "Parse error"}
                    )
                    await websocket.send(json.dumps(asdict(error_response)))
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            # Cleanup connection
            session_id = id(websocket)
            if session_id in self.agent_sessions:
                agent_did = self.agent_sessions[session_id]
                self.connected_agents.pop(agent_did, None)
                self.agent_sessions.pop(session_id, None)
    
    async def start_server(self):
        """Start the MCP server."""
        # websockets.serve passes (websocket) in modern versions; to be compatible with versions
        # that pass (websocket, path), wrap the handler.
        async def _handler(websocket, *args):
            await self.handle_client(websocket)

        server = await websockets.serve(
            _handler,
            self.host,
            self.port
        )
        return server