package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Objects;

import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SdkSourceAssembly.Digest;
import org.xar.ck3.control.build.SdkSourceIntent.Cohort;
import org.xar.ck3.control.build.SdkSourceIntent.Plan;
import org.xar.ck3.control.build.SdkSourceIntent.RequiredReactorSource;
import org.xar.ck3.control.build.SdkSourceIntent.Selection;

/** Produces a new source plan through the existing v2 contract; never grants execution or qualification. */
public final class SdkSourceIntentSuccessor {
    public static final String SCHEMA = "xar.sdk-source-intent-successor/v1";
    private static final int MAX_BYTES = 2 << 20;
    private SdkSourceIntentSuccessor() { }

    /** The admitted shared caller owns this process, all input identities and the complete storage lease. */
    public static void main(String[] arguments) throws IOException {
        if (arguments.length != 5 || !arguments[1].matches("[1-9][0-9]{0,8}")
                || !arguments[4].matches("[1-9][0-9]{0,8}"))
            throw new IllegalArgumentException("REQUEST_PATH BYTES SHA256 NEW_PLAN_PATH MAX_NATIVE_BYTES required");
        FileRef request = new FileRef(arguments[0], Long.parseLong(arguments[1]), arguments[2]);
        Path destination = Path.of(arguments[3]); long maximum = Long.parseLong(arguments[4]);
        if (maximum > 4L << 20 || !destination.isAbsolute() || !destination.equals(destination.normalize())
                || destination.getParent() == null) throw new IllegalArgumentException("Finite canonical metadata-only bound required");
        long unit = NativeStorageGeometry.read(destination.getParent()).clusterBytes();
        if (unit < 1 || unit > 1L << 20) throw new IOException("Bounded native allocation unit required");
        SdkSourceIntent.MetadataGuard guard = pending -> {
            if (pending < 0) throw new IOException("Nonnegative pending allocation required");
            long used = Files.exists(destination) ? SharedSourceFiles.nativeFile(destination).allocatedBytes() : 0;
            long reserved = Math.multiplyExact(Math.floorDiv(Math.addExact(pending, unit - 1), unit), unit);
            if (Math.addExact(unit, Math.addExact(used, reserved)) > maximum)
                throw new IOException("SDK successor output exceeds admitted native bound");
        };
        System.out.println(ControlBuild.strictMapper().writeValueAsString(produce(request, destination, guard)));
    }

    public record SelectionUpdate(Selection previous, Selection selected) {
        public SelectionUpdate {
            Objects.requireNonNull(selected);
            if (previous != null && !key(previous.relativePath()).equals(key(selected.relativePath())))
                throw new IllegalArgumentException("One exact selected source target required");
        }
    }
    public record ReactorUpdate(RequiredReactorSource previous, String relativePath, FileRef selectedSource) {
        public ReactorUpdate {
            ExactSourcePatch.relative(relativePath); Objects.requireNonNull(selectedSource);
            if (previous != null && !key(previous.relativePath()).equals(key(relativePath)))
                throw new IllegalArgumentException("One exact reactor target required");
        }
        public RequiredReactorSource selected() {
            return new RequiredReactorSource(relativePath, new Digest(selectedSource.bytes(), selectedSource.sha256()));
        }
    }
    public record CohortUpdate(Cohort previous, Cohort selected) {
        public CohortUpdate {
            Objects.requireNonNull(selected);
            if (previous != null && !previous.owner().equals(selected.owner()))
                throw new IllegalArgumentException("One exact cohort owner required");
        }
    }
    public record Request(String schema, String machineId, String reviewAtUtc, FileRef predecessorRef,
            FileRef reviewAuthorityRef, List<SelectionUpdate> selectionUpdates,
            List<ReactorUpdate> reactorUpdates, List<CohortUpdate> cohortUpdates) {
        public Request {
            if (!SCHEMA.equals(schema)) throw new IllegalArgumentException("Exact SDK successor schema required");
            if (machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{2,127}"))
                throw new IllegalArgumentException("Exact machine required");
            Instant.parse(reviewAtUtc); Objects.requireNonNull(predecessorRef); Objects.requireNonNull(reviewAuthorityRef);
            selectionUpdates = List.copyOf(selectionUpdates); reactorUpdates = List.copyOf(reactorUpdates);
            cohortUpdates = List.copyOf(cohortUpdates);
            if (selectionUpdates.size() > 512 || reactorUpdates.size() > 512 || cohortUpdates.size() > 32
                    || selectionUpdates.isEmpty() && reactorUpdates.isEmpty() && cohortUpdates.isEmpty())
                throw new IllegalArgumentException("Finite actual source changes required; deadline-only renewal forbidden");
        }
    }

    /** The existing Root metadata37 receipt, including its independently bounded writing and data windows. */
    public record DataReviewScope(String schema, String machineId, String owner, String actualActor,
            String issuedAtUtc, FileRef parentMetadataScopeRef, FileRef sourceGrantRef,
            String metadataWriteReviewAtUtc, String immutableSourceIntentDataReviewUpperAtUtc,
            boolean automaticRenewal, String authorization, String requiredSeparation,
            @com.fasterxml.jackson.annotation.JsonProperty("SC") String storageAccounting) {
        public DataReviewScope {
            if (!"xar.root.sdk-static-intent-data-review/v1".equals(schema) || !"/root".equals(owner)
                    || !"/root/sdk_current".equals(actualActor) || automaticRenewal)
                throw new IllegalArgumentException("Exact finite Root SDK static-data authority required");
            Objects.requireNonNull(machineId); Objects.requireNonNull(parentMetadataScopeRef); Objects.requireNonNull(sourceGrantRef);
            Objects.requireNonNull(authorization); Objects.requireNonNull(requiredSeparation); Objects.requireNonNull(storageAccounting);
            Instant issued = Instant.parse(issuedAtUtc), write = Instant.parse(metadataWriteReviewAtUtc);
            Instant data = Instant.parse(immutableSourceIntentDataReviewUpperAtUtc);
            if (!issued.isBefore(write) || data.isBefore(write)) throw new IllegalArgumentException("Separate ordered write and static-data windows required");
        }
    }

    public static void requireReview(Request request, DataReviewScope authority, Instant now) {
        Objects.requireNonNull(request);
        requireReview(request.machineId(), Instant.parse(request.reviewAtUtc()), authority, now);
    }

    public static void requireReview(String machineId, Instant requestedReview, DataReviewScope authority, Instant now) {
        Objects.requireNonNull(machineId); Objects.requireNonNull(requestedReview);
        Objects.requireNonNull(authority); Objects.requireNonNull(now);
        if (!machineId.equals(authority.machineId())
                || !now.isBefore(Instant.parse(authority.metadataWriteReviewAtUtc()))
                || !now.isBefore(requestedReview)
                || requestedReview.isAfter(Instant.parse(authority.immutableSourceIntentDataReviewUpperAtUtc())))
            throw new IllegalArgumentException("Metadata writing and static source data require their separate actual Root bounds");
    }

    /** Pure preimage transition. A caller must separately validate the actual authority and resource window. */
    public static Plan apply(Plan predecessor, Request request) {
        Objects.requireNonNull(predecessor); Objects.requireNonNull(request);
        if (!predecessor.machineId().equals(request.machineId()))
            throw new IllegalArgumentException("Predecessor and successor machine differ");
        var selections = new LinkedHashMap<String, Selection>();
        for (Selection value : predecessor.consumerSelections()) selections.put(key(value.relativePath()), value);
        var reactors = new LinkedHashMap<String, RequiredReactorSource>();
        for (RequiredReactorSource value : predecessor.requiredReactorSources()) reactors.put(key(value.relativePath()), value);
        var cohorts = new LinkedHashMap<String, Cohort>();
        for (Cohort value : predecessor.cohorts()) {
            if (cohorts.putIfAbsent(value.owner(), value) != null) throw new IllegalArgumentException("Duplicate predecessor cohort");
        }
        var selectionTargets = new java.util.HashSet<String>();
        for (SelectionUpdate update : request.selectionUpdates()) {
            String name = key(update.selected().relativePath());
            requireUpdate(selectionTargets.add(name), selections.get(name), update.previous(), update.selected());
            selections.put(name, update.selected());
        }
        var reactorTargets = new java.util.HashSet<String>();
        for (ReactorUpdate update : request.reactorUpdates()) {
            String name = key(update.relativePath()); RequiredReactorSource selected = update.selected();
            requireUpdate(reactorTargets.add(name), reactors.get(name), update.previous(), selected);
            reactors.put(name, selected);
        }
        var cohortTargets = new java.util.HashSet<String>();
        for (CohortUpdate update : request.cohortUpdates()) {
            String name = update.selected().owner();
            requireUpdate(cohortTargets.add(name), cohorts.get(name), update.previous(), update.selected());
            cohorts.put(name, update.selected());
        }
        return new Plan(SdkSourceIntent.PLAN_SCHEMA, request.machineId(), request.reviewAtUtc(),
                predecessor.baselineTemplateRef(), predecessor.legacyTemplateRef(), predecessor.consumerTemplateRef(),
                predecessor.referenceInputs(), List.copyOf(selections.values()), List.copyOf(cohorts.values()),
                List.copyOf(reactors.values()));
    }

    public static List<FileRef> inputRefs(Request request) throws IOException {
        var values = new ArrayList<FileRef>(List.of(request.predecessorRef(), request.reviewAuthorityRef()));
        DataReviewScope authority = read(request.reviewAuthorityRef(), DataReviewScope.class);
        values.add(authority.parentMetadataScopeRef()); values.add(authority.sourceGrantRef());
        for (SelectionUpdate update : request.selectionUpdates()) {
            values.add(update.selected().selectedSource());
            for (var overlay : update.selected().selectedOverlays()) values.add(overlay.patchRef());
        }
        for (ReactorUpdate update : request.reactorUpdates()) values.add(update.selectedSource());
        for (CohortUpdate update : request.cohortUpdates()) values.addAll(update.selected().evidenceRefs());
        var unique = new LinkedHashMap<String, FileRef>();
        for (FileRef value : values) {
            String name = Path.of(value.path()).toAbsolutePath().normalize().toString().toLowerCase(Locale.ROOT);
            FileRef previous = unique.putIfAbsent(name, value);
            if (previous != null && !previous.equals(value)) throw new IllegalArgumentException("Conflicting original input refs");
        }
        return List.copyOf(unique.values());
    }

    public static FileRef produce(FileRef requestRef, Path destination, SdkSourceIntent.MetadataGuard guard) throws IOException {
        Objects.requireNonNull(guard); Objects.requireNonNull(destination);
        Request request = read(requestRef, Request.class);
        DataReviewScope authority = read(request.reviewAuthorityRef(), DataReviewScope.class);
        try { requireReview(request, authority, Instant.now()); }
        catch (IllegalArgumentException invalid) { throw new IOException("SDK static-data authority rejected", invalid); }
        authority.parentMetadataScopeRef().verify(); authority.sourceGrantRef().verify();
        if (!request.machineId().equals(WindowsJobProcess.currentMachineId())) throw new IOException("Actual machine differs");
        List<FileRef> inputs = inputRefs(request);
        for (FileRef input : inputs) input.verify();
        Plan predecessor = read(request.predecessorRef(), Plan.class);
        Plan successor;
        try { successor = apply(predecessor, request); }
        catch (IllegalArgumentException invalid) { throw new IOException("SDK successor preimage rejected", invalid); }
        byte[] encoded = ControlBuild.strictMapper().writeValueAsBytes(successor);
        if (encoded.length > MAX_BYTES) throw new IOException("Bounded SDK source plan required");
        if (!ControlBuild.strictMapper().readValue(encoded, Plan.class).equals(successor)) throw new IOException("SDK source plan roundtrip differs");
        if (!destination.isAbsolute() || !destination.equals(destination.normalize()) || destination.getParent() == null
                || !Files.isDirectory(destination.getParent()) || Files.exists(destination)) throw new IOException("New canonical destination required");
        ProjectStoragePolicy.requireBulkOutput(destination.getParent()); SharedSourceFiles.plainAncestors(destination);
        guard.revalidate(encoded.length); requestRef.verify();
        Files.write(destination, encoded, StandardOpenOption.CREATE_NEW);
        FileRef result = FileRef.measure(destination);
        if (!read(result, Plan.class).equals(successor)) throw new IOException("Persisted SDK plan differs");
        for (FileRef input : inputs) input.verify();
        requestRef.verify(); guard.revalidate(0);
        try { requireReview(request, authority, Instant.now()); }
        catch (IllegalArgumentException invalid) { throw new IOException("SDK static-data authority expired after write", invalid); }
        return result;
    }

    private static <T> T read(FileRef ref, Class<T> type) throws IOException {
        if (ref.bytes() < 1 || ref.bytes() > MAX_BYTES) throw new IOException("Bounded exact metadata required");
        ref.verify(); T value = ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(ref.path())), type); ref.verify(); return value;
    }
    private static <T> void requireUpdate(boolean unique, T actual, T previous, T selected) {
        if (!unique || !Objects.equals(actual, previous) || Objects.equals(previous, selected))
            throw new IllegalArgumentException("Exact unchanged preimage, unique target and genuine change required");
    }
    private static String key(String value) { return value.replace('\\', '/').toLowerCase(Locale.ROOT); }
}
