# agents/news_agent.py

import finnhub
import time
from datetime import datetime, timedelta
from transformers import pipeline
from agents.base_agent import BaseAgent, AgentResult, AgentError


class NewsIntelligenceAgent(BaseAgent):
    """
    Agent 2: News Intelligence Agent

    Fetches recent financial news for a stock using Finnhub,
    then scores each headline using FinBERT — a sentiment model
    trained specifically on financial text.

    Score interpretation:
        +100 = extremely positive news
           0 = neutral news
        -100 = extremely negative news
    """

    def __init__(self):
        super().__init__(name="NewsIntelligenceAgent", max_retries=2)
        from config.settings import settings
        self.client = finnhub.Client(api_key=settings.FINNHUB_API_KEY)
        self.finbert = None  # Load lazily on first use

    def _get_finbert(self):
        """Load FinBERT only when needed — saves memory at startup."""
        if self.finbert is None:
            # pyrefly: ignore [missing-import]
            from transformers import pipeline
            self.logger.info("Loading FinBERT model...")
            self.finbert = pipeline(
                task="sentiment-analysis",
                model="ProsusAI/finbert",
                tokenizer="ProsusAI/finbert",
                max_length=512,
                truncation=True
        )
            self.logger.info("FinBERT loaded successfully")
        return self.finbert

    def execute(self, symbol: str, days_back: int = 7, **kwargs) -> AgentResult:
        """
        Fetch and analyze news for a stock symbol.

        Args:
            symbol   : stock ticker e.g. 'AAPL'
            days_back: how many days of news to fetch (default 7)
        """
        self.logger.info(f"Fetching news for {symbol} | last {days_back} days")

        # --- Step 1: Fetch news from Finnhub ---
        articles = self._fetch_news(symbol, days_back)

        if not articles:
            self.logger.warning(f"No news found for {symbol}")
            return AgentResult(
                agent_name=self.name,
                success=True,
                data={"articles": [], "analyzed": []},
                score=0.0,
                metadata={"symbol": symbol, "articles_found": 0}
            )

        # --- Step 2: Analyze sentiment with FinBERT ---
        analyzed = self._analyze_sentiment(articles)

        # --- Step 3: Calculate overall news impact score ---
        score = self._calculate_news_score(analyzed)

        self.logger.info(
            f"{symbol} | Articles: {len(analyzed)} | "
            f"News Score: {score}"
        )

        return AgentResult(
            agent_name=self.name,
            success=True,
            data={
                "articles"  : articles,
                "analyzed"  : analyzed,
            },
            score=score,
            metadata={
                "symbol"        : symbol,
                "articles_found": len(articles),
                "days_back"     : days_back
            }
        )

    def _fetch_news(self, symbol: str, days_back: int) -> list:
        """
        Fetch recent news articles from Finnhub.
        Returns list of article dicts with headline, summary, datetime.
        """
        end_date   = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Finnhub expects dates as YYYY-MM-DD strings
        from_date = start_date.strftime("%Y-%m-%d")
        to_date   = end_date.strftime("%Y-%m-%d")

        try:
            news = self.client.company_news(symbol, _from=from_date, to=to_date)
        except Exception as e:
            raise AgentError(f"Finnhub API error: {e}")

        # Clean and normalize
        articles = []
        for item in news[:20]:  # cap at 20 articles
            headline = item.get("headline", "").strip()
            if headline:
                articles.append({
                    "headline" : headline,
                    "summary"  : item.get("summary", "")[:300],
                    "source"   : item.get("source", ""),
                    "datetime" : datetime.fromtimestamp(
                        item.get("datetime", 0)
                    ).strftime("%Y-%m-%d %H:%M"),
                    "url"      : item.get("url", "")
                })

        return articles

    def _analyze_sentiment(self, articles: list) -> list:
        """
        Run each headline through FinBERT.
        FinBERT returns: positive / negative / neutral + confidence score
        """
        analyzed = []

        for article in articles:
            try:
                result = self._get_finbert()(article["headline"])[0]

                # Convert FinBERT label to numeric impact
                label      = result["label"].lower()    # positive/negative/neutral
                confidence = result["score"]            # 0.0 to 1.0

                # Map to impact score
                if label == "positive":
                    impact = round(confidence * 100, 2)
                elif label == "negative":
                    impact = round(-confidence * 100, 2)
                else:
                    impact = 0.0

                analyzed.append({
                    "headline"  : article["headline"],
                    "source"    : article["source"],
                    "datetime"  : article["datetime"],
                    "sentiment" : label,
                    "confidence": round(confidence, 4),
                    "impact"    : impact,
                    "url"       : article["url"]
                })

            except Exception as e:
                self.logger.warning(f"FinBERT failed on headline: {e}")
                continue

        return analyzed

    def _calculate_news_score(self, analyzed: list) -> float:
        """
        Aggregate individual article impacts into one score.

        Method: weighted average where recent articles count more.
        Articles are already sorted newest-first from Finnhub.
        """
        if not analyzed:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0

        for i, article in enumerate(analyzed):
            # More recent articles get higher weight
            # Article 0 (newest) gets weight 1.0
            # Article 1 gets 0.9, Article 2 gets 0.8 etc.
            weight = max(1.0 - (i * 0.1), 0.1)

            weighted_sum += article["impact"] * weight
            total_weight += weight

        raw_score = weighted_sum / total_weight

        # Clamp to -100 to +100
        return round(max(min(raw_score, 100), -100), 2)

    def validate_output(self, result: AgentResult) -> bool:
        if not result.success:
            return False
        if result.score is None:
            return False
        if not (-100 <= result.score <= 100):
            return False
        return True