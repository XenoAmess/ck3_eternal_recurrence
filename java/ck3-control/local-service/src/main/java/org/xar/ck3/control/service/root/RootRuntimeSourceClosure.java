package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;

/** Retains the actual configured producer/input identities between preparation and native admission.
 * This is source custody only: it grants no Game, reducer, restore, action or Ready authority. */
public final class RootRuntimeSourceClosure {
    private static final int MAXIMUM_INPUTS = 8192;
    private final List<SharedSourceFiles.Witness> retained;
    private final List<Path> absent;

    private RootRuntimeSourceClosure(List<SharedSourceFiles.Witness> retained, List<Path> absent) {
        this.retained = List.copyOf(retained);
        this.absent = List.copyOf(absent);
    }

    /** The SDK owns the one configured-source enumeration and validates the actual winner graph. */
    public static RootRuntimeSourceClosure capture(RootRuntimeDefinitions.Inputs inputs,
            RootFrontendRuntime.Sources actualFrontend) throws IOException {
        Objects.requireNonNull(inputs);Objects.requireNonNull(actualFrontend);
        var configuration = inputs.configuration();
        RootRuntimeDefinitions.verifySources(configuration, inputs.sourceIndex());
        var references = new ArrayList<FileRef>();
        references.add(inputs.originalRef());
        references.add(configuration.applicationRef());
        references.add(configuration.storageLeaseRef());
        references.add(configuration.nativeLaunchPlanRef());
        references.add(configuration.runtimePackageRequestRef());
        references.add(configuration.sourceIndex().compressedRef());
        references.add(RootRuntimeDefinitions.sourceIndexOriginalInput(configuration.sourceIndex()));
        var lease = inputs.storageLease();
        references.addAll(List.of(lease.policyRef(), lease.capacityReleaseRef(), lease.runtimeBindingRef(),
                lease.wholeWorkpackageCensusRef()));
        for (var source : RootRuntimeDefinitions.configuredSources(configuration))
            references.add(file(source.sourceRef()));
        for (var data : configuration.originalData()) references.add(data.originalRef());
        for (ExactRef original : actualFrontend.initialPolicy().evidenceClosure()) references.add(file(original));
        for (var grant : inputs.eventSources().evidenceGrants())
            references.add(new FileRef(grant.path().toString(), grant.bytes(), grant.sha256()));
        var history = configuration.crossRun().originalOneLifeHistory();
        List<Path> missing;
        if (history.originalRef() == null) missing = List.of(Path.of(history.path()));
        else {
            references.add(history.originalRef());
            missing = List.of();
        }
        return captureReferences(references, missing);
    }

    /** Mechanical input custody, also exercised with real temporary files by the regression suite. */
    static RootRuntimeSourceClosure captureReferences(List<FileRef> references, List<Path> absent) throws IOException {
        Objects.requireNonNull(references);
        Objects.requireNonNull(absent);
        if (references.isEmpty() || references.size() > MAXIMUM_INPUTS || absent.size() > 64)
            throw new IOException("bounded nonempty configured runtime source/input closure required");
        var unique = new LinkedHashMap<Path, FileRef>();
        for (FileRef reference : references) {
            Objects.requireNonNull(reference);
            Path path = absolute(Path.of(reference.path()));
            FileRef previous = unique.putIfAbsent(path, reference);
            if (previous != null && !same(previous, reference))
                throw new IOException("one runtime source/input path has conflicting exact references: " + path);
        }
        var missing = new ArrayList<Path>();
        for (Path input : absent) {
            Path path = absolute(input);
            if (unique.containsKey(path)) throw new IOException("runtime input cannot be present and absent: " + path);
            if (!missing.contains(path)) missing.add(path);
        }
        var retained = new ArrayList<SharedSourceFiles.Witness>();
        for (var entry : unique.entrySet()) {
            SharedSourceFiles.Witness actual = SharedSourceFiles.observe(entry.getKey());
            if (!same(entry.getValue(), actual.source()))
                throw new IOException("actual runtime input differs from its exact configured producer: " + entry.getKey());
            retained.add(actual);
        }
        var result = new RootRuntimeSourceClosure(retained, missing);
        // Revalidate the whole retained closure after the final capture, rather than blessing a mixed-time set.
        result.requireCurrent();
        return result;
    }

    public void requireCurrent() throws IOException {
        for (var witness : retained) SharedSourceFiles.assertUnchanged(witness);
        for (Path path : absent) {
            SharedSourceFiles.plainAncestors(path.getParent());
            if (Files.exists(path, LinkOption.NOFOLLOW_LINKS))
                throw new IOException("explicitly absent original history appeared after runtime preparation: " + path);
        }
    }

    public int retainedInputCount() { return retained.size(); }

    private static FileRef file(ExactRef reference) {
        return new FileRef(reference.path(), reference.bytes(), reference.sha256());
    }

    private static Path absolute(Path path) throws IOException {
        if (!path.isAbsolute() || !path.normalize().equals(path))
            throw new IOException("normalized absolute configured runtime input path required");
        return path;
    }

    private static boolean same(FileRef left, FileRef right) {
        return Path.of(left.path()).equals(Path.of(right.path())) && left.bytes() == right.bytes()
                && left.sha256().equalsIgnoreCase(right.sha256());
    }
}
