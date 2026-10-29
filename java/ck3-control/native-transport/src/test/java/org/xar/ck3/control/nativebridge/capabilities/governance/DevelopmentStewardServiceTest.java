package org.xar.ck3.control.nativebridge.capabilities.governance;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Optional;
import java.util.HashSet;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.governance.development.DevelopmentModels;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Protocol DATA fixtures exercise the production decoder/service. They grant no actual Root or Game authority. */
final class DevelopmentStewardServiceTest {
    private static final Instant NOW = Instant.parse("2026-10-24T00:00:00Z");
    private static final ExactRef SOURCE = new ExactRef("actual-python-output-as-software-DATA", 1, "c".repeat(64));
    record Fixture(DevelopmentStewardResults.SameFrameFacts facts, byte[] hello) { }

    /** Input is emitted by the unchanged original Python service/configuration oracle. */
    static DevelopmentStewardService.Fault evaluateOriginalConfiguration(JsonNode row) throws Exception {
        var action = new DevelopmentStewardAction.Request("steward-oracle-1", row.get("councillor").intValue(),
                row.get("county").intValue(), row.get("expected_revision").bigIntegerValue(), true);
        JsonNode snapshot = row.get("snapshot");
        try {
            DevelopmentStewardService.beforeQuery(action, snapshot.get("paused").booleanValue(),
                    snapshot.get("revision").bigIntegerValue());
            var fixture = fixture(action, row.get("candidate"), snapshot, row.get("capabilities"));
            var actualSteps = new HashSet<OperationKey>();
            for (JsonNode step : row.get("capabilities").get("action_steps")) actualSteps.add(new OperationKey(step.textValue()));
            DevelopmentStewardService.beforeCandidateRead((NativeWire.Hello) NativeWire.decode(fixture.hello()), actualSteps);
            DevelopmentStewardService.candidate(fixture.facts());
            var capabilities = DevelopmentStewardService.bindCapabilities(fixture.facts(), fixture.hello(), fixture.hello(), fixture.hello());
            throw DevelopmentStewardService.currentHeadlessRejection(fixture.facts(), capabilities,
                    DevelopmentStewardSameFrameTest.sources());
        } catch (DevelopmentStewardService.Failure failure) {
            return failure.fault();
        }
    }

    static Fixture fixture(DevelopmentStewardAction.Request action, JsonNode candidate, JsonNode snapshot,
            JsonNode capabilities) throws Exception {
        String version = candidate.get("provenance").get("game_version").textValue();
        String sha = candidate.get("provenance").get("executable_sha256").textValue();
        var source = new G2Source("steward-oracle-protocol-data", NOW.toString(), version, SOURCE);
        var identity = new ObservationIdentity(source.machineId(),
                new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(candidate.get("player_character_id").bigIntegerValue(),
                        snapshot.get("native_revision").bigIntegerValue(), snapshot.get("date_raw").bigIntegerValue()),
                        snapshot.get("snapshot_id").textValue(), snapshot.get("revision").bigIntegerValue(),
                        snapshot.get("episode_run_id").textValue()), 1);
        var contracts = new GovernanceNativeReads(SOURCE, version, sha);
        var query = new PlanningReadRequest(identity, source, "protocol-only-session", contracts.development().operation(),
                new OpportunityJson.Obj(java.util.Map.of()), NOW.plusSeconds(30));
        ObjectNode helloRow = StrictJson.object().put("type", "hello").put("protocol_version", 1).put("pid", 123)
                .put("connection_generation", 1).put("bridge_version", "software-DATA-only")
                .put("expected_ck3_sha256", sha).put("game_adapter_id", "software-data-fixture")
                .put("game_adapter_status", "ready").put("ck3_build_match", true);
        helloRow.set("capabilities", capabilities.get("bridge_capabilities").deepCopy());
        byte[] hello = NativeWire.packet(StrictJson.canonical(helloRow));
        var helloHash = NativeRequestChronology.PacketIdentity.of(hello);
        var helloRef = new ExactRef("software-DATA/original-hello.packet", helloHash.bytes(), helloHash.sha256());
        ObjectNode frame = StrictJson.object().put("type", "command_result").put("protocol_version", 1)
                .put("request_id", "steward-oracle-query-1").put("ok", true);
        ObjectNode result = frame.putObject("result").put("step", DevelopmentStewardAction.QUERY_STEP)
                .put("accepted", true).put("status", candidate.get("status").textValue()).put("query_sequence", 1)
                .put("snapshot_revision", snapshot.get("native_revision").bigIntegerValue()).put("backend_id", "native-headless");
        result.set("steward_develop_county_candidates", candidate.deepCopy());
        byte[] original = StrictJson.canonical(frame);
        var evidence = new GuardEvidence(identity, source, query.sessionId(), BigInteger.ONE, query.operation(),
                SOURCE, helloRef, "software-DATA-only", NOW, NOW.plusSeconds(30));
        var guard = new PlanningReadGuard(evidence, true, true, true, "b".repeat(64));
        var ack = new NativeActionPort.AckReceived("steward-oracle-query-1", true,
                Optional.of(new RawJson(StrictJson.canonical(result))), new RawJson(original), NativeWire.packet(original));
        var receipt = new PlanningReadReceipt(query, contracts.development().contractId(), ack.requestId(), guard, guard, ack);
        var originalHash = NativeRequestChronology.PacketIdentity.of(ack.originalPacket());
        var known = new PlanningReadResult.Known<>(contracts.development().decode(receipt), receipt,
                new ExactRef("software-DATA/original-candidate.packet", originalHash.bytes(), originalHash.sha256()));
        return new Fixture(DevelopmentStewardResults.bind(action, query, known), hello);
    }

    @Test void preQueryErrorsHaveOriginalPriorityAndNoInventedCandidateEvidence() {
        var paused = assertThrows(DevelopmentStewardService.Failure.class,
                () -> DevelopmentStewardService.beforeQuery(DevelopmentStewardActionTest.request(), false, BigInteger.TEN));
        assertEquals(DevelopmentStewardService.Error.PAUSED_REQUIRED, paused.fault().error());
        assertTrue(paused.fault().candidateOriginal().isEmpty());
        var stale = assertThrows(DevelopmentStewardService.Failure.class,
                () -> DevelopmentStewardService.beforeQuery(DevelopmentStewardActionTest.request(), true, BigInteger.TEN));
        assertEquals(DevelopmentStewardService.Error.STALE_REVISION, stale.fault().error());
    }

    @Test void internalErrorsRoundTripStrictlyWithoutChangingThePublicErrorWire() {
        for (var error : DevelopmentStewardService.Error.values()) {
            Optional<ExactRef> ref = error == DevelopmentStewardService.Error.PAUSED_REQUIRED
                    || error == DevelopmentStewardService.Error.STALE_REVISION
                    || error == DevelopmentStewardService.Error.QUERY_UNSUPPORTED ? Optional.empty() : Optional.of(SOURCE);
            var fault = new DevelopmentStewardService.Fault(error, ref);
            var original = DevelopmentStewardService.encodeFault(fault);
            assertEquals(fault, DevelopmentStewardService.decodeFault(original));
            ObjectNode altered = (ObjectNode) StrictJson.parse(original.bytes());
            altered.put("python_error", "OtherError");
            assertThrows(IllegalArgumentException.class,
                    () -> DevelopmentStewardService.decodeFault(new RawJson(StrictJson.canonical(altered))));
        }
        var value = (ObjectNode) StrictJson.parse(DevelopmentStewardService.encodeFault(
                new DevelopmentStewardService.Fault(DevelopmentStewardService.Error.CANDIDATE_UNAVAILABLE, Optional.of(SOURCE))).bytes());
        ((ObjectNode) value.get("candidate_original")).put("bytes", true);
        assertThrows(IllegalArgumentException.class,
                () -> DevelopmentStewardService.decodeFault(new RawJson(StrictJson.canonical(value))));
    }
}
