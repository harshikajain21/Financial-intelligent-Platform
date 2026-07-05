# api/sanitizer.py

import re
from fastapi import HTTPException


def sanitize_symbol(symbol: str) -> str:
    """
    Clean and validate a stock symbol or company name.
    Allows letters, numbers, dots, hyphens (for symbols like BRK-B, RELIANCE.NS)
    Max 30 chars to prevent abuse.
    """
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol cannot be empty")

    symbol = symbol.strip()

    if len(symbol) > 30:
        raise HTTPException(
            status_code=400,
            detail="Symbol too long. Maximum 30 characters."
        )

    # Allow letters, numbers, dots, hyphens, spaces (for company names)
    if not re.match(r'^[A-Za-z0-9\s.\-&]+$', symbol):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid characters in symbol: '{symbol}'"
        )

    return symbol


def sanitize_query(query: str) -> str:
    """Clean search query — strip dangerous characters."""
    if not query:
        return ""
    query = query.strip()[:50]  # max 50 chars
    # Remove any special chars except letters, numbers, spaces
    query = re.sub(r'[^A-Za-z0-9\s.\-&]', '', query)
    return query


def sanitize_exchange(exchange: str) -> str:
    """Only allow known exchange values."""
    allowed = {"NSE", "BSE", "US"}
    exchange = exchange.upper().strip()
    if exchange not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid exchange. Allowed: NSE, BSE, US"
        )
    return exchange