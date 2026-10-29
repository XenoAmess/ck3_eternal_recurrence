package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.runtime.JavaRuntimePackage;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.NativeInputs;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.NativeProof;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.Request;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.platform.NativeLaunchEvidence;
import org.xar.ck3.control.platform.NativeLaunchPlan;

/** A package proof is derived from the actual three-stage reader, never from persisted status. */
public final class RootPackageNativeVerifier implements JavaRuntimePackage.NativeAuthorityVerifier {
    private final NativeLaunchEvidence.Port nativeReader;
    public RootPackageNativeVerifier() { this(new org.xar.ck3.control.platform.NativeBridgeLaunchEvidence()); }
    public RootPackageNativeVerifier(NativeLaunchEvidence.Port nativeReader) {
        this.nativeReader = Objects.requireNonNull(nativeReader);
        if (nativeReader.getClass().isSynthetic() || nativeReader.getClass().isAnonymousClass())
            throw new IllegalArgumentException("named source-reviewed native stage reader required");
    }
    @Override public NativeProof verify(Request request, FileRef actualHostConfiguration) throws IOException {
        Objects.requireNonNull(request); Objects.requireNonNull(actualHostConfiguration); actualHostConfiguration.verify();
        if (actualHostConfiguration.bytes() != request.hostConfiguration().bytes()
                || !actualHostConfiguration.sha256().equals(request.hostConfiguration().sha256()))
            throw new IOException("physical host configuration differs from selected package input");
        RootApplicationConfiguration configuration = RootApplicationConfiguration.readExact(actualHostConfiguration);
        configuration.requireCurrent(java.time.Clock.systemUTC());
        if (!configuration.machineId().equals(request.machineId()) || configuration.mode() != request.launch().mode())
            throw new IOException("package host machine or mode differs from actual Root configuration");
        NativeLaunchPlan plan = NativeLaunchPlan.readExact(configuration.nativeLaunchPlan(), nativeReader);
        plan.sources().verify(); plan.sources().requireLoadedClass(getClass());
        NativeInputs expected = request.nativeInputs(); var actual = plan.sources().nativeProof(); var review = plan.sources().review();
        if (!review.machineId().equals(request.machineId())
                || !Path.of(expected.sourceRoot()).toRealPath().equals(actual.expected().sourceRoot().toRealPath())
                || !sameFiles(expected.completeSources(), actual.expected().completeSources())
                || !review.gameExecutable().equals(expected.gameExecutable())
                || !review.bridgeDll().equals(expected.bridgeDll()) || !review.injector().equals(expected.injector())
                || !actual.expected().inputs().references().equals(expected.stageActuals())
                || !plan.bridgeVersion().equals(expected.bridgeVersion()) || !plan.adapterId().equals(expected.adapterId())
                || !plan.preparedProfile().preparedInputs().contains(expected.launcherSettings()))
            throw new IOException("actual Native proof or reviewed Game/settings differs from selected package inputs");
        Map<String, FileRef> closure = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        for (FileRef source : actual.completeEvidenceClosure()) retain(closure, source);
        for (FileRef source : expected.mandatoryEvidence()) retain(closure, source);
        for (FileRef source : closure.values()) source.verify();
        plan.sources().verify(); actualHostConfiguration.verify();
        return new NativeProof(request.machineId(), request.launch().mode(), actualHostConfiguration, expected, List.copyOf(closure.values()));
    }
    private static boolean sameFiles(List<FileRef> expected, List<FileRef> actual) throws IOException {
        Map<String, FileRef> left = new TreeMap<>(String.CASE_INSENSITIVE_ORDER), right = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        for (FileRef source : expected) retain(left, source); for (FileRef source : actual) retain(right, source); return left.equals(right);
    }
    private static void retain(Map<String, FileRef> closure, FileRef source) throws IOException {
        String path = Path.of(source.path()).toRealPath().toString(); FileRef previous = closure.putIfAbsent(path, source);
        if (previous != null && !previous.equals(source)) throw new IOException("conflicting native source identity or path alias: " + path);
    }
}
