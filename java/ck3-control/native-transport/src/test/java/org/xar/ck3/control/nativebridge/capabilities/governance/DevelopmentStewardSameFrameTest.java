package org.xar.ck3.control.nativebridge.capabilities.governance;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.governance.development.DevelopmentModels;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Retained actual .3 native material remains data and cannot grant a .4 or legacy action. */
final class DevelopmentStewardSameFrameTest {
    private static final Instant NOW = Instant.parse("2026-10-24T00:00:00Z");
    private static final ExactRef REF = new ExactRef("synthetic-protocol-guard-not-Game-authority", 1, "a".repeat(64));
    private static final String SHA = "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";

    private static PlanningReadRequest query(GovernanceNativeReads reads, int publicRevision) {
        var source = new G2Source("steward-protocol-fixture", NOW.toString(), "1.20.0.3", REF);
        var identity = new ObservationIdentity(source.machineId(),
                new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(16777258),
                        BigInteger.valueOf(77), BigInteger.valueOf(53328600)), "material-fixture:177",
                        BigInteger.valueOf(publicRevision), "protocol-only-episode"), 1);
        return new PlanningReadRequest(identity, source, "protocol-only-session", reads.development().operation(),
                new OpportunityJson.Obj(java.util.Map.of()), NOW.plusSeconds(30));
    }

    private static PlanningReadResult.Known<DevelopmentModels.Observation> original(
            GovernanceNativeReads contracts, PlanningReadRequest request, byte[] bytes) throws Exception {
        var packet = StrictJson.parse(bytes);
        var evidence = new GuardEvidence(request.before(), request.source(), request.sessionId(), BigInteger.ONE,
                request.operation(), REF, REF, "fixture-data-only", NOW, NOW.plusSeconds(30));
        var guard = new PlanningReadGuard(evidence, true, true, true, "b".repeat(64));
        var ack = new NativeActionPort.AckReceived(packet.get("request_id").textValue(), true,
                Optional.of(new RawJson(StrictJson.canonical(packet.get("result")))), new RawJson(bytes), NativeWire.packet(bytes));
        var receipt = new PlanningReadReceipt(request, contracts.development().contractId(),
                packet.get("request_id").textValue(), guard, guard, ack);
        return new PlanningReadResult.Known<>(contracts.development().decode(receipt), receipt, REF);
    }

    static DevelopmentStewardResults.SourceEvidence sources() {
        return new DevelopmentStewardResults.SourceEvidence(
                new ExactRef("original/service.py", 897392, "a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e"),
                new ExactRef("original/native_driver.py", 1658471, "eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603"),
                new ExactRef("original/steward_develop_county_action_contract.py", 14182, "3a029fc7016922adb773e7ee8192b8c0a12a95e097f08976c0bd1f70df24be12"),
                new ExactRef("original/steward_develop_county_action_v1.cpp", 15132, "31f8ac3e392ebd9da78c9a7f413c915a55d58d81f263de18b98f7879badf6453"),
                new ExactRef("original/steward_develop_county_action_v1_abi.json", 2113, "c64dee3e0b7a5f1c3855ace909374156e378b2587d941bea1b1efb010b36574c"));
    }

    @Test void actualRetainedMaterialPassesDecoderAndSameFrameButNeverActionPermission() throws Exception {
        String repository = System.getProperty("xar.repository.root");
        assertNotNull(repository, "actual retained producer repository required; NOT_RUN, no skip");
        byte[] bytes = Files.readAllBytes(Path.of(repository,
                "ck3_autonomous_player/tests/fixtures/steward_develop_county_12003_material/develop_material_available.json"));
        var contracts = new GovernanceNativeReads(REF, "1.20.0.3", SHA);
        var request = query(contracts, 177);
        var actual = original(contracts, request, bytes);
        var intent = new DevelopmentStewardAction.Request("steward-proof-1", 33554449, 67108874, BigInteger.valueOf(177), true);
        var facts = DevelopmentStewardResults.bind(intent, request, actual);
        var closed = DevelopmentStewardResults.prepare(facts, sources());
        assertEquals(DevelopmentStewardResults.Reason.NATIVE_MATERIAL_IS_NOT_ACTION_LEGALITY, closed.permission().reason());
        assertSame(actual, facts.original());
        assertTrue(facts.selectedLegacyCandidate().isEmpty());
        assertEquals(5, closed.permission().source().all().size());
        var stale = new DevelopmentStewardAction.Request("steward-proof-2", 33554449, 67108874, BigInteger.valueOf(77), true);
        assertThrows(IllegalArgumentException.class, () -> DevelopmentStewardResults.bind(stale, request, actual));
        var wrongSteward = new DevelopmentStewardAction.Request("steward-proof-3", 33554450, 67108874, BigInteger.valueOf(177), true);
        var wrongFacts = DevelopmentStewardResults.bind(wrongSteward, request, actual);
        assertEquals(DevelopmentStewardService.Error.CANDIDATE_UNAVAILABLE,
                assertThrows(DevelopmentStewardService.Failure.class,
                        () -> DevelopmentStewardService.candidate(wrongFacts)).fault().error());
        assertThrows(IllegalArgumentException.class,
                () -> DevelopmentStewardResults.bind(intent, query(contracts, 178), actual));
    }
}
