package org.xar.ck3.control.wave2.events.interactionregistry;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/** Optional once-only original producer capture. Default JUnit never launches Python. */
public final class CaptureInteractionRegistryGolden {
    private CaptureInteractionRegistryGolden() { }
    public static void main(String[] args) throws Exception {
        if (args.length != 4) { throw new IllegalArgumentException("repo-root python-exe new-scratch-root new-output required"); }
        Path repo = Path.of(args[0]).toAbsolutePath().normalize();
        Path python = Path.of(args[1]).toAbsolutePath().normalize();
        Path scratch = Path.of(args[2]).toAbsolutePath().normalize();
        Path output = Path.of(args[3]).toAbsolutePath().normalize();
        Path temporary = Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize();
        if (!scratch.startsWith(temporary) || Files.exists(scratch) || !output.startsWith(temporary.getParent().resolve("logs"))
                || Files.exists(output) || !Files.isRegularFile(python)) { throw new IllegalArgumentException("fresh bounded package paths required"); }
        Files.createDirectories(scratch);
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-c", SCRIPT, repo.toString(), scratch.toString(), output.toString());
        builder.directory(repo.toFile()); builder.inheritIO(); builder.environment().put("TEMP", temporary.toString()); builder.environment().put("TMP", temporary.toString());
        Process process = builder.start();
        if (!process.waitFor(90, TimeUnit.SECONDS)) { process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly(); throw new IllegalStateException("capture timeout"); }
        if (process.exitValue() != 0 || !Files.isRegularFile(output) || Files.size(output) > 65_536) { throw new IllegalStateException("original producer capture failed"); }
    }
    private static final String SCRIPT = """
            from pathlib import Path
            import sys,json,hashlib,datetime,copy
            root,scratch,out=map(Path,sys.argv[1:])
            sys.path[:0]=[str(root/'ck3_autonomous_player/src'),str(root/'tools')]
            from xar_autoplayer import interaction_offline_analysis as producer
            from xar_autoplayer import pending_interaction_source_registry as reader
            from ck3_live_run_id import current_machine_id
            sha=lambda raw:hashlib.sha256(raw).hexdigest()
            canonical=lambda value:json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
            game=scratch/'synthetic-game';state=scratch/'state';review=scratch/'review'
            source=game/'common/character_interactions/synthetic.txt';source.parent.mkdir(parents=True)
            source.write_text('synthetic_unknown_interaction = {\\n category = interaction_category_religion\\n on_accept = { scope:recipient = { add_stress = 10 } }\\n on_decline = { # ignored } brace\\n scope:recipient = { add_piety = -5 } }\\n}\\n',encoding='utf-8')
            gui=game/'gui/interaction_notification_window.gui';gui.parent.mkdir(parents=True)
            gui.write_bytes(b'SYNTHETIC GUI: authored left Reject before right Accept; no Game call')
            context={'build':{'version':'1.20.0.4','exe_sha256':'a'*64},'definition':{'canonical_key':'synthetic_unknown_interaction','deterministic_key_hash':12}}
            gui_binding={'source':'gui/interaction_notification_window.gui','sha256':sha(gui.read_bytes())}
            incident='synthetic-interaction-registry-no-native-call'
            before=producer.write_immutable(scratch/'before.json',{'incident_id':incident,'context':context,'gui_binding':gui_binding,'selection':{'action':'reject'}})
            after=producer.write_immutable(scratch/'after.json',{'incident_id':incident})
            manifest=producer.write_immutable(scratch/'manifest.json',{'completed_control_sequence':123,'new_incidents':[{'kind':'pending_character_interaction','incident_id':incident,'before':before['path'],'before_sha256':before['sha256'],'after':after['path'],'after_sha256':after['sha256']}]})
            report=producer.analyze_batch(manifest['path'],game,review,publish_state_dir=state)
            assert len(report['entries'])==1
            published=Path(report['entries'][0]['published']['path']);original_entry=published.read_bytes();entry=json.loads(original_entry)
            facts=Path(entry['source_facts']['path']);original_facts=facts.read_bytes();original_source=source.read_bytes();original_gui=gui.read_bytes()
            cases=[]
            for name in ['known','build','exe_sha','hash','hash_bool','hash_float','gui_pin','source_changed','gui_changed','facts_changed','entry_fingerprint','entry_schema','classification','preferred_action','facts_schema','facts_receipt_sha']:
                c=copy.deepcopy(context);g=copy.deepcopy(gui_binding);e=json.loads(original_entry);f=json.loads(original_facts)
                source.write_bytes(original_source);gui.write_bytes(original_gui);facts.write_bytes(original_facts);published.write_bytes(original_entry)
                if name=='build':c['build']['version']='1.20.0.5'
                elif name=='exe_sha':c['build']['exe_sha256']='b'*64
                elif name=='hash':c['definition']['deterministic_key_hash']=13
                elif name=='hash_bool':c['definition']['deterministic_key_hash']=True
                elif name=='hash_float':c['definition']['deterministic_key_hash']=12.0
                elif name=='gui_pin':g['sha256']='0'*64
                elif name=='source_changed':source.write_bytes(original_source+b'\\n# changed')
                elif name=='gui_changed':gui.write_bytes(original_gui+b' changed')
                elif name=='facts_changed':facts.write_bytes(b'{}')
                elif name=='entry_fingerprint':e['fingerprint']='0'*64;published.write_bytes(canonical(e))
                elif name=='entry_schema':e['schema']='bad-schema';published.write_bytes(canonical(e))
                elif name=='classification':e['classification']='reviewed=true';published.write_bytes(canonical(e))
                elif name=='preferred_action':e['preferred_action']='accept';published.write_bytes(canonical(e))
                elif name=='facts_schema':f['schema']='bad-schema';facts.write_bytes(canonical(f));e['source_facts']['sha256']=sha(facts.read_bytes());published.write_bytes(canonical(e))
                elif name=='facts_receipt_sha':e['source_facts']['sha256']='0'*64;published.write_bytes(canonical(e))
                reader._validate_fingerprint.cache_clear()
                known,audit=reader.load_source_reviewed_interaction_v1(state,c,g)
                cases.append({'name':name,'expected_known':known is not None,'expected_status':audit['status'],'legacy_audit':audit})
            source.write_bytes(original_source);gui.write_bytes(original_gui);facts.write_bytes(original_facts);published.write_bytes(original_entry)
            value={'schema':'xar.interaction-registry-original-producer-golden/v1','machine_id':current_machine_id(),'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'notice':'Actual unchanged offline producer and reader, synthetic sources and no Game/MCP/ledger calls; default Java tests rebind paths into their own temp root.',
                'producer_sha256':sha((root/'ck3_autonomous_player/src/xar_autoplayer/interaction_offline_analysis.py').read_bytes()),'reader_sha256':sha((root/'ck3_autonomous_player/src/xar_autoplayer/pending_interaction_source_registry.py').read_bytes()),
                'entry_utf8':original_entry.decode('utf-8'),'facts_utf8':original_facts.decode('utf-8'),'source_utf8':original_source.decode('utf-8'),'gui_utf8':original_gui.decode('utf-8'),'entry_sha256':sha(original_entry),'facts_sha256':sha(original_facts),'cases':cases}
            raw=canonical(value);assert len(raw)<=65536
            assert sum(p.stat().st_size for p in scratch.rglob('*') if p.is_file())<=262144
            with out.open('xb') as stream:stream.write(raw)
            print(json.dumps({'machine_id':value['machine_id'],'output':str(out),'bytes':len(raw),'sha256':sha(raw),'legacy_cases':len(cases),'Game_MCP_ledger_calls':0}))
            """;
}
