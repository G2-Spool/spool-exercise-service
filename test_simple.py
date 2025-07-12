"""Simple test to verify basic FastAPI functionality."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Create a minimal FastAPI app
app = FastAPI(title="Simple Test")

@app.get("/")
async def root():
    return {"message": "Simple FastAPI is working"}

@app.get("/health")
async def health():
    return JSONResponse(content={"status": "healthy"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003) 