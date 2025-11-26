"""
Multi-Agent Orchestrator
Coordinates multiple agents to answer complex queries with parallel execution
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.planning_agent import PlanningAgent
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
import config
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = get_logger(__name__)

class MultiAgentOrchestrator:
    def __init__(self):
        logger.info("Initializing MultiAgentOrchestrator")
        self.planner = PlanningAgent()
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
        logger.info(f"Synthesizing {len(responses)} responses using {config.SYNTHESIZER_LLM_MODEL}")
        
        # Build the synthesis prompt with complete context
        agent_outputs = []
        for agent_name, response in responses:
            agent_outputs.append(f"### {agent_name}\n\n{response}")
        
        combined_agent_outputs = "\n\n---\n\n".join(agent_outputs)
        
        synthesis_prompt = f"""You are an expert financial advisor synthesizing multiple analyses into ONE cohesive response.

**User's Question:**
{query}

**Agent Analyses:**

{combined_agent_outputs}

**Your Task:**
Synthesize into a single, well-formatted response that:
1. Directly answers the user's question
2. Integrates insights from all agents seamlessly  
3. Removes redundancies and contradictions
4. Presents information in logical order
5. Maintains all specific data and recommendations
6. Flows naturally as ONE expert opinion (not multiple agents)

**FORMATTING REQUIREMENTS:**
- Use clear markdown headers (##, ###)
- Use tables for numerical data
- Use bullet points for lists
- Use bold (**text**) for emphasis
- Add emojis (📊, 💰, ⚠️, ✅) for visual appeal
- Use horizontal rules (---) to separate sections
- Keep paragraphs short and readable

**IMPORTANT:**
- DO NOT mention "Agent X says" or "According to Agent Y"
- Write as if YOU are the expert who analyzed everything
- Be direct, actionable, and easy to understand
- Include all important numbers and percentages

**Synthesized Response:**"""

        try:
            messages = [
                {"role": "system", "content": "You are an expert financial advisor who synthesizes complex information into clear, actionable advice."},
                {"role": "user", "content": synthesis_prompt}
            ]
            
            logger.info(f"Invoking {config.SYNTHESIZER_LLM_MODEL} for response synthesis")
            synthesized = invoke_llm(
                config.SYNTHESIZER_LLM_MODEL,
                messages,
                max_tokens=config.SYNTHESIZER_MAX_TOKENS,
                timeout=config.SYNTHESIZER_TIMEOUT
            )
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
        Process user query through multi-agent system with planning
        
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
            # Step 1: Create execution plan
            logger.info("Step 1: Creating execution plan with Planning Agent")
            planning_start = time.time()
            plan = self.planner.create_plan(query)
            planning_time = time.time() - planning_start
            logger.info(f"Plan created: {plan['agents']} (took {planning_time:.2f}s)")
            logger.info(f"Reasoning: {plan['reasoning']}")
            
            agents_to_execute = plan['execution_order']
            
            # Step 2: Execute agents based on plan
            if len(agents_to_execute) == 1:
                # Single agent execution
                agent_name = agents_to_execute[0]
                logger.info(f"Step 2: Executing single agent: '{agent_name}'")
                agent = self.agents.get(agent_name)
                
                if not agent:
                    logger.error(f"Agent '{agent_name}' not found")
                    return f"⚠️ Agent '{agent_name}' not available. Please try rephrasing your question."
                
                try:
                    logger.info("=" * 60)
                    logger.info(f"EXECUTING AGENT: {agent_name.upper()}")
                    logger.info("=" * 60)
                    
                    agent_start = time.time()
                    response = self._execute_agent(agent_name, agent, query, stream)
                    agent_time = time.time() - agent_start
                    
                    logger.info(f"{agent_name.upper()} AGENT COMPLETED (took {agent_time:.2f}s)")
                    logger.info("=" * 60)
                    
                    # Format response (only if not streaming)
                    if not stream and isinstance(response, str):
                        response = format_response(response)
                    
                    total_time = time.time() - query_start_time
                    logger.info(f"TOTAL QUERY PROCESSING TIME: {total_time:.2f}s")
                    logger.info(f"  - Planning: {planning_time:.2f}s")
                    logger.info(f"  - {agent_name}: {agent_time:.2f}s")
                    
                    return response
                    
                except Exception as e:
                    logger.error(f"Error in {agent_name} agent: {str(e)}")
                    return f"⚠️ Error in {agent_name} agent: {str(e)}\n\nPlease try a different question or check if your portfolio data is loaded."
            
            else:
                # Multiple agents execution with PARALLEL execution for independent agents
                logger.info(f"Step 2: Executing {len(agents_to_execute)} agents: {agents_to_execute}")
                
                # Determine which agents can run in parallel
                # Portfolio must run first (provides context), Strategy must run last (needs other data)
                # Market, Comparison, Goal can run in parallel
                parallel_agents = []
                sequential_agents = []
                
                if 'portfolio' in agents_to_execute:
                    sequential_agents.append('portfolio')
                    agents_to_execute.remove('portfolio')
                
                if 'strategy' in agents_to_execute:
                    agents_to_execute.remove('strategy')
                    # Strategy runs last
                
                # Remaining agents can run in parallel
                parallel_agents = agents_to_execute.copy()
                
                if 'strategy' in plan['agents']:
                    sequential_agents.append('strategy')
                
                responses = []
                agent_timings = []
                
                # Execute portfolio first if needed
                for agent_name in sequential_agents:
                    if agent_name == 'portfolio':
                        agent = self.agents.get(agent_name)
                        if agent:
                            logger.info("=" * 60)
                            logger.info(f"EXECUTING AGENT: {agent_name.upper()} (Sequential - provides context)")
                            logger.info("=" * 60)
                            
                            agent_start = time.time()
                            try:
                                response = self._execute_agent(agent_name, agent, query, stream=False)
                                agent_time = time.time() - agent_start
                                agent_timings.append((agent_name, agent_time))
                                
                                title_map = {
                                    'portfolio': 'Portfolio Analysis',
                                    'market': 'Market Research',
                                    'strategy': 'Strategy Recommendation',
                                    'comparison': 'Fund Comparison',
                                    'goal': 'Goal Planning'
                                }
                                responses.append((title_map.get(agent_name, agent_name.title()), response))
                                
                                logger.info(f"✓ {agent_name.upper()} COMPLETED in {agent_time:.2f}s")
                                logger.info("=" * 60)
                            except Exception as e:
                                logger.error(f"❌ Error in {agent_name}: {str(e)}")
                                responses.append((agent_name.title(), f"⚠️ Error: {str(e)}"))
                
                # Execute parallel agents
                if parallel_agents:
                    logger.info(f"⚡ Executing {len(parallel_agents)} agents in PARALLEL: {parallel_agents}")
                    logger.info("=" * 60)
                    
                    def execute_agent_parallel(agent_name):
                        """Execute agent and return results with timing"""
                        agent = self.agents.get(agent_name)
                        if not agent:
                            return (agent_name, None, 0, f"Agent '{agent_name}' not found")
                        
                        logger.info(f"🚀 Starting {agent_name.upper()} (parallel)")
                        agent_start = time.time()
                        try:
                            response = self._execute_agent(agent_name, agent, query, stream=False)
                            agent_time = time.time() - agent_start
                            logger.info(f"✓ {agent_name.upper()} completed in {agent_time:.2f}s")
                            return (agent_name, response, agent_time, None)
                        except Exception as e:
                            agent_time = time.time() - agent_start
                            logger.error(f"❌ {agent_name} failed: {str(e)}")
                            return (agent_name, None, agent_time, str(e))
                    
                    # Execute in parallel using ThreadPoolExecutor
                    parallel_start = time.time()
                    with ThreadPoolExecutor(max_workers=len(parallel_agents)) as executor:
                        futures = {executor.submit(execute_agent_parallel, agent_name): agent_name 
                                 for agent_name in parallel_agents}
                        
                        for future in as_completed(futures):
                            agent_name, response, agent_time, error = future.result()
                            agent_timings.append((agent_name, agent_time))
                            
                            if error:
                                responses.append((agent_name.title(), f"⚠️ Error: {error}"))
                            else:
                                title_map = {
                                    'portfolio': 'Portfolio Analysis',
                                    'market': 'Market Research',
                                    'strategy': 'Strategy Recommendation',
                                    'comparison': 'Fund Comparison',
                                    'goal': 'Goal Planning'
                                }
                                responses.append((title_map.get(agent_name, agent_name.title()), response))
                    
                    parallel_time = time.time() - parallel_start
                    logger.info(f"⚡ Parallel execution completed in {parallel_time:.2f}s")
                    logger.info("=" * 60)
                
                # Execute strategy last if needed
                for agent_name in sequential_agents:
                    if agent_name == 'strategy':
                        agent = self.agents.get(agent_name)
                        if agent:
                            logger.info("=" * 60)
                            logger.info(f"EXECUTING AGENT: {agent_name.upper()} (Sequential - synthesizes strategy)")
                            logger.info("=" * 60)
                            
                            agent_start = time.time()
                            try:
                                response = self._execute_agent(agent_name, agent, query, stream=False)
                                agent_time = time.time() - agent_start
                                agent_timings.append((agent_name, agent_time))
                                
                                title_map = {
                                    'portfolio': 'Portfolio Analysis',
                                    'market': 'Market Research',
                                    'strategy': 'Strategy Recommendation',
                                    'comparison': 'Fund Comparison',
                                    'goal': 'Goal Planning'
                                }
                                responses.append((title_map.get(agent_name, agent_name.title()), response))
                                
                                logger.info(f"✓ {agent_name.upper()} COMPLETED in {agent_time:.2f}s")
                                logger.info("=" * 60)
                            except Exception as e:
                                logger.error(f"❌ Error in {agent_name}: {str(e)}")
                                responses.append((agent_name.title(), f"⚠️ Error: {str(e)}"))
                
                if not responses:
                    logger.error("No responses received from any agent")
                    return "⚠️ Unable to process your query. Please try rephrasing or upload your CAS data first."
                
                # Log agent timing breakdown
                logger.info("=" * 60)
                logger.info("AGENT TIMING BREAKDOWN:")
                for agent_name, timing in agent_timings:
                    logger.info(f"  ✓ {agent_name}: {timing:.2f}s")
                logger.info("=" * 60)
                
                # Display individual agent responses
                logger.info("=" * 60)
                logger.info("INDIVIDUAL AGENT RESPONSES:")
                logger.info("=" * 60)
                for title, response in responses:
                    logger.info(f"\n{'='*60}")
                    logger.info(f"📋 {title.upper()}")
                    logger.info(f"{'='*60}")
                    logger.info(f"{response[:300]}..." if len(response) > 300 else response)
                    logger.info(f"{'='*60}\n")
                
                # Use LLM to synthesize responses
                logger.info(f"🔄 Synthesizing {len(responses)} agent responses using {config.SYNTHESIZER_LLM_MODEL}")
                synthesis_start = time.time()
                synthesized = self._synthesize_responses(query, responses)
                synthesis_time = time.time() - synthesis_start
                logger.info(f"✓ Response synthesis completed in {synthesis_time:.2f}s")
                
                total_time = time.time() - query_start_time
                logger.info("=" * 60)
                logger.info(f"📊 TOTAL QUERY PROCESSING TIME: {total_time:.2f}s")
                logger.info(f"  - ⏱️  Planning: {planning_time:.2f}s")
                for agent_name, timing in agent_timings:
                    logger.info(f"  - 🤖 {agent_name}: {timing:.2f}s")
                logger.info(f"  - 🔄 Synthesis: {synthesis_time:.2f}s")
                logger.info("=" * 60)
                
                return synthesized
                
        except Exception as e:
            logger.error(f"System error in orchestrator: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return f"⚠️ System error: {str(e)}\n\nPlease try again or contact support if the issue persists."
    
    def _execute_agent(self, agent_name: str, agent, query: str, stream: bool = False):
        """Execute a single agent based on its name"""
        if agent_name == 'portfolio':
            logger.info("Portfolio Agent analyzing holdings and performance...")
            return agent.analyze(query, stream)
        elif agent_name == 'goal':
            logger.info("Goal Agent planning financial objectives...")
            return agent.plan(query, stream)
        elif agent_name == 'market':
            logger.info("Market Agent researching current conditions...")
            return agent.research(query, stream)
        elif agent_name == 'strategy':
            logger.info("Strategy Agent formulating recommendations...")
            return agent.advise(query, stream)
        elif agent_name == 'comparison':
            logger.info("Comparison Agent evaluating funds...")
            return agent.compare(query, stream)
        else:
            raise ValueError(f"Unknown agent: {agent_name}")


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
