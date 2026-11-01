package org.xar.ck3.control.application.session;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.session.OrdinaryAdmissionFixture225.*;
import static org.xar.ck3.control.application.session.SessionPorts.*;

import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionRecord;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.CompositeExecution;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.ObservationProvenance;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;

/** Pure source-owned cycle/archived DATA checks; the mature fixture forbids every physical/native operation. */
final class CycleObservationBarrier274Test {
    @Test void defaultJournalConservativelyRequiresFreshAfterEvenForACompletedReceipt() throws Exception {
        var f=new Fixture(false);
        complete(f);
        BatchJournal legacy=input->new JournalCommit(REF,0);
        assertTrue(legacy.requiresFreshAfterCycle(OWNER,f.receipt));
    }

    @Test void actualRetainRequiresTheAfterBarrierWithoutAnotherCommitOrHeadChange() throws Exception {
        var f=new Fixture(false);
        f.journal.retainCycle(OWNER,f.receipt);
        var before=f.store.current.toJson();int commits=f.store.commits;
        assertTrue(f.journal.requiresFreshAfterCycle(OWNER,f.receipt));
        assertEquals(commits,f.store.commits);
        assertEquals(before,f.store.current.toJson());
    }

    @Test void completedExactOriginalUsesLegacyObservationAndRetainRemainsIdempotent() throws Exception {
        var f=new Fixture(false);
        complete(f);
        var before=f.store.current.toJson();int commits=f.store.commits;
        f.journal.retainCycle(OWNER,f.receipt);
        assertFalse(f.journal.requiresFreshAfterCycle(OWNER,f.receipt));
        assertEquals(commits,f.store.commits);
        assertEquals(before,f.store.current.toJson());
    }

    @Test void canonicalAppliedReceiptWithoutActualRetainCannotChooseAPath() {
        var f=new Fixture(false);
        var before=f.store.current.toJson();
        assertThrows(IllegalArgumentException.class,()->f.journal.requiresFreshAfterCycle(OWNER,f.receipt));
        assertEquals(0,f.store.commits);
        assertEquals(before,f.store.current.toJson());
    }

    @Test void anotherSessionCannotSelectObservationForTheOriginalReceipt() throws Exception {
        var f=new Fixture(false);f.journal.retainCycle(OWNER,f.receipt);
        var foreign=new SessionIdentity(OWNER.machineId(),OWNER.game(),"another-session");
        var before=f.store.current.toJson();
        assertThrows(IllegalArgumentException.class,()->f.journal.requiresFreshAfterCycle(foreign,f.receipt));
        assertEquals(before,f.store.current.toJson());
    }

    @Test void completedOriginalCannotConcealAnotherGenuinePendingCycle() throws Exception {
        var f=new Fixture(false);complete(f);var first=f.receipt;
        var second=installNext(f);f.journal.retainCycle(OWNER,second);
        var before=f.store.current.toJson();int commits=f.store.commits;
        assertThrows(IllegalArgumentException.class,()->f.journal.requiresFreshAfterCycle(OWNER,first));
        assertTrue(f.journal.requiresFreshAfterCycle(OWNER,second));
        assertEquals(commits,f.store.commits);
        assertEquals(before,f.store.current.toJson());
    }

    @Test void findingTheRequestedHeadStillValidatesItsOlderOriginalCycleRecord() throws Exception {
        var f=new Fixture(false);complete(f);var firstRecord=f.archive.lastMaterial;
        var second=installNext(f);f.journal.retainCycle(OWNER,second);
        f.journal.settleCycle(OWNER,second,semantic(frame(5,24048,"independent-second"),TIME.plusSeconds(6)));
        assertFalse(f.journal.requiresFreshAfterCycle(OWNER,second));
        var damaged=ContinuityJson.parseObject(f.archive.materials.get(firstRecord).bytes(),ContinuityJson.DOCUMENT_MAX_BYTES);
        damaged.put("completed_cycles",99);
        f.archive.materials.put(firstRecord,new RawJson(ContinuityJson.canonical(damaged)));
        int commits=f.store.commits;
        assertThrows(IllegalArgumentException.class,()->f.journal.requiresFreshAfterCycle(OWNER,second));
        assertEquals(commits,f.store.commits);
    }

    @Test void equalTerminalOccurrenceRemainsInsufficientForANewPendingCycle() throws Exception {
        var f=new Fixture(false);f.journal.retainCycle(OWNER,f.receipt);
        assertTrue(f.journal.requiresFreshAfterCycle(OWNER,f.receipt));
        var before=f.store.current.toJson();int commits=f.store.commits;
        var stale=semantic(frame(3,24024,"same-terminal-time"),TIME.plusSeconds(2));
        var failure=assertThrows(IllegalArgumentException.class,()->f.journal.settleCycle(OWNER,f.receipt,stale));
        assertTrue(failure.getMessage().contains("collected after"));
        assertEquals(commits,f.store.commits);
        assertEquals(before,f.store.current.toJson());
    }

    private static void complete(Fixture f) throws Exception {
        f.journal.retainCycle(OWNER,f.receipt);
        f.journal.settleCycle(OWNER,f.receipt,semantic(frame(3,24024,"independent-first"),TIME.plusSeconds(3)));
    }

    private static ActionReceipt installNext(Fixture f) {
        var original=f.receipt.command();var before=frame(3,24024,"independent-first");
        var flags=f.receipt.applied().orElseThrow().observation().actual();
        var expected=new ExpectedPostcondition(1,before,original.source(),original.expected().observerSchema(),flags);
        var deadline=TIME.plusSeconds(20);
        var command=new ActionCommand("auto-second",before,original.source(),OWNER.sessionId(),original.operation(),
                original.arguments(),expected,original.claims(),deadline);
        var guard=new GuardEvidence(before,original.source(),OWNER.sessionId(),BigInteger.ONE,original.operation(),
                REF,REF,"fixture",TIME.plusSeconds(4),deadline);
        var effect=new ActionState.EffectObservation(frame(4,24048,"second-terminal"),original.source(),OWNER.sessionId(),
                original.expected().observerSchema(),flags,new ObservationProvenance.Query("independent-second-terminal"),TIME.plusSeconds(5),REF);
        var actual=new ActionReceipt(1,f.store.current.sequence()+1,command,ActionCodec.bodySha256(command),
                new ActionState.CompositeSettled(new CompositeExecution("advance-life/v1",TIME.plusSeconds(4),guard,List.of()),new ActionState.Applied(effect)));
        f.archive.preserveReceipt(actual);
        var record=f.archive.preserveRecord(new ActionRecord(actual,ContinuityActionJournal.recordHead(f.store.current)));
        var state=f.store.current.toJson();state.put("sequence",actual.sequence());state.set(ContinuityActionJournal.STATE_FIELD,record.toJson());
        f.store.current=ContinuityState.fromJson(state,OWNER.machineId());f.receipt=actual;
        return actual;
    }
}
