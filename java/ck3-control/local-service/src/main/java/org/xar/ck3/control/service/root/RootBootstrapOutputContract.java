package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.FormalReleaseProducer.Layout;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.StrictJson;

/** Independent finite immutable input authority. It is neither a runtime lease nor a continuity ledger.
 * Sole budget issuer signs actual financial capacity after the real small asset-root census. */
public final class RootBootstrapOutputContract {
    public static final String DECLARATION="xar.java-root-bootstrap-declaration/v4";
    public static final String CENSUS="xar.java-root-bootstrap-asset-census/v4";
    public static final String CAPACITY="xar.java-root-bootstrap-capacity/v4";
    public static final String BINDING="xar.java-root-bootstrap-binding/v4";
    public static final String PURPOSE="ROOT_BOOTSTRAP_IMMUTABLE_INPUTS";
    public static final String ISSUER="/root/budget_fast_lane";
    public static final String FORMAL_DECLARATION="xar.java-root-bootstrap-formal-release-declaration/v2";
    public static final String FORMAL_CENSUS="xar.java-root-bootstrap-formal-release-census/v2";
    public static final String FORMAL_CAPACITY="xar.java-root-bootstrap-formal-release-capacity/v2";
    public static final String FORMAL_BINDING="xar.java-root-bootstrap-formal-release-binding/v2";
    public static final String FORMAL_PURPOSE="ROOT_FORMAL_RELEASE_PAYLOAD";
    public static final String FORMAL_SCOPE="FORMAL_RELEASE_ASSET_ROOT";
    public static final int MAXIMUM_BYTES=65536,FORMAL_MAXIMUM_AUTHORITY_BYTES=262144;
    public static final int FORMAL_MAXIMUM_FILES=256,FORMAL_MAXIMUM_DIRECTORIES=128,FORMAL_MAXIMUM_SINGLE_BYTES=2<<20;
    public static final long FORMAL_MAXIMUM_ASSET_BYTES=16L<<20,MAXIMUM_CONTROL_BYTES=512L<<10;
    public enum Branch { IMMUTABLE_INPUTS,FORMAL_RELEASE }
    private RootBootstrapOutputContract(){ }
    public sealed interface Authority permits Declaration,AssetCensus,CapacityRelease,Binding { }
    public enum Kind {
        MCP_CATALOG,MCP_ADMISSION,MCP_TOOLS,MCP_RESOURCES,LIFE_SETTINGS,ADVANCE_TIMINGS,CAMPAIGN_DEADLINE,
        REMAINING_DOMAIN_SETTINGS,NATIVE_DOMAIN_ORIGINALS,FAMILY_DOMAIN,CHILD_MATRILINEAL_DOMAIN,DEFAULT_MARRIAGE_DOMAIN,APPLICATION,RUNTIME_DEFINITIONS,STARTUP,FINITE_FIRST_LIVE_REQUEST,
        ROOT_INTENT,SELECTED_REGISTRATION,ORIGINAL_DRIVER_RUN_PROFILE,
        SWAY_CONFIGURATION,TRUSTED_EVENT_SOURCE_CONTEXT,CAPABILITY_CONFIGURATION,CAPABILITY_SESSION_PRESENTATION,MCP_REGISTRATION_FACTS,MCP_INVENTORY_PROOF,COA_READ_LIMITS,
        PROFILE_DLC_LOAD,PROFILE_SETTINGS,PROFILE_TUTORIAL,PROFILE_OUTER_DESCRIPTOR,PROFILE_PRESETS,PROFILE_ENVIRONMENT,
        PROFILE_PRODUCTION_INVENTORY,INITIAL_POLICY,NORMAL_EXIT_TARGET_BINDING,NORMAL_EXIT_SOURCE_INVENTORY,
        NORMAL_EXIT_MANAGED_PROFILE,NORMAL_EXIT_PROFILE_PROJECTION,ORIGINAL_SETTINGS_SNAPSHOT,ARMY_QUERY_HISTORY_CONFIGURATION,RUNTIME_DEFINITIONS_SOURCE_DECLARATION,RUNTIME_DEFINITIONS_PUBLICATION_REQUEST,NATIVE_LAUNCH_PLAN,
        FORMAL_RELEASE_PAYLOAD,FORMAL_RELEASE_MANIFEST
    }
    /** Expected bytes/SHA come from the actual unique typed producer before issuer capacity is requested. */
    public record Output(Kind kind,String fileName,long bytes,String sha256) {
        public Output {
            Objects.requireNonNull(kind);outputName(kind,fileName);if(kind==Kind.ORIGINAL_SETTINGS_SNAPSHOT||kind==Kind.FORMAL_RELEASE_PAYLOAD)nonnegative(bytes);else positive(bytes);digest(sha256);
            require(bytes<=(formalKind(kind)?FORMAL_MAXIMUM_SINGLE_BYTES:1<<20),"bootstrap input exceeds its explicit branch per-file ceiling");
            long leafMaximum=switch(kind){case PROFILE_DLC_LOAD,PROFILE_SETTINGS,PROFILE_TUTORIAL,PROFILE_OUTER_DESCRIPTOR->65536;
                case PROFILE_PRESETS->262144;case ARMY_QUERY_HISTORY_CONFIGURATION->65536;case COA_READ_LIMITS->4096;
                case FINITE_FIRST_LIVE_REQUEST->16384;case FORMAL_RELEASE_PAYLOAD->FORMAL_MAXIMUM_SINGLE_BYTES;default->1<<20;};
            require(bytes<=leafMaximum,"actual encoded output exceeds its sole producer's finite leaf bound");
        }
    }
    public record Declaration(String schema,String purpose,String machineId,String ownerTask,String windowId,
            String observedAtUtc,String reviewAtUtc,String assetRoot,SharedSourceFiles.DirectoryIdentity assetDirectory,
            String controlRoot,SharedSourceFiles.DirectoryIdentity controlDirectory,long assetMaximumChargedBytes,
            long controlMaximumChargedBytes,long maximumSingleWriteBytes,int maximumEntries,List<Output> outputs,List<String> outputDirectories,List<RetainedInput> retainedInputs) implements Authority {
        public Declaration {
            boolean formal=RootBootstrapOutputContract.branch(schema,purpose,DECLARATION,FORMAL_DECLARATION)==Branch.FORMAL_RELEASE;
            machine(machineId);require("/root".equals(ownerTask),"sole Root bootstrap owner required");id(windowId);period(observedAtUtc,reviewAtUtc);
            absolute(assetRoot);absolute(controlRoot);Objects.requireNonNull(assetDirectory);Objects.requireNonNull(controlDirectory);
            Path assets=Path.of(assetRoot),control=Path.of(controlRoot);
            require(!assets.startsWith(control)&&!control.startsWith(assets),"bootstrap asset/control roots must be disjoint canonical actual roots");
            require(assetMaximumChargedBytes>=4096&&assetMaximumChargedBytes<=(formal?FORMAL_MAXIMUM_ASSET_BYTES:1536L*1024)
                    &&controlMaximumChargedBytes>=4096&&controlMaximumChargedBytes<=512L*1024,
                    "bootstrap roots exceed the ceilings of their explicit authority branch");
            require(maximumSingleWriteBytes>0&&maximumSingleWriteBytes<=(formal?FORMAL_MAXIMUM_SINGLE_BYTES:1L<<20)&&maximumEntries>=1
                    &&maximumEntries<=(formal?FORMAL_MAXIMUM_FILES+FORMAL_MAXIMUM_DIRECTORIES:64),
                    "bounded immutable bootstrap per-file/inventory authority required");
            outputs=List.copyOf(outputs);require(!outputs.isEmpty()&&outputs.size()<=(formal?FORMAL_MAXIMUM_FILES:Kind.values().length),"bounded actual bootstrap output inventory required");
            require((formal||outputs.stream().map(Output::kind).distinct().count()==outputs.size())
                    &&outputs.stream().map(Output::fileName).distinct().count()==outputs.size(),"unique bootstrap role and exact filename required");
            require(outputs.stream().allMatch(output->formal==formalKind(output.kind())),"formal payload roles require their explicit formal authority branch");
            for(Output output:outputs)require(output.bytes()<=maximumSingleWriteBytes,"actual planned input exceeds signed per-file cap");
            outputDirectories=List.copyOf(outputDirectories);retainedInputs=List.copyOf(retainedInputs);
            require(outputDirectories.size()<=(formal?FORMAL_MAXIMUM_DIRECTORIES:3)&&outputDirectories.stream().distinct().count()==outputDirectories.size(),"finite unique generated profile directories required");
            for(String directory:outputDirectories){relative(directory);if(!formal)require(profileDirectory(directory),"only original closed profile directories may be created");}
            if(formal){require(retainedInputs.isEmpty(),"formal release output cannot retain a profile input subtree");formalPlan(outputs,outputDirectories);
                require(maximumEntries>=outputs.size()+outputDirectories.size(),"formal signed census must cover every output and directory");}
            for(Output output:outputs){Path parent=Path.of(output.fileName()).getParent();while(parent!=null){
                require(outputDirectories.contains(parent.toString().replace('\\','/')),"every generated output parent must be explicitly declared");parent=parent.getParent();}}
            require(retainedInputs.size()<=1,"only the one complete formal production subtree is retained by this profile authority");
        }
        public Branch branch(){return RootBootstrapOutputContract.branch(schema,purpose,DECLARATION,FORMAL_DECLARATION);}
        public Output output(Path target){return outputs.stream().filter(value->Path.of(assetRoot).resolve(value.fileName()).equals(target)).findFirst().orElseThrow();}
    }
    /** Immutable actual production input. This is independently charged existing storage, not output growth. */
    public record RetainedInput(String directoryName,SharedSourceFiles.DirectoryIdentity parentDirectory,FileRef productionInventory,SharedSourceFiles.NativeFile inventoryNativeFile) {
        public RetainedInput {require("mod-content".equals(directoryName),"the original profile production parent is fixed");Objects.requireNonNull(parentDirectory);file(productionInventory);Objects.requireNonNull(inventoryNativeFile);require(inventoryNativeFile.logicalBytes()==productionInventory.bytes(),"retained production inventory exact native length required");}
    }
    public record DirectoryEntry(String relative,SharedSourceFiles.DirectoryIdentity directory) {
        public DirectoryEntry {RootBootstrapOutputContract.relative(relative);Objects.requireNonNull(directory);}
    }
    /** Sole issuer binds this already allocated input to its actual existing-usage evidence; it is never unspent growth. */
    public enum RetentionPurpose { ACTIVE_PROFILE_PRODUCTION_INPUT }
    public record RetainedAllocation(FileRef productionInventory,long allocatedUpperBytes,FileRef existingUsageEvidence,
            RetentionPurpose retentionPurpose,String reviewAtUtc,FileRef heldCustodyEvidence) {
        public RetainedAllocation {file(productionInventory);positive(allocatedUpperBytes);require(allocatedUpperBytes<=1L<<30,"bounded retained production hold required");file(existingUsageEvidence);require(retentionPurpose==RetentionPurpose.ACTIVE_PROFILE_PRODUCTION_INPUT,"issued retained-input purpose required");instant(reviewAtUtc);file(heldCustodyEvidence);}
    }
    public record Entry(String fileName,SharedSourceFiles.NativeFile nativeFile) {
        public Entry {relative(fileName);Objects.requireNonNull(nativeFile);}
    }
    /** Complete covers this closed generated hierarchy and its explicitly retained immutable input, never the unknown old workpackage. */
    public record AssetCensus(String schema,String status,String scope,String machineId,String windowId,String observedAtUtc,
            String reviewAtUtc,FileRef declarationRef,SharedSourceFiles.DirectoryIdentity assetDirectory,List<Entry> entries,long chargedUpperBytes,List<DirectoryEntry> directories,long retainedAllocatedUpperBytes) implements Authority {
        public AssetCensus {
            boolean formal=FORMAL_CENSUS.equals(schema);
            require((formal&&FORMAL_SCOPE.equals(scope)||CENSUS.equals(schema)&&"BOOTSTRAP_ASSET_ROOT_WITH_EXPLICIT_RETAINED_INPUTS".equals(scope))
                    &&"COMPLETE".equals(status),"actual complete bounded bootstrap asset census required");
            machine(machineId);id(windowId);period(observedAtUtc,reviewAtUtc);file(declarationRef);Objects.requireNonNull(assetDirectory);
            entries=List.copyOf(entries);require(entries.size()<=(formal?FORMAL_MAXIMUM_FILES:64)&&entries.stream().map(Entry::fileName).distinct().count()==entries.size(),"complete unique bounded bootstrap native inventory required");
            directories=List.copyOf(directories);require(directories.size()<=(formal?FORMAL_MAXIMUM_DIRECTORIES:3)&&directories.stream().map(DirectoryEntry::relative).distinct().count()==directories.size(),"complete generated-directory native identities required");
            for(DirectoryEntry directory:directories)if(!formal)require(profileDirectory(directory.relative()),"ordinary census cannot import formal directories");
            nonnegative(retainedAllocatedUpperBytes);require((!formal||retainedAllocatedUpperBytes==0)&&retainedAllocatedUpperBytes<=1L<<30,"bounded explicit retained input allocation required");
            long measured=4096;for(Entry entry:entries)measured=add(measured,entry.nativeFile().allocatedBytes());
            // Directory charge is observed geometry by the sole census producer; the complete sum is verified there.
            require(chargedUpperBytes>=measured,"generated-directory allocation guard cannot be omitted");

        }
    }
    public record OtherReservation(String ownerTask,String windowId,long unspentBytes,FileRef authorityRef) {
        public OtherReservation {StrictJson.text(ownerTask);id(windowId);positive(unspentBytes);file(authorityRef);}
    }
    public record Volume(String volumeRoot,long maximumBootstrapGrowthBytes,long minimumUsableBytes,long systemGrowthReserveBytes,
            Long finiteQuotaOverrideBytes,String quotaReviewAtUtc,RootRuntimeStorageContract.ExistingUsage existingUsage,
            List<OtherReservation> otherReservations,long otherUnspentBytes) {
        public Volume {
            absolute(volumeRoot);require(Path.of(volumeRoot).equals(Path.of(volumeRoot).getRoot()),"actual bootstrap volume root required");
            positive(maximumBootstrapGrowthBytes);nonnegative(minimumUsableBytes);nonnegative(systemGrowthReserveBytes);Objects.requireNonNull(existingUsage);
            require((finiteQuotaOverrideBytes==null)==(quotaReviewAtUtc==null),"explicit quota override/review pair required");
            if(finiteQuotaOverrideBytes!=null){positive(finiteQuotaOverrideBytes);instant(quotaReviewAtUtc);}
            otherReservations=List.copyOf(otherReservations);require(otherReservations.size()<=256,"bounded complete other-reservation evidence inventory required");
            var identities=new HashSet<String>();long sum=0;
            for(OtherReservation reservation:otherReservations){require(identities.add(reservation.ownerTask()+"/"+reservation.windowId()),"duplicate external bootstrap reservation claim");sum=add(sum,reservation.unspentBytes());}
            require(sum==otherUnspentBytes,"complete bootstrap other-reservation sum differs");
        }
    }
    public record CapacityRelease(String schema,String purpose,String machineId,String ownerTask,String issuerTask,String windowId,
            String observedAtUtc,String reviewAtUtc,FileRef policyRef,FileRef declarationRef,FileRef censusRef,
            FileRef originalFinancialHeadRef,long jointMaximumChargedBytes,List<Volume> volumes,List<RetainedAllocation> retainedAllocations) implements Authority {
        public CapacityRelease {
            boolean formal=branch(schema,purpose,CAPACITY,FORMAL_CAPACITY)==Branch.FORMAL_RELEASE;
            require(ISSUER.equals(issuerTask)&&"/root".equals(ownerTask),"sole issuer bootstrap-purpose capacity release required");
            machine(machineId);id(windowId);period(observedAtUtc,reviewAtUtc);
            for(FileRef ref:List.of(policyRef,declarationRef,censusRef,originalFinancialHeadRef))file(ref);
            require(jointMaximumChargedBytes>0&&jointMaximumChargedBytes<=(formal?FORMAL_MAXIMUM_ASSET_BYTES+MAXIMUM_CONTROL_BYTES:2L<<20),"finite allocation must stay inside its explicit bootstrap branch ceiling");
            retainedAllocations=List.copyOf(retainedAllocations);require(retainedAllocations.size()<=(formal?0:1),"finite explicit retained production accounting required");
            volumes=List.copyOf(volumes);require(!volumes.isEmpty()&&volumes.size()<=16&&volumes.stream().map(Volume::volumeRoot).distinct().count()==volumes.size(),"all actual bootstrap volumes required");
        }
    }
    /** Final acyclic selection: declaration -> actual census -> issuer release -> binding. No future runtime lease hash. */
    public record Binding(String schema,String purpose,String machineId,String ownerTask,String issuerTask,String windowId,
            String observedAtUtc,String reviewAtUtc,FileRef declarationRef,FileRef censusRef,FileRef capacityRef) implements Authority {
        public Binding {
            branch(schema,purpose,BINDING,FORMAL_BINDING);
            require(ISSUER.equals(issuerTask)&&"/root".equals(ownerTask),"actual immutable bootstrap binding required");
            machine(machineId);id(windowId);period(observedAtUtc,reviewAtUtc);for(FileRef ref:List.of(declarationRef,censusRef,capacityRef))file(ref);
        }
    }
    public static byte[] encode(Authority typed)throws IOException {
        Objects.requireNonNull(typed);
        return StrictJson.canonical(ControlBuild.strictMapper().valueToTree(typed),authorityMaximum(typed));
    }
    public static <T>T decode(byte[] bytes,Class<T> type)throws IOException {
        if(type!=Declaration.class&&type!=AssetCensus.class&&type!=CapacityRelease.class&&type!=Binding.class)
            throw new IOException("only explicit bootstrap authority record types may be decoded");
        try{StrictJson.parse(bytes,FORMAL_MAXIMUM_AUTHORITY_BYTES);T value=ControlBuild.strictMapper().readValue(bytes,type);
            require(bytes.length<=authorityMaximum((Authority)value),"ordinary bootstrap wire exceeds its unchanged finite byte bound");return value;}
        catch(IllegalArgumentException invalid){throw new IOException("invalid strict bootstrap authority wire",invalid);}
    }
    private static boolean formalKind(Kind kind){return kind==Kind.FORMAL_RELEASE_PAYLOAD||kind==Kind.FORMAL_RELEASE_MANIFEST;}
    private static boolean profileDirectory(String value){return List.of("mod","player","player/game_rules").contains(value);}
    static Branch branch(String schema,String purpose,String ordinarySchema,String formalSchema){
        if(ordinarySchema.equals(schema)&&PURPOSE.equals(purpose))return Branch.IMMUTABLE_INPUTS;
        require(formalSchema.equals(schema)&&FORMAL_PURPOSE.equals(purpose),"exact schema/purpose pair required for the explicit bootstrap branch");return Branch.FORMAL_RELEASE;
    }
    private static int authorityMaximum(Authority value){
        boolean formal=value instanceof Declaration item?FORMAL_DECLARATION.equals(item.schema()):value instanceof AssetCensus item?FORMAL_CENSUS.equals(item.schema())
                :value instanceof CapacityRelease item?FORMAL_CAPACITY.equals(item.schema()):FORMAL_BINDING.equals(((Binding)value).schema());
        return formal?FORMAL_MAXIMUM_AUTHORITY_BYTES:MAXIMUM_BYTES;
    }
    /** One complete formal tree and its sibling manifest; this grants storage, never publication qualification. */
    static void formalPlan(List<Output> outputs,List<String> directories){
        require(!outputs.isEmpty()&&outputs.size()<=FORMAL_MAXIMUM_FILES,"bounded actual formal output inventory required");
        require(outputs.stream().map(output->output.fileName().toLowerCase(java.util.Locale.ROOT)).distinct().count()==outputs.size()
                &&directories.stream().map(directory->directory.toLowerCase(java.util.Locale.ROOT)).distinct().count()==directories.size(),
                "formal output identities cannot alias by Windows path case");
        var manifests=outputs.stream().filter(output->output.kind()==Kind.FORMAL_RELEASE_MANIFEST).toList();
        require(manifests.size()==1&&outputs.stream().allMatch(output->formalKind(output.kind())),"one formal sibling manifest and only formal payload roles required");
        String manifest=manifests.getFirst().fileName(),tree=manifest.substring(0,manifest.length()-".manifest.json".length());name(tree);
        Layout layout=formalLayout(outputs);String production=layout==Layout.DIRECT_STAGING?tree:"profile/mod-content/xar-production";
        var expected=new java.util.TreeSet<String>();Path ancestor=Path.of(production);
        while(ancestor!=null){expected.add(ancestor.toString().replace('\\','/'));ancestor=ancestor.getParent();}
        for(String directory:List.of("common","events","gfx","gui","localization"))expected.add(production+"/"+directory);
        int payloads=0;
        for(Output output:outputs)if(output.kind()==Kind.FORMAL_RELEASE_PAYLOAD){
            payloads++;String prefix=production+"/";require(output.fileName().startsWith(prefix),"formal payload escaped the sibling manifest production root");
            String path=output.fileName().substring(prefix.length());String[] parts=path.split("/");
            if(parts.length==1)require(List.of("descriptor.mod","thumbnail.png").contains(path),"formal root payload is outside its release allowlist");
            else{String lower=path.toLowerCase(java.util.Locale.ROOT);boolean allowed=switch(parts[0]){
                case "common","events"->lower.endsWith(".txt");case "gfx"->lower.endsWith(".dds");case "gui"->lower.endsWith(".gui")||lower.endsWith(".txt");
                case "localization"->lower.endsWith(".yml");default->false;};require(allowed,"formal payload suffix/root is outside its release allowlist");}
            Path parent=Path.of(output.fileName()).getParent();while(parent!=null){expected.add(parent.toString().replace('\\','/'));parent=parent.getParent();}
        }
        require(payloads>0&&outputs.stream().anyMatch(output->output.fileName().equals(production+"/descriptor.mod"))
                &&outputs.stream().anyMatch(output->output.fileName().equals(production+"/thumbnail.png")),"complete formal root descriptor and thumbnail required");
        require(expected.size()<=FORMAL_MAXIMUM_DIRECTORIES&&List.copyOf(expected).equals(directories),"formal directories must be the exact sorted release-parent closure");
    }
    /** The same producer Layout enum governs the complete paths; no implicit manifest inside retained mod-content. */
    static Layout formalLayout(List<Output> outputs){
        var manifests=outputs.stream().filter(output->output.kind()==Kind.FORMAL_RELEASE_MANIFEST).toList();
        require(manifests.size()==1,"one exact formal manifest required before layout selection");
        String manifest=manifests.getFirst().fileName(),tree=manifest.substring(0,manifest.length()-".manifest.json".length());
        boolean direct=outputs.stream().anyMatch(output->output.kind()==Kind.FORMAL_RELEASE_PAYLOAD&&output.fileName().equals(tree+"/descriptor.mod"));
        boolean isolated=manifest.equals("xar-production.manifest.json")&&outputs.stream().anyMatch(output->output.kind()==Kind.FORMAL_RELEASE_PAYLOAD
                &&output.fileName().equals("profile/mod-content/xar-production/descriptor.mod"));
        require(direct!=isolated,"formal plan must select exactly one explicit direct or isolated-profile import layout");
        return direct?Layout.DIRECT_STAGING:Layout.ISOLATED_PROFILE_IMPORT;
    }
    static void outputName(Kind kind,String value){
        relative(value);if(kind==Kind.FORMAL_RELEASE_PAYLOAD){require(Path.of(value).getNameCount()>=2,"formal payload must be inside its one production tree");return;}
        if(kind==Kind.FORMAL_RELEASE_MANIFEST){name(value);require(value.endsWith(".manifest.json"),"formal sibling manifest filename required");return;}
        String fixed=switch(kind){
            case NATIVE_LAUNCH_PLAN->"native-launch-plan.json";case PROFILE_DLC_LOAD->"dlc_load.json";case PROFILE_SETTINGS->"pdx_settings.txt";case PROFILE_TUTORIAL->"tutorial.txt";
            case PROFILE_OUTER_DESCRIPTOR->"mod/xar_autoplayer.mod";case PROFILE_PRESETS->"player/game_rules/presets.txt";
            case PROFILE_ENVIRONMENT->"xar-autoplayer-environment.json";case NORMAL_EXIT_PROFILE_PROJECTION->"normal-exit-profile-binding-projection-v1.json";
            case NORMAL_EXIT_SOURCE_INVENTORY->"normal-exit-source-inventory-v1.json";default->null;};
        if(fixed!=null)require(fixed.equals(value),"closed profile/native original output target differs");else name(value);
    }
    static void relative(String value){require(value!=null&&!value.contains("\\")&&!value.startsWith("/")
            &&value.length()<=256&&java.util.Arrays.stream(value.split("/",-1)).allMatch(part->part.matches("[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}")&&!part.equals("..")),"bounded canonical relative bootstrap path required");}
    static void name(String value){require(value!=null&&value.matches("[A-Za-z0-9][A-Za-z0-9_.-]{0,127}")&&!value.equals(".")&&!value.equals(".."),"flat bounded bootstrap filename required");}
    static void absolute(String value){StrictJson.text(value);Path path=Path.of(value);require(path.isAbsolute()&&path.normalize().equals(path),"actual normalized absolute bootstrap path required");}
    static void file(FileRef ref){Objects.requireNonNull(ref);absolute(ref.path());require(ref.bytes()>0&&ref.bytes()<=1L<<20,"bounded actual bootstrap authority original required");digest(ref.sha256());}
    static void digest(String value){require(value!=null&&value.matches("[0-9a-fA-F]{64}"),"exact original bootstrap SHA required");}
    static void machine(String value){require(value!=null&&value.matches("[a-z0-9][a-z0-9-]{0,127}")&&!value.equals("unknown"),"actual bootstrap machine identity required");}
    static void id(String value){require(value!=null&&value.matches("[A-Za-z0-9][A-Za-z0-9_.-]{0,127}"),"bounded explicit bootstrap window required");}
    static Instant instant(String value){StrictJson.text(value);Instant instant=Instant.parse(value);require(value.equals(instant.toString()),"canonical bootstrap UTC required");return instant;}
    static void period(String observed,String review){Instant first=instant(observed),last=instant(review);require(first.isBefore(last)&&Duration.between(first,last).compareTo(Duration.ofDays(7))<=0,"finite reviewed bootstrap authority required");}
    static long add(long left,long right){return Math.addExact(left,right);}
    static void positive(long value){require(value>0&&value<=StrictJson.MAX_SAFE_INTEGER,"positive safe bootstrap byte count required");}
    static void nonnegative(long value){require(value>=0&&value<=StrictJson.MAX_SAFE_INTEGER,"nonnegative safe bootstrap byte count required");}
    static void require(boolean accepted,String reason){if(!accepted)throw new IllegalArgumentException(reason);}
}
