package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverCheckpointStore;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

final class DriverStateAssemblerTest {
    static final String WIRE="""
        {"format_version":2,"pipe_name":"test-pipe","bridge_pid":42,"episode_character_id":73,"episode_run_id":"episode-real-1",
         "last_checkpoint":null,"command_history":[
          {"index":1,"command":"query-armies","ok":true,"result":{"armies":[],"optional":null,"scale":1.0}},
          {"index":2,"command":"move-army","ok":false,"error":"original native rejection"}],
         "rollback_war_failure":{"reason":"original advisory"},"managed_restore_transaction":{"phase":"completed","lineage":["actual-parent"]},
         "succession_expectation":null,"succession_lifecycle":{"current":{"episode":"episode-real-1"}},
         "campaign_goal":{"campaign_id":"campaign-original","anchor":{"character_id":73}},
         "rollback_war_failures":[{"reason":"original advisory"}]}
        """;
    static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    static ExactRef ref(byte[] raw) { return new ExactRef("memory/test-original.json",raw.length,DriverJson.sha256(raw)); }
    static GameGeneration game() { return new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993"))); }
    static DriverSnapshotFacts.Known known() {
        return DriverFactsRepository.imported(ref(bytes(WIRE)),bytes(WIRE),3,7,game(),new OpportunityJson.Obj(java.util.Map.of()));
    }
    static G2Source source() { return new G2Source("test-machine","2026-10-23T16:00:00Z","test-source",ref(bytes("original-source"))); }
    static ProposalLifecycle.ObservationIdentity identity() {
        return new ProposalLifecycle.ObservationIdentity("test-machine",game(),new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(73),BigInteger.valueOf(9),BigInteger.valueOf(53144328)),"snapshot-9",BigInteger.valueOf(2),"episode-real-1"),1);
    }
    static ActionCommand command() {
        var expected=new ProposalLifecycle.ExpectedPostcondition(1,identity(),source(),"test-effect/v1",List.of(
                new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("native.gameplay_verified"),true)));
        return new ActionCommand("original-action",identity(),source(),"held-session",new OperationKey("move-army"),
                new OpportunityJson.Obj(java.util.Map.of()),expected,new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),Instant.parse("2030-01-01T00:00:00Z"));
    }
    static ActionJournal.Snapshot snapshot(DriverSnapshotFacts.Known known,List<ActionReceipt> actions) {
        return new ActionJournal.Snapshot(8,"a".repeat(64),actions,new ActionJournal.BoundHistoryBasis(known.originalHistoryBasis()));
    }
    static final class Journal implements ActionJournal {
        Snapshot current;int active;
        Journal(Snapshot current) { this.current=current; }
        @Override public synchronized <T>T locked(Function<LockedJournal,T> operation) {
            active++;
            try { return operation.apply(new LockedJournal() {
                @Override public Optional<ActionReceipt> find(String id) { return current.actions().stream().filter(row -> row.command().actionId().equals(id)).findFirst(); }
                @Override public List<ActionReceipt> unresolved() { return current.actions().stream().filter(row -> !row.settled()).toList(); }
                @Override public ActionReceipt append(ActionCommand command,String sha,ActionState state) { throw new AssertionError("assembler must not append a writer action"); }
                @Override public Snapshot snapshot() { return current; }
            }); } finally { active--; }
        }
    }
    @Test void completeOriginalFieldsAndHistorySurviveRoundTrip() {
        var known=known();var projected=assertInstanceOf(DriverStateSnapshot.Complete.class,DriverStateAssembler.project(known,snapshot(known,List.of()),Optional.empty()));
        assertEquals(DriverJson.object(bytes(WIRE),65536),DriverJson.object(projected.encode(),65536));
        assertEquals(2,projected.commandHistory().size());
        assertEquals("campaign-original",OpportunityJson.text(DriverJson.object(((DriverStateSnapshot.Value)projected.campaignGoal()).json(),65536).get("campaign_id"),"campaign_id"));
    }
    @Test void missingAndNullHistoryBaselineNeverProveEmptyHistory() {
        var known=known();
        for(var basis:List.of(new ActionJournal.MissingHistoryBasis(),new ActionJournal.NullHistoryBasis()))
            assertInstanceOf(DriverStateSnapshot.Incomplete.class,DriverStateAssembler.project(known,new ActionJournal.Snapshot(8,"a".repeat(64),List.of(),basis),Optional.empty()));
    }
    @Test void unknownActualActionBlocksCheckpointWithoutErasingHistory() {
        var known=known();var command=command();var action=new ActionReceipt(1,8,command,ActionCodec.bodySha256(command),
                new ActionState.Unknown(Optional.empty(),Optional.empty(),"actual unresolved receipt",List.of(ref(bytes("unknown")))));
        var result=assertInstanceOf(DriverStateSnapshot.Incomplete.class,DriverStateAssembler.project(known,snapshot(known,List.of(action)),Optional.empty()));
        assertTrue(result.missingOrUnreconciledFields().contains("unreconciled_action:original-action"));assertEquals(2,known.driver().commandHistory().size());
    }
    @Test void freezeKeepsOriginalLeaseThroughCallbackAndClosesPublisherAfterException() throws IOException {
        var known=known();var journal=new Journal(snapshot(known,List.of()));
        var authority=new DriverStateAssembler(new ActionSnapshotReader(journal),new DriverFactsRepository(known),actual -> new DriverObservationFacts.Unavailable(List.of("not observed")));
        var escaped=new java.util.concurrent.atomic.AtomicReference<DriverCheckpointStore.CheckpointPublisher>();
        assertThrows(IOException.class,() -> authority.withFrozen((frozen,publisher) -> { assertEquals(1,journal.active);escaped.set(publisher);throw new IOException("actual callback failure"); }));
        assertEquals(0,journal.active);
        assertThrows(IllegalArgumentException.class,() -> escaped.get().publish(known.driver(),known.driver()));
        int actualHistoryRows=authority.withFrozen((frozen,publisher) -> ((DriverStateSnapshot.Complete)frozen).commandHistory().size());
        assertEquals(2,actualHistoryRows);
    }
    @Test void staleOrUnlockedDriverCasIsRejected() {
        var known=known();var repository=new DriverFactsRepository(known);
        var nextStamp=new DriverSnapshotFacts.Stamp(4,7,game(),known.stamp().episodeRunId(),known.stamp().driverSha256());
        var next=new DriverSnapshotFacts.Known(known.driver(),nextStamp,known.originalHistoryBasis(),known.actionRows(),known.auxiliary(),known.loop(),Optional.empty());
        assertThrows(IllegalArgumentException.class,() -> repository.compareAndSet(known.stamp(),next));
        repository.locked(state -> { repository.compareAndSet(known.stamp(),next);assertThrows(IllegalArgumentException.class,() -> repository.compareAndSet(known.stamp(),next));return null; });
    }
    @Test void wrongIntegerTypesAndMissingRequiredFieldAreRejected() {
        for(String malformed:List.of(WIRE.replace("\"bridge_pid\":42","\"bridge_pid\":true"),WIRE.replace("\"episode_character_id\":73","\"episode_character_id\":73.0"),
                WIRE.replace("\"last_checkpoint\":null,","")))assertThrows(IllegalArgumentException.class,() -> DriverStateSnapshot.decodeComplete(bytes(malformed)));
    }
    @Test void onlyCurrentKnownIntentCanObserveItsOwnGuardWhileUnknownAlwaysBlocks() {
        var known=known();var command=command();
        var intent=new ActionReceipt(1,8,command,ActionCodec.bodySha256(command),new ActionState.IntentDurable());
        var durable=snapshot(known,List.of(intent));
        assertInstanceOf(DriverStateSnapshot.Complete.class,DriverStateAssembler.projectObservation(known,durable,Optional.of(command.actionId())));
        assertInstanceOf(DriverStateSnapshot.Incomplete.class,DriverStateAssembler.projectObservation(known,durable,Optional.empty()));
        assertInstanceOf(DriverStateSnapshot.Incomplete.class,DriverStateAssembler.project(known,durable,Optional.of(command.actionId())));
        var unknown=new ActionReceipt(1,8,command,ActionCodec.bodySha256(command),new ActionState.Unknown(Optional.empty(),Optional.empty(),"original unknown",List.of(ref(bytes("unknown")))));
        assertInstanceOf(DriverStateSnapshot.Incomplete.class,DriverStateAssembler.projectObservation(known,snapshot(known,List.of(unknown)),Optional.of(command.actionId())));
        assertInstanceOf(DriverStateSnapshot.Incomplete.class,DriverStateAssembler.projectHistory(known,snapshot(known,List.of(unknown)),Optional.of(command.actionId()),command));
    }
}
