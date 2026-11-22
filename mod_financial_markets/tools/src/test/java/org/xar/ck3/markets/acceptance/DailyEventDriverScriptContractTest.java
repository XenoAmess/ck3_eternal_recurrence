package org.xar.ck3.markets.acceptance;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.markets.acceptance.FollowupContracts.*;
import org.xar.ck3.markets.acceptance.MarketEvolutionScriptContractTest.Vm;

/** Real source AST over the existing bounded VM. The deferred queue below is an
 * explicit software boundary, not a model of CK3 scheduling or a native ABI.
 * Daily module calls remain the existing ordered boundary traces, never fills,
 * payments, fake Game dispatches or historical observation samples. */
final class DailyEventDriverScriptContractTest {
    private static final String SCHEDULE = "xfm_finance_daily_event_schedule_effect";
    private static Vm vm() throws IOException {
        Request r = new Request(2, Profile.MARKET_EVOLUTION, 1,
                new ActorBinding(ActorMode.CURRENT_PLAYER, null),
                new Targets("2", "1", null, null, null, null), null, null);
        Vm v = new Vm(r); v.loadCalendarDispatch(); v.loadDailyEventDriver();
        v.scriptDateOverride = 100L;
        v.exchange.put("xfm_last_date", 100).put("xfm_day", 10)
                .put("xfm_calendar_protocol", 1).put("xfm_a0_migration_scanned", 1);
        return v;
    }
    @Test void legacyExchangeInstallsOnlyOneFutureAppointmentWithoutChangingFinancialDay() throws IOException {
        Vm v = vm(); v.run(SCHEDULE, v.exchange, null); v.run(SCHEDULE, v.exchange, null);
        assertEquals(1, v.delayedDailyActions.size());
        assertEquals(101, v.delayedDailyActions.getFirst().dueDate());
        assertEquals(1, v.exchange.n("xfm_daily_event_generation"));
        assertEquals(10, v.exchange.n("xfm_day")); assertTrue(v.calendarHookTrace.isEmpty());
    }
    @Test void delayedRealEntryCoversAProvidedDateWhenStoryEntryWasNotCalled() throws IOException {
        Vm v = vm(); v.run(SCHEDULE, v.exchange, null); var event = v.delayedDailyActions.getFirst();
        v.scriptDateOverride = 101L; v.deliverDailyEvent(event);
        assertEquals(11, v.exchange.n("xfm_day")); assertEquals(101, v.exchange.n("xfm_last_date"));
        assertEquals(List.of(101L), v.calendarDueDates); assertEquals(List.of(0L), v.calendarRecoveryModes);
        assertEquals(1, v.calendarObservedTails); assertEquals(1, v.delayedDailyActions.size());
        assertFalse(v.exchange.vars.containsKey("xfm_daily_raw_attempt_count"), "event delivery cannot impersonate a Story timer entry");
        assertEquals(102, v.delayedDailyActions.getFirst().dueDate());
    }
    @Test void storyFirstOrEventFirstBothRetainTheOriginalOncePerDateAdmission() throws IOException {
        for (boolean eventFirst : List.of(false, true)) {
            Vm v = vm(); v.run(SCHEDULE, v.exchange, null); var event = v.delayedDailyActions.getFirst();
            v.scriptDateOverride = 101L;
            if (eventFirst) { v.deliverDailyEvent(event); v.calendarCallback(); }
            else { v.calendarCallback(); v.deliverDailyEvent(event); }
            assertEquals(11, v.exchange.n("xfm_day")); assertEquals(List.of(101L), v.calendarDueDates);
            assertEquals(1, v.calendarObservedTails); assertEquals(1, v.delayedDailyActions.size());
        }
    }
    @Test void duplicateCapturedCallbackCannotRepeatBusinessOrGrowTheCurrentChain() throws IOException {
        Vm v = vm(); v.run(SCHEDULE, v.exchange, null); var first = v.delayedDailyActions.getFirst();
        v.scriptDateOverride = 101L; v.deliverDailyEvent(first); long generation = v.exchange.n("xfm_daily_event_generation");
        v.deliverDailyEvent(first); // Explicit duplicate software input, never a Game replay.
        assertEquals(11, v.exchange.n("xfm_day")); assertEquals(1, v.calendarDueDates.size());
        assertEquals(generation, v.exchange.n("xfm_daily_event_generation")); assertEquals(1, v.delayedDailyActions.size());
    }
    @Test void changedOwnerReplacesTheAppointmentAndOldCapturedOwnerCannotDispatchOrRequeue() throws IOException {
        Vm v = vm(); v.run(SCHEDULE, v.exchange, null); var old = v.delayedDailyActions.getFirst();
        v.exchange.owner = v.character("new-custodian", true); v.run(SCHEDULE, v.exchange, null);
        assertEquals(2, v.delayedDailyActions.size()); var current = v.delayedDailyActions.getLast();
        v.scriptDateOverride = 101L; v.deliverDailyEvent(old);
        assertEquals(10, v.exchange.n("xfm_day")); assertTrue(v.calendarHookTrace.isEmpty());
        assertEquals(1, v.delayedDailyActions.size()); v.deliverDailyEvent(current);
        assertEquals(11, v.exchange.n("xfm_day")); assertEquals(1, v.calendarDueDates.size());
    }
    @Test void lateDeliveryRetainsRealRecoveryAndDoesNotManufactureAnOldQaSample() throws IOException {
        Vm v = vm(); v.run(SCHEDULE, v.exchange, null); var event = v.delayedDailyActions.getFirst();
        v.scriptDateOverride = 102L; v.deliverDailyEvent(event);
        assertEquals(List.of(101L, 102L), v.calendarDueDates);
        assertEquals(List.of(1L, 0L), v.calendarRecoveryModes); assertEquals(1, v.calendarObservedTails);
        assertEquals(12, v.exchange.n("xfm_day")); assertEquals(1, v.delayedDailyActions.size());
    }
    @Test void absentOrDeadOwnerAndSaturatedGenerationNeverCreateAnUnboundedQueue() throws IOException {
        Vm missing = vm(); missing.exchange.owner = null; missing.run(SCHEDULE, missing.exchange, null);
        assertTrue(missing.delayedDailyActions.isEmpty());
        Vm dead = vm(); dead.player.alive = false; dead.run(SCHEDULE, dead.exchange, null);
        assertTrue(dead.delayedDailyActions.isEmpty());
        Vm full = vm(); full.exchange.put("xfm_daily_event_generation", 1000000000); full.run(SCHEDULE, full.exchange, null);
        assertTrue(full.delayedDailyActions.isEmpty()); assertEquals(1000000000, full.exchange.n("xfm_daily_event_generation"));
    }
    @Test void unknownOrInflightCalendarCannotBeReplayedByTheSecondEntry() throws IOException {
        for (String kind : List.of("protocol", "inflight")) {
            Vm v = vm(); v.run(SCHEDULE, v.exchange, null); var event = v.delayedDailyActions.getFirst();
            if (kind.equals("protocol")) v.exchange.put("xfm_calendar_protocol", 2);
            else v.exchange.put("xfm_calendar_in_flight", 1);
            v.scriptDateOverride = 101L; v.deliverDailyEvent(event);
            assertEquals(10, v.exchange.n("xfm_day")); assertTrue(v.calendarHookTrace.isEmpty());
        }
    }
    @Test void restoredFutureAppointmentFieldsRebindOnLoadWithoutChangingTheFinancialCursor() throws IOException {
        Vm v = vm();
        // Model only the retained ledger fields. Actual CK3 queued-event SAVE
        // serialization is explicitly outside this NoGame source contract.
        v.exchange.put("xfm_daily_event_generation", 42).put("xfm_daily_event_due_date", 101)
                .ref("xfm_daily_event_owner", v.player);
        v.run("xfm_finance_daily_event_reload_effect", v.exchange, null);
        assertEquals(1, v.delayedDailyActions.size()); assertEquals(43, v.exchange.n("xfm_daily_event_generation"));
        assertEquals(101, v.delayedDailyActions.getFirst().dueDate());
        assertEquals(10, v.exchange.n("xfm_day")); assertEquals(100, v.exchange.n("xfm_last_date"));
    }
    @Test void expiredCapturedAppointmentCannotDispatchAfterAReplacementOnTheSameOwner() throws IOException {
        Vm v = vm(); v.run(SCHEDULE, v.exchange, null); var expired = v.delayedDailyActions.getFirst();
        v.scriptDateOverride = 102L; v.run(SCHEDULE, v.exchange, null);
        assertEquals(2, v.exchange.n("xfm_daily_event_generation"));
        v.deliverDailyEvent(expired);
        assertEquals(10, v.exchange.n("xfm_day")); assertTrue(v.calendarHookTrace.isEmpty());
        assertEquals(1, v.delayedDailyActions.size()); assertEquals(103, v.delayedDailyActions.getFirst().dueDate());
    }
    @Test void currentMarketReadGateIsPureAndNormalSyncUsesTheSameActualCalendar() throws IOException {
        Vm v = vm(); var current = v.program.get("xfm_finance_current_date_trigger");
        assertTrue(v.matches(current, v.player, null)); v.scriptDateOverride = 101L;
        assertFalse(v.matches(current, v.player, null)); assertEquals(10, v.exchange.n("xfm_day"));
        v.run("xfm_finance_sync_current_effect", v.player, null);
        assertTrue(v.matches(current, v.player, null)); assertEquals(11, v.exchange.n("xfm_day"));
        v.exchange.put("xfm_calendar_in_flight", 1); assertFalse(v.matches(current, v.player, null));
        v.exchange.put("xfm_calendar_in_flight", 0).put("xfm_calendar_protocol", 2);
        assertFalse(v.matches(current, v.player, null));
        String pages = Files.readString(Path.of(System.getProperty("xfm.source")).resolve("common/scripted_effects/xfm_market_ui_pages.txt"));
        var refresh = FollowupFixtureTest.parse(pages).block("xfm_market_ui_refresh_effect");
        assertEquals("xfm_finance_sync_current_effect", refresh.entries().getFirst().key());
    }
}
