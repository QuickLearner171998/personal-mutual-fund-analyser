# Performance Improvements & Optimizations

## Overview
This document tracks all performance optimizations made to the MF Portfolio Analyzer system.

## Recent Improvements (Nov 26, 2025)

### 1. Enhanced Logging with Timing Information
**Changed:** Added detailed timing breakdowns in orchestrator logging
**Impact:** Better visibility into performance bottlenecks

Example output:
```
TOTAL QUERY PROCESSING TIME: 72.89s
  - Intent Classification: 1.17s
  - strategy Agent: 43.39s
  - market Agent: 10.34s
  - Response Synthesis: 17.98s
```

**Benefits:**
- Identify slow agents immediately
- Track performance regressions
- Optimize based on actual metrics

### 2. LLM-Based Response Synthesis
**Changed:** Replaced simple concatenation with gpt-4.1-mini synthesis
**Impact:** Better quality responses when multiple agents are involved

**Implementation:**
- Uses gpt-4.1-mini for fast synthesis (~18s)
- Comprehensive prompt with full context
- Removes redundancies and contradictions
- Creates natural, flowing responses

**Prompt Features:**
- Complete agent context provided
- Instructions to remove "Agent X says" references
- Maintains all data points and numbers
- Markdown formatting for readability
- Fallback to concatenation if synthesis fails

### 3. Perplexity Model Optimization
**Changed:** Switched from `sonar-pro` to `sonar`
**Impact:** Faster market research queries

**Before:** 30s timeout with sonar-pro
**After:** ~8-10s with sonar

### 4. Token Limit Optimization
**Changed:** Increased from 2000 to 5000 tokens for PRIMARY_LLM
**Impact:** More detailed responses without excessive latency

**Reasoning:**
- 2000 tokens was too restrictive for complex queries
- 5000 tokens provides good balance
- gpt-5-mini handles 5K tokens reasonably well (~40s)

### 5. Code Organization
**Changed:** Moved all benchmark and test scripts to `scripts/` folder
**Impact:** Cleaner project structure

**Files moved:**
- `benchmark_gpt5.py` → `scripts/benchmark_gpt5.py`
- `benchmark_gpt5_mini.py` → `scripts/benchmark_gpt5_mini.py`
- `benchmark_real_query.py` → `scripts/benchmark_real_query.py`
- `test_formatting.py` → `scripts/test_formatting.py`
- `test_intent_logging.py` → `scripts/test_intent_logging.py`
- `test_reasoning_api.py` → `scripts/test_reasoning_api.py`

### 6. Removed Emojis from Codebase
**Changed:** Removed all emojis from logging statements
**Impact:** Better log parsing and professional output

**Before:**
```
🤖 EXECUTING AGENT: STRATEGY
💡 Strategy Agent formulating recommendations...
✅ STRATEGY AGENT COMPLETED SUCCESSFULLY
```

**After:**
```
EXECUTING AGENT: STRATEGY
Strategy Agent formulating recommendations...
STRATEGY AGENT COMPLETED SUCCESSFULLY (took 43.39s)
```

## Current Performance Metrics

### Real-World Query Benchmark
**Query:** "Should I rebalance my portfolio in the current market conditions?"

**Timing Breakdown:**
| Component | Time | % of Total |
|-----------|------|------------|
| Intent Classification (gpt-4.1-mini) | 1.17s | 1.6% |
| Strategy Agent (gpt-5-mini) | 43.39s | 59.5% |
| Market Agent (Perplexity sonar) | 10.34s | 14.2% |
| Response Synthesis (gpt-4.1-mini) | 17.98s | 24.7% |
| **TOTAL** | **72.89s** | **100%** |

## Bottleneck Analysis

### Primary Bottleneck: gpt-5-mini (43.39s - 59.5%)
**Cause:** Model is slower than expected for complex queries

**Potential Solutions:**
1. Further reduce token limit if acceptable
2. Use streaming in UI for better perceived performance
3. Consider model alternatives if latency is critical
4. Cache common query responses

### Secondary Bottleneck: Response Synthesis (17.98s - 24.7%)
**Cause:** LLM synthesis adds overhead

**Trade-offs:**
- **Pros:** Much better quality, coherent responses
- **Cons:** Adds ~18s to multi-agent queries
- **Decision:** Keep it - quality improvement is worth the latency

**Optimization Options:**
1. Use streaming for synthesis
2. Reduce synthesis prompt length
3. Cache synthesis for similar query patterns

### Minor Bottleneck: Market Agent (10.34s - 14.2%)
**Cause:** External API (Perplexity) latency

**Already Optimized:**
- Switched to `sonar` (faster than `sonar-pro`)
- Reduced timeout to 30s

**Future Options:**
1. Cache market research results
2. Use async/parallel agent execution
3. Implement fallback to faster sources

## Configuration Summary

### Current Settings
```python
# Models
PRIMARY_LLM_MODEL = "gpt-5-mini"
INTENT_CLASSIFICATION_MODEL = "gpt-4.1-mini"
RAG_LLM_MODEL = "gpt-4.1-mini"
REASONING_LLM_MODEL = "gpt-5"
PERPLEXITY_MODEL = "sonar"

# Token Limits
MAX_COMPLETION_TOKENS_PRIMARY = 5000
MAX_COMPLETION_TOKENS_REASONING = 5000

# Timeouts
PRIMARY_TIMEOUT = 90s
REASONING_TIMEOUT = 90s
PERPLEXITY_TIMEOUT = 30s
```

## Recommendations

### For Users Prioritizing Speed
1. Enable streaming in UI
2. Consider using gpt-4o-mini instead of gpt-5-mini
3. Reduce MAX_COMPLETION_TOKENS_PRIMARY to 3000

### For Users Prioritizing Quality
1. Keep current settings (5000 tokens)
2. LLM synthesis provides best results
3. Consider increasing timeouts if queries fail

### For Production Deployment
1. Implement response caching
2. Enable streaming for all agent responses
3. Add retry logic with exponential backoff
4. Monitor and alert on latency thresholds
5. Consider async agent execution for multi-agent queries

## Future Optimization Opportunities

1. **Parallel Agent Execution:** Run strategy and market agents concurrently (~20s savings)
2. **Response Caching:** Cache common queries and market data
3. **Streaming Synthesis:** Stream synthesis for better UX
4. **Model Selection:** Dynamic model selection based on query complexity
5. **Prompt Optimization:** Reduce prompt length while maintaining quality
6. **Edge Caching:** CDN caching for static responses

## Testing Scripts

All benchmark scripts are in `scripts/` folder:

- `scripts/benchmark_gpt5.py` - Test GPT-5 reasoning models
- `scripts/benchmark_gpt5_mini.py` - Isolated gpt-5-mini tests
- `scripts/benchmark_real_query.py` - End-to-end real query testing

Run benchmarks:
```bash
python scripts/benchmark_real_query.py
```

## Monitoring

Key metrics to track:
- Total query processing time
- Individual agent latencies
- Synthesis time
- Cache hit rates (when implemented)
- Error rates and timeouts

Use the logs to identify performance regressions:
```bash
grep "TOTAL QUERY PROCESSING TIME" logs/*.log
```
