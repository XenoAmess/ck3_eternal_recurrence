package org.xar.ck3.markets.acceptance;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;
import java.util.List;
import java.util.Objects;

/** Strict observation inputs. Business IDs bind real objects; expected values never seed them. */
public final class FollowupContracts {
    private FollowupContracts() { }
    public sealed interface Input permits LegacyInput, Request { }
    public record LegacyInput(AcceptanceContracts.Request request) implements Input {
        public LegacyInput { Objects.requireNonNull(request, "core request"); }
    }
    public enum Profile {
        SPOT("spot"), DERIVATIVES("derivatives"), LIFECYCLE("lifecycle"), INHERITANCE("inheritance"),
        COLD_RELOAD("cold-reload"), NEWS_CRISIS("news-crisis"), AI_CAPACITY("ai-capacity"),
        MARKET_EVOLUTION("market-evolution"), DELISTING_GUI("delisting-gui");
        private final String wire;
        Profile(String wire) { this.wire = wire; }
        @JsonValue public String wire() { return wire; }
        public String scriptKey() { return wire.replace('-', '_'); }
        @JsonCreator public static Profile parse(String text) {
            for (Profile value : values()) if (value.wire.equals(text)) return value;
            throw new IllegalArgumentException("unknown follow-up observation case");
        }
    }
    public enum ActorMode { CURRENT_PLAYER, HISTORY_CHARACTER }
    public record ActorBinding(ActorMode mode, String historyId) {
        public ActorBinding {
            Objects.requireNonNull(mode, "actor mode");
            if (mode == ActorMode.HISTORY_CHARACTER) new AcceptanceContracts.Request(1, historyId);
            else require(historyId == null, "current-player binding has no history key");
        }
    }
    public enum ScaleTier {
        SMOKE(128, 100), CONSERVATIVE(2048, 1024), STANDARD(4096, 4000), EXTENDED(8192, 4000);
        private final int coins;
        private final int positions;
        ScaleTier(int coins, int positions) { this.coins = coins; this.positions = positions; }
        public int coins() { return coins; }
        public int positions() { return positions; }
    }
    public record Targets(String accountId, String coinId, String contractId, String positionId,
                          String debtId, String newsId, String indexId) {
        public Targets(String accountId, String coinId, String contractId, String positionId, String debtId, String newsId) {
            this(accountId, coinId, contractId, positionId, debtId, newsId, null);
        }
        public Targets {
            require(accountId != null, "actual account ID required");
            for (String value : new String[]{accountId, coinId, contractId, positionId, debtId, newsId}) id(value);
            require(indexId == null || indexId.matches("[1-3]"), "model index ID must be 1, 2 or 3");
            require(indexId == null || coinId == null, "select a coin or model index, never both");
            require(positionId == null || contractId != null, "position target requires its contract ID");
        }
    }
    public record AccountBaseline(long freeCents, long reservedCents, int systemAccount,
                                  int inheritanceState, int frozen) {
        public AccountBaseline {
            amount(freeCents); amount(reservedCents); bit(systemAccount); bit(frozen);
            require(inheritanceState >= 0 && inheritanceState <= 2, "inheritance state");
        }
    }
    public record CoinBaseline(long supplyUnits, int listingState, long priceVersion) {
        public CoinBaseline { amount(supplyUnits); amount(priceVersion); require(listingState >= 0 && listingState <= 8, "listing state"); }
    }
    public record PositionBaseline(long lots, long markCents, int status, long createdDay,
                                   long settledDay, String longAccountId, String shortAccountId,
                                   long longReservationId, long shortReservationId,
                                   long longRemainingCents, long shortRemainingCents) {
        public PositionBaseline {
            amount(lots); amount(markCents); day(createdDay); day(settledDay);
            require(status >= 0 && status <= 3, "position status");
            require(longAccountId != null && shortAccountId != null, "both real account IDs required");
            id(longAccountId); id(shortAccountId); require(!longAccountId.equals(shortAccountId), "distinct accounts");
            require(longReservationId > 0 && longReservationId <= 1_000_000_000L && shortReservationId > 0 && shortReservationId <= 1_000_000_000L, "reservation IDs");
            amount(longRemainingCents); amount(shortRemainingCents);
        }
    }
    public record DebtBaseline(long originalCents, long outstandingCents, long winnerUnpaidCents,
                               long fundRecourseCents, long fundPaidCents, long repaidCents,
                               long writtenOffCents, long sourceDay, int sourceKind, long dueDay,
                               String debtorAccountId, String creditorAccountId) {
        public DebtBaseline {
            for (long value : new long[]{originalCents, outstandingCents, winnerUnpaidCents, fundRecourseCents, fundPaidCents, repaidCents, writtenOffCents}) amount(value);
            day(sourceDay); day(dueDay); require(sourceKind >= 1 && sourceKind <= 4, "settlement kind");
            require(debtorAccountId != null && creditorAccountId != null, "actual debt parties required");
            id(debtorAccountId); id(creditorAccountId);
            require(originalCents == outstandingCents + repaidCents + writtenOffCents, "baseline debt principal mismatch");
            require(outstandingCents == winnerUnpaidCents + fundRecourseCents, "baseline claim split mismatch");
        }
    }
    public record ColdBaseline(long day, AccountBaseline account, CoinBaseline coin,
                               PositionBaseline position, DebtBaseline debt) {
        public ColdBaseline { FollowupContracts.day(day); Objects.requireNonNull(account, "account baseline"); }
    }
    public record Request(int schemaVersion, Profile caseId, int observationEpoch, ActorBinding actor,
                          Targets targets, ColdBaseline coldBaseline, ScaleTier scaleTier) implements Input {
        public Request {
            require(schemaVersion == 2, "follow-up schemaVersion must be 2");
            Objects.requireNonNull(caseId, "caseId"); Objects.requireNonNull(actor, "actor"); Objects.requireNonNull(targets, "targets");
            require(observationEpoch >= 1 && observationEpoch <= 1_000_000_000, "positive bounded observation epoch");
            if (caseId == Profile.DERIVATIVES) require(targets.coinId != null || targets.indexId != null, "derivatives needs an actual coin or model index");
            else require(targets.indexId == null, "model index observation applies to derivatives only");
            if (caseId == Profile.SPOT) require(targets.coinId != null && targets.contractId == null && targets.positionId == null
                    && targets.debtId == null && targets.newsId == null, "spot requires only a real coin/account target");
            if (caseId == Profile.LIFECYCLE || caseId == Profile.AI_CAPACITY || caseId == Profile.MARKET_EVOLUTION || caseId == Profile.DELISTING_GUI)
                require(targets.coinId != null, "profile needs a real coin target");
            if (caseId == Profile.DELISTING_GUI)
                require(targets.newsId == null, "delisting GUI discovers its new source-bound notice fact, never a historical news target");
            if (caseId == Profile.MARKET_EVOLUTION)
                require(targets.debtId == null && targets.newsId == null, "natural evolution records optional facts without a forced debt/news target");
            if (caseId == Profile.LIFECYCLE || caseId == Profile.INHERITANCE || caseId == Profile.NEWS_CRISIS)
                require(targets.debtId != null, "profile needs its genuine existing claim target");
            if (caseId == Profile.COLD_RELOAD) {
                Objects.requireNonNull(coldBaseline, "actual pre-close baseline required");
                require((coldBaseline.coin != null) == (targets.coinId != null), "coin baseline/target mismatch");
                require((coldBaseline.position != null) == (targets.positionId != null), "position baseline/target mismatch");
                require((coldBaseline.debt != null) == (targets.debtId != null), "debt baseline/target mismatch");
            } else require(coldBaseline == null, "cold baseline only applies to cold-reload");
            require((caseId == Profile.AI_CAPACITY) == (scaleTier != null), "scale tier only and always for capacity");
        }
        public String prefix() { return "xfma_" + caseId.scriptKey() + "_e" + observationEpoch; }
        public List<String> markers() {
            String prefix = "XFMAT: TEST PASS " + caseId.scriptKey() + "_";
            List<String> observations = switch (caseId) {
                case SPOT -> List.of("observation_ready", "watched_sample_readback", "new_buy_filled_readback", "new_sell_filled_readback", "partial_cancelled_readback", "original_order_fee_readback");
                case DERIVATIVES -> List.of("observation_ready", "paired_position_readback", "settled_after_baseline", "claim_accounting_readback");
                case DELISTING_GUI -> List.of("observation_ready", "new_notice_kind8_readback", "day14_exit_window_readback", "termination_state_readback", "day30_venue_exit_readback", "rights_sources_after_exit_readback");
                case LIFECYCLE -> List.of("observation_ready", "new_notice_readback", "exit_state_after_notice", "surviving_claim_readback");
                case INHERITANCE -> List.of("observation_ready", "original_holder_died", "account_inherited_or_frozen", "original_claim_reference_survives");
                case COLD_RELOAD -> List.of("observation_ready", "loaded_sample_matches_baseline", "same_day_refresh_sample_unchanged");
                case NEWS_CRISIS -> List.of("observation_ready", "claim_accounting_readback", "crisis_or_relief_readback", "new_world_fact_after_baseline", "delivery_state_bounded_readback");
                case AI_CAPACITY -> List.of("observation_ready", "declared_inventory_readback", "ai_paid_issuance_readback", "365_daily_samples_after_warmup");
                case MARKET_EVOLUTION -> List.of("observation_ready", "baseline_inventory_captured", "availability_summary_recorded", "35_daily_samples_observed");
            };
            return observations.stream().map(prefix::concat).toList();
        }
    }
    static void require(boolean value, String message) { AcceptanceContracts.require(value, message); }
    private static void id(String value) {
        if (value == null) return;
        require(value.matches("[1-9][0-9]{0,9}"), "canonical positive ID string required");
        require(Long.parseLong(value) <= 1_000_000_000L, "business ID exceeds supported script bound");
    }
    private static void bit(int value) { require(value == 0 || value == 1, "boolean script state must be 0 or 1"); }
    private static void amount(long value) { require(value >= 0 && value <= 1_000_000_000_000L, "nonnegative bounded integer required"); }
    private static void day(long value) { require(value >= 0 && value <= 1_000_000_000L, "bounded financial day required"); }
}
