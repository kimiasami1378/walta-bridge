#!/usr/bin/env python3
"""
LLM-Powered AI Agents for Autonomous Commerce
Connected to Walta via MCP for identity and payments
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from real_mcp_client import MCPClient


@dataclass
class AgentPersonality:
    """AI agent personality configuration."""
    name: str
    role: str
    expertise: List[str]
    personality_traits: List[str]
    risk_tolerance: str
    decision_style: str


class AIAgent:
    """LLM-powered autonomous AI agent."""
    
    def __init__(self, name: str, personality: AgentPersonality, openai_api_key: str):
        self.name = name
        self.personality = personality
        self.agent_did: Optional[str] = None
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            openai_api_key=openai_api_key,
            max_tokens=300
        )
        
        # MCP client for Walta communication
        self.mcp_client = MCPClient()
        
        # Decision history
        self.decision_history: List[Dict[str, Any]] = []
    
    async def connect_to_walta(self):
        """Connect to Walta MCP server and register."""
        await self.mcp_client.connect()
        self.agent_did = await self.mcp_client.register_agent(self.name)
    
    async def make_ai_decision(self, context: str, options: List[str], decision_type: str) -> Dict[str, Any]:
        """Use LLM to make autonomous decisions."""
        
        system_prompt = f"""You are {self.personality.name}, a {self.personality.role}.

Personality: {', '.join(self.personality.personality_traits)}
Expertise: {', '.join(self.personality.expertise)}
Risk tolerance: {self.personality.risk_tolerance}
Decision style: {self.personality.decision_style}

You are an autonomous AI agent making decisions about identity verification, service requests, and USDC payments.

Context: {context}
Options: {options}
Decision type: {decision_type}

Respond ONLY in valid JSON format:
{{
    "decision": "your_choice_from_options",
    "reasoning": "detailed_reasoning_for_decision",
    "confidence": "high/medium/low"
}}"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Make a decision about: {context}")
        ]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            decision_data = json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback if JSON is malformed
            decision_data = {
                "decision": options[0] if options else "proceed",
                "reasoning": response.content,
                "confidence": "medium"
            }
        
        # Record decision
        self.decision_history.append({
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "decision_type": decision_type,
            "decision": decision_data["decision"],
            "reasoning": decision_data["reasoning"],
            "confidence": decision_data.get("confidence", "medium")
        })
        
        return decision_data
    
    async def verify_peer_identity(self, peer_did: str) -> bool:
        """AI decides whether to verify peer identity."""
        context = f"Unknown agent with DID {peer_did[:20]}... wants to interact with me. Should I verify their identity for security?"
        
        decision = await self.make_ai_decision(
            context=context,
            options=["verify", "skip"],
            decision_type="identity_verification"
        )
        
        if decision["decision"] == "verify":
            # Request identity verification via MCP
            result = await self.mcp_client.verify_identity(peer_did)
            return result.get("verified", False)
        
        return False
    
    async def evaluate_service_request(self, requester_did: str, service_name: str, offered_amount: float) -> bool:
        """AI evaluates incoming service requests."""
        context = f"Agent {requester_did[:20]}... requests '{service_name}' service for ${offered_amount} USDC. My expertise: {self.personality.expertise}"
        
        decision = await self.make_ai_decision(
            context=context,
            options=["accept", "reject"],
            decision_type="service_evaluation"
        )
        
        if decision["decision"] == "accept":
            # Accept service and process payment via MCP
            result = await self.mcp_client.accept_service(
                requester_did, service_name, offered_amount
            )
            return result.get("payment_processed", False)
        
        return False
    
    async def request_service(self, provider_did: str, service_name: str, max_budget: float) -> bool:
        """AI decides to request a service."""
        # Get current balance
        balance_result = await self.mcp_client.get_balance()
        current_balance = balance_result.get("balance", {}).get("usdc", 0)
        
        context = f"I need '{service_name}' service from {provider_did[:20]}... Budget: ${max_budget}, My balance: ${current_balance} USDC"
        
        decision = await self.make_ai_decision(
            context=context,
            options=["request", "skip"],
            decision_type="service_request"
        )
        
        if decision["decision"] == "request" and current_balance >= max_budget:
            # Request service via MCP
            result = await self.mcp_client.request_service(
                provider_did, service_name, max_budget
            )
            return result.get("service_requested", False)
        
        return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        balance = await self.mcp_client.get_balance()
        messages = await self.mcp_client.get_messages()
        
        return {
            "name": self.name,
            "did": self.agent_did,
            "role": self.personality.role,
            "balance": balance.get("balance", {}),
            "pending_messages": messages.get("count", 0),
            "decisions_made": len(self.decision_history)
        }


def create_data_scientist_agent(name: str, openai_api_key: str) -> AIAgent:
    """Create a data scientist AI agent."""
    personality = AgentPersonality(
        name=name,
        role="Data Scientist and AI Researcher",
        expertise=["data_analysis", "machine_learning", "statistical_modeling"],
        personality_traits=["analytical", "methodical", "detail-oriented"],
        risk_tolerance="medium",
        decision_style="cautious"
    )
    return AIAgent(name, personality, openai_api_key)


def create_content_creator_agent(name: str, openai_api_key: str) -> AIAgent:
    """Create a content creator AI agent."""
    personality = AgentPersonality(
        name=name,
        role="Content Creator and Marketing Specialist",
        expertise=["content_writing", "marketing", "social_media"],
        personality_traits=["creative", "collaborative", "adaptable"],
        risk_tolerance="medium",
        decision_style="balanced"
    )
    return AIAgent(name, personality, openai_api_key)