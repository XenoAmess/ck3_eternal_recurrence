package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.jna.Native;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinDef.DWORD;
import java.io.IOException;
import java.math.BigDecimal;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.ImmutableDataPackageInstaller.*;
import org.xar.ck3.control.build.SharedSourceFiles.NativeFile;

/** Actual small opaque packages and Win32 custody; fixtures grant no build/provider/SDK qualification. */
final class ImmutableDataPackageInstallerTest {
    private static final String BLOB = "blobs/" + "a".repeat(64) + ".gz";
    @TempDir Path temporary;
    private record Fixture(SourceIndex index, Request request, FileRef requestRef, Path source, Path data, Path control) {
        ImmutableDataPackageInstaller.CopyPlan plan() { return new ImmutableDataPackageInstaller.CopyPlan(requestRef, request, index); }
    }

    @Test void actualSingleCopyProducerToDurableConsumerKeepsDistinctIdentityAndManifestLast() throws Exception {
        Fixture fixture = fixture("roundtrip");
        byte[] originalIndex = Files.readAllBytes(Path.of(fixture.request().sourceIndexRef().path()));
        Actual actual = ImmutableDataPackageInstaller.copy(fixture.plan(), (data, control) -> { });
        assertEquals("EXACT_DATA_BYTES_AND_NATIVE_READBACK_ONLY", actual.qualification());
        assertEquals(List.of(BLOB, "manifest_v1.json"), actual.files().stream().map(InstalledFile::targetRelative).toList());
        assertEquals(actual, ImmutableDataPackageInstaller.readActual(FileRef.measure(fixture.control().resolve("actual.json"))));
        assertEquals(2, actual.files().size()); assertTrue(actual.manifestCopiedLast());
        assertTrue(actual.dataNativeChargedBytes() > 0); assertTrue(actual.controlNativeChargedBytes() > 4096);
        assertEquals("NOT_RUN", actual.providerSdkGame());
        for (InstalledFile row : actual.files()) {
            assertNotEquals(row.sourceNative().identityKey(), row.destinationNative().identityKey());
            assertEquals(1, row.destinationNative().linkCount());
            assertArrayEquals(Files.readAllBytes(Path.of(row.sourceRef().path())), Files.readAllBytes(Path.of(row.destinationRef().path())));
        }
        assertArrayEquals(originalIndex, Files.readAllBytes(Path.of(fixture.request().sourceIndexRef().path())));
        // Blob filename denotes the opaque manifest's evidence key, not the compressed file's SHA.
        assertNotEquals("a".repeat(64), actual.files().getFirst().sourceRef().sha256());
        Path extra = Files.writeString(fixture.data().resolve("extra.txt"), "extra");
        assertThrows(IOException.class, () -> ImmutableDataPackageInstaller.readActual(FileRef.measure(fixture.control().resolve("actual.json"))));
        assertTrue(Files.exists(extra));
    }

    @Test void exactSourceIndexRejectsUnknownMissingNumericIdentityWrongPrimitiveAndTraversal() throws Exception {
        Fixture fixture = fixture("strict");
        ObjectNode base = ControlBuild.strictMapper().valueToTree(fixture.index());
        List<ObjectNode> bad = new ArrayList<>();
        ObjectNode value = base.deepCopy(); value.put("unknown", 1); bad.add(value);
        value = base.deepCopy(); value.remove("source_directories"); bad.add(value);
        value = base.deepCopy(); value.put("target_exists", "false"); bad.add(value);
        value = base.deepCopy(); ((ObjectNode) value.withArray("files").get(0).get("source_ref")).put("bytes", true); bad.add(value);
        value = base.deepCopy(); ((ObjectNode) value.withArray("files").get(0).get("source_ref")).put("bytes", 1.0); bad.add(value);
        value = base.deepCopy(); ((ObjectNode) value.withArray("files").get(0).get("native_identity")).put("file_id_decimal", 9007199254740993L); bad.add(value);
        value = base.deepCopy(); ((ObjectNode) value.withArray("files").get(0).get("native_identity")).put("file_id_decimal", "01"); bad.add(value);
        value = base.deepCopy(); ((ObjectNode) value.withArray("files").get(0)).put("native_links", 2); bad.add(value);
        value = base.deepCopy(); ((ObjectNode) value.withArray("files").get(0)).put("target_relative", "../manifest_v1.json"); bad.add(value);
        value = base.deepCopy(); ((ObjectNode) value.withArray("files").get(0)).put("target_relative", "MANIFEST_v1.json"); bad.add(value);
        value = base.deepCopy(); value.putNull("retention"); bad.add(value);
        for (int i = 0; i < bad.size(); i++) {
            Path raw = Files.write(temporary.resolve("bad-index-" + i + ".json"), ControlBuild.strictMapper().writeValueAsBytes(bad.get(i)));
            FileRef ref = FileRef.measure(raw);
            assertThrows(IOException.class, () -> ImmutableDataPackageInstaller.readSourceIndex(ref), "strict variant " + i);
        }
        assertFalse(Files.exists(fixture.data())); assertFalse(Files.exists(fixture.control()));
    }

    @Test void heldOriginalMutationAndHashMismatchCannotPublishManifest() throws Exception {
        Fixture fixture = fixture("changed");
        Files.writeString(fixture.source().resolve(BLOB), "replacement same-role content");
        assertThrows(IOException.class, () -> ImmutableDataPackageInstaller.copy(fixture.plan(), (data, control) -> { }));
        assertFalse(Files.exists(fixture.data().resolve("manifest_v1.json")));
        assertFalse(Files.exists(fixture.control().resolve("actual.json")));
        Fixture hash = fixture("wrong-hash");
        var rows = new ArrayList<>(hash.index().files()); SourceFile original = rows.get(1);
        rows.set(1, new SourceFile(original.targetRelative(), new FileRef(original.sourceRef().path(), original.sourceRef().bytes(), "0".repeat(64)),
                original.nativeIdentity(), original.nativeAllocationBytes(), original.nativeLinks()));
        SourceIndex index = withFiles(hash.index(), rows);
        var plan = new ImmutableDataPackageInstaller.CopyPlan(hash.requestRef(), hash.request(), index);
        assertThrows(IOException.class, () -> ImmutableDataPackageInstaller.copy(plan, (data, control) -> { }));
        assertFalse(Files.exists(hash.data().resolve("manifest_v1.json")));
        assertFalse(Files.exists(hash.control().resolve("actual.json")));
    }

    @Test void requestAndIssuerRecordRoundtripRequiresExplicitNullVersionStateAndExactPrimitiveTypes() throws Exception {
        Fixture fixture = fixture("admission-wire"); Request request = fixture.request();
        assertEquals(request, ImmutableDataPackageInstaller.readRequest(fixture.requestRef()));
        List<FileRef> runtime = new ArrayList<>();
        for (int i = 0; i < 6; i++) runtime.add(FileRef.measure(Files.writeString(temporary.resolve("synthetic-runtime-" + i), "fixture " + i)));
        long peak = request.maxDataNativeBytes() + request.maxControlNativeBytes(), gib = 1L << 30;
        // A typed record fixture only: it is never passed to the qualified executable install entry.
        Admission card = new Admission(ImmutableDataPackageInstaller.ADMISSION_SCHEMA,
                AdmissionStatus.RELEASED_SINGLE_COPY_IMMUTABLE_DATA_INSTALL, request.machineId(), request.taskOwner(),
                Instant.now().toString(), request.reviewAtUtc(), request.sourceIndexRef(), request.dataRoot(), request.controlRoot(),
                request.ancestorDirectories(), request.dataDirectoryReserveBytes(), request.maxDataNativeBytes(), request.maxControlNativeBytes(),
                fixture.requestRef(), fixture.data().getRoot().toString(),
                new CiBootstrap.VolumeBudget(1L << 40, 100 * gib, peak, 0, gib, gib, 1L << 20, 1L << 39, peak + 2 * gib),
                null, fixture.requestRef(), fixture.requestRef(), new SharedOwnedCommandBinding.AuthorityExpectation("fixture-not-qualified", "FIXTURE_ONLY"),
                fixture.requestRef(), fixture.requestRef(), runtime);
        byte[] raw = ControlBuild.strictMapper().writeValueAsBytes(card);
        assertEquals(card, ControlBuild.strictMapper().readValue(raw, Admission.class));
        ObjectNode base = (ObjectNode) ControlBuild.strictMapper().readTree(raw);
        assertTrue(base.has("quota_override")); assertTrue(base.get("quota_override").isNull());
        ObjectNode missing = base.deepCopy(); missing.remove("quota_override");
        assertThrows(IOException.class, () -> ControlBuild.strictMapper().treeToValue(missing, Admission.class));
        ObjectNode unknownVersion = base.deepCopy(); unknownVersion.put("schema", "xar.immutable-data.install-admission/v0");
        assertThrows(IOException.class, () -> ControlBuild.strictMapper().treeToValue(unknownVersion, Admission.class));
        ObjectNode unreleased = base.deepCopy(); unreleased.put("status", "FINANCIAL_FUTURE_ONLY");
        assertThrows(IOException.class, () -> ControlBuild.strictMapper().treeToValue(unreleased, Admission.class));
        ObjectNode wrongNumber = base.deepCopy(); wrongNumber.put("max_data_native_bytes", true);
        assertThrows(IOException.class, () -> ControlBuild.strictMapper().treeToValue(wrongNumber, Admission.class));
        ObjectNode wrongRequest = ControlBuild.strictMapper().valueToTree(request); wrongRequest.putNull("admission_ref");
        assertThrows(IOException.class, () -> ControlBuild.strictMapper().treeToValue(wrongRequest, Request.class));
        assertFalse(Files.exists(fixture.data())); assertFalse(Files.exists(fixture.control()));
    }

    @Test void preexistingRootsAndClosedSourceInventoryFailBeforeAnyCopy() throws Exception {
        Fixture existingData = fixture("data-exists"); Files.createDirectory(existingData.data());
        assertThrows(IOException.class, () -> ImmutableDataPackageInstaller.copy(existingData.plan(), (data, control) -> { }));
        assertFalse(Files.exists(existingData.control()));
        Fixture existingControl = fixture("control-exists"); Files.createDirectory(existingControl.control());
        assertThrows(IOException.class, () -> ImmutableDataPackageInstaller.copy(existingControl.plan(), (data, control) -> { }));
        assertFalse(Files.exists(existingControl.data()));
        Fixture extra = fixture("source-extra"); Files.writeString(extra.source().resolve("unexpected"), "not admitted");
        assertThrows(IOException.class, () -> ImmutableDataPackageInstaller.copy(extra.plan(), (data, control) -> { }));
        assertFalse(Files.exists(extra.data())); assertFalse(Files.exists(extra.control()));
    }

    @Test void consumerRejectsSelfAuthorizedSubsetAndAnExactByteSourceOutsideOriginalIndex() throws Exception {
        Fixture subset = fixture("forged-subset");
        ImmutableDataPackageInstaller.copy(subset.plan(), (data, control) -> { });
        Path receipt = subset.control().resolve("actual.json"); ObjectNode actual = (ObjectNode) ControlBuild.strictMapper().readTree(Files.readAllBytes(receipt));
        actual.withArray("files").remove(0); Files.delete(subset.data().resolve(BLOB));
        writeConsistentForgedReceipt(actual, subset);
        IOException omitted = assertThrows(IOException.class, () -> ImmutableDataPackageInstaller.readActual(FileRef.measure(receipt)));
        assertTrue(omitted.getMessage().contains("omitted original package files"), omitted.toString());
        Fixture outside = fixture("forged-outside");
        ImmutableDataPackageInstaller.copy(outside.plan(), (data, control) -> { });
        Path other = Files.write(temporary.resolve("same-bytes-outside-index.gz"), Files.readAllBytes(outside.source().resolve(BLOB)));
        ObjectNode swapped = (ObjectNode) ControlBuild.strictMapper().readTree(Files.readAllBytes(outside.control().resolve("actual.json")));
        ObjectNode row = (ObjectNode) swapped.withArray("files").get(0);
        row.set("source_ref", ControlBuild.strictMapper().valueToTree(FileRef.measure(other)));
        row.set("source_native", ControlBuild.strictMapper().valueToTree(SharedSourceFiles.nativeFile(other)));
        writeConsistentForgedReceipt(swapped, outside);
        IOException crossed = assertThrows(IOException.class, () -> ImmutableDataPackageInstaller.readActual(FileRef.measure(outside.control().resolve("actual.json"))));
        assertTrue(crossed.getMessage().contains("original source mapping differs"), crossed.toString());
    }

    @Test void retainedSourceAndNewDestinationRejectWriteDeleteDuringTheSameCopy() throws Exception {
        Fixture fixture = fixture("custody"); AtomicBoolean exercised = new AtomicBoolean();
        AtomicReference<String> bornIdentity = new AtomicReference<>();
        Actual actual = ImmutableDataPackageInstaller.copy(fixture.plan(), (data, control) -> {
            if (Files.exists(fixture.data().resolve(BLOB)) && exercised.compareAndSet(false, true)) {
                bornIdentity.set(SharedSourceFiles.nativeFile(fixture.data().resolve(BLOB)).identityKey());
                assertThrows(IOException.class, () -> Files.writeString(fixture.source().resolve(BLOB), "mutation"));
                assertThrows(IOException.class, () -> Files.delete(fixture.data().resolve(BLOB)));
                assertFalse(Files.exists(fixture.data().resolve("manifest_v1.json")));
            }
        });
        assertTrue(exercised.get()); assertEquals(2, actual.files().size());
        assertEquals(bornIdentity.get(), actual.files().getFirst().destinationNative().identityKey());
    }

    @Test void standaloneReaderRetainsAllMetadataOriginalsAndDestinationsUntilCompleteVerification() throws Exception {
        Fixture fixture = fixture("reader-custody"); ImmutableDataPackageInstaller.copy(fixture.plan(), (data, control) -> { });
        AtomicBoolean exercised = new AtomicBoolean(); Path receipt = fixture.control().resolve("actual.json");
        Actual actual = ImmutableDataPackageInstaller.readActual(FileRef.measure(receipt), () -> {
            exercised.set(true);
            assertThrows(IOException.class, () -> Files.writeString(fixture.source().resolve(BLOB), "between-row source mutation"));
            assertThrows(IOException.class, () -> Files.writeString(fixture.data().resolve(BLOB), "between-row destination mutation"));
            assertThrows(IOException.class, () -> Files.delete(fixture.data().resolve("manifest_v1.json")));
            assertThrows(IOException.class, () -> Files.writeString(receipt, "between-row receipt mutation"));
            assertThrows(IOException.class, () -> Files.writeString(Path.of(fixture.request().sourceIndexRef().path()), "between-row index mutation"));
        });
        assertTrue(exercised.get()); assertEquals(2, actual.files().size());
    }

    @Test void capacityFailureAfterPayloadClosesCustodyAndLeavesNoManifestOrPassReceipt() throws Exception {
        Fixture fixture = fixture("capacity-failure");
        assertThrows(IOException.class, () -> ImmutableDataPackageInstaller.copy(fixture.plan(), (data, control) -> {
            if (Files.exists(fixture.data().resolve(BLOB))) throw new IOException("actual finite output guard rejected");
        }));
        assertTrue(Files.exists(fixture.data().resolve(BLOB)));
        assertFalse(Files.exists(fixture.data().resolve("manifest_v1.json")));
        assertFalse(Files.exists(fixture.control().resolve("actual.json")));
        // The failed core released every held original; no permanent custody leak.
        Files.writeString(fixture.source().resolve(BLOB), "source may be changed after failure");
    }

    @Test void deadlineAndMissingQualifiedAdmissionNeverStartCopy() throws Exception {
        Fixture fixture = fixture("deadline"); Request good = fixture.request();
        Request expired = new Request(good.schema(), good.machineId(), good.taskOwner(), good.reviewAtUtc(), Instant.now().minusSeconds(1).toString(),
                good.sourceIndexRef(), good.admissionRef(), good.dataRoot(), good.controlRoot(), good.ancestorDirectories(),
                good.dataDirectoryReserveBytes(), good.maxDataNativeBytes(), good.maxControlNativeBytes());
        assertThrows(IOException.class, () -> ImmutableDataPackageInstaller.copy(new ImmutableDataPackageInstaller.CopyPlan(fixture.requestRef(), expired, fixture.index()), (data, control) -> { }));
        assertThrows(IOException.class, () -> ImmutableDataPackageInstaller.install(fixture.requestRef()));
        assertFalse(Files.exists(fixture.data())); assertFalse(Files.exists(fixture.control()));
    }

    @Test void exactAllocationRemainsBoundedWhileWriterAndAllReadCustodyHandlesAreStillOpen() throws Exception {
        byte[] payload = new byte[1_310_721];
        for (int i = 0; i < payload.length; i++) payload[i] = (byte) (i * 31);
        Fixture fixture = fixture("live-held-allocation", payload);
        List<AllocationSample> samples = new ArrayList<>();
        Actual actual = ImmutableDataPackageInstaller.copy(fixture.plan(), (data, control) -> {
            assertTrue(data <= fixture.request().maxDataNativeBytes());
            assertTrue(control <= fixture.request().maxControlNativeBytes());
        }, samples::add);
        List<AllocationSample> blob = samples.stream().filter(s -> s.target().equals(fixture.data().resolve(BLOB))).toList();
        assertEquals(List.of(AllocationPhase.PREALLOCATED, AllocationPhase.STREAMED_WRITER_HELD, AllocationPhase.READBACK_READER_HELD),
                blob.stream().map(AllocationSample::phase).toList());
        long cluster = NativeStorageGeometry.read(fixture.data()).clusterBytes();
        long forecast = ((payload.length + cluster - 1) / cluster) * cluster;
        assertEquals(0, blob.getFirst().actual().logicalBytes());
        String identity = blob.getFirst().actual().identityKey();
        for (AllocationSample sample : blob) {
            assertEquals(identity, sample.actual().identityKey());
            assertEquals(1, sample.actual().linkCount());
            assertTrue(sample.actual().allocatedBytes() <= forecast, sample.toString());
            if (sample.phase() != AllocationPhase.PREALLOCATED) assertEquals(payload.length, sample.actual().logicalBytes());
            writeAllocationObservation(sample.phase().name(), sample.target(), sample.actual(), forecast);
        }
        // copy() has now closed its final reader. The result must already have satisfied
        // the same bound at both earlier live stages, rather than relying on this cleanup.
        NativeFile afterLastClose = SharedSourceFiles.nativeFile(fixture.data().resolve(BLOB));
        writeAllocationObservation("AFTER_LAST_CLOSE_REOPEN", fixture.data().resolve(BLOB), afterLastClose, forecast);
        assertEquals(blob.getLast().actual(), afterLastClose);
        assertEquals(payload.length, afterLastClose.logicalBytes());
        assertTrue(afterLastClose.allocatedBytes() <= forecast);
        assertArrayEquals(payload, Files.readAllBytes(fixture.data().resolve(BLOB)));
        assertEquals(actual, ImmutableDataPackageInstaller.readActual(FileRef.measure(fixture.control().resolve("actual.json"))));
        assertEquals(2, actual.files().size()); assertTrue(actual.manifestCopiedLast());
    }

    @Test void exactEofAndAllocationAtNativeClusterAndStreamingEdgesSurviveColdConsumer() throws Exception {
        long cluster = NativeStorageGeometry.read(temporary.toAbsolutePath().normalize()).clusterBytes();
        var empty = assertThrows(IllegalArgumentException.class, () -> fixture("empty-rejected", new byte[0]));
        assertEquals("finite opaque input extent required", empty.getMessage());
        List<Integer> sizes = java.util.stream.Stream.of(1, Math.toIntExact(cluster - 1), Math.toIntExact(cluster),
                Math.toIntExact(cluster + 1), 65535, 65536, 65537).distinct().toList();
        for (int size : sizes) {
            byte[] bytes = new byte[size]; java.util.Arrays.fill(bytes, (byte) 91);
            Fixture fixture = fixture("exact-edge-" + size, bytes);
            List<AllocationSample> live = new ArrayList<>();
            Actual actual = ImmutableDataPackageInstaller.copy(fixture.plan(), (data, control) -> {
                assertTrue(data <= fixture.request().maxDataNativeBytes()); assertTrue(control <= fixture.request().maxControlNativeBytes());
            }, live::add);
            long forecast = ((size + cluster - 1) / cluster) * cluster;
            for (AllocationSample sample : live) if (sample.target().equals(fixture.data().resolve(BLOB))) {
                assertTrue(sample.actual().allocatedBytes() <= forecast);
                if (sample.phase() != AllocationPhase.PREALLOCATED) assertEquals(size, sample.actual().logicalBytes());
            }
            NativeFile reopened = SharedSourceFiles.nativeFile(fixture.data().resolve(BLOB));
            assertEquals(size, reopened.logicalBytes()); assertTrue(reopened.allocatedBytes() <= forecast);
            assertArrayEquals(bytes, Files.readAllBytes(fixture.data().resolve(BLOB)));
            assertEquals(actual, ImmutableDataPackageInstaller.readActual(FileRef.measure(fixture.control().resolve("actual.json"))));
        }
    }

    @Test void actualRetainedEmptyDirectoryDeniesRenameUntilItsProductionHandleCloses() throws Exception {
        Path path = Files.createDirectory(temporary.resolve("isolated-directory-custody"));
        NativeFile before = directory(path);
        try (var held = ImmutableDataPackageInstaller.Held.open(path, true, false)) {
            assertEquals(before.identityKey(), held.actual().identityKey());
            assertRenameDenied(path);
            held.reopenMatches();
        }
        assertMovedAndRestored(path);
        assertEquals(before.identityKey(), directory(path).identityKey());
    }

    @Test void copyAndColdConsumerRetainDirectoryCustodyAndReleaseEveryHandleOnExit() throws Exception {
        Fixture fixture = fixture("directory-custody-copy");
        AtomicBoolean observed = new AtomicBoolean();
        Actual actual = ImmutableDataPackageInstaller.copy(fixture.plan(), (data, control) -> {
            assertTrue(data <= fixture.request().maxDataNativeBytes());
            assertTrue(control <= fixture.request().maxControlNativeBytes());
        }, sample -> {
            if (sample.phase() == AllocationPhase.PREALLOCATED && observed.compareAndSet(false, true)) {
                // No child is open in the still-empty control directory. A file handle in
                // another directory cannot accidentally make this a passing custody test.
                try (var entries = Files.list(fixture.control())) { assertEquals(0, entries.count()); }
                assertRenameDenied(fixture.control());
            }
        });
        assertTrue(observed.get());
        AtomicBoolean read = new AtomicBoolean();
        assertEquals(actual, ImmutableDataPackageInstaller.readActual(FileRef.measure(fixture.control().resolve("actual.json")), () -> {
            assertRenameDenied(fixture.source());
            assertRenameDenied(fixture.data());
            assertRenameDenied(fixture.control());
            read.set(true);
        }));
        assertTrue(read.get());
        assertEquals(actual, ImmutableDataPackageInstaller.readActual(FileRef.measure(fixture.control().resolve("actual.json"))));
        assertMovedAndRestored(fixture.source());
        assertMovedAndRestored(fixture.data());
        assertMovedAndRestored(fixture.control());
        assertEquals("installed directory witness drifted", assertThrows(IOException.class,
                () -> ImmutableDataPackageInstaller.readActual(FileRef.measure(fixture.control().resolve("actual.json")))).getMessage());
    }

    @Test void attributeOnlyFileObservationDoesNotPretendToGrantDeleteOrContentCustody() throws Exception {
        Path path = temporary.resolve("attribute-only-file");
        Files.writeString(path, "metadata-only observation");
        NativeFile before = SharedSourceFiles.nativeFile(path);
        // No production retained source/destination/metadata file uses this read=false
        // branch. Unlike read=true it requests attributes only and is not a custody grant.
        try (var observed = ImmutableDataPackageInstaller.Held.open(path, false, false)) {
            assertMovedAndRestored(path);
            observed.reopenMatches();
            assertEquals(before.identityKey(), observed.actual().identityKey());
        }
        assertEquals("metadata-only observation", Files.readString(path));
    }

    private Path checkedRenameTarget(Path original) {
        Path root = temporary.toAbsolutePath().normalize(), source = original.toAbsolutePath().normalize();
        Path target = source.resolveSibling(source.getFileName() + ".rename-probe");
        assertTrue(source.startsWith(root) && !source.equals(root) && target.startsWith(root));
        assertEquals(source.getRoot(), target.getRoot());
        assertFalse(Files.exists(target));
        return target;
    }
    private void assertRenameDenied(Path original) throws IOException {
        Path target = checkedRenameTarget(original);
        Native.setLastError(0);
        boolean moved = Kernel32.INSTANCE.MoveFileEx(SharedSourceFiles.nativePath(original), SharedSourceFiles.nativePath(target), new DWORD(0));
        int error = Native.getLastError();
        if (moved) {
            boolean restored = Kernel32.INSTANCE.MoveFileEx(SharedSourceFiles.nativePath(target), SharedSourceFiles.nativePath(original), new DWORD(0));
            assertTrue(restored, "unexpected rename must restore this self-owned fixture before reporting failure");
        }
        writeDirectoryCustodyObservation("RETAINED_RENAME_PROBE", original, moved, error);
        assertFalse(moved, "actual retained directory must deny DELETE/rename access");
        assertEquals(32, error, "expected actual ERROR_SHARING_VIOLATION");
        assertTrue(Files.exists(original)); assertFalse(Files.exists(target));
    }
    private void assertMovedAndRestored(Path original) throws IOException {
        Path target = checkedRenameTarget(original);
        Native.setLastError(0);
        boolean moved = Kernel32.INSTANCE.MoveFileEx(SharedSourceFiles.nativePath(original), SharedSourceFiles.nativePath(target), new DWORD(0));
        int error = Native.getLastError();
        assertTrue(moved, "self-owned fixture rename should be available when no custody is claimed; error=" + error);
        boolean restored = Kernel32.INSTANCE.MoveFileEx(SharedSourceFiles.nativePath(target), SharedSourceFiles.nativePath(original), new DWORD(0));
        assertTrue(restored, "self-owned fixture rename must restore its original path");
        writeDirectoryCustodyObservation("RENAME_RELEASED_OR_ATTRIBUTES_ONLY", original, moved, error);
        assertTrue(Files.exists(original)); assertFalse(Files.exists(target));
    }
    private void writeDirectoryCustodyObservation(String phase, Path target, boolean moved, int error) throws IOException {
        ObjectNode row = ControlBuild.strictMapper().createObjectNode();
        row.put("schema", "xar.immutable-data.actual-sharing-regression/v1");
        row.put("machine_id", WindowsJobProcess.currentMachineId()); row.put("observed_at_utc", Instant.now().toString());
        row.put("phase", phase); row.put("target", target.toString()); row.put("rename_returned", moved); row.put("win32_error", error);
        NativeFile actual = Files.isDirectory(target) ? directory(target) : SharedSourceFiles.nativeFile(target);
        row.set("actual_native", ControlBuild.strictMapper().valueToTree(actual));
        System.out.println(ControlBuild.strictMapper().writeValueAsString(row));
    }

    private void writeAllocationObservation(String phase, Path target, NativeFile actual, long forecast) throws Exception {
        ObjectNode row = ControlBuild.strictMapper().createObjectNode(); row.put("schema", "xar.immutable-data.actual-allocation-regression/v1");
        row.put("machine_id", WindowsJobProcess.currentMachineId()); row.put("observed_at_utc", Instant.now().toString());
        row.put("phase", phase); row.put("target", target.toString()); row.put("maximum_cluster_rounded_allocation_bytes", forecast);
        row.set("actual_native", ControlBuild.strictMapper().valueToTree(actual));
        System.out.println(ControlBuild.strictMapper().writeValueAsString(row));
    }

    private Fixture fixture(String label) throws Exception {
        return fixture(label, new byte[]{31, (byte) 139, 8, 1, 2, 3, 4, 5});
    }
    private Fixture fixture(String label, byte[] payload) throws Exception {
        Path root = Files.createDirectory(temporary.resolve(label)); Path source = Files.createDirectory(root.resolve("source"));
        Files.createDirectory(source.resolve("blobs")); Files.writeString(source.resolve("manifest_v1.json"), "{\"opaque_fixture\":true}\n");
        Files.write(source.resolve(BLOB), payload);
        Path data = root.resolve("installed"), control = root.resolve("control");
        List<SourceFile> rows = new ArrayList<>(); long logical = 0, allocated = 0;
        for (String name : List.of("manifest_v1.json", BLOB)) {
            FileRef pin = FileRef.measure(source.resolve(name)); NativeFile nativeFile = SharedSourceFiles.nativeFile(source.resolve(name));
            rows.add(new SourceFile(name, pin, new NativeIdentity(nativeFile.volumeSerialDecimal(), nativeFile.fileIdDecimal(),
                    nativeFile.creationFiletimeDecimal(), nativeFile.lastWriteFiletimeDecimal()), nativeFile.allocatedBytes(), nativeFile.linkCount()));
            logical += pin.bytes(); allocated += nativeFile.allocatedBytes();
        }
        List<SourceDirectory> dirs = new ArrayList<>(); long directoryAllocated = 0;
        for (Path path : List.of(source, source.resolve("blobs"))) {
            NativeFile nativeFile = directory(path); directoryAllocated += nativeFile.allocatedBytes();
            dirs.add(new SourceDirectory(path.toString(), new DirectoryObservation(nativeFile.volumeSerialDecimal(), nativeFile.fileIdDecimal(),
                    nativeFile.creationFiletimeDecimal(), nativeFile.lastWriteFiletimeDecimal(), nativeFile.logicalBytes(), nativeFile.allocatedBytes(), nativeFile.linkCount(), true)));
        }
        String machine = WindowsJobProcess.currentMachineId(), now = Instant.now().toString();
        SourceIndex index = new SourceIndex(ImmutableDataPackageInstaller.INDEX_SCHEMA, machine, now,
                "SOURCE_BYTES_AND_NATIVE_IDENTITY_READBACK_ONLY_NOT_DEPLOYED", Path.of(System.getProperty("java.home"), "bin/java.exe").toString(),
                "Win32 FileIdInfo(18) little-endian u128+FileBasicInfo(0) FILETIME canonical-decimal; FileStandardInfo(1) actual AllocationSize",
                source.toString(), dirs, volume(source), volume(data), data.toString(), control.toString(), false, false,
                rows, new Totals(2, logical, allocated, directoryAllocated, 2, 0, 0), BigDecimal.ZERO,
                new Retention("derived", Instant.now().plusSeconds(600).toString(), false));
        Path indexPath = Files.write(root.resolve("source-index.json"), ControlBuild.strictMapper().writeValueAsBytes(index));
        // Structurally complete synthetic card; its source-index pin is deliberately not a qualified build.
        // The public install test proves that this mechanical fixture cannot acquire execution authority.
        FileRef indexRef = FileRef.measure(indexPath); String review = Instant.now().plusSeconds(600).toString();
        List<FileRef> runtime = new ArrayList<>();
        for (int i = 0; i < 6; i++) runtime.add(FileRef.measure(Files.writeString(root.resolve("runtime-fixture-" + i), "synthetic " + i)));
        Volume geometry = volume(data); long cluster = geometry.clusterBytes();
        long dataCap = Math.max(2L << 20, ((payload.length + cluster - 1) / cluster) * cluster
                + ((rows.getFirst().sourceRef().bytes() + cluster - 1) / cluster) * cluster + (256L << 10));
        long controlCap = Math.max(2L << 20, 2 * cluster);
        long gib = 1L << 30, peak = dataCap + controlCap;
        Admission card = new Admission(ImmutableDataPackageInstaller.ADMISSION_SCHEMA,
                AdmissionStatus.RELEASED_SINGLE_COPY_IMMUTABLE_DATA_INSTALL, machine, "/root/fixture", now, review,
                indexRef, data.toString(), control.toString(), List.of(), 256L << 10, dataCap, controlCap,
                indexRef, data.getRoot().toString(), new CiBootstrap.VolumeBudget(1L << 40, 100 * gib, peak, 0, gib, gib,
                    1L << 20, 1L << 39, peak + 2 * gib), null, indexRef, indexRef,
                new SharedOwnedCommandBinding.AuthorityExpectation("fixture-not-qualified", "FIXTURE_ONLY"), indexRef, indexRef, runtime);
        FileRef syntheticCard = FileRef.measure(Files.write(root.resolve("synthetic-admission.json"), ControlBuild.strictMapper().writeValueAsBytes(card)));
        Request request = new Request(ImmutableDataPackageInstaller.REQUEST_SCHEMA, machine, "/root/fixture", review,
                Instant.now().plusSeconds(120).toString(), indexRef, syntheticCard, data.toString(), control.toString(), List.of(),
                256L << 10, dataCap, controlCap);
        FileRef requestRef = FileRef.measure(Files.write(root.resolve("request.json"), ControlBuild.strictMapper().writeValueAsBytes(request)));
        return new Fixture(index, request, requestRef, source, data, control);
    }

    private SourceIndex withFiles(SourceIndex source, List<SourceFile> files) {
        return new SourceIndex(source.schema(), source.machineId(), source.observedAtUtc(), source.status(), source.probeInterpreter(), source.identitySchema(),
                source.sourceRoot(), source.sourceDirectories(), source.sourceVolume(), source.targetVolume(), source.targetRootCandidate(), source.controlRootCandidate(),
                source.targetExists(), source.controlExists(), files, source.totals(), source.elapsedSeconds(), source.retention());
    }
    /** Build a genuinely self-consistent forged subset so the original-index check is the rejecting boundary. */
    private void writeConsistentForgedReceipt(ObjectNode actual, Fixture fixture) throws Exception {
        long dataCharge = 0;
        for (var item : actual.withArray("files")) {
            ObjectNode row = (ObjectNode) item; Path destination = Path.of(row.get("destination_ref").get("path").textValue());
            NativeFile current = SharedSourceFiles.nativeFile(destination); row.set("destination_native", ControlBuild.strictMapper().valueToTree(current));
            dataCharge += current.allocatedBytes();
        }
        for (var item : actual.withArray("directories")) {
            ObjectNode row = (ObjectNode) item; NativeFile current = directory(Path.of(row.get("path").textValue()));
            row.set("native_observation", ControlBuild.strictMapper().valueToTree(current)); dataCharge += Math.max(4096, current.allocatedBytes());
        }
        actual.put("data_native_charged_bytes", dataCharge); Path receipt = fixture.control().resolve("actual.json");
        for (int pass = 0; pass < 4; pass++) {
            long charge = Math.max(4096, directory(fixture.control()).allocatedBytes()) + SharedSourceFiles.nativeFile(receipt).allocatedBytes();
            actual.put("control_native_charged_bytes", charge); Files.write(receipt, ControlBuild.strictMapper().writeValueAsBytes(actual));
            if (Math.max(4096, directory(fixture.control()).allocatedBytes()) + SharedSourceFiles.nativeFile(receipt).allocatedBytes() == charge) return;
        }
        fail("fixture forged receipt allocation did not stabilize");
    }
    private NativeFile directory(Path path) throws IOException {
        var handle = Kernel32.INSTANCE.CreateFile(SharedSourceFiles.nativePath(path), 0x80, 3, null, 3, 0x02200000, null);
        assertNotEquals(WinBase.INVALID_HANDLE_VALUE, handle);
        try { return SharedSourceFiles.nativeHeldDirectory(handle); }
        finally { assertTrue(Kernel32.INSTANCE.CloseHandle(handle)); }
    }
    private Volume volume(Path path) throws IOException {
        NativeStorageGeometry.Volume actual = NativeStorageGeometry.read(path.toAbsolutePath().normalize());
        return new Volume(actual.root().toString(), actual.sectorsPerCluster(), actual.bytesPerSector(), actual.clusterBytes());
    }
}
