package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.UncheckedIOException;
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

/** Actual shared coordinator/writer ordering at a software packet edge; grants no derived domain permit. */
final class ReservedChildScopeWriterTest {
    @TempDir Path root;

    @Test void exactReservedChildRemainsIdentifiableAfterCoordinatorChangesActionScope() throws Exception {
        var owner = new AtomicReference<ActionWriterIntegrationFixture>();
        var parentCommand = new AtomicReference<ActionCommand>();
        var parentHeadBeforeReservation = new AtomicReference<WriterContracts.Head>();
        var checked = new AtomicInteger();
        var parentOperation = new OperationKey("reserved-child-scope-fixture");
        var childOperation = new OperationKey("pause-map");
        String handlerId = "reserved-child-scope-fixture/v1";
        var preparation = new ActionPorts.PreparationPort() {
            @Override public NativeRequest prepare(ActionCommand command) { throw new AssertionError("actual original writer Session required"); }
            @Override public NativeRequest prepare(ContinuityStorePort.Session same, ActionCommand child, String requestId) {
                try {
                    var fixture = owner.get(); fixture.writer.requireSession(same);
                    assertEquals(RequestIds.forActionBody(ActionCodec.bodySha256(child)), requestId);
                    assertThrows(IllegalArgumentException.class, () -> ActionChildPlanningScope.current(same, same.head()));
                    var actual = ActionChildPlanningScope.reservedParent(same, same.head(), child).orElseThrow();
                    assertEquals(parentCommand.get().actionId(), actual.actionId());
                    assertEquals(ActionCodec.bodySha256(parentCommand.get()), actual.bodySha256());
                    assertEquals(handlerId, actual.handlerId());
                    assertTrue(ContinuityActionJournal.lookup(same.head().state(), child.actionId(), fixture.archive).isEmpty());
                    var changedBody = new ActionCommand(child.actionId(), child.before(), child.source(), child.sessionId(), child.operation(),
                            child.arguments(), child.expected(), child.claims(), child.deadline().minusNanos(1));
                    assertThrows(IllegalArgumentException.class, () -> ActionChildPlanningScope.reservedParent(same, same.head(), changedBody));
                    assertThrows(IllegalArgumentException.class, () -> ActionChildPlanningScope.reservedParent(same, parentHeadBeforeReservation.get(), child));
                    checked.incrementAndGet();
                    return new NativeRequest(child.operation().value(), Optional.of("game.command.pause-map"), raw("{}"));
                } catch (IOException failure) { throw new UncheckedIOException(failure); }
            }
        };
        var primitive = new ActionWriterIntegrationFixture.SoftwareActionScenario(childOperation, "game.command.pause-map",
                (command, attempt, dispatch) -> new ActionPorts.Pending("software child postcondition remains unknown", List.of()),
                () -> { }, Optional.empty(), Optional.empty(), false, Optional.of(preparation));
        var composite = new ActionWriterIntegrationFixture.SoftwareCompositeScenario(handlerId, Set.of(parentOperation),
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, Optional.empty(), context -> {
                    CompositeActionPort handler = new CompositeActionPort() {
                        @Override public String handlerId() { return handlerId; }
                        @Override public boolean supports(OperationKey operation) { return parentOperation.equals(operation); }
                        @Override public void validate(ActionCommand command) { assertEquals(parentOperation, command.operation()); }
                        @Override public ActionPorts.PostconditionResult run(ActionCommand parent, Children children) {
                            parentCommand.set(parent);
                            try {
                                var same = context.journal().borrowedWriterSession();
                                parentHeadBeforeReservation.set(same.head());
                                assertEquals(parent.actionId(), ActionChildPlanningScope.current(same, same.head()).orElseThrow().actionId());
                                var child = new ActionCommand(children.nextActionId(childOperation), parent.before(), parent.source(), parent.sessionId(),
                                        childOperation, parent.arguments(), parent.expected(), parent.claims(), parent.deadline());
                                assertThrows(IllegalArgumentException.class, () -> ActionChildPlanningScope.reservedParent(same, same.head(), child));
                                children.submit(child);
                                throw new AssertionError("unknown child must stop the original composite");
                            } catch (IOException failure) { throw new UncheckedIOException(failure); }
                        }
                        @Override public ActionPorts.PostconditionResult observe(ActionCommand parent, CompositeExecution execution) {
                            return new ActionPorts.Pending("collect only; no child replay", List.of());
                        }
                    };
                    var refusingVerifier = new NativeRecordedEvidenceVerifier.Binding(parentOperation, context.source().sourceRef(),
                            (head, proposed, archive) -> { throw new IllegalArgumentException("software scope fixture has no semantic terminal authority"); });
                    return new ActionWriterIntegrationFixture.SoftwareCompositeInstallation(handler, List.of(refusingVerifier));
                });
        var reads = new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64), "fixture-adapter",
                source -> List.of(), request -> raw("{}"));
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("reserved-child"), false, reads, List.of(primitive), List.of(composite))) {
            owner.set(fixture);
            var seed = fixture.command("reserved-child-parent");
            var parent = new ActionCommand(seed.actionId(), seed.before(), seed.source(), seed.sessionId(), parentOperation,
                    seed.arguments(), seed.expected(), seed.claims(), seed.deadline());
            var receipt = fixture.coordinator.execute(parent);
            assertInstanceOf(ActionState.CompositeUnknown.class, receipt.state());
            assertEquals(1, checked.get()); assertEquals(1, fixture.nativeActionWrites());
            assertEquals(receipt, fixture.coordinator.execute(parent)); assertEquals(1, fixture.nativeActionWrites());
            fixture.journal.locked(locked -> {
                try { assertTrue(ActionChildPlanningScope.reservedParent(locked.writerSession(), locked.head(), seed).isEmpty()); }
                catch (IOException failure) { throw new UncheckedIOException(failure); }
                return null;
            });
            assertFalse(receipt.visibleGameplay()); assertFalse(receipt.eligibleAdvance());
        }
    }

    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }
}
