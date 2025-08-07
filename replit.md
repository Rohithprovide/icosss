# Data Collection App

## Overview

A simple Flask web application for collecting and displaying user data through a web form. The application provides a clean, responsive interface for users to submit text data up to 500 characters, with immediate feedback and success confirmation. Built with Flask and Bootstrap, it follows a traditional MVC pattern with form validation and flash messaging for user feedback.

## User Preferences

Preferred communication style: Simple, everyday language.
Logo positioning: Prefers logo closer to search bar interface.
Icons: Prefers Font Awesome icons over SVG icons (specifically fa-magnifying-glass for search).

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 templates with a base template inheritance pattern
- **UI Framework**: Bootstrap 5 with dark theme and Bootstrap Icons for consistent styling
- **Responsive Design**: Mobile-first approach using Bootstrap's grid system
- **Form Handling**: WTForms integration for client-side and server-side validation

### Backend Architecture
- **Web Framework**: Flask with a simple two-route structure (index and success pages)
- **Form Processing**: Flask-WTF for CSRF protection and form validation
- **Session Management**: Flask sessions with configurable secret key
- **Error Handling**: Flash messaging system for user feedback and form validation errors
- **Logging**: Python logging module configured for debugging

### Data Flow
- **Input Validation**: TextAreaField with length constraints (1-500 characters) and required field validation
- **Data Processing**: Simple form submission flow with GET/POST pattern
- **Success Flow**: Redirect-after-POST pattern to prevent duplicate submissions
- **Error Handling**: Form validation errors displayed via flash messages

### Application Structure
- **Entry Point**: `main.py` imports the Flask app for deployment
- **Core Application**: `app.py` contains route handlers and application logic
- **Form Definitions**: `forms.py` defines the UserDataForm with validation rules
- **Templates**: Modular template structure with base template and page-specific templates

## External Dependencies

### Python Packages
- **Flask**: Core web framework for routing and request handling
- **Flask-WTF**: Form handling and CSRF protection
- **WTForms**: Form validation and rendering

### Frontend Libraries
- **Bootstrap 5**: CSS framework via CDN
- **Font Awesome 6.4.0**: Icon library for UI enhancement (replaced Bootstrap Icons per user preference)

### Environment Configuration
- **SESSION_SECRET**: Environment variable for Flask session security (defaults to development key)

### Deployment Considerations
- **Host Configuration**: Configured to run on 0.0.0.0:5000 for container deployment
- **Debug Mode**: Enabled for development with detailed error logging
- **Migration Status**: Successfully migrated from Replit Agent to Replit environment (August 2025)
  - Fixed CSRF security configuration
  - Resolved LSP compatibility issues
  - Updated error handling for better robustness
  - Integrated Font Awesome for enhanced icon library