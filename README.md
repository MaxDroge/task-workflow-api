# Task & Workflow API

This project is a RESTful API for managing workflow tasks. It allows users to create, retrieve, update, filter, and delete tasks while tracking priority, status, assignee, and due date information.

## Features

- Create workflow tasks
- View all tasks
- View a single task by ID
- Update task details
- Delete tasks
- Filter tasks by status
- Filter tasks by priority
- Validate structured workflow values

## Tech Used

- Python
- FastAPI
- SQLite
- SQLAlchemy
- Pydantic

## How to Run

1. Install dependencies:
   pip install -r requirements.txt

2. Start the server:
   uvicorn main:app --reload

3. Open API docs:
   http://127.0.0.1:8000/docs