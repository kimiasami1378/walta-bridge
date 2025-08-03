import os
import uuid
from typing import Dict

from bridge_api import BridgeClient, MockBridgeClient


class Walta:
    """Identity and payment facade built on top of Bridge.

    It issues DIDs to agents, creates Bridge wallets, and exposes helper
    methods so developers never interact with Bridge directly.
    """

    def __init__(self, bridge_client: BridgeClient | MockBridgeClient | None = None):
        """Create a Walta facade using the provided Bridge client."""
        self.bridge = bridge_client or BridgeClient()
        self.registry: Dict[str, Dict[str, str]] = {}

    def authenticate(self, agent_name: str) -> str:
        did = f"did:walta:{uuid.uuid4()}"
        wallet_id = self.bridge.create_wallet(did)
        self.registry[did] = {"name": agent_name, "wallet_id": wallet_id}
        return did

    def verify(self, did: str) -> bool:
        return did in self.registry

    def wallet_id(self, did: str) -> str:
        return self.registry[did]["wallet_id"]

    def fund(self, did: str, amount_usd: float):
        self.bridge.fund_wallet(self.wallet_id(did), amount_usd)

    def transfer(self, from_did: str, to_did: str, amount_usdc: float):
        self.bridge.transfer_usdc(self.wallet_id(from_did), self.wallet_id(to_did), amount_usdc)


class Agent:
    """Lightweight wrapper for interacting with Walta as an agent."""

    def __init__(self, name: str, walta: Walta):
        self.name = name
        self.walta = walta
        self.did = walta.authenticate(name)

    def verify_peer(self, peer_did: str) -> bool:
        return self.walta.verify(peer_did)

    def fund(self, amount_usd: float):
        self.walta.fund(self.did, amount_usd)

    def transfer_to(self, other: "Agent", amount_usdc: float):
        self.walta.transfer(self.did, other.did, amount_usdc)


def _select_bridge_client():
    if os.getenv("BRIDGE_API_KEY"):
        return BridgeClient()
    return MockBridgeClient()


if __name__ == "__main__":
    bridge = _select_bridge_client()
    walta = Walta(bridge)

    alice = Agent("alice", walta)
    bob = Agent("bob", walta)

    assert alice.verify_peer(bob.did)
    assert bob.verify_peer(alice.did)

    alice.fund(100)
    bob.fund(50)

    alice.transfer_to(bob, 30)

    if isinstance(bridge, MockBridgeClient):
        print(f"Alice USDC balance: {bridge.wallets[walta.wallet_id(alice.did)].usdc}")
        print(f"Bob USDC balance: {bridge.wallets[walta.wallet_id(bob.did)].usdc}")
    else:
        print("Transfer executed via Bridge sandbox. Query Bridge API for balances.")
