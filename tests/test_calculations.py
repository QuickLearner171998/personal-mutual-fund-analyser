"""
XIRR Calculation Tests
"""
from calculations.returns import calculate_xirr, calculate_cagr, calculate_absolute_return
from datetime import date, datetime

def test_xirr():
    """Test XIRR calculation with known values"""
    print("Testing XIRR Calculation...")
    
    # Test case 1: Simple SIP
    transactions = [
        {'date': date(2020, 1, 1), 'amount': 10000, 'type': 'purchase'},
        {'date': date(2020, 7, 1), 'amount': 10000, 'type': 'purchase'},
        {'date': date(2021, 1, 1), 'amount': 10000, 'type': 'purchase'},
        {'date': date(2021, 7, 1), 'amount': 10000, 'type': 'purchase'},
        {'date': date(2022, 1, 1), 'amount': 10000, 'type': 'purchase'},
    ]
    
    # Add current value as redemption
    transactions.append({
        'date': date(2022, 12, 31),
        'amount': 60000,  # Assumed current value
        'type': 'redemption'
    })
    
    xirr = calculate_xirr(transactions)
    print(f"Test 1 - Simple SIP XIRR: {xirr}%")
    
    # Test case 2: Single lumpsum
    transactions2 = [
        {'date': date(2020, 1, 1), 'amount': 100000, 'type': 'purchase'},
        {'date': date(2023, 1, 1), 'amount': 150000, 'type': 'redemption'}
    ]
    
    xirr2 = calculate_xirr(transactions2)
    print(f"Test 2 - Lumpsum XIRR: {xirr2}%")
    
    print("✓ XIRR tests completed")

def test_cagr():
    """Test CAGR calculation"""
    print("\nTesting CAGR Calculation...")
    
    # 3 year investment
    initial = 100000
    final = 150000
    years = 3
    
    cagr = calculate_cagr(initial, final, years)
    expected = 14.47  # Approximately
    
    print(f"CAGR for ₹{initial} → ₹{final} in {years} years: {cagr}%")
    print(f"Expected: ~{expected}%")
    
    if abs(cagr - expected) < 0.5:
        print("✓ CAGR test passed")
    else:
        print("⚠ CAGR test deviation")

def test_absolute_return():
    """Test absolute return calculation"""
    print("\nTesting Absolute Return...")
    
    invested = 100000
    current = 120000
    
    ret = calculate_absolute_return(invested, current)
    expected = 20.0
    
    print(f"Absolute return: {ret}%")
    print(f"Expected: {expected}%")
    
    if abs(ret - expected) < 0.01:
        print("✓ Absolute return test passed")
    else:
        print("⚠ Absolute return test failed")

if __name__ == "__main__":
    test_xirr()
    test_cagr()
    test_absolute_return()
    print("\n✅ All calculation tests completed!")
