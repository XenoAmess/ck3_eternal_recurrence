package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinDef.DWORD;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.ptr.IntByReference;
import com.sun.jna.ptr.LongByReference;
import com.sun.jna.win32.StdCallLibrary;
import java.io.IOException;
import java.io.InterruptedIOException;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles.NativeFile;

/** One create-only opaque DATA copy. It does not decompress data or grant provider/SDK/Game acceptance. */
public final class ImmutableDataPackageInstaller {
    public static final String REQUEST_SCHEMA = "xar.immutable-data.install-request/v1";
    public static final String ADMISSION_SCHEMA = "xar.immutable-data.install-admission/v1";
    public static final String ACTUAL_SCHEMA = "xar.immutable-data.install-actual/v1";
    public static final String INDEX_SCHEMA = "xar.portable-evidence.exact-data-source-refs/v1";
    private static final String IDENTITY_SCHEMA = "Win32 FileIdInfo(18) little-endian u128+FileBasicInfo(0) FILETIME canonical-decimal; FileStandardInfo(1) actual AllocationSize";
    private static final int JSON_LIMIT = 2 << 20, RECEIPT_LIMIT = 1 << 20;
    private static final long DATA_LIMIT = 64L << 20, CONTROL_LIMIT = 4L << 20;
    public interface FilePositionApi extends StdCallLibrary {
        boolean SetFilePointerEx(HANDLE file, long distance, LongByReference newPosition, int method);
        boolean SetEndOfFile(HANDLE file);
    }
    private static final class PositionApi { private static final FilePositionApi VALUE = Native.load("kernel32", FilePositionApi.class); }
    private ImmutableDataPackageInstaller() { }

    public record NativeIdentity(String volumeSerialDecimal, String fileIdDecimal,
                                 String creationFiletimeDecimal, String modifiedFiletimeDecimal) {
        public NativeIdentity {
            decimal(volumeSerialDecimal, 64); decimal(fileIdDecimal, 128);
            decimal(creationFiletimeDecimal, 64); decimal(modifiedFiletimeDecimal, 64);
        }
        String identityKey() { return volumeSerialDecimal + ":" + fileIdDecimal + ":" + creationFiletimeDecimal; }
        boolean matches(NativeFile actual) {
            return identityKey().equals(actual.identityKey()) && modifiedFiletimeDecimal.equals(actual.lastWriteFiletimeDecimal());
        }
    }
    public record SourceFile(String targetRelative, FileRef sourceRef, NativeIdentity nativeIdentity,
                             long nativeAllocationBytes, long nativeLinks) {
        public SourceFile {
            relative(targetRelative); Objects.requireNonNull(sourceRef); Objects.requireNonNull(nativeIdentity);
            require(sourceRef.bytes() > 0 && sourceRef.bytes() <= (targetRelative.equals("manifest_v1.json") ? 2L << 20 : 8L << 20), "finite opaque input extent required");
            require(nativeAllocationBytes >= 0 && nativeLinks == 1, "private ordinary source file required");
        }
    }
    public record DirectoryObservation(String volumeSerialDecimal, String fileIdDecimal,
            String creationFiletimeDecimal, String modifiedFiletimeDecimal, long bytes,
            long allocationBytes, long links, boolean directory) {
        public DirectoryObservation {
            new NativeIdentity(volumeSerialDecimal, fileIdDecimal, creationFiletimeDecimal, modifiedFiletimeDecimal);
            require(bytes >= 0 && allocationBytes >= 0 && links > 0 && directory, "actual ordinary directory facts required");
        }
        boolean matches(NativeFile actual) {
            return new NativeIdentity(volumeSerialDecimal, fileIdDecimal, creationFiletimeDecimal, modifiedFiletimeDecimal).matches(actual)
                    && bytes == actual.logicalBytes() && allocationBytes == actual.allocatedBytes() && links == actual.linkCount();
        }
    }
    public record SourceDirectory(String path, DirectoryObservation nativeObservation) {
        public SourceDirectory { absolute(path); Objects.requireNonNull(nativeObservation); }
    }
    public record Volume(String volumeRoot, long sectorsPerCluster, long bytesPerSector, long clusterBytes) {
        public Volume {
            Path root = absolute(volumeRoot);
            require(root.equals(root.getRoot()) && sectorsPerCluster > 0 && bytesPerSector > 0
                    && clusterBytes == Math.multiplyExact(sectorsPerCluster, bytesPerSector)
                    && clusterBytes >= 512 && clusterBytes <= (2L << 20), "actual finite native cluster geometry required");
        }
    }
    public record Totals(int files, long logicalBytes, long nativeFileAllocationBytes,
                         long nativeDirectoryAllocationBytes, int distinctNativeIds,
                         int newPayloadCopies, long physicalReleaseCreditBytes) {
        public Totals {
            require(files > 0 && files <= 4096 && logicalBytes > 0 && logicalBytes <= DATA_LIMIT
                    && nativeFileAllocationBytes >= 0 && nativeDirectoryAllocationBytes >= 0
                    && distinctNativeIds == files && newPayloadCopies == 0 && physicalReleaseCreditBytes == 0,
                    "complete source-only totals without release credit required");
        }
    }
    public record Retention(String category, String reviewAtUtc, boolean automaticRenewal) {
        public Retention { require("derived".equals(category) && !automaticRenewal, "finite derived retention required"); Instant.parse(reviewAtUtc); }
    }
    /** Exact original observation schema, including its historical probe fact; no interpreter is executed. */
    public record SourceIndex(String schema, String machineId, String observedAtUtc, String status,
            String probeInterpreter, String identitySchema, String sourceRoot, List<SourceDirectory> sourceDirectories,
            Volume sourceVolume, Volume targetVolume, String targetRootCandidate, String controlRootCandidate,
            boolean targetExists, boolean controlExists, List<SourceFile> files, Totals totals,
            BigDecimal elapsedSeconds, Retention retention) {
        public SourceIndex {
            require(INDEX_SCHEMA.equals(schema) && "SOURCE_BYTES_AND_NATIVE_IDENTITY_READBACK_ONLY_NOT_DEPLOYED".equals(status)
                    && IDENTITY_SCHEMA.equals(identitySchema), "unknown DATA source observation contract");
            machine(machineId); Instant.parse(observedAtUtc); absolute(probeInterpreter);
            Path source = absolute(sourceRoot); absolute(targetRootCandidate); absolute(controlRootCandidate);
            Objects.requireNonNull(sourceVolume); Objects.requireNonNull(targetVolume); Objects.requireNonNull(totals); Objects.requireNonNull(retention);
            require(source.getRoot().equals(absolute(sourceVolume.volumeRoot())) && !targetExists && !controlExists
                    && elapsedSeconds != null && elapsedSeconds.signum() >= 0, "source-only fresh candidates required");
            sourceDirectories = List.copyOf(sourceDirectories); files = List.copyOf(files);
            require(sourceDirectories.size() == 2 && absolute(sourceDirectories.get(0).path()).equals(source)
                    && absolute(sourceDirectories.get(1).path()).equals(source.resolve("blobs")), "exact root/blobs directory closure required");
            Set<String> names = new HashSet<>(), identities = new HashSet<>(); long logical = 0, allocated = 0, directoryBytes = 0;
            for (SourceFile row : files) {
                require(names.add(row.targetRelative()) && identities.add(row.nativeIdentity().identityKey())
                        && absolute(row.sourceRef().path()).equals(source.resolve(row.targetRelative()).normalize()), "unique exact source path/native identity required");
                logical = Math.addExact(logical, row.sourceRef().bytes()); allocated = Math.addExact(allocated, row.nativeAllocationBytes());
            }
            for (SourceDirectory row : sourceDirectories) directoryBytes = Math.addExact(directoryBytes, row.nativeObservation().allocationBytes());
            require(names.contains("manifest_v1.json") && names.size() == totals.files() && logical == totals.logicalBytes()
                    && allocated == totals.nativeFileAllocationBytes() && directoryBytes == totals.nativeDirectoryAllocationBytes(), "closed source totals differ");
        }
    }
    public record Request(String schema, String machineId, String taskOwner, String reviewAtUtc, String deadlineUtc,
            FileRef sourceIndexRef, FileRef admissionRef, String dataRoot, String controlRoot,
            List<String> ancestorDirectories, long dataDirectoryReserveBytes, long maxDataNativeBytes, long maxControlNativeBytes) {
        public Request {
            require(REQUEST_SCHEMA.equals(schema), "unknown install request"); machine(machineId); owner(taskOwner);
            Instant review = Instant.parse(reviewAtUtc), deadline = Instant.parse(deadlineUtc);
            require(!deadline.isAfter(review), "one work deadline inside admission review required");
            Objects.requireNonNull(sourceIndexRef); Objects.requireNonNull(admissionRef);
            ancestorDirectories = List.copyOf(ancestorDirectories);
            validateDestinations(dataRoot, controlRoot, ancestorDirectories);
            require(maxDataNativeBytes > 0 && maxDataNativeBytes <= DATA_LIMIT
                    && dataDirectoryReserveBytes >= Math.multiplyExact(ancestorsCount(ancestorDirectories), 4096L)
                    && dataDirectoryReserveBytes < maxDataNativeBytes
                    && maxControlNativeBytes >= RECEIPT_LIMIT + 4096L && maxControlNativeBytes <= CONTROL_LIMIT, "finite native DATA/control ceilings required");
        }
    }
    /** Issuer-owned operation scope; the financial reservation alone cannot instantiate this authority. */
    public enum AdmissionStatus { RELEASED_SINGLE_COPY_IMMUTABLE_DATA_INSTALL }
    public record Admission(String schema, AdmissionStatus status, String machineId, String ownerTask, String observedAtUtc, String reviewAtUtc,
            FileRef sourceIndexRef, String dataRoot, String controlRoot, List<String> ancestorDirectories,
            long dataDirectoryReserveBytes, long maxDataNativeBytes, long maxControlNativeBytes, FileRef policyRef, String volumeRoot,
            CiBootstrap.VolumeBudget volumeBudget, CiBootstrap.QuotaOverride quotaOverride,
            FileRef wholeBuildReceiptRef, FileRef deliveryRef, SharedOwnedCommandBinding.AuthorityExpectation deliveryExpectation,
            FileRef ownArchiveActualRef, FileRef installerSourceRef, List<FileRef> completeRuntime) {
        public Admission {
            require(ADMISSION_SCHEMA.equals(schema) && status == AdmissionStatus.RELEASED_SINGLE_COPY_IMMUTABLE_DATA_INSTALL, "unknown or unreleased install admission"); machine(machineId); owner(ownerTask);
            require(Instant.parse(observedAtUtc).isBefore(Instant.parse(reviewAtUtc)), "finite issuer observation/review required");
            ancestorDirectories = List.copyOf(ancestorDirectories); completeRuntime = List.copyOf(completeRuntime);
            require(completeRuntime.stream().map(ref -> absolute(ref.path())).distinct().count() == 6, "six distinct runtime files required");
            validateDestinations(dataRoot, controlRoot, ancestorDirectories);
            for (FileRef ref : List.of(sourceIndexRef, policyRef, wholeBuildReceiptRef, deliveryRef, ownArchiveActualRef, installerSourceRef)) Objects.requireNonNull(ref);
            Objects.requireNonNull(volumeBudget); Objects.requireNonNull(deliveryExpectation);
            require(volumeBudget.totalVolumeBytes() > 0 && volumeBudget.availableBytes() >= 0
                    && volumeBudget.availableBytes() <= volumeBudget.totalVolumeBytes() && volumeBudget.otherUnspentReservations() >= 0
                    && volumeBudget.systemGrowthReserve() > 0 && volumeBudget.safetyReserve() > 0
                    && volumeBudget.currentProjectUsageConservativeUpper() >= 0 && volumeBudget.effectiveProjectQuota() > 0
                    && volumeBudget.requiredFree() == Math.addExact(Math.addExact(volumeBudget.thisWritePeak(), volumeBudget.otherUnspentReservations()),
                        Math.addExact(volumeBudget.systemGrowthReserve(), volumeBudget.safetyReserve()))
                    && volumeBudget.availableBytes() >= volumeBudget.requiredFree(), "complete shared-policy issuer capacity observation required");
            require(absolute(volumeRoot).equals(absolute(dataRoot).getRoot()) && completeRuntime.size() == 6
                    && maxDataNativeBytes > 0 && maxDataNativeBytes <= DATA_LIMIT && maxControlNativeBytes >= RECEIPT_LIMIT + 4096L
                    && dataDirectoryReserveBytes >= Math.multiplyExact(ancestorsCount(ancestorDirectories), 4096L)
                    && dataDirectoryReserveBytes < maxDataNativeBytes
                    && maxControlNativeBytes <= CONTROL_LIMIT && volumeBudget.thisWritePeak() == Math.addExact(maxDataNativeBytes, maxControlNativeBytes), "complete single-copy operation capacity required");
        }
    }
    public record InstalledFile(String targetRelative, FileRef sourceRef, NativeFile sourceNative,
                                FileRef destinationRef, NativeFile destinationNative) {
        public InstalledFile {
            relative(targetRelative); Objects.requireNonNull(sourceRef); Objects.requireNonNull(sourceNative);
            Objects.requireNonNull(destinationRef); Objects.requireNonNull(destinationNative);
            require(sourceRef.bytes() == destinationRef.bytes() && sourceRef.sha256().equals(destinationRef.sha256())
                    && sourceRef.bytes() == sourceNative.logicalBytes() && destinationRef.bytes() == destinationNative.logicalBytes()
                    && sourceNative.linkCount() == 1 && destinationNative.linkCount() == 1
                    && !sourceNative.identityKey().equals(destinationNative.identityKey()), "distinct exact private copied file facts required");
        }
    }
    public record InstalledDirectory(String path, NativeFile nativeObservation) {
        public InstalledDirectory { absolute(path); Objects.requireNonNull(nativeObservation); }
    }
    public record Actual(String schema, String machineId, String observedAtUtc, String status,
            String qualification, FileRef requestRef, FileRef sourceIndexRef, FileRef admissionRef,
            String dataRoot, String controlRoot, List<InstalledFile> files, List<InstalledDirectory> directories,
            long dataNativeChargedBytes, long controlNativeChargedBytes, boolean manifestCopiedLast,
            boolean closedSourceInventory, boolean closedDestinationInventory, String providerSdkGame) {
        public Actual {
            require(ACTUAL_SCHEMA.equals(schema) && "PASS".equals(status)
                    && "EXACT_DATA_BYTES_AND_NATIVE_READBACK_ONLY".equals(qualification)
                    && "NOT_RUN".equals(providerSdkGame) && manifestCopiedLast && closedSourceInventory && closedDestinationInventory,
                    "physical DATA copy is the sole acceptance scope");
            machine(machineId); Instant.parse(observedAtUtc); files = List.copyOf(files); directories = List.copyOf(directories);
            Objects.requireNonNull(requestRef); Objects.requireNonNull(sourceIndexRef); Objects.requireNonNull(admissionRef);
            require(!files.isEmpty() && files.size() <= 4096 && files.getLast().targetRelative().equals("manifest_v1.json")
                    && dataNativeChargedBytes >= 0 && controlNativeChargedBytes >= 0, "manifest-last actual charged allocation required");
            Set<String> names = new HashSet<>(), identities = new HashSet<>();
            for (InstalledFile file : files) require(names.add(file.targetRelative()) && identities.add(file.destinationNative().identityKey())
                    && absolute(file.destinationRef().path()).equals(absolute(dataRoot).resolve(file.targetRelative())), "closed exact destination records required");
        }
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 4 || !"install".equals(args[0])) throw new IllegalArgumentException("install <request-path> <request-bytes> <request-sha256> required");
        FileRef ref = new FileRef(absolute(args[1]).toString(), Long.parseLong(args[2]), args[3]);
        install(ref);
    }

    public static Actual install(FileRef requestRef) throws IOException {
        List<Held> metadata = new ArrayList<>(); Throwable failure = null;
        try {
            retainMetadata(requestRef, metadata); Request request = readExact(requestRef, Request.class);
            retainMetadata(request.admissionRef(), metadata); retainMetadata(request.sourceIndexRef(), metadata);
            Admission admission = readExact(request.admissionRef(), Admission.class); SourceIndex index = readExact(request.sourceIndexRef(), SourceIndex.class);
            matchScopes(request, admission, index); qualify(admission);
            if (admission.quotaOverride() != null) {
                var pin = admission.quotaOverride().sourceRef(); FileRef authority = new FileRef(pin.path(), pin.bytes(), pin.sha256());
                retainMetadata(authority, metadata); exactBytes(authority);
            }
            retainMetadata(admission.policyRef(), metadata); CiBootstrap.Policy policy = CiBootstrap.readPolicy(exactBytes(admission.policyRef()));
            Guard guard = new Guard(request, admission, policy); guard.check(0, 0);
            Actual actual = copy(new CopyPlan(requestRef, request, index), guard);
            exactBytes(requestRef); exactBytes(request.sourceIndexRef()); exactBytes(request.admissionRef()); exactBytes(admission.policyRef());
            verifyHeldDirectories(metadata); return actual;
        } catch (IOException | RuntimeException | Error error) { failure = error; throw error; }
        finally { closeAll(metadata, failure); }
    }

    private static void matchScopes(Request request, Admission admission, SourceIndex index) throws IOException {
        if (!request.machineId().equals(WindowsJobProcess.currentMachineId()) || !request.machineId().equals(index.machineId())
                || !request.machineId().equals(admission.machineId()) || !request.taskOwner().equals(admission.ownerTask())
                || !request.sourceIndexRef().equals(admission.sourceIndexRef()) || !samePath(request.dataRoot(), admission.dataRoot())
                || !samePath(request.controlRoot(), admission.controlRoot()) || !request.ancestorDirectories().equals(admission.ancestorDirectories())
                || request.dataDirectoryReserveBytes() != admission.dataDirectoryReserveBytes()
                || request.maxDataNativeBytes() != admission.maxDataNativeBytes() || request.maxControlNativeBytes() != admission.maxControlNativeBytes()
                || Instant.parse(request.reviewAtUtc()).isAfter(Instant.parse(admission.reviewAtUtc()))) throw new IOException("request/issuer/machine scopes differ");
        if (!samePath(request.dataRoot(), index.targetRootCandidate()) || !samePath(request.controlRoot(), index.controlRootCandidate()))
            throw new IOException("original source observation and admitted destinations differ");
    }

    private static void qualify(Admission card) throws IOException {
        var build = ControlBuild.verifiedCompletedReceipt(card.wholeBuildReceiptRef());
        card.installerSourceRef().verify(); card.deliveryRef().verify(); card.ownArchiveActualRef().verify();
        if (!build.completeDeployment().equals(card.completeRuntime()) || !ControlBuild.producerClosure().equals(card.completeRuntime())
                || !build.sourcePins().contains(card.installerSourceRef())
                || !absolute(card.installerSourceRef().path()).getFileName().toString().equals("ImmutableDataPackageInstaller.java")
                || !ImmutableDataPackageInstaller.class.getProtectionDomain().getCodeSource().getLocation().equals(ControlBuild.class.getProtectionDomain().getCodeSource().getLocation()))
            throw new IOException("installer must execute from its complete qualified archive and exact compiled source");
        JsonNode delivery = ControlBuild.strictMapper().readTree(exactBytes(card.deliveryRef()));
        SharedOwnedCommandBinding.verifyAuthority(delivery, card.deliveryExpectation(), card.machineId());
        FileRef whole = ControlBuild.strictMapper().treeToValue(delivery.required("qualified_whole_build_receipt_ref"), FileRef.class);
        FileRef own = ControlBuild.strictMapper().treeToValue(delivery.required("qualified_own_archive_actual_ref"), FileRef.class);
        List<FileRef> runtime = ControlBuild.strictMapper().readerForListOf(FileRef.class).readValue(delivery.required("complete_runtime"));
        JsonNode actual = ControlBuild.strictMapper().readTree(exactBytes(card.ownArchiveActualRef()));
        List<FileRef> readbackRuntime = ControlBuild.strictMapper().readerForListOf(FileRef.class).readValue(actual.required("complete_running_runtime"));
        FileRef readbackWhole = ControlBuild.strictMapper().treeToValue(actual.required("build_receipt_ref"), FileRef.class);
        if (!whole.equals(card.wholeBuildReceiptRef()) || !own.equals(card.ownArchiveActualRef()) || !runtime.equals(card.completeRuntime())
                || !"xar.integrated-tools-accepted-readback/v4".equals(actual.path("schema").textValue())
                || !card.machineId().equals(actual.path("machine_id").textValue()) || !"INTEGRATED_TOOLS_RUNTIME_ONLY".equals(actual.path("scope").textValue())
                || !readbackRuntime.equals(runtime) || !readbackWhole.equals(whole)) throw new IOException("whole build/delivery/own-archive closure differs");
    }

    /** One core used by admitted execution and the persistent small-package native regressions. */
    record CopyPlan(FileRef requestRef, Request request, SourceIndex index) {
        CopyPlan {
            Objects.requireNonNull(requestRef); Objects.requireNonNull(request); Objects.requireNonNull(index);
            require(samePath(request.dataRoot(), index.targetRootCandidate()) && samePath(request.controlRoot(), index.controlRootCandidate()), "observed candidate and requested destinations differ");
            Path source = absolute(index.sourceRoot()), data = absolute(request.dataRoot()), control = absolute(request.controlRoot());
            require(!source.startsWith(data) && !data.startsWith(source) && !source.startsWith(control) && !control.startsWith(source)
                    && data.getRoot().equals(absolute(index.targetVolume().volumeRoot())), "source and output scopes must be disjoint");
        }
    }
    @FunctionalInterface interface CapacityGuard { void check(long dataWritten, long controlWritten) throws IOException; }
    enum AllocationPhase { PREALLOCATED, STREAMED_WRITER_HELD, READBACK_READER_HELD }
    record AllocationSample(AllocationPhase phase, Path target, NativeFile actual) { }
    @FunctionalInterface interface AllocationObserver { void observed(AllocationSample sample) throws IOException; }

    static Actual copy(CopyPlan plan, CapacityGuard guard) throws IOException {
        return copyObserved(plan, guard, Optional.empty());
    }
    static Actual copy(CopyPlan plan, CapacityGuard guard, AllocationObserver observer) throws IOException {
        return copyObserved(plan, guard, Optional.of(Objects.requireNonNull(observer)));
    }
    private static Actual copyObserved(CopyPlan plan, CapacityGuard guard, Optional<AllocationObserver> observer) throws IOException {
        Request request = plan.request(); SourceIndex index = plan.index();
        Path data = absolute(request.dataRoot()), control = absolute(request.controlRoot()), source = absolute(index.sourceRoot());
        List<Held> held = new ArrayList<>(), sources = new ArrayList<>(), outputs = new ArrayList<>(), dataDirectories = new ArrayList<>();
        List<InstalledFile> rows = new ArrayList<>(); Throwable failure = null;
        try {
            checkTime(request); guard.check(0, 0); verifyVolume(index.sourceVolume()); verifyVolume(index.targetVolume());
            requireAbsent(data); requireAbsent(control);
            for (String ancestor : request.ancestorDirectories()) requireAbsent(absolute(ancestor));
            holdExistingAncestors(data, held); holdExistingAncestors(control, held); holdExistingAncestors(source, held);
            for (SourceDirectory directory : index.sourceDirectories()) {
                Held handle = Held.open(absolute(directory.path()), true, false); held.add(handle);
                if (!directory.nativeObservation().matches(handle.initial)) throw new IOException("source directory original native witness changed: " + directory.path());
            }
            closedInventory(source, index.files().stream().map(SourceFile::targetRelative).collect(java.util.stream.Collectors.toSet()));
            Set<String> sourceIdentities = new HashSet<>();
            for (SourceFile row : index.files()) {
                checkTime(request); Held handle = Held.open(absolute(row.sourceRef().path()), false, true); held.add(handle); sources.add(handle);
                assertSource(row, handle.initial); sourceIdentities.add(handle.initial.identityKey());
            }
            long pending = 0;
            for (SourceFile row : index.files()) pending = Math.addExact(pending, rounded(row.sourceRef().bytes(), index.targetVolume().clusterBytes()));
            requireIo(Math.addExact(pending, request.dataDirectoryReserveBytes()) <= request.maxDataNativeBytes()
                    && RECEIPT_LIMIT + 4096L <= request.maxControlNativeBytes(), "finite native output forecasts exceed admitted bounds");
            for (String ancestor : request.ancestorDirectories()) createDirectory(absolute(ancestor), held, dataDirectories);
            createDirectory(data, held, dataDirectories); createDirectory(data.resolve("blobs"), held, dataDirectories);
            createDirectory(control, held, new ArrayList<>());
            Set<String> destinationIdentities = new HashSet<>();
            List<SourceFile> order = index.files().stream().sorted(Comparator.comparing((SourceFile f) -> f.targetRelative().equals("manifest_v1.json")).thenComparing(SourceFile::targetRelative)).toList();
            for (SourceFile row : order) {
                checkTime(request); verifyHeldDirectories(held); guard.check(charge(outputs, dataDirectories), chargeControl(control));
                long current = charge(outputs, List.of());
                long plannedFileAllocation = rounded(row.sourceRef().bytes(), index.targetVolume().clusterBytes());
                requireIo(Math.addExact(Math.addExact(current, request.dataDirectoryReserveBytes()), plannedFileAllocation) <= request.maxDataNativeBytes(),
                        "next single-copy allocation exceeds DATA ceiling: actualHeldFiles=" + current + " reservedDirectories=" + request.dataDirectoryReserveBytes()
                        + " nextRounded=" + plannedFileAllocation + " ceiling=" + request.maxDataNativeBytes());
                Held original = sources.get(index.files().indexOf(row)); assertSource(row, original.actual());
                requireIo(original.initial.equals(original.actual()), "held source metadata changed after acquisition");
                Path target = data.resolve(row.targetRelative());
                Held output = Held.create(target); held.add(output); outputs.add(output);
                reserveCreatedLength(output, row.sourceRef().bytes(), index.targetVolume().clusterBytes());
                observeAllocation(observer, AllocationPhase.PREALLOCATED, output);
                checkCeilings(request, outputs, dataDirectories, control);
                guard.check(charge(outputs, dataDirectories), chargeControl(control));
                copyOne(original, output, row.sourceRef(), request, index.targetVolume().clusterBytes());
                observeAllocation(observer, AllocationPhase.STREAMED_WRITER_HELD, output);
                Readback readback = settleCreated(output, row.sourceRef(), request, held);
                outputs.set(outputs.indexOf(output), readback.custody()); output = readback.custody();
                requireHeldLength(output, row.sourceRef().bytes(), plannedFileAllocation, true);
                observeAllocation(observer, AllocationPhase.READBACK_READER_HELD, output);
                FileRef destination = readback.exactRef();
                if (!destination.sha256().equals(row.sourceRef().sha256()) || output.initial.linkCount() != 1
                        || sourceIdentities.contains(output.initial.identityKey()) || !destinationIdentities.add(output.initial.identityKey()))
                    throw new IOException("new destination must be a distinct private exact readback");
                assertSource(row, original.actual()); requireIo(original.initial.equals(original.actual()), "held source metadata changed during copy");
                original.reopenMatches(); output.reopenMatches();
                rows.add(new InstalledFile(row.targetRelative(), row.sourceRef(), original.initial, destination, output.initial));
                checkCeilings(request, outputs, dataDirectories, control); guard.check(charge(outputs, dataDirectories), chargeControl(control));
            }
            for (int i = 0; i < sources.size(); i++) {
                Held original = sources.get(i); assertSource(index.files().get(i), original.actual());
                requireIo(original.initial.equals(original.actual()), "held source metadata changed before final closure"); original.reopenMatches();
            }
            for (Held output : outputs) { requireIo(output.initial.equals(output.actual()), "destination changed after exact copy"); output.reopenMatches(); }
            Set<String> expected = index.files().stream().map(SourceFile::targetRelative).collect(java.util.stream.Collectors.toSet());
            closedInventory(source, expected); closedInventory(data, expected); verifyHeldDirectories(held); checkTime(request);
            List<InstalledDirectory> directories = new ArrayList<>();
            for (Held directory : dataDirectories) directories.add(new InstalledDirectory(directory.path.toString(), directory.actual()));
            Path receipt = control.resolve("actual.json");
            byte[] encoded = null;
            // CREATE_NEW once, then size and encode our own bounded receipt in that same private file.
            // No second DATA package or replaceable staging file is produced.
            Held receiptHandle = Held.create(receipt); held.add(receiptHandle);
            {
                for (int pass = 0; pass < 4; pass++) {
                    checkTime(request); long controlCharge = chargeControl(control);
                    Actual actual = new Actual(ACTUAL_SCHEMA, request.machineId(), Instant.now().toString(), "PASS", "EXACT_DATA_BYTES_AND_NATIVE_READBACK_ONLY",
                            plan.requestRef(), request.sourceIndexRef(), request.admissionRef(), data.toString(), control.toString(), rows, directories,
                            charge(outputs, dataDirectories), controlCharge, true, true, true, "NOT_RUN");
                    encoded = ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(actual);
                    requireIo(encoded.length <= RECEIPT_LIMIT && rounded(encoded.length, index.targetVolume().clusterBytes())
                            + Math.max(4096, nativeDirectoryFile(control).allocatedBytes()) <= request.maxControlNativeBytes(), "bounded control receipt required");
                    guard.check(actual.dataNativeChargedBytes(), Math.max(controlCharge,
                            rounded(encoded.length, index.targetVolume().clusterBytes()) + Math.max(4096, nativeDirectoryFile(control).allocatedBytes())));
                    reserveCreatedLength(receiptHandle, encoded.length, index.targetVolume().clusterBytes());
                    rewind(receiptHandle); writeNative(receiptHandle, encoded, encoded.length);
                    finishCreatedLength(receiptHandle, encoded.length, index.targetVolume().clusterBytes());
                    receiptHandle.completeCreation();
                    if (chargeControl(control) == controlCharge) break;
                    encoded = null;
                }
                requireIo(encoded != null, "control allocation did not stabilize within finite receipt passes");
            }
            FileRef expectedReceipt = new FileRef(receipt.toString(), encoded.length, HexFormat.of().formatHex(sha256().digest(encoded)));
            Readback receiptReadback = settleCreated(receiptHandle, expectedReceipt, request, held);
            FileRef createdReceipt = receiptReadback.exactRef();
            requireIo(java.util.Arrays.equals(encoded, Files.readAllBytes(receipt)), "control readback differs");
            checkCeilings(request, outputs, dataDirectories, control); guard.check(charge(outputs, dataDirectories), chargeControl(control));
            closedInventory(data, expected); checkTime(request);
            Actual actual = readActual(createdReceipt);
            requireIo(actual.controlNativeChargedBytes() == chargeControl(control), "receipt's actual control allocation drifted");
            checkTime(request);
            return actual;
        } catch (IOException | RuntimeException | Error error) { failure = error; throw error; }
        finally {
            IOException closeError = null;
            for (int i = held.size() - 1; i >= 0; i--) try { held.get(i).close(); } catch (IOException error) { if (closeError == null) closeError = error; else closeError.addSuppressed(error); }
            if (closeError != null) { if (failure != null) failure.addSuppressed(closeError); else throw closeError; }
        }
    }

    /** Physical readback revalidates the installed package; it grants no provider/SDK/Game qualification. */
    public static Actual readActual(FileRef exactRef) throws IOException {
        return readActual(exactRef, () -> { });
    }
    @FunctionalInterface interface ReadGuard { void afterAllFilesRetained() throws IOException; }
    static Actual readActual(FileRef exactRef, ReadGuard guard) throws IOException {
        List<Held> owned = new ArrayList<>(); Throwable failure = null;
        try {
            retainMetadata(exactRef, owned); Actual actual = readExact(exactRef, Actual.class);
            requireIo(actual.machineId().equals(WindowsJobProcess.currentMachineId())
                    && absolute(exactRef.path()).equals(absolute(actual.controlRoot()).resolve("actual.json")), "actual machine/control path differs");
            retainMetadata(actual.requestRef(), owned); Request request = readRequest(actual.requestRef());
            retainMetadata(request.admissionRef(), owned); retainMetadata(request.sourceIndexRef(), owned);
            Admission admission = readAdmission(request.admissionRef()); SourceIndex index = readSourceIndex(request.sourceIndexRef());
            matchScopes(request, admission, index);
            Set<String> expected = index.files().stream().map(SourceFile::targetRelative).collect(java.util.stream.Collectors.toSet());
            Set<String> seen = actual.files().stream().map(InstalledFile::targetRelative).collect(java.util.stream.Collectors.toSet());
            requireIo(seen.equals(expected) && actual.files().size() == index.files().size(), "actual omitted original package files");
            Set<Path> expectedDirectories = new HashSet<>();
            for (String path : request.ancestorDirectories()) expectedDirectories.add(absolute(path));
            expectedDirectories.add(absolute(actual.dataRoot())); expectedDirectories.add(absolute(actual.dataRoot()).resolve("blobs"));
            Set<Path> declaredDirectories = actual.directories().stream().map(row -> absolute(row.path())).collect(java.util.stream.Collectors.toSet());
            requireIo(expectedDirectories.equals(declaredDirectories) && actual.directories().size() == expectedDirectories.size(), "actual directory scope differs");
            holdExistingAncestors(absolute(index.sourceRoot()), owned); holdExistingAncestors(absolute(actual.dataRoot()), owned);
            for (SourceDirectory directory : index.sourceDirectories()) {
                Held held = Held.open(absolute(directory.path()), true, false); owned.add(held);
                requireIo(directory.nativeObservation().matches(held.initial), "original source directory observation drifted");
            }
            long directoryCharge = 0;
            for (InstalledDirectory directory : actual.directories()) {
                Held held = Held.open(absolute(directory.path()), true, false); owned.add(held);
                requireIo(directory.nativeObservation().equals(held.initial), "installed directory witness drifted");
                directoryCharge = Math.addExact(directoryCharge, Math.max(4096, held.initial.allocatedBytes()));
            }
            List<Held> originals = new ArrayList<>(), copied = new ArrayList<>(); long dataCharge = directoryCharge;
            // Retain the entire package before validating any row's bytes. There is one simultaneous view.
            for (SourceFile original : index.files()) {
                InstalledFile row = actual.files().stream().filter(candidate -> candidate.targetRelative().equals(original.targetRelative())).findFirst()
                        .orElseThrow(() -> new IOException("original source row missing"));
                requireIo(original.sourceRef().equals(row.sourceRef()), "actual exact original source mapping differs"); assertSource(original, row.sourceNative());
                Held source = Held.open(absolute(row.sourceRef().path()), false, true); owned.add(source); originals.add(source);
                Held destination = Held.open(absolute(row.destinationRef().path()), false, true); owned.add(destination); copied.add(destination);
                requireIo(row.sourceNative().equals(source.initial) && row.destinationNative().equals(destination.initial), "physical package original source or destination witness drifted");
                dataCharge = Math.addExact(dataCharge, destination.initial.allocatedBytes());
            }
            guard.afterAllFilesRetained();
            for (int i = 0; i < index.files().size(); i++) {
                SourceFile original = index.files().get(i); FileRef source = readHeld(originals.get(i), originals.get(i).path, original.sourceRef().bytes(), request);
                FileRef destination = readHeld(copied.get(i), copied.get(i).path, original.sourceRef().bytes(), request);
                requireIo(source.sha256().equals(original.sourceRef().sha256()) && destination.sha256().equals(original.sourceRef().sha256()), "same-held complete package hash differs");
            }
            for (Held held : originals) { requireIo(held.initial.equals(held.actual()), "retained original metadata drifted"); held.reopenMatches(); }
            for (Held held : copied) { requireIo(held.initial.equals(held.actual()), "retained copied metadata drifted"); held.reopenMatches(); }
            for (SourceDirectory directory : index.sourceDirectories()) requireIo(directory.nativeObservation().matches(nativeDirectoryFile(absolute(directory.path()))), "source directory drifted during complete readback");
            for (InstalledDirectory directory : actual.directories()) requireIo(directory.nativeObservation().equals(nativeDirectoryFile(absolute(directory.path()))), "installed directory drifted during complete readback");
            requireIo(request.sourceIndexRef().equals(actual.sourceIndexRef()) && request.admissionRef().equals(actual.admissionRef())
                    && samePath(request.dataRoot(), actual.dataRoot()) && samePath(request.controlRoot(), actual.controlRoot())
                    && directoryCharge <= request.dataDirectoryReserveBytes() && dataCharge == actual.dataNativeChargedBytes()
                    && dataCharge <= request.maxDataNativeBytes() && chargeControl(absolute(actual.controlRoot())) == actual.controlNativeChargedBytes()
                    && actual.controlNativeChargedBytes() <= request.maxControlNativeBytes(), "installed exact directory/allocated-byte closure differs");
            closedInventory(absolute(index.sourceRoot()), expected); closedInventory(absolute(actual.dataRoot()), expected); verifyHeldDirectories(owned);
            exactBytes(exactRef); exactBytes(actual.requestRef()); exactBytes(request.sourceIndexRef()); exactBytes(request.admissionRef());
            return actual;
        } catch (IOException | RuntimeException | Error error) { failure = error; throw error; }
        finally { closeAll(owned, failure); }
    }
    private static void retainMetadata(FileRef ref, List<Held> owned) throws IOException {
        requireIo(ref != null && ref.bytes() > 0 && ref.bytes() <= JSON_LIMIT, "finite exact metadata reference required");
        holdExistingAncestors(absolute(ref.path()), owned); Held held = Held.open(absolute(ref.path()), false, true); owned.add(held);
        requireIo(held.initial.logicalBytes() == ref.bytes(), "retained metadata extent differs");
    }
    private static void closeAll(List<Held> held, Throwable failure) throws IOException {
        IOException closeError = null;
        for (int i = held.size() - 1; i >= 0; i--) try { held.get(i).close(); } catch (IOException error) { if (closeError == null) closeError = error; else closeError.addSuppressed(error); }
        if (closeError != null) { if (failure != null) failure.addSuppressed(closeError); else throw closeError; }
    }
    public static Request readRequest(FileRef exactRef) throws IOException { return readExact(exactRef, Request.class); }
    public static Admission readAdmission(FileRef exactRef) throws IOException { return readExact(exactRef, Admission.class); }
    public static SourceIndex readSourceIndex(FileRef exactRef) throws IOException { return readExact(exactRef, SourceIndex.class); }
    private static <T> T readExact(FileRef ref, Class<T> type) throws IOException {
        T value = ControlBuild.strictMapper().readValue(exactBytes(ref), type);
        requireIo(value != null, "non-null typed metadata object required"); return value;
    }
    private static byte[] exactBytes(FileRef ref) throws IOException {
        if (ref == null || ref.bytes() <= 0 || ref.bytes() > JSON_LIMIT) throw new IOException("finite exact metadata reference required");
        Path path = absolute(ref.path()); SharedSourceFiles.plainAncestors(path); NativeFile before = SharedSourceFiles.nativeFile(path);
        requireIo(before.logicalBytes() == ref.bytes(), "metadata extent differs");
        byte[] raw;
        try (var input = Files.newInputStream(path)) { raw = input.readNBytes(JSON_LIMIT + 1); }
        requireIo(raw.length == ref.bytes() && HexFormat.of().formatHex(sha256().digest(raw)).equals(ref.sha256())
                && before.equals(SharedSourceFiles.nativeFile(path)), "metadata exact bytes or native witness changed");
        return raw;
    }

    private static final class Guard implements CapacityGuard {
        private final Request request; private final Admission admission; private final CiBootstrap.Policy policy;
        private Guard(Request request, Admission admission, CiBootstrap.Policy policy) { this.request = request; this.admission = admission; this.policy = policy; }
        @Override public void check(long dataWritten, long controlWritten) throws IOException {
            checkTime(request); requireIo(Instant.now().isBefore(Instant.parse(admission.reviewAtUtc())), "install admission expired");
            long consumed = Math.addExact(dataWritten, controlWritten); var budget = admission.volumeBudget();
            requireIo(consumed <= budget.thisWritePeak(), "single-copy aggregate allocation exceeded");
            var store = Files.getFileStore(absolute(admission.volumeRoot()));
            requireIo(store.getTotalSpace() == budget.totalVolumeBytes(), "target volume total drifted from issuer observation");
            try {
                CiBootstrap.VolumeBudget actual = CiBootstrap.calculate(policy, store.getTotalSpace(), store.getUsableSpace(),
                        Math.subtractExact(budget.thisWritePeak(), consumed), budget.otherUnspentReservations(), budget.systemGrowthReserve(),
                        Math.addExact(budget.currentProjectUsageConservativeUpper(), consumed), admission.quotaOverride(),
                        Instant.parse(admission.observedAtUtc()), Instant.parse(admission.reviewAtUtc()));
                requireIo(actual.effectiveProjectQuota() == budget.effectiveProjectQuota() && actual.safetyReserve() == budget.safetyReserve(), "shared storage policy differs from issuer snapshot");
            } catch (IllegalArgumentException error) { throw new IOException("shared storage formula rejected installation", error); }
        }
    }
    /** Package visibility permits native lifetime regressions against this actual production
     * handle implementation. It grants no admission or alternate copy authority. */
    static final class Held implements AutoCloseable {
        private final Path path; private final boolean directory; private final HANDLE handle; private final NativeFile birth; private final boolean created;
        private NativeFile initial;
        private boolean closed;
        private Held(Path path, boolean directory, HANDLE handle, NativeFile initial, boolean created) {
            this.path = path; this.directory = directory; this.handle = handle; this.birth = initial; this.initial = initial; this.created = created;
        }
        static Held open(Path path, boolean directory, boolean read) throws IOException {
            return openSharing(path, directory, read, directory ? 3 : 1);
        }
        static Held openSharing(Path path, boolean directory, boolean read, int share) throws IOException {
            // READ_ATTRIBUTES alone is exempt from normal read/delete sharing checks.
            // Every retained directory therefore requests FILE_LIST_DIRECTORY as well.
            // File read=false is metadata observation only, never immutable-byte custody;
            // all current retained source/destination/metadata files explicitly use read=true.
            return openAccess(path, directory, directory ? 0x81 : read ? 0x80000000 : 0x80, share);
        }
        private static Held observeDirectory(Path path) throws IOException {
            // A transient native attribute query is not a retained custody handle.
            return openAccess(path, true, 0x80, 3);
        }
        private static Held openAccess(Path path, boolean directory, int access, int share) throws IOException {
            SharedSourceFiles.plainAncestors(path);
            HANDLE handle = Kernel32.INSTANCE.CreateFile(SharedSourceFiles.nativePath(path), access,
                    share, null, 3, 0x00200000 | (directory ? 0x02000000 : 0), null);
            if (handle == null || WinBase.INVALID_HANDLE_VALUE.equals(handle)) throw new IOException("held DATA open Win32=" + Native.getLastError() + " path=" + path);
            try { return new Held(path, directory, handle, directory ? SharedSourceFiles.nativeHeldDirectory(handle) : SharedSourceFiles.nativeHeldFile(handle), false); }
            catch (IOException | RuntimeException error) { Kernel32.INSTANCE.CloseHandle(handle); throw error; }
        }
        static Held create(Path path) throws IOException {
            SharedSourceFiles.plainAncestors(path);
            HANDLE handle = Kernel32.INSTANCE.CreateFile(SharedSourceFiles.nativePath(path), 0xc0000000, 1, null, 1, 0x00200080, null);
            if (handle == null || WinBase.INVALID_HANDLE_VALUE.equals(handle)) throw new IOException("CREATE_NEW held DATA Win32=" + Native.getLastError() + " path=" + path);
            try { return new Held(path, false, handle, SharedSourceFiles.nativeHeldFile(handle), true); }
            catch (IOException | RuntimeException error) { Kernel32.INSTANCE.CloseHandle(handle); throw error; }
        }
        void completeCreation() throws IOException {
            NativeFile current = actual(); requireIo(created && birth.identityKey().equals(current.identityKey()) && current.linkCount() == 1, "created object's original identity changed");
            initial = current;
        }
        NativeFile actual() throws IOException { return directory ? SharedSourceFiles.nativeHeldDirectory(handle) : SharedSourceFiles.nativeHeldFile(handle); }
        void reopenMatches() throws IOException {
            NativeFile current = directory ? nativeDirectoryFile(path) : SharedSourceFiles.nativeFile(path);
            requireIo(directory ? initial.identityKey().equals(current.identityKey()) : actual().equals(current), "held object and current path differ: " + path);
        }
        @Override public void close() throws IOException {
            if (closed) return;
            if (!Kernel32.INSTANCE.CloseHandle(handle)) throw new IOException("held DATA close Win32=" + Native.getLastError());
            closed = true;
        }
    }
    private record Readback(Held custody, FileRef exactRef) { }
    /** Continuous identity custody across write cleanup, then hash/native observation with no writer handles. */
    private static Readback settleCreated(Held creator, FileRef expected, Request request, List<Held> retained) throws IOException {
        creator.completeCreation();
        Held bridge = Held.openSharing(creator.path, false, true, 3); retained.add(bridge);
        requireIo(creator.birth.identityKey().equals(bridge.initial.identityKey()), "created object identity differs before write cleanup");
        // Both creator and bridge deny FILE_SHARE_DELETE. The identity can never be renamed/replaced.
        // A bridge permits the existing creator's write access; closing that last writer settles NTFS times.
        creator.close();
        Held settled = Held.open(creator.path, false, true); retained.add(settled);
        // If another writer exists, this SHARE_READ-only open fails. Re-read all bytes after that window.
        requireIo(creator.birth.identityKey().equals(settled.initial.identityKey()) && settled.initial.linkCount() == 1, "created identity/private links differ after write cleanup");
        FileRef exact = readHeld(settled, creator.path, expected.bytes(), request);
        requireIo(expected.sha256().equals(exact.sha256()) && settled.initial.equals(settled.actual()), "settled held destination bytes/native metadata differ");
        bridge.close(); settled.reopenMatches(); return new Readback(settled, exact);
    }
    private static NativeFile nativeDirectoryFile(Path path) throws IOException { try (Held held = Held.observeDirectory(path)) { return held.initial; } }
    private static void assertSource(SourceFile row, NativeFile actual) throws IOException {
        requireIo(row.nativeIdentity().matches(actual) && row.nativeAllocationBytes() == actual.allocatedBytes()
                && row.nativeLinks() == actual.linkCount() && row.sourceRef().bytes() == actual.logicalBytes(), "source original native witness changed: " + row.sourceRef().path());
    }
    private static void copyOne(Held original, Held destination, FileRef expected, Request request, long clusterBytes) throws IOException {
        MessageDigest digest = sha256(); long count = 0; byte[] buffer = new byte[65536]; IntByReference received = new IntByReference();
        while (true) {
            checkTime(request);
            if (!Kernel32.INSTANCE.ReadFile(original.handle, buffer, buffer.length, received, null)) throw new IOException("held DATA ReadFile Win32=" + Native.getLastError());
            int length = received.getValue(); if (length == 0) break;
            requireIo(length > 0 && length <= buffer.length, "invalid native read extent"); count = Math.addExact(count, length);
            requireIo(count <= expected.bytes(), "held source grew beyond exact input"); digest.update(buffer, 0, length);
            writeNative(destination, buffer, length);
            requireHeldLength(destination, expected.bytes(), rounded(expected.bytes(), clusterBytes), false);
        }
        if (!Kernel32.INSTANCE.FlushFileBuffers(destination.handle)) throw new IOException("created DATA FlushFileBuffers Win32=" + Native.getLastError());
        requireIo(count == expected.bytes() && HexFormat.of().formatHex(digest.digest()).equals(expected.sha256()), "held source exact bytes differ");
        finishCreatedLength(destination, expected.bytes(), clusterBytes);
    }
    /** The admitted forecast is cluster-rounded exact length, not NTFS streaming growth.
     * Reserve that length before the first write; keep actual held AllocationSize bounded
     * throughout. Last-reader close is never used as an allocation-release mechanism. */
    private static void reserveCreatedLength(Held destination, long bytes, long clusterBytes) throws IOException {
        requireIo(destination.created && destination.birth.identityKey().equals(destination.actual().identityKey()), "only original CREATE_NEW writer may reserve allocation");
        long allocation = rounded(bytes, clusterBytes);
        setCreatedSize(destination, 5, allocation); // FILE_ALLOCATION_INFO: independent of logical EOF.
        requireHeldLength(destination, Math.max(bytes, destination.actual().logicalBytes()), allocation, false);
    }
    private static void finishCreatedLength(Held destination, long bytes, long clusterBytes) throws IOException {
        requireIo(destination.created, "exact EOF belongs only to our original new writer");
        setCreatedSize(destination, 6, bytes); // FILE_END_OF_FILE_INFO, no path-based reopen or replacement.
        setCreatedSize(destination, 5, rounded(bytes, clusterBytes));
        if (!Kernel32.INSTANCE.FlushFileBuffers(destination.handle)) throw new IOException("exact created allocation flush Win32=" + Native.getLastError());
        requireHeldLength(destination, bytes, rounded(bytes, clusterBytes), true);
    }
    private static void setCreatedSize(Held destination, int informationClass, long bytes) throws IOException {
        requireIo(destination.created && !destination.closed && bytes >= 0 && (informationClass == 5 || informationClass == 6), "finite original private size mutation required");
        try (Memory value = new Memory(Long.BYTES)) {
            value.setLong(0, bytes);
            if (!Kernel32.INSTANCE.SetFileInformationByHandle(destination.handle, informationClass, value, new DWORD(Long.BYTES)))
                throw new IOException("created exact size class=" + informationClass + " bytes=" + bytes + " Win32=" + Native.getLastError());
        }
    }
    private static void requireHeldLength(Held destination, long logicalLimit, long allocationLimit, boolean exact) throws IOException {
        NativeFile actual = destination.actual();
        requireIo(destination.birth.identityKey().equals(actual.identityKey()) && actual.linkCount() == 1
                && actual.logicalBytes() <= logicalLimit && (!exact || actual.logicalBytes() == logicalLimit)
                && actual.allocatedBytes() <= allocationLimit,
                "created held length/allocation exceeds forecast: target=" + destination.path + " logical=" + actual.logicalBytes()
                + " allocated=" + actual.allocatedBytes() + " logicalLimit=" + logicalLimit + " allocationLimit=" + allocationLimit);
    }
    private static void observeAllocation(Optional<AllocationObserver> observer, AllocationPhase phase, Held output) throws IOException {
        if (observer.isPresent()) observer.orElseThrow().observed(new AllocationSample(phase, output.path, output.actual()));
    }
    private static void rewind(Held held) throws IOException {
        if (!PositionApi.VALUE.SetFilePointerEx(held.handle, 0L, null, 0)) throw new IOException("same-held-object rewind Win32=" + Native.getLastError());
    }
    private static void writeNative(Held destination, byte[] bytes, int length) throws IOException {
        int offset = 0; IntByReference written = new IntByReference();
        while (offset < length) {
            byte[] remaining = offset == 0 ? bytes : java.util.Arrays.copyOfRange(bytes, offset, length);
            if (!Kernel32.INSTANCE.WriteFile(destination.handle, remaining, length - offset, written, null)) throw new IOException("created DATA WriteFile Win32=" + Native.getLastError());
            int count = written.getValue(); requireIo(count > 0 && count <= length - offset, "invalid native write extent"); offset += count;
        }
    }
    private static FileRef readHeld(Held held, Path path, long maximum, Request request) throws IOException {
        MessageDigest digest = sha256(); long count = 0; byte[] buffer = new byte[65536]; IntByReference received = new IntByReference();
        while (true) {
            checkTime(request);
            if (!Kernel32.INSTANCE.ReadFile(held.handle, buffer, buffer.length, received, null)) throw new IOException("destination readback Win32=" + Native.getLastError());
            int length = received.getValue(); if (length == 0) break;
            requireIo(length > 0 && length <= buffer.length, "invalid native readback extent"); count = Math.addExact(count, length);
            requireIo(count <= maximum, "destination grew beyond source input"); digest.update(buffer, 0, length);
        }
        requireIo(count == maximum, "destination truncated"); return new FileRef(path.toString(), count, HexFormat.of().formatHex(digest.digest()));
    }
    private static void holdExistingAncestors(Path path, List<Held> held) throws IOException {
        for (Path parent = path.getParent(); parent != null; parent = parent.getParent()) {
            if (Files.exists(parent, LinkOption.NOFOLLOW_LINKS)) held.add(Held.open(parent, true, false));
        }
    }
    private static void createDirectory(Path path, List<Held> held, List<Held> charged) throws IOException {
        Files.createDirectory(path); Held directory = Held.open(path, true, false); held.add(directory); charged.add(directory);
    }
    private static void verifyHeldDirectories(List<Held> held) throws IOException { for (Held entry : held) if (entry.directory) entry.reopenMatches(); }
    private static void requireAbsent(Path path) throws IOException {
        SharedSourceFiles.plainAncestors(path.getParent());
        requireIo(!Files.exists(path, LinkOption.NOFOLLOW_LINKS), "CREATE_NEW scope already exists: " + path);
    }
    private static long charge(List<Held> files, List<Held> directories) throws IOException {
        long result = 0; for (Held file : files) result = Math.addExact(result, file.actual().allocatedBytes());
        for (Held directory : directories) result = Math.addExact(result, Math.max(4096, directory.actual().allocatedBytes())); return result;
    }
    private static long chargeControl(Path root) throws IOException {
        long result = Math.max(4096, nativeDirectoryFile(root).allocatedBytes());
        try (DirectoryStream<Path> stream = Files.newDirectoryStream(root)) {
            for (Path path : stream) {
                NativeFile actual = SharedSourceFiles.nativeFile(path);
                requireIo(path.getFileName().toString().equals("actual.json") && actual.linkCount() == 1, "unexpected or shared control output");
                result = Math.addExact(result, actual.allocatedBytes());
            }
        }
        return result;
    }
    private static void checkCeilings(Request request, List<Held> files, List<Held> dirs, Path control) throws IOException {
        requireIo(charge(List.of(), dirs) <= request.dataDirectoryReserveBytes() && charge(files, dirs) <= request.maxDataNativeBytes()
                && chargeControl(control) <= request.maxControlNativeBytes(), "actual native file+directory charge exceeds admission");
    }
    private static void closedInventory(Path root, Set<String> expected) throws IOException {
        Set<String> actual = new HashSet<>(); boolean blobs = false;
        try (DirectoryStream<Path> top = Files.newDirectoryStream(root)) {
            for (Path entry : top) {
                SharedSourceFiles.plainAncestors(entry);
                if (entry.getFileName().toString().equals("blobs") && Files.isDirectory(entry, LinkOption.NOFOLLOW_LINKS)) {
                    requireIo(!blobs, "duplicate blobs directory"); blobs = true;
                    try (DirectoryStream<Path> children = Files.newDirectoryStream(entry)) {
                        for (Path leaf : children) {
                            String name = "blobs/" + leaf.getFileName(); relativeIo(name);
                            requireIo(Files.isRegularFile(leaf, LinkOption.NOFOLLOW_LINKS) && actual.add(name) && SharedSourceFiles.nativeFile(leaf).linkCount() == 1, "ordinary private blob required");
                        }
                    }
                } else {
                    requireIo(entry.getFileName().toString().equals("manifest_v1.json") && Files.isRegularFile(entry, LinkOption.NOFOLLOW_LINKS)
                            && SharedSourceFiles.nativeFile(entry).linkCount() == 1 && actual.add("manifest_v1.json"), "unexpected package entry");
                }
            }
        }
        requireIo(blobs && actual.equals(expected), "closed package inventory differs");
    }
    private static void verifyVolume(Volume volume) throws IOException {
        NativeStorageGeometry.Volume actual = NativeStorageGeometry.read(absolute(volume.volumeRoot()));
        requireIo(actual.sectorsPerCluster() == volume.sectorsPerCluster() && actual.bytesPerSector() == volume.bytesPerSector()
                && actual.clusterBytes() == volume.clusterBytes(), "fresh native volume geometry differs");
    }
    private static void validateDestinations(String dataRoot, String controlRoot, List<String> ancestors) {
        Path data = absolute(dataRoot), control = absolute(controlRoot);
        require(!data.startsWith(control) && !control.startsWith(data) && data.getRoot().equals(control.getRoot())
                && !data.equals(data.getRoot()) && !control.equals(control.getRoot()) && ancestors.size() <= 16, "disjoint same-volume finite output roots required");
        Path previous = null;
        for (String text : ancestors) {
            Path path = absolute(text); require(data.startsWith(path) && !data.equals(path) && (previous == null || path.getParent().equals(previous)), "ordered exact DATA ancestor chain required"); previous = path;
        }
        require(previous == null || data.getParent().equals(previous), "ancestor chain must end at DATA parent");
    }
    private static void checkTime(Request request) throws IOException {
        if (Thread.currentThread().isInterrupted()) throw new InterruptedIOException("DATA copy interrupted");
        requireIo(Instant.now().isBefore(Instant.parse(request.deadlineUtc())) && Instant.now().isBefore(Instant.parse(request.reviewAtUtc())), "DATA copy original deadline or review expired");
    }
    private static Path absolute(String value) {
        require(value != null, "absolute canonical path required"); Path path = Path.of(value);
        require(path.isAbsolute() && path.equals(path.toAbsolutePath().normalize()) && value.indexOf('\0') < 0, "absolute normalized path required"); return path;
    }
    private static boolean samePath(String left, String right) { return absolute(left).equals(absolute(right)); }
    private static long ancestorsCount(List<String> ancestors) { return Math.addExact(ancestors.size(), 2L); }
    private static void relative(String value) { require(value != null && (value.equals("manifest_v1.json") || value.matches("blobs/[0-9a-f]{64}\\.gz")), "canonical two-level package path required"); }
    private static void relativeIo(String value) throws IOException { try { relative(value); } catch (IllegalArgumentException error) { throw new IOException("unexpected blob filename", error); } }
    private static void machine(String value) { require(value != null && value.matches("[a-z0-9][a-z0-9-]{0,127}") && !value.equals("unknown"), "known canonical machine required"); }
    private static void owner(String value) { require(value != null && !value.isBlank() && value.length() <= 128, "finite explicit owner required"); }
    private static void decimal(String value, int bits) { require(value != null && value.matches("0|[1-9][0-9]*") && new BigInteger(value).bitLength() <= bits, "canonical unsigned native identity decimal required"); }
    private static long rounded(long bytes, long cluster) { return Math.multiplyExact(Math.floorDiv(Math.addExact(bytes, cluster - 1), cluster), cluster); }
    private static MessageDigest sha256() { try { return MessageDigest.getInstance("SHA-256"); } catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); } }
    private static void require(boolean condition, String message) { if (!condition) throw new IllegalArgumentException(message); }
    private static void requireIo(boolean condition, String message) throws IOException { if (!condition) throw new IOException(message); }
}
