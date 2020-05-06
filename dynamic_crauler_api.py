import socketio
import asyncio


class DynamicAPI:
    def __init__(self):
        pass

    async def init(self):
        self.CompletedTasks = []
        self.sio = socketio.AsyncClient()

        self.ServerReadyLock = asyncio.Lock()
        self.TaskCompleteLock = asyncio.Lock()
        self.FirstReady = True
        self.PendingUrls = set()

        self.IsServerReady = asyncio.Event()
        self.IsTaskComplete = asyncio.Event()
        self.sio.on("connect", self._connect)
        self.sio.on("disconnect", self._disconnect)
        self.sio.on("message", self._message)
        self.sio.on("ready", self._ready)
        self.sio.on("complete", self._complete)
        self.sio.on("error", self._error)
        await self.sio.connect('http://localhost:8855')
        return self

    async def _connect(self):
        print('connection established')

    async def _disconnect(self):
        async with self.ServerReadyLock:
            self.IsServerReady.clear()
        # TODO: realize task resending
        print('disconnected from server, we are trying to reconnect')

    async def _message(self, data):
        print('message received with ', data)

    async def _ready(self, data):
        print('Server is ready!')
        async with self.ServerReadyLock:
            self.IsServerReady.set()
            if self.FirstReady:
                self.FirstReady = False
                return

        async with self.TaskCompleteLock:
            for url in self.PendingUrls:
                await self._add_url(url)

    async def _complete(self, data):
        print('task complete!')
        async with self.TaskCompleteLock:
            self.CompletedTasks.append(data['result'])
            self.IsTaskComplete.set()
            self.PendingUrls.remove(data['result']['options']['url'])

    async def _error(self, data):
        print('some error')

    async def _add_task(self, task):
        await self.IsServerReady.wait()
        async with self.ServerReadyLock:
            if self.IsServerReady.is_set():
                await self.sio.emit('new_task', task)

    async def get_results(self):
        await self.IsTaskComplete.wait()
        async with self.TaskCompleteLock:
            if self.IsTaskComplete.is_set():
                completed_tasks = self.CompletedTasks
                self.CompletedTasks = []
                self.IsTaskComplete.clear()
                return completed_tasks

    async def destroy(self):
        await self.sio.disconnect()

    async def add_url(self, url):
        async with self.TaskCompleteLock:
            self.PendingUrls.add(url)
            await self._add_url(url)

    async def _add_url(self, url):
        await self._add_task(await self.create_task(url))

    async def create_task(self, url):
        return {'url': url}


async def test_main():
    api = await (DynamicAPI().init())
    await api._add_task({"url": "https://myx-light.ru/"})
    results = await api.get_results()
    print(results)
    await api.sio.wait()


if __name__ == '__main__':
    asyncio.run(test_main())
