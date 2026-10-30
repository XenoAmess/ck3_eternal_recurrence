package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.EntityDirectory;
import org.xar.ck3.control.nativebridge.capabilities.registry.CampaignProjection.Relation;

final class NativePietyDirectoryCursorTest {
    private static PublicBindings.Value args(String value) {
        return new PublicBindings.Value(new RawJson(("{\"expected_revision\":\"4\",\"after_character_id\":" + value + "}").getBytes(StandardCharsets.UTF_8)));
    }
    @Test void actualPublicCursorAcceptsSignedCharacterIdsIncludingZero() {
        for (int id : new int[]{0, -2, Integer.MIN_VALUE, Integer.MAX_VALUE}) {
            assertEquals(id, RootRegistryReadPublicProducts.decodeSearch(args(Integer.toString(id))).directory().afterCharacterId().intValue());
            assertEquals(id, new EntityDirectory.Request(Relation.ANY, id, 50).afterCharacterId().intValue());
        }
    }
    @Test void actualPublicCursorRejectsAbsentWrongTypesAndOutsideInt32() {
        for (String bad : new String[]{"-1", "2147483648", "-2147483649", "true", "0.0", "\"0\""})
            assertThrows(IllegalArgumentException.class, () -> RootRegistryReadPublicProducts.decodeSearch(args(bad)), bad);
        assertNull(RootRegistryReadPublicProducts.decodeSearch(args("null")).directory().afterCharacterId());
        assertThrows(IllegalArgumentException.class, () -> new EntityDirectory.Request(Relation.ANY, -1, 50));
    }
}
