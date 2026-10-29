package org.xar.ck3.control.wave2.governance.succession;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.governance.succession.NativeTimelineBlocker12004.*;
import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider;
import org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004.Frame;

/** Required native-producer CI edge. Missing Root-produced fixture fails; it is never a skipped success. */
final class NativeTimelineBlocker12004NativeIT {
    @Test void actual4WholeNativeProducerPreservesNoModalAckPendingAndIndependentClearance() throws Exception {
        String configured = System.getProperty("xar.m3.timeline.nativeWhole");
        String expectedSha = System.getProperty("xar.m3.timeline.nativeWholeSha256");
        assertNotNull(configured, "Root must produce xar_ck3_death_succession_modal_whole_fixture_12004 and pass its original output path");
        assertNotNull(expectedSha, "Root must bind the exact original native fixture SHA rather than a replacement body");
        Path source = Path.of(configured); long size = Files.size(source);
        assertTrue(size > 0 && size <= MAX_BYTES, "finite original native fixture required");
        byte[] raw = Files.readAllBytes(source);
        assertEquals(size, raw.length); assertEquals(expectedSha, G2RetainedNativeSourceProvider.sha256(raw));
        JsonNode fixture = StrictJson.parse(raw, MAX_BYTES);
        assertEquals("xar.death-succession-12004.whole-fixture.v1", StrictJson.text(fixture.get("schema")));
        assertEquals("GREEN", StrictJson.text(fixture.get("status"))); StrictJson.trueValue(fixture.get("synthetic"));
        StrictJson.integer(fixture.get("live_queries"), 0, 0); StrictJson.integer(fixture.get("game_actions"), 0, 0);
        assertEquals("1.20.0.4", StrictJson.text(fixture.path("build").get("version")));
        assertEquals(NativePlayerHeirObservation12004.EXE_SHA256, StrictJson.text(fixture.path("build").get("exe_sha256")));
        BigInteger revision = StrictJson.integer(fixture.get("snapshot_revision"), BigInteger.ONE, StrictJson.UINT64_MAX);
        int date = (int) StrictJson.integer(fixture.get("date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE);
        int actor = (int) StrictJson.integer(fixture.get("played_character_id"), 1, Integer.MAX_VALUE);
        Frame frame = new Frame("synthetic-whole-native", revision, revision, date, actor, 0);
        Context noModal = parseContext(fixture.get("no_modal"), frame);
        Context modal = parseContext(fixture.get("modal"), frame);
        Context afterAck = parseContext(fixture.get("after_ack"), frame);
        Context cleared = parseContext(fixture.get("cleared"), frame);
        assertTrue(noModal.clearedObserved()); assertInstanceOf(Unknown.class, noModal.canContinue());
        assertTrue(modal.supportedCloseObserved()); assertTrue(afterAck.supportedCloseObserved());
        assertFalse(afterAck.clearedObserved(), "the actual native fixture deliberately leaves the modal open after Close returns");
        assertTrue(cleared.clearedObserved()); assertEquals(noModal, cleared);
        assertEquals(modal, parseContext(StrictJson.parse(encodeContext(modal)), frame));
        JsonNode ack = fixture.get("close_receipt");
        assertEquals("submitted", StrictJson.text(ack.get("status")));
        StrictJson.integer(ack.get("close_invocations"), 1, 1);
        assertTrue(ack.get("material_result_verified").isBoolean());
        assertFalse(ack.get("material_result_verified").booleanValue());
        // This context producer fixture does not contain Bridge.cpp command_result envelopes or a Game continuation.
        // Those actual transport, natural-death, estate, goal and SAVE edges require their separate Root originals.
    }
}
