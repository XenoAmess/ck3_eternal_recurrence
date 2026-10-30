package org.xar.ck3.control.nativebridge.capabilities.interactions;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.OptionalLong;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave3.governance.heirintake.HeirCandidateIntakeConsumerPort;

/** Retained worker100 Native ACK and request DATA; no Root Known, entry, live receipt or lease is created. */
final class FamilyHeirLargeIntakeTest {
    private static final String RESOURCE = "/familyheir/worker100/";
    private static final List<BigInteger> PICKED = List.of(40408, 65697, 40419, 65672, 40506)
            .stream().map(BigInteger::valueOf).toList();

    @Test void retainedWorker100AcknowledgementProjectsAll833RowsIntoRealCandidateIntake() throws Exception {
        var actual = actual();
        var observation = FamilyHeirLegality.decode(raw(actual.result()), actual.binding());
        assertEquals(BigInteger.valueOf(31254), actual.binding().context().actor());
        assertEquals(40526, actual.binding().observedFirstHeir().orElseThrow());
        assertEquals(833, observation.candidates().size());
        assertEquals(833, observation.nativeLegalCandidates().size());
        var projected = OpportunityJson.toNode(FamilyHeirLegality.project(observation));
        assertEquals(actual.result().get("family_candidates"), projected.get("candidates"));
        assertEquals(actual.result().get("family_candidates"), projected.get("native_legal_candidates"));
        var input = input(projected);
        byte[] original = FullJsonTree.encode(input, FullJsonTree.MAXIMUM_BYTES);
        byte[] before = original.clone();
        assertEquals(397922, original.length);
        var decoded = HeirCandidateIntakeConsumerPort.decode(original);
        assertEquals(833, decoded.legalRows().size());
        assertArrayEquals(original, decoded.sourceJson());
        assertTrue(decoded.rejected().isEmpty());
        var evaluation = HeirCandidateIntakeConsumerPort.evaluate(decoded);
        assertEquals(PICKED, evaluation.nextRichCandidateIds().orElseThrow());
        assertArrayEquals(evaluation.result(), HeirCandidateIntakeConsumerPort.consume(original));
        var result = StrictJson.parse(evaluation.result());
        assertEquals(5, result.path("picked").size());
        for (int index = 0; index < PICKED.size(); index++) {
            var pickedId = PICKED.get(index);
            JsonNode picked = result.get("picked").get(index);
            assertEquals(pickedId, picked.get("candidate_character_id").bigIntegerValue());
            var matching = input.get("legal_rows").findValues("candidate_character_id");
            assertTrue(matching.stream().anyMatch(value -> value.bigIntegerValue().equals(pickedId)));
            assertEquals(BigInteger.valueOf(31254), picked.get("played_character_id").bigIntegerValue());
            assertEquals(BigInteger.valueOf(40526), picked.get("subject_character_id").bigIntegerValue());
        }
        assertArrayEquals(before, original);
        assertEquals(833, input.get("legal_rows").size());
    }

    @Test void completeLargeProjectionRetainsActorAndExactIntegerTypeChecks() throws Exception {
        var actual = actual();
        var wrongActor = actual.result().deepCopy(); row(wrongActor).put("played_character_id", 31255);
        assertThrows(IllegalArgumentException.class, () -> FamilyHeirLegality.decode(raw(wrongActor), actual.binding()));
        var wrongSubject = actual.result().deepCopy(); row(wrongSubject).put("subject_character_id", 40527);
        assertThrows(IllegalArgumentException.class, () -> FamilyHeirLegality.decode(raw(wrongSubject), actual.binding()));
        var projected = OpportunityJson.toNode(FamilyHeirLegality.project(
                FamilyHeirLegality.decode(raw(actual.result()), actual.binding())));
        for (JsonNode wrong : List.of(StrictJson.object().put("value", true).get("value"),
                StrictJson.object().put("value", "40408").get("value"),
                StrictJson.object().put("value", 40408.0).get("value"))) {
            ObjectNode changed = input(projected);
            ((ObjectNode) changed.get("legal_rows").get(0)).set("candidate_character_id", wrong);
            byte[] bytes = FullJsonTree.encode(changed, FullJsonTree.MAXIMUM_BYTES);
            assertTrue(bytes.length > StrictJson.INPUT_MAX_BYTES);
            assertThrows(IllegalArgumentException.class, () -> HeirCandidateIntakeConsumerPort.consume(bytes));
        }
        var wrongArray = input(projected); wrongArray.put("legal_rows", true);
        assertThrows(IllegalArgumentException.class, () -> HeirCandidateIntakeConsumerPort.consume(
                FullJsonTree.encode(wrongArray, FullJsonTree.MAXIMUM_BYTES)));
        var extra = input(projected); extra.put("qualified", true);
        assertThrows(IllegalArgumentException.class, () -> HeirCandidateIntakeConsumerPort.consume(
                FullJsonTree.encode(extra, FullJsonTree.MAXIMUM_BYTES)));
        assertEquals(833, actual.result().get("family_candidates").size());
    }

    private record Actual(ObjectNode result, FamilyHeirLegality.Binding binding) { }

    private static Actual actual() throws Exception {
        JsonNode metadata = StrictJson.parse(resource("context.json"));
        byte[] acknowledgement;
        try (var zipped = new GZIPInputStream(stream("legality-ack.json.gz"))) {
            acknowledgement = zipped.readAllBytes();
        }
        assertEquals(398672, acknowledgement.length);
        assertEquals("43e3676399979cd98bc995495218af641d8488e36bd616ffd9cc547881dd71ab",
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(acknowledgement)));
        var packet = NativeWire.parse(acknowledgement);
        assertEquals("step-6-c733b0c606c0", packet.get("request_id").textValue());
        assertTrue(packet.get("ok").booleanValue());
        JsonNode request = metadata.get("request"), before = request.get("before"), frame = before.get("frame");
        JsonNode source = request.get("source"), game = before.get("game");
        var provenance = new G2Source(source.get("machine_id").textValue(), source.get("observed_at_utc").textValue(),
                source.get("exact_build").textValue(), ExactRef.fromJson(source.get("source_ref")));
        var proposal = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(integer(frame, "played_character_id"),
                integer(frame, "native_revision"), integer(frame, "date_raw")), frame.get("snapshot_id").textValue(),
                integer(frame, "revision"), frame.get("episode_run_id").textValue());
        var identity = new ObservationIdentity(before.get("machine_id").textValue(),
                new GameGeneration(game.get("pid").longValue(), new PythonOnlyUInt64(new BigInteger(game.get("creation_filetime").textValue()))),
                proposal, before.get("observation_version").longValue());
        JsonNode arguments = metadata.get("arguments");
        var read = new PlanningReadRequest(identity, provenance, request.get("session_id").textValue(),
                new OperationKey(request.get("operation").textValue()), InteractionArguments.app(InteractionJson.object(arguments)),
                Instant.parse(request.get("deadline").textValue()));
        var binding = new FamilyHeirLegality.Binding(InteractionArguments.context(read), arguments.get("root_query_sequence").bigIntegerValue(),
                OptionalLong.of(arguments.get("first_heir_id").longValue()), ExactRef.fromJson(arguments.get("root_evidence")));
        return new Actual(ObjectNode.class.cast(packet.get("result")), binding);
    }

    private static BigInteger integer(JsonNode value, String key) { return new BigInteger(value.get(key).textValue()); }
    private static RawJson raw(JsonNode value) { return new RawJson(FullJsonTree.encode(value, FullJsonTree.MAXIMUM_BYTES)); }
    private static ObjectNode row(ObjectNode result) { return ObjectNode.class.cast(result.get("family_candidates").get(0)); }
    private static ObjectNode input(JsonNode projected) {
        var input = StrictJson.object(); input.set("legal_rows", projected.get("native_legal_candidates").deepCopy());
        input.putArray("rejected_candidate_ids"); return input;
    }
    private static byte[] resource(String name) throws IOException { try (var stream = stream(name)) { return stream.readAllBytes(); } }
    private static InputStream stream(String name) throws IOException {
        var result = FamilyHeirLargeIntakeTest.class.getResourceAsStream(RESOURCE + name);
        if (result == null) throw new IOException("retained worker100 resource required: " + name);
        return result;
    }
}
