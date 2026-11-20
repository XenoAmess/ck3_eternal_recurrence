package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
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
import org.xar.ck3.control.platform.LaunchSourceBinding;
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
        NativeLaunchPlan plan = RootProfileBootstrapCommand.readMappedSavedPlan(configuration.nativeLaunchPlan());
        plan.sources().verify(); plan.sources().requireLoadedClass(getClass());
        NativeInputs expected = request.nativeInputs(); var review = plan.sources().review();
        if (!review.gameExecutable().equals(expected.gameExecutable())
                || !review.bridgeDll().equals(expected.bridgeDll()) || !review.injector().equals(expected.injector()))
            throw new IOException("Actual host Game/DLL/injector differs from selected package inputs");
        requireHostNativeSources(review,expected);
        final NativeLaunchEvidence.Expected selected;
        try {
            selected = new NativeLaunchEvidence.Expected(request.machineId(),Path.of(expected.sourceRoot()),expected.completeSources(),
                    expected.bridgeDll(),expected.injector(),new NativeLaunchEvidence.Inputs(
                            expected.environmentActual(),expected.buildActual(),expected.registrationActual()));
        } catch (IllegalArgumentException | NullPointerException invalid) {
            throw new IOException("Invalid original package Native evidence inputs",invalid);
        }
        var actual = NativeLaunchEvidence.verifyOriginal(selected,nativeReader);
        if (!review.machineId().equals(request.machineId())
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
    private static void requireHostNativeSources(LaunchSourceBinding.Review review,NativeInputs expected) throws IOException {
        Path declared=review.nativeSourceRoot();
        if(declared==null||!declared.isAbsolute()||!declared.normalize().equals(declared))
            throw new IOException("Actual host Native source root is missing or invalid");
        Path hostRoot=declared.toRealPath(),selectedRoot=Path.of(expected.sourceRoot()).toRealPath();
        if(!Files.isDirectory(hostRoot)||!Files.isDirectory(selectedRoot)||!Files.isSameFile(hostRoot,selectedRoot))
            throw new IOException("Actual host Native source root differs from selected package inputs");
        // Runtime refs remain in Review. Only the actual Native subset must equal the package's complete cut.
        if(!nativeSourcePins(hostRoot,review.completeRuntimeSources(),true)
                .equals(nativeSourcePins(selectedRoot,expected.completeSources(),false)))
            throw new IOException("Actual host Native source cut differs from selected package inputs");
    }
    private static Map<String,FileRef> nativeSourcePins(Path root,List<FileRef> sources,boolean allowRuntimeSources) throws IOException {
        Map<String,FileRef> pins=new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        for(FileRef source:sources){
            Path physical=Path.of(source.path()).toRealPath();
            if(physical.equals(root))throw new IOException("Native source reference names the root directory");
            if(!physical.startsWith(root)){
                if(allowRuntimeSources)continue;
                throw new IOException("Selected Native source is physically outside its source root");
            }
            source.verify();
            var pin=new FileRef(physical.toString(),source.bytes(),source.sha256());
            if(pins.putIfAbsent(physical.toString(),pin)!=null)
                throw new IOException("Duplicate physical Native source reference");
        }
        return Map.copyOf(pins);
    }
    private static void retain(Map<String, FileRef> closure, FileRef source) throws IOException {
        String path = Path.of(source.path()).toRealPath().toString(); FileRef previous = closure.putIfAbsent(path, source);
        if (previous != null && !previous.equals(source)) throw new IOException("conflicting native source identity or path alias: " + path);
    }
}
