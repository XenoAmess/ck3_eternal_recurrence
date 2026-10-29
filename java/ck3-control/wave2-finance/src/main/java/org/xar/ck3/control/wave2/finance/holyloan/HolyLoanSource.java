package org.xar.ck3.control.wave2.finance.holyloan;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanModel.Definition;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanModel.ObservedDecision;
import org.xar.ck3.control.wave2.finance.holyloan.LoanFinancingCodec.PlanningFrame;

/** Sole v2 compiled-source quote boundary. It grants neither a loan submission nor spendable funds. */
public final class HolyLoanSource {
    public static final String NATIVE_SCHEMA = "ck3_12004_holy_order_loan_source_v2";
    public static final String SCHEMA = "xar.holy-order-loan-source.v2";
    public static final String OPERATION = "query-player-holy-order-loan-source-v2";
    private static final BigInteger U32 = new BigInteger("4294967295");
    private static final Set<String> FIELDS = Set.of("schema", "game_version", "executable_sha256", "read_only", "scope",
            "available", "unavailable_reason", "capture_epoch", "native_revision", "date_raw", "actor_character_id",
            "borrow_decision", "repay_decision", "prospective_principal_raw", "debt_copy", "definition_fence", "raw_scale",
            "resource_slot_count", "decision_cost_scope", "complete_loan_terms", "submission_qualified", "received_funds_verified", "funding_credit_raw");
    private static final Set<String> FRAME_FIELDS = Set.of("snapshot_id", "revision", "native_revision", "date_raw",
            "actor_character_id", "episode_run_id", "bridge_pid", "connection_generation");
    private HolyLoanSource() { }

    public enum Refusal { WRONG_EXACT_BUILD, FRAME_DRIFT }
    public enum Failure {
        NOT_READ, EXACT_BUILD, REQUEST_OR_READ_PORTS, APPLICATION_MAIN, PAUSED_FRAME, DEFINITION_FENCE,
        NATIVE_SOURCE_UNAVAILABLE, SOURCE_FRAME_MISMATCH, NATIVE_TEMPORARIES_UNVERIFIED, DEBT_SHAPE,
        DEFINITION_OR_IDENTIFIER_CHANGED, FRAME_OR_SOURCE_CHANGED, EXCEPTION;
        public String wire() { return name().toLowerCase(Locale.ROOT); }
        static Failure exact(String wire) {
            for (Failure value : values()) { if (value.wire().equals(wire)) { return value; } }
            throw new IllegalArgumentException("unrecognized native loan source failure");
        }
    }
    public enum DebtFailure {
        NOT_READ, VARIABLE_IDENTIFIER_UNAVAILABLE, BORROWER_HELD_CONTEXT_UNAVAILABLE,
        BORROWER_SCALAR_ROWS_UNAVAILABLE, LENDER_HELD_SCALAR_CONTEXT_UNAVAILABLE, DEBT_NATIVE_READ_EXCEPTION;
        public String wire() { return name().toLowerCase(Locale.ROOT); }
        static DebtFailure exact(String wire) {
            for (DebtFailure value : values()) { if (value.wire().equals(wire)) { return value; } }
            throw new IllegalArgumentException("unrecognized copied debt source failure");
        }
    }
    public enum NextRead { NATIVE_DECISION_GATES_REFUSED, POSITIVE_NATIVE_PRINCIPAL_UNAVAILABLE, INSPECT_ACTUAL_NATIVE_OFFER_REQUIRED }
    public enum CopyComparison { FRAME_CHANGED, DEFINITIONS_OR_IDENTIFIER_EPOCH_CHANGED, QUOTE_CONTENT_CHANGED, SAME_CAPTURED_CONTENT_USE_CURRENT }
    public enum MissingEvidence {
        LENDER_MEMBERSHIP_AND_VARIABLE_EXPIRY, LOADED_SCRIPT_PROVENANCE, ACTUAL_EVENT_PARTIES_AND_OPTIONS,
        UNIQUE_FINAL_NATIVE_SUBMISSION, DEBT_AND_ATTRIBUTABLE_WALLET_AFTERSTATE, EFFECT_TRANSFER_AND_REPAYMENT_OUTLAY,
        ACTUAL_EVENT_PRINCIPAL_REEVALUATION
    }
    public enum Kind {
        FIXED(1), CHARACTER(4);
        private final int tag;
        Kind(int tag) { this.tag = tag; }
        public int tag() { return tag; }
        static Kind exact(int tag) {
            for (Kind kind : values()) { if (kind.tag == tag) { return kind; } }
            throw new IllegalArgumentException("unqualified native debt scalar kind");
        }
    }
    public enum BorrowerScalar { LOAN_AMOUNT_OWED, LOAN_HOLDER, YEARS_SINCE_LOAN, ORIGINAL_LOAN_HOLDER, ORIGINAL_LENDER }
    public enum ClockKind { NEGATIVE_EXPIRY, TIMED_COUNTER }
    /**
     * Source-equivalent 3727530 counter result. A timed result of -1 is distinct
     * from the native negative-expiry sentinel. Neither result says a debt is
     * active, that cleanup has run, or that a calendar/repayment date is known.
     */
    public record ScalarClock(ClockKind kind, int expiryRaw, int currentClockRaw, int remainingRaw) {
        public ScalarClock {
            Objects.requireNonNull(kind, "kind");
            require((kind == ClockKind.TIMED_COUNTER) == (expiryRaw >= 0), "native expiry sign differs");
            // SUB is native low32 signed arithmetic; do not widen or saturate.
            require(remainingRaw == (expiryRaw >= 0 ? expiryRaw - currentClockRaw : -1), "native scalar remaining differs");
        }
    }
    public record Pointer(BigInteger value) {
        public Pointer { unsigned(value, BigInteger.ONE, StrictJson.UINT64_MAX); require(value.mod(BigInteger.valueOf(8)).signum() == 0, "aligned pointer required"); }
    }
    /** expiry/clock are copied raw values, with no active/expired or repayment-date inference. */
    public record Scalar(Kind kind, long payloadRaw, int expiryRaw) {
        public Scalar {
            Objects.requireNonNull(kind, "kind");
            if (kind == Kind.CHARACTER) { require(payloadRaw >= 0 && payloadRaw < 0xffff_ffffL, "exact full CharacterID payload required"); }
        }
        public ScalarClock clockAt(int currentClockRaw) {
            return new ScalarClock(expiryRaw >= 0 ? ClockKind.TIMED_COUNTER : ClockKind.NEGATIVE_EXPIRY,
                    expiryRaw, currentClockRaw, expiryRaw >= 0 ? expiryRaw - currentClockRaw : -1);
        }
    }
    public record BorrowerRows(Optional<Scalar> loanAmountOwed, Optional<Scalar> loanHolder, Optional<Scalar> yearsSinceLoan,
            Optional<Scalar> originalLoanHolder, Optional<Scalar> originalLender) {
        public BorrowerRows {
            rowKind(loanAmountOwed, Kind.FIXED); rowKind(loanHolder, Kind.CHARACTER); rowKind(yearsSinceLoan, Kind.FIXED);
            rowKind(originalLoanHolder, Kind.CHARACTER); rowKind(originalLender, Kind.CHARACTER);
        }
    }
    public sealed interface DebtCopy permits CopiedDebt, DebtUnavailable { }
    public record DebtUnavailable(DebtFailure reason) implements DebtCopy {
        public DebtUnavailable { Objects.requireNonNull(reason, "reason"); }
    }
    public record CopiedDebt(Pointer borrowerContext, int borrowerClockRaw, BorrowerRows borrower,
            Optional<Boolean> holderResolved, Optional<Pointer> lenderContext, OptionalInt lenderClockRaw,
            Optional<Scalar> lenderYearsRow) implements DebtCopy {
        public CopiedDebt {
            Objects.requireNonNull(borrowerContext, "borrowerContext"); Objects.requireNonNull(borrower, "borrower");
            Objects.requireNonNull(holderResolved, "holderResolved"); Objects.requireNonNull(lenderContext, "lenderContext");
            Objects.requireNonNull(lenderClockRaw, "lenderClockRaw"); rowKind(lenderYearsRow, Kind.FIXED);
            if (borrower.loanHolder().isEmpty()) {
                require(holderResolved.isEmpty() && lenderContext.isEmpty() && lenderClockRaw.isEmpty() && lenderYearsRow.isEmpty(), "absent holder cannot carry lender evidence");
            } else {
                require(holderResolved.isPresent(), "actual full holder resolution status required");
                require(lenderContext.isPresent() == holderResolved.orElseThrow()
                        && lenderClockRaw.isPresent() == lenderContext.isPresent(), "holder resolution/context mismatch");
                require(holderResolved.orElseThrow() || lenderYearsRow.isEmpty(), "unresolved lender has no copied years");
            }
        }
        public boolean expirySemanticsQualified() { return false; }
        public Optional<Boolean> lenderMembership() { return Optional.empty(); }
        /** Uses only this copied borrower's own clock. Missing rows stay absent. */
        public Optional<ScalarClock> borrowerClock(BorrowerScalar row) {
            Objects.requireNonNull(row, "row");
            Optional<Scalar> value = switch (row) {
                case LOAN_AMOUNT_OWED -> borrower.loanAmountOwed();
                case LOAN_HOLDER -> borrower.loanHolder();
                case YEARS_SINCE_LOAN -> borrower.yearsSinceLoan();
                case ORIGINAL_LOAN_HOLDER -> borrower.originalLoanHolder();
                case ORIGINAL_LENDER -> borrower.originalLender();
            };
            return value.map(scalar -> scalar.clockAt(borrowerClockRaw));
        }
        /** A lender row uses its independently copied lender clock, never the borrower's. */
        public Optional<ScalarClock> lenderYearsClock() {
            return lenderYearsRow.map(scalar -> scalar.clockAt(lenderClockRaw.orElseThrow()));
        }
    }
    public record DefinitionFence(List<Pointer> pointers, int variableEpoch) {
        public DefinitionFence { pointers = List.copyOf(pointers); require(pointers.size() == 8 && variableEpoch >= 0 && variableEpoch <= 255, "all eight definition/identifier pointers required"); }
    }
    public sealed interface Result permits Quote, Unavailable, Refused { }
    public record Refused(Refusal reason) implements Result { public Refused { Objects.requireNonNull(reason, "reason"); } }
    public record Unavailable(Failure reason) implements Result {
        public Unavailable { Objects.requireNonNull(reason, "reason"); }
    }
    public static final class Quote implements Result {
        private final PlanningFrame frame;
        private final BigInteger captureEpoch;
        private final ObservedDecision borrow, repay;
        private final long prospectivePrincipalRaw;
        private final DebtCopy debt;
        private final DefinitionFence fence;
        private final byte[] persisted;
        private Quote(PlanningFrame frame, BigInteger epoch, ObservedDecision borrow, ObservedDecision repay,
                long principal, DebtCopy debt, DefinitionFence fence, byte[] persisted) {
            this.frame = frame; this.captureEpoch = epoch; this.borrow = borrow; this.repay = repay;
            this.prospectivePrincipalRaw = principal; this.debt = debt; this.fence = fence; this.persisted = persisted.clone();
        }
        public PlanningFrame frame() { return frame; }
        public BigInteger captureEpoch() { return captureEpoch; }
        public ObservedDecision borrowDecision() { return borrow; }
        public ObservedDecision repayDecision() { return repay; }
        public long prospectivePrincipalRaw() { return prospectivePrincipalRaw; }
        public DebtCopy debt() { return debt; }
        public DefinitionFence definitionFence() { return fence; }
        public NextRead nextRead() {
            if (!borrow.nativeGatesAllowDecision()) { return NextRead.NATIVE_DECISION_GATES_REFUSED; }
            return prospectivePrincipalRaw > 0 ? NextRead.INSPECT_ACTUAL_NATIVE_OFFER_REQUIRED : NextRead.POSITIVE_NATIVE_PRINCIPAL_UNAVAILABLE;
        }
        public List<MissingEvidence> missingEvidence() { return List.of(MissingEvidence.values()); }
        public boolean completeLoanTerms() { return false; }
        public boolean submissionQualified() { return false; }
        public boolean receivedFundsVerified() { return false; }
        public long fundingCreditRaw() { return 0; }
        public byte[] toJson() { return persisted.clone(); }
    }

    /** Root must verify the exact native producer/read origin; JSON validation grants no read permission. */
    public static Result projectNative(byte[] bytes, PlanningFrame expected, BigInteger captureEpoch) {
        validateFrame(expected, captureEpoch);
        ObjectNode node = StrictJson.object(StrictJson.parse(bytes), FIELDS);
        require(NATIVE_SCHEMA.equals(StrictJson.text(node.get("schema"))), "exact loan source v2 schema required");
        if (!HolyLoanCodec.VERSION.equals(StrictJson.text(node.get("game_version")))
                || !HolyLoanCodec.SHA256.equalsIgnoreCase(StrictJson.text(node.get("executable_sha256")))) { return new Refused(Refusal.WRONG_EXACT_BUILD); }
        StrictJson.trueValue(node.get("read_only"));
        require("native_decision_principal_and_copied_debt_only".equals(StrictJson.text(node.get("scope"))), "loan source scope differs");
        require("declared_only_effect_transfers_unquoted".equals(StrictJson.text(node.get("decision_cost_scope"))), "declared costs cannot impersonate effect outlays");
        StrictJson.integer(node.get("raw_scale"), 100000, 100000); StrictJson.integer(node.get("resource_slot_count"), 10, 10);
        for (String key : List.of("complete_loan_terms", "submission_qualified", "received_funds_verified")) { falseValue(node.get(key)); }
        StrictJson.integer(node.get("funding_credit_raw"), 0, 0);
        if (!decimal(node.get("capture_epoch"), BigInteger.ONE).equals(captureEpoch)
                || !decimal(node.get("native_revision"), BigInteger.ONE).equals(expected.nativeRevision())) { return new Refused(Refusal.FRAME_DRIFT); }
        if (!bool(node.get("available"))) {
            for (String key : List.of("date_raw", "actor_character_id", "borrow_decision", "repay_decision", "prospective_principal_raw", "debt_copy", "definition_fence"))
                require(node.get(key).isNull(), "unavailable source cannot retain " + key);
            return new Unavailable(Failure.exact(StrictJson.text(node.get("unavailable_reason"))));
        }
        require(node.get("unavailable_reason").isNull(), "available source carries failure");
        BigInteger actor = StrictJson.integer(node.get("actor_character_id"), BigInteger.ZERO, U32.subtract(BigInteger.ONE));
        BigInteger date = StrictJson.integer(node.get("date_raw"), BigInteger.ZERO, BigInteger.valueOf(Integer.MAX_VALUE));
        if (!actor.equals(expected.actorCharacterId()) || !date.equals(expected.dateRaw())) { return new Refused(Refusal.FRAME_DRIFT); }
        var borrow = gate(node.get("borrow_decision"), Definition.BORROW); var repay = gate(node.get("repay_decision"), Definition.REPAY);
        long principal = StrictJson.integer(node.get("prospective_principal_raw"), Long.MIN_VALUE, Long.MAX_VALUE);
        DebtCopy debt = debt(node.get("debt_copy"));
        ObjectNode fence = StrictJson.object(node.get("definition_fence"), Set.of("pointers", "variable_epoch"));
        JsonNode pointers = fence.get("pointers"); require(pointers.isArray() && pointers.size() == 8, "complete definition fence required");
        List<Pointer> parsedPointers = new ArrayList<>(); for (JsonNode pointer : pointers) { parsedPointers.add(pointer(pointer)); }
        DefinitionFence identity = new DefinitionFence(parsedPointers, (int) StrictJson.integer(fence.get("variable_epoch"), 0, 255));
        ObjectNode persisted = StrictJson.object().put("schema", SCHEMA); persisted.set("planning_frame", frameJson(expected)); persisted.set("native_observation", node);
        return new Quote(expected, captureEpoch, borrow, repay, principal, debt, identity, StrictJson.canonical(persisted));
    }
    /** Exact frame/connection/nonce comparison invalidates stored quotes across continuation and reconnect. */
    public static Result decode(byte[] bytes, PlanningFrame expected, BigInteger captureEpoch) {
        validateFrame(expected, captureEpoch);
        ObjectNode node = StrictJson.object(StrictJson.parse(bytes), Set.of("schema", "planning_frame", "native_observation"));
        require(SCHEMA.equals(StrictJson.text(node.get("schema"))), "loan source persistence v2 required");
        if (!frame(node.get("planning_frame")).equals(expected)) { return new Refused(Refusal.FRAME_DRIFT); }
        return projectNative(StrictJson.canonical(node.get("native_observation")), expected, captureEpoch);
    }
    /** Both copies require Root-qualified read origins. Even equal data always consumes the fresh copy. */
    public static CopyComparison compareCopies(Quote previous, Quote current) {
        Objects.requireNonNull(previous, "previous"); Objects.requireNonNull(current, "current");
        require(!previous.captureEpoch().equals(current.captureEpoch()), "a new read nonce is required for revalidation");
        if (!previous.frame().equals(current.frame())) { return CopyComparison.FRAME_CHANGED; }
        if (!previous.definitionFence().equals(current.definitionFence())) { return CopyComparison.DEFINITIONS_OR_IDENTIFIER_EPOCH_CHANGED; }
        if (!previous.borrowDecision().equals(current.borrowDecision()) || !previous.repayDecision().equals(current.repayDecision())
                || previous.prospectivePrincipalRaw() != current.prospectivePrincipalRaw() || !previous.debt().equals(current.debt())) {
            return CopyComparison.QUOTE_CONTENT_CHANGED;
        }
        return CopyComparison.SAME_CAPTURED_CONTENT_USE_CURRENT;
    }
    private static ObservedDecision gate(JsonNode value, Definition definition) {
        ObjectNode node = StrictJson.object(value, Set.of("is_shown", "can_take", "affordable", "costs_raw_by_native_index"));
        JsonNode vector = node.get("costs_raw_by_native_index"); require(vector.isArray() && vector.size() == 10, "all ten declared resource slots required");
        List<Long> costs = new ArrayList<>(); for (JsonNode raw : vector) { costs.add(StrictJson.integer(raw, Long.MIN_VALUE, Long.MAX_VALUE)); }
        return new ObservedDecision(definition, bool(node.get("is_shown")), bool(node.get("can_take")), bool(node.get("affordable")), costs);
    }
    private static DebtCopy debt(JsonNode value) {
        ObjectNode node = StrictJson.object(value, Set.of("available", "unavailable_reason", "borrower_context", "borrower_clock_raw",
                "borrower_rows", "holder_resolved", "lender_context", "lender_clock_raw", "lender_years_row", "lender_membership", "expiry_semantics_qualified"));
        require(node.get("lender_membership").isNull(), "unread lender list cannot claim membership"); falseValue(node.get("expiry_semantics_qualified"));
        ObjectNode rows = StrictJson.object(node.get("borrower_rows"), Set.of("loan_amount_owed", "loan_holder", "years_since_loan", "original_loan_holder", "original_lender"));
        if (!bool(node.get("available"))) {
            for (String key : List.of("borrower_context", "borrower_clock_raw", "holder_resolved", "lender_context", "lender_clock_raw", "lender_years_row"))
                require(node.get(key).isNull(), "unavailable debt leaked " + key);
            rows.forEach(row -> require(row.isNull(), "unavailable debt leaked scalar"));
            return new DebtUnavailable(DebtFailure.exact(StrictJson.text(node.get("unavailable_reason"))));
        }
        require(node.get("unavailable_reason").isNull(), "copied debt has failure");
        var borrower = new BorrowerRows(scalar(rows.get("loan_amount_owed")), scalar(rows.get("loan_holder")), scalar(rows.get("years_since_loan")),
                scalar(rows.get("original_loan_holder")), scalar(rows.get("original_lender")));
        Optional<Boolean> resolved = node.get("holder_resolved").isNull() ? Optional.empty() : Optional.of(bool(node.get("holder_resolved")));
        Optional<Pointer> lender = node.get("lender_context").isNull() ? Optional.empty() : Optional.of(pointer(node.get("lender_context")));
        OptionalInt clock = node.get("lender_clock_raw").isNull() ? OptionalInt.empty()
                : OptionalInt.of((int) StrictJson.integer(node.get("lender_clock_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE));
        return new CopiedDebt(pointer(node.get("borrower_context")), (int) StrictJson.integer(node.get("borrower_clock_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE),
                borrower, resolved, lender, clock, scalar(node.get("lender_years_row")));
    }
    private static Optional<Scalar> scalar(JsonNode value) {
        if (value.isNull()) { return Optional.empty(); }
        ObjectNode node = StrictJson.object(value, Set.of("kind", "payload_raw", "expiry_raw"));
        return Optional.of(new Scalar(Kind.exact((int) StrictJson.integer(node.get("kind"), 0, 65535)),
                StrictJson.integer(node.get("payload_raw"), Long.MIN_VALUE, Long.MAX_VALUE), (int) StrictJson.integer(node.get("expiry_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE)));
    }
    private static void rowKind(Optional<Scalar> value, Kind expected) {
        Objects.requireNonNull(value, "row"); value.ifPresent(row -> require(row.kind() == expected, "debt row kind differs"));
    }
    private static Pointer pointer(JsonNode value) { return new Pointer(decimal(value, BigInteger.ONE)); }
    private static BigInteger decimal(JsonNode value, BigInteger minimum) {
        String text = StrictJson.text(value); require(text.matches("0|[1-9][0-9]{0,19}"), "canonical decimal uint64 string required");
        BigInteger number = new BigInteger(text); unsigned(number, minimum, StrictJson.UINT64_MAX); return number;
    }
    private static void validateFrame(PlanningFrame frame, BigInteger epoch) {
        Objects.requireNonNull(frame, "frame"); StrictJson.text(frame.snapshotId()); StrictJson.text(frame.episodeRunId());
        unsigned(frame.revision(), BigInteger.ZERO, StrictJson.UINT64_MAX); unsigned(frame.nativeRevision(), BigInteger.ONE, StrictJson.UINT64_MAX);
        unsigned(frame.connectionGeneration(), BigInteger.ZERO, StrictJson.UINT64_MAX); unsigned(epoch, BigInteger.ONE, StrictJson.UINT64_MAX);
        unsigned(frame.actorCharacterId(), BigInteger.ZERO, U32.subtract(BigInteger.ONE)); unsigned(frame.bridgePid(), BigInteger.ONE, U32);
        unsigned(frame.dateRaw(), BigInteger.ZERO, BigInteger.valueOf(Integer.MAX_VALUE));
    }
    private static ObjectNode frameJson(PlanningFrame frame) {
        ObjectNode out = StrictJson.object().put("snapshot_id", frame.snapshotId()).put("revision", frame.revision().toString())
                .put("native_revision", frame.nativeRevision().toString()).put("episode_run_id", frame.episodeRunId()).put("connection_generation", frame.connectionGeneration().toString());
        out.put("actor_character_id", frame.actorCharacterId()); out.put("date_raw", frame.dateRaw()); out.put("bridge_pid", frame.bridgePid()); return out;
    }
    private static PlanningFrame frame(JsonNode value) {
        ObjectNode node = StrictJson.object(value, FRAME_FIELDS);
        return new PlanningFrame(StrictJson.text(node.get("snapshot_id")), decimal(node.get("revision"), BigInteger.ZERO), decimal(node.get("native_revision"), BigInteger.ONE),
                StrictJson.integer(node.get("date_raw"), BigInteger.ZERO, BigInteger.valueOf(Integer.MAX_VALUE)), StrictJson.integer(node.get("actor_character_id"), BigInteger.ZERO, U32.subtract(BigInteger.ONE)),
                StrictJson.text(node.get("episode_run_id")), StrictJson.integer(node.get("bridge_pid"), BigInteger.ONE, U32), decimal(node.get("connection_generation"), BigInteger.ZERO));
    }
    private static boolean bool(JsonNode value) { require(value.isBoolean(), "exact boolean required"); return value.booleanValue(); }
    private static void falseValue(JsonNode value) { require(value.isBoolean() && !value.booleanValue(), "source cannot claim effects, terms or funds"); }
    private static void unsigned(BigInteger value, BigInteger min, BigInteger max) { require(value != null && value.compareTo(min) >= 0 && value.compareTo(max) <= 0, "value outside exact unsigned domain"); }
    private static void require(boolean value, String message) { StrictJson.require(value, message); }
}
