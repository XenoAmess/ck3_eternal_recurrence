package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinDef.DWORDByReference;
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

    private Fixture fixture(String label) throws Exception {
        Path root = Files.createDirectory(temporary.resolve(label)); Path source = Files.createDirectory(root.resolve("source"));
        Files.createDirectory(source.resolve("blobs")); Files.writeString(source.resolve("manifest_v1.json"), "{\"opaque_fixture\":true}\n");
        Files.write(source.resolve(BLOB), new byte[]{31, (byte) 139, 8, 1, 2, 3, 4, 5});
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
        long gib = 1L << 30, peak = 4L << 20;
        Admission card = new Admission(ImmutableDataPackageInstaller.ADMISSION_SCHEMA,
                AdmissionStatus.RELEASED_SINGLE_COPY_IMMUTABLE_DATA_INSTALL, machine, "/root/fixture", now, review,
                indexRef, data.toString(), control.toString(), List.of(), 256L << 10, 2L << 20, 2L << 20,
                indexRef, data.getRoot().toString(), new CiBootstrap.VolumeBudget(1L << 40, 100 * gib, peak, 0, gib, gib,
                    1L << 20, 1L << 39, peak + 2 * gib), null, indexRef, indexRef,
                new SharedOwnedCommandBinding.AuthorityExpectation("fixture-not-qualified", "FIXTURE_ONLY"), indexRef, indexRef, runtime);
        FileRef syntheticCard = FileRef.measure(Files.write(root.resolve("synthetic-admission.json"), ControlBuild.strictMapper().writeValueAsBytes(card)));
        Request request = new Request(ImmutableDataPackageInstaller.REQUEST_SCHEMA, machine, "/root/fixture", review,
                Instant.now().plusSeconds(120).toString(), indexRef, syntheticCard, data.toString(), control.toString(), List.of(),
                256L << 10, 2L << 20, 2L << 20);
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
    private Volume volume(Path path) {
        DWORDByReference sectors = new DWORDByReference(), bytes = new DWORDByReference(), free = new DWORDByReference(), total = new DWORDByReference();
        assertTrue(Kernel32.INSTANCE.GetDiskFreeSpace(path.getRoot().toString(), sectors, bytes, free, total));
        long sectorCount = sectors.getValue().longValue(), byteCount = bytes.getValue().longValue();
        return new Volume(path.getRoot().toString(), sectorCount, byteCount, Math.multiplyExact(sectorCount, byteCount));
    }
}
