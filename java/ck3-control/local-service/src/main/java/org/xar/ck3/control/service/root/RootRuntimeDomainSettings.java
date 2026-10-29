package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.planning.military.M5PeacetimePolicy;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.platform.NormalExitSourceInventory;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.CoaVfs;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.g2.m0.RaiktorActualRecommendationFactory;

/** One explicit original for the remaining runtime's machine/path/policy settings. No setting has a fallback.
 * Required settings content is decoded by its owning codecs; historical references remain immutable DATA. */
public final class RootRuntimeDomainSettings {
    public static final String SCHEMA="xar.java-root-domain-settings/v6";
    public static final int MAXIMUM_BYTES=65536;
    public static final int MAXIMUM_POLICY_BYTES=16<<20;
    private RootRuntimeDomainSettings(){ }
    public record Lifecycle(String stateRoot,String saveGames,String tutorial,String evidenceRoot,
            List<String> expectedClockHandlers,long actionBudgetMillis) {
        public Lifecycle {
            for(String path:List.of(stateRoot,saveGames,tutorial,evidenceRoot))absolute(path);
            expectedClockHandlers=List.copyOf(expectedClockHandlers);
            require(!expectedClockHandlers.isEmpty()&&expectedClockHandlers.size()<=64
                    &&new HashSet<>(expectedClockHandlers).size()==expectedClockHandlers.size(),"explicit complete expected clock-handler inventory required");
            for(String handler:expectedClockHandlers)require(handler!=null&&handler.matches("[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}"),"bounded actual clock-handler identifier required");
            require(actionBudgetMillis>0&&actionBudgetMillis<=3600000,"explicit finite lifecycle action budget required");
        }
        public RootLifecycleRuntimeFactory.Configuration configuration(){return new RootLifecycleRuntimeFactory.Configuration(
                Path.of(stateRoot),Path.of(saveGames),Path.of(tutorial),Path.of(evidenceRoot),Set.copyOf(expectedClockHandlers),Duration.ofMillis(actionBudgetMillis));}
    }
    public record FormalWar(FileRef defaultBudget,FileRef defaultModel,FileRef budgetOverride,FileRef modelOverride) {
        public FormalWar {file(defaultBudget);file(defaultModel);if(budgetOverride!=null)file(budgetOverride);if(modelOverride!=null)file(modelOverride);}
        public List<FileRef> originals(){var refs=new ArrayList<>(List.of(defaultBudget,defaultModel));
            if(budgetOverride!=null)refs.add(budgetOverride);if(modelOverride!=null)refs.add(modelOverride);return List.copyOf(refs);}
        public RaiktorActualRecommendationFactory.Configuration loadConfiguration(){return RaiktorActualRecommendationFactory.loadConfiguration(
                new RaiktorActualRecommendationFactory.ConfigurationSources(formal(defaultBudget),formal(defaultModel),
                        Optional.ofNullable(budgetOverride).map(RootRuntimeDomainSettings::formal),Optional.ofNullable(modelOverride).map(RootRuntimeDomainSettings::formal)));}
    }
    public record Peacetime(boolean enabled,boolean giftEnabled,boolean familyEnabled) {
        public Peacetime {require(enabled&&giftEnabled&&familyEnabled,"complete migration retains all ordinary military/finance/family policies");}
        public M5PeacetimePolicy.Options options(){return new M5PeacetimePolicy.Options(enabled,giftEnabled,familyEnabled);}
    }
    /** Explicit original worker settings; these paths and bounds are not inferred from another domain's directory. */
    public record Offline(String workRoot,String knowledgeRoot,String grantsManifest,int queueCapacity,int retainedWorkMaximum) {
        public Offline {
            for(String value:List.of(workRoot,knowledgeRoot,grantsManifest))absolute(value);
            require(queueCapacity>=1&&queueCapacity<=32&&retainedWorkMaximum>=1&&retainedWorkMaximum<=4096,
                    "explicit finite offline queue and retained-work bounds required");
            require(!Path.of(workRoot).equals(Path.of(knowledgeRoot))&&Path.of(grantsManifest).getParent()!=null,
                    "offline work and knowledge roots must be distinct and the actual grants manifest must have a parent");
        }
        public RootOfflineAnalysisWorker.Settings configuration(){return new RootOfflineAnalysisWorker.Settings(
                new org.xar.ck3.control.service.OfflineAnalysisWorker.Settings(Path.of(workRoot),queueCapacity,retainedWorkMaximum),
                Path.of(knowledgeRoot),Path.of(grantsManifest));}
    }
    /** Three immutable originals are data custody only; actual Managed acceptance belongs to the sole inventory issuer. */
    public record NormalExitOriginals(ExactRef inventory,ExactRef originalManagedProfile,ExactRef immutableOriginalSettingsSnapshot) {
        public NormalExitOriginals {
            normalOriginal(inventory,false);normalOriginal(originalManagedProfile,false);normalOriginal(immutableOriginalSettingsSnapshot,true);
            require(!Path.of(inventory.path()).equals(Path.of(originalManagedProfile.path()))
                    &&!Path.of(inventory.path()).equals(Path.of(immutableOriginalSettingsSnapshot.path()))
                    &&!Path.of(originalManagedProfile.path()).equals(Path.of(immutableOriginalSettingsSnapshot.path())),
                    "normal-exit inventory, profile and immutable launch-settings snapshot require distinct actual originals");
        }
        public NormalExitSourceInventory.Input input(){return new NormalExitSourceInventory.Input(inventory,originalManagedProfile,immutableOriginalSettingsSnapshot);}
        public List<FileRef> originals(){return List.of(normalFile(inventory),normalFile(originalManagedProfile),normalFile(immutableOriginalSettingsSnapshot));}
    }
    /** The original is encoded/decoded only by the CoA VFS owner's strict Limits codec. */
    public record CoaReadLimits(FileRef original) {
        public CoaReadLimits {file(original);require(original.bytes()<=4096,"CoA read-limit original exceeds the sole codec's 4096-byte domain");}
        public CoaVfs.Limits limits()throws IOException {
            return CoaVfs.decodeLimits(new RawJson(RootRuntimeDefinitions.read(original,4096)));
        }
    }
    /** Public planning profile data only. These values do not mint any private action permission. */
    public record PlanFlags(
            @com.fasterxml.jackson.annotation.JsonProperty("allow_private_lifestyle_formal_trial") boolean lifestyleFormalTrial,
            @com.fasterxml.jackson.annotation.JsonProperty("allow_private_faction_gift_formal_trial") boolean factionGiftFormalTrial,
            @com.fasterxml.jackson.annotation.JsonProperty("allow_private_construction_formal_trial") boolean constructionFormalTrial,
            @com.fasterxml.jackson.annotation.JsonProperty("allow_private_family_marriage_formal_trial") boolean familyMarriageFormalTrial,
            @com.fasterxml.jackson.annotation.JsonProperty("allow_private_council_action") boolean councilAction,
            @com.fasterxml.jackson.annotation.JsonProperty("allow_private_m5_joint_collector") boolean m5JointCollector,
            @com.fasterxml.jackson.annotation.JsonProperty("require_initial_lifestyle_focus_before_date_advance") boolean initialLifestyleFocusRequired) { }
    /** Explicit source facts for the optional Stock read branch. These originals and bounds grant no admission. */
    public record StockRead(ExactRef pair,ExactRef pins,String nativeSourceCheckout,RootH2743StockPredicateAdmission.Limits limits) {
        public StockRead {
            normalOriginal(pair,false);normalOriginal(pins,false);absolute(nativeSourceCheckout);Objects.requireNonNull(limits);
            require(!Path.of(pair.path()).equals(Path.of(pins.path())),"Stock pair and pins require distinct original document paths");
        }
        public RootArmyStockReadRuntime.Configuration configuration(){
            return new RootArmyStockReadRuntime.Configuration(
                    new org.xar.ck3.control.application.planning.army.H2743StockPredicateAdmission.Input(
                            Path.of(pair.path()),Path.of(pins.path()),Path.of(nativeSourceCheckout)),limits,pair,pins);
        }
        public List<FileRef> originals(){return List.of(normalFile(pair),normalFile(pins));}
    }
    /** stockRead is a required nullable wire field: null explicitly leaves only that read branch unconfigured. */
    public record Configuration(String schema,String machineId,String observedAtUtc,String reviewAtUtc,
            Lifecycle lifecycle,String familyRelationExportRoot,FormalWar formalWar,Peacetime peacetime,Offline offline,NormalExitOriginals normalExit,CoaReadLimits coaReadLimits,ExactRef queryHistorySettings,PlanFlags planFlags,
            @com.fasterxml.jackson.annotation.JsonProperty(value="stock_read",required=true) StockRead stockRead) {
        public Configuration {
            require(SCHEMA.equals(schema),"exact remaining-domain settings version required");
            require(machineId!=null&&machineId.matches("[a-z0-9][a-z0-9-]{0,127}")&&!machineId.equals("unknown"),"actual domain-settings machine required");
            Instant observed=instant(observedAtUtc),review=instant(reviewAtUtc);
            require(observed.isBefore(review)&&Duration.between(observed,review).compareTo(Duration.ofDays(7))<=0,"finite reviewed domain settings required");
            Objects.requireNonNull(lifecycle);absolute(familyRelationExportRoot);Objects.requireNonNull(formalWar);Objects.requireNonNull(peacetime);Objects.requireNonNull(offline);Objects.requireNonNull(normalExit);Objects.requireNonNull(coaReadLimits);normalOriginal(queryHistorySettings,false);Objects.requireNonNull(planFlags);
            require(queryHistorySettings.bytes()<=org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings.MAX_BYTES,
                    "query-history document exceeds its unique codec's finite source lane");
        }
    }
    public static byte[] encode(Configuration explicit)throws IOException {
        Objects.requireNonNull(explicit);return StrictJson.canonical(ControlBuild.strictMapper().valueToTree(explicit),MAXIMUM_BYTES);
    }
    public static Configuration decode(byte[] original)throws IOException {
        try{var wire=StrictJson.parse(original,MAXIMUM_BYTES);
            require(wire.isObject()&&wire.has("stock_read"),"explicit nullable Stock configuration field required");
            return ControlBuild.strictMapper().readValue(original,Configuration.class);}
        catch(IllegalArgumentException invalid){throw new IOException("invalid strict remaining-domain settings wire",invalid);}
    }
    public static Bound readExact(FileRef original,Clock clock)throws IOException {
        Objects.requireNonNull(original);Objects.requireNonNull(clock);file(original);
        if(original.bytes()>MAXIMUM_BYTES)throw new IOException("domain settings exceed the bounded data lane");
        Configuration configuration=decode(RootRuntimeDefinitions.read(original,MAXIMUM_BYTES));
        requireMachine(configuration);
        var refs=new LinkedHashMap<Path,FileRef>();refs.put(Path.of(original.path()),original);
        var originalInputs=new ArrayList<>(configuration.formalWar().originals());originalInputs.addAll(configuration.normalExit().originals());
        originalInputs.add(configuration.coaReadLimits().original());configuration.coaReadLimits().limits();
        if(configuration.stockRead()!=null)originalInputs.addAll(configuration.stockRead().originals());
        try{originalInputs.addAll(queryHistoryOriginals(configuration));}
        catch(RuntimeException malformed){throw new IOException("invalid query-history configuration originals",malformed);}
        for(var ref:originalInputs){
            FileRef previous=refs.putIfAbsent(Path.of(ref.path()),ref);
            if(previous!=null&&!same(previous,ref))throw new IOException("one domain settings/policy original has conflicting exact refs");
        }
        return new Bound(original,configuration,List.copyOf(refs.values()));
    }
    public static final class Bound {
        private final FileRef original;private final Configuration configuration;private final List<FileRef> retainedOriginals;
        private Bound(FileRef original,Configuration configuration,List<FileRef> retainedOriginals){
            this.original=original;this.configuration=configuration;this.retainedOriginals=List.copyOf(retainedOriginals);}
        public FileRef original(){return original;}
        public Configuration configuration(){return configuration;}
        public void requireCurrent(Clock clock)throws IOException {
            Objects.requireNonNull(clock);
            requireMachine(configuration);
        }
        public void requireManagedRoots(RootRuntimeStorageGuard sameActualStorage)throws IOException {
            var lifecycle=configuration.lifecycle();sameActualStorage.requireManagedRoots(List.of(Path.of(lifecycle.stateRoot()),
                    Path.of(lifecycle.saveGames()),Path.of(lifecycle.evidenceRoot()),Path.of(configuration.familyRelationExportRoot())));
        }
        public List<FileRef> retainedOriginals(){return retainedOriginals;}
    }
    /** Leaf semantics belong to the one Native transport codec; these are retained source originals, not launch authority. */
    private static List<FileRef> queryHistoryOriginals(Configuration configuration)throws IOException {
        var original=normalFile(configuration.queryHistorySettings());
        var document=org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings.decode(
                RootRuntimeDefinitions.read(original,org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings.MAX_BYTES));
        var request=document.request();
        if(!configuration.machineId().equals(request.machineId()))
            throw new IOException("domain settings and query-history configuration belong to different machines");
        var result=new ArrayList<FileRef>();result.add(original);
        result.add(normalFile(document.sourceRefs().configurationOriginal()));result.add(normalFile(document.sourceRefs().producerOriginal()));
        if(request.configuration() instanceof org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings.LegacyCaptured legacy){
            result.add(normalFile(legacy.originalDriver()));
            if(legacy.admissionGuard() instanceof org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings.GuardValue guard)
                result.add(normalFile(guard.original()));
        }
        return List.copyOf(result);
    }
    private static FileRef normalFile(ExactRef value){return new FileRef(value.path(),value.bytes(),value.sha256());}
    private static void normalOriginal(ExactRef value,boolean mayBeEmpty){
        Objects.requireNonNull(value);absolute(value.path());require(value.bytes()>=(mayBeEmpty?0:1)&&value.bytes()<=MAXIMUM_POLICY_BYTES
                &&value.sha256()!=null&&value.sha256().matches("[0-9a-fA-F]{64}"),"bounded exact normal-exit original required");
    }
    private static RaiktorActualRecommendationFactory.FileRef formal(FileRef exact){return new RaiktorActualRecommendationFactory.FileRef(Path.of(exact.path()),exact.bytes(),exact.sha256());}
    private static void requireMachine(Configuration configuration)throws IOException {
        if(!configuration.machineId().equals(WindowsJobProcess.currentMachineId()))
            throw new IOException("actual remaining-domain settings belong to another machine");
    }
    private static Instant instant(String value){StrictJson.text(value);Instant parsed=Instant.parse(value);require(value.equals(parsed.toString()),"canonical UTC domain settings time required");return parsed;}
    private static void absolute(String value){StrictJson.text(value);Path path=Path.of(value);require(path.isAbsolute()&&path.normalize().equals(path),"normalized absolute domain path required");}
    private static void file(FileRef value){Objects.requireNonNull(value);absolute(value.path());require(value.bytes()>0&&value.bytes()<=MAXIMUM_POLICY_BYTES
            &&value.sha256()!=null&&value.sha256().matches("[0-9a-fA-F]{64}"),"actual bounded policy/configuration original required");}
    private static boolean same(FileRef left,FileRef right){return Path.of(left.path()).equals(Path.of(right.path()))&&left.bytes()==right.bytes()&&left.sha256().equalsIgnoreCase(right.sha256());}
    private static void require(boolean condition,String reason){if(!condition)throw new IllegalArgumentException(reason);}
}
