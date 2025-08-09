#!/usr/bin/env python3
"""
Walta AI Agent Autonomous Commerce Demo
Real LLM agents using MCP protocol for identity and USDC payments
"""

import os
import asyncio
import logging
from typing import List

from walta_core import Walta
from bridge_client import BridgeClient
from mcp_server import WaltaMCPServer
from ai_agents import AIAgent, create_data_scientist_agent, create_content_creator_agent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


async def start_walta_infrastructure() -> tuple[Walta, WaltaMCPServer]:
    """Initialize Walta infrastructure with Bridge integration."""
    logger.info("🏗️ Initializing Walta infrastructure...")
    
    # Initialize Bridge client
    bridge_client = BridgeClient()
    
    # Initialize Walta
    walta = Walta(bridge_client)
    
    # Start MCP server
    mcp_server = WaltaMCPServer(walta)
    server = await mcp_server.start_server()
    
    logger.info("✅ Walta MCP server running on ws://localhost:8765")
    
    # Give server time to start
    await asyncio.sleep(1)
    
    return walta, mcp_server


async def create_ai_agents(openai_api_key: str) -> List[AIAgent]:
    """Create and connect AI agents."""
    logger.info("🤖 Creating LLM-powered AI agents...")
    
    # Create agents with different personalities
    alice = create_data_scientist_agent("alice_data_scientist", openai_api_key)
    bob = create_content_creator_agent("bob_content_creator", openai_api_key)
    
    # Connect to Walta MCP server
    await alice.connect_to_walta()
    await bob.connect_to_walta()
    
    logger.info(f"✅ Alice connected: {alice.agent_did[:20]}...")
    logger.info(f"✅ Bob connected: {bob.agent_did[:20]}...")
    
    return [alice, bob]


async def fund_agents(walta: Walta, agents: List[AIAgent]):
    """Fund agent wallets with USDC."""
    logger.info("💰 Funding agent wallets (USD -> USDC)...")
    
    for agent in agents:
        amount = 200.0 if "data_scientist" in agent.name else 150.0
        walta.fund_agent(agent.agent_did, amount)
        
        balance = walta.get_balance(agent.agent_did)
        logger.info(f"✅ {agent.name}: ${balance['usdc']} USDC")


async def demonstrate_autonomous_commerce(agents: List[AIAgent]) -> bool:
    """Demonstrate autonomous agent commerce workflow."""
    logger.info("\n🧠 AUTONOMOUS AI AGENT COMMERCE DEMO")
    logger.info("=" * 50)
    
    alice, bob = agents
    
    # Phase 1: Identity Verification
    logger.info("\n🔐 Phase 1: AI Identity Verification")
    logger.info("Alice evaluating whether to verify Bob's identity...")
    
    alice_verified_bob = await alice.verify_peer_identity(bob.agent_did)
    
    if alice_verified_bob:
        logger.info("✅ Alice verified Bob's identity via Walta DID")
    else:
        logger.info("❌ Alice declined to verify Bob")
        return False
    
    # Phase 2: Service Discovery and Purchase
    logger.info("\n🛒 Phase 2: AI Service Commerce")
    logger.info("Bob evaluating whether to request data analysis service from Alice...")
    
    bob_requested_service = await bob.request_service(
        alice.agent_did,
        "data_analysis",
        max_budget=75.0
    )
    
    if bob_requested_service:
        logger.info("✅ Bob requested data analysis service")
        
        # Give Alice time to process the request
        await asyncio.sleep(2)
        
        # Alice evaluates and potentially accepts the service request
        logger.info("Alice evaluating Bob's service request...")
        
        # Check if Alice received the service request
        alice_status = await alice.get_status()
        if alice_status.get("pending_messages", 0) > 0:
            # Alice autonomously evaluates the service request
            alice_accepted = await alice.evaluate_service_request(
                bob.agent_did, "data_analysis", 75.0
            )
            
            if alice_accepted:
                logger.info("✅ Alice accepted service and processed payment")
                return True
            else:
                logger.info("❌ Alice declined the service request")
                return False
        else:
            logger.info("⚠️ Service request not received")
            return False
    else:
        logger.info("❌ Bob declined to request service")
        return False


async def show_final_results(walta: Walta, agents: List[AIAgent]):
    """Show final agent status and balances."""
    logger.info("\n📊 FINAL RESULTS")
    logger.info("=" * 30)
    
    for agent in agents:
        status = await agent.get_status()
        balance = status.get("balance", {})
        decisions = status.get("decisions_made", 0)
        
        logger.info(f"\n🤖 {agent.name}:")
        logger.info(f"   DID: {agent.agent_did[:25]}...")
        logger.info(f"   Role: {status['role']}")
        logger.info(f"   Balance: ${balance.get('usdc', 0)} USDC")
        logger.info(f"   AI Decisions Made: {decisions}")
        
        # Show recent decisions
        if agent.decision_history:
            recent_decision = agent.decision_history[-1]
            logger.info(f"   Last Decision: {recent_decision['decision']}")
            logger.info(f"   Reasoning: {recent_decision['reasoning'][:80]}...")


async def main():
    """Main demo execution."""
    print("🚀 WALTA AI AGENT AUTONOMOUS COMMERCE")
    print("Real LLM agents • MCP Protocol • Bridge USDC Payments")
    print("=" * 60)
    
    # Check requirements
    openai_api_key = os.getenv("OPENAI_API_KEY")
    bridge_api_key = os.getenv("BRIDGE_API_KEY")
    
    if not openai_api_key:
        logger.error("❌ OPENAI_API_KEY required. Set in .env file or environment.")
        logger.info("Get your key from: https://platform.openai.com/api-keys")
        return
    
    if not bridge_api_key:
        logger.error("❌ BRIDGE_API_KEY required. Set in .env file or environment.")
        logger.info("Get your key from: https://dashboard.bridge.xyz/ (Sandbox)")
        return
    
    try:
        # Step 1: Initialize infrastructure
        walta, mcp_server = await start_walta_infrastructure()
        
        # Step 2: Create AI agents
        agents = await create_ai_agents(openai_api_key)
        
        # Step 3: Fund agents
        await fund_agents(walta, agents)
        
        # Step 4: Demonstrate autonomous commerce
        success = await demonstrate_autonomous_commerce(agents)
        
        # Step 5: Show results
        await show_final_results(walta, agents)
        
        # Final summary
        print("\n" + "=" * 60)
        if success:
            print("🎉 AUTONOMOUS COMMERCE SUCCESSFUL!")
            print("✅ Real LLM agents made autonomous decisions")
            print("✅ Identity verification via Walta DID")
            print("✅ Service commerce via MCP protocol")
            print("✅ USDC payments via Bridge API")
        else:
            print("⚠️ Commerce flow incomplete - check agent decisions")
        
        print("\n💡 Key Technologies Demonstrated:")
        print("   🧠 OpenAI GPT-4 autonomous reasoning")
        print("   🆔 Walta decentralized identity (DID)")
        print("   🔗 Model Context Protocol (MCP)")
        print("   💰 Bridge USDC stablecoin payments")
        print("   🤖 Truly autonomous agent commerce")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        # python-dotenv not installed, environment variables should be set manually
        pass
    
    asyncio.run(main())