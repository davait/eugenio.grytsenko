# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.6.0] - 2024-03-14

### Added
- Dockerfile and deployment instructions for Google Cloud Run
- GitHub Actions CI/CD workflow for automated deployment
- Health check endpoint for monitoring
- Swagger UI documentation section in README

### Changed
- Simplified monitoring implementation to use basic health check
- Updated version numbers across all components

### Fixed
- Relative import issues in monitoring module
- Database connection handling in health check

## [1.5.0] - 2024-03-14

### Changed
- Replaced the `DataGridPro` table with the free `DataGrid` version
- Implemented single table with search functionality
- Added responsive search bar for filtering by username or email
- Updated project screenshots to reflect new design

## [1.4.0] - 2024-03-14

### Added
- Complete English README with project description, tech stack, features
- Detailed installation and usage instructions
- Comprehensive CHANGELOG documentation

## [1.3.0] - 2024-03-14

### Added
- Action column with edit and delete icons
- Modal for user creation and editing
- Delete confirmation modal
- Improved error display in frontend

### Fixed
- React child validation error in UserModal
- Added missing `index.html` and `manifest.json`
- Resolved MUI X license key warning

## [1.2.0] - 2024-03-14

### Fixed
- Resolved FastAPI and Pydantic dependency conflicts
- Added missing dependencies
- Fixed uvicorn virtualenv usage
- Updated Pydantic field validation for v2 compatibility

## [1.1.0] - 2024-03-14

### Added
- Backend validation for email, username, password, and department
- Frontend validation for all user fields
- Improved error messages for duplicates and invalid data

### Fixed
- ResponseValidationError with coroutine returns
- Missing `updated_at` value in model
- Database error handling and rollback

## [1.0.0] - 2024-03-13

### Added
- Initial release with full-stack user management portal
- Backend with FastAPI, SQLAlchemy, SQLite
- Frontend with React, Material-UI
- User table with department grouping
- Modal forms for CRUD operations
- Password encryption and secure storage
- API documentation with Swagger
- Logging and error handling 