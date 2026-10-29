package org.xar.ck3.control.militaryfinance;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.DeserializationFeature;
import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanModel;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionCash;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionCodec;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionModel;

/** Standard JUnit engine regressions over the actual retained original-producer corpus. */
final class MilitaryFinanceResearchTest {
    private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);
    private static final String GOLDEN = "/m4producer/wartime-original02.json.gz";
    private static final String GOLDEN_SHA = "4b3cf840085e5f3d53e290b4ea862e1357a3341a55180ff3670675caa5f6a585";

    @Test void everyOriginalProducerVectorKeepsSharedDecisionAndJsonRoundTrip() throws Exception {
        JsonNode vectors = corpus().path("cases");
        assertEquals(31, vectors.size());
        for (JsonNode vector : vectors) {
            var input = decode(vector);
            var result = MilitaryFinanceResearch.assess(MilitaryFinanceResearch.Request.currentGateOnly(input));
            JsonNode output = StrictJson.parse(MilitaryFinanceJson.encode(result), StrictJson.EXPLICIT_MAX_BYTES);
            assertEquals(vector.get("expected"), output.get("construction_decision"), vector.path("name").asText());
            assertEquals(WartimeConstructionCash.observe(input), result.constructionDecision());
            assertEquals(output, StrictJson.parse(StrictJson.canonical(output, StrictJson.EXPLICIT_MAX_BYTES), StrictJson.EXPLICIT_MAX_BYTES));
            assertEquals(BigInteger.ZERO, result.funding().fundingCreditRaw());
            assertFalse(result.funding().actionSubmissionQualified());
            assertFalse(result.funding().newProcurementEpochOpened());
        }
    }

    @Test void unboughtCompanyCannotAcquireEtaFromContradictorySideObservation() throws Exception {
        var input = input("exact_ample_threshold");
        var quote = input.quotes().getFirst().quote();
        assertEquals(GiftWarCashModel.Presence.NULL, quote.employer());
        var result = assess(input, List.of(route(input, input.context().snapshot().frame(), input.context().snapshot().actor().value())));
        var arrival = result.offers().getFirst().arrival();
        assertEquals(MilitaryFinanceResearch.ArrivalKind.UNBOUGHT_COMPANY_NO_CUNIT_ROUTE, arrival.kind());
        assertTrue(arrival.actualArmyId().isEmpty());
        assertTrue(arrival.forecastDays().isEmpty());
        assertEquals(WartimeConstructionCash.observe(input), result.constructionDecision());
    }

    @Test void employedCompanyForecastRequiresSameCompleteFrameAndObservedEmployer() throws Exception {
        var original = input("exact_ample_threshold");
        var q = original.quotes().getFirst().quote();
        var hired = withQuote(original, new GiftWarCashModel.QuoteRow(q.companyId(), GiftWarCashModel.Presence.VALUE,
                q.costs(), q.resourceScale(), q.available(), q.canHire(), q.canAfford(), q.hireReady(), q.troopsAvailable(),
                q.currentSoldiers(), q.spawnProvince(), q.positionReady(), q.attemptedInActiveWar()));
        var frame = hired.context().snapshot().frame();
        var forecast = assess(hired, List.of(route(hired, frame, frame.playedCharacterId()))).offers().getFirst().arrival();
        assertEquals(MilitaryFinanceResearch.ArrivalKind.CURRENT_NATIVE_ROUTE_FORECAST, forecast.kind());
        assertEquals(Optional.of(BigInteger.valueOf(9)), forecast.forecastDays());
        assertFalse(forecast.actualArrivalVerified());
        assertFalse(forecast.arrivalBeforeLossGuaranteed());
        var stale = new GiftWarCashModel.SourceFrame(frame.playedCharacterId(), frame.nativeRevision().add(BigInteger.ONE),
                frame.dateRaw(), frame.snapshotId(), frame.revision(), frame.episodeRunId());
        assertTrue(assess(hired, List.of(route(hired, stale, frame.playedCharacterId()))).offers().getFirst().arrival().forecastDays().isEmpty());
        assertTrue(assess(hired, List.of(route(hired, frame, frame.playedCharacterId().add(BigInteger.ONE)))).offers().getFirst().arrival().forecastDays().isEmpty());
    }

    @Test void warLossFocusAndEmergencyReserveRemainTheOriginalSharedPolicy() throws Exception {
        var input = input("cheapest_adequate_quote");
        var result = MilitaryFinanceResearch.assess(MilitaryFinanceResearch.Request.currentGateOnly(input));
        var reserve = result.constructionDecision().reserve().orElseThrow();
        assertEquals(WartimeConstructionModel.SelectionBasis.CHEAPEST_ADEQUATE, reserve.basis());
        assertTrue(reserve.focusedWar().isPresent());
        assertTrue(reserve.observedDeficit().orElseThrow().signum() > 0);
        assertEquals(reserve.militaryBuffer().add(reserve.commitments()).add(reserve.selected().contractGold().orElseThrow()), reserve.required());
        assertEquals(WartimeConstructionCash.FIXED_BUFFER.max(reserve.maximumMaintenance().multiply(BigInteger.valueOf(24))), reserve.militaryBuffer());
        var candidate = input("current_assessed_suitable_quote");
        assertEquals(WartimeConstructionModel.SelectionBasis.ASSESSED,
                MilitaryFinanceResearch.assess(MilitaryFinanceResearch.Request.currentGateOnly(candidate)).constructionDecision().reserve().orElseThrow().basis());
    }

    @Test void permittedNativeDebtDoesNotWeakenEmergencyCashOrImplyBattleProbability() throws Exception {
        var original = input("exact_ample_threshold");
        var q = original.quotes().getFirst().quote();
        var input = withQuote(original, new GiftWarCashModel.QuoteRow(q.companyId(), q.employer(), q.costs(), q.resourceScale(),
                q.available(), GiftWarCashModel.Read.of(true), GiftWarCashModel.Read.of(false), q.hireReady(), q.troopsAvailable(),
                q.currentSoldiers(), q.spawnProvince(), q.positionReady(), q.attemptedInActiveWar()));
        var frame = input.context().snapshot().frame();
        var terms = new MilitaryFinanceResearch.NativeTerms(frame, MilitaryFinanceResearch.EXE_SHA256, q.companyId().value(),
                MilitaryFinanceResearch.NativePayment.NATIVE_PERMITTED_DEBT, BigInteger.valueOf(36));
        var counts = new MilitaryFinanceResearch.StrengthObservation(frame, input.context().snapshot().wars().value().getFirst().warId().value(),
                BigInteger.valueOf(500), BigInteger.valueOf(1000), MilitaryFinanceResearch.StrengthScope.DEDUPLICATED_WAR_HEADCOUNTS);
        var result = MilitaryFinanceResearch.assess(new MilitaryFinanceResearch.Request(input, Optional.of(counts), List.of(terms), List.of(), Optional.empty()));
        var offer = result.offers().getFirst();
        assertEquals(MilitaryFinanceResearch.NativeLegality.LEGAL_PERMITTED_DEBT, offer.nativeLegality());
        assertFalse(offer.sharedReserveQuoteUsable());
        assertTrue(offer.conditionalCounts().isPresent());
        assertTrue(offer.battleWinProbability().isEmpty());
        assertTrue(offer.reasons().contains(MilitaryFinanceResearch.Reason.JOINT_ARRIVAL_UNVERIFIED));
        assertEquals(WartimeConstructionCash.observe(input), result.constructionDecision());
    }

    @Test void unknownCommitmentIsPreservedWithoutNewActionOrProcurementEpoch() throws Exception {
        var input = input("mercenary_pending_unknown");
        var result = MilitaryFinanceResearch.assess(MilitaryFinanceResearch.Request.currentGateOnly(input));
        assertFalse(result.constructionDecision().newSpendAllowed());
        assertTrue(result.funding().unresolvedCommitmentPreserved());
        assertEquals(BigInteger.ZERO, result.funding().fundingCreditRaw());
        assertFalse(result.funding().newProcurementEpochOpened());
        assertFalse(result.funding().actionSubmissionQualified());
    }

    @Test void nativeLoanGatesDoNotCreateUnreceivedPrincipalOrRefundQuote() throws Exception {
        var input = input("one_raw_unit_below_threshold");
        var frame = input.context().snapshot().frame();
        var costs = List.of(0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L);
        var observed = new HolyLoanModel.Observation(new HolyLoanModel.ExpectedFrame(frame.playedCharacterId().intValueExact(),
                frame.dateRaw().intValueExact(), HolyLoanModel.UINT64_MAX), new HolyLoanModel.Available(),
                new HolyLoanModel.ObservedDecision(HolyLoanModel.Definition.BORROW, true, true, true, costs),
                new HolyLoanModel.ObservedDecision(HolyLoanModel.Definition.REPAY, true, true, true, costs));
        var result = MilitaryFinanceResearch.assess(new MilitaryFinanceResearch.Request(input, Optional.empty(), List.of(), List.of(),
                Optional.of(new MilitaryFinanceResearch.BoundLoan(frame, observed))));
        assertEquals(MilitaryFinanceResearch.LoanStatus.DECISION_GATES_ONLY_COMPLETE_TERMS_MISSING, result.funding().loanStatus());
        assertEquals(MilitaryFinanceResearch.FundingNeed.REVIEW_CURRENT_FUNDING_OPTIONS, result.funding().need());
        JsonNode output = StrictJson.parse(MilitaryFinanceJson.encode(result), StrictJson.EXPLICIT_MAX_BYTES);
        assertTrue(output.path("funding").path("refund_quote_raw").isNull());
        assertTrue(output.path("funding").path("loan_principal_quote_raw").isNull());
        assertEquals(BigInteger.ZERO, result.funding().fundingCreditRaw());
    }

    @Test void sourceArithmeticRetainsSigned64AndVersionQualification() {
        var ratio = VanillaWarChestCaller12003.project(new VanillaWarChestCaller12003.Operands(100, 18, 300_000, 100_000));
        assertEquals(300_000L, ratio.goldTreasuryRatioRaw());
        assertEquals(30_000_000L, ratio.resourceTargetsRaw().getFirst());
        assertFalse(ratio.current12004Qualified());
        assertFalse(ratio.fullNativeAiChoiceReconstructed());
        assertFalse(ratio.futureWarCostUpperBound());
        var wrapped = VanillaWarChestCaller12003.project(new VanillaWarChestCaller12003.Operands(0, 18, Long.MIN_VALUE, 0));
        assertEquals(0L, wrapped.resourceTargetsRaw().getFirst());
    }

    private static MilitaryFinanceResearch.Assessment assess(WartimeConstructionModel.Input input,
            List<MilitaryFinanceResearch.RouteObservation> routes) {
        return MilitaryFinanceResearch.assess(new MilitaryFinanceResearch.Request(input, Optional.empty(), List.of(), routes, Optional.empty()));
    }
    private static MilitaryFinanceResearch.RouteObservation route(WartimeConstructionModel.Input input,
            GiftWarCashModel.SourceFrame frame, BigInteger employer) {
        return new MilitaryFinanceResearch.RouteObservation(frame, input.quotes().getFirst().quote().companyId().value(),
                employer, BigInteger.valueOf(27), BigInteger.valueOf(2618), BigInteger.valueOf(9));
    }
    private static WartimeConstructionModel.Input withQuote(WartimeConstructionModel.Input input, GiftWarCashModel.QuoteRow quote) {
        return new WartimeConstructionModel.Input(input.kindWire(), input.cost(), input.context(),
                List.of(new WartimeConstructionModel.QuoteEvidence(quote, WartimeConstructionModel.GroupShape.ALL_OBJECTS)),
                input.marketShape(), input.procurement(), input.focusRequest());
    }
    private static WartimeConstructionModel.Input input(String name) throws Exception {
        for (JsonNode vector : corpus().path("cases")) if (name.equals(vector.path("name").asText())) return decode(vector);
        throw new AssertionError("original vector missing: " + name);
    }
    private static WartimeConstructionModel.Input decode(JsonNode vector) throws Exception {
        return WartimeConstructionCodec.decode(JSON.writeValueAsBytes(vector.get("request")));
    }
    private static JsonNode corpus() throws Exception {
        byte[] compressed;
        try (InputStream stream = MilitaryFinanceResearchTest.class.getResourceAsStream(GOLDEN)) {
            assertNotNull(stream, "exact original producer resource is required");
            compressed = stream.readAllBytes();
        }
        assertEquals(6379, compressed.length);
        assertEquals(GOLDEN_SHA, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(compressed)));
        try (InputStream stream = new GZIPInputStream(new ByteArrayInputStream(compressed))) {
            byte[] raw = stream.readNBytes(1_048_577);
            assertTrue(raw.length > 0 && raw.length <= 1_048_576);
            JsonNode root = JSON.readTree(raw);
            assertEquals("xar.wartime-construction-original-producer-golden.v1", root.path("schema").asText());
            return root;
        }
    }
}
