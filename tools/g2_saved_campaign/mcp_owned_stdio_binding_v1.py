"""Default-OFF per-session MCP creator binding; never a Native qualification.

Only stock code objects are rebound. Installed module dictionaries, AnyIO and
subprocess are never patched. The future canonical receiver must supply real
owned/inheritable resources; this file cannot manufacture that custody.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import Mapping, MutableMapping
import hashlib
from pathlib import Path
import subprocess
import threading
from types import FunctionType, ModuleType

_TEST_BOUNDARY = object()
_PINS = {
    "stdio.py": "bc987925a3da72f4ca59ccd627a6fc6ba258582d50515a532503abe6d1b9dbab",
    "utilities.py": "98e87c776a14cf326e63f8da007119156d3ad643ae7fbf27e9b6e6ef1dc534bf",
}


class OwnedBindingUnavailable(RuntimeError):
    pass


def _need(ok, why):
    if not ok:
        raise OwnedBindingUnavailable(why)


def _bind(function, namespace):
    _need(type(function) is FunctionType and not function.__code__.co_freevars,
          "unsupported dependency closure")
    result = FunctionType(function.__code__, namespace, function.__name__, function.__defaults__)
    result.__kwdefaults__ = function.__kwdefaults__
    result.__annotations__ = dict(function.__annotations__)
    result.__qualname__ = function.__qualname__
    result.__doc__ = function.__doc__
    return result


def _job_links(stdio, utilities):
    jobs = utilities._process_jobs
    _need(isinstance(jobs,MutableMapping), "original Job table unavailable")
    _need(utilities._maybe_assign_process_to_job.__globals__.get("_process_jobs") is jobs
          and utilities.terminate_windows_process_tree.__globals__.get("_process_jobs") is jobs
          and utilities.close_process_job.__globals__.get("_process_jobs") is jobs,
          "Job assignment and termination use different tables")
    _need(stdio._stop_server_process.__globals__.get("terminate_windows_process_tree")
          is utilities.terminate_windows_process_tree
          and stdio._stop_server_process.__globals__.get("close_process_job") is utilities.close_process_job,
          "original stdio cleanup does not use the same Job termination helper")
    return jobs


def _dependency_pins(stdio, utilities):
    for module, filename in ((stdio,"stdio.py"),(utilities,"utilities.py")):
        path = Path(module.__file__).resolve()
        _need(path.name == filename and hashlib.sha256(path.read_bytes()).hexdigest() == _PINS[filename],
              "unsupported installed MCP source")
    expected = [
        (stdio.stdio_client.__wrapped__, ("server","errlog")),
        (stdio._create_platform_compatible_process, ("command","args","env","errlog","cwd")),
        (utilities.create_windows_process, ("command","args","env","errlog","cwd")),
        (utilities._create_windows_fallback_process, ("command","args","env","errlog","cwd")),
    ]
    for function, names in expected:
        _need(type(function) is FunctionType and function.__code__.co_varnames[:function.__code__.co_argcount] == names
              and not function.__code__.co_freevars, "unsupported MCP function shape")
        _need(Path(function.__code__.co_filename).resolve() in
              {Path(stdio.__file__).resolve(),Path(utilities.__file__).resolve()},
              "foreign MCP function source")


class BoundOwnedStdioV1:
    """One exact spawn, resources retained on errors; not a provider/DTO."""
    def __init__(self, *, stdio, utilities, expected, startupinfo, custody):
        self._lock = threading.Lock()
        self._phase = "new"
        self.expected = (tuple(expected[0]),dict(expected[1]) if expected[1] is not None else None,expected[2])
        self.startupinfo, self.custody = startupinfo, custody
        self._handles = tuple(startupinfo.lpAttributeList["handle_list"])
        self.created_child = None
        self.creation_error = None
        self.job_table = _job_links(stdio, utilities)
        self.private_stdio = ModuleType("xar_private_owned_stdio")
        self.private_stdio.__dict__.update(stdio.__dict__)
        self.private_stdio.__name__ = "xar_private_owned_stdio"

    def _reserve(self, command, kwargs, phase):
        with self._lock:
            _need(self._phase == ("new" if phase == "async" else "fallback_ready"),
                  "owned creator is one-shot")
            _need(not self.custody.closed, "owned custody closed before creation")
            _need(tuple(self.startupinfo.lpAttributeList.get("handle_list",())) == self._handles
                  and all(h in self.custody._owned for h in self._handles),
                  "owned startup handles changed before creation")
            _need(tuple(command) == self.expected[0] and kwargs.get("env") == self.expected[1]
                  and kwargs.get("cwd") == self.expected[2], "exact owned command/env/cwd changed")
            _need("startupinfo" not in kwargs, "dependency startupinfo collision")
            self._phase = phase

    def _failed(self, error, *, fallback=False):
        with self._lock:
            self.creation_error = error
            self._phase = "fallback_ready" if fallback and self.created_child is None else "failed"

    def _created(self, child):
        with self._lock:
            _need(self.created_child is None, "second child was returned")
            self.created_child = child
            self.creation_error = None
            self._phase = "created"


def _assemble(stdio, utilities, anyio_module, subprocess_module, *, expected, startupinfo,
              custody, _test_boundary=None):
    # Production passes canonical imports; tests only substitute OS/process/Job
    # observations while retaining the exact stock function code objects.
    _need(_test_boundary is _TEST_BOUNDARY or _test_boundary is None, "invalid assembly boundary")
    binding = BoundOwnedStdioV1(stdio=stdio,utilities=utilities,expected=expected,
                               startupinfo=startupinfo,custody=custody)
    windows_globals = dict(utilities.create_windows_process.__globals__)
    fallback_globals = dict(utilities._create_windows_fallback_process.__globals__)

    class AnyIOForward:
        def __getattr__(self, name): return getattr(anyio_module,name)
        async def open_process(self, command, **kwargs):
            binding._reserve(command,kwargs,"async")
            try:
                child = await anyio_module.open_process(command,startupinfo=startupinfo,**kwargs)
            except BaseException as error:
                binding._failed(error,fallback=isinstance(error,NotImplementedError))
                raise
            binding._created(child)
            return child

    class PopenForward:
        def __getattr__(self, name): return getattr(subprocess_module,name)
        def Popen(self, command, **kwargs):
            binding._reserve(command,kwargs,"fallback")
            _need("close_fds" not in kwargs or kwargs["close_fds"] is True,
                  "fallback broad inheritance forbidden")
            kwargs["close_fds"] = True
            try:
                child = subprocess_module.Popen(command,startupinfo=startupinfo,**kwargs)
            except BaseException as error:
                binding._failed(error)
                raise
            binding._created(child)
            return child

    windows_globals["anyio"] = AnyIOForward()
    fallback_globals["subprocess"] = PopenForward()
    windows_globals["_create_windows_fallback_process"] = _bind(
        utilities._create_windows_fallback_process,fallback_globals)
    owned_windows = _bind(utilities.create_windows_process,windows_globals)
    private_globals = binding.private_stdio.__dict__
    private_globals["create_windows_process"] = owned_windows
    platform_creator = _bind(stdio._create_platform_compatible_process,private_globals)

    async def owned_creator(*args, **kwargs):
        try:
            return await platform_creator(*args,**kwargs)
        except BaseException as error:
            # Keep the exact child reference if stock Job/capture setup failed
            # after process creation. The existing owner, never a retry, cleans it.
            binding._failed(error)
            raise

    private_globals["_create_platform_compatible_process"] = owned_creator
    binding.stdio_client = asynccontextmanager(_bind(stdio.stdio_client.__wrapped__,private_globals))
    _need(windows_globals["_process_jobs"] is binding.job_table
          and fallback_globals["_process_jobs"] is binding.job_table,
          "private creator detached the original Job table")
    return binding


def bind_owned_stdio_v1(*, inherited_custody, expected_server, startupinfo, enabled=False):
    """Future Queue bootstrap only; disabled returns None before imports/OS.

    Startup handles must already be inheritable OWNED receiver resources. This
    binder does not reopen a PID/file, infer source custody, or mint a provider.
    Caller must use the actual App receiver ACK before releasing sender copies.
    """
    if enabled is not True:
        return None
    _need(inherited_custody is not None and not isinstance(inherited_custody,(Mapping,list,tuple,str,bytes,int,float,bool)),
          "actual private receiver custody required")
    from xar_autoplayer.bridge.native_loaded_provider_custody_v1 import _PreloadCustodyV1, _RESOURCE_SEAL
    _need(type(inherited_custody) is _PreloadCustodyV1
          and inherited_custody.seal is _RESOURCE_SEAL and not inherited_custody.closed,
          "actual private receiver custody required")
    _need(type(startupinfo) is getattr(subprocess,"STARTUPINFO",None), "Windows startupinfo required")
    attributes = startupinfo.lpAttributeList
    _need(type(attributes) is dict and set(attributes) == {"handle_list"}, "selective handle list required")
    handles = attributes["handle_list"]
    _need(type(handles) is list and len(handles) >= 2 and len(set(handles)) == len(handles)
          and all(type(h) is int and h > 0 and h in inherited_custody._owned for h in handles),
          "only owned receiver handles may be inherited")
    _need(startupinfo.dwFlags == 0 and all(getattr(startupinfo,k) is None
          for k in ("hStdInput","hStdOutput","hStdError")),
          "caller-provided standard/control handles forbidden")
    owned_startup = subprocess.STARTUPINFO(lpAttributeList={"handle_list":list(handles)})
    import mcp.client.stdio as stdio
    import mcp.os.win32.utilities as utilities
    import anyio
    _dependency_pins(stdio,utilities)
    _need(type(expected_server) is stdio.StdioServerParameters,"frozen MCP server parameters required")
    expected = (tuple([stdio._get_executable_command(expected_server.command),*expected_server.args]),
                stdio.get_default_environment() | (expected_server.env or {}), expected_server.cwd)
    return _assemble(stdio,utilities,anyio,subprocess,expected=expected,startupinfo=owned_startup,
                     custody=inherited_custody)
