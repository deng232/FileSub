from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from typing import Callable, Any, Optional
import asyncio
import time


class FileSub:
    def __init__(self, app: FastAPI, suburl: str, hosturl: str, store) -> None:
        self.app = app
        self.suburl = suburl
        self.hosturl = hosturl
        if (not (hasattr(store, "get") and hasattr(store, "put") and hasattr(store, "delete"))):
            raise Exception("store must has function get, put and delete")
        self.store = store
        self.Queue = StreamingResponseQueue(app, suburl)
        self._setup_host()

    def _setup_host(self):
        @self.app.get(self.hosturl)
        def host(id: str, n: str):
            return FileResponse(self.store.get(id))

    async def init(self, id, content):
        self.store.put(id, content)
        c_time = int(time.time() * 1000)
        await self.Queue.push("f{id}:{c_time}")

    async def update(self,id,content):
        self.store.change(id,content)
        c_time = int(time.time() * 1000)
        await self.Queue.push("f{id}:{c_time}")
    async def cancle(self,id):
        self.store.delete(id)
        c_time = int(time.time() * 1000)
        await self.Queue.push("f{id}:gone")


class StreamingResponseQueue:
    def __init__(self, app: FastAPI, suburl: str) -> None:
        self.app = app
        self.suburl = suburl
        self.queue = asyncio.Queue()

        # Setup routes
        self._setup_routes()

    def _setup_routes(self):
        @self.app.get(self.suburl)
        async def stream():
            async def generator():
                while True:
                    data = await self.queue.get()
                    yield data
            return StreamingResponse(generator())

    async def push(self, info: Any):
        await self.queue.put(info)
