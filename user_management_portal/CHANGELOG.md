# Changelog

## [1.0.0] - Initial Release
### Added
- Full-stack user management portal with CRUD operations.
- Backend with FastAPI, SQLAlchemy, SQLite, Pydantic, Passlib.
- Frontend with React, Material-UI, Axios.
- User table grouped by department, with sorting and filtering.
- Modal forms for creating and editing users.
- Delete confirmation dialog.
- Real-time frontend validations.
- Password encryption and secure storage.
- Logging and error handling in backend.
- API documentation with Swagger (OpenAPI).

---

## [1.1.0] - Validation & Error Handling Improvements
### Fixed
- Added backend validation for email, username, password, and department.
- Improved error messages for duplicate email/username and invalid data.
- Added frontend validation for all user fields (email format, username length, password strength, department selection).
- Fixed bug where backend returned coroutine instead of user data (ResponseValidationError).
- Fixed issue with missing `updated_at` value by setting default and non-nullable fields in the model.
- Improved error handling and rollback on database errors.

---

## [1.2.0] - Dependency & Environment Issues
### Fixed
- Resolved dependency conflicts between FastAPI and Pydantic by updating `requirements.txt` with compatible versions.
- Added missing dependencies: `email-validator`, `python-dotenv`, `passlib[bcrypt]`, `python-multipart`, etc.
- Fixed issue where `uvicorn` from system was used instead of virtualenv, causing import errors. Solution: always use the virtualenv's `uvicorn`.
- Updated Pydantic field validation to use `Field` and `pattern` for compatibility with v2.

---

## [1.3.0] - Frontend UX & MUI Issues
### Added
- Action column with edit and delete icons in the user table.
- Modal for user creation and editing, with state reset and error display.
- Delete confirmation modal for safer user removal.
- Improved error display for backend errors in the frontend.

### Fixed
- Fixed runtime error: "Objects are not valid as a React child" by improving error handling in UserModal.
- Added missing `index.html` and `manifest.json` to the React public directory.
- Noted the appearance of "MUI X Missing license key" and suggested switching to the free DataGrid if advanced features are not needed.

---

## [1.4.0] - Documentation & Project Structure
### Added
- Complete English README with project description, tech stack, features, installation, and usage instructions.
- Added this detailed CHANGELOG documenting all major issues and solutions.

---

## [1.5.0] - Data Table Refactor & UX Improvements
### Changed
- Replaced the `DataGridPro` table (license required) with the free `DataGrid` version from MUI to avoid license warnings and simplify maintenance.
- Attempted to implement a single table visually grouped by department (pivot table style) using custom rows, but found that the free `DataGrid` does not support group rows or custom headers between data.
- Returned to a single table with all users and the "Department" column visible, allowing global search and pagination for all users.
- Implemented a responsive search bar next to the "Create User" button that filters by username or email in real time.
- Adjusted the layout so the search bar and button are responsive and user-friendly on both desktop and mobile.
- Updated the project screenshots to reflect the new design and behavior of the data table.

### Experience and decisions
- Explored several alternatives for visual grouping (pivot/group by) in the table, but decided to prioritize user experience and compatibility with the free version of MUI.
- Documented the limitation of the free MUI DataGrid regarding visual grouping, and left the door open for future improvements if a Pro license is acquired.

---

## [Unreleased]
### Planned
- Advanced search and filtering.
- Export/import user data.
- User authentication and roles.
- Dockerization for production deployment. 