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

# Primary LLM (for analysis)
# Available: "gpt-4o", "gpt-4o-mini", "gpt-4-turbo"
# Note: o1 models require special API access
PRIMARY_LLM_MODEL = os.getenv("PRIMARY_LLM_MODEL", "gpt-4o")
PRIMARY_LLM_TEMPERATURE = float(os.getenv("PRIMARY_LLM_TEMPERATURE", "0"))
PRIMARY_LLM_MAX_TOKENS = int(os.getenv("PRIMARY_LLM_MAX_TOKENS", "4096"))

# Fast LLM for RAG and quick queries
# Available: "gpt-4o-mini", "gpt-4o"
RAG_LLM_MODEL = os.getenv("RAG_LLM_MODEL", "gpt-4o-mini")
RAG_LLM_TEMPERATURE = float(os.getenv("RAG_LLM_TEMPERATURE", "0"))
RAG_LLM_MAX_TOKENS = int(os.getenv("RAG_LLM_MAX_TOKENS", "2000"))

# Advanced reasoning LLM (if you have o1 access, otherwise same as primary)
REASONING_LLM_MODEL = os.getenv("REASONING_LLM_MODEL", "gpt-4o")
REASONING_LLM_TEMPERATURE = float(os.getenv("REASONING_LLM_TEMPERATURE", "0"))

# Fallback LLM (when primary fails)
FALLBACK_LLM_MODEL = os.getenv("FALLBACK_LLM_MODEL", "gemini-2.0-flash-exp")
FALLBACK_LLM_TEMPERATURE = float(os.getenv("FALLBACK_LLM_TEMPERATURE", "0"))
FALLBACK_LLM_MAX_TOKENS = int(os.getenv("FALLBACK_LLM_MAX_TOKENS", "2000"))

# Perplexity model (market research)
# Options: "sonar", "sonar-pro", "llama-3.1-sonar-large-128k-online"
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "llama-3.1-sonar-large-128k-online")
PERPLEXITY_TEMPERATURE = float(os.getenv("PERPLEXITY_TEMPERATURE", "0.2"))
PERPLEXITY_MAX_TOKENS = int(os.getenv("PERPLEXITY_MAX_TOKENS", "1000"))

# =============================================================================
# EMBEDDING CONFIGURATION
# =============================================================================
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1536"))

# =============================================================================
# VECTOR STORE CONFIGURATION
# =============================================================================
VECTOR_STORE_K = int(os.getenv("VECTOR_STORE_K", "5"))  # Number of results to retrieve
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
