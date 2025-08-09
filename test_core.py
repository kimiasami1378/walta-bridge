#!/usr/bin/env python3
"""
Tests for Walta Core System
"""

import pytest
from unittest.mock import Mock, MagicMock
from walta_core import Walta, AgentIdentity, MCPMessage
from bridge_client import BridgeClient


class MockBridgeClient:
    """Mock Bridge client for testing."""
    
    def __init__(self):
        self.customers = {}
        self.wallets = {}
        self.balances = {}
    
    def create_customer(self, name: str) -> str:
        customer_id = f"cust_{len(self.customers) + 1}"
        self.customers[customer_id] = {"name": name}
        return customer_id
    
    def create_wallet(self, label: str, customer_id: str) -> str:
        wallet_id = f"wallet_{len(self.wallets) + 1}"
        self.wallets[wallet_id] = {"label": label, "customer_id": customer_id}
        self.balances[wallet_id] = {"usdc": 0.0}
        return wallet_id
    
    def fund_wallet(self, wallet_id: str, amount_usd: float) -> dict:
        if wallet_id in self.balances:
            self.balances[wallet_id]["usdc"] = amount_usd
        return {"status": "completed", "amount": amount_usd}
    
    def transfer_usdc(self, from_wallet: str, to_wallet: str, amount: float) -> dict:
        if from_wallet in self.balances and to_wallet in self.balances:
            if self.balances[from_wallet]["usdc"] >= amount:
                self.balances[from_wallet]["usdc"] -= amount
                self.balances[to_wallet]["usdc"] += amount
                return {"status": "completed", "amount": amount}
        raise ValueError("Insufficient funds or invalid wallets")
    
    def get_wallet_balance(self, wallet_id: str) -> dict:
        return self.balances.get(wallet_id, {"usdc": 0.0})


def test_walta_agent_authentication():
    """Test agent authentication and DID creation."""
    bridge = MockBridgeClient()
    walta = Walta(bridge)
    
    # Authenticate agent
    did = walta.authenticate("test_agent")
    
    # Verify DID format
    assert did.startswith("did:walta:")
    assert len(did) > 20
    
    # Verify identity exists
    assert walta.verify(did)
    identity = walta.get_identity(did)
    assert identity is not None
    assert identity.name == "test_agent"
    assert identity.verified


def test_walta_wallet_funding():
    """Test agent wallet funding."""
    bridge = MockBridgeClient()
    walta = Walta(bridge)
    
    # Create agent
    did = walta.authenticate("funded_agent")
    
    # Fund wallet
    result = walta.fund_agent(did, 100.0)
    assert result["status"] == "completed"
    
    # Check balance
    balance = walta.get_balance(did)
    assert balance["usdc"] == 100.0


def test_walta_usdc_transfer():
    """Test USDC transfer between agents."""
    bridge = MockBridgeClient()
    walta = Walta(bridge)
    
    # Create two agents
    alice_did = walta.authenticate("alice")
    bob_did = walta.authenticate("bob")
    
    # Fund Alice
    walta.fund_agent(alice_did, 200.0)
    
    # Transfer from Alice to Bob
    result = walta.transfer_between_agents(alice_did, bob_did, 50.0, "Payment for service")
    assert result["status"] == "completed"
    
    # Check balances
    alice_balance = walta.get_balance(alice_did)
    bob_balance = walta.get_balance(bob_did)
    
    assert alice_balance["usdc"] == 150.0
    assert bob_balance["usdc"] == 50.0


def test_mcp_messaging():
    """Test MCP message protocol."""
    bridge = MockBridgeClient()
    walta = Walta(bridge)
    
    # Create agents
    alice_did = walta.authenticate("alice")
    bob_did = walta.authenticate("bob")
    
    # Send MCP message
    success = walta.send_mcp_message(
        alice_did, 
        bob_did, 
        "service_request",
        {"service": "data_analysis", "amount": 50.0}
    )
    assert success
    
    # Check Bob received the message
    messages = walta.get_messages(bob_did, "service_request")
    assert len(messages) == 1
    assert messages[0].from_did == alice_did
    assert messages[0].type == "service_request"
    assert messages[0].payload["service"] == "data_analysis"
    
    # Clear messages
    walta.clear_messages(bob_did, "service_request")
    messages = walta.get_messages(bob_did, "service_request")
    assert len(messages) == 0


def test_identity_verification():
    """Test identity verification between agents."""
    bridge = MockBridgeClient()
    walta = Walta(bridge)
    
    # Create agent
    alice_did = walta.authenticate("alice")
    
    # Verify existing agent
    assert walta.verify(alice_did) == True
    
    # Verify non-existent agent
    fake_did = "did:walta:fake-id"
    assert walta.verify(fake_did) == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])