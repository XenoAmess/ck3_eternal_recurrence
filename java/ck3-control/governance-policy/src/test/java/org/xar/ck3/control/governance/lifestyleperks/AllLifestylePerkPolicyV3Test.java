package org.xar.ck3.control.governance.lifestyleperks;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.lifestyleperks.LifestylePerksModel.*;

class AllLifestylePerkPolicyV3Test {
    @Test void unchangedLegacyProducerGoldenAndRetainedNativeProjectionMatch() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.java.lifestyle-perks-legacy-golden.v1", golden.get("schema").textValue());
        assertEquals(AuthoredPerkCatalog.ORIGINAL_CATALOG_SHA256, golden.get("original_catalog_sha256").textValue());
        assertEquals(21, golden.get("cases").size());
        for (JsonNode sample : golden.get("cases")) {
            Input input = LifestylePerksCodec.decode(StrictJson.canonical(sample.get("input")));
            JsonNode actual = StrictJson.parse(LifestylePerksCodec.encodeDecision(AllLifestylePerkPolicyV3.choose(input)));
            assertEquals(sample.get("expected"), actual, sample.get("name").textValue());
            assertEquals(input, LifestylePerksCodec.decode(LifestylePerksCodec.encodeInput(input)), sample.get("name").textValue());
        }
    }

    @Test void boolFloatStringNullMissingIntegerAndBoundaryXpRejectAtRuntime() throws IOException {
        for (String bad : List.of("true", "1.0", "\"1\"", "null", "-1")) {
            ObjectNode sample = firstInput();
            BigInteger sentinel = new BigInteger("987654321098765432109876543210");
            ((ObjectNode) sample.at("/snapshot/all_lifestyle_progress_v3/rows/0")).put("unspent_perk_points", sentinel);
            String encoded = sample.toString(); String needle = "\"unspent_perk_points\":" + sentinel;
            assertEquals(encoded.indexOf(needle), encoded.lastIndexOf(needle), "one exact injection site");
            assertTrue(encoded.contains(needle), "injection site must exist");
            String actualWire = encoded.replace(needle, "\"unspent_perk_points\":" + bad);
            assertTrue(actualWire.contains("\"unspent_perk_points\":" + bad), "actual outgoing token must be retained: " + bad);
            assertThrows(IllegalArgumentException.class,
                    () -> LifestylePerksCodec.decode(actualWire.getBytes(StandardCharsets.UTF_8)), bad);
        }
        ObjectNode missing = firstInput();
        ((ObjectNode) missing.at("/snapshot/all_lifestyle_progress_v3/rows/0")).remove("used_perk_points");
        assertThrows(IllegalArgumentException.class, () -> LifestylePerksCodec.decode(StrictJson.canonical(missing)));
        ObjectNode zeroLevel = firstInput();
        ((ObjectNode) zeroLevel.at("/snapshot/all_lifestyle_progress_v3/rows/0")).put("xp_per_level", 0);
        assertThrows(IllegalArgumentException.class, () -> LifestylePerksCodec.decode(StrictJson.canonical(zeroLevel)));
        ObjectNode boundary = firstInput();
        ((ObjectNode) boundary.at("/snapshot/all_lifestyle_progress_v3/rows/0")).put("xp_within_level_raw", 100_000_000);
        assertThrows(IllegalArgumentException.class, () -> LifestylePerksCodec.decode(StrictJson.canonical(boundary)));
    }

    @Test void originalPythonIntegerDomainUsesBigIntegerWithoutJavascriptRounding() throws IOException {
        ObjectNode sample = firstInput();
        BigInteger huge = new BigInteger("184467440737095516160000000000000001");
        ObjectNode first = (ObjectNode) sample.at("/snapshot/all_lifestyle_progress_v3/rows/0");
        first.put("unspent_perk_points", huge); first.put("used_perk_points", huge);
        Input decoded = LifestylePerksCodec.decode(StrictJson.canonical(sample));
        Recommendation recommendation = assertInstanceOf(Recommendation.class, AllLifestylePerkPolicyV3.choose(decoded));
        assertEquals(huge, recommendation.observedTargetPoints());
        assertEquals(huge, StrictJson.parse(LifestylePerksCodec.encodeDecision(recommendation)).get("observed_target_points").bigIntegerValue());
        assertEquals(decoded, LifestylePerksCodec.decode(LifestylePerksCodec.encodeInput(decoded)));
    }

    @Test void newWrapperAndBindingRejectUnknownDuplicateTrailingAndInvalidUtf8() throws IOException {
        ObjectNode unknown = firstInput(); unknown.put("fallback", true);
        assertThrows(IllegalArgumentException.class, () -> LifestylePerksCodec.decode(StrictJson.canonical(unknown)));
        ObjectNode binding = firstInput(); ((ObjectNode) binding.get("binding")).put("expected_date", 1);
        assertThrows(IllegalArgumentException.class, () -> LifestylePerksCodec.decode(StrictJson.canonical(binding)));
        String valid = new String(StrictJson.canonical(firstInput()), StandardCharsets.UTF_8);
        String duplicate = valid.replaceFirst("\\{", "{\"schema\":\"duplicated\",");
        assertThrows(IllegalArgumentException.class, () -> LifestylePerksCodec.decode(duplicate.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> LifestylePerksCodec.decode((valid + " {}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> LifestylePerksCodec.decode(new byte[]{(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> LifestylePerksCodec.decode(new byte[65_537]));
    }

    @Test void expectedBindingCannotBeForgedAndUnavailableIsNotMissingOrZero() throws IOException {
        ObjectNode binding = firstInput(); ((ObjectNode) binding.get("binding")).put("expected_native_revision", 3499);
        assertThrows(IllegalArgumentException.class, () -> LifestylePerksCodec.decode(StrictJson.canonical(binding)));
        ObjectNode nullProgress = firstInput(); ((ObjectNode) nullProgress.get("snapshot")).putNull("all_lifestyle_progress_v3");
        assertThrows(IllegalArgumentException.class, () -> LifestylePerksCodec.decode(StrictJson.canonical(nullProgress)));
        ObjectNode missingProgress = firstInput(); ((ObjectNode) missingProgress.get("snapshot")).remove("all_lifestyle_progress_v3");
        assertThrows(IllegalArgumentException.class, () -> LifestylePerksCodec.decode(StrictJson.canonical(missingProgress)));
        ObjectNode partial = firstInput();
        ((ObjectNode) partial.at("/snapshot/all_lifestyle_progress_v3")).put("status", "partial");
        ObjectNode unavailable = (ObjectNode) partial.at("/snapshot/all_lifestyle_progress_v3/rows/5");
        unavailable.put("status", "unavailable"); unavailable.putNull("unavailable_reason");
        assertThrows(IllegalArgumentException.class, () -> LifestylePerksCodec.decode(StrictJson.canonical(partial)));
    }

    @Test void catalogIsPinnedCompleteOrderedAndImmutableAndNativeChoiceIsRetained() throws IOException {
        assertEquals(162, AuthoredPerkCatalog.perks().size());
        for (Lifestyle lifestyle : Lifestyle.values()) {
            assertEquals(27, AuthoredPerkCatalog.perks().values().stream().filter(lifestyle::equals).count());
        }
        assertThrows(UnsupportedOperationException.class, () -> AuthoredPerkCatalog.perks().clear());
        ObjectNode sample = firstInput();
        List<String> diplomacy = AuthoredPerkCatalog.perks().entrySet().stream()
                .filter(entry -> entry.getValue() == Lifestyle.DIPLOMACY).map(java.util.Map.Entry::getKey).toList();
        String nativeLast = diplomacy.getLast();
        ((ObjectNode) sample.at("/snapshot/legal_perk_candidates/items/0")).put("key", nativeLast);
        Recommendation result = assertInstanceOf(Recommendation.class,
                AllLifestylePerkPolicyV3.choose(LifestylePerksCodec.decode(StrictJson.canonical(sample))));
        assertEquals(nativeLast, result.action().targetKey());
        assertFalse(result.action().targetKey().equals(diplomacy.getFirst()));
    }

    @Test void domainModelsDefensivelyCopyAndPermitNoExecutionOrReplayState() throws IOException {
        Input decoded = LifestylePerksCodec.decode(StrictJson.canonical(firstInput()));
        List<String> owned = new ArrayList<>();
        Input copied = new Input(decoded.snapshotFrame(), decoded.progress(), decoded.candidates(), decoded.binding(), owned);
        owned.add("thoughtful_perk"); assertTrue(copied.owned().isEmpty());
        assertThrows(UnsupportedOperationException.class, () -> copied.owned().add("thoughtful_perk"));
        assertThrows(UnsupportedOperationException.class, () -> copied.progress().rows().clear());
        assertEquals(Status.RECOMMEND_ACTION, AllLifestylePerkPolicyV3.choose(copied).status());
    }

    @Test void legacySnapshotExtensionsRemainPermittedButConsumedFieldsRemainStrict() throws IOException {
        ObjectNode extended = firstInput();
        ((ObjectNode) extended.get("snapshot")).putObject("future_native_detail").put("new", true);
        ((ObjectNode) extended.at("/snapshot/all_lifestyle_progress_v3/rows/0")).put("native_detail", "retained only in original");
        assertEquals(Status.RECOMMEND_ACTION, AllLifestylePerkPolicyV3.choose(
                LifestylePerksCodec.decode(StrictJson.canonical(extended))).status());
        ObjectNode foreign = firstInput();
        ((ObjectNode) foreign.at("/snapshot/legal_perk_candidates/items/0")).put("key", "invented_perk");
        ObservationUnavailable result = assertInstanceOf(ObservationUnavailable.class, AllLifestylePerkPolicyV3.choose(
                LifestylePerksCodec.decode(StrictJson.canonical(foreign))));
        assertEquals(Reason.TARGET_OUTSIDE_AUTHORED, result.reason());
    }

    private static ObjectNode firstInput() throws IOException {
        return (ObjectNode) golden().get("cases").get(0).get("input").deepCopy();
    }
    private static JsonNode golden() throws IOException {
        try (InputStream stream = AllLifestylePerkPolicyV3Test.class.getResourceAsStream("/lifestyleperks/legacy-golden-v1.json")) {
            assertNotNull(stream, "committed producer golden is mandatory");
            return StrictJson.parse(stream.readAllBytes());
        }
    }
}
