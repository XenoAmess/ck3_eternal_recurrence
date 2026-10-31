package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.lang.reflect.Proxy;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;

/** Actual coordinator+writer+scope, software packets only. Not actual143 reconciliation or Root observer acceptance. */
final class ChildObserverScope144Test {
    @TempDir Path root;
    @Test void freshChildObservationUsesExactReservationWithoutBorrowingParentEntryOrChangingActionScope() throws Exception {
        var owner=new AtomicReference<ActionWriterIntegrationFixture>();
        var parentCommand=new AtomicReference<ActionCommand>();
        var oldHead=new AtomicReference<WriterContracts.Head>();
        var observations=new AtomicInteger();
        var parentOperation=new OperationKey("child-observer-parent-fixture");
        var childOperation=new OperationKey("set-speed-5");
        String handlerId="child-observer-parent-fixture/v1";
        var primitive=new ActionWriterIntegrationFixture.SoftwareActionScenario(childOperation,"game.command.set-speed-5",
                (child,attempt,dispatch)->{
                    try {
                        var fixture=owner.get();var same=fixture.journal.borrowedWriterSession();
                        assertInstanceOf(NativeActionPort.AckReceived.class,dispatch);
                        assertEquals(child.actionId(),ActionScope.currentActionId().orElseThrow());
                        assertThrows(IllegalArgumentException.class,()->ActionChildPlanningScope.current(same,same.head()));
                        assertTrue(ActionChildPlanningScope.isReservedChild(same,same.head(),child));
                        assertEquals(child.actionId(),ActionScope.currentActionId().orElseThrow());
                        var parent=ActionChildPlanningScope.reservedParent(same,same.head(),child).orElseThrow();
                        assertEquals(parentCommand.get().actionId(),parent.actionId());
                        var changed=new ActionCommand(child.actionId(),child.before(),child.source(),child.sessionId(),child.operation(),
                                child.arguments(),child.expected(),child.claims(),child.deadline().minusNanos(1));
                        assertThrows(IllegalArgumentException.class,()->ActionChildPlanningScope.isReservedChild(same,same.head(),changed));
                        assertThrows(IllegalArgumentException.class,()->ActionChildPlanningScope.isReservedChild(same,oldHead.get(),child));
                        var foreign=(ContinuityStorePort.Session)Proxy.newProxyInstance(getClass().getClassLoader(),
                                new Class<?>[]{ContinuityStorePort.Session.class},(proxy,method,args)->{throw new AssertionError("wrong writer must reject before IO");});
                        assertThrows(IllegalArgumentException.class,()->ActionChildPlanningScope.isReservedChild(foreign,same.head(),child));
                        observations.incrementAndGet();
                        return new ActionPorts.Pending("software fresh observer has no post-state; retain UNKNOWN, no cleanup",List.of());
                    }catch(IOException failure){throw new UncheckedIOException(failure);}
                },()->{},Optional.empty(),Optional.empty(),false,Optional.empty());
        var composite=new ActionWriterIntegrationFixture.SoftwareCompositeScenario(handlerId,Set.of(parentOperation),
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.empty(),context->{
                    CompositeActionPort handler=new CompositeActionPort(){
                        public String handlerId(){return handlerId;}
                        public boolean supports(OperationKey operation){return parentOperation.equals(operation);}
                        public void validate(ActionCommand command){assertEquals(parentOperation,command.operation());}
                        public ActionPorts.PostconditionResult run(ActionCommand parent,Children children){
                            parentCommand.set(parent);
                            try {
                                var same=context.journal().borrowedWriterSession();oldHead.set(same.head());
                                assertFalse(ActionChildPlanningScope.isReservedChild(same,same.head(),parent));
                                assertTrue(ActionChildPlanningScope.entryGuard(same,same.head(),parent).isPresent());
                                var child=new ActionCommand(children.nextActionId(childOperation),parent.before(),parent.source(),parent.sessionId(),
                                        childOperation,parent.arguments(),parent.expected(),parent.claims(),parent.deadline());
                                children.submit(child);throw new AssertionError("UNKNOWN child must stop original parent");
                            }catch(IOException failure){throw new UncheckedIOException(failure);}
                        }
                        public ActionPorts.PostconditionResult observe(ActionCommand parent,CompositeExecution execution){return new ActionPorts.Pending("read-only only",List.of());}
                    };
                    var verifier=new NativeRecordedEvidenceVerifier.Binding(parentOperation,context.source().sourceRef(),
                            (head,proposed,archive)->{throw new IllegalArgumentException("software fixture grants no terminal authority");});
                    return new ActionWriterIntegrationFixture.SoftwareCompositeInstallation(handler,List.of(verifier));
                });
        var reads=new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64),"fixture-adapter",source->List.of(),
                request->new RawJson("{}".getBytes(StandardCharsets.UTF_8)));
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("child-observer144"),false,reads,List.of(primitive),List.of(composite))){
            owner.set(fixture);var seed=fixture.command("child-observer-parent");
            var parent=new ActionCommand(seed.actionId(),seed.before(),seed.source(),seed.sessionId(),parentOperation,
                    seed.arguments(),seed.expected(),seed.claims(),seed.deadline());
            var receipt=fixture.coordinator.execute(parent);
            assertInstanceOf(ActionState.CompositeUnknown.class,receipt.state());
            assertEquals(1,observations.get());assertEquals(1,fixture.nativeActionWrites());
            assertEquals(receipt,fixture.coordinator.execute(parent));assertEquals(1,fixture.nativeActionWrites());
            fixture.journal.locked(locked->{
                try{assertFalse(ActionChildPlanningScope.isReservedChild(locked.writerSession(),locked.head(),parent));
                    assertTrue(ActionChildPlanningScope.current(locked.writerSession(),locked.head()).isEmpty());}
                catch(IOException failure){throw new UncheckedIOException(failure);}return null;
            });
            assertFalse(receipt.visibleGameplay());assertFalse(receipt.eligibleAdvance());
        }
    }
}
