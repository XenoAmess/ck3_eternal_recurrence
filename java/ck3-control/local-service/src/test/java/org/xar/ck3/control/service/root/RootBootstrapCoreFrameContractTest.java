package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;

/** Actual public core producer to the shared startup/worker decoder and branch predicates. */
final class RootBootstrapCoreFrameContractTest {
    @Test
    void publicProducerRoundTripsWithoutChangingPartialValues() throws Exception {
        var actual = new CoreFrame.Partial(new CoreFrame.Prefix(Integer.MIN_VALUE, 5, true,
                Integer.MAX_VALUE, true, true, 7, true));
        var original = CoreFramePublicCodec.encode(actual);
        var decoded = RootNativeFreshStartup.decodeCore(original);
        assertEquals(actual, decoded);
        assertEquals(node(original), node(CoreFramePublicCodec.encode(decoded)));
        assertTrue(RootNativeFreshStartup.isCampaignReady(decoded));
        assertTrue(RootNativeFreshStartup.isObservedCoreReady(decoded, true));
        assertTrue(RootNativeFreshStartup.isObservedCoreReady(decoded, false));
        assertTrue(RootNativeFreshStartup.isMapReady(decoded));
    }

    @Test
    void sameGameWorkerRequiresMapWhileFreshRobertRequiresLivingPlayedCharacter() throws Exception {
        var noCharacter = roundTrip(new CoreFrame.Partial(new CoreFrame.Prefix(123, 1, false,
                -1, true, false, -1, false)));
        assertTrue(RootNativeFreshStartup.isMapReady(noCharacter));
        assertTrue(RootNativeFreshStartup.isObservedCoreReady(noCharacter, false));
        assertFalse(RootNativeFreshStartup.isObservedCoreReady(noCharacter, true));
        assertFalse(RootNativeFreshStartup.isCampaignReady(noCharacter));

        var deadCharacter = roundTrip(new CoreFrame.Partial(new CoreFrame.Prefix(123, 2, false,
                4, true, true, 7, false)));
        assertTrue(RootNativeFreshStartup.isMapReady(deadCharacter));
        assertFalse(RootNativeFreshStartup.isCampaignReady(deadCharacter));

        var mapLoading = roundTrip(new CoreFrame.Partial(new CoreFrame.Prefix(123, 2, false,
                4, false, true, 7, true)));
        assertTrue(RootNativeFreshStartup.isObservedCoreReady(mapLoading, false));
        assertFalse(RootNativeFreshStartup.isMapReady(mapLoading));
        assertFalse(RootNativeFreshStartup.isCampaignReady(mapLoading));
    }

    @Test
    void unavailableProducerPreservesNullsAndBothApplicationObservationStates() throws Exception {
        for (boolean observed : List.of(false, true)) {
            var actual = new CoreFrame.Unavailable(observed, "core_prefix_unavailable");
            var original = CoreFramePublicCodec.encode(actual);
            var row = node(original);
            for (String field : List.of("date_raw", "speed", "paused", "local_player_id", "map_ready",
                    "has_played_character", "played_character_id", "played_character_alive")) {
                assertTrue(row.has(field), field);
                assertTrue(row.get(field).isNull(), field);
            }
            var decoded = RootNativeFreshStartup.decodeCore(original);
            assertEquals(actual, decoded);
            assertFalse(RootNativeFreshStartup.isMapReady(decoded));
            assertFalse(RootNativeFreshStartup.isCampaignReady(decoded));
            assertFalse(RootNativeFreshStartup.isObservedCoreReady(decoded, false));
            assertFalse(RootNativeFreshStartup.isObservedCoreReady(decoded, true));
        }
    }

    @Test
    void malformedTypesAndMissingFieldsBecomeIOExceptionWithOriginalDecodeCause() throws Exception {
        var actual = new CoreFrame.Partial(new CoreFrame.Prefix(123, 2, false,
                4, true, true, 7, true));
        var original = CoreFramePublicCodec.encode(actual);
        List<Consumer<ObjectNode>> invalidMutations = List.of(
                row -> row.put("map_ready", 1),
                row -> row.put("map_ready", "true"),
                row -> row.putNull("map_ready"),
                row -> row.remove("map_ready"),
                row -> row.put("core_available", 1),
                row -> row.put("application_main_observed", "true"),
                row -> row.put("has_played_character", 1),
                row -> row.put("played_character_alive", "true"),
                row -> row.put("speed", 2.0),
                row -> row.put("local_player_id", true),
                row -> row.put("played_character_id", 7.0),
                row -> row.put("date_raw", 2147483648L));
        for (var mutation : invalidMutations) {
            var invalid = node(original);
            mutation.accept(invalid);
            var failure = assertThrows(IOException.class,
                    () -> RootNativeFreshStartup.decodeCore(raw(invalid)));
            assertInstanceOf(IllegalArgumentException.class, failure.getCause());
        }

        var missingNull = node(CoreFramePublicCodec.encode(new CoreFrame.Unavailable(false, "loading")));
        missingNull.remove("speed");
        var failure = assertThrows(IOException.class,
                () -> RootNativeFreshStartup.decodeCore(raw(missingNull)));
        assertInstanceOf(IllegalArgumentException.class, failure.getCause());
    }

    private static CoreFrame roundTrip(CoreFrame actual) throws IOException {
        return RootNativeFreshStartup.decodeCore(CoreFramePublicCodec.encode(actual));
    }

    private static ObjectNode node(RawJson original) {
        return assertInstanceOf(ObjectNode.class,
                StrictJson.parse(original.bytes(), StrictJson.EXPLICIT_MAX_BYTES));
    }

    private static RawJson raw(ObjectNode row) {
        return new RawJson(row.toString().getBytes(StandardCharsets.UTF_8));
    }
}
