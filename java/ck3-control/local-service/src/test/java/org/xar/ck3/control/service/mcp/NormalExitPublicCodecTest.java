package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.normalexit.NormalExitProtocol.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.OptionalLong;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;

/** Original contract DATA parity, actual Java protocol producer and public codec; no Managed/process permission. */
final class NormalExitPublicCodecTest {
    private static final BigInteger BIRTH=new BigInteger("18446744073709551615");
    private static RawJson raw(String value){return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
    private static RawJson raw(ObjectNode value){return new RawJson(StrictJson.canonical(value));}
    static ObjectNode memory(){
        Binding b=new Binding(BigInteger.valueOf(72),BigInteger.valueOf(9301),BigInteger.valueOf(43),BigInteger.valueOf(8),BIRTH,"b".repeat(64));
        Target t=new Target(true,true,true,true,true,true,true,true,new BigInteger("9007199254740993"));
        Dispatch none=new Dispatch(false,false,false,false,false);
        Observation n=new Observation(b,Action.CONFIRM_DESKTOP,Status.DISPATCH_PENDING,new BigInteger("9007199254740993"),
                new Proof(true,true,true,true,true,true,true),true,true,false,false,"a".repeat(64),"",List.of(t,t,t),
                List.of(none,none,new Dispatch(true,true,true,false,false)),List.of(true,true,true),Optional.empty());
        RetainedIdentity identity=new RetainedIdentity(BigInteger.valueOf(43),BIRTH,"original-handle");
        ProcessObservation process=new ProcessObservation(identity,0,WaitState.SIGNALED,OptionalLong.of(0),true,true,BigInteger.valueOf(100),5000,false,"driver_monotonic_v1",List.of());
        ObjectNode row=classify(Optional.of(n),process,Optional.of(BigInteger.valueOf(90)),identity).json();
        row.put("schema","ck3-normal-exit-request-result-v1").put("action","confirm_desktop").put("public_revision",BigInteger.valueOf(72))
                .put("process_creation_filetime_100ns",BIRTH).put("source_inventory_sha256",b.sourceInventorySha256())
                .put("request_id","original-confirm").put("claim_path","original-claim").put("uses_desktop_input",false).put("uses_ocr",false)
                .put("native_submission_count",1).put("driver_dispatch_receipt_observed_monotonic_ns",BigInteger.valueOf(90)).put("snapshot_after_required",false);
        row.set("native_observation",observationJson(n));
        row.set("process_preconfirm_pin",StrictJson.object().put("pid",43).put("creation_filetime_100ns",BIRTH).put("retained_handle_token","original-handle")
                .put("wait_result",258).put("verified_monotonic_ns",BigInteger.valueOf(80)).put("observation_clock_domain","driver_monotonic_v1"));
        ObjectNode p=StrictJson.object().put("pid",43).put("creation_filetime_100ns",BIRTH).put("retained_handle_token","original-handle")
                .put("wait_result",0).put("wait_state","signaled").put("exit_code",0).put("process_identity_verified",true).put("process_exit_observed",true)
                .put("observed_monotonic_ns",BigInteger.valueOf(100)).put("timeout_ms",5000).put("observation_deadline_reached",false).put("observation_clock_domain","driver_monotonic_v1");
        p.putArray("errors");row.set("process_observation",p);return row;
    }
    @Test void actualNativeProducerAndTerminalClassifierSurviveFullWidthPublicV2Roundtrip(){
        var result=NormalExitPublicCodec.fromMemory(raw(memory()));var wire=NormalExitPublicCodec.encode(result);ObjectNode row=(ObjectNode)StrictJson.parse(wire.bytes());
        assertEquals("18446744073709551615",row.get("process_creation_filetime_100ns").textValue());assertEquals("72",row.get("public_revision").textValue());
        assertEquals("9007199254740993",row.get("native_observation").get("pump_epoch").textValue());
        assertEquals("9007199254740993",row.get("native_observation").get("targets").get(0).get("target_vtable_rva").textValue());
        var decoded=NormalExitPublicCodec.decode(wire,Optional.of(BIRTH));assertEquals(result.memory(),decoded.memory());
        assertTrue(row.get("typed_normal_exit_observed").booleanValue());assertFalse(row.get("autosave_verified").booleanValue());assertFalse(row.get("retry_authorized").booleanValue());
        assertThrows(IllegalArgumentException.class,()->NormalExitPublicCodec.decode(wire,Optional.of(BIRTH.subtract(BigInteger.ONE))));
        row.put("process_creation_filetime_100ns",BIRTH);assertThrows(IllegalArgumentException.class,()->NormalExitPublicCodec.decode(raw(row),Optional.empty()));
    }
    @Test void actualObserverCannotAddNativeSubmissionOrTurnUnknownReceiptIntoExitProof(){
        ObjectNode row=memory();row.put("schema","ck3-normal-exit-process-observation-result-v1").put("native_submission_count",0).put("observer_retained",false);
        assertEquals(NormalExitPublicCodec.Kind.OBSERVATION,NormalExitPublicCodec.fromMemory(raw(row)).kind());
        row.put("native_submission_count",1);assertThrows(IllegalArgumentException.class,()->NormalExitPublicCodec.fromMemory(raw(row)));
        row.put("native_submission_count",0).putNull("driver_dispatch_receipt_observed_monotonic_ns");
        assertThrows(IllegalArgumentException.class,()->NormalExitPublicCodec.fromMemory(raw(row)));
        ObjectNode bad=memory();bad.put("autosave_verified",true);assertThrows(IllegalArgumentException.class,()->NormalExitPublicCodec.fromMemory(raw(bad)));
    }
    @Test void publicInputsPreserveMissingObserveAndRejectNumericBoolAliasesOverflowAndDuplicateRevisions(){
        assertEquals(new PublicBindings.Missing(),NormalExitPublicCodec.encodeObserve(NormalExitPublicCodec.decodeObserve(new PublicBindings.Missing())));
        assertEquals(PublicBindings.present(raw("{}")),NormalExitPublicCodec.encodeObserve(NormalExitPublicCodec.decodeObserve(PublicBindings.present(raw("{}")))));
        for(String value:List.of("null","[]","{\"x\":1}"))assertThrows(IllegalArgumentException.class,()->NormalExitPublicCodec.decodeObserve(PublicBindings.present(raw(value))));
        var q=NormalExitPublicCodec.decodeQuery(PublicBindings.present(raw("{\"expected_revision\":\"18446744073709551615\"}")));
        assertEquals(StrictJson.UINT64_MAX,q.expectedRevision());assertEquals(q,NormalExitPublicCodec.decodeQuery(PublicBindings.present(NormalExitPublicCodec.encodeQuery(q))));
        for(String value:List.of("1","true","1.0","\"01\"","\"0\"","\"18446744073709551616\"","null"))
            assertThrows(IllegalArgumentException.class,()->NormalExitPublicCodec.decodeQuery(PublicBindings.present(raw("{\"expected_revision\":"+value+"}"))));
        assertThrows(IllegalArgumentException.class,()->NormalExitPublicCodec.decodeQuery(PublicBindings.present(raw("{\"expected_revision\":\"1\",\"expected_revision\":\"2\"}"))));
        var request=new NormalExitPublicCodec.Request(Action.CONTINUE_PREPARATION,BigInteger.ONE,"a".repeat(64));
        assertEquals(request,NormalExitPublicCodec.decodeRequest(PublicBindings.present(NormalExitPublicCodec.encodeRequest(request))));
        assertThrows(IllegalArgumentException.class,()->new NormalExitPublicCodec.Request(Action.QUERY_CONTEXT,BigInteger.ONE,"a".repeat(64)));
    }
    private static ObjectNode unknownPreparation(){
        ObjectNode row=StrictJson.object();row.put("schema","ck3-normal-exit-request-result-v1").put("action",Action.CONTINUE_PREPARATION.wire())
                .put("status","dispatch_unknown_claimed").put("public_revision",72).putNull("native_observation")
                .put("process_creation_filetime_100ns",BIRTH).put("source_inventory_sha256","b".repeat(64)).put("claim_consumed",true)
                .put("retry_authorized",false).put("autosave_verified",false).put("process_exit_observed",false).put("typed_normal_exit_observed",false)
                .put("request_id","original-missing-ack").put("claim_path","original-consumed-phase").put("uses_desktop_input",false)
                .put("uses_ocr",false).put("native_submission_count",1);return row;
    }
    @Test void originalFailureReasonPreservesMissingNullAndExactTextButRejectsOtherJsonTypes(){
        for(int variant=0;variant<4;variant++){
            ObjectNode memory=unknownPreparation();
            if(variant==1)memory.putNull("reason");else if(variant==2)memory.put("reason","");
            else if(variant==3)memory.put("reason","Bridge error: original native response / 原始错误");
            var actual=NormalExitPublicCodec.fromMemory(raw(memory));var wire=NormalExitPublicCodec.encode(actual);
            var round=NormalExitPublicCodec.decode(wire,Optional.of(BIRTH));
            ObjectNode restored=(ObjectNode)StrictJson.parse(round.memory().bytes());assertEquals(memory,restored);
            assertEquals(variant!=0,restored.has("reason"));
            if(variant==1)assertTrue(restored.get("reason").isNull());
            if(variant>=2)assertEquals(memory.get("reason").textValue(),restored.get("reason").textValue());
        }
        for(String invalid:List.of("true","0","1.5","{}","[]")){
            ObjectNode memory=unknownPreparation();memory.set("reason",StrictJson.parse(invalid.getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class,()->NormalExitPublicCodec.fromMemory(raw(memory)));
            ObjectNode wire=(ObjectNode)StrictJson.parse(NormalExitPublicCodec.encode(NormalExitPublicCodec.fromMemory(raw(unknownPreparation()))).bytes());
            wire.set("reason",memory.get("reason"));
            assertThrows(IllegalArgumentException.class,()->NormalExitPublicCodec.decode(raw(wire),Optional.of(BIRTH)));
        }
    }

}
