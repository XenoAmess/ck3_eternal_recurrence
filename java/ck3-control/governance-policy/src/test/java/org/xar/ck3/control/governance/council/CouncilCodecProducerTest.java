package org.xar.ck3.control.governance.council;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.OptionalInt;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.governance.council.CouncilModels.*;

/** Original retained native producer, with separate synthetic corruption cases. Missing originals fail. */
final class CouncilCodecProducerTest {
    private static final Frame FRAME = new Frame("native:council12002", BigInteger.valueOf(8), BigInteger.valueOf(7), 53178264, 16777217);
    private static final String SHA = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
    private static ObjectNode original() throws Exception {
        String root = System.getProperty("xar.repository.root");
        assertNotNull(root, "required retained producer repository was not supplied");
        return CouncilCodec.object(StrictJson.parse(Files.readAllBytes(Path.of(root,
                "ck3_autonomous_player/tests/fixtures/native_12002/governance/council-query.json")))
                .get("result").get("council_composition_candidates"));
    }
    private static ObjectNode core() throws Exception {
        ObjectNode source = original(), core = StrictJson.object();
        CouncilCodec.PAYLOAD_FIELDS.forEach(field -> core.set(field, source.get(field))); return core;
    }
    @Test void retainedNativeProducerProjectsOnceAndRoundTrips() throws Exception {
        Candidates value = CouncilCodec.decodeNative(StrictJson.canonical(original()), FRAME, Position.STEWARD, "1.20.0.2", SHA);
        assertEquals(2, value.candidates().size()); assertEquals(22, value.candidates().get(0).mainSkill());
        assertEquals(OptionalInt.of(16777218), value.seat().incumbentId()); assertTrue(value.seat().tax().isEmpty());
        assertEquals(core(), StrictJson.parse(CouncilCodec.encode(value)));
        assertEquals(value, CouncilCodec.decode(CouncilCodec.encode(value), FRAME, Position.STEWARD));
    }
    @Test void malformedTaxCannotRideAnOtherwiseReadyCandidate() throws Exception {
        ObjectNode core = core(), tax = StrictJson.object();
        tax.put("status", "available").putNull("unavailable_reason").put("active_task_id", 6100)
                .put("owner_character_id", 16777217).put("incumbent_character_id", 16777218)
                .put("task_key", "collect_taxes").put("frozen", false).put("modifier_id", 162)
                .put("keyword_id", 11976).put("observed_keyword_key", "domain_tax_mult");
        tax.set("value", StrictJson.object().put("raw", -5000).put("scale", 100000));
        CouncilCodec.object(core.get("position")).set("current_task_owner_domain_tax_mult_v1", tax);
        var value = CouncilCodec.decode(StrictJson.canonical(core), FRAME, Position.STEWARD);
        assertEquals(-5000, ((AvailableTax) value.seat().tax().orElseThrow()).value().raw());
        tax.put("keyword_id", true);
        assertThrows(IllegalArgumentException.class, () -> CouncilCodec.decode(StrictJson.canonical(core), FRAME, Position.STEWARD));
    }
    @Test void missingFieldsWrongTypesAndFrameDriftFail() throws Exception {
        ObjectNode core = core(); core.remove("readiness");
        assertThrows(IllegalArgumentException.class, () -> CouncilCodec.decode(StrictJson.canonical(core), FRAME, Position.STEWARD));
        ObjectNode wrong = core(); CouncilCodec.object(wrong.get("snapshot")).put("public_revision", 8.0);
        assertThrows(IllegalArgumentException.class, () -> CouncilCodec.decode(StrictJson.canonical(wrong), FRAME, Position.STEWARD));
    }
}
