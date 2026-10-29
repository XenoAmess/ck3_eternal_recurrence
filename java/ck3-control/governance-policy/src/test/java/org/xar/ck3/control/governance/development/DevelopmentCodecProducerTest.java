package org.xar.ck3.control.governance.development;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilCodec;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.governance.development.DevelopmentModels.*;

/** Actual .3 native serialized originals remain .3 evidence; corruptions are explicitly synthetic. */
final class DevelopmentCodecProducerTest {
    private static final Frame FRAME = new Frame(BigInteger.valueOf(77), 53328600);
    private static ObjectNode original(String name) throws Exception {
        String root = System.getProperty("xar.repository.root");
        assertNotNull(root, "required retained native producer originals were not supplied");
        return CouncilCodec.object(StrictJson.parse(Files.readAllBytes(Path.of(root,
                "ck3_autonomous_player/tests/fixtures/steward_develop_county_12003_material/" + name + ".json")))
                .get("result").get("steward_develop_county_candidates"));
    }
    @Test void nativeAvailableOriginalRetainsFalsePredicatesAndNegativeGrowth() throws Exception {
        ObjectNode original = original("develop_material_available");
        Material value = (Material) DevelopmentCodec.decode(StrictJson.canonical(original), FRAME);
        assertEquals(3, value.candidates().size()); assertEquals(-750, value.candidates().get(1).monthlyRate().raw());
        assertFalse(value.candidates().get(2).nativeTargetValid());
        assertEquals("1.20.0.3", value.provenance().gameVersion());
        assertInstanceOf(General.class, value.currentBinding().target());
        assertEquals(original, StrictJson.parse(DevelopmentCodec.encode(value)));
        assertEquals(value, DevelopmentCodec.decode(DevelopmentCodec.encode(value), FRAME));
    }
    @Test void nativeBlockedTaskIsReadyObservationAndCannotInventCandidates() throws Exception {
        ObjectNode original = original("develop_material_blocked");
        Material value = (Material) DevelopmentCodec.decode(StrictJson.canonical(original), FRAME);
        assertTrue(value.candidates().isEmpty()); assertFalse(value.shown() && value.valid());
        original.put("readiness", false);
        assertThrows(IllegalArgumentException.class, () -> DevelopmentCodec.decode(StrictJson.canonical(original), FRAME));
    }
    @Test void identityTypeScaleSourceAndDateMutationsFail() throws Exception {
        ObjectNode wrong = original("develop_material_available"); wrong.put("player_character_id", true);
        assertThrows(IllegalArgumentException.class, () -> DevelopmentCodec.decode(StrictJson.canonical(wrong), FRAME));
        ObjectNode missing = original("develop_material_available"); missing.remove("current_active_task_binding");
        assertThrows(IllegalArgumentException.class, () -> DevelopmentCodec.decode(StrictJson.canonical(missing), FRAME));
        ObjectNode source = original("develop_material_available"); CouncilCodec.object(source.get("provenance")).put("game_version", "1.20.0.4");
        assertThrows(IllegalArgumentException.class, () -> DevelopmentCodec.decode(StrictJson.canonical(source), FRAME));
        assertThrows(IllegalArgumentException.class, () -> DevelopmentCodec.decode(StrictJson.canonical(original("develop_material_available")), new Frame(BigInteger.valueOf(77), 1)));
    }
    @Test void frozenOriginalProvenanceRejectsCaseChangedHashLikeThePythonProducer() throws Exception {
        ObjectNode original = original("develop_material_available");
        assertInstanceOf(Material.class, DevelopmentCodec.decode(StrictJson.canonical(original), FRAME));
        ObjectNode provenance = CouncilCodec.object(original.get("provenance"));
        provenance.put("executable_sha256", provenance.get("executable_sha256").textValue().toLowerCase(java.util.Locale.ROOT));
        assertThrows(IllegalArgumentException.class, () -> DevelopmentCodec.decode(StrictJson.canonical(original), FRAME));
    }
}
