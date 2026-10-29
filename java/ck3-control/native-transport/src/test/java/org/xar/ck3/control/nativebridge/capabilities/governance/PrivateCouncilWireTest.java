package org.xar.ck3.control.nativebridge.capabilities.governance;

import java.math.BigInteger;
import java.time.Instant;
import java.util.Arrays;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.governance.council.CouncilPrivateCodec;
import org.xar.ck3.control.nativebridge.NativeWire;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Real production contract.prepare -> the actual encoder; source identity is synthetic and grants no Root permission. */
final class PrivateCouncilWireTest {
    private static final Instant NOW = Instant.parse("2026-10-23T17:40:00Z");
    private static final ExactRef REF = new ExactRef("synthetic-wire-source-not-runtime-qualified", 1, "a".repeat(64));
    private static PlanningReadRequest request(ReadContract<?> contract, Obj arguments) {
        G2Source source = new G2Source("xenoamess-full-tower-eb9d2c1186", NOW.toString(), "1.20.0.4", REF);
        var observed = new ProposalLifecycle.ObservationIdentity(source.machineId(),
                new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(16777217), BigInteger.valueOf(13), BigInteger.valueOf(53175816)),
                        "public:900", BigInteger.valueOf(900), "synthetic-wire-episode"), 1);
        return new PlanningReadRequest(observed, source, "synthetic-wire-session", contract.operation(), arguments, NOW.plusSeconds(30));
    }
    @Test void initialUsesOnlyNativeRevisionAndExplicitPositionWhileStatusHasNeitherRevisionNorTicket() throws Exception {
        PrivateCouncilReads reads = new PrivateCouncilReads(REF);
        assertEquals(ReadContract.WireProfile.EXECUTE_STEP, reads.gates().wireProfile());
        var request = request(reads.gates(), new Obj(java.util.Map.of()).with("position_key", new Text("councillor_court_chaplain")));
        var prepared = reads.gates().prepare(request, "query-unique-1");
        byte[] packet = NativeWire.execute("query-unique-1", prepared.step(), request.before().frame().identity().nativeRevision(), prepared.additionalFields().bytes());
        var query = NativeWire.object(NativeWire.parse(Arrays.copyOfRange(packet, 4, packet.length)));
        assertEquals(Set.of("type", "protocol_version", "request_id", "step", "expected_revision", "position_key"), keys(query));
        assertEquals(13, query.get("expected_revision").intValue()); assertFalse(query.has("expected_snapshot_revision"));
        var statusRequest = request(reads.status(), new Obj(java.util.Map.of()));
        var statusPrepared = reads.status().prepare(statusRequest, "status-unique-2");
        assertEquals(ReadContract.WireProfile.COUNCIL_MAILBOX_STATUS, reads.status().wireProfile());
        byte[] statusPacket = NativeWire.executeCouncilMailboxStatus("status-unique-2", statusPrepared.step(), statusPrepared.additionalFields().bytes());
        var status = NativeWire.object(NativeWire.parse(Arrays.copyOfRange(statusPacket, 4, statusPacket.length)));
        assertEquals(Set.of("type", "protocol_version", "request_id", "step"), keys(status));
        assertEquals(CouncilPrivateCodec.STATUS, status.get("step").textValue());
        assertNotEquals(query.get("request_id"), status.get("request_id"));
    }
    @Test void injectedRevisionsTicketsAndUnknownRolesAreRejectedBeforeWire() {
        PrivateCouncilReads reads = new PrivateCouncilReads(REF);
        assertThrows(IllegalArgumentException.class, () -> reads.status().prepare(request(reads.status(), new Obj(java.util.Map.of()).with("ticket", new Text("invented"))), "id1"));
        assertThrows(IllegalArgumentException.class, () -> reads.gates().prepare(request(reads.gates(), new Obj(java.util.Map.of()).with("position_key", new Text("councillor_steward"))
                .with("expected_snapshot_revision", new IntegerValue(BigInteger.valueOf(13)))), "id2"));
        assertThrows(IllegalArgumentException.class, () -> reads.query().prepare(request(reads.query(), new Obj(java.util.Map.of()).with("position_key", new Text("unknown_role"))), "id3"));
    }
    private static Set<String> keys(com.fasterxml.jackson.databind.node.ObjectNode value) {
        java.util.HashSet<String> result = new java.util.HashSet<>(); value.fieldNames().forEachRemaining(result::add); return Set.copyOf(result);
    }
}
