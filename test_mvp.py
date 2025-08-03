from walta_mvp import Walta, Agent
from bridge_api import MockBridgeClient


def test_payment_flow():
    walta = Walta()
    bridge = MockBridgeClient()
    alice = Agent('alice', walta, bridge)
    bob = Agent('bob', walta, bridge)

    assert alice.verify_peer(bob.did)
    assert bob.verify_peer(alice.did)

    alice.fund(100)
    bob.fund(50)

    alice.transfer_to(bob, 30)

    assert bridge.wallets[alice.wallet_id].usdc == 70
    assert bridge.wallets[bob.wallet_id].usdc == 80
