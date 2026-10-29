package org.xar.ck3.control.g2.m6;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Source;

/**
 * Reduces independently copied actual4 observations, never a retained outcome label.
 * The existing native source composer remains the only dynamic cause validator.
 */
public final class M6ObservationReducer {
    public static final String SCHEMA = "xar.g2.m6.copied-observation-report/v1";
    private M6ObservationReducer() { }

    public record Input(String actionId, Optional<M6TerminalSourceComposition.Inputs> baseline,
            M6TerminalSourceComposition.Inputs current) {
        public Input {
            StrictJson.text(actionId); Objects.requireNonNull(baseline); Objects.requireNonNull(current);
            baseline.ifPresent(value -> require(value.execution().isEmpty() && value.termination().isEmpty(),
                    "M6 baseline is a material sample, not a borrowed end journal"));
        }
    }
    public enum Terminal { UNKNOWN, TERMINATED_UNATTRIBUTED, AUTHORED_COMPLETE_TRANSITION }
    public enum MaterialChange {
        BASELINE_NOT_PROVIDED, BASELINE_NOT_ACTIVE, BASELINE_PREDATES_ORIGINAL_START, SAMPLE_UNAVAILABLE, MODIFIER_UNREAD,
        CURRENT_INSTANCE_UNOBSERVED, DATE_ORDER_UNAVAILABLE, INCREASE, NO_INCREASE
    }
    public enum EventOrder { UNKNOWN, MATERIAL_AT_OR_BEFORE_END, MATERIAL_AFTER_END }

    /** These are copied facts, not submission or consumption instructions. */
    public record CauseProof(BigInteger session, long ownerThread, BigInteger branchSequence,
            BigInteger parentToastInvocation, BigInteger endInvocation, int originalEndDateRaw,
            ProjectionJson copiedObservation) {
        public CauseProof {
            for (BigInteger value : List.of(session, branchSequence, parentToastInvocation, endInvocation)) {
                require(value.signum() > 0 && value.compareTo(StrictJson.UINT64_MAX) <= 0, "positive exact uint64 source identity");
            }
            require(ownerThread > 0 && ownerThread <= 0xffff_ffffL, "native owner thread required");
            Objects.requireNonNull(copiedObservation);
        }
    }
    public record Sample(G2M6Contracts.Stamp stamp, G2M6Contracts.NamedValue sway,
            G2M6Contracts.NamedValue blocker) {
        public Sample { Objects.requireNonNull(stamp); Objects.requireNonNull(sway); Objects.requireNonNull(blocker); }
    }
    public record Observation(G2M6Contracts.Identity identity, Terminal terminal,
            Optional<CauseProof> cause, Optional<Sample> baseline, Optional<Sample> current,
            MaterialChange materialChange, Optional<BigInteger> namedDelta, EventOrder eventOrder,
            M6TerminalSourceComposition.Result currentComposition) {
        public Observation {
            Objects.requireNonNull(identity); Objects.requireNonNull(terminal); Objects.requireNonNull(cause);
            Objects.requireNonNull(baseline); Objects.requireNonNull(current); Objects.requireNonNull(materialChange);
            Objects.requireNonNull(namedDelta); Objects.requireNonNull(eventOrder); Objects.requireNonNull(currentComposition);
            require(identity.equals(currentComposition.identity()), "observation identity changed");
            require((terminal == Terminal.AUTHORED_COMPLETE_TRANSITION) == cause.isPresent(), "cause branch differs");
            require(namedDelta.isPresent() == (materialChange == MaterialChange.INCREASE
                    || materialChange == MaterialChange.NO_INCREASE), "unmeasured delta was filled");
        }
        public boolean positiveNamedGainObserved() {
            return materialChange == MaterialChange.INCREASE && current.orElseThrow().sway().points()
                    .orElseThrow().signum() > 0;
        }
        public boolean usefulSchemeComplete() { return false; }
    }
    public record Report(G2Source source, List<Observation> observations, ProjectionJson originalLedger) {
        public Report {
            Objects.requireNonNull(source); observations = List.copyOf(observations);
            Objects.requireNonNull(originalLedger);
        }
        public boolean actionAuthorized() { return false; }
        public boolean ledgerCommitted() { return false; }
        public boolean requestRetried() { return false; }
        public boolean wholeM6Complete() { return false; }
    }

    /**
     * No caller-supplied cause flag, precomputed delta or persisted label is accepted.
     * Baseline and current go through the same strict raw-source composer independently.
     */
    public static Report observe(G2M6Contracts.CampaignEvidence evidence, List<Input> inputs) {
        Objects.requireNonNull(evidence); inputs = List.copyOf(inputs);
        require(inputs.size() <= 64, "finite M6 observation batch required");
        Set<String> seen = new HashSet<>(); List<Observation> rows = new ArrayList<>();
        for (Input input : inputs) {
            require(seen.add(input.actionId()), "M6 observation action duplicated");
            G2M6Contracts.Episode episode = evidence.episodes().stream()
                    .filter(value -> value.identity().actionId().equals(input.actionId())).findFirst()
                    .orElseThrow(() -> new IllegalArgumentException("M6 observation has no original episode"));
            Optional<M6TerminalSourceComposition.Result> before = input.baseline()
                    .map(value -> composeChecked(episode, value));
            var current = composeChecked(episode, input.current());
            rows.add(reduce(episode, before, current));
        }
        return new Report(evidence.source(), rows, evidence.originalLedger());
    }

    private static Observation reduce(G2M6Contracts.Episode episode,
            Optional<M6TerminalSourceComposition.Result> before, M6TerminalSourceComposition.Result current) {
        G2M6Contracts.Identity identity = episode.identity();
        Optional<Sample> baseline = before.flatMap(M6ObservationReducer::sample);
        Optional<Sample> latest = sample(current);
        Optional<CauseProof> cause = current.cause().map(value -> proof(value.observation()));
        Terminal terminal = cause.isPresent() ? Terminal.AUTHORED_COMPLETE_TRANSITION
                : current.nativeState() == M6TerminalSourceComposition.NativeState.TERMINATED_UNATTRIBUTED
                || current.wrapperEnd().isPresent() || current.commonEnd().isPresent()
                ? Terminal.TERMINATED_UNATTRIBUTED : Terminal.UNKNOWN;
        MaterialChange change; Optional<BigInteger> delta = Optional.empty();
        if (before.isEmpty()) change = MaterialChange.BASELINE_NOT_PROVIDED;
        else if (before.orElseThrow().nativeState() != M6TerminalSourceComposition.NativeState.CONTINUE) {
            change = MaterialChange.BASELINE_NOT_ACTIVE;
        } else if (baseline.isEmpty() || latest.isEmpty()) change = MaterialChange.SAMPLE_UNAVAILABLE;
        else if (episode.start().isEmpty() || baseline.orElseThrow().stamp().dateRaw()
                < episode.start().orElseThrow().independentActive().dateRaw()) {
            change = MaterialChange.BASELINE_PREDATES_ORIGINAL_START;
        }
        else if (current.nativeState() == M6TerminalSourceComposition.NativeState.UNKNOWN) {
            change = MaterialChange.CURRENT_INSTANCE_UNOBSERVED;
        } else if (baseline.orElseThrow().sway().points().isEmpty() || latest.orElseThrow().sway().points().isEmpty()) {
            change = MaterialChange.MODIFIER_UNREAD;
        } else if (latest.orElseThrow().stamp().dateRaw() <= baseline.orElseThrow().stamp().dateRaw()) {
            // Independent query revisions do not establish a native transaction or clock domain.
            change = MaterialChange.DATE_ORDER_UNAVAILABLE;
        } else {
            BigInteger difference = latest.orElseThrow().sway().points().orElseThrow()
                    .subtract(baseline.orElseThrow().sway().points().orElseThrow());
            delta = Optional.of(difference);
            change = difference.signum() > 0 ? MaterialChange.INCREASE : MaterialChange.NO_INCREASE;
        }
        EventOrder order = cause.isEmpty() || latest.isEmpty() ? EventOrder.UNKNOWN
                : latest.orElseThrow().stamp().dateRaw() <= cause.orElseThrow().originalEndDateRaw()
                ? EventOrder.MATERIAL_AT_OR_BEFORE_END : EventOrder.MATERIAL_AFTER_END;
        return new Observation(identity, terminal, cause, baseline, latest, change, delta, order, current);
    }

    private static M6TerminalSourceComposition.Result composeChecked(G2M6Contracts.Episode episode,
            M6TerminalSourceComposition.Inputs inputs) {
        inputs.opinion().ifPresent(value -> {
            JsonNode opinion = M6TerminalSourceComposition.parse(value);
            M6TerminalSourceComposition.actual4(opinion);
            M6TerminalSourceComposition.textEquals(opinion, "schema", "xar.ck3.sway-outcome-opinion-v1");
            if (M6TerminalSourceComposition.bool(opinion, "available")) {
                M6TerminalSourceComposition.u64(opinion, "snapshot_revision", 1);
                M6TerminalSourceComposition.signed(opinion, "date_raw");
                M6TerminalSourceComposition.named(opinion.get("scheme_sway_opinion"));
                M6TerminalSourceComposition.named(opinion.get("sway_blocker_opinion"));
            }
        });
        return M6TerminalSourceComposition.compose(episode, inputs);
    }
    private static Optional<Sample> sample(M6TerminalSourceComposition.Result composition) {
        return composition.material().map(value -> new Sample(
                new G2M6Contracts.Stamp(value.revision(), value.dateRaw()), value.sway(), value.blocker()));
    }
    private static CauseProof proof(ProjectionJson copied) {
        JsonNode value = M6TerminalSourceComposition.parse(copied);
        return new CauseProof(M6TerminalSourceComposition.u64(value, "observer_session_identity", 1),
                M6TerminalSourceComposition.integer(value, "owner_thread_id", 1, 0xffff_ffffL),
                M6TerminalSourceComposition.u64(value, "branch_source_sequence", 1),
                M6TerminalSourceComposition.u64(value, "parent_toast_invocation_id", 1),
                M6TerminalSourceComposition.u64(value, "end_original_invocation_id", 1),
                M6TerminalSourceComposition.signed(value.at("/termination_record/native_invocation"), "post_date_raw"), copied);
    }

    /** Report-only JSON. It is never accepted as a replacement for raw native input planes. */
    public static ProjectionJson toJson(Report report) {
        Objects.requireNonNull(report);
        ObjectNode root = StrictJson.object(); root.put("schema", SCHEMA);
        root.put("machine_id", report.source().machineId());
        root.put("observed_at_utc", report.source().observedAtUtc());
        root.set("input_source_ref", report.source().sourceRef().toJson());
        var rows = root.putArray("observations");
        for (Observation observation : report.observations()) {
            ObjectNode row = rows.addObject();
            row.set("original_instance", M6TerminalSourceComposition.identityJson(observation.identity()));
            row.put("terminal", observation.terminal().name()); row.put("material_change", observation.materialChange().name());
            row.put("positive_named_gain_observed", observation.positiveNamedGainObserved());
            if (observation.namedDelta().isEmpty()) row.putNull("named_delta_points");
            else row.put("named_delta_points", observation.namedDelta().orElseThrow().toString());
            row.put("material_end_date_order", observation.eventOrder().name());
            writeSample(row, "baseline", observation.baseline()); writeSample(row, "current", observation.current());
            if (observation.cause().isEmpty()) row.putNull("cause");
            else {
                CauseProof proof = observation.cause().orElseThrow(); ObjectNode cause = row.putObject("cause");
                cause.put("key", M6TerminalSourceComposition.COMPLETE);
                cause.put("observer_session_identity", proof.session().toString()); cause.put("owner_thread_id", proof.ownerThread());
                cause.put("branch_source_sequence", proof.branchSequence().toString());
                cause.put("parent_toast_invocation_id", proof.parentToastInvocation().toString());
                cause.put("end_original_invocation_id", proof.endInvocation().toString());
                cause.put("original_end_date_raw", proof.originalEndDateRaw());
            }
            row.put("useful_scheme_complete", false);
        }
        root.put("whole_m6_complete", false); root.put("action_authorized", false); root.put("ledger_committed", false);
        root.put("request_retried", false); root.put("game_day_credit", 0);
        return ProjectionJson.object(StrictJson.canonical(root, M6SourceProducer.MAX_BYTES), M6SourceProducer.MAX_BYTES);
    }
    private static void writeSample(ObjectNode row, String field, Optional<Sample> sample) {
        if (sample.isEmpty()) { row.putNull(field); return; }
        Sample value = sample.orElseThrow(); ObjectNode output = row.putObject(field);
        output.put("native_revision", value.stamp().nativeRevision().toString()); output.put("date_raw", value.stamp().dateRaw());
        writeNamed(output, "scheme_sway_opinion", value.sway()); writeNamed(output, "sway_blocker_opinion", value.blocker());
    }
    private static void writeNamed(ObjectNode parent, String name, G2M6Contracts.NamedValue value) {
        ObjectNode output = parent.putObject(name); output.put("observed", value.observed()); output.put("present", value.present());
        if (value.value().isEmpty()) output.putNull("value"); else output.put("value", value.value().orElseThrow().toString());
    }
}
