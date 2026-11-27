package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentAuthority;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore;
import org.xar.ck3.control.application.driver.DriverBootstrap;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.LoopWitness;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.RestoreSeedSupplement;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.ImmutableArtifactStore;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.continuity.writer.StorageWriteGuardTestSupport;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;

final class RootRestoreSeedSupplementTest {
    private static final String MACHINE = "restore-seed-supplement-fixture";
    private static final byte[] HISTORY = utf8("retained complete Driver fixture");
    private static final GameGeneration SUCCESSOR = new GameGeneration(321, new PythonOnlyUInt64(new BigInteger("133280000000000042")));

    @TempDir Path directory;

    @Test void importedFinalSeedSurvivesExactWriterPreviewWithItsHistoryAndLoop() throws IOException {
        NativeOutcomeArchive archive = archive();
        archive.writer().locked(same -> {
            ExactRef finalDriver = archive.preserveArtifact(same, utf8("final Driver fixture"), RestoreSeedSupplement.MAXIMUM_BYTES);
            ExactRef history = archive.preserveArtifact(same, HISTORY, RestoreSeedSupplement.MAXIMUM_BYTES);
            ExactRef loopOriginal = archive.preserveArtifact(same, utf8("original loop fixture"), RestoreSeedSupplement.MAXIMUM_BYTES);
            var seed = seed(finalDriver, history, Optional.of(new LoopWitness("batch-original", 8, 3, true, 21, false, loopOriginal)));
            ContinuityState predecessor = same.head().state();
            ObjectNode details = details(SavedAttachmentSourceStore.SOURCES_SCHEMA_IMPORTED_SAVE);
            var evidence = new LinkedHashSet<>(List.of(finalDriver));
            var pin = RootRestoreAdapters.archiveFinalSeedSupplement(same, archive, predecessor, details, evidence, seed).orElseThrow();
            var finalRequest = request(details, evidence);
            var prepared = same.preview(finalRequest);
            assertEquals(pin, WriterContracts.Pin.fromJson(prepared.request().detailsObject().get(RestoreSeedSupplement.DETAIL_FIELD)));
            assertTrue(prepared.evidence().contains(pin));
            assertEquals(List.of(finalDriver, pin.reference(), history, loopOriginal),
                    prepared.evidence().stream().map(WriterContracts.Pin::reference).toList());

            RootRestoreAdapters.requireFinalSeedSupplement(same, predecessor, prepared.request().detailsObject(),
                    prepared.request().evidence(), seed, Optional.of(pin));
            byte[] bytes = same.readPinned(pin, RestoreSeedSupplement.MAXIMUM_BYTES);
            RestoreSeedSupplement actual = RestoreSeedSupplement.decode(bytes);
            assertArrayEquals(bytes, actual.encode());
            assertEquals("restore-original", actual.requestId());
            assertEquals(finalDriver, actual.fullDriver());
            assertEquals(history, actual.originalHistoryBasis());
            assertEquals(9, actual.driverVersion());
            assertEquals(3, actual.episodeEpoch());
            assertEquals(SUCCESSOR, actual.successor().game());
            assertEquals(MACHINE, actual.successor().machineId());
            assertEquals("native-successor", actual.successor().sessionId());
            assertEquals(seed.auxiliary(), actual.auxiliary());
            assertEquals(seed.loop(), actual.loop());
            String wire = new String(bytes, StandardCharsets.UTF_8);
            assertTrue(wire.contains("\"score\":-0.00e+3"));
            assertFalse(wire.contains("connection_generation"));
            assertThrows(ContractViolationException.class, () -> RestoreSeedSupplement.decode(utf8(
                    wire.replace("\"session_id\":", "\"connection_generation\":14,\"session_id\":"))));
            var nonIntegerEpoch = assertThrows(IllegalArgumentException.class, () -> RestoreSeedSupplement.decode(utf8(
                    wire.replace("\"episode_epoch\":3", "\"episode_epoch\":3.0"))));
            assertEquals("episode_epoch must be an integer token", nonIntegerEpoch.getMessage());
            return null;
        });
    }

    @Test void revalidationRejectsForeignSeedHistoryAndReplacedSupplement() throws IOException {
        NativeOutcomeArchive archive = archive();
        archive.writer().locked(same -> {
            ExactRef finalDriver = archive.preserveArtifact(same, utf8("final Driver fixture"), RestoreSeedSupplement.MAXIMUM_BYTES);
            ExactRef history = archive.preserveArtifact(same, HISTORY, RestoreSeedSupplement.MAXIMUM_BYTES);
            var seed = seed(finalDriver, history, Optional.empty());
            ContinuityState predecessor = same.head().state();
            ObjectNode details = details(SavedAttachmentSourceStore.SOURCES_SCHEMA_IMPORTED_SAVE);
            var evidence = new LinkedHashSet<>(List.of(finalDriver));
            var pin = RootRestoreAdapters.archiveFinalSeedSupplement(same, archive, predecessor, details, evidence, seed).orElseThrow();
            assertTrue(RestoreSeedSupplement.decode(same.readPinned(pin, RestoreSeedSupplement.MAXIMUM_BYTES)).loop().isEmpty());
            assertThrows(ContractViolationException.class, () -> RootRestoreAdapters.archiveFinalSeedSupplement(same, archive,
                    predecessor, details(SavedAttachmentSourceStore.SOURCES_SCHEMA_IMPORTED_SAVE), new LinkedHashSet<>(),
                    seed(finalDriver, finalDriver, Optional.empty())));

            ObjectNode foreignDetails = details(SavedAttachmentSourceStore.SOURCES_SCHEMA_IMPORTED_SAVE);
            foreignDetails.put("evidence_id", "unrelated-restore");
            var foreignPin = RootRestoreAdapters.archiveFinalSeedSupplement(same, archive, predecessor, foreignDetails, evidence, seed).orElseThrow();
            details.set(RestoreSeedSupplement.DETAIL_FIELD, foreignPin.toJson());
            assertThrows(ContractViolationException.class, () -> RootRestoreAdapters.requireFinalSeedSupplement(same, predecessor, details,
                    evidence, seed, Optional.of(pin)));
            assertThrows(ContractViolationException.class, () -> RootRestoreAdapters.requireFinalSeedSupplement(same, predecessor, details,
                    evidence, seed, Optional.of(foreignPin)));

            details.set(RestoreSeedSupplement.DETAIL_FIELD, pin.toJson());
            assertThrows(ContractViolationException.class, () -> RootRestoreAdapters.requireFinalSeedSupplement(same, predecessor, details,
                    List.of(pin.reference()), seed, Optional.of(pin)));
            byte[] sameBytes = same.readPinned(pin, RestoreSeedSupplement.MAXIMUM_BYTES);
            Path path = Path.of(pin.reference().path());
            Files.move(path, directory.resolve("original-supplement.bin"));
            Files.write(path, sameBytes);
            assertThrows(IOException.class, () -> RootRestoreAdapters.requireFinalSeedSupplement(same, predecessor, details,
                    evidence, seed, Optional.of(pin)));
            return null;
        });
    }

    @Test void earlierAttachmentRetainsItsOriginalIdentityAndEvidence() throws IOException {
        NativeOutcomeArchive archive = archive();
        archive.writer().locked(same -> {
            ExactRef original = archive.preserveArtifact(same, HISTORY, RestoreSeedSupplement.MAXIMUM_BYTES);
            ObjectNode details = details(SavedAttachmentSourceStore.SOURCES_SCHEMA_PHYSICAL_SAVE_WITNESS);
            var evidence = new LinkedHashSet<>(List.of(original));
            var oldRequest = request(details, evidence);
            var seed = seed(original, original, Optional.empty());

            assertTrue(RootRestoreAdapters.archiveFinalSeedSupplement(same, archive, same.head().state(), details, evidence, seed).isEmpty());
            RootRestoreAdapters.requireFinalSeedSupplement(same, same.head().state(), details, evidence, seed, Optional.empty());
            assertFalse(details.has(RestoreSeedSupplement.DETAIL_FIELD));
            assertEquals(oldRequest.identity(), request(details, evidence).identity());
            assertEquals(oldRequest.evidence(), List.copyOf(evidence));
            return null;
        });
    }

    private static DriverBootstrap.Seed seed(ExactRef fullDriver, ExactRef history, Optional<LoopWitness> loop) {
        byte[] auxiliary = utf8("{\"weights\":[{\"score\":-0.00e+3,\"id\":9007199254740997}],\"nullable\":null}");
        return new DriverBootstrap.Seed(fullDriver, history, 9, 3,
                new TransportSession(MACHINE, SUCCESSOR, BigInteger.valueOf(14), "native-successor"),
                DriverJson.object(auxiliary, auxiliary.length), loop);
    }

    private static ObjectNode details(String schema) {
        ObjectNode details = StrictJson.object();
        details.put("evidence_id", "restore-original");
        details.put("source", "java_saved_checkpoint_restore_v1");
        details.putObject(SavedAttachmentSourceStore.SOURCES_DETAIL).put("schema", schema);
        return details;
    }

    private static WriterContracts.Request request(ObjectNode details, LinkedHashSet<ExactRef> evidence) {
        return new WriterContracts.Request(SavedAttachmentAuthority.KIND, ContinuityJson.canonical(details), List.copyOf(evidence));
    }

    private NativeOutcomeArchive archive() throws IOException {
        Path snapshot = directory.resolve("continuity.json");
        Path anchor = directory.resolve("anchor.json");
        Path lock = Files.createFile(directory.resolve("continuity.lock"));
        Path artifacts = Files.createDirectory(directory.resolve("artifacts"));
        Files.createDirectory(directory.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
        Path trustedSource = Files.writeString(directory.resolve("source.txt"), "software Writer preview fixture");
        var history = reference(artifacts.resolve(DriverJson.sha256(HISTORY) + ".bin"), HISTORY);
        ObjectNode state = StrictJson.object();
        state.put("schema", "root.ck3.continuity-window/v1");
        state.put("machine_id", MACHINE);
        state.put("sequence", 0);
        state.put("window_id", 1);
        state.put("status", "running");
        state.put("target_days", 365);
        state.put("start_date_raw", 1008);
        state.put("target_date_raw", 9768);
        state.put("last_settled_date_raw", 1008);
        state.put("last_settled_cycles", 1);
        state.set(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD, history.toJson());
        byte[] original = ContinuityJson.canonical(state);
        Files.write(snapshot, original);
        Files.write(anchor, original);

        var layout = new WriterContracts.Layout(snapshot, reference(anchor, original), MACHINE);
        var storage = StorageWriteGuardTestSupport.create(layout);
        var store = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(artifacts, lock, 1_048_576), storage);
        var writer = new ContinuityWriter(layout, List.of(reference(trustedSource, Files.readAllBytes(trustedSource))), new WriterContracts.TransitionAuthority() {
            @Override public String revalidate(ContinuityState before, WriterContracts.Request request) {
                return ContinuityJson.digest(request.detailsObject());
            }
            @Override public ContinuityState reduce(ContinuityState before, WriterContracts.Request request) {
                return before;
            }
        }, Clock.systemUTC(), new ContinuityWriter.Extensions(List.of(), Optional.of(store), Optional.empty()), storage);
        return new NativeOutcomeArchive(store, writer);
    }

    private static ExactRef reference(Path path, byte[] bytes) {
        return new ExactRef(path.toString(), bytes.length, DriverJson.sha256(bytes));
    }

    private static byte[] utf8(String text) {
        return text.getBytes(StandardCharsets.UTF_8);
    }
}
