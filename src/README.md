# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Teacher-only student signup and unregister controls
- Teacher login using credentials stored as password hashes

## Getting Started

1. Install the dependencies:

   ```
   pip install -r requirements.txt
   ```

2. From the repository root, create a teacher account and start the application:

   ```
   python src/create_teacher_credentials.py
   cd src && uvicorn app:app --reload
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/auth/login`                                                      | Log in as a teacher                                                  |
| GET    | `/auth/status`                                                     | Check teacher login status                                           |
| POST   | `/auth/logout`                                                     | Log out                                                              |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Register a student (teacher login required)                         |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister a student (teacher login required)                    |

## Teacher setup

Create a teacher account by running `python src/create_teacher_credentials.py`.
The helper prompts for a username and password, then stores a salted PBKDF2
password hash in `src/teacher_credentials.json`. That file is ignored by Git.
Run the helper again to add additional teachers.

Set `SESSION_SECRET` to a long, random value before starting the server so
teacher sessions remain valid across restarts. For example, generate one with
`python -c "import secrets; print(secrets.token_urlsafe(32))"` and set it in
your environment. If the app is served over HTTPS, also set
`COOKIE_SECURE=true` so the session cookie is only sent over HTTPS.

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
