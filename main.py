"""Main FastAPI application."""

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from src.database import create_tables
from src.services.seed_data import seed_if_empty
from src.api import game, author


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup code
    create_tables()
    # Run seeding in a background worker so it creates/commits its own session
    # (keeps startup non-blocking and ensures seeds persist).
    await seed_if_empty(in_background=True)
    yield
    # Shutdown code
    # (none for now)


# FastAPI Setup
app = FastAPI(title='DwarfWeave Backend', version="0.1", lifespan=lifespan)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(game.router, prefix="/api", tags=["game"])
app.include_router(author.router, prefix="/author", tags=["author"])


@app.get('/health')
def health():
    """Health check endpoint."""
    return {'ok': True, "time": datetime.now(timezone.utc).isoformat() + "Z"}
