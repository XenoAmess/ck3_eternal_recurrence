package org.xar.ck3.control.service.root;

import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.CampaignRootContextJsonTest;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Real framed Finance ROOT DATA -> owning normalizer -> shared runtime decoder. No writer or live qualification. */
final class RootGovernanceRootReadBoundaryTest {
    private static final Instant NOW = Instant.parse("2026-10-29T00:00:00Z");
    private static final ExactRef REF = new ExactRef("synthetic-root-read-data-not-native-authority", 1, "a".repeat(64));
    private static final G2Source SOURCE = new G2Source("xenoamess-full-tower-eb9d2c1186", NOW.toString(), "1.20.0.4", REF);
    private static final OperationKey ROOT = FinanceReadContracts.Query.ROOT.operation();

    private static ReadContract<FinanceReadContracts.Packet> definition() {
        var definitions = new FinanceReadContracts(query -> new FinanceReadContracts.Registration(REF,
                new FinanceReadContracts.Permission(Optional.empty(), query.operation().value(),
                        ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.EXECUTE_STEP)));
        return definitions.contract(FinanceReadContracts.Query.ROOT);
    }

    private static IntegerValue n(int value) { return new IntegerValue(BigInteger.valueOf(value)); }

    private static Obj largeRoot() throws Exception {
        Obj root = CampaignRootContextJsonTest.originalActual4RootFixture();
        List<Value> vassals = new ArrayList<>(array(root.get("direct_landed_vassal_character_ids"), "original vassals"));
        List<Value> related = new ArrayList<>(array(root.get("related_character_contexts"), "original related contexts"));
        Obj sample = related.stream().map(value -> object(value, "original context"))
                .filter(value -> new Text("direct_landed_vassal").equals(value.get("relationship_role"))).findFirst().orElseThrow();
        for (int index = 0; index < 300; index++) {
            vassals.add(n(100000 + index));
            related.add(sample.with("character_id", n(100000 + index)).with("capital_province_id", n(4000 + index))
                    .with("primary_title", object(sample.get("primary_title"), "original title").with("title_id", n(200000 + index))));
        }
        return root.with("direct_landed_vassal_character_ids", new Arr(vassals)).with("related_character_contexts", new Arr(related));
    }

    private static PlanningReadReceipt receipt(Obj root, BigInteger player, BigInteger revision, BigInteger date,
            OperationKey operation, String contractId) {
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(player, revision, date),
                "native:root-read-data", revision, "root-read-data-episode");
        var observed = new ObservationIdentity(SOURCE.machineId(),
                new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001"))), frame, 1);
        var request = new PlanningReadRequest(observed, SOURCE, "root-read-data-session", operation,
                FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.PUBLIC_QUERY), NOW.plusSeconds(30));
        Obj result = new Obj(Map.of("step", new Text(ROOT.value()), "accepted", new Bool(true), "status", root.get("status"),
                "query_sequence", n(1), "snapshot_revision", root.get("snapshot_revision"),
                "campaign_root_context", root, "backend_id", new Text("native-headless")));
        String requestId = "root-read-data-request";
        byte[] wire = encode(new Obj(Map.of("type", new Text("command_result"), "protocol_version", n(1),
                "request_id", new Text(requestId), "ok", new Bool(true), "result", result)));
        byte[] packet = ByteBuffer.allocate(wire.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(wire.length).put(wire).array();
        var original = new NativeActionPort.AckReceived(requestId, true, Optional.of(new RawJson(encode(result))), new RawJson(wire), packet);
        var binding = new GuardEvidence(observed, SOURCE, request.sessionId(), BigInteger.ONE, operation, REF, REF,
                "synthetic-data-not-installed-runtime", NOW, NOW.plusSeconds(30));
        var guard = new PlanningReadGuard(binding, true, true, true, "b".repeat(64));
        return new PlanningReadReceipt(request, contractId, requestId, guard, guard, original);
    }

    private static PlanningReadReceipt receipt(Obj root) {
        return receipt(root, integer(root.get("player_character_id"), "player"), integer(root.get("snapshot_revision"), "revision"),
                integer(root.get("date_raw"), "date"), ROOT, FinanceReadContracts.ROOT_CONTRACT_ID);
    }

    @Test void actualFramedFinanceRootBeyondReceiptBudgetRetainsEveryNormalizedField() throws Exception {
        Obj root = largeRoot();
        assertTrue(encode(root).length > StrictJson.INPUT_MAX_BYTES);
        assertTrue(encode(root).length < DriverJson.MAX_NATIVE_BYTES);
        var contract = definition(); var read = receipt(root);
        Obj normalized = object(contract.decode(read).result().get("campaign_root_context"), "real normalized ROOT");
        var actual = RootGovernanceDomains.decodeCouncilRoot(contract, read);
        assertEquals(302, actual.get("direct_landed_vassal_character_ids").size());
        assertEquals(304, actual.get("related_character_contexts").size());
        assertEquals(integer(root.get("player_character_id"), "original player"), actual.get("player_character_id").bigIntegerValue());
        assertEquals(integer(root.get("snapshot_revision"), "original revision"), actual.get("snapshot_revision").bigIntegerValue());
        assertEquals(integer(root.get("date_raw"), "original date"), actual.get("date_raw").bigIntegerValue());
        assertEquals(normalized, DriverJson.fromNode(actual), "the shared runtime decoder retains the complete normalized root");
    }

    @Test void actualFramedRootRejectsAnotherActorFrameOrRegisteredReadIdentity() throws Exception {
        Obj root = CampaignRootContextJsonTest.originalActual4RootFixture(); var contract = definition();
        BigInteger player = integer(root.get("player_character_id"), "player");
        BigInteger revision = integer(root.get("snapshot_revision"), "revision"), date = integer(root.get("date_raw"), "date");
        var foreignActor = receipt(root, player.add(BigInteger.ONE), revision, date, ROOT, FinanceReadContracts.ROOT_CONTRACT_ID);
        assertNotNull(contract.decode(foreignActor), "normalization does not replace the actual consumer actor check");
        var actorFailure = assertThrows(IllegalArgumentException.class, () -> RootGovernanceDomains.decodeCouncilRoot(contract, foreignActor));
        assertTrue(actorFailure.getMessage().contains("independent ROOT frame/actor/source differs"));
        for (var invalid : List.of(
                receipt(root, player, revision.add(BigInteger.ONE), date, ROOT, FinanceReadContracts.ROOT_CONTRACT_ID),
                receipt(root, player, revision, date.add(BigInteger.ONE), ROOT, FinanceReadContracts.ROOT_CONTRACT_ID),
                receipt(root, player, revision, date, ROOT, FinanceReadContracts.ROOT_CONTRACT_ID + ":different"),
                receipt(root, player, revision, date, FinanceReadContracts.Query.CASH.operation(), FinanceReadContracts.ROOT_CONTRACT_ID)))
            assertThrows(IllegalArgumentException.class, () -> RootGovernanceDomains.decodeCouncilRoot(contract, invalid));
    }
}
