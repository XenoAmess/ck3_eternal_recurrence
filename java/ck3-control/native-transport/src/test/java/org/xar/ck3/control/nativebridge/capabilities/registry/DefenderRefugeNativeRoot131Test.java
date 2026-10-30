package org.xar.ck3.control.nativebridge.capabilities.registry;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.capabilities.CampaignRootContextJson;
import org.xar.ck3.control.application.capabilities.DefenderRefugeScopes;
import org.xar.ck3.control.application.driver.DriverJson;

/** Actual Native software-serializer Root bytes; no Driver, Game or native execution credit. */
final class DefenderRefugeNativeRoot131Test {
    @Test void actualZeroOwnerRootPreservesObservedDirectVassalCapital() throws IOException {
        Obj original = original();
        Obj normalized = CampaignRootContextJson.normalize(original,
                integer(original.get("date_raw"), "date_raw"),
                integer(original.get("snapshot_revision"), "snapshot_revision"));
        assertEquals(original, normalized);
        assertEquals(normalized, DriverJson.object(DriverJson.encode(normalized), 1_048_576));
        assertEquals(Optional.of(List.of(7)), DefenderRefugeScopes.directVassalCapitalProvinceIds(normalized));
    }

    @Test void absentSentinelAndBooleanOwnerRemainUnavailable() throws IOException {
        Obj root = original();
        assertTrue(DefenderRefugeScopes.directVassalCapitalProvinceIds(
                root.with("player_character_id", new IntegerValue(BigInteger.valueOf(-1)))).isEmpty());
        assertTrue(DefenderRefugeScopes.directVassalCapitalProvinceIds(
                root.with("player_character_id", new Bool(false))).isEmpty());
    }

    private static Obj original() throws IOException {
        String resource = "/registry/m3-defender-refuge131/provenance-full-root.json";
        try (InputStream input = DefenderRefugeNativeRoot131Test.class.getResourceAsStream(resource)) {
            if (input == null) throw new IOException("Required original Native Root bytes missing: " + resource);
            return DriverJson.object(input.readAllBytes(), 1_048_576);
        }
    }
}
