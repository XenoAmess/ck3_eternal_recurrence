package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.CurrentTedActorTransition;
import org.xar.ck3.control.nativebridge.CurrentTedActorTransitionSource;
import org.xar.ck3.control.nativebridge.CurrentTedActorTransitionResult;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Typed Java DATA boundaries only. No C++ positive packet, runtime permission or saved result is manufactured. */
final class NativeOwnerCurrentTedTransitionSelectionTest {
    private static ObjectNode config(boolean transition) {
        var n=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v38").put("mode",transition?"current_ted_two_day_known_transition":"current_ted_query_role")
                .put("overall_timeout_seconds",180).put("read_timeout_seconds",60).put("maximum_frames_per_operation",128);
        n.putObject("owner_descriptor").put("path","D:/ted-Main-Java-DATA/owner.json").put("bytes",1).put("sha256","0".repeat(64));
        if(transition)n.put("maximum_status_polls",128).put("status_poll_delay_ms",500);return n;
    }
    private static CoreFrame.Prefix core(int date,int actor){return new CoreFrame.Prefix(date,1,true,0,true,true,actor,true);}
    private static CurrentTedActorTransitionSource song(boolean shown,boolean admissible) {
        return new CurrentTedActorTransitionSource(CurrentTedActorTransitionSource.Role.SONG,true,Optional.of(shown),BigInteger.ZERO,Optional.of(42),Optional.empty(),Optional.empty(),true,true,admissible,false);
    }
    private static CurrentTedActorTransitionSource recipient(BigInteger epoch) {
        return new CurrentTedActorTransitionSource(CurrentTedActorTransitionSource.Role.RECIPIENT,true,Optional.of(true),epoch,Optional.of(42),Optional.of(77),Optional.empty(),true,true,true,false);
    }
    private static CurrentTedActorTransitionResult role(CurrentTedActorTransitionSource source,int date,int actor) {
        return new CurrentTedActorTransitionResult(CurrentTedActorTransition.Action.QUERY_ROLE,"role-DATA","",CurrentTedActorTransitionResult.Status.AVAILABLE,true,false,
                BigInteger.ONE,BigInteger.TWO,BigInteger.ZERO,source.actorEpoch(),100000,BigInteger.ONE,BigInteger.TWO,BigInteger.valueOf(3),4,
                Optional.of(core(date,actor)),Optional.of(source),Optional.empty(),false,false,true,Optional.empty());
    }
    private static CurrentTedActorTransitionResult day(boolean pending,int before,int after,BigInteger epoch) {
        var progress=new CurrentTedActorTransitionResult.Progress(BigInteger.valueOf(9),1000,1024,1024,before,after,1,0,0,true,true,true,true,pending,true,false,false);
        return new CurrentTedActorTransitionResult(CurrentTedActorTransition.Action.QUERY_OPERATION,"status-DATA","op-DATA",
                pending?CurrentTedActorTransitionResult.Status.TRANSITION_PENDING:CurrentTedActorTransitionResult.Status.COMPLETED_DAY,true,true,
                BigInteger.ONE,BigInteger.TWO,BigInteger.ONE,epoch,100000,BigInteger.ONE,BigInteger.valueOf(5),BigInteger.valueOf(6),4,
                Optional.of(core(1000,before)),Optional.empty(),Optional.of(progress),true,true,true,Optional.empty());
    }
    @Test void explicitTwoModesHaveOnlyTheirOwnFiniteSubmissionBudgets()throws IOException {
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_TED,NativeOwnerSnapshotMain268.observationMode(config(false)));
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_TED,NativeOwnerSnapshotMain268.observationMode(config(true)));
        assertFalse(NativeOwnerSnapshotMain268.currentTedConfig(config(false)).transition());assertEquals(2,NativeOwnerSnapshotMain268.currentTedConfig(config(false)).submissions());
        assertEquals(266,NativeOwnerSnapshotMain268.currentTedConfig(config(true)).submissions());
        assertEquals(522,NativeOwnerSnapshotMain268.currentTedConfig(config(true).put("maximum_status_polls",256)).submissions());
        for(String mode:List.of("current_ted_advance_day","current_ted_confirm_epoch","current_ted_query_operation","current_ted_two_day_known_transition ","current_ted_two_days"))assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config(false).put("mode",mode)));
    }
    @Test void onlyCompositeRequiresStrictBoundedPollingWithoutV17Alias()throws IOException {
        for(var n:List.of(config(true).put("maximum_status_polls",0),config(true).put("maximum_status_polls",257),config(true).put("maximum_status_polls",true),config(true).put("status_poll_delay_ms",0),config(true).put("status_poll_delay_ms",1001),config(true).put("status_poll_delay_ms",1.5)))assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));
        for(String field:List.of("maximum_status_polls","status_poll_delay_ms")) {
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config(false).put(field,1)));
            var missing=config(true);missing.remove(field);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(missing));
        }
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config(true).put("status_poll_interval_ms",500)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config(true).put("max_status_polls",128)));
    }
    @Test void exactOwnerPinAndCommonIntegerBoundsCannotBeBypassed()throws IOException {
        var bad=config(false);((ObjectNode)bad.get("owner_descriptor")).put("bytes",true);
        for(var n:List.of(bad,config(false).put("owner_descriptor","D:/owner.json"),config(false).put("overall_timeout_seconds",601),config(false).put("overall_timeout_seconds",0),config(false).put("read_timeout_seconds",61),config(false).put("maximum_frames_per_operation",0)))assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));
        for(String field:List.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation")){var missing=config(false);missing.remove(field);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(missing));}
    }
    @Test void callerCannotChooseActorsEpochsDaysSpeedKeysOrOperationAuthority()throws IOException {
        for(String field:List.of("days","speed","actor","song_actor_id","recipient_actor_id","role","role_key","actor_epoch","epoch","operation_id","request_id","provider_generation","query_sequence","claim_sequence","deadline","expected_core","source","admissible","retry","checkpoint_archive_path","phase"))assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config(true).put(field,1)),field);
    }
    @Test void oldV37ModeRemainsIndependentAndCannotBorrowTEDPolling()throws IOException {
        var old=config(false).put("schema","xar.native-owner-snapshot-config/v37").put("mode","current_lyd_query_events");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_LYD,NativeOwnerSnapshotMain268.observationMode(old));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(old.deepCopy().put("status_poll_delay_ms",500)));
        for(int v=24;v<=37;v++){final int version=v;assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config(true).put("schema","xar.native-owner-snapshot-config/v"+version)));}
    }
    @Test void positiveRoleRequiresActualShownAndExactSourceIDs()throws IOException {
        var actual=role(song(true,true),1000,42);NativeOwnerSnapshotMain268.requireCurrentTedRole(actual,core(1000,42));
        NativeOwnerSnapshotMain268.requireCurrentTedPositiveRole(actual,core(1000,42),CurrentTedActorTransitionSource.Role.SONG,BigInteger.ZERO,42,-1,false);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentTedPositiveRole(actual,core(1000,42),CurrentTedActorTransitionSource.Role.SONG,BigInteger.ZERO,43,-1,false));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentTedRole(actual,core(1024,42)));
        var rec=role(recipient(BigInteger.ONE),1024,77);NativeOwnerSnapshotMain268.requireCurrentTedPositiveRole(rec,core(1024,77),CurrentTedActorTransitionSource.Role.RECIPIENT,BigInteger.ONE,42,77,false);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentTedPositiveRole(rec,core(1024,77),CurrentTedActorTransitionSource.Role.RECIPIENT,BigInteger.ZERO,42,77,false));
    }
    @Test void ReadonlyAvailableOrShownDoesNotGrantAdvanceOrEpochConfirmation()throws IOException {
        var hidden=role(song(false,false),1000,42);NativeOwnerSnapshotMain268.requireCurrentTedRole(hidden,core(1000,42));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentTedPositiveRole(hidden,core(1000,42),CurrentTedActorTransitionSource.Role.SONG,BigInteger.ZERO,42,-1,false));
        var notAdmitted=role(song(true,false),1000,42);assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentTedPositiveRole(notAdmitted,core(1000,42),CurrentTedActorTransitionSource.Role.SONG,BigInteger.ZERO,42,-1,false));
        var rec=role(recipient(BigInteger.ONE),1024,77);assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentTedPositiveRole(rec,core(1024,77),CurrentTedActorTransitionSource.Role.RECIPIENT,BigInteger.ONE,42,77,true));
    }
    @Test void dayOneMustBeExactKnownActorTransitionPendingRatherThanSameActorCompletion()throws IOException {
        var pending=day(true,42,77,BigInteger.ZERO);NativeOwnerSnapshotMain268.requireCurrentTedDayTerminal(pending,core(1000,42),"op-DATA",1024,true);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentTedDayTerminal(day(false,42,42,BigInteger.ZERO),core(1000,42),"op-DATA",1024,true));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentTedDayTerminal(pending,core(1000,42),"another-op",1024,true));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentTedDayTerminal(pending,core(1000,42),"op-DATA",1048,true));
    }
    @Test void dayTwoRequiresFinalEpochTwoAndNeverCreditsUnknownOrTransitionPending()throws IOException {
        var completed=day(false,77,77,BigInteger.TWO);NativeOwnerSnapshotMain268.requireCurrentTedDayTerminal(completed,core(1000,77),"op-DATA",1024,false);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentTedDayTerminal(day(false,77,77,BigInteger.ONE),core(1000,77),"op-DATA",1024,false));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentTedDayTerminal(day(true,42,77,BigInteger.ZERO),core(1000,42),"op-DATA",1024,false));
        var unknown=new CurrentTedActorTransitionResult(CurrentTedActorTransition.Action.QUERY_OPERATION,"status-DATA","op-DATA",CurrentTedActorTransitionResult.Status.INDETERMINATE,false,false,
                BigInteger.ONE,BigInteger.TWO,BigInteger.ZERO,BigInteger.ZERO,100000,BigInteger.ZERO,BigInteger.ZERO,BigInteger.ZERO,0,Optional.empty(),Optional.empty(),Optional.empty(),false,false,false,Optional.of("Java DATA unknown"));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentTedDayTerminal(unknown,core(1000,77),"op-DATA",1024,false));
    }
    @Test void IndependentAfterCoreExpectationPreservesEveryPrefixFieldAndSignedActor()throws IOException {
        var start=core(1000,42);assertEquals(core(1024,77),NativeOwnerSnapshotMain268.currentTedAfter(start,1024,77));
        assertEquals(0,NativeOwnerSnapshotMain268.currentTedAfter(start,1024,0).playedCharacterId());
        assertEquals(-2,NativeOwnerSnapshotMain268.currentTedAfter(start,1024,-2).playedCharacterId());
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.currentTedAfter(start,1024,-1));assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.currentTedAfter(start,1048,77));
    }
}
