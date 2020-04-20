import socketio
import asyncio


class DynamicAPI:
    CompletedTasks = []
    sio = socketio.Client()

    ServerReadyLock = asyncio.Lock()
    TaskCompleteLock = asyncio.Lock()

    IsServerReady = asyncio.Event()
    IsTaskComplete = asyncio.Event()

    def __init__(self):
        self.sio.connect('http://localhost:8855')

    @sio.event
    def connect(self):
        print('connection established')

    @sio.event
    def disconnect(self):
        with self.ServerReadyLock:
            self.IsServerReady.clear()
        print('disconnected from server, try reconnect')
        self.sio.connect('http://localhost:8855')

    @sio.event
    def message(self, data):
        print('message received with ', data)

    @sio.event
    def ready(self, data):
        print('Server is ready!')
        with self.ServerReadyLock:
            self.IsServerReady.set()

    @sio.event
    def complete(self, data):
        print('task complete!')
        async with self.TaskCompleteLock:
            self.CompletedTasks.append(data)
            self.IsTaskComplete.set()

    @sio.event
    def error(self, data):
        print('some error')

    async def add_task(self, task):
        await self.IsServerReady.wait()
        with self.ServerReadyLock:
            if self.IsServerReady.is_set():
                self.sio.emit('new_task', task)

    async def get_results(self):
        await self.IsTaskComplete.wait()
        async with self.TaskCompleteLock:
            if self.IsTaskComplete.is_set():
                completed_tasks = self.CompletedTasks
                self.CompletedTasks = []
                self.IsTaskComplete.clear()
                return completed_tasks
