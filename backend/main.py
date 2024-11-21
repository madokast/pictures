import logger as _
from http_server import HTTPHandle, HTTPServer
from picture_server import PictureServer

hs = HTTPServer()
hs.add_router(HTTPHandle.hangle_static_resource(path_prefix='/resource', dir='frontend'))

ps = PictureServer()
ps.register_routers(hs)

hs.start()
