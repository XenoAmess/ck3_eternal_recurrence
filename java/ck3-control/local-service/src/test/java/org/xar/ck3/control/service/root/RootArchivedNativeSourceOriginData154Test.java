package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.readiness.*;
import org.xar.ck3.control.application.readiness.NativeSourceFileIdentity.SourceWitness;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.FreshContinuityGenesis;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Software archived DATA only; no SourceQualification, Ready or Game execution. */
final class RootArchivedNativeSourceOriginData154Test {
    @TempDir Path temporary;
    private static final String MACHINE = "software-origin-machine";
    private static final String SESSION = "software-origin-session";
    private static final String AUTHORITY = "software-origin-data";
    private static final int MAX_BYTES = 16 << 20;
    private static final OperationKey OPERATION = new OperationKey("query-software-archived-origin");

    @FunctionalInterface private interface ArchiveWork {
        void run(ContinuityWriter writer, NativeOutcomeArchive archive,
                ContinuityStorePort.Session same) throws IOException;
    }
    private record OriginData(Path sourceFile, Map<String, Path> roleFiles,
            NativeSourceProofDocument proof, ExactRef proofRef, ExactRef epochRef,
            Complete frame, SemanticEvidence semantic, ExactRef hello,
            ExactRef heartbeat, ExactRef capabilities) { }

    private static ExactRef normalized(SharedSourceFiles.Witness actual) {
        return new ExactRef(NativeSourceProofDocument.pathKey(actual.source().path()),
                actual.source().bytes(), actual.source().sha256());
    }
    private static GuardEvidence guard(OriginData data, NativeOutcomeArchive archive,
            ContinuityStorePort.Session same, ExactRef proofRef, ExactRef helloRef) throws IOException {
        var frame = data.frame();
        var originals = new RootGuardEvidence.PhysicalReadOriginals(frame, data.semantic(), helloRef,
                data.heartbeat(), Optional.of(proofRef), data.capabilities());
        var basis = RootGuardEvidence.preservePhysicalRead(originals, OPERATION, AUTHORITY,
                archive.withSession(same), same.head());
        return new GuardEvidence(frame.identity(), frame.source(), frame.sessionId(), frame.connectionGeneration(),
                OPERATION, frame.originalEvidence(), helloRef, AUTHORITY, frame.observedAt(),
                frame.observedAt().plusSeconds(3600), List.of(basis));
    }

    private void withArchive(ArchiveWork work) throws IOException {
        Path ledger = Files.createTempDirectory(temporary, "ledger-");
        Path pathsLock = ledger.resolve("ROOT-CONTINUITY-WINDOW.lock");
        Files.createFile(pathsLock);

        var plan = new FreshContinuityGenesis.Plan(MACHINE, 1, 1);
        byte[] planBytes = FreshContinuityGenesis.encode(plan);
        Path planPath = ledger.resolve("genesis.json");
        Files.write(planPath, planBytes);
        ExactRef planRef = new ExactRef(planPath.toString(), planBytes.length, DriverJson.sha256(planBytes));

        Path controlPath = ledger.resolve("control-source.txt");
        byte[] controlBytes = "stable-control-source".getBytes(StandardCharsets.UTF_8);
        Files.write(controlPath, controlBytes);
        ExactRef controlRef = new ExactRef(controlPath.toString(), controlBytes.length, DriverJson.sha256(controlBytes));

        var initialLayout = new WriterContracts.InitialLayout(ledger.resolve("ROOT-CONTINUITY-WINDOW.json"), ledger.resolve("anchor.json"), MACHINE);

        try (StorageWriteGuardTestSupport storage = StorageWriteGuardTestSupport.create(ledger, pathsLock, 256L << 20)) {
            var initialized = ContinuityWriter.initializeFresh(plan, planRef, initialLayout, storage);

            var artifacts = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(ledger.resolve("artifacts"), pathsLock, 64L << 20), storage);

            var authority = new WriterContracts.TransitionAuthority() {
                @Override public String revalidate(ContinuityState predecessor, WriterContracts.Request request) throws IOException {
                    throw new AssertionError("no transitions permitted");
                }
                @Override public ContinuityState reduce(ContinuityState predecessor, WriterContracts.Request request) throws IOException {
                    throw new AssertionError("no transitions permitted");
                }
            };

            var writer = new ContinuityWriter(initialized.layout(), List.of(controlRef), authority, Clock.systemUTC(), new ContinuityWriter.Extensions(List.of(), Optional.of(artifacts), Optional.empty()), storage);
            var archive = new NativeOutcomeArchive(artifacts, writer);

            writer.locked(same -> {
                work.run(writer, archive, same);
                return null;
            });
        }
    }

private OriginData originData(Path history, ContinuityWriter writer, NativeOutcomeArchive archive, ContinuityStorePort.Session same) throws IOException {
    writer.requireSession(same);
    Files.createDirectories(history);
    Instant at = Instant.now();
    List<String> roles = List.of("bridge_dll", "game_executable", "injector", "java_runtime", "launcher_settings", "native_source");
    Map<String, Path> roleFiles = new LinkedHashMap<>();
    Map<String, ExactRef> refs = new LinkedHashMap<>();
    List<SharedSourceFiles.Witness> actualWitnesses = new ArrayList<>();
    Path sourceFile = null;

    for (String role : roles) {
        Path path = history.resolve(role + ".bin");
        Files.write(path, ("software-" + role + "-data").getBytes(StandardCharsets.UTF_8));
        SharedSourceFiles.Witness witness = SharedSourceFiles.observe(path);
        roleFiles.put(role, path);
        ExactRef ref = normalized(witness);
        refs.put(role, ref);
        actualWitnesses.add(witness);
        if (role.equals("native_source")) sourceFile = path;
    }

    Path hostPath = history.resolve("host.json");
    Files.write(hostPath, ("software-host-data").getBytes(StandardCharsets.UTF_8));
    SharedSourceFiles.Witness hostWitness = SharedSourceFiles.observe(hostPath);
    ExactRef hostRef = normalized(hostWitness);
    actualWitnesses.add(hostWitness);

    List<SourceWitness> persistedWitnesses = RootNativeSourceProofProducer.persistWitnesses(actualWitnesses);

    ObjectNode epoch = StrictJson.object();
    epoch.put("schema", "xar.java-root-source-epoch/v1");
    epoch.put("machine_id", MACHINE);
    var inputs = epoch.putArray("inputs");
    for (String role : roles) {
        var row = inputs.addObject();
        row.put("role", role);
        row.set("source", refs.get(role).toJson());
    }
    byte[] epochBytes = StrictJson.canonical(epoch, StrictJson.EXPLICIT_MAX_BYTES);
    ExactRef epochRef = archive.preserveArtifact(same, epochBytes, MAX_BYTES);

    NativeSourceProofDocument proof = new NativeSourceProofDocument(
            MACHINE, SESSION, at.toString(), NativeSourceProofDocument.Mode.HTTP,
            hostRef, refs.get("native_source"), epochRef.sha256(), epochRef,
            refs.get("game_executable"), List.copyOf(refs.values()), persistedWitnesses);
    byte[] proofBytes = NativeSourceProofCodec.encode(proof);
    ExactRef proofRef = archive.preserveArtifact(same, proofBytes, MAX_BYTES);

    ObjectNode helloRow = StrictJson.object();
    helloRow.put("type", "hello");
    helloRow.put("protocol_version", 1);
    helloRow.put("pid", 991);
    helloRow.put("connection_generation", BigInteger.TWO);
    helloRow.put("bridge_version", "software-data");
    helloRow.put("expected_ck3_sha256", refs.get("game_executable").sha256());
    helloRow.put("game_adapter_id", "software-data");
    helloRow.put("game_adapter_status", "ready");
    helloRow.put("ck3_build_match", true);
    var caps = helloRow.putArray("capabilities");
    caps.add("game.state.snapshot");
    byte[] helloBytes = NativeWire.packet(StrictJson.canonical(helloRow, StrictJson.EXPLICIT_MAX_BYTES));
    ExactRef helloRef = archive.preserveArtifact(same, helloBytes, 1 << 20);

    ObjectNode hbRow = StrictJson.object();
    hbRow.put("type", "heartbeat");
    hbRow.put("protocol_version", 1);
    hbRow.put("sequence", 1);
    byte[] hbBytes = NativeWire.packet(StrictJson.canonical(hbRow, StrictJson.EXPLICIT_MAX_BYTES));
    ExactRef heartbeatRef = archive.preserveArtifact(same, hbBytes, 1 << 20);

    ExactRef capabilitiesRef = archive.preserveArtifact(same, StrictJson.canonical(caps, StrictJson.EXPLICIT_MAX_BYTES), 1 << 20);

    GameGeneration game = new GameGeneration(991, new PythonOnlyUInt64(BigInteger.ONE));
    JointBudgetSelector.Frame budgetFrame = new JointBudgetSelector.Frame(BigInteger.valueOf(73), BigInteger.valueOf(7), BigInteger.valueOf(100));
    JointBudgetSelector.ProposalFrame stateFrame = new JointBudgetSelector.ProposalFrame(budgetFrame, "software:7", BigInteger.valueOf(9), "software-origin-episode");
    ObservationIdentity identity = new ObservationIdentity(MACHINE, game, stateFrame, 1);
    G2Source source = new G2Source(MACHINE, at.toString(), "software-data", refs.get("native_source"));

    ObjectNode driverFacts = StrictJson.object();
    driverFacts.put("software_role", "driver_facts");
    byte[] driverFactsBytes = StrictJson.canonical(driverFacts, StrictJson.EXPLICIT_MAX_BYTES);
    ExactRef driverFactsRef = archive.preserveArtifact(same, driverFactsBytes, 1 << 20);

    ObjectNode semanticTree = StrictJson.object();
    semanticTree.put("software_only", true);
    semanticTree.set("java_driver_facts_evidence", driverFactsRef.toJson());
    byte[] semanticBytes = DriverJson.encodeNode(semanticTree);
    ExactRef semanticRef = archive.preserveArtifact(same, semanticBytes, 1 << 20);

    ObjectNode snapshotRow = StrictJson.object();
    snapshotRow.put("type", "state_snapshot");
    snapshotRow.put("protocol_version", 1);
    snapshotRow.put("snapshot_id", "software:7");
    snapshotRow.put("revision", BigInteger.valueOf(7));
    ObjectNode state = StrictJson.object();
    state.put("date_raw", 100);
    state.put("paused", true);
    state.put("map_ready", true);
    state.put("speed", 1);
    ObjectNode played = StrictJson.object();
    played.put("character_id", 73);
    played.put("alive", true);
    state.set("played_character", played);
    snapshotRow.set("state", state);
    byte[] snapshotBytes = NativeWire.packet(StrictJson.canonical(snapshotRow, StrictJson.EXPLICIT_MAX_BYTES));
    ExactRef nativeRef = archive.preserveArtifact(same, snapshotBytes, DriverJson.MAX_NATIVE_BYTES + 4);

    Complete complete = new Complete(identity, source, SESSION, BigInteger.TWO, DriverJson.object(semanticBytes, DriverJson.MAX_NATIVE_BYTES), nativeRef, at, DriverJson.sha256(semanticBytes));

    ObjectNode stampRow = StrictJson.object();
    stampRow.put("software_role", "driver_stamp");
    byte[] stampBytes = StrictJson.canonical(stampRow, StrictJson.EXPLICIT_MAX_BYTES);
    ExactRef stampRef = archive.preserveArtifact(same, stampBytes, 1 << 20);

    ObjectNode origDriverRow = StrictJson.object();
    origDriverRow.put("software_role", "original_driver");
    byte[] origDriverBytes = StrictJson.canonical(origDriverRow, StrictJson.EXPLICIT_MAX_BYTES);
    ExactRef origDriverRef = archive.preserveArtifact(same, origDriverBytes, 1 << 20);

    SemanticEvidence semanticEvidence = new SemanticEvidence(identity, semanticRef, nativeRef, stampRef, origDriverRef, at);

    return new OriginData(sourceFile, Map.copyOf(roleFiles), proof, proofRef, epochRef, complete, semanticEvidence, helloRef, heartbeatRef, capabilitiesRef);
}

@Test void historicalCodeDeletionKeepsExactArchivedOrigin() throws IOException {
    Path history = Files.createTempDirectory(temporary, "historical-");
    withArchive((writer, archive, same) -> {
        var data = originData(history, writer, archive, same);
        var original = guard(data, archive, same, data.proofRef(), data.hello());
        var result = RootArchivedNativeSourceReader.requireOrigin(writer, archive, same, original, archive.withSession(same));
        assertEquals(data.proof(), result.orElseThrow());
        byte[] proofBytes = archive.readArtifact(same, data.proofRef(), RootArchivedNativeSourceReader.MAXIMUM_SOURCE_BYTES);
        byte[] epochBytes = archive.readArtifact(same, data.epochRef(), RootArchivedNativeSourceReader.MAXIMUM_SOURCE_BYTES);
        Files.delete(data.sourceFile());
        assertFalse(Files.exists(data.sourceFile()));
        var result2 = RootArchivedNativeSourceReader.requireOrigin(writer, archive, same, original, archive.withSession(same));
        assertEquals(data.proof(), result2.orElseThrow());
        byte[] proofBytes2 = archive.readArtifact(same, data.proofRef(), RootArchivedNativeSourceReader.MAXIMUM_SOURCE_BYTES);
        byte[] epochBytes2 = archive.readArtifact(same, data.epochRef(), RootArchivedNativeSourceReader.MAXIMUM_SOURCE_BYTES);
        assertArrayEquals(proofBytes, proofBytes2);
        assertArrayEquals(epochBytes, epochBytes2);
    });
}

@Test void historicalCodeAndWitnessChangesKeepExactArchivedOrigin() throws IOException {
    Path history = Files.createTempDirectory(temporary, "historical-");
    withArchive((writer, archive, same) -> {
        var data = originData(history, writer, archive, same);
        var original = guard(data, archive, same, data.proofRef(), data.hello());
        var result = RootArchivedNativeSourceReader.requireOrigin(writer, archive, same, original, archive.withSession(same));
        assertEquals(data.proof(), result.orElseThrow());
        Files.write(data.sourceFile(), "modified-source-data".getBytes(StandardCharsets.UTF_8));
        Files.write(data.roleFiles().get("bridge_dll"), "modified-bridge-data".getBytes(StandardCharsets.UTF_8));
        var result2 = RootArchivedNativeSourceReader.requireOrigin(writer, archive, same, original, archive.withSession(same));
        assertEquals(data.proof(), result2.orElseThrow());
        assertEquals(data.proof().source(), original.source().sourceRef());
        assertEquals(data.proofRef(), RootGuardEvidence.sourceQualification(original, archive.withSession(same)).orElseThrow());
        assertEquals(data.epochRef(), data.proof().sourceEpochManifest());
        RootArchivedNativeSourceReader.requireOriginalFiles(data.proof());
    });
}

@Test void immutableProofAndEpochCorruptionRemainRejected() throws IOException {
    withArchive((writer, archive, same) -> {
        Path history = Files.createTempDirectory(temporary, "historical-proof-");
        OriginData data = originData(history, writer, archive, same);
        GuardEvidence original = guard(data, archive, same, data.proofRef(), data.hello());
        Optional<NativeSourceProofDocument> baseline = RootArchivedNativeSourceReader.requireOrigin(writer, archive, same, original, archive.withSession(same));
        assertTrue(baseline.isPresent());
        assertEquals(data.proof(), baseline.get());
        Path target = Path.of(data.proofRef().path());
        Files.write(target, "corrupted-proof-bytes".getBytes(StandardCharsets.UTF_8));
        assertThrows(IOException.class, () -> RootArchivedNativeSourceReader.requireOrigin(writer, archive, same, original, archive.withSession(same)));
    });
    withArchive((writer, archive, same) -> {
        Path history = Files.createTempDirectory(temporary, "historical-epoch-");
        OriginData data = originData(history, writer, archive, same);
        GuardEvidence original = guard(data, archive, same, data.proofRef(), data.hello());
        Optional<NativeSourceProofDocument> baseline = RootArchivedNativeSourceReader.requireOrigin(writer, archive, same, original, archive.withSession(same));
        assertTrue(baseline.isPresent());
        assertEquals(data.proof(), baseline.get());
        Path target = Path.of(data.epochRef().path());
        Files.write(target, "corrupted-epoch-bytes".getBytes(StandardCharsets.UTF_8));
        assertThrows(IOException.class, () -> RootArchivedNativeSourceReader.requireOrigin(writer, archive, same, original, archive.withSession(same)));
    });
}

@Test void archivedMetadataMachineSessionAndSourceBindingsRemainRequired() throws IOException {
    withArchive((writer, archive, same) -> {
        Path history = Files.createTempDirectory(temporary, "historical-machine-");
        OriginData data = originData(history, writer, archive, same);
        GuardEvidence original = guard(data, archive, same, data.proofRef(), data.hello());
        assertTrue(RootArchivedNativeSourceReader.requireOrigin(writer, archive, same, original, archive.withSession(same)).isPresent());
        NativeSourceProofDocument altered = new NativeSourceProofDocument("different-machine", data.proof().sessionId(), data.proof().observedAtUtc(), data.proof().mode(), data.proof().hostConfiguration(), data.proof().source(), data.proof().ownerSourceEpoch(), data.proof().sourceEpochManifest(), data.proof().gameExecutable(), data.proof().completeEvidenceClosure(), data.proof().liveWitnesses());
        byte[] bytes = NativeSourceProofCodec.encode(altered);
        ExactRef alteredRef = archive.preserveArtifact(same, bytes, MAX_BYTES);
        GuardEvidence alteredGuard = guard(data, archive, same, alteredRef, data.hello());
        assertThrows(IllegalArgumentException.class, () -> RootArchivedNativeSourceReader.requireOrigin(writer, archive, same, alteredGuard, archive.withSession(same)));
    });
    withArchive((writer, archive, same) -> {
        Path history = Files.createTempDirectory(temporary, "historical-session-");
        OriginData data = originData(history, writer, archive, same);
        GuardEvidence original = guard(data, archive, same, data.proofRef(), data.hello());
        assertTrue(RootArchivedNativeSourceReader.requireOrigin(writer, archive, same, original, archive.withSession(same)).isPresent());
        NativeSourceProofDocument altered = new NativeSourceProofDocument(data.proof().machineId(), "different-session", data.proof().observedAtUtc(), data.proof().mode(), data.proof().hostConfiguration(), data.proof().source(), data.proof().ownerSourceEpoch(), data.proof().sourceEpochManifest(), data.proof().gameExecutable(), data.proof().completeEvidenceClosure(), data.proof().liveWitnesses());
        byte[] bytes = NativeSourceProofCodec.encode(altered);
        ExactRef alteredRef = archive.preserveArtifact(same, bytes, MAX_BYTES);
        GuardEvidence alteredGuard = guard(data, archive, same, alteredRef, data.hello());
        assertThrows(IllegalArgumentException.class, () -> RootArchivedNativeSourceReader.requireOrigin(writer, archive, same, alteredGuard, archive.withSession(same)));
    });
    withArchive((writer, archive, same) -> {
        Path history = Files.createTempDirectory(temporary, "historical-source-");
        OriginData data = originData(history, writer, archive, same);
        GuardEvidence original = guard(data, archive, same, data.proofRef(), data.hello());
        assertTrue(RootArchivedNativeSourceReader.requireOrigin(writer, archive, same, original, archive.withSession(same)).isPresent());
        NativeSourceProofDocument altered = new NativeSourceProofDocument(data.proof().machineId(), data.proof().sessionId(), data.proof().observedAtUtc(), data.proof().mode(), data.proof().hostConfiguration(), data.proof().hostConfiguration(), data.proof().ownerSourceEpoch(), data.proof().sourceEpochManifest(), data.proof().gameExecutable(), data.proof().completeEvidenceClosure(), data.proof().liveWitnesses());
        byte[] bytes = NativeSourceProofCodec.encode(altered);
        ExactRef alteredRef = archive.preserveArtifact(same, bytes, MAX_BYTES);
        GuardEvidence alteredGuard = guard(data, archive, same, alteredRef, data.hello());
        assertThrows(IllegalArgumentException.class, () -> RootArchivedNativeSourceReader.requireOrigin(writer, archive, same, alteredGuard, archive.withSession(same)));
    });
}

@Test void originalHelloPidAndConnectionRemainRequired() throws IOException {
    withArchive((writer, archive, same) -> {
        Path history = Files.createTempDirectory(temporary, "historical-pid-");
        OriginData data = originData(history, writer, archive, same);
        GuardEvidence original = guard(data, archive, same, data.proofRef(), data.hello());
        assertTrue(RootArchivedNativeSourceReader.requireOrigin(writer, archive, same, original, archive.withSession(same)).isPresent());
        byte[] packet = archive.readArtifact(same, data.hello(), 1 << 20);
        ObjectNode row = StrictJson.object(StrictJson.parse(java.util.Arrays.copyOfRange(packet, 4, packet.length)), Set.of("type", "protocol_version", "pid", "connection_generation", "bridge_version", "expected_ck3_sha256", "game_adapter_id", "game_adapter_status", "ck3_build_match", "capabilities"));
        row.put("pid", 992);
        byte[] bytes = NativeWire.packet(StrictJson.canonical(row, StrictJson.EXPLICIT_MAX_BYTES));
        ExactRef newHello = archive.preserveArtifact(same, bytes, 1 << 20);
        GuardEvidence alteredGuard = guard(data, archive, same, data.proofRef(), newHello);
        assertThrows(IllegalArgumentException.class, () -> RootArchivedNativeSourceReader.requireOrigin(writer, archive, same, alteredGuard, archive.withSession(same)));
    });
    withArchive((writer, archive, same) -> {
        Path history = Files.createTempDirectory(temporary, "historical-conn-");
        OriginData data = originData(history, writer, archive, same);
        GuardEvidence original = guard(data, archive, same, data.proofRef(), data.hello());
        assertTrue(RootArchivedNativeSourceReader.requireOrigin(writer, archive, same, original, archive.withSession(same)).isPresent());
        byte[] packet = archive.readArtifact(same, data.hello(), 1 << 20);
        ObjectNode row = StrictJson.object(StrictJson.parse(java.util.Arrays.copyOfRange(packet, 4, packet.length)), Set.of("type", "protocol_version", "pid", "connection_generation", "bridge_version", "expected_ck3_sha256", "game_adapter_id", "game_adapter_status", "ck3_build_match", "capabilities"));
        row.put("connection_generation", BigInteger.valueOf(3));
        byte[] bytes = NativeWire.packet(StrictJson.canonical(row, StrictJson.EXPLICIT_MAX_BYTES));
        ExactRef newHello = archive.preserveArtifact(same, bytes, 1 << 20);
        GuardEvidence alteredGuard = guard(data, archive, same, data.proofRef(), newHello);
        assertThrows(IllegalArgumentException.class, () -> RootArchivedNativeSourceReader.requireOrigin(writer, archive, same, alteredGuard, archive.withSession(same)));
    });
}
}
