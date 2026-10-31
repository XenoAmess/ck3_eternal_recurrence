package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.readiness.NativeSourceFileIdentity.SourceWitness;
import org.xar.ck3.control.application.readiness.NativeSourceProofCodec;
import org.xar.ck3.control.application.readiness.NativeSourceProofDocument;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Original archived DATA and session/HELLO provenance; historical files grant no current source qualification. */
public final class RootArchivedNativeSourceReader {
    public static final int MAXIMUM_SOURCE_BYTES = 16 << 20;
    private static final String EPOCH_SCHEMA = "xar.java-root-source-epoch/v1";
    private static final Set<String> EPOCH_FIELDS = Set.of("schema", "machine_id", "inputs");
    private static final Set<String> INPUT_FIELDS = Set.of("role", "source");

    private RootArchivedNativeSourceReader() { }

    public enum EpochRole {
        JAVA_RUNTIME("java_runtime"), NATIVE_SOURCE("native_source"), BRIDGE_DLL("bridge_dll"),
        INJECTOR("injector"), GAME_EXECUTABLE("game_executable"), LAUNCHER_SETTINGS("launcher_settings");
        private final String wire;
        EpochRole(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        static EpochRole decode(String value) {
            for (EpochRole role : values()) if (role.wire.equals(value)) return role;
            throw new IllegalArgumentException("unrecognized original source epoch role");
        }
    }

    public record EpochInput(EpochRole role, ExactRef source) {
        public EpochInput { Objects.requireNonNull(role); Objects.requireNonNull(source); }
    }

    /** Parsed historical DATA. Its public constructor and decoder grant no source or current-Game authority. */
    public record EpochData(String machineId, List<EpochInput> inputs) {
        public EpochData {
            StrictJson.text(machineId); inputs = List.copyOf(inputs);
            StrictJson.require(!inputs.isEmpty(), "nonempty original software epoch inputs required");
        }
    }

    /** No filesystem, ManagedGameSession, live guard, currentMetadata or source reconstruction occurs here. */
    public static NativeSourceProofDocument readData(ExactRef reference, byte[] original) throws IOException {
        exact(reference, original, MAXIMUM_SOURCE_BYTES);
        // The sole codec rejects v2: those bytes never retained a native Witness/FileID chain.
        return NativeSourceProofCodec.decode(original);
    }

    /** Strict historical epoch DATA joined to every persisted live witness, without consulting today's files. */
    public static EpochData readEpochData(ExactRef reference, byte[] original, NativeSourceProofDocument proof) {
        Objects.requireNonNull(proof); exact(reference, original, MAXIMUM_SOURCE_BYTES);
        StrictJson.require(reference.equals(proof.sourceEpochManifest())
                && reference.sha256().equals(proof.ownerSourceEpoch()), "original source epoch reference differs");
        ObjectNode row = StrictJson.object(FullJsonTree.parse(original, MAXIMUM_SOURCE_BYTES), EPOCH_FIELDS);
        StrictJson.require(EPOCH_SCHEMA.equals(StrictJson.text(row.get("schema")))
                && proof.machineId().equals(StrictJson.text(row.get("machine_id"))),
                "original source epoch schema or machine differs");
        JsonNode values = row.get("inputs");
        StrictJson.require(values != null && values.isArray() && !values.isEmpty()
                && values.size() <= 65_536, "finite nonempty source epoch inputs required");
        Map<String, SourceWitness> witnesses = witnessIndex(proof.liveWitnesses());
        List<EpochInput> inputs = new ArrayList<>();
        Set<EpochRole> roles = new HashSet<>();
        String previous = null;
        for (JsonNode value : values) {
            ObjectNode input = StrictJson.object(value, INPUT_FIELDS);
            EpochRole role = EpochRole.decode(StrictJson.text(input.get("role")));
            ExactRef source = ExactRef.fromJson(input.get("source"));
            String normalized = pathKey(source);
            StrictJson.require(source.path().equals(normalized), "original epoch path is not the producer's normalized path");
            String key = role.wire() + ":" + normalized;
            StrictJson.require(previous == null || previous.compareTo(key) < 0,
                    "original epoch inputs are duplicated or outside the producer's exact order");
            previous = key;
            requireWitness(witnesses, source); roles.add(role);
            inputs.add(new EpochInput(role, source));
            if (role == EpochRole.GAME_EXECUTABLE)
                StrictJson.require(sameFileReference(source, proof.gameExecutable()), "source epoch substituted its executable");
        }
        StrictJson.require(roles.containsAll(Set.of(EpochRole.JAVA_RUNTIME, EpochRole.NATIVE_SOURCE,
                EpochRole.BRIDGE_DLL, EpochRole.INJECTOR, EpochRole.GAME_EXECUTABLE, EpochRole.LAUNCHER_SETTINGS)),
                "original source epoch lost a required actual producer role");
        requireWitness(witnesses, proof.hostConfiguration());
        for (ExactRef source : proof.completeEvidenceClosure()) requireWitness(witnesses, source);
        requireWitness(witnesses, proof.gameExecutable());
        return new EpochData(proof.machineId(), inputs);
    }

    /**
     * Reopens exact immutable proof/epoch materials under their real writer history and validates
     * their recorded session/HELLO relations. Historical source/deployment files are not continuing
     * qualification. This does not mint a guard, refresh a deadline, grant Ready, or authorize an action.
     */
    public static Optional<NativeSourceProofDocument> requireOrigin(ContinuityWriter writer, NativeOutcomeArchive retained, ContinuityStorePort.Session same, GuardEvidence guard, ActionPorts.OutcomeArchive originals) throws IOException {
        Objects.requireNonNull(writer); Objects.requireNonNull(retained); Objects.requireNonNull(guard);
        Objects.requireNonNull(originals); writer.requireSession(same);
        if (retained.writer() != writer) throw new IOException("archived source reader requires the exact writer/archive");
        RootGuardEvidence.requireHistory(guard, originals, same);
        Optional<ExactRef> supplied = RootGuardEvidence.sourceQualification(guard, originals);
        if(supplied.isEmpty())return Optional.empty();
        ExactRef qualification = supplied.orElseThrow();
        WriterContracts.Pin proofPin = same.capturePin(qualification, MAXIMUM_SOURCE_BYTES);
        byte[] proofBytes = retained.readArtifact(same, qualification, MAXIMUM_SOURCE_BYTES);
        exact(qualification, originals.loadMaterial(qualification).bytes(), MAXIMUM_SOURCE_BYTES);
        NativeSourceProofDocument proof = readData(qualification, proofBytes);
        StrictJson.require(proof.machineId().equals(guard.origin().machineId())
                && proof.machineId().equals(guard.source().machineId())
                && proof.sessionId().equals(guard.sessionId())
                && proof.source().equals(guard.source().sourceRef()),
                "archived physical source changed the original guard machine/session/source");
        WriterContracts.Pin epochPin = same.capturePin(proof.sourceEpochManifest(), MAXIMUM_SOURCE_BYTES);
        byte[] epochBytes = retained.readArtifact(same, proof.sourceEpochManifest(), MAXIMUM_SOURCE_BYTES);
        readEpochData(proof.sourceEpochManifest(), epochBytes, proof);
        var hello = NativeWire.decode(originals.readOriginalPacket(guard.capabilityEvidence()));
        StrictJson.require(hello instanceof NativeWire.Hello, "archived source guard has no original HELLO");
        NativeWire.Hello actualHello = (NativeWire.Hello) hello;
        StrictJson.require(actualHello.pid() == guard.origin().game().pid()
                && actualHello.connectionGeneration().equals(guard.connectionGeneration())
                && actualHello.buildMatch()
                && actualHello.gameSha256().equalsIgnoreCase(proof.gameExecutable().sha256()),
                "archived physical source HELLO belongs to another original Game/build/connection");
        same.verifyPin(epochPin); same.verifyPin(proofPin);
        RootGuardEvidence.requireHistory(guard, originals, same);
        return Optional.of(proof);
    }

    /** Compatibility DATA boundary only; never reopens or revalidates today's source/deployment files. */
    public static void requireOriginalFiles(NativeSourceProofDocument proof) throws IOException {
        Objects.requireNonNull(proof);
    }


    private static Map<String, SourceWitness> witnessIndex(List<SourceWitness> originals) {
        Map<String, SourceWitness> result = new HashMap<>();
        for (SourceWitness witness : originals)
            StrictJson.require(result.putIfAbsent(pathKey(witness.source()), witness) == null,
                    "archived source contains duplicate normalized witness paths");
        StrictJson.require(!result.isEmpty(), "archived source lacks its original native witnesses");
        return Map.copyOf(result);
    }

    private static void requireWitness(Map<String, SourceWitness> witnesses, ExactRef source) {
        SourceWitness witness = witnesses.get(pathKey(source));
        StrictJson.require(witness != null && sameFileReference(witness.source(), source),
                "archived source role lacks its actual persisted native witness");
    }

    private static boolean sameFileReference(ExactRef left, ExactRef right) {
        return pathKey(left).equals(pathKey(right)) && left.bytes() == right.bytes() && left.sha256().equals(right.sha256());
    }

    private static String pathKey(ExactRef source) {
        return NativeSourceProofDocument.pathKey(source.path());
    }

    private static void exact(ExactRef reference, byte[] bytes, int maximum) {
        Objects.requireNonNull(reference);
        StrictJson.require(bytes != null && bytes.length > 0 && bytes.length <= maximum
                && reference.bytes() == bytes.length && reference.sha256().equals(DriverJson.sha256(bytes)),
                "archived source original differs from its exact immutable reference");
    }
}
