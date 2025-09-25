import asyncio
import contextlib
import json
import socket
import ssl
import struct
import threading

import pytest
import trustme
import websockets

from scripts.verify_proxies import test_http, test_ws


class AsyncRuntime:
    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

    def run(self, coro):
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def stop(self) -> None:
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join()
        self._loop.close()


@pytest.fixture(scope="module")
def async_runtime():
    runtime = AsyncRuntime()
    try:
        yield runtime
    finally:
        runtime.stop()


async def start_http_server(origin: str, *, ssl_context: ssl.SSLContext | None = None):
    body = json.dumps({"origin": origin}).encode("utf-8")

    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            await reader.readuntil(b"\r\n\r\n")
        except asyncio.IncompleteReadError:
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()
            return

        headers = "\r\n".join(
            [
                "HTTP/1.1 200 OK",
                "Content-Type: application/json",
                f"Content-Length: {len(body)}",
                "Connection: close",
                "",
                "",
            ]
        ).encode("ascii")
        writer.write(headers + body)
        await writer.drain()
        writer.close()
        with contextlib.suppress(Exception):
            await writer.wait_closed()

    server = await asyncio.start_server(handle, host="127.0.0.1", port=0, ssl=ssl_context)
    port = server.sockets[0].getsockname()[1]
    return server, port


async def start_ws_server():
    async def handler(websocket):
        async for message in websocket:
            await websocket.send(message)

    server = await websockets.serve(handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    return server, port


async def start_socks_proxy():
    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            version = await reader.readexactly(1)
            if version != b"\x05":
                raise ValueError("Unsupported SOCKS version")
            n_methods = await reader.readexactly(1)
            await reader.readexactly(n_methods[0])
            writer.write(b"\x05\x00")
            await writer.drain()

            request = await reader.readexactly(4)
            if request[0] != 5 or request[1] != 1:
                raise ValueError("Only CONNECT commands are supported")
            atyp = request[3]
            if atyp == 1:  # IPv4
                addr = await reader.readexactly(4)
                host = socket.inet_ntoa(addr)
            elif atyp == 3:  # Domain name
                length = await reader.readexactly(1)
                addr = await reader.readexactly(length[0])
                host = addr.decode("utf-8")
            else:
                raise ValueError("Unsupported address type")
            port_bytes = await reader.readexactly(2)
            port = struct.unpack("!H", port_bytes)[0]

            remote_reader, remote_writer = await asyncio.open_connection(host, port)
            writer.write(b"\x05\x00\x00\x01" + socket.inet_aton("0.0.0.0") + b"\x00\x00")
            await writer.drain()

            async def pipe(src: asyncio.StreamReader, dst: asyncio.StreamWriter):
                try:
                    while True:
                        data = await src.read(4096)
                        if not data:
                            break
                        dst.write(data)
                        await dst.drain()
                finally:
                    dst.close()
                    with contextlib.suppress(Exception):
                        await dst.wait_closed()

            forward = asyncio.create_task(pipe(reader, remote_writer))
            backward = asyncio.create_task(pipe(remote_reader, writer))
            done, pending = await asyncio.wait({forward, backward}, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
            for task in done:
                with contextlib.suppress(Exception):
                    task.result()
        except Exception:
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()

    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    return server, port


@pytest.fixture(scope="module")
def socks_proxy(async_runtime: AsyncRuntime):
    server, port = async_runtime.run(start_socks_proxy())
    try:
        yield f"127.0.0.1:{port}"
    finally:
        async_runtime.run(_stop_server(server))


async def _stop_server(server):
    server.close()
    await server.wait_closed()


@pytest.fixture(scope="module")
def http_target(async_runtime: AsyncRuntime):
    server, port = async_runtime.run(start_http_server("http-local"))
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        async_runtime.run(_stop_server(server))


@pytest.fixture(scope="module")
def https_target(async_runtime: AsyncRuntime, tmp_path_factory):
    ca = trustme.CA()
    cert = ca.issue_server_cert("127.0.0.1")
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    cert.configure_cert(ssl_context)
    server, port = async_runtime.run(start_http_server("https-local", ssl_context=ssl_context))
    ca_path = tmp_path_factory.mktemp("certs") / "ca.pem"
    ca.cert_pem.write_to_path(ca_path)
    try:
        yield f"https://127.0.0.1:{port}", ca_path
    finally:
        async_runtime.run(_stop_server(server))


@pytest.fixture(scope="module")
def ws_target(async_runtime: AsyncRuntime):
    server, port = async_runtime.run(start_ws_server())
    try:
        yield f"ws://127.0.0.1:{port}"
    finally:
        server.close()
        async_runtime.run(server.wait_closed())


def test_http_over_socks(socks_proxy, http_target):
    ok, error, origin = test_http(socks_proxy, timeout=4, url=http_target)
    assert error is None
    assert ok is True
    assert origin == "http-local"


def test_https_over_socks(socks_proxy, https_target):
    url, ca_path = https_target
    ok, error, origin = test_http(socks_proxy, timeout=4, url=url, verify=str(ca_path))
    assert error is None
    assert ok is True
    assert origin == "https-local"


def test_ws_over_socks(socks_proxy, ws_target):
    ok, error = test_ws(socks_proxy, timeout=4, url=ws_target)
    assert error is None
    assert ok is True
