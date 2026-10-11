"""Stop tests from reaching real services.

A test that creates a real Gemini client or opens a network connection would send a
real request (possibly with a real key) and pass or fail depending on the network.
This happened once: an old code path sent a real request with a dummy key.
"""

import socket
from typing import Any

import pytest

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


class RealServiceAccessError(BaseException):
    """Raised when a test tries to reach a real service.

    A BaseException, not an Exception, so DiffSage's own `except Exception` handlers
    (the CLI error handler, CliRunner) cannot catch it and let the test pass anyway.
    """


def _refuse_gemini_client(*_args: Any, **_kwargs: Any) -> None:
    raise RealServiceAccessError(
        "A test tried to create a real Gemini client. Use the fake_provider fixture, or "
        'patch("diffsage.providers.gemini_provider.genai.Client").'
    )


def _host(address: Any) -> str | None:
    return str(address[0]) if isinstance(address, tuple) and address else None


def install(monkeypatch: pytest.MonkeyPatch) -> None:
    """Block real Gemini clients, DNS lookups and connections outside this machine.

    Local sockets keep working; Git and gh run as subprocesses and are not affected.
    """

    monkeypatch.setattr("diffsage.providers.gemini_provider.genai.Client", _refuse_gemini_client)

    real_connect = socket.socket.connect
    real_connect_ex = socket.socket.connect_ex
    real_getaddrinfo = socket.getaddrinfo

    def check(sock: socket.socket, address: Any) -> None:
        host = _host(address)

        if sock.family in (socket.AF_INET, socket.AF_INET6) and host not in LOCAL_HOSTS:
            raise RealServiceAccessError(f"A test tried to connect to {address!r}.")

    def guarded_connect(sock: socket.socket, address: Any) -> None:
        check(sock, address)
        real_connect(sock, address)

    def guarded_connect_ex(sock: socket.socket, address: Any) -> int:
        check(sock, address)
        return real_connect_ex(sock, address)

    def guarded_getaddrinfo(host: Any, *args: Any, **kwargs: Any) -> Any:
        if host is not None and str(host) not in LOCAL_HOSTS:
            raise RealServiceAccessError(f"A test tried to look up the host {host!r}.")

        return real_getaddrinfo(host, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", guarded_connect_ex)
    monkeypatch.setattr(socket, "getaddrinfo", guarded_getaddrinfo)
