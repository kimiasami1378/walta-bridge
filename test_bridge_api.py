from bridge_api import BridgeClient


class DummyResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


class DummySession:
    def __init__(self):
        self.last_request = None

    def post(self, url, json=None, headers=None):
        self.last_request = {"url": url, "json": json, "headers": headers}
        if url.endswith("/wallets"):
            return DummyResponse({"id": "w1"})
        if url.endswith("/wallets/w1/fund"):
            return DummyResponse({"wallet_id": "w1", "usd": json["amount"], "usdc": json["amount"]})
        if url.endswith("/transfers"):
            return DummyResponse({"tx": "1"})
        raise AssertionError("unexpected url" + url)


def test_bridge_client_calls_correct_endpoints():
    session = DummySession()
    client = BridgeClient(base_url="https://bridge", api_key="k", session=session)

    wallet_id = client.create_wallet("agent")
    assert wallet_id == "w1"
    assert session.last_request["url"] == "https://bridge/wallets"
    assert session.last_request["headers"]["Authorization"] == "Bearer k"

    client.fund_wallet("w1", 10)
    assert session.last_request["url"] == "https://bridge/wallets/w1/fund"
    assert session.last_request["json"] == {"amount": 10, "currency": "USD"}

    client.transfer_usdc("w1", "w2", 5)
    assert session.last_request["url"] == "https://bridge/transfers"
    assert session.last_request["json"]["from"] == "w1"
    assert session.last_request["json"]["to"] == "w2"
    assert session.last_request["json"]["amount"] == 5
