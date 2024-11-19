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

async def hello(req:HTTPRequest) -> HttpResponse:
    return HttpResponse.ok_json({"user":"mdk", "time":time.time()})

s = Server()

s.add_router(HTTPHandle(path_prefix='/hello', method='GET', async_callback=hello))

s.start()

