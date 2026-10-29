package org.xar.ck3.control.application.history;

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
import java.util.Optional;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.history.DriverReturnedPublicReadHistoryMaterial.*;

/** Original recording policy -> complete cold row DATA. No fake Source/CP19 token/Managed positive is used. */
final class DriverReturnedPublicReadHistoryRowProducerTest {
    private static final String H="query-route-contact-horizon-v1-0-to-9-h-1-2",P="preview-move-army-0-to-9";
    private static ExactRef ref(String name){return new ExactRef("software-data-only/"+name,1,"a".repeat(64));}
    private static Obj json(String raw){return DriverJson.object(raw.getBytes(StandardCharsets.UTF_8),DriverJson.MAX_NATIVE_BYTES);}
    private static Obj change(Obj row,String key,Value value){var fields=new LinkedHashMap<>(row.members());fields.put(key,value);return new Obj(fields);}
    private static Obj report(Kind kind) {
        Obj common=json("""
                {"accepted":false,"backend_id":"native-headless","queried_snapshot_id":"native:7","queried_revision":9,
                 "queried_native_revision":7,"queried_connection_generation":3,"queried_episode_run_id":"software-episode",
                 "opaque_original":{"ordered":[2,0,1],"nullable":null,"numeric_text":"001"}}
                """);
        var fields=new LinkedHashMap<>(common.members());
        if(kind==Kind.HORIZON_UNAVAILABLE) {
            fields.putAll(json("""
                    {"schema":"xar.route-contact-readonly-unavailable.v1","step":"query-route-contact-horizon-v1-0-to-9-h-1-2",
                     "available":false,"status":"unavailable","read_only":true,"business_submission":false,"replay_allowed":false,
                     "replan_required":true,"route_contact_horizon":null,"unavailable_reason":"native_complete_contact_route_unavailable",
                     "snapshot_revision":7,"queried_date_raw":1000,"queried_actor_character_id":73,"queried_bridge_pid":42,
                     "readonly_unavailable_evidence":{"schema":"xar.native-readonly-terminal-rejection.v1",
                      "native_request_id":"original-negative","native_request":{"type":"execute_step","protocol_version":1,
                       "request_id":"original-negative","step":"query-route-contact-horizon-v1-0-to-9-h-1-2","expected_revision":7},
                      "native_command_result":{"type":"command_result","protocol_version":1,"request_id":"original-negative","ok":false,
                       "error":"CK3 route arrival timeline is unavailable"},"same_frame_readback":{"starting_frame":{},"ending_frame":{}}}}
                    """).members());
        } else fields.putAll(json("""
                {"step":"preview-move-army-0-to-9","status":"deferred","route_preview":{"status":"deferred",
                 "reason":"army_not_move_ready","native_rejection_stage":"army_state_rejected","native_error":"CK3 army state rejects movement",
                 "army_id":0,"origin_province_id":-1,"target_province_id":9,"route_province_ids":[],"previewed_date_raw":1000},
                 "player_armies":[{"army_id":0,"opaque":null}],"snapshot_id":"native:7","revision":9}
                """).members());
        return new Obj(fields);
    }
    private static DriverReturnedPublicReadHistoryRowProducer.RawHistoryRow row(Kind kind,Obj report,PublicNumbers numbers) {
        var frames=new FrameOriginals(ref("driver"),ref("known"),ref("native"),ref("facts"),ref("readback-native"),ref("readback-facts"));
        var input=new InvocationData(ref("actual-negative-collection-metadata"),new OperationKey("encoded-original-command:42"),frames,
                ref("actual-caller"),ref("actual-epoch"),7,"b".repeat(64),List.of(ref("original-producer.java")));
        var source=new DriverReturnedPublicReadHistoryRowProducer.HistorySource(kind,new OperationKey(kind==Kind.HORIZON_UNAVAILABLE?H:P),input,
                ref("invocation"),ref("negative-ack"),ref("prepared"),new NativeRequestChronology.PacketIdentity(10,"c".repeat(64)),
                ref("full-result"),numbers,List.of(ref("support")),List.of(ref("original-producer.java")),List.of(ref("fixed-formatter.java")));
        return new DriverReturnedPublicReadHistoryRowProducer.RawHistoryRow(5,source,report);
    }
    @Test void normalReturnedNegativeReadsPreserveFullResultWithoutErrorAndKeepCommandRolesSeparate() {
        for(Kind kind:Kind.values()) {
            Obj original=report(kind);var row=row(kind,original,new PublicNumbers(List.of()));
            assertEquals(kind==Kind.PREVIEW_DEFERRED,row.ok());assertEquals("encoded-original-command:42",row.command());
            assertEquals(new Text(kind==Kind.HORIZON_UNAVAILABLE?H:P),row.result().get("step"));
            assertFalse(row.toJson().members().containsKey("error"));assertEquals(original,row.result());
            var cold=DriverReturnedPublicReadHistoryRowProducer.decode(row.encode());assertEquals(row,cold);
            assertArrayEquals(row.historyEntry().originalRow().json(),cold.historyEntry().originalRow().json());
            assertEquals(original.get("opaque_original"),cold.result().get("opaque_original"));
            assertEquals(row.source().publicNumbers(),DriverReturnedPublicReadHistoryRowProducer.publicNumbersFromSource(
                    cold.toJson().get(DriverReturnedPublicReadHistoryRowProducer.SOURCE_FIELD)));
            assertFalse(cold.source().evidence().isEmpty());assertFalse(cold.toJson().members().containsKey("read_history_source"));
        }
    }
    @Test void exactPublicNumberRolesRoundtripTheCompleteReportAndNeverInferAnIntegerFromText() {
        Obj original=change(report(Kind.HORIZON_UNAVAILABLE),"queried_revision",new IntegerValue(new BigInteger("18446744073709551615")));
        Obj exposed=change(original,"queried_revision",new Text("18446744073709551615"));
        PublicNumbers roles=PublicNumbers.fromResults(RawJson.fullMaterial(DriverJson.encode(original)),RawJson.fullMaterial(DriverJson.encode(exposed)));
        var row=row(Kind.HORIZON_UNAVAILABLE,original,roles);var cold=DriverReturnedPublicReadHistoryRowProducer.decode(row.encode());
        assertEquals(exposed,cold.source().publicNumbers().toPublic(cold.result()));assertEquals(original,roles.fromPublic(exposed));
        assertEquals(new Text("001"),OpportunityJson.object(cold.result().get("opaque_original"),"original opaque object").get("numeric_text"));
        assertThrows(IllegalArgumentException.class,()->roles.fromPublic(change(exposed,"queried_revision",new Text("018446744073709551615"))));
    }
    @Test void strictColdRowRejectsWrongOutcomeAliasMissingNullBoolIntegersAndSourceRoles() {
        var original=row(Kind.HORIZON_UNAVAILABLE,report(Kind.HORIZON_UNAVAILABLE),new PublicNumbers(List.of()));
        Obj raw=original.toJson();
        for(Obj invalid:List.of(change(raw,"ok",new Bool(true)),change(raw,"ok",new IntegerValue(BigInteger.ZERO)),
                change(raw,"index",new Bool(true)),change(raw,"command",new Text(H)),change(raw,"error",new Text("not a thrown error"))))
            assertThrows(IllegalArgumentException.class,()->DriverReturnedPublicReadHistoryRowProducer.decode(DriverJson.encode(invalid)));
        var missing=new LinkedHashMap<>(report(Kind.HORIZON_UNAVAILABLE).members());missing.remove("route_contact_horizon");
        assertThrows(IllegalArgumentException.class,()->row(Kind.HORIZON_UNAVAILABLE,new Obj(missing),new PublicNumbers(List.of())));
        Obj source=(Obj)raw.get(DriverReturnedPublicReadHistoryRowProducer.SOURCE_FIELD);
        Obj wrong=change(source,"outbound_bytes",new IntegerValue(BigInteger.TEN));
        assertThrows(IllegalArgumentException.class,()->DriverReturnedPublicReadHistoryRowProducer.decode(
                DriverJson.encode(change(raw,DriverReturnedPublicReadHistoryRowProducer.SOURCE_FIELD,wrong))));
        assertThrows(IllegalArgumentException.class,()->DriverReturnedPublicReadHistoryRowProducer.decodeSource(change(source,"schema",new Text("returned-sampling-not-read"))));
    }
    @Test void optionalEpochManifestRoundtripsAbsentNullAndPresentWithoutCrossingStrictFields() {
        var frames=new FrameOriginals(ref("driver"),ref("known"),ref("native"),ref("facts"),ref("readback-native"),ref("readback-facts"));
        var present=new InvocationData(ref("meta"),new OperationKey("cmd:1"),frames,ref("caller"),ref("epoch-present"),1,"a".repeat(64),List.of(ref("src")));
        var absent=new InvocationData(ref("meta"),new OperationKey("cmd:1"),frames,ref("caller"),Optional.<ExactRef>empty(),1,"a".repeat(64),List.of(ref("src")));
        var coldPresent=DriverReturnedPublicReadHistoryRowProducer.decodeInvocation(DriverReturnedPublicReadHistoryRowProducer.invocationJson(present).bytes());
        assertEquals(present,coldPresent);assertEquals(ref("epoch-present"),coldPresent.epochManifest().orElseThrow());
        var coldAbsent=DriverReturnedPublicReadHistoryRowProducer.decodeInvocation(DriverReturnedPublicReadHistoryRowProducer.invocationJson(absent).bytes());
        assertEquals(absent,coldAbsent);assertTrue(coldAbsent.epochManifest().isEmpty());
        var obj=DriverJson.object(DriverReturnedPublicReadHistoryRowProducer.invocationJson(absent).bytes(),DriverJson.MAX_NATIVE_BYTES);
        var nullEpoch=change(obj,"epoch_manifest",Nil.INSTANCE);
        assertEquals(absent,DriverReturnedPublicReadHistoryRowProducer.decodeInvocation(DriverJson.encode(nullEpoch)));
        var missingEpoch=new LinkedHashMap<>(obj.members());missingEpoch.remove("epoch_manifest");
        assertEquals(absent,DriverReturnedPublicReadHistoryRowProducer.decodeInvocation(DriverJson.encode(new Obj(missingEpoch))));
        for(Value bad:List.<Value>of(new Bool(true),new Text("epoch"),new IntegerValue(BigInteger.ONE),new Arr(List.of()),new DecimalValue("1.0"),new Obj(Map.of())))
            assertThrows(IllegalArgumentException.class,()->DriverReturnedPublicReadHistoryRowProducer.decodeInvocation(DriverJson.encode(change(obj,"epoch_manifest",bad))));
    }
    @Test void actualOriginalRecordCommandExpressionProducesBothColdRowsWithNoThrownError()throws Exception {
        var cases=new ArrayList<Value>();for(Kind kind:Kind.values())cases.add(new Obj(Map.of("step",new Text(kind==Kind.HORIZON_UNAVAILABLE?H:P),"result",report(kind))));
        Obj actual=originalPolicy(new Obj(Map.of("cases",new Arr(cases))));
        List<Value> outcomes=OpportunityJson.array(actual.get("recorded_ok"),"actual original recording outcomes");
        assertEquals(List.of(new Bool(false),new Bool(true)),outcomes);
        for(int i=0;i<Kind.values().length;i++) {
            Kind kind=Kind.values()[i];var retained=row(kind,report(kind),new PublicNumbers(List.of()));
            assertEquals(outcomes.get(i),new Bool(retained.ok()));
            assertEquals(retained,DriverReturnedPublicReadHistoryRowProducer.decode(retained.encode()));
            assertFalse(retained.toJson().members().containsKey("error"));
        }
    }
    private static Obj originalPolicy(Obj input)throws Exception {
        String python=System.getProperty("xar.python"),configured=System.getProperty("xar.repository.root");
        if(python==null||configured==null)throw new IOException("MISSING/NOT_RUN: actual original-producer xar.python/xar.repository.root");
        Path root=Path.of(configured).toRealPath(),source=root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py").toRealPath();
        assertTrue(source.startsWith(root));assertEquals("eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603",
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(source))));
        for(var entry:Map.of("war_contract.py","b1b14953f01d66c9f6720e4c92cb6b30c26eb1946b20e9b4ba932c9b5e1f7937",
                "battle_control_contract.py","2a5509214b8c0187bb0799a4fc10728d7ea7b7954a525af977d768de0528c3de",
                "war_declared_overview_contract.py","86ebfb0fc5ba6a0150f28c8ac4aeceb3c65116b03d0f5175a99fc9659377ece0").entrySet())
            assertEquals(entry.getValue(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(
                    Files.readAllBytes(source.getParent().resolve(entry.getKey()).toRealPath()))));
        String script="""
                import ast,copy,json,pathlib,sys
                root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player'/'src'))
                from xar_autoplayer.bridge import war_contract
                from xar_autoplayer.bridge import war_declared_overview_contract
                from xar_autoplayer.bridge import battle_control_contract
                tree=ast.parse((root/'ck3_autonomous_player'/'src'/'xar_autoplayer'/'bridge'/'native_driver.py').read_text(encoding='utf-8'))
                matches=[]
                for node in ast.walk(tree):
                    if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Attribute) or node.func.attr!='_record_command':continue
                    for item in node.keywords:
                        if item.arg=='ok' and isinstance(item.value,ast.IfExp):
                            names={part.id for part in ast.walk(item.value) if isinstance(part,ast.Name)}
                            if 'parse_query_route_contact_horizon_step' in names:matches.append(item.value)
                assert len(matches)==1,'one actual normal-return recording policy required'
                expression=compile(ast.Expression(body=copy.deepcopy(matches[0])),'actual-native-driver-recording-policy','eval')
                values=[]
                for case in json.load(sys.stdin)['cases']:
                    env=dict(vars(war_contract));env.update(step=case['step'],result=case['result'],
                        QUERY_WAR_DECLARED_OVERVIEW_STEP=war_declared_overview_contract.QUERY_STEP,
                        CLOSE_WAR_DECLARED_OVERVIEW_STEP=war_declared_overview_contract.CLOSE_STEP,
                        parse_query_battle_control_snapshot_v1_step=battle_control_contract.parse_query_battle_control_snapshot_v1_step)
                    values.append(eval(expression,env))
                print(json.dumps({'recorded_ok':values},allow_nan=False,separators=(',',':')))
                """;
        var builder=new ProcessBuilder(python,"-B","-c",script,root.toString());
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1");builder.environment().put("PYTHONIOENCODING","utf-8");
        Process process=builder.start();
        try {
            process.getOutputStream().write(DriverJson.encode(input));process.getOutputStream().close();
            var out=java.util.concurrent.CompletableFuture.supplyAsync(()->bounded(process.getInputStream()));
            var err=java.util.concurrent.CompletableFuture.supplyAsync(()->bounded(process.getErrorStream()));
            if(!process.waitFor(30,TimeUnit.SECONDS)){process.destroyForcibly();throw new IOException("actual original record policy timed out");}
            byte[] bytes=out.get(5,TimeUnit.SECONDS),errors=err.get(5,TimeUnit.SECONDS);
            assertEquals(0,process.exitValue(),new String(errors,StandardCharsets.UTF_8));return DriverJson.object(bytes,1024*1024);
        } finally {if(process.isAlive())process.destroyForcibly();}
    }
    private static byte[] bounded(java.io.InputStream input) {
        try {byte[] result=input.readNBytes(1024*1024+1);if(result.length>1024*1024)throw new IOException("finite actual original policy output exceeded");return result;}
        catch(IOException error){throw new java.io.UncheckedIOException(error);}
    }
}

