package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigInteger;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

final class FullSnapshotGuiControlTest {
    private static final BigInteger REVISION = new BigInteger("9007199254740993");
    private static final Instant DEADLINE = Instant.parse("2026-11-18T13:00:00Z");

    @Test void queryCarriesExactFullOriginalDeadlineAndZeroObservationIds() {
        var request = FullSnapshotGuiControl.query("native:" + REVISION, REVISION, DEADLINE, "xfm_market_entry");
        var root = StrictJson.parse(request.additionalFields().bytes());
        var claim = root.get("gui_control_v1");
        assertEquals(FullSnapshotGuiControl.QUERY_STEP, request.step());
        assertEquals(11, claim.size());
        assertEquals(REVISION, claim.get("native_revision").bigIntegerValue());
        assertEquals(DEADLINE.toEpochMilli(), claim.get("deadline_unix_ms").longValue());
        assertEquals("0", claim.get("query_generation").textValue());
        assertEquals("0", claim.get("widget_id").textValue());
        assertEquals("xfm_market_entry", claim.get("root_name").textValue());
        assertTrue(root.get("arguments").isObject());
        assertEquals(0, root.get("arguments").size());
    }

    @Test void activationKeepsUint64IdsAsCanonicalDecimalStrings() {
        var maximum = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
        var request = FullSnapshotGuiControl.activate("native:" + REVISION, REVISION, DEADLINE,
                "xfm_market_window", REVISION, maximum);
        var claim = StrictJson.parse(request.additionalFields().bytes()).get("gui_control_v1");
        assertEquals(FullSnapshotGuiControl.ACTIVATE_STEP, request.step());
        assertEquals(REVISION.toString(), claim.get("query_generation").textValue());
        assertEquals(maximum.toString(), claim.get("widget_id").textValue());
    }

    @Test void rejectsUnboundFullInjectionAndInvalidObservationIds() {
        assertThrows(IllegalArgumentException.class, () -> FullSnapshotGuiControl.query("native:1", REVISION, DEADLINE, "xfm_market_entry"));
        for (String name : new String[] { "", "../xfm_market", "xfm_market' ).Execute( ", "a\nb", "x".repeat(129) })
            assertThrows(IllegalArgumentException.class, () -> FullSnapshotGuiControl.query("native:" + REVISION, REVISION, DEADLINE, name));
        for (BigInteger value : new BigInteger[] { BigInteger.ZERO, BigInteger.ONE.negate(), BigInteger.ONE.shiftLeft(64) })
            assertThrows(IllegalArgumentException.class, () -> FullSnapshotGuiControl.activate("native:" + REVISION, REVISION, DEADLINE,
                    "xfm_market_window", value, BigInteger.ONE));
        assertThrows(IllegalArgumentException.class, () -> FullSnapshotGuiControl.query("native:" + REVISION, REVISION,
                Instant.EPOCH, "xfm_market_entry"));
    }
}
