"""Future C17 exact outer creator hunks over the frozen C16 graph, in memory only.

This does not choose a complete SDK canonical tree, create a Task, or supply a
future checkpoint. The caller must freeze the complete M7 prerequisite closure.
"""
import ast
import hashlib
from pathlib import Path

import prepare_checkpoint6397_c16_sources_v1 as prior

OWN = Path(__file__).resolve().parent
MAP = [('P37C16','P37C17'),('p37c16','p37c17'),('_c16','_c17'),('-C16','-C17'),
       ('SDKC16','SDKC17'),('xar.c16.','xar.c17.'),('NATIVE29','NATIVE30'),
       ('root_native29_supervisor','root_native30_supervisor')]
PINS = {'root_native29_supervisor_c16.py':'2b470516f05f324440b0c23f3354109bbe67c2792339dc5a15f2166be5c3ae77',
    'root_checkpoint_bootstrap_c16.py':'7db736e1fe3db39c3c119c01bb18e06fc72bab8b67792ac3854b382f33bf520b',
    'launch_sdk_p37c16_owner.py':'8302bee328111f411d5a5c33eb1a2a97a6aea06b7ca957d4bb0f20f702de20ea',
    'root_p37c16_sdk_queue.py':'58f6ff2126793cb1c2f1d61f37ea8f9057c65fe1e53e84fdf921d33ab8ee9d83',
    'root_p37c16_mcp_entry.py':'e486fa1ccd3b10e290bcc96cfdf4c66c2b0a4a6f34f5fa78d1d85341d8d760fa'}


def swap(value, old, new, changes):
    if value.count(old)!=1:
        raise ValueError('unique actual C16 creator seam absent: '+old[:100])
    changes.append((old,new))
    return value.replace(old,new,1)


def name17(name):
    for old,new in MAP:name=name.replace(old,new)
    return name


def build_sources(*, enabled=False, native_build_label=None):
    if type(enabled) is not bool:raise ValueError('explicit source boolean required')
    if enabled and (not isinstance(native_build_label,str) or not native_build_label.startswith('Native30 ')):
        raise ValueError('future exact qualified Native30 build label required; no guessed label')
    base=prior.build_sources()
    for name,digest in PINS.items():
        if hashlib.sha256(base[name]).hexdigest()!=digest:raise ValueError('C16 actual baseline differs: '+name)
    out={name17(name):prior.prior.port(raw.decode(),MAP) for name,raw in base.items()}
    ported=dict(out);records={}
    def patch(name,old,new):out[name]=swap(out[name],old,new,records.setdefault(name,[]))
    state='True' if enabled else 'False'
    helper='root_c17_canonical_outer'
    supervisor='root_native30_supervisor_c17.py';boot='root_checkpoint_bootstrap_c17.py'
    owner='launch_sdk_p37c17_owner.py';queue='root_p37c17_sdk_queue.py';app='root_p37c17_mcp_entry.py'
    patch(boot,'def launch_prepared(spec, dll, injector, *, before_process_create=None):',
        'def launch_prepared(spec, dll, injector, *, before_process_create=None, pre_native_resume=None):')
    patch(boot,"    return runtime.launch(spec, native_bridge=bridge, continue_last_save=False,",
        "    preload_options = {} if pre_native_resume is None else {'pre_native_resume': pre_native_resume}\n"
        "    return runtime.launch(spec, native_bridge=bridge, continue_last_save=False,")
    patch(boot,'        start_minimized=True, before_process_create=before_process_create)',
        '        start_minimized=True, before_process_create=before_process_create, **preload_options)')
    patch(boot,'    from root_checkpoint6397_cold_contract_c17 import validate_abnormal_closure\n    validate_abnormal_closure(close)',
        "    if close.get('old_sdk_closure_kind') == 'EXACT_C15_INTERRUPTED_F90':\n"
        '        from root_checkpoint6397_cold_contract_c17 import validate_abnormal_closure\n'
        '        validate_abnormal_closure(close)\n'
        '    else:\n        from root_c17_normal_checkpoint_inputs import validate_normal_closure\n'
        '        validate_normal_closure(close, checked)')
    patch('root_p37c17_cold_resume.py',
        '    validate_rollback(admission, seed, gov, checkpoint_saved=checkpoint_saved)',
        "    if admission.get('old_sdk_closure_kind') == 'EXACT_C16_NORMAL_CHECKPOINT_FOR_C17':\n"
        '        from root_c17_normal_checkpoint_inputs import validate_saved_seed\n'
        '        validate_saved_seed(admission, seed, original, save, saved_semantic, gov,\n'
        '            projector=project_checkpoint_seed, checked=checked)\n'
        '    else:\n        validate_rollback(admission, seed, gov, checkpoint_saved=checkpoint_saved)')
    patch(supervisor,'    frozen = read(N / "ROOT-FINAL-SDK-FREEZE-P37C17.json")',
        '    frozen = read(N / "ROOT-FINAL-SDK-FREEZE-P37C17.json")\n'
        f'    from {helper} import prepare_supervisor\n'
        f'    canonical = prepare_supervisor(N, enabled={state})')
    old='''    for relative in ("xar_autoplayer/environment.py", "xar_autoplayer/runtime.py"):
        if digest(source / relative) != digest(final_source / relative):
            raise ValueError("clean master public runtime differs from the final SDK freeze")'''
    new='''    if canonical is None:
'''+''.join('    '+line+'\n' for line in old.splitlines()).rstrip('\n')+'''
    else:
        canonical.verify_runtime_sources(source, final_source)'''
    patch(supervisor,old,new)
    patch(supervisor,'    sys.path.insert(0, str(source))\n    from xar_autoplayer import environment, runtime',
        '    creator_source = source if canonical is None else final_source\n'
        '    sys.path.insert(0, str(creator_source))\n    from xar_autoplayer import environment, runtime')
    patch(supervisor,'Path(environment.__file__).resolve() != source / "xar_autoplayer/environment.py"',
        'Path(environment.__file__).resolve() != creator_source / "xar_autoplayer/environment.py"')
    patch(supervisor,'Path(runtime.__file__).resolve() != source / "xar_autoplayer/runtime.py"',
        'Path(runtime.__file__).resolve() != creator_source / "xar_autoplayer/runtime.py"')
    patch(supervisor,'        spec = environment.make_spec(state_dir=N / "state", game_dir=game_dir)',
        '        if canonical is not None:\n'
        '            from root_checkpoint_bootstrap_c17 import api as canonical_api\n'
        '            actual_environment, _, actual_runtime = canonical_api()\n'
        '            if actual_environment is not environment or actual_runtime is not runtime:\n'
        '                raise ValueError("canonical creator runtime differs from original cold validator")\n'
        '            canonical.prepare_factory(config["dll_sha256"])\n'
        '        spec = environment.make_spec(state_dir=N / "state", game_dir=game_dir)')
    patch(supervisor,'            handle = launch_prepared(spec, dll, injector, before_process_create=None)',
        '            handle = launch_prepared(spec, dll, injector, before_process_create=None,\n'
        '                pre_native_resume=None if canonical is None else canonical.factory.pre_native_resume)')
    patch(supervisor,'            retain_sdk_pair(sdk_pair, RetainedProcessGeneration)',
        '            if canonical is not None:\n'
        '                canonical.maybe_create_owner(generation)\n'
        '            retain_sdk_pair(sdk_pair, RetainedProcessGeneration)')
    patch(supervisor,'    finally:\n        if handle is not None:',
        '    finally:\n        if canonical is not None:\n'
        '            try:\n                canonical.revoke()\n'
        '            except Exception as error:\n'
        '                if failure is None:\n'
        '                    failure = {"type": type(error).__name__, "message": str(error)[:4096]}\n'
        '        if handle is not None:')
    patch(supervisor,'        keeper.stop()',
        '        if canonical is not None:\n'
        '            try:\n                canonical.close()\n'
        '            except Exception as error:\n'
        '                if failure is None:\n'
        '                    failure = {"type": type(error).__name__, "message": str(error)[:4096]}\n'
        '        keeper.stop()')
    for name,role,anchor in ((owner,'owner','N=Path(__file__).resolve().parent\n'),
            (queue,'Queue','N = Path(__file__).resolve().parent\n')):
        patch(name,anchor,anchor+f'from {helper} import receive_entry\n'
            f'_canonical = receive_entry(N, {role!r}, sys.argv, enabled={state})\n')
    patch(owner,"        child=subprocess.Popen(argv,cwd=str(N),stdout=stdout,stderr=stderr,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))",
        "        child=(_canonical.spawn_queue(argv,stdout=stdout,stderr=stderr) if _canonical is not None else\n"
        "            subprocess.Popen(argv,cwd=str(N),stdout=stdout,stderr=stderr,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)))")
    patch(owner,"if __name__=='__main__': raise SystemExit(main())",
        "if __name__=='__main__':\n    try:\n        raise SystemExit(main())\n"
        "    finally:\n        if _canonical is not None:\n            _canonical.close()")
    patch(queue,'    dependency_root = str((Path(sys.prefix) / "Lib/site-packages").resolve())',
        '    dependency_root = (str(_canonical.dependency_root) if _canonical is not None else\n'
        '        str((Path(sys.prefix) / "Lib/site-packages").resolve()))')
    patch(queue,'    child_env["XAR_STATIONARY_HOLD_AB_SPEED"] = hold_ab_speed',
        '    child_env["XAR_STATIONARY_HOLD_AB_SPEED"] = hold_ab_speed\n'
        '    if _canonical is not None:\n        child_env = _canonical.child_env(child_env)')
    old='''                async with retain_mcp_stdio_process(stdio, expected_executable=base_executable) as captured:
                    async with stdio.stdio_client(StdioServerParameters(command=argv[0], args=argv[1:], cwd=str(N), env=child_env), errlog=err) as streams:
                        application = captured.require_generation()'''
    new=f'''                from {helper} import owned_stdio
                async with owned_stdio(_canonical, stdio,
                        StdioServerParameters(command=argv[0], args=argv[1:], cwd=str(N), env=child_env),
                        errlog=err, capture_factory=retain_mcp_stdio_process) as (streams, application):
                    if True:  # Preserve the original inner suite and all original MCP/Queue statements.'''
    patch(queue,old,new)
    patch(queue,'    raise SystemExit(asyncio.run(main(args)))',
        '    try:\n        raise SystemExit(asyncio.run(main(args)))\n'
        '    finally:\n        if _canonical is not None:\n            _canonical.close()')
    patch(app,'from root_p37c17_compact_decision_feed import publish_before_submit',
        'from root_p37c17_compact_decision_feed import publish_before_submit\n'
        f'from {helper} import receive_entry\n'
        f'_canonical = receive_entry(N, "MCPApp", sys.argv, enabled={state})')
    patch(app,'    service=bound_services[0]',
        '    service=bound_services[0]\n    if _canonical is not None:\n        _canonical.install_service(service)')
    patch(app,'mcp_server.main()','try:\n    mcp_server.main()\nfinally:\n'
        '    if _canonical is not None:\n        _canonical.close()')
    if enabled:
        factory='root_p37c17_cold_resume.py'
        patch(factory,"freeze['native_build_label'] == 'Native29 minimized camera and bounded native diagnostics'",
            "freeze['native_build_label'] == "+repr(native_build_label))
    for name,changes in records.items():
        inverse=out[name]
        for old,new in reversed(changes):
            if inverse.count(new)!=1:raise ValueError('ambiguous inverse creator seam')
            inverse=inverse.replace(new,old,1)
        if inverse!=ported[name]:raise ValueError('unreviewed change outside creator seams')
    for name,source in out.items():compile(source,name,'exec')
    out['root_c17_canonical_outer.py']=(OWN/'canonical_c17_outer_binding_v1.py').read_text(encoding='utf-8')
    out['root_c17_normal_checkpoint_inputs.py']=(OWN/'c17_normal_checkpoint_inputs_v1.py').read_text(encoding='utf-8')
    result={name:source.encode() for name,source in out.items()}
    return result,records
