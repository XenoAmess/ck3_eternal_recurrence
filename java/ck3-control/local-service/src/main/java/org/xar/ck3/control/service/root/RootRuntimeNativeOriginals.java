package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.NativeLaunchPlan;

/** Exact original provenance needed by the actual remaining Java factories.
 * Python originals are evidence only. C++/header originals must separately belong to the real retained native cut. */
public final class RootRuntimeNativeOriginals {
    public static final String SCHEMA="xar.java-root-native-originals/v7";
    public static final int MAXIMUM_BYTES=1<<20;
    public static final int MAXIMUM_SOURCE_BYTES=64<<20;
    private RootRuntimeNativeOriginals(){ }
    public enum Role {
        HOLY_PRODUCER("src/xar_autoplayer/bridge/player_holy_order_context_private_transport.py"),
        HOLY_COST_NORMALIZER("src/xar_autoplayer/bridge/player_holy_order_hire_cost_context.py"),
        HOLY_REINFORCEMENT_NORMALIZER("src/xar_autoplayer/bridge/holy_order_current_reinforcement_v1.py"),
        HOLY_MAILBOX("native_bridge/src/ck3_12003_player_holy_order_mailbox.cpp"),
        HOLY_WIRE("native_bridge/src/ck3_12003_player_holy_order_wire.cpp"),
        HOLY_CONTEXT("native_bridge/src/ck3_12003_player_holy_order_context.cpp"),
        HOLY_REINFORCEMENT("native_bridge/src/ck3_12003_holy_order_current_reinforcement.cpp"),
        HOLY_BUILD4_BINDING("native_bridge/src/ck3_12004_holy_order_bindings.cpp"),
        RELIGION_PRODUCER("src/xar_autoplayer/bridge/player_religion_context_private_transport.py"),
        RELIGION_MAILBOX("native_bridge/src/ck3_12002_religion_mailbox.cpp"),
        RELIGION_CONTEXT("native_bridge/src/ck3_12002_religion_context.cpp"),
        CLAIM_PRODUCER("src/xar_autoplayer/bridge/ordinary_interaction_contract.py"),
        CLAIM_HOST_RELEASE("src/xar_autoplayer/bridge/ordinary_interaction_host_release.py"),
        REGULAR_MAA_PRODUCER("src/xar_autoplayer/bridge/regular_maa_create_private_action_v1.py"),
        REGULAR_MAA_MAILBOX("native_bridge/src/ck3_12003_maa_create_private_mailbox.cpp"),
        REGULAR_MAA_CREATE("native_bridge/src/ck3_12003_maa_create.cpp"),
        REGULAR_MAA_BUILD4_BINDING("native_bridge/src/ck3_12004_military.cpp"),
        RITE_CREATION_PUBLIC_PRODUCER("src/xar_autoplayer/bridge/rite_creation_action_mcp_v1.py"),
        RITE_CREATION_PRIVATE_PRODUCER("src/xar_autoplayer/bridge/rite_creation_action_private_v1.py"),
        RITE_CREATION_NATIVE_DOMAIN("native_bridge/src/rite_creation_actions12004.cpp"),
        RITE_CREATION_NATIVE_WIRE("native_bridge/src/rite_creation_actions12004_wire.cpp"),
        RITE_CREATION_NATIVE_MAILBOX("native_bridge/src/rite_creation_actions12004_mailbox.cpp"),
        RITE_CREATION_NATIVE_HEADER("native_bridge/include/xar_bridge/rite_creation_actions12004.hpp"),
        RITE_CREATION_NATIVE_WIRE_HEADER("native_bridge/include/xar_bridge/rite_creation_actions12004_wire.hpp"),
        RITE_CREATION_NATIVE_MAILBOX_HEADER("native_bridge/include/xar_bridge/rite_creation_actions12004_mailbox.hpp"),
        WAR_DECLARED_OVERVIEW_POLICY("src/xar_autoplayer/bridge/war_declared_overview_contract.py"),
        WAR_RECORDING_POLICY("src/xar_autoplayer/bridge/war_contract.py"),
        BATTLE_RECORDING_POLICY("src/xar_autoplayer/bridge/battle_control_contract.py"),
        CACHED_SUCCESSION_MAILBOX("native_bridge/src/actor_cached_succession12004_mailbox.cpp"),
        CACHED_SUCCESSION_CORE("native_bridge/src/actor_cached_succession12004_v1.cpp"),
        GOVERNMENT_BINDER("native_bridge/src/government_runtime_adapter_bridge_binder_v1.cpp"),
        NATIVE_DISPATCHER("native_bridge/src/bridge.cpp"),
        ARMY_SUPPLEMENTAL_WAR_NATIVE("native_bridge/src/ck3_11906.cpp"),
        H2743_PREACTION_TRUCE("native_bridge/src/h2743_preaction_existing_truce_v1.cpp"),
        WAR_BOUND_LOSS_CANDIDATE("native_bridge/src/raiktor_war_bound_loss_candidate_v1.cpp"),
        CLOCK_STATUS_DEFINITION("native_bridge/src/ck3_11906_adapter.cpp"),
        AUB_POLICY_OPTIONS("native_bridge/src/aub_policy_options_v1.cpp"),
        AUB_POLICY_MAILBOX("native_bridge/src/aub_policy_options_mailbox_v1.cpp"),
        AUB_BUSINESS("native_bridge/src/aub_business_state_v1.cpp"),
        AUB_INGAME_DECISION("native_bridge/src/ingame_decision_item_v1.cpp"),
        AUB_HOLY_SITE_DETAIL("native_bridge/src/ck3_12004_holy_site_adoption_detail_json.cpp"),
        AUB_POLICY_DELTA_TEST("native_bridge/tests/aub_policy_options_delta.cpp"),
        AUB_POLICY_HEADER("native_bridge/include/xar_bridge/aub_policy_options_v1.hpp"),
        AUB_POLICY_MAILBOX_HEADER("native_bridge/include/xar_bridge/aub_policy_options_mailbox_v1.hpp"),
        AUB_BUSINESS_HEADER("native_bridge/include/xar_bridge/aub_business_state_v1.hpp"),
        AUB_INGAME_DECISION_HEADER("native_bridge/include/xar_bridge/ingame_decision_item_v1.hpp"),
        LIFECYCLE_CAMPAIGN_ROOT("native_bridge/src/campaign_root_context_v1.cpp"),
        LIFECYCLE_ROOT_SERIALIZER("native_bridge/src/campaign_root_context_v1_serializer.cpp"),
        LIFECYCLE_ROOT_MAILBOX("native_bridge/src/campaign_root_context_v1_mailbox.cpp"),
        LIFECYCLE_TIMELINE("native_bridge/src/current_timeline_blocker_context_v1.cpp"),
        LIFECYCLE_TIMELINE_NATIVE("native_bridge/src/current_timeline_blocker_context_v1_native.cpp"),
        LIFECYCLE_TIMELINE_MAILBOX("native_bridge/src/current_timeline_blocker_context_v1_mailbox.cpp"),
        LIFECYCLE_CLOSE("native_bridge/src/death_succession_modal_continue_v1.cpp"),
        LIFECYCLE_CLOSE_MAILBOX("native_bridge/src/death_succession_modal_continue_v1_mailbox.cpp"),
        LIFECYCLE_SUCCESSION_MODAL("native_bridge/src/ck3_12004_succession_modal.cpp"),
        LIFECYCLE_PRISONER_RETAINED("native_bridge/src/ck3_12004_prisoner_retained_target_state.cpp"),
        LIFECYCLE_PRISONER_COLLECTION("native_bridge/src/player_prisoner_collection_query_v1_private.cpp");
        private final String repositoryRelative;
        Role(String relative){repositoryRelative="ck3_autonomous_player/"+relative;}
        public String repositoryRelative(){return repositoryRelative;}
        public RootRuntimeSelectedSources.OriginalKind kind(){
            if(repositoryRelative.endsWith(".py"))return RootRuntimeSelectedSources.OriginalKind.ORIGINAL_PYTHON;
            if(repositoryRelative.endsWith(".hpp"))return RootRuntimeSelectedSources.OriginalKind.NATIVE_HEADER;
            return RootRuntimeSelectedSources.OriginalKind.NATIVE_CPP;
        }
    }
    public record Original(Role role,String repositoryRelative,FileRef original) {
        public Original {
            Objects.requireNonNull(role);file(original);
            require(role.repositoryRelative().equals(repositoryRelative),"native/provenance role has another exact repository source target");
            require(Path.of(original.path()).getFileName().equals(Path.of(repositoryRelative).getFileName()),
                    "actual original source filename differs from its explicit role; a Java stand-in or renamed source is forbidden");
        }
        public ExactRef exact(){return new ExactRef(original.path(),original.bytes(),original.sha256());}
    }
    public record Configuration(String schema,String machineId,String observedAtUtc,String reviewAtUtc,List<Original> originals) {
        public Configuration {
            require(SCHEMA.equals(schema),"exact runtime native-originals version required");
            require(machineId!=null&&machineId.matches("[a-z0-9][a-z0-9-]{0,127}")&&!machineId.equals("unknown"),"actual native-original machine identity required");
            Instant observed=instant(observedAtUtc),review=instant(reviewAtUtc);
            require(observed.isBefore(review)&&Duration.between(observed,review).compareTo(Duration.ofDays(7))<=0,"finite reviewed native provenance required");
            originals=List.copyOf(originals);var roles=EnumSet.noneOf(Role.class);
            for(var source:originals)require(roles.add(source.role()),"duplicate native/provenance source role");
            require(roles.equals(EnumSet.allOf(Role.class)),"all actual native/header/Python provenance roles are mandatory");
        }
        public Original source(Role role){return originals.stream().filter(value->value.role()==Objects.requireNonNull(role)).findFirst().orElseThrow();}
    }
    public static byte[] encode(Configuration explicit)throws IOException {
        Objects.requireNonNull(explicit);return StrictJson.canonical(ControlBuild.strictMapper().valueToTree(explicit),MAXIMUM_BYTES);
    }
    public static Configuration decode(byte[] original)throws IOException {
        try{StrictJson.parse(original,MAXIMUM_BYTES);return ControlBuild.strictMapper().readValue(original,Configuration.class);}
        catch(IllegalArgumentException invalid){throw new IOException("invalid strict runtime native-originals wire",invalid);}
    }
    public static Bound readExact(FileRef original,Clock clock)throws IOException {
        Objects.requireNonNull(original);Objects.requireNonNull(clock);file(original);
        if(original.bytes()>MAXIMUM_BYTES||SharedSourceFiles.nativeFile(Path.of(original.path())).logicalBytes()!=original.bytes())
            throw new IOException("native provenance original exceeds or differs from its exact bounded data lane");
        var configWitness=SharedSourceFiles.observe(Path.of(original.path()));
        Configuration configuration=decode(RootRuntimeDefinitions.read(original,MAXIMUM_BYTES));
        current(configuration,clock);
        var refs=new LinkedHashMap<Path,FileRef>();refs.put(Path.of(original.path()),original);
        for(var source:configuration.originals()){
            FileRef previous=refs.putIfAbsent(Path.of(source.original().path()),source.original());
            if(previous!=null&&!same(previous,source.original()))throw new IOException("one native/provenance path has conflicting actual source refs");
        }
        var witnesses=new ArrayList<SharedSourceFiles.Witness>();
        for(var entry:refs.entrySet()){
            var nativeBefore=SharedSourceFiles.nativeFile(entry.getKey());
            if(nativeBefore.logicalBytes()!=entry.getValue().bytes())throw new IOException("native original differs from its bounded configured length");
            var actual=entry.getKey().equals(Path.of(original.path()))?configWitness:SharedSourceFiles.observe(entry.getKey());
            if(!same(actual.source(),entry.getValue())||!nativeBefore.equals(actual.nativeFile()))
                throw new IOException("actual native/provenance original differs from its exact configured body or identity");
            witnesses.add(actual);
        }
        Bound result=new Bound(original,configuration,witnesses);result.requireCurrent(clock);return result;
    }
    public static final class Bound {
        private final FileRef original;private final Configuration configuration;private final List<SharedSourceFiles.Witness> witnesses;
        private Bound(FileRef original,Configuration configuration,List<SharedSourceFiles.Witness> witnesses){
            this.original=original;this.configuration=configuration;this.witnesses=List.copyOf(witnesses);}
        public FileRef original(){return original;}
        public Configuration configuration(){return configuration;}
        public ExactRef source(Role role){return configuration.source(role).exact();}
        public void requireCurrent(Clock clock)throws IOException {
            Objects.requireNonNull(clock);
            current(configuration,clock);
            for(var witness:witnesses){
                if(!SharedSourceFiles.nativeFile(Path.of(witness.source().path())).equals(witness.nativeFile()))
                    throw new IOException("native/provenance source original identity or bounded length drifted");
                SharedSourceFiles.assertUnchanged(witness);
            }
        }
        /** Native sources require membership of this real frozen cut; this grants source custody only, never Game readiness. */
        public void requireQualifiedCut(NativeLaunchPlan sameActualPlan)throws IOException {
            Objects.requireNonNull(sameActualPlan);sameActualPlan.sources().verify();
            List<FileRef> actualCut=sameActualPlan.sources().nativeProof().expected().completeSources();
            for(var source:configuration.originals())if(source.role().kind()!=RootRuntimeSelectedSources.OriginalKind.ORIGINAL_PYTHON){
                boolean found=false;
                for(FileRef candidate:actualCut)if(same(candidate,source.original())
                        &&Path.of(candidate.path()).toRealPath().equals(Path.of(source.original().path()).toRealPath())){found=true;break;}
                if(!found)throw new IOException("native/header original is outside this actual qualified cut: "+source.role());
            }
        }
        public List<FileRef> retainedOriginals(){return witnesses.stream().map(SharedSourceFiles.Witness::source).toList();}
    }
    private static void file(FileRef value){Objects.requireNonNull(value);Path path=Path.of(value.path());
        require(path.isAbsolute()&&path.normalize().equals(path)&&value.bytes()>0&&value.bytes()<=MAXIMUM_SOURCE_BYTES
                &&value.sha256()!=null&&value.sha256().matches("[0-9a-fA-F]{64}"),"bounded actual native/provenance FileRef required");}
    private static void current(Configuration configuration,Clock clock)throws IOException {
        if(!configuration.machineId().equals(WindowsJobProcess.currentMachineId())||clock.instant().isBefore(instant(configuration.observedAtUtc()))
                ||!clock.instant().isBefore(instant(configuration.reviewAtUtc())))throw new IOException("actual native originals are foreign, future-dated or expired");
    }
    private static Instant instant(String value){StrictJson.text(value);Instant parsed=Instant.parse(value);require(value.equals(parsed.toString()),"canonical UTC native provenance timestamp required");return parsed;}
    private static boolean same(FileRef left,FileRef right){return Path.of(left.path()).equals(Path.of(right.path()))&&left.bytes()==right.bytes()&&left.sha256().equalsIgnoreCase(right.sha256());}
    private static void require(boolean condition,String reason){if(!condition)throw new IllegalArgumentException(reason);}
}
