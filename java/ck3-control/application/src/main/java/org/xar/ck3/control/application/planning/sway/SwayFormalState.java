package org.xar.ck3.control.application.planning.sway;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Identity;
import org.xar.ck3.control.g2.m6.SwayLifecycle;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.swayreuse.ReusedSwayOpportunity;
import org.xar.ck3.control.vanilla.schemesway.OrdinarySwaySchedule;

/** Single Sway domain reducer. Native Start, exact-instance recovery and Stop remain separate transitions. */
public final class SwayFormalState {
    public static final String SCHEMA = "xar.java.sway-formal-ledger/v2";
    private SwayFormalState() { }
    public enum PendingStage { SUBMISSION_UNRESOLVED, RECEIPT_PENDING, POSTCONDITION_PENDING }
    public enum StopStage { SUBMISSION_UNRESOLVED, POSTCONDITION_PENDING, TERMINAL_OBSERVED }
    public enum MandatoryContext { CLEAR, MANDATORY, UNAVAILABLE }
    public enum FollowupDecision { FIRST_SELECTED_RELATION, RETARGET_SELECTED_RELATION, RETAIN_EXISTING_SWAY,
        OBSERVE_TRACKED_INSTANCE_END, DEFER_OCCUPIED_SLOT, FINISH_SELECTED_RELATION, OBSERVE_CURRENT_NAMED_MATERIAL,
        REPEAT_SELECTED_TARGET, RETURN_TO_OPPORTUNITY_SELECTION }
    public record Pending(String actionId, SwayNativeWire.TargetRead original, PendingStage stage,
            Optional<SwayNativeWire.StartAck> acknowledgement, Optional<SwayNativeWire.AppliedReceipt> receipt) {
        public Pending {
            SwayNativeWire.action(actionId, false); Objects.requireNonNull(original); Objects.requireNonNull(stage); Objects.requireNonNull(acknowledgement); Objects.requireNonNull(receipt);
            acknowledgement.ifPresent(value -> require(value.actionId().equals(actionId) && value.actor() == original.binding().actor() && value.target() == original.target(), "retained Start ACK identity"));
            receipt.ifPresent(value -> require(value.actionId().equals(actionId) && value.binding().sameSession(original.binding()) && value.postCaptureEpoch().compareTo(original.captureEpoch()) > 0 && value.postDateRaw() == original.binding().date(), "retained original Start receipt identity/epoch"));
            require(stage != PendingStage.POSTCONDITION_PENDING || receipt.isPresent(), "postcondition pending preserves original receipt");
        }
    }
    public record Stop(String actionId, SwayNativeWire.Binding submittedFrom, StopStage stage,
            Optional<SwayNativeWire.StopAck> acknowledgement, Optional<ObservationIdentity> terminalObserved,
            Optional<ObservationIdentity> following) {
        public Stop {
            SwayNativeWire.action(actionId, true); Objects.requireNonNull(submittedFrom); Objects.requireNonNull(stage);
            Objects.requireNonNull(acknowledgement); Objects.requireNonNull(terminalObserved); Objects.requireNonNull(following);
            require((stage == StopStage.TERMINAL_OBSERVED) == terminalObserved.isPresent(), "Stop terminal branch requires independent exact observation");
            require(following.isEmpty() || terminalObserved.isPresent() && later(following.orElseThrow(), terminalObserved.orElseThrow()), "Stop following frame must be later");
        }
    }
    public record Episode(Identity identity, Optional<SwayNativeWire.TargetRead> originalIntent, SwayNativeWire.TargetRead independentActive,
            Optional<SwayNativeWire.AppliedReceipt> nativeReceipt, Optional<SwayNativeWire.AppliedReceipt> retainedReceipt,
            SwayLifecycle.State lifecycle, Optional<ObservationIdentity> startFollowing, Optional<Stop> stop,
            Optional<SwayLegacyImport.OriginalIntent> importedIntent, List<SwayLifecycle.State> retainedScopes) {
        public Episode(Identity identity, Optional<SwayNativeWire.TargetRead> originalIntent, SwayNativeWire.TargetRead independentActive,
                Optional<SwayNativeWire.AppliedReceipt> nativeReceipt, Optional<SwayNativeWire.AppliedReceipt> retainedReceipt,
                SwayLifecycle.State lifecycle, Optional<ObservationIdentity> startFollowing, Optional<Stop> stop, Optional<SwayLegacyImport.OriginalIntent> importedIntent) {
            this(identity, originalIntent, independentActive, nativeReceipt, retainedReceipt, lifecycle, startFollowing, stop, importedIntent, List.of());
        }
        public Episode(Identity identity, SwayNativeWire.TargetRead originalIntent, SwayNativeWire.TargetRead independentActive,
                Optional<SwayNativeWire.AppliedReceipt> nativeReceipt, Optional<SwayNativeWire.AppliedReceipt> retainedReceipt,
                SwayLifecycle.State lifecycle, Optional<ObservationIdentity> startFollowing, Optional<Stop> stop) {
            this(identity, Optional.of(originalIntent), independentActive, nativeReceipt, retainedReceipt, lifecycle, startFollowing, stop, Optional.empty());
        }
        public Episode {
            Objects.requireNonNull(identity); Objects.requireNonNull(originalIntent); Objects.requireNonNull(independentActive); Objects.requireNonNull(nativeReceipt); Objects.requireNonNull(retainedReceipt);
            Objects.requireNonNull(lifecycle); Objects.requireNonNull(startFollowing); Objects.requireNonNull(stop);
            require(lifecycle.identity().equals(identity) && independentActive.binding().actor() == identity.actorCharacterId() && independentActive.target() == identity.targetCharacterId(), "resolved Sway identity differs");
            Objects.requireNonNull(importedIntent); require(originalIntent.isPresent() != importedIntent.isPresent(), "exactly one original Java or historical intent required");
            originalIntent.ifPresent(original -> require(original.binding().sameEpisode(independentActive.binding()) && original.target() == identity.targetCharacterId(), "resolved Sway original intent crossed episode"));
            importedIntent.ifPresent(original -> original.requireIdentity(identity));
            require(independentActive.instances().stream().filter(row -> row.fullId() == identity.schemeInstanceId() && row.generation() == identity.schemeInstanceGeneration() && row.target() == identity.targetCharacterId()).count() == 1, "resolved Sway retains one exact active row");
            for (Optional<SwayNativeWire.AppliedReceipt> value : List.of(nativeReceipt, retainedReceipt)) value.ifPresent(receipt -> require(receipt.actionId().equals(identity.actionId()) && receipt.fullId() == identity.schemeInstanceId() && receipt.generation() == identity.schemeInstanceGeneration(), "resolved receipt original full ID differs"));
            startFollowing.ifPresent(value -> require(later(value, independentActive.binding().before()), "Start following observation must advance"));
            retainedScopes = List.copyOf(retainedScopes); require(retainedScopes.size() <= 64, "bounded retained actual Sway source scopes");
            var scopeGames = new HashSet<org.xar.ck3.control.contracts.GameGeneration>(); scopeGames.add(lifecycle.origin().game());
            for (SwayLifecycle.State old : retainedScopes) require(old.identity().equals(identity) && old.origin().machineId().equals(lifecycle.origin().machineId()) && old.origin().frame().episodeRunId().equals(lifecycle.origin().frame().episodeRunId()) && scopeGames.add(old.origin().game()), "retained Sway scope crossed identity or repeats a physical Game");
        }
    }
    /** Imported is explicit; absent storage must never construct an empty Ledger. */
    public record Ledger(String machineId, String episodeRunId, Optional<Pending> pending, Optional<Episode> resolved,
            List<Episode> previous, Optional<OrdinarySwaySchedule.State> schedule, ExactRef originalMigrationInput,
            Optional<SwayLegacyImport.Imported> imported, Optional<ExactRef> activeStage) {
        public Ledger(String machineId, String episodeRunId, Optional<Pending> pending, Optional<Episode> resolved,
                List<Episode> previous, Optional<OrdinarySwaySchedule.State> schedule, ExactRef originalMigrationInput, Optional<SwayLegacyImport.Imported> imported) {
            this(machineId, episodeRunId, pending, resolved, previous, schedule, originalMigrationInput, imported, Optional.empty());
        }
        public Ledger(String machineId, String episodeRunId, Optional<Pending> pending, Optional<Episode> resolved,
                List<Episode> previous, Optional<OrdinarySwaySchedule.State> schedule, ExactRef originalMigrationInput) {
            this(machineId, episodeRunId, pending, resolved, previous, schedule, originalMigrationInput, Optional.empty());
        }
        public Ledger {
            require(machineId != null && !machineId.equals("unknown") && !machineId.isBlank(), "Sway explicit source machine");
            require(episodeRunId != null && !episodeRunId.isBlank(), "Sway episode identity"); Objects.requireNonNull(pending); Objects.requireNonNull(resolved);
            previous = List.copyOf(previous); require(previous.size() <= 4096, "bounded retained original Sway episodes"); Objects.requireNonNull(schedule); Objects.requireNonNull(originalMigrationInput);
            require(originalMigrationInput.bytes() > 0, "original full Python or explicit initial Java domain input required");
            Objects.requireNonNull(imported); Objects.requireNonNull(activeStage);
            pending.ifPresent(value -> binding(machineId, episodeRunId, value.original().binding()));
            resolved.ifPresent(value -> binding(machineId, episodeRunId, value.independentActive().binding()));
            HashSet<String> actions = new HashSet<>(); resolved.ifPresent(value -> actions.add(value.identity().actionId()));
            for (Episode value : previous) { binding(machineId, episodeRunId, value.independentActive().binding()); require(actions.add(value.identity().actionId()), "duplicate Sway original action history"); }
        }
    }
    public sealed interface Change permits StartIntent, StartAcknowledged, ReceiptRetained, Recovered, LifecycleObserved, StopIntent, StopAcknowledged, StopObserved, Following, FollowingGameplay, SchedulerSaved, HistoricalAttached, StageRecorded, ScopeRebound { }
    public record ScopeRebound(ObservationIdentity queried, ExactRef restoreMaterial) implements Change { public ScopeRebound { Objects.requireNonNull(queried); Objects.requireNonNull(restoreMaterial); } }
    public record StageRecorded(ExactRef basis) implements Change { public StageRecorded { Objects.requireNonNull(basis); } }
    /** restoreAttachment is an immutable actual committed restoration, never a tuple-derived permission. */
    public record HistoricalAttached(SwayNativeWire.TargetRead independent, ExactRef restoreAttachment) implements Change { public HistoricalAttached { Objects.requireNonNull(independent); Objects.requireNonNull(restoreAttachment); } }
    public enum StartAdmission { ORDINARY_OPPORTUNITY, PUBLIC_NATIVE_FINAL }
    public record StartIntent(String actionId, SwayNativeWire.TargetRead original, MandatoryContext context,StartAdmission admission) implements Change {
        public StartIntent(String actionId,SwayNativeWire.TargetRead original,MandatoryContext context){this(actionId,original,context,StartAdmission.ORDINARY_OPPORTUNITY);}
        public StartIntent {Objects.requireNonNull(original);Objects.requireNonNull(context);Objects.requireNonNull(admission);}
    }
    public static boolean startEligible(SwayNativeWire.TargetRead read,boolean clear,StartAdmission admission) {
        Objects.requireNonNull(read);Objects.requireNonNull(admission);
        return admission==StartAdmission.ORDINARY_OPPORTUNITY?read.startable(clear):clear&&read.activeCount()==0&&!read.matching()&&read.canSend()&&read.legal();
    }
    public record StartAcknowledged(SwayNativeWire.StartAck acknowledgement) implements Change { public StartAcknowledged { Objects.requireNonNull(acknowledgement); } }
    public record ReceiptRetained(SwayNativeWire.AppliedReceipt receipt) implements Change { public ReceiptRetained { Objects.requireNonNull(receipt); } }
    public record Recovered(SwayNativeWire.TargetRead independent) implements Change { public Recovered { Objects.requireNonNull(independent); } }
    public record LifecycleObserved(SwayLifecycle.State state) implements Change { public LifecycleObserved { Objects.requireNonNull(state); } }
    public record StopIntent(String actionId, SwayNativeWire.TargetRead target) implements Change { public StopIntent { Objects.requireNonNull(target); } }
    public record StopAcknowledged(SwayNativeWire.StopAck acknowledgement) implements Change { public StopAcknowledged { Objects.requireNonNull(acknowledgement); } }
    public record StopObserved(SwayLifecycle.State state, ObservationIdentity queried) implements Change { public StopObserved { Objects.requireNonNull(state); Objects.requireNonNull(queried); } }
    public record Following(ObservationIdentity after) implements Change { public Following { Objects.requireNonNull(after); } }
    /** v4 binds consumption to an exact canonical gameplay result and its pre-action knowledge. */
    public record FollowingGameplay(ObservationIdentity actionBefore, ObservationIdentity after, ExactRef receipt) implements Change {
        public FollowingGameplay { Objects.requireNonNull(actionBefore); Objects.requireNonNull(after); Objects.requireNonNull(receipt); require(receipt.bytes() > 0, "nonempty exact following receipt required"); require(atOrAfter(after, actionBefore), "following gameplay read predates the actual action"); }
    }
    public record SchedulerSaved(OrdinarySwaySchedule.State state, ExactRef replay) implements Change { public SchedulerSaved { Objects.requireNonNull(state); Objects.requireNonNull(replay); } }

    public static Ledger reduce(Ledger prior, Change change) {
        Objects.requireNonNull(prior); Objects.requireNonNull(change);
        return switch (change) {
            case StartIntent value -> {
                require(prior.pending().isEmpty(), "original pending Start cannot be cleared or replayed");
                require(!historicalPendingUnresolved(prior), "historical UNKNOWN pending is observation only");
                require(prior.imported().flatMap(SwayLegacyImport.Imported::resolved).isEmpty() || prior.resolved().isPresent(), "historical resolved episode requires actual restoration before followup");
                binding(prior.machineId(), prior.episodeRunId(), value.original().binding());
                require(value.context() == MandatoryContext.CLEAR && startEligible(value.original(),true,value.admission()), "Sway Start requires clear paused legal empty-slot opportunity");
                FollowupDecision followup = followup(prior, value.original());
                require(followup == FollowupDecision.FIRST_SELECTED_RELATION || followup == FollowupDecision.RETARGET_SELECTED_RELATION || followup == FollowupDecision.REPEAT_SELECTED_TARGET, "original selected relation requires observation or completion before a new Start");
                require(prior.resolved().stream().noneMatch(row -> row.identity().actionId().equals(value.actionId())) && prior.previous().stream().noneMatch(row -> row.identity().actionId().equals(value.actionId())), "new Sway action must differ from every original episode");
                yield with(prior, Optional.of(new Pending(value.actionId(), value.original(), PendingStage.SUBMISSION_UNRESOLVED, Optional.empty(), Optional.empty())), prior.resolved(), prior.previous(), prior.schedule());
            }
            case StartAcknowledged value -> {
                Pending pending = prior.pending().orElseThrow(() -> new IllegalArgumentException("Start intent must be durable before ACK"));
                require(pending.stage() == PendingStage.SUBMISSION_UNRESOLVED && pending.acknowledgement().isEmpty(), "Start ACK cannot overwrite later evidence");
                Pending after = new Pending(pending.actionId(), pending.original(), PendingStage.RECEIPT_PENDING, Optional.of(value.acknowledgement()), pending.receipt());
                yield with(prior, Optional.of(after), prior.resolved(), prior.previous(), prior.schedule());
            }
            case ReceiptRetained value -> {
                Pending pending = prior.pending().orElseThrow(() -> new IllegalArgumentException("original Start intent required"));
                require(pending.receipt().isEmpty() || pending.receipt().orElseThrow().equals(value.receipt()), "original native receipt cannot be replaced");
                yield with(prior, Optional.of(new Pending(pending.actionId(), pending.original(), PendingStage.POSTCONDITION_PENDING, pending.acknowledgement(), Optional.of(value.receipt()))), prior.resolved(), prior.previous(), prior.schedule());
            }
            case Recovered value -> recover(prior, value.independent());
            case LifecycleObserved value -> {
                Episode current = prior.resolved().orElseThrow(() -> new IllegalArgumentException("original Sway episode required"));
                require(current.identity().equals(value.state().identity()) && current.lifecycle().origin().equals(value.state().origin()), "lifecycle update changed original identity/source");
                yield resolved(prior, new Episode(current.identity(), current.originalIntent(), current.independentActive(), current.nativeReceipt(), current.retainedReceipt(), value.state(), current.startFollowing(), current.stop(), current.importedIntent(), current.retainedScopes()));
            }
            case StopIntent value -> {
                requireStopEligible(prior, value.target()); Episode current = prior.resolved().orElseThrow();
                Stop stop = new Stop(value.actionId(), value.target().binding(), StopStage.SUBMISSION_UNRESOLVED, Optional.empty(), Optional.empty(), Optional.empty());
                yield resolved(prior, episode(current, current.lifecycle(), current.startFollowing(), Optional.of(stop)));
            }
            case StopAcknowledged value -> {
                Episode current = prior.resolved().orElseThrow(); Stop stop = current.stop().orElseThrow();
                require(stop.stage() == StopStage.SUBMISSION_UNRESOLVED && stop.acknowledgement().isEmpty(), "Stop ACK cannot replace independent terminal evidence");
                SwayNativeWire.StopAck ack = value.acknowledgement(); Identity id = current.identity();
                require(ack.actionId().equals(stop.actionId()) && ack.actor() == id.actorCharacterId() && ack.target() == id.targetCharacterId() && ack.fullId() == id.schemeInstanceId() && ack.generation() == id.schemeInstanceGeneration(), "Stop ACK changed original selected instance");
                yield resolved(prior, episode(current, current.lifecycle(), current.startFollowing(), Optional.of(new Stop(stop.actionId(), stop.submittedFrom(), StopStage.POSTCONDITION_PENDING, Optional.of(ack), Optional.empty(), Optional.empty()))));
            }
            case StopObserved value -> {
                Episode current = prior.resolved().orElseThrow(); Stop stop = current.stop().orElseThrow();
                require(current.identity().equals(value.state().identity()) && current.lifecycle().origin().equals(value.state().origin()), "Stop observer changed original episode");
                boolean observed = SwayLifecycle.observedTerminal(value.state(), value.queried());
                // Missing, purged or reused slots preserve UNKNOWN. An old terminal is not a fresh Stop result.
                Optional<ObservationIdentity> terminal = stop.terminalObserved().isPresent() ? stop.terminalObserved() : observed ? Optional.of(value.queried()) : Optional.empty();
                StopStage stage = terminal.isPresent() ? StopStage.TERMINAL_OBSERVED : StopStage.POSTCONDITION_PENDING;
                yield resolved(prior, episode(current, value.state(), current.startFollowing(), Optional.of(new Stop(stop.actionId(), stop.submittedFrom(), stage, stop.acknowledgement(), terminal, stop.following()))));
            }
            case Following value -> {
                List<Episode> previous = prior.previous().stream().map(row -> following(row, value.after())).toList();
                yield with(prior, prior.pending(), prior.resolved().map(row -> following(row, value.after())), previous, prior.schedule());
            }
            case FollowingGameplay value -> {
                List<Episode> previous = prior.previous().stream().map(row -> following(row, value.actionBefore(), value.after())).toList();
                yield with(prior, prior.pending(), prior.resolved().map(row -> following(row, value.actionBefore(), value.after())), previous, prior.schedule());
            }
            case SchedulerSaved value -> with(prior, prior.pending(), prior.resolved(), prior.previous(), Optional.of(value.state()));
            case StageRecorded value -> new Ledger(prior.machineId(), prior.episodeRunId(), prior.pending(), prior.resolved(), prior.previous(), prior.schedule(), prior.originalMigrationInput(), prior.imported(), Optional.of(value.basis()));
            case ScopeRebound value -> {
                Episode current = prior.resolved().orElseThrow(); ObservationIdentity after = value.queried(), old = current.lifecycle().origin();
                require(!old.game().equals(after.game()) && old.machineId().equals(after.machineId()) && old.frame().episodeRunId().equals(after.frame().episodeRunId()) && old.frame().identity().player().equals(after.frame().identity().player()), "explicit Sway source rebind requires the same restored episode/player on a new physical Game");
                var scopes = new ArrayList<>(current.retainedScopes()); scopes.add(current.lifecycle());
                yield resolved(prior, new Episode(current.identity(), current.originalIntent(), current.independentActive(), current.nativeReceipt(), current.retainedReceipt(), SwayLifecycle.empty(current.identity(), after), current.startFollowing(), current.stop(), current.importedIntent(), scopes));
            }
            case HistoricalAttached value -> {
                require(prior.pending().isEmpty() && prior.resolved().isEmpty(), "historical attachment cannot overwrite a Java episode");
                var imported = prior.imported().orElseThrow(); var intent = imported.currentIntent();
                binding(prior.machineId(), prior.episodeRunId(), value.independent().binding());
                Identity identity = intent.requireCurrent(value.independent());
                Episode current = new Episode(identity, Optional.empty(), value.independent(), Optional.empty(), Optional.empty(),
                        SwayLifecycle.empty(identity, value.independent().binding().before()), Optional.empty(), Optional.empty(), Optional.of(intent));
                // Original pending remains preserved in Imported. Its observed current attachment prevents replay;
                // it does not settle the Root action journal or grant original Start credit.
                yield resolved(prior, current);
            }
        };
    }

    /** Same pure guard used by the real public producer and again by StopIntent in the original writer. */
    public static void requireStopEligible(Ledger prior, SwayNativeWire.TargetRead target) {
        Objects.requireNonNull(prior); Objects.requireNonNull(target);
        require(prior.pending().isEmpty(), "pending Start recovery precedes any Stop"); Episode current = prior.resolved().orElseThrow(() -> new IllegalArgumentException("original Sway episode required"));
        require(current.stop().isEmpty(), "existing Stop is observation only and is never resubmitted");
        require(current.importedIntent().stream().noneMatch(original -> original.kind() == SwayLegacyImport.Kind.RESOLVED && org.xar.ck3.control.g2.m6.SwayHistoricalImport.parse(original.original()).plane(org.xar.ck3.control.g2.m6.SwayHistoricalImport.Plane.STOP) instanceof org.xar.ck3.control.g2.m6.SwayHistoricalImport.Retained), "original historical Stop remains observation only; no duplicate request");
        binding(prior.machineId(), prior.episodeRunId(), target.binding());
        require(target.binding().actor() == current.identity().actorCharacterId() && target.target() == current.identity().targetCharacterId() && target.matching()
                && SwayLifecycle.mayFinish(current.lifecycle(), target.binding().before(), target.targetOpinion()), "selected Stop needs current exact active instance and positive named benefit");
    }
    private static Ledger recover(Ledger prior, SwayNativeWire.TargetRead read) {
        Pending pending = prior.pending().orElseThrow(() -> new IllegalArgumentException("recovery requires retained original Start"));
        SwayNativeWire.TargetRead original = pending.original(); binding(prior.machineId(), prior.episodeRunId(), read.binding());
        require(original.binding().sameEpisode(read.binding()) && original.target() == read.target() && read.matching() && read.activeCount() >= 1, "fresh Start recovery crossed episode/actor/target or is not active");
        Optional<SwayNativeWire.AppliedReceipt> receipt = pending.receipt();
        List<SwayNativeWire.Instance> candidates = read.instances().stream().filter(row -> row.target() == read.target())
                .filter(row -> receipt.isEmpty() || row.fullId() == receipt.orElseThrow().fullId() && row.generation() == receipt.orElseThrow().generation()).toList();
        require(candidates.size() == 1, "Start recovery needs exactly one matching original full instance"); SwayNativeWire.Instance instance = candidates.get(0);
        boolean sameSession = receipt.isPresent() && receipt.orElseThrow().binding().sameSession(read.binding());
        if (sameSession) require(read.captureEpoch().compareTo(receipt.orElseThrow().postCaptureEpoch()) > 0 && read.binding().date() == receipt.orElseThrow().postDateRaw(), "same-session independent read must follow original receipt");
        Identity identity = new Identity(pending.actionId(), read.binding().actor(), read.target(), instance.fullId(), instance.generation());
        Episode result = new Episode(identity, original, read, sameSession ? receipt : Optional.empty(), sameSession ? Optional.empty() : receipt,
                SwayLifecycle.empty(identity, read.binding().before()), Optional.empty(), Optional.empty());
        List<Episode> history = new ArrayList<>(prior.previous()); prior.resolved().ifPresent(history::add);
        return with(prior, Optional.empty(), Optional.of(result), history, prior.schedule());
    }
    public static FollowupDecision followup(Ledger prior, SwayNativeWire.TargetRead read) {
        if (prior.resolved().isEmpty()) return FollowupDecision.FIRST_SELECTED_RELATION;
        Episode resolved = prior.resolved().orElseThrow();
        if (resolved.identity().actorCharacterId() != read.binding().actor() || resolved.identity().targetCharacterId() != read.target()) return FollowupDecision.RETARGET_SELECTED_RELATION;
        if (read.matching()) return FollowupDecision.RETAIN_EXISTING_SWAY;
        // Reuse remains the shared source-bound observation gap; it does not manufacture an old terminal or gain.
        if (resolved.lifecycle().origin().game().equals(read.binding().before().game())) {
            com.fasterxml.jackson.databind.node.ObjectNode input = org.xar.ck3.control.contracts.StrictJson.object();
            var old = SwayFormalCodec.originalResolved(resolved); old.retain("status", "postcondition_verified", "action_id", "actor_character_id", "target_character_id", "pre_capture_epoch", "post_capture_epoch", "post_date_raw", "native_receipt", "recovered_instance_observation", "latest_instance_observation", "terminal_intervention"); input.set("resolved", old);
            var current = (com.fasterxml.jackson.databind.node.ObjectNode)org.xar.ck3.control.contracts.StrictJson.parse(read.body().bytes(), SwayFormalCodec.MAX);
            current.put("exact_ck3_build", read.binding().exactBuild()); current.put("exe_sha256", read.binding().exeSha256()); input.set("readback", current);
            if (ReusedSwayOpportunity.decodeFreshEmptySlot(org.xar.ck3.control.contracts.StrictJson.canonical(input)).isPresent()) return FollowupDecision.REPEAT_SELECTED_TARGET;
        }
        if (resolved.lifecycle().terminal().isEmpty()) return FollowupDecision.OBSERVE_TRACKED_INSTANCE_END;
        if (read.activeCount() != 0) return FollowupDecision.DEFER_OCCUPIED_SLOT;
        if (read.targetOpinion() > 50) return FollowupDecision.FINISH_SELECTED_RELATION;
        var material = resolved.lifecycle().material();
        if (material.isEmpty() || !material.orElseThrow().source().game().equals(read.binding().before().game())
                || material.orElseThrow().source().frame().identity().dateRaw().intValueExact() != read.binding().date()) return FollowupDecision.OBSERVE_CURRENT_NAMED_MATERIAL;
        if (material.orElseThrow().dedicatedBenefitObserved()) return FollowupDecision.REPEAT_SELECTED_TARGET;
        if (material.orElseThrow().source().frame().identity().nativeRevision().equals(read.binding().revision())
                && material.orElseThrow().sway().points().filter(value -> value.signum() <= 0).isPresent() && material.orElseThrow().blocker().points().isPresent()) return FollowupDecision.RETURN_TO_OPPORTUNITY_SELECTION;
        return FollowupDecision.OBSERVE_CURRENT_NAMED_MATERIAL;
    }
    private static Episode following(Episode row, ObservationIdentity after) {
        if (!row.independentActive().binding().before().machineId().equals(after.machineId())
                || !row.independentActive().binding().before().frame().episodeRunId().equals(after.frame().episodeRunId())
                || row.identity().actorCharacterId() != after.frame().identity().player().longValueExact()) return row;
        Optional<ObservationIdentity> start = row.importedIntent().isPresent() || row.startFollowing().isPresent() || !later(after, row.independentActive().binding().before()) ? row.startFollowing() : Optional.of(after);
        Optional<Stop> stop = row.stop().map(value -> value.terminalObserved().isPresent() && value.following().isEmpty() && later(after, value.terminalObserved().orElseThrow())
                ? new Stop(value.actionId(), value.submittedFrom(), value.stage(), value.acknowledgement(), value.terminalObserved(), Optional.of(after)) : value);
        SwayLifecycle.State lifecycle = row.lifecycle().origin().game().equals(after.game()) ? SwayLifecycle.consumeFollowing(row.lifecycle(), after) : row.lifecycle();
        return episode(row, lifecycle, start, stop);
    }
    private static Episode following(Episode row, ObservationIdentity actionBefore, ObservationIdentity after) {
        Episode candidate = following(row, after);
        var old = row.lifecycle(); var next = candidate.lifecycle();
        // A later read cannot turn an earlier action into the turn that consumed a newer fact.
        var bounded = new SwayLifecycle.State(old.identity(), old.origin(),
                old.latest().map(value -> atOrAfter(actionBefore, value.source()) ? next.latest().orElseThrow() : value),
                old.terminal().map(value -> atOrAfter(actionBefore, value.source()) ? next.terminal().orElseThrow() : value),
                old.material().map(value -> atOrAfter(actionBefore, value.source()) ? next.material().orElseThrow() : value),
                old.firstGain().map(value -> atOrAfter(actionBefore, value.observed().source()) ? next.firstGain().orElseThrow() : value),
                old.phase().map(value -> atOrAfter(actionBefore, value.source()) ? next.phase().orElseThrow() : value));
        var start = atOrAfter(actionBefore, row.independentActive().binding().before()) ? candidate.startFollowing() : row.startFollowing();
        var stop = row.stop().map(value -> value.terminalObserved().filter(source -> atOrAfter(actionBefore, source)).isPresent() ? candidate.stop().orElseThrow() : value);
        return episode(row, bounded, start, stop);
    }
    public static boolean atOrAfter(ObservationIdentity after, ObservationIdentity before) {
        return after.machineId().equals(before.machineId()) && after.game().equals(before.game())
                && after.frame().episodeRunId().equals(before.frame().episodeRunId())
                && after.frame().identity().player().equals(before.frame().identity().player())
                && after.frame().revision().compareTo(before.frame().revision()) >= 0
                && after.frame().identity().nativeRevision().compareTo(before.frame().identity().nativeRevision()) >= 0
                && after.frame().identity().dateRaw().compareTo(before.frame().identity().dateRaw()) >= 0;
    }
    static boolean later(ObservationIdentity after, ObservationIdentity before) {
        return after.machineId().equals(before.machineId()) && after.game().equals(before.game()) && after.frame().episodeRunId().equals(before.frame().episodeRunId())
                && after.frame().identity().player().equals(before.frame().identity().player())
                && (after.frame().identity().nativeRevision().compareTo(before.frame().identity().nativeRevision()) > 0 || after.frame().identity().dateRaw().compareTo(before.frame().identity().dateRaw()) > 0);
    }
    public static boolean historicalPendingUnresolved(Ledger ledger) {
        return ledger.imported().flatMap(SwayLegacyImport.Imported::pending).map(pending -> java.util.stream.Stream.concat(ledger.resolved().stream(), ledger.previous().stream())
                .noneMatch(row -> row.identity().actionId().equals(pending.actionId()) && row.importedIntent().isPresent())).orElse(false);
    }
    private static void binding(String machine, String episode, SwayNativeWire.Binding binding) { require(binding.before().machineId().equals(machine) && binding.before().frame().episodeRunId().equals(episode), "Sway domain crossed machine/episode"); }
    static Episode episode(Episode row, SwayLifecycle.State lifecycle, Optional<ObservationIdentity> following, Optional<Stop> stop) { return new Episode(row.identity(), row.originalIntent(), row.independentActive(), row.nativeReceipt(), row.retainedReceipt(), lifecycle, following, stop, row.importedIntent(), row.retainedScopes()); }
    static Ledger resolved(Ledger prior, Episode result) { return with(prior, prior.pending(), Optional.of(result), prior.previous(), prior.schedule()); }
    static Ledger with(Ledger prior, Optional<Pending> pending, Optional<Episode> resolved, List<Episode> history, Optional<OrdinarySwaySchedule.State> schedule) { return new Ledger(prior.machineId(), prior.episodeRunId(), pending, resolved, history, schedule, prior.originalMigrationInput(), prior.imported(), prior.activeStage()); }
}
