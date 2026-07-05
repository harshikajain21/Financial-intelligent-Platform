# create_stock_db.py

content = """
# data/stock_universe.py
# Stock search database — company name to ticker mapping

STOCK_UNIVERSE = {
    # ── US Stocks ──────────────────────────────────────────────
    "Apple":                    {"symbol": "AAPL",      "market": "US",     "name": "Apple Inc"},
    "Microsoft":                {"symbol": "MSFT",      "market": "US",     "name": "Microsoft Corporation"},
    "Google":                   {"symbol": "GOOGL",     "market": "US",     "name": "Alphabet Inc"},
    "Alphabet":                 {"symbol": "GOOGL",     "market": "US",     "name": "Alphabet Inc"},
    "Amazon":                   {"symbol": "AMZN",      "market": "US",     "name": "Amazon.com Inc"},
    "Tesla":                    {"symbol": "TSLA",      "market": "US",     "name": "Tesla Inc"},
    "Meta":                     {"symbol": "META",      "market": "US",     "name": "Meta Platforms Inc"},
    "Facebook":                 {"symbol": "META",      "market": "US",     "name": "Meta Platforms Inc"},
    "Nvidia":                   {"symbol": "NVDA",      "market": "US",     "name": "NVIDIA Corporation"},
    "Netflix":                  {"symbol": "NFLX",      "market": "US",     "name": "Netflix Inc"},
    "JPMorgan":                 {"symbol": "JPM",       "market": "US",     "name": "JPMorgan Chase & Co"},
    "Goldman Sachs":            {"symbol": "GS",        "market": "US",     "name": "Goldman Sachs Group"},
    "Berkshire":                {"symbol": "BRK-B",     "market": "US",     "name": "Berkshire Hathaway"},
    "Visa":                     {"symbol": "V",         "market": "US",     "name": "Visa Inc"},
    "Mastercard":               {"symbol": "MA",        "market": "US",     "name": "Mastercard Inc"},
    "Johnson & Johnson":        {"symbol": "JNJ",       "market": "US",     "name": "Johnson & Johnson"},
    "Walmart":                  {"symbol": "WMT",       "market": "US",     "name": "Walmart Inc"},
    "Exxon":                    {"symbol": "XOM",       "market": "US",     "name": "Exxon Mobil Corporation"},
    "Procter & Gamble":         {"symbol": "PG",        "market": "US",     "name": "Procter & Gamble Co"},
    "Coca Cola":                {"symbol": "KO",        "market": "US",     "name": "The Coca-Cola Company"},
    "Disney":                   {"symbol": "DIS",       "market": "US",     "name": "The Walt Disney Company"},
    "AMD":                      {"symbol": "AMD",       "market": "US",     "name": "Advanced Micro Devices"},
    "Intel":                    {"symbol": "INTC",      "market": "US",     "name": "Intel Corporation"},
    "Salesforce":               {"symbol": "CRM",       "market": "US",     "name": "Salesforce Inc"},
    "Adobe":                    {"symbol": "ADBE",      "market": "US",     "name": "Adobe Inc"},
    "PayPal":                   {"symbol": "PYPL",      "market": "US",     "name": "PayPal Holdings"},
    "Uber":                     {"symbol": "UBER",      "market": "US",     "name": "Uber Technologies"},
    "Airbnb":                   {"symbol": "ABNB",      "market": "US",     "name": "Airbnb Inc"},
    "Spotify":                  {"symbol": "SPOT",      "market": "US",     "name": "Spotify Technology"},
    "Twitter":                  {"symbol": "X",         "market": "US",     "name": "X Corp"},
    "Oracle":                   {"symbol": "ORCL",      "market": "US",     "name": "Oracle Corporation"},
    "IBM":                      {"symbol": "IBM",       "market": "US",     "name": "IBM Corporation"},
    "Qualcomm":                 {"symbol": "QCOM",      "market": "US",     "name": "Qualcomm Inc"},
    "Pfizer":                   {"symbol": "PFE",       "market": "US",     "name": "Pfizer Inc"},
    "Bank of America":          {"symbol": "BAC",       "market": "US",     "name": "Bank of America Corp"},
    "Citigroup":                {"symbol": "C",         "market": "US",     "name": "Citigroup Inc"},
    "Morgan Stanley":           {"symbol": "MS",        "market": "US",     "name": "Morgan Stanley"},

    # ── Indian Stocks (NSE) ────────────────────────────────────
    "Reliance":                 {"symbol": "RELIANCE.NS",   "market": "IN", "name": "Reliance Industries"},
    "Reliance Industries":      {"symbol": "RELIANCE.NS",   "market": "IN", "name": "Reliance Industries"},
    "TCS":                      {"symbol": "TCS.NS",        "market": "IN", "name": "Tata Consultancy Services"},
    "Tata Consultancy":         {"symbol": "TCS.NS",        "market": "IN", "name": "Tata Consultancy Services"},
    "Infosys":                  {"symbol": "INFY.NS",       "market": "IN", "name": "Infosys Limited"},
    "HDFC Bank":                {"symbol": "HDFCBANK.NS",   "market": "IN", "name": "HDFC Bank Limited"},
    "HDFC":                     {"symbol": "HDFCBANK.NS",   "market": "IN", "name": "HDFC Bank Limited"},
    "ICICI Bank":               {"symbol": "ICICIBANK.NS",  "market": "IN", "name": "ICICI Bank Limited"},
    "ICICI":                    {"symbol": "ICICIBANK.NS",  "market": "IN", "name": "ICICI Bank Limited"},
    "Wipro":                    {"symbol": "WIPRO.NS",      "market": "IN", "name": "Wipro Limited"},
    "HCL":                      {"symbol": "HCLTECH.NS",    "market": "IN", "name": "HCL Technologies"},
    "HCL Technologies":         {"symbol": "HCLTECH.NS",    "market": "IN", "name": "HCL Technologies"},
    "Bajaj Finance":            {"symbol": "BAJFINANCE.NS", "market": "IN", "name": "Bajaj Finance Limited"},
    "Bajaj":                    {"symbol": "BAJFINANCE.NS", "market": "IN", "name": "Bajaj Finance Limited"},
    "Asian Paints":             {"symbol": "ASIANPAINT.NS", "market": "IN", "name": "Asian Paints Limited"},
    "Maruti":                   {"symbol": "MARUTI.NS",     "market": "IN", "name": "Maruti Suzuki India"},
    "Maruti Suzuki":            {"symbol": "MARUTI.NS",     "market": "IN", "name": "Maruti Suzuki India"},
    "Sun Pharma":               {"symbol": "SUNPHARMA.NS",  "market": "IN", "name": "Sun Pharmaceutical"},
    "Tata Motors":              {"symbol": "TATAMOTORS.NS", "market": "IN", "name": "Tata Motors Limited"},
    "Tata Steel":               {"symbol": "TATASTEEL.NS",  "market": "IN", "name": "Tata Steel Limited"},
    "Kotak Bank":               {"symbol": "KOTAKBANK.NS",  "market": "IN", "name": "Kotak Mahindra Bank"},
    "Kotak":                    {"symbol": "KOTAKBANK.NS",  "market": "IN", "name": "Kotak Mahindra Bank"},
    "Axis Bank":                {"symbol": "AXISBANK.NS",   "market": "IN", "name": "Axis Bank Limited"},
    "Axis":                     {"symbol": "AXISBANK.NS",   "market": "IN", "name": "Axis Bank Limited"},
    "Larsen":                   {"symbol": "LT.NS",         "market": "IN", "name": "Larsen & Toubro"},
    "L&T":                      {"symbol": "LT.NS",         "market": "IN", "name": "Larsen & Toubro"},
    "ITC":                      {"symbol": "ITC.NS",        "market": "IN", "name": "ITC Limited"},
    "ONGC":                     {"symbol": "ONGC.NS",       "market": "IN", "name": "Oil & Natural Gas Corp"},
    "Power Grid":               {"symbol": "POWERGRID.NS",  "market": "IN", "name": "Power Grid Corporation"},
    "NTPC":                     {"symbol": "NTPC.NS",       "market": "IN", "name": "NTPC Limited"},
    "Adani Ports":              {"symbol": "ADANIPORTS.NS", "market": "IN", "name": "Adani Ports & SEZ"},
    "Adani":                    {"symbol": "ADANIPORTS.NS", "market": "IN", "name": "Adani Ports & SEZ"},
    "Bharti Airtel":            {"symbol": "BHARTIARTL.NS", "market": "IN", "name": "Bharti Airtel Limited"},
    "Airtel":                   {"symbol": "BHARTIARTL.NS", "market": "IN", "name": "Bharti Airtel Limited"},
    "Zomato":                   {"symbol": "ZOMATO.NS",     "market": "IN", "name": "Zomato Limited"},
    "Paytm":                    {"symbol": "PAYTM.NS",      "market": "IN", "name": "One97 Communications"},
    "Nifty 50":                 {"symbol": "^NSEI",         "market": "IN", "name": "Nifty 50 Index"},
    "Sensex":                   {"symbol": "^BSESN",        "market": "IN", "name": "BSE Sensex Index"},

    # ── Global Stocks ──────────────────────────────────────────
    "Samsung":                  {"symbol": "005930.KS",  "market": "KR", "name": "Samsung Electronics"},
    "Toyota":                   {"symbol": "TM",         "market": "JP", "name": "Toyota Motor Corporation"},
    "Sony":                     {"symbol": "SONY",       "market": "JP", "name": "Sony Group Corporation"},
    "TSMC":                     {"symbol": "TSM",        "market": "TW", "name": "Taiwan Semiconductor"},
    "Alibaba":                  {"symbol": "BABA",       "market": "CN", "name": "Alibaba Group"},
    "Tencent":                  {"symbol": "TCEHY",      "market": "CN", "name": "Tencent Holdings"},
    "SAP":                      {"symbol": "SAP",        "market": "DE", "name": "SAP SE"},
    "ASML":                     {"symbol": "ASML",       "market": "NL", "name": "ASML Holding"},
    "Nestle":                   {"symbol": "NSRGY",      "market": "CH", "name": "Nestle S.A."},
    "LVMH":                     {"symbol": "LVMUY",      "market": "FR", "name": "LVMH Moet Hennessy"},
    "Shell":                    {"symbol": "SHEL",       "market": "UK", "name": "Shell PLC"},
    "BP":                       {"symbol": "BP",         "market": "UK", "name": "BP PLC"},
    "HSBC":                     {"symbol": "HSBC",       "market": "UK", "name": "HSBC Holdings"},
}


def search_stocks(query: str, limit: int = 8) -> list:
    \"\"\"
    Search stocks by company name or ticker symbol.
    Returns list of matches sorted by relevance.
    \"\"\"
    query = query.strip().lower()
    if not query or len(query) < 2:
        return []

    results = []

    for name, info in STOCK_UNIVERSE.items():
        name_lower = name.lower()
        symbol_lower = info["symbol"].lower().replace(".ns", "").replace(".bo", "")

        # Exact match gets highest priority
        if query == name_lower or query == symbol_lower:
            results.append({"match_score": 100, "name": name, **info})

        # Starts with query
        elif name_lower.startswith(query) or symbol_lower.startswith(query):
            results.append({"match_score": 80, "name": name, **info})

        # Contains query
        elif query in name_lower or query in symbol_lower:
            results.append({"match_score": 60, "name": name, **info})

    # Sort by score, remove duplicates by symbol
    seen = set()
    unique = []
    for r in sorted(results, key=lambda x: x["match_score"], reverse=True):
        if r["symbol"] not in seen:
            seen.add(r["symbol"])
            unique.append(r)

    return unique[:limit]


def resolve_symbol(query: str, exchange: str = "NSE") -> str:
    \"\"\"
    Convert company name or ticker to the correct symbol.
    For Indian stocks, applies NSE (.NS) or BSE (.BO) suffix.
    \"\"\"
    query = query.strip()

    # Direct ticker input — check if Indian stock needs suffix
    if query.upper() in [s["symbol"].replace(".NS","").replace(".BO","")
                         for s in STOCK_UNIVERSE.values() if s["market"] == "IN"]:
        suffix = ".NS" if exchange == "NSE" else ".BO"
        return query.upper() + suffix

    # Search by name
    results = search_stocks(query)
    if results:
        symbol = results[0]["symbol"]
        # If Indian stock and user wants BSE, swap suffix
        if results[0]["market"] == "IN" and exchange == "BSE":
            symbol = symbol.replace(".NS", ".BO")
        return symbol

    # Return as-is (might be a valid ticker we don't have in our list)
    return query.upper()
"""

with open("data/stock_universe.py", "w", encoding="utf-8") as f:
    f.write(content.strip())
    print("data/stock_universe.py written successfully")