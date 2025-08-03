import uuid
from bridge_api import MockBridgeClient, BridgeClient  # BridgeClient imported for real usage


class Walta:
    def __init__(self):
        self.registry = {}

    def authenticate(self, agent_name: str) -> str:
        did = f"did:walta:{uuid.uuid4()}"
        self.registry[did] = agent_name
        return did

    def verify(self, did: str) -> bool:
        return did in self.registry


class Agent:
    def __init__(self, name: str, walta: Walta, bridge_client: MockBridgeClient):
        self.name = name
        self.walta = walta
        self.did = self.walta.authenticate(name)
        self.bridge = bridge_client
        self.wallet_id = self.bridge.create_wallet(self.did)

    def verify_peer(self, peer_did: str) -> bool:
        return self.walta.verify(peer_did)

    def fund(self, amount_usd: float):
        self.bridge.fund_wallet(self.wallet_id, amount_usd)

    def transfer_to(self, other: "Agent", amount_usdc: float):
        self.bridge.transfer_usdc(self.wallet_id, other.wallet_id, amount_usdc)


if __name__ == "__main__":
    walta = Walta()
    bridge = MockBridgeClient()

    alice = Agent("alice", walta, bridge)
    bob = Agent("bob", walta, bridge)

    assert alice.verify_peer(bob.did)
    assert bob.verify_peer(alice.did)

    alice.fund(100)
    bob.fund(50)

    alice.transfer_to(bob, 30)

    print(f"Alice USDC balance: {bridge.wallets[alice.wallet_id].usdc}")
    print(f"Bob USDC balance: {bridge.wallets[bob.wallet_id].usdc}")
