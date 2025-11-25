# LLM Usage Documentation

## Overview

This document summarizes all LLM calls in the codebase, models being used, and their purposes.

---

## LLM Architecture

The application uses a **multi-model architecture** with automatic fallback:

```
OpenAI Models
├─ gpt-5 (Primary - General tasks with reasoning)
├─ gpt-4.1-mini (RAG - Fast queries)
└─ gpt-5 (Reasoning - Complex thinking, same as primary)

External APIs
└─ Perplexity Sonar Pro (Market research)

Fallback
└─ Gemini 2.0 Flash (Google)
```

---

## Model Configuration

### OpenAI Models

**1. GPT-5 (Primary)**
- **Model**: `gpt-5`
- **Use Case**: General queries, analysis, multi-agent coordination with reasoning
- **Used By**: Coordinator, Strategy Agent, Comparison Agent, Goal Agent
- **Note**: Same model used for both primary and reasoning tasks

**2. GPT-4.1-mini (RAG)**
- **Model**: `gpt-4.1-mini`
- **Use Case**: Fast RAG queries, portfolio lookups, simple Q&A
- **Used By**: Portfolio Agent
- **Optimization**: Optimized for factual accuracy with retrieval

**3. GPT-5 (Reasoning)**
- **Model**: `gpt-5`
- **Use Case**: Complex reasoning, strategy planning, deep analysis
- **Used By**: Strategy Agent (when `use_reasoning=True`)
- **Note**: Advanced thinking capabilities

### External APIs

**Perplexity Sonar Pro**
- **Model**: `sonar-pro`
- **Use Case**: Real-time market research, fund news, NAV updates
- **Used By**: Market Agent
- **Features**: Web access, citations, up-to-date information

### Fallback Model

**Gemini 2.0 Flash**
- **Model**: `gemini-2.0-flash-exp`
- **Use Case**: Automatic fallback when OpenAI fails
- **Cost**: Free tier available

---

## LLM Wrapper

**File**: `llm/llm_wrapper.py`

### Core Function

```python
def invoke_llm(
    messages: List[Dict], 
    use_reasoning: bool = False, 
    use_rag: bool = False, 
    stream: bool = False
)
```

**Model Selection Logic**:
- `use_reasoning=True` → GPT-5 (complex thinking)
- `use_rag=True` → GPT-4.1-mini (fast RAG)
- Default → GPT-5-mini (general tasks)

**Fallback Logic**:
1. Try selected OpenAI model
2. On failure, automatically fall back to Gemini 2.0 Flash
3. Return error if both fail

---

## LLM Usage by Component

### 1. Coordinator Agent

**File**: `agents/coordinator.py`

**LLM Call**:
```python
invoke_llm(messages)  # Uses gpt-5-mini
```

**Model**: GPT-5-mini  
**Purpose**: Routes queries to appropriate specialized agents  
**Frequency**: Every user query

**Prompt**: Analyzes query and determines routing:
- Portfolio questions → Portfolio Agent
- Market questions → Market Agent
- Strategy questions → Strategy Agent
- Comparison questions → Comparison Agent
- Goal planning → Goal Agent

---

### 2. Portfolio Agent

**File**: `agents/portfolio_agent.py`

**LLM Call**:
```python
invoke_llm(messages, use_rag=True, stream=stream)
```

**Model**: GPT-4.1-mini (RAG)  
**Purpose**: Answers portfolio-specific questions using RAG  
**Frequency**: High (most common queries)

**Context Retrieved**:
- Portfolio holdings data
- Transaction history
- SIP details
- Broker information
- XIRR/CAGR metrics

**Example Queries**:
- "What is my total investment?"
- "Show me my top performing funds"
- "Which broker manages my HDFC funds?"
- "When is my next SIP installment?"

**Why GPT-4.1-mini**: Fast, cheap, accurate for factual queries

---

### 3. Market Agent

**File**: `agents/market_agent.py`

**External API**: Perplexity Sonar Pro  
**LLM Call**: Direct Perplexity API call (not through wrapper)

**Model**: Perplexity Sonar Pro  
**Purpose**: Real-time market research with web access  
**Frequency**: Medium

**Perplexity Configuration**:
```python
{
    "model": "sonar-pro",
    "temperature": 0.2,
    "max_tokens": 1000
}
```

**Features**:
- **Web Access**: Real-time data from the internet
- **Citations**: Provides source URLs
- **Up-to-date**: Latest market information

**Example Queries**:
- "Current NAV of SBI Small Cap Fund"
- "Latest news on HDFC Mutual Fund"
- "Market outlook for mid-cap funds"
- "Compare performance of large cap funds"

**API Endpoint**: `https://api.perplexity.ai/chat/completions`

---

### 4. Strategy Agent

**File**: `agents/strategy_agent.py`

**LLM Call**:
```python
invoke_llm(messages, use_reasoning=False, stream=stream)
```

**Model**: GPT-5-mini (can use GPT-5 with `use_reasoning=True`)  
**Purpose**: Investment strategy recommendations  
**Frequency**: Medium

**Context**:
- Portfolio allocation
- Risk profile
- Investment goals
- Market conditions

**Example Queries**:
- "Should I rebalance my portfolio?"
- "Suggest funds for tax saving"
- "How to diversify my equity allocation?"

---

### 5. Comparison Agent

**File**: `agents/comparison_agent.py`

**LLM Call**:
```python
invoke_llm(messages, stream=stream)
```

**Model**: GPT-5-mini  
**Purpose**: Fund comparison and analysis  
**Frequency**: Low-Medium

**Example Queries**:
- "Compare HDFC Flexi Cap vs ICICI Flexi Cap"
- "Which is better: SBI Small Cap or Kotak Small Cap?"
- "Compare my equity funds by XIRR"

---

### 6. Goal Agent

**File**: `agents/goal_agent.py`

**LLM Call**:
```python
invoke_llm(messages, use_reasoning=False, stream=stream)
```

**Model**: GPT-5-mini  
**Purpose**: Financial goal planning  
**Frequency**: Low

**Example Queries**:
- "How much to invest for retirement?"
- "SIP amount needed for ₹1 crore in 10 years"
- "Plan for child's education fund"

---

## API Call Summary

| Component | Model | Use Case | Frequency |
|-----------|-------|----------|-----------|
| Coordinator | gpt-5 | Query routing | Every query |
| Portfolio Agent | gpt-4.1-mini | Portfolio Q&A (RAG) | High |
| Market Agent | Perplexity Sonar Pro | Market research | Medium |
| Strategy Agent | gpt-5 | Investment advice | Medium |
| Comparison Agent | gpt-5 | Fund comparison | Low |
| Goal Agent | gpt-5 | Goal planning | Low |

---

## Perplexity API Usage

### Configuration

**File**: `external/perplexity_client.py`

**API Details**:
- **Base URL**: `https://api.perplexity.ai/chat/completions`
- **Model**: `sonar-pro` (online model with web access)
- **Timeout**: 30 seconds

### Methods

**1. `search(query: str)`**
- General search with citations
- Returns: `{"answer": str, "citations": List[str], "success": bool}`

**2. `search_fund_news(fund_name: str)`**
- Latest news about specific fund
- Includes NAV trends, fund manager changes

**3. `search_market_trends()`**
- Current market trends
- Top performing categories
- Investment outlook

**4. `analyze_fund_comparison(fund1: str, fund2: str)`**
- Compare two funds
- Performance, expense ratio, strategy

### Usage in Market Agent

```python
from external.perplexity_client import perplexity

# Search
result = perplexity.search("Current NAV of SBI Small Cap Fund")

# Response
{
    "answer": "SBI Small Cap Fund NAV is ₹168.95 as of Nov 25, 2025...",
    "citations": ["https://www.sbimf.com/...", "https://www.moneycontrol.com/..."],
    "success": True
}
```

---

## Cost Optimization

### Strategies

1. **Model Selection**:
   - Use GPT-4.1-mini for RAG (cheapest, fastest)
   - Use GPT-5-mini for general tasks (balanced)
   - Use GPT-5 only for complex reasoning (most expensive)

2. **Context Management**:
   - Vector DB retrieves only relevant context
   - Limits context size to reduce tokens

3. **Perplexity for Market Data**:
   - Use Perplexity instead of GPT for market research
   - Cheaper and provides real-time data with citations

4. **Streaming**:
   - Stream responses for better UX
   - Allows early termination

5. **Fallback**:
   - Automatic fallback to free Gemini tier
   - Reduces costs during OpenAI outages

### Estimated Costs (per 1000 queries)

**Assumptions**:
- 60% Portfolio queries (gpt-4.1-mini)
- 25% General queries (gpt-5-mini)
- 10% Market queries (Perplexity)
- 5% Complex reasoning (gpt-5)

**Note**: Actual costs depend on GPT-5 and GPT-4.1-mini pricing (TBD)

---

## Environment Variables

Required API keys in `.env`:

```bash
# OpenAI (GPT-5, GPT-5-mini, GPT-4.1-mini)
OPENAI_API_KEY=sk-...

# Google (Fallback)
GOOGLE_API_KEY=...

# Perplexity (Market Research)
PERPLEXITY_API_KEY=pplx-...
```

### Model Configuration

```bash
# Primary model (general tasks with reasoning)
PRIMARY_LLM_MODEL=gpt-5

# RAG model (fast queries)
RAG_LLM_MODEL=gpt-4.1-mini

# Reasoning model (complex thinking)
REASONING_LLM_MODEL=gpt-5

# Perplexity model
PERPLEXITY_MODEL=sonar-pro
```

---

## Best Practices

1. **Use RAG for portfolio queries** - GPT-4.1-mini is fast and cheap
2. **Use Perplexity for market data** - Real-time info with citations
3. **Stream responses** - Better user experience
4. **Monitor token usage** - Control costs
5. **Test fallback regularly** - Ensure Gemini works
6. **Log all API calls** - Debug and optimize

---

## Troubleshooting

### Common Issues

**1. OpenAI API Failure**
- **Symptom**: "Primary LLM failed" warning
- **Solution**: Automatic fallback to Gemini
- **Action**: Check OpenAI API key and quota

**2. Perplexity Timeout**
- **Symptom**: Market queries fail
- **Solution**: Increase timeout in config
- **Action**: Check Perplexity API key and quota

**3. Slow Responses**
- **Symptom**: Long wait times
- **Solution**: Enable streaming
- **Action**: Use `stream=True` parameter

**4. High Costs**
- **Symptom**: Unexpected API bills
- **Solution**: Review model selection
- **Action**: Use GPT-4.1-mini for more queries

---

## Summary

The application uses a **smart multi-model approach**:

**OpenAI Models**:
- **GPT-4.1-mini** for fast, cheap RAG queries (Portfolio Agent)
- **GPT-5** for general tasks with reasoning (Coordinator, Strategy, Comparison, Goal)
- **GPT-5** for complex reasoning (same model, when `use_reasoning=True`)

**External APIs**:
- **Perplexity Sonar Pro** for real-time market research (Market Agent)

**Fallback**:
- **Gemini 2.0 Flash** for reliability when OpenAI fails

All LLM calls go through a **unified wrapper** (`llm/llm_wrapper.py`) that handles model selection, automatic fallback, streaming, and error handling.

Perplexity calls are direct API calls through `external/perplexity_client.py` for market research with web access and citations.
