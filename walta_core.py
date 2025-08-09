#!/usr/bin/env python3
"""
Walta Core - Identity and Payment Infrastructure for AI Agents
Built on top of Bridge API for real USDC transactions
"""

import os
import uuid
import json
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

from bridge_client import BridgeClient


@dataclass
class AgentIdentity:
    """Decentralized Identity for AI agents."""
    did: str
    name: str
    wallet_id: str
    customer_id: str
    created_at: datetime
    verified: bool = True
    
    def to_dict(self) -> dict:
        result = asdict(self)
        result['created_at'] = self.created_at.isoformat()
        return result


@dataclass
class MCPMessage:
    """Message format for MCP protocol communication."""
    from_did: str
    to_did: str
    type: str
    payload: dict
    timestamp: datetime
    
    def to_dict(self) -> dict:
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


class Walta:
    """Identity and payment infrastructure for autonomous agents built on Bridge."""
    
    def __init__(self, bridge_client: Optional[BridgeClient] = None):
        """Initialize Walta with Bridge integration."""
        self.bridge = bridge_client or BridgeClient()
        self.registry: Dict[str, AgentIdentity] = {}  # DID -> Identity
        self.message_queue: Dict[str, List[MCPMessage]] = {}  # DID -> Messages
        
    def authenticate(self, agent_name: str) -> str:
        """Authenticate agent and create DID with Bridge wallet.
        
        If WALTA_CUSTOMER_ID is set in the environment, use that existing
        Bridge customer instead of creating a new one (useful for sandbox
        where KYC requirements are enforced).
        """
        # Create DID
        did = f"did:walta:{uuid.uuid4()}"
        
        # Create or reuse Bridge customer, then create wallet
        existing_customer_id = os.getenv("WALTA_CUSTOMER_ID")
        if existing_customer_id:
            customer_id = existing_customer_id
        else:
            customer_id = self.bridge.create_customer(agent_name)
        wallet_id = self.bridge.create_wallet(f"{agent_name}_wallet", customer_id)
        
        # Create identity
        identity = AgentIdentity(
            did=did,
            name=agent_name,
            wallet_id=wallet_id,
            customer_id=customer_id,
            created_at=datetime.now(timezone.utc),
            verified=True
        )
        
        self.registry[did] = identity
        self.message_queue[did] = []
        
        return did
    
    def verify(self, did: str) -> bool:
        """Verify if DID exists and is valid."""
        return did in self.registry and self.registry[did].verified
    
    def get_identity(self, did: str) -> Optional[AgentIdentity]:
        """Get agent identity by DID."""
        return self.registry.get(did)
    
    def fund_agent(self, did: str, amount_usd: float) -> dict:
        """Fund agent wallet with USD -> USDC conversion."""
        identity = self.registry[did]
        return self.bridge.fund_wallet(identity.wallet_id, amount_usd, on_behalf_of=identity.customer_id)
    
    def transfer_between_agents(self, from_did: str, to_did: str, amount_usdc: float, memo: str = "") -> dict:
        """Transfer USDC between agent wallets."""
        from_identity = self.registry[from_did]
        to_identity = self.registry[to_did]
        
        return self.bridge.transfer_usdc(
            from_identity.wallet_id,
            to_identity.wallet_id,
            amount_usdc,
            on_behalf_of=from_identity.customer_id
        )
    
    def get_balance(self, did: str) -> dict:
        """Get agent wallet balance."""
        identity = self.registry[did]
        return self.bridge.get_wallet_balance(identity.wallet_id)
    
    # MCP Protocol Methods
    def send_mcp_message(self, from_did: str, to_did: str, message_type: str, payload: dict) -> bool:
        """Send MCP message between agents."""
        if not (self.verify(from_did) and self.verify(to_did)):
            return False
        
        message = MCPMessage(
            from_did=from_did,
            to_did=to_did,
            type=message_type,
            payload=payload,
            timestamp=datetime.now(timezone.utc)
        )
        
        if to_did not in self.message_queue:
            self.message_queue[to_did] = []
        
        self.message_queue[to_did].append(message)
        return True
    
    def get_messages(self, did: str, message_type: Optional[str] = None) -> List[MCPMessage]:
        """Get messages for agent."""
        if did not in self.message_queue:
            return []
        
        messages = self.message_queue[did]
        if message_type:
            messages = [msg for msg in messages if msg.type == message_type]
        
        return messages
    
    def clear_messages(self, did: str, message_type: Optional[str] = None):
        """Clear messages for agent."""
        if did not in self.message_queue:
            return
        
        if message_type:
            self.message_queue[did] = [msg for msg in self.message_queue[did] if msg.type != message_type]
        else:
            self.message_queue[did] = []