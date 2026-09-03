import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Union

app = FastAPI()

# SECURITY FIX: Allow Vercel to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows any origin (including your Vercel URL)
    allow_methods=["*"],
    allow_headers=["*"],
)

class Candle(BaseModel):
    time: Union[int, str, float]
    open: float
    high: float
    low: float
    close: float

class OHLCRequest(BaseModel):
    symbol: str
    candles: List[Candle]

@app.post("/api/analyze-ohlc")
async def analyze_ohlc(data: OHLCRequest):
    if len(data.candles) < 5:
        raise HTTPException(status_code=400, detail="Select at least 5 candles.")

    target_candles = data.candles
    
    start_close = target_candles[0].close
    end_close = target_candles[-1].close
    
    price_change_pct = ((end_close - start_close) / start_close) * 100

    if price_change_pct > 0.05:
        pattern_name = "Bull Flag"
        confidence = min(0.99, 0.60 + (price_change_pct / 2))
    elif price_change_pct < -0.05:
        pattern_name = "Bearish Breakdown"
        confidence = min(0.99, 0.60 + (abs(price_change_pct) / 2))
    else:
        pattern_name = "Consolidation Channel"
        confidence = 0.85

    high_price = max(c.high for c in target_candles)
    low_price = min(c.low for c in target_candles)

    return {
        "success": True,
        "pattern": {
            "pattern": pattern_name,
            "confidence": round(confidence, 3),
            "startTime": target_candles[0].time,
            "endTime": target_candles[-1].time,
            "highPrice": high_price,
            "lowPrice": low_price
        }
    }

# PRODUCTION FIX: Bind to the dynamically assigned port
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)