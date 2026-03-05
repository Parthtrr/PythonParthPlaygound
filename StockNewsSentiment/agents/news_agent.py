from ..services.news_service import NewsService
import json
import requests


class NewsAgent:

    def __init__(self):
        self.news_service = NewsService()

        # fetch wide market news once
        self.wide_market_news = self.news_service.fetch(
            "National and International news that impacts Indian stock market"
        )

    def call_llm(self, prompt: str):

        try:
            response = requests.post(
                "http://127.0.0.1:11434/api/generate",
                json={
                    "model": "llama3",
                    "prompt": prompt,
                    "stream": False
                }
            )

            response.raise_for_status()

            return response.json()["response"]

        except requests.RequestException as e:
            print(f"Error sending request to LLM: {e}")
            return None

    def get_latest_news(self, stock_name: str, sector: str):

        # query formation responsibility moved here
        stock_query = f"{stock_name} stock NSE OR BSE"
        sector_query = f"{sector} sector stock India"

        stock_news = self.news_service.fetch(stock_query)
        sector_news = self.news_service.fetch(sector_query)

        stock_news = stock_news[:5]
        sector_news = sector_news[:5]
        wide_market_news = self.wide_market_news[:5]

        stock_news_text = json.dumps(stock_news, indent=2)
        sector_news_text = json.dumps(sector_news, indent=2)
        market_news_text = json.dumps(wide_market_news, indent=2)

        prompt = f"""
You are a financial news analyst.

Analyze the following news and determine sentiment impact for stock investing.

Consider three layers of news:

1. Stock specific news
2. Sector level news
3. Overall market news

Return the result strictly in JSON format:

{{
"stock_sentiment": "Positive | Negative | Neutral",
"sector_sentiment": "Positive | Negative | Neutral",
"market_sentiment": "Positive | Negative | Neutral",
"Trading Sentiment": "The stock is  positive only if all the news ie market sector and stock are positive if any one news is marked not positive then make the trading sentiment as negative - just tell positive or negative"
"Reason" : Explain the reason for sentiment
"top_stock_news": most defining one single top news,
"top_sector_news": most defining one single top news,
"top_market_news": most defining one single top news,
}}

------------ STOCK NEWS ({stock_name}) ------------

{stock_news_text}

------------ SECTOR NEWS ({sector}) ------------

{sector_news_text}

------------ MARKET NEWS ------------

{market_news_text}
"""

        # print(f"prompt = {market_news_text}")

        return self.call_llm(prompt)