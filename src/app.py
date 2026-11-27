"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import hashlib
import hmac
import json
import logging
import os
import secrets
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware import Middleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

logger = logging.getLogger(__name__)
session_secret = os.environ.get("SESSION_SECRET")
if not session_secret:
    logger.warning(
        "SESSION_SECRET is not set; using a temporary session secret. "
        "Set SESSION_SECRET to keep teacher sessions valid across restarts."
    )
    session_secret = secrets.token_urlsafe(32)

app = FastAPI(
    title="Mergington High School API",
    description="API for viewing and signing up for extracurricular activities",
    middleware=[
        Middleware(
            SessionMiddleware,
            secret_key=session_secret,
            same_site="strict",
            https_only=os.environ.get("COOKIE_SECURE", "").lower() == "true",
        )
    ],
)

credentials_file = Path(
    os.environ.get(
        "TEACHER_CREDENTIALS_FILE",
        Path(__file__).parent / "teacher_credentials.json",
    )
)


class LoginRequest(BaseModel):
    username: str
    password: str


def load_teacher_credentials():
    try:
        credentials = json.loads(credentials_file.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503,
            detail="Teacher login is not configured.",
        ) from error
    except (OSError, json.JSONDecodeError) as error:
        logger.exception("Could not read teacher credentials")
        raise HTTPException(
            status_code=500,
            detail="Teacher credentials configuration is invalid.",
        ) from error

    teachers = credentials.get("teachers") if isinstance(credentials, dict) else None
    if not isinstance(teachers, list):
        raise HTTPException(
            status_code=500,
            detail="Teacher credentials configuration is invalid.",
        )
    return teachers


def require_teacher(request: Request):
    username = request.session.get("teacher")
    if not username:
        raise HTTPException(status_code=401, detail="Teacher login required.")
    return username


@app.post("/auth/login")
def login(credentials: LoginRequest, request: Request):
    for teacher in load_teacher_credentials():
        if not isinstance(teacher, dict) or teacher.get("username") != credentials.username:
            continue

        salt = teacher.get("salt")
        stored_hash = teacher.get("password_hash")
        iterations = teacher.get("iterations")
        if (
            not isinstance(salt, str)
            or not isinstance(stored_hash, str)
            or not isinstance(iterations, int)
            or isinstance(iterations, bool)
            or not 100_000 <= iterations <= 1_000_000
        ):
            raise HTTPException(
                status_code=500,
                detail="Teacher credentials configuration is invalid.",
            )

        candidate_hash = hashlib.pbkdf2_hmac(
            "sha256",
            credentials.password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        ).hex()
        if hmac.compare_digest(candidate_hash, stored_hash):
            request.session.clear()
            request.session["teacher"] = credentials.username
            return {"authenticated": True, "username": credentials.username}
        break

    raise HTTPException(status_code=401, detail="Invalid username or password.")


@app.get("/auth/status")
def auth_status(request: Request):
    username = request.session.get("teacher")
    return {"authenticated": bool(username), "username": username}


@app.post("/auth/logout")
def logout(request: Request):
    request.session.clear()
    return {"authenticated": False}

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, request: Request):
    """Sign up a student for an activity"""
    require_teacher(request)

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, request: Request):
    """Unregister a student from an activity"""
    require_teacher(request)

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
