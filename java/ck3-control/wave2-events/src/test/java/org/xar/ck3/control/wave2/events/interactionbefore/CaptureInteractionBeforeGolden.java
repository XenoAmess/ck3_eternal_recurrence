package org.xar.ck3.control.wave2.events.interactionbefore;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/** Optional once-only original before producer capture; no default test or production Python dependency. */
public final class CaptureInteractionBeforeGolden {
    private CaptureInteractionBeforeGolden() { }
    public static void main(String[] args) throws Exception {
        if (args.length == 5) { sourceHost(args); return; }
        if (args.length != 4) { throw new IllegalArgumentException("repo-root python-exe new-scratch-root new-output required"); }
        Path repo = Path.of(args[0]).toAbsolutePath().normalize(); Path python = Path.of(args[1]).toAbsolutePath().normalize();
        Path scratch = Path.of(args[2]).toAbsolutePath().normalize(); Path output = Path.of(args[3]).toAbsolutePath().normalize();
        Path temporary = Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize();
        if (!scratch.startsWith(temporary) || Files.exists(scratch) || !output.startsWith(temporary.getParent().resolve("logs")) || Files.exists(output)) { throw new IllegalArgumentException("fresh package paths required"); }
        Files.createDirectories(scratch); ProcessBuilder builder = new ProcessBuilder(python.toString(), "-c", SCRIPT, repo.toString(), scratch.toString(), output.toString());
        builder.directory(repo.toFile()); builder.inheritIO(); builder.environment().put("TEMP", temporary.toString()); builder.environment().put("TMP", temporary.toString());
        Process process = builder.start();
        if (!process.waitFor(90, TimeUnit.SECONDS)) { process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly(); throw new IllegalStateException("before capture timeout"); }
        if (process.exitValue() != 0 || !Files.isRegularFile(output) || Files.size(output) > 98_304) { throw new IllegalStateException("original before capture failed"); }
    }
    private static void sourceHost(String[] args) throws Exception {
        Path repo = Path.of(args[0]).toAbsolutePath().normalize(), python = Path.of(args[1]).toAbsolutePath().normalize();
        Path output = Path.of(args[2]).toAbsolutePath().normalize(), game = Path.of(args[3]).toAbsolutePath().normalize();
        Path proof = Path.of(args[4]).toAbsolutePath().normalize();
        Path temporary = Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize();
        if (!Files.isDirectory(repo) || !Files.isRegularFile(python) || !Files.isDirectory(game) || !Files.isRegularFile(proof)
                || Files.size(proof) > 16_384 || Files.exists(output) || !output.getParent().equals(temporary.getParent().resolve("logs"))) {
            throw new IllegalArgumentException("fixed actual stock input and fresh package output required");
        }
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-", repo.toString(), game.toString(), proof.toString())
                .directory(repo.toFile()).redirectError(ProcessBuilder.Redirect.INHERIT);
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTHONPATH", repo.resolve("ck3_autonomous_player/src").toString());
        builder.environment().put("TEMP", temporary.toString()); builder.environment().put("TMP", temporary.toString());
        Process process = builder.start();
        java.util.concurrent.FutureTask<byte[]> reading = new java.util.concurrent.FutureTask<>(() -> process.getInputStream().readNBytes(65_537));
        Thread.startVirtualThread(reading);
        try {
            try (var input = process.getOutputStream()) { input.write(SOURCE_HOST.getBytes(java.nio.charset.StandardCharsets.UTF_8)); }
            if (!process.waitFor(90, TimeUnit.SECONDS)) { throw new IllegalStateException("interaction source host capture timeout"); }
            byte[] data = reading.get(5, TimeUnit.SECONDS);
            if (process.exitValue() != 0 || data.length == 0 || data.length > 65_536) { throw new IllegalStateException("interaction source host producer rejected"); }
            Files.write(output, data, java.nio.file.StandardOpenOption.CREATE_NEW);
            System.out.println("captured original interaction source host: " + data.length + " bytes");
        } finally { if (process.isAlive()) { process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly(); } reading.cancel(true); }
    }
    private static final String SOURCE_HOST = """
            from pathlib import Path
            import base64,copy,datetime,gzip,hashlib,inspect,json,sys,tempfile
            root,game,proof=map(lambda value:Path(value).resolve(),sys.argv[1:])
            sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'));sys.path.insert(0,str(root/'tools'))
            from test_pending_interaction_left_fallback import fixture,ACTIONS,reply
            from xar_autoplayer import pending_interaction_fallback as original
            from xar_autoplayer import interaction_offline_analysis as offline
            from xar_autoplayer import pending_interaction_source_registry as registry
            from ck3_live_run_id import current_machine_id
            sha=lambda raw:hashlib.sha256(raw).hexdigest()
            canonical=lambda value:json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
            machine=current_machine_id(); proof_raw=proof.read_bytes()
            history=Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime/state/profile/xar-autoplayer-environment.json')
            history_raw=history.read_bytes();assert len(history_raw)==9363 and sha(history_raw)=='b21938a142d4b8b21c1befe99fc7399c18091f08457e8e0192d398203061ad46'
            historical=json.loads(history_raw);assert historical['machine_id']==machine and historical['game']['raw_version']=='1.20.0.4'
            assert sha(proof_raw)=='716a08c7af82ee3cd0cf5c8d5f388609dc62dd6281d9b618c3b96ec5270a7165','stock proof source changed'
            stock=json.loads(proof_raw)
            assert stock['schema']=='xar.events-interaction-stock-inputs/v1' and stock['machine_id']==machine
            assert Path(stock['game_root']).resolve()==game and stock['all_expected_anchors_match'] is True
            expected={original.GUI_LEFT_REPLY['source']:original.GUI_LEFT_REPLY['sha256']}
            rule=original.PENDING_INTERACTION_REPLY_REGISTRY_V1['request_clerical_chastity_interaction']
            expected[rule['source']]=rule['source_sha256'];assert len(stock['files'])==2
            files=[];identities={}
            identity=lambda value:(str(value.st_dev),str(value.st_ino),value.st_size,str(value.st_mtime_ns))
            for row in stock['files']:
                relative=row['relative_path'];assert relative in expected and '..' not in Path(relative).parts
                path=(game/relative).resolve();assert path.is_relative_to(game) and path==Path(row['path']).resolve()
                before=path.stat();assert 0<before.st_size<=2097152
                raw=path.read_bytes();after=path.stat()
                assert identity(before)==identity(after) and len(raw)==before.st_size and sha(raw)==row['sha256']==row['expected_sha256']==expected.pop(relative)
                assert row['expected_anchor_matches'] is True
                assert (str(before.st_dev),str(before.st_ino),str(before.st_mtime_ns))==(row['device_decimal'],row['file_id_decimal'],row['last_write_ns_decimal'])
                identities[path]=identity(after)
                files.append({'relative':relative,'bytes':len(raw),'sha256':sha(raw),'gzip_base64':base64.b64encode(gzip.compress(raw,mtime=0)).decode('ascii')})
            assert not expected
            names=['known','unknown','disabled','unsupported','acknowledge','missing-definition','false-notification','stale-native','wrong-pending','signed-pending','null-context','null-snapshot']
            cases=[];base=inspect.unwrap(fixture)();reviewed=None
            with tempfile.TemporaryDirectory(prefix='interaction-source-host-') as temporary:
                scratch=Path(temporary)
                for name in names:
                    snapshot,context,_=copy.deepcopy(base);actions=set(ACTIONS)
                    if name=='known':context['build']={'version':historical['game']['raw_version'],'exe_sha256':historical['game']['executable_sha256']}
                    elif name=='unknown':context['definition'].update(canonical_key='synthetic_unknown_interaction',deterministic_key_hash=12)
                    elif name=='disabled':context['legality']['reject']={'status':'available','allowed':False,'reason':'synthetic_disabled'}
                    elif name=='unsupported':actions.discard('reject-pending-character-interaction')
                    elif name=='acknowledge':
                        snapshot['pending_character_interaction']['auto_accept_notification']=True
                        context['legality']['acknowledge']={'status':'available','allowed':True,'reason':None};actions.add('acknowledge-pending-character-interaction')
                    elif name=='missing-definition':context.pop('definition')
                    elif name=='false-notification':snapshot['pending_character_interaction']['auto_accept_notification']=None
                    elif name=='stale-native':snapshot['native_revision']+=1
                    elif name=='wrong-pending':context['pending_interaction_id']+=1
                    elif name=='signed-pending':
                        snapshot['pending_character_interaction']['instance_id']=-2147483648;context['pending_interaction_id']=-2147483648
                    elif name=='null-context':context=None
                    elif name=='null-snapshot':snapshot=None
                    previous={'phase':'pending_synthetic','opaque_float_hint':1.0,'opaque_empty':[],'opaque_null':None}
                    request={'schema':'xar.pending-interaction-left-plan-input/v1','snapshot':snapshot,'context':context,'original_plan':previous,'action_steps':sorted(actions),'registry_requested':False}
                    plan=original.plan_pending_interaction_left_reply_v1(snapshot=snapshot,context=context,original_plan=previous,action_steps=actions)
                    planned={'snapshot_id':None if snapshot is None else snapshot['snapshot_id'],'revision':None if snapshot is None else snapshot['revision'],'plan':plan}
                    planned_raw=canonical(planned);ticket=original.capture_pending_interaction_before_v1(scratch/name,planned)
                    before=None if ticket is None else json.loads(Path(ticket['before']['path']).read_bytes())
                    cases.append({'name':name,'request':request,'expected_plan':plan,'planned_utf8':planned_raw.decode('utf-8'),'planned_sha256':sha(planned_raw),'before':before})
                    if name=='known':
                        original.capture_pending_interaction_after_v1(ticket,outcome={'result':reply((snapshot,context,[]))})
                        incidents=original.collect_completed_interaction_incidents_v1(scratch/name);assert len(incidents)==1
                        batch={'completed_control_sequence':1,'new_incidents':incidents};manifest=scratch/'completed-batch.json';manifest.write_bytes(canonical(batch))
                        state=scratch/'review-state';report=offline.analyze_batch(manifest,game,scratch/'review',publish_state_dir=state)
                        assert len(report['entries'])==1 and not report['unresolved']
                        entry,audit=registry.load_source_reviewed_interaction_v1(state,context,original.GUI_LEFT_REPLY)
                        assert entry is not None and audit['status']=='offline-source-reviewed'
                        entry_raw=Path(audit['entry_path']).read_bytes();facts_raw=Path(entry['source_facts']['path']).read_bytes()
                        reviewed={'lookup':{'schema':'xar.interaction-registry-lookup/v1','build':context['build'],'definition':{key:context['definition'][key] for key in ('canonical_key','deterministic_key_hash')},'gui_sha256':original.GUI_LEFT_REPLY['sha256']},'entry_utf8':entry_raw.decode('utf-8'),'entry_sha256':sha(entry_raw),'facts_utf8':facts_raw.decode('utf-8'),'facts_sha256':sha(facts_raw),'expected_reviewed':entry,'expected_audit':audit,'original_report':report}
                assert sum(p.stat().st_size for p in scratch.rglob('*') if p.is_file())<=262144
            for path,previous in identities.items():
                assert identity(path.stat())==previous and sha(path.read_bytes())==next(row['sha256'] for row in files if (game/row['relative']).resolve()==path)
            sources=[]
            for path in sorted({Path(module.__file__).resolve() for module in list(sys.modules.values()) if getattr(module,'__file__',None) and str(getattr(module,'__file__')).endswith('.py') and Path(module.__file__).resolve().is_relative_to(root)}):
                raw=path.read_bytes();sources.append({'path':str(path),'bytes':len(raw),'sha256':sha(raw)})
            value={'schema':'xar.interaction-source-host-golden/v1','machine_id':machine,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stock_proof':{'path':str(proof),'bytes':len(proof_raw),'sha256':sha(proof_raw)},'historical_build_ref':{'path':str(history),'bytes':len(history_raw),'sha256':sha(history_raw),'prepared_at':historical['prepared_at'],'current_runtime_qualified':False},'files':files,'sources':sources,'cases':cases,'registry':reviewed,'scope':'Original planner/before plus original offline analyzer and registry on synthetic native frames; known frame uses explicitly historical build identity, never current native qualification. Actual unchanged stock GUI/source. No native, Game, dispatcher or canonical ledger calls.','Game_MCP_OBS_calls':0,'timeline_writer_calls':0}
            raw=canonical(value);assert len(raw)<=1048576 and len(cases)==12
            compressed=gzip.compress(raw,mtime=0);assert len(compressed)<=65536
            sys.stdout.buffer.write(compressed)
            """;
    private static final String SCRIPT = """
            from pathlib import Path
            import sys,json,copy,hashlib,datetime
            root,scratch,out=map(Path,sys.argv[1:]);sys.path[:0]=[str(root/'ck3_autonomous_player/src'),str(root/'ck3_autonomous_player/tests/unit'),str(root/'tools')]
            from test_pending_interaction_left_fallback import fixture,ACTIONS
            from xar_autoplayer import pending_interaction_fallback as original
            from ck3_live_run_id import current_machine_id
            canonical=lambda value:json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
            sha=lambda raw:hashlib.sha256(raw).hexdigest();cases=[];base=fixture.__wrapped__()
            for name in ['known','unknown','disabled','unsupported','acknowledge','wrong_snapshot','wrong_revision','wrong_step','false_legality']:
                snapshot,context,_=copy.deepcopy(base);actions=set(ACTIONS)
                if name=='unknown':context['definition'].update(canonical_key='synthetic_unknown_interaction',deterministic_key_hash=12)
                if name=='disabled':context['legality']['reject']={'status':'available','allowed':False,'reason':'synthetic_disabled'}
                if name=='unsupported':actions.discard('reject-pending-character-interaction')
                if name=='acknowledge':
                    snapshot['pending_character_interaction']['auto_accept_notification']=True;context['legality']['acknowledge']={'status':'available','allowed':True,'reason':None};actions.add('acknowledge-pending-character-interaction')
                original_plan={'phase':'pending_synthetic','opaque_float_hint':1.0,'opaque_empty':[],'opaque_null':None}
                plan=original.plan_pending_interaction_left_reply_v1(snapshot=snapshot,context=context,original_plan=original_plan,action_steps=actions)
                planned={'snapshot_id':snapshot['snapshot_id'],'revision':snapshot['revision'],'plan':plan}
                if name=='wrong_snapshot':planned['snapshot_id']='synthetic:wrong'
                elif name=='wrong_revision':planned['revision']+=1
                elif name=='wrong_step':plan['selected_step']='accept-pending-character-interaction'
                elif name=='false_legality':plan['unhandled_interaction_fallback']['selection']['native_legal']=False
                try:
                    ticket=original.capture_pending_interaction_before_v1(scratch/name,planned)
                    before=json.loads(Path(ticket['before']['path']).read_bytes())
                    retained={key:value for key,value in before.items() if key not in ('incident_id','stage','captured_at_utc','dispatch_attempted')}
                    assert canonical(retained)==canonical(plan['unhandled_interaction_fallback'])
                    result={'status':'prepared','incident_id':ticket['incident_id'],'captured_at_utc':before['captured_at_utc'],'legacy_capture_body_sha256':sha(canonical(retained)),'actual_before_ref':ticket['before']}
                except ValueError as error:result={'status':'rejected','error_type':type(error).__name__,'error_message':str(error)}
                cases.append({'name':name,'planned_utf8':canonical(planned).decode('utf-8'),'planned_sha256':sha(canonical(planned)),'result':result})
            source=root/'ck3_autonomous_player/src/xar_autoplayer/pending_interaction_fallback.py'
            data={'schema':'xar.interaction-before-original-producer-golden/v1','machine_id':current_machine_id(),'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'producer_sha256':sha(source.read_bytes()),'gui_source':original.GUI_LEFT_REPLY['source'],'gui_sha256':original.GUI_LEFT_REPLY['sha256'],'notice':'Actual original planner and before capture on synthetic native frames. Captured body equals original source capture by exact Python canonical JSON before metadata. No native, dispatcher, Game or canonical ledger calls.','cases':cases}
            raw=canonical(data);assert len(raw)<=98304;assert sum(p.stat().st_size for p in scratch.rglob('*') if p.is_file())<=262144
            with out.open('xb') as stream:stream.write(raw)
            print(json.dumps({'machine_id':data['machine_id'],'output':str(out),'bytes':len(raw),'sha256':sha(raw),'cases':len(cases),'Game_MCP_ledger_calls':0}))
            """;
}
