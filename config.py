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
# LLM MODEL CONFIGURATION
# =============================================================================

# Primary LLM (for general tasks with reasoning)
PRIMARY_LLM_MODEL = os.getenv("PRIMARY_LLM_MODEL", "gpt-5-mini")  # Changed from gpt-5 for better latency

# Fast LLM for RAG and quick queries (also used for intent classification)
RAG_LLM_MODEL = os.getenv("RAG_LLM_MODEL", "gpt-4.1-mini")

# Intent Classification Model (GPT-4.1 for accuracy and speed)
INTENT_CLASSIFICATION_MODEL = os.getenv("INTENT_CLASSIFICATION_MODEL", "gpt-4.1-mini")

# Advanced reasoning LLM (for complex thinking) - Only use when explicitly needed
REASONING_LLM_MODEL = os.getenv("REASONING_LLM_MODEL", "gpt-5")

# Fallback LLM (when primary fails)
FALLBACK_LLM_MODEL = os.getenv("FALLBACK_LLM_MODEL", "gemini-2.0-flash-exp")

# Perplexity model (market research) - sonar is faster than sonar-pro
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "sonar")

# =============================================================================
# GPT-5 / O1 REASONING EFFORT CONFIGURATION
# =============================================================================
# Reasoning effort controls latency vs accuracy trade-off for GPT-5/o1 reasoning models ONLY
# Does NOT apply to gpt-4.1-mini or other non-reasoning models
# - "low":    ~1-3s latency,  Good for simple tasks, fast responses
# - "medium": ~3-6s latency,  Balanced for moderate complexity (DEFAULT)
# - "high":   ~10-30s latency, Best accuracy for complex reasoning
#
# Usage:
# - General Queries (PRIMARY_LLM if using gpt-5): Use medium (balanced)
# - Complex Strategy/Analysis (REASONING_LLM when explicitly needed): Use medium
# - Note: Intent classification uses gpt-4.1-mini, so these settings don't apply

REASONING_EFFORT_DEFAULT = os.getenv("REASONING_EFFORT_DEFAULT", "medium")
REASONING_EFFORT_STRATEGY = os.getenv("REASONING_EFFORT_STRATEGY", "medium")

# =============================================================================
# REASONING MODEL LATENCY OPTIMIZATION
# =============================================================================
# Additional parameters for GPT-5/o1 models to optimize performance

# Include reasoning traces in response (debugging only, adds latency)
INCLUDE_REASONING = os.getenv("INCLUDE_REASONING", "false").lower() == "true"

# Max completion tokens (lower = faster response, higher = more detailed)
# Reasoning models: 4000-16000 tokens typical, adjust based on use case
# Primary models: 1000-3000 tokens sufficient for most queries
MAX_COMPLETION_TOKENS_REASONING = int(os.getenv("MAX_COMPLETION_TOKENS_REASONING", "5000"))
MAX_COMPLETION_TOKENS_PRIMARY = int(os.getenv("MAX_COMPLETION_TOKENS_PRIMARY", "3000"))  # Reduced from 8000 for faster responses

# Enable prompt caching for faster repeated queries (if supported by model)
ENABLE_PROMPT_CACHING = os.getenv("ENABLE_PROMPT_CACHING", "true").lower() == "true"

# Timeout for reasoning models (in seconds) - prevents hanging on long responses
REASONING_TIMEOUT = int(os.getenv("REASONING_TIMEOUT", "90"))
PRIMARY_TIMEOUT = int(os.getenv("PRIMARY_TIMEOUT", "90"))

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
# PATHS - All local storage
# =============================================================================
DATA_DIR = os.getenv("DATA_DIR", "./data")
PORTFOLIO_FILE = f"{DATA_DIR}/portfolio.json"
TRANSACTIONS_FILE = f"{DATA_DIR}/transactions.json"
HISTORY_DIR = f"{DATA_DIR}/portfolio_history"

# =============================================================================
# AGENT CONFIGURATION
# =============================================================================

# Enable/disable specific agents
ENABLE_PORTFOLIO_AGENT = os.getenv("ENABLE_PORTFOLIO_AGENT", "true").lower() == "true"
ENABLE_GOAL_AGENT = os.getenv("ENABLE_GOAL_AGENT", "true").lower() == "true"
ENABLE_MARKET_AGENT = os.getenv("ENABLE_MARKET_AGENT", "true").lower() == "true"
ENABLE_STRATEGY_AGENT = os.getenv("ENABLE_STRATEGY_AGENT", "true").lower() == "true"
ENABLE_COMPARISON_AGENT = os.getenv("ENABLE_COMPARISON_AGENT", "true").lower() == "true"

# Enable RAG (semantic search)
ENABLE_RAG = os.getenv("ENABLE_RAG", "true").lower() == "true"

# Enable streaming responses
ENABLE_STREAMING = os.getenv("ENABLE_STREAMING", "true").lower() == "true"

# =============================================================================
# FINANCIAL CALCULATION DEFAULTS
# =============================================================================

# Expected returns for goal planning (annual %)
EXPECTED_EQUITY_RETURN = float(os.getenv("EXPECTED_EQUITY_RETURN", "12"))
EXPECTED_DEBT_RETURN = float(os.getenv("EXPECTED_DEBT_RETURN", "7"))
EXPECTED_HYBRID_RETURN = float(os.getenv("EXPECTED_HYBRID_RETURN", "10"))

# Risk thresholds
MAX_EQUITY_ALLOCATION = float(os.getenv("MAX_EQUITY_ALLOCATION", "80"))  # %
MIN_DEBT_ALLOCATION = float(os.getenv("MIN_DEBT_ALLOCATION", "20"))  # %

# =============================================================================
# EXTERNAL API CONFIGURATION
# =============================================================================

# MFAPI.in
MFAPI_BASE_URL = "https://api.mfapi.in"
MFAPI_TIMEOUT = int(os.getenv("MFAPI_TIMEOUT", "10"))  # seconds

# Perplexity API
PERPLEXITY_BASE_URL = "https://api.perplexity.ai/chat/completions"
PERPLEXITY_TIMEOUT = int(os.getenv("PERPLEXITY_TIMEOUT", "30"))  # seconds

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

# Print agent classifications
SHOW_INTENT_CLASSIFICATION = os.getenv("SHOW_INTENT_CLASSIFICATION", "true").lower() == "true"

# Create data directories
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(VECTOR_STORE_PATH, exist_ok=True)
os.makedirs(HISTORY_DIR, exist_ok=True)
