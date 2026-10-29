package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.OptionalInt;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.nativebridge.capabilities.gui.GuiCameraCapabilities;
import org.xar.ck3.control.nativebridge.capabilities.gui.NativeCameraObserver;
import org.xar.ck3.control.nativebridge.capabilities.gui.NativeCameraObserver.Capture;
import org.xar.ck3.control.nativebridge.capabilities.gui.NativeCameraObserver.DetailedCapture;
import org.xar.ck3.control.nativebridge.publicmethods.gui.GuiRealmCameraStatus;
import org.xar.ck3.control.nativebridge.publicmethods.gui.GuiRealmCameraStatus.*;

/** Actual native binary decoder -> original Service ownership/filter -> sole public DATA encoder. No Game/OS authority. */
final class GuiRealmCameraStatusTest {
    private static final float[] TARGET={1,2,3,4,5,6};
    private static Owner owner(){return new Owner(73,"camera-episode",314,BigInteger.ONE);}
    private static Submission submission(Owner owner,Mode mode) {
        return new Submission(new GuiCameraCapabilities.Binding(2,owner.actor(),1000,owner.episodeRunId()),owner,mode,
                mode==Mode.TRACKED_HOTSPOT?OptionalInt.of(2000):OptionalInt.empty());
    }
    private static byte[] result(int code,int actor,int date,float[] target,float[] current) {
        ByteBuffer b=ByteBuffer.allocate(NativeCameraObserver.RESULT_BYTES).order(ByteOrder.LITTLE_ENDIAN);
        b.putInt(2).putInt(code).putInt(actor).putInt(date).putInt(1).putInt(1280).putInt(720).putInt(3);
        b.putInt(1).putInt(2).putInt(30).putInt(40);
        for(float value:target)b.putFloat(value);for(float value:current)b.putFloat(value);
        b.putInt(456).putInt(0).putInt(42);return b.array();
    }
    private static byte[] tail(int reason,int flags,int mask) {
        ByteBuffer b=ByteBuffer.allocate(168).order(ByteOrder.LITTLE_ENDIAN);
        b.putInt(0x44434158).putInt(1).putInt(168).putInt(2).putInt(7).putInt(reason).putInt(314).putInt(73);
        b.putInt(1024).putInt(1000).putInt(1).putInt(flags).putInt(mask).putInt(1).putInt(1280).putInt(720).putInt(3);
        b.putInt(1).putInt(2).putInt(30).putInt(40);
        for(float value:TARGET)b.putFloat(value);
        for(float value:TARGET)b.putFloat(value);
        for(int i=0;i<6;i++)b.putFloat(reason==4&&i==0?8:TARGET[i]);
        b.putInt(0).putLong(-1L);assertEquals(168,b.position());return b.array();
    }
    private static DetailedCapture capture(byte[] raw,byte[] tail) {
        return new DetailedCapture(new Capture("explicit-software-camera-test",314,"camera-session",4,Instant.parse("2026-10-24T03:00:00Z"),
                NativeCameraObserver.decodeResult(raw),raw),tail);
    }
    private static StatusData project(Submission submission,byte[] raw,byte[] tail) {
        return GuiRealmCameraStatus.project(true,submission.owner(),Optional.of(submission),Optional.of(capture(raw,tail)));
    }
    private static com.fasterxml.jackson.databind.node.ObjectNode json(StatusData result){return PublicDataJson.object(GuiRealmCameraStatus.encode(result));}

    @Test void originalAbsentClientAndUnsubmittedClientRemainDistinctWithoutOpeningAnyMapping()throws Exception {
        var none=GuiRealmCameraStatus.query(Optional.empty(),owner(),Optional.empty());
        var wire=json(none);assertEquals("not_requested",wire.get("status").textValue());
        assertTrue(wire.get("requested_sequence").isNull());assertTrue(wire.get("native_actual").isNull());
        var installed=GuiRealmCameraStatus.project(true,owner(),Optional.empty(),Optional.empty());
        assertEquals("available",json(installed).get("status").textValue());
        assertFalse(json(installed).get("same_frame_with_gameplay_claim").booleanValue());
    }
    @Test void actualDecodedResultRetainsAllOriginalPublicFieldsAndUnavailableOptionalTail() {
        var state=project(submission(owner(),Mode.REALM),result(1,73,1024,TARGET,TARGET),new byte[168]);
        var wire=json(state);assertEquals(2,wire.get("requested_sequence").intValue());var actual=wire.get("native_actual");
        assertEquals("submitted",actual.get("status").textValue());assertEquals(73,actual.get("actor_character_id").intValue());
        assertEquals(1024,actual.get("date_raw").intValue());assertEquals(1,actual.get("county_count").intValue());
        assertEquals(42,actual.get("county_title_ids").get(0).intValue());assertEquals(4,actual.get("bounds").size());
        assertEquals(1280,actual.get("client_size").get(0).intValue());assertEquals(720,actual.get("client_size").get(1).intValue());
        assertEquals(3,actual.get("zoom_index").intValue());assertEquals(6,actual.get("target").size());assertEquals(6,actual.get("current").size());
        assertEquals(456,actual.get("native_elapsed_us").intValue());assertFalse(actual.get("coverage_verified").booleanValue());
        assertFalse(actual.get("camera_postcondition_verified").booleanValue());assertFalse(actual.get("same_frame_with_gameplay_claim").booleanValue());
        assertEquals("native_bucket_with_viewport_padding",actual.get("fit_model").textValue());
        assertEquals("legacy_or_absent_extension",actual.get("settle_diagnostics").get("reason").textValue());
        assertEquals(wire,PublicDataJson.object(GuiRealmCameraStatus.encode(state)));
    }
    @Test void originalOwnerSequenceActorAndSevenDayProcessingWindowRejectStaleTail() {
        var original=submission(owner(),Mode.REALM);var good=capture(result(8,73,1168,TARGET,TARGET),new byte[168]);
        assertTrue(GuiRealmCameraStatus.project(true,owner(),Optional.of(original),Optional.of(good)).nativeActual().isPresent());
        for(Owner changed:List.of(new Owner(74,"camera-episode",314,BigInteger.ONE),new Owner(73,"other",314,BigInteger.ONE),
                new Owner(73,"camera-episode",315,BigInteger.ONE),new Owner(73,"camera-episode",314,BigInteger.TWO)))
            assertTrue(GuiRealmCameraStatus.project(true,changed,Optional.of(original),Optional.of(good)).nativeActual().isEmpty());
        for(int date:List.of(999,1169))assertTrue(project(original,result(8,73,date,TARGET,TARGET),new byte[168]).nativeActual().isEmpty());
        assertTrue(project(original,result(8,74,1024,TARGET,TARGET),new byte[168]).nativeActual().isEmpty());
        byte[] wrong=result(8,73,1024,TARGET,TARGET);ByteBuffer.wrap(wrong).order(ByteOrder.LITTLE_ENDIAN).putInt(0,4);
        assertTrue(project(original,wrong,new byte[168]).nativeActual().isEmpty());
    }
    @Test void identicalSubmissionLatchesNativeTargetAndSettledRequiresActualCurrentEquality() {
        var original=submission(owner(),Mode.REALM);
        assertTrue(project(original,result(1,73,1000,TARGET,TARGET),new byte[168]).nativeActual().isPresent());
        float[] changed=TARGET.clone();changed[0]=8;
        assertTrue(project(original,result(1,73,1024,changed,changed),new byte[168]).nativeActual().isEmpty());
        assertTrue(project(original,result(2,73,1024,TARGET,changed),new byte[168]).nativeActual().isEmpty());
        var settled=json(project(original,result(2,73,1024,TARGET,TARGET),new byte[168]));
        assertTrue(settled.get("native_actual").get("camera_postcondition_verified").booleanValue());
        assertFalse(settled.get("native_actual").get("coverage_verified").booleanValue());
        float[] plusZero=TARGET.clone(),minusZero=TARGET.clone();plusZero[0]=0.0f;minusZero[0]=-0.0f;
        var zeros=submission(owner(),Mode.REALM);
        assertTrue(project(zeros,result(1,73,1000,plusZero,plusZero),new byte[168]).nativeActual().isPresent());
        assertTrue(project(zeros,result(2,73,1024,minusZero,plusZero),new byte[168]).nativeActual().isPresent());
    }
    @Test void cancelIsBoundBeforeNativeGameFrameAndLegacyResultCannotPretendToBeTracking() {
        var cancelled=project(submission(owner(),Mode.CANCEL),result(3,0,0,TARGET,TARGET),new byte[168]);
        assertEquals("cancelled",json(cancelled).get("native_actual").get("status").textValue());
        assertFalse(json(cancelled).get("native_actual").get("camera_postcondition_verified").booleanValue());
        var tracked=project(submission(owner(),Mode.TRACKED_HOTSPOT),result(2,73,1024,TARGET,TARGET),new byte[168]);
        assertTrue(tracked.nativeActual().isEmpty());assertEquals("available",json(tracked).get("status").textValue());
        assertThrows(IllegalArgumentException.class,()->new Submission(new GuiCameraCapabilities.Binding(2,73,1000,"camera-episode"),owner(),Mode.TRACKED_HOTSPOT,OptionalInt.empty()));
    }
    @Test void actualOptionalDiagnosticReasonAndGeometryFlowToTypedPublicJsonWithoutLosingUint64() {
        Owner precise=new Owner(73,"camera-episode",314,new BigInteger("18446744073709551615"));
        var state=project(submission(precise,Mode.REALM),result(7,73,1024,TARGET,TARGET),tail(4,15,1));
        var diag=json(state).get("native_actual").get("settle_diagnostics");assertTrue(diag.get("available").booleanValue());
        assertEquals("target_changed",diag.get("reason").textValue());assertEquals("18446744073709551615",diag.get("observation_uptime_ms").textValue());
        assertEquals("18446744073709551615",diag.get("request_source_frame").get("connection_generation").textValue());
        assertTrue(diag.get("provider").get("game_creation_filetime").isNull());assertTrue(diag.get("observation_game_frame").isNull());
        assertEquals(1,diag.get("target_difference_mask").intValue());assertEquals(6,diag.get("observed_target_float_bits").size());
        assertEquals(8,diag.get("observed_target").get(0).intValue());assertFalse(diag.get("camera_postcondition_verified").booleanValue());
        assertFalse(diag.get("coverage_verified").booleanValue());assertFalse(diag.get("same_frame_with_gameplay_claim").booleanValue());
    }
    @Test void diagnosticNaNPreservesOriginalBitsAsJsonNullAndDoesNotRepairNativeFailure() {
        byte[] tail=tail(3,11,0);ByteBuffer.wrap(tail).order(ByteOrder.LITTLE_ENDIAN).putInt(108,0x7fc01234);
        var state=project(submission(owner(),Mode.REALM),result(7,73,1024,TARGET,TARGET),tail);
        var diag=json(state).get("native_actual").get("settle_diagnostics");assertTrue(diag.get("available").booleanValue());
        assertEquals("current_nonfinite",diag.get("reason").textValue());assertTrue(diag.get("observed_current").get(0).isNull());
        assertEquals(Integer.toUnsignedLong(0x7fc01234),diag.get("observed_current_float_bits").get(0).longValue());
        assertFalse(diag.get("current_finite").booleanValue());assertFalse(diag.get("camera_postcondition_verified").booleanValue());
    }
    @Test void malformedOptionalTailFailsOnlyDiagnosticsAndCannotBorrowAnotherRequestGeometryOrFlags() {
        int[] offsets={0,4,8,12,16,24,28,32,36,40,44,48,52,56,60,64,68,84,156};
        for(int offset:offsets) {
            byte[] bad=tail(4,15,1);ByteBuffer bytes=ByteBuffer.wrap(bad).order(ByteOrder.LITTLE_ENDIAN);
            bytes.putInt(offset,bytes.getInt(offset)^0x40000000);
            var state=project(submission(owner(),Mode.REALM),result(7,73,1024,TARGET,TARGET),bad);
            assertTrue(state.nativeActual().isPresent(),"legacy actual is still observed at offset "+offset);
            assertFalse(json(state).get("native_actual").get("settle_diagnostics").get("available").booleanValue(),"offset "+offset);
        }
    }
    @Test void publicDataCannotReplaceOriginalResultAndDetailedCaptureOwnsItsActualByteCopies() {
        byte[] raw=result(1,73,1024,TARGET,TARGET),tail=new byte[168];DetailedCapture actual=capture(raw,tail);
        raw[0]=9;tail[0]=1;assertEquals(2,actual.base().originalResult()[0]);assertEquals(0,actual.originalDiagnostics()[0]);
        byte[] returned=actual.originalDiagnostics();returned[0]=1;assertEquals(0,actual.originalDiagnostics()[0]);
        byte[] changed=result(1,74,1024,TARGET,TARGET);
        var forged=new DetailedCapture(new Capture(actual.base().machineId(),actual.base().gamePid(),actual.base().sessionId(),actual.base().resultSequence(),
                actual.base().observedAt(),NativeCameraObserver.decodeResult(changed),actual.base().originalResult()),new byte[168]);
        assertThrows(IllegalArgumentException.class,()->GuiRealmCameraStatus.project(true,owner(),Optional.of(submission(owner(),Mode.REALM)),Optional.of(forged)));
        assertThrows(IllegalArgumentException.class,()->NativeCameraObserver.decodeResult(new byte[4]));
        byte[] nonfinite=result(1,73,1024,TARGET,TARGET);ByteBuffer.wrap(nonfinite).order(ByteOrder.LITTLE_ENDIAN).putInt(48,0x7f800000);
        assertThrows(IllegalArgumentException.class,()->NativeCameraObserver.decodeResult(nonfinite));
    }
}
