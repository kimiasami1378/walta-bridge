# 🤖 Walta AI Agent Autonomous Commerce

**Real LLM-powered agents using Walta MCP for identity and Bridge API for USDC payments**

## 🎯 Overview

This is a production-ready system where AI agents autonomously:
- Verify each other's identities using Walta DIDs (decentralized identities)
- Communicate via MCP (Model Context Protocol) 
- Purchase services from each other using real USDC stablecoins
- Make decisions using OpenAI GPT-4 reasoning

## 🏗️ Architecture

```
AI Agent A (GPT-4) ←→ Walta MCP Server ←→ AI Agent B (GPT-4)
                             ↓
                      Walta Identity (DIDs)
                             ↓
                      Bridge API (USDC)
```

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Copy environment template
cp env_template.txt .env

# Edit .env with your API keys:
# OPENAI_API_KEY=your_openai_key
# BRIDGE_API_KEY=your_bridge_sandbox_key
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Demo
```bash
python main_demo.py
```

## 🔑 API Keys Required

### OpenAI API Key
- Get from: https://platform.openai.com/api-keys
- Used for: Real LLM agent reasoning

### Bridge Sandbox API Key  
- Get from: https://dashboard.bridge.xyz/ (Sandbox mode)
- Used for: Real USDC wallet management and transfers

## 📊 Demo Flow

1. **🏗️ Infrastructure**: Walta MCP server starts, Bridge client connects
2. **🤖 Agents**: AI agents register with Walta, receive DIDs 
3. **💰 Funding**: Agent wallets funded with USDC via Bridge API
4. **🔐 Identity**: Agents verify each other's DIDs via Walta
5. **🛒 Commerce**: One agent requests service, other evaluates and accepts
6. **💸 Payment**: USDC transferred between agent wallets automatically

## 🧠 AI Decision Making

Each agent uses GPT-4 to make autonomous decisions:

```python
# Example AI reasoning
context = "Agent requests 'data_analysis' service for $75 USDC"
decision = await agent.make_ai_decision(context, ["accept", "reject"], "service_evaluation")

# AI Response:
{
  "decision": "accept",
  "reasoning": "This service matches my data analysis expertise and $75 is fair market rate",
  "confidence": "high"
}
```

## 🔗 Core Components

- **`walta_core.py`** - Identity and payment infrastructure
- **`bridge_client.py`** - Real Bridge API integration  
- **`ai_agents.py`** - LLM-powered autonomous agents
- **`mcp_server.py`** - Model Context Protocol server
- **`real_mcp_client.py`** - MCP client for agents
- **`main_demo.py`** - Complete demonstration

## 🧪 Testing

```bash
# Run core tests
python -m pytest test_mvp.py -v

# Test Bridge integration  
python -m pytest test_bridge_api.py -v
```

## 💡 Key Features

- ✅ **Real LLM Integration**: OpenAI GPT-4 autonomous reasoning
- ✅ **Real Identity System**: Walta DIDs for agent authentication
- ✅ **Real MCP Protocol**: Standards-compliant agent communication
- ✅ **Real USDC Payments**: Bridge API stablecoin transfers
- ✅ **Production Ready**: Complete error handling and logging

## 🎯 What This Demonstrates

This system proves that AI agents can:
1. Make autonomous decisions about identity and commerce
2. Communicate via standardized protocols (MCP)
3. Transact real value (USDC) based on AI reasoning
4. Verify identities using decentralized systems (DIDs)
5. Operate without human intervention

**This is the future of autonomous agent commerce.**