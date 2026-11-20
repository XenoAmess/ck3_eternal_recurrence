package org.xar.ck3.markets.acceptance;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.markets.acceptance.FollowupContracts.*;
import org.xar.ck3.markets.acceptance.MarketEvolutionScriptContractTest.Node;
import org.xar.ck3.markets.acceptance.MarketEvolutionScriptContractTest.Vm;

/** Actual production calendar/oracle/AI/debt AST subsets. Boundary traces do not
 * simulate cash, settle contracts or claim whole-finance/Game coverage. */
final class CalendarDeferredScriptContractTest {
    private static Vm vm(long date, long previous, boolean adopted) throws IOException {
        Request request = new Request(2, Profile.MARKET_EVOLUTION, 1, new ActorBinding(ActorMode.CURRENT_PLAYER, null),
                new Targets("2", "1", null, null, null, null), null, null);
        Vm v = new Vm(request); v.loadCalendarDispatch(); v.scriptDateOverride = date;
        v.exchange.put("xfm_last_date", previous).put("xfm_day", 108).put("xfm_a0_migration_scanned", 1);
        if (adopted) v.exchange.put("xfm_calendar_protocol", 1).put("xfm_calendar_origin_date", previous);
        return v;
    }
    @Test void firstAdoptionRecordsPreoriginGapAndOnlyExecutesTheCurrentPeriod() throws IOException {
        Vm v = vm(389472, 389458, false); v.calendarCallback();
        assertEquals(109, v.exchange.n("xfm_day")); assertEquals(389472, v.exchange.n("xfm_last_date"));
        assertEquals(13, v.exchange.n("xfm_calendar_preorigin_unprocessed_dates"));
        assertEquals(List.of(389472L), v.calendarDueDates); assertEquals(List.of(0L), v.calendarRecoveryModes);
        assertEquals(389472, v.exchange.n("xfm_calendar_origin_date"));
    }
    @Test void twoOwedPeriodsRunTheOrderedRealEntryChainWithHonestDateProvenance() throws IOException {
        Vm v = vm(389472, 389470, true); v.calendarCallback();
        assertEquals(110, v.exchange.n("xfm_day")); assertEquals(389472, v.exchange.n("xfm_last_date"));
        assertEquals(List.of(389471L, 389472L), v.calendarDueDates);
        assertEquals(List.of(389472L, 389472L), v.calendarObservedDates);
        assertEquals(List.of(1L, 0L), v.calendarRecoveryModes);
        List<String> tick = List.of("xfm_spot_daily_effect", "xfm_oracle_daily_effect", "xfm_finance_capitalize_default_fund_effect",
                "xfm_futures_daily_effect", "xfm_coin_daily_effect", "xfm_listing_daily_effect", "xfm_debt_daily_effect",
                "xfm_news_daily_effect", "xfm_finance_run_ai_budget_effect");
        assertEquals(tick, v.calendarHookTrace.subList(0, 9)); assertEquals(tick, v.calendarHookTrace.subList(9, 18));
        assertEquals(0, v.exchange.n("xfm_calendar_backlog")); assertEquals(0, v.exchange.n("xfm_calendar_in_flight"));
        assertEquals(1, v.exchange.n("xfm_daily_attempt_count"), "callback counts are not financial tick counts");
    }
    @Test void sevenPeriodCapPreservesTheRemainingCursorWithoutDroppingDates() throws IOException {
        Vm v = vm(389478, 389458, true); v.calendarCallback();
        assertEquals(7, v.calendarDueDates.size()); assertEquals(115, v.exchange.n("xfm_day"));
        assertEquals(389465, v.exchange.n("xfm_last_date")); assertEquals(13, v.exchange.n("xfm_calendar_backlog"));
        assertTrue(v.calendarRecoveryModes.stream().allMatch(mode -> mode == 1));
        assertEquals(0, v.exchange.n("xfm_calendar_recovery"), "recovery permission is restored after return");
    }
    @Test void sameDateAndBackwardCallbacksDoNotDispatchOrResetTheOriginalCursor() throws IOException {
        for (long date : List.of(389470L, 389469L)) {
            Vm v = vm(date, 389470, true); v.calendarCallback();
            assertTrue(v.calendarHookTrace.isEmpty()); assertEquals(108, v.exchange.n("xfm_day"));
            assertEquals(389470, v.exchange.n("xfm_last_date"));
        }
    }
    @Test void unknownProtocolAndInFlightPeriodAreNeverReplayed() throws IOException {
        Vm unknown = vm(389472, 389470, true); unknown.exchange.put("xfm_calendar_protocol", 2); unknown.calendarCallback();
        assertEquals(108, unknown.exchange.n("xfm_day")); assertTrue(unknown.calendarHookTrace.isEmpty());
        Vm inFlight = vm(389472, 389470, true); inFlight.exchange.put("xfm_calendar_in_flight", 1); inFlight.calendarCallback();
        assertEquals(108, inFlight.exchange.n("xfm_day")); assertTrue(inFlight.calendarHookTrace.isEmpty());
        assertEquals(1, inFlight.exchange.n("xfm_calendar_in_flight"));
    }
    @Test void recoveryOracleUsesActualSourceAndCannotRollSlotsOrPromoteCurrentWorldIntoHistory() throws IOException {
        Vm v = vm(389472, 389470, true); v.loadCalendarSource("xfm_oracle_reference.txt");
        v.calendarBoundaryHooks.remove("xfm_oracle_daily_effect");
        v.exchange.put("xfm_calendar_recovery", 1);
        Node coin = v.global("xfm_coin_registry").getFirst();
        coin.put("xfm_oracle_quality", 1).put("xfm_max_leverage", 10).put("xfm_oracle_day", 107).put("xfm_mark_cents", 123)
                .put("xfm_oracle_bucket_day", 107).put("xfm_oracle_slot_0_day", 106).put("xfm_oracle_slot_0_price", 122);
        Node index = v.node("real-current-index-input", "xfm_finance_coin", true).put("xfm_oracle_quality", 3)
                .put("xfm_max_leverage", 5).put("xfm_oracle_day", 107).put("xfm_mark_cents", 456);
        v.global("xfm_index_registry").add(index);
        v.run("xfm_oracle_daily_effect", v.exchange, null);
        for (Node asset : List.of(coin, index)) { assertEquals(0, asset.n("xfm_oracle_quality")); assertEquals(0, asset.n("xfm_max_leverage")); assertEquals(107, asset.n("xfm_oracle_day")); }
        assertEquals(123, coin.n("xfm_mark_cents")); assertEquals(456, index.n("xfm_mark_cents"));
        assertEquals(107, coin.n("xfm_oracle_bucket_day")); assertEquals(106, coin.n("xfm_oracle_slot_0_day")); assertEquals(122, coin.n("xfm_oracle_slot_0_price"));
    }
    @Test void recoveryTradeAdmissionAndAIUseActualSourceAndDoNotCreateNewSamplesOrDecisionBudgets() throws IOException {
        Vm v = vm(389472, 389470, true); v.loadCalendarSource("xfm_oracle_samples.txt"); v.loadCalendarSource("xfm_finance_attention.txt");
        v.calendarBoundaryHooks.remove("xfm_finance_run_ai_budget_effect"); v.exchange.put("xfm_calendar_recovery", 1);
        Node coin = v.global("xfm_coin_registry").getFirst(); coin.put("xfm_oracle_bucket_samples", 3).put("xfm_qualified_volume_cents", 1234);
        v.run("xfm_oracle_record_trade_effect", coin, null); v.run("xfm_finance_run_ai_budget_effect", v.exchange, null);
        assertEquals(3, coin.n("xfm_oracle_bucket_samples")); assertEquals(1234, coin.n("xfm_qualified_volume_cents"));
        assertEquals(0, v.exchange.n("xfm_ai_work_today")); assertEquals(0, v.exchange.n("xfm_ai_decisions_today")); assertEquals(0, v.exchange.n("xfm_attention_work_today"));
        assertFalse(v.exchange.vars.containsKey("xfm_ai_remaining"));
    }
    @Test void recoveryObserverTailDoesNotManufactureCapacityOrEvolutionDailySamples() throws IOException {
        Vm v = vm(389472, 389470, true); v.calendarCallback();
        assertEquals(2, v.calendarDueDates.size()); assertEquals(1, v.calendarObservedTails);
        Vm bounded = vm(389478, 389458, true); bounded.calendarCallback();
        assertEquals(7, bounded.calendarDueDates.size()); assertEquals(0, bounded.calendarObservedTails);
    }
    @Test void actualCurrentRollPreservesOldBucketIdentityAndCannotTurnOneObservedDayIntoThreeValidDays() throws IOException {
        Vm v = vm(389472, 389470, true); v.loadCalendarSource("xfm_oracle_samples.txt");
        v.loadCalendarSource("xfm_oracle_reference.txt"); v.loadCalendarValues("xfm_oracle_values.txt");
        Node coin = v.global("xfm_coin_registry").getFirst();
        coin.put("xfm_oracle_bucket_day", 107).put("xfm_oracle_bucket_samples", 4)
                .put("xfm_oracle_bucket_notional", 1000).put("xfm_oracle_bucket_lots", 10)
                .put("xfm_qualified_volume_cents", 1000);
        v.exchange.put("xfm_calendar_recovery", 1); v.calendarBoundaryHooks.remove("xfm_oracle_daily_effect");
        v.run("xfm_oracle_daily_effect", v.exchange, null);
        assertEquals(107, coin.n("xfm_oracle_bucket_day"));
        coin.nodes("xfm_oracle_participants").add(v.player);
        v.exchange.put("xfm_calendar_recovery", 0).put("xfm_day", 110);
        v.run("xfm_oracle_roll_coin_effect", coin, null);
        assertEquals(107, coin.n("xfm_oracle_slot_9_day")); assertEquals(100, coin.n("xfm_oracle_slot_9_price"));
        assertEquals(8, coin.n("xfm_oracle_slot_9_participants")); assertEquals(107, coin.n("xfm_last_completed_volume_day"));
        assertEquals(110, coin.n("xfm_oracle_bucket_day")); assertEquals(0, coin.n("xfm_oracle_bucket_samples"));
        v.run("xfm_oracle_roll_coin_effect", coin, null); v.run("xfm_oracle_recalculate_effect", coin, null);
        assertEquals(1, coin.n("xfm_oracle_valid_days")); assertEquals(0, coin.n("xfm_oracle_quality"));
        assertFalse(coin.vars.containsKey("xfm_oracle_slot_10_day")); assertFalse(coin.vars.containsKey("xfm_oracle_slot_11_day"));
        assertTrue(coin.vars.keySet().stream().noneMatch(key -> key.contains("$SLOT$")), "the actual parameter must be substituted, never a literal fake slot");
        assertTrue(coin.lists.get("xfm_oracle_participants").isEmpty(), "real has-list branch clears the source list");
        Vm absent = vm(389472, 389470, true); absent.loadCalendarSource("xfm_oracle_samples.txt"); absent.loadCalendarValues("xfm_oracle_values.txt");
        Node noList = absent.global("xfm_coin_registry").getFirst();
        noList.put("xfm_oracle_bucket_day", 107).put("xfm_oracle_bucket_samples", 0).put("xfm_oracle_bucket_notional", 0)
                .put("xfm_oracle_bucket_lots", 0).put("xfm_qualified_volume_cents", 0);
        absent.exchange.put("xfm_day", 110); assertFalse(noList.lists.containsKey("xfm_oracle_participants"));
        absent.run("xfm_oracle_roll_coin_effect", noList, null);
        assertFalse(noList.lists.containsKey("xfm_oracle_participants"), "a missing source list does not become an existing empty list");
    }
    @Test void debtPrivateCollectionIsExplicitlyClearedOnBothSidesOfEveryRealTick() throws IOException {
        Path source = Path.of(System.getProperty("xfm.source"));
        var debt = FollowupFixtureTest.parse(Files.readString(source.resolve("common/scripted_effects/xfm_debt_daily.txt"))).block("xfm_debt_daily_effect");
        assertEquals("clear_variable_list", debt.entries().getFirst().key()); assertEquals("clear_variable_list", debt.entries().getLast().key());
        Vm v = vm(389472, 389470, true); v.loadCalendarSource("xfm_debt_daily.txt");
        // Explicitly isolate collection/reset semantics. Financial servicing and crisis
        // callbacks are boundary traces here; the full financial module remains required.
        v.calendarBoundaryHooks.addAll(List.of("xfm_debt_auto_service_effect", "xfm_debt_account_review_effect"));
        Node stale = v.account("stale", 99, v.player, 0); v.exchange.nodes("xfm_debt_accounts_this_tick").add(stale);
        Node claim = v.node("claim", "xfm_finance_claim", true).put("xfm_outstanding_cents", 500).put("xfm_due_day", 100).ref("xfm_debtor_account", v.privateAccount);
        v.global("xfm_debts_active").add(claim);
        v.run("xfm_debt_daily_effect", v.exchange, null);
        assertTrue(v.exchange.nodes("xfm_debt_accounts_this_tick").isEmpty()); assertEquals(8, claim.n("xfm_overdue_days"));
        assertEquals(1, v.calendarHookTrace.stream().filter("xfm_debt_account_review_effect"::equals).count());
        claim.put("xfm_outstanding_cents", 0); v.exchange.put("xfm_day", 109); v.calendarHookTrace.clear();
        v.run("xfm_debt_daily_effect", v.exchange, null);
        assertTrue(v.calendarHookTrace.isEmpty()); assertTrue(v.exchange.nodes("xfm_debt_accounts_this_tick").isEmpty());
        assertFalse(v.aliases.containsKey("xfm_debt_collecting_account"));
    }
}
