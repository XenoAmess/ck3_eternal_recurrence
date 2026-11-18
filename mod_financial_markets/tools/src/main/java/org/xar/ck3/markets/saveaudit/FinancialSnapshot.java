package org.xar.ck3.markets.saveaudit;

import java.math.BigInteger;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.save.SaveContracts.NativeId;

/** Exact integer financial data. Absent values stay absent; they are never manufactured as zero. */
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
        WINDOW_ID, RECEIPT_ID, PRICE_CENTS, INITIAL_CENTS, PAID_CENTS, PAID_UNITS, RECLAIMED_CENTS,
        BUDGET_AFTER_CENTS, REDEMPTION_ACCOUNT_ID, ISSUER_ACCOUNT_ID, PAYER_ACCOUNT_ID, PAYEE_ACCOUNT_ID,
        NEXT_REDEMPTION_WINDOW_ID, NEXT_REDEMPTION_RECEIPT_ID, SYSTEM_ACCOUNT, REDEMPTION_ONLY,
        REDEMPTION_LIFETIME_PAID_CENTS, REDEMPTION_LIFETIME_UNITS, LAST_RECLAIM_DAY,
        REDEMPTION_NEXT_PUBLISH_DAY, ACTUAL_UTILITY_CENTS, PROJECT_SPENT_CENTS;
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
    public record Story(Type type, NativeId nativeId, Optional<NativeId> permanentId,
                        Map<NumberField, BigInteger> numbers, Map<ReferenceField, Reference> references) {
        public Story {
            Objects.requireNonNull(type); Objects.requireNonNull(nativeId); Objects.requireNonNull(permanentId);
            EnumMap<NumberField, BigInteger> numeric = new EnumMap<>(NumberField.class); numeric.putAll(numbers);
            EnumMap<ReferenceField, Reference> scopes = new EnumMap<>(ReferenceField.class); scopes.putAll(references);
            numbers = Map.copyOf(numeric); references = Map.copyOf(scopes);
        }
        public String identity() { return type + ":" + permanentId.map(NativeId::value).orElse("native-" + nativeId.value()); }
        public Optional<BigInteger> number(NumberField field) { return Optional.ofNullable(numbers.get(field)); }
        public Optional<Reference> reference(ReferenceField field) { return Optional.ofNullable(references.get(field)); }
    }
}
