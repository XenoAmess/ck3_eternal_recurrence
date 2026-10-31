package org.xar.ck3.control.application.action;

import java.time.Clock;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.Function;
import org.xar.ck3.control.contracts.StrictJson;

/** Same coordinator, same durable writer, bounded children. It is not another attempt runner. */
final class CompositeCoordinatorSupport {
    private CompositeCoordinatorSupport() { }
    static ActionReceipt execute(ActionJournal.LockedJournal locked, ActionCommand parent, String digest,
            CompositeActionPort handler, GuardEvidence guard, Clock clock, ActionPorts.IntentPreparationPort intentPreparation,
            ActionPorts.IntentBarrierPort intentBarrier,
            Function<ActionCommand, ActionReceipt> executeChild) {
        boolean fixture=handler instanceof FixtureCompositeActionPort&&FixturePlan.isParent(parent);
        if(fixture)FixturePlan.requireParent(parent);
        StrictJson.require(fixture || parent.origin() instanceof CommandOrigin.Gameplay || parent.origin() instanceof CommandOrigin.LifecycleTerminal
                && parent.lifecycleExpected().operation() != LifecycleExpectedPostcondition.Operation.CLOSE_DEATH_MODAL,
                "only gameplay or an exact canonical terminal lifecycle composite may own children");
        handler.validate(parent); intentBarrier.check(locked.writerSession(), parent);
        intentPreparation.prepare(locked.writerSession(), parent); intentBarrier.check(locked.writerSession(), parent);
        ActionCoordinator.append(locked, parent, digest, new ActionState.IntentDurable());
        CompositeExecution execution = new CompositeExecution(handler.handlerId(), clock.instant(), guard, List.of());
        ActionCoordinator.append(locked, parent, digest, new ActionState.CompositeRunning(execution));
        AtomicBoolean active = new AtomicBoolean(true);
        CompositeActionPort.Children children = new CompositeActionPort.Children() {
            private CompositeExecution current() {
                StrictJson.require(active.get(), "composite child custody has closed");
                ActionState state = locked.find(parent.actionId()).orElseThrow().state();
                StrictJson.require(state instanceof ActionState.CompositeRunning, "composite parent is no longer running"); return ((ActionState.CompositeRunning) state).execution();
            }
            @Override public String nextActionId() { return ActionIds.child(parent.actionId(), current().children().size() + 1); }
            @Override public String nextActionId(OperationKey operation) { return ActionIds.child(parent.actionId(), current().children().size() + 1, operation); }
            @Override public List<ActionReceipt> completed() {
                List<ActionReceipt> result = new ArrayList<>();
                for (CompositeExecution.Child child : current().children()) {
                    ActionReceipt receipt = locked.find(child.actionId()).orElseThrow();
                    StrictJson.require(receipt.bodySha256().equals(child.bodySha256()) && receipt.settled(), "composite child is unknown or body changed; do not continue"); result.add(receipt);
                }
                return List.copyOf(result);
            }
            @Override public ActionReceipt submit(ActionCommand child) {
                CompositeExecution previous = current(); completed();
                StrictJson.require(child.actionId().equals(nextActionId(child.operation())) && child.sessionId().equals(parent.sessionId()) && child.source().equals(parent.source())
                        && !child.deadline().isAfter(parent.deadline()), "child ID/source/session/deadline crossed parent authority");
                if(fixture){
                    StrictJson.require((child.origin() instanceof CommandOrigin.Frontend||child.origin() instanceof CommandOrigin.Gameplay)
                            &&child.origin().machineId().equals(parent.origin().machineId())&&child.origin().game().equals(parent.origin().game()),
                            "fixture child crossed its actual held Game or unsupported phase");
                    ((FixtureCompositeActionPort)handler).requireFixtureChild(parent,previous,child);
                }else if (parent.origin() instanceof CommandOrigin.Gameplay) {
                    StrictJson.require(child.origin() instanceof CommandOrigin.Gameplay
                            && child.before().machineId().equals(parent.before().machineId()) && child.before().game().equals(parent.before().game())
                            && child.before().frame().episodeRunId().equals(parent.before().frame().episodeRunId())
                            && child.before().frame().identity().player().equals(parent.before().frame().identity().player()), "gameplay child crossed its parent Game/player/episode");
                } else {
                    StrictJson.require(child.origin() instanceof CommandOrigin.LifecycleTerminal
                            && parent.lifecycleExpected().operation() == LifecycleExpectedPostcondition.Operation.CONTINUE_SUCCESSOR
                            && child.lifecycleExpected().operation() == LifecycleExpectedPostcondition.Operation.CLOSE_DEATH_MODAL,
                            "only the exact source-bound death-modal primitive may be a terminal lifecycle native child");
                    LifecycleIdentity before = parent.lifecycleBefore(), actual = child.lifecycleBefore();
                    StrictJson.require(before.sameSession(actual) && actual.subject().driverVersion() >= before.subject().driverVersion()
                            && before.currentPlayer().equals(actual.currentPlayer()) && before.terminalReason() == actual.terminalReason()
                            && before.frame().dateRaw().equals(actual.frame().dateRaw())
                            && actual.frame().nativeRevision().compareTo(before.frame().nativeRevision()) >= 0,
                            "terminal child changed the old subject/current native actor/episode/date/source session");
                }
                StrictJson.require(!clock.instant().isAfter(parent.deadline()), "composite parent deadline expired");
                List<CompositeExecution.Child> bound = new ArrayList<>(previous.children()); bound.add(new CompositeExecution.Child(child.actionId(), ActionCodec.bodySha256(child)));
                ActionCoordinator.append(locked, parent, digest, new ActionState.CompositeRunning(new CompositeExecution(previous.handlerId(), previous.startedAt(), previous.guard(), bound)));
                ActionReceipt receipt = executeChild.apply(child);
                StrictJson.require(receipt.settled(), "composite child outcome is unknown; no following primitive or cleanup may submit"); return receipt;
            }
            @Override public org.xar.ck3.control.application.lifecycle.LifecycleCommit lifecycle(org.xar.ck3.control.application.lifecycle.LifecycleChild child) {
                Objects.requireNonNull(child); current(); completed();
                StrictJson.require(clock.instant().isBefore(parent.deadline()), "lifecycle parent deadline expired");
                String operation = switch (child.phase()) {
                    case DEATH_RECORDED -> "death-terminal";
                    case SUCCESSOR_COMMITTED, SUCCESSOR_PENDING_FINALIZED -> "continue-as-reconciled-successor";
                    case NEXT_EPISODE_ENTERED, NEXT_EPISODE_COMMITTED -> "start-next-episode";
                };
                var details = child.request().detailsObject();
                StrictJson.require(child.parentActionId().equals(parent.actionId()) && parent.operation().value().equals(operation)
                        && child.request().kind().equals(org.xar.ck3.control.application.lifecycle.LifecycleChild.KIND)
                        && StrictJson.text(details.get("parent_action_id")).equals(parent.actionId())
                        && StrictJson.text(details.get("parent_body_sha256")).equals(digest)
                        && StrictJson.text(details.get("operation")).equals(parent.operation().value())
                        && details.get("source").equals(org.xar.ck3.control.g2.planning.ProposalLifecycleCodec.source(parent.source())), "lifecycle child crossed its exact registered parent/source/body/phase");
                try {
                    var session = locked.writerSession(); var prepared = session.preview(child.request()); child.rememberPrepared(prepared); var committed = session.commit(prepared);
                    return new org.xar.ck3.control.application.lifecycle.LifecycleCommit(prepared, committed, session.head().documents());
                } catch (java.io.IOException failure) { throw new java.io.UncheckedIOException(failure); }
            }
        };
        ActionPorts.PostconditionResult result;
        try { result = Objects.requireNonNull(ActionChildPlanningScope.within(locked, parent, handler.handlerId(), () -> handler.run(parent, children))); }
        catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); result = new ActionPorts.Pending("composite interrupted; retain all child facts, no replay", List.of()); }
        catch (ReadPublicationRequiredException publication) {
            CompositeExecution actual = ((ActionState.CompositeRunning) locked.find(parent.actionId()).orElseThrow().state()).execution();
            ActionCoordinator.append(locked, parent, digest, new ActionState.CompositeUnknown(actual,
                    "READ publication interrupted the original composite; retain actual child history and reconcile only", List.of()));
            throw publication;
        }
        catch (RuntimeException failure) { result = new ActionPorts.Pending(ActionCoordinator.diagnostic("composite incomplete", failure), List.of()); }
        finally { active.set(false); }
        CompositeExecution retained = ((ActionState.CompositeRunning) locked.find(parent.actionId()).orElseThrow().state()).execution();
        return finish(locked, parent, digest, retained, result,handler);
    }
    static ActionReceipt finish(ActionJournal.LockedJournal locked, ActionCommand parent, String digest, CompositeExecution retained, ActionPorts.PostconditionResult result) {
        return finish(locked,parent,digest,retained,result,null);
    }
    static ActionReceipt finish(ActionJournal.LockedJournal locked, ActionCommand parent, String digest, CompositeExecution retained,
            ActionPorts.PostconditionResult result,CompositeActionPort actualSource) {
        if (result instanceof ActionPorts.CompositeNoGameplayWriteObserved noGameplay) {
            ActionReceipt current = locked.find(parent.actionId()).orElseThrow();
            if (!(current.state() instanceof ActionState.CompositeUnknown unknown)) {
                if (current.state() instanceof ActionState.CompositeRunning running)
                    return ActionCoordinator.append(locked, current.command(), current.bodySha256(), new ActionState.CompositeUnknown(
                            running.execution(), "no-gameplay-write terminal requires canonical read-only reconciliation", List.of()));
                return current;
            }
            if (!current.command().equals(parent) || !current.bodySha256().equals(digest)
                    || !unknown.execution().equals(retained) || !retained.children().isEmpty()) return current;
            if (!(actualSource instanceof CompositeActionPort.ZeroGameplayBeforeChildren zeroSource)
                    || !zeroSource.handlerId().equals(retained.handlerId()) || !zeroSource.supports(parent.operation())) return current;
            try {
                noGameplay.observation().validate(parent, retained);
                zeroSource.requireNoGameplayWrite(parent, retained);
                var settlement = new ActionState.CompositeNoGameplayWrite(noGameplay.observation());
                ActionEffects.validateComposite(parent, retained, settlement);
                ActionEffects.validateCompositeChildren(retained, settlement, List.of());
            } catch (RuntimeException failure) {
                return current;
            }
            return ActionCoordinator.append(locked, parent, digest, new ActionState.CompositeSettled(retained, new ActionState.CompositeNoGameplayWrite(noGameplay.observation())));
        }
        if (!(result instanceof ActionPorts.FixtureBusinessObserved) && !(result instanceof ActionPorts.ControlSequenceObserved) && !(result instanceof ActionPorts.EffectObserved) && !(result instanceof ActionPorts.CompositeControlObserved) && !(result instanceof ActionPorts.LifecycleObserved) && !(result instanceof ActionPorts.CompositeRejectionObserved) && !(result instanceof ActionPorts.SwaySchedulerObserved)) {
            String reason = result instanceof ActionPorts.Pending pending ? pending.reason() : "composite has no independently verified semantic terminal observation";
            return ActionCoordinator.append(locked, parent, digest, new ActionState.CompositeUnknown(retained, reason, result instanceof ActionPorts.Pending pending ? pending.evidence() : List.of()));
        }
        List<ActionReceipt> canonicalChildren = new ArrayList<>();
        for (CompositeExecution.Child child : retained.children()) {
            ActionReceipt receipt = locked.find(child.actionId()).orElseThrow();
            if (!receipt.settled() || !receipt.bodySha256().equals(child.bodySha256()))
                return ActionCoordinator.append(locked, parent, digest, new ActionState.CompositeUnknown(retained, "child remains unresolved; root cannot settle",
                        result instanceof ActionPorts.CompositeRejectionObserved rejected ? rejected.evidence() : List.of()));
            canonicalChildren.add(receipt);
        }
        ActionState.Settlement settlement = result instanceof ActionPorts.FixtureBusinessObserved completed ? new ActionState.FixtureBusinessCompleted(completed.observation())
                : result instanceof ActionPorts.ControlSequenceObserved sequence ? new ActionState.ControlSequenceCompleted(sequence.observation())
                : result instanceof ActionPorts.EffectObserved effect ? new ActionState.Applied(effect.observation())
                : result instanceof ActionPorts.SwaySchedulerObserved scheduler ? new ActionState.SwaySchedulerCompleted(scheduler.proof())
                : result instanceof ActionPorts.LifecycleObserved lifecycle ? new ActionState.LifecycleApplied(lifecycle.proof())
                : result instanceof ActionPorts.CompositeRejectionObserved rejected ? new ActionState.CompositeRejected(rejected.reason(), rejected.children(), rejected.evidence())
                : new ActionState.CompositeControlApplied(((ActionPorts.CompositeControlObserved) result).observation());
        try {
            if(settlement instanceof ActionState.FixtureBusinessCompleted completed){
                StrictJson.require(actualSource instanceof FixtureCompositeActionPort&&actualSource.handlerId().equals(retained.handlerId())
                        &&actualSource.supports(parent.operation()),"fixture completion lost its identical registered composite source");
                ((FixtureCompositeActionPort)actualSource).requireFixtureCompletion(parent,retained,completed.observation());
            }
            ActionEffects.validateComposite(parent, retained, settlement); ActionEffects.validateCompositeChildren(retained, settlement, canonicalChildren);
        }
        catch (RuntimeException failure) { return ActionCoordinator.append(locked, parent, digest, new ActionState.CompositeUnknown(retained, ActionCoordinator.diagnostic("composite effect not proven", failure), List.of())); }
        return ActionCoordinator.append(locked, parent, digest, new ActionState.CompositeSettled(retained, settlement));
    }
}
