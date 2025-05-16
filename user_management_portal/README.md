# User Management Portal

## Description

The **User Management Portal** is a full-stack application for managing users within an organization. It allows administrators to create, read, update, and delete users, as well as view and group users by department. It features robust validations, error handling, and a modern, responsive interface.

## Screenshots

> **Main dashboard with user table**
>
> ![Dashboard](./screenshots/dashboard.png)

> **Edit user modal**
>
> ![Edit User](./screenshots/edit_user.png)

> **Delete confirmation dialog**
>
> ![Delete Confirmation](./screenshots/delete_confirmation.png)

> **Create user modal with validation**
>
> ![Create User Validation](./screenshots/create_user_validation.png)

## Technologies Used

- **Backend:** FastAPI, SQLAlchemy, SQLite, Pydantic, Passlib
- **Frontend:** React, Material-UI (MUI), Axios
- **Others:** Docker (optional), Python-dotenv

## Architecture

- **Backend:**
  - RESTful API built with FastAPI
  - SQLite database
  - Models and validations with SQLAlchemy and Pydantic
  - Password encryption with Passlib
  - Logging and error handling
  - Automatic documentation with Swagger (OpenAPI)

- **Frontend:**
  - React application with Material-UI
  - Dynamic table to display users (DataGrid)
  - Modal forms for creating and editing users
  - Real-time validations
  - Confirmation dialog for deleting users

## Main Features

- **User CRUD:** Create, read, update, and delete users
- **Validations:**
  - Unique and valid email
  - Unique username, 6-20 characters, alphanumeric only
  - Minimum password length of 8 characters
  - Valid department (Tech, RRHH, Sales)
- **Table grouped by department**
- **Sorting and filtering**
- **Delete confirmation**
- **Clear error handling and messages**

## Installation and Usage

### 1. Clone the repository
```bash
git clone <REPOSITORY_URL>
cd user-management-portal
```

### 2. Backend (FastAPI)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
- Access the API documentation at: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

### 3. Frontend (React)
```bash
cd ../frontend
npm install
npm start
```
- Access the application at: [http://localhost:3000](http://localhost:3000)

## Notes
- If you see the message "MUI X Missing license key", you can switch to the free version of DataGrid (`@mui/x-data-grid`) if you do not need advanced features.
- The default database is SQLite, but you can adapt the configuration for other engines.

## License
This project is for educational and demonstration purposes only.
