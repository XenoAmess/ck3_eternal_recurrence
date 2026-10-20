"""Real fresh base-Python -S dependency/role imports; no CK3, Task, RPC or writes."""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import prepare_c23_a04_isolated_controls_v1 as p
T=p.OLD_RUNTIME
S=Path('Z:/ck3_mod_rewrite/tools/.venv/Lib/site-packages')
ROLES={'owner':'launch_sdk_p37c23_owner.py','Queue':'root_p37c23_sdk_queue.py','MCPApp':'root_p37c23_mcp_entry.py'}


def child(role):
    assert sys.flags.no_site and str(S) in sys.path
    outer=T/'root_c23_canonical_outer.py';data=outer.read_bytes()
    if role!='original':data=p.dependency_outer(data)
    scope={'__file__':str(outer),'__name__':'_offline_actual_outer'}
    exec(compile(data,str(outer),'exec'),scope)
    binding=scope['OuterBindingV1'](T)
    os.environ.update(binding.child_env({}))
    if role=='original':
        try:__import__('mcp')
        except ModuleNotFoundError as error:
            assert error.name=='pywintypes'
            return {'role':role,'status':'ORIGINAL_MISSING_PYWINTYPES_REPRODUCED','missing':error.name}
        raise AssertionError('original precondition unexpectedly imported MCP')
    sys.path.insert(0,str(T))
    path=T/ROLES[role];tree=ast.parse(path.read_bytes())
    count=0
    for i,node in enumerate(tree.body):
        if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='_canonical' for x in node.targets):
            assert isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='receive_entry'
            tree.body[i]=ast.copy_location(ast.Assign(targets=node.targets,value=ast.Constant(None)),node);count+=1
    assert count==1
    if role=='MCPApp':
        assert isinstance(tree.body[-1],ast.Try) and ast.unparse(tree.body[-1].body[0])=='mcp_server.main()'
        tree.body.pop()
    exec(compile(ast.fix_missing_locations(tree),str(path),'exec'),
        {'__file__':str(path),'__name__':'_offline_actual_'+role})
    from mcp import ClientSession,StdioServerParameters
    from mcp.client import stdio
    import mcp,pywintypes,pywin32_bootstrap
    assert Path(mcp.__file__).resolve().is_relative_to(S.resolve())
    assert Path(pywintypes.__file__).resolve()==(S/'pywin32_system32/pywintypes313.dll').resolve()
    names=['pywin32.pth','win32/lib/pywin32_bootstrap.py','win32/lib/pywintypes.py']
    pins=[p.ref(S/name) for name in names]
    pins.append(p.ref(pywintypes.__file__))
    return {'role':role,'status':'ACTUAL_BASE_NO_SITE_ROLE_IMPORTS_PASS',
        'python':str(Path(sys.executable).resolve()),'no_site':sys.flags.no_site,
        'stage':p.ref(path),'mcp':str(Path(mcp.__file__).resolve()),
        'pywin32_bootstrap':str(Path(pywin32_bootstrap.__file__).resolve()),
        'pywintypes_DLL':str(Path(pywintypes.__file__).resolve()),'additional_dependency_pins':pins,
        'private_custody_receipt':'SUPPRESSED_OFFLINE_ONLY','stage_main_calls':0,
        'Game_Task_RPC_Driver_Service_calls':0,'files_written':0}


def main():
    if len(sys.argv)==3 and sys.argv[1]=='--child':
        print(json.dumps(child(sys.argv[2])));return 0
    base=Path(sys._base_executable).resolve()
    env={**os.environ,'PYTHONPATH':str(S),'PYTHONDONTWRITEBYTECODE':'1'}
    rows=[]
    for role in ('original',*ROLES):
        done=subprocess.run([str(base),'-B','-S','-X','utf8',str(Path(__file__).resolve()),'--child',role],
            env=env,cwd=T,capture_output=True,text=True,encoding='utf-8',timeout=120)
        if done.returncode:raise RuntimeError(role+':'+done.stderr[-6000:])
        rows.append(json.loads(done.stdout))
    print(json.dumps({'schema':'xar.A04-base-no-site-role-import-qualification/v1','machine_id':p.MACHINE,
        'rows':rows,'separate_fresh_processes':4,'Game_Task_RPC_Driver_Service_calls':0,'files_written':0}))
    return 0


if __name__=='__main__':raise SystemExit(main())

