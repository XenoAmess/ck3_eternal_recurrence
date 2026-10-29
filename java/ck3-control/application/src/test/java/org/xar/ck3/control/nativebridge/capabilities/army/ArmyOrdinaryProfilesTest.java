package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.military.OrdinaryAutomaticSurrenderPolicy.Variant;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments.*;

/** Canonical profile custody is DATA. A constructor or a successful round trip grants no native permission. */
final class ArmyOrdinaryProfilesTest {
    private static final ExactRef QUOTE = new ExactRef("D:/synthetic-no-authority/options.json", 17, "a".repeat(64));
    private static RawJson raw(String text) { return new RawJson(text.getBytes(StandardCharsets.UTF_8)); }
    private static ArmyCalls.War surrender() { return new ArmyCalls.War(PublicMethod.SURRENDER_WAR,
            new ArmyCalls.Revision(new ArmyTypes.Present<>(BigInteger.TEN)), BigInteger.valueOf(23)); }
    private static ArmyOrdinaryActionArguments automatic(Variant variant) {
        return new ArmyOrdinaryActionArguments(Kind.SURRENDER_WAR, ArmyCallCodec.encode(surrender()), List.of(QUOTE),
                ExecutionProfile.GENERIC_AUTOMATIC_SURRENDER, Optional.of(variant));
    }
    @Test void specializedSdkV1RetainsExactlyItsFourOriginalOuterFieldsAndBytes() {
        var args = new ArmyOrdinaryActionArguments(Kind.SURRENDER_WAR, ArmyCallCodec.encode(surrender()), List.of(QUOTE));
        String golden = "{\"schema\":\"xar.ck3.army-ordinary-action-arguments/v1\",\"kind\":\"surrender_war\","
                + "\"public_arguments\":{\"expected_revision\":\"10\",\"war_id\":23},\"preflight_reads\":[{\"bytes\":17,"
                + "\"path\":\"D:/synthetic-no-authority/options.json\",\"sha256\":\"" + "a".repeat(64) + "\"}]}";
        assertArrayEquals(golden.getBytes(StandardCharsets.UTF_8), args.raw().bytes());
        var restored = decode(args.raw()); assertEquals(args, restored); assertEquals(ExecutionProfile.SDK_ORDINARY, restored.executionProfile());
        assertTrue(restored.automaticSurrender().isEmpty());
    }
    @Test void allAutomaticVariantsSurviveFullCanonicalArgsAndPublicCallRoundTrip() {
        for (Variant variant : Variant.values()) {
            var original = automatic(variant); var restored = decode(original.raw());
            assertEquals(original, restored); assertArrayEquals(original.raw().bytes(), restored.raw().bytes());
            assertEquals(ExecutionProfile.GENERIC_AUTOMATIC_SURRENDER, restored.executionProfile());
            assertEquals(variant, restored.automaticSurrender().orElseThrow());
            assertEquals(surrender(), ArmyCallCodec.decode(PublicMethod.SURRENDER_WAR, restored.publicArguments()));
            assertEquals(PROFILE_SCHEMA, StrictJson.parse(restored.raw().bytes()).get("schema").textValue());
        }
    }
    @Test void directFixedWindowIsAnExplicitClosedProfileAndCannotAuthorizeOtherKinds() {
        for (PublicMethod method : List.of(PublicMethod.CLOSE_WAR_DECLARED_OVERVIEW_V1, PublicMethod.CLOSE_WAR_RESULTS_WINDOW_V1)) {
            var call = new ArmyCalls.Frame(method, surrender().revision());
            var direct = new ArmyOrdinaryActionArguments(Kind.valueOf(method.name()), ArmyCallCodec.encode(call), List.of(), ExecutionProfile.DIRECT_FIXED_WINDOW, Optional.empty());
            var restored = decode(direct.raw()); assertEquals(direct, restored); assertEquals(ExecutionProfile.DIRECT_FIXED_WINDOW, restored.executionProfile());
            assertTrue(StrictJson.parse(restored.raw().bytes()).get("generic_automatic_surrender_variant").isNull());
            assertFalse(direct.raw().equals(new ArmyOrdinaryActionArguments(direct.kind(), direct.publicArguments(), List.of()).raw()),
                    "empty preflight alone must never select the direct close profile");
            assertThrows(IllegalArgumentException.class, () -> new ArmyOrdinaryActionArguments(direct.kind(), direct.publicArguments(), List.of(QUOTE), ExecutionProfile.DIRECT_FIXED_WINDOW, Optional.empty()));
        }
        for (Kind other : Kind.values()) if (other != Kind.CLOSE_WAR_DECLARED_OVERVIEW_V1 && other != Kind.CLOSE_WAR_RESULTS_WINDOW_V1)
            assertThrows(IllegalArgumentException.class, () -> new ArmyOrdinaryActionArguments(other, raw("{}"), List.of(), ExecutionProfile.DIRECT_FIXED_WINDOW, Optional.empty()));
        assertThrows(IllegalArgumentException.class, () -> new ArmyOrdinaryActionArguments(Kind.SURRENDER_WAR, ArmyCallCodec.encode(surrender()), List.of(), ExecutionProfile.GENERIC_AUTOMATIC_SURRENDER, Optional.of(Variant.TERMINAL_SCORE_DEFEAT)));
    }
    @Test void schemaProfilesVariantsNullMissingAndWrongTypesAreDifferentDomains() {
        for (String key : List.of("execution_profile", "generic_automatic_surrender_variant")) {
            var original = (com.fasterxml.jackson.databind.node.ObjectNode) StrictJson.parse(automatic(Variant.TERMINAL_SCORE_DEFEAT).raw().bytes());
            var missing = original.deepCopy(); missing.remove(key);
            assertThrows(IllegalArgumentException.class, () -> decode(new RawJson(StrictJson.canonical(missing))));
            for (String token : List.of("null", "true", "1", "1.0", "[]", "{}", "\"unknown\"")) {
                var changed = original.deepCopy(); changed.set(key, StrictJson.parse(token.getBytes(StandardCharsets.UTF_8)));
                assertThrows(IllegalArgumentException.class, () -> decode(new RawJson(StrictJson.canonical(changed))));
            }
        }
        var automatic = (com.fasterxml.jackson.databind.node.ObjectNode) StrictJson.parse(automatic(Variant.RAIKTOR_LONG_WAR_UTILITY).raw().bytes());
        automatic.put("kind", "move_army"); assertThrows(IllegalArgumentException.class, () -> decode(new RawJson(StrictJson.canonical(automatic))));
        automatic.put("kind", "surrender_war").put("schema", SCHEMA);
        assertThrows(IllegalArgumentException.class, () -> decode(new RawJson(StrictJson.canonical(automatic))), "v1 must not silently accept a new mode field");
    }
}
