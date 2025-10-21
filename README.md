# AI-Validator

A full-stack AI-powered document validation application that compares and validates document images using Google's Gemini API. Built with React and Flask.

## Prerequisites

- Node.js (v16+)
- Python (3.8+)
- PostgreSQL (optional, SQLite works for development)

## Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd AI-Validator
```

### 2. Backend Setup

```bash
cd server

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://username:password@localhost:5432/middesk_validator
JWT_SECRET_KEY=your-secure-jwt-secret-key
SECRET_KEY=your-secure-flask-secret-key
GEMINI_API_KEY=your-gemini-api-key
EOF

# Run database migrations
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Start server
python app.py
```

Server runs on `http://localhost:5001`

### 3. Frontend Setup

```bash
cd client

# Install dependencies
npm install

# Create .env file
echo "REACT_APP_API_URL=http://localhost:5001" > .env

# Start development server
npm start
```

Frontend runs on `http://localhost:3000`

## Environment Variables

### Server (`server/.env`)

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string (use SQLite for dev) | Yes |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | Yes |
| `SECRET_KEY` | Flask secret key | Yes |
| `GEMINI_API_KEY` | Google Gemini API key ([Get here](https://makersuite.google.com/app/apikey)) | Yes |

### Client (`client/.env`)

| Variable | Description | Required |
|----------|-------------|----------|
| `REACT_APP_API_URL` | Backend API URL | Yes |

## Features

- Multi-image upload (drag-and-drop, file selection, paste)
- AI-powered document validation with Gemini API
- Simple text comparison validation
- Session history tracking
- PostgreSQL database with SQLAlchemy ORM
- JWT authentication
- Responsive UI with dark mode

## Project Structure

```
AI-Validator/
├── client/          # React frontend
│   ├── src/
│   └── package.json
└── server/          # Flask backend
    ├── models/      # Database models
    ├── routes/      # API endpoints
    ├── services/    # Business logic
    ├── app.py       # Main application
    └── requirements.txt
```

## Production Deployment

### Backend
```bash
cd server
gunicorn -w 4 -b 0.0.0.0:5001 app:app
```

### Frontend
```bash
cd client
npm run build
# Deploy the build/ folder to your hosting service
```

## API Endpoints

- `GET /health` - Health check
- `POST /api/uploads/main/upload` - Upload main image
- `POST /api/uploads/secondary/upload` - Upload secondary image
- `POST /api/validate/simple` - Simple text validation
- `POST /api/validate/gemini` - AI-powered validation
- `GET /api/history/sessions` - Get validation history

## Troubleshooting

**Database connection fails**: Check `DATABASE_URL` in server/.env

**CORS errors**: Ensure backend is running and `REACT_APP_API_URL` is correct

**Gemini API errors**: Verify `GEMINI_API_KEY` is valid

**Module not found**: Run `pip install -r requirements.txt` (backend) or `npm install` (client)

## Tech Stack

**Frontend**: React 19, TailwindCSS, React Router
**Backend**: Flask 2.3, SQLAlchemy, PostgreSQL
**AI**: Google Gemini API
**Image Processing**: Pillow, python-magic
