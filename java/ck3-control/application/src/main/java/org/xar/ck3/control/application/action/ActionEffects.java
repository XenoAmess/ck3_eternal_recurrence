package org.xar.ck3.control.application.action;

import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;

/** Used again in the authoritative writer reducer, not only in the caller before commit. */
public final class ActionEffects {
    private ActionEffects() { }
    /** Structural legacy entry. Read-dependent qualification requires the original dispatch as well. */
    public static void validate(ActionCommand command, ActionState.Attempt attempt, ActionState.Settlement settlement) {
        StrictJson.require(!(settlement instanceof ActionState.LifeControlPrefixInterrupted), "Life control-prefix interruption belongs only to its registered composite");
        StrictJson.require(!(settlement instanceof ActionState.FixtureStarted || settlement instanceof ActionState.FixtureBusinessCompleted || settlement instanceof ActionState.DirectFixedWindowCompleted || settlement instanceof ActionState.PauseConfirmed || settlement instanceof ActionState.ControlSequenceCompleted || settlement instanceof ActionState.ControlApplied || settlement instanceof ActionState.LifecycleControlApplied
                || settlement instanceof ActionState.NonAppliedTerminal || settlement instanceof ActionState.FamilySendConfirmed || settlement instanceof ActionState.NativeSourceCompleted || settlement instanceof ActionState.NormalExitPhaseConfirmed || settlement instanceof ActionState.OperatorRebound), "actual original dispatch and request chronology required for read-dependent settlement");
        validateStructure(command, attempt, settlement);
    }
    public static void validate(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome actualDispatch, ActionState.Settlement settlement) {
        StrictJson.require(!(settlement instanceof ActionState.LifeControlPrefixInterrupted), "Life control-prefix interruption belongs only to its registered composite");
        java.util.Objects.requireNonNull(actualDispatch);
        StrictJson.require(actualDispatch.requestId().equals(attempt.requestId()), "settlement changed the exact original dispatch");
        StrictJson.require(!(settlement instanceof ActionState.CompositeNoGameplayWrite), "no-gameplay-write settlement belongs only to its registered composite");
        if(settlement instanceof ActionState.FixtureStarted started){started.observation().validate(command,attempt,actualDispatch);return;}
        StrictJson.require(!(settlement instanceof ActionState.FixtureBusinessCompleted),"fixture business completion belongs only to its original registered composite");
        if (settlement instanceof ActionState.OperatorRebound rebound) {
            var expected = command.expectation().requireOperatorRebind(); expected.validateCommand(command);
            expected.validateCompletion(rebound.observation()); rebound.observation().validate(command, attempt, actualDispatch); return;
        }
        StrictJson.require(!(command.expectation() instanceof CommandExpectation.OperatorRebind) || settlement instanceof ActionState.Rejected,
                "operator expectation cannot settle as ordinary gameplay/control");
        if (settlement instanceof ActionState.DirectFixedWindowCompleted completed) {
            StrictJson.require(command.origin() instanceof CommandOrigin.Gameplay
                    && command.expectation() instanceof CommandExpectation.Gameplay,
                    "direct fixed-window completion belongs only to its actual gameplay primitive");
            completed.completion().validate(command, attempt, actualDispatch); return;
        }
        if (settlement instanceof ActionState.PauseConfirmed pause) { PauseConfirmation.validate(command, attempt, actualDispatch, pause.observation()); return; }
        StrictJson.require(!(settlement instanceof ActionState.ControlSequenceCompleted), "control sequence belongs to its registered composite");
        if (settlement instanceof ActionState.NativeSourceCompleted source) { source.observation().validate(command, attempt, actualDispatch); return; }
        if (settlement instanceof ActionState.NormalExitPhaseConfirmed phase) { phase.observation().validate(command, attempt, actualDispatch); return; }
        if (settlement instanceof ActionState.FamilySendConfirmed sent) {
            sent.observation().validate(command, attempt, actualDispatch); return;
        }
        validateStructure(command, attempt, settlement);
        if (settlement instanceof ActionState.ControlApplied control) {
            NativeActionPort.AckReceived ack = controlAcknowledgement(command, attempt, actualDispatch, control);
            var read = control.read();
            if (reconciliationClockControl(command, read)) {
                NativeRequestChronology.requireReconciledSampledAfter(read, command, attempt, ack);
            } else {
                NativeRequestChronology.requireSampledAfter(read, attempt, ack);
            }
            control.supportingReads().forEach(supporting -> NativeRequestChronology.requireSampledAfter(supporting, attempt, ack));
        } else if (settlement instanceof ActionState.LifecycleControlApplied control) {
            NativeActionPort.AckReceived ack = successfulAck(actualDispatch);
            NativeRequestChronology.requireBeforeSubmission(control.observation().beforeStatus(), attempt, ack);
            NativeRequestChronology.requireSampledAfter(control.observation().independentRead(), attempt, ack);
        } else if (settlement instanceof ActionState.NonAppliedTerminal terminal) {
            PlanningReadReceipt read = terminal.observation().afterCollection(); NativeRequestChronology query = requireChronology(read);
            if (actualDispatch instanceof NativeActionPort.AckReceived ack && ack.nativeOk())
                NativeRequestChronology.requireSampledAfter(read, attempt, ack);
            else {
                StrictJson.require(actualDispatch instanceof NativeActionPort.Unknown,
                        "a non-applied terminal cannot reinterpret a rejected or never-written submission");
                StrictJson.require(!query.writeEntered().observedAt().isBefore(attempt.submittedAt()),
                        "terminal collection query predates the canonical original attempt");
            }
        }
    }
    /** The original UNKNOWN remains the dispatch. Only the actual same-request late original supplies control chronology. */
    public static NativeActionPort.AckReceived controlAcknowledgement(ActionCommand command, ActionState.Attempt attempt,
            NativeActionPort.DispatchOutcome original, ActionState.ControlApplied control) {
        if (control.reconciledAck().isPresent()) {
            var observed = control.reconciledAck().orElseThrow(); observed.requireMatches(command, attempt, original); return observed.ack();
        }
        return successfulAck(original);
    }
    private static NativeActionPort.AckReceived successfulAck(NativeActionPort.DispatchOutcome original) {
        StrictJson.require(original instanceof NativeActionPort.AckReceived ack && ack.nativeOk(), "exact successful original ACK required for ordered control sampling");
        return (NativeActionPort.AckReceived) original;
    }
    private static NativeRequestChronology requireChronology(PlanningReadReceipt read) {
        NativeRequestChronology actual = read.original().custody().orElseThrow(() -> new IllegalArgumentException("actual query chronology is absent; historical data grants no sampling freshness"));
        actual.verify(read); return actual;
    }
    private static boolean reconciliationClockControl(ActionCommand command, PlanningReadReceipt read) {
        return command.origin() instanceof CommandOrigin.Gameplay
                && command.expected().observerSchema().equals(org.xar.ck3.control.application.advance.AdvancePrimitives.CLOCK_OBSERVER)
                && (command.operation().value().startsWith(org.xar.ck3.control.application.advance.ClockStatusRead.ARM_PREFIX)
                    || command.operation().value().startsWith(org.xar.ck3.control.application.advance.ClockStatusRead.CANCEL_PREFIX))
                && read.request().origin() instanceof CommandOrigin.Reconciliation
                && read.contractId().equals("java.tactical-daily-sentinel.status.reconciliation.v1")
                && read.before().guardMode() == ReadContract.GuardMode.RECONCILIATION_OBSERVATION
                && read.after().guardMode() == ReadContract.GuardMode.RECONCILIATION_OBSERVATION;
    }
    private static void validateStructure(ActionCommand command, ActionState.Attempt attempt, ActionState.Settlement settlement) {
        StrictJson.require(!(settlement instanceof ActionState.DirectFixedWindowCompleted || settlement instanceof ActionState.PauseConfirmed || settlement instanceof ActionState.ControlSequenceCompleted), "typed pause/control sequence requires its exact dispatch or canonical children");
        StrictJson.require(!(settlement instanceof ActionState.SwaySchedulerCompleted), "Sway scheduler publication only settles its registered composite");
        if (settlement instanceof ActionState.LifecycleControlApplied control) { control.observation().validate(command, attempt); return; }
        StrictJson.require(!(settlement instanceof ActionState.CompositeRejected), "canonical child rejection only settles its registered composite");
        if (settlement instanceof ActionState.NonAppliedTerminal terminal) { terminal.observation().validate(command, attempt); return; }
        StrictJson.require(!(settlement instanceof ActionState.LifecycleApplied), "canonical lifecycle settlement requires its registered composite");
        if (settlement instanceof ActionState.Rejected rejected) {
            StrictJson.require(rejected.requestId().equals(attempt.requestId()), "terminal rejection must bind the exact original command"); return;
        }
        if (settlement instanceof ActionState.FrontendApplied frontend) {
            frontend.observation().validate(command, attempt); return;
        }
        if (settlement instanceof ActionState.GameplayEntered entered) {
            entered.observation().validate(command, attempt); return;
        }
        StrictJson.require(command.origin() instanceof CommandOrigin.Gameplay, "gameplay/control settlement requires an actual gameplay origin");
        StrictJson.require(!(settlement instanceof ActionState.CompositeControlApplied), "composite control cannot settle a primitive");
        if (settlement instanceof ActionState.ControlApplied control) {
            PlanningReadReceipt read = control.read();
            StrictJson.require(read.original().nativeOk() && !read.requestId().equals(attempt.requestId()), "native control effect needs an independent successful Status read");
            StrictJson.require(read.request().sessionId().equals(command.sessionId()), "native control read changed session");
            var observed = reconciliationClockControl(command, read)
                    ? read.after().binding().origin().requireReconciliation().factual() : read.after().binding().observed();
            StrictJson.require(ProposalLifecycle.compare(command.expected(), observed, read.request().source(), control.observerSchema(), control.actual())
                    == ProposalLifecycle.ObservationComparison.EXPECTED_FIELDS_MATCH, "native control Status did not prove the exact expected generation/state");
            java.util.HashSet<String> requestIds = new java.util.HashSet<>(); requestIds.add(read.requestId());
            for (PlanningReadReceipt supporting : control.supportingReads()) {
                StrictJson.require(supporting.original().nativeOk() && requestIds.add(supporting.requestId()) && !supporting.requestId().equals(attempt.requestId()), "supporting read failed or is not independent");
                StrictJson.require(supporting.request().source().equals(command.source()) && supporting.request().sessionId().equals(command.sessionId())
                        && supporting.after().binding().observed().game().equals(command.before().game())
                        && supporting.after().binding().observed().frame().episodeRunId().equals(command.before().frame().episodeRunId())
                        && supporting.after().binding().observed().frame().identity().player().equals(command.before().frame().identity().player()), "supporting read source/Game/player/episode changed");
            }
            return;
        }
        ActionState.EffectObservation effect = ((ActionState.Applied) settlement).observation();
        StrictJson.require(effect.sessionId().equals(command.sessionId()), "effect session drift");
        effect.provenance().validate(effect.after(), effect.originalEvidence());
        StrictJson.require(effect.provenance().independentOf(attempt.requestId()), "an ACK cannot double as an independent effect read");
        StrictJson.require(!effect.originalEvidence().equals(attempt.guard().nativeEvidence()), "effect must retain a different original packet from its before guard");
        StrictJson.require(!effect.observedAt().isBefore(attempt.submittedAt()), "effect observation precedes original submission");
        StrictJson.require(!effect.after().frame().snapshotId().equals(command.before().frame().snapshotId())
                && effect.after().frame().identity().nativeRevision().compareTo(command.before().frame().identity().nativeRevision()) > 0,
                "effect needs an independent later native frame");
        StrictJson.require(ProposalLifecycle.compare(command.expected(), effect.after(), effect.source(), effect.observerSchema(), effect.actual())
                == ProposalLifecycle.ObservationComparison.EXPECTED_FIELDS_MATCH, "fresh independent postcondition did not match");
    }
    public static void validateComposite(ActionCommand command, CompositeExecution execution, ActionState.Settlement settlement) {
        if(settlement instanceof ActionState.FixtureBusinessCompleted completed){
            completed.observation().validateParent(command);
            StrictJson.require(execution.guard().origin() instanceof CommandOrigin.Frontend
                    &&execution.guard().origin().requireFrontend().sameSession(command.origin().requireFrontend()),"fixture parent lost its original frontend guard");return;
        }
        if (settlement instanceof ActionState.LifeControlPrefixInterrupted interrupted) {
            interrupted.observation().validateParent(command, execution);
            return;
        }
        if (settlement instanceof ActionState.CompositeNoGameplayWrite noGameplay) {
            noGameplay.observation().validate(command, execution);
            StrictJson.require(execution.children().isEmpty(), "no-gameplay-write requires empty canonical child vector");
            return;
        }
        StrictJson.require(!FixturePlan.isParent(command)&&!(settlement instanceof ActionState.FixtureStarted),"fixture parent or primitive cannot reinterpret another terminal contract");
        StrictJson.require(!(settlement instanceof ActionState.DirectFixedWindowCompleted || settlement instanceof ActionState.PauseConfirmed), "direct execution and pause confirmations are exact native primitives");
        if (settlement instanceof ActionState.ControlSequenceCompleted sequence) {
            org.xar.ck3.control.application.effects.control.ControlSequenceObservation.validateParent(command);
            StrictJson.require(java.util.Arrays.equals(ActionCodec.encodeCommand(command), ActionCodec.encodeCommand(sequence.observation().parent())),
                    "control sequence changed its complete original parent command");
            return;
        }
        StrictJson.require(!(settlement instanceof ActionState.OperatorRebound) && !(command.expectation() instanceof CommandExpectation.OperatorRebind), "operator rebind is an exact primitive, never a composite");
        StrictJson.require(!(settlement instanceof ActionState.FamilySendConfirmed), "an outgoing family request settles only its exact original primitive; composite relationship credit is unavailable");
        if (settlement instanceof ActionState.SwaySchedulerCompleted scheduler) { scheduler.proof().validateParent(command); return; }
        if (settlement instanceof ActionState.LifecycleApplied lifecycle) { lifecycle.proof().validateParent(command); return; }
        StrictJson.require(command.origin() instanceof CommandOrigin.Gameplay, "ordinary composites require gameplay; terminal lifecycle uses its dedicated canonical proof");
        if (settlement instanceof ActionState.CompositeRejected rejected) {
            if(!rejected.evidence().isEmpty()) {
                org.xar.ck3.control.application.advance.GenericPublicPauseRecovery.validateParent(command);
                StrictJson.require(rejected.evidence().size()==1,"public pause rejection retains one exact replayable report");
            }
            StrictJson.require(rejected.children().equals(execution.children()), "composite rejection must retain the complete exact canonical child history"); return;
        }
        if (settlement instanceof ActionState.CompositeControlApplied control) {
            validateCompositeControl(command, execution, control.observation()); return;
        }
        StrictJson.require(settlement instanceof ActionState.Applied, "composite root must have a real semantic terminal observation, not a child ACK or clock-only read");
        ActionState.EffectObservation effect = ((ActionState.Applied) settlement).observation();
        effect.provenance().validate(effect.after(), effect.originalEvidence());
        StrictJson.require(!effect.originalEvidence().equals(execution.guard().nativeEvidence()), "composite terminal needs a different original semantic packet");
        StrictJson.require(effect.sessionId().equals(command.sessionId()) && !effect.observedAt().isBefore(execution.startedAt()), "composite effect source/session/time drift");
        StrictJson.require(!effect.after().frame().snapshotId().equals(command.before().frame().snapshotId())
                && effect.after().frame().identity().nativeRevision().compareTo(command.before().frame().identity().nativeRevision()) > 0, "composite needs independently observed later native state");
        StrictJson.require(ProposalLifecycle.compare(command.expected(), effect.after(), effect.source(), effect.observerSchema(), effect.actual())
                == ProposalLifecycle.ObservationComparison.EXPECTED_FIELDS_MATCH, "composite actual postcondition did not match");
    }
    /** Shared terminal semantic projection. Control-only observations never become gameplay/day credit. */
    public static java.util.Optional<ActionState.EffectObservation> observation(ActionReceipt receipt) {
        if (receipt.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.PauseConfirmed pause)
            return java.util.Optional.of(pause.observation());
        java.util.Optional<ActionState.Applied> applied = receipt.applied();
        if (applied.isPresent()) return java.util.Optional.of(applied.orElseThrow().observation());
        if (receipt.state() instanceof ActionState.CompositeSettled settled
                && settled.settlement() instanceof ActionState.CompositeControlApplied control)
            return java.util.Optional.of(control.observation().semantic());
        return java.util.Optional.empty();
    }
    /** Original physical material to be re-decoded by the exact registered archived verifier. */
    public static java.util.List<org.xar.ck3.control.contracts.ExactRef> supportingEvidence(ActionState.Settlement settlement) {
        if(settlement instanceof ActionState.FixtureStarted started)return started.observation().references();
        if(settlement instanceof ActionState.FixtureBusinessCompleted completed)return completed.observation().references();
        if (settlement instanceof ActionState.LifeControlPrefixInterrupted interrupted) return java.util.List.of(interrupted.observation().ending().nativeFrame(), interrupted.observation().ending().driverFacts(), interrupted.observation().ending().semantic());
        if (settlement instanceof ActionState.CompositeRejected rejected) return rejected.evidence();
        if (settlement instanceof ActionState.DirectFixedWindowCompleted completed) return completed.completion().references();
        if (settlement instanceof ActionState.PauseConfirmed pause) {
            var refs = new java.util.ArrayList<org.xar.ck3.control.contracts.ExactRef>();
            refs.add(pause.observation().originalEvidence()); refs.addAll(pause.observation().supportingEvidence()); return java.util.List.copyOf(refs);
        }
        if (settlement instanceof ActionState.ControlSequenceCompleted sequence) return sequence.observation().references();
        if (settlement instanceof ActionState.OperatorRebound rebound) return rebound.observation().references();
        if (settlement instanceof ActionState.NativeSourceCompleted source) return source.observation().references();
        if (settlement instanceof ActionState.NormalExitPhaseConfirmed phase) return phase.observation().references();
        if (settlement instanceof ActionState.Applied applied) return applied.observation().supportingEvidence();
        if (settlement instanceof ActionState.CompositeControlApplied control) return control.observation().semantic().supportingEvidence();
        if (settlement instanceof ActionState.GameplayEntered entered) return entered.observation().references();
        if (settlement instanceof ActionState.LifecycleApplied lifecycle) return lifecycle.proof().originalEvidence();
        if (settlement instanceof ActionState.SwaySchedulerCompleted scheduler) return scheduler.proof().originalEvidence();
        if (settlement instanceof ActionState.FrontendApplied frontend) return frontend.observation().references();
        if (settlement instanceof ActionState.Rejected rejected) return java.util.List.of(rejected.originalEvidence());
        if (settlement instanceof ActionState.NonAppliedTerminal terminal) return terminal.observation().references();
        if (settlement instanceof ActionState.LifecycleControlApplied control) return control.observation().references();
        return java.util.List.of();
    }
    private static void validateCompositeControl(ActionCommand command, CompositeExecution execution, CompositeControlObservation control) {
        ActionState.EffectObservation effect = control.semantic(); PlanningReadReceipt terminal = control.terminalStatus();
        StrictJson.require(terminal.original().nativeOk() && terminal.request().source().equals(command.source())
                && terminal.request().sessionId().equals(command.sessionId()), "terminal Status must be successful and source/session bound");
        NativeRequestChronology terminalCustody = requireChronology(terminal);
        StrictJson.require(!terminalCustody.writeEntered().observedAt().isBefore(execution.startedAt()), "terminal Status query predates the original composite");
        // A frozen SEM packet can predate a fresh query; actual request custody supplies query time.
        effect.provenance().validate(effect.after(), effect.originalEvidence());
        StrictJson.require(effect.sessionId().equals(command.sessionId()) && effect.provenance().independentOf(terminal.requestId())
                && !effect.originalEvidence().equals(execution.guard().nativeEvidence()), "zero-day semantic evidence must be independent of guard and Status");
        requireSameControlFrame(command.before(), effect.after());
        requireSameControlFrame(effect.after(), terminal.after().binding().observed());
        java.util.HashSet<String> requests = new java.util.HashSet<>(); requests.add(terminal.requestId());
        for (PlanningReadReceipt read : control.supportingReads()) {
            StrictJson.require(read.original().nativeOk() && read.request().source().equals(command.source())
                    && read.request().sessionId().equals(command.sessionId())
                    && !requireChronology(read).writeEntered().observedAt().isBefore(execution.startedAt()), "supporting control query is stale, failed or out of scope");
            requireSameControlFrame(command.before(), read.after().binding().observed());
            StrictJson.require(effect.provenance().independentOf(read.requestId()), "semantic packet cannot double as a control query ACK");
            requests.add(read.requestId());
        }
        for (String field : java.util.List.of("native.gameplay_verified", "timeline.advance_verified", "timeline.checkpoint_eligible"))
            StrictJson.require(effect.actual().contains(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey(field), false)), "zero-day control must explicitly decline gameplay, advance and SAVE credit");
        StrictJson.require(ProposalLifecycle.compare(command.expected(), effect.after(), effect.source(), effect.observerSchema(), effect.actual())
                == ProposalLifecycle.ObservationComparison.EXPECTED_FIELDS_MATCH, "zero-day parent observation did not match the original exact expectation");
    }
    private static void requireSameControlFrame(ProposalLifecycle.ObservationIdentity expected, ProposalLifecycle.ObservationIdentity actual) {
        StrictJson.require(expected.machineId().equals(actual.machineId()) && expected.game().equals(actual.game())
                && expected.observationVersion() == actual.observationVersion()
                && expected.frame().episodeRunId().equals(actual.frame().episodeRunId())
                && expected.frame().identity().player().equals(actual.frame().identity().player())
                && expected.frame().identity().dateRaw().equals(actual.frame().identity().dateRaw())
                && expected.frame().identity().nativeRevision().equals(actual.frame().identity().nativeRevision()), "zero-day control crossed Game/player/episode/date/native revision");
    }
    /** Repeated from the actual original writer head. A caller's list cannot grant child settlement. */
    public static void validateCompositeChildren(ActionCommand parent, CompositeExecution execution,
            ActionState.Settlement settlement, java.util.List<ActionReceipt> children) {
        java.util.Objects.requireNonNull(parent);
        if (settlement instanceof ActionState.LifeControlPrefixInterrupted interrupted) {
            interrupted.observation().validateParent(parent, execution);
            interrupted.observation().validateChildren(parent, children);
            return;
        }
        validateCompositeChildren(execution, settlement, children);
    }
    /** Legacy callers retain their exact previous rules; the new contract requires its actual parent. */
    public static void validateCompositeChildren(CompositeExecution execution, ActionState.Settlement settlement, java.util.List<ActionReceipt> children) {
        StrictJson.require(!(settlement instanceof ActionState.LifeControlPrefixInterrupted), "life control-prefix interruption requires its exact original parent command");
        StrictJson.require(children.size() == execution.children().size(), "complete canonical child history required");
        if (settlement instanceof ActionState.CompositeNoGameplayWrite noGameplay) {
            StrictJson.require(children.isEmpty() && execution.children().isEmpty()
                    && noGameplay.observation().execution().equals(execution),
                    "no-gameplay-write terminal must retain its exact empty canonical child history");
            return;
        }
        for (int index = 0; index < children.size(); index++) {
            ActionReceipt child = children.get(index); CompositeExecution.Child expected = execution.children().get(index);
            StrictJson.require(child.command().actionId().equals(expected.actionId()) && child.bodySha256().equals(expected.bodySha256())
                    && child.settled(), "composite cannot settle over a missing, conflicting or unresolved child");
        }
        if(settlement instanceof ActionState.FixtureBusinessCompleted completed){completed.observation().validateChildren(execution,children);return;}
        if (settlement instanceof ActionState.ControlSequenceCompleted sequence) { sequence.observation().validateChildren(execution, children); return; }
        if (settlement instanceof ActionState.SwaySchedulerCompleted scheduler) {
            scheduler.proof().newlyAppliedBusiness().ifPresent(business -> StrictJson.require(children.stream().anyMatch(child -> child.command().actionId().equals(business.childActionId())
                    && child.bodySha256().equals(business.childBodySha256()) && child.state() instanceof ActionState.Settled settled
                    && settled.settlement() instanceof ActionState.Applied), "new Sway business must be the exact canonical newly applied primitive child"));
            return;
        }
        if (settlement instanceof ActionState.CompositeRejected rejected) {
            StrictJson.require(rejected.children().equals(execution.children()) && !children.isEmpty(), "complete original rejected child chain required");
            if(!rejected.evidence().isEmpty()) {
                StrictJson.require(execution.guard().operation().equals(org.xar.ck3.control.application.effects.control.ControlSequenceObservation.OPERATION)
                        &&children.size()<=2&&rejected.evidence().size()==1,"only exact finite public pause may retain a failed control recovery");
                org.xar.ck3.control.application.effects.control.ControlSequenceObservation.requireMapUnavailable(children.getFirst());
                for(ActionReceipt child:children) {
                    StrictJson.require(child.command().operation().value().equals("pause-map")&&child.command().arguments().members().isEmpty(),
                            "failed public pause cannot hide another child operation");
                    var owner=execution.guard().observed();var actual=child.command().before();
                    StrictJson.require(child.command().source().equals(execution.guard().source())
                            &&child.command().sessionId().equals(execution.guard().sessionId())&&actual.machineId().equals(owner.machineId())
                            &&actual.game().equals(owner.game())&&actual.frame().episodeRunId().equals(owner.frame().episodeRunId())
                            &&actual.frame().identity().player().equals(owner.frame().identity().player()),
                            "failed public pause child crossed its actual source/Game/session/actor/episode");
                    StrictJson.require(child.state() instanceof ActionState.RejectedBeforeDispatch
                            || child.state() instanceof ActionState.Settled value && (value.settlement() instanceof ActionState.Rejected
                            || value.settlement() instanceof ActionState.PauseConfirmed || value.settlement() instanceof ActionState.ControlApplied),
                            "failed control recovery cannot erase gameplay or UNKNOWN");
                }
                return;
            }
            boolean actualRejected = false;
            for (ActionReceipt child : children) {
                if (child.state() instanceof ActionState.RejectedBeforeDispatch) continue;
                StrictJson.require(child.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.Rejected,
                        "negative parent cannot erase a successful, control-only or unresolved child");
                actualRejected = true;
            }
            StrictJson.require(actualRejected, "native rejected child proof required; all-zero children need their own terminal contract"); return;
        }
        if (!(settlement instanceof ActionState.CompositeControlApplied control)) return;
        boolean matchedControl = false;
        for (ActionReceipt child : children) {
            StrictJson.require(!child.command().operation().value().equals("resume-map"), "same-revision zero-day control cannot reinterpret a submitted resume");
            StrictJson.require(!(child.state() instanceof ActionState.Settled settled) || !(settled.settlement() instanceof ActionState.Applied), "zero-day control cannot erase a semantic mutation child");
            if (child.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.ControlApplied actual)
                matchedControl |= control.observation().supportingReads().contains(actual.read());
            ActionTransitions.attempt(child.state()).ifPresent(attempt -> {
                child.ack().ifPresent(ack -> NativeRequestChronology.requireSampledAfter(control.observation().terminalStatus(), attempt, ack));
                StrictJson.require(control.observation().semantic().provenance().independentOf(attempt.requestId())
                        && !control.observation().terminalStatus().requestId().equals(attempt.requestId()), "child submission ACK cannot become terminal Status/SEM proof");
            });
        }
        StrictJson.require(matchedControl, "zero-day terminal must retain an actual canonical child-control read");
    }
}

