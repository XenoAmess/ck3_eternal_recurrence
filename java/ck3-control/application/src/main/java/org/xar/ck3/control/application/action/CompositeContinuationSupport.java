package org.xar.ck3.control.application.action;

import java.time.Clock;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.Function;
import org.xar.ck3.control.contracts.StrictJson;

/** Source-qualified continuation of one retained parent. Ordinary reconciliation never receives Children. */
final class CompositeContinuationSupport {
    private CompositeContinuationSupport() { }
    private static void collectNew(ActionJournal.LockedJournal locked, ActionReceipt receipt, long boundary, List<ActionReceipt> created, int depth) {
        StrictJson.require(depth <= 2 && created.size() <= 1024, "bounded continuation attempt report exceeded");
        if (receipt.sequence() <= boundary) return;
        if (ActionTransitions.attempt(receipt.state()).isPresent() && !(receipt.state() instanceof ActionState.RejectedBeforeDispatch)) created.add(receipt);
        ActionTransitions.composite(receipt.state()).ifPresent(cursor -> cursor.children().forEach(child -> {
            var original = locked.find(child.actionId()); original.ifPresent(actual -> collectNew(locked, actual, boundary, created, depth + 1));
        }));
    }
    static CompositeContinuationReport continueOriginal(ActionJournal.LockedJournal locked, CompositeContinuationToken token,
            CompositeRegistry registry, Clock clock, Function<ActionCommand, ActionReceipt> submit) {
        ActionCommand parent = Objects.requireNonNull(token.originalParent());
        ActionReceipt original = locked.find(parent.actionId()).orElseThrow(() -> new IllegalArgumentException("original continuation parent is absent"));
        StrictJson.require(java.util.Arrays.equals(ActionCodec.encodeCommand(parent), ActionCodec.encodeCommand(original.command())), "continuation changed the original parent body");
        boolean fixture=FixturePlan.isParent(parent)&&token.kind()==CompositeContinuationToken.Kind.FIXTURE_STARTUP;
        if(fixture)FixturePlan.requireParent(parent);
        StrictJson.require(fixture||parent.origin() instanceof CommandOrigin.LifecycleTerminal
                && parent.lifecycleExpected().operation() == LifecycleExpectedPostcondition.Operation.CONTINUE_SUCCESSOR,
                "only the exact original successor or registered fixture parent has this continuation");
        if (original.settled()) return new CompositeContinuationReport(original, List.of(), CompositeContinuationReport.Disposition.NO_NEW_CHILD_ATTEMPT);
        StrictJson.require(original.state() instanceof ActionState.CompositeUnknown && clock.instant().isBefore(token.deadline()), "a retained successor cursor and fresh source deadline are required");
        CompositeExecution retained = ((ActionState.CompositeUnknown) original.state()).execution();
        CompositeActionPort actual = registry.require(retained.handlerId());
        StrictJson.require(actual.supports(parent.operation()) && actual instanceof CompositeActionPort.OriginalContinuation,
                "the actual installed composite has no original continuation producer");
        var source = (CompositeActionPort.OriginalContinuation) actual;
        StrictJson.require(!fixture||actual instanceof FixtureCompositeActionPort,"fixture continuation requires its registered source-owned fixture producer");
        source.requireContinuation(parent, retained, token);
        for (CompositeExecution.Child child : retained.children()) {
            var existing = locked.find(child.actionId());
            if (existing.isEmpty() || !fixture&&!existing.orElseThrow().settled())
                return new CompositeContinuationReport(original, List.of(), CompositeContinuationReport.Disposition.NO_NEW_CHILD_ATTEMPT);
            StrictJson.require(existing.orElseThrow().bodySha256().equals(child.bodySha256()), "continuation child body changed");
        }
        long initialSequence = locked.head().state().sequence();
        List<ActionReceipt> created = new ArrayList<>(); AtomicBoolean active = new AtomicBoolean(true);
        CompositeActionPort.Children children = new CompositeActionPort.Children() {
            private CompositeExecution current() {
                StrictJson.require(active.get(), "continuation Children custody has closed");
                ActionReceipt current = locked.find(parent.actionId()).orElseThrow();
                StrictJson.require(current.state() instanceof ActionState.CompositeUnknown && current.bodySha256().equals(original.bodySha256()), "original unresolved parent cursor changed");
                return ((ActionState.CompositeUnknown) current.state()).execution();
            }
            @Override public String nextActionId() { return ActionIds.child(parent.actionId(), current().children().size() + 1); }
            @Override public String nextActionId(OperationKey operation) { return ActionIds.child(parent.actionId(), current().children().size() + 1, operation); }
            @Override public List<ActionReceipt> completed() {
                List<ActionReceipt> result = new ArrayList<>();
                for (var child : current().children()) {
                    var receipt = locked.find(child.actionId()).orElseThrow();
                    StrictJson.require(receipt.settled() && receipt.bodySha256().equals(child.bodySha256()), "unknown child forbids another continuation dispatch"); result.add(receipt);
                }
                return List.copyOf(result);
            }
            @Override public ActionReceipt submit(ActionCommand child) {
                var previous = current(); completed(); source.requireContinuation(parent, previous, token);
                StrictJson.require(clock.instant().isBefore(token.deadline()) && !child.deadline().isAfter(token.deadline())
                        && child.actionId().equals(nextActionId(child.operation())) && child.sessionId().equals(parent.sessionId())
                        && child.source().equals(parent.source()) && (child.origin() instanceof CommandOrigin.Gameplay
                            ||fixture&&child.origin() instanceof CommandOrigin.Frontend)
                        && child.origin().machineId().equals(parent.origin().machineId()) && child.origin().game().equals(parent.origin().game()),
                        "continuation child crossed its exact ordinal/source/session/Game/fresh deadline");
                if (token.kind() == CompositeContinuationToken.Kind.SUCCESSOR_UI_CLOSE)
                    StrictJson.require(child.operation().equals(LifecycleExpectedPostcondition.Operation.CLOSE_DEATH_MODAL.key()), "Close token cannot authorize another operation");
                source.requireContinuationChild(parent, previous, token, child);
                if(fixture)((FixtureCompositeActionPort)source).requireFixtureChild(parent,previous,child);
                var reserved = new ArrayList<>(previous.children()); reserved.add(new CompositeExecution.Child(child.actionId(), ActionCodec.bodySha256(child)));
                ActionCoordinator.append(locked, parent, original.bodySha256(), new ActionState.CompositeUnknown(
                        new CompositeExecution(previous.handlerId(), previous.startedAt(), previous.guard(), reserved),
                        "source-qualified successor continuation reserved its original child", ((ActionState.CompositeUnknown) locked.find(parent.actionId()).orElseThrow().state()).evidence()));
                var receipt = CompositeContinuationNesting.within(parent, token, child, () -> submit.apply(child));
                collectNew(locked, receipt, initialSequence, created, 0);
                StrictJson.require(receipt.settled(), "continuation child is unknown; retain it and do not dispatch another");
                return receipt;
            }
            @Override public org.xar.ck3.control.application.lifecycle.LifecycleCommit lifecycle(org.xar.ck3.control.application.lifecycle.LifecycleChild child) {
                StrictJson.require(!fixture,"fixture Entry must use its original qualified Entry authority, never a successor lifecycle child");
                current(); completed(); source.requireContinuation(parent, current(), token);
                StrictJson.require(clock.instant().isBefore(token.deadline()) && child.parentActionId().equals(parent.actionId())
                        && child.phase() == org.xar.ck3.control.application.lifecycle.LifecycleChild.Phase.SUCCESSOR_PENDING_FINALIZED,
                        "only actual finalized successor lifecycle commit may complete this original parent");
                var details = child.request().detailsObject();
                StrictJson.require(StrictJson.text(details.get("parent_action_id")).equals(parent.actionId())
                        && StrictJson.text(details.get("parent_body_sha256")).equals(original.bodySha256())
                        && details.get("source").equals(org.xar.ck3.control.g2.planning.ProposalLifecycleCodec.source(parent.source())), "final lifecycle child changed original parent/source/body");
                try { var same = locked.writerSession(); var prepared = same.preview(child.request()); child.rememberPrepared(prepared); var committed = same.commit(prepared);
                    return new org.xar.ck3.control.application.lifecycle.LifecycleCommit(prepared, committed, same.head().documents());
                } catch (java.io.IOException failure) { throw new java.io.UncheckedIOException(failure); }
            }
        };
        ActionPorts.PostconditionResult result;
        try { result = ActionChildPlanningScope.withinContinuation(locked, parent, retained.handlerId(), token.deadline(), () -> source.continueOriginal(parent, retained, token, children)); }
        catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); result = new ActionPorts.Pending("successor continuation interrupted; original children retained", List.of()); }
        catch (ReadPublicationRequiredException publication) { throw publication; }
        catch (RuntimeException failure) { result = new ActionPorts.Pending(ActionCoordinator.diagnostic("source-qualified continuation incomplete", failure), List.of()); }
        finally { active.set(false); }
        var cursor = ((ActionState.CompositeUnknown) locked.find(parent.actionId()).orElseThrow().state()).execution();
        ActionReceipt finished = CompositeCoordinatorSupport.finish(locked, parent, original.bodySha256(), cursor, Objects.requireNonNull(result),source);
        return new CompositeContinuationReport(finished, created, created.isEmpty() ? CompositeContinuationReport.Disposition.NO_NEW_CHILD_ATTEMPT : CompositeContinuationReport.Disposition.NEW_CHILD_ATTEMPT);
    }
}
