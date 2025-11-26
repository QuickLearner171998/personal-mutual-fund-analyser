"""
Multi-Agent Orchestrator
Coordinates multiple agents to answer complex queries
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.coordinator import IntentClassifier
from agents.portfolio_agent import PortfolioAgent
from agents.goal_agent import GoalAgent
from agents.market_agent import MarketAgent
from agents.strategy_agent import StrategyAgent
from agents.comparison_agent import ComparisonAgent
from typing import Iterator, Union, List, Tuple
from utils.logger import get_logger
from utils.response_formatter import format_response
from llm.llm_wrapper import invoke_llm
import time

logger = get_logger(__name__)

class MultiAgentOrchestrator:
    def __init__(self):
        logger.info("Initializing MultiAgentOrchestrator")
        self.classifier = IntentClassifier()
        self.agents = {
            'portfolio': PortfolioAgent(),
            'goal': GoalAgent(),
            'market': MarketAgent(),
            'strategy': StrategyAgent(),
            'comparison': ComparisonAgent()
        }
        logger.info(f"Initialized {len(self.agents)} agents: {list(self.agents.keys())}")
    
    def _synthesize_responses(self, query: str, responses: List[Tuple[str, str]]) -> str:
        """
        Use gpt-4.1-mini to intelligently synthesize multiple agent responses
        into a coherent, comprehensive answer.
        
        Args:
            query: Original user query
            responses: List of (agent_name, response) tuples
        
        Returns:
            Synthesized response
        """
        logger.info(f"Synthesizing {len(responses)} responses using gpt-4.1-mini")
        
        # Build the synthesis prompt with complete context
        agent_outputs = []
        for agent_name, response in responses:
            agent_outputs.append(f"### {agent_name}\n\n{response}")
        
        combined_agent_outputs = "\n\n---\n\n".join(agent_outputs)
        
        synthesis_prompt = f"""You are an expert financial advisor tasked with synthesizing multiple specialized analyses into a single, coherent, and comprehensive response for the user.

**User's Question:**
{query}

**Context:**
Multiple specialized agents have analyzed different aspects of this question. Your job is to:
1. Synthesize these analyses into ONE unified, flowing response
2. Remove redundancies and contradictions
3. Prioritize the most relevant information
4. Ensure logical flow and coherence
5. Maintain all specific numbers, percentages, and data points
6. Keep the response well-structured with clear sections
7. Use markdown formatting for better readability
8. If agents provide conflicting advice, acknowledge both perspectives and explain why

**Agent Analyses:**

{combined_agent_outputs}

**Your Task:**
Create a single, comprehensive response that:
- Directly answers the user's question
- Integrates insights from all agents seamlessly
- Presents information in a logical order
- Uses clear sections with markdown headers
- Includes all specific data and recommendations
- Flows naturally as if written by one expert, not multiple agents
- Is actionable and easy to understand

Do NOT simply concatenate the responses. Do NOT mention "Agent X says" or "According to Agent Y". Write as if YOU are the expert who has analyzed all aspects.

**Synthesized Response:**"""

        try:
            messages = [
                {"role": "system", "content": "You are an expert financial advisor who synthesizes complex information into clear, actionable advice."},
                {"role": "user", "content": synthesis_prompt}
            ]
            
            logger.info("Invoking gpt-4.1-mini for response synthesis")
            synthesized = invoke_llm(messages, use_rag=True, stream=False)
            logger.info(f"Successfully synthesized response ({len(synthesized)} chars)")
            
            # Apply formatting
            synthesized = format_response(synthesized)
            
            return synthesized
            
        except Exception as e:
            logger.error(f"Error during synthesis: {str(e)}, falling back to simple concatenation")
            # Fallback to simple concatenation if synthesis fails
            combined_parts = []
            for title, resp in responses:
                formatted_resp = format_response(resp) if isinstance(resp, str) else resp
                combined_parts.append(f"## {title}\n\n{formatted_resp}")
            return "\n\n---\n\n".join(combined_parts)
    
    def process_query(self, query: str, stream: bool = False) -> Union[str, Iterator]:
        """
        Process user query through multi-agent system with error handling
        
        Args:
            query: User's question
            stream: Whether to stream response
        
        Returns:
            Agent response (string or iterator if streaming)
        """
        query_start_time = time.time()
        
        logger.info("=" * 60)
        logger.info("PROCESSING NEW QUERY")
        logger.info("=" * 60)
        logger.info(f"Query: '{query}'")
        logger.info(f"Stream mode: {stream}")
        
        try:
            # Step 1: Classify intent
            logger.info("Step 1: Classifying intent with dedicated GPT-4.1 model")
            intent_start = time.time()
            intents = self.classifier.classify(query)
            intent_time = time.time() - intent_start
            logger.info(f"Classified intents: {intents} (took {intent_time:.2f}s)")
            
            # Step 2: Route to appropriate agent(s)
            if len(intents) == 1:
                # Single agent
                intent = intents[0]
                logger.info(f"Step 2: Routing to single agent: '{intent}'")
                agent = self.agents.get(intent)
                
                if not agent:
                    logger.error(f"Agent for intent '{intent}' not found")
                    return f"⚠️ Agent for '{intent}' not found. Please try rephrasing your question."
                
                try:
                    logger.info("=" * 60)
                    logger.info(f"EXECUTING AGENT: {intent.upper()}")
                    logger.info("=" * 60)
                    
                    agent_start = time.time()
                    
                    if intent == 'portfolio':
                        logger.info("Portfolio Agent analyzing holdings and performance...")
                        response = agent.analyze(query, stream)
                    elif intent == 'goal':
                        logger.info("Goal Agent planning financial objectives...")
                        response = agent.plan(query, stream)
                    elif intent == 'market':
                        logger.info("Market Agent researching current conditions...")
                        response = agent.research(query, stream)
                    elif intent == 'strategy':
                        logger.info("Strategy Agent formulating recommendations...")
                        response = agent.advise(query, stream)
                    elif intent == 'comparison':
                        logger.info("Comparison Agent evaluating funds...")
                        response = agent.compare([], stream)
                    
                    agent_time = time.time() - agent_start
                    logger.info(f"{intent.upper()} AGENT COMPLETED SUCCESSFULLY (took {agent_time:.2f}s)")
                    logger.info("=" * 60)
                    
                    # Format response for better readability (only if not streaming)
                    if not stream and isinstance(response, str):
                        response = format_response(response)
                    
                    total_time = time.time() - query_start_time
                    logger.info(f"TOTAL QUERY PROCESSING TIME: {total_time:.2f}s")
                    return response
                    
                except Exception as e:
                    logger.error(f"Error in {intent} agent: {str(e)}")
                    return f"⚠️ Error in {intent} agent: {str(e)}\n\nPlease try a different question or check if your portfolio data is loaded."
            
            else:
                # Multiple agents needed - run sequentially and synthesize
                logger.info(f"Step 2: Routing to multiple agents: {intents}")
                responses = []
                agent_timings = []
                
                for intent in intents:
                    logger.info(f"Processing intent: '{intent}'")
                    agent = self.agents.get(intent)
                    
                    if not agent:
                        logger.warning(f"Agent for intent '{intent}' not found, skipping")
                        continue
                    
                    try:
                        logger.info("=" * 60)
                        logger.info(f"EXECUTING AGENT {intents.index(intent) + 1}/{len(intents)}: {intent.upper()}")
                        logger.info("=" * 60)
                        
                        agent_start = time.time()
                        
                        if intent == 'portfolio':
                            logger.info("Portfolio Agent analyzing holdings and performance...")
                            responses.append(("Portfolio Analysis", agent.analyze(query)))
                        elif intent == 'goal':
                            logger.info("Goal Agent planning financial objectives...")
                            responses.append(("Goal Planning", agent.plan(query)))
                        elif intent == 'market':
                            logger.info("Market Agent researching current conditions...")
                            responses.append(("Market Research", agent.research(query)))
                        elif intent == 'strategy':
                            logger.info("Strategy Agent formulating recommendations...")
                            responses.append(("Strategy Advice", agent.advise(query)))
                        elif intent == 'comparison':
                            logger.info("Comparison Agent evaluating funds...")
                            responses.append(("Fund Comparison", agent.compare([])))
                        
                        agent_time = time.time() - agent_start
                        agent_timings.append((intent, agent_time))
                        logger.info(f"{intent.upper()} AGENT COMPLETED SUCCESSFULLY (took {agent_time:.2f}s)")
                        logger.info("=" * 60)
                        
                    except Exception as e:
                        logger.error(f"Error in {intent} agent: {str(e)}")
                        responses.append((f"{intent.title()} Agent", f"⚠️ Error: {str(e)}"))
                
                if not responses:
                    logger.error("No responses received from any agent")
                    return "⚠️ Unable to process your query. Please try rephrasing or upload your CAS data first."
                
                # Log agent timing breakdown
                logger.info("=" * 60)
                logger.info("AGENT TIMING BREAKDOWN:")
                for agent_name, timing in agent_timings:
                    logger.info(f"  {agent_name}: {timing:.2f}s")
                logger.info("=" * 60)
                
                # Use LLM to synthesize responses intelligently
                logger.info(f"Using gpt-4.1-mini to synthesize {len(responses)} agent responses")
                synthesis_start = time.time()
                synthesized = self._synthesize_responses(query, responses)
                synthesis_time = time.time() - synthesis_start
                logger.info(f"Response synthesis completed (took {synthesis_time:.2f}s)")
                
                total_time = time.time() - query_start_time
                logger.info("=" * 60)
                logger.info(f"TOTAL QUERY PROCESSING TIME: {total_time:.2f}s")
                logger.info(f"  - Intent Classification: {intent_time:.2f}s")
                for agent_name, timing in agent_timings:
                    logger.info(f"  - {agent_name} Agent: {timing:.2f}s")
                logger.info(f"  - Response Synthesis: {synthesis_time:.2f}s")
                logger.info("=" * 60)
                
                return synthesized
                
        except Exception as e:
            logger.error(f"System error in orchestrator: {str(e)}")
            return f"⚠️ System error: {str(e)}\n\nPlease try again or contact support if the issue persists."


# Global instance
orchestrator = MultiAgentOrchestrator()


def answer_query(query: str, stream: bool = False):
    """Convenience function to answer queries"""
    return orchestrator.process_query(query, stream)


# Test
if __name__ == "__main__":
    orchestrator = MultiAgentOrchestrator()
    
    # Test single intent
    response = orchestrator.process_query("What is my total portfolio value?")
    logger.info(f"Response received: {len(response)} characters")
    
    logger.info("\n" + "="*50 + "\n")
    
    # Test multiple intents
    response = orchestrator.process_query("Show my portfolio and suggest if I should rebalance")
    logger.info(f"Response received: {len(response)} characters")
