# Clever Photos API

A production-ready RESTful API for photo management using FastAPI, Supabase, and PostgreSQL.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ (3.13 preferred)
- [uv package manager](https://astral.sh/uv/install.sh)
- [Supabase account](https://supabase.com) (free tier)

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/clever-photos.git
   cd clever-photos
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Set up Supabase:**
   - Create a new project at [supabase.com](https://supabase.com)
   - Get your database connection string from Project Settings > Database
   - Get your Supabase URL from Project Settings > API

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase credentials
   ```

5. **Run the application:**
   ```bash
   python entrypoint.py
   ```

6. **Seed the database (optional):**
   ```bash
   python -m clever.seed
   ```

7. **Access the API:**
   - API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Health Check: [http://localhost:8000/api/v1/health/](http://localhost:8000/api/v1/health/)

## 🏗️ Architecture

### Tech Stack

- **Framework**: FastAPI (async, OpenAPI docs, Pydantic validation)
- **Database**: Supabase PostgreSQL (hosted, zero setup)
- **ORM**: SQLAlchemy 2.0 (async support, type hints)
- **Auth**: Supabase Auth (JWT tokens, JWKS validation)
- **Package Manager**: uv (fast, modern)

### Key Features

- **Authentication**: JWT validation against Supabase JWKS endpoint
- **Authorization**: Ownership-based access control
- **Database**: Async SQLAlchemy with proper relationships
- **Logging**: Centralized configuration with text/JSON formats
- **Configuration**: Pydantic Settings with environment variables
- **Error Handling**: Proper HTTP status codes and error responses

### Project Structure

```
clever-photos/
├── entrypoint.py          # Application bootstrap
├── pyproject.toml         # Project configuration
├── .env.example           # Environment template
├── .gitignore            # Git ignore patterns
├── photos.csv            # Seed data (ignored by git)
├── src/
│   └── clever/
│       ├── __init__.py
│       ├── main.py        # FastAPI app factory
│       ├── config.py      # Centralized configuration
│       ├── logging.py     # Logging setup
│       ├── database.py    # Database connection
│       ├── models.py      # SQLAlchemy models
│       ├── schemas.py     # Pydantic schemas
│       ├── seed.py        # CSV seeding script
│       ├── auth/
│       │   ├── __init__.py
│       │   └── deps.py    # Auth dependencies
│       └── api/
│           ├── __init__.py
│           ├── router.py  # Main router
│           ├── health.py  # Health check
│           └── photos.py  # Photo endpoints
└── tests/
    ├── __init__.py
    ├── conftest.py        # Test fixtures
    └── test_photos.py     # Photo endpoint tests
```

## 🔐 Authentication

### Supabase Auth Flow

1. **User Authentication**: Users authenticate via Supabase Auth (hosted login UI or API)
2. **JWT Issuance**: Supabase issues JWT tokens signed with RS256
3. **Token Validation**: Our API validates JWTs against Supabase's JWKS endpoint
4. **User Resolution**: Extract user ID from JWT and get/create user in database

### Authorization Rules

| Operation | Rule |
|-----------|------|
| Read (GET) | Any authenticated user can read all photos |
| Create (POST) | Any authenticated user; photo owned by creator |
| Update (PUT/PATCH) | Only if `photo.user_id == current_user.id` |
| Delete | Only if `photo.user_id == current_user.id` |

## 📖 API Documentation

### Base URL

```
http://localhost:8000/api/v1
```

### Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health/` | None | Health check |
| GET | `/photos/` | Required | List photos (paginated) |
| GET | `/photos/{id}` | Required | Get single photo |
| POST | `/photos/` | Required | Create photo |
| PUT | `/photos/{id}` | Owner | Full update |
| PATCH | `/photos/{id}` | Owner | Partial update |
| DELETE | `/photos/{id}` | Owner | Delete photo |

### Health Check

```bash
curl http://localhost:8000/api/v1/health/
```

Response:
```json
{
  "status": "healthy",
  "message": "Clever Photos API is running"
}
```

## 🗃️ Database Schema

### User Model

```python
class User(Base):
    id: str          # Supabase auth user ID (primary key)
    email: str       # User email (unique)
    created_at: datetime
    updated_at: datetime
    photos: List[Photo]  # One-to-many relationship
```

### Photo Model

```python
class Photo(Base):
    id: int          # Primary key
    pexels_id: int   # Unique Pexels ID (indexed)
    width: int       # Image width
    height: int      # Image height
    url: str         # Pexels photo URL
    photographer: str
    photographer_id: int  # Indexed
    photographer_url: str
    avg_color: str   # Hex color code
    src_original: str
    src_large2x: str
    src_large: str
    src_medium: str
    src_small: str
    src_portrait: str
    src_landscape: str
    src_tiny: str
    alt: str         # Description (nullable)
    user_id: str     # Foreign key to User (indexed)
    created_at: datetime
    updated_at: datetime
```

## 🧪 Testing

### Run Tests

```bash
pytest
```

### Test Structure

- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **Auth Tests**: Authentication flow validation
- **Database Tests**: Model and query testing

## 🚀 Deployment

### Environment Variables

Create `.env` file with:

```env
# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres

# Supabase Configuration
SUPABASE_URL=https://your-project-ref.supabase.co

# Application Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
LOG_FORMAT=json
HOST=0.0.0.0
PORT=8000

# CORS Configuration
CORS_ORIGINS=https://your-frontend.com

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60
```

### Run in Production

```bash
uvicorn clever.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📚 Development

### Code Formatting

```bash
ruff format .
ruff check .
```

### Add New Dependencies

```bash
uv add package-name
uv add --dev package-name  # For development dependencies
```

### Database Migrations

This project uses SQLAlchemy's `create_all()` for simplicity. For production, consider:

- Alembic for migrations
- Supabase SQL editor for schema changes

## 🎯 Roadmap

### Completed ✅

- [x] Project scaffolding and setup
- [x] Supabase integration (Auth + Database)
- [x] Core configuration and logging
- [x] Database models (User, Photo)
- [x] Authentication system (JWT/JWKS)
- [x] Health check endpoint
- [x] Photo CRUD endpoints with pagination
- [x] Ownership-based authorization
- [x] Pydantic schemas
- [x] CSV seeding script
- [x] Comprehensive tests (27 tests)
- [x] API documentation (OpenAPI/Swagger)

### Future Enhancements 🔮

- [ ] Rate limiting (slowapi installed)
- [ ] RBAC (Role-Based Access Control)
- [ ] Caching (Redis)
- [ ] File uploads
- [ ] Full-text search
- [ ] OpenTelemetry tracing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m 'Add some feature'`
4. Push to branch: `git push origin feature/your-feature`
5. Open a pull request

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [Supabase](https://supabase.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Pydantic](https://pydantic.dev/)

---

**Clever Real Estate Backend Coding Assessment**

This project demonstrates production-ready API design, authentication, database integration, and software engineering best practices.