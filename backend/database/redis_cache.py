import aioredis
from ..config import Config

class RedisCache:
    def __init__(self):
        self.redis = None

    async def connect(self):
        try:
            self.redis = await aioredis.from_url( f'redis://{Config.REDIS_HOST}:{Config.REDIS_PORT}')
            print("Connected to Redis")
        except Exception as e:
            print(f"Error connecting to Redis: {e}")
            self.redis = None

    async def close(self):
        if self.redis:
            await self.redis.close()

    async def get(self, key: str):
        # Get value from cache
        if self.redis:
            value = await self.redis.get(key)
            if value:
                return value
        return None

    async def set(self, key: str, value: str):
        # Set value in cache with expiration time
        if self.redis:
            await self.redis.set(key, value, ex=Config.CACHE_EXPIRATION)