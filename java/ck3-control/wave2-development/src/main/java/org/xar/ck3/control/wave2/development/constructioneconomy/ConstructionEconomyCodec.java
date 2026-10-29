package org.xar.ck3.control.wave2.development.constructioneconomy;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.wave2.development.ConstructionInputValidation;
import org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.EnumMap;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

import static org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel.*;

/** Strict declared numeric fields; SDK receipt and cash containers remain extensible. */
public final class ConstructionEconomyCodec {
    public static final int MAX_BYTES = 131_072;
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(64).maxNumberLength(128).maxStringLength(65_536).build()).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private static final BigInteger I64_MIN = BigInteger.ONE.shiftLeft(63).negate();
    private static final BigInteger I64_MAX = BigInteger.ONE.shiftLeft(63).subtract(BigInteger.ONE);
    private static final BigInteger U32_MAX = BigInteger.ONE.shiftLeft(32).subtract(BigInteger.ONE);
    private static final BigInteger U64_MAX = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private static final String SHA3 = "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
    private static final String SHA4 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private ConstructionEconomyCodec() { }

    public static OutcomeRequest decodeOutcomeRequest(byte[] bytes) {
        ObjectNode root = StrictJson.object(parse(bytes),
                Set.of("schema", "receipt", "exact_ck3_build", "pre_cash_v2", "post_cash_v2"));
        if (!text(root.get("schema"), "schema").equals("xar.ck3.construction-economy-input.v1")) throw invalid("outcome input schema");
        return new OutcomeRequest(receipt(root.get("receipt")), text(root.get("exact_ck3_build"), "exact_ck3_build"),
                cashOptional(root.get("pre_cash_v2")), cashOptional(root.get("post_cash_v2")));
    }
    public static BudgetRequest decodeBudgetRequest(byte[] bytes) {
        ObjectNode root = StrictJson.object(parse(bytes), Set.of("schema", "cash",
                "construction_gold_cost_raw", "reserve_gold_raw", "existing_commitment_gold_raw", "horizon_months"));
        if (!text(root.get("schema"), "schema").equals("xar.ck3.construction-monthly-budget-input.v1")) throw invalid("budget input schema");
        return new BudgetRequest(cash(root.get("cash")), new BudgetPolicy(
                nonnegative(root.get("construction_gold_cost_raw"), "construction_gold_cost_raw"),
                nonnegative(root.get("reserve_gold_raw"), "reserve_gold_raw"),
                nonnegative(root.get("existing_commitment_gold_raw"), "existing_commitment_gold_raw"),
                Math.toIntExact(ConstructionInputValidation.read(() -> StrictJson.integer(root.get("horizon_months"), 1, 24)))));
    }
    public static Receipt decodeReceipt(byte[] bytes) { return receipt(parse(bytes)); }
    public static CashPacket decodeCash(byte[] bytes) { return cash(parse(bytes)); }
    public static ConstructionQuote decodeQuote(byte[] bytes) {
        return decodeQuoteProjection(parse(bytes));
    }
    static Receipt decodeReceiptProjection(JsonNode raw) { return receipt(raw); }
    static CashPacket decodeCashProjection(JsonNode raw) { return cash(raw); }
    static JsonNode parseProjection(byte[] raw) { return parse(raw); }
    static ConstructionQuote decodeQuoteProjection(JsonNode raw) {
        object(raw, "construction quote");
        JsonNode c = raw.get("candidate"); object(c, "quote candidate");
        Optional<QuoteFrame> frame = Optional.empty();
        JsonNode source = raw.get("source_frame");
        if (!absent(source)) {
            object(source, "quote source_frame");
            frame = Optional.of(new QuoteFrame(identity(source.get("actor_character_id"), "quote.actor_character_id"),
                    revision(source.get("native_revision"), "quote.native_revision"), date(source.get("date_raw"), "quote.date_raw")));
        }
        return new ConstructionQuote(new Candidate(identity(c.get("barony_title_id"), "barony_title_id"),
                identity(c.get("province_id"), "province_id"), integer(c.get("authored_monthly_income_delta_hundredths"), "authored_monthly_income_delta_hundredths"),
                integer(c.get("stock_gold_cost_raw"), "stock_gold_cost_raw"), integer(c.get("gold_before_raw"), "gold_before_raw")), frame, retain(raw));
    }
    public static M5Plan decodePlan(byte[] bytes) {
        return decodePlanProjection(parse(bytes));
    }
    static M5Plan decodePlanProjection(JsonNode raw) {
        object(raw, "M5 baseline plan");
        JsonNode consumed = raw.get("construction_receipt_consumed");
        return new M5Plan(absent(consumed) ? Optional.empty() : Optional.of(receipt(consumed)), retain(raw));
    }

    private static Receipt receipt(JsonNode raw) {
        object(raw, "receipt");
        JsonNode candidate = raw.get("candidate");
        if (candidate == null || candidate.isNull()) candidate = JSON.createObjectNode();
        object(candidate, "candidate");
        return new Receipt(status(raw.get("status")), truth(raw.get("postcondition_verified"), "postcondition_verified"),
                completion(raw.get("completion_status")), date(raw.get("completion_observed_date_raw"), "completion_observed_date_raw"),
                optionalText(raw.get("action_request_id"), "action_request_id"), identity(raw.get("actor_character_id"), "actor_character_id"),
                optionalText(raw.get("episode_run_id"), "episode_run_id"),
                new Candidate(identity(candidate.get("barony_title_id"), "barony_title_id"),
                        identity(candidate.get("province_id"), "province_id"),
                        integer(candidate.get("authored_monthly_income_delta_hundredths"), "authored_monthly_income_delta_hundredths"),
                        integer(candidate.get("stock_gold_cost_raw"), "stock_gold_cost_raw"),
                        integer(candidate.get("gold_before_raw"), "gold_before_raw")),
                integer(raw.get("pre_player_monthly_gold_income_raw"), "pre_player_monthly_gold_income_raw"),
                integer(raw.get("observed_player_monthly_gold_income_raw"), "observed_player_monthly_gold_income_raw"),
                date(raw.get("income_observed_date_raw"), "income_observed_date_raw"), date(raw.get("pre_date_raw"), "pre_date_raw"),
                province(raw.get("pre_province_income_observation")), province(raw.get("construction_province_income_observation")),
                start(raw.get("start_receipt")), cashOptional(raw.get("pre_cash_v2")), cashOptional(raw.get("post_cash_v2")),
                raw.has("observed_material_tuple") && !raw.get("observed_material_tuple").isNull()
                        ? Optional.of(retain(raw.get("observed_material_tuple"))) : Optional.empty(), retain(raw));
    }
    private static Optional<ProvinceObservation> province(JsonNode raw) {
        if (absent(raw)) return Optional.empty();
        object(raw, "province income observation");
        return Optional.of(new ProvinceObservation("observed".equals(optionalText(raw.get("status"), "province.status").orElse("")),
                identity(raw.get("barony_title_id"), "province.barony_title_id"), identity(raw.get("province_id"), "province.province_id"),
                integer(raw.get("native_province_monthly_income_raw"), "native_province_monthly_income_raw"), date(raw.get("date_raw"), "province.date_raw")));
    }
    private static Optional<StartReceipt> start(JsonNode raw) {
        if (absent(raw)) return Optional.empty();
        object(raw, "start_receipt");
        return Optional.of(new StartReceipt(status(raw.get("status")), truth(raw.get("postcondition_verified"), "start.postcondition_verified"),
                optionalText(raw.get("action_request_id"), "start.action_request_id"), integer(raw.get("post_player_gold_raw"), "post_player_gold_raw")));
    }
    private static Optional<CashPacket> cashOptional(JsonNode raw) { return absent(raw) ? Optional.empty() : Optional.of(cash(raw)); }

    private static CashPacket cash(JsonNode raw) {
        object(raw, "cash packet");
        // All direct budget, persisted receipt and completion entries share the native source contract.
        // This validates source semantics only; caller-owned current-snapshot binding remains separate.
        RawCashCodec.validateMonthlySourceContract(bytes(raw));
        String version = text(raw.get("game_version"), "game_version");
        String sha = text(raw.get("executable_sha256"), "executable_sha256");
        String expectedSha = version.equals("1.20.0.3") ? SHA3 : version.equals("1.20.0.4") ? SHA4 : "";
        if (expectedSha.isEmpty() || !sha.equalsIgnoreCase(expectedSha)) throw new ProjectionDomainRejection("native source does not match a frozen exact build");
        JsonNode marker = raw.get("monthly_income_semantics");
        StrictJson.object(marker, Set.of("version", "time_basis", "source_scope", "income_source", "expense_source", "military_expenses_included"));
        if (!text(marker.get("version"), "semantics.version").equals("ck3-" + version + "-native-income-minus-total-expenses-v2")
                || !text(marker.get("time_basis"), "semantics.time_basis").equals("month")
                || !text(marker.get("source_scope"), "semantics.source_scope").equals("played_character_personal_gold")
                || !text(marker.get("income_source"), "semantics.income_source").equals("native_character_monthly_gold_income")
                || !text(marker.get("expense_source"), "semantics.expense_source").equals("native_character_monthly_total_gold_expenses")
                || !truth(marker.get("military_expenses_included"), "military_expenses_included"))
            throw new ProjectionDomainRejection("war cash monthly flow lost its exact-build semantics");
        JsonNode ready = raw.get("readiness");
        object(ready, "cash readiness");
        Map<CashField, FixedObservation> values = new EnumMap<>(CashField.class);
        for (CashField field : CashField.values()) {
            if (field != CashField.TREASURY && !raw.has(field.wire())) throw invalid("war cash monthly flow scalar is absent");
            JsonNode fixed = raw.get(field.wire());
            Optional<BigInteger> value = Optional.empty();
            if (!absent(fixed)) {
                object(fixed, field.wire());
                value = Optional.of(StrictJson.integer(fixed.get("raw"), I64_MIN, I64_MAX));
                if (StrictJson.integer(fixed.get("scale"), SCALE, SCALE) != SCALE) throw invalid("wrong gold scale");
            }
            boolean observed = truth(ready.get(field.flag()), field.flag());
            Optional<String> reason = optionalText(raw.get(field.reason()), field.reason());
            if (field != CashField.TREASURY && (observed != value.isPresent()
                    || (value.isEmpty() && (reason.isEmpty() || !isFalse(ready.get(field.flag()))))
                    || (value.isPresent() && reason.isPresent()))) throw invalid("war cash monthly flow availability is inconsistent");
            values.put(field, new FixedObservation(value, observed, reason));
        }
        Optional<BigInteger> gross = values.get(CashField.GROSS).raw(), expense = values.get(CashField.EXPENSES).raw(), net = values.get(CashField.NET).raw();
        if (net.isPresent() && (gross.isEmpty() || expense.isEmpty()
                || !net.orElseThrow().equals(gross.orElseThrow().subtract(expense.orElseThrow()))))
            throw invalid("war cash monthly NET is not income minus total expenses");
        if (gross.isPresent() && expense.isPresent() && net.isEmpty()) {
            BigInteger difference = gross.orElseThrow().subtract(expense.orElseThrow());
            if (difference.compareTo(I64_MIN) >= 0 && difference.compareTo(I64_MAX) <= 0
                    || !values.get(CashField.NET).unavailableReason().orElse("").equals("war_cash_monthly_net_income_overflow"))
                throw invalid("war cash available monthly flow was replaced by unknown NET");
        }
        JsonNode military = raw.get("military_expenses");
        if (!absent(military)) object(military, "military_expenses");
        SourceFrame frame = new SourceFrame(version, sha, identity(raw.get("played_character_id"), "played_character_id"),
                revision(raw.get("snapshot_revision"), "snapshot_revision"), date(raw.get("date_raw"), "cash.date_raw"),
                optionalText(raw.get("queried_snapshot_id"), "queried_snapshot_id"), revision(raw.get("queried_revision"), "queried_revision"),
                revision(raw.get("queried_native_revision"), "queried_native_revision"));
        return new CashPacket(frame, truth(ready.get("same_frame_ready"), "same_frame_ready"), values,
                maintenance(absent(military) ? null : military.get("current"), ready, "current"),
                maintenance(absent(military) ? null : military.get("all_raised"), ready, "all_raised"),
                "xar.ck3.war-cash-current-resources.v1".equals(optionalText(raw.get("schema"), "cash.schema").orElse(""))
                        && truth(raw.get("read_only"), "cash.read_only"), retain(raw));
    }
    private static Optional<MilitaryObservation> maintenance(JsonNode row, JsonNode ready, String kind) {
        if (absent(row)) return Optional.empty();
        object(row, "military_expenses." + kind);
        String status = text(row.get("status"), "military.status");
        JsonNode flag = ready.get(kind + "_military_expenses_ready");
        if (status.equals("unavailable")) {
            String reason = text(row.get("unavailable_reason"), "military.unavailable_reason");
            if (!isFalse(flag) || reason.isEmpty()) throw invalid("military unavailable observation is malformed");
            return Optional.of(new MilitaryObservation(Optional.empty(), Optional.of(reason)));
        }
        JsonNode vector = row.get("resource_raw_native");
        if (!status.equals("available") || !truth(flag, "military readiness") || vector == null || !vector.isArray() || vector.size() != 10)
            throw invalid("military available observation is malformed");
        for (JsonNode amount : vector) StrictJson.integer(amount, I64_MIN, I64_MAX);
        BigInteger gold = StrictJson.integer(row.get("gold_raw"), I64_MIN, I64_MAX);
        if (!gold.equals(vector.get(0).bigIntegerValue())) throw invalid("military gold differs from native vector slot zero");
        return Optional.of(new MilitaryObservation(Optional.of(gold), Optional.empty()));
    }

    public static byte[] encodeOutcome(Outcome outcome) { return bytes(outcomeNode(outcome)); }
    public static byte[] encodeBudget(Budget budget) { return bytes(budgetNode(budget)); }
    public static byte[] encodePrepared(PreparedFields fields) {
        ObjectNode result = JSON.createObjectNode();
        result.set("pre_cash_v2", tree(fields.preCash().original())); result.set("construction_monthly_budget", budgetNode(fields.budget()));
        return bytes(result);
    }
    public static byte[] encodeCompleted(CompletedFields fields) {
        ObjectNode result = JSON.createObjectNode();
        result.set("receipt", tree(fields.receipt().original())); result.set("construction_economic_outcome", outcomeNode(fields.outcome()));
        return bytes(result);
    }
    public static byte[] encodeQueryOutcome(QueryOutcome query) {
        return bytes(queryNode(query));
    }
    private static ObjectNode queryNode(QueryOutcome query) {
        ObjectNode result = JSON.createObjectNode();
        result.put("schema", "xar.ck3.construction-cash-outcome-query.v1"); result.put("read_only", true);
        result.put("source", "ck3_query_war_cash_current_resources_private_v1");
        result.set("current_cash_scenarios", budgetNode(query.currentScenarios()));
        result.set("material_receipt", tree(query.completed().receipt().original()));
        result.set("construction_economic_outcome", outcomeNode(query.completed().outcome()));
        result.put("new_construction_spend_projected_raw", 0); result.put("formal_action_ready", false);
        return result;
    }
    public static byte[] encodeQuoteProjection(QuoteProjection projection) {
        ObjectNode quote = (ObjectNode) tree(projection.quote().original());
        if (projection.prepared().isPresent()) {
            PreparedFields fields = projection.prepared().orElseThrow();
            quote.set("pre_cash_v2", tree(fields.preCash().original()));
            quote.set("construction_monthly_budget", budgetNode(fields.budget()));
        }
        ObjectNode result = JSON.createObjectNode(); result.set("quote", quote); string(result, "deferred_reason", projection.deferredReason());
        return bytes(result);
    }
    public static byte[] encodeEnrichedPlan(PlanCashEnrichment enrichment) {
        ObjectNode result = (ObjectNode) tree(enrichment.plan().original());
        result.set("construction_cash_outcome", queryNode(enrichment.observation()));
        if (enrichment.replaceConsumedReceipt()) {
            result.set("construction_receipt_consumed", tree(enrichment.observation().completed().receipt().original()));
            result.set("construction_economic_outcome", outcomeNode(enrichment.observation().completed().outcome()));
        }
        return bytes(result);
    }
    static byte[] receiptWithPostCash(Receipt receipt, CashPacket post) {
        ObjectNode result = (ObjectNode) tree(receipt.original());
        result.set("post_cash_v2", tree(post.original()));
        return bytes(result);
    }

    private static ObjectNode outcomeNode(Outcome o) {
        Receipt r = o.receipt();
        ObjectNode result = JSON.createObjectNode();
        result.put("schema", "xar.ck3.construction-economic-outcome.v1"); result.put("phase", o.phase().wire());
        string(result, "action_request_id", r.actionRequestId()); number(result, "actor_character_id", r.actor());
        string(result, "episode_run_id", r.episodeRunId()); result.put("exact_ck3_build", o.exactBuild());
        result.put("material_completed", o.materialCompleted());
        number(result, "completion_observed_date_raw", o.materialCompleted() ? r.completionDate() : Optional.empty());
        number(result, "authored_direct_monthly_income_delta_hundredths", o.phase() == Phase.MISMATCHED ? Optional.empty() : r.candidate().authoredIncomeHundredths());
        result.put("requested_construction_verified", o.phase() != Phase.MISMATCHED && r.verified());
        if (r.observedMaterialTuple().isPresent()) result.set("observed_material_tuple", tree(r.observedMaterialTuple().orElseThrow()));
        else result.putNull("observed_material_tuple");
        ObjectNode gross = aggregate(o.gross()); gross.put("scale", SCALE); gross.put("time_basis", "month");
        gross.put("source_scope", "played_character_gross_income_aggregate"); number(gross, "observation_date_raw", r.incomeDate());
        result.set("player_gross_monthly_income_change", gross);
        ObjectNode province = aggregate(o.province()); province.putNull("scale"); province.put("source_scope", "province_income_aggregate");
        result.set("province_income_change", province); string(result, "next_observation_kind", o.nextObservationKind());
        result.set("observed_cash_change", cashChange(o.cash()));
        ObjectNode ready = result.putObject("readiness"); ready.put("material_completed", o.materialCompleted());
        ready.put("player_gross_aggregate_change_ready", o.gross().values().ready()); ready.put("province_aggregate_change_ready", o.province().values().ready());
        Change net = o.cash().monthlyChanges().get(CashField.NET); ready.put("player_net_monthly_change_ready", net != null && net.ready());
        ready.put("building_attribution_ready", false); ready.put("net_benefit_ready", false); ready.put("m5_realized_value_ready", false);
        result.put("formal_action_ready", false); return result;
    }
    private static ObjectNode aggregate(AggregateChange change) {
        ObjectNode result = change(change.values(), false); string(result, "unavailable_reason", change.unavailableReason()); return result;
    }
    private static ObjectNode change(Change value, boolean scale) {
        ObjectNode result = JSON.createObjectNode(); result.put("ready", value.ready()); if (scale) result.put("scale", SCALE);
        number(result, "before_raw", value.before()); number(result, "after_raw", value.after()); number(result, "delta_raw", value.delta()); return result;
    }
    private static ObjectNode cashChange(CashChange cash) {
        ObjectNode result = JSON.createObjectNode(); result.put("status", cash.observed() ? "observed" : "unavailable");
        string(result, "unavailable_reason", cash.unavailableReason());
        if (cash.frames().isEmpty()) result.putNull("source_frames"); else {
            ArrayNode frames = result.putArray("source_frames"); for (SourceFrame frame : cash.frames()) frames.add(frame(frame, true));
        }
        number(result, "elapsed_game_hours", cash.elapsedGameHours());
        ObjectNode monthly = result.putObject("monthly_rate_changes");
        cash.monthlyChanges().forEach((key, value) -> monthly.set(key.wire(), change(value, true)));
        if (cash.personalGoldChange().isPresent()) result.set("personal_gold_change", change(cash.personalGoldChange().orElseThrow(), true));
        else result.putNull("personal_gold_change");
        number(result, "verified_construction_gold_debit_raw", cash.verifiedDebit());
        number(result, "personal_gold_residual_after_verified_debit_raw", cash.residualAfterDebit());
        result.put("unallocated_other_transactions", true); result.put("building_attribution_ready", false);
        result.put("actual_roi_ready", false); result.put("future_war_cost_upper_ready", false); return result;
    }
    private static ObjectNode budgetNode(Budget budget) {
        ObjectNode result = JSON.createObjectNode(); BudgetPolicy p = budget.policy(); SourceFrame f = budget.cash().frame();
        result.put("schema", "xar.ck3.construction-monthly-budget.v1");
        result.put("status", budget.current().ready() && budget.allRaised().ready() ? "available" : "partial");
        result.put("projection_kind", "constant_current_state_cash_scenarios"); result.put("read_only", true);
        result.put("game_version", f.gameVersion()); result.put("executable_sha256", f.executableSha256().toUpperCase(java.util.Locale.ROOT));
        result.put("gold_scale", SCALE); result.put("time_basis", "month"); result.put("horizon_months", p.horizonMonths());
        result.put("construction_gold_cost_raw", p.constructionCost()); result.put("construction_cost_basis", "caller_supplied_gold_quote");
        result.put("reserve_gold_raw", p.reserve()); result.put("existing_commitment_gold_raw", p.commitments());
        result.set("source_frame", frame(f, false)); result.set("source_cash_resources", tree(budget.cash().original()));
        ObjectNode scenarios = result.putObject("scenarios"); scenarios.set("current", scenario(budget.current())); scenarios.set("all_raised", scenario(budget.allRaised()));
        ArrayNode assumptions = result.putArray("assumptions");
        assumptions.add("observed monthly income and nonmilitary expenses remain constant");
        assumptions.add("each scenario holds its observed military total constant for the explicit policy months");
        assumptions.add("all-raised replaces current military expense once across all wars");
        assumptions.add("only the explicit construction cost and existing commitments are deducted up front");
        assumptions.add("no future events, embark fees, new regiments, income gains or other transactions are predicted");
        result.put("future_war_cost_upper_ready", false); result.put("per_regiment_upkeep_ready", false);
        result.putNull("selected_step"); result.put("formal_action_ready", false);
        if (budget.fromQuery()) result.put("source", "ck3_query_war_cash_current_resources_private_v1"); return result;
    }
    private static ObjectNode frame(SourceFrame f, boolean build) {
        ObjectNode result = JSON.createObjectNode();
        if (build) { result.put("game_version", f.gameVersion()); result.put("executable_sha256", f.executableSha256()); }
        number(result, "played_character_id", f.actor()); number(result, "snapshot_revision", f.snapshotRevision()); number(result, "date_raw", f.date());
        string(result, "queried_snapshot_id", f.queriedSnapshotId()); number(result, "queried_revision", f.queriedRevision()); number(result, "queried_native_revision", f.queriedNativeRevision());
        return result;
    }
    private static ObjectNode scenario(Scenario s) {
        ObjectNode result = JSON.createObjectNode(); result.put("scenario_ready", s.ready()); number(result, "net_monthly_gold_raw", s.netRate());
        number(result, "cash_after_construction_and_commitments_raw", s.cashAfterUpfront()); number(result, "projected_ending_gold_raw", s.projectedEnd());
        number(result, "burn_reservation_raw", s.burnReservation()); number(result, "minimum_projected_gold_raw", s.minimum());
        if (s.floorReady().isPresent()) result.put("scenario_floor_ready", s.floorReady().orElseThrow()); else result.putNull("scenario_floor_ready");
        number(result, "maximum_one_off_spend_raw", s.maximumOneOffSpend());
        if (s.firstReserveBreach().isPresent()) result.put("first_month_reserve_breach", s.firstReserveBreach().orElseThrow()); else result.putNull("first_month_reserve_breach");
        ObjectNode missing = result.putObject("missing_inputs"); s.missingInputs().forEach((key, reason) -> missing.put(key.wire(), reason)); return result;
    }

    private static Optional<BigInteger> integer(JsonNode node, String field) {
        if (absent(node)) return Optional.empty();
        if (!node.isIntegralNumber()) throw invalid(field + " requires an integer token");
        return Optional.of(StrictJson.integer(node, I64_MIN, I64_MAX));
    }
    private static BigInteger nonnegative(JsonNode node, String field) {
        if (node == null || !node.isIntegralNumber() || node.bigIntegerValue().signum() < 0) throw invalid(field + " requires a nonnegative integer token");
        return node.bigIntegerValue();
    }
    private static Optional<BigInteger> identity(JsonNode node, String field) {
        return absent(node) ? Optional.empty() : Optional.of(StrictJson.integer(node, BigInteger.ONE, U32_MAX));
    }
    private static Optional<BigInteger> revision(JsonNode node, String field) {
        return absent(node) ? Optional.empty() : Optional.of(StrictJson.integer(node, BigInteger.ZERO, U64_MAX));
    }
    private static Optional<BigInteger> date(JsonNode node, String field) {
        return absent(node) ? Optional.empty() : Optional.of(BigInteger.valueOf(StrictJson.integer(node, Integer.MIN_VALUE, Integer.MAX_VALUE)));
    }
    private static boolean absent(JsonNode node) { return node == null || node.isNull(); }
    private static boolean truth(JsonNode node, String field) {
        if (absent(node)) return false;
        if (!node.isBoolean()) throw invalid(field + " requires a boolean token");
        return node.booleanValue();
    }
    private static boolean isFalse(JsonNode node) { return node != null && node.isBoolean() && !node.booleanValue(); }
    private static Optional<String> optionalText(JsonNode node, String field) { return absent(node) ? Optional.empty() : Optional.of(text(node, field)); }
    private static String text(JsonNode node, String field) {
        if (node == null || !node.isTextual()) throw invalid(field + " requires a string token");
        String value = node.textValue(); if (!value.isEmpty()) StrictJson.text(value); return value;
    }
    private static ReceiptStatus status(JsonNode node) {
        return switch (optionalText(node, "status").orElse("")) {
            case "applied" -> ReceiptStatus.APPLIED;
            case "observed_mismatched_construction" -> ReceiptStatus.MISMATCHED;
            case "restored_before_action" -> ReceiptStatus.RESTORED_BEFORE_ACTION;
            default -> ReceiptStatus.OTHER;
        };
    }
    private static CompletionStatus completion(JsonNode node) {
        return switch (optionalText(node, "completion_status").orElse("")) {
            case "completed" -> CompletionStatus.COMPLETED; case "in_progress" -> CompletionStatus.IN_PROGRESS; default -> CompletionStatus.OTHER;
        };
    }
    private static void object(JsonNode node, String field) { if (node == null || !node.isObject()) throw invalid(field + " must be an object"); }
    private static OriginalJson retain(JsonNode node) { return new OriginalJson(bytes(node)); }
    private static JsonNode tree(OriginalJson raw) { return parse(raw.bytes()); }
    private static JsonNode parse(byte[] raw) {
        if (raw == null || raw.length == 0 || raw.length > MAX_BYTES) throw invalid("construction JSON byte budget");
        try {
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
            JsonNode value = JSON.readTree(text);
            if (value == null) throw invalid("empty construction JSON"); return value;
        } catch (IOException failure) { throw new IllegalArgumentException("invalid construction JSON", failure); }
    }
    private static byte[] bytes(JsonNode node) {
        try {
            byte[] value = JSON.writeValueAsBytes(node);
            if (value.length > MAX_BYTES) throw invalid("construction JSON output byte budget"); return value;
        } catch (IOException failure) { throw new IllegalStateException("construction JSON encoding", failure); }
    }
    private static void number(ObjectNode target, String field, Optional<BigInteger> value) {
        if (value.isPresent()) target.put(field, value.orElseThrow()); else target.putNull(field);
    }
    private static void string(ObjectNode target, String field, Optional<String> value) {
        if (value.isPresent()) target.put(field, value.orElseThrow()); else target.putNull(field);
    }
    private static IllegalArgumentException invalid(String message) { return new IllegalArgumentException(message); }
}
