package org.xar.ck3.control.nativebridge.capabilities.registry;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.registry.RegistryPublicProfile.Profile.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CampaignProjection.*;

/** DATA serializers only: these typed original records cannot grant a Native read/action authority. */
final class RegistryPublicProfileTest {
    private static final BigInteger WIDE = BigInteger.ONE.shiftLeft(100);
    private static final BigInteger U64 = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private static final Source SOURCE = new Source("game.command.query-campaign-root-context-v1", U64,
            "1.20.0.4", "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518");

    @Test void actualTypedSerializersKeepInternalIntegersAndPublishOnlyDeclaredRoles() {
        Binding binding = new Binding("original-registry-data", WIDE, U64, 53182008, WIDE);
        UnavailableRoot root = new UnavailableRoot(binding, SOURCE, "original unavailable input");
        EntityDirectory.Result directory = EntityDirectory.build(root, new EntityDirectory.Request(Relation.ANY, null, 50));
        RawJson internal = RegistryWire.encodeDirectory(directory);
        ObjectNode wire = tree(RegistryWire.encodePublicDirectory(directory));
        assertEquals(U64.toString(), wire.get("snapshot_revision").textValue());
        assertEquals(U64.toString(), wire.at("/source/query_sequence").textValue());
        assertTrue(wire.get("date_raw").isIntegralNumber());
        assertTrue(wire.get("after_character_id").isNull());
        assertEquals(tree(internal), tree(RegistryPublicProfile.decode(ENTITY_DIRECTORY, json(wire))));

        TurnBundle.Result<String,String> bundle = new TurnBundle.Result<>(TurnBundle.SCHEMA, Status.UNAVAILABLE,
                binding, Component.unavailable("original"), Component.unavailable("original"), Component.unavailable("original"),
                Component.unavailable("original"), Component.unavailable("original"), Component.unavailable("original"),
                new TurnBundle.Readiness(false,false,false,false,false,false,false,false,false,false,false,false,false,false,false),
                "original", new TurnBundle.BundleSource(SOURCE.capability(), U64, "native-headless"));
        ObjectNode publicBundle = tree(RegistryWire.encodePublicBundle(bundle));
        assertEquals(WIDE.toString(), publicBundle.at("/binding/revision").textValue());
        assertEquals(WIDE.toString(), publicBundle.at("/binding/expected_revision").textValue());
        assertEquals(U64.toString(), publicBundle.at("/binding/native_revision").textValue());
        assertEquals(tree(RegistryWire.encodeBundle(bundle)), tree(RegistryPublicProfile.decode(TURN_BUNDLE, json(publicBundle))));
        assertTrue(tree(RegistryWire.encodeBundle(bundle)).at("/binding/revision").isIntegralNumber());
    }

    @Test void revisionDomainIsNotUint64AndCanonicalTextNeverChangesItsValue() {
        assertEquals(WIDE, RegistryPublicProfile.revision(StrictJson.parse(WIDE.toString().getBytes(StandardCharsets.UTF_8))));
        assertEquals(WIDE, RegistryPublicProfile.revision(StrictJson.parse(('"' + WIDE.toString() + '"').getBytes(StandardCharsets.UTF_8))));
        assertEquals(BigInteger.ZERO, RegistryPublicProfile.revision(StrictJson.parse("\"0\"".getBytes(StandardCharsets.UTF_8))));
        for (String invalid : List.of("true", "4.0", "null", "-1", "\"-1\"", "\"01\"", "\"+1\"", "\"1.0\"", "\" 1\"", "\"\""))
            assertThrows(IllegalArgumentException.class, () -> RegistryPublicProfile.revision(StrictJson.parse(invalid.getBytes(StandardCharsets.UTF_8))), invalid);
        assertThrows(IllegalArgumentException.class, () -> RegistryPublicProfile.revision(StrictJson.parse(('"' + "1".repeat(4301) + '"').getBytes(StandardCharsets.UTF_8))));
    }

    @Test void exactFixedPointPathsRoundTripButPendingAndUndeclaredFieldsAreNeverGuessed() {
        ObjectNode original = tree(raw("""
                {"schema":"xar.ck3.turn-bundle/v1","binding":{"revision":1267650600228229401496703205376,"native_revision":18446744073709551615,"expected_revision":1267650600228229401496703205376},
                 "source":{"query_sequence":18446744073709551615},
                 "ruler_state":{"value":{"gold":{"value":{"raw":-9223372036854775808,"scale":100000}},"income":{"value":{"raw":1,"scale":100000}}}},
                 "realm_state":{"value":{"council":{"value":{"positions":[{"progress":{"current":{"raw":9223372036854775807},"maximum":{"raw":9223372036854775807}}}]}}}},
                 "pending_state":{"value":{"active_event":{"value":{"revision":"script-source-revision","raw":7}}}},
                 "war_state":{"value":{"wars":[{"player_relative_war_score":-1267650600228229401496703205376}]}}}
                """));
        ObjectNode wire = tree(RegistryPublicProfile.encode(TURN_BUNDLE, json(original)));
        assertEquals("-9223372036854775808", wire.at("/ruler_state/value/gold/value/raw").textValue());
        assertTrue(wire.at("/ruler_state/value/income/value/raw").isIntegralNumber());
        assertEquals("9223372036854775807", wire.at("/realm_state/value/council/value/positions/0/progress/current/raw").textValue());
        assertEquals("script-source-revision", wire.at("/pending_state/value/active_event/value/revision").textValue());
        assertEquals(WIDE.negate().toString(), wire.at("/war_state/value/wars/0/player_relative_war_score").textValue());
        assertEquals(original, tree(RegistryPublicProfile.decode(TURN_BUNDLE, json(wire))));
        ObjectNode unsafe = original.deepCopy(); unsafe.put("unqualified_revision", U64);
        assertThrows(IllegalArgumentException.class, () -> RegistryPublicProfile.encode(TURN_BUNDLE, json(unsafe)));
        ObjectNode pending = original.deepCopy(); ((ObjectNode) pending.at("/pending_state/value/active_event/value")).put("revision", U64);
        assertThrows(IllegalArgumentException.class, () -> RegistryPublicProfile.encode(TURN_BUNDLE, json(pending)));
        assertThrows(IllegalArgumentException.class, () -> RegistryPublicProfile.encode(ENTITY_DIRECTORY, json(original)));
    }

    @Test void missingNullFloatBooleanOverflowAndWrongWireRepresentationFailClosed() {
        for (String value : List.of("null", "true", "1.0", "0", "-1", "18446744073709551616")) {
            RawJson original = raw("{\"schema\":\"xar.ck3.entity-directory/v1\",\"snapshot_revision\":" + value + ",\"source\":{\"query_sequence\":1}}");
            assertThrows(IllegalArgumentException.class, () -> RegistryPublicProfile.encode(ENTITY_DIRECTORY, original), value);
        }
        assertThrows(IllegalArgumentException.class, () -> RegistryPublicProfile.encode(ENTITY_DIRECTORY,
                raw("{\"schema\":\"xar.ck3.entity-directory/v1\",\"source\":{\"query_sequence\":1}}")));
        for (String value : List.of("1", "\"01\"", "\"0\"", "\"18446744073709551616\""))
            assertThrows(IllegalArgumentException.class, () -> RegistryPublicProfile.decode(ENTITY_DIRECTORY,
                    raw("{\"schema\":\"xar.ck3.entity-directory/v1\",\"snapshot_revision\":" + value + ",\"source\":{\"query_sequence\":\"1\"}}")), value);
    }
    @Test void largePayloadPreservesFloatsAndConvertsDeclaredIntegers() {
        String base = """
                {"schema":"xar.ck3.turn-bundle/v1","binding":{"revision":1,"native_revision":1,"expected_revision":1},
                 "source":{"query_sequence":1},
                 "pending_state":{"value":{"amount":1.25}}}
                """;
        ObjectNode original = tree(raw(base));
        original.put("padding", "观".repeat(400_000));
        RawJson internal = json(original);
        assertTrue(internal.bytes().length > StrictJson.EXPLICIT_MAX_BYTES);
        RawJson encoded = RegistryPublicProfile.encode(TURN_BUNDLE, internal);
        assertTrue(encoded.bytes().length > StrictJson.EXPLICIT_MAX_BYTES);
        ObjectNode encodedTree = tree(encoded);
        assertEquals("1", encodedTree.at("/binding/revision").textValue());
        assertTrue(encodedTree.at("/pending_state/value/amount").isFloatingPointNumber());
        assertEquals(1.25, encodedTree.at("/pending_state/value/amount").doubleValue());
        RawJson decoded = RegistryPublicProfile.decode(TURN_BUNDLE, encoded);
        assertTrue(decoded.bytes().length > StrictJson.EXPLICIT_MAX_BYTES);
        ObjectNode decodedTree = tree(decoded);
        assertTrue(decodedTree.at("/binding/revision").isIntegralNumber());
        assertEquals(1, decodedTree.at("/binding/revision").intValue());
        assertTrue(decodedTree.at("/pending_state/value/amount").isFloatingPointNumber());
        assertEquals(1.25, decodedTree.at("/pending_state/value/amount").doubleValue());
        assertEquals(tree(internal), decodedTree);
        ObjectNode unsafe = original.deepCopy();
        unsafe.put("undeclared", BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE));
        assertThrows(IllegalArgumentException.class, () -> RegistryPublicProfile.encode(TURN_BUNDLE, json(unsafe)));
        String nonfinite = """
                {"schema":"xar.ck3.turn-bundle/v1","binding":{"revision":1,"native_revision":1,"expected_revision":1},
                 "source":{"query_sequence":1},
                 "pending_state":{"value":{"amount":1e1000}}}
                """;
        assertThrows(IllegalArgumentException.class, () -> RegistryPublicProfile.encode(TURN_BUNDLE, raw(nonfinite)));
    }
    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }
    private static RawJson json(ObjectNode value) { return RegistryJson.encode(value); }
    private static ObjectNode tree(RawJson value) { return RegistryJson.object(value); }
}
