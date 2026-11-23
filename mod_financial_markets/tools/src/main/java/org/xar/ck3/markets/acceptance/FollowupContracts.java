package org.xar.ck3.markets.acceptance;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;
import java.util.List;
import java.util.Objects;

/** Strict observation inputs. Business IDs bind real objects; expected values never seed them. */
public final class FollowupContracts {
    private FollowupContracts() { }
    public sealed interface Input permits LegacyInput, Request, ControlledFundingRequest, ControlledDebtAidNewsRequest, ControlledLoadRequest, ControlledCrisis20Request, ControlledFuturesRiskRequest { }
    /** Explicit isolated county-input fixture; not natural-market or funding qualification. */
    public record ControlledFuturesRiskRequest(int schemaVersion,String caseId,boolean controlledFixtureOnly) implements Input {
        public ControlledFuturesRiskRequest { new ControlledFuturesRiskFixture.Request(schemaVersion,caseId,controlledFixtureOnly); }
        public List<String> markers() { return ControlledFuturesRiskFixture.markers(); }
    }
    public record LegacyInput(AcceptanceContracts.Request request) implements Input {
        public LegacyInput { Objects.requireNonNull(request, "core request"); }
    }
    /** Explicit test-only opt-in; never a schema1/2 read-only observer request. */
    public record ControlledFundingRequest(int schemaVersion, String caseId, boolean controlledFixtureOnly) implements Input {
        public ControlledFundingRequest {
            require(schemaVersion == 3, "controlled funding schemaVersion must be 3");
            require("perpetual-funding-engine-fixture".equals(caseId), "exact controlled funding case required");
            require(controlledFixtureOnly, "explicit controlled fixture opt-in required");
        }
        public List<String> markers() {
            return List.of("XFMAT: TEST PASS controlled_funding_seeded_baseline", "XFMAT: TEST PASS controlled_funding_real_pairs_registered", "XFMAT: TEST PASS controlled_funding_funding_capture_recorded", "XFMAT: TEST PASS controlled_funding_same_day_retry_recorded", "XFMAT: TEST PASS controlled_funding_next_settlement_recorded", "XFMAT: TEST PASS controlled_funding_closed_rights_recorded");
        }
    }
    /** Explicit API-liability fixture; these inputs never claim a real market loss. */
    public record ControlledDebtParticipants(String debtorAccountId, String aidCreditorAccountId,
                                             String playerAccountId) {
        public ControlledDebtParticipants {
            for (String value : new String[]{debtorAccountId, aidCreditorAccountId, playerAccountId}) {
                require(value != null, "all three actual account IDs required"); id(value);
            }
            require(java.util.Set.of(debtorAccountId, aidCreditorAccountId, playerAccountId).size() == 3,
                    "three distinct controlled account IDs required");
        }
    }
    public record ControlledDebtAidNewsRequest(int schemaVersion, String caseId,
                                               boolean controlledFixtureOnly,
                                               ControlledDebtParticipants participants) implements Input {
        public ControlledDebtAidNewsRequest {
            require(schemaVersion == 3, "controlled debt schemaVersion must be 3");
            require("debt-aid-news-engine-fixture".equals(caseId), "exact controlled debt case required");
            require(controlledFixtureOnly, "explicit controlled fixture opt-in required");
            Objects.requireNonNull(participants, "actual controlled participants");
        }
        public List<String> markers() {
            return List.of("XFMAT: TEST PASS controlled_debt_api_claims_recorded",
                    "XFMAT: TEST PASS controlled_debt_gui_help_and_retry_recorded");
        }
    }
    /** Synthetic shape/load only: no natural AI issuance, paid fee or matured-market credit. */
    public record ControlledLoadRequest(int schemaVersion, String caseId, boolean controlledFixtureOnly,
                                        List<Integer> loadCoins) implements Input {
        public ControlledLoadRequest {
            require(schemaVersion == 3, "controlled load schemaVersion must be 3");
            require("synthetic-controlled-load".equals(caseId), "exact synthetic load case required");
            require(controlledFixtureOnly, "explicit synthetic business-effects opt-in required");
            require(List.of(2048, 4096).equals(loadCoins), "only ordered standard-rule 2048 then 4096 allowed");
            loadCoins = List.copyOf(loadCoins);
        }
        public List<String> markers() {
            return List.of("XFMAT: TEST PASS synthetic_load_2048_built",
                    "XFMAT: TEST PASS synthetic_load_2048_window_recorded",
                    "XFMAT: TEST PASS synthetic_load_4096_built",
                    "XFMAT: TEST PASS synthetic_load_4096_window_recorded");
        }
    }
    /** Independent controlled scene test: IDs only, never caller assertions about identity or context. */
    public record CrisisSceneRole(int sceneId, String accountId) {
        public CrisisSceneRole { require(sceneId >= 1 && sceneId <= 20, "scene ID1..20"); require(accountId != null, "actual account ID"); id(accountId); }
    }
    public record CrisisControls(String childAccountId, String inheritedAccountId, String assetAccountId,
                                 String aidAccountId, String restructureAccountId) {
        public CrisisControls { for (String value : new String[]{childAccountId,inheritedAccountId,assetAccountId,aidAccountId,restructureAccountId}) { require(value != null,"actual control account ID"); id(value); } }
    }
    public record ControlledCrisis20Request(int schemaVersion, String caseId, boolean controlledFixtureOnly,
            String playerAccountId, String aidCreditorAccountId, List<CrisisSceneRole> scenes,
            CrisisControls controls) implements Input {
        public ControlledCrisis20Request {
            require(schemaVersion == 3 && "crisis-scenes20-engine-fixture".equals(caseId) && controlledFixtureOnly,
                    "exact independent controlled crisis20 opt-in required");
            require(playerAccountId != null && aidCreditorAccountId != null,"actual owner/creditor IDs"); id(playerAccountId); id(aidCreditorAccountId);
            Objects.requireNonNull(scenes); Objects.requireNonNull(controls); scenes=List.copyOf(scenes);
            require(scenes.size()==20,"exact ordered twenty actual roles required");
            java.util.Set<String> accounts=new java.util.HashSet<>(); accounts.add(playerAccountId); accounts.add(aidCreditorAccountId);
            for(int index=0;index<20;index++) { require(scenes.get(index).sceneId()==index+1,"scene order1..20 required"); accounts.add(scenes.get(index).accountId()); }
            accounts.addAll(List.of(controls.childAccountId(),controls.inheritedAccountId(),controls.assetAccountId(),controls.aidAccountId(),controls.restructureAccountId()));
            require(accounts.size()==27,"twenty-seven distinct actual account IDs required");
        }
        public List<String> markers() { return List.of("XFMAT: TEST PASS controlled_crisis20_setup_recorded", "XFMAT: TEST PASS controlled_crisis20_dispatch_recorded", "XFMAT: TEST PASS controlled_crisis20_reentry_recorded"); }
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
