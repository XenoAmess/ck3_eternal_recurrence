package org.xar.ck3.markets.saveaudit;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;
import java.math.BigInteger;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.save.SaveContracts.NativeId;

/** Exact integer financial data plus original typed issuance envelopes. Absent values are never manufactured as zero. */
public record FinancialSnapshot(String machineId, String saveSha256, String gameVersion, String saveFormat,
                                String gameDate, List<Story> stories, List<Issue> issues) {
    public FinancialSnapshot {
        Objects.requireNonNull(machineId); Objects.requireNonNull(saveSha256); Objects.requireNonNull(gameVersion);
        Objects.requireNonNull(saveFormat); Objects.requireNonNull(gameDate);
        stories = List.copyOf(stories); issues = List.copyOf(issues);
    }
    public enum Severity { INCOMPLETE, VIOLATION, UNQUALIFIED }
    public record Issue(Severity severity, String identity, String field, String detail) {
        public Issue { Objects.requireNonNull(severity); Objects.requireNonNull(identity); Objects.requireNonNull(field); Objects.requireNonNull(detail); }
    }
    public enum Type {
        EXCHANGE("xfm_finance_exchange", null), ACCOUNT("xfm_finance_account", NumberField.ACCOUNT_ID),
        RESERVATION("xfm_finance_reservation", NumberField.RESERVATION_ID), COIN("xfm_finance_coin", NumberField.COIN_ID),
        SPOT_POSITION("xfm_finance_position", null), SPOT_ORDER("xfm_spot_order", NumberField.ORDER_ID),
        FUTURES_CONTRACT("xfm_futures_contract", NumberField.CONTRACT_ID),
        FUTURES_ORDER("xfm_futures_order", NumberField.ORDER_ID),
        FUTURES_POSITION("xfm_futures_position", NumberField.POSITION_ID),
        DEBT("xfm_debt_claim", NumberField.DEBT_ID),
        REDEMPTION_WINDOW("xfm_finance_redemption_window", NumberField.WINDOW_ID),
        REDEMPTION_RECEIPT("xfm_finance_redemption_receipt", NumberField.RECEIPT_ID), INDEX("xfm_oracle_index", NumberField.INDEX_ID);
        private final String wire; private final NumberField permanent;
        Type(String wire, NumberField permanent) { this.wire = wire; this.permanent = permanent; }
        public String wire() { return wire; }
        public Optional<NumberField> permanentField() { return Optional.ofNullable(permanent); }
        public static Optional<Type> fromWire(String wire) {
            for (Type type : values()) if (type.wire.equals(wire)) return Optional.of(type);
            return Optional.empty();
        }
    }
    public enum NumberField {
        ACCOUNT_ID, RESERVATION_ID, COIN_ID, ORDER_ID, CONTRACT_ID, POSITION_ID, DEBT_ID, INDEX_ID,
        MODEL_QUOTE_DIVISOR,
        FREE_CENTS, RESERVED_CENTS, REMAINING_CENTS, FEE_CENTS,
        SUPPLY_UNITS, MAXIMUM_SUPPLY_UNITS, QUANTITY_UNITS, RESERVED_UNITS,
        REMAINING_LOTS, ORIGINAL_LOTS, FILLED_LOTS, LOTS, LIMIT_CENTS, MARK_CENTS, RESERVE_PRICE_CENTS,
        FILLED_NOTIONAL_CENTS, FILLED_GROSS_CENTS, FEE_PAID_CENTS, SIDE, STATUS,
        LONG_LEVERAGE, SHORT_LEVERAGE, LEVERAGE, PERPETUAL, EXPIRY_DAY, CREATED_DAY, LAST_SETTLED_DAY,
        LAST_DAILY_DAY, DAY, SOURCE_DAY, SOURCE_KIND, ORIGINAL_CENTS, OUTSTANDING_CENTS,
        WINNER_UNPAID_CENTS, FUND_PAID_CENTS, FUND_RECOURSE_CENTS, REPAID_CENTS, WRITTEN_OFF_CENTS,
        STATE, FUND_ELIGIBLE, TOTAL_DEBT_CENTS, REDUCE_ORDER,
        NEXT_ACCOUNT_ID, NEXT_RESERVATION_ID, NEXT_COIN_ID, NEXT_ORDER_ID, NEXT_FUTURES_ORDER_ID,
        NEXT_FUTURES_CONTRACT_ID, NEXT_FUTURES_POSITION_ID, DEBT_COUNTER,
        PENDING_PAYMENT, PENDING_AMOUNT, PENDING_PAID, PENDING_DAY, PENDING_KIND, PENDING_NEW_MARK,
        PENDING_LOSER, LAST_FUNDING_DAY,
        CANCEL_RECEIPT_VERSION, CANCEL_REASON, CANCEL_DAY, CANCEL_RECOVERY,
        CANCEL_RELEASE_VERIFIED, CANCEL_RELEASED_CENTS, CANCEL_RELEASE_RESULT, CANCEL_RELEASE_API_CALLED,
        CANCEL_BEFORE_FREE_CENTS, CANCEL_AFTER_FREE_CENTS,
        CANCEL_BEFORE_RESERVED_CENTS, CANCEL_AFTER_RESERVED_CENTS,
        CANCEL_BEFORE_REMAINING_CENTS, CANCEL_AFTER_REMAINING_CENTS,
        WINDOW_ID, RECEIPT_ID, PRICE_CENTS, INITIAL_CENTS, PAID_CENTS, PAID_UNITS, RECLAIMED_CENTS,
        BUDGET_AFTER_CENTS, REDEMPTION_ACCOUNT_ID, ISSUER_ACCOUNT_ID, PAYER_ACCOUNT_ID, PAYEE_ACCOUNT_ID,
        NEXT_REDEMPTION_WINDOW_ID, NEXT_REDEMPTION_RECEIPT_ID, SYSTEM_ACCOUNT, REDEMPTION_ONLY,
        REDEMPTION_LIFETIME_PAID_CENTS, REDEMPTION_LIFETIME_UNITS, LAST_RECLAIM_DAY,
        REDEMPTION_NEXT_PUBLISH_DAY, ACTUAL_UTILITY_CENTS, PROJECT_SPENT_CENTS,
        FILL_RECEIPT_VERSION, FILL_DAY, FILL_LOTS, FILL_MARK_CENTS,
        FILL_BUY_ORDER_ID, FILL_SELL_ORDER_ID, FILL_BUY_ACCOUNT_ID, FILL_SELL_ACCOUNT_ID,
        FILL_BUY_INTENT, FILL_SELL_INTENT, FILL_BUY_CLOSE_SOURCE_ID, FILL_SELL_CLOSE_SOURCE_ID,
        FILL_SLICE_SOURCE_POSITION_ID;
        public String wire() { return "xfm_" + name().toLowerCase(java.util.Locale.ROOT); }
    }
    public enum ReferenceField {
        HOLDER, BENEFICIAL_OWNER, CONTROLLER, ACCOUNT, COIN, CONTRACT, RESERVATION, SELL_POSITION,
        LONG_ACCOUNT, SHORT_ACCOUNT, LONG_RESERVATION, SHORT_RESERVATION,
        DEBTOR_ACCOUNT, CREDITOR_ACCOUNT, FUND_ACCOUNT, SOURCE, DEFAULT_FUND_ACCOUNT,
        ISSUER_ACCOUNT, PENDING_DEBTOR, PENDING_CREDITOR, CLOSE_POSITION,
        REDEMPTION_ACCOUNT, REDEMPTION_WINDOW, WINDOW, PAYER_ACCOUNT, PAYEE_ACCOUNT,
        PREVIOUS_RECEIPT, REDEMPTION_LAST_RECEIPT, LEGAL_ENTITY, PUBLISHER, MARKET_MAKER_ACCOUNT;
        public String wire() { return "xfm_" + name().toLowerCase(java.util.Locale.ROOT); }
        public boolean characterReference() { return this == HOLDER || this == BENEFICIAL_OWNER || this == CONTROLLER || this == PUBLISHER; }
    }
    public record Reference(String serializedType, NativeId nativeId) {
        public Reference { Objects.requireNonNull(serializedType); Objects.requireNonNull(nativeId); }
    }
    /** Fields written by the immutable issuance producer; no inference from current issuer state. */
    public enum ReceiptField {
        COIN_ID, ACTOR, PAYER, PAYER_ID, DAY, IS_AI, IS_LANDED, HIGHEST_TIER, FEE_CENTS,
        GOLD_BEFORE, GOLD_PRE_FEE, GOLD_AFTER, FREE_BEFORE, FREE_PRE_FEE, FREE_AFTER,
        RESERVED_BEFORE, RESERVED_AFTER, FEES_BEFORE, FEES_AFTER, TOPUP_CENTS, VERSION;
        @JsonValue public String wire() { return "xfm_issue_receipt_" + name().toLowerCase(java.util.Locale.ROOT); }
        @JsonCreator public static ReceiptField fromWire(String wire) {
            for (ReceiptField field : values()) if (field.wire().equals(wire)) return field;
            throw new IllegalArgumentException("Unknown issuance receipt field: " + wire);
        }
        public boolean reference() { return this == ACTOR || this == PAYER; }
        public boolean fractionalGold() { return this == GOLD_BEFORE || this == GOLD_PRE_FEE || this == GOLD_AFTER; }
    }
    /** Original assigned data envelope. Numeric identities remain serialized integer strings, NOT decoded cents/Gold.
     * Decode only with the report's explicit numericScale/numberIdentityEncoding; omitted zero stays lexically absent. */
    public record ReceiptValue(String serializedType, boolean identityPresent, String rawIdentity) {
        public ReceiptValue {
            if (serializedType == null || serializedType.isBlank() || rawIdentity == null
                    || identityPresent && rawIdentity.isEmpty() || !identityPresent && !rawIdentity.isEmpty())
                throw new IllegalArgumentException("Explicit issuance envelope type and identity presence required.");
        }
    }
    /** observed=false means a legacy report/caller never projected this field, not a known empty receipt. */
    public record ReceiptProjection(boolean observed, Map<ReceiptField, ReceiptValue> fields) {
        public ReceiptProjection {
            EnumMap<ReceiptField, ReceiptValue> values = new EnumMap<>(ReceiptField.class); values.putAll(fields);
            fields = Map.copyOf(values);
            if (!observed && !fields.isEmpty()) throw new IllegalArgumentException("Unobserved issuance projection cannot contain values.");
        }
        public static ReceiptProjection unobserved() { return new ReceiptProjection(false, Map.of()); }
    }
    public record Story(Type type, NativeId nativeId, Optional<NativeId> permanentId,
                         Map<NumberField, BigInteger> numbers, Map<ReferenceField, Reference> references,
                         ReceiptProjection issuanceReceipt) {
        /** Source-compatible old callers retain Unknown, never an asserted empty observation. */
        public Story(Type type, NativeId nativeId, Optional<NativeId> permanentId,
                     Map<NumberField, BigInteger> numbers, Map<ReferenceField, Reference> references) {
            this(type, nativeId, permanentId, numbers, references, ReceiptProjection.unobserved());
        }
        public Story {
            Objects.requireNonNull(type); Objects.requireNonNull(nativeId); Objects.requireNonNull(permanentId);
            EnumMap<NumberField, BigInteger> numeric = new EnumMap<>(NumberField.class); numeric.putAll(numbers);
            EnumMap<ReferenceField, Reference> scopes = new EnumMap<>(ReferenceField.class); scopes.putAll(references);
            numbers = Map.copyOf(numeric); references = Map.copyOf(scopes); Objects.requireNonNull(issuanceReceipt);
        }
        public String identity() { return type + ":" + permanentId.map(NativeId::value).orElse("native-" + nativeId.value()); }
        public Optional<BigInteger> number(NumberField field) { return Optional.ofNullable(numbers.get(field)); }
        public Optional<Reference> reference(ReferenceField field) { return Optional.ofNullable(references.get(field)); }
    }
}
