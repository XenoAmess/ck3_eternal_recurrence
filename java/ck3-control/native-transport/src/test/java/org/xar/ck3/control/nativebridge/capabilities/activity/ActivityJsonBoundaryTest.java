package org.xar.ck3.control.nativebridge.capabilities.activity;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual leaf entry/serialization uses the shared explicit cap; an invalid larger limit rejects even tiny input. */
final class ActivityJsonBoundaryTest {
    @Test void actualParseAppAndRawAllRoundTripInsideTheSharedOneMiBContract() {
        byte[] original="{\"snapshot_revision\":7,\"date_raw\":42,\"actor_character_id\":29829}".getBytes(StandardCharsets.UTF_8);
        var actual=ActivityJson.parse(original);
        assertEquals(actual,StrictJson.parse(ActivityJson.raw(actual).bytes(),StrictJson.EXPLICIT_MAX_BYTES));
        assertEquals(actual,OpportunityJson.toNode(ActivityJson.app(actual)));
        assertThrows(IllegalArgumentException.class,()->ActivityJson.parse(new byte[StrictJson.EXPLICIT_MAX_BYTES+1]));
    }
}
