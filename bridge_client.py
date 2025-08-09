#!/usr/bin/env python3
"""
Bridge API Client for Real USDC Payments
Connects to Bridge sandbox for agent wallet management
"""

import os
import uuid
from typing import Dict, Any, Optional
import requests


class BridgeClient:
    """Real Bridge API client for USDC payments and wallet management."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("BRIDGE_API_KEY")
        self.base_url = os.getenv("BRIDGE_API_URL", "https://api.bridge.xyz/v0")
        
        if not self.api_key:
            raise ValueError("BRIDGE_API_KEY is required. Get it from https://dashboard.bridge.xyz/")
        
        self.session = requests.Session()
    
    def _headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        return {
            "Api-Key": self.api_key,
            "Content-Type": "application/json",
            "Idempotency-Key": str(uuid.uuid4())
        }
    
    def create_customer(self, agent_name: str) -> str:
        """Create Bridge customer for agent.
        
        Note: Sandbox may require a tax identification number. Provide a
        test SSN format for US to satisfy validation.
        """
        first = agent_name.split('_')[0].title()
        customer_data = {
            "type": "individual",
            "first_name": first,
            "last_name": "Agent",
            "email": f"{agent_name}@walta.ai",
            # Add minimal identifying info for sandbox KYC validation
            "identifying_information": {
                "tax_identification": {
                    "country": "US",
                    "type": "ssn",
                    "value": "123-45-6789"
                }
            }
        }
        
        resp = self.session.post(
            f"{self.base_url}/customers",
            json=customer_data,
            headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()["id"]
    
    def create_wallet(self, label: str, customer_id: str) -> str:
        """Create custodial wallet for agent.

        Bridge wallets are created via /wallets with on_behalf_of.
        """
        payload = {
            "label": label,
            "on_behalf_of": customer_id
        }
        resp = self.session.post(
            f"{self.base_url}/wallets",
            json=payload,
            headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()["id"]
    
    def fund_wallet(self, wallet_id: str, amount_usd: float, on_behalf_of: Optional[str] = None) -> Dict[str, Any]:
        """Fund wallet with USD -> USDC conversion."""
        transfer_data = {
            "source": {
                "payment_rail": "ach_push",
                "currency": "usd"
            },
            "destination": {
                "payment_rail": "bridge_wallet",
                "currency": "usdc",
                "bridge_wallet_id": wallet_id
            },
            "amount": str(amount_usd)
        }
        if on_behalf_of:
            transfer_data["on_behalf_of"] = on_behalf_of
        
        resp = self.session.post(
            f"{self.base_url}/transfers",
            json=transfer_data,
            headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()
    
    def transfer_usdc(self, from_wallet: str, to_wallet: str, amount: float, on_behalf_of: Optional[str] = None) -> Dict[str, Any]:
        """Transfer USDC between agent wallets."""
        transfer_data = {
            "source": {
                "payment_rail": "bridge_wallet",
                "currency": "usdc",
                "bridge_wallet_id": from_wallet
            },
            "destination": {
                "payment_rail": "bridge_wallet", 
                "currency": "usdc",
                "bridge_wallet_id": to_wallet
            },
            "amount": str(amount)
        }
        if on_behalf_of:
            transfer_data["on_behalf_of"] = on_behalf_of
        
        resp = self.session.post(
            f"{self.base_url}/transfers",
            json=transfer_data,
            headers=self._headers()
        )
        resp.raise_for_status()
        return resp.json()
    
    def get_wallet_balance(self, wallet_id: str) -> Dict[str, float]:
        """Get wallet balance."""
        resp = self.session.get(
            f"{self.base_url}/wallets/{wallet_id}",
            headers=self._headers()
        )
        resp.raise_for_status()
        
        data = resp.json()
        usdc_balance = next(
            (float(item['amount']) for item in data.get('balances', []) 
             if item['currency'] == 'usdc'), 
            0.0
        )
        
        return {"usdc": usdc_balance}