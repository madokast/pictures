"""
simple async http server

async def hello2(obj):
    return {'hello':obj.get('name', 'default')}

s = Server()

s.add_router(HTTPHandle.handle_json(path_prefix='/hello', method='GET', callback=lambda o:{'user':'madokast'}))
s.add_router(HTTPHandle.handle_json(path_prefix='/hello2', method='POST', callback=hello2))

s.start()
"""

import os
import json
import logging
import asyncio
import inspect
from typing import List, Literal, Coroutine, Callable, Tuple, Dict, Any, NoReturn, Optional, Union

logger = logging.getLogger(__name__)
JsonObj = Any

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
    """
    use JSONContentType to create quickly
    """
    Key_Content_Length = 'Content-Length'
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
    """
    use ok_json to create quickly
    """
    def __init__(self, status:HTTPStatus, header:HTTPHeader, content:bytes) -> None:
        self.status = status
        self.header = header
        self.content = content
    
    def send(self, dest:Callable[[bytes], None]) -> None:
        dest(self.status.bytes())
        dest(self.header.bytes())
        dest(self.content)
    
    @staticmethod
    def ok_json(obj:JsonObj) -> 'HttpResponse':
        content = json.dumps(obj, ensure_ascii=False).encode()
        header = HTTPHeader.JSONContentType().content_length(len(content))
        return HttpResponse(status=HTTPStatus.OK(), header=header, content=content)

    @staticmethod
    def not_found(obj:JsonObj) -> 'HttpResponse':
        content = json.dumps(obj, ensure_ascii=False).encode()
        header = HTTPHeader.JSONContentType().content_length(len(content))
        return HttpResponse(status=HTTPStatus.NotFound(), header=header, content=content)

class HTTPRequest:
    def __init__(self, method:str = 'GET', path:str = '/hello', protocol:str = 'HTTP/1.1', header:HTTPHeader = None, content:Optional[bytes] = None) -> None:
        self.method = method
        self.path = path
        self.protocol = protocol
        self.header = header
        self.content = content
    
    def __str__(self) -> str:
        return f"{self.method} {self.path} {self.protocol}"
    
    def to_dict(self) -> Dict:
        return {
            'method': self.method,
            'path': self.path,
            'protocol': self.protocol,
            'header': self.header.kv,
        }
    
    class Error(BaseException):
        def __init__(self, *args: Any) -> None:
            super().__init__(*args)
    class Exception(BaseException):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)


class HTTPHandle:
    """
    use handle_json to create quickly
    """
    Callback = Callable[[HTTPRequest], Coroutine[None, None, HttpResponse]]
    def __init__(self, path_prefix:str, method:Literal['GET', 'POST'], async_callback:Callback) -> None:
        self.path_prefix = path_prefix
        self.method = method
        self.async_callback = async_callback
    
    def __str__(self) -> str:
        return f"{self.method} {self.path_prefix}"
    
    @staticmethod
    def handle_json(path_prefix:str, method:Literal['GET', 'POST'], callback:Union[Callable[[Optional[JsonObj]], JsonObj],Callable[[Optional[JsonObj]], Coroutine[None, None, JsonObj]]]) -> 'HTTPHandle':

        async def _callback(request:HTTPRequest) -> 'HttpResponse':
            obj = json.loads(request.content) if request.content else None
            if inspect.iscoroutinefunction(callback):
                res = await callback(obj)
            else:
                res = callback(obj)
            return HttpResponse.ok_json(res)
        
        return HTTPHandle(path_prefix=path_prefix, method=method, async_callback=_callback)
    
    mimetypes = {'html':'text/html; charset=utf-8', 
                 'js':'application/x-javascript',
                 'webp':'image/webp'}
    
    @staticmethod
    def handle_static_resource(dir:str = 'res', path_prefix:str='/res') -> 'HTTPHandle':
        """
        when requesting 'GET {path_prefix}/a/b/c.html', return resource at '{dir}/a/b/c.html'

        dir: the root dir of all resource
        path_prefix: the URL path prefix when requested
        """
        async def _callback(request:HTTPRequest) -> 'HttpResponse':
            path = request.path[len(path_prefix)+1:]
            dot = path.rfind('.')
            if dot == -1:
                logger.warning(f'unknown static resource type {path}')
                content_type = 'application/octet-stream'
            else:
                content_type = HTTPHandle.mimetypes[path[dot+1:]]
            with open(file=os.path.join(dir, path), mode='rb') as f:
                data = f.read()
            header = HTTPHeader().content_type(content_type).content_length(len(data))
            return HttpResponse(status=HTTPStatus.OK(), header=header, content=data)

        return HTTPHandle(path_prefix=path_prefix, method='GET', async_callback=_callback)
    
    @staticmethod
    async def not_found(request:HTTPRequest) -> 'HttpResponse':
        return HttpResponse.not_found(request.to_dict())

class HTTPReader:
    """
    inner method
    """
    def __init__(self, reader:asyncio.StreamReader, peername:str, timeout:float, ) -> None:
        self.peername = peername
        self.reader = reader
        self.timeout = timeout

        logger.debug("conn with %s", peername)

    async def read_request_header(self) -> HTTPRequest:
        """
        read request line and header
        the content may read part and should use read_request_body
        """
        async def read_header() -> Tuple[bytes, bytes]:
            HEADER_END = b"\r\n\r\n"
            buffer = bytes()
            while True: # read 
                data = await asyncio.wait_for(self.reader.read(1024), timeout=self.timeout)
                if len(data) == 0: # conn closed
                    raise HTTPRequest.Exception("connection closed")
                buffer += data
                delimiter = buffer.find(HEADER_END)
                if delimiter != -1: #  read whole header
                    return buffer[:delimiter], buffer[delimiter + len(HEADER_END):]
                if len(buffer) > 10240:
                    raise HTTPRequest.Error(f'request header too long! ({buffer.decode(encoding='utf-8')})')
        
        header_content, part_content = await read_header()
        method, path, protocol = None, None, None
        header = HTTPHeader()

        for line in header_content.decode(encoding='utf-8').split('\r\n'):
            if method is None: # first line
                logger.debug("request %s", line)
                parts = line.split(' ')
                if len(parts) != 3:
                    raise HTTPRequest.Error(f'bad http request line {line}')
                method, path, protocol = parts
            else:
                delimiter = line.find(': ')
                if delimiter == -1:
                    raise HTTPRequest.Error(f'bad http request header {line}')
                key, value = line[:delimiter], line[delimiter + len(': '):]
                header.kv[key] = value
        
        return HTTPRequest(method=method, path=path, protocol=protocol, header=header, content=part_content)


    async def read_request_body(self, part_request:HTTPRequest) -> HTTPRequest:
        """
        read request body and combine with part_request.content
        """
        async def read_content(part_content:bytes, content_length:int) -> bytes:
            while len(part_content) < content_length:
                data = await asyncio.wait_for(self.reader.read(1024), timeout=self.timeout)
                if len(data) == 0:
                    raise HTTPRequest.Exception("connection closed")
                part_content += data
            return part_content
        
        content_length = int(part_request.header.kv.get(HTTPHeader.Key_Content_Length, '0'))
        if content_length > 0:
            content = await read_content(part_content=part_request.content, content_length=content_length)
            part_request.content = content
        
        return part_request
        
class Router:
    """
    TODO optimize
    """
    def __init__(self) -> None:
        self.handles:List[HTTPHandle] = []
        self.fall_back:HTTPHandle.Callback = HTTPHandle.not_found
        self.postprocesses:List[Callable[[HttpResponse], None]] = []
    
    def add_router(self, handler:HTTPHandle) -> None:
        self.handles.append(handler)
        logger.debug('add router %s', str(handler))

    def add_postprocess(self, postprocess:Callable[[HttpResponse], None]) -> None:
        self.postprocesses.append(postprocess)
    
    def keep_alive(self, flag:bool) -> None:
        self.add_postprocess(lambda res:res.header.keep_alive(flag=flag))
    
    def route(self, request:HTTPRequest) -> HTTPHandle.Callback:
        callback:HTTPHandle.Callback = None
        for handle in self.handles:
            if handle.method == request.method:
                if request.path.startswith(handle.path_prefix):
                    callback = handle.async_callback
        if callback is None:
            callback = self.fall_back
        
        async def _full_callback(request:HTTPRequest) -> HttpResponse:
            response = await callback(request)
            for postprocess in self.postprocesses:
                postprocess(response)
            return response
        
        return _full_callback

class HTTPServer:
    def __init__(self, ip = '0.0.0.0', port = 35000, timeout = 5.0, keep_alive = True) -> None:
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.router = Router()

        self.router.keep_alive(flag=keep_alive)

    def add_router(self, handler:HTTPHandle) -> None:
        self.router.add_router(handler)

    async def server_each_conn(self, reader:asyncio.StreamReader, writer:asyncio.StreamWriter):
        peername = str(writer.get_extra_info('peername', default='unknon'))
        http_reader = HTTPReader(reader=reader, peername=peername, timeout=self.timeout)
        try:
            while True:
                part_request = await http_reader.read_request_header()
                callback = self.router.route(part_request)
                request = await http_reader.read_request_body(part_request=part_request)
                response = await callback(request)
                response.send(writer.write)
                await asyncio.wait_for(writer.drain(), timeout=self.timeout)
        except TimeoutError:
            logger.debug(f"timeout with %s. closed", peername)
        except Exception as e:
            logger.warning(f"%s in %s, %s. closed", type(e).__name__, peername, str(e))
        finally:
            writer.close()

    async def start_async(self) -> NoReturn:
        server = await asyncio.start_server(self.server_each_conn, self.ip, self.port)
        addr = server.sockets[0].getsockname()
        logger.info(f'Serving on {addr}')
        async with server:
            await server.serve_forever()
    
    def start(self) -> NoReturn:
        try:
            asyncio.run(self.start_async())
        except KeyboardInterrupt:
            logger.info('stop server')
        
