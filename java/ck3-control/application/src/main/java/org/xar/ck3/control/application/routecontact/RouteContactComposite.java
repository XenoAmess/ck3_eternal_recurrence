package org.xar.ck3.control.application.routecontact;

import static org.xar.ck3.control.application.routecontact.RouteContactModel.*;
import java.math.BigInteger;
import java.time.Clock;
import java.time.Instant;
import java.time.Duration;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.AdvanceObservationPort;
import org.xar.ck3.control.application.advance.AdvanceClock;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;

/** Only the two original route composites. The existing shared life/battle clocks execute every durable child. */
public final class RouteContactComposite implements CompositeActionPort {
    public static final String HANDLER = "native-route-contact-composites-v1";
    public static final String OBSERVER = "xar.ck3.java-route-contact-observation/v1";
    /** Exact missing/stale same-frame proof; source, owner and frame violations retain their own errors. */
    public static final class ProofUnavailable extends IllegalArgumentException {
        private static final long serialVersionUID = 1L;
        public ProofUnavailable() { super("route complete same-frame inputs changed or followup exhausted"); }
    }
    /** The source is the one held writer branch, not an independent planner cache or a copied Python transcript. */
    public interface History {
        List<RouteContactProofs.QueryEntry> survivingQueries(ActionCommand parent);
        List<TimelineEntry> survivingTimeline(ActionCommand parent);
    }
    /** Same shared application evidence archive as the original clock; it stores facts and cannot advance a writer. */
    public interface EvidenceArchive {
        ExactRef completed(ActionCommand parent, Completion completion);
        ExactRef failed(ActionCommand parent, ContactFailure failure);
    }
    public record ContactRefresh(AdvanceObservationPort.Frame from, Optional<ActionReceipt> child,
            Optional<AdvanceObservationPort.Frame> published, Optional<String> ackStatus, Optional<RawJson> originalDriverResult) {
        public ContactRefresh {
            Objects.requireNonNull(from); child = Objects.requireNonNull(child); published = Objects.requireNonNull(published); ackStatus = Objects.requireNonNull(ackStatus);
            originalDriverResult = Objects.requireNonNull(originalDriverResult); ackStatus.ifPresent(StrictJson::text);
            StrictJson.require(originalDriverResult.isEmpty() || child.filter(RouteContactComposite::currentPauseConfirmed).isPresent(), "complete original pause Driver result requires its actual typed child");
            child.ifPresent(value -> StrictJson.require(value.command().operation().value().equals("pause-map")
                    && value.command().before().equals(from.identity()) && value.command().source().equals(from.source())
                    && value.command().sessionId().equals(from.sessionId()), "contact refresh child crossed its actual original frame"));
            StrictJson.require(ackStatus.isEmpty() || child.isPresent(), "contact refresh ACK requires its actual child");
            StrictJson.require(published.isEmpty() || child.isPresent() && ackStatus.equals(Optional.of("already_paused")), "contact refresh publication requires the original already-paused child");
        }
        /** Explicit historical/controller DATA; current shared clocks retain the actual complete primitive result. */
        public ContactRefresh(AdvanceObservationPort.Frame from, Optional<ActionReceipt> child, Optional<AdvanceObservationPort.Frame> published, Optional<String> ackStatus) {
            this(from, child, published, ackStatus, Optional.empty());
        }
    }
    public record Completion(AdvanceObservationPort.Frame starting, AdvanceObservationPort.Frame ending, Proof proof,
            Optional<Transition> transition, ClockResult clockResult, List<ActionReceipt> children, Optional<ContactRefresh> refresh) {
        public Completion { Objects.requireNonNull(starting); Objects.requireNonNull(ending); Objects.requireNonNull(proof);
            transition = Objects.requireNonNull(transition); Objects.requireNonNull(clockResult); children = List.copyOf(children); refresh = Objects.requireNonNull(refresh);
            StrictJson.require(clockResult.nativeClockVerified() && !clockResult.unknown() && clockResult.failureEvidence().isEmpty(),
                    "completed route requires a verified clock without failure originals");
            if (refresh.isPresent()) {var actual = refresh.orElseThrow(); StrictJson.require(actual.from().equals(clockResult.ending())
                    && actual.published().equals(Optional.of(ending)) && actual.child().filter(children::contains).isPresent(), "completed contact refresh differs from original clock/child/publication");} }
        public Completion(AdvanceObservationPort.Frame starting, AdvanceObservationPort.Frame ending, Proof proof,
                Optional<Transition> transition, ClockResult clockResult, List<ActionReceipt> children) {
            this(starting, ending, proof, transition, clockResult, children, Optional.empty());
        }
    }
    public record ContactFailure(AdvanceObservationPort.Frame starting, AdvanceObservationPort.Frame ending, Proof proof,
            String status, boolean strictFollowupUnresolved, List<ActionReceipt> children, List<ExactRef> failureEvidence,
            Optional<ClockResult> clockResult, Optional<ContactRefresh> refresh, Optional<String> originalErrorMessage) {
        public ContactFailure { Objects.requireNonNull(starting); Objects.requireNonNull(ending); Objects.requireNonNull(proof);
            StrictJson.text(status); children = List.copyOf(children); failureEvidence = List.copyOf(failureEvidence);
            clockResult = Objects.requireNonNull(clockResult); refresh = Objects.requireNonNull(refresh); originalErrorMessage = Objects.requireNonNull(originalErrorMessage); originalErrorMessage.ifPresent(StrictJson::text);
            clockResult.ifPresent(value -> StrictJson.require(value.nativeClockVerified() && !value.unknown() && value.originalReport().isPresent(), "partial contact failure requires its actual completed clock report"));
            if (refresh.isPresent()) StrictJson.require(clockResult.isPresent() && refresh.orElseThrow().from().equals(clockResult.orElseThrow().ending()), "partial refresh lacks its original completed clock");
            StrictJson.require(originalErrorMessage.isEmpty() || clockResult.isPresent() && refresh.isPresent(), "partial postcondition error needs its actual completed clock and refresh branch"); }
        public ContactFailure(AdvanceObservationPort.Frame starting, AdvanceObservationPort.Frame ending, Proof proof,
                String status, boolean strictFollowupUnresolved, List<ActionReceipt> children, List<ExactRef> failureEvidence,
                Optional<ClockResult> clockResult, Optional<ContactRefresh> refresh) {
            this(starting, ending, proof, status, strictFollowupUnresolved, children, failureEvidence, clockResult, refresh, Optional.empty());
        }
        public ContactFailure(AdvanceObservationPort.Frame starting, AdvanceObservationPort.Frame ending, Proof proof,
                String status, boolean strictFollowupUnresolved, List<ActionReceipt> children, List<ExactRef> failureEvidence) {
            this(starting, ending, proof, status, strictFollowupUnresolved, children, failureEvidence, Optional.empty(), Optional.empty());
        }
        public ContactFailure(AdvanceObservationPort.Frame starting, AdvanceObservationPort.Frame ending, Proof proof,
                String status, boolean strictFollowupUnresolved, List<ActionReceipt> children) {
            this(starting, ending, proof, status, strictFollowupUnresolved, children, List.of());
        }
    }
    /** Method references to shared BattleAdvanceComposite.executeWindow and LifeAdvanceComposite exact-day execution. */
    public interface Clocks {
        ClockResult window(ActionCommand parent, Children children, AdvanceObservationPort.Frame starting, Proof proof, int speed) throws InterruptedException;
        ClockResult exactDay(ActionCommand parent, Children children, AdvanceObservationPort.Frame starting, Proof proof, int speed) throws InterruptedException;
        /** One durable pause-map child. Only called after a known clock result; must preserve its actual ACK. */
        PauseRefresh refreshPaused(ActionCommand parent, Children children, AdvanceObservationPort.Frame ending, Instant deadline) throws InterruptedException;
    }
    @FunctionalInterface public interface SpeedSelection { int select(ActionCommand parent, AdvanceObservationPort.Frame starting, Proof proof, int fallbackSpeed); }
    public enum ClockProgress { POSTCONDITION, MODAL_INTERRUPTED, BOUNDARY_INTERRUPTED, WALL_TIMEOUT_WITH_DATE_PROGRESS, POSTCONDITION_FAILED;
        public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
    }
    public record ClockResult(AdvanceObservationPort.Frame ending, boolean nativeClockVerified, boolean unknown, String reason,
            ClockProgress progressStatus, int timelineSpeed, String timelinePolicy, boolean checkpointEligible,
            Optional<ClockStatusRead.Observation> nativeStopRead, List<ExactRef> failureEvidence, Optional<RawJson> originalReport) {
        public ClockResult { Objects.requireNonNull(ending); StrictJson.text(reason); Objects.requireNonNull(progressStatus); StrictJson.text(timelinePolicy);
            nativeStopRead = Objects.requireNonNull(nativeStopRead); failureEvidence = List.copyOf(failureEvidence); originalReport = Objects.requireNonNull(originalReport);
            StrictJson.require(!nativeClockVerified || failureEvidence.isEmpty(), "verified clock cannot carry failure originals");
            StrictJson.require(!unknown || !nativeClockVerified, "unknown clock cannot be verified"); StrictJson.require(timelineSpeed >= 1 && timelineSpeed <= 5, "actual timeline speed required");
            StrictJson.require(originalReport.isEmpty() || nativeClockVerified && !unknown && failureEvidence.isEmpty(), "an original completed clock report cannot describe an unresolved clock"); }
        /** Explicit historical/DATA shape; current shared clocks supply the actual complete report. */
        public ClockResult(AdvanceObservationPort.Frame ending, boolean nativeClockVerified, boolean unknown, String reason,
                ClockProgress progressStatus, int timelineSpeed, String timelinePolicy, boolean checkpointEligible,
                Optional<ClockStatusRead.Observation> nativeStopRead, List<ExactRef> failureEvidence) {
            this(ending, nativeClockVerified, unknown, reason, progressStatus, timelineSpeed, timelinePolicy, checkpointEligible, nativeStopRead, failureEvidence, Optional.empty());
        }
        public ClockResult(AdvanceObservationPort.Frame ending, boolean nativeClockVerified, boolean unknown, String reason,
                ClockProgress progressStatus, int timelineSpeed, String timelinePolicy, boolean checkpointEligible,
                Optional<ClockStatusRead.Observation> nativeStopRead) {
            this(ending, nativeClockVerified, unknown, reason, progressStatus, timelineSpeed, timelinePolicy, checkpointEligible, nativeStopRead, List.of());
        }
        public ClockResult(AdvanceObservationPort.Frame ending, boolean nativeClockVerified, boolean unknown, String reason,
                ClockProgress progressStatus, int timelineSpeed, String timelinePolicy, boolean checkpointEligible) {
            this(ending, nativeClockVerified, unknown, reason, progressStatus, timelineSpeed, timelinePolicy, checkpointEligible, Optional.empty());
        }
        public ClockResult(AdvanceObservationPort.Frame ending, boolean nativeClockVerified, boolean unknown, String reason) {
            this(ending, nativeClockVerified, unknown, reason, nativeClockVerified ? ClockProgress.POSTCONDITION : ClockProgress.POSTCONDITION_FAILED, RouteContactCodec.frame(ending).speed(), "fixture_or_retained_clock", nativeClockVerified);
        }
    }
    public record PauseRefresh(ActionReceipt child, String ackStatus, Optional<RawJson> originalDriverResult) {
        public PauseRefresh { Objects.requireNonNull(child); StrictJson.text(ackStatus); originalDriverResult = Objects.requireNonNull(originalDriverResult); }
        public PauseRefresh(ActionReceipt child, String ackStatus) { this(child, ackStatus, Optional.empty()); }
    }
    public record Settings(int effectiveRouteSpeed, boolean explicitCampaignDeadline, Duration commandTimeout, int maximumRefreshFrames) {
        public Settings { StrictJson.require(effectiveRouteSpeed >= 1 && effectiveRouteSpeed <= 5, "configured effective route speed required");
            Objects.requireNonNull(commandTimeout); StrictJson.require(!commandTimeout.isNegative() && !commandTimeout.isZero()
                    && maximumRefreshFrames >= 1 && maximumRefreshFrames <= 65536, "bounded original command timeout/refresh reads required"); }
        public Settings(int effectiveRouteSpeed, boolean explicitCampaignDeadline) { this(effectiveRouteSpeed, explicitCampaignDeadline, Duration.ofSeconds(30), 1024); }
    }
    private final AdvanceObservationPort observations;
    private final History history;
    private final Clocks clocks;
    private final Settings settings;
    private final Clock clock;
    private final EvidenceArchive archive;
    private final Optional<SpeedSelection> speedTrial;
    public RouteContactComposite(AdvanceObservationPort observations, History history, Clocks clocks, Settings settings, Clock clock, EvidenceArchive archive) {
        this(observations, history, clocks, settings, clock, archive, Optional.empty());
    }
    public RouteContactComposite(AdvanceObservationPort observations, History history, Clocks clocks, Settings settings, Clock clock, EvidenceArchive archive, Optional<SpeedSelection> speedTrial) {
        this.observations = Objects.requireNonNull(observations); this.history = Objects.requireNonNull(history);
        this.clocks = Objects.requireNonNull(clocks); this.settings = Objects.requireNonNull(settings); this.clock = Objects.requireNonNull(clock);
        this.archive = Objects.requireNonNull(archive);
        this.speedTrial = Objects.requireNonNull(speedTrial);
    }
    @Override public String handlerId() { return HANDLER; }
    @Override public boolean supports(OperationKey operation) { return RouteContactSteps.supports(operation.value()); }
    @Override public void validate(ActionCommand parent) { requireIntent(parent, prepare(parent)); }
    /** Reuses the actual current frame and surviving-history proof; no child submission or action permission is issued. */
    public Proof project(ActionCommand provisional) { return prepare(provisional).proof(); }
    private record Entry(AdvanceObservationPort.Frame raw, Frame frame, Proof proof) { }
    private Entry prepare(ActionCommand parent) {
        StrictJson.require(supports(parent.operation()) && parent.deadline().isAfter(clock.instant()), "route operation/deadline unavailable");
        RouteContactSteps.Request request = RouteContactSteps.parse(parent.operation().value());
        AdvanceObservationPort.Frame raw = observations.current(parent, parent.deadline()); Frame frame = RouteContactCodec.frame(raw);
        StrictJson.require(raw.identity().equals(parent.before()) && raw.source().equals(parent.source()) && raw.sessionId().equals(parent.sessionId()), "route starting source/revision changed");
        StrictJson.require(frame.mapReady() && frame.paused() && !frame.playerDecision(), "route advance requires paused map without pending player decision");
        var days = RouteContactProofs.oneDayEntries(frame, history.survivingQueries(parent), history.survivingTimeline(parent));
        Proof proof = request.days() == 1 ? days.get(request.scope()) : RouteContactProofs.window(frame, days, request.scope(), request.days(), settings.explicitCampaignDeadline()).orElse(null);
        if (proof == null) throw new ProofUnavailable();
        if (request.days() > 1) StrictJson.require(frame.ownArmies().stream().filter(Army::controllable).noneMatch(army -> army.inCombat() || army.retreating()), "route window rejects active combat/retreat");
        return new Entry(raw, frame, proof);
    }
    private static void requireIntent(ActionCommand parent, Entry actual) {
        requireIntent(parent, actual.frame(), actual.proof());
    }
    static void requireIntent(ActionCommand parent, Frame actual, Proof proof) {
        StrictJson.require(parent.expected().observerSchema().equals(OBSERVER) && parent.expected().values().equals(expected(proof)),
                "route submitted expectation differs from the actual source-bound proof");
        var controlled = actual.controlledIds().stream().map(BigInteger::valueOf).collect(java.util.stream.Collectors.toUnmodifiableSet());
        var required = proof.kind() == ProofKind.BOUNDED_FROZEN_ROUTE_WINDOW ? controlled : java.util.Set.of(BigInteger.valueOf(proof.subjectId()));
        StrictJson.require(controlled.containsAll(parent.claims().armyIds()) && parent.claims().armyIds().containsAll(required),
                "route submitted army claims differ from actual controlled units; hostile watches are not owned claims");
    }
    /** Current pause confirmations carry no gameplay/day credit. Legacy Applied is accepted only by archived readers. */
    public static boolean currentPauseConfirmed(ActionReceipt child) {
        Objects.requireNonNull(child);
        return child.command().operation().value().equals("pause-map") && child.state() instanceof ActionState.Settled settled
                && settled.settlement() instanceof ActionState.PauseConfirmed && child.outcome() == ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT;
    }
    @Override public ActionPorts.PostconditionResult run(ActionCommand parent, Children children) throws InterruptedException {
        Entry entry = prepare(parent); requireIntent(parent, entry); Proof proof = entry.proof();
        int speed = proof.kind() == ProofKind.UNAVOIDABLE_CURRENT_PROVINCE_CONTACT ? 1 : settings.effectiveRouteSpeed();
        if (proof.horizonDays() == 1 && speedTrial.isPresent()) speed = speedTrial.orElseThrow().select(parent, entry.raw(), proof, speed);
        ClockResult advanced = proof.kind() == ProofKind.BOUNDED_FROZEN_ROUTE_WINDOW
                ? clocks.window(parent, children, entry.raw(), proof, speed) : clocks.exactDay(parent, children, entry.raw(), proof, speed);
        // A timeout/unknown child forbids every later primitive, including pause cleanup and same-date refresh.
        if (advanced.unknown() || !advanced.nativeClockVerified() || children.completed().stream().anyMatch(child -> child.outcome() == ActionReceipt.Outcome.UNRESOLVED))
            return failed(parent, entry, advanced.ending(), advanced.reason(), children, false, advanced.failureEvidence());
        AdvanceObservationPort.Frame endingRaw = advanced.ending(); Frame ending = RouteContactCodec.frame(endingRaw);
        boolean controlOnly = controlEnding(entry.frame(), ending, advanced);
        if (!controlOnly && proof.kind() == ProofKind.UNAVOIDABLE_CURRENT_PROVINCE_CONTACT && (!ending.mapReady() || !ending.paused()))
            return failedAfterClock(parent, entry, endingRaw, "contact day lacks its original paused refresh map", children, true, advanced,
                    Optional.of(new ContactRefresh(endingRaw, Optional.empty(), Optional.empty(), Optional.empty())),
                    Optional.of("the proof-bound unavoidable contact day ended without a paused map eligible for one same-date refresh"));
        if (!validEnding(entry.frame(), ending, proof) && !controlOnly) return failedAfterClock(parent, entry, endingRaw, "route clock lacks original paused successor/date postcondition", children, false, advanced, Optional.empty());
        Optional<Transition> transition = Optional.empty();
        Optional<ContactRefresh> refreshEvidence = Optional.empty();
        if (!controlOnly && proof.kind() == ProofKind.UNAVOIDABLE_CURRENT_PROVINCE_CONTACT) {
            transition = RouteContactPostconditions.observed(entry.frame(), ending, proof);
            if (transition.isEmpty()) {
                refreshEvidence = Optional.of(new ContactRefresh(endingRaw, Optional.empty(), Optional.empty(), Optional.empty()));
                // Exactly one original same-date refresh; it is a durable child, not a retry of the clock or a second day.
                if (!parent.deadline().isAfter(clock.instant())) return failedAfterClock(parent, entry, endingRaw, "same-date contact refresh deadline exhausted", children, true, advanced, refreshEvidence,
                        Optional.of("same-date unavoidable-contact refresh timed out before pause-map submission"));
                Instant refreshDeadline = clock.instant().plus(settings.commandTimeout());
                if (refreshDeadline.isAfter(parent.deadline())) refreshDeadline = parent.deadline();
                PauseRefresh refresh;
                try { refresh = clocks.refreshPaused(parent, children, endingRaw, refreshDeadline); }
                catch (RuntimeException unavailable) { return failedAfterClock(parent, entry, endingRaw, "same-date contact refresh submission unavailable: " + unavailable.getMessage(), children, true, advanced, refreshEvidence, Optional.ofNullable(unavailable.getMessage()).filter(value -> !value.isBlank())); }
                refreshEvidence = Optional.of(new ContactRefresh(endingRaw, Optional.of(refresh.child()), Optional.empty(),
                        currentPauseConfirmed(refresh.child()) ? Optional.of(refresh.ackStatus()) : Optional.empty(), refresh.originalDriverResult()));
                if (!currentPauseConfirmed(refresh.child()) || !refresh.ackStatus().equals("already_paused"))
                    return failedAfterClock(parent, entry, endingRaw, "same-date contact refresh ACK/readback unavailable; never replay", children, true, advanced, refreshEvidence,
                            Optional.of(refreshFailureMessage(refresh)));
                Frame prior = ending;
                try {
                    for (int count = 0; count < settings.maximumRefreshFrames() && refreshDeadline.isAfter(clock.instant()); count++) {
                        endingRaw = observations.next(parent, endingRaw.identity(), refreshDeadline); ending = RouteContactCodec.frame(endingRaw);
                        if (RouteContactPostconditions.newer(prior, ending)) break;
                    }
                } catch (RuntimeException unavailable) { return failedAfterClock(parent, entry, endingRaw, "same-date contact refresh readback unavailable: " + unavailable.getMessage(), children, true, advanced, refreshEvidence, Optional.ofNullable(unavailable.getMessage()).filter(value -> !value.isBlank())); }
                if (!RouteContactPostconditions.newer(prior, ending)) return failedAfterClock(parent, entry, endingRaw, "same-date contact refresh did not publish a newer native frame", children, true, advanced, refreshEvidence,
                        Optional.of("same-date unavoidable-contact refresh timed out waiting for a newer native frame"));
                refreshEvidence = Optional.of(new ContactRefresh(advanced.ending(), Optional.of(refresh.child()), Optional.of(endingRaw), Optional.of(refresh.ackStatus()), refresh.originalDriverResult()));
                if (!RouteContactPostconditions.samePausedRefreshOwner(prior, ending)) return failedAfterClock(parent, entry, endingRaw, "same-date contact refresh owner/date/speed/native revision changed", children, true, advanced, refreshEvidence,
                        Optional.of("same-date unavoidable-contact refresh did not publish a newer frame for the same paused timeline owner"));
                transition = RouteContactPostconditions.observed(entry.frame(), ending, proof);
                if (transition.isEmpty()) transition = RouteContactPostconditions.predictedEndpoint(entry.frame(), ending, proof);
                if (transition.isEmpty()) return failedAfterClock(parent, entry, endingRaw, proof.strictFollowup() ? "exhausted_without_strong_transition" : "contact transition not observed after one same-date refresh", children, true, advanced, refreshEvidence,
                        Optional.of("the proof-bound unavoidable contact day advanced and published one same-date refresh, but the required transition was not observed; required_transition="
                                + (proof.strictFollowup() ? "episode, war, subject-army, combat, or retreat transition" : "combat, retreat, war/episode transition, or hostile state change")
                                + "; refreshed_revision=" + ending.revision() + ", refreshed_native_revision=" + ending.nativeRevision()));
            }
        }
        ExactRef evidence = archive.completed(parent, new Completion(entry.raw(), endingRaw, proof, transition, advanced, children.completed(), refreshEvidence));
        return effect(parent, entry.frame(), endingRaw, proof, transition, advanced, evidence, children.completed(), controlOnly);
    }
    /** No child interface, no resume, no pause refresh, and no attempt to infer lost clock status from geometry. */
    @Override public ActionPorts.PostconditionResult observe(ActionCommand parent, CompositeExecution retained) {
        StrictJson.require(retained.handlerId().equals(HANDLER) && retained.guard().observed().equals(parent.before())
                && retained.guard().source().equals(parent.source()) && retained.guard().sessionId().equals(parent.sessionId())
                && retained.guard().operation().equals(parent.operation()), "retained route composite parent/guard differs");
        return new ActionPorts.Pending("retained route composite requires original child clock/transition evidence; UNKNOWN never grants replay or cleanup",
                List.of(retained.guard().nativeEvidence()));
    }
    private static boolean validEnding(Frame before, Frame after, Proof proof) {
        return after.mapReady() && after.paused() && RouteContactPostconditions.newer(before, after)
                && after.owner().machineId().equals(before.owner().machineId()) && after.owner().game().equals(before.owner().game())
                && after.owner().sessionId().equals(before.owner().sessionId()) && after.owner().connectionGeneration().equals(before.owner().connectionGeneration())
                && after.owner().bridgePid() == before.owner().bridgePid() && after.dateRaw() >= before.dateRaw() && after.dateRaw() <= proof.targetDateRaw();
    }
    /** The shared helper still verifies real settled Arm/Cancel, independent IDLE and a fresh semantic packet. */
    private static boolean controlEnding(Frame before, Frame after, ClockResult clockResult) {
        return clockResult.nativeStopRead().isPresent() && after.owner().equals(before.owner())
                && after.mapReady() && after.paused() && after.playerDecision()
                && after.dateRaw() == before.dateRaw() && after.nativeRevision().equals(before.nativeRevision())
                && after.revision().compareTo(before.revision()) >= 0;
    }
    private static ActionPorts.Pending pending(String reason, AdvanceObservationPort.Frame ending) { return new ActionPorts.Pending(reason, List.of(ending.originalEvidence())); }
    private ActionPorts.Pending failed(ActionCommand parent, Entry entry, AdvanceObservationPort.Frame ending, String status, Children children) {
        return failed(parent, entry, ending, status, children, false);
    }
    private ActionPorts.Pending failed(ActionCommand parent, Entry entry, AdvanceObservationPort.Frame ending, String status, Children children, boolean enteredContactFollowup) {
        return failed(parent, entry, ending, status, children, enteredContactFollowup, List.of());
    }
    private ActionPorts.Pending failed(ActionCommand parent, Entry entry, AdvanceObservationPort.Frame ending, String status, Children children,
            boolean enteredContactFollowup, List<ExactRef> failureEvidence) {
        return failed(parent, entry, ending, status, children, enteredContactFollowup, failureEvidence, Optional.empty(), Optional.empty());
    }
    private ActionPorts.Pending failedAfterClock(ActionCommand parent, Entry entry, AdvanceObservationPort.Frame ending, String status, Children children,
            boolean enteredContactFollowup, ClockResult actual, Optional<ContactRefresh> refresh) {
        return failedAfterClock(parent, entry, ending, status, children, enteredContactFollowup, actual, refresh, Optional.empty());
    }
    private static String refreshFailureMessage(PauseRefresh refresh) {
        if (refresh.child().state() instanceof ActionState.Unknown unknown) return unknown.reason();
        if (refresh.child().state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.Rejected rejected) return rejected.reason();
        return "same-date unavoidable-contact refresh expected an already_paused ACK, got " + refresh.ackStatus();
    }
    private ActionPorts.Pending failedAfterClock(ActionCommand parent, Entry entry, AdvanceObservationPort.Frame ending, String status, Children children,
            boolean enteredContactFollowup, ClockResult actual, Optional<ContactRefresh> refresh, Optional<String> originalMessage) {
        Optional<ClockResult> original = actual.originalReport().isPresent() ? Optional.of(actual) : Optional.empty();
        return failed(parent, entry, ending, status, children, enteredContactFollowup, List.of(), original, original.isPresent() ? refresh : Optional.empty(), original.isPresent() ? originalMessage : Optional.empty());
    }
    private ActionPorts.Pending failed(ActionCommand parent, Entry entry, AdvanceObservationPort.Frame ending, String status, Children children,
            boolean enteredContactFollowup, List<ExactRef> failureEvidence, Optional<ClockResult> actualClock, Optional<ContactRefresh> refresh) {
        return failed(parent, entry, ending, status, children, enteredContactFollowup, failureEvidence, actualClock, refresh, Optional.empty());
    }
    private ActionPorts.Pending failed(ActionCommand parent, Entry entry, AdvanceObservationPort.Frame ending, String status, Children children,
            boolean enteredContactFollowup, List<ExactRef> failureEvidence, Optional<ClockResult> actualClock, Optional<ContactRefresh> refresh, Optional<String> originalMessage) {
        ExactRef evidence = archive.failed(parent, new ContactFailure(entry.raw(), ending, entry.proof(), status,
                enteredContactFollowup && entry.proof().strictFollowup(), children.completed(), failureEvidence, actualClock, refresh, originalMessage));
        var originals = new java.util.ArrayList<ExactRef>(); originals.add(evidence); originals.add(ending.originalEvidence()); originals.addAll(failureEvidence);
        return new ActionPorts.Pending(originalMessage.orElse(status), originals);
    }
    public static List<ExpectedValue> expected(Proof proof) {
        return List.of(new ExpectedBoolean(new FieldKey("route_contact.completion_verified"), true),
                new ExpectedBoolean(new FieldKey("paused"), true),
                new ExpectedInteger(new FieldKey("route_contact.target_date_raw"), BigInteger.valueOf(proof.targetDateRaw())),
                new ExpectedInteger(new FieldKey("route_contact.requested_horizon_days"), BigInteger.valueOf(proof.horizonDays())));
    }
    private static ActionPorts.PostconditionResult effect(ActionCommand parent, Frame starting, AdvanceObservationPort.Frame raw, Proof proof, Optional<Transition> transition, ClockResult clockResult, ExactRef evidence, List<ActionReceipt> children, boolean controlOnly) {
        var semantic = new ActionState.EffectObservation(raw.identity(), raw.source(), raw.sessionId(), OBSERVER,
                actualValues(starting, RouteContactCodec.frame(raw), proof, transition, clockResult, controlOnly), raw.provenance(), raw.observedAt(), raw.originalEvidence(), List.of(evidence));
        if (controlOnly) return new ActionPorts.CompositeControlObserved(AdvanceClock.compositeControlTerminal(
                parent, clockResult.nativeStopRead().orElseThrow(), children, semantic));
        return new ActionPorts.EffectObserved(semantic);
    }
    public static List<ExpectedValue> actualValues(Frame starting, Frame ending, Proof proof, Optional<Transition> transition, ClockResult clockResult, boolean controlOnly) {
        // The values above attest a verified bounded execution, not a guarantee that the native stop reached its requested target.
        // Actual date/progress/contact are separate fields and checkpoint eligibility still requires a positive actual day delta.
        var actual = new java.util.ArrayList<ExpectedValue>(expected(proof));
        actual.add(new ExpectedInteger(new FieldKey("ending_date_raw"), BigInteger.valueOf(ending.dateRaw())));
        actual.add(new ExpectedInteger(new FieldKey("starting_date_raw"), BigInteger.valueOf(starting.dateRaw())));
        actual.add(new ExpectedInteger(new FieldKey("requested_horizon_days"), BigInteger.valueOf(proof.horizonDays())));
        actual.add(new ExpectedInteger(new FieldKey("elapsed_days"), BigInteger.valueOf((ending.dateRaw() - starting.dateRaw()) / 24)));
        actual.add(new ExpectedText(new FieldKey("progress_status"), clockResult.progressStatus().wire()));
        actual.add(new ExpectedInteger(new FieldKey("timeline_speed"), BigInteger.valueOf(clockResult.timelineSpeed())));
        actual.add(new ExpectedText(new FieldKey("timeline_policy"), clockResult.timelinePolicy()));
        actual.add(new ExpectedBoolean(new FieldKey("native.gameplay_verified"), !controlOnly));
        actual.add(new ExpectedBoolean(new FieldKey("timeline.advance_verified"), !controlOnly && ending.dateRaw() > starting.dateRaw()));
        actual.add(new ExpectedBoolean(new FieldKey("timeline.checkpoint_eligible"), !controlOnly && clockResult.checkpointEligible() && !ending.playerDecision() && ending.dateRaw() > starting.dateRaw()));
        transition.ifPresent(value -> {
            actual.add(new ExpectedText(new FieldKey("contact_transition.postcondition"), value.kind().wire()));
            actual.add(new ExpectedText(new FieldKey("contact_transition.status"), value.kind() == TransitionKind.PREDICTED_CONTACT_BOUNDARY_REACHED ? "predicted_only" : "observed"));
            actual.add(new ExpectedText(new FieldKey("contact_transition.proof_kind"), "unavoidable_current_province_contact"));
            actual.add(new ExpectedBoolean(new FieldKey("contact_transition.contact_observed"), value.contactObserved()));
            actual.add(new ExpectedText(new FieldKey("contact_transition.episode_run_id"), value.episodeRunId()));
            actual.add(new ExpectedInteger(new FieldKey("contact_transition.subject_army_id"), BigInteger.valueOf(value.subjectArmyId())));
            actual.add(new ExpectedInteger(new FieldKey("contact_transition.contact_province_id"), BigInteger.valueOf(value.contactProvinceId())));
            actual.add(new ExpectedInteger(new FieldKey("contact_transition.starting_date_raw"), BigInteger.valueOf(value.startingDateRaw())));
            actual.add(new ExpectedInteger(new FieldKey("contact_transition.ending_date_raw"), BigInteger.valueOf(value.endingDateRaw())));
        });
        if (proof.kind() == ProofKind.BOUNDED_FROZEN_ROUTE_WINDOW)
            actual.add(new ExpectedText(new FieldKey("route_contact_window_context_basis"), "frozen_current_routes"));
        return List.copyOf(actual);
    }
}
