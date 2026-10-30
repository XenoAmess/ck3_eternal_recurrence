package org.xar.ck3.control.application.planning.sway;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.application.planning.sway.SwayFormalState.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m6.M6TerminalSourceComposition;
import org.xar.ck3.control.g2.m6.SwayLifecycle;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Concrete Root pending producer, Native observer and original-evidence replay. All sending stays in ActionCoordinator. */
public final class SwayActionLifecycle {
    public static final String START_OBSERVER = "xar.java.sway-start-effect/v1";
    public static final String STOP_OBSERVER = "xar.java.sway-selected-stop-effect/v1";
    private static final String PROOF = "xar.java.sway-independent-effect-proof/v1";
    public record View(ObservationIdentity before, G2Source source, String sessionId, Instant deadline) {
        public View { Objects.requireNonNull(before); Objects.requireNonNull(source); StrictJson.text(sessionId); Objects.requireNonNull(deadline); }
    }
    /** Actual Root driver observation, on the borrowed writer scope. An unavailable reader must throw. */
    @FunctionalInterface public interface CurrentView { View current(ActionCommand original); }
    /** The sole Root read catalog issues and retains each exact definition; factories alone are not registered. */
    public interface RegisteredReads {
        ReadContract<SwayNativeWire.TargetRead> target(long target);
        ReadContract<SwayNativeWire.AppliedReceipt> receipt(long target, String actionId, java.math.BigInteger preEpoch);
        ReadContract<SwayObservationReads.Plane> plane(SwayObservationReads.Kind kind, org.xar.ck3.control.g2.m6.G2M6Contracts.Identity identity);
    }
    private final SwayCanonicalDomain domain;
    private final ActionPorts.OutcomeArchive archive;
    private final PlanningReadPort reads;
    private final RegisteredReads definitions;
    private final Supplier<ContinuityStorePort.Session> borrowed;
    private final CurrentView current;
    private final org.xar.ck3.control.application.effects.NativeEffectEvidence.FrameLoader frames;
    public SwayActionLifecycle(SwayCanonicalDomain domain, ActionPorts.OutcomeArchive archive, PlanningReadPort reads,
            RegisteredReads definitions, Supplier<ContinuityStorePort.Session> borrowed, CurrentView current,
            org.xar.ck3.control.application.effects.NativeEffectEvidence.FrameLoader frames) {
        this.domain = Objects.requireNonNull(domain); this.archive = Objects.requireNonNull(archive); this.reads = Objects.requireNonNull(reads);
        this.definitions = Objects.requireNonNull(definitions); this.borrowed = Objects.requireNonNull(borrowed); this.current = Objects.requireNonNull(current);
        this.frames = Objects.requireNonNull(frames);
    }
    public ActionPorts.IntentPreparationPort pendingProducer() {
        return (session, command) -> {
            try {
                ActionPorts.OutcomeArchive originals = archive.withSession(session); JsonNode row = StrictJson.parse(OpportunityJson.encode(command.arguments()));
                if (command.operation().value().startsWith(SwayNativeWire.START)) {
                    var admission=SwayNativeBindings.startAdmission(row); SwayNativeWire.action(command.actionId(), false);
                    long target = SwayNativeWire.actionCharacter(row, "target_character_id"); require(command.operation().value().equals(SwayNativeWire.START + target), "exact native Sway Start differs");
                    ExactRef readRef = ExactRef.fromJson(row.get("original_target_read")); PlanningReadReceipt read = originals.loadRead(readRef);
                    require(read.request().before().equals(command.before()) && read.request().source().equals(command.source()) && read.request().sessionId().equals(command.sessionId()), "Sway Start input crossed command origin");
                    SwayNativeWire.TargetRead targetRead = SwayNativeWire.target(read.original().originalFrame().bytes(), read.requestId(), SwayNativeBindings.bind(read, new OperationKey(SwayNativeWire.TARGET + target)), target);
                    domain.commit(session, new StartIntent(command.actionId(), targetRead, MandatoryContext.CLEAR,admission), new SwayTransitionCodec.Proofs(List.of(readRef), Optional.empty(), Optional.of(read.after().binding().nativeEvidence())));
                } else if (command.operation().value().equals(SwayNativeWire.STOP)) {
                    SwayNativeWire.equals(row, "schema", SwayNativeBindings.STOP_ARGUMENTS); ExactRef readRef = ExactRef.fromJson(row.get("original_target_read")); PlanningReadReceipt read = originals.loadRead(readRef);
                    long target = SwayNativeWire.integer(row, "target_character_id", 1, Integer.MAX_VALUE); require(read.request().before().equals(command.before()) && read.request().source().equals(command.source()) && read.request().sessionId().equals(command.sessionId()), "Sway Stop input crossed command origin");
                    Ledger state = domain.load(session).ledger(); Episode original = state.resolved().orElseThrow();
                    require(original.identity().actionId().equals(SwayNativeWire.string(row, "original_action_id")) && original.identity().schemeInstanceId() == SwayNativeWire.integer(row, "scheme_instance_id", 0, 0xffff_fffeL)
                            && original.identity().schemeInstanceGeneration() == SwayNativeWire.integer(row, "scheme_instance_generation", 0, 255), "selected Stop changed original action/full instance");
                    // Re-run the current completion/opinion producer before granting Stop eligibility.
                    List<ExactRef> planes = List.of(ExactRef.fromJson(row.get("completion_read")), ExactRef.fromJson(row.get("opinion_read")));
                    SwayLifecycle.State lifecycle = lifecycle(original, planes, originals); domain.commit(session, new LifecycleObserved(lifecycle), new SwayTransitionCodec.Proofs(planes, Optional.empty(), Optional.empty()));
                    SwayNativeWire.TargetRead targetRead = SwayNativeWire.target(read.original().originalFrame().bytes(), read.requestId(), SwayNativeBindings.bind(read, new OperationKey(SwayNativeWire.TARGET + target)), target);
                    domain.commit(session, new StopIntent(command.actionId(), targetRead), new SwayTransitionCodec.Proofs(List.of(readRef), Optional.empty(), Optional.empty()));
                } else throw new IllegalArgumentException("foreign action cannot use the Sway pending producer");
            } catch (IOException failure) { throw new UncheckedIOException("same-writer Sway intent unavailable", failure); }
        };
    }
    public NativeEffectRegistry.Binding start(OperationKey exactOperation, ExactRef producerSource) {
        require(exactOperation.value().startsWith(SwayNativeWire.START), "exact Sway Start operation required");
        return new NativeEffectRegistry.Binding(exactOperation, producerSource, guardedPreparation(false), this::observeStart);
    }
    public NativeEffectRegistry.Binding stop(ExactRef producerSource) {
        return new NativeEffectRegistry.Binding(new OperationKey(SwayNativeWire.STOP), producerSource, guardedPreparation(true), this::observeStop);
    }
    private ActionPorts.PreparationPort guardedPreparation(boolean stop) {
        return new ActionPorts.PreparationPort() {
            @Override public NativeRequest prepare(ActionCommand command) { throw new IllegalStateException("Sway Native preparation requires the actual borrowed writer Session"); }
            @Override public NativeRequest prepare(ContinuityStorePort.Session session, ActionCommand command, String requestId) {
                // The shared coordinator runs pure preparation before its READ barrier and before the one pending hook.
                // Actual Start/Stop source/reducer eligibility is revalidated by pendingProducer on this same writer.
                Objects.requireNonNull(session);
                return stop ? SwayNativeBindings.stopPreparation().prepare(command, requestId) : SwayNativeBindings.startPreparation(archive.withSession(session)).prepare(command, requestId);
            }
        };
    }
    /** Cold/process recovery queries the retained target once and never executes the old ActionCommand. */
    public org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService.FormalResult recoverPending(ContinuityStorePort.Session session, View fresh) {
        try {
            Ledger ledger = domain.load(session).ledger(); Pending original = ledger.pending().orElse(null);
            if (original == null) return formal(org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService.FormalStatus.ALREADY_APPLIED, ledger.resolved().isPresent(), ledger.resolved().map(value -> value.identity().actionId()), ledger.resolved().map(value -> SwayNativeWire.json(SwayFormalCodec.originalResolved(value))).orElseGet(SwayActionLifecycle::emptyEvidence));
            require(fresh.before().machineId().equals(ledger.machineId()) && fresh.before().frame().episodeRunId().equals(ledger.episodeRunId())
                    && fresh.before().frame().identity().player().longValueExact() == original.original().binding().actor(), "Sway cold recovery changed original actor/episode");
            var result = read(session, definitions.target(original.original().target()), fresh, number("target_character_id", original.original().target()));
            if (!(result instanceof PlanningReadResult.Known<SwayNativeWire.TargetRead> known)) return formal(org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService.FormalStatus.PENDING_RECOVERY, false, Optional.of(original.actionId()), emptyEvidence());
            Ledger after = domain.commit(session, new Recovered(known.value()), new SwayTransitionCodec.Proofs(List.of(archive.withSession(session).readReferenceOf(known.receipt())), Optional.empty(), Optional.empty()));
            return formal(org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService.FormalStatus.APPLIED, true, Optional.of(original.actionId()), SwayNativeWire.json(SwayFormalCodec.originalResolved(after.resolved().orElseThrow())));
        } catch (ReadPublicationRequiredException required) { throw required; }
        catch (IOException | IllegalArgumentException | IllegalStateException failure) {
            ObjectNode evidence = StrictJson.object(); evidence.put("postcondition_verified", false); evidence.put("recovery_error", message(failure));
            return formal(org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService.FormalStatus.PENDING_RECOVERY, false, Optional.empty(), SwayNativeWire.json(evidence));
        }
    }
    private NativeEffectRegistry.Projected observeStart(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch) {
        try {
            ContinuityStorePort.Session session = Objects.requireNonNull(borrowed.get(), "Sway original writer scope missing"); ActionPorts.OutcomeArchive originals = archive.withSession(session);
            Ledger ledger = domain.load(session).ledger(); Pending pending = ledger.pending().orElse(null);
            if (pending == null || !pending.actionId().equals(command.actionId())) return NativeEffectRegistry.Projected.pending("Sway original pending intent is unavailable; no retry", List.of(attempt.guard().nativeEvidence()));
            if (dispatch instanceof NativeActionPort.AckReceived ack && pending.stage() == PendingStage.SUBMISSION_UNRESOLVED) {
                var typed = SwayNativeWire.startAck(ack.originalFrame().bytes(), ack.requestId(), pending.actionId(), pending.original());
                domain.commit(session, new StartAcknowledged(typed), new SwayTransitionCodec.Proofs(List.of(), Optional.of(originals.referenceOf(dispatch)), Optional.empty()));
            }
            ledger = domain.load(session).ledger(); pending = ledger.pending().orElseThrow();
            if (pending.receipt().isEmpty() && dispatch instanceof NativeActionPort.AckReceived) {
                View view = view(command); var definition = definitions.receipt(pending.original().target(), pending.actionId(), pending.original().captureEpoch());
                var result = read(session, definition, view, object("action_id", pending.actionId()));
                if (result instanceof PlanningReadResult.Known<SwayNativeWire.AppliedReceipt> known) {
                    domain.commit(session, new ReceiptRetained(known.value()), new SwayTransitionCodec.Proofs(List.of(originals.readReferenceOf(known.receipt())), Optional.empty(), Optional.empty()));
                }
            }
            // UNKNOWN, a failed receipt read or a cold original all reach read-only recovery, never another Start.
            pending = domain.load(session).ledger().pending().orElseThrow(); View view = view(command);
            var targetResult = read(session, definitions.target(pending.original().target()), view, number("target_character_id", pending.original().target()));
            if (!(targetResult instanceof PlanningReadResult.Known<SwayNativeWire.TargetRead> known)) return NativeEffectRegistry.Projected.pending("Sway independent active read unavailable; original pending preserved", List.of(attempt.guard().nativeEvidence()));
            ExactRef activeRef = originals.readReferenceOf(known.receipt()); Ledger resolved = domain.commit(session, new Recovered(known.value()), new SwayTransitionCodec.Proofs(List.of(activeRef), Optional.empty(), Optional.empty()));
            Episode episode = resolved.resolved().orElseThrow(); return effect(command, known.receipt(), episode, activeRef, false, originals);
        } catch (ReadPublicationRequiredException required) { throw required; }
        catch (IOException | IllegalArgumentException | IllegalStateException failure) {
            return NativeEffectRegistry.Projected.pending("Sway Start postcondition pending: " + message(failure), List.of(attempt.guard().nativeEvidence()));
        }
    }
    private NativeEffectRegistry.Projected observeStop(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch) {
        try {
            ContinuityStorePort.Session session = Objects.requireNonNull(borrowed.get(), "Sway original writer scope missing"); ActionPorts.OutcomeArchive originals = archive.withSession(session);
            Episode original = domain.load(session).ledger().resolved().orElseThrow(); Stop stop = original.stop().orElseThrow();
            require(stop.actionId().equals(command.actionId()), "Stop original durable action differs");
            if (dispatch instanceof NativeActionPort.AckReceived ack && stop.stage() == StopStage.SUBMISSION_UNRESOLVED) {
                var id = original.identity(); var typed = SwayNativeWire.stopAck(ack.originalFrame().bytes(), ack.requestId(), stop.submittedFrom(), stop.actionId(), id.targetCharacterId(), id.schemeInstanceId(), id.schemeInstanceGeneration());
                domain.commit(session, new StopAcknowledged(typed), new SwayTransitionCodec.Proofs(List.of(), Optional.of(originals.referenceOf(dispatch)), Optional.empty()));
            }
            View view = view(command); var result = read(session, definitions.plane(SwayObservationReads.Kind.COMPLETION, original.identity()), view, instanceArguments(original));
            if (!(result instanceof PlanningReadResult.Known<SwayObservationReads.Plane> known)) return NativeEffectRegistry.Projected.pending("selected Stop original full-instance read unavailable", List.of(attempt.guard().nativeEvidence()));
            ExactRef ref = originals.readReferenceOf(known.receipt()); original = domain.load(session).ledger().resolved().orElseThrow();
            SwayLifecycle.State lifecycle = lifecycle(original, List.of(ref), originals);
            Ledger state = domain.commit(session, new StopObserved(lifecycle, known.value().binding().before()), new SwayTransitionCodec.Proofs(List.of(ref), Optional.empty(), Optional.empty()));
            Episode after = state.resolved().orElseThrow();
            if (after.stop().orElseThrow().terminalObserved().isEmpty()) return NativeEffectRegistry.Projected.pending("selected Stop ACK, purged or reused storage has no independent terminal", List.of(ref));
            return effect(command, known.receipt(), after, ref, true, originals);
        } catch (ReadPublicationRequiredException required) { throw required; }
        catch (IOException | IllegalArgumentException | IllegalStateException failure) {
            return NativeEffectRegistry.Projected.pending("selected Stop postcondition pending: " + message(failure), List.of(attempt.guard().nativeEvidence()));
        }
    }
    private NativeEffectRegistry.Projected effect(ActionCommand command, PlanningReadReceipt independent, Episode episode, ExactRef readRef, boolean stop, ActionPorts.OutcomeArchive originals) {
        ObjectNode proof = StrictJson.object(); proof.put("schema", PROOF); proof.put("kind", stop ? "stop" : "start"); proof.set("independent_read", readRef.toJson()); proof.set("episode", SwayFormalCodec.episode(episode));
        JsonNode arguments = StrictJson.parse(OpportunityJson.encode(command.arguments())); proof.set("original_target_read", ExactRef.fromJson(arguments.get("original_target_read")).toJson());
        ExactRef proofRef = originals.preserveMaterial(new RawJson(StrictJson.canonical(proof, SwayFormalCodec.MAX)));
        List<ExpectedValue> values = values(episode, command.actionId(), stop); String schema = stop ? STOP_OBSERVER : START_OBSERVER;
        var observed = new ActionState.EffectObservation(independent.request().before(), command.source(), command.sessionId(), schema, values,
                independent.requestId(), independent.after().binding().observedAt(), independent.after().binding().nativeEvidence(), List.of(proofRef));
        return new NativeEffectRegistry.Projected(new ActionPorts.EffectObserved(observed), Optional.of(new RawJson(StrictJson.canonical(SwayFormalCodec.originalResolved(episode), SwayFormalCodec.MAX))));
    }
    public NativeRecordedEvidenceVerifier.Binding recorded(OperationKey operation, ExactRef verifierSource) {
        return new NativeRecordedEvidenceVerifier.Binding(operation, verifierSource, (head, proposed, originals) -> verifyArchived(frames, head.state(), proposed, originals));
    }
    public static void verifyArchived(org.xar.ck3.control.application.effects.NativeEffectEvidence.FrameLoader frames,
            org.xar.ck3.control.continuity.ContinuityState head, ActionReceipt proposed, ActionPorts.OutcomeArchive originals) {
            ActionState.Settlement settlement = NativeRecordedEvidenceVerifier.settlement(proposed.state()); require(settlement instanceof ActionState.Applied, "Sway settlement requires independent gameplay effect");
            ActionState.EffectObservation effect = ((ActionState.Applied)settlement).observation(); require(effect.supportingEvidence().size() == 1, "Sway effect has one full reducer basis");
            JsonNode proof = StrictJson.object(StrictJson.parse(originals.loadMaterial(effect.supportingEvidence().get(0)).bytes(), SwayFormalCodec.MAX), Set.of("schema", "kind", "independent_read", "episode", "original_target_read"));
            SwayNativeWire.equals(proof, "schema", PROOF); boolean stop = SwayNativeWire.string(proof, "kind").equals("stop"); require(stop || SwayNativeWire.string(proof, "kind").equals("start"), "Sway proof kind differs");
            Episode episode = SwayFormalCodec.episode(proof.get("episode")); PlanningReadReceipt read = originals.loadRead(ExactRef.fromJson(proof.get("independent_read")));
            verifyOriginalRead(read, originals, frames);
            var canonicalRef = org.xar.ck3.control.continuity.writer.DomainBodies.reference(head, org.xar.ck3.control.continuity.writer.DomainBodies.Slot.SWAY).orElseThrow(() -> new IllegalArgumentException("Sway settlement has no actual canonical domain body"));
            require(canonicalRef.contractSchema().equals(SwayFormalState.SCHEMA), "Sway actual body contract differs"); Ledger canonical = SwayFormalCodec.decode(originals.loadMaterial(canonicalRef.payload()).bytes());
            List<Episode> episodes = new ArrayList<>(canonical.previous()); canonical.resolved().ifPresent(episodes::add);
            Episode durable = episodes.stream().filter(value -> value.identity().equals(episode.identity())).findFirst().orElseThrow(() -> new IllegalArgumentException("Sway original action is absent from actual canonical body"));
            require(durable.originalIntent().equals(episode.originalIntent()) && durable.independentActive().equals(episode.independentActive()) && durable.nativeReceipt().equals(episode.nativeReceipt()) && durable.retainedReceipt().equals(episode.retainedReceipt()), "Sway settlement changed original verified canonical Start evidence");
            PlanningReadReceipt originalTarget = originals.loadRead(ExactRef.fromJson(proof.get("original_target_read")));
            verifyOriginalRead(originalTarget, originals, frames);
            require(originalTarget.request().before().equals(proposed.command().before()) && originalTarget.request().source().equals(proposed.command().source()) && originalTarget.request().sessionId().equals(proposed.command().sessionId()), "Sway effect original input crossed command origin");
            if (stop) {
                require(proposed.command().operation().value().equals(SwayNativeWire.STOP), "Stop replay operation differs");
                require(durable.stop().isPresent() && durable.stop().orElseThrow().actionId().equals(proposed.command().actionId()) && durable.stop().orElseThrow().terminalObserved().equals(episode.stop().orElseThrow().terminalObserved()), "Stop effect differs from actual canonical pending/resolution");
                var plane = SwayObservationReads.decode(read, SwayObservationReads.Kind.COMPLETION, episode.identity());
                require(SwayLifecycle.observedTerminal(episode.lifecycle(), plane.binding().before()) && episode.stop().orElseThrow().actionId().equals(proposed.command().actionId()), "Stop replay lacks original exact terminal");
                SwayLifecycle.State replayed = lifecycle(episode, List.of(ExactRef.fromJson(proof.get("independent_read"))), originals);
                require(SwayLifecycle.observedTerminal(replayed, plane.binding().before()), "Stop actual native re-read source is not terminal");
            } else {
                require(proposed.command().operation().value().equals(SwayNativeWire.START + episode.identity().targetCharacterId()) && proposed.command().actionId().equals(episode.identity().actionId()), "Start replay original action differs");
                var originalRead = SwayNativeWire.target(originalTarget.original().originalFrame().bytes(), originalTarget.requestId(), SwayNativeBindings.bind(originalTarget, new OperationKey(SwayNativeWire.TARGET + episode.identity().targetCharacterId())), episode.identity().targetCharacterId());
                require(originalRead.equals(episode.originalIntent().orElseThrow()) && SwayFormalState.startEligible(originalRead,true,SwayNativeBindings.startAdmission(StrictJson.parse(OpportunityJson.encode(proposed.command().arguments())))), "Start effect lacks the original empty legal slot read");
                var active = SwayNativeWire.target(read.original().originalFrame().bytes(), read.requestId(), SwayNativeBindings.bind(read, new OperationKey(SwayNativeWire.TARGET + episode.identity().targetCharacterId())), episode.identity().targetCharacterId());
                require(active.equals(episode.independentActive()) && active.matching() && active.instances().stream().filter(row -> row.fullId() == episode.identity().schemeInstanceId() && row.generation() == episode.identity().schemeInstanceGeneration()).count() == 1, "Start replay lost exact independent active row");
            }
            require(effect.after().equals(read.request().before()) && effect.provenance() instanceof ObservationProvenance.Query query && query.requestId().equals(read.requestId()) && effect.originalEvidence().equals(read.after().binding().nativeEvidence())
                    && effect.source().equals(proposed.command().source()) && effect.sessionId().equals(proposed.command().sessionId())
                    && effect.observerSchema().equals(stop ? STOP_OBSERVER : START_OBSERVER) && effect.actual().equals(values(episode, proposed.command().actionId(), stop)), "Sway effect differs from original native producer/consumer");
    }
    public static List<ExpectedValue> values(Episode episode, String actionId, boolean stop) {
        return List.of(new ExpectedBoolean(new FieldKey(stop ? "sway.selected_terminal_observed" : "sway.exact_active_observed"), true),
                new ExpectedText(new FieldKey("sway.action_id"), actionId), new ExpectedInteger(new FieldKey("sway.actor_character_id"), java.math.BigInteger.valueOf(episode.identity().actorCharacterId())),
                new ExpectedInteger(new FieldKey("sway.target_character_id"), java.math.BigInteger.valueOf(episode.identity().targetCharacterId())));
    }
    private View view(ActionCommand original) {
        View view = Objects.requireNonNull(current.current(original)); require(view.source().equals(original.source()) && view.sessionId().equals(original.sessionId())
                && view.before().machineId().equals(original.before().machineId()) && view.before().game().equals(original.before().game())
                && view.before().frame().episodeRunId().equals(original.before().frame().episodeRunId()) && view.before().frame().identity().player().equals(original.before().frame().identity().player()), "Sway current source/authority/Game/episode changed"); return view;
    }
    private <T> PlanningReadResult<T> read(ContinuityStorePort.Session session, ReadContract<T> definition, View view, OpportunityJson.Obj arguments) {
        return reads.read(session, definition, new PlanningReadRequest(view.before(), view.source(), view.sessionId(), definition.operation(), arguments, view.deadline()));
    }
    private static SwayLifecycle.State lifecycle(Episode episode, List<ExactRef> refs, ActionPorts.OutcomeArchive originals) {
        Optional<org.xar.ck3.control.contracts.projection.ProjectionJson> completion = Optional.empty(), opinion = Optional.empty(); ObservationIdentity queried = null;
        for (ExactRef ref : refs) {
            PlanningReadReceipt read = originals.loadRead(ref); var kind = read.request().operation().value().equals(SwayObservationReads.Kind.COMPLETION.step()) ? SwayObservationReads.Kind.COMPLETION : SwayObservationReads.Kind.OPINION;
            SwayObservationReads.Plane plane = SwayObservationReads.decode(read, kind, episode.identity()); if (queried == null) queried = plane.binding().before(); else require(queried.equals(plane.binding().before()), "Stop input query frames differ");
            if (kind == SwayObservationReads.Kind.COMPLETION) { require(completion.isEmpty(), "duplicate selected completion"); completion = Optional.of(plane.normalized()); }
            else { require(opinion.isEmpty(), "duplicate selected opinion"); opinion = Optional.of(plane.normalized()); }
        }
        return SwayLifecycle.observe(episode.lifecycle(), SwayFormalCodec.m6Episode(episode), new M6TerminalSourceComposition.Inputs(completion, Optional.empty(), Optional.empty(), opinion), Objects.requireNonNull(queried));
    }
    private static OpportunityJson.Obj object(String key, String value) { ObjectNode row = StrictJson.object(); row.put(key, value); return asArguments(row); }
    private static OpportunityJson.Obj number(String key, long value) { ObjectNode row = StrictJson.object(); row.put(key, value); return asArguments(row); }
    private static OpportunityJson.Obj instanceArguments(Episode original) { ObjectNode row = StrictJson.object(); row.put("target_character_id", original.identity().targetCharacterId()); row.put("scheme_instance_id", original.identity().schemeInstanceId()); return asArguments(row); }
    private static OpportunityJson.Obj asArguments(ObjectNode row) { return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(row)), "Sway query arguments"); }
    private static org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService.FormalResult formal(org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService.FormalStatus status, boolean verified, Optional<String> actionId, org.xar.ck3.control.contracts.projection.ProjectionJson evidence) {
        return new org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService.FormalResult(status, verified, actionId, Optional.empty(), evidence);
    }
    private static org.xar.ck3.control.contracts.projection.ProjectionJson emptyEvidence() { return SwayNativeWire.json(StrictJson.object()); }
    private static void verifyOriginalRead(PlanningReadReceipt read, ActionPorts.OutcomeArchive originals, org.xar.ck3.control.application.effects.NativeEffectEvidence.FrameLoader frames) {
        NativeRecordedEvidenceVerifier.requireRead(read, originals);
        for (GuardEvidence guard : List.of(read.before().binding(), read.after().binding())) org.xar.ck3.control.application.effects.RootGuardEvidence.loadFrame(guard, originals, frames);
    }
    private static String message(Throwable failure) { String value = failure.getMessage(); return value == null ? failure.getClass().getSimpleName() : value; }
}
