package org.xar.ck3.control.nativebridge;
import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.Arrays;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.RiteDoctrineFrameV1;
import org.xar.ck3.control.nativebridge.capabilities.registry.RiteDoctrineFrameV1PublicCodec;
final class RiteFinalConfirmation26785313ProducerTest {
    @Test void genuineSixRequestsRoundtripWithTheirExactInitialOrFinalStep()throws Exception{
        for(String file:new String[]{"query-request.json","open_dynastic_category-request.json","select_dynastic-request.json","confirm_edit-request.json","query-final-request.json","accept-final-request.json"}){
            byte[] packet=NativeWire.packet(RiteFinalCppFrames.json(file));var request=RiteDoctrineFrameV1PublicCodec.decodeRequestPacket(packet);
            byte[] encoded=NativeWire.execute("java-final-data",request.action().step(),BigInteger.ZERO,RiteDoctrineFrameV1PublicCodec.additionalFields(request).bytes());
            assertEquals(request,RiteDoctrineFrameV1PublicCodec.decodeRequestPacket(encoded));
            assertEquals(request.action().finalConfirmation()?RiteDoctrineFrameV1.FINAL_STEP:RiteDoctrineFrameV1.STEP,NativeWire.decodeExecuteRequest(encoded).step());
        }
    }
    @Test void genuineTwelveResultsRoundtripAndVoidFinalIsNotPersistedEdit()throws Exception{
        for(String file:new String[]{"query-SYNTHETIC-DATA.json","category-opened-SYNTHETIC-DATA.json","selected-SYNTHETIC-DATA.json","confirmation-dispatched-SYNTHETIC-DATA.json","pam-unresolved-SYNTHETIC-DATA.json","indeterminate-SYNTHETIC-DATA.json","unavailable-NoGame.json","final-ready-SYNTHETIC-DATA.json","final-dispatched-SYNTHETIC-DATA.json","final-pending-SYNTHETIC-DATA.json","final-incoherent-SYNTHETIC-DATA.json","final-unavailable-NoGame.json"}){
            var actual=RiteFinalCppFrames.response(file);var frame=RiteDoctrineFrameV1PublicCodec.decodePacket(new RawJson(actual.payload().value()),actual.requestId());
            assertEquals(frame,RiteDoctrineFrameV1.decode(RiteDoctrineFrameV1PublicCodec.encode(frame)));
            var json=NativeWire.object(NativeWire.parse(RiteDoctrineFrameV1PublicCodec.encode(frame).bytes()));assertFalse(json.get("rite_edit_confirmed").booleanValue());assertFalse(json.get("physical_save_confirmed").booleanValue());
        }
        var finalFrame=RiteFinalCppFrames.frame("final-dispatched-SYNTHETIC-DATA.json");assertTrue(finalFrame.effectAttempted());assertTrue(finalFrame.nativeReturned());assertFalse(finalFrame.nativeHandled());assertTrue(finalFrame.nativeOk());
        assertTrue(RiteFinalCppFrames.frame("confirmation-dispatched-SYNTHETIC-DATA.json").nativeHandled());
    }
    @Test void finalFactoriesRetainOriginalStageOneCoreSourceLeaseAndDeadline()throws Exception{
        var before=RiteDoctrineFrameV1PublicCodec.decodeRequestPacket(NativeWire.packet(RiteFinalCppFrames.json("confirm_edit-request.json")));
        for(var value:new RiteDoctrineFrameV1PublicCodec.Request[]{RiteDoctrineFrameV1PublicCodec.finalQuery(before),RiteDoctrineFrameV1PublicCodec.acceptFinal(before)}){
            assertEquals(before.expectedCore(),value.expectedCore());assertEquals(before.sourceRiteId(),value.sourceRiteId());assertEquals(before.lease(),value.lease());assertEquals(before.deadlineUnixMs(),value.deadlineUnixMs());
        }
        var query=RiteDoctrineFrameV1PublicCodec.decodeRequestPacket(NativeWire.packet(RiteFinalCppFrames.json("query-request.json")));
        assertThrows(IllegalArgumentException.class,()->RiteDoctrineFrameV1PublicCodec.finalQuery(query));
        assertThrows(IllegalArgumentException.class,()->RiteDoctrineFrameV1PublicCodec.action(query,RiteDoctrineFrameV1.Action.ACCEPT_FINAL_CONFIRMATION,java.time.Instant.now().plusSeconds(10),before.lease().orElseThrow()));
    }
    @Test void newActionsCannotUseOldStepOrAnImportedZeroLease()throws Exception{
        for(String file:new String[]{"query-final-request.json","accept-final-request.json"}){
            var row=NativeWire.object(NativeWire.parse(RiteFinalCppFrames.json(file)));row.put("step",RiteDoctrineFrameV1.STEP);
            assertThrows(IllegalArgumentException.class,()->RiteDoctrineFrameV1PublicCodec.decodeRequestPacket(NativeWire.packet(StrictJson.canonical(row))));
            var zero=NativeWire.object(NativeWire.parse(RiteFinalCppFrames.json(file)));NativeWire.object(zero.get("rite_doctrine")).put("provider_generation","0");assertThrows(IllegalArgumentException.class,()->RiteDoctrineFrameV1PublicCodec.decodeRequestPacket(NativeWire.packet(StrictJson.canonical(zero))));
        }
    }
    @Test void pendingIsReadonlyNotReadyAndCannotCarryAnEffectClaim()throws Exception{
        var pending=RiteFinalCppFrames.frame("final-pending-SYNTHETIC-DATA.json");assertEquals(RiteDoctrineFrameV1.Status.FINAL_CONFIRMATION_PENDING,pending.status());assertFalse(pending.nativeOk());assertFalse(pending.effectAttempted());assertEquals(BigInteger.ZERO,pending.claimSequence());
        var row=NativeWire.object(NativeWire.parse(RiteFinalCppFrames.result("final-pending-SYNTHETIC-DATA.json").bytes()));row.put("claim_sequence","1");assertThrows(IllegalArgumentException.class,()->RiteDoctrineFrameV1.decode(new RawJson(StrictJson.canonical(row))));
        var falseSource=NativeWire.object(NativeWire.parse(RiteFinalCppFrames.result("final-pending-SYNTHETIC-DATA.json").bytes()));NativeWire.object(falseSource.get("facts")).put("selected",false);assertThrows(IllegalArgumentException.class,()->RiteDoctrineFrameV1.decode(new RawJson(StrictJson.canonical(falseSource))));
    }
    @Test void voidFinalCannotInventHandledBoolOrPersistence()throws Exception{
        for(String field:new String[]{"native_handled","rite_edit_confirmed","physical_save_confirmed"}){
            var row=NativeWire.object(NativeWire.parse(RiteFinalCppFrames.result("final-dispatched-SYNTHETIC-DATA.json").bytes()));row.put(field,true);assertThrows(IllegalArgumentException.class,()->RiteDoctrineFrameV1.decode(new RawJson(StrictJson.canonical(row))));
        }
        var unknown=RiteFinalCppFrames.frame("final-incoherent-SYNTHETIC-DATA.json");assertEquals(RiteDoctrineFrameV1.Status.INDETERMINATE,unknown.status());assertFalse(unknown.nativeOk());
    }
    @Test void originalSignedActorAndCanonicalUInt64LeaseRemainExact()throws Exception{
        var request=RiteDoctrineFrameV1PublicCodec.decodeRequestPacket(NativeWire.packet(RiteFinalCppFrames.json("query-final-request.json")));assertEquals(-16777215,request.expectedCore().prefix().playedCharacterId());assertEquals(new BigInteger("18446744073709551615"),request.lease().orElseThrow().providerGeneration());
        for(String value:new String[]{"+1","01","-0","18446744073709551616"}){
            var row=NativeWire.object(NativeWire.parse(RiteFinalCppFrames.json("query-final-request.json")));NativeWire.object(row.get("rite_doctrine")).put("query_sequence",value);assertThrows(IllegalArgumentException.class,()->RiteDoctrineFrameV1PublicCodec.decodeRequestPacket(NativeWire.packet(StrictJson.canonical(row))));
        }
    }
}
