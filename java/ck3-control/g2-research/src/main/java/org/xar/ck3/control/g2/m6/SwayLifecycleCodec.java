package org.xar.ck3.control.g2.m6;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.g2.m6.M6TerminalSourceComposition.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Consumption;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Identity;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Stamp;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.g2.m6.SwayLifecycle.*;

/** One strict schema, bounded and with interned source packets. Decode revalidates the actual proofs. */
final class SwayLifecycleCodec {
    private SwayLifecycleCodec() { }
    static byte[] encode(State state) {
        List<Proof> proofs = new ArrayList<>();
        Function<Proof, JsonNode> reference = value -> {
            int index = proofs.indexOf(value); if (index < 0) { require(proofs.size() < 16, "finite Sway proof table required"); index = proofs.size(); proofs.add(value); }
            return StrictJson.object().numberNode(index);
        };
        ObjectNode root = StrictJson.object(); root.put("schema", SwayLifecycle.SCHEMA); root.set("identity", identityJson(state.identity()));
        root.set("origin", ProposalLifecycleCodec.observation(state.origin()));
        put(root, "latest", state.latest(), value -> instance(value, reference));
        put(root, "terminal", state.terminal(), value -> terminal(value, reference));
        put(root, "material", state.material(), value -> material(value, reference));
        put(root, "first_gain", state.firstGain(), value -> {
            ObjectNode row = StrictJson.object(); row.set("baseline", ProposalLifecycleCodec.observation(value.baseline()));
            row.set("before", SwayLifecycle.namedJson(value.before())); row.set("baseline_proof_ref", reference.apply(value.baselineProof()));
            row.set("observed", material(value.observed(), reference)); return row;
        });
        put(root, "phase", state.phase(), value -> phase(value, reference));
        var table = root.putArray("proofs"); proofs.forEach(value -> table.add(proof(value)));
        // Copied source base64 is a bounded role value and may exceed business-text's 32KiB limit.
        return ProjectionJson.object(root.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8), SwayLifecycle.MAX_BYTES).bytes();
    }
    static State decode(byte[] raw) {
        JsonNode root = StrictJson.parse(raw, SwayLifecycle.MAX_BYTES);
        StrictJson.object(root, Set.of("schema", "identity", "origin", "proofs", "latest", "terminal", "material", "first_gain", "phase"));
        textEquals(root, "schema", SwayLifecycle.SCHEMA);
        JsonNode identity = root.get("identity"); StrictJson.object(identity, Set.of("action_id", "actor_character_id", "target_character_id", "scheme_instance_id", "scheme_instance_generation"));
        Identity tuple = new Identity(text(identity, "action_id"), integer(identity, "actor_character_id", 1, 0xffff_fffeL), integer(identity, "target_character_id", 1, 0xffff_fffeL),
                integer(identity, "scheme_instance_id", 0, 0xffff_fffeL), Math.toIntExact(integer(identity, "scheme_instance_generation", 0, 255)));
        JsonNode table = root.get("proofs"); require(table.isArray() && table.size() <= 16, "finite Sway proof table required");
        List<Proof> proofs = new ArrayList<>(); for (JsonNode row : table) { Proof value = proof(row); require(!proofs.contains(value), "duplicate copied Sway proof refused"); proofs.add(value); }
        Set<Integer> used = new java.util.HashSet<>();
        Function<JsonNode, Proof> reference = node -> { int index = Math.toIntExact(StrictJson.integer(node, 0, proofs.size() - 1L)); used.add(index); return proofs.get(index); };
        State result = new State(tuple, ProposalLifecycleCodec.decodeObservation(root.get("origin")),
                get(root, "latest", value -> instance(value, reference)), get(root, "terminal", value -> terminal(value, reference)),
                get(root, "material", value -> material(value, reference)), get(root, "first_gain", value -> {
                    StrictJson.object(value, Set.of("baseline", "before", "baseline_proof_ref", "observed"));
                    return new Gain(ProposalLifecycleCodec.decodeObservation(value.get("baseline")), named(value.get("before")),
                            reference.apply(value.get("baseline_proof_ref")), material(value.get("observed"), reference));
                }), get(root, "phase", value -> phase(value, reference)));
        require(used.size() == proofs.size(), "unreferenced Sway proof is not authoritative state"); return result;
    }
    private static ObjectNode proof(Proof value) {
        ObjectNode row = StrictJson.object(); row.set("source", ProposalLifecycleCodec.observation(value.source())); copy(row, "original_resolved", value.originalResolved());
        nullableCopy(row, "completion", value.inputs().completion()); nullableCopy(row, "execution", value.inputs().execution());
        nullableCopy(row, "termination", value.inputs().termination()); nullableCopy(row, "opinion", value.inputs().opinion()); nullableCopy(row, "census", value.census()); return row;
    }
    private static Proof proof(JsonNode row) {
        StrictJson.object(row, Set.of("source", "original_resolved", "completion", "execution", "termination", "opinion", "census"));
        return new Proof(ProposalLifecycleCodec.decodeObservation(row.get("source")), copied(row.get("original_resolved")),
                new Inputs(get(row, "completion", SwayLifecycleCodec::copied), get(row, "execution", SwayLifecycleCodec::copied),
                    get(row, "termination", SwayLifecycleCodec::copied), get(row, "opinion", SwayLifecycleCodec::copied)), get(row, "census", SwayLifecycleCodec::copied));
    }
    private static ObjectNode instance(Instance value, Function<Proof, JsonNode> ref) {
        ObjectNode row = StrictJson.object(); row.set("proof_ref", ref.apply(value.proof())); row.put("state", value.state().name()); row.set("consumption", consumption(value.consumption())); return row;
    }
    private static Instance instance(JsonNode row, Function<JsonNode, Proof> ref) {
        StrictJson.object(row, Set.of("proof_ref", "state", "consumption")); return new Instance(ref.apply(row.get("proof_ref")), M6SourceProducer.NativeState.valueOf(text(row, "state")), consumption(row.get("consumption")));
    }
    private static ObjectNode terminal(Terminal value, Function<Proof, JsonNode> ref) {
        ObjectNode row = StrictJson.object(); row.set("proof_ref", ref.apply(value.proof())); row.put("kind", value.kind().name());
        value.causeProof().ifPresentOrElse(found -> row.set("cause_proof_ref", ref.apply(found)), () -> row.putNull("cause_proof_ref")); row.set("consumption", consumption(value.consumption())); return row;
    }
    private static Terminal terminal(JsonNode row, Function<JsonNode, Proof> ref) {
        StrictJson.object(row, Set.of("proof_ref", "kind", "cause_proof_ref", "consumption"));
        return new Terminal(ref.apply(row.get("proof_ref")), TerminalKind.valueOf(text(row, "kind")), get(row, "cause_proof_ref", ref), consumption(row.get("consumption")));
    }
    private static ObjectNode material(Material value, Function<Proof, JsonNode> ref) {
        ObjectNode row = StrictJson.object(); row.set("proof_ref", ref.apply(value.proof())); row.set("sway", SwayLifecycle.namedJson(value.sway())); row.set("blocker", SwayLifecycle.namedJson(value.blocker()));
        value.totalOpinion().ifPresentOrElse(opinion -> row.put("total_opinion", opinion), () -> row.putNull("total_opinion"));
        row.put("tracked_active", value.trackedActive()); row.put("terminal_observed", value.terminalObserved()); put(row, "previous_sway", value.previousSway(), SwayLifecycle::namedJson);
        value.previousProof().ifPresentOrElse(found -> row.set("previous_proof_ref", ref.apply(found)), () -> row.putNull("previous_proof_ref"));
        row.put("incremental_named_gain", value.incrementalNamedGain()); row.set("consumption", consumption(value.consumption())); return row;
    }
    private static Material material(JsonNode row, Function<JsonNode, Proof> ref) {
        StrictJson.object(row, Set.of("proof_ref", "sway", "blocker", "total_opinion", "tracked_active", "terminal_observed", "previous_sway", "previous_proof_ref", "incremental_named_gain", "consumption"));
        Optional<Integer> total = row.get("total_opinion").isNull() ? Optional.empty() : Optional.of(signed(row, "total_opinion"));
        return new Material(ref.apply(row.get("proof_ref")), named(row.get("sway")), named(row.get("blocker")), total, bool(row, "tracked_active"), bool(row, "terminal_observed"),
                get(row, "previous_sway", M6TerminalSourceComposition::named), get(row, "previous_proof_ref", ref), bool(row, "incremental_named_gain"), consumption(row.get("consumption")));
    }
    private static ObjectNode phase(Phase value, Function<Proof, JsonNode> ref) {
        ObjectNode row = StrictJson.object(); row.set("proof_ref", ref.apply(value.proof())); row.put("sequence", value.sequence().toString()); row.put("execution_date_raw", value.executionDateRaw()); row.put("branch", value.branch()); row.set("consumption", consumption(value.consumption())); return row;
    }
    private static Phase phase(JsonNode row, Function<JsonNode, Proof> ref) {
        StrictJson.object(row, Set.of("proof_ref", "sequence", "execution_date_raw", "branch", "consumption"));
        return new Phase(ref.apply(row.get("proof_ref")), decimal(row.get("sequence"), true), signed(row, "execution_date_raw"), text(row, "branch"), consumption(row.get("consumption")));
    }
    private static ObjectNode consumption(Consumption value) {
        ObjectNode row = StrictJson.object(); row.put("consumed", value.nextTurnConsumed());
        put(row, "following", value.following(), stamp -> { ObjectNode following = StrictJson.object(); following.put("native_revision", stamp.nativeRevision().toString()); following.put("date_raw", stamp.dateRaw()); return following; }); return row;
    }
    private static Consumption consumption(JsonNode row) {
        StrictJson.object(row, Set.of("consumed", "following")); boolean consumed = bool(row, "consumed");
        Optional<Stamp> following = get(row, "following", value -> { StrictJson.object(value, Set.of("native_revision", "date_raw"));
            return new Stamp(decimal(value.get("native_revision"), true), signed(value, "date_raw")); });
        require(!consumed || following.isPresent(), "consumed lifecycle needs the actual following stamp"); return new Consumption(consumed, following);
    }
    private static BigInteger decimal(JsonNode raw, boolean positive) {
        require(raw != null && raw.isTextual(), "canonical uint64 string required"); BigInteger value = new BigInteger(new CrossJsDecimalUInt64(raw.textValue()).decimal());
        require(!positive || value.signum() > 0, "positive uint64 string required"); return value;
    }
    private static void copy(ObjectNode row, String field, ProjectionJson value) { row.put(field, Base64.getEncoder().encodeToString(value.bytes())); }
    private static void nullableCopy(ObjectNode row, String field, Optional<ProjectionJson> value) { value.ifPresentOrElse(raw -> copy(row, field, raw), () -> row.putNull(field)); }
    private static ProjectionJson copied(JsonNode raw) {
        require(raw != null && raw.isTextual() && raw.textValue().length() <= ((M6SourceProducer.MAX_BYTES + 2L) / 3L) * 4L, "finite copied JSON base64 required");
        byte[] bytes = Base64.getDecoder().decode(raw.textValue()); require(Base64.getEncoder().encodeToString(bytes).equals(raw.textValue()), "canonical copied JSON base64 required");
        return ProjectionJson.object(bytes, M6SourceProducer.MAX_BYTES);
    }
    private static <T> void put(ObjectNode row, String field, Optional<T> value, Function<T, ObjectNode> encode) { value.ifPresentOrElse(found -> row.set(field, encode.apply(found)), () -> row.putNull(field)); }
    private static <T> Optional<T> get(JsonNode row, String field, Function<JsonNode, T> decode) {
        JsonNode value = row.get(field); require(value != null, "required nullable lifecycle field missing: " + field); return value.isNull() ? Optional.empty() : Optional.of(decode.apply(value));
    }
}
