"""
Planning Agent
Uses GPT-5 with medium reasoning to create optimal execution plans
Replaces simple intent classification with intelligent task planning
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import List, Dict
from utils.logger import get_logger
from llm.llm_wrapper import invoke_llm
import config
import json

logger = get_logger(__name__)

class PlanningAgent:
    """
    Planning Agent - Decides optimal use of agents based on query
    
    Acts like a team lead of mutual fund advisors, coordinating specialists:
    - Portfolio Analyst: Understands current holdings
    - Market Researcher: Tracks market trends
    - Strategy Advisor: Formulates recommendations
    - Fund Comparison Specialist: Compares specific funds
    - Goal Planner: Plans financial goals
    """
    
    def __init__(self):
        logger.info(f"Planning Agent initialized with {config.PLANNING_LLM_MODEL} (reasoning: {config.PLANNING_REASONING_EFFORT})")
    
    def create_plan(self, query: str) -> Dict:
        """
        Create an execution plan for the query
        
        Returns:
            {
                "agents": ["portfolio", "market", "strategy"],
                "reasoning": "Explanation of why these agents are needed",
                "execution_order": ["portfolio", "market", "strategy"]
            }
        """
        logger.info(f"Creating execution plan for query: '{query}'")
        
        planning_prompt = f"""You are coordinating a team of mutual fund advisors. Create an execution plan for this query.

**Team Members:**
• portfolio: Analyzes user's holdings, allocations, performance
• market: Researches live market data, fund news, trends
• strategy: Provides investment advice and recommendations
• comparison: Compares specific funds in detail
• goal: Plans financial goals and SIP calculations

**Query:** "{query}"

**CRITICAL CONSTRAINTS:**
- Maximum 3 agents (keep it simple and focused)
- Select ONLY the minimum required specialists
- Order them logically (portfolio first if needed, strategy last)

**Rules:**
- Portfolio questions only → portfolio
- Market data only → market
- "Should I..." questions → portfolio + market + strategy (max 3)
- Fund comparisons → comparison OR comparison + market (max 2)
- Goal planning → goal OR portfolio + goal (max 2)

**Output (JSON only, no markdown):**
{{
    "agents": ["agent1", "agent2"],
    "reasoning": "One sentence why",
    "execution_order": ["agent1", "agent2"]
}}

**Examples:**

Q: "What is my total investment?"
{{"agents": ["portfolio"], "reasoning": "Simple portfolio query", "execution_order": ["portfolio"]}}

Q: "Should I shift from large cap to mid cap?"
{{"agents": ["portfolio", "market", "strategy"], "reasoning": "Need holdings, trends, strategy", "execution_order": ["portfolio", "market", "strategy"]}}

Q: "Latest NAV of HDFC Flexi Cap"
{{"agents": ["market"], "reasoning": "Real-time market data", "execution_order": ["market"]}}

Q: "Compare SBI vs Kotak Small Cap"
{{"agents": ["comparison"], "reasoning": "Fund comparison query", "execution_order": ["comparison"]}}

Create plan:"""

        try:
            messages = [
                {"role": "system", "content": "You are a planning coordinator for mutual fund advisors. Output valid JSON only."},
                {"role": "user", "content": planning_prompt}
            ]
            
            logger.info(f"Invoking {config.PLANNING_LLM_MODEL} with {config.PLANNING_REASONING_EFFORT} reasoning")
            response = invoke_llm(
                config.PLANNING_LLM_MODEL,
                messages,
                max_tokens=config.PLANNING_MAX_TOKENS,
                timeout=config.PLANNING_TIMEOUT,
                reasoning_effort=config.PLANNING_REASONING_EFFORT
            )
            
            # Parse JSON response
            
            # Clean up response - remove markdown code blocks if present
            response = response.strip()
            if response.startswith("```"):
                # Remove markdown code blocks
                lines = response.split("\n")
                response = "\n".join([line for line in lines if not line.startswith("```")])
                response = response.replace("json", "").strip()
            
            plan = json.loads(response)
            
            # Validate plan structure
            required_keys = ["agents", "reasoning", "execution_order"]
            for key in required_keys:
                if key not in plan:
                    raise ValueError(f"Missing required key: {key}")
            
            # Enforce max 3 agents
            if len(plan["agents"]) > 3:
                logger.warning(f"Plan has {len(plan['agents'])} agents, limiting to 3")
                plan["agents"] = plan["agents"][:3]
                plan["execution_order"] = plan["execution_order"][:3]
            
            # Validate agents
            valid_agents = ["portfolio", "market", "strategy", "comparison", "goal"]
            for agent in plan["agents"]:
                if agent not in valid_agents:
                    logger.warning(f"Unknown agent '{agent}' in plan, removing")
                    plan["agents"].remove(agent)
                    if agent in plan["execution_order"]:
                        plan["execution_order"].remove(agent)
            
            logger.info(f"✓ Execution plan created: {plan['agents']}")
            logger.info(f"✓ Reasoning: {plan['reasoning']}")
            
            return plan
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse planning response as JSON: {str(e)}")
            logger.error(f"Response was: {response[:500]}")
            
            # Fallback: Intelligent default based on keywords
            return self._fallback_plan(query)
            
        except Exception as e:
            logger.error(f"Error in planning: {str(e)}")
            return self._fallback_plan(query)
    
    def _fallback_plan(self, query: str) -> Dict:
        """
        Fallback plan based on simple keyword matching
        Used when LLM planning fails
        """
        logger.warning("Using fallback planning logic")
        
        query_lower = query.lower()
        
        # Simple portfolio queries
        if any(word in query_lower for word in ["my portfolio", "my holdings", "my investment", "total value", "how much", "show me"]):
            return {
                "agents": ["portfolio"],
                "reasoning": "Portfolio query detected (fallback)",
                "execution_order": ["portfolio"]
            }
        
        # Market queries
        if any(word in query_lower for word in ["nav", "market", "news", "current", "latest", "trend"]):
            return {
                "agents": ["market"],
                "reasoning": "Market query detected (fallback)",
                "execution_order": ["market"]
            }
        
        # Strategy queries (should I, what should, recommend)
        if any(word in query_lower for word in ["should i", "should we", "recommend", "suggest", "advice", "rebalance", "shift"]):
            return {
                "agents": ["portfolio", "market", "strategy"],
                "reasoning": "Strategy query detected, need full analysis (fallback)",
                "execution_order": ["portfolio", "market", "strategy"]
            }
        
        # Comparison queries
        if any(word in query_lower for word in ["compare", "vs", "versus", "better", "which fund"]):
            return {
                "agents": ["comparison", "market"],
                "reasoning": "Comparison query detected (fallback)",
                "execution_order": ["market", "comparison"]
            }
        
        # Goal planning
        if any(word in query_lower for word in ["goal", "target", "plan", "retirement", "education", "sip amount"]):
            return {
                "agents": ["portfolio", "goal"],
                "reasoning": "Goal planning query detected (fallback)",
                "execution_order": ["portfolio", "goal"]
            }
        
        # Default: Full analysis
        return {
            "agents": ["portfolio", "market", "strategy"],
            "reasoning": "Unable to classify, using comprehensive approach (fallback)",
            "execution_order": ["portfolio", "market", "strategy"]
        }
