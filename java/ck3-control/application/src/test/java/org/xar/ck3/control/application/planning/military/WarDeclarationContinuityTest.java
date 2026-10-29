package org.xar.ck3.control.application.planning.military;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract;

/** Pure DATA only: no fake Managed Root, writer, Ready, Game or dispatch is constructed. */
final class WarDeclarationContinuityTest {
    private static final DeclarationContract.Choice CHOICE=new DeclarationContract.Choice("24-2--1",BigInteger.valueOf(24),
            BigInteger.TWO,"claim_cb",BigInteger.valueOf(-1),BigInteger.valueOf(73),List.of(BigInteger.valueOf(91)));
    private static Obj json(String raw){return DriverJson.object(raw.getBytes(StandardCharsets.UTF_8),1024*1024);}
    private static Obj replace(Obj row,String key,Value value){var out=new LinkedHashMap<>(row.members());out.put(key,value);return new Obj(out);}
    private static Obj before(){return json("""
            {"snapshot_id":"native:10","revision":20,"native_revision":10,"date_raw":1000,
             "episode_run_id":"software-episode","paused":true,"map_ready":true,
             "played_character":{"character_id":73,"alive":true},
             "diagnostics":{"bridge_pid":42,"connection_generation":5,"hello":{"pid":42}},
             "active_wars":[{"war_id":7}]}
            """);}
    private static Obj after(){return replace(replace(replace(before(),"snapshot_id",new Text("native:11")),
            "revision",new IntegerValue(BigInteger.valueOf(21))),"native_revision",new IntegerValue(BigInteger.valueOf(11)));}
    private static Obj matched(){return replace(after(),"active_wars",json("""
            {"rows":[{"war_id":7},{"war_id":8,"player_side":"attacker","player_is_primary_war_leader":true,
             "primary_opponent_character_id":24,"targeted_title_ids":[91]}]}
            """).get("rows"));}
    private static WarDeclarationContinuity.Record armed(Optional<WarDeclarationContinuity.Roles> roles) {
        var origin=WarDeclarationContinuity.arm(before(),CHOICE,roles,"original-request-1");
        return new WarDeclarationContinuity.Record(origin,WarDeclarationContinuity.Status.SUBMISSION_UNKNOWN,
                WarDeclarationContinuity.NativeResponse.UNKNOWN,true,OptionalInt.empty(),false,Optional.empty(),
                WarDeclarationContinuity.Reason.ORIGINAL_REQUEST_NOT_YET_OBSERVED);
    }
    @Test void originalAcceptedRequestNeedsUniqueNewFinalizedRoleAndExactTitleIdentity() {
        var original=armed(Optional.of(new WarDeclarationContinuity.Roles(73,24)));
        var accepted=WarDeclarationContinuity.mark(original,true);
        var started=WarDeclarationContinuity.observe(accepted,matched());
        assertEquals(WarDeclarationContinuity.Status.WAR_STARTED,started.status());assertEquals(8,started.warId().orElseThrow());
        assertTrue(started.postconditionVerified());assertFalse(((Bool)WarDeclarationContinuity.json(started).get("casus_belli_identity_observed")).value());
        assertFalse(((Bool)WarDeclarationContinuity.json(started).get("request_retried")).value());
        assertEquals(started,WarDeclarationContinuity.decode(WarDeclarationContinuity.encode(started)));
        assertEquals(original,WarDeclarationContinuity.decode(WarDeclarationContinuity.encode(original)));
        // The original unknown request stays unknown even when a matching war is seen; no ACK is synthesized.
        var unknownObserved=WarDeclarationContinuity.observe(original,matched());
        assertEquals(WarDeclarationContinuity.Status.SUBMISSION_UNKNOWN,unknownObserved.status());
        assertFalse(unknownObserved.postconditionVerified());
    }
    @Test void ambiguityStaleFrameMissingRolesAndWrongOwnerNeverUpgradeWarCountToSuccess() {
        var accepted=WarDeclarationContinuity.mark(armed(Optional.of(new WarDeclarationContinuity.Roles(73,24))),true);
        var rows=new ArrayList<>(((Arr)matched().get("active_wars")).items());
        rows.add(replace((Obj)rows.getLast(),"war_id",new IntegerValue(BigInteger.valueOf(9))));
        assertEquals(WarDeclarationContinuity.Reason.AMBIGUOUS_NEW_WARS,
                WarDeclarationContinuity.observe(accepted,replace(matched(),"active_wars",new Arr(rows))).reason());
        assertEquals(WarDeclarationContinuity.Reason.ACTUAL_ROLE_TITLE_OR_FRESH_FRAME_IDENTITY_UNAVAILABLE,
                WarDeclarationContinuity.observe(accepted,replace(matched(),"native_revision",new IntegerValue(BigInteger.TEN))).reason());
        assertFalse(WarDeclarationContinuity.observe(WarDeclarationContinuity.mark(armed(Optional.empty()),true),matched()).postconditionVerified());
        var changed=replace(matched(),"episode_run_id",new Text("foreign-episode"));
        assertEquals(WarDeclarationContinuity.Reason.ACTUAL_PROCESS_CONNECTION_OR_EPISODE_CHANGED,
                WarDeclarationContinuity.observe(accepted,changed).reason());
        var rejected=WarDeclarationContinuity.mark(armed(Optional.of(new WarDeclarationContinuity.Roles(73,24))),false);
        assertEquals(rejected,WarDeclarationContinuity.observe(rejected,matched()));
        assertThrows(IllegalArgumentException.class,()->WarDeclarationContinuity.mark(accepted,true));
    }
    @Test void strictPersistedConsumerRejectsWrongFieldsBoolIntegersMissingNullAndForgedSuccess() {
        var raw=WarDeclarationContinuity.json(armed(Optional.empty()));
        for(Obj invalid:List.of(replace(raw,"war_id",new Bool(false)),replace(raw,"request_retried",new Bool(true)),
                replace(raw,"casus_belli_identity_observed",new Bool(true)),replace(raw,"in_flight",new IntegerValue(BigInteger.ONE)),
                replace(raw,"unknown_alias",Nil.INSTANCE),replace(raw,"final_cb_roles",new Obj(Map.of())),
                replace(raw,"status",new Text("war_started"))))
            assertThrows(IllegalArgumentException.class,()->WarDeclarationContinuity.decode(DriverJson.encode(invalid)));
        var missing=new LinkedHashMap<>(raw.members());missing.remove("war_id");
        assertThrows(IllegalArgumentException.class,()->WarDeclarationContinuity.decode(DriverJson.encode(new Obj(missing))));
        var mutable=new ArrayList<>(List.of(7));
        var origin=WarDeclarationContinuity.arm(before(),CHOICE,Optional.empty(),"request");
        var copied=new WarDeclarationContinuity.Origin(origin.requestId(),CHOICE,mutable,Optional.empty(),origin.owner(),
                origin.submittedSnapshotId(),origin.submittedRevision(),origin.submittedNativeRevision(),origin.submittedDateRaw());
        mutable.clear();assertEquals(List.of(7),copied.beforeWarIds());
    }
    @Test void actualOriginalPythonPrepareMarkObserveFeedsTheNewStrictPersistedConsumer()throws Exception {
        var inputs=new ArrayList<Value>();var expected=new ArrayList<WarDeclarationContinuity.Record>();
        for(int variant=0;variant<7;variant++) {
            Obj observed=matched();boolean accepted=variant!=1;boolean roles=variant!=2;
            if(variant==3)observed=replace(observed,"native_revision",new IntegerValue(BigInteger.TEN));
            if(variant==4)observed=replace(observed,"episode_run_id",new Text("foreign"));
            if(variant==5) {
                var rows=new ArrayList<>(((Arr)observed.get("active_wars")).items());
                rows.add(replace((Obj)rows.getLast(),"war_id",new IntegerValue(BigInteger.valueOf(9))));
                observed=replace(observed,"active_wars",new Arr(rows));
            }
            if(variant==6) {
                var rows=new ArrayList<>(((Arr)observed.get("active_wars")).items());
                rows.set(1,replace((Obj)rows.get(1),"targeted_title_ids",new Arr(List.of(new IntegerValue(BigInteger.valueOf(92))))));
                observed=replace(observed,"active_wars",new Arr(rows));
            }
            var original=armed(roles?Optional.of(new WarDeclarationContinuity.Roles(73,24)):Optional.empty());
            var result=WarDeclarationContinuity.observe(WarDeclarationContinuity.mark(original,accepted),observed);
            expected.add(result);
            Obj selected=DriverJson.object(org.xar.ck3.control.contracts.StrictJson.canonical(DeclarationContract.encodeChoice(CHOICE)),32768);
            inputs.add(new Obj(Map.of("before",before(),"after",observed,"choice",selected,"accepted",new Bool(accepted),"roles",new Bool(roles))));
        }
        Obj result=oracle(new Obj(Map.of("cases",new Arr(inputs))));
        List<Value> records=OpportunityJson.array(result.get("records"),"actual original records");
        assertEquals(expected.size(),records.size());
        for(int i=0;i<records.size();i++) {
            var actual=WarDeclarationContinuity.decode(DriverJson.encode(records.get(i)));
            assertEquals(expected.get(i),actual,"original prepare -> response -> observation -> Java persisted consumer");
            assertEquals(records.get(i),WarDeclarationContinuity.json(actual));
        }
    }
    private static Obj oracle(Obj input)throws Exception {
        String python=System.getProperty("xar.python"),repository=System.getProperty("xar.repository.root");
        if(python==null||repository==null)throw new IOException("MISSING/NOT_RUN: xar.python and xar.repository.root actual original-producer inputs");
        Path root=Path.of(repository).toRealPath();
        String[][] pins={
            {"ck3_autonomous_player/src/xar_autoplayer/bridge/war_declaration_continuity_v1.py","c4c33bdee442526b0ab666670fbfab29b6971405881486440c394dd77c04cd50"},
            {"ck3_autonomous_player/src/xar_autoplayer/bridge/declaration_contract.py","b5ed2eb40f8f52298886d764259501559a551b4096ecaa839e39fa45a12e151c"}};
        for(String[] pin:pins) {
            Path file=root.resolve(pin[0]).toRealPath();assertTrue(file.startsWith(root));
            assertEquals(pin[1],HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file))),"original producer changed");
        }
        String script="""
                import ast,copy,json,pathlib,re,sys,threading,types
                from collections.abc import Mapping
                from functools import wraps
                root=pathlib.Path(sys.argv[1]);base=root/'ck3_autonomous_player'/'src'/'xar_autoplayer'/'bridge'
                env={'__name__':'actual_declaration_source_oracle','re':re,'json':json,'deepcopy':copy.deepcopy,
                     'Mapping':Mapping,'wraps':wraps}
                exec(compile((base/'declaration_contract.py').read_text(encoding='utf-8'),str(base/'declaration_contract.py'),'exec'),env)
                tree=ast.parse((base/'war_declaration_continuity_v1.py').read_text(encoding='utf-8'))
                # Actual source bodies and constants; imports alone are omitted. No business algorithm is copied.
                tree.body=[node for node in tree.body if not isinstance(node,(ast.Import,ast.ImportFrom))]
                exec(compile(ast.fix_missing_locations(tree),str(base/'war_declaration_continuity_v1.py'),'exec'),env)
                records=[]
                for case in json.load(sys.stdin)['cases']:
                    driver=types.SimpleNamespace(state_dir=None,_driver_state_lock=threading.RLock())
                    role={'available':True,'source':'finalized_selected_cb_context',
                          'primary_attacker_character_id':73,'primary_defender_character_id':24} if case['roles'] else None
                    driver.get_current_prewar_force_coalition_coverage_v2=lambda *args,r=role:{'prewar_force_coalition_coverage_v2':{'final_cb_roles':r}}
                    env['prepare_declaration_attempt_v1'](driver,case['before'],case['choice'],'original-request-1')
                    env['mark_declaration_response_v1'](driver,accepted=case['accepted'])
                    records.append(env['observe_declaration_attempt_v1'](driver,case['after']))
                print(json.dumps({'records':records},ensure_ascii=False,allow_nan=False,separators=(',',':')))
                """;
        var processBuilder=new ProcessBuilder(python,"-B","-c",script,root.toString());
        processBuilder.environment().put("PYTHONDONTWRITEBYTECODE","1");processBuilder.environment().put("PYTHONIOENCODING","utf-8");
        Process process=processBuilder.start();
        try {
            process.getOutputStream().write(DriverJson.encode(input));process.getOutputStream().close();
            var output=java.util.concurrent.CompletableFuture.supplyAsync(()->readBounded(process.getInputStream()));
            var errors=java.util.concurrent.CompletableFuture.supplyAsync(()->readBounded(process.getErrorStream()));
            if(!process.waitFor(30,TimeUnit.SECONDS)){process.destroyForcibly();throw new IOException("original declaration oracle timed out");}
            byte[] stdout=output.get(5,TimeUnit.SECONDS),stderr=errors.get(5,TimeUnit.SECONDS);
            assertEquals(0,process.exitValue(),new String(stderr,StandardCharsets.UTF_8));
            return DriverJson.object(stdout,1024*1024);
        } finally {if(process.isAlive())process.destroyForcibly();}
    }
    private static byte[] readBounded(java.io.InputStream stream) {
        try {byte[] bytes=stream.readNBytes(1024*1024+1);if(bytes.length>1024*1024)throw new IOException("bounded original oracle output exceeded");return bytes;}
        catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
    }
}

