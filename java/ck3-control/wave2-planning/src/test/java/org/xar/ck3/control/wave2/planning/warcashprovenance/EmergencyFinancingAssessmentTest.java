package org.xar.ck3.control.wave2.planning.warcashprovenance;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.holyloan.LoanFinancingCodec;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.planning.warcashprovenance.EmergencyFinancingAssessment.*;
import static org.xar.ck3.control.wave2.planning.warcashprovenance.FinancingGapModels.*;

/** Original loan inputs are retained corpus bytes; additional crisis/pending cases are software fixtures. */
final class EmergencyFinancingAssessmentTest {
    private record Original(String kind, ObjectNode arguments, JsonNode expected) { }
    private static List<Original> originals() throws Exception {
        var stream = EmergencyFinancingAssessmentTest.class.getResourceAsStream("/holyloan/original-v1.jsonl.gz");
        assertNotNull(stream, "the retained original corpus is required; no missing-environment PASS");
        try (var reader = new BufferedReader(new InputStreamReader(new GZIPInputStream(stream), StandardCharsets.UTF_8))) {
            JsonNode header = StrictJson.parse(reader.readLine().getBytes(StandardCharsets.UTF_8));
            assertEquals("xar.holyloan-rawcash-original-golden.v1", header.path("schema").asText());
            assertEquals("xenoamess-full-tower-eb9d2c1186", header.path("machine_id").asText());
            assertEquals(0, header.path("skips").intValue());
            List<Original> result = new ArrayList<>(); String metadata;
            while ((metadata = reader.readLine()) != null) {
                JsonNode meta = StrictJson.parse(metadata.getBytes(StandardCharsets.UTF_8));
                JsonNode request = StrictJson.parse(reader.readLine().getBytes(StandardCharsets.UTF_8));
                JsonNode expected = StrictJson.parse(reader.readLine().getBytes(StandardCharsets.UTF_8));
                if (request.path("operation").asText().equals("financing")) {
                    result.add(new Original(meta.path("expected_kind").asText(), ((ObjectNode) request.get("arguments")).deepCopy(), expected));
                }
            }
            assertEquals(37, header.path("calls").path("financing").intValue());
            assertEquals(18, result.size()); return List.copyOf(result);
        }
    }
    @Test void allRetainedOriginalFinancingInputsReachConsumerAndKeepZeroCredit() throws Exception {
        int valid = 0, invalid = 0;
        for (Original vector : originals()) {
            byte[] wire = SdkProjectionJson.encode(vector.arguments());
            if (vector.kind().equals("invalid_contract")) {
                assertThrows(IllegalArgumentException.class, () -> LoanFinancingCodec.decodeAndProject(wire)); invalid++; continue;
            }
            LoanFinancingCodec.LoanInput loan = LoanFinancingCodec.decodeAndProject(wire);
            assertEquals(vector.expected(), StrictJson.parse(LoanFinancingCodec.encode(loan)));
            Input input = input(loan instanceof LoanFinancingCodec.Projected projected ? frame(projected) : baseFrame(), BigInteger.valueOf(1_000_000));
            Assessment result = EmergencyFinancingAssessment.assess(input, loan, PendingObservation.seamUnavailable(),
                    loan instanceof LoanFinancingCodec.Projected projected ? Optional.of(projected.planningFrame()) : Optional.empty());
            assertEquals(WarFinancingCapabilityGap.observe(input), result.gap());
            assertEquals(input.treasuryRaw(), result.actualWalletRaw()); zeroAuthority(result);
            assertEquals(result, EmergencyFinancingAssessmentCodec.decodeResult(EmergencyFinancingAssessmentCodec.encode(result))); valid++;
        }
        assertEquals(18, valid + invalid); assertTrue(valid > 0);
    }
    @Test void legalDecisionGatesPrincipalAndEverySignedCostAreStillIncompleteTerms() throws Exception {
        LoanFinancingCodec.Projected projected = allowed();
        Assessment result = EmergencyFinancingAssessment.assess(input(frame(projected), BigInteger.valueOf(1_000_000)), projected,
                new NoPendingAction(), Optional.of(projected.planningFrame()));
        assertEquals(Eligibility.ALLOWED, result.loan().eligibility());
        assertEquals(LoanStatus.COMPLETE_LOAN_TERMS_MISSING, result.loan().status());
        assertTrue(result.loan().prospectivePrincipalRaw().isPresent());
        assertEquals(List.of(-5L, -4L, -3L, -2L, -1L, 0L, 1L, 2L, 3L, 4L), result.loan().declaredCostsRaw().orElseThrow());
        assertThrows(UnsupportedOperationException.class, () -> result.loan().declaredCostsRaw().orElseThrow().add(1L));
        assertFalse(result.loan().completeLoanTermsVerified()); assertFalse(result.loan().typedDebtReadbackVerified());
        assertFalse(result.loan().independentlyAttributedReceivedFundsVerified());
        assertEquals(CancellationStatus.NATIVE_FINAL_GATE_REFUND_AND_RECEIVER_UNAVAILABLE, result.cancellation());
        zeroAuthority(result);
    }
    @Test void eachSharedOuterSourceFieldRejectsAStaleOtherwiseQualifiedLoan() throws Exception {
        LoanFinancingCodec.Projected loan = allowed(); ObservedFrame f = frame(loan);
        List<ObservedFrame> changed = List.of(
                new ObservedFrame(f.playedCharacterId().add(BigInteger.ONE), f.nativeRevision(), f.dateRaw(), f.snapshotId(), f.revision(), f.episodeRunId()),
                new ObservedFrame(f.playedCharacterId(), f.nativeRevision().add(BigInteger.ONE), f.dateRaw(), f.snapshotId(), f.revision(), f.episodeRunId()),
                new ObservedFrame(f.playedCharacterId(), f.nativeRevision(), f.dateRaw().add(BigInteger.ONE), f.snapshotId(), f.revision(), f.episodeRunId()),
                new ObservedFrame(f.playedCharacterId(), f.nativeRevision(), f.dateRaw(), f.snapshotId() + "-other", f.revision(), f.episodeRunId()),
                new ObservedFrame(f.playedCharacterId(), f.nativeRevision(), f.dateRaw(), f.snapshotId(), f.revision().add(BigInteger.ONE), f.episodeRunId()),
                new ObservedFrame(f.playedCharacterId(), f.nativeRevision(), f.dateRaw(), f.snapshotId(), f.revision(), f.episodeRunId() + "-other"));
        for (ObservedFrame current : changed) {
            Assessment result = EmergencyFinancingAssessment.assess(input(current, BigInteger.ZERO), loan, new NoPendingAction(), Optional.empty());
            assertEquals(LoanStatus.SOURCE_FRAME_MISMATCH, result.loan().status());
            assertTrue(result.loan().prospectivePrincipalRaw().isEmpty()); assertTrue(result.loan().declaredCostsRaw().isEmpty()); zeroAuthority(result);
        }
    }
    @Test void prospectiveSignedPrincipalNeverIncreasesTheActualObservedWallet() throws Exception {
        for (long amount : List.of(0L, 1L, Long.MAX_VALUE, Long.MIN_VALUE)) {
            ObjectNode wrapper = allowedWrapper();
            ObjectNode principal = (ObjectNode) wrapper.path("cash_resources").path("holy_order_loan_observation_v1").path("principal");
            principal.put("prospective_principal_raw", amount);
            Assessment result = EmergencyFinancingAssessmentCodec.assess(EmergencyFinancingAssessmentCodec.decode(request(wrapper, null)));
            assertEquals(amount, result.loan().prospectivePrincipalRaw().orElseThrow());
            assertEquals(Optional.of(BigInteger.valueOf(1_000_000)), result.actualWalletRaw()); zeroAuthority(result);
            assertEquals(result, EmergencyFinancingAssessmentCodec.decodeResult(EmergencyFinancingAssessmentCodec.encode(result)));
        }
    }
    @Test void floatCostInTheRealSubtreePathStaysUnknownAndNeverBecomesIntegerCash() throws Exception {
        ObjectNode wrapper = allowedWrapper();
        var costs = (com.fasterxml.jackson.databind.node.ArrayNode) wrapper.path("cash_resources")
                .path("holy_order_loan_observation_v1").path("decision_costs").path("borrow_decision").path("costs_raw_by_native_index");
        costs.set(0, com.fasterxml.jackson.databind.node.DoubleNode.valueOf(1.0));
        Assessment result = EmergencyFinancingAssessmentCodec.assess(EmergencyFinancingAssessmentCodec.decode(request(wrapper, null)));
        assertEquals(LoanStatus.NATIVE_INPUT_UNAVAILABLE, result.loan().status());
        assertTrue(result.loan().declaredCostsRaw().isEmpty()); assertTrue(result.loan().prospectivePrincipalRaw().isPresent()); zeroAuthority(result);
    }
    @Test void sameSharedSixFieldsCannotHidePidOrConnectionDriftAndMissingCurrentReader() throws Exception {
        for (String field : List.of("bridge_pid", "connection_generation")) {
            ObjectNode outer = (ObjectNode) StrictJson.parse(request(allowedWrapper(), null));
            ObjectNode diagnostics = (ObjectNode) outer.path("gap_request").path("snapshot").path("diagnostics");
            diagnostics.put(field, diagnostics.get(field).bigIntegerValue().add(BigInteger.ONE));
            Assessment result = EmergencyFinancingAssessmentCodec.assess(EmergencyFinancingAssessmentCodec.decode(SdkProjectionJson.encode(outer)));
            assertEquals(LoanStatus.SOURCE_FRAME_MISMATCH, result.loan().status()); zeroAuthority(result);
        }
        ObjectNode outer = (ObjectNode) StrictJson.parse(request(allowedWrapper(), null));
        ((ObjectNode) outer.path("gap_request").path("snapshot").path("diagnostics")).remove("bridge_pid");
        Assessment result = EmergencyFinancingAssessmentCodec.assess(EmergencyFinancingAssessmentCodec.decode(SdkProjectionJson.encode(outer)));
        assertEquals(LoanStatus.CURRENT_PLANNING_FRAME_UNAVAILABLE, result.loan().status()); zeroAuthority(result);
        ObjectNode unpaused = (ObjectNode) StrictJson.parse(request(allowedWrapper(), null));
        ((ObjectNode) unpaused.path("gap_request").path("snapshot")).put("paused", false);
        assertEquals(LoanStatus.CURRENT_PLANNING_FRAME_UNAVAILABLE, EmergencyFinancingAssessmentCodec.assess(
                EmergencyFinancingAssessmentCodec.decode(SdkProjectionJson.encode(unpaused))).loan().status());
    }
    @Test void ackUnknownAndSubmittedNeverReplayAndKeepTheOriginalProcurementEpoch() throws Exception {
        LoanFinancingCodec.Projected loan = allowed();
        for (SubmissionState state : SubmissionState.values()) for (FundingKind kind : FundingKind.values()) {
            PendingAction action = new PendingAction(kind, "opaque-action-18446744073709551615", "same-procurement-epoch", state);
            Assessment result = EmergencyFinancingAssessment.assess(input(frame(loan), BigInteger.ZERO), loan, action, Optional.of(loan.planningFrame()));
            assertEquals(ReplayGuard.UNRESOLVED_ACTION_NEVER_REPLAY, result.replay());
            assertEquals(action, result.pending());
            assertEquals(result, EmergencyFinancingAssessmentCodec.decodeResult(EmergencyFinancingAssessmentCodec.encode(result))); zeroAuthority(result);
        }
    }
    @Test void jsonEntryDistinguishesMissingNullAndExplicitClearPendingAndRejectsBadTypes() throws Exception {
        ObjectNode wrapper = allowedWrapper(); ObjectNode request = (ObjectNode) StrictJson.parse(request(wrapper, null));
        Assessment unavailable = EmergencyFinancingAssessmentCodec.assess(EmergencyFinancingAssessmentCodec.decode(SdkProjectionJson.encode(request)));
        assertEquals(ReplayGuard.LEDGER_UNAVAILABLE, unavailable.replay());
        ObjectNode clear = StrictJson.object().put("status", "no_pending_action"); request.set("pending_observation", clear);
        assertEquals(ReplayGuard.NO_UNRESOLVED_ACTION_OBSERVED,
                EmergencyFinancingAssessmentCodec.assess(EmergencyFinancingAssessmentCodec.decode(SdkProjectionJson.encode(request))).replay());
        request.remove("pending_observation");
        assertThrows(IllegalArgumentException.class, () -> EmergencyFinancingAssessmentCodec.decode(SdkProjectionJson.encode(request)));
        ObjectNode integerType = (ObjectNode) StrictJson.parse(request(wrapper, null));
        ((ObjectNode) integerType.path("gap_request").path("snapshot")).put("revision", true);
        assertThrows(IllegalArgumentException.class, () -> EmergencyFinancingAssessmentCodec.decode(SdkProjectionJson.encode(integerType)));
        ((ObjectNode) integerType.path("gap_request").path("snapshot")).put("revision", 9.0);
        assertThrows(IllegalArgumentException.class, () -> EmergencyFinancingAssessmentCodec.decode(SdkProjectionJson.encode(integerType)));
    }
    @Test void persistedAssessmentCannotGrantFundsRefundSubmissionOrAlterItsActualWallet() throws Exception {
        ObjectNode result = (ObjectNode) StrictJson.parse(EmergencyFinancingAssessmentCodec.evaluate(request(allowedWrapper(), null)));
        for (String key : List.of("unreceived_funding_credited_raw", "raw_scale", "actual_wallet_raw")) {
            ObjectNode altered = result.deepCopy(); altered.put(key, 99);
            assertThrows(IllegalArgumentException.class, () -> EmergencyFinancingAssessmentCodec.decodeResult(StrictJson.canonical(altered)));
        }
        for (String key : List.of("submit_planned", "optional_construction_may_use_prospective_funding")) {
            ObjectNode altered = result.deepCopy(); altered.put(key, true);
            assertThrows(IllegalArgumentException.class, () -> EmergencyFinancingAssessmentCodec.decodeResult(StrictJson.canonical(altered)));
        }
        ObjectNode refund = result.deepCopy(); ((ObjectNode) refund.get("cancellation")).put("refund_quote_raw", 50);
        assertThrows(IllegalArgumentException.class, () -> EmergencyFinancingAssessmentCodec.decodeResult(StrictJson.canonical(refund)));
        ObjectNode debt = result.deepCopy(); ((ObjectNode) debt.get("loan")).put("typed_debt_readback_verified", true);
        assertThrows(IllegalArgumentException.class, () -> EmergencyFinancingAssessmentCodec.decodeResult(StrictJson.canonical(debt)));
    }
    @Test void consumerReadsCurrentInputsOnceAndRetainsTheOriginalGapBoundary() {
        Input original = input(baseFrame(), BigInteger.valueOf(20_000_000));
        var request = new EmergencyFinancingAssessmentCodec.Request(original, new LoanFinancingCodec.NotProvided(), new NoPendingAction(), Optional.empty());
        AtomicInteger reads = new AtomicInteger();
        Assessment result = EmergencyFinancingConsumer.observe(() -> { reads.incrementAndGet(); return request; });
        assertEquals(1, reads.get()); assertEquals(WarFinancingCapabilityGap.observe(original), result.gap()); assertTrue(result.gap().isEmpty());
        Input shortage = input(baseFrame(), BigInteger.valueOf(19_999_999));
        assertTrue(EmergencyFinancingAssessment.assess(shortage, new LoanFinancingCodec.NotProvided(), new NoPendingAction(), Optional.empty()).gap().isPresent());
        zeroAuthority(result);
    }
    private static void zeroAuthority(Assessment result) {
        assertEquals(0, result.unreceivedFundingCreditedRaw()); assertFalse(result.submitPlanned());
        assertTrue(result.refundQuoteRaw().isEmpty()); assertFalse(result.currentActiveProjectIndependentlyObserved());
        assertFalse(result.optionalConstructionMayUseProspectiveFunding()); assertTrue(result.continueExistingWarAction());
        assertTrue(result.futureFundingReceiptMustKeepSameProcurementEpoch());
    }
    private static Input input(ObservedFrame frame, BigInteger wallet) {
        return new Input(frame, Set.of(BigInteger.valueOf(7)),
                List.of(new PriorityWar(BigInteger.valueOf(7), true, Optional.of(BigInteger.ZERO), false, false, false, false)),
                Optional.of(wallet), Optional.of(BigInteger.ZERO), false, Optional.of(true));
    }
    private static ObservedFrame baseFrame() {
        return new ObservedFrame(BigInteger.valueOf(41), BigInteger.valueOf(12), BigInteger.valueOf(53_300_000),
                "synthetic-cash-source", BigInteger.valueOf(9), "synthetic-episode");
    }
    private static ObservedFrame frame(LoanFinancingCodec.Projected loan) {
        var f = loan.planningFrame(); return new ObservedFrame(f.actorCharacterId(), f.nativeRevision(), f.dateRaw(), f.snapshotId(), f.revision(), f.episodeRunId());
    }
    private static LoanFinancingCodec.Projected allowed() throws Exception {
        return (LoanFinancingCodec.Projected) LoanFinancingCodec.decodeAndProject(SdkProjectionJson.encode(allowedWrapper()));
    }
    private static ObjectNode allowedWrapper() throws Exception {
        for (Original vector : originals()) if (vector.kind().equals("result") && vector.expected().path("borrow_eligible").asBoolean()) {
            return vector.arguments().deepCopy();
        }
        throw new IllegalStateException("required retained allowed-gates vector absent");
    }
    private static byte[] request(ObjectNode loan, ObjectNode pending) {
        ObjectNode wrapper = StrictJson.object().put("schema", EmergencyFinancingAssessmentCodec.REQUEST_SCHEMA);
        ObjectNode gap = wrapper.putObject("gap_request").put("schema", FinancingGapCodec.REQUEST_SCHEMA);
        ObjectNode snapshot = ((ObjectNode) loan.get("snapshot")).deepCopy();
        snapshot.set("played_character_gold", loan.path("cash_resources").path("current_treasury").deepCopy()); gap.set("snapshot", snapshot);
        ObjectNode priority = gap.putObject("priority");
        priority.putArray("wars").addObject().put("war_id", 7).put("primary_player_war", true).put("player_relative_war_score", 0);
        gap.putNull("root"); gap.putNull("construction_ledger"); gap.putArray("bridge_capabilities").add(FinancingGapCodec.CAPABILITY);
        wrapper.set("loan_request", loan.deepCopy());
        if (pending == null) wrapper.putNull("pending_observation"); else wrapper.set("pending_observation", pending);
        return SdkProjectionJson.encode(wrapper);
    }
}
