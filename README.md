# Agent MCP Payment Stable Demo

This repository shows an MVP flow where two agents authenticate through Walta and exchange USDC using Bridge's wallet APIs.  For local testing the Bridge calls are mocked via `MockBridgeClient`.

## Running the demo

```bash
python walta_mvp.py
```

To use the real Bridge sandbox set the environment variables `BRIDGE_API_URL` and `BRIDGE_API_KEY` and swap `MockBridgeClient` for `BridgeClient` in `walta_mvp.py`.

## Tests

```bash
pytest -q
```
