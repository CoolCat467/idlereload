import io
from collections.abc import Callable
from idlelib import (
    autocomplete as autocomplete,
    calltip as calltip,
    debugger_r as debugger_r,
    debugobj_r as debugobj_r,
    iomenu as iomenu,
    rpc as rpc,
    stackviewer as stackviewer,
)
from idlelib.pyshell import PyShellEditorWindow
from socket import socket
from tkinter import Misc, Tk
from types import TracebackType
from typing import Any

LOCALHOST: str
eof: str

def idle_formatwarning(
    message: str,
    category: type,
    filename: str,
    lineno: str,
    line: str | None = ...,
) -> str: ...
def idle_showwarning_subproc(
    message: str,
    category: type,
    filename: str,
    lineno: str,
    file: str | None = ...,
    line: str | None = ...,
) -> None: ...
def capture_warnings(capture: bool) -> None: ...

tcl: Tk

def handle_tk_events(tcl: Tk = ...) -> None: ...

exit_now: bool
quitting: bool
interruptible: bool

def main(del_exitfunc: bool = ...) -> None: ...
def manage_socket(address: tuple[str, int]) -> None: ...
def show_socket_error(
    err: OSError,
    address: tuple[str | int, str | int],
) -> None: ...
def get_message_lines(
    typ: BaseException,
    exc: str,
    tb: TracebackType,
) -> list[str]: ...
def print_exception() -> None: ...
def cleanup_traceback(tb: TracebackType, exclude: list[str]) -> None: ...
def flush_stdout() -> None: ...
def exit() -> None: ...
def fix_scaling(root: Misc) -> None: ...
def fixdoc(fun: Callable[..., Any], text: str) -> None: ...

RECURSIONLIMIT_DELTA: int

def install_recursionlimit_wrappers() -> None: ...
def uninstall_recursionlimit_wrappers() -> None: ...

class MyRPCServer(rpc.RPCServer):
    def handle_error(
        self,
        request: socket | tuple[bytes, socket],
        client_address: tuple[str, int] | str,
    ) -> None: ...

class StdioFile(io.TextIOBase):
    shell: PyShellEditorWindow
    tags: str
    def __init__(
        self,
        shell: PyShellEditorWindow,
        tags: str,
        encoding: str = ...,
        errors: str = ...,
    ) -> None: ...
    @property
    def encoding(self) -> str: ...  # type: ignore[override]
    @property
    def errors(self) -> str: ...  # type: ignore[override,mutable-override]
    @property
    def name(self) -> str: ...
    def isatty(self) -> bool: ...

class StdOutputFile(StdioFile):
    def writable(self) -> bool: ...
    def write(self, s: str) -> int: ...

class StdInputFile(StdioFile):
    def readable(self) -> bool: ...
    def read(self, size: int | None = ...) -> str: ...
    def readline(self, size: int | None = ...) -> str: ...  # type: ignore[override]
    def close(self) -> None: ...

class MyHandler(rpc.RPCHandler):
    console: rpc.RPCProxy
    interp: rpc.RPCProxy
    def handle(self) -> None: ...
    def exithook(self) -> None: ...
    def EOFhook(self) -> None: ...
    def decode_interrupthook(self) -> None: ...

class Executive:
    rpchandler: rpc.RPCHandler
    locals: dict[str, object]
    calltip: calltip.Calltip
    autocomplete: autocomplete.AutoComplete
    def __init__(self, rpchandler: rpc.RPCHandler) -> None: ...
    user_exc_info: tuple[BaseException, str, TracebackType] | None
    def runcode(self, code: str) -> None: ...
    def interrupt_the_server(self) -> None: ...
    def start_the_debugger(self, gui_adap_oid: str) -> str: ...
    def stop_the_debugger(self, idb_adap_oid: str) -> None: ...
    def get_the_calltip(self, name: str) -> str: ...
    def get_the_completion_list(
        self,
        what: str,
        mode: int,
    ) -> tuple[list[str], list[str]]: ...
    def stackviewer(  # noqa: F811
        self,
        flist_oid: str | None = ...,
    ) -> int: ...
