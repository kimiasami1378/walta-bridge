#!/usr/bin/env python3
"""
Real MCP (Model Context Protocol) Client for AI Agents
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, Any, Optional, Callable
import websockets
from websockets.client import WebSocketClientProtocol

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPClient:
    """Real MCP Client for AI agent communication."""
    
    def __init__(self, server_url: str = "ws://localhost:8765"):
        self.server_url = server_url
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.agent_did: Optional[str] = None
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.connected = False
        
    async def connect(self):
        """Connect to the MCP server."""
        try:
            logger.info(f"🔗 Connecting to MCP server: {self.server_url}")
            self.websocket = await websockets.connect(self.server_url)
            self.connected = True
            logger.info("✅ Connected to MCP server")
            
            # Start message listener
            asyncio.create_task(self._listen_for_messages())
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MCP server: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info("🔌 Disconnected from MCP server")
    
    async def _listen_for_messages(self):
        """Listen for incoming messages from the MCP server."""
        try:
            async for message in self.websocket:
                await self._handle_message(json.loads(message))
        except websockets.exceptions.ConnectionClosed:
            logger.info("🔌 MCP connection closed")
            self.connected = False
        except Exception as e:
            logger.error(f"❌ Error in message listener: {e}")
    
    async def _handle_message(self, data: Dict[str, Any]):
        """Handle incoming messages."""
        if "id" in data and data["id"] in self.pending_requests:
            # Response to a request
            future = self.pending_requests.pop(data["id"])
            future.set_result(data)
        elif "method" in data:
            # Notification or method call
            method = data["method"]
            if method in self.message_handlers:
                await self.message_handlers[method](data.get("params", {}))
            else:
                logger.info(f"📨 Unhandled notification: {method}")
    
    def register_handler(self, method: str, handler: Callable):
        """Register a handler for incoming method calls."""
        self.message_handlers[method] = handler
    
    async def _send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a request and wait for response."""
        if not self.connected or not self.websocket:
            raise ConnectionError("Not connected to MCP server")
        
        request_id = str(uuid.uuid4())
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {}
        }
        
        # Create future for response
        future = asyncio.Future()
        self.pending_requests[request_id] = future
        
        # Send request
        await self.websocket.send(json.dumps(request))
        
        # Wait for response
        try:
            response = await asyncio.wait_for(future, timeout=30.0)
            
            if "error" in response:
                raise Exception(f"MCP Error: {response['error']}")
            
            return response.get("result", {})
            
        except asyncio.TimeoutError:
            self.pending_requests.pop(request_id, None)
            raise TimeoutError(f"MCP request timeout: {method}")
    
    async def register_agent(self, agent_name: str) -> str:
        """Register agent with the MCP server."""
        logger.info(f"🔐 Registering agent: {agent_name}")
        
        result = await self._send_request("walta.register", {
            "agent_name": agent_name
        })
        
        self.agent_did = result["agent_did"]
        logger.info(f"✅ Agent registered with DID: {self.agent_did[:20]}...")
        
        return self.agent_did
    
    async def authenticate_agent(self, agent_name: str) -> Dict[str, Any]:
        """Authenticate agent and get identity."""
        logger.info(f"🔐 Authenticating agent: {agent_name}")
        
        result = await self._send_request("walta.authenticate", {
            "agent_name": agent_name
        })
        
        if not self.agent_did:
            self.agent_did = result["agent_did"]
        
        return result
    
    async def verify_identity(self, target_did: str) -> Dict[str, Any]:
        """Verify another agent's identity."""
        logger.info(f"🔍 Verifying identity: {target_did[:20]}...")
        
        return await self._send_request("walta.verify_identity", {
            "target_did": target_did
        })
    
    async def request_service(self, provider_did: str, service_name: str, offered_amount: float) -> Dict[str, Any]:
        """Request a service from another agent."""
        logger.info(f"🛒 Requesting service: {service_name} from {provider_did[:20]}... for ${offered_amount}")
        
        return await self._send_request("walta.request_service", {
            "provider_did": provider_did,
            "service_name": service_name,
            "offered_amount": offered_amount
        })
    
    async def accept_service(self, requester_did: str, service_name: str, amount: float) -> Dict[str, Any]:
        """Accept a service request and process payment."""
        logger.info(f"✅ Accepting service: {service_name} from {requester_did[:20]}... for ${amount}")
        
        return await self._send_request("walta.accept_service", {
            "provider_did": self.agent_did,
            "requester_did": requester_did,
            "service_name": service_name,
            "amount": amount
        })
    
    async def transfer_funds(self, to_did: str, amount: float, memo: str = "") -> Dict[str, Any]:
        """Transfer funds to another agent."""
        logger.info(f"💸 Transferring ${amount} to {to_did[:20]}...")
        
        return await self._send_request("walta.transfer_funds", {
            "from_did": self.agent_did,
            "to_did": to_did,
            "amount": amount,
            "memo": memo
        })
    
    async def get_balance(self) -> Dict[str, Any]:
        """Get current wallet balance."""
        return await self._send_request("walta.get_balance", {
            "agent_did": self.agent_did
        })
    
    async def get_messages(self, message_type: str = None) -> Dict[str, Any]:
        """Get pending messages."""
        return await self._send_request("walta.get_messages", {
            "agent_did": self.agent_did,
            "message_type": message_type
        })
    
    async def fund_wallet(self, amount_usd: float):
        """Fund the agent's wallet (this would typically be done through the Bridge API directly)."""
        # This is a placeholder - in a real system, wallet funding would be done
        # through the Bridge API directly or through a separate funding service
        logger.info(f"💰 Funding wallet with ${amount_usd} USD (placeholder)")
        # For now, just log - the actual funding would be handled by the Walta system

# Usage example and testing
async def test_mcp_client():
    """Test the MCP client functionality."""
    client = MCPClient()
    
    try:
        # Connect to server
        await client.connect()
        
        # Register agent
        agent_did = await client.register_agent("test_agent")
        
        # Get balance
        balance = await client.get_balance()
        print(f"Balance: {balance}")
        
        # Get messages
        messages = await client.get_messages()
        print(f"Messages: {messages}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_mcp_client())