from walta_mvp import Walta, Agent
from bridge_api import MockBridgeClient


def test_payment_flow():
    """Ensure an authenticated transfer flows through Bridge."""
    bridge = MockBridgeClient()
    walta = Walta(bridge_client=bridge)
    alice = Agent('alice', walta)
    bob = Agent('bob', walta)

    assert alice.verify_peer(bob.did)
    assert bob.verify_peer(alice.did)

    alice.fund(100)
    bob.fund(50)
    alice.transfer_to(bob, 30)

    assert bridge.wallets[walta.wallet_id(alice.did)].usdc == 70
    assert bridge.wallets[walta.wallet_id(bob.did)].usdc == 80
