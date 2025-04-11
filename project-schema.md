PRODUCT_ENHANCER_BACKEND/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── endpoints/
│   │   │   ├── __init__.py
│   │   │   ├── analysis.py        # Main analysis endpoints
│   │   │   ├── enhancements.py    # Enhancement generation endpoints
│   │   │   ├── screenshots.py     # Screenshot handling endpoints
│   │   │   └── tealium.py         # Tealium-specific endpoints
│   │   ├── dependencies.py        # API dependencies
│   │   └── router.py              # API router setup
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Application configuration
│   │   ├── security.py            # Authentication/authorization
│   │   └── errors.py              # Error handling
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py              # Database models
│   │   ├── crud.py                # Database operations
│   │   └── session.py             # Database session
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── analysis.py            # Analysis request/response schemas
│   │   ├── enhancements.py        # Enhancement schemas
│   │   ├── tealium.py             # Tealium data schemas
│   │   └── errors.py              # Error response schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── browser/
│   │   │   ├── __init__.py
│   │   │   ├── playwright.py      # Playwright browser interactions
│   │   │   └── screenshot.py      # Screenshot capture and processing
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── openai.py          # OpenAI API integration
│   │   │   ├── prompts.py         # System prompts for different analyses
│   │   │   └── processing.py      # Response processing for AI outputs
│   │   ├── tealium/
│   │   │   ├── __init__.py
│   │   │   ├── analyzer.py        # Tealium implementation analyzer
│   │   │   ├── scripts/           # JavaScript injection scripts
│   │   │   │   ├── tag_detection.js
│   │   │   │   └── data_layer.js
│   │   │   └── validators.py      # Tealium implementation validators
│   │   ├── content/
│   │   │   ├── __init__.py
│   │   │   ├── extractor.py       # Content extraction logic
│   │   │   └── analyzer.py        # Content analysis logic
│   │   └── storage/
│   │       ├── __init__.py
│   │       ├── cloud.py           # Cloud storage integration
│   │       └── cache.py           # Redis cache integration
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── worker.py              # Celery worker configuration
│   │   ├── analysis.py            # Analysis task definitions
│   │   └── enhancements.py        # Enhancement generation tasks
│   └── utils/
│       ├── __init__.py
│       ├── logging.py             # Logging utilities
│       └── validators.py          # Input validation utilities
├── alembic/                       # Database migrations
│   └── versions/
├── tests/
│   ├── api/
│   ├── services/
│   └── conftest.py
├── .env                           # Environment variables (gitignored)
├── .env.example                   # Example environment variables
├── .gitignore
├── alembic.ini                    # Alembic configuration
├── main.py                        # Application entry point
├── Dockerfile                     # Docker configuration
├── docker-compose.yml             # Docker Compose configuration
├── celery.py                      # Celery configuration
├── requirements.txt               # Python dependencies
└── README.md                      # Project documentation