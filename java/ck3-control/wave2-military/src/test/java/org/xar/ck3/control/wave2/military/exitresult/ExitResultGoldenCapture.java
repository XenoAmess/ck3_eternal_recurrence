package org.xar.ck3.control.wave2.military.exitresult;

import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/** Explicit original-producer capture, scheduled by the shared bounded execution owner only. */
public final class ExitResultGoldenCapture {
    private ExitResultGoldenCapture() { }
    public static void main(String[] args) throws Exception {
        if (args.length != 3) { throw new IllegalArgumentException("repository root, existing Python and new capture output required"); }
        Path root = Path.of(args[0]).toAbsolutePath().normalize();
        Path python = Path.of(args[1]).toAbsolutePath().normalize();
        Process identity = new ProcessBuilder(python.toString(), root.resolve("tools/ck3_live_run_id.py").toString(), "machine")
                .directory(root.toFile()).redirectErrorStream(true).start();
        if (!identity.waitFor(15, TimeUnit.SECONDS)) {
            identity.destroyForcibly();
            throw new IllegalStateException("machine identity timed out");
        }
        String machineId = new String(identity.getInputStream().readNBytes(1024), StandardCharsets.UTF_8).trim();
        if (identity.exitValue() != 0 || !machineId.matches("[A-Za-z0-9-]{1,128}")) { throw new IllegalStateException("actual machine required"); }
        String script = """
                import sys,json,hashlib,datetime,copy,unittest,io
                from pathlib import Path
                root=Path(sys.argv[1])
                sys.path.insert(0,str(root/'ck3_autonomous_player/tests'))
                import test_ordinary_war_exit_observation_v1 as t
                stream=io.StringIO()
                original=unittest.TextTestRunner(stream=stream).run(unittest.defaultTestLoader.loadTestsFromModule(t))
                if not original.wasSuccessful():
                    raise RuntimeError(stream.getvalue())
                post=t.snapshot(after=True)
                base={'before_snapshot':t.snapshot(),'post_snapshot':post,'action_result':{'step':'surrender-war-77','accepted':True,'status':'submitted','war_termination_result':{'outcome':'attacker_defeat','status':'applied'}},'claims_result':t.claims(post),'title_holder_results':[t.holder(post)],'truce_result':t.truce(post)}
                cases=[]
                def change(path,value):
                    return {'path':path,'value':value}
                def add(name,patches):
                    actual=copy.deepcopy(base)
                    for patch in patches:
                        owner=actual
                        for part in patch['path'][:-1]:
                            owner=owner[part]
                        owner[patch['path'][-1]]=copy.deepcopy(patch['value'])
                    cases.append({'name':name,'patches':patches,'expected':t.LEAF.compose_ordinary_war_exit_observation_v1(**actual)})
                add('all-existing-typed-materials',[])
                add('no-optional-observations',[change(['claims_result'],None),change(['title_holder_results'],None),change(['truce_result'],None)])
                add('war-still-present',[change(['post_snapshot','active_wars'],t.snapshot(after=True,active=True)['active_wars'])])
                add('crossed-connection',[change(['post_snapshot','diagnostics','connection_generation'],4)])
                add('defender-surrender-polarity',[change(['before_snapshot','active_wars',0,'player_side'],'defender')])
                add('white-peace-is-only-requested',[change(['action_result','step'],'offer-white-peace-77')])
                add('enforce-demands-is-only-requested',[change(['action_result','step'],'enforce-demands-77')])
                add('claims-actor-mismatch',[change(['claims_result','player_claims','actor_character_id'],30000)])
                add('title-query-frame-mismatch',[change(['title_holder_results',0,'queried_revision'],8)])
                add('truce-owner-mismatch',[change(['truce_result','raiktor_actual_truce_expiry','owner_character_id'],52)])
                add('observed-no-truce',[change(['truce_result'],t.truce(post,absent=True))])
                add('unknown-piety-is-not-zero',[change(['post_snapshot','played_character_piety'],None)])
                add('empty-targets',[change(['before_snapshot','active_wars',0,'targeted_title_ids'],[]),change(['claims_result'],None),change(['title_holder_results'],[]),change(['truce_result'],None)])
                add('non-terminal-action',[change(['action_result','step'],'life-advance-day')])
                add('leading-zero-war-id',[change(['action_result','step'],'surrender-war-077')])
                add('signed-int64-difference-widens',[change(['before_snapshot','played_character_gold','raw'],-2**63),change(['post_snapshot','played_character_gold','raw'],2**63-1)])
                add('ack-false-does-not-erase-observed-absence',[change(['action_result','accepted'],False)])
                add('historical-build-rejected',[change(['post_snapshot','diagnostics','hello','game_version'],'1.19.0.6')])
                source=t.SOURCE
                paths=[source/'ordinary_war_exit_observation_v1.py',source/'bridge/player_claims_contract.py',source/'bridge/title_holder_contract.py',source/'bridge/player_truce_expiry_contract.py',source/'bridge/native_driver.py',source/'native_auto_run.py',Path(t.__file__)]
                metadata={'schema':'xar.ck3.java.exitresult.golden.v1','machine_id':sys.argv[2],'captured_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'capture':'actual unchanged composer and three native normalizers; synthetic offline fixture, no current-game result identity','original_unit_tests':original.testsRun,'original_failures':len(original.failures),'original_errors':len(original.errors),'sources':[{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths],'base_input':base,'cases':cases}
                main_path=Path(sys.argv[3])
                out=main_path.parent
                large_path=out/(main_path.name+'.large-targets.json')
                out.mkdir(parents=True,exist_ok=True)
                main_raw=(json.dumps(metadata,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode('utf-8')
                if len(main_raw)>65536:
                    raise RuntimeError('main golden exceeds explicit byte budget')
                large=copy.deepcopy(base)
                large['before_snapshot']['active_wars'][0]['targeted_title_ids']=list(range(4096))
                large.update(claims_result=None,title_holder_results=None,truce_result=None)
                boundary={'schema':'xar.ck3.java.exitresult.large-targets.golden.v1','machine_id':sys.argv[2],'captured_at_utc':metadata['captured_at_utc'],'main_golden_sha256':hashlib.sha256(main_raw).hexdigest(),'input':large,'expected':t.LEAF.compose_ordinary_war_exit_observation_v1(**large)}
                raw=(json.dumps(boundary,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode('utf-8')
                if len(raw)>65536:
                    raise RuntimeError('large-target golden exceeds explicit byte budget')
                module=root/'java/ck3-control/wave2-military'
                owned=list((module/'src/main/java/org/xar/ck3/control/wave2/military/exitresult').glob('*.java'))+list((module/'src/test/java/org/xar/ck3/control/wave2/military/exitresult').glob('*.java'))+[module/'MIGRATION-exitresult.md']
                lane_bytes=len(main_raw)+len(raw)+sum(p.stat().st_size for p in owned)
                if lane_bytes>160*1024:
                    raise RuntimeError('actual complete lane exceeds 160KiB before golden write: '+str(lane_bytes))
                if main_path.exists() or large_path.exists():
                    raise RuntimeError('capture refuses to replace an existing golden')
                with main_path.open('xb') as stream:
                    stream.write(main_raw)
                with large_path.open('xb') as stream:
                    stream.write(raw)
                print(json.dumps({'path':str(main_path),'bytes':len(main_raw),'sha256':hashlib.sha256(main_raw).hexdigest(),'cases':len(cases),'original_tests':original.testsRun}))
                print(json.dumps({'path':str(large_path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'cases':1,'lane_bytes':lane_bytes}))
                """;
        Process process = new ProcessBuilder(python.toString(), "-c", script, root.toString(), machineId,
                Path.of(args[2]).toAbsolutePath().normalize().toString())
                .directory(root.toFile()).redirectErrorStream(true).start();
        if (!process.waitFor(90, TimeUnit.SECONDS)) {
            process.destroyForcibly();
            process.waitFor(5, TimeUnit.SECONDS);
            throw new IllegalStateException("original producer timed out");
        }
        byte[] output = process.getInputStream().readNBytes(8193);
        if (output.length > 8192) { throw new IllegalStateException("capture output exceeds limit"); }
        System.out.print(new String(output, StandardCharsets.UTF_8));
        if (process.exitValue() != 0) { throw new IllegalStateException("original producer exited " + process.exitValue()); }
    }
}
