package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.Base64;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;

/** Independent Python process invokes the actual production WAL writer/replayer, with bounded test files only. */
final class OriginalDriverJournalOriginalProducerTest {
    @TempDir Path temporary;
    private static final String ORIGINAL="""
        import base64,copy,importlib.util,json,pathlib,sys
        source=pathlib.Path(sys.argv[1])/'ck3_autonomous_player/src/xar_autoplayer/bridge/driver_state_wal_v1.py'
        spec=importlib.util.spec_from_file_location('original_wal',source)
        wal=importlib.util.module_from_spec(spec);spec.loader.exec_module(wal)
        work=pathlib.Path(sys.argv[2]);work.mkdir(exist_ok=True)
        def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
        lifecycle={'schema':'xar.ck3.succession-lifecycle-binding/v1','lifecycle':'rogue_one_life','xar_enabled':'xar_on','pact_contract':'terminal_settlement_required','source':'legacy-driver-default','environment_sha256':None}
        row={'index':1,'command':'actual-unknown-history','ok':False,'result':{'ack':'UNKNOWN','full_id':18446744073709551615,'float':1e23,'negative_zero':-0.0,'text':'原件😀'}}
        full={'format_version':2,'pipe_name':'original-wal-fixture','bridge_pid':123,'episode_character_id':29829,'episode_run_id':'original-episode','last_checkpoint':None,'command_history':[row],'rollback_war_failure':None,'managed_restore_transaction':None,'succession_expectation':None,'succession_lifecycle':lifecycle,'campaign_goal':None,'rollback_war_failures':[]}
        base=wal.sealed_base_bytes(canonical(full));header=wal.new_journal_header(base,1)
        scalar={k:v for k,v in full.items() if k!='command_history'}
        delta={'index':2,'command':'life-advance-one-day','ok':True,'result':{'opaque':[-0.0,1e-7,1e16,9007199254740993]}}
        journal=wal.append_delta(header,[delta],scalar)
        cases=[]
        def add(name,b,j):
            folder=work/name;folder.mkdir();p=folder/'driver-state.json';p.write_bytes(b)
            if j is not None:(folder/wal.FILENAME).write_bytes(j)
            try:
                payload,status=wal.load_pair(p);outcome={'status':status,'payload':payload}
            except wal.JournalInvalid:outcome={'status':'invalid'}
            cases.append({'name':name,'base':base64.b64encode(b).decode(),'journal':None if j is None else base64.b64encode(j).decode(),'expected':outcome})
        add('active',base,canonical(journal));add('full-v2',canonical(full),None)
        legacy=copy.deepcopy(full);legacy['format_version']=1;legacy.pop('succession_lifecycle');legacy.pop('rollback_war_failures')
        add('prewal-v1',canonical(legacy),None)
        future={'format_version':99,'unknown':{'not_a_seed':True}};add('future-data-only',canonical(future),None)
        replayed,_=wal.load_pair(work/'active/driver-state.json');complete=canonical(replayed)
        marker=wal.mark_consolidation(journal,complete);add('marked-full-v2',complete,canonical(marker))
        add('missing-journal',base,None)
        bad=copy.deepcopy(journal);bad['entries'][0]['sha256']='0'*64;add('wrong-hash',base,canonical(bad))
        bad=copy.deepcopy(marker);bad['entries'][0]['sha256']='0'*64;add('bad-chain-even-with-matching-marker',complete,canonical(bad))
        bad=copy.deepcopy(journal);bad['entries'][0]['history_rows'][0]['index']=4;add('gap',base,canonical(bad))
        bad=copy.deepcopy(journal);bad['entries'][0]['sequence']=True;add('bool-sequence',base,canonical(bad))
        bad=copy.deepcopy(journal);bad['base_history_rows']=1.0;add('float-base-count',base,canonical(bad))
        bad=copy.deepcopy(journal);bad['entries'][0]['state_fields'].pop('campaign_goal');add('missing-scalar',base,canonical(bad))
        add('foreign-base',canonical(full),canonical(journal))
        add('malformed-base',b'{',None)
        print(json.dumps(cases,ensure_ascii=False,allow_nan=False,separators=(',',':')))
        """;
    @Test void actualOriginalWriterPairsAndReplayRetainEveryHistoryRowAndNumericToken()throws Exception {
        String python=required("xar.python"),repository=required("xar.repository.root");
        ProcessBuilder command=new ProcessBuilder(python,"-B","-c",ORIGINAL,repository,temporary.toString());
        // Set fixture environment before the independent process imports its source.
        command.environment().put("PYTHONDONTWRITEBYTECODE","1");command.environment().put("PYTHONUTF8","1");
        Path outputPath=temporary.resolve("actual-original-output.json");command.redirectOutput(outputPath.toFile());
        command.redirectError(ProcessBuilder.Redirect.INHERIT);Process process=command.start();
        boolean finished=process.waitFor(45,TimeUnit.SECONDS);if(!finished)process.destroyForcibly();
        assertTrue(finished,"actual Python source producer timed out");assertEquals(0,process.exitValue());
        assertTrue(java.nio.file.Files.size(outputPath)<=2*1024*1024);byte[] output=java.nio.file.Files.readAllBytes(outputPath);
        var rows=(ArrayValue)OriginalDriverJournal.parse(output,2*1024*1024);assertEquals(14,rows.values().size());
        for(Value value:rows.values()) {
            var row=(ObjectValue)value;String name=RetainedJson.string(row.get("name"));
            byte[] base=Base64.getDecoder().decode(RetainedJson.string(row.get("base")));
            Optional<byte[]> journal=row.get("journal") instanceof NullValue?Optional.empty():Optional.of(Base64.getDecoder().decode(RetainedJson.string(row.get("journal"))));
            var expected=(ObjectValue)row.get("expected");String status=RetainedJson.string(expected.get("status"));
            if(status.equals("invalid")){assertThrows(OriginalDriverJournal.JournalInvalid.class,()->OriginalDriverJournal.replay(base,journal),name);continue;}
            var actual=OriginalDriverJournal.replay(base,journal);assertEquals(status,actual.status().name().toLowerCase(java.util.Locale.ROOT),name);
            assertEquals(OriginalDriverJournal.canonical(expected.get("payload"),1048576).sha256(),OriginalDriverJournal.canonical(actual.payload(),1048576).sha256(),name);
        }
    }
    @Test void duplicateFieldsAndWrongTypesCannotHideCorruptOriginals() {
        for(String invalid:List.of("[]","{} {}"))
            assertThrows(OriginalDriverJournal.JournalInvalid.class,()->OriginalDriverJournal.replay(invalid.getBytes(StandardCharsets.UTF_8),Optional.empty()));
        for(String strict:List.of("{\"format_version\":3,\"format_version\":2}","{\"n\":NaN}"))
            assertThrows(OriginalDriverJournal.InputRejected.class,()->OriginalDriverJournal.replay(strict.getBytes(StandardCharsets.UTF_8),Optional.empty()));
    }
    private static String required(String property){String value=System.getProperty(property);assertNotNull(value,"required complete cold-step fixture property: "+property);assertFalse(value.isBlank());return value;}
}
