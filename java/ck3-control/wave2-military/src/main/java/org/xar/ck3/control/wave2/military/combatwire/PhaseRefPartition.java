package org.xar.ck3.control.wave2.military.combatwire;

import static org.xar.ck3.control.wave2.military.combatwire.CombatWire.*;
import static org.xar.ck3.control.wave2.military.combatwire.CombatPhaseSchema.*;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.Set;
import java.util.TreeSet;

/** Reproves the manifest's 81-native plus 51-offline exact path partition. */
final class PhaseRefPartition {
    private static final JsonNodeFactory J = JsonNodeFactory.instance;
    private final Set<String> nativeRefs;
    private final Set<String> offlineRefs;
    PhaseRefPartition(PhaseEventRuntime runtime) {
        require(runtime.manifestSha256().equals(MANIFEST), "stock phase manifest source SHA mismatch");
        Set<String> all = Set.copyOf(runtime.requiredStateRefs());
        Set<String> offline = new HashSet<>(keys(DERIVED)); offline.addAll(keys(OFFLINE_CONTAINERS));
        for (String key : keys(ATTRIBUTES)) offline.add("root.accolade_unlocks." + key + ".valid");
        Set<String> nativeSet = new HashSet<>(all); nativeSet.removeAll(offline);
        require(all.size() == 132 && nativeSet.size() == 81 && offline.size() == 51 && all.containsAll(offline), "phase 132-ref partition malformed");
        require(digest(all).equals(REQUIRED_SHA) && digest(nativeSet).equals(NATIVE_SHA) && digest(offline).equals(OFFLINE_SHA), "phase exact path partition digest drifted");
        nativeRefs = Set.copyOf(nativeSet); offlineRefs = Set.copyOf(offline);
    }
    Set<String> nativeRefs() { return nativeRefs; }
    Set<String> offlineRefs() { return offlineRefs; }
    ObjectNode toJson() {
        ObjectNode out = coverage(); out.set("native_leaf_paths", paths(nativeRefs)); out.set("offline_exact_paths", paths(offlineRefs)); return out;
    }
    static ObjectNode coverage() {
        ObjectNode out = J.objectNode();
        out.putObject("manifest_domain_counts").put("character_relation", 79).put("army", 13).put("side", 10).put("global", 3).put("derived", 27);
        out.putObject("abi_level_counts").put("native_leaf_exact", 81).put("offline_exact", 51).put("determinable", 132).put("missing", 0);
        out.putObject("path_set_sha256").put("native_leaf_exact", NATIVE_SHA).put("offline_exact", OFFLINE_SHA).put("required", REQUIRED_SHA);
        return out.put("native_payload_policy", POLICY);
    }
    static ArrayNode paths(Set<String> refs) { ArrayNode out = J.arrayNode(); new TreeSet<>(refs).forEach(out::add); return out; }
    static String digest(Set<String> refs) {
        try { return HexFormat.of().withUpperCase().formatHex(MessageDigest.getInstance("SHA-256").digest(paths(refs).toString().getBytes(StandardCharsets.UTF_8))); }
        catch (NoSuchAlgorithmException exception) { throw new IllegalStateException("SHA-256 unavailable", exception); }
    }
}
