from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api.routes import jobs, coins, companies, exchanges, stats, charts

# Lifespan context
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting crypto jobs API...")
    yield
    # Shutdown
    print("🛑 Shutting down crypto jobs API...")

app = FastAPI(
    title="Crypto Jobs API",
    description="Professional dashboard API for crypto job market analytics",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(coins.router, prefix="/api/coins", tags=["coins"])
app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
app.include_router(exchanges.router, prefix="/api/exchanges", tags=["exchanges"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(charts.router, prefix="/api/charts", tags=["charts"])

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "crypto-jobs-api",
        "version": "1.0.0",
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "Crypto Jobs API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
