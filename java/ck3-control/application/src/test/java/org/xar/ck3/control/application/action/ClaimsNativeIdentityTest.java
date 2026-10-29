package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Claims TitleIDs keep their ordered native-step identity through registration and inventory serde. */
final class ClaimsNativeIdentityTest {
    @Test void orderedClaimsHaveDistinctCanonicalKeysAndOriginalWireWithNoExtraArguments() {
        var source = new ArrayList<>(List.of(2, 1));
        var claims = new NativeStepDiscriminator.ClaimsIdentity(source);
        source.set(0, 9);
        assertEquals(List.of(2, 1), claims.titles());
        assertThrows(UnsupportedOperationException.class, () -> claims.titles().add(3));
        assertEquals("query-player-claims-v1-2:1", claims.operationKey().value());
        assertEquals("query-player-claims-v1-2,1", claims.nativeStep());
        assertNotEquals(claims.operationKey(), new NativeStepDiscriminator.ClaimsIdentity(List.of(1, 2)).operationKey());
        assertEquals(claims, NativeStepDiscriminator.ClaimsIdentity.parse(claims.operationKey()).orElseThrow());
        var identity = NativeStepDiscriminator.identity(claims.operationKey());
        assertEquals(claims.nativeStep(), identity.nativeStep());
        assertTrue(identity.selector().isEmpty());
        var json = NativeStepDiscriminator.toJson(identity);
        assertTrue(json.get("selector").isNull());
        assertEquals(identity, NativeStepDiscriminator.fromJson(StrictJson.parse(StrictJson.canonical(json))));
        var wire = new NativeRequest(claims.nativeStep(), "game.command.query-player-claims-v1-IDS", new RawJson(new byte[]{123,125}));
        NativeStepDiscriminator.requireRequest(claims.operationKey(), ExecutableStepBindings.Kind.READ, wire);
        NativeStepDiscriminator.requireWire(claims.operationKey(), ExecutableStepBindings.Kind.READ, wire.step(), wire.additionalFields());
        assertFalse(NativeStepDiscriminator.matchesRequest(claims.operationKey(), ExecutableStepBindings.Kind.ACTION, wire));
        assertFalse(NativeStepDiscriminator.matchesRequest(claims.operationKey(), ExecutableStepBindings.Kind.READ,
                new NativeRequest("query-player-claims-v1-1,2", wire.requiredCapability(), wire.additionalFields())));
        assertFalse(NativeStepDiscriminator.matchesRequest(claims.operationKey(), ExecutableStepBindings.Kind.READ,
                new NativeRequest(claims.nativeStep(), Optional.empty(), wire.additionalFields())));
        assertFalse(NativeStepDiscriminator.matchesRequest(claims.operationKey(), ExecutableStepBindings.Kind.READ,
                new NativeRequest(claims.nativeStep(), wire.requiredCapability(), new RawJson("{\"title_ids\":[2,1]}".getBytes(java.nio.charset.StandardCharsets.UTF_8)))));
        var changed = json.deepCopy(); changed.put("native_step", claims.operationKey().value());
        assertThrows(IllegalArgumentException.class, () -> NativeStepDiscriminator.fromJson(changed));
    }

    @Test void singletonHistoricalIdentityAndBoundaryTitlesRetainExactRepresentation() {
        for (int id : List.of(0, 2, Integer.MAX_VALUE)) {
            var claims = new NativeStepDiscriminator.ClaimsIdentity(List.of(id));
            assertEquals("query-player-claims-v1-" + id, claims.operationKey().value());
            assertEquals(claims.operationKey().value(), claims.nativeStep());
            var historical = NativeStepDiscriminator.toJson(NativeStepDiscriminator.identity(claims.operationKey()));
            historical.put("schema", NativeStepDiscriminator.LEGACY_SCHEMA);
            assertEquals(historical, NativeStepDiscriminator.toJson(NativeStepDiscriminator.fromJson(historical)));
        }
        var current = NativeStepDiscriminator.toJson(NativeStepDiscriminator.identity(
                new NativeStepDiscriminator.ClaimsIdentity(List.of(0, Integer.MAX_VALUE)).operationKey()));
        current.put("schema", NativeStepDiscriminator.LEGACY_SCHEMA);
        assertThrows(IllegalArgumentException.class, () -> NativeStepDiscriminator.fromJson(current));
    }

    @Test void malformedAliasesDuplicatesEmptyAndOversizedClaimsAreRejected() {
        assertThrows(IllegalArgumentException.class, () -> new OperationKey("query-player-claims-v1-2,1"));
        for (String nativeStep : List.of("unrelated-2,1", "query-player-claims-v1-2:1", "query-player-claims-v1-1,", "query-player-claims-v1-1,01", "query-player-claims-v1-1,1"))
            assertThrows(IllegalArgumentException.class, () -> new NativeRequest(nativeStep, Optional.empty(), new RawJson(new byte[]{123,125})));
        for (String suffix : List.of("", "01", "1:", ":1", "1::2", "1:1", "1:01", "-1", "2147483648", "١")) {
            if (suffix.equals("١")) {
                assertThrows(IllegalArgumentException.class, () -> new OperationKey("query-player-claims-v1-" + suffix));
            } else {
                var operation = new OperationKey("query-player-claims-v1-" + suffix);
                assertThrows(IllegalArgumentException.class, () -> NativeStepDiscriminator.identity(operation), suffix);
            }
        }
        assertThrows(IllegalArgumentException.class, () -> new NativeStepDiscriminator.ClaimsIdentity(List.of()));
        assertThrows(IllegalArgumentException.class, () -> new NativeStepDiscriminator.ClaimsIdentity(List.of(-1)));
        assertThrows(IllegalArgumentException.class, () -> new NativeStepDiscriminator.ClaimsIdentity(List.of(1, 1)));
        assertThrows(IllegalArgumentException.class, () -> new NativeStepDiscriminator.ClaimsIdentity(
                java.util.stream.IntStream.range(0, 256).map(i -> Integer.MAX_VALUE-i).boxed().toList()));
    }
}
