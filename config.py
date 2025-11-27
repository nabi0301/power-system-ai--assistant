import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', 5432),
    'database': os.getenv('DB_NAME', 'postgres'),
    'username': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'your_password_here')
}

DATABASE_URL = f"postgresql://{DATABASE_CONFIG['username']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"

# AI/ML Configuration
AI_CONFIG = {
    'embedding_model': 'all-MiniLM-L6-v2',
    'embedding_dimensions': 384,
    'use_pgvector': False,  # Using JSONB for now
    'similarity_threshold': 0.7,
    'openai_api_key': 'sk-4UJCbpRTNTx-lvO_4bxNdQ'
}

# Application Configuration
APP_CONFIG = {
    'debug': True,
    'host': '0.0.0.0',
    'port': 8000
}