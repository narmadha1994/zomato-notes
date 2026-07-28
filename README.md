## CORS Configuration

The frontend is served locally using a static development server.

Allowed frontend origin:

- `http://127.0.0.1:5500`

The FastAPI backend is served at:

- `http://127.0.0.1:8000`

The backend uses FastAPI `CORSMiddleware` to allow the frontend to communicate with the API across origins.