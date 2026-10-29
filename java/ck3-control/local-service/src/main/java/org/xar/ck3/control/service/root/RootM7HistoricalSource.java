package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.HashSet;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Strict historical decoding of the sole Root source producer's retained bytes. No live source qualification. */
final class RootM7HistoricalSource {
    private static final Set<String> PROOF_FIELDS = Set.of("schema", "machine_id", "session_id", "observed_at_utc",
            "mode", "host_configuration", "source", "owner_source_epoch", "source_epoch_manifest",
            "game_executable", "complete_evidence_closure");
    private static final Set<String> ROLES = Set.of("java_runtime", "native_source", "bridge_dll", "injector",
            "game_executable", "launcher_settings");
    private static final Set<String> SINGLE_ROLES = Set.of("bridge_dll", "injector", "game_executable", "launcher_settings");
    private static final int LIMIT = 16 << 20;

    private RootM7HistoricalSource() { }

    /** Data from original immutable proof bytes only. Construction is package-private and grants no authority. */
    record Decoded(String epoch, ExactRef executable, ExactRef manifest) { }

    static ExactRef manifest(ExactRef proof, byte[] proofBytes, GuardEvidence actualGuard) {
        return ExactRef.fromJson(proof(proof, proofBytes, actualGuard).get("source_epoch_manifest"));
    }

    static Decoded decode(ExactRef proof, byte[] proofBytes, GuardEvidence actualGuard, byte[] manifestBytes) {
        ObjectNode source = proof(proof, proofBytes, actualGuard);
        ExactRef manifest = ExactRef.fromJson(source.get("source_epoch_manifest"));
        exact(manifest, manifestBytes);
        String epoch = StrictJson.text(source.get("owner_source_epoch"));
        StrictJson.require(epoch.matches("[0-9a-f]{64}") && epoch.equals(manifest.sha256()),
                "historical software epoch must be the exact original manifest digest");
        ExactRef executable = positive(source.get("game_executable"));
        ObjectNode definition = StrictJson.object(parse(manifestBytes), Set.of("schema", "machine_id", "inputs"));
        StrictJson.require("xar.java-root-source-epoch/v1".equals(StrictJson.text(definition.get("schema")))
                && actualGuard.source().machineId().equals(StrictJson.text(definition.get("machine_id"))),
                "historical source epoch manifest schema or machine differs");
        ArrayNode inputs = array(definition.get("inputs"));
        StrictJson.require(!inputs.isEmpty() && inputs.size() <= 30_000, "bounded complete historical epoch inputs required");
        Set<String> present = new HashSet<>();
        Set<String> singular = new HashSet<>();
        String prior = null;
        ExactRef manifestExecutable = null;
        for (JsonNode value : inputs) {
            ObjectNode row = StrictJson.object(value, Set.of("role", "source"));
            String role = StrictJson.text(row.get("role"));
            StrictJson.require(ROLES.contains(role), "unknown historical epoch input role");
            ExactRef ref = ExactRef.fromJson(row.get("source"));
            String normalized = ref.path();
            StrictJson.require(Path.of(normalized).isAbsolute() && !normalized.contains("\\")
                    && normalized.equals(normalized.toLowerCase(Locale.ROOT)), "retained epoch path is not the producer's normalized absolute path");
            String key = role + ":" + normalized;
            StrictJson.require(prior == null || prior.compareTo(key) < 0, "historical epoch inputs must retain unique sorted role/path keys");
            prior = key; present.add(role);
            if (SINGLE_ROLES.contains(role)) {
                StrictJson.require(singular.add(role) && ref.bytes() > 0, "historical epoch has duplicate or empty mandatory artifact role");
            }
            if (role.equals("game_executable")) manifestExecutable = ref;
        }
        StrictJson.require(present.equals(ROLES) && singular.equals(SINGLE_ROLES) && manifestExecutable != null,
                "historical epoch is missing original runtime, native sources or artifact roles");
        // The producer resolved physical aliases before normalization. Original proof paths can retain the launch alias;
        // rereading today's filesystem cannot reconstruct an expired original alias and is not historical source proof.
        StrictJson.require(manifestExecutable.bytes() == executable.bytes() && manifestExecutable.sha256().equals(executable.sha256()),
                "historical epoch's unique executable bytes differ from its original source qualification");
        return new Decoded(epoch, executable, manifest);
    }

    private static ObjectNode proof(ExactRef reference, byte[] bytes, GuardEvidence guard) {
        Objects.requireNonNull(guard); exact(reference, bytes);
        ObjectNode source = StrictJson.object(parse(bytes), PROOF_FIELDS);
        StrictJson.require("xar.java-root-native-source-proof/v2".equals(StrictJson.text(source.get("schema")))
                && guard.source().machineId().equals(StrictJson.text(source.get("machine_id")))
                && guard.sessionId().equals(StrictJson.text(source.get("session_id")))
                && guard.source().sourceRef().equals(ExactRef.fromJson(source.get("source"))),
                "original source qualification does not belong to the canonical SAVE guard");
        String instant = StrictJson.text(source.get("observed_at_utc"));
        StrictJson.require(instant.endsWith("Z"), "original source qualification instant must be UTC");
        Instant.parse(instant); HostMode.valueOf(StrictJson.text(source.get("mode")));
        positive(source.get("host_configuration"));
        ExactRef executable = positive(source.get("game_executable"));
        ExactRef manifest = positive(source.get("source_epoch_manifest"));
        String epoch = StrictJson.text(source.get("owner_source_epoch"));
        StrictJson.require(epoch.matches("[0-9a-f]{64}") && epoch.equals(manifest.sha256()), "original source epoch/manifest binding differs");
        ArrayNode closure = array(source.get("complete_evidence_closure"));
        StrictJson.require(!closure.isEmpty() && closure.size() <= 30_000, "bounded original physical evidence closure required");
        Set<ExactRef> unique = new HashSet<>();
        for (JsonNode item : closure) {
            ExactRef ref = ExactRef.fromJson(item);
            StrictJson.require(Path.of(ref.path()).isAbsolute() && unique.add(ref), "original physical evidence closure has relative or duplicate sources");
        }
        StrictJson.require(unique.contains(executable), "original physical evidence closure omits its actual executable");
        return source;
    }

    private static ArrayNode array(JsonNode value) {
        StrictJson.require(value instanceof ArrayNode, "actual historical source array required"); return (ArrayNode) value;
    }
    private static ExactRef positive(JsonNode value) {
        ExactRef ref = ExactRef.fromJson(value);
        StrictJson.require(ref.bytes() > 0 && Path.of(ref.path()).isAbsolute(), "original nonempty absolute physical source required"); return ref;
    }
    private static void exact(ExactRef reference, byte[] bytes) {
        Objects.requireNonNull(reference); Objects.requireNonNull(bytes);
        StrictJson.require(Path.of(reference.path()).isAbsolute() && reference.bytes() > 0 && reference.bytes() <= LIMIT && bytes.length == reference.bytes()
                && ActionCodec.sha256(bytes).equals(reference.sha256()), "historical original bytes or digest changed");
    }
    private static JsonNode parse(byte[] bytes) {
        try {
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString();
            return org.xar.ck3.control.build.ControlBuild.strictMapper().readTree(text);
        } catch (IOException failure) { throw new IllegalArgumentException("invalid bounded historical source JSON", failure); }
    }
}
