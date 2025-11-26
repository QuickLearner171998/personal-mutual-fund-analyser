"""
Configuration management for MF Portfolio Bot
All parameters configurable from this single file
"""
import os
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# API KEYS
# =============================================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

# =============================================================================
# LLM MODEL CONFIGURATION - Agent-Specific Models
# =============================================================================

# Planning Agent - Decides optimal use of agents (GPT-5 with medium reasoning)
PLANNING_LLM_MODEL = os.getenv("PLANNING_LLM_MODEL", "gpt-5")
PLANNING_REASONING_EFFORT = os.getenv("PLANNING_REASONING_EFFORT", "medium")
PLANNING_MAX_TOKENS = int(os.getenv("PLANNING_MAX_TOKENS", "500"))  # Optimized: JSON responses are concise

# Portfolio Agent - RAG queries (fast and accurate)
PORTFOLIO_LLM_MODEL = os.getenv("PORTFOLIO_LLM_MODEL", "gpt-4.1-mini")
PORTFOLIO_MAX_TOKENS = int(os.getenv("PORTFOLIO_MAX_TOKENS", "5000"))

# Market Agent - Real-time market research (Perplexity)
MARKET_LLM_MODEL = os.getenv("MARKET_LLM_MODEL", "sonar-pro")
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "sonar-pro")  # Alias for backward compat

# Comparison Agent - Fund comparison (Perplexity)
COMPARISON_LLM_MODEL = os.getenv("COMPARISON_LLM_MODEL", "sonar-pro")

# Goal Agent - Financial goal planning (GPT-5-mini with medium reasoning)
GOAL_LLM_MODEL = os.getenv("GOAL_LLM_MODEL", "gpt-5-mini")
GOAL_MAX_TOKENS = int(os.getenv("GOAL_MAX_TOKENS", "2000"))
GOAL_REASONING_EFFORT = os.getenv("GOAL_REASONING_EFFORT", "medium")

# Strategy Agent - Investment strategy (GPT-5-mini with medium reasoning)
STRATEGY_LLM_MODEL = os.getenv("STRATEGY_LLM_MODEL", "gpt-5-mini")
STRATEGY_MAX_TOKENS = int(os.getenv("STRATEGY_MAX_TOKENS", "2000"))
STRATEGY_REASONING_EFFORT = os.getenv("STRATEGY_REASONING_EFFORT", "medium")

# Synthesizer - Combines agent responses for best presentation
SYNTHESIZER_LLM_MODEL = os.getenv("SYNTHESIZER_LLM_MODEL", "gpt-4.1-mini")
SYNTHESIZER_MAX_TOKENS = int(os.getenv("SYNTHESIZER_MAX_TOKENS", "5000"))
SYNTHESIZER_TIMEOUT = int(os.getenv("SYNTHESIZER_TIMEOUT", "90"))

# Fallback LLM (when OpenAI models fail)
FALLBACK_LLM_MODEL = os.getenv("FALLBACK_LLM_MODEL", "gemini-2.0-flash-exp")

# =============================================================================
# AGENT TIMEOUT CONFIGURATION
# =============================================================================
# Timeout values in seconds for different agents to prevent hanging

PLANNING_TIMEOUT = int(os.getenv("PLANNING_TIMEOUT", "60"))      # Planning agent
PORTFOLIO_TIMEOUT = int(os.getenv("PORTFOLIO_TIMEOUT", "30"))    # Portfolio agent (fast RAG)
MARKET_TIMEOUT = int(os.getenv("MARKET_TIMEOUT", "45"))          # Market agent (Perplexity)
COMPARISON_TIMEOUT = int(os.getenv("COMPARISON_TIMEOUT", "45"))  # Comparison agent (Perplexity)
GOAL_TIMEOUT = int(os.getenv("GOAL_TIMEOUT", "120"))             # Goal agent (GPT-5-mini reasoning)
STRATEGY_TIMEOUT = int(os.getenv("STRATEGY_TIMEOUT", "120"))     # Strategy agent (GPT-5-mini reasoning)

# =============================================================================
# EMBEDDING CONFIGURATION
# =============================================================================
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1536"))

# =============================================================================
# VECTOR STORE CONFIGURATION
# =============================================================================
VECTOR_STORE_K = int(os.getenv("VECTOR_STORE_K", "10"))  # Number of results to retrieve
VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", "./data/vector_store")

# =============================================================================
# TOKEN LIMITS
# =============================================================================
MAX_COMPLETION_TOKENS = int(os.getenv("MAX_COMPLETION_TOKENS", "4000"))  # Default for non-agent calls

# =============================================================================
# PATHS - All local storage
# =============================================================================
DATA_DIR = os.getenv("DATA_DIR", "./data")
PORTFOLIO_FILE = f"{DATA_DIR}/portfolio.json"
TRANSACTIONS_FILE = f"{DATA_DIR}/transactions.json"
HISTORY_DIR = f"{DATA_DIR}/portfolio_history"

# =============================================================================
# AGENT CONFIGURATION
# =============================================================================
# Enable RAG (semantic search)
ENABLE_RAG = os.getenv("ENABLE_RAG", "true").lower() == "true"

# =============================================================================
# EXTERNAL API CONFIGURATION
# =============================================================================

# MFAPI.in
MFAPI_BASE_URL = "https://api.mfapi.in"
MFAPI_TIMEOUT = int(os.getenv("MFAPI_TIMEOUT", "10"))  # seconds

# Perplexity API
PERPLEXITY_BASE_URL = "https://api.perplexity.ai/chat/completions"
PERPLEXITY_TIMEOUT = int(os.getenv("PERPLEXITY_TIMEOUT", "90"))  # seconds

# =============================================================================
# UI CONFIGURATION
# =============================================================================
APP_TITLE = os.getenv("APP_TITLE", "MF Portfolio Bot")
PAGE_ICON = os.getenv("PAGE_ICON", "💹")
LAYOUT = os.getenv("LAYOUT", "wide")

# =============================================================================
# LOGGING & DEBUG
# =============================================================================
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Create data directories
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(VECTOR_STORE_PATH, exist_ok=True)
os.makedirs(HISTORY_DIR, exist_ok=True)
