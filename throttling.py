import asyncio
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import Message
from aiogram.utils.exceptions import Throttled

class ThrottlingMiddleware(BaseMiddleware):
    def init(self, limit=1):
        self.rate_limit = limit
        self.cache = {}
        super().init()

    async def on_pre_process_message(self, message: Message, data: dict):
        user_id = message.from_user.id
        now = asyncio.get_event_loop().time()
        if user_id in self.cache and now - self.cache[user_id] < self.rate_limit:
            raise Throttled()
        self.cache[user_id] = now
