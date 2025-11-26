"""
Response Formatter - Improves markdown formatting for better readability
"""
import re
from utils.logger import get_logger

logger = get_logger(__name__)

def format_response(raw_response: str) -> str:
    """
    Format raw LLM response with better markdown formatting
    
    Args:
        raw_response: Raw text from LLM
    
    Returns:
        Formatted markdown text
    """
    try:
        formatted = raw_response
        
        # 1. Add line breaks before main sections for better spacing
        formatted = re.sub(r'(\*\*[A-Z][^*]+\*\*:)', r'\n\n\1', formatted)
        
        # 2. Format bullet points consistently with proper spacing
        formatted = re.sub(r'^(\s*)-\s*(\*\*)', r'\n\1- \2', formatted, flags=re.MULTILINE)
        formatted = re.sub(r'^(\s*)\*\s+', r'\n\1- ', formatted, flags=re.MULTILINE)
        
        # 3. Add spacing around numbered lists
        formatted = re.sub(r'^(\d+\.)\s+', r'\n\1 ', formatted, flags=re.MULTILINE)
        
        # 4. Format tables properly - ensure spacing
        lines = formatted.split('\n')
        in_table = False
        new_lines = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Detect table start
            if '|' in stripped and not in_table:
                if new_lines and new_lines[-1].strip():
                    new_lines.append('')  # Add blank line before table
                in_table = True
            
            # Detect table end
            elif in_table and '|' not in stripped:
                in_table = False
                new_lines.append(line)
                if stripped:  # Add blank line after table
                    new_lines.append('')
                continue
            
            new_lines.append(line)
        
        formatted = '\n'.join(new_lines)
        
        # 5. Format currency consistently
        formatted = re.sub(r'Rs\.?\s*(\d)', r'₹\1', formatted)
        formatted = re.sub(r'INR\s*(\d)', r'₹\1', formatted)
        
        # 6. Format percentages consistently
        formatted = re.sub(r'(\d+\.?\d*)\s*%', r'\1%', formatted)
        
        # 7. Add emphasis to key metrics with emojis
        formatted = re.sub(r'\*\*Total (Value|Portfolio|Investment)([^*]*)\*\*', r'💰 **Total \1\2**', formatted)
        formatted = re.sub(r'\*\*Returns?([^*]*)\*\*', r'📈 **Return\1**', formatted)
        formatted = re.sub(r'\*\*(Risk|Warning|Alert)([^*]*)\*\*', r'⚠️ **\1\2**', formatted)
        formatted = re.sub(r'\*\*Recommendation([^*]*)\*\*', r'💡 **Recommendation\1**', formatted)
        formatted = re.sub(r'\*\*Action([^*]*)\*\*', r'✅ **Action\1**', formatted)
        formatted = re.sub(r'\*\*Goal([^*]*)\*\*', r'🎯 **Goal\1**', formatted)
        formatted = re.sub(r'\*\*Strategy([^*]*)\*\*', r'📋 **Strategy\1**', formatted)
        formatted = re.sub(r'\*\*Analysis([^*]*)\*\*', r'📊 **Analysis\1**', formatted)
        formatted = re.sub(r'\*\*Market([^*]*)\*\*', r'🔍 **Market\1**', formatted)
        formatted = re.sub(r'\*\*Tax([^*]*)\*\*', r'💼 **Tax\1**', formatted)
        
        # 8. Format section headers with proper spacing
        formatted = re.sub(r'\n(#{1,6})\s*([^\n]+)', r'\n\n\1 \2\n', formatted)
        
        # 9. Clean up excessive blank lines (max 2 consecutive)
        formatted = re.sub(r'\n{3,}', '\n\n', formatted)
        
        # 10. Ensure single space after periods in sentences
        formatted = re.sub(r'\.(\S)', r'. \1', formatted)
        
        # 11. Format code blocks properly
        formatted = re.sub(r'```(\w+)?\n', r'\n```\1\n', formatted)
        formatted = re.sub(r'\n```\s*\n', r'\n```\n\n', formatted)
        
        # 12. Format fund names consistently (all caps HDFC, ICICI, etc)
        fund_keywords = ['hdfc', 'icici', 'sbi', 'axis', 'kotak', 'nippon', 'aditya birla', 'mirae', 'parag parikh']
        for keyword in fund_keywords:
            pattern = re.compile(r'\b' + keyword + r'\b', re.IGNORECASE)
            formatted = pattern.sub(lambda m: m.group(0).upper() if len(m.group(0)) <= 6 else m.group(0).title(), formatted)
        
        # 13. Add dividers for major sections
        formatted = re.sub(r'\n(📊 \*\*.*?\*\*)', r'\n---\n\n\1', formatted)
        formatted = re.sub(r'\n(💡 \*\*.*?\*\*)', r'\n---\n\n\1', formatted)
        formatted = re.sub(r'\n(⚠️ \*\*.*?\*\*)', r'\n---\n\n\1', formatted)
        formatted = re.sub(r'\n(✅ \*\*.*?\*\*)', r'\n---\n\n\1', formatted)
        
        # 14. Trim leading/trailing whitespace
        formatted = formatted.strip()
        
        # 15. Ensure the response starts cleanly
        if not formatted.startswith(('📊', '💰', '📈', '⚠️', '💡', '✅', '🎯', '📋', '🔍', '💼', '#')):
            # Add a nice header if missing
            formatted = f"📊 **Analysis**\n\n{formatted}"
        
        logger.info("Response formatted successfully")
        return formatted
        
    except Exception as e:
        logger.error(f"Error formatting response: {str(e)}")
        return raw_response  # Return original if formatting fails


def format_portfolio_summary(portfolio_data: dict) -> str:
    """
    Format portfolio summary as a nice markdown card
    
    Args:
        portfolio_data: Dictionary with portfolio metrics
    
    Returns:
        Formatted markdown summary
    """
    try:
        total_value = portfolio_data.get('total_value', 0)
        total_invested = portfolio_data.get('total_invested', 0)
        total_gain = total_value - total_invested
        gain_pct = (total_gain / total_invested * 100) if total_invested > 0 else 0
        xirr = portfolio_data.get('xirr', 0)
        
        allocation = portfolio_data.get('allocation', {})
        equity_pct = allocation.get('Equity', 0)
        debt_pct = allocation.get('Debt', 0)
        hybrid_pct = allocation.get('Hybrid', 0)
        
        summary = f"""
## 💰 Portfolio Overview

| Metric | Value |
|--------|-------|
| **Total Current Value** | ₹{total_value:,.2f} |
| **Total Invested** | ₹{total_invested:,.2f} |
| **Total Gains** | ₹{total_gain:,.2f} ({gain_pct:+.2f}%) |
| **XIRR** | {xirr:.2f}% |

### 📊 Asset Allocation

```
Equity: {equity_pct:.1f}% │ Debt: {debt_pct:.1f}% │ Hybrid: {hybrid_pct:.1f}%
```

---
"""
        return summary.strip()
        
    except Exception as e:
        logger.error(f"Error formatting portfolio summary: {str(e)}")
        return "Unable to format portfolio summary"


def format_comparison_table(funds_data: list) -> str:
    """
    Format fund comparison as a markdown table
    
    Args:
        funds_data: List of fund dictionaries with metrics
    
    Returns:
        Formatted markdown table
    """
    try:
        if not funds_data:
            return "No funds to compare"
        
        # Build table header
        table = "\n## 📊 Fund Comparison\n\n"
        table += "| Metric | " + " | ".join([f["name"] for f in funds_data]) + " |\n"
        table += "|" + "---|" * (len(funds_data) + 1) + "\n"
        
        # Add rows for each metric
        metrics = [
            ("1Y Return", "return_1y", "%"),
            ("3Y Return", "return_3y", "%"),
            ("5Y Return", "return_5y", "%"),
            ("Expense Ratio", "expense_ratio", "%"),
            ("AUM", "aum", "Cr"),
            ("Risk", "risk", "")
        ]
        
        for metric_name, key, suffix in metrics:
            row = f"| **{metric_name}** | "
            values = []
            for fund in funds_data:
                value = fund.get(key, "-")
                if value != "-" and suffix:
                    values.append(f"{value}{suffix}")
                else:
                    values.append(str(value))
            row += " | ".join(values) + " |"
            table += row + "\n"
        
        return table
        
    except Exception as e:
        logger.error(f"Error formatting comparison table: {str(e)}")
        return "Unable to format comparison table"


def add_section_divider(text: str, section_title: str) -> str:
    """Add a styled section divider"""
    return f"\n\n---\n\n## {section_title}\n\n{text}"


def format_bullet_list(items: list, emoji: str = "•") -> str:
    """Format a list of items as markdown bullets"""
    return "\n".join([f"{emoji} {item}" for item in items])


def format_numbered_list(items: list) -> str:
    """Format a list of items as numbered markdown list"""
    return "\n".join([f"{i+1}. {item}" for i, item in enumerate(items)])


# Emoji mappings for different contexts
EMOJI_MAP = {
    'positive': '✅',
    'negative': '⚠️',
    'neutral': '💡',
    'value': '💰',
    'return': '📈',
    'risk': '⚠️',
    'goal': '🎯',
    'strategy': '📋',
    'analysis': '📊',
    'market': '🔍',
    'tax': '💼',
    'action': '✅',
    'warning': '🚨',
    'info': 'ℹ️'
}


def get_emoji(context: str) -> str:
    """Get appropriate emoji for context"""
    return EMOJI_MAP.get(context.lower(), '•')
