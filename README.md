# Agent MCP Payment Stable Demo


This repository shows an MVP flow where two agents authenticate through Walta and exchange USDC using Bridge's wallet APIs. For local testing the Bridge calls are mocked via `MockBridgeClient`, but providing a Bridge sandbox API key lets the demo talk to the real Bridge service.

## Running the demo

1. Copy `.env.example` to `.env` and set your `BRIDGE_API_KEY` (and optionally `BRIDGE_API_URL`).
2. `source .env` to load the environment variables.
3. Run the demo:


This repository shows an MVP flow where two agents authenticate through Walta and exchange USDC using Bridge's wallet APIs.  For local testing the Bridge calls are mocked via `MockBridgeClient`.

## Running the demo

```bash
python walta_mvp.py
```


If `BRIDGE_API_KEY` is set, Walta will automatically use the real Bridge sandbox; otherwise an in-memory `MockBridgeClient` is used.

To use the real Bridge sandbox set the environment variables `BRIDGE_API_URL` and `BRIDGE_API_KEY` and swap `MockBridgeClient` for `BridgeClient` in `walta_mvp.py`.

## Tests

```bash
pytest -q
```
