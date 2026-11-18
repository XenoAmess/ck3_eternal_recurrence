package org.xar.ck3.control.nativebridge.capabilities.registry;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.semantic.NativePlayedResources;

/** Partial actor DATA only: no complete Snapshot, old family qualification, treasury, flow, private receiver or action role. */
public sealed interface ActorFoundationFrame permits ActorFoundationFrame.Partial,ActorFoundationFrame.Unavailable {
    String STEP="query-actor-foundation-frame-v1";
    String CAPABILITY="game.query.actor-foundation-frame.v1";
    String SCHEMA="ck3_1210_actor_foundation_frame_v1";
    String ADAPTER="ck3-1.21.0-msvc-x64";
    String BACKEND="ck3-1.21.0-native-headless-main-thread";
    ExactCk3Build BUILD=ExactCk3Build.CK3_1210;
    int SPOUSE_OBSERVATION_LIMIT=64;
    Set<String> FIELDS=Set.of("step","schema","game_version","executable_sha256","adapter_id","backend","status",
            "foundation_available","resources_available","relationships_available","application_main_observed",
            "complete_snapshot","treasury_observed","monthly_flow_observed","core_frame","resources","relationships",
            "resources_unavailable_reason","relationships_unavailable_reason","unavailable_reason");
    default ExactCk3Build build(){return BUILD;}
    CoreFrame coreFrame();
    boolean applicationMainObserved();
    ResourceGroup resources();
    RelationshipGroup relationships();

    sealed interface ResourceGroup permits AvailableResources,UnavailableResources { }
    /** Each resource preserves its exact signed native int64 and scale; stress preserves signed native int32. */
    record AvailableResources(NativePlayedResources.Amount gold,NativePlayedResources.Amount prestige,
            NativePlayedResources.Amount piety,int stressPoints) implements ResourceGroup {
        public AvailableResources {Objects.requireNonNull(gold);Objects.requireNonNull(prestige);Objects.requireNonNull(piety);}
    }
    /** An original JSON null resource group, never a manufactured zero wallet. */
    record UnavailableResources(String reason) implements ResourceGroup {
        public UnavailableResources {originalReason(reason);}
    }
    sealed interface RelationshipGroup permits AvailableRelationships,UnavailableRelationships { }
    /** Signed full32 scalar IDs retain -1 absence. Vector order, zero IDs and duplicates are not rewritten. */
    record AvailableRelationships(int betrothedCharacterId,int primarySpouseCharacterId,List<Integer> spouseCharacterIds)
            implements RelationshipGroup {
        public AvailableRelationships {
            spouseCharacterIds=List.copyOf(spouseCharacterIds);
            RegistryJson.require(spouseCharacterIds.size()<=SPOUSE_OBSERVATION_LIMIT,"spouse observation scope exceeded");
            for(int id:spouseCharacterIds)RegistryJson.require(id!=-1,"invalid native spouse vector sentinel");
        }
    }
    /** An original JSON null relation group, distinct from successfully observed -1/-1/empty relations. */
    record UnavailableRelationships(String reason) implements RelationshipGroup {
        public UnavailableRelationships {originalReason(reason);}
    }
    record Partial(CoreFrame.Partial coreFrame,ResourceGroup resources,RelationshipGroup relationships)
            implements ActorFoundationFrame {
        public Partial {
            exactCore(coreFrame);Objects.requireNonNull(resources);Objects.requireNonNull(relationships);
            var prefix=coreFrame.prefix();
            RegistryJson.require(prefix.mapReady()&&prefix.paused()&&prefix.localPlayerId()>=0
                    &&prefix.hasPlayedCharacter()&&prefix.playedCharacterAlive(),"actor foundation requires its actual paused living actor Core prefix");
            RegistryJson.require(anyAvailable(resources,relationships),"partial actor foundation requires at least one observed group");
        }
        @Override public boolean applicationMainObserved(){return true;}
    }
    record Unavailable(CoreFrame coreFrame,boolean applicationMainObserved,ResourceGroup resources,
            RelationshipGroup relationships,String reason) implements ActorFoundationFrame {
        public Unavailable {
            exactCore(coreFrame);Objects.requireNonNull(resources);Objects.requireNonNull(relationships);originalReason(reason);
            RegistryJson.require(applicationMainObserved==coreObserved(coreFrame),"actor foundation and Core application-main observations differ");
            RegistryJson.require(!(coreFrame instanceof CoreFrame.Partial)||!anyAvailable(resources,relationships),
                    "stable Core plus an observed actor group must remain partial");
        }
    }
    private static boolean anyAvailable(ResourceGroup resources,RelationshipGroup relationships){
        return resources instanceof AvailableResources||relationships instanceof AvailableRelationships;
    }
    private static void originalReason(String reason){RegistryJson.require(reason!=null&&!reason.isEmpty(),"original actor group unavailability reason required");}
    private static void exactCore(CoreFrame core){Objects.requireNonNull(core);RegistryJson.require(core.build()==BUILD,"actor foundation requires the exact Florin Core frame");}
    private static boolean coreObserved(CoreFrame core){return core instanceof CoreFrame.Partial||((CoreFrame.Unavailable)core).applicationMainObserved();}

    static ActorFoundationFrame decode(RawJson original){
        var row=RegistryJson.object(original);RegistryJson.keys(row,FIELDS);
        RegistryJson.require(STEP.equals(RegistryJson.text(row.get("step")))&&SCHEMA.equals(RegistryJson.text(row.get("schema")))
                &&BUILD.matches(RegistryJson.text(row.get("game_version")),RegistryJson.text(row.get("executable_sha256")))
                &&ADAPTER.equals(RegistryJson.text(row.get("adapter_id")))&&BACKEND.equals(RegistryJson.text(row.get("backend"))),
                "actor foundation exact source mismatch");
        RegistryJson.require(!RegistryJson.bool(row.get("complete_snapshot"))&&!RegistryJson.bool(row.get("treasury_observed"))
                &&!RegistryJson.bool(row.get("monthly_flow_observed")),"actor foundation cannot claim complete, treasury or monthly observations");
        var core=CoreFrame.decodeObject(RegistryJson.object(row.get("core_frame")));exactCore(core);
        boolean observed=RegistryJson.bool(row.get("application_main_observed"));
        RegistryJson.require(observed==coreObserved(core),"actor foundation and Core application-main observations differ");
        boolean resourceAvailable=RegistryJson.bool(row.get("resources_available"));
        boolean relationshipAvailable=RegistryJson.bool(row.get("relationships_available"));
        ResourceGroup resources=decodeResources(row,resourceAvailable);
        RelationshipGroup relationships=decodeRelationships(row,relationshipAvailable);
        boolean available=RegistryJson.bool(row.get("foundation_available"));
        RegistryJson.require(available==((core instanceof CoreFrame.Partial)&&(resourceAvailable||relationshipAvailable)),
                "actor foundation availability disagrees with its independent groups and Core prefix");
        if(!available){
            RegistryJson.require("unavailable".equals(RegistryJson.text(row.get("status"))),"actor foundation unavailable status mismatch");
            return new Unavailable(core,observed,resources,relationships,RegistryJson.text(row.get("unavailable_reason")));
        }
        RegistryJson.require("partial".equals(RegistryJson.text(row.get("status")))&&observed&&row.get("unavailable_reason").isNull(),
                "partial actor foundation requires its original status/reason");
        return new Partial((CoreFrame.Partial)core,resources,relationships);
    }
    private static ResourceGroup decodeResources(ObjectNode row,boolean available){
        if(!available){
            RegistryJson.require(row.get("resources").isNull(),"unavailable resource group must retain explicit null");
            return new UnavailableResources(RegistryJson.text(row.get("resources_unavailable_reason")));
        }
        RegistryJson.require(row.get("resources_unavailable_reason").isNull(),"available resources must retain null reason");
        var values=RegistryJson.object(row.get("resources"));RegistryJson.keys(values,Set.of("gold","prestige","piety","stress_points"));
        return new AvailableResources(amount(values,"gold"),amount(values,"prestige"),amount(values,"piety"),RegistryJson.int32(values.get("stress_points")));
    }
    private static NativePlayedResources.Amount amount(ObjectNode row,String field){
        var value=NativePlayedResources.decode(row.get(field));
        RegistryJson.require(value instanceof NativePlayedResources.Amount,"available atomic resource group requires all three exact amounts");
        return (NativePlayedResources.Amount)value;
    }
    private static RelationshipGroup decodeRelationships(ObjectNode row,boolean available){
        if(!available){
            RegistryJson.require(row.get("relationships").isNull(),"unavailable relationship group must retain explicit null");
            return new UnavailableRelationships(RegistryJson.text(row.get("relationships_unavailable_reason")));
        }
        RegistryJson.require(row.get("relationships_unavailable_reason").isNull(),"available relationships must retain null reason");
        var values=RegistryJson.object(row.get("relationships"));
        RegistryJson.keys(values,Set.of("betrothed_character_id","primary_spouse_character_id","spouse_character_ids"));
        var ids=RegistryJson.array(values.get("spouse_character_ids")).stream().map(RegistryJson::int32).toList();
        return new AvailableRelationships(RegistryJson.int32(values.get("betrothed_character_id")),RegistryJson.int32(values.get("primary_spouse_character_id")),ids);
    }
}
