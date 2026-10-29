package org.xar.ck3.control.g2.context;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.wave2.runtime.closedadoption.RootColdResumeSession;
import org.xar.ck3.control.build.CanonicalColdWarmStage;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.FreshSdkFixtureStage;
import org.xar.ck3.control.build.SdkSourceAssembly;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.WindowsPreloadCustody;

/** Accepted software/runtime provenance; this class alone never grants Native authority. */
public final class RootNativeRuntimeBinding {
    public sealed interface RuntimeRequest permits Request, SavedMapRequest {
        String machineId(); Instant reviewAt(); ControlBuild.FileRef nativeBuildResult(); Path nativeSourceRoot();
        ControlBuild.FileRef gameExecutable(); ControlBuild.FileRef launcherSettings(); ControlBuild.FileRef nativeDll();
        ControlBuild.FileRef injector(); List<ControlBuild.FileRef> ownerProgramSources(); List<String> ownerArguments();
        long maximumSourceBytes();
    }
    /** The first map uses actual finite map/cold software qualification, without full SDK research steps. */
    public record SavedMapRequest(String machineId, Instant reviewAt, ControlBuild.FileRef nativeBuildResult,
            Path nativeSourceRoot, ControlBuild.FileRef gameExecutable, ControlBuild.FileRef launcherSettings,
            ControlBuild.FileRef nativeDll, ControlBuild.FileRef injector, ControlBuild.FileRef directBasePython,
            List<ControlBuild.FileRef> ownerProgramSources, List<String> ownerArguments, long maximumSourceBytes,
            RootNativeSoftwareQualification.Plan softwareQualification) implements RuntimeRequest {
        public SavedMapRequest {
            Objects.requireNonNull(machineId); Objects.requireNonNull(reviewAt); Objects.requireNonNull(nativeBuildResult);
            nativeSourceRoot=absolute(nativeSourceRoot); Objects.requireNonNull(gameExecutable); Objects.requireNonNull(launcherSettings);
            Objects.requireNonNull(nativeDll); Objects.requireNonNull(injector); Objects.requireNonNull(directBasePython);
            ownerProgramSources=List.copyOf(ownerProgramSources); ownerArguments=List.copyOf(ownerArguments);
            Objects.requireNonNull(softwareQualification);
            if(machineId.isBlank() || !machineId.equals(softwareQualification.machineId())
                    || reviewAt.isAfter(softwareQualification.deadline()) || maximumSourceBytes<1 || maximumSourceBytes>(1L<<30)
                    || ownerProgramSources.isEmpty() || ownerArguments.isEmpty()
                    || !Path.of(gameExecutable.path()).getFileName().toString().equalsIgnoreCase("ck3.exe")
                    || !Path.of(nativeDll.path()).getFileName().toString().equalsIgnoreCase("xar_ck3_bridge.dll")
                    || !Path.of(injector.path()).getFileName().toString().equalsIgnoreCase("xar_ck3_bridge_injector.exe"))
                throw new IllegalArgumentException("Exact finite saved map source/artifact plan required");
        }
    }
    public record Request(String machineId, Instant reviewAt,
            ControlBuild.FileRef freshActual, ControlBuild.FileRef canonicalActual,
            ControlBuild.FileRef assemblyActual, ControlBuild.FileRef nativeBuildResult,
            Path nativeSourceRoot, ControlBuild.FileRef gameExecutable,
            ControlBuild.FileRef launcherSettings,
            ControlBuild.FileRef nativeDll, ControlBuild.FileRef injector,
            List<ControlBuild.FileRef> ownerProgramSources, List<String> ownerArguments,
            long maximumSourceBytes) implements RuntimeRequest {
        public Request {
            Objects.requireNonNull(machineId); Objects.requireNonNull(reviewAt);
            Objects.requireNonNull(freshActual); Objects.requireNonNull(canonicalActual);
            Objects.requireNonNull(assemblyActual); Objects.requireNonNull(nativeBuildResult);
            Objects.requireNonNull(gameExecutable); Objects.requireNonNull(nativeDll); Objects.requireNonNull(injector);
            Objects.requireNonNull(launcherSettings);
            nativeSourceRoot = absolute(nativeSourceRoot); ownerProgramSources = List.copyOf(ownerProgramSources);
            ownerArguments = List.copyOf(ownerArguments);
            if (machineId.isBlank() || ownerProgramSources.isEmpty() || ownerArguments.isEmpty()
                    || maximumSourceBytes < 1 || maximumSourceBytes > (1L << 30)
                    || !Path.of(gameExecutable.path()).getFileName().toString().equalsIgnoreCase("ck3.exe")
                    || !Path.of(launcherSettings.path()).getFileName().toString().equals("launcher-settings.json")
                    || !Path.of(nativeDll.path()).getFileName().toString().equalsIgnoreCase("xar_ck3_bridge.dll")
                    || !Path.of(injector.path()).getFileName().toString().equalsIgnoreCase("xar_ck3_bridge_injector.exe")) {
                throw new IllegalArgumentException("Explicit original Game, Native artifacts and finite frozen source closure required");
            }
        }
    }
    private final RuntimeRequest request;
    private final Optional<RootColdResumeSession> coldSession;
    private final FreshSdkFixtureStage.Config fresh;
    private final Optional<RootNativeSoftwareQualification.Qualified> software;
    private final Optional<org.xar.ck3.control.build.MapVerticalSoftwareHost.MapVerticalSoftwareResult> mapSoftware;
    private final List<SharedSourceFiles.Witness> witnesses;
    private final List<ControlBuild.FileRef> completeSources;
    private final List<Path> nativeFiles;

    private RootNativeRuntimeBinding(RuntimeRequest request, FreshSdkFixtureStage.Config fresh,
            List<SharedSourceFiles.Witness> witnesses, List<ControlBuild.FileRef> completeSources,
            List<Path> nativeFiles, Optional<RootColdResumeSession> coldSession,
            Optional<RootNativeSoftwareQualification.Qualified> software,
            Optional<org.xar.ck3.control.build.MapVerticalSoftwareHost.MapVerticalSoftwareResult> mapSoftware) {
        this.software=software; this.mapSoftware=mapSoftware;
        this.coldSession = coldSession; this.request = request; this.fresh = fresh; this.witnesses = List.copyOf(witnesses);
        this.completeSources = List.copyOf(completeSources); this.nativeFiles = List.copyOf(nativeFiles);
    }

    /** Replays real accepted readers; JSON status flags or a source-only assembly cannot substitute. */
    public static RootNativeRuntimeBinding accept(Request request) throws IOException {
        return acceptBound(request, Optional.empty());
    }
    public static RootNativeRuntimeBinding accept(Request request, RootColdResumeSession session) throws IOException {
        return acceptBound(request, Optional.of(Objects.requireNonNull(session)));
    }
    private static RootNativeRuntimeBinding acceptBound(Request request, Optional<RootColdResumeSession> cold) throws IOException {
        Objects.requireNonNull(request); requireCurrent(request);
        FreshSdkFixtureStage.ResourceGuard guard = ignored -> requireCurrent(request);
        if (!FreshSdkFixtureStage.requireAccepted(Path.of(request.freshActual().path()), guard).equals(request.freshActual())
                || !CanonicalColdWarmStage.requireAccepted(Path.of(request.canonicalActual().path()), guard).equals(request.canonicalActual())) {
            throw new IOException("Exact accepted full SDK and complete canonical step are required");
        }
        FreshSdkFixtureStage.Actual actual = read(request.freshActual(), FreshSdkFixtureStage.Actual.class);
        FreshSdkFixtureStage.Config config = read(actual.configRef(), FreshSdkFixtureStage.Config.class);
        CanonicalColdWarmStage.Actual canonicalActual = read(request.canonicalActual(), CanonicalColdWarmStage.Actual.class);
        CanonicalColdWarmStage.Config canonical = read(canonicalActual.configRef(), CanonicalColdWarmStage.Config.class);
        if (!FreshSdkFixtureStage.SCHEMA.equals(config.schema())
                || !request.machineId().equals(config.machineId())
                || !config.selectedAssemblyActualRef().equals(request.assemblyActual())
                || canonical.bootstrapMode() != CanonicalColdWarmStage.BootstrapMode.ROOT_SOFTWARE_FIXTURE
                || !config.rootBootstrapRef().equals(canonical.rootBootstrapRef())
                || !config.pythonExecutable().equals(canonical.pythonExecutable())) {
            throw new IOException("Accepted SDK must be the explicitly selected new frozen launch graph");
        }
        FreshSdkFixtureStage.readProducerGoldenSources(config.producerGoldenPlanRef());
        SdkSourceAssembly.Actual assembly = SdkSourceAssembly.readActual(request.assemblyActual());
        Map<String, ControlBuild.FileRef> all = new LinkedHashMap<>();
        for (ControlBuild.FileRef ref : List.of(request.freshActual(), request.canonicalActual(), request.assemblyActual(),
                request.nativeBuildResult(), request.gameExecutable(), request.launcherSettings(), request.nativeDll(), request.injector(), actual.configRef(),
                canonicalActual.configRef(), config.rootBootstrapRef(), config.producerGoldenPlanRef())) add(all, ref);
        for (ControlBuild.FileRef ref : actual.sourcePins()) add(all, ref);
        for (SdkSourceAssembly.OutputSource source : assembly.actualSourceClosure()) add(all, source.actual());
        for (SdkSourceAssembly.DeploymentEvidence deployment : assembly.deploymentClosure()) {
            for (ControlBuild.FileRef ref : deployment.completeFiles()) add(all, ref);
            for (ControlBuild.FileRef ref : deployment.producerRuntime()) add(all, ref);
            add(all, deployment.javaExecutable());
        }
        if (cold.isPresent()) {
            var inputs = cold.orElseThrow().runtimeInputs();
            if (!inputs.sdkRoot().toRealPath().equals(Path.of(assembly.sdkRoot()).toRealPath()))
                throw new IOException("Saved cold SDK differs from the accepted full SDK physical graph");
            for (ControlBuild.FileRef ref : cold.orElseThrow().approvedProgramSources()) add(all, ref);
        }
        for (ControlBuild.FileRef ref : request.ownerProgramSources()) {
            if (!all.containsKey(real(ref.path()))) throw new IOException("MCP program source is outside accepted SDK closure");
            add(all, ref);
        }
        requireDirectEntry(request, assembly, cold);
        requireLoadedRuntimeSources(all);
        List<Path> nativeFiles = nativeFiles(request.nativeSourceRoot());
        for (Path file : nativeFiles) add(all, ControlBuild.FileRef.measure(file));
        verifyNativeBuild(request, nativeFiles);
        List<SharedSourceFiles.Witness> witnesses = new ArrayList<>(); long bytes = 0;
        for (ControlBuild.FileRef ref : all.values()) {
            bytes = Math.addExact(bytes, ref.bytes());
            if (bytes > request.maximumSourceBytes()) throw new IOException("Frozen launch source budget exceeded");
            ref.verify(); SharedSourceFiles.Witness witness = SharedSourceFiles.observe(Path.of(ref.path()));
            if (witness.source().bytes() != ref.bytes() || !witness.source().sha256().equals(ref.sha256())) throw new IOException("Frozen source changed while retained");
            witnesses.add(witness);
        }
        RootNativeRuntimeBinding binding = new RootNativeRuntimeBinding(request, config, witnesses,
                new ArrayList<>(all.values()), nativeFiles, cold, Optional.empty(), Optional.empty());
        binding.verify(); return binding;
    }

    /** Actual first-map branch: both software results were minted by real producers in this JVM. */
    public static RootNativeRuntimeBinding acceptSavedMap(SavedMapRequest request, RootColdResumeSession session,
            RootNativeSoftwareQualification.Qualified software,
            org.xar.ck3.control.build.MapVerticalSoftwareHost.MapVerticalSoftwareResult map) throws IOException {
        Objects.requireNonNull(request); Objects.requireNonNull(session); Objects.requireNonNull(software); Objects.requireNonNull(map);
        requireCurrent(request); software.requirePlan(request.softwareQualification()); map.verifyCurrent();
        Map<String,ControlBuild.FileRef> all=new LinkedHashMap<>();
        for(var ref:software.completeCodeSources()) add(all,ref);
        for(var ref:software.completeLoadedFiles()) add(all,ref);
        for(var ref:software.actualTerminals()) add(all,ref);
        for(var ref:session.approvedProgramSources()) add(all,ref);
        for(var ref:List.of(map.captureRef(),map.programRef(),map.runningRef(),map.proofRef(),
                request.nativeBuildResult(),request.gameExecutable(),request.launcherSettings(),request.nativeDll(),
                request.injector(),request.directBasePython())) add(all,ref);
        // All actual Python entry/import sources are qualified by the genuine original Root ticket
        // and current quoted output/profile guard; source refs declared by this request cannot add authority.
        List<ControlBuild.FileRef> original=session.approvedProgramSources();
        for(var ref:request.ownerProgramSources()) {
            if(!original.contains(ref)) throw new IOException("MCP source outside actual Root-approved SDK/quote closure");
            add(all,ref);
        }
        requireDirectEntry(request,Path.of(session.runtimeInputs().entrypoint().path()));
        requireLoadedRuntimeSources(all);
        List<Path> nativeFiles=nativeFiles(request.nativeSourceRoot());
        for(Path file:nativeFiles) add(all,ControlBuild.FileRef.measure(file));
        verifyNativeBuild(request,nativeFiles);
        List<SharedSourceFiles.Witness> witnesses=new ArrayList<>(); long bytes=0;
        for(var ref:all.values()) {
            bytes=Math.addExact(bytes,ref.bytes());
            if(bytes>request.maximumSourceBytes()) throw new IOException("Finite first-map exact source budget exceeded");
            ref.verify(); var witness=SharedSourceFiles.observe(Path.of(ref.path()));
            if(witness.source().bytes()!=ref.bytes() || !witness.source().sha256().equals(ref.sha256()))
                throw new IOException("First-map source changed while original resources were retained");
            witnesses.add(witness);
        }
        var binding=new RootNativeRuntimeBinding(request,null,witnesses,new ArrayList<>(all.values()),nativeFiles,
                Optional.of(session),Optional.of(software),Optional.of(map));
        binding.verify(); return binding;
    }
    private static void requireDirectEntry(RuntimeRequest request,Path selectedEntry) throws IOException {
        List<String> arguments=request.ownerArguments(); int index=0;
        while(index<arguments.size() && arguments.get(index).startsWith("-")) {
            String flag=arguments.get(index++);
            if(List.of("-B","-S","-I","-u").contains(flag)) continue;
            if(flag.equals("-X") && index<arguments.size() && arguments.get(index++).equals("utf8")) continue;
            throw new IOException("First-map MCP uses the exact direct quoted entry, not inline/module/shell source");
        }
        if(index>=arguments.size() || !real(arguments.get(index)).equals(real(selectedEntry.toString())))
            throw new IOException("First-map actual Root-quoted MCP entry differs");
        boolean pinned=false;
        for(var ref:request.ownerProgramSources()) if(real(ref.path()).equals(real(selectedEntry.toString()))) pinned=true;
        if(!pinned) throw new IOException("First-map actual entry is missing from the Root-approved invocation");
    }

    public RuntimeRequest request() { return request; }
    public void requireColdResumeSession(RootColdResumeSession actual) throws IOException {
        if (coldSession.orElse(null) != Objects.requireNonNull(actual))
            throw new IOException("Same private original Root cold session required; provenance alone grants no Game creation");
        actual.runtimeInputs(); verify();
    }
    public void requirePythonExecutable(ControlBuild.FileRef executable) throws IOException {
        boolean selected=request instanceof SavedMapRequest saved ? executable.equals(saved.directBasePython())
                : executable.equals(fresh.pythonExecutable()) || executable.equals(fresh.basePythonExecutable());
        if(!selected) throw new IOException("Exact accepted direct Python executable required");
        executable.verify();
    }
    public List<ControlBuild.FileRef> completeSources() { return completeSources; }
    public void verify() throws IOException {
        requireCurrent(request);
        if(software.isPresent()) software.orElseThrow().requireCurrent();
        if(mapSoftware.isPresent()) mapSoftware.orElseThrow().verifyCurrent();
        for (SharedSourceFiles.Witness witness : witnesses) SharedSourceFiles.assertUnchanged(witness);
        if (!nativeFiles(request.nativeSourceRoot()).equals(nativeFiles)) throw new IOException("Native build source inventory changed");
        verifyNativeBuild(request, nativeFiles);
    }
    /** Called before MCP CREATE: its constructor/receiver may read or persist Driver state. */
    public void requireOwnerSpecification(WindowsJobProcess.OwnedStdioSpec spec) throws IOException {
        Objects.requireNonNull(spec); verify();
        if (!spec.command().arguments().equals(request.ownerArguments())
                || !spec.programSourceRefs().equals(request.ownerProgramSources())
                ) {
            throw new IOException("Actual owned MCP program is outside the exact accepted frozen invocation");
        }
        requirePythonExecutable(spec.executableRef());
    }
    public void requireOwner(WindowsJobProcess.OwnedStdio channel) throws IOException {
        Objects.requireNonNull(channel); var spec = channel.spec(); requireOwnerSpecification(spec);
        if (!Path.of(channel.identity().executable()).toRealPath().equals(Path.of(spec.executableRef().path()).toRealPath())) {
            throw new IOException("Owned MCP image differs from its frozen executable");
        }
        if (!WindowsJobProcess.observeLiveProcess(channel.identity().pid()).identity().equals(channel.identity())) throw new IOException("Actual held MCP owner exited or changed");
    }
    private static void requireCurrent(RuntimeRequest request) throws IOException {
        if (!request.machineId().equals(WindowsJobProcess.currentMachineId()) || !Instant.now().isBefore(request.reviewAt())) {
            throw new IOException("Current machine and unexpired Root launch binding required");
        }
        request.nativeBuildResult().verify();
        if(request instanceof Request full) for(ControlBuild.FileRef ref:List.of(full.freshActual(),full.canonicalActual(),full.assemblyActual())) ref.verify();
        else ((SavedMapRequest)request).directBasePython().verify();
    }
    private static <T> T read(ControlBuild.FileRef ref, Class<T> type) throws IOException {
        ref.verify(); if (ref.bytes() < 1 || ref.bytes() > 16 * 1024 * 1024) throw new IOException("Bounded accepted runtime document required");
        byte[] raw = Files.readAllBytes(Path.of(ref.path())); T value = ControlBuild.strictMapper().readValue(raw, type); ref.verify(); return value;
    }
    private static void add(Map<String, ControlBuild.FileRef> values, ControlBuild.FileRef ref) throws IOException {
        String key = real(ref.path()); ControlBuild.FileRef prior = values.putIfAbsent(key, ref);
        if (prior != null && !prior.equals(ref)) throw new IOException("Conflicting source references in frozen runtime");
    }
    private static String real(String path) throws IOException { SharedSourceFiles.plainAncestors(Path.of(path)); return Path.of(path).toRealPath().toString(); }
    /** The same exact deployed class roster is consumed by production configuration selection and this live guard. */
    public static List<String> requiredRuntimeClassNames() {
        return List.of("org.xar.ck3.control.g2.context.RootNativeRuntimeBinding",
                "org.xar.ck3.control.g2.context.RootNativeMapMain",
                "org.xar.ck3.control.g2.context.RootNativeSoftwareQualification",
                "org.xar.ck3.control.build.MapVerticalSoftwareHost",
                "org.xar.ck3.control.contracts.NativeColdAdoptionProjection",
                "org.xar.ck3.control.g2.context.RootNativePreloadAuthority",
                "org.xar.ck3.control.g2.context.RootNativeMapLaunch",
                "org.xar.ck3.control.g2.context.G2WindowsRootSources",
                "org.xar.ck3.control.g2.context.RootSteamOfflineGate",
                "org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider",
                "org.xar.ck3.control.g2.context.RootMcpSemanticClient",
                "org.xar.ck3.control.g2.context.RootMcpWire",
                "org.xar.ck3.control.g2.context.RootMcpEnvelope",
                "org.xar.ck3.control.g2.context.RootMcpRawWire",
                "org.xar.ck3.control.g2.context.RootSavedLoadReadiness",
                "org.xar.ck3.control.build.WindowsPreloadCustody",
                "org.xar.ck3.control.build.WindowsJobProcess",
                "org.xar.ck3.control.wave2.runtime.closedadoption.RootColdResumeSession",
                "org.xar.ck3.control.wave2.runtime.closedadoption.RootColdStageReview",
                "org.xar.ck3.control.wave2.runtime.closedadoption.ColdStageAttempts",
                "org.xar.ck3.control.wave2.runtime.closedadoption.ColdModAbsenceProof",
                "org.xar.ck3.control.wave2.runtime.closedadoption.NativeOwnerResumeSession",
                "org.xar.ck3.control.wave2.runtime.closedadoption.ClosedInputsSessionAuthority",
                "org.xar.ck3.control.wave2.runtime.closedadoption.OriginalWriterTransaction",
                "org.xar.ck3.control.wave2.runtime.closedadoption.ColdRawRestoreQualification",
                "org.xar.ck3.control.wave2.runtime.closedadoption.ColdRestoreProfile",
                "org.xar.ck3.control.wave2.runtime.closedadoption.RawRestoreAdmissionReducer",
                "org.xar.ck3.control.wave2.runtime.savedproof.SavedCheckpointMeasurementCoordinator",
                "org.xar.ck3.control.g2.context.RootNativeGameLaunch",
                "org.xar.ck3.control.platform.NativeLaunchPolicy",
                "org.xar.ck3.control.build.ProjectStoragePolicy",
                "org.xar.ck3.control.application.readiness.NativeSourceFileIdentity",
                "org.xar.ck3.control.application.readiness.NativeSourceProofDocument",
                "org.xar.ck3.control.application.readiness.NativeSourceProofCodec",
                "org.xar.ck3.control.service.root.RootNativeSourceProofProducer",
                "org.xar.ck3.control.service.root.RootArchivedNativeSourceReader",
                "org.xar.ck3.control.service.root.RootSourceProofContinuity",
                "org.xar.ck3.control.service.root.RootPublicPausePublicResult",
                "org.xar.ck3.control.service.root.RootPublicPauseArchiveClassifier",
                "org.xar.ck3.control.application.history.DriverPublicExecuteFailureMaterial",
                "org.xar.ck3.control.application.history.DriverPublicExecuteFailureRowProducer",
                "org.xar.ck3.control.application.history.DriverEarlyExecuteFailure",
                "org.xar.ck3.control.application.history.DriverEarlyExecuteFailureRowProducer",
                "org.xar.ck3.control.service.root.RootPublicStepFailureOriginals",
                "org.xar.ck3.control.platform.SteamOfflineProbe",
                "org.xar.ck3.control.platform.SteamOfflineProfiles",
                "org.xar.ck3.control.platform.SteamOfflineObservation",
                "org.xar.ck3.control.platform.SteamOfflineObservationCodec",
                "org.xar.ck3.control.platform.SteamOfflineCefProvider",
                "org.xar.ck3.control.platform.SteamOfflineCefWire",
                "org.xar.ck3.control.platform.Win32Host",
                "org.xar.ck3.control.application.checkpoint.RestoreCheckpointService",
                "org.xar.ck3.control.application.checkpoint.RestoredEpisodeOriginData",
                "org.xar.ck3.control.application.planning.OriginalTerminalPlanning",
                "org.xar.ck3.control.application.planning.campaign.PublicTerminalDataContext");
    }
    private static void requireLoadedRuntimeSources(Map<String, ControlBuild.FileRef> accepted) throws IOException {
        for(String name:requiredRuntimeClassNames())requireLoadedRuntimeSource(name,accepted);
    }
    /** Shared actual membership boundary; tests may measure loaded artifacts but cannot create a binding. */
    static void requireLoadedRuntimeSource(String name, Map<String, ControlBuild.FileRef> accepted) throws IOException {
        try {
            Class<?> anchor = Class.forName(name, false, RootNativeRuntimeBinding.class.getClassLoader());
            Path location = Path.of(anchor.getProtectionDomain().getCodeSource().getLocation().toURI());
            Path loaded = Files.isDirectory(location) ? location.resolve(anchor.getName().replace('.', '/') + ".class") : location;
            if (!accepted.containsKey(real(loaded.toString()))) throw new IOException("Loaded Native Root code is outside accepted deployment: " + anchor.getName());
        } catch (ClassNotFoundException | java.net.URISyntaxException | NullPointerException unavailable) {
            throw new IOException("Exact loaded Native Root code source unavailable", unavailable);
        }
    }
    private static void requireDirectEntry(Request request, SdkSourceAssembly.Actual assembly, Optional<RootColdResumeSession> cold) throws IOException {
        List<String> arguments = request.ownerArguments(); int index = 0;
        while (index < arguments.size() && arguments.get(index).startsWith("-")) {
            String flag = arguments.get(index++);
            if (List.of("-B", "-S", "-I", "-u").contains(flag)) continue;
            if (flag.equals("-X") && index < arguments.size() && arguments.get(index++).equals("utf8")) continue;
            throw new IOException("Native MCP owner must execute a pinned direct entry, never inline/module/shell source");
        }
        if (index >= arguments.size()) throw new IOException("Actual direct MCP entry operand missing");
        Path entry = Path.of(arguments.get(index));
        if (!entry.isAbsolute() || !entry.getFileName().toString().endsWith(".py")) throw new IOException("Pinned absolute original Python entry required");
        String actual = real(entry.toString()); boolean pinned = false;
        Path selectedEntry = cold.isPresent() ? Path.of(cold.orElseThrow().runtimeInputs().entrypoint().path())
                : Path.of(assembly.graphRoot()).resolve("ck3_autonomous_player/mcp_server.py");
        if (!actual.equals(real(selectedEntry.toString()))) throw new IOException("Original selected MCP production entry required");
        for (ControlBuild.FileRef source : request.ownerProgramSources()) if (real(source.path()).equals(actual)) pinned = true;
        if (!pinned) throw new IOException("Actual direct entry does not belong to accepted owner source closure");
    }
    private static Path absolute(Path path) {
        Objects.requireNonNull(path); if (!path.isAbsolute() || !path.normalize().equals(path)) throw new IllegalArgumentException("Normalized absolute root required"); return path;
    }
    private static List<Path> nativeFiles(Path root) throws IOException {
        SharedSourceFiles.plainAncestors(root); List<Path> files = new ArrayList<>(); files.add(root.resolve("CMakeLists.txt"));
        for (String tree : List.of("include", "src")) try (var walk = Files.walk(root.resolve(tree))) {
            for (Path file : walk.toList()) {
                SharedSourceFiles.plainAncestors(file);
                if (Files.isRegularFile(file)) {
                    String name = file.getFileName().toString().toLowerCase(Locale.ROOT);
                    if (name.endsWith(".cpp") || name.endsWith(".hpp") || name.endsWith(".h") || name.endsWith(".c")) files.add(file.toRealPath());
                }
                if (files.size() > 8192) throw new IOException("Native source inventory exceeds explicit finite limit");
            }
        }
        files.sort(Comparator.comparing(path -> path.toString().toLowerCase(Locale.ROOT))); return List.copyOf(files);
    }
    /** Matches the existing C++ producer's build_fresh.py:78–94 inventory/fingerprint. */
    private static void verifyNativeBuild(RuntimeRequest request, List<Path> files) throws IOException {
        request.nativeBuildResult().verify();
        if (request.nativeBuildResult().bytes() > 131072) throw new IOException("Bounded original Native build result required");
        JsonNode build = ControlBuild.strictMapper().readTree(Files.readAllBytes(Path.of(request.nativeBuildResult().path())));
        if (!text(build, "status").equals("ready") || !text(build, "build_status").equals("build_succeeded")
                || !build.path("tests_ran").isBoolean() || !build.path("tests_ran").booleanValue()
                || !text(build, "test_scope").equals("all-native-offline")
                || !text(build, "dependency_gate").equals("ck3_11906.hpp-recorded")
                || !real(text(build, "dll_path")).equals(real(request.nativeDll().path()))
                || !real(text(build, "injector_path")).equals(real(request.injector().path()))
                || !text(build, "dll_sha256").equalsIgnoreCase(request.nativeDll().sha256())
                || !text(build, "injector_sha256").equalsIgnoreCase(request.injector().sha256())) throw new IOException("Original full Native build output differs from selected artifacts");
        List<String> lines = new ArrayList<>();
        for (Path file : files) {
            String relative = request.nativeSourceRoot().relativize(file).toString();
            if (!relative.chars().allMatch(c -> c > 0 && c < 128)) throw new IOException("Unsupported Native inventory filename encoding");
            lines.add(relative + '\0' + ControlBuild.FileRef.measure(file).sha256().toUpperCase(Locale.ROOT));
        }
        String fingerprint;
        try { fingerprint = HexFormat.of().withUpperCase().formatHex(MessageDigest.getInstance("SHA-256").digest(String.join("\n", lines).getBytes(StandardCharsets.UTF_8))); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
        if (!fingerprint.equalsIgnoreCase(text(build, "source_fingerprint_sha256"))) throw new IOException("Complete Native source fingerprint differs from original build");
        request.nativeDll().verify(); request.injector().verify(); request.nativeBuildResult().verify();
    }
    private static String text(JsonNode object, String key) throws IOException {
        JsonNode value = object.get(key); if (value == null || !value.isTextual() || value.textValue().isBlank()) throw new IOException("Native build field missing/wrong type: " + key); return value.textValue();
    }
}

