package org.xar.ck3.control.application.driver;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.*;
import org.xar.ck3.control.application.lifecycle.SeedAdoption;
import org.xar.ck3.control.application.lifecycle.SeedArtifact;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Stamp;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.application.planning.military.ActiveRetreatState;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyRetreatTokens;

/** The shared cache producer. Its only publication target is the existing sole Driver repository. */
public final class DriverCapabilityStateProducer {
    public static final String STATE_SCHEMA="xar.driver-capability-state/v2";
    public static final String TERMINAL_STATE_SCHEMA="xar.driver-terminal-capability-state/v1";
    public static final String STATE_SOURCE="capability_state_source";
    private static final String VERSION="capability_state_version";
    private static final String CONFIG="capability_configuration";
    private static final String PATHS="capability_session_paths";
    private static final String INITIAL="capability_initialization_source";
    private static final String READS="capability_read_sources";
    private static final String NATIVE="capability_observed_native_source";
    public static final int MAX_PUBLIC_PLANNING_SOURCE_REFS=16384;
    public static final int MAX_PUBLIC_TERMINAL_INPUT_BYTES=16*1024*1024;
    private static final String PUBLIC_TERMINAL="public_planning_terminal_inputs";
    private static final Set<String> CACHE_KEYS=Set.of("arrange_marriage_choices","arrange_marriage_query_sequence",
            "campaign_root_context_query","active_combat_retreat_token","episode_seed","episode_transition","succession_reconciliation",
            "driver_state_restored","driver_state_error","restore_kind","episode_binding_state","cold_candidate_rejection",
            "episode_transition_error","independent_battle_speed_readiness",CONFIG,PATHS,INITIAL,READS,NATIVE);
    private DriverCapabilityStateProducer() { }

    /** Private minting prevents a caller from turning an arbitrary auxiliary map into a repository publication. */
    public static final class InitialAuxiliary {
        private final Stamp expectedStamp;
        private final String expectedAuxiliarySha256;
        private final Obj auxiliary;
        private final ExactRef source;
        InitialAuxiliary(Known before,Obj auxiliary,ExactRef source) {
            expectedStamp=before.stamp();expectedAuxiliarySha256=DriverJson.sha256(DriverJson.encode(before.auxiliary()));
            this.auxiliary=auxiliary;this.source=source;
        }
        public Stamp expectedStamp() { return expectedStamp; }
        public String expectedAuxiliarySha256() { return expectedAuxiliarySha256; }
        public Obj auxiliary() { return auxiliary; }
        public ExactRef source() { return source; }
    }
    public enum Cause { INITIAL_NEW_EPISODE, MARRIAGE_QUERY, CAMPAIGN_ROOT_QUERY, OBSERVED_FRAME, RETREAT_DOMAIN, IMMUTABLE_SEED, INDEPENDENT_READINESS, MARRIAGE_ATTEMPT, SEMANTIC_QUERY, PERSISTENT_PLANNING, PUBLIC_PLANNING_VIEW }

    /** Actual current-frame input DATA. Private construction and raw-scope custody prevent this
     * uncommitted view from becoming a Driver publication, readiness or a reusable action permit. */
    public static final class PublicPlanningInputs implements DynamicCapabilities.ActualDriverInputsSource {
        private final DriverStateAssembler.ReadOnlyPlanningScope scope;
        private final Complete frame;
        private final Known known;
        private final ActionPorts.OutcomeArchive archive;
        private final ExactRef originalState,originalInputs;
        private final DynamicCapabilities.DriverInputs inputs;
        private final Optional<PublicTerminalInputs> terminalInputs;
        private PublicPlanningInputs(DriverStateAssembler.ReadOnlyPlanningScope scope,Complete frame,Known known,
                InitialAuxiliary prepared,Optional<PublicTerminalInputs> terminalInputs,ActionPorts.OutcomeArchive archive)throws java.io.IOException {
            this.scope=Objects.requireNonNull(scope);this.frame=frame;this.known=known;this.archive=archive;
            this.terminalInputs=terminalInputs;
            scope.requireInputs(frame,known);
            require(prepared.expectedStamp().equals(known.stamp())
                    &&prepared.expectedAuxiliarySha256().equals(DriverJson.sha256(DriverJson.encode(known.auxiliary()))),
                    "public planning view crossed its actual immutable Driver owner");
            originalState=prepared.source();
            require(replay(frame,known,originalState,archive).equals(prepared.auxiliary()),
                    "public planning input source differs from the actual shared original replay");
            originalInputs=decodeReference(object(prepared.auxiliary().get(DriverRuntimeCapabilities.AUXILIARY_KEY),DriverRuntimeCapabilities.AUXILIARY_KEY));
            inputs=DynamicCapabilities.DriverInputs.decode(frame,known,originalInputs,readMaterial(archive,originalInputs).bytes());
            require(terminalInputs.isEmpty()
                    ? !prepared.auxiliary().members().containsKey(PUBLIC_TERMINAL)
                    : reference(terminalInputs.orElseThrow().original()).equals(prepared.auxiliary().get(PUBLIC_TERMINAL)),
                    "public planning original terminal-input role differs from its actual live product");
            requireScope(frame,known);
        }
        public void requireScope(Complete actual,Known current)throws java.io.IOException {
            scope.requireInputs(actual,current);require(actual==frame&&current==known,"public planning view lost its actual producer objects");
            readMaterial(archive,originalState);readMaterial(archive,originalInputs);
            if(terminalInputs.isPresent())terminalInputs.orElseThrow().requireScope(actual.originalProjection().orElseThrow(),current);
        }
        public void verifySource(ExactRef actual)throws IOException{scope.verifySource(actual);}
        public Optional<org.xar.ck3.control.contracts.NativeColdAdoptionProjection.Lifecycle> privateCapabilityLifecycle(){
            return terminalInputs.map(PublicTerminalInputs::capabilityLifecycle);
        }
        @Override public DynamicCapabilities.InputState capture(Complete actual,Known current)throws java.io.IOException {
            requireScope(actual,current);return new DynamicCapabilities.AvailableInputs(inputs);
        }
        @Override public boolean stillCurrent(DynamicCapabilities.DriverInputs captured,Complete actual,Known current)throws java.io.IOException {
            requireScope(actual,current);return captured==inputs&&captured.originalFacts().equals(originalInputs);
        }
    }
    public enum PublicTerminalLifecycleMode { OBSERVED_BINDING, NATIVE_CAMPAIGN_FIXTURE_NULL_CONSTRUCTOR, NATIVE_CAMPAIGN_SAVED_NULL_CONSTRUCTOR }
    public enum DeclaredLifecyclePresence { MISSING, NULL, VALUE }
    /** The original private capability input is a distinct role from public snapshot/game-rule lifecycle. */
    public record PublicTerminalLifecycleData(PublicTerminalLifecycleMode mode,
            DeclaredLifecyclePresence declaredPresence,Value declaredLifecycle,
            org.xar.ck3.control.contracts.NativeColdAdoptionProjection.Lifecycle capabilityLifecycle,
            Optional<ExactRef> policySource,Optional<ExactRef> environmentSource,Optional<ExactRef> nativeSource,List<ExactRef> sourceClosure) {
        public static final String SCHEMA="xar.public-terminal-lifecycle-inputs/v1";
        public PublicTerminalLifecycleData {
            Objects.requireNonNull(mode);Objects.requireNonNull(declaredPresence);Objects.requireNonNull(declaredLifecycle);Objects.requireNonNull(capabilityLifecycle);
            require((declaredPresence==DeclaredLifecyclePresence.VALUE)==(declaredLifecycle!=Nil.INSTANCE),"declared lifecycle presence/value roles differ");
            Objects.requireNonNull(policySource);Objects.requireNonNull(environmentSource);Objects.requireNonNull(nativeSource);sourceClosure=List.copyOf(sourceClosure);
            require(sourceClosure.size()<=MAX_PUBLIC_PLANNING_SOURCE_REFS&&sourceClosure.stream().distinct().count()==sourceClosure.size()&&sourceClosure.stream().allMatch(ref->ref.bytes()>=0),"terminal lifecycle source closure cannot contain aliases");
            if(mode==PublicTerminalLifecycleMode.OBSERVED_BINDING){
                require(declaredPresence==DeclaredLifecyclePresence.VALUE&&DriverJson.fromNode(capabilityLifecycle.toJson()).equals(declaredLifecycle)&&policySource.isEmpty()&&environmentSource.isEmpty()
                        &&nativeSource.isEmpty()&&sourceClosure.isEmpty(),"observed lifecycle DATA must preserve its actual six-field binding");
            }else{
                require(capabilityLifecycle.equals(privateNullConstructorLifecycle())
                        &&policySource.filter(ref->ref.bytes()>0).isPresent()&&environmentSource.filter(ref->ref.bytes()>0).isPresent()&&nativeSource.filter(ref->ref.bytes()>0).isPresent()
                        &&sourceClosure.containsAll(List.of(policySource.orElseThrow(),environmentSource.orElseThrow(),nativeSource.orElseThrow())),
                        "native_campaign private constructor DATA requires its explicit actual policy/source closure");
            }
        }
        public Obj toJson(){
            return new Obj(Map.of("schema",new Text(SCHEMA),"mode",new Text(mode.name()),
                    "declared_presence",new Text(declaredPresence.name()),"declared_lifecycle",declaredLifecycle,
                    "capability_lifecycle",DriverJson.fromNode(capabilityLifecycle.toJson()),"policy_source",nullableReference(policySource),
                    "environment_source",nullableReference(environmentSource),"native_source",nullableReference(nativeSource),
                    "source_closure",new Arr(sourceClosure.stream().map(value->(Value)reference(value)).toList())));
        }
    }
    static org.xar.ck3.control.contracts.NativeColdAdoptionProjection.Lifecycle privateNullConstructorLifecycle(){
        // Exact native_driver.py2119..2125 constructor branch. This is private capability DATA, never a game-rule/pact assertion.
        return new org.xar.ck3.control.contracts.NativeColdAdoptionProjection.Lifecycle("rogue_one_life",Optional.of("xar_on"),
                "terminal_settlement_required","legacy-driver-default",Optional.empty());
    }
    private static org.xar.ck3.control.contracts.NativeColdAdoptionProjection.Lifecycle lifecycleObject(Obj row){
        require(row.members().keySet().equals(Set.of("schema","lifecycle","xar_enabled","pact_contract","source","environment_sha256"))
                &&new Text("xar.ck3.succession-lifecycle-binding/v1").equals(row.get("schema")),"strict six-field original lifecycle DATA required");
        var result=new org.xar.ck3.control.contracts.NativeColdAdoptionProjection.Lifecycle(text(row.get("lifecycle"),"lifecycle"),
                optionalString(row,"xar_enabled"),text(row.get("pact_contract"),"pact_contract"),text(row.get("source"),"source"),optionalString(row,"environment_sha256"));
        require(DriverJson.fromNode(result.toJson()).equals(row),"normalized lifecycle DATA differs from its actual original");return result;
    }
    private static Optional<String> optionalString(Obj row,String field){Value value=row.get(field);return value==Nil.INSTANCE?Optional.empty():Optional.of(text(value,field));}
    private static Value nullableReference(Optional<ExactRef> value){return value.<Value>map(DriverCapabilityStateProducer::reference).orElse(Nil.INSTANCE);}
    private static Optional<ExactRef> optionalReference(Obj row,String field){Value value=row.get(field);return value==Nil.INSTANCE?Optional.empty():Optional.of(decodeReference(object(value,field)));}
    private static PublicTerminalLifecycleData decodePublicTerminalLifecycle(Obj row){
        require(row.members().keySet().equals(Set.of("schema","mode","declared_presence","declared_lifecycle","capability_lifecycle","policy_source","environment_source","native_source","source_closure"))
                &&new Text(PublicTerminalLifecycleData.SCHEMA).equals(row.get("schema")),"strict terminal lifecycle input fields/schema required");
        Value declared=row.get("declared_lifecycle");List<ExactRef> refs=new ArrayList<>();
        for(Value value:array(row.get("source_closure"),"source_closure"))refs.add(decodeReference(object(value,"source reference")));
        return new PublicTerminalLifecycleData(PublicTerminalLifecycleMode.valueOf(text(row.get("mode"),"mode")),
                DeclaredLifecyclePresence.valueOf(text(row.get("declared_presence"),"declared_presence")),declared,
                lifecycleObject(object(row.get("capability_lifecycle"),"capability_lifecycle")),optionalReference(row,"policy_source"),
                optionalReference(row,"environment_source"),optionalReference(row,"native_source"),refs);
    }
    public record PublicTerminalWire(String frameSha256,ExactRef nativePacket,ExactRef semanticSource,ExactRef fullDriver,
            BigInteger stateVersion,DynamicCapabilities.Configuration configuration,Optional<Obj> episodeSeed,
            Optional<Obj> episodeTransition,Optional<Obj> successionReconciliation,PublicTerminalLifecycleData lifecycleInputs) {
        public static final String SCHEMA="xar.public-terminal-capability-inputs/v2";
        public PublicTerminalWire {
            require(frameSha256!=null&&frameSha256.matches("[0-9a-f]{64}"),"terminal frame digest must be canonical SHA256");
            Objects.requireNonNull(nativePacket);Objects.requireNonNull(semanticSource);Objects.requireNonNull(fullDriver);
            require(stateVersion!=null&&stateVersion.signum()>=0,"terminal capability state version must be nonnegative");
            Objects.requireNonNull(configuration);Objects.requireNonNull(episodeSeed);Objects.requireNonNull(episodeTransition);Objects.requireNonNull(successionReconciliation);Objects.requireNonNull(lifecycleInputs);
        }
        public Obj toJson(){
            Map<String,Value> row=new LinkedHashMap<>();row.put("schema",new Text(SCHEMA));row.put("frame_sha256",new Text(frameSha256));
            row.put("native",reference(nativePacket));row.put("semantic_source",reference(semanticSource));row.put("full_driver",reference(fullDriver));
            row.put("state_version",new Text(stateVersion.toString()));row.put("configuration",DynamicCapabilities.encodeConfiguration(configuration));
            row.put("episode_seed",nullable(episodeSeed));row.put("episode_transition",nullable(episodeTransition));
            row.put("succession_reconciliation",nullable(successionReconciliation));row.put("lifecycle_inputs",lifecycleInputs.toJson());return new Obj(row);
        }
    }
    /** Single strict decoder for producer replay and negative/roundtrip regression. DATA alone grants no scope. */
    public static PublicTerminalWire decodePublicTerminalWire(byte[] original){
        Obj row=DriverJson.object(original,MAX_PUBLIC_TERMINAL_INPUT_BYTES);
        require(row.members().keySet().equals(Set.of("schema","frame_sha256","native","semantic_source","full_driver",
                "state_version","configuration","episode_seed","episode_transition","succession_reconciliation","lifecycle_inputs"))
                &&new Text(PublicTerminalWire.SCHEMA).equals(row.get("schema")),"terminal capability input strict fields/schema required");
        String version=text(row.get("state_version"),"state_version");require(version.matches("0|[1-9][0-9]*"),"canonical decimal terminal state version required");
        return new PublicTerminalWire(text(row.get("frame_sha256"),"frame_sha256"),decodeReference(object(row.get("native"),"native")),
                decodeReference(object(row.get("semantic_source"),"semantic_source")),decodeReference(object(row.get("full_driver"),"full_driver")),
                new BigInteger(version),DynamicCapabilities.decodeConfiguration(object(row.get("configuration"),"configuration")),
                optionalObject(row,"episode_seed"),optionalObject(row,"episode_transition"),optionalObject(row,"succession_reconciliation"),
                decodePublicTerminalLifecycle(object(row.get("lifecycle_inputs"),"lifecycle_inputs")));
    }
    private static Optional<Obj> optionalObject(Obj row,String field){
        Value actual=row.get(field);return actual==Nil.INSTANCE?Optional.empty():Optional.of(object(actual,field));
    }
    /** Internal application port. The actual runtime retains its privately constructed capture and full source/owner checks. */
    interface SourceLifecycleCapture {
        void requireCurrent(DriverStateAssembler.ReadOnlyTerminalPlanningScope scope,
                DriverObservationAssembler.FullSnapshot actual,Known current)throws IOException;
        PublicTerminalLifecycleData data();
    }
    /** Three-role terminal planning DATA over the actual full raw subject. It never creates an
     * ordinary frame/actor, DriverInputs stamp, lifecycle lease or action permission. */
    public static final class PublicTerminalInputs {
        private final DriverStateAssembler.ReadOnlyTerminalPlanningScope scope;
        private final DriverObservationAssembler.FullSnapshot full;
        private final Known known;
        private final DriverRuntimeCapabilities.Fields fields;
        private final ActionPorts.OutcomeArchive archive;
        private final ExactRef original;
        private final Obj wire;
        private final PublicTerminalLifecycleData lifecycle;
        private final Optional<SourceLifecycleCapture> lifecycleCapture;
        private PublicTerminalInputs(DriverStateAssembler.ReadOnlyTerminalPlanningScope scope,
                DriverObservationAssembler.FullSnapshot full,Known known,DriverRuntimeCapabilities.Fields fields,
                Obj wire,PublicTerminalLifecycleData lifecycle,Optional<SourceLifecycleCapture> lifecycleCapture,
                ActionPorts.OutcomeArchive archive)throws IOException {
            this.scope=scope;this.full=full;this.known=known;this.fields=fields;this.archive=archive;this.wire=wire;
            this.lifecycle=lifecycle;this.lifecycleCapture=lifecycleCapture;
            scope.requireInputs(full,known);byte[] originalBytes=DriverJson.encode(wire);require(originalBytes.length<=MAX_PUBLIC_TERMINAL_INPUT_BYTES,"bounded complete terminal capability input required");
            original=archive.preserveMaterial(RawJson.fullMaterial(originalBytes));requireScope(full,known);
        }
        public void requireScope(DriverObservationAssembler.FullSnapshot actual,Known current)throws IOException {
            scope.requireInputs(actual,current);require(actual==full&&current==known,"terminal input view crossed its actual producer objects");
            if(lifecycleCapture.isPresent())lifecycleCapture.orElseThrow().requireCurrent(scope,actual,current);
            PublicTerminalWire restored=decodePublicTerminalWire(readMaterial(archive,original).bytes());
            require(restored.toJson().equals(wire),"terminal capability input original changed its strict field contract");
        }
        public DynamicCapabilities.Configuration configuration(){return fields.configuration();}
        public Optional<Obj> episodeSeed(){return fields.episodeSeed();}
        public Optional<Obj> episodeTransition(){return fields.episodeTransition();}
        public Optional<Obj> successionReconciliation(){return fields.successionReconciliation();}
        public ExactRef original(){return original;}
        public void verifySource(ExactRef actual)throws IOException{scope.verifySource(actual);}
        public org.xar.ck3.control.contracts.NativeColdAdoptionProjection.Lifecycle capabilityLifecycle(){return lifecycle.capabilityLifecycle();}
        public boolean nativeCampaignConstructor(){return lifecycle.mode()!=PublicTerminalLifecycleMode.OBSERVED_BINDING;}
    }
    public static PublicTerminalInputs publicTerminalInputs(DriverStateAssembler.ReadOnlyTerminalPlanningScope scope,
            DriverObservationAssembler.FullSnapshot full,Known current,DriverPersistentPlanningState.Publication canonical,
            ActionPorts.OutcomeArchive archive)throws IOException {
        return publicTerminalInputs(scope,full,current,canonical,Optional.empty(),archive);
    }
    static PublicTerminalInputs publicTerminalInputs(DriverStateAssembler.ReadOnlyTerminalPlanningScope scope,
            DriverObservationAssembler.FullSnapshot full,Known current,DriverPersistentPlanningState.Publication canonical,
            Optional<SourceLifecycleCapture> lifecycleCapture,ActionPorts.OutcomeArchive archive)throws IOException {
        Objects.requireNonNull(scope).requireInputs(full,current);Objects.requireNonNull(canonical);
        require(canonical.expectedStamp().equals(current.stamp())
                &&canonical.expectedAuxiliarySha256().equals(DriverJson.sha256(DriverJson.encode(current.auxiliary()))),
                "terminal input view crossed its actual canonical cross-run source");
        DriverPersistentPlanningState.replay(canonical.auxiliary(),archive);
        Map<String,Value> auxiliary=initialized(current);auxiliary.putAll(canonical.auxiliary().members());
        readMaterial(archive,decodeReference(object(auxiliary.get(INITIAL),INITIAL)));
        replaySuccessionSource(new Obj(auxiliary),archive);replayImmutableSeedSource(new Obj(auxiliary),archive);
        DriverRuntimeCapabilities.Fields fields=fields(new Obj(auxiliary));
        PublicTerminalLifecycleData lifecycle;
        if(lifecycleCapture.isPresent()){lifecycleCapture.orElseThrow().requireCurrent(scope,full,current);lifecycle=lifecycleCapture.orElseThrow().data();}
        else {
            require(full.facts().observationVersion()!=DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION,
                    "native_campaign needs its actual installed source-owned constructor input; a raw lifecycle field grants no default");
            var declared=lifecycleObject(object(full.semantic().get("succession_lifecycle"),"actual observed lifecycle"));
            lifecycle=new PublicTerminalLifecycleData(PublicTerminalLifecycleMode.OBSERVED_BINDING,DeclaredLifecyclePresence.VALUE,DriverJson.fromNode(declared.toJson()),declared,
                    Optional.empty(),Optional.empty(),Optional.empty(),List.of());
        }
        ExactRef driver=archive.preserveMaterial(RawJson.fullMaterial(current.driver().encode()));
        PublicTerminalWire wire=new PublicTerminalWire(full.fullBindingSha256(),full.originalEvidence(),
                current.observation().orElseThrow().semanticFactsEvidence(),driver,version(current.auxiliary()),fields.configuration(),
                fields.episodeSeed(),fields.episodeTransition(),fields.successionReconciliation(),lifecycle);
        return new PublicTerminalInputs(scope,full,current,fields,wire.toJson(),lifecycle,lifecycleCapture,archive);
    }

    /** Called by the sole lifecycle reducer after its genuine episode-cache clear, preserving unrelated original state. */
    public static Obj afterEpisodeCacheClear(Obj actualReducedAuxiliary) {
        boolean hasCapabilityState=actualReducedAuxiliary.members().containsKey(STATE_SOURCE);
        if(!hasCapabilityState&&!actualReducedAuxiliary.members().containsKey(DriverPreclockExpectationProducer.SOURCE_KEY))return actualReducedAuxiliary;
        require(new Arr(List.of()).equals(actualReducedAuxiliary.get("arrange_marriage_choices"))
                && actualReducedAuxiliary.get("arrange_marriage_query_sequence")==Nil.INSTANCE
                && actualReducedAuxiliary.get("active_combat_retreat_token")==Nil.INSTANCE,"lifecycle has not actually cleared its episode caches");
        Map<String,Value> auxiliary=new LinkedHashMap<>(actualReducedAuxiliary.members());
        auxiliary.remove(DriverPreclockExpectationProducer.SOURCE_KEY);
        if(!hasCapabilityState)return new Obj(auxiliary);
        Obj originals=object(auxiliary.get(READS),READS);Map<String,Value> reads=new LinkedHashMap<>(originals.members());reads.put("marriage",Nil.INSTANCE);
        auxiliary.put(READS,new Obj(reads));auxiliary.remove("capability_retreat_source");if(auxiliary.get("succession_reconciliation")==Nil.INSTANCE)auxiliary.remove("capability_succession_source");return DriverSemanticReadState.clearForCold(new Obj(auxiliary));
    }
    /** One explicit conversion of the sole lifecycle/private producer into its public presentation contract. */
    public static CapabilitySessionPresentation sessionPresentation(Obj actualAuxiliary) {
        Obj p=object(actualAuxiliary.get(PATHS),PATHS);Map<String,Value> presentation=new LinkedHashMap<>();
        for(String key:List.of("driver_state_restored","driver_state_error","episode_binding_state","cold_candidate_rejection","episode_transition_error")) {
            require(actualAuxiliary.members().containsKey(key),"actual session owner field missing: "+key);presentation.put(key,actualAuxiliary.get(key));
        }
        require(actualAuxiliary.members().containsKey("restore_kind"),"actual private restore kind missing");
        presentation.put("driver_state_restore_kind",actualAuxiliary.get("restore_kind"));presentation.put("queue_dir",p.get("queue_dir"));presentation.put("driver_state_path",p.get("driver_state_path"));
        return CapabilitySessionPresentation.decode(new Obj(presentation));
    }

    /** Invoked only by the actual fresh-entry factory after its first genuine native/Driver observation. */
    public static InitialAuxiliary initializeNewEpisode(Complete first,Known current,DynamicCapabilities.Configuration configuration,
            CapabilitySessionPresentation presentation,ExactRef archivedStartupPolicy,ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(first);Objects.requireNonNull(current);Objects.requireNonNull(configuration);Objects.requireNonNull(presentation);
        require(current.driver().commandHistory().isEmpty() && !current.auxiliary().members().containsKey(DriverRuntimeCapabilities.AUXILIARY_KEY)
                && !current.auxiliary().members().containsKey(STATE_SOURCE),"new cache initialization requires the actual fresh empty gameplay branch, once");
        require(!presentation.driverStateRestored() && presentation.restoreKind().equals(Optional.of(CapabilitySessionPresentation.RestoreKind.NEW_EPISODE))
                && presentation.bindingState()==CapabilitySessionPresentation.BindingState.ACTIVE_NEW
                && presentation.driverStateError().isEmpty() && presentation.coldCandidateRejection().isEmpty()
                && presentation.episodeTransitionError().isEmpty(),"actual new-episode session initialization required");
        presentation.validateConfiguration(configuration);readMaterial(archive,archivedStartupPolicy);
        Map<String,Value> aux=new LinkedHashMap<>(current.auxiliary().members());
        putInitial(aux,"arrange_marriage_choices",new Arr(List.of()));putInitial(aux,"arrange_marriage_query_sequence",Nil.INSTANCE);
        for(String key:List.of("campaign_root_context_query","active_combat_retreat_token","episode_seed","episode_transition",
                "succession_reconciliation","independent_battle_speed_readiness"))putInitial(aux,key,Nil.INSTANCE);
        putInitial(aux,"driver_state_restored",new Bool(false));putInitial(aux,"driver_state_error",Nil.INSTANCE);
        putInitial(aux,"restore_kind",new Text("new_episode"));putInitial(aux,"episode_binding_state",new Text("active_new"));
        for(String key:List.of("cold_candidate_rejection","episode_transition_error"))putInitial(aux,key,Nil.INSTANCE);
        putInitial(aux,CONFIG,configuration(configuration));putInitial(aux,PATHS,paths(presentation));
        putInitial(aux,INITIAL,reference(archivedStartupPolicy));putInitial(aux,READS,new Obj(Map.of("marriage",Nil.INSTANCE,"campaign_root",Nil.INSTANCE)));
        return mint(first,current,DriverSemanticReadState.initializeFresh(new Obj(aux)),BigInteger.ZERO,Cause.INITIAL_NEW_EPISODE,archive);
    }

    /** The exact successfully decoded/archived read is the producer; an ACK or request alone is refused. */
    public static InitialAuxiliary observeRead(Complete frame,Known current,PlanningReadResult.Known<?> actual,
            ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(actual);PlanningReadReceipt receipt=archive.loadRead(actual.originalReceipt());
        require(receipt.equals(actual.receipt()) && archive.readReferenceOf(receipt).equals(actual.originalReceipt()),"cache read is not the original archived successful decoder result");
        requireRead(frame,receipt);String step=receipt.request().operation().value();
        require(step.equals("query-arrange-marriage-choices") || step.equals("query-campaign-root-context-v1"),"read does not own a capability cache");
        Map<String,Value> aux=initialized(current);Obj oldSources=object(aux.get(READS),READS);
        Map<String,Value> sources=new LinkedHashMap<>(oldSources.members());Cause cause;
        if(step.equals("query-arrange-marriage-choices")) {
            Obj result=result(receipt);Arr choices=marriage(result,receipt);
            aux.put("arrange_marriage_choices",choices);aux.put("arrange_marriage_query_sequence",result.get("query_sequence"));
            sources.put("marriage",reference(actual.originalReceipt()));cause=Cause.MARRIAGE_QUERY;
        } else {
            aux.put("campaign_root_context_query",campaignRoot(result(receipt),receipt));
            sources.put("campaign_root",reference(actual.originalReceipt()));cause=Cause.CAMPAIGN_ROOT_QUERY;
        }
        aux.put(READS,new Obj(sources));return mint(frame,current,new Obj(aux),nextVersion(current),cause,archive);
    }
    public static InitialAuxiliary observeSemanticRead(Complete frame,Known current,ReadContract<?> installed,
            PlanningReadResult.Known<?> actual,ActionPorts.OutcomeArchive archive) {
        requireRead(frame,actual.receipt());
        Obj changed=DriverSemanticReadState.apply(frame,new Obj(initialized(current)),installed,actual,archive);
        return mint(frame,current,changed,nextVersion(current),Cause.SEMANTIC_QUERY,archive);
    }
    public static InitialAuxiliary observeSemanticRead(Complete frame,Known current,ReadContract<?> installed,
            PlanningReadResult.Known<?> actual,org.xar.ck3.control.nativebridge.capabilities.army.ArmyWindowAttempts.Snapshot attempts,
            ActionPorts.OutcomeArchive archive) {
        requireRead(frame,actual.receipt());
        Obj changed=DriverSemanticReadState.apply(frame,new Obj(initialized(current)),installed,actual,archive);
        changed=DriverSemanticReadState.withWindowAttempts(changed,attempts,archive);
        return mint(frame,current,changed,nextVersion(current),Cause.SEMANTIC_QUERY,archive);
    }
    public static InitialAuxiliary observePersistentPlanning(Complete frame,Known current,DriverPersistentPlanningState.Publication actual,ActionPorts.OutcomeArchive archive) {
        require(actual.expectedStamp().equals(current.stamp())&&actual.expectedAuxiliarySha256().equals(DriverJson.sha256(DriverJson.encode(current.auxiliary()))),"persistent planning publication crossed its exact original Driver owner");
        DriverPersistentPlanningState.replay(actual.auxiliary(),archive);
        return mint(frame,current,actual.auxiliary(),nextVersion(current),Cause.PERSISTENT_PLANNING,archive);
    }
    /** A distinct terminal data branch. No ordinary Complete, capsule or action capability is produced. */
    public static InitialAuxiliary observeTerminalStrategy(DriverObservationAssembler.FullSnapshot full,LifecycleIdentity terminal,
            Known current,DriverPersistentPlanningState.Publication actual,ActionPorts.OutcomeArchive archive) {
        require(actual.expectedStamp().equals(current.stamp())&&actual.expectedAuxiliarySha256().equals(DriverJson.sha256(DriverJson.encode(current.auxiliary()))),"terminal strategy crossed its exact original Driver CAS");
        requireTerminalOriginal(full,terminal,current,archive);DriverPersistentPlanningState.replay(actual.auxiliary(),archive);
        Obj owner=ownerAuxiliary(actual.auxiliary().with(NATIVE,reference(full.originalEvidence())));BigInteger version=nextVersion(current);
        Obj state=new Obj(Map.of("schema",new Text(TERMINAL_STATE_SCHEMA),"state_version",new Text(version.toString()),
                "terminal",parse(org.xar.ck3.control.contracts.StrictJson.canonical(LifecycleIdentityCodec.encode(terminal))),
                "semantic_source",reference(full.facts().semanticFactsEvidence()),"native",reference(full.originalEvidence()),
                "before_auxiliary",current.auxiliary(),"owner_auxiliary",owner));
        ExactRef source=archive.preserveMaterial(new RawJson(DriverJson.encode(state)));
        Obj auxiliary=owner.with(VERSION,new Text(version.toString())).with(STATE_SOURCE,reference(source)).with(DriverRuntimeCapabilities.AUXILIARY_KEY,Nil.INSTANCE);
        InitialAuxiliary result=new InitialAuxiliary(current,auxiliary,source);
        var after=new Known(current.driver(),current.stamp(),current.originalHistoryBasis(),current.actionRows(),auxiliary,current.loop(),current.observation());
        require(replayTerminal(after,source,archive).equals(auxiliary),"terminal strategy failed its identical archived consumer");return result;
    }
    /** Historical terminal data may be replayed without creating ordinary planning/SAVE eligibility. */
    public static Obj replayTerminal(Known originalDriver,ExactRef originalState,ActionPorts.OutcomeArchive archive) {
        Obj state=DriverJson.object(readMaterial(archive,originalState).bytes(),DriverJson.MAX_NATIVE_BYTES);
        require(state.members().keySet().equals(Set.of("schema","state_version","terminal","semantic_source","native","before_auxiliary","owner_auxiliary"))
                &&new Text(TERMINAL_STATE_SCHEMA).equals(state.get("schema")),"exact terminal capability-state contract required");
        LifecycleIdentity terminal=LifecycleIdentityCodec.decode(toNode(state.get("terminal")));ExactRef manifest=decodeReference(object(state.get("semantic_source"),"semantic_source"));
        RawJson body=readMaterial(archive,manifest);ExactRef nativeSource=decodeReference(object(state.get("native"),"native"));
        var actual=DriverObservationEvidenceReader.nativeFrame(manifest,body,archive.loadNativeFrame(nativeSource));
        RawJson driver=readMaterial(archive,DriverObservationEvidenceReader.currentDriverReference(manifest,body));
        var facts=DriverObservationEvidenceReader.decode(manifest,body,driver,actual);
        var full=new DriverObservationAssembler().projectFull(actual,facts,nativeSource);
        var before=new Known(originalDriver.driver(),originalDriver.stamp(),originalDriver.originalHistoryBasis(),originalDriver.actionRows(),
                object(state.get("before_auxiliary"),"before_auxiliary"),originalDriver.loop(),Optional.of(facts));
        requireTerminalOriginal(full,terminal,before,archive);
        Obj owner=object(state.get("owner_auxiliary"),"owner_auxiliary");require(ownerAuxiliary(owner).equals(owner),"terminal owner contains circular capsule/state fields");
        DriverPersistentPlanningState.replay(owner,archive);DriverSemanticReadState.replaySources(owner,archive);replaySuccessionSource(owner,archive);
        BigInteger version=decimal(state.get("state_version"),"state_version");
        return owner.with(VERSION,new Text(version.toString())).with(STATE_SOURCE,reference(originalState)).with(DriverRuntimeCapabilities.AUXILIARY_KEY,Nil.INSTANCE);
    }
    /** Actual terminal snapshot producers call under their original writer; this DATA check grants no NEXT authority. */
    public static org.xar.ck3.control.application.planning.campaign.CrossRunPlanning.State requireCurrentTerminalStrategy(
            org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,Known current,ActionPorts.OutcomeArchive archive) throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(current);Objects.requireNonNull(archive);
        ExactRef originalState=decodeReference(object(current.auxiliary().get(STATE_SOURCE),STATE_SOURCE));
        require(replayTerminal(current,originalState,archive).equals(current.auxiliary()),"terminal current auxiliary differs from its complete original source replay");
        return DriverPersistentPlanningState.requireCurrentStrategy(same,current,archive);
    }
    private static void requireTerminalOriginal(DriverObservationAssembler.FullSnapshot full,LifecycleIdentity terminal,Known current,ActionPorts.OutcomeArchive archive) {
        require(current.observation().filter(full.facts()::equals).isPresent()&&Arrays.equals(current.driver().encode(),full.facts().driver().encode())
                &&current.stamp().driverVersion()==full.facts().driverVersion()&&current.stamp().episodeEpoch()==full.facts().episodeEpoch()
                &&current.stamp().game().equals(full.actual().session().game())&&current.stamp().episodeRunId().equals(full.facts().driver().session().episodeRunId()),
                "terminal strategy lacks its actual complete current Driver/native Game birth, episode or facts");
        require(terminal.evidence().nativePacket().equals(full.originalEvidence())&&terminal.evidence().observationManifest().equals(full.facts().semanticFactsEvidence()),"terminal strategy crossed original native/manifest sources");
        for(ExactRef source:terminal.supportingEvidence())readMaterial(archive,source);
        byte[] packet=archive.loadNativeFrame(full.originalEvidence());require(Arrays.equals(packet,full.actual().originalPacket()),"terminal original native packet differs");
        for(var field:current.auxiliary().members().entrySet())require(Objects.equals(full.facts().originalSemanticFields().get(field.getKey()),field.getValue()),"terminal original owner auxiliary differs from the actual manifest: "+field.getKey());
        var reprojected=new DriverObservationAssembler().projectFull(full.actual(),full.facts(),full.originalEvidence());
        require(reprojected.semantic().equals(full.semantic())&&reprojected.fullBindingSha256().equals(full.fullBindingSha256()),"terminal full projection differs from its sole original producer");
        var projected=LifecycleOriginFactory.project(reprojected,terminal.evidence().helloPacket(),terminal.evidence().originalDriver(),terminal.evidence().completeSourceQualification());
        require(projected instanceof LifecycleOriginFactory.Projected&&((LifecycleOriginFactory.Projected)projected).identity().equals(terminal),"terminal identity is not the actual source-bound lifecycle projection");
    }
    /** One repository CAS joins independently replayed persistent facts, the actual retreat domain and window attempts. */
    public static Optional<InitialAuxiliary> observeCurrentFrame(Complete frame,Known current,
            Optional<DriverPersistentPlanningState.Publication> persistent,Optional<Obj> actualToken,ExactRef originalDomainState,
            org.xar.ck3.control.nativebridge.capabilities.army.ArmyWindowAttempts.Snapshot attempts,ActionPorts.OutcomeArchive archive) {
        return refreshPrepared(frame,current,currentFrameAuxiliary(current,persistent,actualToken,originalDomainState,attempts,archive),archive);
    }
    /** Deferred availability drop is joined to the existing observation publication, outside raw callbacks. */
    public static Optional<InitialAuxiliary> observeCurrentFrame(Complete frame,Known current,
            Optional<DriverPersistentPlanningState.Publication> persistent,Optional<Obj> actualToken,ExactRef originalDomainState,
            org.xar.ck3.control.nativebridge.capabilities.army.ArmyWindowAttempts.Snapshot attempts,Optional<ExactRef> unavailableArmyCore,
            ActionPorts.OutcomeArchive archive) {
        Obj auxiliary=currentFrameAuxiliary(current,persistent,actualToken,originalDomainState,attempts,archive);
        auxiliary=DriverSemanticReadState.clearArmyCoreIfSource(auxiliary,Objects.requireNonNull(unavailableArmyCore));
        return refreshPrepared(frame,current,auxiliary,archive);
    }
    public static Optional<InitialAuxiliary> refreshAfterUnavailableArmyCore(Complete frame,Known current,
            Optional<ExactRef> source,ActionPorts.OutcomeArchive archive) {
        return refreshPrepared(frame,current,DriverSemanticReadState.clearArmyCoreIfSource(new Obj(initialized(current)),source),archive);
    }
    /** Uses the identical full current-state producer and serializer, without publishing its result
     * to the Driver. The actual runtime state version stays unchanged in this read-only view. */
    public static PublicPlanningInputs publicPlanningInputs(DriverStateAssembler.ReadOnlyPlanningScope scope,Complete frame,Known current,
            Optional<DriverPersistentPlanningState.Publication> persistent,Optional<Obj> actualToken,ExactRef originalDomainState,
            org.xar.ck3.control.nativebridge.capabilities.army.ArmyWindowAttempts.Snapshot attempts,ActionPorts.OutcomeArchive archive)throws java.io.IOException {
        return publicPlanningInputs(scope,frame,current,persistent,actualToken,originalDomainState,attempts,Optional.empty(),archive);
    }
    static PublicPlanningInputs publicPlanningInputs(DriverStateAssembler.ReadOnlyPlanningScope scope,Complete frame,Known current,
            Optional<DriverPersistentPlanningState.Publication> persistent,Optional<Obj> actualToken,ExactRef originalDomainState,
            org.xar.ck3.control.nativebridge.capabilities.army.ArmyWindowAttempts.Snapshot attempts,Optional<PublicTerminalInputs> terminalInputs,
            ActionPorts.OutcomeArchive archive)throws java.io.IOException {
        Objects.requireNonNull(scope).requireInputs(frame,current);
        Obj auxiliary=currentFrameAuxiliary(current,persistent,actualToken,originalDomainState,attempts,archive);
        if(terminalInputs.isPresent()){
            terminalInputs.orElseThrow().requireScope(frame.originalProjection().orElseThrow(),current);
            auxiliary=auxiliary.with(PUBLIC_TERMINAL,reference(terminalInputs.orElseThrow().original()));
        }else require(frame.identity().observationVersion()!=DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION,
                "native_campaign raw inputs need the actual private constructor source");
        InitialAuxiliary prepared=mint(frame,current,auxiliary,version(current.auxiliary()),Cause.PUBLIC_PLANNING_VIEW,archive);
        var result=new PublicPlanningInputs(scope,frame,current,prepared,terminalInputs,archive);result.requireScope(frame,current);return result;
    }
    private static Obj currentFrameAuxiliary(Known current,Optional<DriverPersistentPlanningState.Publication> persistent,
            Optional<Obj> actualToken,ExactRef originalDomainState,
            org.xar.ck3.control.nativebridge.capabilities.army.ArmyWindowAttempts.Snapshot attempts,ActionPorts.OutcomeArchive archive) {
        Obj auxiliary=new Obj(initialized(current));
        if(persistent.isPresent()) {
            var publication=persistent.orElseThrow();
            require(publication.expectedStamp().equals(current.stamp())&&publication.expectedAuxiliarySha256().equals(DriverJson.sha256(DriverJson.encode(current.auxiliary()))),
                    "persistent frame publication crossed its actual Driver CAS");
            DriverPersistentPlanningState.replay(publication.auxiliary(),archive);auxiliary=publication.auxiliary();
        }
        Obj domain=DriverJson.object(readMaterial(archive,originalDomainState).bytes(),DriverJson.MAX_NATIVE_BYTES);
        require(ArmyRetreatTokens.capabilityToken(ActiveRetreatState.decode(domain)).equals(actualToken),"retreat frame token differs from its sole domain producer");
        auxiliary=auxiliary.with("active_combat_retreat_token",nullable(actualToken)).with("capability_retreat_source",reference(originalDomainState));
        auxiliary=DriverSemanticReadState.withWindowAttempts(auxiliary,attempts,archive);
        return auxiliary;
    }
    /** Native army owns token creation and consumption. This method copies only its genuine archived domain projection. */
    public static InitialAuxiliary observeRetreat(Complete frame,Known current,Optional<Obj> actualToken,
            ExactRef originalDomainState,ActionPorts.OutcomeArchive archive) {
        return observeRetreatPrepared(frame,current,actualToken,originalDomainState,new Obj(initialized(current)),archive);
    }
    public static InitialAuxiliary observeRetreat(Complete frame,Known current,Optional<Obj> actualToken,
            ExactRef originalDomainState,ActionPorts.OutcomeArchive archive,org.xar.ck3.control.nativebridge.capabilities.army.ArmyWindowAttempts.Snapshot actualAttempts) {
        return observeRetreatPrepared(frame,current,actualToken,originalDomainState,
                DriverSemanticReadState.withWindowAttempts(new Obj(initialized(current)),actualAttempts,archive),archive);
    }
    private static InitialAuxiliary observeRetreatPrepared(Complete frame,Known current,Optional<Obj> actualToken,
            ExactRef originalDomainState,Obj actualAuxiliary,ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(actualToken);Obj domain=DriverJson.object(readMaterial(archive,originalDomainState).bytes(),DriverJson.MAX_NATIVE_BYTES);
        Optional<Obj> original=ArmyRetreatTokens.capabilityToken(ActiveRetreatState.decode(domain));
        require(original.equals(actualToken),"retreat capability token must be projected by the original native army domain state");
        // A stale actual domain token remains factual data. The shared Dynamic selector alone decides current action eligibility.
        Map<String,Value> aux=new LinkedHashMap<>(actualAuxiliary.members());aux.put("active_combat_retreat_token",nullable(actualToken));
        aux.put("capability_retreat_source",reference(originalDomainState));
        return mint(frame,current,new Obj(aux),nextVersion(current),Cause.RETREAT_DOMAIN,archive);
    }
    public static InitialAuxiliary observeSeed(Complete frame,Known current,SeedAdoption.Available actual,
            CheckpointFiles actualFiles,ActionPorts.OutcomeArchive archive) throws IOException {
        SeedArtifact seed=Objects.requireNonNull(actual).artifact();seed.requireCurrent(actualFiles);
        Map<String,Value> metadata=new LinkedHashMap<>();metadata.put("name",new Text(SeedArtifact.NAME));
        metadata.put("size",new IntegerValue(BigInteger.valueOf(seed.save().reference().bytes())));metadata.put("sha256",new Text(seed.save().reference().sha256()));
        metadata.put("date_raw",new IntegerValue(seed.dateRaw()));metadata.put("character_id",new IntegerValue(seed.characterId()));
        metadata.put("source_run_id",new Text(seed.sourceRunId()));
        Map<String,Value> aux=initialized(current);aux.put("episode_seed",new Obj(metadata));
        byte[] originalMetadata=actualFiles.read(seed.metadata(),65536);
        aux.put("capability_seed_source",reference(archive.preserveMaterial(new RawJson(originalMetadata))));
        return mint(frame,current,new Obj(aux),nextVersion(current),Cause.IMMUTABLE_SEED,archive);
    }
    /** The canonical attempt has already occurred; invalidate on reject/unknown as well as confirmed marriage. */
    public static InitialAuxiliary observeMarriageAttempt(Complete frame,Known current,ActionReceipt actual,ActionPorts.OutcomeArchive archive) {
        require(actual.command().origin() instanceof CommandOrigin.Gameplay&&actual.command().operation().value().matches("arrange-marriage-[0-9]+-[0-9]+")
                &&ActionTransitions.attempt(actual.state()).isPresent(),"actual original marriage attempt required");
        var submitted=actual.command().origin().requireGameplay();
        require(submitted.game().equals(current.stamp().game())&&submitted.frame().episodeRunId().equals(current.stamp().episodeRunId())
                &&submitted.frame().identity().player().equals(current.driver().session().actorId()),"marriage attempt crossed actual Driver episode");
        ExactRef source=archive.preserveReceipt(actual);require(actual.equals(archive.loadReceipt(source)),"original actual marriage attempt receipt differs");
        Map<String,Value> aux=initialized(current);aux.put("arrange_marriage_choices",new Arr(List.of()));aux.put("arrange_marriage_query_sequence",Nil.INSTANCE);
        Map<String,Value> reads=new LinkedHashMap<>(object(aux.get(READS),READS).members());reads.put("marriage",Nil.INSTANCE);aux.put(READS,new Obj(reads));
        aux.put("capability_marriage_attempt_source",reference(source));return mint(frame,current,new Obj(aux),nextVersion(current),Cause.MARRIAGE_ATTEMPT,archive);
    }
    /** A same-frame independently archived proof, never the readiness of a historical software declaration. */
    public static InitialAuxiliary observeIndependentReadiness(Complete frame,Known current,ExactRef actualProof,ActionPorts.OutcomeArchive archive) {
        Obj proof=DriverJson.object(readMaterial(archive,actualProof).bytes(),DriverJson.MAX_NATIVE_BYTES);
        require(bool(proof.get("ready"),"ready"),"actual independent proof is not ready");Obj binding=object(proof.get("source_binding"),"source_binding");
        for(String key:List.of("snapshot_id","revision","native_revision","date_raw","episode_run_id"))require(Objects.equals(binding.get(key),frame.semantic().get(key)),"independent proof frame differs: "+key);
        require(integer(binding.get("connection_generation"),"connection_generation").equals(frame.connectionGeneration()),"independent proof connection differs");
        Map<String,Value> aux=initialized(current);aux.put("independent_battle_speed_readiness",proof);aux.put("capability_independent_source",reference(actualProof));
        return mint(frame,current,new Obj(aux),nextVersion(current),Cause.INDEPENDENT_READINESS,archive);
    }

    /** Reframe the actual current private state. A repeated unchanged call reuses the exact existing material. */
    public static Optional<InitialAuxiliary> refresh(Complete frame,Known current,ActionPorts.OutcomeArchive archive) {
        return refreshPrepared(frame,current,new Obj(initialized(current)),archive);
    }
    public static Optional<InitialAuxiliary> refresh(Complete frame,Known current,ActionPorts.OutcomeArchive archive,
            org.xar.ck3.control.nativebridge.capabilities.army.ArmyWindowAttempts.Snapshot actualAttempts) {
        return refreshPrepared(frame,current,DriverSemanticReadState.withWindowAttempts(new Obj(initialized(current)),actualAttempts,archive),archive);
    }
    private static Optional<InitialAuxiliary> refreshPrepared(Complete frame,Known current,Obj actualAuxiliary,ActionPorts.OutcomeArchive archive) {
        Map<String,Value> aux=new LinkedHashMap<>(DriverSemanticReadState.invalidate(frame,actualAuxiliary,archive).members());BigInteger version=version(current.auxiliary());
        RawJson candidate=DriverRuntimeCapabilities.encode(frame,current,version,fields(new Obj(aux)));
        Value old=current.auxiliary().get(DriverRuntimeCapabilities.AUXILIARY_KEY);
        if(old instanceof Obj ref && Arrays.equals(candidate.bytes(),readMaterial(archive,decodeReference(ref)).bytes())) {
            Obj retained=DriverJson.object(readMaterial(archive,decodeReference(object(current.auxiliary().get(STATE_SOURCE),STATE_SOURCE))).bytes(),DriverJson.MAX_NATIVE_BYTES);
            if(new Text(STATE_SCHEMA).equals(retained.get("schema"))&&ownerAuxiliary(new Obj(aux)).equals(retained.get("owner_auxiliary")))return Optional.empty();
        }
        return Optional.of(mint(frame,current,new Obj(aux),version.add(BigInteger.ONE),Cause.OBSERVED_FRAME,archive));
    }

    /** Replay reads the original full state and its original input capsule, including explicit nulls and actual query receipts. */
    public static Obj replay(Complete originalFrame,Known originalDriver,ExactRef originalState,ActionPorts.OutcomeArchive archive) {
        Obj state=DriverJson.object(readMaterial(archive,originalState).bytes(),DriverJson.MAX_NATIVE_BYTES);
        require(state.members().keySet().equals(Set.of("schema","cause","state_version","inputs","cache_values","owner_auxiliary","semantic_source"))
                && text(state.get("schema"),"schema").equals(STATE_SCHEMA),"complete original capability state schema required");
        Cause cause=Cause.valueOf(text(state.get("cause"),"cause"));
        Obj cache=object(state.get("cache_values"),"cache_values");require(cache.members().keySet().containsAll(CACHE_KEYS),"incomplete original cache state");
        Obj owner=object(state.get("owner_auxiliary"),"owner_auxiliary");require(ownerAuxiliary(owner).equals(owner),"saved owner auxiliary includes circular capability refs/version");
        for(var field:cache.members().entrySet())require(Objects.equals(owner.get(field.getKey()),field.getValue()),"saved cache differs from full original private owner auxiliary: "+field.getKey());
        BigInteger version=decimal(state.get("state_version"),"state_version");ExactRef inputs=decodeReference(object(state.get("inputs"),"inputs"));
        RawJson raw=readMaterial(archive,inputs);DynamicCapabilities.DriverInputs decoded=DynamicCapabilities.DriverInputs.decode(originalFrame,originalDriver,inputs,raw.bytes());
        require(version.equals(decoded.stateVersion()) && DriverJson.object(raw.bytes(),DriverJson.MAX_NATIVE_BYTES).equals(
                DriverJson.object(DriverRuntimeCapabilities.encode(originalFrame,originalDriver,version,fields(cache)).bytes(),DriverJson.MAX_NATIVE_BYTES)),
                "cached values differ from original complete runtime capsule");
        readMaterial(archive,decodeReference(object(cache.get(INITIAL),INITIAL)));
        ExactRef semantic=decodeReference(object(state.get("semantic_source"),"semantic_source"));RawJson manifest=readMaterial(archive,semantic);
        var nativeFrame=DriverObservationEvidenceReader.nativeFrame(semantic,manifest,archive.loadNativeFrame(originalFrame.originalEvidence()));
        var originalFacts=DriverObservationEvidenceReader.decode(semantic,manifest,new RawJson(originalDriver.driver().encode()),nativeFrame);
        require(originalFacts.driverVersion()==originalDriver.stamp().driverVersion()
                && originalFacts.episodeEpoch()==originalDriver.stamp().episodeEpoch()
                && originalFacts.snapshotId().equals(originalFrame.identity().frame().snapshotId())
                && originalFacts.publicRevision().equals(originalFrame.identity().frame().revision()),"original cache source semantic manifest crossed the saved Driver/native frame");
        Obj sources=object(cache.get(READS),READS);require(sources.members().keySet().equals(Set.of("marriage","campaign_root")),"complete query receipt source table required");
        if(sources.get("marriage")!=Nil.INSTANCE) {
            PlanningReadReceipt receipt=archive.loadRead(decodeReference(object(sources.get("marriage"),"marriage")));
            require(marriage(result(receipt),receipt).equals(cache.get("arrange_marriage_choices")),"original marriage cache differs from actual read producer");
        }
        if(sources.get("campaign_root")!=Nil.INSTANCE) {
            PlanningReadReceipt receipt=archive.loadRead(decodeReference(object(sources.get("campaign_root"),"campaign_root")));
            require(campaignRoot(result(receipt),receipt).equals(cache.get("campaign_root_context_query")),"original campaign-root cache differs from actual read producer");
        }
        if(cache.members().containsKey("capability_retreat_source")) {
            Obj domain=DriverJson.object(readMaterial(archive,decodeReference(object(cache.get("capability_retreat_source"),"capability_retreat_source"))).bytes(),DriverJson.MAX_NATIVE_BYTES);
            require(ArmyRetreatTokens.capabilityToken(ActiveRetreatState.decode(domain)).equals(optional(cache,"active_combat_retreat_token")),"replayed token differs from original sole retreat domain");
        }
        require(decodeReference(object(cache.get(NATIVE),NATIVE)).equals(originalFrame.originalEvidence()),"capability cache original observed packet source differs");
        if(cache.members().containsKey("capability_marriage_attempt_source")) {
            ActionReceipt attempt=archive.loadReceipt(decodeReference(object(cache.get("capability_marriage_attempt_source"),"capability_marriage_attempt_source")));
            require(attempt.command().operation().value().matches("arrange-marriage-[0-9]+-[0-9]+")&&ActionTransitions.attempt(attempt.state()).isPresent(),"original marriage invalidation source is not an actual attempt");
        }
        replayImmutableSeedSource(cache,archive);
        if(cache.get("independent_battle_speed_readiness")!=Nil.INSTANCE)require(DriverJson.object(readMaterial(archive,decodeReference(object(cache.get("capability_independent_source"),"capability_independent_source"))).bytes(),DriverJson.MAX_NATIVE_BYTES).equals(cache.get("independent_battle_speed_readiness")),"replayed independent proof differs from actual archived original");
        replaySuccessionSource(cache,archive);DriverSemanticReadState.replaySources(owner,archive);DriverPersistentPlanningState.replay(owner,archive);
        if(owner.members().containsKey(PUBLIC_TERMINAL)){
            require(cause==Cause.PUBLIC_PLANNING_VIEW,"private terminal input role cannot enter ordinary persisted capability state");
            PublicTerminalWire terminal=decodePublicTerminalWire(readMaterial(archive,decodeReference(object(owner.get(PUBLIC_TERMINAL),PUBLIC_TERMINAL))).bytes());
            require(terminal.frameSha256().equals(originalFrame.fullBindingSha256())&&terminal.nativePacket().equals(originalFrame.originalEvidence())
                    &&terminal.semanticSource().equals(semantic)&&terminal.stateVersion().equals(version)
                    &&Arrays.equals(readMaterial(archive,terminal.fullDriver()).bytes(),originalDriver.driver().encode()),
                    "private terminal capability role crossed its actual raw Native/full Driver source");
        }
        Map<String,Value> output=new LinkedHashMap<>(owner.members());
        output.put(VERSION,new Text(version.toString()));output.put(STATE_SOURCE,reference(originalState));
        output.put(DriverRuntimeCapabilities.AUXILIARY_KEY,reference(inputs));return new Obj(output);
    }
    private static void replayImmutableSeedSource(Obj cache,ActionPorts.OutcomeArchive archive){
        if(cache.get("episode_seed")!=Nil.INSTANCE) {
            Obj metadata=DriverJson.object(readMaterial(archive,decodeReference(object(cache.get("capability_seed_source"),"capability_seed_source"))).bytes(),65536);
            require(metadata.members().keySet().equals(Set.of("format_version","name","path","size","sha256","date_raw","character_id","source_run_id","source_checkpoint_name","immutable"))
                    &&integer(metadata.get("format_version"),"format_version").equals(BigInteger.ONE)&&bool(metadata.get("immutable"),"immutable")
                    &&text(metadata.get("source_checkpoint_name"),"source_checkpoint_name").equals("xar_checkpoint.ck3")
                    &&java.nio.file.Path.of(text(metadata.get("path"),"path")).getFileName().toString().equals(SeedArtifact.NAME),"original immutable seed metadata invalid");
            Obj seed=object(cache.get("episode_seed"),"episode_seed");for(String key:List.of("name","size","sha256","date_raw","character_id","source_run_id"))require(Objects.equals(seed.get(key),metadata.get(key)),"replayed seed cache differs from actual immutable metadata: "+key);
        }
    }

    /** Replays the sole M3 comparison from the archived preclock and final Root originals; grants no live source authority. */
    public static void replaySuccessionSource(Obj auxiliary,ActionPorts.OutcomeArchive archive) {
        if(!auxiliary.members().containsKey("capability_succession_source")) {
            require(auxiliary.get("succession_reconciliation")==Nil.INSTANCE,"non-null succession comparison lacks its actual originals");return;
        }
        Obj proof=DriverJson.object(readMaterial(archive,decodeReference(object(auxiliary.get("capability_succession_source"),"capability_succession_source"))).bytes(),DriverJson.MAX_NATIVE_BYTES);
        var requiredKeys=new java.util.HashSet<>(proof.members().keySet());requiredKeys.remove("preclock_source");requiredKeys.remove("final_source");
        require(requiredKeys.equals(Set.of("schema","preclock_capture","preclock_root_read","preclock_root_result","preclock_semantic","preclock_driver","preclock_native",
                "final_root_read","final_root_result","final_semantic","final_driver","final_native","reconciliation"))
                &&text(proof.get("schema"),"schema").equals("xar.driver-succession-estate-source/v1"),"complete original estate comparison source required");
        readMaterial(archive,decodeReference(object(proof.get("preclock_capture"),"preclock_capture")));
        for(String field:List.of("preclock_source","final_source"))if(proof.members().containsKey(field))ExactRef.optionalFromJson(DriverJson.toNode(proof.get(field)));
        var before=archive.loadRead(decodeReference(object(proof.get("preclock_root_read"),"preclock_root_read")));
        var after=archive.loadRead(decodeReference(object(proof.get("final_root_read"),"final_root_read")));
        require(before.request().origin() instanceof CommandOrigin.Gameplay&&after.request().origin() instanceof CommandOrigin.LifecycleTerminal
                &&before.request().operation().value().equals("query-campaign-root-context-v1")&&after.request().operation().value().equals("query-campaign-root-context-v1")
                &&before.request().source().equals(after.request().source())&&before.request().sessionId().equals(after.request().sessionId()),"estate original query custody differs");
        var terminal=after.request().origin().requireLifecycleTerminal();var origin=before.request().origin().requireGameplay();
        require(terminal.game().equals(origin.game())&&terminal.subject().episodeRunId().equals(origin.frame().episodeRunId())
                &&terminal.subject().characterId().equals(origin.frame().identity().player())&&terminal.terminalReason()==org.xar.ck3.control.application.action.LifecycleIdentity.TerminalReason.CHANGED
                &&terminal.currentPlayer() instanceof org.xar.ck3.control.application.action.LifecycleIdentity.Character player&&player.alive(),"estate old subject/current successor mismatch");
        RawJson initial=readMaterial(archive,decodeReference(object(proof.get("preclock_root_result"),"preclock_root_result")));
        RawJson current=readMaterial(archive,decodeReference(object(proof.get("final_root_result"),"final_root_result")));
        require(initial.equals(before.original().originalResultToken().orElseThrow())&&current.equals(after.original().originalResultToken().orElseThrow()),"estate raw result differs from actual original query");
        for(String phase:List.of("preclock","final")) {
            var driver=org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.decodeComplete(readMaterial(archive,decodeReference(object(proof.get(phase+"_driver"),phase+"_driver"))).bytes());
            require(driver.session().bridgePid()==terminal.game().pid()&&driver.session().episodeRunId().equals(terminal.subject().episodeRunId())
                    &&driver.session().actorId().equals(terminal.subject().characterId()),"estate full Driver original crossed old episode");
            ExactRef packet=decodeReference(object(proof.get(phase+"_native"),phase+"_native"));byte[] framed=archive.loadNativeFrame(packet);
            require(framed.length==packet.bytes()&&DriverJson.sha256(framed).equals(packet.sha256()),"estate original native packet differs");
        }
        var frozen=org.xar.ck3.control.wave2.governance.succession.SuccessionNativeEstate12004.freeze(initial.bytes(),readMaterial(archive,decodeReference(object(proof.get("preclock_semantic"),"preclock_semantic"))).bytes());
        var compared=org.xar.ck3.control.wave2.governance.succession.SuccessionNativeEstate12004.reconcile(frozen,current.bytes(),readMaterial(archive,decodeReference(object(proof.get("final_semantic"),"final_semantic"))).bytes());
        Obj wire=DriverJson.object(compared.wire(),DriverJson.MAX_NATIVE_BYTES);
        require(wire.equals(proof.get("reconciliation"))&&wire.equals(auxiliary.get("succession_reconciliation")),"estate comparison differs from original M3 replay");
    }
    private static InitialAuxiliary mint(Complete frame,Known before,Obj privateState,BigInteger version,Cause cause,ActionPorts.OutcomeArchive archive) {
        byte[] nativePacket=archive.loadNativeFrame(frame.originalEvidence());require(nativePacket.length==frame.originalEvidence().bytes()
                &&DriverJson.sha256(nativePacket).equals(frame.originalEvidence().sha256()),"actual capability frame original packet absent/different");
        privateState=DriverSemanticReadState.invalidate(frame,privateState,archive).with(NATIVE,reference(frame.originalEvidence()));
        RawJson wire=DriverRuntimeCapabilities.encode(frame,before,version,fields(privateState));ExactRef inputs=archive.preserveMaterial(wire);
        require(inputs.equals(archive.materialReferenceOf(wire)),"complete capability capsule archive differs");
        Map<String,Value> cache=new LinkedHashMap<>();
        for(String key:CACHE_KEYS){require(privateState.members().containsKey(key),"missing actual runtime cache field: "+key);cache.put(key,privateState.get(key));}
        for(String key:List.of("capability_retreat_source","capability_seed_source","capability_independent_source","capability_marriage_attempt_source","capability_succession_source"))
            if(privateState.members().containsKey(key))cache.put(key,privateState.get(key));
        ExactRef semantic=before.observation().orElseThrow(() -> new IllegalArgumentException("actual held native/Driver observation required")).semanticFactsEvidence();
        Map<String,Value> source=new LinkedHashMap<>();source.put("schema",new Text(STATE_SCHEMA));source.put("cause",new Text(cause.name()));
        source.put("state_version",new Text(version.toString()));source.put("inputs",reference(inputs));source.put("cache_values",new Obj(cache));source.put("owner_auxiliary",ownerAuxiliary(privateState));source.put("semantic_source",reference(semantic));
        RawJson original=new RawJson(DriverJson.encode(new Obj(source)));ExactRef state=archive.preserveMaterial(original);
        Map<String,Value> result=new LinkedHashMap<>(privateState.members());result.put(VERSION,new Text(version.toString()));
        result.put(STATE_SOURCE,reference(state));result.put(DriverRuntimeCapabilities.AUXILIARY_KEY,reference(inputs));
        return new InitialAuxiliary(before,new Obj(result),state);
    }
    private static Obj ownerAuxiliary(Obj actual) {
        Map<String,Value> fields=new LinkedHashMap<>(actual.members());fields.remove(VERSION);fields.remove(STATE_SOURCE);fields.remove(DriverRuntimeCapabilities.AUXILIARY_KEY);return new Obj(fields);
    }
    private static DriverRuntimeCapabilities.Fields fields(Obj state) {
        require(state.members().keySet().containsAll(CACHE_KEYS),"actual full runtime caches unavailable; no empty defaults");
        List<Obj> choices=new ArrayList<>();for(Value choice:array(state.get("arrange_marriage_choices"),"arrange_marriage_choices"))choices.add(object(choice,"choice"));
        DynamicCapabilities.Configuration config=DynamicCapabilities.decodeConfiguration(object(state.get(CONFIG),CONFIG));
        return new DriverRuntimeCapabilities.Fields(choices,optional(state,"campaign_root_context_query"),optional(state,"active_combat_retreat_token"),
                optional(state,"episode_seed"),optional(state,"episode_transition"),optional(state,"succession_reconciliation"),config,
                optional(state,"independent_battle_speed_readiness"),sessionPresentation(state));
    }
    private static Map<String,Value> initialized(Known before) {
        require(before.auxiliary().members().keySet().containsAll(CACHE_KEYS) && before.auxiliary().members().containsKey(STATE_SOURCE),"actual runtime cache initializer/replay unavailable");
        return new LinkedHashMap<>(before.auxiliary().members());
    }
    /** Canonical shared native marriage row normalization; extra raw row material stays only in the original receipt. */
    public static List<Obj> normalizeMarriageChoices(Value original) {
        List<Obj> rows=new ArrayList<>();Set<String> seen=new java.util.HashSet<>();
        for(Value value:array(original,"arrange_marriage_choices")) {
            Obj row=object(value,"marriage_choice");BigInteger played=nonnegative(row.get("played_character_id"),"played_character_id");
            BigInteger candidate=nonnegative(row.get("candidate_character_id"),"candidate_character_id");String canonical=played+"-"+candidate;
            require(!played.equals(candidate)&&canonical.equals(text(row.get("choice_id"),"choice_id"))&&seen.add(canonical),"canonical distinct native marriage choice required");
            rows.add(new Obj(Map.of("choice_id",new Text(canonical),"played_character_id",new IntegerValue(played),"candidate_character_id",new IntegerValue(candidate),"source",new Text("native"))));
        }
        require(rows.size()<=65536,"bounded complete marriage choices required");return List.copyOf(rows);
    }
    private static Arr marriage(Obj result,PlanningReadReceipt receipt) {
        require(text(result.get("step"),"step").equals("query-arrange-marriage-choices") && bool(result.get("accepted"),"accepted"),"actual marriage read result required");
        require(integer(result.get("query_sequence"),"query_sequence").signum()>0,"actual marriage query sequence required");
        BigInteger actor=receipt.request().origin().requireGameplay().frame().identity().player();List<Obj> rows=normalizeMarriageChoices(result.get("arrange_marriage_choices"));
        for(Obj row:rows)require(integer(row.get("played_character_id"),"played_character_id").equals(actor),"actual marriage query belongs to another player");
        return new Arr(rows.stream().map(row -> (Value)row).toList());
    }
    /** Pure projection of this exact successful original query, shared by every root-cache consumer. */
    public static Obj campaignRootFromOriginal(PlanningReadReceipt actual) {
        require(actual.request().operation().value().equals("query-campaign-root-context-v1")&&actual.original().nativeOk()
                &&actual.request().origin() instanceof CommandOrigin.Gameplay,"actual original ordinary root query required");
        return campaignRoot(result(actual),actual);
    }
    private static Obj campaignRoot(Obj result,PlanningReadReceipt receipt) {
        var actualFrame=receipt.request().origin().requireGameplay().frame();
        result=CampaignRootContextJson.normalizeNativeResult(result,actualFrame.identity().dateRaw(),actualFrame.identity().nativeRevision());
        Obj normalizedRoot=object(result.get("campaign_root_context"),"campaign_root_context");
        if(text(normalizedRoot.get("status"),"status").equals("available"))require(integer(normalizedRoot.get("player_character_id"),"player_character_id").equals(actualFrame.identity().player()),"actual campaign-root cache belongs to another player");
        BigInteger sequence=integer(result.get("query_sequence"),"query_sequence");require(sequence.signum()>0,"actual campaign-root query sequence required");
        var id=receipt.request().origin().requireGameplay();var f=id.frame();Map<String,Value> binding=new LinkedHashMap<>();
        binding.put("snapshot_id",new Text(f.snapshotId()));binding.put("revision",new IntegerValue(f.revision()));binding.put("native_revision",new IntegerValue(f.identity().nativeRevision()));
        binding.put("date_raw",new IntegerValue(f.identity().dateRaw()));binding.put("actor_character_id",new IntegerValue(f.identity().player()));
        binding.put("bridge_pid",new IntegerValue(BigInteger.valueOf(id.game().pid())));binding.put("connection_generation",new IntegerValue(receipt.before().binding().connectionGeneration()));
        Map<String,Value> cached=new LinkedHashMap<>();cached.put("query_sequence",new IntegerValue(sequence));
        cached.put("campaign_root_context",object(result.get("campaign_root_context"),"campaign_root_context"));cached.put("cache_binding",new Obj(binding));
        if(object(result.get("campaign_root_context"),"campaign_root_context").members().containsKey("player_heir_candidate_v1")) {
            // This runtime has no admitted loaded-provider/fixed-original-anchor producer. Preserve an explicit unknown via the sole M3 mapper.
            cached.put("player_heir_fixed_dynasty_projection_v1",DriverJson.object(
                    org.xar.ck3.control.wave2.governance.succession.FixedDynastyHeirProjection12004.encodeUnqualified(null,
                            "original_fixed_campaign_anchor_or_loaded_native_provider_unavailable"),DriverJson.MAX_NATIVE_BYTES));
        }
        return new Obj(cached);
    }
    private static void requireRead(Complete frame,PlanningReadReceipt receipt) {
        require(receipt.original().nativeOk() && receipt.request().origin() instanceof CommandOrigin.Gameplay,
                "only a successful original gameplay planning read may publish cache facts");
        require(receipt.request().origin().requireGameplay().equals(frame.identity()) && receipt.request().source().equals(frame.source())
                && receipt.request().sessionId().equals(frame.sessionId()) && receipt.before().binding().origin().equals(receipt.after().binding().origin()),
                "actual cache read crossed current held native frame/source/session");
    }
    private static Obj result(PlanningReadReceipt receipt) { return DriverJson.object(receipt.original().originalResultToken().orElseThrow().bytes(),DriverJson.MAX_NATIVE_BYTES); }
    private static RawJson readMaterial(ActionPorts.OutcomeArchive archive,ExactRef source) {
        RawJson raw=archive.loadMaterial(source);require(source.bytes()==raw.bytes().length && source.sha256().equals(DriverJson.sha256(raw.bytes())),"actual capability source bytes/SHA differ");return raw;
    }
    private static Obj configuration(DynamicCapabilities.Configuration c) { return DynamicCapabilities.encodeConfiguration(c); }
    private static Obj paths(CapabilitySessionPresentation p) { return new Obj(Map.of("queue_dir",p.queueDirectory().<Value>map(v -> new Text(v.toString())).orElse(Nil.INSTANCE),"driver_state_path",p.driverStatePath().<Value>map(v -> new Text(v.toString())).orElse(Nil.INSTANCE))); }
    private static Optional<java.nio.file.Path> path(Obj row,String key) { return row.get(key)==Nil.INSTANCE?Optional.empty():Optional.of(java.nio.file.Path.of(text(row.get(key),key))); }
    private static Optional<Obj> optional(Obj row,String key) { return row.get(key)==Nil.INSTANCE?Optional.empty():Optional.of(object(row.get(key),key)); }
    private static Value nullable(Optional<Obj> value) { return value.<Value>map(v -> v).orElse(Nil.INSTANCE); }
    private static void putInitial(Map<String,Value> row,String key,Value value) { Value before=row.putIfAbsent(key,value);require(before==null || before.equals(value),"fresh initializer cannot overwrite existing actual state: "+key); }
    private static BigInteger version(Obj row) { return decimal(row.get(VERSION),VERSION); }
    private static BigInteger nextVersion(Known current) { return version(current.auxiliary()).add(BigInteger.ONE); }
    private static BigInteger decimal(Value raw,String field) { String value=text(raw,field);require(value.matches("0|[1-9][0-9]*"),"canonical exact state version required");return new BigInteger(value); }
    private static Obj reference(ExactRef ref) { return DriverRuntimeCapabilities.referenceJson(ref); }
    private static ExactRef decodeReference(Obj value) { require(value.members().keySet().equals(Set.of("path","bytes","sha256")),"complete source reference required");return new ExactRef(text(value.get("path"),"path"),integer(value.get("bytes"),"bytes").longValueExact(),text(value.get("sha256"),"sha256")); }
}
