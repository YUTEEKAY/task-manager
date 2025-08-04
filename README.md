# task-manager
A secure task management application where users can register, login, and manage their personal to-do lists with data stored securely in a database.
<br>Key Features:
<br>User Registration & Login: Secure password hashing with bcrypt
<br>Session Management: Flask sessions for user authentication
<br>CRUD Operations: Create, read, update, delete tasks
<br>Data Security: SQL injection protection, input validation
<br>Responsive Design: Mobile-friendly interface
<br>Database Schema:
<br>sqlUsers Table:
<br>- id (Primary Key)
<br>- username (Unique)
<br>- email (Unique)
<br>- password_hash
<br>- created_at

<br>Tasks Table:
<br>- id (Primary Key)
<br>- user_id (Foreign Key)
<br>- title
<br>- description
<br>- priority (High/Medium/Low)
<br>- completed (Boolean)
<br>- due_date
<br>- created_at

<br>Security Features:
<br>Session-based authentication
<br>Password hashing with bcrypt
<br>CSRF protection
Input sanitization
SQL injection prevention using parameterized queries
Rate limiting for login attempts
