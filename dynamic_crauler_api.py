import socketio

sio = socketio.Client()

@sio.event
def connect():
    print('connection established')

@sio.event
def message(data):
    print('message received with ', data)
    sio.emit('new_task', {"url": "https://myx-light.ru/"})

@sio.event
def disconnect():
    print('disconnected from server')

@sio.event
def complete(data):
    print('task complete!')
    print(data)

@sio.event
def error(data):
    print('some error')

sio.connect('http://localhost:8855')
# sio.emit('new_task', {"url": "https://myx-light.ru/"})
sio.wait()