package org.xar.ck3.control.nativebridge.capabilities.normalexit;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.normalexit.NormalExitProtocol.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.OptionalLong;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Protocol/semantic DATA only. No fixture can qualify a process/source inventory or Game actor. */
final class NormalExitProtocolTest {
    private static final Binding B=new Binding(BigInteger.valueOf(72),BigInteger.valueOf(9301),BigInteger.valueOf(43),BigInteger.valueOf(8),new BigInteger("133000000000000043"),"b".repeat(64));
    private static final Proof PROOF=new Proof(true,true,true,true,true,true,true);
    private static final Dispatch NONE=new Dispatch(false,false,false,false,false);
    private static Observation observed(Action action,Status status,List<Dispatch> dispatches,List<Boolean> stages,Optional<Autosave> autosave){
        Target t=new Target(true,true,true,true,true,true,true,true,BigInteger.valueOf(32));
        return new Observation(B,action,status,BigInteger.ONE,PROOF,true,true,false,false,"a".repeat(64),"",List.of(t,t,t),dispatches,stages,autosave);
    }
    @Test void originalPythonEncoderCaseFeedsTheRealNativePacketDecoderWithoutFiletimeRounding() throws Exception {
        Request request=new Request("req-1",Action.QUERY_CONTEXT,B,"nonce-1",Optional.empty());
        String original="{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\"req-1\",\"step\":\"normal-exit-map-v1\",\"action\":\"query_context\",\"expected_revision\":72,\"expected_player_character_id\":9301,\"expected_game_pid\":43,\"expected_connection_generation\":8,\"expected_process_creation_filetime_100ns\":133000000000000043,\"source_inventory_sha256\":\""+"b".repeat(64)+"\",\"request_nonce\":\"nonce-1\"}";
        assertArrayEquals(original.getBytes(StandardCharsets.UTF_8),payload(request));
        byte[] packet=packet(request);var decoded=NativeWire.decodeExecuteRequest(packet);
        assertEquals("req-1",decoded.requestId());assertEquals(STEP,decoded.step());assertEquals(B.nativeRevision(),decoded.expectedRevision().orElseThrow());
        assertEquals(B.creationFiletime(),StrictJson.parse(decoded.normalizedAdditionalFields().value()).get("expected_process_creation_filetime_100ns").bigIntegerValue());
        assertEquals(request,decodeRequest(Arrays.copyOfRange(packet,4,packet.length)));assertArrayEquals(packet,decoded.originalPacket().value());
    }
    @Test void actualRequestParserRejectsWrongTypesDuplicatesBindingsAndCallerInjectedFields(){
        String valid=new String(payload(new Request("req-1",Action.QUERY_CONTEXT,B,"nonce-1",Optional.empty())),StandardCharsets.UTF_8);
        for(String wrong:List.of(valid.replace("\"expected_revision\":72","\"expected_revision\":true"),valid.replace("\"expected_revision\":72","\"expected_revision\":72.0"),
                valid.replace("\"expected_revision\":72","\"expected_revision\":\"72\""),valid.replace("\"expected_revision\":72","\"expected_revision\":72,\"expected_revision\":72"),
                valid.replace("\"expected_revision\":72","\"expected_revision\":0"),valid.replace("\"type\":","\"widget_path\":\"caller\",\"type\":")))
            assertThrows(IllegalArgumentException.class,()->decodeRequest(wrong.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class,()->new Request("req",Action.QUERY_CONTEXT,B,"nonce",Optional.of("a".repeat(64))));
        assertThrows(IllegalArgumentException.class,()->new Request("req",Action.CONFIRM_DESKTOP,B,"nonce",Optional.empty()));
        assertThrows(IllegalArgumentException.class,()->new Request("req\n",Action.CONFIRM_DESKTOP,B,"nonce",Optional.of("a".repeat(64))));
    }
    @Test void nativeProducerDecoderAndRemainingStagePredicatePreserveActualStageRules(){
        Target ready=new Target(true,true,true,true,true,true,true,true,BigInteger.ONE);
        Target hidden=new Target(true,true,false,false,false,false,false,false,BigInteger.ZERO);
        Observation query=new Observation(B,Action.QUERY_CONTEXT,Status.CONTEXT_OBSERVED,BigInteger.ONE,PROOF,false,false,false,false,"a".repeat(64),"",List.of(ready,ready,hidden),List.of(NONE,NONE,NONE),List.of(true,false,false),Optional.empty());
        assertEquals(query,decodeObservation(observationJson(query),B,Action.QUERY_CONTEXT));assertTrue(query.continuePreparationReady());
        var claimed=observationJson(query);((com.fasterxml.jackson.databind.node.ObjectNode)claimed.get("dispatches").get(0)).put("claim_latched",true);
        assertThrows(IllegalArgumentException.class,()->decodeObservation(claimed,B,Action.QUERY_CONTEXT));
        var changed=observationJson(query);changed.put("process_creation_filetime_100ns",new BigInteger("133000000000000044"));
        assertThrows(IllegalArgumentException.class,()->decodeObservation(changed,B,Action.QUERY_CONTEXT));
        assertThrows(IllegalArgumentException.class,()->observed(Action.CONTINUE_PREPARATION,Status.CONTEXT_OBSERVED,List.of(new Dispatch(true,true,true,true,true),NONE,NONE),List.of(true,false,false),Optional.empty()));
    }
    @Test void autosaveReadbackDoesNotBecomeExitOrSaveIntegrity(){
        Observation disabled=observed(Action.DISABLE_EXIT_AUTOSAVE,Status.AUTOSAVE_DISABLED,List.of(NONE,NONE,NONE),List.of(true,true,false),Optional.of(new Autosave(true,true,true,false,true,true,true)));
        assertEquals(disabled,decodeObservation(observationJson(disabled),B,Action.DISABLE_EXIT_AUTOSAVE));assertFalse(disabled.autosaveVerified());
        var falseCredit=observationJson(disabled);falseCredit.put("autosave_verified",true);
        assertThrows(IllegalArgumentException.class,()->decodeObservation(falseCredit,B,Action.DISABLE_EXIT_AUTOSAVE));
    }
    @Test void independentSignalCodeIdentityAndChronologyControlTerminalClassification(){
        Observation nativeConfirm=observed(Action.CONFIRM_DESKTOP,Status.DISPATCH_PENDING,List.of(NONE,NONE,new Dispatch(true,true,true,false,false)),List.of(true,true,true),Optional.empty());
        RetainedIdentity identity=new RetainedIdentity(B.gamePid(),B.creationFiletime(),"original-handle");
        ProcessObservation zero=new ProcessObservation(identity,0,WaitState.SIGNALED,OptionalLong.of(0),true,true,BigInteger.valueOf(100),5000,false,"driver_monotonic_v1",List.of());
        Facts success=classify(Optional.of(nativeConfirm),zero,Optional.of(BigInteger.valueOf(90)),identity);assertTrue(success.typedNormalExitObserved());assertFalse(success.json().get("autosave_verified").booleanValue());
        assertFalse(classify(Optional.of(nativeConfirm),zero,Optional.of(BigInteger.valueOf(101)),identity).typedNormalExitObserved());
        assertFalse(classify(Optional.empty(),zero,Optional.empty(),identity).typedNormalExitObserved());
        ProcessObservation code259=new ProcessObservation(identity,0,WaitState.SIGNALED,OptionalLong.of(259),true,true,BigInteger.valueOf(100),5000,false,"driver_monotonic_v1",List.of());
        Facts actual259=classify(Optional.of(nativeConfirm),code259,Optional.of(BigInteger.valueOf(90)),identity);assertTrue(actual259.processExitObserved());assertEquals(259,actual259.exitCode().orElseThrow());assertFalse(actual259.typedNormalExitObserved());
        RetainedIdentity other=new RetainedIdentity(identity.pid(),identity.creationFiletime(),"another-handle");assertEquals(FactStatus.ORIGINAL_RETAINED_HANDLE_IDENTITY_MISMATCH,classify(Optional.of(nativeConfirm),zero,Optional.of(BigInteger.valueOf(90)),other).status());
        ProcessObservation timeout=new ProcessObservation(identity,258,WaitState.TIMEOUT,OptionalLong.of(259),true,false,BigInteger.valueOf(100),5000,true,"driver_monotonic_v1",List.of());
        Facts pending=classify(Optional.of(nativeConfirm),timeout,Optional.of(BigInteger.valueOf(90)),identity);assertEquals(FactStatus.DISPATCH_PENDING,pending.status());assertFalse(pending.processExitObserved());assertFalse(pending.json().get("retry_authorized").booleanValue());
    }
    @Test void processDataRejectsWaitStateAndExitBooleanContradictionsBeforePublicClassification(){
        RetainedIdentity id=new RetainedIdentity(B.gamePid(),B.creationFiletime(),"same-original-handle");
        assertThrows(IllegalArgumentException.class,()->new ProcessObservation(id,0,WaitState.TIMEOUT,OptionalLong.of(0),true,true,BigInteger.ONE,0,false,"driver_monotonic_v1",List.of()));
        assertThrows(IllegalArgumentException.class,()->new ProcessObservation(id,258,WaitState.SIGNALED,OptionalLong.empty(),true,false,BigInteger.ONE,0,false,"driver_monotonic_v1",List.of()));
        assertThrows(IllegalArgumentException.class,()->new ProcessObservation(id,0,WaitState.FAILED,OptionalLong.empty(),true,false,BigInteger.ONE,0,false,"driver_monotonic_v1",List.of()));
        assertThrows(IllegalArgumentException.class,()->new ProcessObservation(id,0,WaitState.SIGNALED,OptionalLong.of(0),true,false,BigInteger.ONE,0,false,"driver_monotonic_v1",List.of()));
        assertThrows(IllegalArgumentException.class,()->new ProcessObservation(id,258,WaitState.TIMEOUT,OptionalLong.of(259),true,true,BigInteger.ONE,0,false,"driver_monotonic_v1",List.of()));
        assertDoesNotThrow(()->new ProcessObservation(id,0,WaitState.SIGNALED,OptionalLong.of(259),true,true,BigInteger.ONE,0,false,"driver_monotonic_v1",List.of()));
    }

}
