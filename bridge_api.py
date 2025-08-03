import os
import uuid
from dataclasses import dataclass
from typing import Dict, Any

try:
    import requests
except ModuleNotFoundError:  # requests is optional for tests
    requests = None


class BridgeClient:
    """Simple wrapper around Bridge sandbox HTTP API.

    Parameters are read from environment variables:
    - BRIDGE_API_URL: base URL for the Bridge sandbox (default used if unset)
    - BRIDGE_API_KEY: API key for authentication
    """

    def __init__(self, base_url: str | None = None, api_key: str | None = None, session=None):
        self.base_url = base_url or os.getenv("BRIDGE_API_URL", "https://api.bridge-sandbox.example")
        self.api_key = api_key or os.getenv("BRIDGE_API_KEY")
        if session is not None:
            self.session = session
        elif requests is not None:
            self.session = requests.Session()
        else:  # pragma: no cover - only triggered when requests missing
            raise RuntimeError("requests is required for HTTP operations")

    def _headers(self) -> Dict[str, str]:
        if not self.api_key:
            raise RuntimeError("BRIDGE_API_KEY not configured")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def create_wallet(self, label: str) -> str:
        """Create a new wallet for an agent."""
        resp = self.session.post(
            f"{self.base_url}/wallets",
            json={"label": label},
            headers=self._headers(),
        )
        resp.raise_for_status()
        data: Dict[str, Any] = resp.json()
        return data["id"]

    def fund_wallet(self, wallet_id: str, amount_usd: float) -> Dict[str, Any]:
        """Fund a wallet with USD that is auto-converted to USDC."""
        payload = {"amount": amount_usd, "currency": "USD"}
        resp = self.session.post(
            f"{self.base_url}/wallets/{wallet_id}/fund",
            json=payload,
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def transfer_usdc(self, from_wallet: str, to_wallet: str, amount: float) -> Dict[str, Any]:
        payload = {
            "from": from_wallet,
            "to": to_wallet,
            "amount": amount,
            "currency": "USDC",
        }
        resp = self.session.post(
            f"{self.base_url}/transfers",
            json=payload,
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()


@dataclass
class BridgeWallet:
    usd: float = 0.0
    usdc: float = 0.0


class MockBridgeClient:
    """In-memory stand-in for BridgeClient used in tests and demo."""

    def __init__(self):
        self.wallets: Dict[str, BridgeWallet] = {}

    def create_wallet(self, label: str) -> str:
        wallet_id = str(uuid.uuid4())
        self.wallets[wallet_id] = BridgeWallet()
        return wallet_id

    def fund_wallet(self, wallet_id: str, amount_usd: float) -> Dict[str, Any]:
        wallet = self.wallets[wallet_id]
        wallet.usd += amount_usd
        # convert 1:1 for simplicity
        wallet.usdc += amount_usd
        return {"wallet_id": wallet_id, "usd": wallet.usd, "usdc": wallet.usdc}

    def transfer_usdc(self, from_wallet: str, to_wallet: str, amount: float) -> Dict[str, Any]:
        sender = self.wallets[from_wallet]
        receiver = self.wallets[to_wallet]
        if sender.usdc < amount:
            raise ValueError("Insufficient USDC balance")
        sender.usdc -= amount
        receiver.usdc += amount
        return {"from": from_wallet, "to": to_wallet, "amount": amount}
