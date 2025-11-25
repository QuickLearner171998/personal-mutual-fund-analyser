"""
Formatting utilities for the application.
"""

def format_currency(amount: float) -> str:
    """
    Format amount in Indian currency format (Lakhs/Crores).
    Example: 1234567.89 -> ₹12,34,567
    """
    if amount is None:
        return "₹0"
        
    # Convert to string and split integer/decimal
    s = f"{int(amount)}"
    
    # Handle negative numbers
    is_negative = False
    if s.startswith('-'):
        is_negative = True
        s = s[1:]
    
    # Format integer part
    if len(s) <= 3:
        formatted = s
    else:
        # Last 3 digits
        last_three = s[-3:]
        # Remaining digits
        remaining = s[:-3]
        # Add commas every 2 digits from right
        formatted_remaining = ""
        while len(remaining) > 2:
            formatted_remaining = "," + remaining[-2:] + formatted_remaining
            remaining = remaining[:-2]
        formatted_remaining = remaining + formatted_remaining
        
        formatted = formatted_remaining + "," + last_three
        
    # Add negative sign if needed
    if is_negative:
        formatted = "-" + formatted
        
    return f"₹{formatted}"

def format_lakhs_crores(amount: float) -> str:
    """
    Format large numbers into Lakhs/Crores text.
    Example: 1500000 -> 15.00 L
    """
    if amount >= 10000000:
        return f"₹{amount/10000000:.2f} Cr"
    elif amount >= 100000:
        return f"₹{amount/100000:.2f} L"
    else:
        return format_currency(amount)
