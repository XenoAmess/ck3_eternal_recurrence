package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Supplier;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.advance.AdvanceObservationPort;
import org.xar.ck3.control.application.advance.LifeAdvanceRootReplay;
import org.xar.ck3.control.application.advance.ProductionAdvanceReadiness;
import org.xar.ck3.control.application.history.DriverHistoryAccess;
import org.xar.ck3.control.application.planning.governance.CrownRetryDue;
import org.xar.ck3.control.application.planning.governance.CrownRetryPublication;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Real collector, actual complete Driver history, original writer/archive and production Life readiness caller.
 * The absent optional CROWN value performs no CROWN query/publication; this fixture grants no Game qualification.
 */
final class ProductionAdvanceReadinessScopeTest {
    @TempDir Path temporary;

    @Test void actualProductionCallerEntersTheCurrentCollectorBeforeResolvingImmutableHistoryAndOnlyBorrowsInside()throws Exception {
        try(var actual=new ActionWriterIntegrationFixture(temporary.resolve("actual-life-readiness-scope"),false)) {
            AtomicBoolean entered=new AtomicBoolean();AtomicInteger resolutions=new AtomicInteger();
            DriverHistoryAccess history=new DriverHistoryAccess(()->{
                assertTrue(entered.get(),"real current scope must precede history/facts freezing");
                resolutions.incrementAndGet();return actual.driverAuthority();
            },actual.archive);
            class CurrentRuntime implements ProductionAdvanceReadiness.RuntimeFactsPort,ProductionAdvanceReadiness.RuntimeScope {
                @Override public <T>T current(ActionCommand parent,AdvanceObservationPort.Frame frame,Supplier<T> work) {
                    try {
                        var same=actual.writer.borrowedSession();
                        return actual.collector.current(same,frame.identity(),parent.deadline(),lease->{
                            assertEquals(frame,LifeAdvanceRootReplay.push(lease.frame()));entered.set(true);
                            try{return work.get();}finally{entered.set(false);}
                        });
                    }catch(IOException failure){throw new UncheckedIOException(failure);}
                }
                @Override public ProductionAdvanceReadiness.RuntimeFacts inspect(ActionCommand parent,AdvanceObservationPort.Frame frame,DriverHistoryAccess.View view) {
                    try {
                        return actual.collector.borrowCurrent(actual.writer.borrowedSession(),frame.identity(),parent.deadline(),lease->{
                            assertTrue(entered.get());assertEquals(lease.driver().stamp(),view.stamp());
                            return new ProductionAdvanceReadiness.RuntimeFacts(frame.identity(),frame.source(),frame.sessionId(),view.stamp(),
                                    lease.executableSteps(),lease.bridgeCapabilities(),Optional.empty(),false,false,false,view.currentDriverEvidence());
                        });
                    }catch(IOException failure){throw new UncheckedIOException(failure);}
                }
            }
            var runtime=new CurrentRuntime();var due=unusedAbsentCrown(actual);
            var consumer=new ProductionAdvanceReadiness(history,runtime,due,()->session(actual),runtime);
            actual.writer.locked(same->actual.collector.withOwnedPlanning(same,actual.observationIdentity(),Instant.now().plusSeconds(20),(request,lease)->{
                var frame=LifeAdvanceRootReplay.push(lease.frame());
                final ActionCommand parent;
                try{parent=actual.command("actual-readiness-parent");}
                catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("actual readiness parent collection interrupted",interrupted);}
                int packets=actual.nativePacketReads(),queries=actual.nativeReadWrites();String head=same.head().digest();
                var facts=consumer.inspect(parent,frame);assertEquals(frame.identity(),facts.observed());assertEquals(1,resolutions.get());
                assertEquals(packets,actual.nativePacketReads());assertEquals(queries,actual.nativeReadWrites());assertEquals(head,same.head().digest());
                assertFalse(entered.get());return null;
            }));
            assertEquals(0,actual.nativeActionWrites());
        }
    }
    private static ContinuityStorePort.Session session(ActionWriterIntegrationFixture actual) {
        try{return actual.writer.borrowedSession();}catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    /** Real service on the same writer; every optional-publication callback fails if accidentally invoked. */
    private static CrownRetryDue unusedAbsentCrown(ActionWriterIntegrationFixture actual) {
        ExactRef source=new ExactRef(Path.of("fixture-unused-crown-source").toAbsolutePath().toString(),1,"a".repeat(64));
        var publication=new CrownRetryPublication(actual.writer.originalLockPath(),"fixture.unused-crown/v1",List.of(source),List.of(source),
                new CrownRetryPublication.MaterialPort() {
                    @Override public CrownRetryPublication.Material capture(WriterContracts.Head head,CrownRetryPublication.Input input, Instant callerDeadline) {
                        throw new AssertionError("absent optional CROWN must not invoke its producer");
                    }
                    @Override public void requireCurrent(WriterContracts.Head head,CrownRetryPublication.Input input,ObservationIdentity frame,G2Source current, Instant callerDeadline) {
                        throw new AssertionError("absent optional CROWN must not fabricate a publication proof");
                    }
                },(id,body)->{throw new AssertionError("absent optional CROWN cannot publish");});
        return new CrownRetryDue(actual.writer,actual.writer::requireSession,publication);
    }
}
