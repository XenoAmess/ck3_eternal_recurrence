package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.time.Clock;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.presentation.DecisionDisplay;
import org.xar.ck3.control.application.presentation.DecisionDisplayTest;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual coordinator/composite execution with explicit in-memory journal/native ports; no Root or writer qualification. */
final class DecisionDisplayCoordinatorTest {
    @Test void internalChildIsDisplayedBeforeItsOnlyNativeSubmitAndUnknownRetainsExactParentAndAttempt() {
        MemoryJournal journal = new MemoryJournal();
        List<DecisionDisplay.Snapshot> views = new ArrayList<>();
        DecisionDisplay feed = new DecisionDisplay(Clock.fixed(DecisionDisplayTest.NOW, ZoneOffset.UTC), views::add,
                failure -> fail(failure.reason()));
        AtomicInteger nativeCalls = new AtomicInteger();
        ActionCommand parent = DecisionDisplayTest.command("display-parent", "life-advance-one-day");
        CompositeActionPort composite = new CompositeActionPort() {
            @Override public String handlerId() { return "display-software-composite"; }
            @Override public boolean supports(OperationKey operation) { return operation.equals(parent.operation()); }
            @Override public void validate(ActionCommand original) { assertEquals(parent, original); }
            @Override public ActionPorts.PostconditionResult run(ActionCommand original, Children children) {
                String childId = children.nextActionId(new OperationKey("pause-map"));
                children.submit(DecisionDisplayTest.command(childId, "pause-map"));
                fail("UNKNOWN child must stop the actual composite before any following action");
                return new ActionPorts.Pending("unreachable", List.of());
            }
            @Override public ActionPorts.PostconditionResult observe(ActionCommand original, CompositeExecution retained) {
                return new ActionPorts.Pending("same original composite remains unknown", List.of());
            }
        };
        ActionPorts.PreparationPort preparation = new ActionPorts.PreparationPort() {
            @Override public void requireOutsideReadOnlyScope(ContinuityStorePort.Session ignored, ActionCommand actual) { }
            @Override public NativeRequest prepare(ContinuityStorePort.Session same, ActionCommand actual, String requestId) {
                assertNull(same); assertEquals(RequestIds.forCommand(actual), requestId); return prepare(actual);
            }
            @Override public NativeRequest prepare(ActionCommand actual) {
                return new NativeRequest(actual.operation().value(), Optional.of("game.command." + actual.operation().value()), new RawJson(new byte[]{'{','}'}));
            }
        };
        ActionCoordinator coordinator = new ActionCoordinator("display-test-authority", journal,
                (head, actual) -> new GuardEvidence(actual.before(), actual.source(), actual.sessionId(), BigInteger.ONE,
                        actual.operation(), actual.source().sourceRef(), actual.source().sourceRef(), "display-test-authority",
                        DecisionDisplayTest.NOW, actual.deadline()),
                preparation, (permit, request, deadline) -> {
                    permit.consumeOnce();
                    nativeCalls.incrementAndGet();
                    DecisionDisplay.Card before = feed.snapshot().current().orElseThrow();
                    assertEquals(DecisionDisplay.Status.PREPARING, before.status());
                    assertEquals(permit.actionId(), before.action().orElseThrow().actionId());
                    assertEquals(List.of(DecisionDisplay.Identity.from(parent)), before.parents());
                    assertTrue(before.attemptRequestId().isEmpty());
                    return new NativeActionPort.Unknown(permit.requestId(), "software wire extent unknown", new byte[0], Optional.empty());
                },
                (actual, attempt, dispatch) -> new ActionPorts.Pending("independent state remains unavailable", List.of()),
                Clock.fixed(DecisionDisplayTest.NOW, ZoneOffset.UTC), new CompositeRegistry(List.of(composite)));
        coordinator.bindDecisionDisplay(feed);
        ActionReceipt first = coordinator.execute(parent);
        assertEquals(ActionReceipt.Outcome.UNRESOLVED, first.outcome());
        assertEquals(1, nativeCalls.get());
        ActionReceipt child = journal.records.values().stream().filter(row -> !row.command().actionId().equals(parent.actionId())).findFirst().orElseThrow();
        DecisionDisplay.Card displayedChild = views.stream().map(view -> view.current().orElseThrow())
                .filter(card -> card.action().orElseThrow().actionId().equals(child.command().actionId())
                        && card.status() == DecisionDisplay.Status.UNRESOLVED).reduce((left, right) -> right).orElseThrow();
        assertEquals(ActionTransitions.attempt(child.state()).map(ActionState.Attempt::requestId), displayedChild.attemptRequestId());
        assertEquals(child.bodySha256(), displayedChild.action().orElseThrow().bodySha256());
        assertEquals(List.of(DecisionDisplay.Identity.from(parent)), displayedChild.parents());
        assertSame(first, coordinator.execute(parent));
        assertEquals(1, nativeCalls.get());
        assertThrows(IllegalArgumentException.class, () -> coordinator.bindDecisionDisplay(feed));
    }

    /** No private Session is fabricated: this public interface seam intentionally provides only software state. */
    private static final class MemoryJournal implements ActionJournal {
        final LinkedHashMap<String, ActionReceipt> records = new LinkedHashMap<>();
        long sequence;
        final WriterContracts.Head head;
        MemoryJournal() {
            var node = StrictJson.object().put("schema", "root.ck3.continuity-window/v1")
                    .put("machine_id", "display-software-vector").put("sequence", 0).put("window_id", 1)
                    .put("status", "running").put("start_date_raw", 24000).put("target_date_raw", 286992)
                    .put("target_days", 10958).put("last_settled_cycles", 0).put("last_settled_date_raw", 24000)
                    .put("binding_lineage_count", 0);
            head = new WriterContracts.Head(ContinuityState.fromJson(node, "display-software-vector"), List.of(), List.of(), List.of(), false);
        }
        @Override public <T> T locked(Function<LockedJournal, T> operation) {
            return operation.apply(new LockedJournal() {
                @Override public ContinuityStorePort.Session writerSession() { return null; }
                @Override public WriterContracts.Head head() { return head; }
                @Override public Optional<ActionReceipt> find(String id) { return Optional.ofNullable(records.get(id)); }
                @Override public List<ActionReceipt> unresolved() { return records.values().stream().filter(row -> !row.settled()).toList(); }
                @Override public Snapshot snapshot() { return new Snapshot(sequence, head.digest(), List.copyOf(records.values()), new MissingHistoryBasis()); }
                @Override public ActionReceipt append(ActionCommand command, String digest, ActionState next) {
                    ActionTransitions.validate(find(command.actionId()), command, digest, next);
                    var actual = new ActionReceipt(1, ++sequence, command, digest, next);
                    records.put(command.actionId(), actual);
                    return actual;
                }
            });
        }
    }
}

