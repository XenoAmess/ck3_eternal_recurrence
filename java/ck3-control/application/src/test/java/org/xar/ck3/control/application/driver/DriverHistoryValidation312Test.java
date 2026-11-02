package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Pure original DATA projections; these typed records issue no canonical membership or Native permission. */
public final class DriverHistoryValidation312Test {
    private static final String WIRE = """
        {"format_version":2,"pipe_name":"test-pipe","bridge_pid":42,"episode_character_id":73,"episode_run_id":"episode-real-1",
         "last_checkpoint":null,"command_history":[
          {"index":1,"command":"query-armies","ok":true,"result":{"armies":[],"optional":null,"scale":1.0}},
          {"index":2,"command":"move-army","ok":false,"error":"original native rejection"}],
         "rollback_war_failure":{"reason":"original advisory"},"managed_restore_transaction":{"phase":"completed","lineage":["actual-parent"]},
         "succession_expectation":null,"succession_lifecycle":{"current":{"episode":"episode-real-1"}},
         "campaign_goal":{"campaign_id":"campaign-original","anchor":{"character_id":73}},
         "rollback_war_failures":[{"reason":"original advisory"}]}""";

    private static byte[] bytes(String text) { return text.getBytes(java.nio.charset.StandardCharsets.UTF_8); }
    private static ExactRef ref(byte[] raw) { return new ExactRef("memory/test-original.json", raw.length, DriverJson.sha256(raw)); }
    private static GameGeneration game() { return new GameGeneration(42, new PythonOnlyUInt64(new BigInteger("9007199254740993"))); }
    private static G2Source source() { return new G2Source("test-machine", "2026-10-23T16:00:00Z", "test-source", ref(bytes("original-source"))); }
    private static ProposalLifecycle.ObservationIdentity identity() {
        return new ProposalLifecycle.ObservationIdentity("test-machine", game(), new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(73), BigInteger.valueOf(9), BigInteger.valueOf(53144328)), "snapshot-9", BigInteger.valueOf(2), "episode-real-1"), 1);
    }
    private static ActionCommand command(String actionId, String operation) {
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, identity(), source(), "test-effect/v1", List.of(
                new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("native.gameplay_verified"), true)));
        return new ActionCommand(actionId, identity(), source(), "held-session", new OperationKey(operation),
                new OpportunityJson.Obj(Map.of()), expected, new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), java.time.Instant.parse("2030-01-01T00:00:00Z"));
    }
    private static DriverSnapshotFacts.Known known() {
        return DriverFactsRepository.imported(ref(bytes(WIRE)), bytes(WIRE), 3, 7, game(), new OpportunityJson.Obj(Map.of()));
    }
    private static List<Obj> history(DriverSnapshotFacts.Known value) {
        return value.driver().commandHistory().stream().map(row->DriverJson.object(row.originalRow().json(),DriverJson.MAX_NATIVE_BYTES)).toList();
    }
    private static DriverSnapshotFacts.Known withHistory(List<Obj> rows) {
        var wire=DriverJson.object(bytes(WIRE),DriverJson.MAX_NATIVE_BYTES).with("command_history",new Arr(new ArrayList<Value>(rows)));
        byte[] raw=DriverJson.encode(wire);
        return DriverFactsRepository.imported(ref(raw),raw,3,7,game(),new Obj(Map.of()));
    }
    private static DriverSnapshotFacts.Known changed(DriverSnapshotFacts.Known original,int ordinal,Obj row) {
        var values=new ArrayList<>(history(original));values.set(ordinal-1,row);return withHistory(values);
    }
    private static Obj without(Obj row,String field) {
        var values=new LinkedHashMap<>(row.members());values.remove(field);return new Obj(values);
    }
    private static ActionReceipt ended(String id,String operation,long sequence) {
        var command=command(id,operation);
        return new ActionReceipt(1,sequence,command,ActionCodec.bodySha256(command),
                new ActionState.IntentAbandoned(ref(bytes("past-intent-"+id)),ref(bytes("past-head-"+id))));
    }
    private static DriverSnapshotFacts.Known covered(DriverSnapshotFacts.Known value,int ordinal,List<ActionReceipt> actions) {
        var rows=new ArrayList<DriverSnapshotFacts.ActionRow>();
        ExactRef exactRow=ref(value.driver().commandHistory().get(ordinal-1).originalRow().json());
        for(var action:actions)rows.add(new DriverSnapshotFacts.ActionRow(action.command().actionId(),action.bodySha256(),action.sequence(),ordinal,exactRow));
        return new DriverSnapshotFacts.Known(value.driver(),value.stamp(),value.originalHistoryBasis(),rows,value.auxiliary(),value.loop(),value.observation());
    }
    private static ActionJournal.Snapshot snapshot(DriverSnapshotFacts.Known value,List<ActionReceipt> actions) {
        return new ActionJournal.Snapshot(20,"a".repeat(64),actions,new ActionJournal.BoundHistoryBasis(value.originalHistoryBasis()));
    }
    private static DriverStateSnapshot project(DriverSnapshotFacts.Known value,List<ActionReceipt> actions,boolean observation) {
        return observation?DriverStateAssembler.projectObservation(value,snapshot(value,actions),Optional.empty())
                :DriverStateAssembler.project(value,snapshot(value,actions),Optional.empty());
    }
    private static void incomplete(DriverStateSnapshot actual,String reason) {
        assertTrue(assertInstanceOf(DriverStateSnapshot.Incomplete.class,actual).missingOrUnreconciledFields().contains(reason));
    }
    private static List<Obj> invalidPrimitiveRows(Obj valid) {
        return List.of(without(valid,"command"),valid.with("command",new IntegerValue(BigInteger.ONE)),
                without(valid,"ok"),valid.with("ok",new Text("false")));
    }
    private static DriverActionHistoryCodec.Legacy material(DriverActionHistoryCodec.Recording recording) {
        var original=ref(bytes("past-original-material"));
        return new DriverActionHistoryCodec.Legacy(recording,
                recording==DriverActionHistoryCodec.Recording.RAISED?Optional.empty():Optional.of(original),
                recording==DriverActionHistoryCodec.Recording.RAISED?Optional.of("original native rejection"):Optional.empty(),
                List.of(new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.MATERIAL,original)),List.of(ref(bytes("past-producer"))));
    }
    private static DriverActionHistoryCodec.Source sourceData(ActionReceipt action,DriverActionHistoryCodec.Legacy material) {
        return new DriverActionHistoryCodec.Source(action.command().actionId(),action.bodySha256(),action.sequence(),
                ref(bytes("past-receipt")),ref(bytes("past-record")),action.outcome(),material);
    }
    private static Obj sourceRow(Obj row,DriverActionHistoryCodec.Source source) {
        return row.with(DriverActionHistoryCodec.SOURCE_FIELD,DriverJson.object(DriverActionHistoryCodec.encode(source).bytes(),DriverActionHistoryCodec.MAX_SOURCE_BYTES));
    }

    @Test
    public void uncoveredRowsKeepPrimitiveAndMissingDataChecks() {
        var base=known();byte[] original=base.driver().encode();
        for(boolean observation:List.of(false,true)) {
            assertSame(base.driver(),project(base,List.of(),observation));
            for(Obj invalid:invalidPrimitiveRows(history(base).get(0))) {
                var changed=changed(base,1,invalid);
                assertThrows(IllegalArgumentException.class,()->project(changed,List.of(),observation));
                assertSame(base.driver(),project(base,List.of(),observation));
            }
        }
        for(var basis:List.of(new ActionJournal.MissingHistoryBasis(),new ActionJournal.NullHistoryBasis(),
                new ActionJournal.BoundHistoryBasis(ref(bytes("another-original-history")))))
            incomplete(DriverStateAssembler.project(base,new ActionJournal.Snapshot(20,"a".repeat(64),List.of(),basis),Optional.empty()),
                    "original_full_history_baseline_not_bound_in_canonical_writer");
        var unavailable=assertInstanceOf(DriverStateSnapshot.Incomplete.class,DriverStateAssembler.project(
                new DriverSnapshotFacts.Unavailable(List.of("actual_full_driver_unavailable")),snapshot(base,List.of()),Optional.empty()));
        assertEquals(List.of("actual_full_driver_unavailable"),unavailable.missingOrUnreconciledFields());
        var c=command("unknown-action","move-army");
        var unknown=new ActionReceipt(1,8,c,ActionCodec.bodySha256(c),new ActionState.Unknown(Optional.empty(),Optional.empty(),"actual unknown",List.of(ref(bytes("unknown-original")))));
        incomplete(DriverStateAssembler.projectObservation(base,snapshot(base,List.of(unknown)),Optional.of(c.actionId())),"unreconciled_action:unknown-action");
        incomplete(DriverStateAssembler.project(base,snapshot(base,List.of(unknown)),Optional.of(c.actionId())),"unreconciled_action:unknown-action");
        assertArrayEquals(original,base.driver().encode());
    }

    @Test
    public void coveredRowsKeepActionSourceAndPerCallBindings() {
        var base=known();var first=ended("first","move-army",8);var second=ended("second","move-army",9);
        var good=covered(base,2,List.of(first,second));byte[] original=good.driver().encode();
        for(boolean observation:List.of(false,true)) {
            assertSame(good.driver(),project(good,List.of(first,second),observation));
            var wrongSecond=ended("second","query-armies",9);var shared=covered(base,2,List.of(first,wrongSecond));
            incomplete(project(shared,List.of(first,wrongSecond),observation),"original_history_result_disagrees:second");
            for(Obj invalid:invalidPrimitiveRows(history(base).get(1))) {
                var changed=covered(changed(base,2,invalid),2,List.of(first));
                assertThrows(IllegalArgumentException.class,()->project(changed,List.of(first),observation));
                // A prior successful covered call cannot exempt this ordinal in a fresh uncovered call.
                assertThrows(IllegalArgumentException.class,()->project(changed,List.of(),observation));
            }
            for(Obj mismatch:List.of(history(base).get(1).with("ok",new Bool(true)),history(base).get(1).with("command",new Text("query-armies"))))
                incomplete(project(covered(changed(base,2,mismatch),2,List.of(first)),List.of(first),observation),"original_history_result_disagrees:first");
            var changedBody=new DriverSnapshotFacts.ActionRow(first.command().actionId(),"0".repeat(64),first.sequence(),2,
                    ref(base.driver().commandHistory().get(1).originalRow().json()));
            var missing=new DriverSnapshotFacts.Known(base.driver(),base.stamp(),base.originalHistoryBasis(),List.of(changedBody),base.auxiliary(),base.loop(),base.observation());
            incomplete(project(missing,List.of(first),observation),"original_history_row_unavailable:first");
        }
        var raised=sourceData(first,material(DriverActionHistoryCodec.Recording.RAISED));
        var validSource=covered(changed(base,2,sourceRow(history(base).get(1),raised)),2,List.of(first));
        assertSame(validSource.driver(),project(validSource,List.of(first),false));
        var wrongSources=List.of(
                new DriverActionHistoryCodec.Source("other",raised.bodySha256(),raised.durableSequence(),raised.receipt(),raised.record(),raised.outcome(),raised.material()),
                new DriverActionHistoryCodec.Source(raised.actionId(),"0".repeat(64),raised.durableSequence(),raised.receipt(),raised.record(),raised.outcome(),raised.material()),
                new DriverActionHistoryCodec.Source(raised.actionId(),raised.bodySha256(),9,raised.receipt(),raised.record(),raised.outcome(),raised.material()),
                new DriverActionHistoryCodec.Source(raised.actionId(),raised.bodySha256(),raised.durableSequence(),raised.receipt(),raised.record(),ActionReceipt.Outcome.REJECTED_CONFIRMED,raised.material()));
        for(var wrong:wrongSources) {
            var input=covered(changed(base,2,sourceRow(history(base).get(1),wrong)),2,List.of(first));
            assertThrows(IllegalArgumentException.class,()->project(input,List.of(first),false));
        }
        var accepted=sourceData(first,material(DriverActionHistoryCodec.Recording.ACCEPTED_RETURN));
        var acceptedRow=sourceRow(history(base).get(1),accepted).with("result",new Obj(Map.of("accepted",new Bool(false))));
        var returned=covered(changed(base,2,acceptedRow),2,List.of(first));
        assertSame(returned.driver(),project(returned,List.of(first),true));
        var badAccepted=covered(changed(base,2,acceptedRow.with("result",new Obj(Map.of("accepted",new Text("false"))))),2,List.of(first));
        assertThrows(IllegalArgumentException.class,()->project(badAccepted,List.of(first),true));
        assertSame(good.driver(),project(good,List.of(first,second),false));
        assertThrows(UnsupportedOperationException.class,()->good.actionRows().add(good.actionRows().get(0)));
        byte[] borrowed=good.driver().commandHistory().get(1).originalRow().json();borrowed[0]^=1;
        assertArrayEquals(original,good.driver().encode());
    }
}
