import logging
import time
from http_server import Server, HTTPHandle, HTTPRequest, HttpResponse

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

async def hello2(obj):
    return {'hello':obj.get('name', 'default')}

s = Server()

s.add_router(HTTPHandle.handle_json(path_prefix='/hello', method='GET', callback=lambda o:{'user':'madokast'}))
s.add_router(HTTPHandle.handle_json(path_prefix='/hello2', method='POST', callback=hello2))

s.start()

