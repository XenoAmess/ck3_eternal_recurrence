package org.xar.ck3.control.application.battleadvance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Duration;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.*;
import org.xar.ck3.control.application.advance.AdvanceObservationPort.Frame;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;

/** Actual public cleanup pause over the original Life parent plan. Offline packets confer no live qualification. */
final class AdvanceClockCleanupTest {
    private static final Set<String> CAPS = Set.of(ClockStatusRead.ARM_CAP, ClockStatusRead.STATUS_CAP,
            ClockStatusRead.CANCEL_CAP, "game.state.pending-character-interaction");
    private static final Set<OperationKey> STEPS = Set.of(new OperationKey("set-speed-2"),
            new OperationKey("pause-map"), new OperationKey("resume-map"));
    private static Obj json(String value) { return object(org.xar.ck3.control.planning.opportunity.OpportunityJson.parse(value.getBytes(StandardCharsets.UTF_8)), "fixture"); }
    private static IntegerValue number(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
    private static Obj army(int id, int owner, boolean controlled) {
        return new Obj(Map.of("army_id",number(id),"owner_character_id",number(owner),"current_province_id",number(7),
                "move_target_province_id",Nil.INSTANCE,"in_combat",new Bool(false),"retreating",new Bool(false),
                "controllable",new Bool(controlled),"army_state",new Text("regular"),"army_state_code",number(1)));
    }
    private static Obj semantic(int revision, boolean paused) {
        Obj own = army(11,29829,true), ally = army(22,40000,false), enemy = army(33,50000,false);
        Obj hello = new Obj(Map.of("ck3_build_match",new Bool(true),"expected_ck3_version",new Text(ExactCk3Build.CK3_12004.version()),
                "expected_ck3_sha256",new Text(ExactCk3Build.CK3_12004.executableSha256())));
        return BattleAdvanceFixture.frame(revision,100,paused,false).semantic()
                .with("snapshot_id",new Text("native:"+revision)).with("speed",number(2)).with("one_life_terminal",new Bool(false))
                .with("local_player_id",number(0)).with("top_exclusive_modal_choice_hint",json("{\"status\":\"absent\",\"owner_verified\":true}"))
                .with("diagnostics",json("{\"bridge_pid\":123,\"connection_generation\":1,\"connected\":true}").with("hello",hello))
                .with("player_armies",new Arr(List.of(own))).with("active_wars",new Arr(List.of(new Obj(Map.of("war_id",number(1),
                        "allied_armies",new Arr(List.of(own,ally)),"enemy_armies",new Arr(List.of(enemy)))))));
    }
    private static Frame frame(Obj semantic) { return frame(semantic,BattleAdvanceFixture.SOURCE,"session-1"); }
    private static Frame frame(Obj semantic, G2Source source, String session) {
        var identity = new ObservationIdentity(source.machineId(),BattleAdvanceFixture.GAME,
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(
                        integer(object(semantic.get("played_character"),"played").get("character_id"),"actor"),
                        integer(semantic.get("native_revision"),"native"),integer(semantic.get("date_raw"),"date")),
                        text(semantic.get("snapshot_id"),"snapshot"),integer(semantic.get("revision"),"revision"),text(semantic.get("episode_run_id"),"episode")),1);
        var nativeRef = BattleAdvanceFixture.frame(integer(semantic.get("revision"),"revision").intValueExact(),100,true,false).originalEvidence();
        return new Frame(identity,source,session,semantic,new ObservationProvenance.Push(identity.frame().snapshotId(),
                identity.frame().identity().nativeRevision(),nativeRef),BattleAdvanceFixture.NOW.plusMillis(identity.frame().revision().longValueExact()),nativeRef);
    }
    private static ActionCommand parent() {
        Frame starting = frame(semantic(1,true));
        WarDailyWatch.Context context = WarDailyWatch.select(starting,true,true,"life-advance-one-day",Optional.empty(),CAPS,STEPS,false).orElseThrow();
        AdvancePlan plan = new AdvancePlan(BigInteger.valueOf(100),BigInteger.valueOf(124),1,2,WarDailyWatch.POLICY,true,
                AdvancePlan.ClockMode.EXACT_SENTINEL,Optional.empty(),Optional.of(context));
        return new ActionCommand("actual-watch-cleanup",starting.identity(),starting.source(),starting.sessionId(),new OperationKey("life-advance-one-day"),
                new Obj(Map.of(AdvancePlan.KEY,plan.json())),new ExpectedPostcondition(1,starting.identity(),starting.source(),AdvancePlan.OBSERVER,plan.expected()),
                new JointBudgetSelector.Claims(Set.of(BigInteger.valueOf(11),BigInteger.valueOf(22),BigInteger.valueOf(33)),Set.of(),Set.of(),Set.of()),
                BattleAdvanceFixture.NOW.plusSeconds(30));
    }
    private static AdvanceClock clock(BattleAdvanceFixture fixture) {
        var status = new ClockStatusRead(fixture,BattleAdvanceFixture.REF,fixture.archiveForTest());
        return new AdvanceClock(fixture,status,(command,frame) -> { throw new AssertionError("cleanup must not prepare or replan a clock"); },
                Clock.fixed(BattleAdvanceFixture.NOW,ZoneOffset.UTC),8,Duration.ofSeconds(2),Duration.ofSeconds(3));
    }
    @Test void frozenWatchRejectsChangedInitialActorEpisodeSpeedConnectionMapAndAuthorityBeforeAnyRead() {
        var rows = new ArrayList<Frame>();
        Obj normal = semantic(2,true);
        rows.add(frame(normal.with("played_character",json("{\"character_id\":29830,\"alive\":true}")).with("episode_character_id",number(29830))));
        rows.add(frame(normal.with("episode_run_id",new Text("another-episode"))));
        rows.add(frame(normal.with("speed",number(3))));
        rows.add(frame(normal.with("map_ready",new Bool(false))));
        rows.add(frame(normal.with("diagnostics",object(normal.get("diagnostics"),"diagnostics").with("connection_generation",number(2)))));
        rows.add(frame(normal,BattleAdvanceFixture.SOURCE,"another-session"));
        rows.add(frame(normal,new G2Source(BattleAdvanceFixture.SOURCE.machineId(),BattleAdvanceFixture.NOW.plusSeconds(1).toString(),"1.20.0.4",BattleAdvanceFixture.REF),"session-1"));
        for (Frame changed : rows) {
            var fixture = new BattleAdvanceFixture();
            assertThrows(IllegalArgumentException.class,() -> clock(fixture).pause(parent(),fixture,changed));
            assertEquals(0,fixture.frameReads); assertTrue(fixture.steps.isEmpty());
        }
    }
    @Test void actualFreshReadCannotMoveCleanupToAnotherOwnerAndAlreadyPausedSpeedDriftIsAlsoRefused() {
        var fixture = new BattleAdvanceFixture();
        fixture.frames.add(frame(semantic(3,false).with("episode_run_id",new Text("another-episode"))));
        assertThrows(IllegalArgumentException.class,() -> clock(fixture).pause(parent(),fixture,frame(semantic(2,false))));
        assertEquals(1,fixture.frameReads); assertTrue(fixture.steps.isEmpty());
        var paused = new BattleAdvanceFixture();
        paused.frames.add(frame(semantic(3,true).with("speed",number(3))));
        assertThrows(IllegalArgumentException.class,() -> clock(paused).pause(parent(),paused,frame(semantic(2,false))));
        assertEquals(1,paused.frameReads); assertTrue(paused.steps.isEmpty());
    }
    @Test void singleActualPauseRequiresPausedSameWatchPoststateAndNeverRetriesAnAcceptedRunningFrame() {
        var fixture = new BattleAdvanceFixture();
        Frame before = frame(semantic(2,false));
        Frame after = frame(semantic(3,true).with("active_event",json("{\"instance_id\":\"actual-new-event\",\"option_count\":2}")));
        fixture.frames.add(before); fixture.frames.add(after);
        Frame result = clock(fixture).pause(parent(),fixture,before);
        assertEquals(after,result); assertEquals(List.of("pause-map"),fixture.steps);
        assertEquals(before.identity(),fixture.children.getFirst().command().before());
        assertEquals(parent().claims(),fixture.children.getFirst().command().claims());
        var running = new BattleAdvanceFixture();
        running.frames.add(before); running.frames.add(frame(semantic(3,false)));
        assertThrows(IllegalArgumentException.class,() -> clock(running).pause(parent(),running,before));
        assertEquals(List.of("pause-map"),running.steps); assertEquals(2,running.frameReads);
        var drift = new BattleAdvanceFixture();
        drift.frames.add(before); drift.frames.add(frame(semantic(3,true).with("speed",number(3))));
        assertThrows(IllegalArgumentException.class,() -> clock(drift).pause(parent(),drift,before));
        assertEquals(List.of("pause-map"),drift.steps);
    }
    @Test void definitiveMapRejectionWaitCannotReturnPausedDriftOrAuthorizeAnotherPause() {
        var fixture = new BattleAdvanceFixture(); var rejected = new MapRejectedChildren();
        Frame before = frame(semantic(2,false));
        fixture.frames.add(before); fixture.frames.add(before); fixture.frames.add(frame(semantic(3,true).with("speed",number(3))));
        assertThrows(IllegalArgumentException.class,() -> clock(fixture).pause(parent(),rejected,before));
        assertEquals(1,rejected.receipts.size()); assertEquals(3,fixture.frameReads);
    }
    @Test void unresolvedOriginalChildForbidsEvenCleanupReadsAndNonLifeCallersNeedNoLifePlan() {
        var fixture = new BattleAdvanceFixture(); var parent = parent(); Frame before = frame(semantic(2,false));
        fixture.unknownStep = "resume-map";
        fixture.submit(AdvancePrimitives.child(parent,before,"actual-unknown-resume","resume-map",parent.deadline()));
        for (int attempt=0;attempt<2;attempt++) assertThrows(IllegalArgumentException.class,() -> clock(fixture).pause(parent,fixture,before));
        assertEquals(List.of("resume-map"),fixture.steps); assertEquals(0,fixture.frameReads);
        var other = new BattleAdvanceFixture();
        var nonLife = new ActionCommand(parent.actionId(),parent.before(),parent.source(),parent.sessionId(),new OperationKey("committed-route-sentinel-advance"),
                new Obj(Map.of()),parent.expected(),parent.claims(),parent.deadline());
        Frame running = frame(semantic(2,false).with("speed",number(3))), paused = frame(semantic(3,true).with("speed",number(3)));
        other.frames.add(paused);
        assertEquals(paused,clock(other).pause(nonLife,other,running)); assertTrue(other.steps.isEmpty());
    }
    private static final class MapRejectedChildren implements CompositeActionPort.Children {
        final List<ActionReceipt> receipts = new ArrayList<>();
        @Override public String nextActionId() { return "definitive-pause-"+receipts.size(); }
        @Override public List<ActionReceipt> completed() { return List.copyOf(receipts); }
        @Override public ActionReceipt submit(ActionCommand command) {
            var guard = new GuardEvidence(command.before(),command.source(),command.sessionId(),BigInteger.ONE,command.operation(),
                    BattleAdvanceFixture.REF,BattleAdvanceFixture.REF,"fixture-authority",BattleAdvanceFixture.NOW,command.deadline());
            var attempt = new ActionState.Attempt("request-"+command.actionId(),BattleAdvanceFixture.NOW,guard,AdvancePrimitives.prepareRequest(command));
            var raw = new RawJson("{\"error\":\"CK3 map state is unavailable\"}".getBytes(StandardCharsets.UTF_8));
            var ack = new NativeActionPort.AckReceived(attempt.requestId(),false,Optional.empty(),raw,new byte[]{1});
            var rejected = new ActionState.Rejected(attempt.requestId(),"CK3 map state is unavailable",BattleAdvanceFixture.REF);
            var receipt = new ActionReceipt(1,receipts.size()+1,command,ActionCodec.bodySha256(command),new ActionState.Settled(attempt,ack,rejected));
            receipts.add(receipt); return receipt;
        }
    }
}
