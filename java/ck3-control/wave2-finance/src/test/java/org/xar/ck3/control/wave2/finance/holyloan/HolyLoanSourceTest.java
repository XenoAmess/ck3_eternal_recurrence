package org.xar.ck3.control.wave2.finance.holyloan;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.holyloan.LoanFinancingCodec.PlanningFrame;

class HolyLoanSourceTest {
    private static final BigInteger EPOCH = new BigInteger("18446744073709551614");
    private static PlanningFrame frame(long actor) {
        return new PlanningFrame("loan-source:19", BigInteger.valueOf(19), BigInteger.valueOf(7), BigInteger.valueOf(53288496),
                BigInteger.valueOf(actor), "synthetic-loan-fixture", BigInteger.valueOf(123), new BigInteger("133700000000000001"));
    }
    /** Mandatory actual native fixture bytes. No Java-generated substitute and no skipped pass. */
    private static JsonNode golden() throws Exception {
        String configured = System.getProperty("xar.holy.loan.source.producer.golden");
        String sha = System.getProperty("xar.holy.loan.source.producer.golden.sha256");
        assertNotNull(configured, "actual native source producer golden role is required");
        assertNotNull(sha, "actual producer golden sha256 is required");
        assertTrue(sha.matches("[a-f0-9]{64}"));
        byte[] bytes = Files.readAllBytes(Path.of(configured));
        assertEquals(sha, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        ObjectNode node = StrictJson.object(StrictJson.parse(bytes), Set.of("schema", "rows"));
        assertEquals("xar.holy-loan-source-native-producer-golden.v1", node.get("schema").textValue());
        assertTrue(node.get("rows").isArray()); assertEquals(18, node.get("rows").size()); return node.get("rows");
    }
    private static ObjectNode receipt(JsonNode rows, int scenario) {
        ObjectNode row = StrictJson.object(rows.get(scenario), Set.of("scenario", "receipt"));
        assertEquals(scenario, StrictJson.integer(row.get("scenario"), scenario, scenario));
        return (ObjectNode) row.get("receipt").deepCopy();
    }
    private static HolyLoanSource.Result project(ObjectNode node, long actor) {
        return HolyLoanSource.projectNative(StrictJson.canonical(node), frame(actor), EPOCH);
    }
    @Test void actualNativeReadSerializeFeedsTheOnlyTypedQuoteConsumerAndPersistence() throws Exception {
        JsonNode rows = golden(); Set<Integer> available = Set.of(0,1,2,11,12,13,14,15);
        for (int scenario = 0; scenario < 18; scenario++) {
            long actor = scenario == 11 ? 0 : scenario == 12 ? 2147483649L : 17;
            var result = project(receipt(rows, scenario), actor);
            if (!available.contains(scenario)) { assertInstanceOf(HolyLoanSource.Unavailable.class, result); continue; }
            var quote = assertInstanceOf(HolyLoanSource.Quote.class, result);
            assertEquals(Long.MIN_VALUE, quote.borrowDecision().declaredCostsRaw().get(9).longValue());
            assertEquals(10, quote.borrowDecision().declaredCostsRaw().size()); assertEquals(8, quote.definitionFence().pointers().size());
            assertEquals(new BigInteger("9007199254749184"), quote.definitionFence().pointers().get(0).value());
            assertEquals(frame(actor), quote.frame()); assertEquals(EPOCH, quote.captureEpoch());
            assertFalse(quote.completeLoanTerms()); assertFalse(quote.submissionQualified()); assertFalse(quote.receivedFundsVerified());
            assertEquals(0, quote.fundingCreditRaw()); assertEquals(7, quote.missingEvidence().size());
            var copied = assertInstanceOf(HolyLoanSource.Quote.class, HolyLoanSource.decode(quote.toJson(), frame(actor), EPOCH));
            assertArrayEquals(quote.toJson(), copied.toJson());
            assertEquals(scenario == 2 || scenario == 13 ? HolyLoanSource.NextRead.NATIVE_DECISION_GATES_REFUSED
                    : scenario == 14 ? HolyLoanSource.NextRead.POSITIVE_NATIVE_PRINCIPAL_UNAVAILABLE
                    : HolyLoanSource.NextRead.INSPECT_ACTUAL_NATIVE_OFFER_REQUIRED, quote.nextRead());
            if (scenario == 1) { assertInstanceOf(HolyLoanSource.DebtUnavailable.class, quote.debt()); }
            if (scenario == 2) {
                var debt = assertInstanceOf(HolyLoanSource.CopiedDebt.class, quote.debt());
                assertEquals(91, debt.borrower().originalLoanHolder().orElseThrow().payloadRaw());
                assertEquals(2147483650L, debt.borrower().loanHolder().orElseThrow().payloadRaw());
                assertEquals(0, debt.lenderYearsRow().orElseThrow().payloadRaw());
                assertEquals(0, debt.lenderYearsRow().orElseThrow().expiryRaw());
                assertEquals(-1, debt.lenderClockRaw().orElseThrow());
                assertTrue(debt.lenderMembership().isEmpty()); assertFalse(debt.expirySemanticsQualified());
                assertEquals(new HolyLoanSource.ScalarClock(HolyLoanSource.ClockKind.NEGATIVE_EXPIRY, -1, 0, -1),
                        debt.borrowerClock(HolyLoanSource.BorrowerScalar.LOAN_AMOUNT_OWED).orElseThrow());
                assertEquals(new HolyLoanSource.ScalarClock(HolyLoanSource.ClockKind.TIMED_COUNTER, 0, -1, 1),
                        debt.lenderYearsClock().orElseThrow());
                var restoredDebt = assertInstanceOf(HolyLoanSource.CopiedDebt.class, copied.debt());
                assertEquals(debt.lenderYearsClock(), restoredDebt.lenderYearsClock());
            }
            if (scenario == 15) { assertFalse(((HolyLoanSource.CopiedDebt) quote.debt()).holderResolved().orElseThrow()); }
        }
    }
    @Test void nativeCounterProjectionKeepsTimedMinusOneAndWrapDistinctWithoutCalendarOrFundingCredit() throws Exception {
        // Start at the real producer->consumer debt copy, retaining every frame/fence check.
        ObjectNode source = receipt(golden(), 2);
        var debt = (ObjectNode) source.get("debt_copy");
        var owed = (ObjectNode) debt.get("borrower_rows").get("loan_amount_owed");
        debt.put("borrower_clock_raw", 101); owed.put("expiry_raw", 100);
        var quote = assertInstanceOf(HolyLoanSource.Quote.class, project(source, 17));
        var copied = assertInstanceOf(HolyLoanSource.CopiedDebt.class, quote.debt());
        var timed = copied.borrowerClock(HolyLoanSource.BorrowerScalar.LOAN_AMOUNT_OWED).orElseThrow();
        assertEquals(HolyLoanSource.ClockKind.TIMED_COUNTER, timed.kind()); assertEquals(-1, timed.remainingRaw());
        // Same integer result, different source state: never infer active/expired from -1 alone.
        assertEquals(HolyLoanSource.ClockKind.NEGATIVE_EXPIRY,
                copied.borrowerClock(HolyLoanSource.BorrowerScalar.LOAN_HOLDER).orElseThrow().kind());
        owed.put("expiry_raw", Integer.MAX_VALUE); debt.put("borrower_clock_raw", Integer.MIN_VALUE);
        var wrapped = (HolyLoanSource.Quote) project(source, 17);
        var wrappedDebt = (HolyLoanSource.CopiedDebt) wrapped.debt();
        assertEquals(-1, wrappedDebt.borrowerClock(HolyLoanSource.BorrowerScalar.LOAN_AMOUNT_OWED).orElseThrow().remainingRaw());
        assertFalse(wrappedDebt.expirySemanticsQualified()); assertTrue(wrappedDebt.lenderMembership().isEmpty());
        assertEquals(0, wrapped.fundingCreditRaw()); assertFalse(wrapped.completeLoanTerms());
        assertArrayEquals(wrapped.toJson(), ((HolyLoanSource.Quote) HolyLoanSource.decode(wrapped.toJson(), frame(17), EPOCH)).toJson());
        var empty = (HolyLoanSource.CopiedDebt) ((HolyLoanSource.Quote) project(receipt(golden(), 0), 17)).debt();
        assertTrue(empty.borrowerClock(HolyLoanSource.BorrowerScalar.LOAN_AMOUNT_OWED).isEmpty());
        assertTrue(empty.lenderYearsClock().isEmpty());
        assertThrows(IllegalArgumentException.class, () -> new HolyLoanSource.ScalarClock(HolyLoanSource.ClockKind.NEGATIVE_EXPIRY, 0, 0, -1));
        assertThrows(IllegalArgumentException.class, () -> new HolyLoanSource.ScalarClock(HolyLoanSource.ClockKind.TIMED_COUNTER, 100, 101, 0));
    }
    @Test void copiedNativeTermsNeverImpersonateEffectTransfersReceivedFundsOrCompleteLoans() throws Exception {
        ObjectNode actual = receipt(golden(), 0);
        for (String field : Set.of("complete_loan_terms", "submission_qualified", "received_funds_verified")) {
            ObjectNode changed = actual.deepCopy(); changed.put(field, true);
            assertThrows(IllegalArgumentException.class, () -> project(changed, 17));
        }
        for (String field : Set.of("raw_scale", "resource_slot_count", "funding_credit_raw")) {
            ObjectNode changed = actual.deepCopy(); changed.put(field, true);
            assertThrows(IllegalArgumentException.class, () -> project(changed, 17));
        }
        ObjectNode effect = actual.deepCopy(); effect.put("decision_cost_scope", "full_repayment_outlay");
        assertThrows(IllegalArgumentException.class, () -> project(effect, 17));
        ObjectNode membership = actual.deepCopy(); ((ObjectNode) membership.get("debt_copy")).put("lender_membership", true);
        assertThrows(IllegalArgumentException.class, () -> project(membership, 17));
        ObjectNode alias = actual.deepCopy(); alias.put("principal_quote_raw", 999);
        assertThrows(IllegalArgumentException.class, () -> project(alias, 17));
        ObjectNode missing = actual.deepCopy(); missing.remove("prospective_principal_raw");
        assertThrows(IllegalArgumentException.class, () -> project(missing, 17));
    }
    @Test void exactFrameConnectionEpochDefinitionsAndMutableContentRequireAFreshNativeRead() throws Exception {
        ObjectNode actual = receipt(golden(), 0); var old = (HolyLoanSource.Quote) project(actual, 17);
        ObjectNode changed = actual.deepCopy(); changed.put("capture_epoch", EPOCH.subtract(BigInteger.ONE).toString());
        var fresh = (HolyLoanSource.Quote) HolyLoanSource.projectNative(StrictJson.canonical(changed), frame(17), EPOCH.subtract(BigInteger.ONE));
        assertEquals(HolyLoanSource.CopyComparison.SAME_CAPTURED_CONTENT_USE_CURRENT, HolyLoanSource.compareCopies(old, fresh));
        assertThrows(IllegalArgumentException.class, () -> HolyLoanSource.compareCopies(old, old));
        ObjectNode altered = changed.deepCopy(); ((ObjectNode) altered.get("definition_fence")).put("variable_epoch", 8);
        var reloaded = (HolyLoanSource.Quote) HolyLoanSource.projectNative(StrictJson.canonical(altered), frame(17), EPOCH.subtract(BigInteger.ONE));
        assertEquals(HolyLoanSource.CopyComparison.DEFINITIONS_OR_IDENTIFIER_EPOCH_CHANGED, HolyLoanSource.compareCopies(old, reloaded));
        ObjectNode valueChanged = changed.deepCopy(); valueChanged.put("prospective_principal_raw", 30000001);
        var repriced = (HolyLoanSource.Quote) HolyLoanSource.projectNative(StrictJson.canonical(valueChanged), frame(17), EPOCH.subtract(BigInteger.ONE));
        assertEquals(HolyLoanSource.CopyComparison.QUOTE_CONTENT_CHANGED, HolyLoanSource.compareCopies(old, repriced));
        var expected = frame(17);
        var reconnected = new PlanningFrame(expected.snapshotId(), expected.revision(), expected.nativeRevision(), expected.dateRaw(), expected.actorCharacterId(),
                expected.episodeRunId(), expected.bridgePid(), expected.connectionGeneration().add(BigInteger.ONE));
        assertEquals(new HolyLoanSource.Refused(HolyLoanSource.Refusal.FRAME_DRIFT), HolyLoanSource.decode(old.toJson(), reconnected, EPOCH));
        actual.put("native_revision", "19");
        assertEquals(new HolyLoanSource.Refused(HolyLoanSource.Refusal.FRAME_DRIFT), project(actual, 17));
    }
    @Test void rawDebtKindsNullsFullIdsAndUint64StringsAreStrict() throws Exception {
        ObjectNode actual = receipt(golden(), 2);
        ObjectNode wrongKind = actual.deepCopy(); ((ObjectNode) wrongKind.get("debt_copy").get("borrower_rows").get("loan_holder")).put("kind", 1);
        assertThrows(IllegalArgumentException.class, () -> project(wrongKind, 17));
        ObjectNode sentinel = actual.deepCopy(); ((ObjectNode) sentinel.get("debt_copy").get("borrower_rows").get("loan_holder")).put("payload_raw", 4294967295L);
        assertThrows(IllegalArgumentException.class, () -> project(sentinel, 17));
        ObjectNode epochNumber = actual.deepCopy(); epochNumber.put("capture_epoch", EPOCH);
        assertThrows(IllegalArgumentException.class, () -> project(epochNumber, 17));
        ObjectNode pointerNumber = actual.deepCopy(); ((ObjectNode) pointerNumber.get("debt_copy")).put("borrower_context", new BigInteger("9007199254750752"));
        assertThrows(IllegalArgumentException.class, () -> project(pointerNumber, 17));
        ObjectNode unavailable = receipt(golden(), 3); unavailable.set("borrow_decision", actual.get("borrow_decision"));
        assertThrows(IllegalArgumentException.class, () -> project(unavailable, 17));
    }

    @Test void capturedNativeResourceComparisonFeedsTheActualProducerConsumerAndPersistenceBoundary() throws Exception {
        String configured = System.getProperty("xar.m4.loan.affordability.capture.manifest");
        String expectedSha = System.getProperty("xar.m4.loan.affordability.capture.manifest.sha256");
        assertNotNull(configured, "actual captured native helper manifest role is mandatory");
        assertNotNull(expectedSha, "actual capture manifest digest role is mandatory");
        assertEquals("1ea912cd58a88941415a6876d0a2387087ad120ce2bac5fad4da2c45b729bc8e", expectedSha);
        Path manifest = Path.of(configured);
        byte[] original = Files.readAllBytes(manifest);
        assertEquals(expectedSha, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
        JsonNode capture = StrictJson.parse(original);
        assertEquals("xar.native-raw-window-capture/v1", StrictJson.text(capture.get("schema")));
        assertEquals("COMPLETE", StrictJson.text(capture.get("status")));
        assertTrue(HolyLoanCodec.SHA256.equalsIgnoreCase(StrictJson.text(capture.get("inherited_image_sha256"))));
        assertEquals(468, StrictJson.integer(capture.get("counts").get("reported_read").get("code"), 468, 468));
        assertEquals(1808, StrictJson.integer(capture.get("counts").get("reported_read").get("metadata"), 1808, 1808));
        assertEquals(0, StrictJson.integer(capture.get("counts").get("unknown_read_outcomes"), 0, 0));
        assertTrue(capture.get("windows").isArray()); assertEquals(4, capture.get("windows").size());
        byte[] helper = null;
        for (JsonNode window : capture.get("windows")) {
            assertEquals("COMPLETE", StrictJson.text(window.get("status")));
            JsonNode artifact = window.get("raw_artifact");
            String name = StrictJson.text(artifact.get("filename"));
            assertTrue(name.matches("window-00[0-3]\\.raw"), "original sibling artifact only");
            byte[] raw = Files.readAllBytes(manifest.getParent().resolve(name));
            assertEquals(StrictJson.integer(artifact.get("bytes"), 1, 888), raw.length);
            assertEquals(StrictJson.text(artifact.get("sha256")),
                    HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
            if ("whole-rf-310edc0".equals(StrictJson.text(window.get("window").get("id")))) { helper = raw; }
        }
        assertNotNull(helper); assertEquals(468, helper.length);
        assertEquals("6b37f4be70816f9b2f970ca0642d41d089ae1c04ce79a23e4d2753ecc34bf279",
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(helper)));
        // Actual zero-cost and signed-JGE branches; do not recreate native affordability in Java.
        assertArrayEquals(HexFormat.of().parseHex("4d85c00f847b010000488b02493bc00f8d6f010000"),
                java.util.Arrays.copyOfRange(helper, 0x31, 0x46));
        assertArrayEquals(HexFormat.of().parseHex("32c0eb02b001"), java.util.Arrays.copyOfRange(helper, 0x1b1, 0x1b7));
        JsonNode producerRows = golden(); // Actual C++ Read+Serialize producer; no Java-generated receipt.
        for (int scenario : new int[] {0, 2, 13}) {
            ObjectNode nativeReceipt = receipt(producerRows, scenario);
            var quote = assertInstanceOf(HolyLoanSource.Quote.class, project(nativeReceipt, 17));
            var restored = assertInstanceOf(HolyLoanSource.Quote.class,
                    HolyLoanSource.decode(quote.toJson(), frame(17), EPOCH));
            JsonNode persistedNative = StrictJson.parse(restored.toJson()).get("native_observation");
            for (String decision : Set.of("borrow_decision", "repay_decision")) {
                assertEquals(nativeReceipt.get(decision), persistedNative.get(decision));
            }
            for (int index = 0; index < 10; index++) {
                assertEquals(StrictJson.integer(nativeReceipt.get("borrow_decision").get("costs_raw_by_native_index").get(index),
                        Long.MIN_VALUE, Long.MAX_VALUE), restored.borrowDecision().declaredCostsRaw().get(index).longValue());
            }
            assertEquals(0, restored.fundingCreditRaw());
            assertFalse(restored.completeLoanTerms()); assertFalse(restored.submissionQualified());
            assertFalse(restored.receivedFundsVerified());
            assertTrue(restored.missingEvidence().contains(HolyLoanSource.MissingEvidence.EFFECT_TRANSFER_AND_REPAYMENT_OUTLAY));
        }
        ObjectNode malformed = receipt(producerRows, 0);
        ((ObjectNode) malformed.get("borrow_decision")).put("affordable", 1);
        assertThrows(IllegalArgumentException.class, () -> project(malformed, 17));
    }
}
