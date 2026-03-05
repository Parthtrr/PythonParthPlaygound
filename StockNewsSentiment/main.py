from StockNewsSentiment.agents.news_agent import NewsAgent
from StockNewsSentiment.config.settings import STOCK_TO_SECTOR, NUM_STOCKS_TO_COVER

if __name__ == "__main__":
    news_agent = NewsAgent()
    stocks_to_cover = list(STOCK_TO_SECTOR.keys())[:NUM_STOCKS_TO_COVER]

    for stock in stocks_to_cover:
        sector = STOCK_TO_SECTOR[stock]
        result = news_agent.get_latest_news(stock, sector)
        print(f"Stock: {stock}, Sector: {sector}")
        print(result)
