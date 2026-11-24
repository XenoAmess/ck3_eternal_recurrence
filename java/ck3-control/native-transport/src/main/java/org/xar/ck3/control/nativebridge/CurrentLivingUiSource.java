package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Fixed Living UI observation DATA. It cannot reconstruct private scopes, owner leases or finite-case claims. */
public record CurrentLivingUiSource(Kind kind, long actorFullId, Optional<Weapon> weapon,
        Optional<Events> events, Optional<Detail> detail, boolean sampledTwice) {
    public enum Kind {
        WEAPON("weapon"), EVENTS("events"), DETAIL("detail");
        private final String wire;
        Kind(String wire) { this.wire=wire; }
        public String wire(){return wire;}
        public static Kind parse(String text)throws IOException {
            for(var kind:values())if(kind.wire.equals(text))return kind;
            throw new IOException("Unknown Living UI Source kind");
        }
    }

    public record Weapon(long targetFullId, Optional<Long> weaponArtifactFullId, boolean windowFound,
            boolean visible, boolean enabled, boolean targetEquipped, boolean weaponSelected,
            Optional<Boolean> nativeSlotAvailable, Optional<Boolean> nativeCanHold,
            boolean selectAdmissible, boolean equipAdmissible, boolean unequipAdmissible) {
        public Weapon {
            CurrentLivingInventoryQuery.requireFullId(targetFullId);Objects.requireNonNull(weaponArtifactFullId);
            Objects.requireNonNull(nativeSlotAvailable);Objects.requireNonNull(nativeCanHold);
            weaponArtifactFullId.ifPresent(CurrentLivingInventoryQuery::requireFullId);
            StrictJson.require(!visible||windowFound,"Visible weapon window must be observed found");
            boolean nativeAllowed=nativeSlotAvailable.orElse(false)&&nativeCanHold.orElse(false);
            if(selectAdmissible)StrictJson.require(windowFound&&visible&&enabled&&nativeAllowed&&!weaponSelected&&!targetEquipped,
                    "Select necessary actual slot conditions differ");
            if(equipAdmissible)StrictJson.require(windowFound&&visible&&enabled&&nativeAllowed&&weaponSelected&&!targetEquipped,
                    "Equip necessary actual selected slot conditions differ");
            if(unequipAdmissible)StrictJson.require(windowFound&&visible&&enabled&&targetEquipped
                    &&weaponArtifactFullId.equals(Optional.of(targetFullId)),"Unequip must retain the actual target in weapon slot");
        }
        static Weapon decode(JsonNode node)throws IOException {
            var r=StrictJson.object(node,Set.of("target_full_id","weapon_artifact_full_id","window_found","visible","enabled",
                    "target_equipped","weapon_selected","native_slot_available","native_can_hold","select_admissible","equip_admissible","unequip_admissible"));
            return new Weapon(CurrentLivingInventoryQuery.fullId(r.get("target_full_id")),id(r.get("weapon_artifact_full_id")),
                    b(r,"window_found"),b(r,"visible"),b(r,"enabled"),b(r,"target_equipped"),b(r,"weapon_selected"),
                    optionalBoolean(r.get("native_slot_available")),optionalBoolean(r.get("native_can_hold")),
                    b(r,"select_admissible"),b(r,"equip_admissible"),b(r,"unequip_admissible"));
        }
        ObjectNode encode() {
            var r=StrictJson.object().put("target_full_id",targetFullId).put("window_found",windowFound).put("visible",visible)
                    .put("enabled",enabled).put("target_equipped",targetEquipped).put("weapon_selected",weaponSelected)
                    .put("select_admissible",selectAdmissible).put("equip_admissible",equipAdmissible).put("unequip_admissible",unequipAdmissible);
            putId(r,"weapon_artifact_full_id",weaponArtifactFullId);putBool(r,"native_slot_available",nativeSlotAvailable);
            putBool(r,"native_can_hold",nativeCanHold);return r;
        }
    }

    public record ArtifactReference(CurrentLivingInventoryQuerySource.ReferenceState state, int scopeKind,
            Optional<Long> artifactFullId) {
        public ArtifactReference {
            Objects.requireNonNull(state);Objects.requireNonNull(artifactFullId);
            StrictJson.require(scopeKind>=0&&scopeKind<=0xffff,"Actual uint16 ScopeKind required");
            artifactFullId.ifPresent(CurrentLivingInventoryQuery::requireFullId);
            switch(state) {
                case ABSENT,PRESENT_EMPTY -> StrictJson.require(scopeKind==0&&artifactFullId.isEmpty(),"Empty held reference differs");
                case WRONG_KIND -> StrictJson.require(scopeKind!=0&&scopeKind!=36&&artifactFullId.isEmpty(),"Wrong-kind held reference differs");
                case ARTIFACT -> StrictJson.require(scopeKind==36&&artifactFullId.isPresent(),"Actual kind36 full artifact reference required");
            }
        }
        static ArtifactReference decode(JsonNode node)throws IOException {
            var r=StrictJson.object(node,Set.of("state","scope_kind","artifact_full_id"));
            return new ArtifactReference(CurrentLivingInventoryQuerySource.ReferenceState.parse(NativeWire.text(r.get("state"))),
                    NativeWire.integer(r.get("scope_kind"),BigInteger.ZERO,BigInteger.valueOf(0xffff)).intValueExact(),id(r.get("artifact_full_id")));
        }
        ObjectNode encode(){var r=StrictJson.object().put("state",state.wire()).put("scope_kind",scopeKind);putId(r,"artifact_full_id",artifactFullId);return r;}
    }

    public record EventBinding(int instanceId, int recipientId, String definitionKey, ArtifactReference target,
            ArtifactReference material, boolean targetOwned, boolean materialOwned, boolean materialRequired,
            boolean completeNamedScopes, boolean sampledTwice) {
        public EventBinding {
            Objects.requireNonNull(target);Objects.requireNonNull(material);key(definitionKey);
            StrictJson.require(instanceId>0&&recipientId!=-1&&completeNamedScopes&&sampledTwice&&targetOwned
                    &&target.artifactFullId().isPresent(),"Actual complete bound target and recipient required");
            StrictJson.require(definitionKey.equals("xalw.12")||definitionKey.equals("xalw.10")||definitionKey.equals("xalw.11"),
                    "Only fixed Living definitions have held bindings");
            StrictJson.require(materialRequired==definitionKey.equals("xalw.11"),"Review material requirement differs from actual definition");
            if(materialOwned)StrictJson.require(material.artifactFullId().isPresent(),"Owned material must have an actual artifact reference");
            if(materialRequired)StrictJson.require(materialOwned&&!target.artifactFullId().equals(material.artifactFullId()),
                    "Review requires two distinct actually owned artifacts");
        }
        static EventBinding decode(JsonNode node)throws IOException {
            var r=StrictJson.object(node,Set.of("instance_id","recipient_id","definition_key","target","material","target_owned",
                    "material_owned","material_required","complete_named_scopes","sampled_twice"));
            return new EventBinding(CurrentLivingInventoryQuery.i32(r.get("instance_id")),CurrentLivingInventoryQuery.i32(r.get("recipient_id")),
                    NativeWire.text(r.get("definition_key")),ArtifactReference.decode(r.get("target")),ArtifactReference.decode(r.get("material")),
                    b(r,"target_owned"),b(r,"material_owned"),b(r,"material_required"),b(r,"complete_named_scopes"),b(r,"sampled_twice"));
        }
        ObjectNode encode() {
            var r=StrictJson.object().put("instance_id",instanceId).put("recipient_id",recipientId).put("definition_key",definitionKey)
                    .put("target_owned",targetOwned).put("material_owned",materialOwned).put("material_required",materialRequired)
                    .put("complete_named_scopes",completeNamedScopes).put("sampled_twice",sampledTwice);
            r.set("target",target.encode());r.set("material",material.encode());return r;
        }
    }

    public record FixedAction(CurrentLivingUi.Action action, int instanceId, int authoredOptionIndex, boolean admissible) {
        public FixedAction {
            Objects.requireNonNull(action);
            StrictJson.require(action.sourceKind()==Kind.EVENTS&&!action.queryOnly()&&instanceId>0
                    &&authoredOptionIndex>=0&&authoredOptionIndex<64,"Actual fixed event action and authored index required");
        }
        static FixedAction decode(JsonNode node)throws IOException {
            var r=StrictJson.object(node,Set.of("action","instance_id","authored_option_index","admissible"));
            return new FixedAction(CurrentLivingUi.Action.parse(NativeWire.text(r.get("action"))),
                    CurrentLivingInventoryQuery.i32(r.get("instance_id")),CurrentLivingInventoryQuery.i32(r.get("authored_option_index")),b(r,"admissible"));
        }
        ObjectNode encode(){return StrictJson.object().put("action",action.wire()).put("instance_id",instanceId)
                .put("authored_option_index",authoredOptionIndex).put("admissible",admissible);}
    }

    /** Independent64-root Living census; common rows are DATA only and never inherit LYD roles or permissions. */
    public record Events(boolean censusComplete, int namedRootCount, List<CurrentLydSource.EventRow> events,
            List<EventBinding> bindings, List<FixedAction> fixedActions, boolean completeBindings) {
        private record ActionKey(int instanceId,CurrentLivingUi.Action action) { }
        public Events {
            events=List.copyOf(events);bindings=List.copyOf(bindings);fixedActions=List.copyOf(fixedActions);
            StrictJson.require(censusComplete&&completeBindings&&namedRootCount>=0&&namedRootCount<=64
                    &&namedRootCount==events.size()&&bindings.size()<=64&&fixedActions.size()<=128,"Complete bounded Living event/binding census required");
            var ids=new HashSet<Integer>();
            for(var event:events) {
                key(event.definitionKey());CurrentLivingEntry.requireActualText(event.opening());CurrentLivingEntry.requireActualText(event.description());
                StrictJson.require(ids.add(event.instanceId()),"Unique actual event required");
                // EventRow validates every displayed authored index against the complete loaded definition count.
                // Conditional options absent from the displayed census are not fabricated as placeholder rows.
                for(var option:event.options()) {
                    CurrentLivingEntry.requireActualText(option.text());CurrentLivingEntry.requireActualText(option.disabledReason());
                    StrictJson.require(option.permittedRole().isEmpty()&&option.sourceBoundOptionKey().isEmpty(),
                            "Living cannot borrow a LYD role or source-bound option key");
                }
            }
            var bound=new HashSet<Integer>();
            for(var binding:bindings) {
                StrictJson.require(bound.add(binding.instanceId()),"Duplicate held event binding");
                var event=events.stream().filter(e->e.instanceId()==binding.instanceId()).findFirst().orElseThrow(
                        ()->new IllegalArgumentException("Binding lacks actual event"));
                StrictJson.require(event.recipientCharacterId()==binding.recipientId()&&event.definitionKey().equals(binding.definitionKey())
                        &&event.authoredOptionCount()==(binding.definitionKey().equals("xalw.10")?10:2),"Binding/event actual identity differs");
            }
            var seen=new HashSet<ActionKey>();
            for(var fixed:fixedActions) {
                var binding=bindings.stream().filter(b->b.instanceId()==fixed.instanceId()).findFirst().orElseThrow(
                        ()->new IllegalArgumentException("Fixed action lacks actual held binding"));
                StrictJson.require(CurrentLivingUi.fixedIndex(fixed.action(),binding.definitionKey())==fixed.authoredOptionIndex()
                        &&seen.add(new ActionKey(fixed.instanceId(),fixed.action())),"Actual fixed action mapping or uniqueness differs");
                var event=events.stream().filter(e->e.instanceId()==fixed.instanceId()).findFirst().orElseThrow();
                var option=event.options().stream().filter(o->o.authoredOptionIndex()==fixed.authoredOptionIndex()).findFirst().orElseThrow(
                        ()->new IllegalArgumentException("Fixed authored option absent"));
                if(fixed.admissible())StrictJson.require(event.windowVisible()&&event.windowEnabled()&&option.nativeCanSelect(),
                        "Admissible fixed action lacks actual visible/enabled NativeCan");
            }
        }
        void requireActualActor(int actor) {
            for(var binding:bindings)StrictJson.require(binding.recipientId()==actor,"Held binding recipient differs from actual actor");
            for(var event:events)if(event.recipientCharacterId()==actor&&(event.definitionKey().equals("xalw.12")
                    ||event.definitionKey().equals("xalw.10")||event.definitionKey().equals("xalw.11")))
                StrictJson.require(bindings.stream().anyMatch(b->b.instanceId()==event.instanceId()),"Own fixed event lacks complete held binding");
        }
        static Events decode(JsonNode node)throws IOException {
            var r=StrictJson.object(node,Set.of("census_complete","named_root_count","events","bindings","fixed_actions","complete_bindings"));
            var rows=new ArrayList<CurrentLydSource.EventRow>();
            for(var n:array(r.get("events"),64))rows.add(CurrentLydSource.EventRow.decode(n));
            var bindings=new ArrayList<EventBinding>();for(var n:array(r.get("bindings"),64))bindings.add(EventBinding.decode(n));
            var actions=new ArrayList<FixedAction>();for(var n:array(r.get("fixed_actions"),128))actions.add(FixedAction.decode(n));
            return new Events(b(r,"census_complete"),CurrentLivingInventoryQuery.i32(r.get("named_root_count")),rows,bindings,actions,b(r,"complete_bindings"));
        }
        ObjectNode encode() {
            var r=StrictJson.object().put("census_complete",censusComplete).put("named_root_count",namedRootCount).put("complete_bindings",completeBindings);
            var rows=r.putArray("events");for(var event:events) {
                var e=rows.addObject().put("instance_id",event.instanceId()).put("recipient_character_id",event.recipientCharacterId())
                        .put("definition_key",event.definitionKey()).put("authored_option_count",event.authoredOptionCount())
                        .put("named_root_bound",event.namedRootBound()).put("window_visible",event.windowVisible())
                        .put("window_enabled",event.windowEnabled()).put("opening",event.opening()).put("description",event.description());
                var options=e.putArray("options");for(var option:event.options())options.addObject()
                        .put("authored_option_index",option.authoredOptionIndex()).put("native_can_select",option.nativeCanSelect())
                        .put("text",option.text()).put("disabled_reason",option.disabledReason()).putNull("permitted_role").putNull("source_bound_option_key");
            }
            var bindingArray=r.putArray("bindings");for(var binding:bindings)bindingArray.add(binding.encode());
            var actions=r.putArray("fixed_actions");for(var action:fixedActions)actions.add(action.encode());return r;
        }
    }

    public record Detail(long targetFullId, boolean windowFound, boolean visible, boolean enabled, boolean targetBound,
            Optional<String> modifierEffectsText, Optional<String> customEffectsText, Optional<String> descriptionText) {
        public Detail {
            CurrentLivingInventoryQuery.requireFullId(targetFullId);Objects.requireNonNull(modifierEffectsText);
            Objects.requireNonNull(customEffectsText);Objects.requireNonNull(descriptionText);
            StrictJson.require(!visible||windowFound,"Visible actual detail must be observed found");
            StrictJson.require(!targetBound||windowFound,"Bound detail target must be observed found");
            for(var text:List.of(modifierEffectsText,customEffectsText,descriptionText))text.ifPresent(value->{
                StrictJson.require(targetBound,"Observed engine text requires actual target binding");CurrentLivingEntry.requireActualText(value);
            });
        }
        static Detail decode(JsonNode node)throws IOException {
            var r=StrictJson.object(node,Set.of("target_full_id","window_found","visible","enabled","target_bound",
                    "modifier_effects_text","custom_effects_text","description_text"));
            return new Detail(CurrentLivingInventoryQuery.fullId(r.get("target_full_id")),b(r,"window_found"),b(r,"visible"),b(r,"enabled"),
                    b(r,"target_bound"),text(r.get("modifier_effects_text")),text(r.get("custom_effects_text")),text(r.get("description_text")));
        }
        ObjectNode encode() {
            var r=StrictJson.object().put("target_full_id",targetFullId).put("window_found",windowFound).put("visible",visible)
                    .put("enabled",enabled).put("target_bound",targetBound);putText(r,"modifier_effects_text",modifierEffectsText);
            putText(r,"custom_effects_text",customEffectsText);putText(r,"description_text",descriptionText);return r;
        }
    }

    public CurrentLivingUiSource {
        Objects.requireNonNull(kind);Objects.requireNonNull(weapon);Objects.requireNonNull(events);Objects.requireNonNull(detail);
        CurrentLivingInventoryQuery.requireFullId(actorFullId);
        StrictJson.require(sampledTwice&&(weapon.isPresent()?1:0)+(events.isPresent()?1:0)+(detail.isPresent()?1:0)==1,
                "Exactly one double-sampled Living UI branch required");
        StrictJson.require(kind==Kind.WEAPON?weapon.isPresent():kind==Kind.EVENTS?events.isPresent():detail.isPresent(),"UI kind/union differs");
        events.ifPresent(e->e.requireActualActor((int)actorFullId));
    }

    /** Necessary Source shape only; private native state still owns authority and once-claim identity. */
    public boolean actionAdmissible(CurrentLivingUi.Action action) {
        if(kind!=action.sourceKind())return false;if(action.queryOnly())return true;
        if(weapon.isPresent())return switch(action) {
            case SELECT_WEAPON -> weapon.orElseThrow().selectAdmissible();
            case EQUIP_TARGET -> weapon.orElseThrow().equipAdmissible();
            case UNEQUIP_TARGET -> weapon.orElseThrow().unequipAdmissible();
            default -> false;
        };
        return events.isPresent()&&events.orElseThrow().fixedActions().stream().filter(a->a.action()==action&&a.admissible()).count()==1;
    }

    public static CurrentLivingUiSource decode(JsonNode node)throws IOException {
        try {
            var r=StrictJson.object(node,Set.of("schema","kind","actor_full_id","weapon","events","detail","sampled_twice"));
            CurrentLivingInventoryQuery.identity(r,"schema",CurrentLivingUi.SOURCE_SCHEMA);
            return new CurrentLivingUiSource(Kind.parse(NativeWire.text(r.get("kind"))),CurrentLivingInventoryQuery.fullId(r.get("actor_full_id")),
                    r.get("weapon").isNull()?Optional.empty():Optional.of(Weapon.decode(r.get("weapon"))),
                    r.get("events").isNull()?Optional.empty():Optional.of(Events.decode(r.get("events"))),
                    r.get("detail").isNull()?Optional.empty():Optional.of(Detail.decode(r.get("detail"))),b(r,"sampled_twice"));
        }catch(IllegalArgumentException|ArithmeticException invalid){throw new IOException("Invalid exact Living UI Source DATA",invalid);}
    }
    public ObjectNode encode() {
        var r=StrictJson.object().put("schema",CurrentLivingUi.SOURCE_SCHEMA).put("kind",kind.wire()).put("actor_full_id",actorFullId).put("sampled_twice",sampledTwice);
        if(weapon.isPresent())r.set("weapon",weapon.orElseThrow().encode());else r.putNull("weapon");
        if(events.isPresent())r.set("events",events.orElseThrow().encode());else r.putNull("events");
        if(detail.isPresent())r.set("detail",detail.orElseThrow().encode());else r.putNull("detail");return r;
    }
    private static void key(String text){StrictJson.require(text!=null&&text.length()>=1&&text.length()<=256&&text.matches("[A-Za-z0-9_.-]+"),"Actual native fixed-key shape required");}
    private static boolean b(ObjectNode n,String key)throws IOException{return CurrentLivingInventoryQuery.bool(n,key);}
    private static Optional<Long> id(JsonNode n)throws IOException{return n.isNull()?Optional.empty():Optional.of(CurrentLivingInventoryQuery.fullId(n));}
    private static Optional<String> text(JsonNode n)throws IOException{return n.isNull()?Optional.empty():Optional.of(CurrentLivingEntry.actualText(n));}
    private static Optional<Boolean> optionalBoolean(JsonNode n)throws IOException {
        if(n.isNull())return Optional.empty();if(!n.isBoolean())throw new IOException("Nullable actual bool required");return Optional.of(n.booleanValue());
    }
    private static JsonNode array(JsonNode n,int maximum)throws IOException {
        if(n==null||!n.isArray()||n.size()>maximum)throw new IOException("Complete bounded actual array required");return n;
    }
    private static void putId(ObjectNode n,String key,Optional<Long> value){if(value.isPresent())n.put(key,value.orElseThrow());else n.putNull(key);}
    private static void putBool(ObjectNode n,String key,Optional<Boolean> value){if(value.isPresent())n.put(key,value.orElseThrow());else n.putNull(key);}
    private static void putText(ObjectNode n,String key,Optional<String> value){if(value.isPresent())n.put(key,value.orElseThrow());else n.putNull(key);}
}
