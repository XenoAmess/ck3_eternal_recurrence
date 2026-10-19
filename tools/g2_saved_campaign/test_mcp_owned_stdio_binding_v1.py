"""Stock creator code; injected Job observations; owned Python children ONLY."""
import asyncio
from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
import subprocess
import sys
from types import FunctionType, ModuleType, SimpleNamespace
import unittest
import weakref
from unittest.mock import patch

import anyio
import mcp.client.stdio as stock
import mcp.os.win32.utilities as windows

from tools.g2_saved_campaign import mcp_owned_stdio_binding_v1 as binding
from tools.g2_saved_campaign.owned_python_launch_v1 import owned_python_launch_v1

RUNS = []
CHILD = "import os,sys,json,msvcrt; a=msvcrt.open_osfhandle(int(sys.argv[1]),os.O_RDONLY); b=msvcrt.open_osfhandle(int(sys.argv[2]),os.O_WRONLY); data=os.read(a,1).decode(); os.close(a); os.close(b); print(json.dumps({'pid':os.getpid(),'payload':data}),flush=True); sys.stdin.readline()"


def fake_job():
    return object()


def fake_assign(process, job):
    _process_jobs[process] = job
    _observed.append(("assigned",process.pid))


async def fake_terminate(process):
    _process_jobs.pop(process, None)
    _observed.append(("cleanup",process.pid))


def fake_close_job(process):
    _process_jobs.pop(process,None)
    _observed.append(("normal_cleanup",process.pid))


def fake_modules():
    u = ModuleType("owned_fake_windows")
    u.__dict__.update(windows.__dict__)
    u._process_jobs, u._observed = weakref.WeakKeyDictionary(), []
    for name, func in (("_create_job_object",fake_job),("_maybe_assign_process_to_job",fake_assign),
                       ("terminate_windows_process_tree",fake_terminate),("close_process_job",fake_close_job)):
        u.__dict__[name] = FunctionType(func.__code__,u.__dict__,name)
    for name in ("create_windows_process","_create_windows_fallback_process"):
        u.__dict__[name] = binding._bind(getattr(windows,name),u.__dict__)
    s = ModuleType("owned_fake_stdio")
    s.__dict__.update(stock.__dict__)
    stop_globals = dict(stock._stop_server_process.__globals__)
    stop_globals["terminate_windows_process_tree"] = u.terminate_windows_process_tree
    stop_globals["close_process_job"] = u.close_process_job
    s._stop_server_process = binding._bind(stock._stop_server_process,stop_globals)
    s.create_windows_process = u.create_windows_process
    s._create_platform_compatible_process = binding._bind(stock._create_platform_compatible_process,s.__dict__)
    return s,u


def assemble(s,u,*,command,env,cwd=None,startup=None,custody=None,async_open=None):
    proxy = SimpleNamespace(open_process=async_open or anyio.open_process)
    return binding._assemble(s,u,proxy,subprocess,expected=(tuple(command),dict(env),cwd),
        startupinfo=startup or SimpleNamespace(lpAttributeList={"handle_list":[111,222]}),
        custody=custody or SimpleNamespace(closed=False,_owned=[111,222]),
        _test_boundary=binding._TEST_BOUNDARY)


class PureBindingTests(unittest.TestCase):
    @unittest.skipUnless(os.name=="nt","Windows constructor shape")
    def test_public_constructor_uses_original_weak_job_table_and_copies_handles(self):
        src=str(Path(__file__).resolve().parents[2]/"ck3_autonomous_player/src")
        if src not in sys.path:sys.path.insert(0,src)
        from xar_autoplayer.bridge import native_loaded_provider_custody_v1 as custody
        resource=object.__new__(custody._PreloadCustodyV1)
        resource.seal,resource.closed,resource._owned=custody._RESOURCE_SEAL,False,[111,222]
        startup=subprocess.STARTUPINFO(lpAttributeList={"handle_list":[111,222]})
        a=binding.bind_owned_stdio_v1(inherited_custody=resource,
            expected_server=stock.StdioServerParameters(command=sys.executable,args=[]),
            startupinfo=startup,enabled=True)
        self.assertIs(a.job_table,windows._process_jobs)
        self.assertIsNot(a.startupinfo,startup)
        startup.lpAttributeList["handle_list"].append(333)
        self.assertEqual(a.startupinfo.lpAttributeList["handle_list"],[111,222])
        self.assertIsNone(a.created_child)

    def test_disabled_and_public_json_refuse_before_dependency_or_OS(self):
        with patch.object(binding,"_dependency_pins",side_effect=AssertionError("must stay lazy")):
            self.assertIsNone(binding.bind_owned_stdio_v1(inherited_custody={},expected_server={},
                                                        startupinfo=None))
        with self.assertRaisesRegex(binding.OwnedBindingUnavailable,"private receiver"):
            binding.bind_owned_stdio_v1(inherited_custody={"handles":[1,2]},expected_server={},
                                         startupinfo=None,enabled=True)

    def test_original_job_table_and_all_global_modules_remain_identical(self):
        before=(stock._create_platform_compatible_process,windows.anyio,windows.subprocess,
                dict(windows._process_jobs))
        self.assertIs(binding._job_links(stock,windows),windows._process_jobs)
        binding._dependency_pins(stock,windows)
        s,u=fake_modules();a=assemble(s,u,command=["owned"],env={});b=assemble(s,u,command=["other"],env={})
        self.assertIsNot(a.private_stdio.__dict__,b.private_stdio.__dict__)
        self.assertIs(a.stdio_client.__wrapped__.__globals__,a.private_stdio.__dict__)
        self.assertIs(a.job_table,u._process_jobs)
        self.assertIs(b.job_table,u._process_jobs)
        self.assertEqual(before,(stock._create_platform_compatible_process,windows.anyio,
                                 windows.subprocess,dict(windows._process_jobs)))

    def test_detached_job_cleanup_table_is_rejected(self):
        for name in ("terminate_windows_process_tree","close_process_job"):
            with self.subTest(helper=name):
                s,u=fake_modules()
                wrong=dict(u.__dict__);wrong["_process_jobs"]={}
                setattr(u,name,binding._bind(getattr(u,name),wrong))
                with self.assertRaisesRegex(binding.OwnedBindingUnavailable,"different tables"):
                    assemble(s,u,command=["owned"],env={})

    def test_one_shot_command_mutation_and_original_oserror(self):
        sentinel=OSError("owned creation marker")
        async def fail(*args,**kwargs):raise sentinel
        async def check():
            s,u=fake_modules();a=assemble(s,u,command=["owned"],env={},async_open=fail)
            with self.assertRaises(binding.OwnedBindingUnavailable):
                await a.private_stdio._create_platform_compatible_process("foreign",[],env={})
            self.assertIsNone(a.created_child)
            a=assemble(s,u,command=["owned"],env={},async_open=fail)
            with self.assertRaises(OSError) as seen:
                await a.private_stdio._create_platform_compatible_process("owned",[],env={})
            self.assertIs(seen.exception,sentinel)
            self.assertIs(a.creation_error,sentinel)
            with self.assertRaisesRegex(binding.OwnedBindingUnavailable,"one-shot"):
                await a.private_stdio._create_platform_compatible_process("owned",[],env={})
            a=assemble(s,u,command=["owned"],env={},async_open=fail)
            a.startupinfo.lpAttributeList["handle_list"].append(333)
            with self.assertRaisesRegex(binding.OwnedBindingUnavailable,"handles changed"):
                await a.private_stdio._create_platform_compatible_process("owned",[],env={})
        anyio.run(check)


@unittest.skipUnless(os.name=="nt","owned Windows subprocess checks")
class OwnedProcessTests(unittest.TestCase):
    def handles(self, label):
        import _winapi,msvcrt
        read,write=os.pipe()
        current=_winapi.GetCurrentProcess()
        handles=[_winapi.DuplicateHandle(current,msvcrt.get_osfhandle(fd),current,0,True,
                    _winapi.DUPLICATE_SAME_ACCESS) for fd in (read,write)]
        os.write(write,label.encode())
        return (read,write),handles

    def test_parallel_async_and_stock_fallback_isolated_owned_children(self):
        import _winapi
        from tools.g2_saved_campaign.sdk_process_custody import RetainedProcessGeneration
        original=(stock._create_platform_compatible_process,windows.anyio,windows.subprocess,
                  dict(windows._process_jobs))
        s,u=fake_modules();opened=[];results=[]
        async def fallback(*args,**kwargs):raise NotImplementedError("owned test fallback")
        async def one(label, use_fallback):
            fds,handles=self.handles(label);opened.append((fds,handles))
            startup=subprocess.STARTUPINFO(lpAttributeList={"handle_list":handles})
            executable,env=owned_python_launch_v1()
            command=[executable,"-B","-c",CHILD,*map(str,handles)]
            a=assemble(s,u,command=command,env=env,startup=startup,
                custody=SimpleNamespace(closed=False,_owned=handles),
                async_open=fallback if use_fallback else None)
            child=await a.private_stdio._create_platform_compatible_process(command[0],command[1:],env=env)
            generation=None
            try:
                line=await child.stdout.receive()
                observed=json.loads(line)
                self.assertEqual(observed,{"pid":child.pid,"payload":label})
                generation=RetainedProcessGeneration.capture(child.pid,expected_executable=executable)
                self.assertEqual(a.created_child.pid,child.pid)
                self.assertIsNone(a.creation_error)
                self.assertIn(child,u._process_jobs)
                await child.stdin.send(b"close\n");await child.stdin.aclose()
                self.assertEqual(await child.wait(),0)
                await u.terminate_windows_process_tree(child)
                results.append({"path":"stock_fallback" if use_fallback else "async", "pid":child.pid,
                    "creation_filetime":str(generation.creation_filetime),"inherited_payload":label,
                    "exit_code":0,"injected_job_cleanup":True,"real_MCP_or_Job":False})
            finally:
                if hasattr(child,"aclose"):
                    await child.aclose()
                else:
                    await child.stdout.aclose()
                if generation is not None:generation.close()
        async def run():
            async with anyio.create_task_group() as group:
                group.start_soon(one,"A",False);group.start_soon(one,"B",True)
        try:anyio.run(run)
        finally:
            for fds,handles in opened:
                for handle in handles:_winapi.CloseHandle(handle)
                for fd in fds:os.close(fd)
        self.assertEqual(len(results),2)
        self.assertEqual(u._process_jobs,{})
        self.assertEqual(original,(stock._create_platform_compatible_process,windows.anyio,
                                   windows.subprocess,dict(windows._process_jobs)))
        RUNS.extend(results)

    def test_post_create_error_keeps_exact_child_and_original_exception(self):
        async def check():
            s,u=fake_modules();sentinel=RuntimeError("injected Job setup marker")
            def fail_job():raise sentinel
            u.__dict__["_create_job_object"]=fail_job
            executable,env=owned_python_launch_v1()
            command=[executable,"-B","-c","import sys; sys.stdin.readline()"]
            a=assemble(s,u,command=command,env=env,
                startup=subprocess.STARTUPINFO(lpAttributeList={"handle_list":[]}),
                custody=SimpleNamespace(closed=False,_owned=[]))
            with self.assertRaises(RuntimeError) as seen:
                await a.private_stdio._create_platform_compatible_process(command[0],command[1:],env=env)
            self.assertIs(seen.exception,sentinel)
            self.assertIs(a.creation_error,sentinel)
            child=a.created_child
            self.assertIsNotNone(child)
            await child.stdin.send(b"close\n");await child.stdin.aclose()
            self.assertEqual(await child.wait(),0)
            await child.aclose()
            self.assertEqual(u._process_jobs,{})
        anyio.run(check)


    def test_cancel_preserves_original_cancellation_without_second_spawn(self):
        async def cancelled(*args,**kwargs):raise asyncio.CancelledError()
        async def check():
            s,u=fake_modules();a=assemble(s,u,command=["owned"],env={},async_open=cancelled)
            with self.assertRaises(asyncio.CancelledError):
                await a.private_stdio._create_platform_compatible_process("owned",[],env={})
            self.assertIsNone(a.created_child)
            self.assertIsInstance(a.creation_error,asyncio.CancelledError)
            with self.assertRaisesRegex(binding.OwnedBindingUnavailable,"one-shot"):
                await a.private_stdio._create_platform_compatible_process("owned",[],env={})
        anyio.run(check)


@unittest.skipUnless(os.name=="nt" and os.environ.get("XAR_OWNED_STOCK_MCP_TEST")=="1",
                     "explicit isolated stock MCP/Job owned-test opt-in")
class RealStockOwnedTest(unittest.TestCase):
    def test_stock_stdio_job_identity_and_original_normal_cleanup(self):
        import _winapi
        import ctypes
        from ctypes import wintypes
        src=str(Path(__file__).resolve().parents[2]/"ck3_autonomous_player/src")
        if src not in sys.path:sys.path.insert(0,src)
        from xar_autoplayer.bridge import native_loaded_provider_custody_v1 as custody
        from tools.g2_saved_campaign.sdk_process_custody import retain_mcp_stdio_process
        self.assertEqual(len(windows._process_jobs),0,"requires fresh isolated test interpreter")
        before=(stock._create_platform_compatible_process,windows.anyio,windows.subprocess)
        fds,handles=OwnedProcessTests().handles("R")
        resource=object.__new__(custody._PreloadCustodyV1)
        resource.seal,resource.closed,resource._owned=custody._RESOURCE_SEAL,False,handles
        program="import os,sys,json,msvcrt; a=msvcrt.open_osfhandle(int(sys.argv[1]),os.O_RDONLY); b=msvcrt.open_osfhandle(int(sys.argv[2]),os.O_WRONLY); payload=os.read(a,1).decode(); os.close(a); os.close(b); print(json.dumps({'jsonrpc':'2.0','method':'owned_ready','params':{'pid':os.getpid(),'payload':payload}}),flush=True); sys.stdin.read()"
        executable,env=owned_python_launch_v1()
        params=stock.StdioServerParameters(command=executable,args=["-B","-c",program,*map(str,handles)],env=env)
        owned=binding.bind_owned_stdio_v1(inherited_custody=resource,expected_server=params,
            startupinfo=subprocess.STARTUPINFO(lpAttributeList={"handle_list":handles}),enabled=True)
        record={"real_stock_MCP":True,"existing_runtime_access":False,"production_custody":False}
        async def run():
            async with retain_mcp_stdio_process(owned.private_stdio,expected_executable=executable) as capture:
                async with owned.stdio_client(params) as (read,write):
                    with anyio.fail_after(10):message=await read.receive()
                    self.assertEqual(message.message.method,"owned_ready")
                    child=owned.created_child
                    self.assertEqual(message.message.params,{"pid":child.pid,"payload":"R"})
                    gen=capture.require_generation()
                    self.assertEqual(gen.pid,child.pid)
                    job=windows._process_jobs.get(child)
                    job_value=int(job) if job is not None else None
                    record.update(pid=child.pid,creation_filetime=str(gen.creation_filetime),
                                  inherited_payload="R",job_table_entry=job is not None)
                    if job is not None:
                        try:
                            record["child_in_exact_job"]=bool(windows.win32job.IsProcessInJob(int(gen._handle),job))
                        except Exception as error:
                            record["child_in_exact_job"]="unknown:"+type(error).__name__
                        record["job_handle"]=str(int(job))
                    else:record["child_in_exact_job"]="unknown:no_stock_job"
                record["exit_code"]=gen._api.get_exit_code(gen._handle)
                record["wait_zero"]=gen._api.wait_zero(gen._handle)
                self.assertEqual((record["exit_code"],record["wait_zero"]),(0,0))
                self.assertNotIn(child,windows._process_jobs)
                record["original_job_entry_removed"]=True
                if job is not None:
                    flags=wintypes.DWORD()
                    query=gen._api._kernel.GetHandleInformation
                    query.argtypes,query.restype=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)],wintypes.BOOL
                    ctypes.set_last_error(0)
                    record["job_handle_closed"]=not bool(query(job_value,ctypes.byref(flags)))
                    record["job_handle_error"]=ctypes.get_last_error()
                record["capture_handle_closed_by_owner_after_context"]=True
            self.assertTrue(capture.generation._closed)
        try:anyio.run(run)
        finally:
            for handle in handles:_winapi.CloseHandle(handle)
            for fd in fds:os.close(fd)
        self.assertEqual(before,(stock._create_platform_compatible_process,windows.anyio,windows.subprocess))
        self.assertEqual(len(windows._process_jobs),0)
        RUNS.append(record)

if __name__=="__main__":unittest.main()
