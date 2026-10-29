package org.xar.ck3.control.contracts.semantic;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.MissingNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

/** Real receive semantic DATA, not a gameplay readiness or qualified character-ID issuer. */
final class NativePlayedCharacterTest {
    static final BigInteger REVISION = BigInteger.valueOf(17);
    static final JsonNode DATE = node("1000");
    record Case(String name, JsonNode value, BigInteger revision, JsonNode date) { }

    @Test void nullableActorProjectionPreservesPresenceAndDetachesAllOriginalInput() {
        assertTrue(normalize(NullNode.instance).isNull()); assertTrue(normalize(MissingNode.getInstance()).isNull());
        var original = actor().putNull("source").put("unknown_future_field", "ignored")
                .put("stress_points", Integer.MAX_VALUE).put("has_heir", false);
        original.putNull("betrothed_id").putNull("primary_spouse_id").putArray("spouse_ids");
        var actual = normalize(original);
        assertEquals(BigInteger.valueOf(73), actual.get("character_id").bigIntegerValue());
        assertEquals("native", actual.get("source").textValue());
        assertFalse(actual.has("unknown_future_field")); assertTrue(actual.get("primary_heir_id").isNull());
        assertFalse(normalize(actor()).has("primary_heir_id"));
        assertFalse(normalize(actor()).has("stress_points"));
        JsonNode retained = actual.deepCopy(); original.put("character_id", 99).put("stress_points", 0);
        assertEquals(retained, actual);
        ((ObjectNode) actual).put("character_id", 100);
        assertEquals(99, original.get("character_id").intValue());
    }

    @Test void independentPresenceAndRelationshipRulesDoNotInventExtraNativeInvariants() {
        var none = actor().put("has_heir", false);
        assertTrue(normalize(none).get("primary_heir_id").isNull());
        var zero = actor().put("character_id", 0).put("alive", false).put("has_heir", true).put("primary_heir_id", 0)
                .put("betrothed_id", 0).put("primary_spouse_id", 0);
        zero.putArray("spouse_ids").add(0);
        assertEquals(BigInteger.ZERO, normalize(zero).get("character_id").bigIntegerValue());
        var noPrimary = actor().putNull("betrothed_id").putNull("primary_spouse_id");
        noPrimary.putArray("spouse_ids").add(9).add(2);
        var values = normalize(noPrimary).get("spouse_ids");
        assertEquals(9, values.get(0).intValue()); assertEquals(2, values.get(1).intValue());
        BigInteger wide = BigInteger.ONE.shiftLeft(160);
        var wideActor = actor().put("character_id", wide);
        assertThrows(IllegalArgumentException.class, () -> normalize(wideActor), "native public actor cannot exceed its signed int32 wire");
    }

    @Test void sharedTraitProducerKeepsIndependentRevisionDateAndReasonDomainsBeforeBusinessQualification() {
        BigInteger actor = BigInteger.valueOf(Integer.MAX_VALUE), revision = BigInteger.ONE.shiftLeft(100), date = BigInteger.ONE.shiftLeft(110).negate();
        var membership = membership(actor, revision, date).put("status", "unavailable").putNull("traits").put("unavailable_reason", "r".repeat(33000));
        var input = actor().put("character_id", actor); input.set("event_trait_membership", membership);
        JsonNode actual = NativePlayedCharacter.normalize(input, revision, node(date.toString()));
        assertEquals(33000, actual.get("event_trait_membership").get("unavailable_reason").textValue().length());
        assertEquals(actor, actual.get("event_trait_membership").get("played_character_id").bigIntegerValue());
        assertThrows(IllegalArgumentException.class, () -> NativePlayedCharacter.normalize(input, revision.add(BigInteger.ONE), node(date.toString())));
        assertThrows(IllegalArgumentException.class, () -> NativePlayedCharacter.normalize(input, revision, NullNode.instance));
        assertThrows(IllegalArgumentException.class, () -> NativePlayedCharacter.normalize(input, revision, MissingNode.getInstance()));
    }

    @Test void strictMissingNullBooleanFloatAndPairFailuresAreRejectedBeforeAnyConsumerUsesData() {
        for (Case test : invalidCases())
            assertThrows(IllegalArgumentException.class, () -> NativePlayedCharacter.normalize(test.value(), test.revision(), test.date()), test.name());
    }

    @Test void normalizationAndExistingStrictJsonSerializationRoundTripWithoutAliases() {
        for (Case test : validCases()) {
            JsonNode first = NativePlayedCharacter.normalize(test.value(), test.revision(), test.date());
            JsonNode transported = StrictJson.parse(first.toString().getBytes(StandardCharsets.UTF_8), StrictJson.EXPLICIT_MAX_BYTES);
            assertEquals(first, NativePlayedCharacter.normalize(transported, test.revision(), test.date()), test.name());
        }
        assertThrows(IllegalArgumentException.class, () -> node("{\"character_id\":73,\"character_id\":74,\"alive\":true}"));
        assertThrows(IllegalArgumentException.class, () -> node("{\"character_id\":73,\"alive\":true} trailing"));
        assertThrows(IllegalArgumentException.class, () -> StrictJson.parse(new byte[] {'{','"',(byte) 0xFF,'"',':','0','}'}, StrictJson.EXPLICIT_MAX_BYTES));
    }

    /** Source-backed correction, not a claim that the legacy Python normalizer accepted negative actors. */
    @Test void signedNativeActorBoundaryRoundTripsWithoutReinterpretingIndependentLeafDomains() {
        for (int id : new int[] {Integer.MIN_VALUE, -2, 0, Integer.MAX_VALUE}) {
            JsonNode actual = normalize(actor().put("character_id", id));
            assertTrue(actual.get("character_id").isInt()); assertEquals(id, actual.get("character_id").intValue());
            assertEquals(actual, normalize(node(actual.toString())));
        }
        for (String raw : List.of("-1", "-2147483649", "2147483648", "4294967294", "true", "1.0", "null", "\"-2\""))
            assertThrows(IllegalArgumentException.class, () -> normalize(actor().set("character_id", node(raw))), raw);
        var related = actor().put("character_id", -2).put("has_heir", true).put("primary_heir_id", 0)
                .put("betrothed_id", 0).put("primary_spouse_id", 0);
        related.putArray("spouse_ids").add(0);
        assertEquals(-2, normalize(related).get("character_id").intValue());
        assertThrows(IllegalArgumentException.class, () -> normalize(related.deepCopy().put("primary_heir_id", -2)));
        assertThrows(IllegalArgumentException.class, () -> normalize(related.deepCopy().put("betrothed_id", -2)));
        var negativeSpouse = related.deepCopy(); negativeSpouse.putArray("spouse_ids").add(-2);
        assertThrows(IllegalArgumentException.class, () -> normalize(negativeSpouse));
        var trait = actor().put("character_id", -2);
        trait.set("event_trait_membership", membership(BigInteger.valueOf(-2), REVISION, BigInteger.valueOf(1000)));
        assertThrows(IllegalArgumentException.class, () -> normalize(trait), "independent trait positive actor rule is retained");
    }

    /** Native producer sets the signed actor before returning unavailable; metadata is not a qualified identity. */
    @Test void unavailableTraitMetadataRetainsSignedAndAbsentScalarsWithoutQualifyingAvailableTraits() {
        for (int id : new int[] {Integer.MIN_VALUE, -2, -1, 0, Integer.MAX_VALUE}) {
            BigInteger actorId = BigInteger.valueOf(id);
            var frame = new NativePlayerEventTraitMembership.Frame(REVISION, BigInteger.valueOf(1000), actorId);
            var observation = new NativePlayerEventTraitMembership.Unavailable(frame, "current_player_frame_unavailable");
            var raw = NativePlayerEventTraitMembership.toJson(observation);
            JsonNode wire = node(raw.toString());
            var reopened = NativePlayerEventTraitMembership.read(wire, actorId, REVISION, DATE);
            assertEquals(observation, reopened);
            assertEquals(actorId, NativePlayerEventTraitMembership.toJson(reopened).get("played_character_id").bigIntegerValue());
            var publicActor = actor().put("character_id", id);
            publicActor.set("event_trait_membership", raw);
            if (id == -1)
                assertThrows(IllegalArgumentException.class, () -> normalize(publicActor), "unavailable absent metadata is not a valid outer actor");
            else
                assertEquals(actorId, normalize(publicActor).get("event_trait_membership").get("played_character_id").bigIntegerValue());
            if (id <= 0) {
                assertThrows(IllegalArgumentException.class, () -> new NativePlayerEventTraitMembership.Available(frame,
                        new NativePlayerEventTraitMembership.Traits(false, false)), "unavailable metadata cannot qualify available traits");
                var falseAvailable = raw.deepCopy().put("status", "available").putNull("unavailable_reason");
                falseAvailable.putObject("traits").put("lifestyle_poet", false).put("journaller", false);
                assertThrows(IllegalArgumentException.class,
                        () -> NativePlayerEventTraitMembership.read(falseAvailable, actorId, REVISION, DATE));
            }
            assertThrows(IllegalArgumentException.class,
                    () -> NativePlayerEventTraitMembership.read(wire, actorId.add(BigInteger.ONE), REVISION, DATE), "metadata still binds exact actor");
        }
        BigInteger belowSignedMinimum = BigInteger.valueOf(Integer.MIN_VALUE).subtract(BigInteger.ONE);
        assertThrows(IllegalArgumentException.class, () -> new NativePlayerEventTraitMembership.Frame(
                REVISION, BigInteger.valueOf(1000), belowSignedMinimum));
    }

    static List<Case> validCases() {
        List<Case> result = new ArrayList<>();
        add(result, "null", NullNode.instance); add(result, "missing", MissingNode.getInstance());
        add(result, "minimal", actor()); add(result, "native signed maximum", actor().put("character_id", Integer.MAX_VALUE)); add(result, "dead zero", actor().put("character_id", 0).put("alive", false));
        add(result, "stress zero", actor().put("stress_points", 0));
        add(result, "stress maximum", actor().put("stress_points", Integer.MAX_VALUE));
        add(result, "ignored source and extras", actor().putNull("source").put("unused", 9));
        add(result, "ignored source Python overflow float", actor().set("source", node("1e400")));
        add(result, "ignored unknown Python overflow float", actor().set("unused", node("{\"nested\":1e400}")));
        add(result, "false heir missing id", actor().put("has_heir", false));
        add(result, "false heir null id", actor().put("has_heir", false).putNull("primary_heir_id"));
        add(result, "true zero heir", actor().put("has_heir", true).put("primary_heir_id", 0));
        var none = actor().putNull("betrothed_id").putNull("primary_spouse_id"); none.putArray("spouse_ids"); add(result, "empty relationships", none);
        var noPrimary = actor().put("betrothed_id", 0).putNull("primary_spouse_id"); noPrimary.putArray("spouse_ids").add(9).add(2);
        add(result, "spouse list order without primary", noPrimary);
        var self = actor().put("betrothed_id", 73).put("primary_spouse_id", 73); self.putArray("spouse_ids").add(73);
        add(result, "no invented self or overlap rule", self);
        var available = actor(); available.set("event_trait_membership", membership(BigInteger.valueOf(73), REVISION, BigInteger.valueOf(1000)));
        add(result, "trait available", available);
        var unavailable = actor(); unavailable.set("event_trait_membership", membership(BigInteger.valueOf(73), REVISION, BigInteger.valueOf(1000))
                .put("status", "unavailable").putNull("traits").put("unavailable_reason", " "));
        add(result, "trait unavailable whitespace reason", unavailable);
        var broad = actor().put("character_id", Integer.MAX_VALUE);
        BigInteger rev = BigInteger.ONE.shiftLeft(90), date = BigInteger.ONE.shiftLeft(100).negate();
        broad.set("event_trait_membership", membership(BigInteger.valueOf(Integer.MAX_VALUE), rev, date).put("status", "unavailable").putNull("traits").put("unavailable_reason", "r".repeat(33000)));
        result.add(new Case("unbounded independent trait revision/date/reason", broad, rev, node(date.toString())));
        return List.copyOf(result);
    }

    static List<Case> invalidCases() {
        List<Case> result = new ArrayList<>();
        for (String raw : List.of("true", "1", "1.0", "[]", "\"\"", "{}", "{\"character_id\":73}", "{\"alive\":true}"))
            add(result, "invalid played shape " + raw, node(raw));
        for (String raw : List.of("null", "true", "1.0", "-1", "\"73\""))
            add(result, "invalid actor " + raw, actor().set("character_id", node(raw)));
        for (String raw : List.of("null", "1", "1.0", "\"true\""))
            add(result, "invalid alive " + raw, actor().set("alive", node(raw)));
        for (String raw : List.of("null", "true", "1.0", "-1", "2147483648", "\"1\""))
            add(result, "invalid stress " + raw, actor().set("stress_points", node(raw)));
        add(result, "heir id without boolean", actor().putNull("primary_heir_id"));
        add(result, "true heir missing id", actor().put("has_heir", true));
        add(result, "false heir conflicts id", actor().put("has_heir", false).put("primary_heir_id", 0));
        for (String raw : List.of("null", "true", "1.0", "-1", "\"2\""))
            add(result, "invalid true heir id " + raw, actor().put("has_heir", true).set("primary_heir_id", node(raw)));
        add(result, "nonboolean heir", actor().put("has_heir", 1).putNull("primary_heir_id"));
        add(result, "partial relationships", actor().putNull("betrothed_id"));
        for (String raw : List.of("null", "true", "1", "{}", "[1,1]", "[true]", "[1.0]", "[-1]", "[\"1\"]")) {
            var value = actor().putNull("betrothed_id").putNull("primary_spouse_id"); value.set("spouse_ids", node(raw));
            add(result, "invalid spouse list " + raw, value);
        }
        var absentPrimary = actor().putNull("betrothed_id").put("primary_spouse_id", 2); absentPrimary.putArray("spouse_ids").add(1);
        add(result, "primary not in spouse ids", absentPrimary);
        for (String field : List.of("betrothed_id", "primary_spouse_id")) for (String raw : List.of("true", "1.0", "-1", "\"1\"")) {
            var value = actor().putNull("betrothed_id").putNull("primary_spouse_id"); value.putArray("spouse_ids"); value.set(field, node(raw));
            add(result, "invalid relationship " + field + raw, value);
        }
        for (String raw : List.of("null", "true", "[]", "{}")) add(result, "invalid trait leaf " + raw, actor().set("event_trait_membership", node(raw)));
        for (String field : List.of("schema", "game_version", "executable_sha256", "status", "snapshot_revision", "date_raw",
                "played_character_id", "traits", "unavailable_reason")) {
            var membership = membership(BigInteger.valueOf(73), REVISION, BigInteger.valueOf(1000)); membership.remove(field);
            add(result, "missing trait field " + field, actor().set("event_trait_membership", membership));
        }
        for (String field : List.of("snapshot_revision", "date_raw", "played_character_id")) {
            for (String raw : List.of("null", "true", "1.0", "\"17\"")) {
                var membership = membership(BigInteger.valueOf(73), REVISION, BigInteger.valueOf(1000)); membership.set(field, node(raw));
                add(result, "invalid trait integer " + field + raw, actor().set("event_trait_membership", membership));
            }
        }
        var wrong = membership(BigInteger.valueOf(74), REVISION, BigInteger.valueOf(1000)); add(result, "trait actor differs", actor().set("event_trait_membership", wrong));
        wrong = membership(BigInteger.valueOf(73), REVISION.add(BigInteger.ONE), BigInteger.valueOf(1000)); add(result, "trait revision differs", actor().set("event_trait_membership", wrong));
        wrong = membership(BigInteger.valueOf(73), REVISION, BigInteger.valueOf(1001)); add(result, "trait date differs", actor().set("event_trait_membership", wrong));
        wrong = membership(BigInteger.valueOf(73), REVISION, BigInteger.valueOf(1000)).put("extra", true); add(result, "unknown trait field", actor().set("event_trait_membership", wrong));
        var badTraits = membership(BigInteger.valueOf(73), REVISION, BigInteger.valueOf(1000)); ((ObjectNode) badTraits.get("traits")).put("lifestyle_poet", 1);
        add(result, "trait value not boolean", actor().set("event_trait_membership", badTraits));
        var badUnavailable = membership(BigInteger.valueOf(73), REVISION, BigInteger.valueOf(1000)).put("status", "unavailable").putNull("traits").put("unavailable_reason", "");
        add(result, "empty unavailable reason", actor().set("event_trait_membership", badUnavailable));
        var nullAvailable = membership(BigInteger.valueOf(73), REVISION, BigInteger.valueOf(1000)).putNull("traits");
        add(result, "available null traits", actor().set("event_trait_membership", nullAvailable));
        for (String field : List.of("schema", "game_version", "executable_sha256", "status")) {
            var changed = membership(BigInteger.valueOf(73), REVISION, BigInteger.valueOf(1000)).put(field, "wrong");
            add(result, "wrong trait identity or status " + field, actor().set("event_trait_membership", changed));
        }
        var reasonPresent = membership(BigInteger.valueOf(73), REVISION, BigInteger.valueOf(1000)).put("unavailable_reason", "unexpected");
        add(result, "available reason not null", actor().set("event_trait_membership", reasonPresent));
        var unavailableValues = membership(BigInteger.valueOf(73), REVISION, BigInteger.valueOf(1000)).put("status", "unavailable").put("unavailable_reason", "reason");
        add(result, "unavailable values not null", actor().set("event_trait_membership", unavailableValues));
        for (String raw : List.of("true", "null", "1", "1.0")) {
            var changed = membership(BigInteger.valueOf(73), REVISION, BigInteger.valueOf(1000)).put("status", "unavailable").putNull("traits");
            changed.set("unavailable_reason", node(raw)); add(result, "invalid unavailable reason " + raw, actor().set("event_trait_membership", changed));
        }
        var zeroActor = actor().put("character_id", 0); zeroActor.set("event_trait_membership", membership(BigInteger.ZERO, REVISION, BigInteger.valueOf(1000)));
        add(result, "trait zero player", zeroActor);
        result.add(new Case("trait context null date", actor().set("event_trait_membership", membership(BigInteger.valueOf(73), REVISION, BigInteger.valueOf(1000))), REVISION, NullNode.instance));
        result.add(new Case("trait context missing date", actor().set("event_trait_membership", membership(BigInteger.valueOf(73), REVISION, BigInteger.valueOf(1000))), REVISION, MissingNode.getInstance()));
        result.add(new Case("trait context zero revision", actor().set("event_trait_membership", membership(BigInteger.valueOf(73), REVISION, BigInteger.valueOf(1000))), BigInteger.ZERO, DATE));
        for (String raw : List.of("true", "1.0", "\"1000\""))
            result.add(new Case("trait noninteger context date " + raw, actor().set("event_trait_membership", membership(BigInteger.valueOf(73), REVISION, BigInteger.valueOf(1000))), REVISION, node(raw)));
        return List.copyOf(result);
    }
    static ObjectNode actor() { return StrictJson.object().put("character_id", 73).put("alive", true); }
    static ObjectNode membership(BigInteger actor, BigInteger revision, BigInteger date) {
        var frame = new NativePlayerEventTraitMembership.Frame(revision.signum() > 0 ? revision : BigInteger.ONE, date, actor.signum() > 0 ? actor : BigInteger.ONE);
        var result = NativePlayerEventTraitMembership.toJson(new NativePlayerEventTraitMembership.Available(frame,
                new NativePlayerEventTraitMembership.Traits(false, true)));
        return result.put("snapshot_revision", revision).put("played_character_id", actor);
    }
    static JsonNode node(String raw) { return StrictJson.parse(raw.getBytes(StandardCharsets.UTF_8), StrictJson.EXPLICIT_MAX_BYTES); }
    private static JsonNode normalize(JsonNode value) { return NativePlayedCharacter.normalize(value, REVISION, DATE); }
    private static void add(List<Case> cases, String name, JsonNode value) { cases.add(new Case(name, value, REVISION, DATE)); }
}
