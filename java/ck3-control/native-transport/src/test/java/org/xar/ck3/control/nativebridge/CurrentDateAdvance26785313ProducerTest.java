package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.DateAdvanceFrameV1;
import org.xar.ck3.control.nativebridge.capabilities.registry.DateAdvanceFrameV1PublicCodec;

final class CurrentDateAdvance26785313ProducerTest {
    @Test void actualCppRequestsRoundtripAndQueryPreservesOriginalBodyAndDeadline()throws Exception {
        for(String name:new String[]{"request-advance-v1","request-status-v1"}) {
            var raw=NativeWire.packet(CurrentDateCppFrames.bytes(name));var envelope=NativeWire.decodeExecuteRequest(raw);
            var request=DateAdvanceFrameV1PublicCodec.decodeRequestPacket(raw);
            byte[] encoded=NativeWire.execute(envelope.requestId(),request.step().wire(),BigInteger.ZERO,DateAdvanceFrameV1PublicCodec.additionalFields(request).bytes());
            assertEquals(request,DateAdvanceFrameV1PublicCodec.decodeRequestPacket(encoded));
            var lookup=DateAdvanceFrameV1PublicCodec.query(request);assertEquals(request.expectedCore(),lookup.expectedCore());
            assertEquals(request.deadlineUnixMs(),lookup.deadlineUnixMs());assertEquals(request.operationId(),lookup.operationId());
        }
        var old=DateAdvanceFrameV1PublicCodec.action(CurrentDateCppFrames.core(),Instant.ofEpochMilli(1),"original-expired-data");
        assertEquals(BigInteger.ONE,DateAdvanceFrameV1PublicCodec.query(old).deadlineUnixMs());
    }
    @Test void actualFourCppResultsRoundtripWithoutInventedAfterCoreOrSave()throws Exception {
        for(String name:new String[]{"submitted-SYNTHETIC-DATA","completed-SYNTHETIC-DATA","indeterminate-SYNTHETIC-DATA","unavailable-NoGame"}) {
            var original=CurrentDateCppFrames.response(name);var frame=DateAdvanceFrameV1PublicCodec.decodePacket(new RawJson(original.payload().value()),original.requestId());
            assertEquals(frame,DateAdvanceFrameV1.decode(DateAdvanceFrameV1PublicCodec.encode(frame)));
            var encoded=StrictJson.parse(DateAdvanceFrameV1PublicCodec.encode(frame).bytes());assertTrue(encoded.get("core_after").isNull());
            assertFalse(encoded.get("complete_snapshot").booleanValue());assertFalse(encoded.get("physical_save_confirmed").booleanValue());
        }
    }
    @Test void completedNeedsExactOriginalGenerationOneTickPauseAndCleanDisarm()throws Exception {
        var raw=CurrentDateCppFrames.result("completed-SYNTHETIC-DATA");
        for(String field:new String[]{"exact_day_confirmed","shutdown_safe","owner_before_verified"}) {
            var row=NativeWire.object(StrictJson.parse(raw.bytes()));row.put(field,false);assertThrows(IllegalArgumentException.class,()->DateAdvanceFrameV1.decode(new RawJson(StrictJson.canonical(row))));
        }
        for(String field:new String[]{"armed","access_cleanup_unknown"}) {
            var row=NativeWire.object(StrictJson.parse(raw.bytes()));row.put(field,true);assertThrows(IllegalArgumentException.class,()->DateAdvanceFrameV1.decode(new RawJson(StrictJson.canonical(row))));
        }
        for(String field:new String[]{"target_date_raw","last_observed_date_raw","trigger_date_raw","completed_daily_ticks","trigger_flags"}) {
            var row=NativeWire.object(StrictJson.parse(raw.bytes()));var sentinel=NativeWire.object(row.get("sentinel"));sentinel.put(field,sentinel.get(field).longValue()+1);
            assertThrows(IllegalArgumentException.class,()->DateAdvanceFrameV1.decode(new RawJson(StrictJson.canonical(row))),field);
        }
    }
    @Test void completedRejectsOwnerEpochMutationNumericUint64AndSyntheticAfterCore()throws Exception {
        var original=CurrentDateCppFrames.result("completed-SYNTHETIC-DATA");
        for(String token:new String[]{"0","-1","+1","01","18446744073709551616"}) {
            var row=NativeWire.object(StrictJson.parse(original.bytes()));row.put("generation",token);
            assertThrows(IllegalArgumentException.class,()->DateAdvanceFrameV1.decode(new RawJson(StrictJson.canonical(row))));
        }
        var row=NativeWire.object(StrictJson.parse(original.bytes()));row.put("generation",1);assertThrows(IllegalArgumentException.class,()->DateAdvanceFrameV1.decode(new RawJson(StrictJson.canonical(row))));
        var after=NativeWire.object(StrictJson.parse(original.bytes()));after.set("core_after",after.get("core_before"));assertThrows(IllegalArgumentException.class,()->DateAdvanceFrameV1.decode(new RawJson(StrictJson.canonical(after))));
    }
    @Test void requestRejectsWrongTupleUnpausedCoreBoolDeadlineAndAdditionalClaims()throws Exception {
        byte[] raw=CurrentDateCppFrames.bytes("request-advance-v1");
        for(String field:new String[]{"paused","map_ready","played_character_alive"}) {
            var row=NativeWire.object(StrictJson.parse(raw));NativeWire.object(row.get("date_advance").get("expected_core")).put(field,false);
            assertThrows(IllegalArgumentException.class,()->DateAdvanceFrameV1PublicCodec.decodeRequestPacket(NativeWire.packet(StrictJson.canonical(row))));
        }
        var row=NativeWire.object(StrictJson.parse(raw));NativeWire.object(row.get("date_advance")).put("deadline_unix_ms",true);assertThrows(IllegalArgumentException.class,()->DateAdvanceFrameV1PublicCodec.decodeRequestPacket(NativeWire.packet(StrictJson.canonical(row))));
        var wrong=NativeWire.object(StrictJson.parse(raw));NativeWire.object(wrong.get("date_advance")).put("game_version","1.20.0.4");assertThrows(IllegalArgumentException.class,()->DateAdvanceFrameV1PublicCodec.decodeRequestPacket(NativeWire.packet(StrictJson.canonical(wrong))));
        var extra=NativeWire.object(StrictJson.parse(raw));extra.put("core_control_deadline_unix_ms",123);assertThrows(IllegalArgumentException.class,()->DateAdvanceFrameV1PublicCodec.decodeRequestPacket(NativeWire.packet(StrictJson.canonical(extra))));
    }
    @Test void queryClaimFoundIsNotActionAcceptanceAndUnknownDoesNotBecomeCompleted()throws Exception {
        var completed=DateAdvanceFrameV1.decode(CurrentDateCppFrames.result("completed-SYNTHETIC-DATA"));assertFalse(completed.accepted());assertTrue(completed.nativeOk());
        var unknown=DateAdvanceFrameV1.decode(CurrentDateCppFrames.result("indeterminate-SYNTHETIC-DATA"));assertEquals(DateAdvanceFrameV1.Status.INDETERMINATE,unknown.status());assertFalse(unknown.exactDayConfirmed());
        var row=NativeWire.object(StrictJson.parse(CurrentDateCppFrames.result("completed-SYNTHETIC-DATA").bytes()));row.put("accepted",true);assertThrows(IllegalArgumentException.class,()->DateAdvanceFrameV1.decode(new RawJson(StrictJson.canonical(row))));
    }
}
