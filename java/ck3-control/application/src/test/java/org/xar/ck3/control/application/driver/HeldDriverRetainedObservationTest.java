package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.ObservationProvenance;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real framed-packet/Driver assembly into the same bounded retained-before consumer. */
final class HeldDriverRetainedObservationTest {
    private static DriverObservationAssembler.FullSnapshot full(String state) {
        var actual=DriverObservationAssemblerTest.actual(state);
        return new DriverObservationAssembler().projectFull(actual,DriverObservationAssemblerTest.facts(actual),
                DriverStateAssemblerTest.ref(actual.originalPacket()));
    }
    private static DriverObservationAssembler.Complete complete(DriverObservationAssembler.FullSnapshot full) {
        return assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler()
                .assemble(full.actual(),full.facts(),full.originalEvidence()));
    }
    private static HeldDriverObservationPort noIo() {
        return new HeldDriverObservationPort(deadline -> {throw new AssertionError("retaining must not query Native");},
                actual -> {throw new AssertionError("retaining must not reread Driver");},
                actual -> {throw new AssertionError("retaining must preserve original evidence");},
                new DriverObservationAssembler(),1);
    }
    @Test void originalFramedPacketAndActualDriverProjectionBecomeRetainedWithoutObservationOrNewEvidence() {
        var full=full(DriverObservationAssemblerTest.STATE);var complete=complete(full);var held=noIo();
        held.retainVerified(full,complete);
        assertSame(complete,held.requireRetained(complete.identity(),complete.originalEvidence()));
        assertEquals(full.actual().observedAt(),complete.observedAt());
        assertEquals(full.actual().session().connectionGeneration(),complete.connectionGeneration());
        assertEquals(full.semantic(),complete.semantic());
        assertEquals(full.fullBindingSha256(),complete.fullBindingSha256());
        assertThrows(IllegalArgumentException.class,()->held.lifecycle(null));
    }
    @Test void forgedFullSemanticOrBindingCannotEnterCacheEvenWhenOrdinaryIdentityMatches() {
        var full=full(DriverObservationAssemblerTest.STATE);var complete=complete(full);var held=noIo();
        var fields=new LinkedHashMap<String,OpportunityJson.Value>(full.semantic().members());
        fields.put("unobserved_extension",new OpportunityJson.Bool(true));
        var alteredSemantic=new DriverObservationAssembler.FullSnapshot(full.actual(),full.facts(),
                new OpportunityJson.Obj(fields),full.originalEvidence(),full.fullBindingSha256());
        var alteredBinding=new DriverObservationAssembler.FullSnapshot(full.actual(),full.facts(),
                full.semantic(),full.originalEvidence(),"0".repeat(64));
        for(var altered:List.of(alteredSemantic,alteredBinding))
            assertThrows(IllegalArgumentException.class,()->held.retainVerified(altered,complete));
        assertThrows(IllegalStateException.class,()->held.requireRetained(complete.identity(),complete.originalEvidence()));
    }
    @Test void mismatchedCompleteSessionConnectionTimeAndEvidenceAndIncompleteOriginalAreRejected() {
        var full=full(DriverObservationAssemblerTest.STATE);var actual=complete(full);var held=noIo();
        for(var wrong:List.of(
                new DriverObservationAssembler.Complete(actual.identity(),actual.source(),"another-session",actual.connectionGeneration(),actual.semantic(),actual.originalEvidence(),actual.observedAt(),actual.fullBindingSha256()),
                new DriverObservationAssembler.Complete(actual.identity(),actual.source(),actual.sessionId(),actual.connectionGeneration().add(BigInteger.ONE),actual.semantic(),actual.originalEvidence(),actual.observedAt(),actual.fullBindingSha256()),
                new DriverObservationAssembler.Complete(actual.identity(),actual.source(),actual.sessionId(),actual.connectionGeneration(),actual.semantic(),actual.originalEvidence(),actual.observedAt().plusNanos(1),actual.fullBindingSha256()),
                new DriverObservationAssembler.Complete(actual.identity(),actual.source(),actual.sessionId(),actual.connectionGeneration(),actual.semantic(),DriverStateAssemblerTest.ref(DriverStateAssemblerTest.bytes("another original packet")),actual.observedAt(),actual.fullBindingSha256())))
            assertThrows(IllegalArgumentException.class,()->held.retainVerified(full,wrong));
        var terminal=full(DriverObservationAssemblerTest.STATE.replace("{\"character_id\":73,\"alive\":true}","null"));
        assertThrows(IllegalArgumentException.class,()->held.retainVerified(terminal,actual));
        assertThrows(IllegalStateException.class,()->held.requireRetained(actual.identity(),actual.originalEvidence()));
    }
    @Test void bootstrapRetainedFrameAndLaterRealObserveShareOneBoundedCache() throws InterruptedException {
        var original=full(DriverObservationAssemblerTest.STATE);var first=complete(original);
        var next=full(DriverObservationAssemblerTest.STATE.replace("\"speed\":3","\"speed\":4"));
        var reads=new AtomicInteger();var facts=new AtomicInteger();var archives=new AtomicInteger();
        var held=new HeldDriverObservationPort(deadline -> {reads.incrementAndGet();return next.actual();},
                observed -> {facts.incrementAndGet();assertSame(next.actual(),observed);return new DriverObservationFacts.Known(next.facts());},
                observed -> {archives.incrementAndGet();assertSame(next.actual(),observed);return next.originalEvidence();},
                new DriverObservationAssembler(),1);
        held.retainVerified(original,first);held.retainVerified(original,first);
        var later=held.observe(Instant.now().plusSeconds(60));
        assertEquals(1,reads.get());assertEquals(1,facts.get());assertEquals(1,archives.get());
        assertSame(later,held.requireRetained(later.identity(),later.originalEvidence()));
        assertThrows(IllegalStateException.class,()->held.requireRetained(first.identity(),first.originalEvidence()));
        assertEquals(next.actual().observedAt(),later.observedAt());
    }
    @Test void actualHeldAdvanceCurrentAndNextKeepNativePushProvenanceAndOriginalPacket() {
        var earlier=fullAtRevision(8);var later=fullAtRevision(9);var before=complete(earlier);var observed=complete(later);
        var reads=new AtomicInteger();
        var held=new HeldDriverObservationPort(deadline->{reads.incrementAndGet();return later.actual();},
                actual->new DriverObservationFacts.Known(later.facts()),actual->later.originalEvidence(),new DriverObservationAssembler(),2);
        var parent=parent(before);var current=held.current(parent,Instant.now().plusSeconds(60));
        var currentPush=assertInstanceOf(ObservationProvenance.Push.class,current.provenance());
        assertEquals(observed.identity().frame().snapshotId(),currentPush.snapshotId());
        assertEquals(observed.identity().frame().identity().nativeRevision(),currentPush.nativeRevision());
        assertEquals(later.originalEvidence(),currentPush.originalPacket());
        assertEquals(observed.identity(),current.identity());assertEquals(observed.semantic(),current.semantic());
        var next=held.next(parent,before.identity(),Instant.now().plusSeconds(60));
        assertEquals(current.provenance(),next.provenance());assertEquals(2,reads.get());
        assertThrows(IllegalArgumentException.class,()->held.next(parent,observed.identity(),Instant.now().plusSeconds(60)));
    }
    @Test void actualAdvanceBoundaryRestoresInterruptAndNeverReturnsForgedObservation() {
        var before=complete(fullAtRevision(8));var original=new InterruptedException("actual held observation interrupted");
        var held=new HeldDriverObservationPort(deadline->{throw original;},
                actual->{throw new AssertionError("interrupted transport cannot produce Driver facts");},
                actual->{throw new AssertionError("interrupted transport cannot produce evidence");},new DriverObservationAssembler(),1);
        assertFalse(Thread.currentThread().isInterrupted());
        try {
            var failure=assertThrows(IllegalStateException.class,()->held.current(parent(before),Instant.now().plusSeconds(60)));
            assertSame(original,failure.getCause());assertTrue(Thread.currentThread().isInterrupted());
        } finally { Thread.interrupted(); }
        try {
            var failure=assertThrows(IllegalStateException.class,()->held.next(parent(before),before.identity(),Instant.now().plusSeconds(60)));
            assertSame(original,failure.getCause());assertTrue(Thread.currentThread().isInterrupted());
        } finally { Thread.interrupted(); }
    }
    private static DriverObservationAssembler.FullSnapshot fullAtRevision(int revision) {
        var base=DriverObservationAssemblerTest.actual(DriverObservationAssemblerTest.STATE);
        byte[] json=DriverStateAssemblerTest.bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"held-"+revision+"\",\"revision\":"+revision+",\"state\":"+DriverObservationAssemblerTest.STATE+"}");
        byte[] packet=ByteBuffer.allocate(json.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(json.length).put(json).array();
        var actual=new NativeObservationPort.ObservedFrame(base.session(),"held-"+revision,BigInteger.valueOf(revision),
                new RawJson(base.state().bytes()),packet,base.observedAt());
        return new DriverObservationAssembler().projectFull(actual,DriverObservationAssemblerTest.facts(actual),DriverStateAssemblerTest.ref(packet));
    }
    private static ActionCommand parent(DriverObservationAssembler.Complete before) {
        return new ActionCommand("actual-held-parent",before.identity(),before.source(),before.sessionId(),new OperationKey("fixture-held-observation"),
                new OpportunityJson.Obj(java.util.Map.of()),new ExpectedPostcondition(1,before.identity(),before.source(),"fixture-held/v1",
                List.of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"),true))),
                new JointBudgetSelector.Claims(java.util.Set.of(),java.util.Set.of(),java.util.Set.of(),java.util.Set.of()),Instant.now().plusSeconds(60));
    }
}
