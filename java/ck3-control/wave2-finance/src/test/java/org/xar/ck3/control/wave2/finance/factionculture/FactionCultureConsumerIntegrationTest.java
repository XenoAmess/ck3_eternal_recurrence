package org.xar.ck3.control.wave2.finance.factionculture;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertsCodec;

import java.io.IOException;
import java.io.InputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.xar.ck3.control.wave2.finance.factionculture.FactionCultureModel.*;

/** Runs the complete sibling normalizer and shared culture projection against original producer data. */
final class FactionCultureConsumerIntegrationTest {
    private static final ObjectMapper JSON = new ObjectMapper();

    @Test
    void fullAlertNormalizerAndSharedCultureProjectionRetainAllNonCultureNativeInputs() throws IOException, NoSuchAlgorithmException {
        JsonNode golden = alertGolden();
        for (String name : new String[]{"county-native-material", "signed-full-culture-ids", "partial-culture-keeps-zero-id"}) {
            JsonNode vector = vector(golden, name);
            ObjectNode input = materialize(golden, vector);
            FactionAlertsCodec.Normalized normalized = FactionAlertsCodec.normalize(JSON.writeValueAsBytes(input),
                    FactionAlertsCodec.expected(JSON.writeValueAsBytes(vector.path("expected_frame"))));
            FactionAlertsCodec.validateWarHandoffs(normalized.frame(), JSON.writeValueAsBytes(vector.path("active_wars")));
            byte[] canonical = StrictJson.canonical(JSON.readTree(normalized.json()), FactionAlertsCodec.MAX_BYTES);
            assertEquals(vector.path("expected_sha256").textValue(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(canonical)));

            Context context = FactionCultureCodec.projectNormalizedAlert(normalized.json());
            JsonNode whole = JSON.readTree(normalized.json());
            assertEquals(whole.path("snapshot_revision").bigIntegerValue(), context.frame().snapshotRevision());
            assertEquals(whole.path("date_raw").intValue(), context.frame().dateRaw());
            assertEquals(whole.path("player_character_id").intValue(), context.frame().playerCharacterId());
            assertEquals(whole.path("provenance"), JSON.readTree(context.provenance().json()));

            JsonNode sourceFaction = whole.path("targeting_factions").get(1);
            int factionId = sourceFaction.path("faction_id").intValue();
            int countyId = sourceFaction.path("county_member_observations").get(0).path("county_title_id").intValue();
            ContextRow row = context.rows().stream().filter(item -> item.factionId() == factionId && item.countyTitleId() == countyId)
                    .findFirst().orElseThrow();
            if (name.equals("signed-full-culture-ids")) {
                assertEquals(Optional.of(new AvailableCulture(-2, -2, true)), row.relation());
                assertTrue(row.relationInputReady());
            } else if (name.equals("partial-culture-keeps-zero-id")) {
                assertEquals(Optional.of(new UnavailableCulture(Optional.of(0), Optional.empty())), row.relation());
                assertFalse(row.relationInputReady());
                assertEquals(Optional.of(UnavailableReason.CULTURE_RELATION_UNAVAILABLE), row.unavailableReason());
            } else {
                assertTrue(row.relation().isEmpty());
                assertEquals(Optional.of(UnavailableReason.CULTURE_FIELDS_NOT_PUBLISHED), row.unavailableReason());
            }
        }
    }

    private static ObjectNode materialize(JsonNode golden, JsonNode vector) {
        ObjectNode root = (ObjectNode) golden.path("bases").get(vector.path("base").textValue()).deepCopy();
        for (JsonNode operation : vector.path("operations")) {
            String pointer = operation.path("path").textValue();
            int separator = pointer.lastIndexOf('/');
            JsonNode parent = root.at(pointer.substring(0, separator));
            String key = pointer.substring(separator + 1);
            if (parent instanceof ObjectNode object) {
                if (operation.path("remove").booleanValue()) object.remove(key);
                else object.set(key, operation.get("value").deepCopy());
            } else if (parent instanceof ArrayNode array) {
                int index = Integer.parseInt(key);
                if (operation.path("remove").booleanValue()) array.remove(index);
                else array.set(index, operation.get("value").deepCopy());
            } else throw new IllegalArgumentException("invalid retained producer operation " + pointer);
        }
        return root;
    }

    private static JsonNode vector(JsonNode root, String name) {
        for (JsonNode vector : root.path("cases")) if (name.equals(vector.path("name").textValue())) return vector;
        throw new IllegalArgumentException("missing original producer sample " + name);
    }

    private static JsonNode alertGolden() throws IOException {
        try (InputStream input = FactionCultureConsumerIntegrationTest.class.getResourceAsStream("/factionalerts/original-producer-golden.json")) {
            assertNotNull(input, "complete original alert normalizer golden required; no skipped substitute");
            byte[] bytes = input.readNBytes(FactionAlertsCodec.MAX_BYTES + 1);
            assertTrue(bytes.length <= FactionAlertsCodec.MAX_BYTES);
            return JSON.readTree(bytes);
        }
    }
}
