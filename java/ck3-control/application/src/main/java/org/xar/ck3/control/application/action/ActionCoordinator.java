package org.xar.ck3.control.application.action;

import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;

/** One assembled instance per Game. Durable intent, one native write, independent later observation, one writer. */
public final class ActionCoordinator implements ActionCoordinatorPort {
    private final String authorityId;
    private final ActionJournal journal;
    private final ActionPorts.GuardPort guard;
    private final ActionPorts.PreparationPort preparation;
    private final NativeActionPort nativePort;
    private final ActionPorts.PostconditionPort postcondition;
    private final Clock clock;
    private final CompositeRegistry composites;
    private final ActionPorts.IntentPreparationPort intentPreparation;
    private final ActionPorts.AttemptCompletionPort attemptCompletion;
    private final ActionPorts.IntentBarrierPort intentBarrier;
    private volatile ActionPorts.ReconciliationObservationPort reconciliationObservation;
    private boolean reconciliationStarted;
    private volatile PhysicalActionRegistry physicalActions;
    private volatile org.xar.ck3.control.application.presentation.DecisionDisplay decisionDisplay;
    private volatile boolean decisionDisplayStarted;
    /** Read-only audience observations bind once; they possess no submit or writer capability. */
    public synchronized void bindDecisionDisplay(org.xar.ck3.control.application.presentation.DecisionDisplay actual) {
        StrictJson.require(decisionDisplay == null && !decisionDisplayStarted, "decision display binds once before coordinator use");
        decisionDisplay = Objects.requireNonNull(actual);
    }
    public synchronized void bindPhysicalActions(PhysicalActionRegistry actual) {
        StrictJson.require(physicalActions == null, "physical source registry is installed once on the original coordinator");
        physicalActions = Objects.requireNonNull(actual); actual.bindCoordinator(this);
    }

    /** Root installs its actual physical authority once. An unbound instance cannot qualify gameplay reconciliation. */
    public synchronized void bindReconciliationObservation(ActionPorts.ReconciliationObservationPort actual) {
        StrictJson.require(reconciliationObservation == null && !reconciliationStarted, "reconciliation observation authority is installed once before use");
        reconciliationObservation = Objects.requireNonNull(actual);
    }

    public ActionCoordinator(String authorityId, ActionJournal journal, ActionPorts.GuardPort guard,
            ActionPorts.PreparationPort preparation, NativeActionPort nativePort, ActionPorts.PostconditionPort postcondition, Clock clock) {
        this(authorityId, journal, guard, preparation, nativePort, postcondition, clock, new CompositeRegistry(List.of()));
    }
    public ActionCoordinator(String authorityId, ActionJournal journal, ActionPorts.GuardPort guard,
            ActionPorts.PreparationPort preparation, NativeActionPort nativePort, ActionPorts.PostconditionPort postcondition, Clock clock, CompositeRegistry composites) {
        this(authorityId, journal, guard, preparation, nativePort, postcondition, clock, composites, (session, command) -> { });
    }
    public ActionCoordinator(String authorityId, ActionJournal journal, ActionPorts.GuardPort guard,
            ActionPorts.PreparationPort preparation, NativeActionPort nativePort, ActionPorts.PostconditionPort postcondition, Clock clock,
            CompositeRegistry composites, ActionPorts.IntentPreparationPort intentPreparation) {
        this(authorityId, journal, guard, preparation, nativePort, postcondition, clock, composites, intentPreparation, (session, receipt) -> { });
    }
    public ActionCoordinator(String authorityId, ActionJournal journal, ActionPorts.GuardPort guard,
            ActionPorts.PreparationPort preparation, NativeActionPort nativePort, ActionPorts.PostconditionPort postcondition, Clock clock,
            CompositeRegistry composites, ActionPorts.IntentPreparationPort intentPreparation, ActionPorts.AttemptCompletionPort attemptCompletion) {
        this(authorityId, journal, guard, preparation, nativePort, postcondition, clock, composites, intentPreparation, attemptCompletion, (session, command) -> { });
    }
    public ActionCoordinator(String authorityId, ActionJournal journal, ActionPorts.GuardPort guard,
            ActionPorts.PreparationPort preparation, NativeActionPort nativePort, ActionPorts.PostconditionPort postcondition, Clock clock,
            CompositeRegistry composites, ActionPorts.IntentPreparationPort intentPreparation, ActionPorts.AttemptCompletionPort attemptCompletion,
            ActionPorts.IntentBarrierPort intentBarrier) {
        this.authorityId = StrictJson.text(authorityId); this.journal = Objects.requireNonNull(journal); this.guard = Objects.requireNonNull(guard);
        this.preparation = Objects.requireNonNull(preparation); this.nativePort = Objects.requireNonNull(nativePort);
        this.postcondition = Objects.requireNonNull(postcondition); this.clock = Objects.requireNonNull(clock);
        this.composites = Objects.requireNonNull(composites);
        this.intentPreparation = Objects.requireNonNull(intentPreparation);
        this.attemptCompletion = Objects.requireNonNull(attemptCompletion);
        this.intentBarrier = Objects.requireNonNull(intentBarrier);
    }
    @Override public ActionReceipt execute(ActionCommand command) {
        Objects.requireNonNull(command);
        return journal.locked(locked -> ActionScope.run(command.actionId(), () -> executeLocked(locked, command, List.of())));
    }
    @Override public ActionReceipt execute(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed, ActionCommand command) {
        Objects.requireNonNull(command);
        return journal.locked(borrowed, locked -> ActionScope.run(command.actionId(), () -> executeLocked(locked, command, List.of())));
    }
    /** Only the installed automatic physical producer can use this same writer/journal path. */
    private void requireOutsideCaptureReadOnly(ActionCommand command) {
        if(preparation instanceof RootExecutableBindings installed) {
            try{installed.requireOutsideCaptureReadOnly(command.origin().game());}
            catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}
        }
    }
    private void collectPhysical(ActionJournal.LockedJournal locked) {
        if(preparation instanceof RootExecutableBindings installed) {
            try{installed.requireOutsideCaptureReadOnly();}
            catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}
        }
        PhysicalActionRegistry registry=Objects.requireNonNull(physicalActions,"actual physical source registry required");
        PhysicalCoordinatorSupport.collect(locked,registry);
    }
    public ActionReceipt deferAutomatic(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,ActionCommand command) {
        return journal.locked(same,locked->{
            requireOutsideCaptureReadOnly(Objects.requireNonNull(command));
            PhysicalActionRegistry registry=Objects.requireNonNull(physicalActions,"actual physical source registry required");
            return PhysicalCoordinatorSupport.defer(locked,command,registry,authorityId,clock,intentPreparation,intentBarrier);
        });
    }
    public void collectAutomatic(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same) {
        journal.locked(same,locked->{collectPhysical(locked);return true;});
    }
    private ActionReceipt executeLocked(ActionJournal.LockedJournal locked, ActionCommand command, List<String> ancestors) {
        return ActionCommandScope.within(command, () -> ActionReadPublicationScope.within(locked, command, intentBarrier,
                () -> {
                    displayBefore(locked, command, ancestors, false);
                    try {
                        ActionReceipt actual = executeOwnedLocked(locked, command, ancestors);
                        displayReturned(actual); return actual;
                    } catch (RuntimeException failure) {
                        displayUnavailable(command); throw failure;
                    }
                }));
    }
    private ActionReceipt executeOwnedLocked(ActionJournal.LockedJournal locked, ActionCommand command, List<String> ancestors) {
            preparation.requireOutsideReadOnlyScope(locked.writerSession(), command);
            if(physicalActions!=null)collectPhysical(locked);
            String digest = ActionCodec.bodySha256(command);
            Optional<ActionReceipt> existing = locked.find(command.actionId());
            if (existing.isPresent()) {
                StrictJson.require(existing.orElseThrow().bodySha256().equals(digest), "action ID body conflict");
                return existing.orElseThrow(); // Even INTENT/SUBMITTING/UNKNOWN are returned, never retried.
            }
            PhysicalActionRegistry.VerifiedPresentations optional;
            try{optional=physicalActions==null?null:physicalActions.verified(locked.writerSession(),locked.snapshot());}
            catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}
            StrictJson.require(locked.unresolved().stream().allMatch(receipt -> ancestors.contains(receipt.command().actionId()) || optional!=null&&optional.contains(receipt)), "another action is unresolved; global action authority remains isolated");
            ProtocolIdentityAdmission.requireUnique(locked.snapshot().actions(), command);
            PhysicalActionRegistry physical = physicalActions;
            if (physical != null && physical.find(command.operation()).isPresent())
                return PhysicalCoordinatorSupport.execute(locked, command, physical, authorityId, clock, intentPreparation, intentBarrier);
            GuardEvidence initial = guard.verify(locked.head(), command); verifyGuard(command, initial, authorityId, clock.instant());
            checkBarrier(locked, command);
            Optional<CompositeActionPort> composite = composites.find(command.operation());
            if (composite.isPresent()) {
                StrictJson.require(ancestors.isEmpty() || CompositeContinuationNesting.authorizes(command, ancestors), "nested composites require the exact source-owned successor Life continuation");
                return CompositeCoordinatorSupport.execute(locked, command, digest, composite.orElseThrow(), initial, clock, intentPreparation, intentBarrier,
                        child -> ActionScope.run(child.actionId(), () -> executeLocked(locked, child, appendAncestor(ancestors, command.actionId()))));
            }
            try { return executePrimitive(locked, command, digest, initial); }
            finally {
                locked.find(command.actionId()).filter(receipt -> ActionTransitions.attempt(receipt.state()).isPresent())
                        .ifPresent(receipt -> attemptCompletion.afterAttempt(locked.writerSession(), receipt));
            }
    }
    private ActionReceipt executePrimitive(ActionJournal.LockedJournal locked, ActionCommand command, String digest, GuardEvidence initial) {
            preparation.requireProtocolIdentity(command);
            String requestId = RequestIds.forCommand(command);
            NativeRequest request;
            var priorHead = locked.head();
            try { request = Objects.requireNonNull(preparation.prepare(locked.writerSession(), command, requestId)); }
            catch (IllegalArgumentException failure) {
                // executeOwnedLocked already returned every existing selected action; unchanged ACTION head preserves its absence.
                if (Objects.equals(ContinuityActionJournal.recordHead(priorHead.state()), ContinuityActionJournal.recordHead(locked.head().state())))
                    throw new PreIntentContractRejection(command, failure);
                throw failure;
            }
            NativeStepDiscriminator.requireRequest(command.operation(), ExecutableStepBindings.Kind.ACTION, request);
            checkBarrier(locked, command);
            ActionPreparationScope.within(locked.writerSession(), command, request,
                    () -> intentPreparation.prepare(locked.writerSession(), command));
            checkBarrier(locked, command);
            ActionReceipt intent = append(locked, command, digest, new ActionState.IntentDurable());
            GuardEvidence atSubmission;
            try { atSubmission = guard.verify(locked.head(), command); verifyGuard(command, atSubmission, authorityId, clock.instant()); checkBarrier(locked, command); }
            catch (ReadPublicationRequiredException publication) {
                StrictJson.require(java.util.Arrays.equals(ActionCodec.encodeCommand(publication.command()), ActionCodec.encodeCommand(command)), "READ barrier changed the original command");
                ActionState.Attempt neverSent = new ActionState.Attempt(requestId, clock.instant(), initial, request);
                var zero = new NativeActionPort.ZeroDispatchProof(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE, 0, "actual READ publication required before primitive write", Optional.empty());
                ActionReceipt rejected = append(locked, command, digest, new ActionState.RejectedBeforeDispatch(neverSent, new NativeActionPort.RejectedBeforeDispatch(requestId, zero)));
                throw new ReadPublicationRequiredException(command, Optional.of(rejected));
            }
            catch (PreSubmissionRevisionMismatchException mismatch) {
                ActionState.Attempt planned = new ActionState.Attempt(requestId, clock.instant(), initial, request);
                var proof = new NativeActionPort.ZeroDispatchProof(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE, 0, "pre-submission-revision-mismatch", Optional.empty());
                ActionReceipt rejected = append(locked, command, digest, new ActionState.RejectedBeforeDispatch(planned, new NativeActionPort.RejectedBeforeDispatch(requestId, proof)));
                throw new PreSubmissionRevisionMismatchException(mismatch.current(), Optional.of(rejected));
            }
            catch (RuntimeException failure) {
                try {
                    ActionState.Attempt neverSent = new ActionState.Attempt(requestId, clock.instant(), initial, request);
                    var zero = new NativeActionPort.ZeroDispatchProof(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE, 0,
                            diagnostic("guard/barrier failure before dispatch", failure), Optional.empty());
                    append(locked, command, digest, new ActionState.RejectedBeforeDispatch(neverSent,
                            new NativeActionPort.RejectedBeforeDispatch(requestId, zero)));
                } catch (RuntimeException recordingFailure) {
                    if (recordingFailure != failure) failure.addSuppressed(recordingFailure);
                }
                throw failure;
            }
            Instant submittedAt = clock.instant();
            ActionState.Attempt attempt = new ActionState.Attempt(requestId, submittedAt, atSubmission, request);
            ActionReceipt submitting = append(locked, command, digest, new ActionState.Submitting(attempt));
            SubmissionPermit permit = new SubmissionPermit(command, digest, submitting.sequence(), requestId, submittedAt, atSubmission, request);
            permit.beforeFirstWrite(()->{
                PhysicalActionRegistry registry=physicalActions;if(registry==null)return;
                for(var binding:registry.installed())try{
                    binding.producer().beforeNative(locked.writerSession(),command,atSubmission,locked.snapshot().actions(),
                        camera->PhysicalCoordinatorSupport.defer(locked,camera,registry,authorityId,clock,intentPreparation,intentBarrier));
                }catch(java.io.IOException|RuntimeException cameraUnavailable){ /* Optional presentation never replays or replaces the original native action. */ }
            });
            NativeActionPort.DispatchOutcome outcome;
            try { outcome = Objects.requireNonNull(nativePort.submit(permit, request, command.deadline())); }
            catch (InterruptedException interrupted) {
                Thread.interrupted();
                try { return append(locked, command, digest, unknown(attempt, Optional.empty(), "interrupted after SUBMITTING; no replay")); }
                finally { Thread.currentThread().interrupt(); }
            } catch (RuntimeException failure) {
                return append(locked, command, digest, unknown(attempt, Optional.empty(), diagnostic("native dispatch result unknown", failure)));
            }
            if (!outcome.requestId().equals(requestId))
                return append(locked, command, digest, unknown(attempt, Optional.empty(), "native return request ID mismatch; preserve SUBMITTING, no replay"));
            if (outcome instanceof NativeActionPort.RejectedBeforeDispatch rejected)
                return append(locked, command, digest, new ActionState.RejectedBeforeDispatch(attempt, rejected));
            ActionReceipt returned = outcome instanceof NativeActionPort.AckReceived ack
                    ? append(locked, command, digest, new ActionState.AckReceived(attempt, ack))
                    : append(locked, command, digest, unknown(attempt, Optional.of(outcome), ((NativeActionPort.Unknown) outcome).reason()));
            if(physicalActions!=null)collectPhysical(locked);
            displayReturned(returned); // Native ACK remains separate from the independent later observer.
            return observe(locked, returned, attempt, outcome);
    }
    @Override public CompositeContinuationReport continueOriginalComposite(CompositeContinuationToken token) throws java.io.IOException {
        Objects.requireNonNull(token);
        try { return journal.locked(locked -> ActionScope.run(token.originalParent().actionId(), () -> continueLocked(locked, token))); }
        catch (java.io.UncheckedIOException failure) { throw failure.getCause(); }
    }
    @Override public CompositeContinuationReport continueOriginalComposite(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed,
            CompositeContinuationToken token) throws java.io.IOException {
        Objects.requireNonNull(borrowed); Objects.requireNonNull(token);
        try { return journal.locked(borrowed, locked -> ActionScope.run(token.originalParent().actionId(), () -> continueLocked(locked, token))); }
        catch (java.io.UncheckedIOException failure) { throw failure.getCause(); }
    }
    private CompositeContinuationReport continueLocked(ActionJournal.LockedJournal locked, CompositeContinuationToken token) {
        preparation.requireOutsideReadOnlyScope(locked.writerSession(), token.originalParent());
        displayBefore(locked, token.originalParent(), List.of(), true);
        try {
            CompositeContinuationReport actual = ActionCommandScope.within(token.originalParent(), () -> CompositeContinuationSupport.continueOriginal(locked, token, composites, clock,
                    child -> ActionScope.run(child.actionId(), () -> executeLocked(locked, child, List.of(token.originalParent().actionId())))));
            displayReturned(actual.parent()); return actual;
        } catch (RuntimeException failure) {
            displayUnavailable(token.originalParent()); throw failure;
        }
    }
    @Override public ActionReceipt reconcile(String actionId) {
        StrictJson.text(actionId);
        return journal.locked(locked -> ActionScope.run(actionId, () -> reconcileLocked(locked, actionId)));
    }
    @Override public ActionReceipt reconcile(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed, String actionId) {
        StrictJson.text(actionId);
        return journal.locked(borrowed, locked -> ActionScope.run(actionId, () -> reconcileLocked(locked, actionId)));
    }
    private ActionReceipt reconcileLocked(ActionJournal.LockedJournal locked, String actionId) {
        return reconcileLocked(locked, actionId, List.of());
    }
    private ActionReceipt reconcileLocked(ActionJournal.LockedJournal locked, String actionId, List<String> ancestors) {
        Optional<ActionReceipt> original = locked.find(actionId);
        original.ifPresent(receipt -> displayBefore(locked, receipt.command(), ancestors, true));
        try {
        Optional<DirectFixedWindowQueryContinuation> supplied = DirectFixedWindowQueryInvocation.claim(locked.writerSession(), actionId);
        ActionReceipt actual = supplied.isPresent() ? reconcileDirectQueryLocked(locked, supplied.orElseThrow())
                : ActionObservationWindow.reconcile(actionId, clock, () -> observeRetainedLocked(locked, actionId, ancestors));
        displayReturned(actual); return actual;
        } catch (RuntimeException failure) {
            original.ifPresent(receipt -> displayUnavailable(receipt.command())); throw failure;
        }
    }
    private ActionReceipt observeRetainedLocked(ActionJournal.LockedJournal locked, String actionId, List<String> ancestors) {
            ActionReceipt current = locked.find(actionId).orElseThrow(() -> new IllegalArgumentException("unknown action ID"));
            return ActionCommandScope.within(current.command(), () -> reconcileOwnedLocked(locked, current, ancestors));
    }
    private ActionReceipt reconcileOwnedLocked(ActionJournal.LockedJournal locked, ActionReceipt retained, List<String> ancestors) {
            preparation.requireOutsideReadOnlyScope(locked.writerSession(), retained.command());
            ActionReceipt current = retained;
            if (current.settled()) return current;
            if (current.state() instanceof PhysicalActionState) {
                PhysicalActionRegistry physical = physicalActions;
                StrictJson.require(physical != null, "original physical source registry is unavailable; no replay");
                return PhysicalCoordinatorSupport.observe(locked, current, physical, clock);
            }
            Optional<CompositeExecution> composite = ActionTransitions.composite(current.state());
            if (composite.isPresent()) {
                for (CompositeExecution.Child child : composite.orElseThrow().children()) {
                    Optional<ActionReceipt> recorded = locked.find(child.actionId());
                    if (recorded.isEmpty()) {
                        if (current.state() instanceof ActionState.CompositeUnknown) return current;
                        return append(locked, current.command(), current.bodySha256(), new ActionState.CompositeUnknown(composite.orElseThrow(),
                                "reserved child has no durable intent; preserve its original identity and do not submit", List.of()));
                    }
                    ActionReceipt fact = recorded.orElseThrow();
                    StrictJson.require(fact.bodySha256().equals(child.bodySha256()), "retained composite child body drift");
                    if (!fact.settled()) ActionScope.run(child.actionId(), () -> reconcileLocked(locked, child.actionId(), appendAncestor(ancestors, retained.command().actionId())));
                }
                ActionPorts.PostconditionResult result;
                try { result = composites.require(composite.orElseThrow().handlerId()).observe(current.command(), composite.orElseThrow()); }
                catch (RuntimeException failure) { result = new ActionPorts.Pending(diagnostic("composite read-only reconciliation unavailable", failure), List.of()); }
                return CompositeCoordinatorSupport.finish(locked, current.command(), current.bodySha256(), composite.orElseThrow(), result, composites.require(composite.orElseThrow().handlerId()));
            }
            Optional<ActionState.Attempt> attempt = ActionTransitions.attempt(current.state());
            if (attempt.isEmpty()) {
                if (current.state() instanceof ActionState.IntentDurable && current.command().operation().value().equals("resume-map")) {
                    Optional<ActionState.IntentAbandoned> abandoned = locked.abandonableIntent(current);
                    if (abandoned.isPresent()) return append(locked, current.command(), current.bodySha256(), abandoned.orElseThrow());
                }
                if (current.state() instanceof ActionState.Unknown) return current;
                return append(locked, current.command(), current.bodySha256(), new ActionState.Unknown(Optional.empty(), Optional.empty(), "restored intent without a durable send proof; reconciliation only", List.of()));
            }
            NativeActionPort.DispatchOutcome dispatch = ActionTransitions.dispatch(current.state()).orElseGet(() ->
                    new NativeActionPort.Unknown(attempt.orElseThrow().requestId(), "restored SUBMITTING has no definitive ACK", new byte[0], Optional.empty()));
            if (current.state() instanceof ActionState.Submitting)
                current = append(locked, current.command(), current.bodySha256(), unknown(attempt.orElseThrow(), Optional.of(dispatch), "restored SUBMITTING is unknown; no replay"));
            return observe(locked, current, attempt.orElseThrow(), dispatch, true);
    }
    private ActionReceipt observe(ActionJournal.LockedJournal locked, ActionReceipt current, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch) {
        return observe(locked, current, attempt, dispatch, false);
    }
    private ActionReceipt observe(ActionJournal.LockedJournal locked, ActionReceipt current, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch, boolean reconciliation) {
        ActionCommand command = current.command(); String digest = current.bodySha256();
        if (dispatch instanceof NativeActionPort.AckReceived ack && ack.outbound().isEmpty())
            return append(locked, command, digest, unknown(attempt, Optional.of(dispatch), "ACK has no retained actual outbound packet; effect qualification unavailable, no replay"));
        ActionPorts.PostconditionResult result;
        try {
            if (reconciliation && command.expectation() instanceof CommandExpectation.OperatorRebind) {
                result = observeOperatorReconciliation(locked, current, attempt, dispatch);
            } else if (reconciliation && command.origin() instanceof CommandOrigin.Gameplay) {
                ActionPorts.ReconciliationObservationPort actual;
                synchronized (this) { reconciliationStarted = true; actual = reconciliationObservation; }
                if (command.operation().value().equals("private-assign-councillor-v1"))
                    result = new ActionPorts.Pending("Council mailbox continuation requires its canonical issued/collect chain; generic reconciliation cannot issue STATUS", List.of(attempt.guard().nativeEvidence()));
                else if (actual == null)
                    result = new ActionPorts.Pending("actual original-pending reconciliation observation authority is unavailable; no replay", List.of(attempt.guard().nativeEvidence()));
                else {
                    boolean[] entered = {false};
                    ActionPorts.PostconditionResult[] observed = {null};
                    result = Objects.requireNonNull(actual.observe(locked.writerSession(), current, ActionObservationWindow.deadline(command),
                            (frame, provenance, identity, basis) -> {
                                StrictJson.require(!entered[0], "a reconciliation authority may enter the original observer only once");
                                entered[0] = true;
                                return observed[0] = ActionReconciliationScope.within(locked, current, attempt, frame, provenance, identity, basis,
                                        authorityId, ActionObservationWindow.deadline(command), clock,
                                        () -> Objects.requireNonNull(postcondition.observe(command, attempt, dispatch)));
                            }));
                    StrictJson.require(!entered[0] || result == observed[0], "reconciliation provider replaced the actual observer result");
                    StrictJson.require(entered[0] || result instanceof ActionPorts.Pending, "raw-only observation cannot invent a semantic settlement");
                }
            } else result = Objects.requireNonNull(postcondition.observe(command, attempt, dispatch));
        } catch (InterruptedException interrupted) {
            Thread.interrupted();
            try { return append(locked, command, digest, unknown(attempt, Optional.of(dispatch), "read-only reconciliation interrupted; original request retained, no replay")); }
            finally { Thread.currentThread().interrupt(); }
        } catch (java.io.IOException failure) {
            return append(locked, command, digest, unknown(attempt, Optional.of(dispatch), "read-only reconciliation source unavailable:" + failure.getClass().getName() + "; no replay"));
        }
        catch (RuntimeException failure) { return append(locked, command, digest, unknown(attempt, Optional.of(dispatch), diagnostic("postcondition unavailable", failure))); }
        if (result instanceof ActionPorts.Pending pending)
            return append(locked, command, digest, new ActionState.Unknown(Optional.of(attempt), Optional.of(dispatch), pending.reason(), pending.evidence()));
        if (result instanceof ActionPorts.ControlSequenceObserved)
            return append(locked, command, digest, unknown(attempt, Optional.of(dispatch), "control sequence belongs to its registered composite; original primitive retained, no replay"));
        if (result instanceof ActionPorts.CompositeControlObserved)
            return append(locked, command, digest, unknown(attempt, Optional.of(dispatch), "composite control cannot settle a primitive; original dispatch retained, no replay"));
        if (result instanceof ActionPorts.SwaySchedulerObserved)
            return append(locked, command, digest, unknown(attempt, Optional.of(dispatch), "canonical Sway scheduler proof belongs to its registered composite; primitive dispatch retained, no replay"));
        if (result instanceof ActionPorts.LifecycleObserved)
            return append(locked, command, digest, unknown(attempt, Optional.of(dispatch), "canonical lifecycle proof belongs to its registered composite; primitive dispatch retained, no replay"));
        if (result instanceof ActionPorts.CompositeRejectionObserved)
            return append(locked, command, digest, unknown(attempt, Optional.of(dispatch), "composite rejected children cannot settle a primitive; original dispatch retained, no replay"));
        if(result instanceof ActionPorts.FixtureBusinessObserved)
            return append(locked,command,digest,unknown(attempt,Optional.of(dispatch),"fixture business proof belongs only to its original composite; no replay"));
        if(result instanceof ActionPorts.CompositeNoGameplayWriteObserved || result instanceof ActionPorts.LifeControlPrefixInterruptedObserved)
            return append(locked,command,digest,unknown(attempt,Optional.of(dispatch),"no-gameplay-write proof belongs only to its original composite; no replay"));
        ActionState.Settlement settlement = switch (result) {
            case ActionPorts.FixtureStartObserved started -> new ActionState.FixtureStarted(started.observation());
            case ActionPorts.FixtureBusinessObserved ignored -> throw new IllegalArgumentException("fixture business proof cannot settle a primitive");
            case ActionPorts.DirectFixedWindowObserved completed -> new ActionState.DirectFixedWindowCompleted(completed.completion());
            case ActionPorts.PauseObserved pause -> new ActionState.PauseConfirmed(pause.observation());
            case ActionPorts.ControlSequenceObserved ignored -> throw new IllegalArgumentException("control sequence cannot settle a primitive");
            case ActionPorts.OperatorRebindObserved rebound -> new ActionState.OperatorRebound(rebound.observation());
            case ActionPorts.NativeSourceObserved source -> new ActionState.NativeSourceCompleted(source.observation());
            case ActionPorts.NormalExitPhaseObserved phase -> new ActionState.NormalExitPhaseConfirmed(phase.observation());
            case ActionPorts.FamilySendObserved sent -> new ActionState.FamilySendConfirmed(sent.observation());
            case ActionPorts.EffectObserved effect -> new ActionState.Applied(effect.observation());
            case ActionPorts.ControlObserved control -> control.observation();
            case ActionPorts.FrontendObserved frontend -> new ActionState.FrontendApplied(frontend.observation());
            case ActionPorts.GameplayEntryObserved entered -> new ActionState.GameplayEntered(entered.observation());
            case ActionPorts.RejectionObserved rejected -> rejected.rejection();
            case ActionPorts.TerminalObserved terminal -> new ActionState.NonAppliedTerminal(terminal.observation());
            case ActionPorts.LifecycleControlObserved control -> new ActionState.LifecycleControlApplied(control.observation());
            case ActionPorts.CompositeRejectionObserved ignored -> throw new IllegalArgumentException("composite rejection cannot settle a primitive");
            case ActionPorts.CompositeControlObserved ignored -> throw new IllegalArgumentException("composite control cannot settle a primitive");
            case ActionPorts.SwaySchedulerObserved ignored -> throw new IllegalArgumentException("Sway scheduler proof cannot settle a primitive");
            case ActionPorts.LifecycleObserved ignored -> throw new IllegalArgumentException("lifecycle proof cannot settle a primitive");
            case ActionPorts.CompositeNoGameplayWriteObserved ignored -> throw new IllegalArgumentException("no-gameplay-write proof cannot settle a primitive");
            case ActionPorts.LifeControlPrefixInterruptedObserved ignored -> throw new IllegalArgumentException("Life control-prefix interruption cannot settle a primitive");
            case ActionPorts.Pending ignored -> throw new IllegalStateException("pending was already handled");
        };
        try { ActionEffects.validate(command, attempt, dispatch, settlement); }
        catch (RuntimeException failure) { return append(locked, command, digest, unknown(attempt, Optional.of(dispatch), diagnostic("postcondition not proven", failure))); }
        return append(locked, command, digest, new ActionState.Settled(attempt, dispatch, settlement));
    }
    private ActionPorts.PostconditionResult observeOperatorReconciliation(ActionJournal.LockedJournal locked,
            ActionReceipt current, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch)
            throws java.io.IOException, InterruptedException {
        ActionCommand command = current.command();
        StrictJson.require(command.expectation() instanceof CommandExpectation.OperatorRebind, "typed operator expectation required");
        ActionReceipt retained = locked.find(command.actionId()).orElseThrow(() -> new IllegalArgumentException("original operator is absent"));
        StrictJson.require(!retained.settled() && retained.sequence() == current.sequence()
                && retained.bodySha256().equals(current.bodySha256())
                && java.util.Arrays.equals(ActionCodec.encodeCommand(retained.command()), ActionCodec.encodeCommand(command))
                && ActionTransitions.attempt(retained.state()).filter(attempt::equals).isPresent()
                && ActionTransitions.dispatch(retained.state()).filter(dispatch::equals).isPresent(),
                "operator reconciliation changed its actual canonical original request/attempt/dispatch");
        if (!(dispatch instanceof NativeActionPort.AckReceived ack))
            return new ActionPorts.Pending("operator reconciliation has no original ACK; no replay", List.of(attempt.guard().nativeEvidence()));
        ack.custody().orElseThrow(() -> new IllegalArgumentException("original operator ACK receive custody is unavailable")).verify(ack, attempt.guard());
        boolean[] entered = {false}; ActionPorts.PostconditionResult[] observed = {null};
        ActionPorts.PostconditionResult result = Objects.requireNonNull(preparation.observeOperatorReconciliation(
                locked.writerSession(), retained, ActionObservationWindow.deadline(command), () -> {
                    StrictJson.require(!entered[0], "the actual operator source may enter its original observer only once");
                    entered[0] = true;
                    var actual = Objects.requireNonNull(postcondition.observe(command, attempt, dispatch));
                    StrictJson.require(ack.nativeOk() || actual instanceof ActionPorts.RejectionObserved || actual instanceof ActionPorts.Pending,
                            "negative original operator ACK can only retain pending or prove its finite source-owned rejection");
                    return observed[0] = actual;
                }));
        StrictJson.require(!entered[0] || result == observed[0], "operator source replaced the actual observer result");
        StrictJson.require(entered[0] || result instanceof ActionPorts.Pending, "unentered operator source cannot invent a settlement");
        StrictJson.require(ack.nativeOk() || result instanceof ActionPorts.RejectionObserved || result instanceof ActionPorts.Pending,
                "negative original operator ACK cannot rebind identity or grant another effect");
        return result;
    }

    /** Consumes one already completed owner query under the original journal lock; it never dispatches or recaptures. */
    private ActionReceipt reconcileDirectQueryLocked(ActionJournal.LockedJournal locked, DirectFixedWindowQueryContinuation token) {
        Objects.requireNonNull(token); StrictJson.text(token.actionId()); Objects.requireNonNull(token.deadline());
        ActionReceipt retained = locked.find(token.actionId()).orElseThrow(() -> new IllegalArgumentException("original close action is absent"));
        ActionCommand command = retained.command();
        preparation.requireOutsideReadOnlyScope(locked.writerSession(), command);
        StrictJson.require(clock.instant().isBefore(token.deadline()), "original owner query continuation expired");
        StrictJson.require(command.origin() instanceof CommandOrigin.Gameplay
                && (command.operation().value().equals("close-war-declared-overview-v1")
                    || command.operation().value().equals("close-war-results-window-v1")),
                "only the finite original gameplay window CLOSE may consume an owner query");
        // A repeated public query cannot reopen or mutate a previously settled attempt.
        if (retained.settled()) return retained;
        StrictJson.require(retained.state() instanceof ActionState.Unknown, "owner query requires the canonical original UNKNOWN close");
        ActionState.Attempt attempt = ActionTransitions.attempt(retained.state()).orElseThrow(() -> new IllegalArgumentException("original close attempt is absent"));
        NativeActionPort.DispatchOutcome dispatch = ActionTransitions.dispatch(retained.state()).orElseThrow(() -> new IllegalArgumentException("original close dispatch is absent"));
        if (!(dispatch instanceof NativeActionPort.AckReceived ack) || !ack.nativeOk()) return retained;
        ack.custody().orElseThrow(() -> new IllegalArgumentException("original close receive custody is absent")).verify(ack, attempt.guard());
        PlanningReadReceipt query = Objects.requireNonNull(token.queryReceipt()); Objects.requireNonNull(token.queryRef());
        StrictJson.require(query.request().origin() instanceof CommandOrigin.Gameplay
                && query.before().guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                && query.after().guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                && query.request().source().equals(command.source()) && query.request().sessionId().equals(command.sessionId())
                && query.request().origin().game().equals(command.origin().game())
                && query.request().origin().machineId().equals(command.origin().machineId())
                && !query.requestId().equals(attempt.requestId()), "supplied public query crossed the exact original owner/source/Game or ordinary QUERY profile");
        NativeRequestChronology.requireSampledAfter(query, attempt, ack);
        return ActionCommandScope.within(command, () -> {
            boolean[] entered = {false}; ActionPorts.PostconditionResult[] observed = {null};
            ActionPorts.PostconditionResult result;
            try {
                result = Objects.requireNonNull(preparation.observeOriginalDirectWindowQuery(locked.writerSession(), retained, token, () -> {
                    StrictJson.require(!entered[0], "original owner query may enter its observer only once");
                    entered[0] = true;
                    ActionReceipt current = locked.find(command.actionId()).orElseThrow();
                    StrictJson.require(current.equals(retained), "original close changed while binding its actual query");
                    return observed[0] = Objects.requireNonNull(postcondition.observe(command, attempt, dispatch));
                }));
            } catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt(); throw new java.io.UncheckedIOException(new java.io.IOException("original owner query interrupted; no replay", interrupted));
            } catch (java.io.IOException failure) { throw new java.io.UncheckedIOException(failure); }
            StrictJson.require(!entered[0] || result == observed[0], "owner query source replaced its actual observer result");
            StrictJson.require(entered[0] || result instanceof ActionPorts.Pending, "unentered owner query cannot invent completion");
            if (result instanceof ActionPorts.Pending pending) {
                if (!entered[0]) return retained;
                return append(locked, command, retained.bodySha256(), new ActionState.Unknown(Optional.of(attempt),
                        Optional.of(dispatch), pending.reason(), pending.evidence()));
            }
            StrictJson.require(result instanceof ActionPorts.DirectFixedWindowObserved, "owner query cannot grant another settlement");
            var completion = ((ActionPorts.DirectFixedWindowObserved) result).completion();
            ActionState.DirectFixedWindowCompleted completed = new ActionState.DirectFixedWindowCompleted(completion);
            ActionEffects.validate(command, attempt, dispatch, completed);
            return append(locked, command, retained.bodySha256(), new ActionState.Settled(attempt, dispatch, completed));
        });
    }

    private static List<String> appendAncestor(List<String> previous, String originalParent) {
        StrictJson.require(previous.size() < 2, "bounded successor continuation nesting exceeded");
        var next = new java.util.ArrayList<>(previous); next.add(originalParent); return List.copyOf(next);
    }
    static void verifyGuard(ActionCommand command, GuardEvidence evidence, String authorityId, Instant now) {
        StrictJson.require(now.isBefore(command.deadline()) && !now.isBefore(evidence.observedAt()) && !now.isAfter(evidence.validUntil()), "expired or future native guard");
        StrictJson.require(evidence.source().equals(command.source())
                && evidence.sessionId().equals(command.sessionId()) && evidence.operation().equals(command.operation())
                && evidence.authorityId().equals(authorityId), "pre-dispatch Game/frame/source/session/capability/authority changed");
        StrictJson.require(evidence.origin().machineId().equals(command.origin().machineId()) && evidence.origin().game().equals(command.origin().game()), "pre-dispatch Game/process birth changed");
        if (command.origin() instanceof CommandOrigin.Gameplay gameplay) {
            StrictJson.require(evidence.origin() instanceof CommandOrigin.Gameplay, "pre-dispatch origin phase changed");
            var actual = evidence.origin().requireGameplay(); var expected = gameplay.before();
            StrictJson.require(actual.frame().episodeRunId().equals(expected.frame().episodeRunId())
                    && actual.frame().identity().player().equals(expected.frame().identity().player()), "pre-dispatch player/episode changed");
        } else if (command.origin() instanceof CommandOrigin.LifecycleTerminal lifecycle) {
            StrictJson.require(evidence.origin() instanceof CommandOrigin.LifecycleTerminal
                    && lifecycle.identity().sameSession(evidence.origin().requireLifecycleTerminal()), "pre-dispatch terminal subject/session changed");
            StrictJson.require(!evidence.supportingEvidence().isEmpty(), "terminal dispatch needs actual lifecycle source custody");
        } else StrictJson.require(evidence.origin() instanceof CommandOrigin.Frontend
                && command.origin().requireFrontend().sameSession(evidence.origin().requireFrontend()), "pre-dispatch frontend session changed");
        if (!command.origin().acceptsGuard(evidence.origin())) throw new PreSubmissionRevisionMismatchException(evidence, Optional.empty());
    }
    private static ActionState.Unknown unknown(ActionState.Attempt attempt, Optional<NativeActionPort.DispatchOutcome> dispatch, String reason) {
        return new ActionState.Unknown(Optional.of(attempt), dispatch, reason, List.of(attempt.guard().nativeEvidence()));
    }
    private void checkBarrier(ActionJournal.LockedJournal locked, ActionCommand command) {
        try { intentBarrier.check(locked.writerSession(), command); }
        catch (ReadPublicationRequiredException publication) {
            StrictJson.require(java.util.Arrays.equals(ActionCodec.encodeCommand(publication.command()), ActionCodec.encodeCommand(command))
                    && publication.zeroDispatchReceipt().isEmpty(), "only the coordinator may attach its actual durable zero-dispatch receipt"); throw publication;
        }
    }
    private void displayBefore(ActionJournal.LockedJournal locked, ActionCommand command, List<String> ancestors, boolean readOnly) {
        decisionDisplayStarted = true;
        var display = decisionDisplay;
        if (display == null) return;
        try {
            boolean retained = locked.find(command.actionId()).isPresent();
            display.preparing(command, () -> ancestors.stream().map(id -> locked.find(id).orElseThrow(
                    () -> new IllegalStateException("actual canonical display parent absent")).command()).toList(), readOnly || retained);
        } catch (RuntimeException unavailable) { display.callUnavailable(command); }
    }
    private void displayReturned(ActionReceipt actual) {
        var display = decisionDisplay; if (display != null) display.returned(actual);
    }
    private void displayUnavailable(ActionCommand original) {
        var display = decisionDisplay; if (display != null) display.callUnavailable(original);
    }
    static ActionReceipt append(ActionJournal.LockedJournal locked, ActionCommand command, String digest, ActionState next) {
        ActionTransitions.validate(locked.find(command.actionId()), command, digest, next);
        ActionReceipt receipt = locked.append(command, digest, next);
        StrictJson.require(java.util.Arrays.equals(ActionCodec.encodeCommand(receipt.command()), ActionCodec.encodeCommand(command))
                && receipt.bodySha256().equals(digest) && receipt.state().equals(next), "writer did not return the exact durable action event"); return receipt;
    }
    static String diagnostic(String context, RuntimeException failure) {
        String message = context + ":" + failure.getClass().getName() + ":" + String.valueOf(failure.getMessage());
        return message.length() <= 2048 ? message : message.substring(0, 2048);
    }
}


