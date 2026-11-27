package org.xar.ck3.control.application.session;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentAuthority;
import org.xar.ck3.control.application.session.SessionPorts.JournalInput;
import org.xar.ck3.control.application.session.SessionPorts.JournalKind;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.continuity.writer.WriterContracts.HistoricalTransition;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;

/** Software DATA drives the actual batch request producer and reducer without borrowing action or file authority. */
final class CommittedImportedBatchTailTest {
    private static final String MACHINE = "empty-batch-fixture";
    private static final String PREFIX = "imported-batch-fixture";
    private static final SessionIdentity DEPARTED = owner(2,"departed-owner");
    private static final SessionIdentity SUCCESSOR = owner(3,"successor-owner");
    private static final ExactRef REF = new ExactRef("/fixture/reference.json",1,"b".repeat(64));
    private static final WriterContracts.Pin PIN = new WriterContracts.Pin(REF,
            new WriterContracts.FileIdentity("1","2","3",Instant.EPOCH.toString(),1));
    private final OrdinaryCycleTransitions transitions = new OrdinaryCycleTransitions(forbiddenArchive(),
            (same,owner,semantic) -> { throw new AssertionError("metadata must not qualify SEM"); },
            (same,owner,pair,proof) -> { throw new AssertionError("metadata must not qualify SAVE"); },
            new OriginalWindowReducer.Policy(365), same -> { throw new AssertionError("pure replay cannot open a writer"); });

    @Test void consumesOnlyClosedSuccessorBatchIds() {
        var fixture = new Anchor();
        var start = batch(fixture.rebind.after(), SUCCESSOR, PREFIX+"-2", JournalKind.BATCH_STARTED);
        var finish = batch(start.after(), SUCCESSOR, PREFIX+"-2", JournalKind.BATCH_FINISHED);
        var nextStart = batch(finish.after(), SUCCESSOR, PREFIX+"-3", JournalKind.BATCH_STARTED);
        var deferred = batch(nextStart.after(), SUCCESSOR, PREFIX+"-3", JournalKind.BATCH_DEFERRED);
        assertEquals(List.of(PREFIX+"-2",PREFIX+"-3"), fixture.verify(List.of(start,finish,nextStart,deferred),deferred.after()));
        assertEquals(List.of(),fixture.verify(List.of(),fixture.rebind.after()));
    }

    @Test void rejectsOpenBatchInvalidOwnerAndReusedOrSkippedIds() {
        var fixture = new Anchor();
        var start = batch(fixture.rebind.after(), SUCCESSOR, PREFIX+"-2", JournalKind.BATCH_STARTED);
        assertThrows(IllegalArgumentException.class, () -> fixture.verify(List.of(start),start.after()));
        var wrongOwner = batch(fixture.rebind.after(), owner(3,"some-other-session"), PREFIX+"-2", JournalKind.BATCH_STARTED);
        var wrongFinish = batch(wrongOwner.after(), SUCCESSOR, PREFIX+"-2", JournalKind.BATCH_FINISHED);
        assertThrows(IllegalArgumentException.class, () -> fixture.verify(List.of(wrongOwner,wrongFinish),wrongFinish.after()));
        for (String id : List.of(PREFIX+"-1", PREFIX+"-02", PREFIX+"-3")) {
            var shifted = batch(fixture.rebind.after(), SUCCESSOR, id, JournalKind.BATCH_STARTED);
            var terminal = batch(shifted.after(), SUCCESSOR, id, JournalKind.BATCH_DEFERRED);
            assertThrows(IllegalArgumentException.class, () -> fixture.verify(List.of(shifted,terminal),terminal.after()));
        }
        var finish=batch(start.after(),SUCCESSOR,PREFIX+"-2",JournalKind.BATCH_FINISHED);
        var repeated = batch(finish.after(),SUCCESSOR,PREFIX+"-2",JournalKind.BATCH_STARTED);
        var repeatedFinish = batch(repeated.after(),SUCCESSOR,PREFIX+"-2",JournalKind.BATCH_FINISHED);
        assertThrows(IllegalArgumentException.class, () -> fixture.verify(List.of(start,finish,repeated,repeatedFinish),repeatedFinish.after()));
    }

    @Test void rejectsOrdinaryActionReadAndNoncontiguousSuffix() {
        var fixture = new Anchor();
        var start = batch(fixture.rebind.after(), SUCCESSOR, PREFIX+"-2", JournalKind.BATCH_STARTED);
        for (String kind : List.of(ContinuityActionJournal.KIND, WriterContracts.DRIVER_READ_HISTORY_KIND)) {
            var details = StrictJson.object().put("evidence_id","different-original").put("source","test").put("boundary","BATCH_FINISHED");
            var request = new WriterContracts.Request(kind, ContinuityJson.canonical(details), List.of());
            var unrelated = edge(start.after(), start.after(), request);
            assertThrows(IllegalArgumentException.class, () -> fixture.verify(List.of(start,unrelated),unrelated.after()));
        }
        var finishWithoutStart = batch(fixture.rebind.after(), SUCCESSOR, PREFIX+"-2", JournalKind.BATCH_FINISHED);
        assertThrows(IllegalArgumentException.class, () -> fixture.verify(List.of(start,finishWithoutStart),finishWithoutStart.after()));
        var finish = batch(start.after(), SUCCESSOR, PREFIX+"-2", JournalKind.BATCH_FINISHED);
        var extra = batch(finish.after(),SUCCESSOR,PREFIX+"-3",JournalKind.BATCH_STARTED);
        assertThrows(IllegalArgumentException.class, () -> fixture.verify(List.of(start,finish),extra.after()));
    }

    @Test void comparesAllStateAndTheExactOrdinaryRequest() {
        var fixture = new Anchor();
        var start = batch(fixture.rebind.after(), SUCCESSOR, PREFIX+"-2", JournalKind.BATCH_STARTED);
        var request = request(SUCCESSOR,PREFIX+"-2",JournalKind.BATCH_FINISHED);
        var expected = transitions.reduce(start.after(),request);
        for(String field : List.of("last_settled_date_raw", "last_settled_cycles")) {
            var after=expected.toJson(); after.put(field,after.get(field).longValue()+1);
            var changed=edge(start.after(),ContinuityState.fromJson(after,MACHINE),request);
            assertThrows(IllegalArgumentException.class,() -> fixture.verify(List.of(start,changed),changed.after()));
        }
        for(String field : List.of(WriterContracts.ORDINARY_CYCLE_FIELD, WriterContracts.ORDINARY_SAVED_CYCLE_FIELD,
                "java_action_lifecycle_head", "java_driver_action_history_v1", "last_current_saved_cold")) {
            var after=expected.toJson(); after.set(field,StrictJson.object().put("drift",true));
            var changed=edge(start.after(),ContinuityState.fromJson(after,MACHINE),request);
            assertThrows(IllegalArgumentException.class,() -> fixture.verify(List.of(start,changed),changed.after()));
        }
        var details=request.detailsObject().put("source","unqualified-caller");
        var replaced=new WriterContracts.Request(request.kind(),ContinuityJson.canonical(details),List.of());
        var different=edge(start.after(),transitions.reduce(start.after(),replaced),replaced);
        assertThrows(IllegalArgumentException.class,() -> fixture.verify(List.of(start,different),different.after()));
    }

    private HistoricalTransition batch(ContinuityState before, SessionIdentity owner, String batch, JournalKind kind) {
        var request = request(owner,batch,kind);
        return edge(before,transitions.reduce(before,request),request);
    }

    private WriterContracts.Request request(SessionIdentity owner, String batch, JournalKind kind) {
        return transitions.batchRequest(new JournalInput(owner,batch,kind,Optional.empty(),Optional.empty(),Optional.empty(),List.of()));
    }

    private static HistoricalTransition edge(ContinuityState before, ContinuityState reduced, WriterContracts.Request request) {
        long sequence=before.sequence()+1;
        var after=ContinuityState.fromJson(reduced.toJson().put("sequence",sequence).put("last_event_identity",request.identity()),MACHINE);
        return new HistoricalTransition(sequence,request.kind(),request.details(),request.identity(),before,after,PIN);
    }

    private static SessionIdentity owner(long pid,String session) {
        return new SessionIdentity(MACHINE,new GameGeneration(pid,new PythonOnlyUInt64(BigInteger.valueOf(100+pid))),session);
    }

    private static ActionPorts.OutcomeArchive forbiddenArchive() {
        return (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(CommittedImportedBatchTailTest.class.getClassLoader(),
                new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,args) -> {
                    throw new AssertionError("metadata must not access the action archive: "+method.getName());
                });
    }

    private final class Anchor {
        final HistoricalTransition attachment;
        final HistoricalTransition rebind;

        Anchor() {
            var json=StrictJson.object().put("schema","root.ck3.continuity-window/v1").put("machine_id",MACHINE)
                    .put("sequence",58).put("status","repair_required").put("window_id",1)
                    .put("start_date_raw",24000).put("target_date_raw",32760).put("target_days",365)
                    .put("last_settled_date_raw",24024).put("last_settled_cycles",4);
            var batch=json.putObject(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD)
                    .put("batch_id",PREFIX+"-1").put("boundary",JournalKind.BATCH_INTERRUPTED.name());
            batch.set("session",OrdinaryCycleTransitions.sessionToJson(DEPARTED));
            json.set("game_binding",DEPARTED.game().toJson());
            var predecessor=ContinuityState.fromJson(json,MACHINE);
            json.put("status","running").set("game_binding",SUCCESSOR.game().toJson());
            var attachDetails=StrictJson.object().put("source","test").put("evidence_id","fixture-imported-attachment");
            attachment=edge(predecessor,ContinuityState.fromJson(json,MACHINE),
                    new WriterContracts.Request(SavedAttachmentAuthority.KIND,ContinuityJson.canonical(attachDetails),List.of()));
            var details=StrictJson.object().put("source",WriterContracts.ORDINARY_IMPORTED_CYCLE_RESTORE_SOURCE)
                    .put("evidence_id","restore-cycle:"+attachment.eventIdentity()).put("operation","REBIND")
                    .put("attachment_identity",attachment.eventIdentity())
                    .put("attachment_head_digest",ContinuityJson.digest(attachment.after().toJson()));
            details.set("session",OrdinaryCycleTransitions.sessionToJson(SUCCESSOR));
            var restored=attachment.after().toJson();
            var cycle=restored.putObject(WriterContracts.ORDINARY_CYCLE_FIELD).putNull("head").putNull("pending_receipt");
            cycle.set("session",OrdinaryCycleTransitions.sessionToJson(SUCCESSOR));
            restored.set(WriterContracts.ORDINARY_IMPORTED_CYCLE_ORIGIN_FIELD,REF.toJson());
            rebind=edge(attachment.after(),ContinuityState.fromJson(restored,MACHINE),
                    new WriterContracts.Request(WriterContracts.ORDINARY_CYCLE_KIND,ContinuityJson.canonical(details),List.of()));
        }

        List<String> verify(List<HistoricalTransition> suffix, ContinuityState last) {
            return CommittedImportedBatchTail.verify(last,attachment,rebind,suffix);
        }
    }
}
