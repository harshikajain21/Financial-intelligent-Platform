# fix_sentiment_agent.py

content = """
# agents/sentiment_agent.py

import requests
from datetime import datetime
from agents.base_agent import BaseAgent, AgentResult, AgentError


class SocialSentimentAgent(BaseAgent):
    BASE_URL = "https://api.stocktwits.com/api/2/streams/symbol"

    def __init__(self, finbert_pipeline=None):
        super().__init__(name="SocialSentimentAgent", max_retries=2)
        self._finbert = finbert_pipeline

    def _get_finbert(self):
        if self._finbert is None:
            from transformers import pipeline
            self.logger.info("Loading FinBERT for sentiment agent...")
            self._finbert = pipeline(
                task="sentiment-analysis",
                model="ProsusAI/finbert",
                tokenizer="ProsusAI/finbert",
                max_length=512,
                truncation=True
            )
        return self._finbert

    def execute(self, symbol: str, **kwargs) -> AgentResult:
        self.logger.info(f"Fetching social sentiment for {symbol}")
        messages = self._fetch_messages(symbol)

        if not messages:
            self.logger.warning(f"No social messages found for {symbol}")
            return AgentResult(
                agent_name=self.name,
                success=True,
                data={"messages": [], "analyzed": []},
                score=0.0,
                metadata={"symbol": symbol, "messages_found": 0}
            )

        analyzed   = self._analyze_messages(messages)
        trend_data = self._calculate_trend_metrics(messages)
        score      = self._calculate_sentiment_score(analyzed)

        self.logger.info(
            f"{symbol} | Messages: {len(analyzed)} | "
            f"Sentiment Score: {score} | "
            f"Volume: {trend_data['message_count']}"
        )

        return AgentResult(
            agent_name=self.name,
            success=True,
            data={"analyzed": analyzed, "trend": trend_data},
            score=score,
            metadata={"symbol": symbol, "messages_found": len(messages)}
        )

    def _fetch_messages(self, symbol: str) -> list:
        url = f"{self.BASE_URL}/{symbol}.json"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json",
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            raise AgentError(f"StockTwits API error: {e}")

        messages = data.get("messages", [])
        cleaned  = []
        for msg in messages:
            body = msg.get("body", "").strip()
            if not body:
                continue
            entities       = msg.get("entities", {})
            sentiment_tag  = entities.get("sentiment")
            user_sentiment = sentiment_tag.get("basic") if sentiment_tag else None
            cleaned.append({
                "body"           : body,
                "created_at"     : msg.get("created_at", ""),
                "user_sentiment" : user_sentiment,
                "likes"          : msg.get("likes", {}).get("total", 0) if msg.get("likes") else 0,
            })
        return cleaned

    def _analyze_messages(self, messages: list) -> list:
        analyzed = []
        for msg in messages:
            if msg["user_sentiment"] == "Bullish":
                impact     = 80.0
                sentiment  = "positive"
                confidence = 1.0
            elif msg["user_sentiment"] == "Bearish":
                impact     = -80.0
                sentiment  = "negative"
                confidence = 1.0
            else:
                try:
                    result     = self._get_finbert()(msg["body"][:512])[0]
                    label      = result["label"].lower()
                    confidence = result["score"]
                    if label == "positive":
                        impact = round(confidence * 100, 2)
                    elif label == "negative":
                        impact = round(-confidence * 100, 2)
                    else:
                        impact = 0.0
                    sentiment = label
                except Exception:
                    continue

            analyzed.append({
                "body"      : msg["body"][:200],
                "sentiment" : sentiment,
                "impact"    : impact,
                "confidence": round(confidence, 4),
                "likes"     : msg["likes"],
                "source"    : "user_tag" if msg["user_sentiment"] else "finbert"
            })
        return analyzed

    def _calculate_trend_metrics(self, messages: list) -> dict:
        return {
            "message_count": len(messages),
            "total_likes"  : sum(m["likes"] for m in messages),
        }

    def _calculate_sentiment_score(self, analyzed: list) -> float:
        if not analyzed:
            return 0.0
        weighted_sum = 0.0
        total_weight = 0.0
        for msg in analyzed:
            weight        = 1.0 + min(msg["likes"] * 0.1, 5.0)
            weighted_sum += msg["impact"] * weight
            total_weight += weight
        if total_weight == 0:
            return 0.0
        return round(max(min(weighted_sum / total_weight, 100), -100), 2)

    def validate_output(self, result: AgentResult) -> bool:
        if not result.success:
            return False
        if result.score is None:
            return False
        if not (-100 <= result.score <= 100):
            return False
        return True
"""

with open("agents/sentiment_agent.py", "w", encoding="utf-8") as f:
    f.write(content.strip())
    print("agents/sentiment_agent.py rewritten successfully")