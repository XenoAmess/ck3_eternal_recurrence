package org.xar.ck3.control.wave3.development.wartimesequencing;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.locks.ReentrantLock;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.holyloan.LoanFinancingCodec;
import org.xar.ck3.control.wave2.planning.warcashprovenance.EmergencyFinancingAssessment;
import org.xar.ck3.control.wave2.planning.warcashprovenance.EmergencyFinancingAssessmentCodec;
import org.xar.ck3.control.wave2.planning.warcashprovenance.FinancingGapModels;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionCash;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionCodec;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionModel;
import static org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction.*;

/** Original 31-vector differential plus NEW consumer compositions; these are not new historical goldens. */
final class OrdinaryWartimeConstructionTest {
    private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);

    @Test void originalCompleteProducerRemainsBytePinnedAndSemanticallyUnchanged() throws Exception {
        JsonNode original = golden(); assertEquals(31, original.get("cases").size());
        for (JsonNode row : original.get("cases")) {
            var input = WartimeConstructionCodec.decode(bytes(row.get("request")));
            assertEquals(row.get("expected"), StrictJson.parse(WartimeConstructionCodec.encode(WartimeConstructionCash.observe(input))), row.get("name").asText());
            ObjectNode request = envelope(row.get("request"), false);
            var result = OrdinaryWartimeConstructionCodec.verifyResponse(bytes(request), OrdinaryWartimeConstructionCodec.evaluate(bytes(request)));
            assertEquals(Optional.of("life-advance"), result.selectedStep()); assertTrue(result.continueOrdinaryPlanner());
            assertFalse(result.canSubmitAction()); assertEquals(BigInteger.ZERO, result.unreceivedFundingCreditedRaw());
        }
    }

    @Test void missingOptionalMarketDoesNotQueryOrStarveSelectedWarWork() throws Exception {
        ObjectNode unavailable = envelope(named("market_unavailable").get("request"), false);
        var pre = observed(unavailable); AtomicInteger quotes = new AtomicInteger();
        Result result = OrdinaryWartimeConstructionConsumer.plan(() -> pre, () -> { quotes.incrementAndGet(); throw new AssertionError("optional quote must not run"); });
        assertEquals(Disposition.DEFER_OPTIONAL_CONSTRUCTION, result.disposition()); assertEquals(0, quotes.get());
        unavailable.put("opportunity", "CONTINUE_SELECTED_WORK"); unavailable.put("original_selected_step", "native-war-army-route-v1");
        Result war = OrdinaryWartimeConstructionCodec.verifyResponse(bytes(unavailable), OrdinaryWartimeConstructionCodec.evaluate(bytes(unavailable)));
        assertEquals(Disposition.CONTINUE_SELECTED_WORK, war.disposition()); assertEquals(Optional.of("native-war-army-route-v1"), war.selectedStep());
        assertTrue(war.continueOrdinaryPlanner());
    }

    @Test void nativeFinalizerAuthoredSelectorAndBothMilitaryCashScenariosReachConsumer() throws Exception {
        ObjectNode quoted = complete(); var request = observed(quoted);
        Result result = OrdinaryWartimeConstructionConsumer.plan(() -> observed(envelope(quoted.get("cash_input"), false)),
                () -> new OrdinaryWartimeConstructionConsumer.ObservedQuote(request));
        assertEquals(Disposition.QUOTED_CANDIDATE, result.disposition());
        assertEquals(BigInteger.valueOf(23_000_000), result.candidate().orElseThrow().candidate().cost().orElseThrow());
        assertEquals(BigInteger.valueOf(77_000_000), result.cash().reserve().orElseThrow().required());
        assertEquals(BigInteger.valueOf(7_000_000), result.cash().reserve().orElseThrow().commitments());
        assertEquals(BigInteger.valueOf(-200_000), result.monthly().orElseThrow().prepared().orElseThrow().budget().current().netRate().orElseThrow());
        assertEquals(BigInteger.valueOf(-500_000), result.monthly().orElseThrow().prepared().orElseThrow().budget().allRaised().netRate().orElseThrow());
        assertEquals(Optional.of("life-advance"), result.selectedStep()); assertFalse(result.canSubmitAction());
        Result missingProvider = OrdinaryWartimeConstructionConsumer.plan(
                () -> observed(envelope(quoted.get("cash_input"), false)),
                () -> new OrdinaryWartimeConstructionConsumer.UnavailableQuote(OrdinaryWartimeConstructionConsumer.UnavailableReason.NATIVE_PROVIDER_UNAVAILABLE));
        assertEquals(Disposition.DEFER_OPTIONAL_CONSTRUCTION, missingProvider.disposition());
        assertEquals(Optional.of("life-advance"), missingProvider.selectedStep()); assertTrue(missingProvider.continueOrdinaryPlanner());
    }

    @Test void rejectedNativeLegalityAndUnknownExpenseOnlyDeferNewConstruction() throws Exception {
        ObjectNode quoted = complete(); world(quoted).put("native_final_legality_evaluated", false);
        Result rejected = compose(OrdinaryWartimeConstructionCodec.decode(bytes(quoted)));
        assertEquals(Optional.of(Reason.QUERY_SOURCE_UNAVAILABLE), rejected.reason()); assertTrue(rejected.continueOrdinaryPlanner());
        quoted = complete(); ObjectNode packet = cash(quoted); packet.withObject("/readiness").put("all_raised_military_expenses_ready", false);
        ObjectNode military = packet.withObject("/military_expenses/all_raised"); military.put("status", "unavailable");
        military.put("unavailable_reason", "native_all_raised_maintenance_unavailable"); military.putNull("gold_raw"); military.putNull("resource_raw_native");
        Result missing = compose(OrdinaryWartimeConstructionCodec.decode(bytes(quoted)));
        assertEquals(Optional.of(Reason.CURRENT_OR_ALL_RAISED_CASH_NOT_RETAINED), missing.reason());
        assertTrue(missing.monthly().orElseThrow().prepared().orElseThrow().budget().current().ready());
        assertFalse(missing.monthly().orElseThrow().prepared().orElseThrow().budget().allRaised().ready());
        assertEquals(Optional.of("life-advance"), missing.selectedStep());
        quoted = complete(); cash(quoted).remove("military_expenses");
        Result absentMilitary = compose(OrdinaryWartimeConstructionCodec.decode(bytes(quoted)));
        assertEquals(Disposition.DEFER_OPTIONAL_CONSTRUCTION, absentMilitary.disposition());
        assertEquals(Optional.of("life-advance"), absentMilitary.selectedStep()); assertTrue(absentMilitary.continueOrdinaryPlanner());
    }

    @Test void zeroSpendPrequerySuccessCannotReplaceTheActualQuotedOutlayCheck() throws Exception {
        ObjectNode below = (ObjectNode) named("one_raw_unit_below_threshold").get("request").deepCopy();
        ObjectNode quoted = complete(); quoted.set("cash_input", below);
        FinancingConstructionAdmissionTest.attachCurrentFinancing(quoted);
        long wallet = below.path("snapshot").path("played_character_gold").path("raw").bigIntegerValue().longValueExact();
        world(quoted).put("player_gold_raw", wallet); cash(quoted).withObject("/current_treasury").put("raw", wallet);
        ((ArrayNode) world(quoted).path("legal_samples").get(0).get("cost_raw_native")).set(0, below.get("construction_gold_raw"));
        AtomicInteger calls = new AtomicInteger();
        Result result = OrdinaryWartimeConstructionConsumer.plan(
                () -> observed(envelope(below, false)),
                () -> { calls.incrementAndGet(); return new OrdinaryWartimeConstructionConsumer.ObservedQuote(observed(quoted)); });
        assertEquals(1, calls.get()); assertEquals(Disposition.DEFER_OPTIONAL_CONSTRUCTION, result.disposition());
        assertEquals(WartimeConstructionModel.Reason.NOT_AMPLE, result.cash().reason().orElseThrow());
        assertEquals(BigInteger.valueOf(76_999_999), result.cash().reserve().orElseThrow().afterConstruction());
        assertEquals(Optional.of("life-advance"), result.selectedStep()); assertTrue(result.continueOrdinaryPlanner());
    }

    @Test void mismatchedCostFrameEpisodeAndExactBuildCannotCreateCandidate() throws Exception {
        ObjectNode quote = complete(); quote.withObject("/cash_input").put("construction_gold_raw", 22_000_000);
        assertEquals(Optional.of(Reason.QUOTE_COST_OR_WALLET_MISMATCH), compose(OrdinaryWartimeConstructionCodec.decode(bytes(quote))).reason());
        quote = complete(); quote.withObject("/quoted_outlay/query_observation/starting_snapshot").put("episode_run_id", "other-episode");
        quote.withObject("/quoted_outlay/query_observation/ending_snapshot").put("episode_run_id", "other-episode");
        assertEquals(Optional.of(Reason.QUOTE_FRAME_MISMATCH), compose(OrdinaryWartimeConstructionCodec.decode(bytes(quote))).reason());
        quote = complete(); cash(quote).put("queried_revision", 4);
        assertEquals(Optional.of(Reason.MONTHLY_CASH_SOURCE_MISMATCH), compose(OrdinaryWartimeConstructionCodec.decode(bytes(quote))).reason());
    }

    @Test void finalReadUsesOriginalLockAndNewCommitmentsBeforeOriginalIntentCallback() throws Exception {
        ObjectNode quote = complete(); Result planned = compose(OrdinaryWartimeConstructionCodec.decode(bytes(quote)));
        ObjectNode higher = quote.deepCopy(); higher.withObject("/cash_input/spending/budget/reserved_raw").put("gold", 8_000_000);
        ReentrantLock lock = new ReentrantLock(); AtomicInteger calls = new AtomicInteger(); AtomicInteger reads = new AtomicInteger();
        var refused = OrdinaryWartimeConstructionConsumer.withCurrentBeforeIntent(planned, lock, () -> {
            assertTrue(lock.isHeldByCurrentThread()); reads.incrementAndGet(); return observed(higher);
        }, result -> { calls.incrementAndGet(); return "should-not-create-intent"; });
        assertTrue(refused.existingAuthorityResult().isEmpty()); assertEquals(1, reads.get()); assertEquals(0, calls.get()); assertFalse(lock.isLocked());
        assertEquals(BigInteger.valueOf(8_000_000), refused.currentAssessment().orElseThrow().cash().reserve().orElseThrow().commitments());
        assertTrue(refused.continueOrdinaryPlanner()); assertFalse(refused.nativeActionAppliedVerified());
        JsonNode reviewed = StrictJson.parse(OrdinaryWartimeConstructionCodec.encodeFinalReview(refused.review()), OrdinaryWartimeConstructionCodec.MAX_BYTES);
        assertEquals(BigInteger.valueOf(8_000_000), reviewed.path("current_assessment").path("wartime_cash").path("existing_unpaid_commitments_raw").bigIntegerValue());
        assertFalse(reviewed.get("existing_authority_called").booleanValue()); assertFalse(reviewed.get("review_grants_authority").booleanValue());
        var roundTrip = OrdinaryWartimeConstructionCodec.decodeFinalReview(OrdinaryWartimeConstructionCodec.encodeFinalReview(refused.review()),
                Optional.of(OrdinaryWartimeConstructionCodec.decode(bytes(higher))));
        assertEquals(refused.status(), roundTrip.status()); assertFalse(roundTrip.nativeActionAppliedVerified());
        ((ObjectNode) reviewed).put("native_action_applied_verified", true);
        assertThrows(IllegalArgumentException.class, () -> OrdinaryWartimeConstructionCodec.decodeFinalReview(bytes(reviewed),
                Optional.of(OrdinaryWartimeConstructionCodec.decode(bytes(higher)))));
        var admitted = OrdinaryWartimeConstructionConsumer.withCurrentBeforeIntent(planned, lock,
                () -> observed(quote), result -> {
                    assertTrue(lock.isHeldByCurrentThread()); calls.incrementAndGet(); return "existing-authority-only";
                });
        assertEquals(Optional.of("existing-authority-only"), admitted.existingAuthorityResult()); assertEquals(1, calls.get()); assertFalse(lock.isLocked());
        assertFalse(admitted.nativeActionAppliedVerified());
    }

    @Test void finalChangedNativeQuoteOrFrameNeedsAReplan() throws Exception {
        ObjectNode quote = complete(); Result planned = compose(OrdinaryWartimeConstructionCodec.decode(bytes(quote)));
        ObjectNode changed = quote.deepCopy(); world(changed).withArray("legal_samples").get(0).withObject("/unused").put("marker", true);
        ReentrantLock lock = new ReentrantLock(); AtomicInteger calls = new AtomicInteger();
        assertTrue(OrdinaryWartimeConstructionConsumer.withCurrentBeforeIntent(planned, lock,
                () -> observed(changed), result -> { calls.incrementAndGet(); return "bad"; }).existingAuthorityResult().isEmpty());
        assertEquals(0, calls.get()); assertFalse(lock.isLocked());
    }

    @Test void pendingFinancingNeverCreditsMoneyOrReplaysAndKeepsWarAction() throws Exception {
        Request current = OrdinaryWartimeConstructionCodec.decode(bytes(complete())); var frame = current.current().context().snapshot().frame();
        FinancingGapModels.ObservedFrame source = new FinancingGapModels.ObservedFrame(frame.playedCharacterId(), frame.nativeRevision(), frame.dateRaw(), frame.snapshotId(), frame.revision(), frame.episodeRunId());
        FinancingGapModels.Input gap = new FinancingGapModels.Input(source, java.util.Set.of(BigInteger.ONE), List.of(),
                Optional.of(BigInteger.valueOf(100_000_000)), Optional.of(BigInteger.valueOf(451_200)), false, Optional.empty());
        var financing = new EmergencyFinancingAssessmentCodec.Request(gap, new LoanFinancingCodec.NotProvided(),
                new EmergencyFinancingAssessment.PendingAction(EmergencyFinancingAssessment.FundingKind.HOLY_ORDER_LOAN,
                        "actual-pending-fixture", "same-procurement-epoch", EmergencyFinancingAssessment.SubmissionState.UNKNOWN), Optional.empty());
        Result result = compose(new Request(current.selection(), current.stage(), current.current(), current.quoted(), Optional.of(financing)));
        assertEquals(Optional.of(Reason.FINANCING_ACTION_UNKNOWN), result.reason()); assertTrue(result.continueOrdinaryPlanner());
        assertEquals(0, result.financing().assessment().orElseThrow().unreceivedFundingCreditedRaw());
        assertTrue(result.financing().assessment().orElseThrow().refundQuoteRaw().isEmpty());
        assertEquals(EmergencyFinancingAssessment.CancellationStatus.NATIVE_FINAL_GATE_REFUND_AND_RECEIVER_UNAVAILABLE,
                result.financing().assessment().orElseThrow().cancellation());
        byte[] encoded = OrdinaryWartimeConstructionCodec.encode(result);
        assertFalse(StrictJson.parse(encoded, OrdinaryWartimeConstructionCodec.MAX_BYTES).get("can_submit_action").booleanValue());
    }

    @Test void strictBoundaryAndPersistedResponseRejectWrongFieldsTypesAndTampering() throws Exception {
        ObjectNode original = complete(); byte[] raw = bytes(original);
        assertEquals(Disposition.QUOTED_CANDIDATE, OrdinaryWartimeConstructionCodec.verifyResponse(raw, OrdinaryWartimeConstructionCodec.evaluate(raw)).disposition());
        ObjectNode missing = original.deepCopy(); missing.remove("financing_request"); assertThrows(IllegalArgumentException.class, () -> OrdinaryWartimeConstructionCodec.decode(bytes(missing)));
        ObjectNode extra = original.deepCopy(); extra.put("can_submit_action", true); assertThrows(IllegalArgumentException.class, () -> OrdinaryWartimeConstructionCodec.decode(bytes(extra)));
        for (JsonNode token : List.of(JSON.getNodeFactory().booleanNode(true), JSON.getNodeFactory().numberNode(23_000_000.0), JSON.getNodeFactory().textNode("23000000"))) {
            ObjectNode bad = original.deepCopy(); bad.withObject("/cash_input").set("construction_gold_raw", token);
            assertThrows(IllegalArgumentException.class, () -> OrdinaryWartimeConstructionCodec.decode(bytes(bad)));
        }
        String nativeEnvelope = new String(raw, java.nio.charset.StandardCharsets.UTF_8);
        assertTrue(nativeEnvelope.contains("\"protocol_version\":1"));
        for (String floating : List.of("1.0", "1e0")) assertThrows(IllegalArgumentException.class,
                () -> OrdinaryWartimeConstructionCodec.decode(nativeEnvelope.replace("\"protocol_version\":1", "\"protocol_version\":" + floating)
                        .getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        ObjectNode response = (ObjectNode) StrictJson.parse(OrdinaryWartimeConstructionCodec.evaluate(raw), OrdinaryWartimeConstructionCodec.MAX_BYTES);
        response.put("can_submit_action", true); assertThrows(IllegalArgumentException.class, () -> OrdinaryWartimeConstructionCodec.verifyResponse(raw, bytes(response)));
        assertThrows(IllegalArgumentException.class, () -> OrdinaryWartimeConstructionCodec.decode("{} {}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
    }

    @Test void optionalOpportunityMustMatchTheActualSelectedClockOrDeclaration() {
        assertThrows(IllegalArgumentException.class, () -> new Selection(Optional.of("native-war-army-route-v1"), Optional.empty(), Opportunity.ORDINARY_ADVANCE));
        assertDoesNotThrow(() -> new Selection(Optional.of("declare-war-2-0--1"), Optional.empty(), Opportunity.PREWAR_ARBITRATION));
        String valid = "advance-route-contact-horizon-v1-0-to-2-h-2-1-3";
        assertDoesNotThrow(() -> new Selection(Optional.of(valid), Optional.of("native_war_route_contact_horizon_progress"), Opportunity.QUIET_ROUTE_ADVANCE));
        assertThrows(IllegalArgumentException.class, () -> new Selection(Optional.of(valid), Optional.empty(), Opportunity.QUIET_ROUTE_ADVANCE));
        for (String invalid : List.of("advance-route-contact-horizon-v1-0-to-2-h-2-1-1", "advance-route-contact-horizon-v1-0-to-2-h-1-0",
                "advance-route-contact-horizon-v1-00-to-2-h-1-1", "advance-route-contact-horizon-v1-0-to-0-h-1-1",
                "advance-route-contact-horizon-v1-0-to-2-h-1-2147483648", "advance-route-contact-horizon-v1-0-to-2-h-65-1"))
            assertFalse(OrdinaryConstructionOpportunity.isAdvanceRouteContactHorizon(invalid), invalid);
    }

    static ObjectNode complete() throws Exception {
        ObjectNode input = (ObjectNode) named("exact_ample_threshold").get("request").deepCopy();
        ObjectNode request = envelope(input, true); ObjectNode outlay = request.withObject("/quoted_outlay");
        ObjectNode nativeInput = outlay.putObject("query_observation"); nativeInput.put("schema", "xar.construction-query-observation-input.v1");
        nativeInput.set("starting_snapshot", input.get("snapshot").deepCopy()); nativeInput.set("ending_snapshot", input.get("snapshot").deepCopy());
        nativeInput.put("expected_revision", 3); nativeInput.put("native_query_request_id", "new-controlled-query");
        nativeInput.put("material_receipt", false); nativeInput.put("wartime_observation", false);
        ObjectNode nativeEnvelope = nativeInput.putObject("native_envelope"); nativeEnvelope.put("type", "command_result");
        nativeEnvelope.put("protocol_version", 1); nativeEnvelope.put("request_id", "new-controlled-query"); nativeEnvelope.put("ok", true);
        ObjectNode result = nativeEnvelope.putObject("result"); result.put("step", "g2_player_construction_view_probe_v1"); result.put("accepted", true);
        ObjectNode probe = result.putObject("private_probe"); probe.put("advertised", false); probe.put("snapshot_revision", 3); probe.put("date_raw", 53288472); probe.put("proof_epoch", 1);
        ObjectNode world = probe.putObject("player_world_building_sources"); world.put("status", "source_available"); world.put("snapshot_revision", 3); world.put("date_raw", 53288472); world.put("player_character_id", 29829);
        world.put("native_final_legality_evaluated", true); world.put("native_cost_evaluated", true); world.put("player_gold_raw", 100_000_000);
        // The existing authored selector requires an observed idle barony, not an absent construction inventory.
        ObjectNode idle = world.putArray("active_constructions").addObject();
        idle.put("barony_title_id", 2103); idle.put("province_id", 2635); idle.put("active", false);
        world.put("completed_buildings_observed", true); world.putArray("completed_buildings"); world.put("positive_income_coverage_complete", true);
        ObjectNode sample = world.putArray("legal_samples").addObject(); sample.put("barony_title_id", 2103); sample.put("province_id", 2635);
        sample.put("building_type_id", 11); sample.put("slot_index", 0); sample.put("building_key", "farm_estates_01"); sample.put("native_cost_observed", true);
        var costs = sample.putArray("cost_raw_native"); costs.add(23_000_000); for (int i = 1; i < 10; i++) costs.add(0);
        ObjectNode observed = outlay.putObject("cash_observation"); observed.put("kind", "observed"); observed.put("reserve_gold_raw", 3_000_000); observed.set("cash", packet());
        return request;
    }
    private static ObjectNode packet() {
        ObjectNode cash = JSON.createObjectNode(); cash.put("schema", "xar.ck3.war-cash-current-resources.v1"); cash.put("read_only", true);
        cash.put("game_version", "1.20.0.4"); cash.put("executable_sha256", "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518");
        cash.put("played_character_id", 29829); cash.put("snapshot_revision", 3); cash.put("date_raw", 53288472);
        cash.put("queried_snapshot_id", "native:3"); cash.put("queried_revision", 3); cash.put("queried_native_revision", 3);
        String[] fields = {"current_treasury", "player_monthly_gross_income", "player_monthly_total_expenses", "player_monthly_net_income"};
        long[] amounts = {100_000_000, 800_000, 1_000_000, -200_000};
        for (int i = 0; i < fields.length; i++) cash.putObject(fields[i]).put("raw", amounts[i]).put("scale", 100000);
        ObjectNode semantics = cash.putObject("monthly_income_semantics"); semantics.put("version", "ck3-1.20.0.4-native-income-minus-total-expenses-v2");
        semantics.put("time_basis", "month"); semantics.put("source_scope", "played_character_personal_gold"); semantics.put("income_source", "native_character_monthly_gold_income");
        semantics.put("expense_source", "native_character_monthly_total_gold_expenses"); semantics.put("military_expenses_included", true);
        ObjectNode readiness = cash.putObject("readiness"); for (String flag : List.of("current_treasury_ready", "monthly_gross_income_ready", "monthly_total_expenses_ready", "monthly_net_income_ready", "current_military_expenses_ready", "all_raised_military_expenses_ready", "same_frame_ready")) readiness.put(flag, true);
        ObjectNode military = cash.putObject("military_expenses");
        for (String kind : List.of("current", "all_raised")) {
            int cost = kind.equals("current") ? 500_000 : 800_000; ObjectNode row = military.putObject(kind); row.put("status", "available"); row.put("gold_raw", cost);
            var vector = row.putArray("resource_raw_native"); vector.add(cost); for (int i = 1; i < 10; i++) vector.add(0);
        }
        return cash;
    }
    private static ObjectNode envelope(JsonNode cashInput, boolean quoted) {
        ObjectNode result = JSON.createObjectNode(); result.put("schema", OrdinaryWartimeConstructionCodec.SCHEMA);
        result.put("stage", quoted ? "QUOTED_OUTLAY" : "BEFORE_OPTIONAL_QUERY"); result.put("original_selected_step", "life-advance");
        result.putNull("original_phase");
        result.put("opportunity", "ORDINARY_ADVANCE"); result.set("cash_input", cashInput.deepCopy()); result.putNull("financing_request");
        if (quoted) result.putObject("quoted_outlay"); else result.putNull("quoted_outlay");
        FinancingConstructionAdmissionTest.attachCurrentFinancing(result); return result;
    }
    private static ObjectNode world(ObjectNode request) { return request.withObject("/quoted_outlay/query_observation/native_envelope/result/private_probe/player_world_building_sources"); }
    private static ObjectNode cash(ObjectNode request) { return request.withObject("/quoted_outlay/cash_observation/cash"); }
    private static JsonNode named(String name) throws Exception {
        for (JsonNode row : golden().get("cases")) if (row.get("name").textValue().equals(name)) return row;
        throw new IOException("required original vector missing: " + name);
    }
    private static JsonNode golden() throws Exception {
        byte[] compressed; String configured = System.getProperty("wartime.original.corpus");
        if (configured == null) {
            try (InputStream resource = OrdinaryWartimeConstructionTest.class.getResourceAsStream("/m4producer/wartime-original02.json.gz")) {
                if (resource == null) throw new IOException("required unchanged original wartime31 resource absent; NOT_RUN is not PASS");
                compressed = resource.readNBytes(32_001);
            }
        } else compressed = Files.readAllBytes(Path.of(configured));
        assertEquals(6379, compressed.length); assertEquals("4b3cf840085e5f3d53e290b4ea862e1357a3341a55180ff3670675caa5f6a585", HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(compressed)));
        try (GZIPInputStream input = new GZIPInputStream(new java.io.ByteArrayInputStream(compressed))) {
            byte[] raw = input.readNBytes(524_289); assertTrue(raw.length <= 524_288); return JSON.readTree(raw);
        }
    }
    private static byte[] bytes(JsonNode node) {
        try { return JSON.writeValueAsBytes(node); } catch (IOException failure) { throw new IllegalStateException(failure); }
    }
    private static OrdinaryWartimeConstructionCodec.ObservedRequest observed(JsonNode node) {
        return new OrdinaryWartimeConstructionCodec.ObservedRequest(bytes(node));
    }
}
