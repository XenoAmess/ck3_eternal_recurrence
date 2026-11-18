package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.application.advance.PreparedCleanupEvidence;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.LateOutcome.State;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.SentinelObservation;

/** Real Native34 packets and explicit negative DATA only. No Root role, permit, custody, Full or second actual READ is made. */
final class PreparedCleanupCancellation1210Test {
    private static final String BUILD=ExactCk3Build.CK3_1210.executableSha256();
    private static final String STEP=ClockStatusRead.CANCEL_PREFIX+"1";
    private record Original(byte[] json,byte[] packet,NativeActionPort.AckReceived ack) { }

    @Test void realArmedControlCancellationRetainsAllFieldsAndUnpausedWrapperFlag() throws Exception {
        var originals=originals();var cancel=originals.get("cancel-result");
        var actual=PreparedCleanupEvidence.acknowledgedCancellation(BUILD,cancel.ack(),STEP).orElseThrow();
        var before=ClockStatusRead.decode(originals.get("before-status").ack());
        var after=ClockStatusRead.decode(originals.get("independent-after-status").ack());
        assertEquals(State.ARMED,before.state());assertEquals(State.IDLE,actual.state());assertEquals(after,actual);
        assertEquals(0,actual.armyCount());assertEquals(0,actual.completedDailyTicks());
        assertFalse(actual.pauseObserved());assertFalse(actual.pauseWrapperCalled());assertFalse(actual.abnormal());
        assertArrayEquals(cancel.json(),cancel.ack().originalFrame().bytes());assertArrayEquals(cancel.packet(),cancel.ack().originalPacket());
        assertTrue(cancel.ack().custody().isEmpty());assertTrue(cancel.ack().outbound().isEmpty());
        // Equality DATA does not claim that Native34 made the full prepared-cleanup two-READ/Full chain.
        assertDoesNotThrow(()->PreparedCleanupEvidence.requireIndependentCancellationStatuses(Optional.of(actual),after,after));
    }
    @Test void exactHelloTriplesKeepBothLegacyProfilesAndRejectMixedSources() {
        var rows=List.of(new String[]{"1.19.0.6","2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"},
                new String[]{"1.20.0.4",ExactCk3Build.CK3_12004.executableSha256()},new String[]{"1.21.0",BUILD});
        for(var row:rows) {
            String adapter="ck3-"+row[0]+"-msvc-x64";
            assertTrue(PreparedCleanupEvidence.supportsCancellationHello(adapter,row[0],row[1].toUpperCase(Locale.ROOT)));
            assertFalse(PreparedCleanupEvidence.supportsCancellationHello(adapter,row[0]+".0",row[1]));
            assertFalse(PreparedCleanupEvidence.supportsCancellationHello(adapter+"-alias",row[0],row[1]));
            assertFalse(PreparedCleanupEvidence.supportsCancellationHello(adapter,row[0],"0".repeat(64)));
            assertFalse(PreparedCleanupEvidence.supportsCancellationHello(adapter,null,row[1]));
            assertFalse(PreparedCleanupEvidence.supportsCancellationHello(adapter,row[0],null));
            for(var other:rows)if(!other[0].equals(row[0]))assertFalse(PreparedCleanupEvidence.supportsCancellationHello(adapter,other[0],other[1]));
        }
    }
    @Test void legacyCanceledShapeAndFlorinAvailableShapeCannotBeSubstituted() throws Exception {
        ObjectNode legacy=StrictJson.object();legacy.put("step",STEP).put("accepted",true).put("status","canceled");
        for(String sha:List.of(ExactCk3Build.CK3_12004.executableSha256(),"2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86")) {
            assertEquals(Optional.empty(),PreparedCleanupEvidence.acknowledgedCancellation(sha,data(legacy),STEP));
            assertThrows(RuntimeException.class,()->PreparedCleanupEvidence.acknowledgedCancellation(sha,originals().get("cancel-result").ack(),STEP));
            ObjectNode extra=legacy.deepCopy();extra.put("available",true);
            assertThrows(RuntimeException.class,()->PreparedCleanupEvidence.acknowledgedCancellation(sha,data(extra),STEP));
        }
        assertThrows(RuntimeException.class,()->PreparedCleanupEvidence.acknowledgedCancellation(BUILD,data(legacy),STEP));
    }
    @Test void availableAckRejectsAddedMissingNullWrongTypedAndConflictingOriginalFields() throws Exception {
        var original=originals().get("cancel-result");ObjectNode token=(ObjectNode)StrictJson.parse(original.ack().originalResultToken().orElseThrow().bytes());
        for(String field:List.of("step","accepted","status","tactical_daily_sentinel")) {
            ObjectNode missing=token.deepCopy();missing.remove(field);
            assertThrows(RuntimeException.class,()->PreparedCleanupEvidence.acknowledgedCancellation(BUILD,data(missing),STEP));
            ObjectNode nulled=token.deepCopy();nulled.putNull(field);
            assertThrows(RuntimeException.class,()->PreparedCleanupEvidence.acknowledgedCancellation(BUILD,data(nulled),STEP));
        }
        ObjectNode extra=token.deepCopy();extra.put("canceled",true);rejected(extra);
        ObjectNode unknown=token.deepCopy();unknown.put("status","unavailable");rejected(unknown);
        ObjectNode wrongStep=token.deepCopy();wrongStep.put("step",ClockStatusRead.CANCEL_PREFIX+"2");rejected(wrongStep);
        ObjectNode accepted=token.deepCopy();accepted.put("accepted","true");rejected(accepted);
        ObjectNode declined=token.deepCopy();declined.put("accepted",false);rejected(declined);
        ObjectNode sentinel=token.deepCopy();sentinel.withObject("/tactical_daily_sentinel").put("extra",0);rejected(sentinel);
        var wrongId=new NativeActionPort.AckReceived("different-native-id",true,original.ack().originalResultToken(),
                original.ack().originalFrame(),original.packet());
        assertThrows(RuntimeException.class,()->PreparedCleanupEvidence.acknowledgedCancellation(BUILD,wrongId,STEP));
        ObjectNode frame=(ObjectNode)StrictJson.parse(original.json());frame.withObject("/result").put("status","unavailable");
        var conflicting=new NativeActionPort.AckReceived(original.ack().requestId(),true,original.ack().originalResultToken(),
                new RawJson(StrictJson.canonical(frame)),original.packet());
        assertThrows(RuntimeException.class,()->PreparedCleanupEvidence.acknowledgedCancellation(BUILD,conflicting,STEP));
    }
    @Test void bothIndependentStatusesMustMatchEveryOneOfTheTwentyAcknowledgedFields() throws Exception {
        var actual=PreparedCleanupEvidence.acknowledgedCancellation(BUILD,originals().get("cancel-result").ack(),STEP).orElseThrow();
        var token=SentinelObservation.toJson(actual);assertEquals(20,token.size());
        for(var names=token.fieldNames();names.hasNext();) {
            String field=names.next();ObjectNode changed=token.deepCopy();
            switch(field) {
                case "state" -> changed.put(field,"armed");
                case "mode" -> changed.put(field,"decision_epoch");
                case "abnormal" -> {changed.put(field,true);changed.put("state","failed");}
                case "trigger_flags","trigger_reasons" -> {changed.put("trigger_flags",1);changed.putArray("trigger_reasons").add("date_deadline");}
                case "terminal_observed" -> {changed.put(field,true);changed.put("trigger_flags",256);changed.putArray("trigger_reasons").add("combat_terminal");}
                case "pause_observed","pause_wrapper_called" -> changed.put(field,true);
                case "speed" -> changed.put(field,4);
                default -> changed.put(field,token.get(field).bigIntegerValue().add(java.math.BigInteger.ONE));
            }
            assertNotEquals(token.get(field),changed.get(field),field);
            var other=SentinelObservation.decode(changed);assertNotEquals(actual,other,field);
            assertThrows(RuntimeException.class,()->PreparedCleanupEvidence.requireIndependentCancellationStatuses(Optional.of(actual),other,actual),field+" first");
            assertThrows(RuntimeException.class,()->PreparedCleanupEvidence.requireIndependentCancellationStatuses(Optional.of(actual),actual,other),field+" second");
        }
    }
    @Test void florinCannotAuthorizePositiveArmyDecisionOrTerminalPassthroughSlots() throws Exception {
        var original=originals().get("cancel-result");ObjectNode token=(ObjectNode)StrictJson.parse(original.ack().originalResultToken().orElseThrow().bytes());
        for(String field:List.of("army_count","mode","state")) {
            ObjectNode changed=token.deepCopy();ObjectNode status=changed.withObject("/tactical_daily_sentinel");
            if(field.equals("army_count"))status.put(field,1);else status.put(field,field.equals("mode")?"decision_epoch":"triggered");
            rejected(changed);
            var typed=SentinelObservation.decode(status);
            if(!field.equals("state")) {
                assertThrows(RuntimeException.class,()->PreparedCleanupEvidence.requireSupportedCancellationSlot(BUILD,typed));
                assertDoesNotThrow(()->PreparedCleanupEvidence.requireSupportedCancellationSlot(ExactCk3Build.CK3_12004.executableSha256(),typed));
            }
        }
    }
    private static void rejected(ObjectNode token) {
        assertThrows(RuntimeException.class,()->PreparedCleanupEvidence.acknowledgedCancellation(BUILD,data(token),STEP));
    }
    private static NativeActionPort.AckReceived data(ObjectNode token) throws IOException {
        ObjectNode frame=StrictJson.object();frame.put("type","command_result").put("protocol_version",1).put("request_id","negative-data").put("ok",true);frame.set("result",token);
        byte[] raw=StrictJson.canonical(frame);
        return new NativeActionPort.AckReceived("negative-data",true,Optional.of(new RawJson(StrictJson.canonical(token))),new RawJson(raw),NativeWire.packet(raw));
    }
    private static Map<String,Original> originals() throws Exception {
        String configured=System.getProperty("xar.native.preparedCleanup1210.receipt");
        String digest=System.getProperty("xar.native.preparedCleanup1210.receiptSha256");
        if(configured==null||digest==null)throw new IOException("required actual Native34 receipt and SHA properties are absent");
        Path path=Path.of(configured);assertTrue(path.isAbsolute());byte[] readyBytes=small(path);
        assertEquals(digest,ActionCodec.sha256(readyBytes));JsonNode ready=StrictJson.parse(readyBytes);
        assertEquals("xar.native.armed-cancel-software-ready34/v1",ready.path("schema").textValue());
        assertEquals(0,ready.path("result").path("execute_exit").intValue());
        assertFalse(ready.path("result").path("terminal_shortcut_before_cancel").booleanValue());
        assertTrue(ready.path("result").path("actual_control_effect_attempted").booleanValue());
        JsonNode actual=StrictJson.parse(pinned(ready.get("actual")));
        assertEquals("xar.native.actual-armed-cancel-control34/v1",actual.path("schema").textValue());
        assertTrue(actual.path("accepted").booleanValue());assertFalse(actual.path("live").booleanValue());
        Map<String,Original> result=new HashMap<>();assertEquals(3,actual.path("outputs").size());
        for(JsonNode row:actual.path("outputs")) {
            byte[] json=pinned(row.get("json")),packet=pinned(row.get("packet"));
            var decoded=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(packet));
            assertArrayEquals(json,decoded.payload().value());assertTrue(decoded.nativeOk());
            assertEquals(row.path("request_id").textValue(),decoded.requestId());
            byte[] token=decoded.result().token().orElseThrow().value();
            assertEquals(row.path("step").textValue(),StrictJson.parse(token).path("step").textValue());
            var ack=new NativeActionPort.AckReceived(decoded.requestId(),decoded.nativeOk(),Optional.of(new RawJson(token)),new RawJson(json),packet);
            assertNull(result.put(row.path("role").textValue(),new Original(json,packet,ack)));
        }
        assertEquals(java.util.Set.of("before-status","cancel-result","independent-after-status"),result.keySet());
        pinned(actual.get("actual_sequence"));return Map.copyOf(result);
    }
    private static byte[] pinned(JsonNode pin) throws Exception {
        Path path=Path.of(pin.path("path").textValue());assertTrue(path.isAbsolute());byte[] bytes=small(path);
        assertEquals(pin.path("bytes").longValue(),bytes.length);assertEquals(pin.path("sha256").textValue(),ActionCodec.sha256(bytes));return bytes;
    }
    private static byte[] small(Path path) throws IOException {
        long bytes=Files.size(path);if(bytes<1||bytes>65536)throw new IOException("bounded cold metadata/packet required");
        try(var in=Files.newInputStream(path)) {
            byte[] raw=in.readNBytes(65537);if(raw.length!=bytes||raw.length>65536)throw new IOException("captured original size changed");return raw;
        }
    }
}
