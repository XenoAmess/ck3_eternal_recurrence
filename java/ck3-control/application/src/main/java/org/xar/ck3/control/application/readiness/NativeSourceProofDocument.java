package org.xar.ck3.control.application.readiness;

import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.application.readiness.NativeSourceFileIdentity.SourceWitness;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Durable original source DATA. Constructing or decoding this record grants no Game custody. */
public record NativeSourceProofDocument(String machineId, String sessionId, String observedAtUtc,
        Mode mode, ExactRef hostConfiguration, ExactRef source, String ownerSourceEpoch,
        ExactRef sourceEpochManifest, ExactRef gameExecutable,
        List<ExactRef> completeEvidenceClosure, List<SourceWitness> liveWitnesses) {
    public static final String SCHEMA = "xar.java-root-native-source-proof/v3";
    public static final int MAXIMUM_BYTES = 16 << 20;
    public static final int MAXIMUM_WITNESSES = 65_536;

    /** Actual package HostMode wire values; no dependency from application back into build tools. */
    public enum Mode { HTTP, MCP_STDIO, COMPLETE_MIGRATION }

    public NativeSourceProofDocument {
        StrictJson.text(machineId);
        StrictJson.text(sessionId);
        StrictJson.utc(observedAtUtc);
        Objects.requireNonNull(mode);
        Objects.requireNonNull(hostConfiguration);
        Objects.requireNonNull(source);
        Objects.requireNonNull(sourceEpochManifest);
        Objects.requireNonNull(gameExecutable);
        pathKey(source.path()); pathKey(sourceEpochManifest.path());
        StrictJson.require(ownerSourceEpoch != null && ownerSourceEpoch.matches("[0-9a-f]{64}")
                        && ownerSourceEpoch.equals(sourceEpochManifest.sha256()),
                "source epoch must bind its complete original manifest");
        completeEvidenceClosure = List.copyOf(completeEvidenceClosure);
        liveWitnesses = List.copyOf(liveWitnesses);
        StrictJson.require(!completeEvidenceClosure.isEmpty()
                        && completeEvidenceClosure.size() <= MAXIMUM_WITNESSES,
                "bounded complete evidence closure required");
        StrictJson.require(!liveWitnesses.isEmpty() && liveWitnesses.size() <= MAXIMUM_WITNESSES,
                "durable actual live native Witnesses required; v2 cannot supply them");
        Map<String, SourceWitness> witnessed = new HashMap<>();
        for (SourceWitness witness : liveWitnesses) {
            String key = pathKey(witness.source().path());
            StrictJson.require(witnessed.putIfAbsent(key, witness) == null,
                    "duplicate physical source Witness path");
        }
        HashSet<String> declared = new HashSet<>();
        for (ExactRef reference : completeEvidenceClosure) {
            StrictJson.require(declared.add(pathKey(reference.path())), "duplicate evidence closure path");
            requireWitness(witnessed, reference);
        }
        requireWitness(witnessed, hostConfiguration);
        requireWitness(witnessed, gameExecutable);
    }

    private static void requireWitness(Map<String, SourceWitness> witnessed, ExactRef reference) {
        SourceWitness witness = witnessed.get(pathKey(reference.path()));
        StrictJson.require(witness != null && witness.source().bytes() == reference.bytes()
                        && witness.source().sha256().equals(reference.sha256()),
                "declared native source has no exact original durable Witness");
    }

    /** Windows case and separator equivalence only; this does not inspect or resolve a filesystem. */
    public static String pathKey(String path) {
        String normalized = StrictJson.text(path).replace('\\', '/').toLowerCase(Locale.ROOT);
        boolean drive = normalized.matches("[a-z]:/.+");
        boolean unc = normalized.matches("//[^/]+/[^/]+/.+");
        String body = unc ? normalized.substring(2) : normalized;
        StrictJson.require((drive || unc) && !body.contains("//") && !normalized.endsWith("/")
                        && !normalized.contains("/./") && !normalized.contains("/../")
                        && !normalized.endsWith("/.") && !normalized.endsWith("/.."),
                "unambiguous absolute original Windows source path required");
        return normalized;
    }
}
