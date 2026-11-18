package org.xar.ck3.control.nativebridge.capabilities.interactions;

import static org.junit.jupiter.api.Assertions.*;

import java.util.List;
import java.util.Locale;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.common.G2Source;

/** Source identity DATA only. No ordinary Context, request, Installed product or Native operation is constructed. */
final class KnownPendingUnavailableSourceTest {
    private static final ExactCk3Build BUILD = ExactCk3Build.CK3_1210;
    private static final ExactRef SOURCE = new ExactRef("D:/fixture/held-context-source", 1, "a".repeat(64));

    @Test void heldFrameFactoryRetainsBothExistingExactSourceSpellingsWithoutInventingARequest() {
        for (String spelling : List.of(BUILD.executableSha256(), BUILD.executableSha256().toUpperCase(Locale.ROOT),
                BUILD.version()+"@sha256:"+BUILD.executableSha256())) {
            var source = source(spelling);
            var unavailable = KnownPendingInteractionPolicy.unavailableForSource(BUILD.version(), BUILD.executableSha256(), source).result();
            assertEquals("interaction_native_contract_unmigrated", unavailable.reason());
            assertTrue(unavailable.original().isEmpty());
            assertTrue(unavailable.decodeFailure().isEmpty());
            assertTrue(unavailable.observedFailure().isEmpty());
            assertEquals(spelling, source.exactBuild());
        }
    }

    @Test void missingWrongOrVersionOnlySourceCannotAcquireTheExactNegativeContract() {
        for (String spelling : List.of(BUILD.version(), "0".repeat(64),
                BUILD.version()+"@sha256:"+ExactCk3Build.CK3_12004.executableSha256())) {
            assertThrows(IllegalArgumentException.class, () -> KnownPendingInteractionPolicy.unavailableForSource(
                    BUILD.version(), BUILD.executableSha256(), source(spelling)));
        }
        assertThrows(NullPointerException.class, () -> KnownPendingInteractionPolicy.unavailableForSource(
                BUILD.version(), BUILD.executableSha256(), null));
    }

    @Test void configuredTupleStillRequiresExactFlorinAndCannotUseOldBuildAsUnavailableAlias() {
        var source = source(BUILD.executableSha256());
        assertThrows(IllegalArgumentException.class, () -> KnownPendingInteractionPolicy.unavailableForSource(
                "1.21.0.0", BUILD.executableSha256(), source));
        assertThrows(IllegalArgumentException.class, () -> KnownPendingInteractionPolicy.unavailableForSource(
                BUILD.version(), "0".repeat(64), source));
        var old = ExactCk3Build.CK3_12004;
        assertThrows(IllegalArgumentException.class, () -> KnownPendingInteractionPolicy.unavailableForSource(
                old.version(), old.executableSha256(), source(old.executableSha256())));
    }

    private static G2Source source(String exactBuild) {
        return new G2Source("held-context-software", "2026-11-18T00:00:00Z", exactBuild, SOURCE);
    }
}
