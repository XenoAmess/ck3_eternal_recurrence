package org.xar.ck3.control.service.root;

import java.nio.file.Path;
import java.time.Instant;
import java.util.EnumSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityActionRoutes;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernanceActionPreparation;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.evidence.PortableEvidenceJson;

/** Pure, closed configuration data. No function, installed runtime, admission or restored proof is serialized. */
public final class RootRuntimeDefinitionModel {
    public static final String SCHEMA="xar.java.root-runtime-definitions/v7";
    public static final String LEASE_SCHEMA="xar.java.root-runtime-storage-lease/v1";
    public static final String ARMY_WAR_EXIT_TRUCE_TARGET="native-transport/src/main/java/org/xar/ck3/control/nativebridge/capabilities/army/ArmyWarExitTruceReads.java";
    private RootRuntimeDefinitionModel() { }
    public enum SourceKind { JAVA, NATIVE, ORIGINAL_PYTHON, STOCK_SCRIPT }
    public enum SourceRole {
        NATIVE_GOV_LIFESTYLE,NATIVE_GOV_COUNCIL,NATIVE_GOV_CROWN,GOV_PLANNING_DECODER,GOV_COUNCIL_DECODER,
        GOV_ACTION_DECODER,GOV_EFFECT_VERIFIER,GOV_COUNCIL_EFFECT_VERIFIER,NATIVE_GOV_FINAL_TERMS,GOV_FINAL_TERMS_DECODER,
        FINANCE_POLICY,FINANCE_MERCENARY_MATERIAL,FINANCE_GIFT_MATERIAL,FINANCE_QUOTE_ARCHIVE,FINANCE_READ_CODEC,
        FINANCE_HIRE_ACK_CODEC,FINANCE_DOMAIN,FINANCE_DOMAIN_REDUCER,FINANCE_WAR_PRIORITY,FINANCE_FACTION_DEFINITION,
        FINANCE_FACTION_CODEC,FINANCE_GIFT_DOMAIN,FINANCE_GIFT_BODY_CODEC,FINANCE_GIFT_BODY_REDUCER,
        FINANCE_GIFT_COLD_READ_CODEC,FINANCE_GIFT_COLD_CLASSIFIER,FINANCE_GIFT_COLD_CLASSIFIER_CODEC,FINANCE_GIFT_COLD_PROVIDER,
        FINANCE_GIFT_PROCESS_IDENTITY,
        ARMY_CLOSED_DEFINITION,ARMY_CLOSED_DECODER,ARMY_BATTLE_DEFINITION,ARMY_BATTLE_DECODER,ARMY_ROUTE_DEFINITION,
        ARMY_ROUTE_DECODER,ARMY_WINDOW_DEFINITION,ARMY_WINDOW_DECODER,ARMY_DOMAIN,ARMY_COMPOSITE,ARMY_CLOSED_SERVICE,
        ARMY_BATTLE_SERVICE,ARMY_PREVIEW_SERVICE,ARMY_ORDER_SERVICE,ARMY_WINDOW_SERVICE,
        CONSTRUCTION_POLICY,CONSTRUCTION_COLLECTOR,CONSTRUCTION_NATIVE_ACTION,CONSTRUCTION_OBSERVER,
        CONSTRUCTION_ARCHIVE_VERIFIER,CONSTRUCTION_LIFECYCLE,CONSTRUCTION_SNAPSHOT_VERIFIER,CONSTRUCTION_ORIGINALS,
        PRISONER_COLLECTION_PRODUCER,PRISONER_COLLECTION_DECODER,PRISONER_WAR_PRODUCER,PRISONER_WAR_DECODER,
        PRISONER_ACTION_PRODUCER,PRISONER_ACTION_PREPARATION,PRISONER_ACTION_OBSERVER,PRISONER_ACTION_DECODER,
        PRISONER_RECORDED_VERIFIER,PRISONER_ORDINARY_POLICIES,PRISONER_SUCCESSION_POLICIES,PRISONER_STOCK_INTERACTIONS,
        PRISONER_LEDGER_PRODUCER,PRISONER_EPISODE_LEDGER,TURN_BUNDLE_DEFINITION,TURN_BUNDLE_DECODER,
        ORDINARY_GOV_POLICY,ORDINARY_GOV_FEAST_POLICY,ORDINARY_GOV_FEAST_EFFECTS,ORDINARY_GOV_ACTIVITY_ACTION_DECODER,
        ORDINARY_GOV_OPENING_TRANSITIONS,FEAST_STATE_IMPLEMENTATION,GOVERNANCE_DOMAINS_IMPLEMENTATION,CROWN_RETRY_IMPLEMENTATION,
        ACTIVITY_CODEC,ACTIVITY_ACTION_DECODER,FRONTEND_ORIGINAL_DRIVER,FRONTEND_RULES_EFFECTS,FRONTEND_RULES_DECODER,
        FRONTEND_START_EFFECTS,FRONTEND_START_DECODER,FRONTEND_ENTRY_GUARD,FRONTEND_ENTRY_AUTHORITY,
        INTERACTION_MARRIAGE,INTERACTION_LAWS,INTERACTION_CLAIMS,INTERACTION_HOLDER,INTERACTION_APPOINTMENT,
        INTERACTION_ORDINARY,INTERACTION_PLAYER_CONTROL,INTERACTION_GRANT,INTERACTION_PENDING,INTERACTION_HEIR,
        INTERACTION_READ_DECODER,INTERACTION_POLICY,INTERACTION_EFFECTS,INTERACTION_EFFECTS_DECODER,
        CROSS_RUN_IMPLEMENTATION,INCIDENT_IMPLEMENTATION,PUBLIC_AUTO_TURN,PUBLIC_CAPABILITIES,PUBLIC_SNAPSHOT,
        PUBLIC_ACTIVITY,PUBLIC_CURRENT_ARMY,STARTUP_IMPLEMENTATION,ROLLBACK_IMPLEMENTATION,SWAY_IMPLEMENTATION,
        MILITARY_RETREAT_POLICY,MILITARY_COMMANDER_POLICY,MILITARY_RENDEZVOUS_POLICY,MILITARY_FORECAST_POLICY,
        COMMANDER_READ_DEFINITION,COMMANDER_READ_DECODER,COMMANDER_ACTION_DEFINITION,COMMANDER_ACTION_DECODER,
        COMMANDER_ACTION_OBSERVER,COMMANDER_ARCHIVED_VERIFIER,ARMY_FORECAST_READS,ARMY_FORECAST_DECODER,
        ARMY_PLANNING_READS,ARMY_PLANNING_DECODER,ARMY_REINFORCEMENT_DEFINITION,ARMY_REINFORCEMENT_DECODER,ARMY_ADDITIONAL_SERVICE,
        COMMANDER_RECONCILIATION_QUERY,ARMY_RECONCILIATION_DEFINITION,ARMY_RECONCILIATION_DECODER,
        ARMY_WAR_READS,ARMY_WAR_DECODER,ARMY_WAR_EXIT_TRUCE_DEFINITION,
        SAVE_PREPARATION,SAVE_POSTSTATE,SAVE_ARCHIVED_REPLAY
    }
    public enum ClosureRole {
        NATIVE_GOV_CONTINUATION,ARMY_DOMAIN,CONSTRUCTION_DOMAIN,OPENING_PRODUCERS,CADENCE_PRODUCERS,
        FEAST_STATE,COUNCIL_DOMAIN,CROWN_DOMAIN,CROWN_RETRY,CROWN_RETRY_PRODUCERS,READ_HISTORY,CROSS_RUN,PRISONER_DOMAIN,
        FAMILY,CAPABILITIES,ACTIVITY,STARTUP,ROLLBACK,SWAY,MILITARY,COMBAT
    }
    public enum DataRole {
        FAMILY_DOMAIN,CHILD_MATRILINEAL_DOMAIN,DEFAULT_MARRIAGE_DOMAIN,INITIAL_PREPARED_ENVIRONMENT,INITIAL_POLICY,ORIGINAL_DRIVER_RUN_PROFILE,
        EXPLICIT_FRESH_PACT,CAPABILITY_CONFIGURATION,CAPABILITY_SESSION_PRESENTATION,SWAY_CONFIGURATION,
        MCP_CATALOG,MCP_ADMISSION,MCP_TOOLS,MCP_RESOURCES,ORIGINAL_MCP_CAPTURE_RECEIPT,TRUSTED_EVENT_SOURCE_CONTEXT,ROLLBACK_PROOF,
        LIFE_SETTINGS,ADVANCE_TIMINGS,CAMPAIGN_DEADLINE,REMAINING_DOMAIN_SETTINGS,NATIVE_DOMAIN_ORIGINALS,
        PORTABLE_EVENT_EVIDENCE_MANIFEST
    }
    public record SelectedSource(String targetRelative,ExactRef sourceRef) {
        public SelectedSource { relative(targetRelative);exact(sourceRef); }
    }
    public record SourcePin(SourceRole role,SourceKind kind,SelectedSource selected) {
        public SourcePin { Objects.requireNonNull(role);Objects.requireNonNull(kind);Objects.requireNonNull(selected);
            StrictJson.require(kind==expectedKind(role),"source role has another producer kind");
            if(role==SourceRole.ARMY_WAR_EXIT_TRUCE_DEFINITION)StrictJson.require(ARMY_WAR_EXIT_TRUCE_TARGET.equals(selected.targetRelative()),
                    "truce reconciliation requires the actual sole ArmyWarExitTruceReads Java target");
            String suffix=switch(kind){case JAVA->".java";case NATIVE->".cpp";case ORIGINAL_PYTHON->".py";case STOCK_SCRIPT->".txt";};
            StrictJson.require(selected.targetRelative().endsWith(suffix)&&Path.of(selected.sourceRef().path()).getFileName().toString().endsWith(suffix),"source role requires its actual producer source kind"); }
    }
    public record ProducerClosure(ClosureRole role,List<SelectedSource> sources) {
        public ProducerClosure { Objects.requireNonNull(role);sources=List.copyOf(sources);bounded(sources.size(),1,256,"complete producer closure");
            unique(sources.stream().map(SelectedSource::targetRelative).toList(),"closure producer target"); }
    }
    public record DataPin(DataRole role,FileRef originalRef) {
        public DataPin { Objects.requireNonNull(role);file(originalRef,maximumDataBytes(role)); }
    }
    public record SourceIndex(FileRef compressedRef,long uncompressedBytes,String uncompressedSha256) {
        public SourceIndex {
            file(compressedRef,org.xar.ck3.control.build.SingleWinnerSourceIndex.MAX_BYTES);
            bounded(uncompressedBytes,1,org.xar.ck3.control.build.SingleWinnerSourceIndex.MAX_BYTES,"bounded decompressed source index");
            new org.xar.ck3.control.build.SourceGraphSdkIndexProducer.IndexArtifact(compressedRef,
                    Math.toIntExact(uncompressedBytes),uncompressedSha256);
        }
    }
    public record Build(String gameVersion,String executableSha256) {
        public Build { StrictJson.text(gameVersion);digest(executableSha256); }
    }
    public record GovInputs(Build build,String authorityId,List<String> admittedActions,int maximumStatusPolls,int maximumContinuations) {
        public GovInputs { Objects.requireNonNull(build);id(authorityId);admittedActions=List.copyOf(admittedActions);
            bounded(admittedActions.size(),1,5,"finite governance action inventory");unique(admittedActions,"governance action");
            admittedActions.forEach(value->{new OperationKey(value);StrictJson.require(GovernanceActionPreparation.OPERATIONS.contains(value),"unknown governance action");});bounded(maximumStatusPolls,1,3000,"status poll bound");bounded(maximumContinuations,3,1024,"continuation bound"); }
    }
    public enum FinanceQuery { ROOT,CASH,MERCENARIES,CONSTRUCTION,FACTION_GIFT,FACTION_GIFT_RECEIPT }
    public enum PermissionMode { ADVERTISED_CAPABILITY,SOURCE_QUALIFIED_PRIVATE }
    public enum WireProfile { EXECUTE_STEP }
    public record ReadPermission(String capability,String permissionKey,PermissionMode mode,WireProfile wireProfile) {
        public ReadPermission { Objects.requireNonNull(mode);Objects.requireNonNull(wireProfile);StrictJson.text(permissionKey);
            StrictJson.require((mode==PermissionMode.ADVERTISED_CAPABILITY)==(capability!=null),"public capability and private permission are distinct");
            if(capability!=null)StrictJson.text(capability); }
    }
    public record FinanceRead(FinanceQuery query,SelectedSource definition,ReadPermission permission) {
        public FinanceRead { Objects.requireNonNull(query);Objects.requireNonNull(definition);Objects.requireNonNull(permission); }
    }
    public record FinanceInputs(List<FinanceRead> reads,SelectedSource giftColdDefinition,ReadPermission giftColdPermission) {
        public FinanceInputs { reads=List.copyOf(reads);Objects.requireNonNull(giftColdDefinition);Objects.requireNonNull(giftColdPermission);
            StrictJson.require(EnumSet.copyOf(reads.stream().map(FinanceRead::query).toList()).equals(EnumSet.allOf(FinanceQuery.class))&&reads.size()==6,"all six actual finance reads required"); }
    }
    public record ArmyInputs(long commandReadTimeoutMs,long reconciliationReadTimeoutMs,String actionIdPrefix) {
        public ArmyInputs { bounded(commandReadTimeoutMs,1,3600000,"army command timeout");bounded(reconciliationReadTimeoutMs,1,3600000,"army reconciliation timeout");id(actionIdPrefix); }
    }
    public record PrisonerInputs(Build build,String authorityId) {
        public PrisonerInputs { Objects.requireNonNull(build);id(authorityId); }
    }
    public record MatrilinealPair(int subjectCharacterId,int candidateCharacterId) {
        public MatrilinealPair { bounded(subjectCharacterId,1,Integer.MAX_VALUE,"matrilineal subject CharacterID");bounded(candidateCharacterId,1,Integer.MAX_VALUE,"matrilineal candidate CharacterID");
            StrictJson.require(subjectCharacterId!=candidateCharacterId,"matrilineal pair must contain distinct characters"); }
    }
    public record FamilyInputs(boolean familyEnabled,boolean fulfillCurrentBetrothal,boolean childFocusEnabled,boolean childDefaultEnabled,MatrilinealPair matrilinealPair) {
        public FamilyInputs { StrictJson.require(familyEnabled&&fulfillCurrentBetrothal&&childFocusEnabled&&childDefaultEnabled,"complete migration uses all family capabilities"); }
    }
    public record FrontendInputs(Build build,long freshnessMs,long heartbeatMaximumAgeMs,int retainedFrames,int retainedOrigins,String authorityId) {
        public FrontendInputs { Objects.requireNonNull(build);bounded(freshnessMs,1,60000,"frontend freshness");bounded(heartbeatMaximumAgeMs,1,60000,"heartbeat age");
            bounded(retainedFrames,1,4096,"retained frames");bounded(retainedOrigins,1,65536,"retained origins");id(authorityId); }
    }
    public record InteractionInputs(Build build,List<Long> lawTitles,List<List<Integer>> claimTitleSets,List<Integer> holderTitles) {
        public InteractionInputs { Objects.requireNonNull(build);lawTitles=List.copyOf(lawTitles);holderTitles=List.copyOf(holderTitles);
            claimTitleSets=claimTitleSets.stream().map(List::copyOf).toList();bounded(lawTitles.size(),0,4096,"law targets");bounded(holderTitles.size(),0,4096,"holder targets");bounded(claimTitleSets.size(),0,4096,"claim target sets");
            for(long value:lawTitles)bounded(value,0,0xffff_fffeL,"full law TitleID");for(int value:holderTitles)bounded(value,0,Integer.MAX_VALUE,"holder TitleID");
            for(var group:claimTitleSets){bounded(group.size(),1,4096,"explicit claim TitleID set");for(int value:group)bounded(value,0,Integer.MAX_VALUE,"claim TitleID");unique(group,"claim TitleID");}
            unique(lawTitles,"law TitleID");unique(holderTitles,"holder TitleID");unique(claimTitleSets,"claim target set"); }
    }
    public record ActivityQuery(ActivityNativeContracts.Query query,SelectedSource definition) {
        public ActivityQuery { Objects.requireNonNull(query);Objects.requireNonNull(definition); }
    }
    public record ActivityMutation(ActivityActionRoutes.Kind kind,SelectedSource definition) {
        public ActivityMutation { Objects.requireNonNull(kind);Objects.requireNonNull(definition); }
    }
    public record ActivityInputs(List<ActivityQuery> reads,List<ActivityMutation> mutations) {
        public ActivityInputs { reads=List.copyOf(reads);mutations=List.copyOf(mutations);bounded(reads.size(),ActivityNativeContracts.Query.values().length,ActivityNativeContracts.Query.values().length,"all actual activity reads");bounded(mutations.size(),ActivityActionRoutes.Kind.values().length,ActivityActionRoutes.Kind.values().length,"all five activity mutations");
            unique(reads.stream().map(ActivityQuery::query).toList(),"activity query");unique(mutations.stream().map(ActivityMutation::kind).toList(),"activity mutation"); }
    }
    /** Explicit null originalRef denotes observed absence only; actual private fresh-entry admission remains elsewhere. */
    public record OriginalHistory(String path,FileRef originalRef) {
        public OriginalHistory { absolute(path);if(originalRef!=null){file(originalRef,16L<<20);StrictJson.require(Path.of(path).equals(Path.of(originalRef.path())),"original history pin/path differ");} }
    }
    public record CrossRunInputs(OriginalHistory originalOneLifeHistory) {
        public CrossRunInputs { Objects.requireNonNull(originalOneLifeHistory);StrictJson.require(Path.of(originalOneLifeHistory.path()).getFileName().toString().equals("one-life-history.json"),"explicit original one-life history path required"); }
    }
    public record IncidentInputs(String incidentBase,String scanBase,long maximumSingleWriteBytes) {
        public IncidentInputs { absolute(incidentBase);absolute(scanBase);Path a=Path.of(incidentBase),b=Path.of(scanBase);
            StrictJson.require(!a.startsWith(b)&&!b.startsWith(a),"incident and scan roots must be disjoint");bounded(maximumSingleWriteBytes,1,16L<<20,"incident bounded write"); }
    }
    public record PublicInputs(long observationTimeoutMs,long autoTimeoutMs,List<PublicMethod> requiredServices) {
        public PublicInputs { bounded(observationTimeoutMs,1,3600000,"public observation timeout");bounded(autoTimeoutMs,1,86400000,"public auto timeout");
            requiredServices=List.copyOf(requiredServices);bounded(requiredServices.size(),1,4096,"required public service inventory");unique(requiredServices,"required public service"); }
    }
    public record StartupInputs(int retainedEffects,long ordinaryFreshnessMs,String authorityId) {
        public StartupInputs { bounded(retainedEffects,1,4096,"retained effects");bounded(ordinaryFreshnessMs,1,60000,"ordinary freshness");id(authorityId); }
    }
    public record Configuration(String schema,String machineId,String observedAtUtc,String reviewAtUtc,
            FileRef applicationRef,FileRef storageLeaseRef,FileRef nativeLaunchPlanRef,FileRef runtimePackageRequestRef,
            SourceIndex sourceIndex,List<SourcePin> sources,List<ProducerClosure> closures,List<DataPin> originalData,
            GovInputs governance,FinanceInputs finance,ArmyInputs army,PrisonerInputs prisoners,FamilyInputs family,FrontendInputs frontend,
            InteractionInputs interactions,ActivityInputs activity,CrossRunInputs crossRun,IncidentInputs incidents,
            PublicInputs publicCatalog,StartupInputs startup) {
        public Configuration {
            StrictJson.require(SCHEMA.equals(schema),"exact runtime definitions schema required");machine(machineId);Instant observed=instant(observedAtUtc),review=instant(reviewAtUtc);
            StrictJson.require(observed.isBefore(review),"finite runtime definitions review required");
            for(var ref:List.of(applicationRef,storageLeaseRef,nativeLaunchPlanRef))file(ref,StrictJson.EXPLICIT_MAX_BYTES);
            file(runtimePackageRequestRef,8L<<20);
            Objects.requireNonNull(sourceIndex);sources=List.copyOf(sources);closures=List.copyOf(closures);originalData=List.copyOf(originalData);
            StrictJson.require(sources.size()==SourceRole.values().length&&EnumSet.copyOf(sources.stream().map(SourcePin::role).toList()).equals(EnumSet.allOf(SourceRole.class)),"every unique migration source role is required");
            StrictJson.require(closures.size()==ClosureRole.values().length&&EnumSet.copyOf(closures.stream().map(ProducerClosure::role).toList()).equals(EnumSet.allOf(ClosureRole.class)),"every unique migration closure is required");
            SelectedSource episodeLedger=sources.stream().filter(row->row.role()==SourceRole.PRISONER_EPISODE_LEDGER).findFirst().orElseThrow().selected();
            ProducerClosure prisonerDomain=closures.stream().filter(row->row.role()==ClosureRole.PRISONER_DOMAIN).findFirst().orElseThrow();
            StrictJson.require(prisonerDomain.sources().contains(episodeLedger),"prisoner domain and definitions must retain the identical current episode-ledger target and exact source");
            validateOriginalData(originalData);
            Objects.requireNonNull(governance);Objects.requireNonNull(finance);Objects.requireNonNull(army);Objects.requireNonNull(prisoners);Objects.requireNonNull(family);Objects.requireNonNull(frontend);
            Objects.requireNonNull(interactions);Objects.requireNonNull(activity);Objects.requireNonNull(crossRun);Objects.requireNonNull(incidents);Objects.requireNonNull(publicCatalog);Objects.requireNonNull(startup);
            StrictJson.require(governance.build().equals(prisoners.build())&&governance.build().equals(frontend.build())&&governance.build().equals(interactions.build()),"one exact native build across runtime domains required");
        }
        public ExactRef source(SourceRole role) { return sources.stream().filter(row->row.role()==role).findFirst().orElseThrow().selected().sourceRef(); }
        public List<ExactRef> closure(ClosureRole role) { return closures.stream().filter(row->row.role()==role).findFirst().orElseThrow().sources().stream().map(SelectedSource::sourceRef).toList(); }
        public FileRef data(DataRole role) {
            Objects.requireNonNull(role);
            StrictJson.require(role!=DataRole.ROLLBACK_PROOF,"optional original rollback proof requires the explicit optional accessor");
            return originalData.stream().filter(row->row.role()==role).findFirst().orElseThrow().originalRef();
        }
        /** Both startup roles retain the one original v4 run-profile and its explicit no-pact field. */
        public FileRef explicitFreshPactProfile() { return RootRuntimeDefinitionModel.explicitFreshPactProfile(originalData); }
        /** Only this original proof is optional: absence disables the cold route, never supplies guessed inputs. */
        public Optional<FileRef> optionalData(DataRole role) {
            StrictJson.require(role==DataRole.ROLLBACK_PROOF,"only the original rollback proof has optional presence");
            return originalData.stream().filter(row->row.role()==role).map(DataPin::originalRef).findFirst();
        }
    }
    public record RootBudget(String path,long maximumNativeBytes) {
        public RootBudget { absolute(path);bounded(maximumNativeBytes,4096,Long.MAX_VALUE,"runtime root native cap"); }
    }
    public record VolumeThreshold(String root,long minimumUsableBytes,long systemGrowthReserveBytes) {
        public VolumeThreshold { absolute(root);bounded(minimumUsableBytes,0,Long.MAX_VALUE,"volume free minimum");bounded(systemGrowthReserveBytes,0,Long.MAX_VALUE,"system growth reserve"); }
    }
    public record StorageLease(String schema,String purpose,String machineId,String ownerTask,String observedAtUtc,String reviewAtUtc,
            FileRef policyRef,FileRef capacityReleaseRef,FileRef runtimeBindingRef,FileRef wholeWorkpackageCensusRef,
            long wholeWorkpackageMaximumNativeBytes,List<RootBudget> roots,List<VolumeThreshold> volumes) {
        public StorageLease {
            StrictJson.require(LEASE_SCHEMA.equals(schema)&&"ROOT_GAME_RUNTIME".equals(purpose),"actual runtime storage lease required; source/build cards cannot substitute");
            machine(machineId);StrictJson.require("/root".equals(ownerTask),"sole Root runtime owner required");StrictJson.require(instant(observedAtUtc).isBefore(instant(reviewAtUtc)),"finite runtime lease required");
            for(var ref:List.of(policyRef,capacityReleaseRef,runtimeBindingRef,wholeWorkpackageCensusRef))file(ref,16L<<20);
            bounded(wholeWorkpackageMaximumNativeBytes,4096,Long.MAX_VALUE,"whole-workpackage runtime cap");roots=List.copyOf(roots);volumes=List.copyOf(volumes);
            bounded(roots.size(),1,64,"runtime roots");bounded(volumes.size(),1,16,"runtime volume thresholds");
            unique(roots.stream().map(RootBudget::path).toList(),"runtime budget root");unique(volumes.stream().map(VolumeThreshold::root).toList(),"runtime volume root");
        }
    }
    static void file(FileRef ref,long maximum) { Objects.requireNonNull(ref);absolute(ref.path());bounded(ref.bytes(),1,maximum,"exact bounded input bytes");digest(ref.sha256()); }
    /** Bounds follow each unique producer's existing wire contract; portable manifest JSON keeps its independent parser domain. */
    static int maximumDataBytes(DataRole role) {
        return switch(Objects.requireNonNull(role)) {
            case FAMILY_DOMAIN,CHILD_MATRILINEAL_DOMAIN,DEFAULT_MARRIAGE_DOMAIN->org.xar.ck3.control.continuity.ContinuityJson.DOMAIN_MAX_BYTES;
            case ORIGINAL_DRIVER_RUN_PROFILE,EXPLICIT_FRESH_PACT->RootFrozenRunProfile.MAXIMUM_REQUEST_BYTES;
            case ORIGINAL_MCP_CAPTURE_RECEIPT->org.xar.ck3.control.build.OriginalMcpCapture.CONTROL_MAX;
            case LIFE_SETTINGS->RootAdvanceRuntimeFacts.SETTINGS_MAX_BYTES;
            case ADVANCE_TIMINGS->RootAdvanceInfrastructureFactory.TIMINGS_MAX_BYTES;
            case CAMPAIGN_DEADLINE->RootCampaignPoliciesFactory.MAX_CONFIGURATION_BYTES;
            case REMAINING_DOMAIN_SETTINGS->RootRuntimeDomainSettings.MAXIMUM_BYTES;
            case NATIVE_DOMAIN_ORIGINALS->RootRuntimeNativeOriginals.MAXIMUM_BYTES;
            case PORTABLE_EVENT_EVIDENCE_MANIFEST->PortableEvidenceJson.MANIFEST_LIMIT;
            default->16<<20;
        };
    }
    /** Role binding only. The actual frozen reader still verifies the plan, environment and initial policy.
     * EXPLICIT_FRESH_PACT is the explicit field of the original Driver run profile, not a second document
     * or InitialEpisodePolicy.FreshPact. No lifecycle or game observation is inferred here. */
    static FileRef explicitFreshPactProfile(List<DataPin> originalData) {
        List<DataPin> selected=List.copyOf(originalData);
        var profiles=selected.stream().filter(row->row.role()==DataRole.ORIGINAL_DRIVER_RUN_PROFILE).toList();
        var pacts=selected.stream().filter(row->row.role()==DataRole.EXPLICIT_FRESH_PACT).toList();
        StrictJson.require(profiles.size()==1&&pacts.size()==1,
                "one original Driver run profile and one explicit fresh pact role are required");
        FileRef profile=profiles.getFirst().originalRef();
        StrictJson.require(profile.equals(pacts.getFirst().originalRef()),
                "explicit fresh pact must retain the identical original Driver run profile");
        return profile;
    }
    static void validateOriginalData(List<DataPin> originalData) {
        var required=EnumSet.allOf(DataRole.class);required.remove(DataRole.ROLLBACK_PROOF);
        var present=EnumSet.noneOf(DataRole.class);for(DataPin row:originalData)StrictJson.require(present.add(row.role()),"duplicate original data role");
        StrictJson.require(present.containsAll(required),"every mandatory original data role is required");
    }
    static SourceKind expectedKind(SourceRole role) {
        return switch(role) {
            case NATIVE_GOV_LIFESTYLE,NATIVE_GOV_COUNCIL,NATIVE_GOV_CROWN,NATIVE_GOV_FINAL_TERMS,
                 FINANCE_FACTION_DEFINITION,ARMY_CLOSED_DEFINITION,ARMY_BATTLE_DEFINITION,ARMY_ROUTE_DEFINITION,
                 ARMY_WINDOW_DEFINITION,CONSTRUCTION_NATIVE_ACTION,PRISONER_ACTION_PRODUCER,TURN_BUNDLE_DEFINITION,
                 INTERACTION_MARRIAGE,INTERACTION_LAWS,INTERACTION_CLAIMS,INTERACTION_HOLDER,INTERACTION_APPOINTMENT,
                 INTERACTION_ORDINARY,INTERACTION_PLAYER_CONTROL,INTERACTION_GRANT,INTERACTION_PENDING,INTERACTION_HEIR->SourceKind.NATIVE;
            case FRONTEND_ORIGINAL_DRIVER->SourceKind.ORIGINAL_PYTHON;
            case PRISONER_STOCK_INTERACTIONS->SourceKind.STOCK_SCRIPT;
            default->SourceKind.JAVA;
        };
    }
    static void exact(ExactRef ref) { Objects.requireNonNull(ref);absolute(ref.path());bounded(ref.bytes(),1,64L<<20,"actual source bytes");digest(ref.sha256()); }
    static void absolute(String value) { StrictJson.text(value);Path path=Path.of(value);StrictJson.require(path.isAbsolute()&&path.normalize().equals(path)&&value.indexOf('\0')<0,"canonical absolute path required"); }
    static void relative(String value) { StrictJson.text(value);StrictJson.require(!value.startsWith("/")&&!value.contains("\\")&&!value.contains(":")&&!value.contains("//"),"canonical source target required");
        for(String part:value.split("/",-1))StrictJson.require(!part.isEmpty()&&!part.equals(".")&&!part.equals(".."),"relative target traversal is forbidden"); }
    static void bounded(long value,long minimum,long maximum,String name) { StrictJson.require(value>=minimum&&value<=maximum,name); }
    static void digest(String value) { StrictJson.require(value!=null&&value.matches("[0-9a-fA-F]{64}"),"exact SHA-256 required"); }
    static void machine(String value) { StrictJson.require(value!=null&&value.matches("[a-z0-9][a-z0-9-]{0,127}")&&!value.equals("unknown"),"explicit machine identity required"); }
    static void id(String value) { StrictJson.require(value!=null&&value.matches("[A-Za-z0-9][A-Za-z0-9._-]{0,127}"),"bounded named runtime identity required"); }
    static Instant instant(String value) { StrictJson.text(value);Instant parsed=Instant.parse(value);StrictJson.require(value.equals(parsed.toString()),"canonical UTC timestamp required");return parsed; }
    static <T> void unique(List<T> values,String name) { StrictJson.require(values.stream().distinct().count()==values.size(),"duplicate "+name); }
}
