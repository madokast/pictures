import json
import logging
import asyncio
from collections import defaultdict
from typing import List, Literal, Coroutine, Callable, Union, Dict, Any, NoReturn

logger = logging.getLogger(__name__)

class HTTPStatus:
    def __init__(self, code:int, description:str) -> None:
        self.value = f"HTTP/1.1 {code} {description}"
    def __str__(self) -> str:
        return self.value
    def bytes(self) -> bytes:
        return self.value.encode() + b'\r\n'
    @staticmethod
    def OK() -> 'HTTPStatus':
        return HTTPStatus(200, "OK")
    @staticmethod
    def NotFound() -> 'HTTPStatus':
        return HTTPStatus(404, "NOT FOUND")

class HTTPHeader:
    def __init__(self) -> None:
        self.kv:Dict[str, str] = dict()
    def header(self, key:str, value:any) -> 'HTTPHeader':
        self.kv[key] = str(value)
        return self
    def content_type(self, value:str) -> 'HTTPHeader':
        return self.header("Content-type", value)
    def content_length(self, length:int) -> 'HTTPHeader':
        return self.header("Content-Length", length)
    def keep_alive(self, flag:bool) -> 'HTTPHeader':
        return self.header("Connection", "keep-alive" if flag else "close")
    def __str__(self) -> str:
        return ("\r\n".join((f"{k}: {v}" for k, v in self.kv.items()))) + '\r\n\r\n'
    def bytes(self) -> bytes:
        return bytes(str(self).encode())
    @staticmethod
    def JSONContentType() -> 'HTTPHeader':
        return HTTPHeader().content_type("application/json; charset=utf-8")
    @staticmethod
    def HTMLContentType() -> 'HTTPHeader':
        return HTTPHeader().content_type("text/html; charset=utf-8")

class HttpResponse:
    def __init__(self, status:HTTPStatus, header:HTTPHeader, content:bytes) -> None:
        self.status = status
        self.header = header
        self.content = content
    
    @staticmethod
    def ok_json(obj:Any) -> 'HttpResponse':
        content = json.dumps(obj, ensure_ascii=False).encode()
        header = HTTPHeader.JSONContentType().content_length(len(content))
        return HttpResponse(status=HTTPStatus.OK(), header=header, content=content)

    @staticmethod
    def not_found(path:str) -> 'HttpResponse':
        content = json.dumps({'path':path}, ensure_ascii=False).encode()
        header = HTTPHeader.JSONContentType().content_length(len(content))
        return HttpResponse(status=HTTPStatus.NotFound(), header=header, content=content)


class Handler:
    def __init__(self, path_prefix:str, method:Literal['GET', 'POST'], async_callback:Callable[[Any], Coroutine[None, None, HttpResponse]]) -> None:
        self.path = path_prefix
        self.method = method
        self.async_callback = async_callback
    
    @staticmethod
    async def not_found(path:str) -> 'HttpResponse':
        return HttpResponse.not_found(path)

class Server:
    def __init__(self, ip = '0.0.0.0', port = 35000) -> None:
        self.ip = ip
        self.port = port
        self.callbacks = []
    
    def add_router(self, handler:Handler) -> None:
        pass

    async def server_each_conn(self, reader:asyncio.StreamReader, writer:asyncio.StreamWriter):
        try:
            while True:
                recv_data = await reader.read()
                logger.info(recv_data.decode())
                response = await Handler.not_found('hello')
                writer.write(response.status.bytes())
                writer.write(response.header.bytes())
                writer.write(response.content)
                await writer.drain()
        except Exception:
            pass
        finally:
            writer.close()
        


    async def start_async(self) -> NoReturn:
        server = await asyncio.start_server(self.server_each_conn, self.ip, self.port)
        addr = server.sockets[0].getsockname()
        logger.info(f'Serving on {addr}')

        async with server:
            await server.serve_forever()
    
    def start(self) -> NoReturn:
        asyncio.run(self.start_async())
