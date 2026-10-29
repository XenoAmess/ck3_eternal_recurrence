package org.xar.ck3.control.nativebridge.capabilities.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.time.Instant;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Map;
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
import org.xar.ck3.control.nativebridge.NativeWire;

/** Contract.prepare -> actual production encoder. Synthetic source identity grants no runtime permission. */
class NativeFinanceWireTest {
    private static final BigInteger EPOCH = new BigInteger("18446744073709551614");
    private static final ExactRef SYNTHETIC = new ExactRef("synthetic-finance-wire-not-runtime-qualified", 1, "a".repeat(64));
    private static PlanningReadRequest request(ReadContract<?> contract, Obj arguments) {
        Instant now = Instant.parse("2026-10-23T18:00:00Z");
        G2Source source = new G2Source("xenoamess-full-tower-eb9d2c1186", now.toString(), "1.20.0.4", SYNTHETIC);
        var observed = new ProposalLifecycle.ObservationIdentity(source.machineId(),
                new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(17), BigInteger.valueOf(7), BigInteger.valueOf(53288496)),
                        "synthetic-public:19", BigInteger.valueOf(19), "synthetic-finance-wire-episode"), 1);
        return new PlanningReadRequest(observed, source, "synthetic-finance-wire-session", contract.operation(), arguments, now.plusSeconds(30));
    }

    @Test void onlyActualNativeRevisionAndTypedProvinceEpochReachTheRealEncoder() throws Exception {
        NativeFinanceReads reads = new NativeFinanceReads(SYNTHETIC);
        assertEquals(ReadContract.WireProfile.EXECUTE_STEP, reads.cancelQuote().wireProfile());
        assertEquals(ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, reads.cancelQuote().permissionMode());
        assertTrue(reads.cancelQuote().requiredCapability().isEmpty());
        var request = request(reads.cancelQuote(), new NativeFinanceReads.CancelQuoteRequest(2, EPOCH).arguments());
        var prepared = reads.cancelQuote().prepare(request, "finance-query-1");
        byte[] packet = NativeWire.execute("finance-query-1", prepared.step(), request.before().frame().identity().nativeRevision(), prepared.additionalFields().bytes());
        var nativeNode = NativeWire.object(NativeWire.parse(Arrays.copyOfRange(packet, 4, packet.length)));
        Set<String> fields = new HashSet<>(); nativeNode.fieldNames().forEachRemaining(fields::add);
        assertEquals(Set.of("type", "protocol_version", "request_id", "step", "expected_revision", "province_id", "capture_epoch"), fields);
        assertEquals(7, nativeNode.get("expected_revision").intValue()); assertEquals(2, nativeNode.get("province_id").intValue());
        assertEquals(EPOCH.toString(), nativeNode.get("capture_epoch").textValue());
        assertFalse(nativeNode.has("expected_snapshot_revision")); assertFalse(nativeNode.has("native_entry_rva"));
    }

    @Test void missingCoercedAndInjectedFieldsFailBeforeWireOrNativeInvocation() {
        NativeFinanceReads reads = new NativeFinanceReads(SYNTHETIC);
        for (Obj arguments : new Obj[] {
                new Obj(Map.of("province_id", new IntegerValue(BigInteger.TWO))),
                new Obj(Map.of("province_id", new IntegerValue(BigInteger.TWO), "capture_epoch", new IntegerValue(EPOCH))),
                new Obj(Map.of("province_id", new Text("2"), "capture_epoch", new Text(EPOCH.toString()))),
                new Obj(Map.of("province_id", new IntegerValue(BigInteger.TWO), "capture_epoch", new Text("01"))),
                new Obj(Map.of("province_id", new IntegerValue(BigInteger.TWO), "capture_epoch", new Text(EPOCH.toString()), "expected_revision", new IntegerValue(BigInteger.valueOf(19)))),
                new Obj(Map.of("province_id", new IntegerValue(BigInteger.TWO), "capture_epoch", new Text(EPOCH.toString()), "native_entry_rva", new IntegerValue(BigInteger.valueOf(0x310DB20L))))}) {
            assertThrows(IllegalArgumentException.class, () -> reads.cancelQuote().prepare(request(reads.cancelQuote(), arguments), "bad-finance-query"));
        }
        assertThrows(IllegalArgumentException.class, () -> new NativeFinanceReads.CancelQuoteRequest(0, EPOCH));
        assertThrows(IllegalArgumentException.class, () -> new NativeFinanceReads.CancelQuoteRequest(2, BigInteger.ZERO));
    }
    @Test void loanSourceHasItsOwnWitnessAndOnlyItsCanonicalNonceReachesActualExecuteEncoder() throws Exception {
        var loan = NativeFinanceReads.holyLoanSource(SYNTHETIC);
        assertEquals(ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, loan.permissionMode());
        assertEquals(ReadContract.WireProfile.EXECUTE_STEP, loan.wireProfile());
        assertTrue(loan.requiredCapability().isEmpty()); assertFalse(loan.hasPureReplay());
        var request = request(loan, new NativeFinanceReads.HolyLoanSourceRequest(EPOCH).arguments());
        var nativeRequest = loan.prepare(request, "loan-source-1");
        byte[] packet = NativeWire.execute("loan-source-1", nativeRequest.step(),
                request.before().frame().identity().nativeRevision(), nativeRequest.additionalFields().bytes());
        var node = NativeWire.object(NativeWire.parse(Arrays.copyOfRange(packet, 4, packet.length)));
        Set<String> keys = new HashSet<>(); node.fieldNames().forEachRemaining(keys::add);
        assertEquals(Set.of("type", "protocol_version", "request_id", "step", "expected_revision", "capture_epoch"), keys);
        assertEquals(7, node.get("expected_revision").intValue());
        assertEquals(EPOCH.toString(), node.get("capture_epoch").textValue());
        // An old refund-only composition does not quietly acquire another private read.
        assertEquals(1, new NativeFinanceReads(SYNTHETIC).registeredContracts().size());
        for (Obj arguments : new Obj[] {
                new Obj(Map.of()), new Obj(Map.of("capture_epoch", new IntegerValue(EPOCH))), new Obj(Map.of("capture_epoch", new Text("01"))),
                new Obj(Map.of("capture_epoch", new Text(EPOCH.toString()), "province_id", new IntegerValue(BigInteger.TWO))),
                new Obj(Map.of("capture_epoch", new Text(EPOCH.toString()), "expected_revision", new IntegerValue(BigInteger.valueOf(19)))),
                new Obj(Map.of("capture_epoch", new Text(EPOCH.toString()), "native_entry_rva", new IntegerValue(BigInteger.valueOf(0x310DB20L))))}) {
            assertThrows(IllegalArgumentException.class, () -> loan.prepare(request(loan, arguments), "bad-loan-source"));
        }
        assertThrows(IllegalArgumentException.class, () -> new NativeFinanceReads.HolyLoanSourceRequest(BigInteger.ZERO));
    }
}
