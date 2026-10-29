package org.xar.ck3.control.g2.m6;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.g2.m6.M6TerminalSourceComposition.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Base64;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Consumption;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Episode;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Identity;
import org.xar.ck3.control.g2.m6.G2M6Contracts.NamedValue;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Stamp;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Pure reducer for original Sway observations. The guarded query and sole writer stay outside. */
public final class SwayLifecycle {
    public static final String SCHEMA = "xar.java.sway-lifecycle/v1";
    public static final int MAX_BYTES = 1_048_576;
    private static final Consumption UNCONSUMED = new Consumption(false, Optional.empty());
    private SwayLifecycle() { }

    /** Original inputs are JSON-domain copies, never newly sampled or an attestation by construction. */
    public record Proof(ObservationIdentity source, ProjectionJson originalResolved, Inputs inputs, Optional<ProjectionJson> census) {
        public Proof { Objects.requireNonNull(source); Objects.requireNonNull(originalResolved); Objects.requireNonNull(inputs); Objects.requireNonNull(census); }
        public Proof(ObservationIdentity source, ProjectionJson originalResolved, Inputs inputs) { this(source, originalResolved, inputs, Optional.empty()); }
        @Override public boolean equals(Object other) {
            return other instanceof Proof value && source.equals(value.source)
                    && java.util.Arrays.equals(originalResolved.bytes(), value.originalResolved.bytes())
                    && sameCopy(inputs.completion(), value.inputs.completion()) && sameCopy(inputs.execution(), value.inputs.execution())
                    && sameCopy(inputs.termination(), value.inputs.termination()) && sameCopy(inputs.opinion(), value.inputs.opinion()) && sameCopy(census, value.census);
        }
        @Override public int hashCode() {
            return Objects.hash(source, java.util.Arrays.hashCode(originalResolved.bytes()), copyHash(inputs.completion()),
                    copyHash(inputs.execution()), copyHash(inputs.termination()), copyHash(inputs.opinion()), copyHash(census));
        }
        private static boolean sameCopy(Optional<ProjectionJson> left, Optional<ProjectionJson> right) {
            return left.isPresent() == right.isPresent() && (left.isEmpty() || java.util.Arrays.equals(left.orElseThrow().bytes(), right.orElseThrow().bytes()));
        }
        private static int copyHash(Optional<ProjectionJson> value) { return value.map(raw -> java.util.Arrays.hashCode(raw.bytes())).orElse(0); }
    }
    public record Instance(Proof proof, M6SourceProducer.NativeState state, Consumption consumption) {
        public Instance { Objects.requireNonNull(proof); Objects.requireNonNull(state); Objects.requireNonNull(consumption); }
        public ObservationIdentity source() { return proof.source(); }
        public boolean active() { return state == M6SourceProducer.NativeState.CONTINUE; }
        public boolean observedTerminal() { return state == M6SourceProducer.NativeState.TERMINATED_UNATTRIBUTED; }
    }
    public enum TerminalKind { CURRENT_STATUS, WRAPPER_RETURN, COMMON_RETURN, CAUSAL_END }
    public record Terminal(Proof proof, TerminalKind kind, Optional<Proof> causeProof, Consumption consumption) {
        public Terminal { Objects.requireNonNull(proof); Objects.requireNonNull(kind); Objects.requireNonNull(causeProof); Objects.requireNonNull(consumption); }
        public ObservationIdentity source() { return proof.source(); }
        public boolean terminalCauseObserved() { return kind == TerminalKind.CAUSAL_END || causeProof.isPresent(); }
        public String cause() { return terminalCauseObserved() ? COMPLETE : "unknown"; }
        public boolean instanceTerminalOutcomeObserved() { return true; }
        /** Event time comes only from the copied return frame, never the later query receipt. */
        public Optional<Integer> eventDateRaw() {
            JsonNode wire = parse(compose(causeProof.orElse(proof)).wire()); JsonNode value;
            if (causeProof.isPresent()) { value = wire.at("/causal_observation/termination_record/native_invocation/post_date_raw");
                return value.isIntegralNumber() && value.canConvertToInt() ? Optional.of(value.intValue()) : Optional.empty(); }
            if (kind == TerminalKind.COMMON_RETURN) value = wire.at("/retained_common_end_observation/copied_common_native_end_record/returned/core_frame/date_raw");
            else if (kind == TerminalKind.WRAPPER_RETURN) value = wire.at("/retained_end_observation/copied_termination_record/native_invocation/post_date_raw");
            else if (kind == TerminalKind.CAUSAL_END) value = wire.at("/causal_observation/termination_record/native_invocation/post_date_raw");
            else return Optional.empty();
            return value.isIntegralNumber() && value.canConvertToInt() ? Optional.of(value.intValue()) : Optional.empty();
        }
    }
    public record Material(Proof proof, NamedValue sway, NamedValue blocker, Optional<Integer> totalOpinion,
            boolean trackedActive, boolean terminalObserved, Optional<NamedValue> previousSway, Optional<Proof> previousProof,
            boolean incrementalNamedGain, Consumption consumption) {
        public Material {
            Objects.requireNonNull(proof); Objects.requireNonNull(sway); Objects.requireNonNull(blocker);
            Objects.requireNonNull(totalOpinion); Objects.requireNonNull(previousSway); Objects.requireNonNull(previousProof); Objects.requireNonNull(consumption);
        }
        public ObservationIdentity source() { return proof.source(); }
        public boolean dedicatedBenefitObserved() { return sway.points().filter(value -> value.signum() > 0).isPresent(); }
        public boolean dedicatedSetbackObserved() { return blocker.points().filter(value -> value.signum() < 0).isPresent(); }
    }
    public record Gain(ObservationIdentity baseline, NamedValue before, Proof baselineProof, Material observed) {
        public Gain { Objects.requireNonNull(baseline); Objects.requireNonNull(before); Objects.requireNonNull(baselineProof); Objects.requireNonNull(observed); }
    }
    public record Phase(Proof proof, BigInteger sequence, int executionDateRaw, String branch, Consumption consumption) {
        public Phase { Objects.requireNonNull(proof); Objects.requireNonNull(sequence); Objects.requireNonNull(branch); Objects.requireNonNull(consumption); }
        public ObservationIdentity source() { return proof.source(); }
        public boolean materialEffectObserved() { return false; }
        public boolean nativeTerminalStateObserved() { return false; }
    }
    public record State(Identity identity, ObservationIdentity origin, Optional<Instance> latest,
            Optional<Terminal> terminal, Optional<Material> material, Optional<Gain> firstGain, Optional<Phase> phase) {
        public State {
            Objects.requireNonNull(identity); Objects.requireNonNull(origin); Objects.requireNonNull(latest);
            Objects.requireNonNull(terminal); Objects.requireNonNull(material); Objects.requireNonNull(firstGain); Objects.requireNonNull(phase);
            require(origin.frame().identity().player().equals(BigInteger.valueOf(identity.actorCharacterId())), "Sway lifecycle origin player differs");
            latest.ifPresent(value -> { validateProof(identity, origin, value.proof());
                var raw = M6SourceProducer.fromRawCompletion(value.proof().inputs().completion().orElseThrow().bytes(), identity);
                require(raw.nativeState() == value.state(), "persisted instance state differs from copied native source"); });
            terminal.ifPresent(value -> {
                validateProof(identity, origin, value.proof()); require(hasTerminal(compose(value.proof()), value.kind()), "persisted terminal lacks its native proof");
                value.causeProof().ifPresent(proof -> { validateProof(identity, origin, proof); require(compose(proof).cause().isPresent(), "persisted cause lacks qualified dynamic relation"); });
            });
            material.ifPresent(value -> validateMaterial(identity, origin, value));
            firstGain.ifPresent(value -> {
                sameScope(origin, value.baseline()); validateMaterial(identity, origin, value.observed());
                validateProof(identity, origin, value.baselineProof());
                require(value.baselineProof().source().equals(value.baseline())
                        && materialFact(value.baselineProof()).filter(points -> points.active() && points.sway().equals(value.before())).isPresent(), "persisted gain baseline differs from its independently copied named source");
                require(value.observed().incrementalNamedGain() && value.observed().previousSway().filter(value.before()::equals).isPresent()
                        && date(value.observed().source()) > date(value.baseline()) && value.before().points().isPresent()
                        && value.observed().sway().points().filter(points -> points.compareTo(value.before().points().orElseThrow()) > 0).isPresent(), "persisted gain is not a later independently named increase");
            });
            phase.ifPresent(value -> { validateProof(identity, origin, value.proof()); JsonNode row = phaseRow(value.proof(), value.sequence());
                require(text(row, "source_branch").equals(value.branch()) && signed(row, "date_raw") == value.executionDateRaw(), "persisted phase differs from copied execution row"); });
        }
    }

    public static State empty(Identity identity, ObservationIdentity origin) {
        return new State(identity, origin, Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty());
    }
    /** All planes were issued through the owning real guarded read coordinator before this pure call. */
    public static State observe(State state, Episode episode, Inputs inputs, ObservationIdentity queried) {
        Objects.requireNonNull(state); Objects.requireNonNull(episode); Objects.requireNonNull(inputs); Objects.requireNonNull(queried);
        require(state.identity().equals(episode.identity()), "Sway observation belongs to another original episode"); sameScope(state.origin(), queried);
        M6TerminalSourceComposition.validateInputs(inputs, episode.identity(), queried);
        Result result = M6TerminalSourceComposition.compose(episode, inputs);
        Proof proof = new Proof(queried, compactOriginal(episode), inputs);
        Optional<Instance> latest = state.latest();
        if (inputs.completion().isPresent()) {
            var observation = M6SourceProducer.fromRawCompletion(inputs.completion().orElseThrow().bytes(), state.identity());
            Consumption consumed = state.latest().filter(old -> sameInstanceFacts(old.proof().inputs().completion().orElseThrow(), inputs.completion().orElseThrow()))
                    .map(Instance::consumption).orElse(UNCONSUMED);
            latest = Optional.of(new Instance(proof, observation.nativeState(), consumed));
        }
        Optional<Terminal> terminal = state.terminal();
        Optional<TerminalKind> newKind = terminalKind(result);
        if (terminal.isEmpty() && newKind.isPresent()) terminal = Optional.of(new Terminal(proof, newKind.orElseThrow(), Optional.empty(), UNCONSUMED));
        else if (terminal.isPresent() && result.cause().isPresent() && !terminal.orElseThrow().terminalCauseObserved()) {
            Terminal old = terminal.orElseThrow(); terminal = Optional.of(new Terminal(old.proof(), old.kind(), Optional.of(proof), old.consumption()));
        }
        MaterialUpdate named = updateMaterial(state, proof, terminal.isPresent());
        Optional<Phase> phase = state.phase();
        if (inputs.execution().isPresent()) {
            JsonNode read = parse(validateExecution(inputs.execution().orElseThrow(), state.identity()));
            if (bool(read, "available") && !read.get("records").isEmpty()) {
                JsonNode row = read.get("records").get(read.get("records").size() - 1); BigInteger sequence = u64(row, "sequence", 1);
                int eventDate = signed(row, "date_raw"); String branch = text(row, "source_branch");
                Consumption consumed = phase.filter(old -> old.sequence().equals(sequence) && old.executionDateRaw() == eventDate && old.branch().equals(branch))
                        .map(Phase::consumption).orElse(UNCONSUMED);
                phase = Optional.of(new Phase(proof, sequence, eventDate, branch, consumed));
            }
        }
        return new State(state.identity(), state.origin(), latest, terminal, named.material(), named.firstGain(), phase);
    }

    /** Existing target-census plus opinion entrance. No synthetic exact-instance read is manufactured. */
    public static State observeCensusMaterial(State state, Episode episode, ProjectionJson census,
            ProjectionJson opinion, ObservationIdentity queried) {
        require(state.identity().equals(episode.identity()), "Sway census belongs to another original episode"); sameScope(state.origin(), queried);
        Proof proof = new Proof(queried, compactOriginal(episode), new Inputs(Optional.empty(), Optional.empty(), Optional.empty(), Optional.of(opinion)), Optional.of(census));
        validateProof(state.identity(), state.origin(), proof); MaterialUpdate named = updateMaterial(state, proof, state.terminal().isPresent());
        return new State(state.identity(), state.origin(), state.latest(), state.terminal(), named.material(), named.firstGain(), state.phase());
    }
    private record MaterialFact(NamedValue sway, NamedValue blocker, Optional<Integer> total, boolean active, boolean currentTerminal) { }
    private record MaterialUpdate(Optional<Material> material, Optional<Gain> firstGain) { }
    private static MaterialUpdate updateMaterial(State state, Proof proof, boolean terminal) {
        Optional<MaterialFact> fact = materialFact(proof); if (fact.isEmpty()) return new MaterialUpdate(state.material(), state.firstGain());
        MaterialFact named = fact.orElseThrow(); Material old = state.material().orElse(null);
        boolean gain = old != null && old.trackedActive() && (named.active() || named.currentTerminal()) && date(proof.source()) > date(old.source())
                && old.sway().points().isPresent() && named.sway().points().filter(points -> points.compareTo(old.sway().points().orElseThrow()) > 0).isPresent();
        boolean same = old != null && old.trackedActive() == named.active() && old.terminalObserved() == terminal
                && old.sway().equals(named.sway()) && old.blocker().equals(named.blocker()) && old.totalOpinion().equals(named.total());
        Material next = new Material(proof, named.sway(), named.blocker(), named.total(), named.active(), terminal,
                old == null ? Optional.empty() : Optional.of(old.sway()), gain ? Optional.of(old.proof()) : Optional.empty(), gain, same ? old.consumption() : UNCONSUMED);
        Optional<Gain> first = state.firstGain(); if (gain && first.isEmpty()) first = Optional.of(new Gain(old.source(), old.sway(), old.proof(), next));
        return new MaterialUpdate(Optional.of(next), first);
    }
    private static Optional<MaterialFact> materialFact(Proof proof) {
        if (proof.census().isEmpty()) {
            Result result = compose(proof); return result.material().map(value -> new MaterialFact(value.sway(), value.blocker(), optionalOpinion(proof.inputs().opinion().orElseThrow()),
                    result.nativeState() == NativeState.CONTINUE, result.nativeState() == NativeState.TERMINATED_UNATTRIBUTED));
        }
        JsonNode opinion = parse(proof.inputs().opinion().orElseThrow()); if (!bool(opinion, "available")) return Optional.empty();
        JsonNode census = parse(proof.census().orElseThrow()); Identity identity = episode(proof).identity(); boolean active = false;
        for (JsonNode row : census.get("active_sway_instances")) {
            long fullId = integer(row, "scheme_instance_id", 0, 0xffff_fffeL);
            require(integer(row, "scheme_instance_generation", 0, 255) == fullId >>> 24, "census full instance generation differs");
            long target = integer(row, "target_character_id", 1, 0xffff_fffeL);
            active |= fullId == identity.schemeInstanceId() && target == identity.targetCharacterId();
        }
        return Optional.of(new MaterialFact(named(opinion.get("scheme_sway_opinion")), named(opinion.get("sway_blocker_opinion")), optionalOpinion(proof.inputs().opinion().orElseThrow()), active, false));
    }
    /** A later selected ordinary turn consumes each plane independently; no action is submitted here. */
    public static State consumeFollowing(State state, ObservationIdentity after) {
        sameScope(state.origin(), after);
        return new State(state.identity(), state.origin(), state.latest().map(value -> new Instance(value.proof(), value.state(), consume(value.consumption(), value.source(), after))),
                state.terminal().map(value -> new Terminal(value.proof(), value.kind(), value.causeProof(), consume(value.consumption(), value.source(), after))),
                state.material().map(value -> consumed(value, after)), state.firstGain().map(value -> new Gain(value.baseline(), value.before(), value.baselineProof(), consumed(value.observed(), after))),
                state.phase().map(value -> new Phase(value.proof(), value.sequence(), value.executionDateRaw(), value.branch(), consume(value.consumption(), value.source(), after))));
    }
    /** Caller additionally verifies current target-read matching_sway_active before proposing typed Stop. */
    public static boolean mayFinish(State state, ObservationIdentity current, int targetOpinion) {
        sameScope(state.origin(), current);
        return targetOpinion > 50 && state.latest().filter(value -> value.source().equals(current) && value.active()).isPresent()
                && state.material().filter(value -> value.source().equals(current) && value.dedicatedBenefitObserved()
                    && value.totalOpinion().filter(opinion -> opinion == targetOpinion).isPresent()).isPresent();
    }
    /** Fresh exact-instance status after Stop. A retained old end or vanished slot cannot resolve it. */
    public static boolean observedTerminal(State state, ObservationIdentity current) {
        sameScope(state.origin(), current); return state.latest().filter(value -> value.source().equals(current) && value.observedTerminal()).isPresent();
    }
    public static boolean hasPendingFollowing(State state) {
        return state.latest().filter(value -> !value.consumption().nextTurnConsumed()).isPresent()
                || state.terminal().filter(value -> !value.consumption().nextTurnConsumed()).isPresent()
                || state.material().filter(value -> !value.consumption().nextTurnConsumed()).isPresent()
                || state.firstGain().filter(value -> !value.observed().consumption().nextTurnConsumed()).isPresent()
                || state.phase().filter(value -> !value.consumption().nextTurnConsumed()).isPresent();
    }

    private static Material consumed(Material value, ObservationIdentity after) { return new Material(value.proof(), value.sway(), value.blocker(), value.totalOpinion(),
            value.trackedActive(), value.terminalObserved(), value.previousSway(), value.previousProof(), value.incrementalNamedGain(), consume(value.consumption(), value.source(), after)); }
    private static Consumption consume(Consumption old, ObservationIdentity source, ObservationIdentity after) {
        return old.nextTurnConsumed() || !stamp(after).laterThan(stamp(source)) ? old : new Consumption(true, Optional.of(stamp(after)));
    }
    private static void sameScope(ObservationIdentity before, ObservationIdentity after) {
        require(before.machineId().equals(after.machineId()) && before.game().equals(after.game())
                && before.frame().episodeRunId().equals(after.frame().episodeRunId()) && before.frame().identity().player().equals(after.frame().identity().player())
                && before.observationVersion() == after.observationVersion(), "Sway lifecycle crossed machine, original Game birth, episode, player or observation contract");
    }
    private static Stamp stamp(ObservationIdentity source) { return new Stamp(source.frame().identity().nativeRevision(), source.frame().identity().dateRaw().intValueExact()); }
    private static int date(ObservationIdentity source) { return source.frame().identity().dateRaw().intValueExact(); }
    private static Episode episode(Proof proof) {
        JsonNode read = parse(proof.originalResolved()); JsonNode receipt = read.get("native_receipt");
        JsonNode identity = receipt == null || receipt.isNull() ? read.get("recovered_instance_observation") : receipt;
        Identity tuple = new Identity(text(read, "action_id"), integer(read, "actor_character_id", 1, 0xffff_fffeL), integer(read, "target_character_id", 1, 0xffff_fffeL),
                integer(identity, "scheme_instance_id", 0, 0xffff_fffeL), Math.toIntExact(integer(identity, "scheme_instance_generation", 0, 255)));
        return new Episode(tuple, Optional.empty(), Optional.empty(), Optional.empty(), proof.originalResolved());
    }
    private static Result compose(Proof proof) { return M6TerminalSourceComposition.compose(episode(proof), proof.inputs()); }
    private static ProjectionJson compactOriginal(Episode episode) {
        JsonNode old = parse(episode.originalResolved()); ObjectNode result = StrictJson.object();
        for (String field : List.of("status", "postcondition_verified", "action_id", "actor_character_id", "target_character_id", "native_receipt", "recovered_instance_observation", "applied_instance_observation"))
            if (old.has(field)) result.set(field, old.get(field));
        return json(result);
    }
    private static void validateProof(Identity expected, ObservationIdentity origin, Proof proof) {
        sameScope(origin, proof.source()); require(episode(proof).identity().equals(expected), "copied lifecycle proof has a different original identity");
        M6TerminalSourceComposition.validateInputs(proof.inputs(), expected, proof.source()); compose(proof);
        proof.census().ifPresent(raw -> {
            require(proof.inputs().completion().isEmpty() && proof.inputs().opinion().isPresent(), "census material is an independent explicit plane");
            JsonNode census = parse(raw); actual4(census); textEquals(census, "schema", "active-scheme-sway-private-read-v1");
            M6InputValidation.exactIdentity(census, expected, false); M6InputValidation.queryStamp(census, proof.source());
            array(census.get("active_sway_instances")); materialFact(proof);
        });
    }
    private static void validateMaterial(Identity identity, ObservationIdentity origin, Material value) {
        validateProof(identity, origin, value.proof()); MaterialFact material = materialFact(value.proof()).orElseThrow();
        require(value.sway().equals(material.sway()) && value.blocker().equals(material.blocker()) && value.totalOpinion().equals(material.total())
                && value.trackedActive() == material.active(), "persisted material differs from its independent named source");
        if (value.incrementalNamedGain()) {
            Proof previous = value.previousProof().orElseThrow(); validateProof(identity, origin, previous);
            require(materialFact(previous).filter(points -> points.active() && value.previousSway().filter(points.sway()::equals).isPresent()).isPresent()
                    && date(value.source()) > date(previous.source())
                    && value.previousSway().orElseThrow().points().isPresent()
                    && value.sway().points().filter(points -> points.compareTo(value.previousSway().orElseThrow().points().orElseThrow()) > 0).isPresent(), "gain baseline or points were invented");
        } else require(value.previousProof().isEmpty(), "non-gain material cannot borrow a baseline proof");
    }
    private static Optional<TerminalKind> terminalKind(Result result) {
        if (result.cause().isPresent()) return Optional.of(TerminalKind.CAUSAL_END);
        if (result.commonEnd().isPresent()) return Optional.of(TerminalKind.COMMON_RETURN);
        if (result.wrapperEnd().isPresent()) return Optional.of(TerminalKind.WRAPPER_RETURN);
        return result.nativeState() == NativeState.TERMINATED_UNATTRIBUTED ? Optional.of(TerminalKind.CURRENT_STATUS) : Optional.empty();
    }
    private static boolean hasTerminal(Result result, TerminalKind kind) { return switch (kind) {
        case CURRENT_STATUS -> result.nativeState() == NativeState.TERMINATED_UNATTRIBUTED;
        case WRAPPER_RETURN -> result.wrapperEnd().isPresent(); case COMMON_RETURN -> result.commonEnd().isPresent(); case CAUSAL_END -> result.cause().isPresent(); }; }
    private static boolean sameInstanceFacts(ProjectionJson before, ProjectionJson after) {
        JsonNode left = parse(before), right = parse(after);
        return List.of("instance_source_observed", "instance_present", "storage_slot_reused", "exact_instance_join_ready", "native_owner_raw", "native_status_raw", "native_terminal_state_observed")
                .stream().allMatch(field -> Objects.equals(left.get(field), right.get(field)));
    }
    private static Optional<Integer> optionalOpinion(ProjectionJson raw) {
        JsonNode read = parse(raw), value = read.get("target_opinion_of_actor"); return value == null || value.isNull() ? Optional.empty() : Optional.of(signed(read, "target_opinion_of_actor"));
    }
    private static JsonNode phaseRow(Proof proof, BigInteger sequence) {
        JsonNode journal = parse(validateExecution(proof.inputs().execution().orElseThrow(), episode(proof).identity()));
        for (JsonNode row : journal.get("records")) if (u64(row, "sequence", 1).equals(sequence)) return row;
        throw new IllegalArgumentException("persisted phase sequence is absent from its copied journal");
    }

    /** New persistence uses decimal strings and base64 for copied JSON; unsafe source numbers never pass through JS Number. */
    public static byte[] encode(State state) { return SwayLifecycleCodec.encode(state); }
    public static State decode(byte[] raw) { return SwayLifecycleCodec.decode(raw); }

    /** Internal legacy evidence projection. It is derived bookkeeping, never a native packet or JS wire. */
    public static ProjectionJson interventions(State state) {
        ObjectNode result = StrictJson.object();
        state.latest().ifPresent(value -> { ObjectNode row = legacy(state.identity(), value.source(), value.consumption());
            row.put("tracked_instance_active", value.active()); row.put("instance_terminal_outcome_observed", value.observedTerminal());
            row.put("native_status_key", value.active() ? "continue" : value.observedTerminal() ? "terminated_unattributed" : "unobserved"); row.put("terminal_cause_observed", false); row.put("terminal_cause", "unknown");
            row.set("native_observation", parse(value.proof().inputs().completion().orElseThrow())); result.set("latest_instance_observation", row); });
        state.terminal().ifPresent(value -> { ObjectNode row = legacy(state.identity(), value.source(), value.consumption());
            row.put("tracked_instance_active", false); row.put("instance_terminal_outcome_observed", true); row.put("native_status_key", "terminated_unattributed");
            row.put("terminal_cause_observed", value.terminalCauseObserved()); row.put("terminal_cause", value.cause());
            value.eventDateRaw().ifPresentOrElse(date -> row.put("event_date_raw", date), () -> row.putNull("event_date_raw"));
            value.proof().inputs().completion().ifPresent(raw -> row.set("native_observation", parse(raw)));
            if (value.terminalCauseObserved()) row.set("causal_observation", parse(compose(value.causeProof().orElse(value.proof())).cause().orElseThrow().observation()));
            result.set("terminal_intervention", row); });
        state.material().ifPresent(value -> result.set("material_intervention", materialLegacy(state.identity(), value)));
        state.firstGain().ifPresent(value -> { ObjectNode row = materialLegacy(state.identity(), value.observed()); row.put("baseline_source_native_revision", stamp(value.baseline()).nativeRevision());
            row.put("baseline_source_date_raw", date(value.baseline())); result.set("first_named_gain_intervention", row); });
        state.phase().ifPresent(value -> { ObjectNode row = legacy(state.identity(), value.source(), value.consumption());
            row.put("source_sequence", value.sequence()); row.put("execution_date_raw", value.executionDateRaw()); row.put("source_branch", value.branch());
            JsonNode source = phaseRow(value.proof(), value.sequence()); row.set("stock_event", source.get("stock_event")); row.set("phase_result", source.get("phase_result"));
            row.put("executing_input_observed", true); row.put("material_effect_observed", false); row.put("native_terminal_state_observed", false);
            row.set("native_observation", parse(value.proof().inputs().execution().orElseThrow())); result.set("phase_intervention", row); });
        return json(result);
    }
    private static ObjectNode materialLegacy(Identity identity, Material value) {
        ObjectNode row = legacy(identity, value.source(), value.consumption()); row.set("scheme_sway_opinion", namedJson(value.sway())); row.set("sway_blocker_opinion", namedJson(value.blocker()));
        value.totalOpinion().ifPresentOrElse(opinion -> row.put("target_opinion_of_actor", opinion), () -> row.putNull("target_opinion_of_actor"));
        row.put("tracked_instance_active", value.trackedActive()); row.put("instance_terminal_outcome_observed", value.terminalObserved());
        row.put("dedicated_benefit_observed", value.dedicatedBenefitObserved()); row.put("dedicated_setback_observed", value.dedicatedSetbackObserved()); row.put("incremental_named_gain_observed", value.incrementalNamedGain());
        value.previousSway().ifPresentOrElse(before -> row.set("previous_scheme_sway_opinion", namedJson(before)), () -> row.putNull("previous_scheme_sway_opinion"));
        row.put("decision", value.trackedActive() ? "retain_existing_sway" : value.terminalObserved() ? "consume_retained_termination" : "observe_tracked_instance_end"); return row;
    }
    private static ObjectNode legacy(Identity identity, ObservationIdentity source, Consumption consumption) {
        ObjectNode row = identityJson(identity); row.put("exact_ck3_build", BUILD); row.put("exe_sha256", EXE);
        row.put("source_native_revision", stamp(source).nativeRevision()); row.put("source_date_raw", date(source)); row.put("next_turn_consumed", consumption.nextTurnConsumed());
        consumption.following().ifPresent(value -> { row.put("following_native_revision", value.nativeRevision()); row.put("following_date_raw", value.dateRaw()); }); return row;
    }
    static ObjectNode namedJson(NamedValue value) { ObjectNode row = StrictJson.object(); row.put("observed", value.observed()); row.put("present", value.present());
        value.value().ifPresentOrElse(points -> row.put("value", points), () -> row.putNull("value")); return row; }
}
