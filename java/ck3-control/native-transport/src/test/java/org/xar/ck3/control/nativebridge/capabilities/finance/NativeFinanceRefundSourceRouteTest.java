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
import org.xar.ck3.control.wave2.finance.rawcash.ConstructionRefundSource;

/** Actual native Read/SerializeQueryResult values, synthetic command envelope and guards; real Java wire encoder.
 * This test never constructs a Game session, native permission, mailbox stamp or action authority. */
final class NativeFinanceRefundSourceRouteTest {
    private static final BigInteger EPOCH = new BigInteger("18446744073709551614");
    private static final Instant NOW = Instant.parse("2026-10-23T22:28:00Z");
    private static final ExactRef REF = new ExactRef("synthetic-refund-route-source-not-runtime-qualified", 1, "a".repeat(64));
    private static ReadContract<ConstructionRefundSource.Result> contract() { return new NativeFinanceReads(REF).cancelQuote(); }

    private static JsonNode rows() throws Exception {
        String path = System.getProperty("xar.construction.refund.producer.golden");
        String sha = System.getProperty("xar.construction.refund.producer.golden.sha256");
        assertNotNull(path, "actual emitted native refund producer golden required");
        assertNotNull(sha, "actual native refund golden SHA required"); assertTrue(sha.matches("[a-f0-9]{64}"));
        byte[] bytes = Files.readAllBytes(Path.of(path));
        assertEquals(sha, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        ObjectNode root = StrictJson.object(StrictJson.parse(bytes), Set.of("schema", "rows"));
        assertEquals("xar.construction-refund-native-producer-golden.v1", StrictJson.text(root.get("schema")));
        assertTrue(root.get("rows").isArray()); assertEquals(13, root.get("rows").size()); return root.get("rows");
    }
    private static ObjectNode frame(JsonNode rows, int index) {
        ObjectNode row = StrictJson.object(rows.get(index), Set.of("scenario", "receipt", "result"));
        assertEquals(index, StrictJson.integer(row.get("scenario"), index, index));
        assertEquals(row.get("receipt"), row.get("result").get("construction_refund_source_v1"));
        ObjectNode envelope = StrictJson.object().put("type", "command_result").put("protocol_version", 1)
                .put("request_id", "synthetic-refund-" + index).put("ok", true);
        envelope.set("result", row.get("result").deepCopy()); return envelope;
    }
    private static PlanningReadReceipt receipt(ReadContract<?> contract, ObjectNode nativeFrame, long actor) throws Exception {
        var source = new G2Source("xenoamess-full-tower-eb9d2c1186", NOW.toString(), "1.20.0.4", REF);
        var before = new ProposalLifecycle.ObservationIdentity(source.machineId(),
                new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(actor), BigInteger.valueOf(7), BigInteger.valueOf(53288496)),
                        "refund-source:19", BigInteger.valueOf(19), "synthetic-refund-fixture"), 1);
        var request = new PlanningReadRequest(before, source, "synthetic-refund-route-session", contract.operation(),
                new NativeFinanceReads.CancelQuoteRequest(2, EPOCH).arguments(), NOW.plusSeconds(30));
        var binding = new GuardEvidence(before, source, request.sessionId(), new BigInteger("133700000000000001"),
                request.operation(), REF, REF, "synthetic-refund-route-custody", NOW, NOW.plusSeconds(30));
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
    @Test void actualRefundProducerResultsTraverseSharedWireDecoderAndPersistence() throws Exception {
        JsonNode rows = rows(); var contract = contract();
        var expected = assertInstanceOf(ConstructionRefundSource.Candidate.class,
                contract.decode(receipt(contract, frame(rows, 0), 17))).frame();
        Set<Integer> available = Set.of(0, 1, 2, 3, 10, 11);
        for (int scenario = 0; scenario < 13; ++scenario) {
            ObjectNode full = frame(rows, scenario);
            long actor = scenario == 10 ? 0 : 17;
            var result = contract.decode(receipt(contract, full, actor));
            if (!available.contains(scenario)) {
                var unavailable = assertInstanceOf(ConstructionRefundSource.Unavailable.class, result);
                var persisted = StrictJson.object(StrictJson.parse(unavailable.toJson()), Set.of("schema", "planning_frame", "native_observation"));
                assertEquals(full.get("result").get("construction_refund_source_v1"), persisted.get("native_observation"));
                assertArrayEquals(unavailable.toJson(), assertInstanceOf(ConstructionRefundSource.Unavailable.class,
                        ConstructionRefundSource.decode(unavailable.toJson(), expected, EPOCH, 2)).toJson());
                continue;
            }
            var candidate = assertInstanceOf(ConstructionRefundSource.Candidate.class, result);
            assertEquals(BigInteger.valueOf(19), candidate.frame().revision());
            assertEquals(BigInteger.valueOf(7), candidate.frame().nativeRevision());
            assertEquals(EPOCH, candidate.captureEpoch()); assertEquals(2, candidate.provinceId());
            assertEquals(actor, candidate.receiver().characterId()); assertFalse(candidate.finalCancelGateObserved());
            assertFalse(candidate.submissionQualified()); assertFalse(candidate.receivedFundsVerified()); assertEquals(0, candidate.fundingCreditRaw());
            var restored = assertInstanceOf(ConstructionRefundSource.Candidate.class,
                    ConstructionRefundSource.decode(candidate.toJson(), candidate.frame(), EPOCH, 2));
            assertArrayEquals(candidate.toJson(), restored.toJson());
            assertEquals(candidate.receiver(), restored.receiver()); assertEquals(candidate.activeRecord(), restored.activeRecord());
            if (scenario == 1) assertTrue(candidate.receiver().currentGoldRaw().isEmpty());
            if (scenario == 2) assertTrue(candidate.activeRecord().isEmpty());
            if (scenario == 3) assertFalse(candidate.copiedCancelGateAllows());
            if (scenario == 11) assertEquals(0, candidate.receiver().currentGoldRaw().orElseThrow());
            if (scenario != 2) assertNotEquals(candidate.receiver().characterId(),
                    candidate.activeRecord().orElseThrow().recordedBuilderCharacterId());
        }
    }
    @Test void actualSignedNativeReceiptsTraverseTheSharedDecoderInExplicitSoftwareEnvelopes() throws Exception {
        String path = System.getProperty("xar.construction.refund.signed.golden");
        String sha = System.getProperty("xar.construction.refund.signed.golden.sha256");
        assertNotNull(path); assertNotNull(sha);
        byte[] bytes = Files.readAllBytes(Path.of(path));
        assertEquals(sha, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        ObjectNode signed = StrictJson.object(StrictJson.parse(bytes), Set.of("cases"));
        var contract = contract();
        for (JsonNode row : signed.get("cases")) {
            String name = StrictJson.text(row.get("case"));
            assertEquals(name.equals("negative-two-typed-data") ? "typed-serialize-data" : "native-read",
                    StrictJson.text(row.get("source_kind")));
            // The exact C++ source receipt is unchanged; only this command envelope/guard is software DATA.
            ObjectNode envelope = frame(rows(), 0);
            ((ObjectNode) envelope.get("result")).set("construction_refund_source_v1", row.get("receipt").deepCopy());
            boolean available = row.get("receipt").get("available").booleanValue();
            ((ObjectNode) envelope.get("result")).put("status", available ? "source_available" : "source_unavailable");
            long actor = available ? row.get("receipt").get("actor_character_id").longValue() : 17;
            var result = contract.decode(receipt(contract, envelope, actor));
            if (!available) { assertInstanceOf(ConstructionRefundSource.Unavailable.class, result); continue; }
            var candidate = assertInstanceOf(ConstructionRefundSource.Candidate.class, result);
            assertEquals(actor, candidate.receiver().characterId()); assertEquals(BigInteger.valueOf(actor), candidate.frame().actorCharacterId());
            var saved = StrictJson.parse(candidate.toJson()); assertEquals(row.get("receipt"), saved.get("native_observation"));
            assertFalse(candidate.submissionQualified()); assertFalse(candidate.receivedFundsVerified()); assertEquals(0, candidate.fundingCreditRaw());
            assertArrayEquals(candidate.toJson(), assertInstanceOf(ConstructionRefundSource.Candidate.class,
                    ConstructionRefundSource.decode(candidate.toJson(), candidate.frame(), EPOCH, 2)).toJson());
        }
    }
    @Test void actualOutboundProvinceAndOriginalReturnPacketCannotBeReplaced() throws Exception {
        var contract = contract(); ObjectNode full = frame(rows(), 0);
        PlanningReadReceipt good = receipt(contract, full, 17); var ack = good.original();
        var crossed = new NativeActionPort.OutboundPacket(ack.requestId(), NativeWire.execute(ack.requestId(),
                contract.operation().value(), BigInteger.valueOf(7),
                org.xar.ck3.control.planning.opportunity.OpportunityJson.encode(new NativeFinanceReads.CancelQuoteRequest(3, EPOCH).arguments())));
        var wrongProvince = new NativeActionPort.AckReceived(ack.requestId(), true, ack.originalResultToken(),
                ack.originalFrame(), ack.originalPacket(), Optional.of(crossed));
        assertThrows(IllegalArgumentException.class, () -> contract.decode(replace(good, wrongProvince)));
        ObjectNode other = full.deepCopy(); ((ObjectNode) other.get("result")).put("query_sequence", "999");
        var wrongPacket = new NativeActionPort.AckReceived(ack.requestId(), true, ack.originalResultToken(),
                ack.originalFrame(), NativeWire.packet(StrictJson.canonical(other)), ack.outbound());
        assertThrows(IllegalArgumentException.class, () -> contract.decode(replace(good, wrongPacket)));
        ObjectNode drift = full.deepCopy();
        ((ObjectNode) drift.get("result").get("construction_refund_source_v1")).put("province_id", 3);
        assertEquals(new ConstructionRefundSource.Refused(ConstructionRefundSource.Refusal.FRAME_DRIFT),
                contract.decode(receipt(contract, drift, 17)));
    }
    private static PlanningReadReceipt replace(PlanningReadReceipt receipt, NativeActionPort.AckReceived original) {
        return new PlanningReadReceipt(receipt.request(), receipt.contractId(), receipt.requestId(), receipt.before(), receipt.after(), original);
    }
}
