package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real sole coordinator/writer negative boundaries; no fabricated private natural proof or Root. */
final class RootEpisodeContinuationRuntimeTest {
    @TempDir Path temporary;

    @Test void originalUnknownCannotBecomeAContinuationAndRepeatedExecuteDoesNotResubmit() throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("unknown"),true)) {
            var command=fixture.command("unknown-is-not-natural");
            var original=fixture.coordinator.execute(command);
            assertInstanceOf(ActionState.Unknown.class,original.state());
            var owner=owner(command);byte[] retained=fixture.ledgerBytes();
            int actions=fixture.nativeActionWrites(),reads=fixture.nativeReadWrites();
            assertThrows(IllegalArgumentException.class,()->RootEpisodeContinuationRuntime.requireNaturalParent(owner,original));
            assertEquals(original,fixture.coordinator.execute(command));
            assertArrayEquals(retained,fixture.ledgerBytes());
            assertEquals(actions,fixture.nativeActionWrites());assertEquals(reads,fixture.nativeReadWrites());
            assertEquals(1,actions);
            var otherBirth=new GameGeneration(owner.game().pid(),new PythonOnlyUInt64(owner.game().creationFiletime().value().add(BigInteger.ONE)));
            var foreign=new SessionIdentity(owner.machineId(),otherBirth,owner.sessionId());
            assertThrows(IllegalArgumentException.class,()->RootEpisodeContinuationRuntime.requireNaturalParent(foreign,original));
            assertArrayEquals(retained,fixture.ledgerBytes());assertEquals(actions,fixture.nativeActionWrites());
        }
    }

    @Test void actualIntentDurableAtTheOriginalSecondGuardIsStillNotACommittedNaturalTransition() throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("intent"),true)) {
            var checked=new AtomicInteger();
            fixture.bindGuardObserver((head,command)->{
                try {
                    var same=fixture.writer.borrowedSession();fixture.writer.requireSession(same);
                    var actual=ContinuityActionJournal.lookup(head.state(),command.actionId(),fixture.archive.withSession(same));
                    if(actual.isPresent()) {
                        assertInstanceOf(ActionState.IntentDurable.class,actual.orElseThrow().state());
                        assertThrows(IllegalArgumentException.class,()->RootEpisodeContinuationRuntime.requireNaturalParent(owner(command),actual.orElseThrow()));
                        assertEquals(head.digest(),same.head().digest());checked.incrementAndGet();
                    }
                }catch(IOException failure){throw new UncheckedIOException(failure);}
            });
            var command=fixture.command("durable-intent-is-not-natural");
            var original=fixture.coordinator.execute(command);
            assertInstanceOf(ActionState.Unknown.class,original.state());
            assertEquals(1,checked.get());assertEquals(1,fixture.nativeActionWrites());
            assertEquals(original,fixture.coordinator.execute(command));assertEquals(1,checked.get());
            assertEquals(1,fixture.nativeActionWrites());
        }
    }

    @Test void actualSoleCoordinatorControlSettlementCannotPretendToBeANaturalEpisode() throws Exception {
        var actual=new AtomicReference<ActionWriterIntegrationFixture>();
        var scenario=new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey("pause-map"),"game.command.pause-map",
                (command,attempt,dispatch)->{
                    var fixture=actual.get();
                    try {
                        return fixture.collector.current(fixture.journal.borrowedWriterSession(),command.before(),command.deadline(),lease->{
                            var request=new PlanningReadRequest(lease.frame().identity(),command.source(),command.sessionId(),
                                    fixture.readContract.operation(),new OpportunityJson.Obj(Map.of()),command.deadline());
                            var result=fixture.reads.read(fixture.readContract,request);
                            if(!(result instanceof PlanningReadResult.Known<?> known))throw new AssertionError("real independent control read unavailable");
                            return new ActionPorts.ControlObserved(new ActionState.ControlApplied(known.receipt(),
                                    command.expected().observerSchema(),command.expected().values()));
                        });
                    }catch(IOException failure){throw new UncheckedIOException(failure);}
                },()->{});
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("control"),false,scenario)) {
            actual.set(fixture);var command=fixture.command("actual-control-is-not-natural");
            var receipt=fixture.coordinator.execute(command);
            var settled=assertInstanceOf(ActionState.Settled.class,receipt.state());
            assertInstanceOf(ActionState.ControlApplied.class,settled.settlement());
            assertFalse(receipt.visibleGameplay());assertFalse(receipt.eligibleAdvance());
            byte[] retained=fixture.ledgerBytes();int actions=fixture.nativeActionWrites(),reads=fixture.nativeReadWrites();
            assertThrows(IllegalArgumentException.class,()->RootEpisodeContinuationRuntime.requireNaturalParent(owner(command),receipt));
            assertEquals(receipt,fixture.coordinator.execute(command));assertEquals(1,actions);
            assertArrayEquals(retained,fixture.ledgerBytes());assertEquals(actions,fixture.nativeActionWrites());
            assertEquals(reads,fixture.nativeReadWrites());
        }
    }

    private static SessionIdentity owner(ActionCommand command) {
        return new SessionIdentity(command.origin().machineId(),command.origin().game(),command.sessionId());
    }
}
