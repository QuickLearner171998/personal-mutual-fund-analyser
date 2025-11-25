def _enrich_holdings_with_xirr(holdings: List[Dict], xirr_map: Dict) -> List[Dict]:
    """Add XIRR data to holdings from XIRR JSON"""
    
    for holding in holdings:
        # Try exact match first
        key = (holding['scheme_name'], holding['folio_number'])
        if key in xirr_map:
            holding['xirr'] = xirr_map[key]
        else:
            # Try fuzzy match on scheme name
            for (xirr_scheme, xirr_folio), xirr_value in xirr_map.items():
                if (xirr_folio == holding['folio_number'] and 
                    _schemes_match(xirr_scheme, holding['scheme_name'])):
                    holding['xirr'] = xirr_value
                    break
            else:
                holding['xirr'] = 0.0
    
    return holdings


def _calculate_portfolio_xirr(holdings: List[Dict]) -> float:
    """Calculate weighted average XIRR for portfolio"""
    if not holdings:
        return 0.0
    
    total_value = sum(h.get('current_value', 0) for h in holdings)
    if total_value == 0:
        return 0.0
    
    weighted_xirr = sum(
        h.get('xirr', 0) * h.get('current_value', 0)
        for h in holdings
    ) / total_value
    
    return round(weighted_xirr, 2)
