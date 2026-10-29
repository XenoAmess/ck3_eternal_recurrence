package org.xar.ck3.control.platform;

import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.LinkedHashMap;
import org.xar.ck3.control.build.NativeRunProfileManifest;
import org.xar.ck3.control.build.NativeRunProfileManifest.ProfileKind;
import java.io.IOException;
import java.nio.file.Files;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Set;
import com.fasterxml.jackson.databind.JsonNode;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.ControlBuild;

/** Exact CK3 launch arguments; ContinueLastSave is deliberately not an ambiguous restore route. */
public record NativeLaunchPlan(String requestId, String sessionId, LaunchSourceBinding sources,
        Path profileDirectory, Path stateDirectory, Path evidenceRoot, String pipeName,
        String bridgeVersion, String adapterId, Load load, boolean debugMode, WindowPolicy windowPolicy,
        Map<String,String> environment, long gameMemoryBytes, long injectorMemoryBytes,
        Instant deadline, Duration injectorTimeout, Duration startupTimeout,
        SteamOfflineProbe.Plan steam, PreparedProfile preparedProfile, int maximumEvidenceRows) {
    public sealed interface Load permits NewGame, SavedGame { }
    public enum WindowPolicy { MINIMIZED_NO_ACTIVATE, SHOWN_NO_ACTIVATE }
    /** Explicit profile settings used to form actual launch arguments. */
    public static final class PreparedProfile {
        public sealed interface Declaration permits OrdinaryProduction,ExplicitEnvironment,NoMods { }
        public record OrdinaryProduction(Path productionRoot,String enabledOuterDescriptorRef,
                List<ControlBuild.FileRef> completeProductionFiles) implements Declaration {
            public OrdinaryProduction {
                Objects.requireNonNull(productionRoot);Objects.requireNonNull(enabledOuterDescriptorRef);
                completeProductionFiles=List.copyOf(completeProductionFiles);
                if(!absolute(productionRoot)||enabledOuterDescriptorRef.isBlank())throw new IllegalArgumentException("exact ordinary singleton production required");
            }
        }
        public record ExplicitEnvironment(ProfileKind kind,List<Path> productionRoots) implements Declaration {
            public ExplicitEnvironment {
                Objects.requireNonNull(kind);productionRoots=List.copyOf(productionRoots);
                if(kind==ProfileKind.ORDINARY_PRODUCTION||productionRoots.stream().anyMatch(path->!absolute(path))
                        ||productionRoots.stream().distinct().count()!=productionRoots.size()
                        ||(kind==ProfileKind.SAVED_VANILLA?!productionRoots.isEmpty():productionRoots.isEmpty()))
                    throw new IllegalArgumentException("explicit profile kind and its real production roots required");
            }
        }
        public record NoMods() implements Declaration { }
        private final Optional<ControlBuild.FileRef> environmentManifest;
        private final List<ControlBuild.FileRef> preparedInputs;
        private final Declaration declaration;
        /** Historical ordinary production constructor and its strict domain remain available. */
        public PreparedProfile(ControlBuild.FileRef environmentManifest,Path productionRoot,String enabledOuterDescriptorRef,
                List<ControlBuild.FileRef> preparedInputs,List<ControlBuild.FileRef> completeProductionFiles) {
            this(Optional.of(environmentManifest),preparedInputs,new OrdinaryProduction(productionRoot,enabledOuterDescriptorRef,completeProductionFiles));
        }
        private PreparedProfile(ControlBuild.FileRef environmentManifest,List<ControlBuild.FileRef> preparedInputs,Declaration declaration) {
            this(Optional.of(Objects.requireNonNull(environmentManifest)),preparedInputs,declaration);
        }
        private PreparedProfile(Optional<ControlBuild.FileRef> environmentManifest,List<ControlBuild.FileRef> preparedInputs,Declaration declaration) {
            this.environmentManifest=Objects.requireNonNull(environmentManifest);this.preparedInputs=List.copyOf(preparedInputs);this.declaration=Objects.requireNonNull(declaration);
        }
        /** Data declaration only; no historical environment qualification is performed at launch. */
        public static PreparedProfile explicit(ControlBuild.FileRef environmentManifest,ProfileKind kind,
                List<Path> productionRoots,List<ControlBuild.FileRef> preparedInputs) {
            return new PreparedProfile(environmentManifest,preparedInputs,new ExplicitEnvironment(kind,productionRoots));
        }
        public ControlBuild.FileRef environmentManifest(){return environmentManifest.orElseThrow(()->new IllegalStateException("No environment manifest for NoMods profile"));}
        public Optional<ControlBuild.FileRef> optionalEnvironmentManifest(){return environmentManifest;}
        public List<ControlBuild.FileRef> preparedInputs(){return preparedInputs;}
        public Declaration declaration(){return declaration;}
        public ProfileKind kind(){if(declaration instanceof NoMods)throw new IllegalStateException("NoMods has no ProfileKind");return declaration instanceof OrdinaryProduction?ProfileKind.ORDINARY_PRODUCTION:((ExplicitEnvironment)declaration).kind();}
        public List<Path> productionRoots(){if(declaration instanceof NoMods)return List.of();return declaration instanceof OrdinaryProduction value?List.of(value.productionRoot()):((ExplicitEnvironment)declaration).productionRoots();}
        public Optional<OrdinaryProduction> ordinary(){return declaration instanceof OrdinaryProduction value?Optional.of(value):Optional.empty();}
        public Optional<ExplicitEnvironment> explicit(){return declaration instanceof ExplicitEnvironment value?Optional.of(value):Optional.empty();}
        public Optional<NoMods> noMods(){return declaration instanceof NoMods value?Optional.of(value):Optional.empty();}
        private OrdinaryProduction singleton(){return ordinary().orElseThrow(()->new IllegalStateException("explicit profile has no ordinary singleton projection"));}
        public Path productionRoot(){return singleton().productionRoot();}
        public String enabledOuterDescriptorRef(){return singleton().enabledOuterDescriptorRef();}
        public List<ControlBuild.FileRef> completeProductionFiles(){return singleton().completeProductionFiles();}
        public static PreparedProfile vanilla(){return new PreparedProfile(Optional.empty(),List.of(),new NoMods());}
        @Override public boolean equals(Object value){return value instanceof PreparedProfile other&&environmentManifest.equals(other.environmentManifest)&&preparedInputs.equals(other.preparedInputs)&&declaration.equals(other.declaration);}
        @Override public int hashCode(){return Objects.hash(environmentManifest,preparedInputs,declaration);}

        /** Real producer-to-consumer projection; later request/startup originals stay outside the earlier ENV. */
        public static PreparedProfile fromExplicitEnvironment(ControlBuild.FileRef environmentManifest,
                List<ControlBuild.FileRef> additionalInputs)throws IOException {
            Objects.requireNonNull(additionalInputs);
            byte[] raw;
            try(var input=Files.newInputStream(Path.of(environmentManifest.path()))) { raw=input.readNBytes(1048577); }
            if(raw.length==0||raw.length>1048576)throw new IOException("Bounded explicit profile configuration required");
            var explicit=ControlBuild.strictMapper().readValue(raw,NativeRunProfileManifest.ExplicitManifest.class);
            var inputs=new LinkedHashMap<Path,ControlBuild.FileRef>();
            var required=new ArrayList<>(explicit.requiredPreparedFileRefs());
            required.add(explicit.request().vanillaRules());required.add(explicit.request().launcherSettings());
            for(var ref:required)addInput(inputs,ref);
            for(var ref:additionalInputs)addInput(inputs,ref);
            return explicit(environmentManifest,explicit.kind(),explicit.productionRoots().stream().map(Path::of).toList(),List.copyOf(inputs.values()));
        }
        private static void addInput(Map<Path,ControlBuild.FileRef> inputs,ControlBuild.FileRef ref)throws IOException {
            Path actual=Path.of(ref.path()).normalize();var prior=inputs.putIfAbsent(actual,ref);
            if(prior!=null&&!prior.equals(ref))throw new IOException("conflicting prepared input originals");
        }
        /** Compatibility hook: prepared profile is configuration, not a launch qualification. */
        public void verify(NativeLaunchPlan plan)throws IOException {
            Objects.requireNonNull(plan);
        }
    }
    /** Same-plan loaded deployment closure, including the actual domain branch classes. */
    public static List<Class<?>> requiredPreparedProfileTypes() {
        return List.of(NativeLaunchPlan.class,PreparedProfile.class,PreparedProfile.Declaration.class,
                PreparedProfile.OrdinaryProduction.class,PreparedProfile.ExplicitEnvironment.class,PreparedProfile.NoMods.class);
    }
    public record NewGame() implements Load { }
    public record SavedGame(String basename, ControlBuild.FileRef save) implements Load {
        public SavedGame {
            Objects.requireNonNull(save);
            if (basename == null || basename.isEmpty() || basename.length()>251 || basename.indexOf('.')>=0
                    || basename.indexOf('/')>=0 || basename.indexOf('\\')>=0 || basename.indexOf('\0')>=0
                    || !Path.of(save.path()).getFileName().toString().equals(basename + ".ck3"))
                throw new IllegalArgumentException("Exact save basename and original .ck3 source required");
        }
    }
    public NativeLaunchPlan {
        Objects.requireNonNull(sources); Objects.requireNonNull(load); Objects.requireNonNull(steam);
        Objects.requireNonNull(windowPolicy); Objects.requireNonNull(preparedProfile);
        Objects.requireNonNull(deadline); Objects.requireNonNull(injectorTimeout); Objects.requireNonNull(startupTimeout);
        environment = NativeLaunchPolicy.requireEnvironment(environment, pipeName);
        if (requestId == null || requestId.isBlank() || sessionId == null || sessionId.isBlank()
                || !absolute(profileDirectory) || !absolute(stateDirectory) || !absolute(evidenceRoot)
                || pipeName == null || !pipeName.startsWith("\\\\.\\pipe\\") || pipeName.length() <= 9
                || bridgeVersion == null || bridgeVersion.isBlank() || adapterId == null || adapterId.isBlank())
            throw new IllegalArgumentException("Required Java Game launch configuration missing");
    }
    public List<String> gameArguments() {
        return arguments(profileDirectory,load,debugMode);
    }
    /** Reads ordinary launch configuration; it does not requalify historical build evidence. */
    public static NativeLaunchPlan readExact(org.xar.ck3.control.contracts.ExactRef source,NativeLaunchEvidence.Port nativeReader)throws IOException{
        return NativeLaunchPlanCodec.readExact(source,nativeReader);
    }
    /** One exact Saved child plan for checkpoint restore and immutable seed replacement. */
    public NativeLaunchPlan savedReplacement(String parentLifecycleIntentId,ControlBuild.FileRef save,Instant requestedDeadline)throws IOException{
        Objects.requireNonNull(save);Objects.requireNonNull(requestedDeadline);
        Path path=Path.of(save.path());String name=path.getFileName().toString();
        if(!name.endsWith(".ck3")||!path.normalize().getParent().equals(profileDirectory.resolve("save games").normalize()))throw new IOException("Replacement SAVE must be the exact original configured profile file");
        String child=JavaGameLifecycle.replacementRequestId(parentLifecycleIntentId);
        Instant until=requestedDeadline.isBefore(deadline)?requestedDeadline:deadline;
        return new NativeLaunchPlan(child,"session-"+child,sources,profileDirectory,stateDirectory,
                evidenceRoot.getParent().resolve(child),pipeName,bridgeVersion,adapterId,new SavedGame(name.substring(0,name.length()-4),save),
                debugMode,windowPolicy,environment,gameMemoryBytes,injectorMemoryBytes,until,injectorTimeout,startupTimeout,steam,preparedProfile,maximumEvidenceRows);
    }
    static List<String> arguments(Path profileDirectory,Load load,boolean debugMode) {
        List<String> args = new ArrayList<>();
        if (debugMode) args.add("-debug_mode");
        args.add("-gdpr-compliant"); args.add("-userdir=" + profileDirectory);
        if (load instanceof SavedGame saved) args.add("-loadsave=" + saved.basename());
        return List.copyOf(args);
    }
    private static boolean absolute(Path path) { return path != null && path.isAbsolute() && path.normalize().equals(path); }
}
