package org.xar.ck3.control.wave3.planning.scorestate;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Properties;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

final class CampaignScoreCompatibilityInputsTest {
    @TempDir Path temporary;

    @Test void recordedMetadataRoundtripsWithoutOpeningTodaysReferenceOrRepository() {
        var selected = recorded();
        assertFalse(Files.exists(selected.python()));
        assertFalse(Files.exists(selected.repository()));
        byte[] wire = selected.encode();
        var reconstructed = CampaignScoreCompatibilityInputs.decode(wire);
        assertEquals(selected, reconstructed);
        assertEquals(selected, CampaignScoreCompatibilityInputs.fromProperties(reconstructed.properties()));
        assertArrayEquals(wire, reconstructed.encode());
        assertFalse(Files.exists(selected.repository()));
        assertEquals("seven-named-score-consumers-reference-only/v1", StrictJson.text(reconstructed.json().get("scope")));
    }

    @Test void eachRecordedRolePropertyIsMandatoryWithNoEnvironmentJsonOrMeasuredHashFallback() {
        Properties original = recorded().properties();
        for (String name : original.stringPropertyNames()) {
            Properties missing = recorded().properties(); missing.remove(name);
            missing.setProperty("XAR_SCORE_REFERENCE_CLIENT_REF", recorded().referenceClient().toJson().toString());
            assertThrows(IllegalArgumentException.class, () -> CampaignScoreCompatibilityInputs.fromProperties(missing), name);
        }
        for (String value : List.of("024703", "24703.0", "true", "-1", "0", " 24703")) {
            Properties invalid = recorded().properties(); invalid.setProperty("xar.fullParity.fixture.SCORE_COMPATIBILITY_CANDIDATE.bytes", value);
            assertThrows(IllegalArgumentException.class, () -> CampaignScoreCompatibilityInputs.fromProperties(invalid), value);
        }
        Properties changed = recorded().properties(); changed.setProperty("xar.score.compat.candidate.sha256", "0".repeat(64));
        assertThrows(IllegalArgumentException.class, () -> CampaignScoreCompatibilityInputs.fromProperties(changed));
    }

    @Test void exactWireRejectsAliasesWrongNumericDomainsMissingSourcesAndSdkRoleSubstitution() {
        ObjectNode valid = recorded().json();
        ObjectNode extra = valid.deepCopy(); extra.put("current_sdk_qualified", true); rejected(extra);
        ObjectNode scope = valid.deepCopy(); scope.put("scope", "fresh-current-sdk/v1"); rejected(scope);
        ObjectNode missing = valid.deepCopy(); missing.remove("reference_client"); rejected(missing);
        ObjectNode boolBytes = valid.deepCopy(); ((ObjectNode)boolBytes.get("candidate")).put("bytes", true); rejected(boolBytes);
        ObjectNode floating = valid.deepCopy(); ((ObjectNode)floating.get("candidate")).put("bytes", 24703.0); rejected(floating);
        ObjectNode forged = valid.deepCopy(); ((ObjectNode)forged.get("candidate")).put("sha256", "0".repeat(64)); rejected(forged);
        ObjectNode swapped = valid.deepCopy(); swapped.set("candidate", valid.get("reference_client")); swapped.set("reference_client", valid.get("candidate")); rejected(swapped);
        ObjectNode alias = valid.deepCopy(); ((ObjectNode)alias.get("reference_client")).put("reference", true); rejected(alias);
        ObjectNode dropped = valid.deepCopy(); dropped.putArray("original_sources"); rejected(dropped);
        ObjectNode altered = valid.deepCopy(); ((ObjectNode)altered.get("original_sources").get(0)).put("sha256", "0".repeat(64)); rejected(altered);
    }

    @Test void actualContentIsRecheckedEvenWhenPathAndByteCountRemainEqual() throws Exception {
        Path file = temporary.resolve("original-reference.py"); Files.writeString(file, "abc", StandardCharsets.UTF_8);
        ExactRef original = new ExactRef(file.toString(), 3, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
        assertArrayEquals("abc".getBytes(StandardCharsets.UTF_8), CampaignScoreCompatibilityInputs.verifyFile(original));
        Files.writeString(file, "abd", StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> CampaignScoreCompatibilityInputs.verifyFile(original));
        Files.writeString(file, "abcd", StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> CampaignScoreCompatibilityInputs.verifyFile(original));
    }

    private CampaignScoreCompatibilityInputs.Selected recorded() {
        return new CampaignScoreCompatibilityInputs.Selected(temporary.resolve("missing-python.exe"), temporary.resolve("missing-repository"),
                new ExactRef(temporary.resolve("candidate.py").toString(), 24703, "65737d5a2082a83fe5c4ab63b057ce6d49f400a54f20bc8b661361acf6c598bf"),
                new ExactRef(temporary.resolve("reference-only-client.py").toString(), 201161, "0415281fd865bb7e9bbf68175caca2c6ee25a265f194ff5bb623870bea34c970"));
    }
    private static void rejected(ObjectNode value) { assertThrows(IllegalArgumentException.class, () -> CampaignScoreCompatibilityInputs.decode(StrictJson.canonical(value))); }
}
