package org.xar.ck3.control.nativebridge.capabilities.governance;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.governance.development.DevelopmentModels;
import org.xar.ck3.control.nativebridge.NativeWire;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Complete retained native .3 result -> actual Java contract -> public handler/encoder; enclosing guard is synthetic. */
final class GovernanceProtocolTest {
    private static final String SHA = "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
    private static final Instant NOW = Instant.parse("2026-10-23T17:00:00Z");
    private static final ExactRef REF = new ExactRef("synthetic/governance-protocol-only.json", 1, "a".repeat(64));
    private static RawJson raw(String text) { return new RawJson(text.getBytes(StandardCharsets.UTF_8)); }
    private static IntegerValue n(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
    private static PlanningRequest planning() {
        var source = new G2Source("xenoamess-full-tower-eb9d2c1186", NOW.toString(), "1.20.0.3", REF);
        var identity = new ObservationIdentity(source.machineId(), new GameGeneration(123,
                new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(16777258), BigInteger.valueOf(77), BigInteger.valueOf(53328600)),
                        "material-fixture:177", BigInteger.valueOf(177), "offline-develop-material-fixture"), 1);
        Obj snapshot = new Obj(java.util.Map.of()).with("snapshot_id", new Text("material-fixture:177")).with("revision", n(177)).with("native_revision", n(77)).with("date_raw", n(53328600)).with("paused", new Bool(true)).with("map_ready", new Bool(true)).with("backend_id", new Text("native-headless")).with("played_character", new Obj(java.util.Map.of()).with("character_id", n(16777258)).with("alive", new Bool(true))).with("active_wars", new Arr(List.of())).with("episode_run_id", new Text("offline-develop-material-fixture")).with("player_armies", new Arr(List.of())).with("active_event", Nil.INSTANCE).with("pending_character_interaction", Nil.INSTANCE);
        return new PlanningRequest(identity, source, "synthetic-governance-session", NOW.plusSeconds(30),
                new PlanningObservation(snapshot, List.of(), Set.of(), Set.of(), Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false));
    }
    private static final class OriginalPort implements PlanningReadPort {
        private final byte[] bytes; private int reads;
        private OriginalPort() throws Exception {
            String root = System.getProperty("xar.repository.root"); assertNotNull(root, "required producer fixture repository missing");
            bytes = Files.readAllBytes(Path.of(root, "ck3_autonomous_player/tests/fixtures/steward_develop_county_12003_material/develop_material_available.json"));
        }
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
            reads++;
            try {
                var frame = StrictJson.parse(bytes); String id = frame.get("request_id").textValue();
                var binding = new GuardEvidence(request.before(), request.source(), request.sessionId(), BigInteger.ONE, request.operation(),
                        REF, REF, "synthetic-guard-no-native-qualification", NOW, NOW.plusSeconds(30));
                var guard = new PlanningReadGuard(binding, true, true, true, "b".repeat(64));
                var ack = new NativeActionPort.AckReceived(id, true, Optional.of(new RawJson(StrictJson.canonical(frame.get("result")))), new RawJson(bytes), NativeWire.packet(bytes));
                var receipt = new PlanningReadReceipt(request, contract.contractId(), id, guard, guard, ack);
                return new PlanningReadResult.Known<>(contract.decode(receipt), receipt, REF);
            } catch (java.io.IOException error) { throw new java.io.UncheckedIOException(error); }
        }
    }
    @Test void completeProducerPassesActualContractFacadeAndSerializesDistinctRevisions() throws Exception {
        OriginalPort port = new OriginalPort(); PlanningRequest request = planning();
        var contracts = new GovernanceNativeReads(REF, "1.20.0.3", SHA);
        ActionCoordinatorPort noAction = new ActionCoordinatorPort() {
            @Override public ActionReceipt execute(ActionCommand command) { throw new AssertionError("query-only material cannot dispatch"); }
            @Override public ActionReceipt reconcile(String id) { throw new AssertionError("no original action exists"); }
        };
        var service = new GovernancePublicService(() -> request, port, contracts, noAction, Optional.empty());
        var reply = service.query_steward_develop_county_candidates_v1(GovernancePublicService.decodeDevelopment(raw("{\"expected_revision\":177}")));
        assertInstanceOf(DevelopmentModels.Material.class, reply.value());
        var output = StrictJson.parse(GovernancePublicService.encodeDevelopment(reply).bytes());
        assertEquals("177", output.get("source").get("revision").textValue()); assertEquals("77", output.get("source").get("native_revision").textValue());
        assertEquals("native-headless", output.get("source").get("backend_id").textValue());
        assertEquals("exact-steward-develop-county-candidates", output.get("scope").textValue());
        assertEquals("77",output.get("steward_develop_county_candidates").get("snapshot_revision").textValue());
        assertEquals("8250",output.get("steward_develop_county_candidates").get("candidates").get(0).get("monthly_development_rate").get("raw").textValue());
        assertEquals(67108874,output.get("steward_develop_county_candidates").get("candidates").get(0).get("county_title_id").intValue());
        assertTrue(StrictJson.parse(port.bytes).get("result").get("snapshot_revision").isIntegralNumber());
        assertThrows(UnsupportedOperationException.class, () -> service.change_steward_develop_county_task_v1(
                GovernancePublicService.decodeChange(raw("{\"councillor_character_id\":33554449,\"target_county_title_id\":67108874,\"expected_revision\":177,\"replace_existing_task\":true}"))));
        assertEquals(2, port.reads);
        assertThrows(IllegalArgumentException.class, () -> GovernancePublicService.decodeDevelopment(raw("{\"expected_revision\":true}")));
        assertThrows(IllegalArgumentException.class, () -> GovernancePublicService.decodeChange(raw("{\"councillor_character_id\":1,\"target_county_title_id\":2,\"expected_revision\":177,\"replace_existing_task\":null}")));
    }
}
