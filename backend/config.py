# backend/config.py
class Config:
    # MongoDB
    MONGO_URI = "mongodb://localhost:27017"
    MONGO_DB = "chatbot_db"
    
    # Redis
    REDIS_HOST = "172.26.43.121"
    REDIS_PORT = 6379
    
    # API
    API_HOST = "0.0.0.0"
    API_PORT = 8000
    
    # Cache settings
    CACHE_EXPIRATION = 3600  # 1 hour