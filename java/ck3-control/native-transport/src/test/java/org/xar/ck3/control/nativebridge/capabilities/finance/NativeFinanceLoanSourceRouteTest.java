package org.xar.ck3.control.nativebridge.capabilities.finance;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.PlanningReadGuard;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanSource;

/** Actual compiled native parser/Read/whole serializer values with explicitly synthetic guards.
 * This test never constructs a Game session, native permission, mailbox stamp or action authority. */
final class NativeFinanceLoanSourceRouteTest {
    private static final BigInteger EPOCH = new BigInteger("18446744073709551614");
    private static final Instant NOW = Instant.parse("2026-10-23T22:28:00Z");
    private static final ExactRef REF = new ExactRef("synthetic-loan-route-source-not-runtime-qualified", 1, "a".repeat(64));
    private static ReadContract<HolyLoanSource.Result> contract() { return NativeFinanceReads.holyLoanSource(REF); }

    private static JsonNode rows() throws Exception {
        String path = System.getProperty("xar.holy.loan.source.route.producer.golden");
        String sha = System.getProperty("xar.holy.loan.source.route.producer.golden.sha256");
        assertNotNull(path, "actual emitted native loan route golden required");
        assertNotNull(sha, "actual native route golden SHA required"); assertTrue(sha.matches("[a-f0-9]{64}"));
        byte[] bytes = Files.readAllBytes(Path.of(path));
        assertEquals(sha, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        ObjectNode root = StrictJson.object(StrictJson.parse(bytes), Set.of("schema", "rows"));
        assertEquals("xar.holy-loan-source-route-producer-golden.v1", StrictJson.text(root.get("schema")));
        assertTrue(root.get("rows").isArray()); assertEquals(18, root.get("rows").size()); return root.get("rows");
    }
    private static ObjectNode frame(JsonNode rows, int index) {
        ObjectNode row = StrictJson.object(rows.get(index), Set.of("scenario", "request", "frame"));
        assertEquals(index, StrictJson.integer(row.get("scenario"), index, index));
        ObjectNode request = StrictJson.object(row.get("request"),
                Set.of("type", "protocol_version", "request_id", "step", "expected_revision", "capture_epoch"));
        assertEquals(HolyLoanSource.OPERATION, StrictJson.text(request.get("step")));
        assertEquals(EPOCH.toString(), StrictJson.text(request.get("capture_epoch")));
        return (ObjectNode) row.get("frame").deepCopy();
    }
    private static PlanningReadReceipt receipt(ReadContract<?> contract, ObjectNode nativeFrame, long actor) throws Exception {
        var source = new G2Source("xenoamess-full-tower-eb9d2c1186", NOW.toString(), "1.20.0.4", REF);
        var before = new ProposalLifecycle.ObservationIdentity(source.machineId(),
                new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(actor), BigInteger.valueOf(7), BigInteger.valueOf(53288496)),
                        "loan-source:19", BigInteger.valueOf(19), "synthetic-loan-fixture"), 1);
        var request = new PlanningReadRequest(before, source, "synthetic-loan-route-session", contract.operation(),
                new NativeFinanceReads.HolyLoanSourceRequest(EPOCH).arguments(), NOW.plusSeconds(30));
        var binding = new GuardEvidence(before, source, request.sessionId(), new BigInteger("133700000000000001"),
                request.operation(), REF, REF, "synthetic-loan-route-custody", NOW, NOW.plusSeconds(30));
        var guard = new PlanningReadGuard(binding, true, true, true, "b".repeat(64));
        String requestId = StrictJson.text(nativeFrame.get("request_id"));
        byte[] bytes = StrictJson.canonical(nativeFrame);
        var prepared = contract.prepare(request, requestId);
        var outbound = new NativeActionPort.OutboundPacket(requestId, NativeWire.execute(requestId, prepared.step(),
                request.before().frame().identity().nativeRevision(), prepared.additionalFields().bytes()));
        var ack = new NativeActionPort.AckReceived(requestId, true,
                Optional.of(new RawJson(StrictJson.canonical(nativeFrame.get("result")))), new RawJson(bytes),
                NativeWire.packet(bytes), Optional.of(outbound));
        return new PlanningReadReceipt(request, contract.contractId(), requestId, guard, guard, ack);
    }
    @Test void actualNativeParserReadAndWholeSerializerFeedTheOnlySourceQualifiedJavaDecoder() throws Exception {
        JsonNode rows = rows(); var contract = contract();
        Set<Integer> available = Set.of(0, 1, 2, 11, 12, 13, 14, 15);
        for (int scenario = 0; scenario < 18; ++scenario) {
            long actor = scenario == 11 ? 0 : scenario == 12 ? 2147483649L : 17;
            ObjectNode full = frame(rows, scenario);
            if (scenario == 11) {
                // The actual shared planner Frame still requires positive(player).
                // Preserve native actor0; do not fabricate a different actor or a
                // permissive authority to make this unsupported whole path green.
                assertThrows(IllegalArgumentException.class, () -> receipt(contract, full, 0));
                continue;
            }
            HolyLoanSource.Result result = contract.decode(receipt(contract, full, actor));
            if (!available.contains(scenario)) { assertInstanceOf(HolyLoanSource.Unavailable.class, result); continue; }
            var quote = assertInstanceOf(HolyLoanSource.Quote.class, result);
            assertEquals(EPOCH, quote.captureEpoch()); assertEquals(BigInteger.valueOf(actor), quote.frame().actorCharacterId());
            assertEquals(BigInteger.valueOf(19), quote.frame().revision()); assertEquals(BigInteger.valueOf(7), quote.frame().nativeRevision());
            assertEquals(0, quote.fundingCreditRaw()); assertFalse(quote.completeLoanTerms()); assertFalse(quote.submissionQualified());
            assertFalse(quote.receivedFundsVerified()); assertFalse(contract.hasPureReplay());
            assertArrayEquals(quote.toJson(), ((HolyLoanSource.Quote) HolyLoanSource.decode(quote.toJson(), quote.frame(), EPOCH)).toJson());
        }
    }
    @Test void wrongOuterOriginsStatusSequenceNativeRevisionAndOriginalTokensAreRejected() throws Exception {
        var contract = contract(); ObjectNode original = frame(rows(), 0);
        for (String field : Set.of("backend_id", "status", "snapshot_revision", "query_sequence")) {
            ObjectNode changed = original.deepCopy();
            ((ObjectNode) changed.get("result")).put(field, field.equals("snapshot_revision") ? "19" : field.equals("query_sequence") ? "01" : "forged");
            assertThrows(IllegalArgumentException.class, () -> contract.decode(receipt(contract, changed, 17)));
        }
        ObjectNode numericSequence = original.deepCopy(); ((ObjectNode) numericSequence.get("result")).put("query_sequence", 99);
        assertThrows(IllegalArgumentException.class, () -> contract.decode(receipt(contract, numericSequence, 17)));
        ObjectNode falseRead = original.deepCopy(); ((ObjectNode) falseRead.get("result").get("holy_order_loan_source_v2")).put("received_funds_verified", true);
        assertThrows(IllegalArgumentException.class, () -> contract.decode(receipt(contract, falseRead, 17)));
        ObjectNode missing = original.deepCopy(); ((ObjectNode) missing.get("result")).remove("holy_order_loan_source_v2");
        assertThrows(IllegalArgumentException.class, () -> contract.decode(receipt(contract, missing, 17)));
        PlanningReadReceipt good = receipt(contract, original, 17);
        var ack = good.original();
        var wrongToken = new NativeActionPort.AckReceived(ack.requestId(), true, Optional.of(new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8))),
                ack.originalFrame(), ack.originalPacket(), ack.outbound());
        var crossed = new PlanningReadReceipt(good.request(), good.contractId(), good.requestId(), good.before(), good.after(), wrongToken);
        assertThrows(IllegalArgumentException.class, () -> contract.decode(crossed));
    }
    @Test void actualFramingOutboundRequestAndResultTokenCustodyCannotBeReplacedByEquivalentJson() throws Exception {
        var contract = contract(); ObjectNode full = frame(rows(), 0);
        PlanningReadReceipt good = receipt(contract, full, 17); var ack = good.original();
        ObjectNode other = full.deepCopy(); ((ObjectNode) other.get("result")).put("query_sequence", "1000");
        var wrongPacket = new NativeActionPort.AckReceived(ack.requestId(), true, ack.originalResultToken(),
                ack.originalFrame(), NativeWire.packet(StrictJson.canonical(other)), ack.outbound());
        assertThrows(IllegalArgumentException.class, () -> contract.decode(replace(good, wrongPacket)));
        byte[] equivalent = (new String(ack.originalResultToken().orElseThrow().bytes(), java.nio.charset.StandardCharsets.UTF_8) + " ")
                .getBytes(java.nio.charset.StandardCharsets.UTF_8);
        var rewrittenToken = new NativeActionPort.AckReceived(ack.requestId(), true, Optional.of(new RawJson(equivalent)),
                ack.originalFrame(), ack.originalPacket(), ack.outbound());
        assertThrows(IllegalArgumentException.class, () -> contract.decode(replace(good, rewrittenToken)));
        var noOutbound = new NativeActionPort.AckReceived(ack.requestId(), true, ack.originalResultToken(),
                ack.originalFrame(), ack.originalPacket());
        assertThrows(IllegalArgumentException.class, () -> contract.decode(replace(good, noOutbound)));
        for (var revision : new BigInteger[] {BigInteger.valueOf(19), BigInteger.valueOf(7)}) {
            var args = revision.intValueExact() == 7
                    ? new NativeFinanceReads.HolyLoanSourceRequest(EPOCH.subtract(BigInteger.ONE)).arguments()
                    : good.request().arguments();
            var outbound = new NativeActionPort.OutboundPacket(ack.requestId(), NativeWire.execute(ack.requestId(),
                    contract.operation().value(), revision, org.xar.ck3.control.planning.opportunity.OpportunityJson.encode(args)));
            var crossed = new NativeActionPort.AckReceived(ack.requestId(), true, ack.originalResultToken(),
                    ack.originalFrame(), ack.originalPacket(), Optional.of(outbound));
            assertThrows(IllegalArgumentException.class, () -> contract.decode(replace(good, crossed)));
        }
        var foreign = new NativeActionPort.OutboundPacket(ack.requestId(), NativeWire.execute("another-request",
                contract.operation().value(), BigInteger.valueOf(7),
                org.xar.ck3.control.planning.opportunity.OpportunityJson.encode(good.request().arguments())));
        var wrongRequest = new NativeActionPort.AckReceived(ack.requestId(), true, ack.originalResultToken(),
                ack.originalFrame(), ack.originalPacket(), Optional.of(foreign));
        assertThrows(IllegalArgumentException.class, () -> contract.decode(replace(good, wrongRequest)));
    }
    private static PlanningReadReceipt replace(PlanningReadReceipt receipt, NativeActionPort.AckReceived original) {
        return new PlanningReadReceipt(receipt.request(), receipt.contractId(), receipt.requestId(), receipt.before(), receipt.after(), original);
    }
}
