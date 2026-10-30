package org.xar.ck3.control.wave2.events.unhandledevent;

import java.math.BigInteger;
import org.xar.ck3.control.contracts.events.GuiAvailabilityObservation;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.ObjectValue;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.Value;

/** Native displayed-option proposals and the independent after-response predicate. */
public final class UnhandledEventFallback {
    public static final String SCHEMA = "xar.unhandled-event-first-rendered/v1";
    private UnhandledEventFallback() { }
    public enum Phase { FIRST_RENDERED_OPTION, FIRST_RENDERED_DISABLED, FIRST_RENDERED_UNSUPPORTED }
    public enum DisplayPolicy {
        LEGACY_FIRST_ENABLED("native_rendered_index_after_shown_enabled_filter"),
        FIRST_DISPLAYED("native_rendered_index_after_shown_filter"),
        EXPLICIT_REQUESTED("public_explicit_authored_native_option_number");
        private final String wire;
        DisplayPolicy(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record ActiveEvent(BigInteger instanceId, BigInteger optionCount) { }
    public record FrameBinding(String snapshotId, BigInteger revision, BigInteger nativeRevision,
                                BigInteger dateRaw, String episodeRunId, BigInteger connectionGeneration,
                                BigInteger bridgePid, Boolean paused, Boolean mapReady, BigInteger actorCharacterId) { }
    public record Snapshot(FrameBinding binding, ActiveEvent activeEvent, ObjectValue originalSnapshot) {
        public Snapshot { Objects.requireNonNull(binding, "binding"); Objects.requireNonNull(originalSnapshot, "originalSnapshot"); }
    }
    public record Option(BigInteger renderedIndex, BigInteger nativeOptionIndex, Boolean shown,
                          Boolean enabled, String resolvedName, GuiAvailabilityObservation guiAvailability) {
        public Option { Objects.requireNonNull(guiAvailability); }
        public Option(BigInteger renderedIndex, BigInteger nativeOptionIndex, Boolean shown, Boolean enabled, String resolvedName) {
            this(renderedIndex, nativeOptionIndex, shown, enabled, resolvedName, new GuiAvailabilityObservation.LegacyNotReported());
        }
        public boolean selectionAllowed() { return guiAvailability.permitsSelectionWithRawFallback(Boolean.TRUE.equals(enabled)); }
    }
    public record Context(BigInteger currentEventInstanceId, BigInteger snapshotRevision, BigInteger dateRaw,
                           String eventDefinitionKey, List<Option> options, ObjectValue retainedWindowContext) {
        public Context {
            if (options != null) options = List.copyOf(options);
            Objects.requireNonNull(retainedWindowContext, "retainedWindowContext");
            boolean v2 = "current-event-window-context-v2".equals(RetainedJson.string(retainedWindowContext.get("schema")))
                    || BigInteger.TWO.equals(RetainedJson.integer(retainedWindowContext.get("schema_version")));
            if (v2 && options != null && options.stream().anyMatch(option -> option.guiAvailability() instanceof GuiAvailabilityObservation.LegacyNotReported))
                throw new IllegalArgumentException("v2 typed options must retain GUI observations");
        }
    }
    public record Request(Snapshot snapshot, Context context, ObjectValue eventSummary,
                           Value registryDecision, List<String> actionSteps) {
        public Request {
            Objects.requireNonNull(eventSummary, "eventSummary"); Objects.requireNonNull(registryDecision, "registryDecision");
            actionSteps = actionSteps == null ? List.of() : List.copyOf(actionSteps);
        }
    }
    public record Selection(BigInteger renderedIndex, BigInteger nativeOptionIndex, BigInteger optionNumber,
                             String resolvedName, Boolean enabled, String selectedStep,
                             List<BigInteger> excludedDisabledRenderedIndices, GuiAvailabilityObservation guiAvailability) {
        public Selection {
            Objects.requireNonNull(guiAvailability);
            Objects.requireNonNull(renderedIndex); Objects.requireNonNull(nativeOptionIndex); Objects.requireNonNull(optionNumber);
            if (renderedIndex.signum() < 0 || nativeOptionIndex.signum() < 0 || !optionNumber.equals(nativeOptionIndex.add(BigInteger.ONE))
                    || !("select-event-option-" + optionNumber).equals(selectedStep)) throw new IllegalArgumentException("selected native/rendered mapping");
            excludedDisabledRenderedIndices = List.copyOf(excludedDisabledRenderedIndices);
        }
        public Selection(BigInteger renderedIndex, BigInteger nativeOptionIndex, BigInteger optionNumber,
                String resolvedName, Boolean enabled, String selectedStep, List<BigInteger> excludedDisabledRenderedIndices) {
            this(renderedIndex, nativeOptionIndex, optionNumber, resolvedName, enabled, selectedStep,
                    excludedDisabledRenderedIndices, new GuiAvailabilityObservation.LegacyNotReported());
        }
    }
    public record Plan(Phase phase, String selectedStep, String reason, String eventDefinitionKey,
                        BigInteger eventInstanceId, BigInteger snapshotOptionCount, FrameBinding binding,
                        Selection selection, ObjectValue windowContext, Value originalRegistryDecision,
                        ObjectValue originalEventSummary, DisplayPolicy displayPolicy) {
        public Plan {
            Objects.requireNonNull(phase); Objects.requireNonNull(reason); Objects.requireNonNull(eventInstanceId);
            Objects.requireNonNull(snapshotOptionCount); Objects.requireNonNull(binding); Objects.requireNonNull(selection);
            Objects.requireNonNull(windowContext); Objects.requireNonNull(originalRegistryDecision); Objects.requireNonNull(originalEventSummary);
            Objects.requireNonNull(displayPolicy);
        }
        public Plan(Phase phase, String selectedStep, String reason, String eventDefinitionKey,
                BigInteger eventInstanceId, BigInteger snapshotOptionCount, FrameBinding binding,
                Selection selection, ObjectValue windowContext, Value originalRegistryDecision, ObjectValue originalEventSummary) {
            this(phase, selectedStep, reason, eventDefinitionKey, eventInstanceId, snapshotOptionCount, binding, selection,
                    windowContext, originalRegistryDecision, originalEventSummary, DisplayPolicy.LEGACY_FIRST_ENABLED);
        }
        public boolean actionAuthorized() { return false; }
        public boolean offlineFollowupRequired() { return true; }
    }
    public record Ticket(BigInteger eventInstanceId, BigInteger selectedNativeOptionIndex) {
        public Ticket {
            if (!positive(eventInstanceId) || selectedNativeOptionIndex == null || selectedNativeOptionIndex.signum() < 0) {
                throw new IllegalArgumentException("ticket must retain the original event/option identity");
            }
        }
    }
    public record NativeSelection(String status, Boolean postconditionVerified, BigInteger oldEventInstanceId,
                                   BigInteger newEventInstanceId, BigInteger selectedNativeOptionIndex) { }
    public record AfterObservation(Boolean accepted, NativeSelection selection) { }
    public record AfterAssessment(boolean commandAcknowledged, boolean eventInstanceAdvancedVerified) {
        public AfterAssessment {
            if (eventInstanceAdvancedVerified && !commandAcknowledged) throw new IllegalArgumentException("verified advance requires its original accepted result");
        }
        public boolean replayAllowed() { return false; }
    }
    public record ExistingPlan(String phase, String selectedStep, ObjectValue retainedUnhandledFallback) { }

    public static Optional<Plan> plan(Request request) {
        return plan(request, DisplayPolicy.LEGACY_FIRST_ENABLED);
    }
    /** Current owner policy: disabled first displayed row is captured, never skipped to another row. */
    public static Optional<Plan> planFirstDisplayed(Request request) {
        return plan(request, DisplayPolicy.FIRST_DISPLAYED);
    }
    private static Optional<Plan> plan(Request request, DisplayPolicy policy) {
        Objects.requireNonNull(request, "request");
        Snapshot snapshot = request.snapshot(); Context context = request.context();
        if (snapshot == null || context == null || context.options() == null) return Optional.empty();
        List<Option> shown = context.options().stream().filter(option -> Boolean.TRUE.equals(option.shown())).toList();
        if (shown.isEmpty() || shown.stream().anyMatch(option -> option.renderedIndex() == null || option.renderedIndex().signum() < 0)) return Optional.empty();
        if (new HashSet<>(shown.stream().map(Option::renderedIndex).toList()).size() != shown.size()) return Optional.empty();
        List<Option> enabled = shown.stream().filter(Option::selectionAllowed).toList();
        Option first = (policy == DisplayPolicy.FIRST_DISPLAYED || enabled.isEmpty() ? shown : enabled).stream().min(Comparator.comparing(Option::renderedIndex)).orElseThrow();
        ActiveEvent active = snapshot.activeEvent();
        if (active == null || !positive(active.instanceId()) || active.optionCount() == null || first.nativeOptionIndex() == null
                || first.nativeOptionIndex().signum() < 0 || first.nativeOptionIndex().compareTo(active.optionCount()) >= 0
                || !Objects.equals(context.currentEventInstanceId(), active.instanceId())
                || !Objects.equals(context.snapshotRevision(), snapshot.binding().nativeRevision())
                || !Objects.equals(context.dateRaw(), snapshot.binding().dateRaw())) return Optional.empty();
        BigInteger number = first.nativeOptionIndex().add(BigInteger.ONE);
        String step = "select-event-option-" + number;
        boolean selectedEnabled = first.selectionAllowed();
        boolean advertised = request.actionSteps().contains(step);
        Phase phase = selectedEnabled && advertised ? Phase.FIRST_RENDERED_OPTION : !selectedEnabled ? Phase.FIRST_RENDERED_DISABLED : Phase.FIRST_RENDERED_UNSUPPORTED;
        String reason = selectedEnabled && advertised
            ? policy == DisplayPolicy.FIRST_DISPLAYED
                ? "Uncovered event: capture the current card, select its first displayed option under the owner's continuation instruction, then review offline."
                : "Uncovered event: capture the current card, select its first enabled rendered option under the owner's continuation instruction, then review offline."
            : !selectedEnabled ? policy == DisplayPolicy.FIRST_DISPLAYED ? "The first displayed native option is disabled." : "No shown native event option is enabled."
            : "The first rendered option has no advertised native selection step.";
        List<BigInteger> excluded = new ArrayList<>();
        shown.forEach(option -> { if (!option.selectionAllowed()) excluded.add(option.renderedIndex()); });
        Selection selection = new Selection(first.renderedIndex(), first.nativeOptionIndex(), number,
            first.resolvedName(), first.enabled(), step, excluded, first.guiAvailability());
        return Optional.of(new Plan(phase, selectedEnabled && advertised ? step : null, reason, context.eventDefinitionKey(),
            active.instanceId(), active.optionCount(), snapshot.binding(), selection, context.retainedWindowContext(),
            request.registryDecision(), request.eventSummary(), policy));
    }

    /** The real strategy wrapper keeps a selected dedicated strategy and only fills blocked event phases. */
    public static Optional<Plan> proposeForUnhandledPhase(ExistingPlan existing, Request request) {
        Objects.requireNonNull(existing, "existing");
        if (existing.selectedStep() != null || existing.retainedUnhandledFallback() != null
                || existing.phase() == null || !existing.phase().startsWith("active_event")) return Optional.empty();
        return plan(request);
    }

    /** Pure part of capture_unhandled_event_after_v1; artifact writing stays with the original owner. */
    public static Optional<AfterAssessment> assessAfter(Ticket ticket, AfterObservation observed) {
        if (ticket == null) return Optional.empty();
        boolean acknowledged = observed != null && Boolean.TRUE.equals(observed.accepted());
        NativeSelection selection = observed == null ? null : observed.selection();
        boolean verified = acknowledged && selection != null && "event_instance_advanced".equals(selection.status())
            && Boolean.TRUE.equals(selection.postconditionVerified()) && ticket.eventInstanceId().equals(selection.oldEventInstanceId())
            && !ticket.eventInstanceId().equals(selection.newEventInstanceId())
            && ticket.selectedNativeOptionIndex().equals(selection.selectedNativeOptionIndex());
        return Optional.of(new AfterAssessment(acknowledged, verified));
    }
    private static boolean positive(BigInteger value) { return value != null && value.signum() > 0; }
}
