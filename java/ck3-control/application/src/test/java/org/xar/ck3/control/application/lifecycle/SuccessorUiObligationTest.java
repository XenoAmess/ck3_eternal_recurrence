package org.xar.ck3.control.application.lifecycle;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.LifecycleIdentity;
import org.xar.ck3.control.application.lifecycle.SuccessorUiObligation.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;

/** Pure deterministic producer -> sole codec -> reducer consumers. These fixtures grant no Root/M3/native authority. */
final class SuccessorUiObligationTest {
    private static final Instant AT=Instant.parse("2026-10-24T00:00:00Z");
    private static final BigInteger HIGH=new BigInteger("18446744073709551615");
    private static ExactRef ref(String name){return new ExactRef("D:/synthetic-pending-ui/"+name,11,"a".repeat(64));}
    private static Binding binding(){var game=new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001")));var old=new LifecycleIdentity("synthetic-ui-machine",game,"session",BigInteger.ONE,new LifecycleIdentity.Subject(BigInteger.valueOf(10),"old-run",1,2),new LifecycleIdentity.Frame("old",HIGH,BigInteger.TEN,BigInteger.valueOf(100),true,true),new LifecycleIdentity.Character(BigInteger.valueOf(20),true),LifecycleIdentity.TerminalReason.CHANGED,new LifecycleIdentity.Evidence(ref("native"),ref("hello"),ref("manifest"),ref("driver"),ref("source")),AT);return new Binding(old,BigInteger.valueOf(20),"new-run","b".repeat(64),"c".repeat(64),"parent","d".repeat(64),ref("parent"),ref("preclock"),ref("cause"),AT);}
    private static UiFrame frame(int date){var b=binding();return new UiFrame(b.predecessor().machineId(),b.predecessor().game(),"session",BigInteger.ONE,b.sourceEpochSha256(),"current-"+date,HIGH,BigInteger.valueOf(date),BigInteger.valueOf(date),b.successorCharacterId(),b.successorEpisodeRunId(),2,3,ref("native-"+date),ref("sem-"+date),ref("driver-"+date),Optional.of(ref("qualified")),AT.plusSeconds(date));}
    private static Observation observation(UiState state,int date,int sequence){return new Observation(frame(date),state,BigInteger.valueOf(sequence),BigInteger.valueOf(sequence),ref("query-"+sequence),ref("raw-"+sequence),Optional.empty(),Optional.empty());}
    private static SuccessorUiObligation observed(){return SuccessorUiObligationReducer.observe(SuccessorUiObligationReducer.pending(binding()),observation(UiState.CLOSE_REQUIRED,100,1));}
    private static SuccessorUiObligation entered(){var before=observed();return SuccessorUiObligationReducer.enterClose(before,new CloseAttempt("close","e".repeat(64),ref("close-command"),before.observation().orElseThrow().frame(),AT.plusSeconds(101),Optional.empty()));}
    private static SuccessorUiObligation roundtrip(SuccessorUiObligation v){var decoded=SuccessorUiObligationCodec.decode(SuccessorUiObligationCodec.encode(v));assertEquals(v,decoded);return decoded;}
    @Test void dataProducerAndCodecPreserveExactRevisionAndClosedFields(){var state=roundtrip(observed());assertEquals(HIGH,state.observation().orElseThrow().frame().revision());assertTrue(state.blocksOrdinaryActionsAndSave());var json=SuccessorUiObligationCodec.toJson(state);json.put("extra",true);assertThrows(IllegalArgumentException.class,()->SuccessorUiObligationCodec.fromJson(json));var missing=SuccessorUiObligationCodec.toJson(state);missing.remove("rebind");assertThrows(IllegalArgumentException.class,()->SuccessorUiObligationCodec.fromJson(missing));}
    @Test void onceIntentSurvivesUnknownRoundtripAndCannotResubmit(){var entered=roundtrip(entered());assertFalse(entered.closeCanBeConsidered());var unknown=roundtrip(SuccessorUiObligationReducer.retainCloseReceipt(entered,new CloseReceipt(ActionReceipt.Outcome.UNRESOLVED,ref("unknown"),Optional.empty(),Optional.empty(),Optional.empty())));assertThrows(IllegalArgumentException.class,()->SuccessorUiObligationReducer.enterClose(unknown,entered.closeAttempt().orElseThrow()));assertThrows(IllegalArgumentException.class,()->new CloseReceipt(ActionReceipt.Outcome.UNRESOLVED,ref("unknown"),Optional.of(ref("clear")),Optional.empty(),Optional.empty()));assertTrue(unknown.blocksOrdinaryActionsAndSave());}
    @Test void readOnlyReconciliationPreservesOriginalAndRequiresMaterialDateForFinalization(){var unknown=SuccessorUiObligationReducer.retainCloseReceipt(entered(),new CloseReceipt(ActionReceipt.Outcome.UNRESOLVED,ref("unknown"),Optional.empty(),Optional.empty(),Optional.empty()));var reconciled=roundtrip(SuccessorUiObligationReducer.retainVerifiedReconciliation(unknown,new ReadOnlyReconciliation(ref("unknown"),ref("confirmed"),ref("same-action"),Optional.of(ref("clear")),Optional.of(ref("date")))));assertEquals(ref("unknown"),reconciled.closeAttempt().orElseThrow().receipt().orElseThrow().canonicalReceipt());var clear=SuccessorUiObligationReducer.observe(reconciled,observation(UiState.CLEAR,101,2));var done=roundtrip(SuccessorUiObligationReducer.finalizeVerified(clear,new Finalization(binding().causeDigest(),ref("actual-final-m3"),frame(101),Optional.of(ref("confirmed")),Optional.of(ref("date")),AT.plusSeconds(102))));assertFalse(done.blocksOrdinaryActionsAndSave());assertFalse(done.closeCanBeConsidered());}
    @Test void alreadyClearDoesNotInventCloseOrDays(){var clear=SuccessorUiObligationReducer.observe(SuccessorUiObligationReducer.pending(binding()),observation(UiState.CLEAR,100,1));var done=roundtrip(SuccessorUiObligationReducer.finalizeVerified(clear,new Finalization(binding().causeDigest(),ref("actual-final-m3"),frame(100),Optional.empty(),Optional.empty(),AT.plusSeconds(101))));assertTrue(done.closeAttempt().isEmpty());assertThrows(IllegalArgumentException.class,()->SuccessorUiObligationReducer.observe(clear,observation(UiState.CLEAR,100,1)));}
    @Test void actualPendingProjectionPreservesGoalAndUsesSoleCacheResetWithoutFinalContinuedCredit() {
        var b=binding();var lifecycle=LifecycleJson.row().put("schema","xar.ck3.succession-lifecycle-binding/v1").put("lifecycle","ordinary_campaign_succession")
                .put("xar_enabled","xar_on").put("pact_contract","synthetic").put("source","synthetic-source").put("environment_sha256","a".repeat(64));
        var goal=new org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Value("{\"original_goal\":true}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        var nil=new org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.NullValue();
        var old=new org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Complete(new org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Session("pipe",123,java.math.BigInteger.TEN,"old-run"),java.util.List.of(),nil,nil,nil,nil,
                new org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Value(LifecycleJson.bytes(lifecycle)),goal,new org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Value(new byte[]{'[',']'}));
        var state=LifecycleJson.row().put("snapshot_id","old").put("revision",HIGH).put("native_revision",10).put("episode_run_id","old-run").put("date_raw",100).put("paused",true).put("map_ready",true).put("one_life_terminal_reason","played_character_changed");
        state.putObject("played_character").put("character_id",20).put("alive",true);state.putNull("succession_reconciliation");state.putNull("one_life_settlement");
        var envelope=LifecycleJson.row().put("type","state_snapshot").put("protocol_version",1).put("snapshot_id","old").put("revision",10);envelope.set("state",state);
        byte[] json=LifecycleJson.bytes(envelope),packet=java.nio.ByteBuffer.allocate(json.length+4).order(java.nio.ByteOrder.LITTLE_ENDIAN).putInt(json.length).put(json).array();
        var original=new ExactRef("D:/synthetic-pending-ui/actual-packet",packet.length,LifecycleJson.sha(packet));
        var actual=new org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame(new org.xar.ck3.control.application.action.NativeObservationPort.TransportSession(b.predecessor().machineId(),b.predecessor().game(),java.math.BigInteger.ONE,"session"),"old",java.math.BigInteger.TEN,new org.xar.ck3.control.application.action.RawJson(LifecycleJson.bytes(state)),packet,AT);
        var known=new org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known(old,new org.xar.ck3.control.application.driver.DriverSnapshotFacts.Stamp(b.predecessor().subject().driverVersion(),b.predecessor().subject().episodeEpoch(),b.predecessor().game(),"old-run",LifecycleJson.sha(old.encode())),ref("history"),java.util.List.of(),
                new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(java.util.Map.of("historical",new org.xar.ck3.control.planning.opportunity.OpportunityJson.Text("retained"))),Optional.empty(),Optional.empty());
        var source=new org.xar.ck3.control.g2.common.G2Source(b.predecessor().machineId(),AT.toString(),"synthetic-build",ref("source"));
        var snapshot=new LifecycleObservationPort.Snapshot(actual,source,org.xar.ck3.control.planning.opportunity.OpportunityJson.object(LifecycleJson.immutable(state),"synthetic terminal"),known,original);
        var identity=new LifecycleIdentity(b.predecessor().machineId(),b.predecessor().game(),"session",java.math.BigInteger.ONE,b.predecessor().subject(),b.predecessor().frame(),b.predecessor().currentPlayer(),LifecycleIdentity.TerminalReason.CHANGED,new LifecycleIdentity.Evidence(original,ref("hello"),ref("manifest"),ref("driver"),ref("source")),AT);
        var bound=new Binding(identity,b.successorCharacterId(),b.successorEpisodeRunId(),b.sourceEpochSha256(),b.causeDigest(),b.parentActionId(),b.parentBodySha256(),b.originalParentCommand(),b.preclockDocument(),b.qualifiedCause(),AT);
        var pending=SuccessorUiObligationReducer.pendingEpisode(snapshot,bound);
        assertSame(goal,pending.driver().campaignGoal());assertEquals(java.math.BigInteger.valueOf(20),pending.driver().session().actorId());assertEquals("new-run",pending.driver().session().episodeRunId());
        assertEquals(new org.xar.ck3.control.planning.opportunity.OpportunityJson.Text("retained"),pending.auxiliary().get("historical"));
        assertEquals(org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil.INSTANCE,pending.auxiliary().get("active_combat_retreat_token"));
        assertEquals(new org.xar.ck3.control.planning.opportunity.OpportunityJson.Text("successor_ui_pending"),pending.auxiliary().get("episode_binding_state"));
        assertTrue(roundtrip(pending.obligation()).blocksOrdinaryActionsAndSave());assertFalse(pending.auxiliary().members().containsKey("scored_terminal"));
        var restored=org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.decodeComplete(pending.driver().encode());
        assertArrayEquals(goal.json(),((org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Value)restored.campaignGoal()).json());assertTrue(known.driver().session().episodeRunId().equals("old-run"));
        var published=new org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known(pending.driver(),
                new org.xar.ck3.control.application.driver.DriverSnapshotFacts.Stamp(known.stamp().driverVersion()+1,known.stamp().episodeEpoch()+1,b.predecessor().game(),bound.successorEpisodeRunId(),LifecycleJson.sha(pending.driver().encode())),
                ref("actual-empty-pending-history"),java.util.List.of(),pending.auxiliary(),Optional.empty(),Optional.empty());
        var originalKnown=org.xar.ck3.control.application.driver.DriverSnapshotFacts.encodeKnownOriginal(published);
        var reopened=org.xar.ck3.control.application.driver.DriverSnapshotFacts.decodeKnownOriginal(
                org.xar.ck3.control.application.driver.DriverSnapshotFacts.originalKnownJson(originalKnown.bytes()),Optional.empty());
        var actualRebind=Rebind.unobserved(bound,reconnectFrame("fresh-domain",2),ref("canonical-pending-obligation"),ref("actual-private-proof"));
        var pure=org.xar.ck3.control.application.driver.DriverPendingEpisodeMutations.project(reopened,pending.obligation(),
                new org.xar.ck3.control.application.driver.DriverPendingEpisodeSource.Rebind(actualRebind));
        assertArrayEquals(pending.driver().encode(),pure.driver().encode());assertTrue(pure.result().isEmpty());
        assertEquals(Phase.PENDING,roundtrip(pure.obligation()).phase());assertTrue(pure.obligation().observation().isEmpty());
    }

    @Test void strictWireRejectsBooleanNumericRevisionWrongMachineAndActorType() {
        var json=SuccessorUiObligationCodec.toJson(observed());((com.fasterxml.jackson.databind.node.ObjectNode)json.get("observation").get("frame")).put("revision",true);
        assertThrows(IllegalArgumentException.class,()->SuccessorUiObligationCodec.fromJson(json));
        var actor=SuccessorUiObligationCodec.toJson(observed());((com.fasterxml.jackson.databind.node.ObjectNode)actor.get("observation").get("frame")).put("actor_character_id",20.0);
        assertThrows(IllegalArgumentException.class,()->SuccessorUiObligationCodec.fromJson(actor));
        var machine=SuccessorUiObligationCodec.toJson(observed());machine.put("machine_id","another-machine");assertThrows(IllegalArgumentException.class,()->SuccessorUiObligationCodec.fromJson(machine));
    }
    @Test void reconnectRequiresFreshQueryAndDoesNotRearmRetainedClose() {
        var before=observed();var old=before.observation().orElseThrow().frame();
        var resumed=new UiFrame(old.machineId(),old.game(),"new-session",BigInteger.TWO,old.sourceEpochSha256(),"resumed",BigInteger.ZERO,old.nativeRevision(),old.dateRaw(),old.actorCharacterId(),old.episodeRunId(),old.episodeEpoch(),old.driverVersion(),old.nativePacket(),old.semantic(),old.originalDriver(),old.sourceQualification(),old.observedAtUtc());
        var reconnect=new Rebind(old,resumed,ref("old-canonical"),ref("actual-private-rebind"));
        var rebound=roundtrip(SuccessorUiObligationReducer.rebind(before,reconnect));assertFalse(rebound.closeCanBeConsidered());
        var queried=SuccessorUiObligationReducer.observe(rebound,new Observation(resumed,UiState.CLOSE_REQUIRED,BigInteger.ONE,BigInteger.ONE,ref("reconnected-query"),ref("reconnected-native"),Optional.empty(),Optional.empty()));assertTrue(queried.closeCanBeConsidered());
        var attempted=SuccessorUiObligationReducer.enterClose(queried,new CloseAttempt("once","e".repeat(64),ref("once-command"),resumed,AT.plusSeconds(101),Optional.empty()));
        assertFalse(roundtrip(attempted).closeCanBeConsidered());assertTrue(attempted.blocksOrdinaryActionsAndSave());
    }

    @Test void legacyFinalBytesStayV1AndNewCanonicalContinuityIsStrictlyRequiredOnlyByV2() {
        var clear=SuccessorUiObligationReducer.observe(SuccessorUiObligationReducer.pending(binding()),observation(UiState.CLEAR,100,1));
        var oldFinal=new Finalization(binding().causeDigest(),ref("actual-final"),frame(100),Optional.empty(),Optional.empty(),AT.plusSeconds(101));
        var legacy=SuccessorUiObligationReducer.finalizeVerified(clear,oldFinal);byte[] original=SuccessorUiObligationCodec.encode(legacy);
        assertArrayEquals(original,SuccessorUiObligationCodec.encode(roundtrip(legacy)));
        assertEquals("xar.java.successor-ui-obligation/v1",SuccessorUiObligationCodec.toJson(legacy).get("schema").textValue());
        assertFalse(SuccessorUiObligationCodec.toJson(legacy).get("finalization").has("continuity_binding"));
        var fresh=new Finalization(oldFinal.causeDigest(),oldFinal.finalM3Proof(),oldFinal.current(),oldFinal.actualCloseReceipt(),oldFinal.verifiedDateAdvance(),oldFinal.finalizedAtUtc(),Optional.of(ref("canonical-continuity")));
        var result=roundtrip(SuccessorUiObligationReducer.finalizeVerified(clear,fresh));
        assertEquals(Optional.of(ref("canonical-continuity")),result.finalization().orElseThrow().continuityBinding());
        assertEquals("xar.java.successor-ui-obligation/v2",SuccessorUiObligationCodec.toJson(result).get("schema").textValue());
        for(int variant=0;variant<4;variant++){
            var malformed=SuccessorUiObligationCodec.toJson(result);var row=(com.fasterxml.jackson.databind.node.ObjectNode)malformed.get("finalization");
            switch(variant){case 0->row.remove("continuity_binding");case 1->row.putNull("continuity_binding");case 2->row.put("continuity_binding",true);case 3->malformed.put("schema","xar.java.successor-ui-obligation/v1");default->throw new AssertionError();}
            assertThrows(IllegalArgumentException.class,()->SuccessorUiObligationCodec.fromJson(malformed));
        }
        assertTrue(result.closeAttempt().isEmpty());assertEquals(legacy.binding(),result.binding());
    }
    private static UiFrame reconnectFrame(String session,int generation){var old=frame(100);return new UiFrame(old.machineId(),old.game(),session,BigInteger.valueOf(generation),old.sourceEpochSha256(),"actual-"+session,BigInteger.ZERO,old.nativeRevision(),old.dateRaw(),old.actorCharacterId(),old.episodeRunId(),old.episodeEpoch(),old.driverVersion(),ref("native-"+session),ref("semantic-"+session),old.originalDriver(),Optional.of(ref("source-"+session)),old.observedAtUtc());}
    @Test void unobservedCanonicalBindingRebindKeepsPendingAndRequiresAnActualNewQueryBeforeClose() {
        var pending=SuccessorUiObligationReducer.pending(binding());var current=reconnectFrame("second",2);
        var actual=Rebind.unobserved(pending.binding(),current,ref("canonical-pending"),ref("private-continuity"));
        var rebound=roundtrip(SuccessorUiObligationReducer.rebind(pending,actual));
        assertEquals(Phase.PENDING,rebound.phase());assertTrue(rebound.observation().isEmpty());assertTrue(rebound.closeAttempt().isEmpty());assertFalse(rebound.closeCanBeConsidered());
        assertEquals(Optional.of(pending.binding()),rebound.rebind().orElseThrow().retainedPending());
        assertThrows(IllegalArgumentException.class,actual::retained);
        var encoded=SuccessorUiObligationCodec.toJson(rebound);assertEquals("xar.java.successor-ui-obligation/v3",encoded.get("schema").textValue());
        var alias=encoded.deepCopy();alias.put("schema","xar.java.successor-ui-obligation/v1");assertThrows(IllegalArgumentException.class,()->SuccessorUiObligationCodec.fromJson(alias));
        for(int kind=0;kind<3;kind++){var wrong=encoded.deepCopy();var row=(com.fasterxml.jackson.databind.node.ObjectNode)wrong.get("rebind");switch(kind){case 0->row.remove("retained_pending_binding");case 1->row.putNull("retained_pending_binding");case 2->row.put("retained_pending_binding",true);default->throw new AssertionError();}assertThrows(IllegalArgumentException.class,()->SuccessorUiObligationCodec.fromJson(wrong));}
        var queried=roundtrip(SuccessorUiObligationReducer.observe(rebound,new Observation(current,UiState.CLOSE_REQUIRED,BigInteger.ONE,BigInteger.ONE,ref("query-second"),ref("query-native-second"),Optional.empty(),Optional.empty())));
        assertTrue(queried.closeCanBeConsidered());assertEquals(Phase.OBSERVED,queried.phase());
    }
    @Test void successiveRealTransportChangesKeepTheSameOriginalObservedOrUnobservedCustodyWithoutInventingQuery() {
        for(boolean observed:java.util.List.of(false,true)){
            var before=observed?observed():SuccessorUiObligationReducer.pending(binding());var second=reconnectFrame("second",2);var third=reconnectFrame("third",3);
            var once=observed?new Rebind(before.observation().orElseThrow().frame(),second,ref("before"),ref("proof-second")):Rebind.unobserved(before.binding(),second,ref("before"),ref("proof-second"));
            var rebound=roundtrip(SuccessorUiObligationReducer.rebind(before,once));
            var again=observed?new Rebind(before.observation().orElseThrow().frame(),third,ref("second-obligation"),ref("proof-third")):Rebind.unobserved(before.binding(),third,ref("second-obligation"),ref("proof-third"));
            var result=roundtrip(SuccessorUiObligationReducer.rebind(rebound,again));
            assertEquals(before.observation(),result.observation());assertEquals(before.closeAttempt(),result.closeAttempt());assertFalse(result.closeCanBeConsidered());
            assertThrows(IllegalArgumentException.class,()->SuccessorUiObligationReducer.rebind(result,again));
        }
    }

    private static Binding signedBinding(int predecessor,int successor) {
        var original=binding();var old=original.predecessor();
        var origin=new LifecycleIdentity(old.machineId(),old.game(),old.sessionId(),old.connectionGeneration(),
                new LifecycleIdentity.Subject(BigInteger.valueOf(predecessor),old.subject().episodeRunId(),old.subject().episodeEpoch(),old.subject().driverVersion()),
                old.frame(),new LifecycleIdentity.Character(BigInteger.valueOf(successor),true),old.terminalReason(),old.evidence(),old.observedAt());
        return new Binding(origin,BigInteger.valueOf(successor),original.successorEpisodeRunId(),original.sourceEpochSha256(),original.causeDigest(),
                original.parentActionId(),original.parentBodySha256(),original.originalParentCommand(),original.preclockDocument(),original.qualifiedCause(),original.qualifiedAtUtc());
    }
    private static UiFrame signedFrame(Binding binding,String session,int generation) {
        var source=frame(100);
        return new UiFrame(source.machineId(),source.game(),session,BigInteger.valueOf(generation),source.sourceEpochSha256(),source.snapshotId(),
                source.revision(),source.nativeRevision(),source.dateRaw(),binding.successorCharacterId(),binding.successorEpisodeRunId(),
                source.episodeEpoch(),source.driverVersion(),source.nativePacket(),source.semantic(),source.originalDriver(),source.sourceQualification(),source.observedAtUtc());
    }
    @Test void signedRolesSurviveObservedAndUnobservedReconnectWithoutRearmingUnknown() {
        int[][] pairs={{10,0},{10,-2},{10,Integer.MIN_VALUE},{10,Integer.MAX_VALUE},{0,20},{-2,20},{Integer.MIN_VALUE,20}};
        for(int[] pair:pairs) {
            var binding=signedBinding(pair[0],pair[1]);var current=signedFrame(binding,"session",1);
            var pending=roundtrip(SuccessorUiObligationReducer.pending(binding));
            var unobserved=roundtrip(SuccessorUiObligationReducer.rebind(pending,Rebind.unobserved(binding,signedFrame(binding,"resumed",2),ref("pending"),ref("pending-rebind"))));
            assertEquals(Phase.PENDING,unobserved.phase());assertTrue(unobserved.observation().isEmpty());assertFalse(unobserved.closeCanBeConsidered());
            var observed=SuccessorUiObligationReducer.observe(pending,new Observation(current,UiState.CLOSE_REQUIRED,BigInteger.ONE,BigInteger.ONE,
                    ref("signed-query"),ref("signed-native"),Optional.empty(),Optional.empty()));
            var entered=SuccessorUiObligationReducer.enterClose(observed,new CloseAttempt("signed-once","e".repeat(64),ref("signed-command"),current,AT.plusSeconds(101),Optional.empty()));
            var unknown=roundtrip(SuccessorUiObligationReducer.retainCloseReceipt(entered,new CloseReceipt(ActionReceipt.Outcome.UNRESOLVED,ref("signed-unknown"),Optional.empty(),Optional.empty(),Optional.empty())));
            var rebound=roundtrip(SuccessorUiObligationReducer.rebind(unknown,new Rebind(current,signedFrame(binding,"resumed",2),ref("unknown-obligation"),ref("unknown-rebind"))));
            assertEquals(binding,rebound.binding());assertFalse(rebound.closeCanBeConsidered());assertTrue(rebound.blocksOrdinaryActionsAndSave());
            assertEquals(unknown.closeAttempt(),rebound.closeAttempt());
            assertEquals(ActionReceipt.Outcome.UNRESOLVED,rebound.closeAttempt().orElseThrow().receipt().orElseThrow().outcome());
            assertThrows(IllegalArgumentException.class,()->SuccessorUiObligationReducer.enterClose(rebound,entered.closeAttempt().orElseThrow()));
            var wire=SuccessorUiObligationCodec.toJson(rebound);assertTrue(wire.get("binding").get("successor_character_id").isIntegralNumber());
            assertEquals(BigInteger.valueOf(pair[1]),wire.get("binding").get("successor_character_id").bigIntegerValue());
        }
    }
    @Test void characterJsonBoundariesRejectMissingNullWrongTypesAndRoles() {
        var invalid=java.util.List.<com.fasterxml.jackson.databind.JsonNode>of(
                com.fasterxml.jackson.databind.node.IntNode.valueOf(-1),com.fasterxml.jackson.databind.node.LongNode.valueOf(2147483648L),
                com.fasterxml.jackson.databind.node.LongNode.valueOf(-2147483649L),com.fasterxml.jackson.databind.node.LongNode.valueOf(4294967294L),
                com.fasterxml.jackson.databind.node.BooleanNode.TRUE,com.fasterxml.jackson.databind.node.DoubleNode.valueOf(20.0),
                com.fasterxml.jackson.databind.node.TextNode.valueOf("20"),com.fasterxml.jackson.databind.node.NullNode.instance);
        for(String role:java.util.List.of("successor_character_id","actor_character_id")) {
            for(var value:invalid) {
                var wire=SuccessorUiObligationCodec.toJson(observed());
                var owner=(com.fasterxml.jackson.databind.node.ObjectNode)(role.equals("successor_character_id")?wire.get("binding"):wire.get("observation").get("frame"));
                owner.set(role,value);assertThrows(IllegalArgumentException.class,()->SuccessorUiObligationCodec.fromJson(wire));
            }
            var absent=SuccessorUiObligationCodec.toJson(observed());
            var owner=(com.fasterxml.jackson.databind.node.ObjectNode)(role.equals("successor_character_id")?absent.get("binding"):absent.get("observation").get("frame"));
            owner.remove(role);assertThrows(IllegalArgumentException.class,()->SuccessorUiObligationCodec.fromJson(absent));
        }
        var mismatch=SuccessorUiObligationCodec.toJson(observed());
        ((com.fasterxml.jackson.databind.node.ObjectNode)mismatch.get("observation").get("frame")).put("actor_character_id",21);
        assertThrows(IllegalArgumentException.class,()->SuccessorUiObligationCodec.fromJson(mismatch));
        var invalidActors=new BigInteger[]{null,BigInteger.valueOf(-1),new BigInteger("2147483648"),new BigInteger("-2147483649")};
        var good=binding();var source=frame(100);
        for(BigInteger actor:invalidActors) {
            assertThrows(IllegalArgumentException.class,()->new Binding(good.predecessor(),actor,good.successorEpisodeRunId(),good.sourceEpochSha256(),good.causeDigest(),
                    good.parentActionId(),good.parentBodySha256(),good.originalParentCommand(),good.preclockDocument(),good.qualifiedCause(),good.qualifiedAtUtc()));
            assertThrows(IllegalArgumentException.class,()->new UiFrame(source.machineId(),source.game(),source.sessionId(),source.connectionGeneration(),source.sourceEpochSha256(),
                    source.snapshotId(),source.revision(),source.nativeRevision(),source.dateRaw(),actor,source.episodeRunId(),source.episodeEpoch(),source.driverVersion(),
                    source.nativePacket(),source.semantic(),source.originalDriver(),source.sourceQualification(),source.observedAtUtc()));
        }
    }
}
