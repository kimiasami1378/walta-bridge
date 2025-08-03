# MVP Plan

1. **Identity via Walta**
   - Each agent authenticates through Walta to obtain a DID.
   - Agents verify peers by checking the DID against Walta's registry.

2. **Wallets and Funding via Bridge**
   - Developers provision wallets for their agents through Bridge's sandbox API (`BridgeClient`).
   - Funding a wallet with USD automatically mints the same amount of USDC.

3. **Agent Communication**
   - Agents communicate through MCP, exchange DIDs and verify identities.

4. **Stablecoin Transfers**
   - After verification, agents transfer USDC between Bridge wallets to settle payments.
   - Example: Agent A pays Agent B for API services.

This MVP uses `MockBridgeClient` for local testing but can call the real Bridge API by using `BridgeClient` with proper credentials.
