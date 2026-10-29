package org.xar.ck3.control.application.effects;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

final class NativeGovernanceEffectsTest {
    private static final String TITLES = "{\"primary_title_id\":10,\"held_titles\":[{\"title_id\":10,\"primary\":true,\"successor_character_ids\":[19,20]}]}";
    @Test void actualOrderedSuccessorsKeepStrictIntegerAndPrimaryIdentity() {
        assertDoesNotThrow(()->NativeGovernanceEffects.validateTitles(StrictJson.parse(TITLES.getBytes(StandardCharsets.UTF_8))));
        for(String wrong:java.util.List.of(TITLES.replace("[19,20]","[true,20]"),TITLES.replace("[19,20]","[19.0,20]"),
                TITLES.replace("[19,20]","[19,19]"),TITLES.replace("\"primary_title_id\":10","\"primary_title_id\":11")))
            assertThrows(IllegalArgumentException.class,()->NativeGovernanceEffects.validateTitles(StrictJson.parse(wrong.getBytes(StandardCharsets.UTF_8))));
    }
    @Test void absentOrEmptyHeldTitlesDoNotBecomeACompletedCrownReceipt() {
        for(String wrong:java.util.List.of("{}","{\"primary_title_id\":10,\"held_titles\":null}","{\"primary_title_id\":10,\"held_titles\":[]}"))
            assertThrows(IllegalArgumentException.class,()->NativeGovernanceEffects.validateTitles(StrictJson.parse(wrong.getBytes(StandardCharsets.UTF_8))));
    }
}
