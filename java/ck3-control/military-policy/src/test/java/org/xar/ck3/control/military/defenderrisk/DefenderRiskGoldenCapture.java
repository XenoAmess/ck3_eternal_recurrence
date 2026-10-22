package org.xar.ck3.control.military.defenderrisk;

import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/** Explicit one-time capture utility. Normal Java tests only read the committed golden. */
public final class DefenderRiskGoldenCapture {
    private DefenderRiskGoldenCapture() { }

    public static void main(String[] args) throws Exception {
        if (args.length != 2) { throw new IllegalArgumentException("repository root and existing Python executable required"); }
        Path root = Path.of(args[0]).toAbsolutePath().normalize();
        Path python = Path.of(args[1]).toAbsolutePath().normalize();
        Process identity = new ProcessBuilder(python.toString(), root.resolve("tools/ck3_live_run_id.py").toString(), "machine")
                .directory(root.toFile()).redirectErrorStream(true).start();
        if (!identity.waitFor(15, TimeUnit.SECONDS)) {
            identity.destroyForcibly();
            throw new IllegalStateException("machine identity probe timed out");
        }
        String machineId = new String(identity.getInputStream().readNBytes(1024), StandardCharsets.UTF_8).trim();
        if (identity.exitValue() != 0 || !machineId.matches("[A-Za-z0-9-]{1,128}")) {
            throw new IllegalStateException("actual machine identity required");
        }
        String script = """
                import sys,json,hashlib,datetime
                from pathlib import Path
                root=Path(sys.argv[1])
                sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'))
                import test_formal_defender_continue_risk_v1 as t
                observe=t.observe_defender_continue_risk_v1
                frame,contact=t._r0271_inputs()
                h=json.loads(t.H2743.read_text(encoding='utf-8'))
                o=h['frame']
                hf={'snapshot_id':o['snapshot_id_before_and_after'],'revision':o['queried_public_revision'],'native_revision':o['queried_native_revision'],'date_raw':o['date_raw'],'episode_run_id':o['episode_run_id'],'connection_generation':o['queried_connection_generation'],'played_character_id':o['actor_character_id'],'war_id':o['war_id'],'player_relative_war_score':o['player_relative_war_score']}
                hs={'source_frame':hf,'source_sha256':h['source']['read_only_result_sha256'],'province_id':2628,'besieging_army_ids':[50331920],'remaining_days_estimate':1}
                cases=[]
                def add(name,f,c=None,s=None):
                    cases.append({'name':name,'request':{'frame':f,'contact':c,'siege':s},'expected':observe(frame=f,contact=c,siege=s)})
                add('r0271-contact',frame,contact)
                add('h2743-siege',hf,None,hs)
                add('no-observations',frame)
                add('same-province-combined',frame,contact,dict(hs,source_frame=frame,source_sha256=contact['source_sha256'],province_id=contact['target_province_id']))
                add('contact-conflict-is-not-a-loss-bound',frame,dict(contact,conflicts=[{'proof':'unknown','weight':0.5}]))
                add('short-horizon-no-full-day',frame,dict(contact,horizon_end_date_raw=frame['date_raw']+23))
                add('false-contact-free',frame,dict(contact,one_day_contact_free=False))
                add('no-offsite-roster',frame,dict(contact,offsite_target_arrivals=[]))
                add('later-offsite-under-current-orders',frame,dict(contact,offsite_target_arrivals=[{'army_id':99,'arrival_date_raw':contact['subject_target_arrival_date_raw']+1}]))
                add('first-waypoint-at-horizon',frame,dict(contact,first_waypoint_arrival_date_raw=contact['horizon_end_date_raw']))
                add('missing-route-estimates-are-null',frame,dict(contact,first_waypoint_arrival_date_raw=None,subject_target_arrival_date_raw=None))
                add('zero-siege-days-remains-estimate',hf,None,dict(hs,remaining_days_estimate=0))
                add('max-siege-days',hf,None,dict(hs,remaining_days_estimate=(2**31-1)//24))
                big=dict(frame,date_raw=2**100,revision=2**90,native_revision=2**95,war_id=2**80,player_relative_war_score=-(2**75))
                add('arbitrary-python-integer-domain',big,None,dict(hs,source_frame=big))
                paths=[root/'ck3_autonomous_player/src/xar_autoplayer/formal_defender_continue_risk_v1.py',Path(t.__file__),t.R0271,t.H2743,root/'ck3_autonomous_player/native_bridge/research/project_h2743_attempt11_continue_risk.py']
                result={'schema':'xar.ck3.java.defenderrisk.golden.v1','machine_id':sys.argv[2],'captured_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'capture':'actual unmodified Python producer; no game/RPC/ledger access','sources':[{'path':p.relative_to(root).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in paths],'cases':cases}
                out=root/'java/ck3-control/military-policy/src/test/resources/defenderrisk/producer-golden-v1.json'
                out.parent.mkdir(parents=True,exist_ok=True)
                raw=(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode('utf-8')
                out.write_bytes(raw)
                print(json.dumps({'path':str(out),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'cases':len(cases)}))
                """;
        Process process = new ProcessBuilder(python.toString(), "-c", script, root.toString(), machineId)
                .directory(root.toFile()).redirectErrorStream(true).start();
        if (!process.waitFor(30, TimeUnit.SECONDS)) {
            process.destroyForcibly();
            process.waitFor(5, TimeUnit.SECONDS);
            throw new IllegalStateException("original producer capture timed out");
        }
        byte[] output = process.getInputStream().readNBytes(8193);
        if (output.length > 8192) { throw new IllegalStateException("capture output exceeded limit"); }
        System.out.print(new String(output, StandardCharsets.UTF_8));
        if (process.exitValue() != 0) { throw new IllegalStateException("actual Python producer exited " + process.exitValue()); }
    }
}
