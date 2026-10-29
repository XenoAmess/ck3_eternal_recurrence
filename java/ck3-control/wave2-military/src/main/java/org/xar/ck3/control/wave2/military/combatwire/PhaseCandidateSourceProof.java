package org.xar.ck3.control.wave2.military.combatwire;

import static org.xar.ck3.control.wave2.military.combatwire.CombatWire.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;

/** Exact C++ sequence-preimage order, shared by v3 admission and the stock AST evaluator. */
public record PhaseCandidateSourceProof(int sideIndex, List<Source> orderedSources, String sequenceSha256) {
    public static final String POLICY = "ccombat_side_commanders_then_knights_native_source_equivalence_v1";
    private static final JsonNodeFactory J = JsonNodeFactory.instance;
    public enum Role {
        COMMANDER("commander"), KNIGHT("knight");
        private final String wire;
        Role(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record Source(Role role, int sourceArmyId, Integer sourceRegimentId, int characterId) {
        public Source {
            require(role != null && sourceArmyId >= 0 && characterId > 0, "invalid candidate source identity");
            require(role == Role.COMMANDER ? sourceRegimentId == null
                    : sourceRegimentId != null && sourceRegimentId > 0, "invalid source RegimentID");
        }
        public ObjectNode toJson() {
            ObjectNode out = J.objectNode().put("role", role.wire()).put("source_army_id", sourceArmyId);
            if (sourceRegimentId == null) out.putNull("source_regiment_id");
            else out.put("source_regiment_id", sourceRegimentId);
            return out.put("character_id", characterId);
        }
    }
    public PhaseCandidateSourceProof {
        require(sideIndex == 0 || sideIndex == 1, "candidate source side index must be 0 or 1");
        orderedSources = List.copyOf(orderedSources);
        boolean reachedKnights = false;
        for (Source source : orderedSources) {
            require(!(reachedKnights && source.role() == Role.COMMANDER), "commander after native knight rows");
            reachedKnights |= source.role() == Role.KNIGHT;
        }
        require(digest(sideIndex, orderedSources).equals(sequenceSha256), "candidate source sequence SHA-256 mismatch");
    }
    public static PhaseCandidateSourceProof normalize(JsonNode value, int sideIndex) {
        ObjectNode in = object(value, "policy source_vector_equivalence sequence_sha256 ordered_sources", "candidate_source_proof");
        require(text(in.get("policy"), "policy").equals(POLICY), "candidate source policy drifted");
        require(bool(in.get("source_vector_equivalence"), "source_vector_equivalence"), "source vector equivalence not proven");
        ArrayNode rows = array(in.get("ordered_sources"), "ordered_sources");
        List<Source> sources = new ArrayList<>();
        for (JsonNode raw : rows) {
            ObjectNode row = object(raw, "role source_army_id source_regiment_id character_id", "source row");
            String roleToken = token(row.get("role"), "role", "commander", "knight");
            Role role = roleToken.equals("commander") ? Role.COMMANDER : Role.KNIGHT;
            Integer regiment = nil(row.get("source_regiment_id")) ? null : positive(row.get("source_regiment_id"), "source_regiment_id");
            sources.add(new Source(role, nonnegative(row.get("source_army_id"), "source_army_id"), regiment,
                    positive(row.get("character_id"), "character_id")));
        }
        return new PhaseCandidateSourceProof(sideIndex, sources, text(in.get("sequence_sha256"), "sequence_sha256"));
    }
    public ObjectNode toJson() {
        ObjectNode out = J.objectNode().put("policy", POLICY).put("source_vector_equivalence", true)
                .put("sequence_sha256", sequenceSha256);
        ArrayNode rows = out.putArray("ordered_sources");
        orderedSources.forEach(source -> rows.add(source.toJson()));
        return out;
    }
    public static byte[] preimage(int sideIndex, List<Source> sources) {
        require(sideIndex == 0 || sideIndex == 1, "invalid side index");
        ObjectNode out = J.objectNode().put("policy", POLICY).put("side_index", sideIndex);
        ArrayNode rows = out.putArray("ordered_sources");
        sources.forEach(source -> rows.add(source.toJson()));
        return out.toString().getBytes(StandardCharsets.UTF_8);
    }
    public static String digest(int sideIndex, List<Source> sources) {
        try { return HexFormat.of().withUpperCase().formatHex(MessageDigest.getInstance("SHA-256").digest(preimage(sideIndex, sources))); }
        catch (NoSuchAlgorithmException exception) { throw new IllegalStateException("SHA-256 unavailable", exception); }
    }
}
