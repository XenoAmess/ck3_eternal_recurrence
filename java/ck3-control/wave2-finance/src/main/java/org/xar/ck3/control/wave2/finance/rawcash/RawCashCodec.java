package org.xar.ck3.control.wave2.finance.rawcash;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanCodec;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanModel;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanModel.ExpectedFrame;

/** Pure current-cash normalizer. Native source/frame evidence is checked here, never supplied as caller GREEN. */
public final class RawCashCodec {
    public static final String SCHEMA = "xar.ck3.war-cash-current-resources.v1";
    public static final String LOAN_KEY = "holy_order_loan_observation_v1";
    public static final String LOAN_SCHEMA = "xar.ck3.holy-order-loan-war-cash.v1";
    private static final BigInteger U64 = StrictJson.UINT64_MAX;
    private static final BigInteger I64_MIN = BigInteger.valueOf(Long.MIN_VALUE), I64_MAX = BigInteger.valueOf(Long.MAX_VALUE);
    private static final Map<String, String> BUILDS = Map.of(
            "1.19.0.6", "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
            "1.20.0.2", "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D",
            "1.20.0.3", "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6",
            HolyLoanCodec.VERSION, HolyLoanCodec.SHA256);
    private RawCashCodec() { }

    public enum Presence { MISSING, NULL, INVALID, VALUE }
    /** INVALID preserves a permissive legacy extension's type without turning it into an observed number. */
    public record Read<T>(Presence presence, T value) {
        public Read {
            Objects.requireNonNull(presence, "presence");
            if ((presence == Presence.VALUE) != (value != null)) { throw new IllegalArgumentException("read presence differs"); }
        }
        public boolean known() { return presence == Presence.VALUE; }
    }
    public record Frame(String gameVersion, String executableSha256, int playedCharacterId,
            BigInteger snapshotRevision, int dateRaw) { }
    public record FixedPoint(BigInteger raw, int scale) { }
    public record Readiness(Read<Boolean> sameFrameReady, Read<Boolean> currentTreasuryReady,
            Read<Boolean> monthlyGrossIncomeReady, Read<Boolean> monthlyTotalExpensesReady,
            Read<Boolean> monthlyNetIncomeReady, Read<Boolean> currentMilitaryExpensesReady,
            Read<Boolean> allRaisedMilitaryExpensesReady) { }
    public record Expense(boolean available, Read<String> resourceKind, Read<BigInteger> goldRaw,
            Read<BigInteger> treasuryRaw, Read<BigInteger> rawScale, List<Long> nativeResourceRaw) {
        public Expense { nativeResourceRaw = List.copyOf(nativeResourceRaw); }
    }
    public record Metrics(Read<FixedPoint> currentTreasury, Read<FixedPoint> monthlyGrossIncome,
            Read<FixedPoint> monthlyTotalExpenses, Read<FixedPoint> monthlyNetIncome,
            boolean trueNetSemantics, Readiness readiness, Expense currentMilitaryExpenses,
            Expense allRaisedMilitaryExpenses, Read<String> queriedSnapshotId,
            Read<BigInteger> queriedRevision, Read<BigInteger> queriedNativeRevision) { }
    public enum LoanStatus { AVAILABLE, PARTIAL, UNAVAILABLE }
    public enum BorrowEligibility { UNKNOWN, ALLOWED, DENIED }
    public record LoanObservation(LoanStatus status, Optional<HolyLoanModel.Observation> decisions,
            OptionalLong prospectivePrincipalRaw, BorrowEligibility borrowEligibility,
            Read<String> decisionCostsUnavailableReason, Read<String> principalUnavailableReason) {
        public LoanObservation {
            Objects.requireNonNull(status, "status"); Objects.requireNonNull(decisions, "decisions");
            Objects.requireNonNull(prospectivePrincipalRaw, "prospectivePrincipalRaw");
            Objects.requireNonNull(borrowEligibility, "borrowEligibility");
        }
        public boolean completeLoanTerms() { return false; }
        public boolean receivedFundsVerified() { return false; }
        public long fundingCreditRaw() { return 0; }
        public boolean submitPlanned() { return false; }
    }
    /** The constructor is private; only normalization of actual native/snapshot inputs creates this value. */
    public static final class NormalizedCurrentCash {
        private final Frame frame;
        private final List<BigInteger> activeWarIds;
        private final List<BigInteger> playerArmyIds;
        private final Metrics metrics;
        private final Read<LoanObservation> loanObservation;
        private final byte[] wire;
        private NormalizedCurrentCash(Frame frame, List<BigInteger> activeWarIds, List<BigInteger> playerArmyIds,
                Metrics metrics, Read<LoanObservation> loanObservation, byte[] wire) {
            this.frame = frame; this.activeWarIds = List.copyOf(activeWarIds); this.playerArmyIds = List.copyOf(playerArmyIds);
            this.metrics = metrics; this.loanObservation = loanObservation; this.wire = wire.clone();
        }
        public Frame frame() { return frame; }
        public List<BigInteger> activeWarIds() { return activeWarIds; }
        public List<BigInteger> playerArmyIds() { return playerArmyIds; }
        public Metrics metrics() { return metrics; }
        public Read<LoanObservation> loanObservation() { return loanObservation; }
        /** Existing SDK extension fields are retained; these bytes are a normalization, not the original native response. */
        public byte[] toJson() { return wire.clone(); }
    }

    /**
     * Validate the shared native balance/monthly-flow/military source contract without constructing a
     * snapshot or granting same-frame qualification. Loan/context extensions still require normalize.
     */
    public static void validateMonthlySourceContract(byte[] currentBytes) {
        monthlySource(object(StrictJson.parse(currentBytes)));
    }

    private record MonthlySource(Frame frame, List<BigInteger> activeWarIds, List<BigInteger> playerArmyIds,
            Expense currentMilitary, Expense allRaisedMilitary) { }

    private static MonthlySource monthlySource(JsonNode current) {
        require(SCHEMA.equals(text(current.get("schema"))), "war cash native schema malformed");
        String version = build(current);
        int played = (int) number(current.get("played_character_id"), 1, Integer.MAX_VALUE);
        BigInteger revision = unsigned(current.get("snapshot_revision"), 1);
        int date = (int) number(current.get("date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE);
        require(flag(current, "read_only", true) && flag(current, "advertised", false)
                && flag(current, "formal_action_ready", false), "war cash source does not match paused frame");
        require(Set.of("available", "partial", "unavailable").contains(text(current.get("status"))), "war cash status malformed");
        List<BigInteger> wars = ids(current.get("active_war_ids"), 1), armies = ids(current.get("player_army_ids"), 0);
        for (String key : List.of("current_treasury", "player_monthly_net_income")) {
            JsonNode fixed = current.get(key);
            if (!nil(fixed)) { fixed(fixed, false); }
        }
        JsonNode expenses = object(current.get("military_expenses"));
        Expense present = expense(expenses.get("current"), current, wars), raised = expense(expenses.get("all_raised"), current, wars);
        validateMonthlyFlow(current);
        return new MonthlySource(new Frame(version, BUILDS.get(version), played, revision, date), wars, armies, present, raised);
    }

    public static NormalizedCurrentCash normalize(byte[] currentBytes, byte[] snapshotBytes) {
        JsonNode current = object(StrictJson.parse(currentBytes)), snapshot = object(StrictJson.parse(snapshotBytes));
        MonthlySource source = monthlySource(current);
        Frame frame = source.frame();
        require(frame.gameVersion().equals(snapshotBuild(snapshot)), "war cash native source belongs to another build");
        JsonNode actor = object(snapshot.get("played_character"));
        require(integerEquals(actor.get("character_id"), BigInteger.valueOf(frame.playedCharacterId()))
                && integerEquals(snapshot.get("native_revision"), frame.snapshotRevision())
                && integerEquals(snapshot.get("date_raw"), BigInteger.valueOf(frame.dateRaw())),
                "war cash source does not match paused frame");
        if (current.has("current_raw_context_v1")) { rawContext(current, snapshot); }
        ObjectNode output = ((ObjectNode) current).deepCopy();
        if (current.has(LOAN_KEY)) { output.set(LOAN_KEY, normalizeLoan(current.get(LOAN_KEY), current, snapshot)); }
        JsonNode readiness = current.get("readiness");
        Readiness ready = new Readiness(readBoolean(part(readiness, "same_frame_ready")), readBoolean(part(readiness, "current_treasury_ready")),
                readBoolean(part(readiness, "monthly_gross_income_ready")), readBoolean(part(readiness, "monthly_total_expenses_ready")),
                readBoolean(part(readiness, "monthly_net_income_ready")), readBoolean(part(readiness, "current_military_expenses_ready")),
                readBoolean(part(readiness, "all_raised_military_expenses_ready")));
        Metrics metrics = new Metrics(readFixed(current.get("current_treasury")), readFixed(current.get("player_monthly_gross_income")),
                readFixed(current.get("player_monthly_total_expenses")), readFixed(current.get("player_monthly_net_income")),
                !nil(current.get("monthly_income_semantics")), ready, source.currentMilitary(), source.allRaisedMilitary(), readText(current.get("queried_snapshot_id")),
                readInteger(current.get("queried_revision")), readInteger(current.get("queried_native_revision")));
        Read<LoanObservation> loan = output.has(LOAN_KEY) ? new Read<>(Presence.VALUE, loanModel(output.get(LOAN_KEY)))
                : new Read<>(Presence.MISSING, null);
        return new NormalizedCurrentCash(frame, source.activeWarIds(), source.playerArmyIds(), metrics, loan, serialize(output));
    }

    /** Full original pure monthly-flow validation, including legacy unmarked packets and explicit signed overflow. */
    public static void validateMonthlyFlow(byte[] currentBytes) { validateMonthlyFlow(object(StrictJson.parse(currentBytes))); }

    /** Shared empty observation contract for the original optional financing consumer's refusal branches. */
    public static byte[] unavailableLoanObservation(String reason) {
        StrictJson.text(reason); return serialize(unavailableLoan(reason));
    }
    private static LoanObservation loanModel(JsonNode node) {
        try { return generatedLoanModel(node); }
        catch (ContractViolationException error) {
            throw new IllegalStateException("generated raw cash loan observation violates its contract", error);
        }
    }
    private static LoanObservation generatedLoanModel(JsonNode node) {
        Optional<HolyLoanModel.Observation> decisions = nil(node.get("decision_observation")) ? Optional.empty()
                : Optional.of(HolyLoanCodec.decodeObservation(serialize(node.get("decision_observation"))));
        OptionalLong principal = nil(node.get("principal_quote_raw")) ? OptionalLong.empty()
                : OptionalLong.of(number(node.get("principal_quote_raw"), Long.MIN_VALUE, Long.MAX_VALUE));
        JsonNode eligibility = node.get("borrow_eligible");
        BorrowEligibility eligible = nil(eligibility) ? BorrowEligibility.UNKNOWN : bool(eligibility) ? BorrowEligibility.ALLOWED : BorrowEligibility.DENIED;
        LoanStatus status = switch (text(node.get("status"))) {
            case "available" -> LoanStatus.AVAILABLE;
            case "partial" -> LoanStatus.PARTIAL;
            case "unavailable" -> LoanStatus.UNAVAILABLE;
            default -> throw new IllegalArgumentException("invalid normalized loan status");
        };
        return new LoanObservation(status, decisions, principal, eligible, readText(node.get("decision_costs_unavailable_reason")),
                readText(node.get("principal_unavailable_reason")));
    }
    private static void validateMonthlyFlow(JsonNode current) {
        JsonNode marker = current.get("monthly_income_semantics");
        if (nil(marker)) {
            require(!current.has("player_monthly_gross_income") && !current.has("player_monthly_total_expenses"), "monthly flow lacks semantics marker");
            return;
        }
        String version = text(current.get("game_version"));
        require((version.equals("1.20.0.3") || version.equals(HolyLoanCodec.VERSION))
                && marker.equals(monthlyMarker(version)), "monthly flow lost exact-build semantics");
        JsonNode ready = object(current.get("readiness"));
        List<BigInteger> values = new ArrayList<>();
        for (String stem : List.of("gross_income", "total_expenses", "net_income")) {
            String key = "player_monthly_" + stem, flagName = "monthly_" + stem + "_ready", reason = "monthly_" + stem + "_unavailable_reason";
            require(current.has(key), "monthly scalar absent"); JsonNode value = current.get(key);
            BigInteger raw = value.isNull() ? null : fixed(value, true).raw(); values.add(raw);
            require(flag(ready, flagName, raw != null)
                    && (raw == null ? part(current, reason) != null && part(current, reason).isTextual() : nil(current.get(reason))),
                    "monthly flow availability inconsistent");
        }
        BigInteger gross = values.get(0), expenses = values.get(1), net = values.get(2);
        require(net == null || gross != null && expenses != null && net.equals(gross.subtract(expenses)),
                "monthly NET is not income minus total expenses");
        if (gross != null && expenses != null && net == null) {
            BigInteger difference = gross.subtract(expenses);
            require((difference.compareTo(I64_MIN) < 0 || difference.compareTo(I64_MAX) > 0)
                    && "war_cash_monthly_net_income_overflow".equals(text(current.get("monthly_net_income_unavailable_reason"))),
                    "available monthly flow replaced by unknown NET");
        }
    }
    private static ObjectNode monthlyMarker(String version) {
        ObjectNode marker = StrictJson.object(); marker.put("version", "ck3-" + version + "-native-income-minus-total-expenses-v2");
        marker.put("time_basis", "month"); marker.put("source_scope", "played_character_personal_gold");
        marker.put("income_source", "native_character_monthly_gold_income"); marker.put("expense_source", "native_character_monthly_total_gold_expenses");
        marker.put("military_expenses_included", true); return marker;
    }
    private static Expense expense(JsonNode value, JsonNode current, List<BigInteger> wars) {
        JsonNode row = object(value); String status = text(row.get("status"));
        require(Set.of("available", "unavailable").contains(status)
                && integerEquals(row.get("owner_character_id"), current.get("played_character_id").bigIntegerValue())
                && current.get("played_character_id").bigIntegerValue().toString().equals(text(row.get("resource_id")))
                && ids(row.get("war_ids"), 1).equals(wars) && number(row.get("raw_scale"), 100000, 100000) == 100000
                && "month".equals(text(row.get("time_basis"))) && "actor_owned_military_once_across_all_wars".equals(text(row.get("source_scope")))
                && flag(row, "future_war_cost_upper_ready", false), "military expense lost actor-global semantics");
        List<Long> vector = List.of();
        if (status.equals("available")) {
            vector = vector(row.get("resource_raw_native"));
            require(integerEquals(row.get("gold_raw"), BigInteger.valueOf(vector.get(0)))
                    && integerEquals(row.get("treasury_raw"), BigInteger.valueOf(vector.get(6))), "military expense vector malformed");
        } else {
            require(nil(row.get("resource_raw_native")) && nil(row.get("gold_raw")) && row.has("unavailable_reason")
                    && row.get("unavailable_reason").isTextual(), "unavailable expenses replaced by cost");
        }
        return new Expense(status.equals("available"), readText(row.get("resource_kind")), readInteger(row.get("gold_raw")),
                readInteger(row.get("treasury_raw")), readInteger(row.get("raw_scale")), vector);
    }

    private static ObjectNode unavailableLoan(String reason) {
        ObjectNode node = StrictJson.object(); node.put("schema", LOAN_SCHEMA); node.put("status", "unavailable");
        node.put("read_only", true); node.put("advertised", false); node.put("formal_action_ready", false);
        for (String key : List.of("source_frame", "decision_costs", "decision_observation", "principal", "principal_quote_raw",
                "borrow_eligible", "existing_debt_principal_raw")) { node.putNull(key); }
        node.put("decision_costs_unavailable_reason", reason); node.put("principal_unavailable_reason", reason);
        node.put("complete_loan_terms", false); node.put("received_funds_verified", false); node.put("funding_credit_raw", 0);
        node.put("submit_planned", false); return node;
    }
    private static ObjectNode normalizeLoan(JsonNode value, JsonNode current, JsonNode snapshot) {
        if (!HolyLoanCodec.VERSION.equals(build(current)) || value == null || !value.isObject()
                || !LOAN_SCHEMA.equals(string(value.get("schema"))) || !flag(value, "read_only", true)
                || !flag(value, "advertised", false) || !flag(value, "formal_action_ready", false)
                || !flag(value, "complete_loan_terms", false) || !nil(value.get("existing_debt_principal_raw"))
                || !flag(value, "received_funds_verified", false) || !integerEquals(value.get("funding_credit_raw"), BigInteger.ZERO)
                || !flag(value, "submit_planned", false)) { return unavailableLoan("loan_scope_or_funding_assertion_unqualified"); }
        JsonNode f = value.get("source_frame"), ready = current.get("readiness");
        if (!flag(snapshot, "paused", true) || !flag(snapshot, "map_ready", true) || !isObject(f) || !isObject(ready)
                || !flag(ready, "same_frame_ready", true) || !flag(f, "full_snapshot_owner_retained", true)
                || !flag(f, "same_frame_ready", true) || !inRange(f.get("snapshot_revision"), BigInteger.ONE, U64)
                || !sameInteger(f.get("snapshot_revision"), current.get("snapshot_revision"))
                || !inRange(f.get("played_character_id"), BigInteger.ONE, BigInteger.valueOf(Integer.MAX_VALUE))
                || !sameInteger(f.get("played_character_id"), current.get("played_character_id"))
                || !inRange(f.get("date_raw"), BigInteger.ZERO, BigInteger.valueOf(Integer.MAX_VALUE))
                || !sameInteger(f.get("date_raw"), current.get("date_raw"))
                || !inRange(f.get("local_player_id"), BigInteger.valueOf(Integer.MIN_VALUE), BigInteger.valueOf(Integer.MAX_VALUE))
                || !inRange(f.get("ticket_sequence"), BigInteger.ONE, U64)) { return unavailableLoan("loan_native_source_frame_unqualified"); }
        JsonNode stamp = f.get("execution_stamp");
        if (!isObject(stamp) || !flag(stamp, "paused", true) || !sameInteger(stamp.get("date_raw"), f.get("date_raw"))) {
            return unavailableLoan("loan_execution_stamp_unqualified");
        }
        for (String key : List.of("pump_epoch", "thread_id", "rng_wrapper", "rng_state", "rng_owner_thread_id",
                "tls_initialized_flag_address", "tls_initialized", "tls_context", "tls_main_thread_marker", "jomini_state", "game_state")) {
            BigInteger minimum = key.equals("pump_epoch") || key.equals("thread_id") ? BigInteger.ONE : BigInteger.ZERO;
            BigInteger maximum = key.equals("tls_initialized") || key.equals("tls_main_thread_marker") ? BigInteger.valueOf(255)
                    : key.equals("thread_id") || key.equals("rng_owner_thread_id") ? BigInteger.ONE.shiftLeft(32).subtract(BigInteger.ONE) : U64;
            if (!inRange(stamp.get(key), minimum, maximum)) { return unavailableLoan("loan_execution_stamp_unqualified"); }
        }
        ObjectNode result = unavailableLoan("not_sampled"); result.set("source_frame", f.deepCopy());
        result.put("decision_costs_unavailable_reason", nonempty(value.get("decision_costs_unavailable_reason"), "decision_costs_unavailable"));
        JsonNode decisions = value.get("decision_costs"); boolean costsReady = false;
        if (!nil(decisions)) {
            HolyLoanModel.Observation observation = null;
            try {
                observation = HolyLoanCodec.project(SdkProjectionJson.encode(decisions), new ExpectedFrame(f.get("played_character_id").intValue(),
                        f.get("date_raw").intValue(), stamp.get("pump_epoch").bigIntegerValue()));
            } catch (ContractViolationException error) {
                result.put("decision_costs_unavailable_reason", "loan_decision_child_malformed_or_mismatched");
            }
            if (observation != null) {
                JsonNode projected = generatedDecisionObservation(observation);
                result.set("decision_costs", decisions.deepCopy()); result.set("decision_observation", projected);
                result.set("decision_costs_unavailable_reason", projected.get("unavailable_reason"));
                result.set("borrow_eligible", projected.get("borrow_decision").get("native_gates_allow_decision"));
                costsReady = observation.availability() instanceof HolyLoanModel.Available;
            }
        }
        JsonNode principal = value.get("principal");
        result.put("principal_unavailable_reason", nonempty(part(principal, "unavailable_reason"), "principal_unavailable"));
        boolean quoteReady = isObject(principal) && "available".equals(string(principal.get("status")))
                && "holy_order_gold_value".equals(string(principal.get("value_key")))
                && integerEquals(principal.get("raw_scale"), BigInteger.valueOf(100000))
                && flag(principal, "owned_temporaries_released", true) && nil(principal.get("unavailable_reason"))
                && inRange(principal.get("prospective_principal_raw"), I64_MIN, I64_MAX);
        if (quoteReady) {
            result.set("principal", principal.deepCopy()); result.set("principal_quote_raw", principal.get("prospective_principal_raw"));
            result.putNull("principal_unavailable_reason");
        }
        result.put("status", costsReady && quoteReady ? "available" : costsReady || quoteReady ? "partial" : "unavailable"); return result;
    }

    private static void rawContext(JsonNode current, JsonNode snapshot) {
        JsonNode v = StrictJson.object(current.get("current_raw_context_v1"), Set.of("schema_version", "character_full_id", "character",
                "snapshot_revision", "date_raw", "actor_identity_stable", "same_frame_ready", "admission_ready", "observation_kind",
                "attribution_scope", "maintenance_attribution", "values", "unavailable_reason"));
        require(HolyLoanCodec.VERSION.equals(build(current)) && number(v.get("schema_version"), 0, 4294967295L) == 1
                && "paused_current_raw_context".equals(text(v.get("observation_kind")))
                && "current_raw_context_only".equals(text(v.get("attribution_scope")))
                && "unclosed".equals(text(v.get("maintenance_attribution"))), "raw context scope/build relabeled");
        BigInteger character = unsigned(v.get("character"), 1); require(character.signum() > 0, "raw context character absent");
        number(v.get("character_full_id"), 1, Integer.MAX_VALUE); unsigned(v.get("snapshot_revision"), 0);
        number(v.get("date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE);
        JsonNode actor = object(snapshot.get("played_character")), ready = object(current.get("readiness"));
        require(sameInteger(v.get("character_full_id"), current.get("played_character_id"))
                && sameInteger(v.get("character_full_id"), actor.get("character_id")) && flag(v, "actor_identity_stable", true)
                && sameInteger(v.get("snapshot_revision"), current.get("snapshot_revision"))
                && sameInteger(v.get("snapshot_revision"), snapshot.get("native_revision"))
                && sameInteger(v.get("date_raw"), current.get("date_raw")) && sameInteger(v.get("date_raw"), snapshot.get("date_raw")),
                "raw context actor/revision/date differs");
        boolean sameFrame = bool(v.get("same_frame_ready")); require(bool(ready.get("same_frame_ready")) == sameFrame, "raw context readiness differs");
        JsonNode raw = StrictJson.object(v.get("values"), Set.of("context_identity_before", "context_identity_after", "value_2c0", "value_2c8",
                "value_28", "value_30", "capture_complete", "context_stable", "failed_reads"));
        BigInteger before = optionalUnsigned(raw.get("context_identity_before")), after = optionalUnsigned(raw.get("context_identity_after"));
        boolean stable = before != null && before.signum() != 0 && before.equals(after);
        require(bool(raw.get("context_stable")) == stable, "generic raw context identity stability inconsistent");
        boolean allValues = true;
        for (String key : List.of("value_2c0", "value_2c8", "value_28", "value_30")) {
            JsonNode value = raw.get(key); if (value.isNull()) { allValues = false; } else { number(value, Long.MIN_VALUE, Long.MAX_VALUE); }
            require(before != null && before.signum() != 0 || value.isNull(), "generic values without input context identity");
        }
        long failed = number(raw.get("failed_reads"), 0, 4294967295L);
        boolean complete = stable && failed == 0 && allValues;
        require(bool(raw.get("capture_complete")) == complete, "generic context completeness inconsistent");
        boolean frame = sameFrame && flag(snapshot, "paused", true) && flag(snapshot, "map_ready", true) && flag(actor, "alive", true);
        boolean aligned = before != null && before.signum() != 0 && before.mod(BigInteger.valueOf(8)).signum() == 0
                && before.compareTo(U64.subtract(BigInteger.valueOf(0x2cf))) <= 0;
        String reason = !frame ? "war_cash_current_raw_context_frame_unqualified" : !complete ? "war_cash_current_raw_context_incomplete"
                : !aligned ? "war_cash_current_raw_context_unaligned_or_overflow" : null;
        require(bool(v.get("admission_ready")) == (frame && complete && aligned)
                && (reason == null ? v.get("unavailable_reason").isNull() : reason.equals(string(v.get("unavailable_reason")))),
                "raw context admission/reason disagrees with evidence");
    }

    private static String build(JsonNode node) {
        String version = text(node.get("game_version")), sha = text(node.get("executable_sha256"));
        require(BUILDS.containsKey(version) && BUILDS.get(version).equalsIgnoreCase(sha), "source lacks frozen exact build"); return version;
    }
    private static String snapshotBuild(JsonNode snapshot) {
        JsonNode hello = part(part(snapshot, "diagnostics"), "hello"); if (!isObject(hello)) { return "1.19.0.6"; }
        ObjectNode source = StrictJson.object();
        source.set("game_version", hello.has("expected_ck3_version") ? hello.get("expected_ck3_version") : hello.get("game_version"));
        source.set("executable_sha256", hello.has("expected_ck3_sha256") ? hello.get("expected_ck3_sha256") : hello.get("executable_sha256"));
        return build(source);
    }
    private static FixedPoint fixed(JsonNode value, boolean signed64) {
        JsonNode node = object(value); BigInteger raw = signed64 ? StrictJson.integer(node.get("raw"), I64_MIN, I64_MAX) : integer(node.get("raw"));
        number(node.get("scale"), 100000, 100000); return new FixedPoint(raw, 100000);
    }
    private static List<BigInteger> ids(JsonNode node, int minimum) {
        require(node != null && node.isArray(), "ID array required"); List<BigInteger> values = new ArrayList<>(); Set<BigInteger> unique = new HashSet<>();
        for (JsonNode value : node) { BigInteger id = integer(value); require(id.compareTo(BigInteger.valueOf(minimum)) >= 0 && unique.add(id), "duplicate or invalid ID"); values.add(id); }
        return List.copyOf(values);
    }
    private static List<Long> vector(JsonNode node) {
        require(node != null && node.isArray() && node.size() == 10, "all ten signed resource slots required");
        List<Long> result = new ArrayList<>(); for (JsonNode value : node) { result.add(number(value, Long.MIN_VALUE, Long.MAX_VALUE)); } return List.copyOf(result);
    }
    private static Read<FixedPoint> readFixed(JsonNode value) {
        if (value == null) { return new Read<>(Presence.MISSING, null); } if (value.isNull()) { return new Read<>(Presence.NULL, null); }
        try { return new Read<>(Presence.VALUE, fixed(value, false)); } catch (ContractViolationException error) { return new Read<>(Presence.INVALID, null); }
    }
    private static Read<BigInteger> readInteger(JsonNode value) {
        return value == null ? new Read<>(Presence.MISSING, null) : value.isNull() ? new Read<>(Presence.NULL, null)
                : value.isIntegralNumber() ? new Read<>(Presence.VALUE, value.bigIntegerValue()) : new Read<>(Presence.INVALID, null);
    }
    private static Read<Boolean> readBoolean(JsonNode value) {
        return value == null ? new Read<>(Presence.MISSING, null) : value.isNull() ? new Read<>(Presence.NULL, null)
                : value.isBoolean() ? new Read<>(Presence.VALUE, value.booleanValue()) : new Read<>(Presence.INVALID, null);
    }
    private static Read<String> readText(JsonNode value) {
        return value == null ? new Read<>(Presence.MISSING, null) : value.isNull() ? new Read<>(Presence.NULL, null)
                : value.isTextual() ? new Read<>(Presence.VALUE, value.textValue()) : new Read<>(Presence.INVALID, null);
    }
    /** Encoding generated state is an implementation failure, never an input refusal. */
    private static byte[] serialize(JsonNode node) {
        try { return SdkProjectionJson.encode(node); }
        catch (ContractViolationException error) {
            throw new IllegalStateException("generated raw cash output violates its wire contract", error);
        }
    }
    private static JsonNode generatedDecisionObservation(HolyLoanModel.Observation observation) {
        try { return StrictJson.parse(HolyLoanCodec.encode(observation)); }
        catch (ContractViolationException error) {
            throw new IllegalStateException("generated holy loan decision observation violates its contract", error);
        }
    }
    private static JsonNode object(JsonNode node) { require(isObject(node), "cash object required"); return node; }
    private static boolean isObject(JsonNode node) { return node != null && node.isObject(); }
    private static JsonNode part(JsonNode node, String key) { return isObject(node) ? node.get(key) : null; }
    private static String text(JsonNode node) { return StrictJson.text(node); }
    private static String string(JsonNode node) { return node != null && node.isTextual() ? node.textValue() : null; }
    private static String nonempty(JsonNode node, String fallback) { String result = string(node); return result != null && !result.isEmpty() ? result : fallback; }
    private static boolean bool(JsonNode node) { require(node != null && node.isBoolean(), "actual boolean token required"); return node.booleanValue(); }
    private static boolean flag(JsonNode node, String key, boolean expected) { JsonNode value = part(node, key); return value != null && value.isBoolean() && value.booleanValue() == expected; }
    private static boolean nil(JsonNode node) { return node == null || node.isNull(); }
    private static BigInteger integer(JsonNode node) { require(node != null && node.isIntegralNumber(), "exact integer token required"); return node.bigIntegerValue(); }
    private static long number(JsonNode node, long minimum, long maximum) { return StrictJson.integer(node, minimum, maximum); }
    private static BigInteger unsigned(JsonNode node, int minimum) { return StrictJson.integer(node, BigInteger.valueOf(minimum), U64); }
    private static BigInteger optionalUnsigned(JsonNode node) { return node.isNull() ? null : unsigned(node, 0); }
    private static boolean inRange(JsonNode node, BigInteger minimum, BigInteger maximum) {
        return node != null && node.isIntegralNumber() && node.bigIntegerValue().compareTo(minimum) >= 0 && node.bigIntegerValue().compareTo(maximum) <= 0;
    }
    private static boolean integerEquals(JsonNode node, BigInteger value) { return node != null && node.isIntegralNumber() && node.bigIntegerValue().equals(value); }
    private static boolean sameInteger(JsonNode left, JsonNode right) { return left != null && right != null && left.isIntegralNumber() && right.isIntegralNumber() && left.bigIntegerValue().equals(right.bigIntegerValue()); }
    private static void require(boolean condition, String message) { StrictJson.require(condition, message); }
}
