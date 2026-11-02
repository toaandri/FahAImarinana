import asyncio
import time


class RequestLimiter:
    """Shared per-client/process pacing; retries consume quota as well."""
    def __init__(self, requests_per_minute, *, clock=time.monotonic, sleep=asyncio.sleep):
        self.interval = 60.0 / requests_per_minute
        self.clock = clock
        self.sleep = sleep
        self.lock = asyncio.Lock()
        self.next_slot = 0.0

    async def acquire(self):
        async with self.lock:
            current = self.clock()
            slot = max(current, self.next_slot)
            self.next_slot = slot + self.interval
        delay = slot - current
        if delay > 0:
            await self.sleep(delay)
