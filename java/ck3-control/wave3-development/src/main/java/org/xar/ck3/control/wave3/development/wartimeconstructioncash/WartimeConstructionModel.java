package org.xar.ck3.control.wave3.development.wartimeconstructioncash;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.CashContext;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.QuoteRow;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Read;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.SourceFrame;

/** Construction-specific reserve policy over shared observed context, never an action submitter. */
public final class WartimeConstructionModel {
    private WartimeConstructionModel() { }
    public enum Kind {
        NEW_BUILDING("new_building"), UPGRADE_BUILDING("upgrade_building"), NEW_HOLDING("new_holding"), UNKNOWN("");
        private final String wire;
        Kind(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Kind of(String wire) {
            for (Kind kind : values()) if (!kind.wire.isEmpty() && kind.wire.equals(wire)) return kind;
            return UNKNOWN;
        }
    }
    public enum GroupShape { ALL_OBJECTS, INCOMPLETE }
    public enum MarketShape { MISSING, EMPTY, NONEMPTY }
    public record QuoteEvidence(QuoteRow quote, GroupShape groups) {
        public QuoteEvidence { Objects.requireNonNull(quote); Objects.requireNonNull(groups); }
    }
    public record FinanceFrame(Read<BigInteger> actor, Read<BigInteger> revision, Read<BigInteger> date, boolean exactKeys) { }
    public record ProcurementCandidate(boolean emptyRejections, Read<FinanceFrame> financeFrame,
            Read<List<BigInteger>> purposeWars, Read<BigInteger> companyId, Read<BigInteger> goldCost) {
        public ProcurementCandidate {
            if (purposeWars.known()) purposeWars = Read.of(List.copyOf(purposeWars.value()));
        }
    }
    public record Input(String kindWire, Read<BigInteger> cost, CashContext context,
            List<QuoteEvidence> quotes, MarketShape marketShape, Read<ProcurementCandidate> procurement,
            WartimeConstructionCodec.FocusRequest focusRequest) {
        public Input {
            Objects.requireNonNull(kindWire); Objects.requireNonNull(cost); Objects.requireNonNull(context);
            quotes = List.copyOf(quotes); Objects.requireNonNull(marketShape); Objects.requireNonNull(procurement); Objects.requireNonNull(focusRequest);
        }
    }
    public enum Status {
        DEFER("defer_optional_construction"), PEACE("outside_wartime"), AMPLE("ample_wartime_cash");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum Reason {
        KIND("construction_kind_unidentified"), HOLDING("new_holding_native_action_interface_unavailable"),
        WARS("current_active_wars_unobserved"), COST("complete_current_construction_gold_quote_missing"),
        TREASURY("current_treasury_unobserved"), MAINTENANCE("same_frame_maximum_military_maintenance_unobserved"),
        SPENDING("same_frame_existing_spending_commitments_unobserved"), MERCENARY("mercenary_commitment_unknown_or_pending_never_replay"),
        MARKET("same_frame_available_mercenary_emergency_quotes_unobserved"), EMPTY_MARKET("complete_market_empty_no_emergency_company"),
        NO_USABLE("no_current_native_usable_emergency_company_quote"), RETAIN("retain_maximum_military_commitments_and_native_emergency_quote"),
        NOT_AMPLE("wartime_cash_not_very_ample_after_optional_outlay");
        private final String wire;
        Reason(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum QuoteReason {
        INCOMPLETE("native_terms_incomplete"), USABLE("current_native_legal_emergency_cash_buffer_quote"),
        NOT_READY("native_legal_strength_or_spawn_terms_not_ready");
        private final String wire;
        QuoteReason(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record Comparison(Read<BigInteger> companyId, boolean completeGroups, boolean usable,
            Optional<BigInteger> contractGold, Read<BigInteger> soldiers, QuoteReason reason) { }
    public enum SelectionBasis {
        ASSESSED("current_frame_assessed_suitable_procurement_quote"),
        CHEAPEST_ADEQUATE("cheapest_current_legal_quote_covering_focused_observed_headcount_deficit"),
        CONSERVATIVE_MAXIMUM("conservative_maximum_complete_native_legal_quote_not_a_win_or_arrival_forecast");
        private final String wire;
        SelectionBasis(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record Reserve(BigInteger treasury, BigInteger afterConstruction, BigInteger required,
            BigInteger maximumMaintenance, BigInteger militaryBuffer, BigInteger commitments,
            Comparison selected, SelectionBasis basis, Optional<BigInteger> focusedWar,
            Optional<BigInteger> observedDeficit) { }
    public record Decision(SourceFrame frame, String kindWire, Read<BigInteger> quotedCost, Status status,
            Optional<Reason> reason, Optional<Boolean> marketEmpty, Optional<List<Comparison>> comparisons,
            Optional<Reserve> reserve) {
        public Decision {
            comparisons = comparisons.map(List::copyOf);
            if ((status == Status.PEACE) != reason.isEmpty() || status == Status.AMPLE && reserve.isEmpty())
                throw new IllegalArgumentException("construction result branch shape");
        }
        public boolean newSpendAllowed() { return status != Status.DEFER; }
    }
}
