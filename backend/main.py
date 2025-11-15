from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
import jwt
import os
from dotenv import load_dotenv

from database import engine, Base, get_db, SessionLocal
from models.db_models import User, Puller, Ride, Location, RideStatus
from routers import rides, pullers, admin, auth

load_dotenv()

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize background scheduler for timeout tasks (MVP requirement)
scheduler = BackgroundScheduler()

def check_ride_timeouts():
    """
    Background task to check for ride timeouts (MVP requirement)
    Runs every 10 seconds, marks rides > 60 seconds as TIMEOUT
    """
    db = SessionLocal()
    try:
        timeout_threshold = datetime.utcnow() - timedelta(seconds=60)
        
        # Find pending rides that have exceeded 60 seconds
        expired_rides = db.query(Ride).filter(
            Ride.status == RideStatus.PENDING,
            Ride.requested_at < timeout_threshold
        ).all()
        
        for ride in expired_rides:
            ride.status = RideStatus.TIMEOUT
            print(f"Ride {ride.ride_id} marked as TIMEOUT")
        
        if expired_rides:
            db.commit()
            print(f"Marked {len(expired_rides)} rides as timeout")
    except Exception as e:
        print(f"Error in timeout checker: {e}")
        db.rollback()
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Modern lifespan context manager for startup and shutdown events
    Replaces deprecated @app.on_event decorators
    """
    # Startup
    print("AERAS Backend started")
    scheduler.add_job(check_ride_timeouts, 'interval', seconds=10)
    scheduler.start()
    print("Background timeout checker started (10s interval)")
    
    yield
    
    # Shutdown
    scheduler.shutdown()
    print("Background scheduler stopped")

app = FastAPI(title="AERAS E-Rickshaw Backend", lifespan=lifespan)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
