package org.xar.ck3.control.application.planning.governance;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilCodec;
import org.xar.ck3.control.governance.council.CouncilModels;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Shared Council19 decoder -> original final-gate filtering and deterministic skill selection. */
public final class CouncilSelection {
    private CouncilSelection() { }
    public enum Position {
        STEWARD(CouncilModels.Position.STEWARD), CHANCELLOR(CouncilModels.Position.CHANCELLOR),
        CHAPLAIN(CouncilModels.Position.CHAPLAIN);
        private final CouncilModels.Position shared;
        Position(CouncilModels.Position shared) { this.shared = shared; }
        public String key() { return shared.key(); }
        public String skill() { return shared.skill(); }
    }
    public record Candidate(BigInteger characterId, BigInteger ordinal, int skill, List<String> blockers, Obj original) {
        public Candidate {
            Objects.requireNonNull(characterId); Objects.requireNonNull(ordinal); blockers = List.copyOf(blockers);
            Objects.requireNonNull(original);
        }
        public boolean nativeLegal() { return blockers.isEmpty(); }
    }
    public record Query(Position position, boolean available, Optional<BigInteger> incumbent, Optional<Integer> incumbentSkill,
            List<Candidate> candidates, Obj original) {
        public Query {
            Objects.requireNonNull(position); Objects.requireNonNull(incumbent); Objects.requireNonNull(incumbentSkill);
            candidates = List.copyOf(candidates); Objects.requireNonNull(original);
            StrictJson.require(incumbent.isPresent() == incumbentSkill.isPresent(), "incumbent identity/skill readiness differs");
        }
    }
    public enum Outcome { QUERY_UNAVAILABLE, NO_CHANGE, ASSIGN_REQUIRED, REPLACE_REQUIRED }
    public record Decision(Outcome outcome, Optional<Candidate> selected, Query original, String reason) {
        public Decision { Objects.requireNonNull(outcome); Objects.requireNonNull(selected); Objects.requireNonNull(original); StrictJson.text(reason); }
    }
    public static Query decode(PlanningRequest request, Position role, Obj original) {
        return decodeObserved(request.before(),role,original);
    }
    /** Pure rederivation from the original command frame, without manufacturing a PlanningRequest. */
    public static Query decodeObserved(ObservationIdentity observed,Position role,Obj original) {
        bindPrivateOuter(observed, original);
        if (!new Text("available").equals(original.get("status")))
            return new Query(role, false, Optional.empty(), Optional.empty(), List.of(), original);
        return decodePayload(observed, role, original, object(original.get("council_composition_candidates"), "council candidates"), true);
    }
    public static Query decodeComposition(PlanningRequest request, Obj originalPayload) {
        return decodeCompositionObserved(request.before(),originalPayload);
    }
    public static Query decodeCompositionObserved(ObservationIdentity observed,Obj originalPayload) {
        return decodePayload(observed, Position.STEWARD, originalPayload, originalPayload, false);
    }
    /** Consume the unique registered public Council typed contract directly. */
    public static Query fromComposition(PlanningRequest request, CouncilModels.Candidates decoded) {
        var expected = request.before().frame();
        require(decoded.frame().equals(new CouncilModels.Frame(expected.snapshotId(), expected.revision(), expected.identity().nativeRevision(),
                expected.identity().dateRaw().intValueExact(), expected.identity().player().intValueExact()))
                && decoded.seat().position() == CouncilModels.Position.STEWARD, "typed public Council frame/role drift");
        Obj original = object(parse(decoded.original().bytes()), "original typed Council payload");
        List<Value> rows = array(original.get("candidates"), "typed candidate originals");
        require(rows.size() == decoded.candidates().size(), "typed candidate originals incomplete");
        List<Candidate> candidates = new ArrayList<>();
        for (int index = 0; index < decoded.candidates().size(); index++) {
            var value = decoded.candidates().get(index);
            candidates.add(new Candidate(BigInteger.valueOf(value.characterId()), BigInteger.valueOf(value.nativeCollectionOrdinal()), value.mainSkill(), List.of(), object(rows.get(index), "original typed candidate")));
        }
        return new Query(Position.STEWARD, true, decoded.seat().incumbentId().isPresent()
                ? Optional.of(BigInteger.valueOf(decoded.seat().incumbentId().orElseThrow())) : Optional.empty(),
                decoded.seat().incumbentSkill().isPresent() ? Optional.of(decoded.seat().incumbentSkill().orElseThrow()) : Optional.empty(), candidates, original);
    }
    private static void bindPrivateOuter(ObservationIdentity observed, Obj original) {
        var expected = observed.frame();
        require(new Text(expected.snapshotId()).equals(original.get("queried_snapshot_id"))
                && integer(original.get("queried_revision"), "queried public revision").equals(expected.revision())
                && integer(original.get("queried_native_revision"), "queried native revision").equals(expected.identity().nativeRevision()),
                "private Council outer query binding drift");
        Obj publicFrame = object(original.get("source_frame"), "private Council public source frame");
        require(publicFrame.members().keySet().equals(java.util.Set.of("snapshot_id", "revision", "native_revision", "date_raw", "player_character_id", "paused"))
                && new Text(expected.snapshotId()).equals(publicFrame.get("snapshot_id"))
                && integer(publicFrame.get("revision"), "public revision").equals(expected.revision())
                && integer(publicFrame.get("native_revision"), "native revision").equals(expected.identity().nativeRevision())
                && integer(publicFrame.get("date_raw"), "date").equals(expected.identity().dateRaw())
                && integer(publicFrame.get("player_character_id"), "player").equals(expected.identity().player())
                && bool(publicFrame.get("paused"), "paused"), "private Council complete public source frame drift");
    }
    private static Query decodePayload(ObservationIdentity observed, Position role, Obj original, Obj payload, boolean privateGates) {
        var expected = observed.frame();
        if (privateGates) bindPrivateOuter(observed, original);
        var frame = new CouncilModels.Frame(privateGates ? "native:" + expected.identity().nativeRevision() : expected.snapshotId(),
                privateGates ? expected.identity().nativeRevision() : expected.revision(), expected.identity().nativeRevision(),
                expected.identity().dateRaw().intValueExact(), expected.identity().player().intValueExact());
        // One shared runtime contract handles token kinds, exact fields, full IDs, readiness and optional tax.
        CouncilModels.Candidates decoded = CouncilCodec.decode(encode(payload), frame, role.shared);
        List<Value> raw = array(payload.get("candidates"), "candidates");
        List<Value> gates = List.of();
        if (privateGates) {
            Obj gateEnvelope = object(original.get("council_final_gates"), "council final gates");
            require(new Text("available").equals(gateEnvelope.get("status")), "final gates unavailable");
            gates = array(gateEnvelope.get("rows"), "final gates rows");
            require(integer(gateEnvelope.get("candidate_count"), "candidate_count").equals(BigInteger.valueOf(gates.size()))
                    && raw.size() == gates.size(), "incomplete final gate collection");
        }
        List<Candidate> candidates = new ArrayList<>();
        for (int index = 0; index < decoded.candidates().size(); index++) {
            CouncilModels.Candidate candidate = decoded.candidates().get(index);
            List<String> blockers = new ArrayList<>();
            if (privateGates) {
                Obj gate = object(gates.get(index), "final gate");
                require(integer(gate.get("character_id"), "gate candidate").equals(BigInteger.valueOf(candidate.characterId()))
                        && integer(gate.get("native_collection_ordinal"), "gate ordinal").equals(BigInteger.valueOf(candidate.nativeCollectionOrdinal())),
                        "final gate row identity mismatch");
                if (!bool(gate.get("final_gate_available"), "final_gate_available")) blockers.add("final_legality_unavailable");
                for (String key : List.of("candidate_already_councillor", "candidate_is_guest", "pending_character_interaction"))
                    if (bool(gate.get(key), key)) blockers.add(key);
                boolean evaluated = bool(gate.get("incumbent_fireability_evaluated"), "incumbent_fireability_evaluated");
                boolean fireable = bool(gate.get("incumbent_can_be_fired"), "incumbent_can_be_fired");
                if (decoded.seat().incumbentId().isPresent() && !(evaluated && fireable)) blockers.add("incumbent_cannot_be_replaced");
            }
            candidates.add(new Candidate(BigInteger.valueOf(candidate.characterId()), BigInteger.valueOf(candidate.nativeCollectionOrdinal()),
                    candidate.mainSkill(), blockers, object(raw.get(index), "original candidate")));
        }
        return new Query(role, true, decoded.seat().incumbentId().isPresent()
                ? Optional.of(BigInteger.valueOf(decoded.seat().incumbentId().orElseThrow())) : Optional.empty(),
                decoded.seat().incumbentSkill().isPresent() ? Optional.of(decoded.seat().incumbentSkill().orElseThrow()) : Optional.empty(),
                candidates, original);
    }
    public static Decision choose(Query query) {
        if (!query.available()) return new Decision(Outcome.QUERY_UNAVAILABLE, Optional.empty(), query, "private_query_unavailable");
        Optional<Candidate> selected = query.candidates().stream().filter(Candidate::nativeLegal)
                .sorted(Comparator.comparingInt(Candidate::skill).reversed().thenComparing(Candidate::characterId)).findFirst();
        if (selected.isEmpty()) return new Decision(Outcome.NO_CHANGE, selected, query, "no_eligible_candidates");
        if (query.incumbentSkill().filter(value -> selected.orElseThrow().skill() <= value).isPresent())
            return new Decision(Outcome.NO_CHANGE, selected, query, "incumbent_not_outperformed");
        return new Decision(query.incumbent().isPresent() ? Outcome.REPLACE_REQUIRED : Outcome.ASSIGN_REQUIRED,
                selected, query, "native_final_gate_and_observed_skill");
    }
}

