package org.xar.ck3.control.g2.m6;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.m6.G2M6Contracts.NativeSubject;

/** Explicit synthetic character substitutions in the original producer corpus; no native action credit. */
final class M6NativeCharacterFacadeTest {
    @ParameterizedTest
    @ValueSource(longs = {Integer.MIN_VALUE, -2, 0, 1, Integer.MAX_VALUE})
    void typedActorPreservesNativeSignedCharacterDomain(long actor) {
        NativeCharacterId.of(actor);
        assertEquals(actor, new NativeSubject(actor, 17, 0, 0).actorCharacterId());
    }

    @ParameterizedTest
    @ValueSource(longs = {Integer.MIN_VALUE, -2, 0, 1, Integer.MAX_VALUE})
    void typedTargetPreservesNativeSignedCharacterDomain(long target) {
        NativeCharacterId.of(target);
        assertEquals(target, new NativeSubject(17, target, 0, 0).targetCharacterId());
    }

    @ParameterizedTest
    @ValueSource(longs = {-1, -2147483649L, 2147483648L, 4294967295L})
    void typedActorRefusesAbsentOrOutsideSignedIdentity(long actor) {
        assertThrows(IllegalArgumentException.class, () -> NativeCharacterId.of(actor));
        assertThrows(IllegalArgumentException.class, () -> new NativeSubject(actor, 17, 0, 0));
    }

    @ParameterizedTest
    @ValueSource(longs = {-1, -2147483649L, 2147483648L, 4294967295L})
    void typedTargetRefusesAbsentOrOutsideSignedIdentity(long target) {
        assertThrows(IllegalArgumentException.class, () -> NativeCharacterId.of(target));
        assertThrows(IllegalArgumentException.class, () -> new NativeSubject(17, target, 0, 0));
    }

    @ParameterizedTest
    @ValueSource(longs = {Integer.MIN_VALUE, -2, 0, 1, Integer.MAX_VALUE})
    void originalProducerToPublicFacadePreservesActorAndTarget(long actor) throws IOException {
        NativeCharacterId.of(actor);
        long target = actor == 0 ? -2 : 0;
        NativeCharacterId.of(target);
        ObjectNode root = (ObjectNode) StrictJson.parse(M6SourceProducerTest.ledger());
        replaceCharacter(root, "actor_character_id", StrictJson.parse(Long.toString(actor).getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        JsonNode targetNode = StrictJson.parse(Long.toString(target).getBytes(java.nio.charset.StandardCharsets.UTF_8));
        replaceCharacter(root, "target_character_id", targetNode);
        replaceCharacter(root, "last_target_character_id", targetNode);
        byte[] raw = StrictJson.canonical(root, M6SourceProducer.MAX_BYTES);
        var source = M6SourceProducerTest.source(raw, "memory:synthetic-m6-native-character");
        var result = new M6Research().evaluate(new G2Request("m6-native-character", Milestone.M6, source,
                ProjectionJson.object(raw, M6SourceProducer.MAX_BYTES)));
        JsonNode output = StrictJson.parse(result.result().bytes());
        assertEquals(2, output.get("episodes").size());
        for (JsonNode row : output.get("episodes")) {
            assertEquals(actor, row.get("actor_character_id").longValue());
            assertEquals(target, row.get("target_character_id").longValue());
        }
        assertFalse(output.get("grants_submission_authority").booleanValue());
        assertEquals(0, output.get("game_day_credit").intValue());
    }

    @ParameterizedTest
    @ValueSource(strings = {"true", "0.0", "\"0\"", "null", "-1", "-2147483649", "2147483648", "4294967295"})
    void producerRejectsWrongCharacterTokensWithFreshSyntheticSourceHash(String token) throws IOException {
        ObjectNode root = (ObjectNode) StrictJson.parse(M6SourceProducerTest.ledger());
        String marker = "__M6_NATIVE_CHARACTER_TOKEN__";
        replaceCharacter(root, "actor_character_id", com.fasterxml.jackson.databind.node.TextNode.valueOf(marker));
        byte[] raw = root.toString().replace("\"" + marker + "\"", token).getBytes(java.nio.charset.StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> M6SourceProducer.fromClosedLedger(raw,
                M6SourceProducerTest.source(raw, "memory:synthetic-invalid-m6-character")));
    }

    private static void replaceCharacter(JsonNode node, String field, JsonNode replacement) {
        if (node.isObject()) {
            ObjectNode object = (ObjectNode) node;
            List<String> fields = new ArrayList<>(); object.fieldNames().forEachRemaining(fields::add);
            for (String name : fields) {
                if (name.equals(field)) { object.set(name, replacement.deepCopy()); }
                else { replaceCharacter(object.get(name), field, replacement); }
            }
        } else if (node.isArray()) {
            for (JsonNode child : node) { replaceCharacter(child, field, replacement); }
        }
    }
}
