package org.xar.ck3.control.wave2.governance.succession;

/** Test-oracle source for the existing shared capture controller; starts no process. */
public final class M3ResidentUiCaptureProgram {
    private M3ResidentUiCaptureProgram() { }
    public static String pythonProgram() { return PROGRAM; }
    public static void main(String[] args) throws java.io.IOException {
        if (args.length != 1) throw new IllegalArgumentException("owned create-new capture-program output required");
        java.nio.file.Path output = java.nio.file.Path.of(args[0]).toAbsolutePath().normalize();
        output.getParent().toRealPath();
        java.nio.file.Files.writeString(output, PROGRAM, java.nio.charset.StandardCharsets.UTF_8, java.nio.file.StandardOpenOption.CREATE_NEW);
    }
    private static final String PROGRAM = """
        import copy,datetime,hashlib,io,json,os,subprocess,sys,tempfile,unittest
        from pathlib import Path
        root=Path(sys.argv[1]).resolve(strict=True)
        scratch=Path(sys.argv[2]).resolve(strict=True)
        if not scratch.is_dir():raise RuntimeError('existing admitted capture scratch required')
        tempfile.tempdir=str(scratch)
        os.environ.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
        packages=('ck3_autonomous_player/src','tools/g2_saved_campaign','ck3_autonomous_player/tests/unit','ck3_autonomous_player/mod_bridge/tools')
        paths={p.resolve() for package in packages for p in (root/package).rglob('*.py')}
        paths.add((root/'tools/ck3_live_run_id.py').resolve(strict=True))
        paths.add((root/'tools/gen_ck3_live_run_identity_package.py').resolve(strict=True))
        def refs():
            out=[]
            for path in sorted(paths):
                raw=path.read_bytes();out.append({'path':path.relative_to(root).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
            return out
        before=refs()
        sys.path[:0]=[str(root/'ck3_autonomous_player/tests/unit'),str(root/'ck3_autonomous_player/src'),str(root)]
        import test_successor_ui_app_owner_v1 as original
        queue=original.queue_module
        active=[];captured=[];keys=set()
        saved_call=original.RegisteredQueue.call
        saved_resume=queue.resume_successor_ui
        def call(self,name,arguments,kind):
            payload,path=saved_call(self,name,arguments,kind)
            if active:
                if kind=='m7-successor-ui-resume':active[-1]['app_response']=copy.deepcopy(payload)
                if kind=='m7-successor-ui-independent-post':active[-1]['independent_snapshot']=copy.deepcopy(payload)
            return payload,path
        def resume(actual,current,transition):
            row={'schema':'xar.java-successor-ui-queue/v1','operation':'consume_resume','transition':copy.deepcopy(transition)}
            active.append(row)
            try:outcome=saved_resume(actual,current,transition)
            finally:active.pop()
            if 'app_response' in row and 'independent_snapshot' in row:
                key=(row['app_response']['status'],bool((row['app_response'].get('cold_resume_binding') or {}).get('connection_rebound')))
                if key not in keys:
                    keys.add(key);captured.append(row)
            return outcome
        original.RegisteredQueue.call=call
        queue.resume_successor_ui=resume
        try:
            suite=unittest.defaultTestLoader.loadTestsFromTestCase(original.AppOwnerTests)
            log=io.StringIO();result=unittest.TextTestRunner(stream=log,verbosity=1).run(suite)
            if not result.wasSuccessful():raise RuntimeError('original App suite failed: '+log.getvalue()[-12000:])
        finally:
            original.RegisteredQueue.call=saved_call
            queue.resume_successor_ui=saved_resume
        if not captured:raise RuntimeError('original registered MCP/App/Queue produced no resident input')
        def expected(row):
            app=row['app_response'];post=row['independent_snapshot'];diagnostics=post['diagnostics']
            return {'schema':'xar.java-successor-ui-queue-result/v1','status':app['status'],'pending':app['pending'],
                'player_decision_pending':queue._player_decision_pending(post),'unavailable_reason':None,
                'frame':{**{k:post[k] for k in ('snapshot_id','revision','native_revision','date_raw','episode_run_id')},
                    **{k:diagnostics[k] for k in ('bridge_pid','connection_generation')},'successor_character_id':post['episode_character_id']},
                'submission_authorized':False,'action_replay_authorized':False,'queries_performed':0,
                'ordinary_cycle_credit':0,'new_natural_succession_credit':0,'original_app_queue_verification_required':True}
        cases=[];cold=[]
        for index,row in enumerate(captured):
            entry={'name':'registered_app_'+row['app_response']['status']+'_'+str(index),'request':row}
            if (row['app_response'].get('cold_resume_binding') or {}).get('connection_rebound') is True:cold.append(entry)
            else:entry['expected']=expected(row);cases.append(entry)
        if not {'deferred_player_decision','close_required','clear'}<={entry['expected']['status'] for entry in cases}:
            raise RuntimeError('complete original deferred/typed-Close/clear sequence required; captured='+repr(keys))
        base=next(entry['request'] for entry in cases if entry['expected']['status']=='deferred_player_decision')
        rejected=[]
        class ReplayQueue:
            def __init__(self,row):self.row=row;self.actions=0
            def call(self,name,arguments,kind):
                if name=='ck3_resume_successor_ui_v1':return copy.deepcopy(self.row['app_response']),Path('synthetic-original-resume.json')
                if name=='ck3_take_snapshot':return copy.deepcopy(self.row['independent_snapshot']),Path('synthetic-independent-post.json')
                self.actions+=1;raise RuntimeError('negative fixture attempted an action')
        def negative(name,change):
            row=copy.deepcopy(base);change(row);replay=ReplayQueue(row)
            try:saved_resume(replay,copy.deepcopy(row['independent_snapshot']),copy.deepcopy(row['transition']))
            except ValueError as error:rejected.append({'name':name,'request':row,'error_type':type(error).__name__,'error_message':str(error)})
            else:raise RuntimeError('original Queue unexpectedly accepted '+name)
            if replay.actions:raise RuntimeError('negative fixture submitted an action')
        negative('independent_frame_drift',lambda row:row['independent_snapshot'].update(native_revision=row['independent_snapshot']['native_revision']+1))
        negative('original_handoff_changed',lambda row:row['app_response']['transition'].update(successor_character_id=999991))
        negative('queue_episode_drift',lambda row:row['independent_snapshot'].update(episode_run_id='synthetic-foreign-episode'))
        negative('queue_process_drift',lambda row:row['independent_snapshot']['diagnostics'].update(bridge_pid=999991))
        negative('queue_goal_drift',lambda row:row['independent_snapshot']['campaign_goal'].update(campaign_id='synthetic-foreign-campaign'))
        negative('missing_pending',lambda row:row['app_response'].pop('pending'))
        dependencies=(root/'tools/.venv').resolve()
        imported={Path(m.__file__).resolve() for m in list(sys.modules.values()) if getattr(m,'__file__',None)
            and str(m.__file__).endswith('.py') and Path(m.__file__).resolve().is_relative_to(root)
            and not Path(m.__file__).resolve().is_relative_to(dependencies)}
        if not imported<=paths:raise RuntimeError('repository imports absent from pre-import pins: '+repr(sorted(str(p) for p in imported-paths)))
        if refs()!=before:raise RuntimeError('original source pre/post changed')
        machine=subprocess.run([sys.executable,str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True).stdout.strip()
        output=json.dumps({'schema':'xar.g2.m3.original-resident-ui-golden/v1','machine_id':machine,
            'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),
            'synthetic_fixture':True,'source_refs':before,'source_refs_unchanged':True,'actual_repository_import_count':len(imported),
            'original_suite':{'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped)},
            'cases':cases,'cold_owner_required_cases':cold,'rejected':rejected,
            'scope':'Actual unchanged registered MCP/App/Service/Queue software tests. Synthetic driver and OS identity only. Original Continue/Close/SAVE assertions retained. No real Game, native pipe, campaign Driver/SAVE body or writer authority.'},
            ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')
        if len(output)>2097152:raise RuntimeError('resident capture exceeds admitted2MiB output estimate')
        sys.stdout.buffer.write(output+b'\\n')
        """;
}
