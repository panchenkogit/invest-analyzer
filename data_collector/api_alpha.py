import aiohttp
from fastapi import HTTPException

async def fetch_single_ticker(session: aiohttp.ClientSession, ticker: str, api_key: str):
    """Получает данные по одному тикеру от Alpha Vantage."""
    url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}'
    async with session.get(url) as response:
        if response.status != 200:
            raise HTTPException(status_code=response.status, detail=await response.text())
        data = await response.json()
        if not data:
            raise HTTPException(status_code=404, detail=f"Data not found for {ticker}")
        return ticker, data