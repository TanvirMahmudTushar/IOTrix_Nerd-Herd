from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt
import os
from dotenv import load_dotenv

from database import engine, Base, get_db
from models.db_models import User, Puller, Ride, Location
from routers import rides, pullers, admin, auth

load_dotenv()

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AERAS E-Rickshaw Backend")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(rides.router, prefix="/api/rides", tags=["rides"])
app.include_router(pullers.router, prefix="/api/pullers", tags=["pullers"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

@app.get("/")
def read_root():
    return {"message": "AERAS E-Rickshaw API"}

@app.on_event("startup")
async def startup():
    print("AERAS Backend started")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
