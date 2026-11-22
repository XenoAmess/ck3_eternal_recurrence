package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Immutable typed union DATA. A validated deep copy preserves native nulls and richtext; it grants no origin/custody. */
public final class CurrentLydSource {
    public record DecisionRow(CurrentLyd.DecisionKey decisionKey,boolean canOpenDetail,boolean isSelected) {
        public DecisionRow {Objects.requireNonNull(decisionKey);}
    }
    public record Decisions(boolean listFound,boolean listVisible,boolean listEnabled,boolean detailFound,boolean detailVisible,
            boolean detailEnabled,boolean otherDecisionSelected,boolean openListAdmissible,boolean completeModelCensus,
            boolean blockedByVisibleModal,boolean confirmAdmissible,Optional<Integer> groupsCount,Optional<Integer> totalModelRows,
            Optional<Integer> widgetState,Optional<CurrentLyd.DecisionKey> selectedDecisionKey,Optional<Boolean> nativeCanConfirm,
            List<DecisionRow> rows,Optional<String> conditionsText) {
        public Decisions {
            Objects.requireNonNull(groupsCount);Objects.requireNonNull(totalModelRows);Objects.requireNonNull(widgetState);
            Objects.requireNonNull(selectedDecisionKey);Objects.requireNonNull(nativeCanConfirm);Objects.requireNonNull(conditionsText);rows=List.copyOf(rows);
            StrictJson.require(rows.size()<=5,"At most five fixed LYD decision rows");
            if(!listFound)StrictJson.require(!listVisible&&!listEnabled&&!completeModelCensus&&rows.isEmpty()&&groupsCount.isEmpty()&&totalModelRows.isEmpty(),"Absent list has no material census");
            if(!detailFound)StrictJson.require(!detailVisible&&!detailEnabled&&selectedDecisionKey.isEmpty()&&!otherDecisionSelected&&nativeCanConfirm.isEmpty()&&widgetState.isEmpty(),"Absent detail has no material selection");
            StrictJson.require(completeModelCensus==(groupsCount.isPresent()&&totalModelRows.isPresent()),"Complete model/count roles differ");
            if(!completeModelCensus)StrictJson.require(rows.isEmpty()&&groupsCount.isEmpty()&&totalModelRows.isEmpty(),"Unmaterialized list cannot invent rows/counts");
            groupsCount.ifPresent(n->StrictJson.require(n>=0&&n<=64,"Actual group count bound"));totalModelRows.ifPresent(n->StrictJson.require(n>=0&&n<=1024,"Actual model row bound"));
            StrictJson.require(!otherDecisionSelected||selectedDecisionKey.isEmpty(),"Other selection cannot masquerade as fixed key");
            if(nativeCanConfirm.isPresent())StrictJson.require(selectedDecisionKey.isPresent()&&detailVisible,"NativeCan belongs to actual visible selected detail");
            if(confirmAdmissible)StrictJson.require(detailFound&&detailVisible&&detailEnabled&&!blockedByVisibleModal&&selectedDecisionKey.isPresent()
                    &&selectedDecisionKey.orElseThrow()!=CurrentLyd.DecisionKey.BEGIN_READONLY&&nativeCanConfirm.orElse(false),"Confirmation lacks actual Native admission; begin remains read-only");
            if(openListAdmissible)StrictJson.require(!listVisible&&!blockedByVisibleModal,"Open is not an idempotent toggle");
            var seen=new HashSet<CurrentLyd.DecisionKey>();
            for(var row:rows){StrictJson.require(seen.add(row.decisionKey()),"Duplicate decision key");
                StrictJson.require(row.isSelected()==(detailVisible&&selectedDecisionKey.filter(row.decisionKey()::equals).isPresent()),"Actual row/detail selection differs");
                if(row.canOpenDetail())StrictJson.require(listVisible&&listEnabled&&!row.isSelected()&&!blockedByVisibleModal,"Detail opening lacks actual list context");}
            conditionsText.ifPresent(CurrentLyd::text);
        }
        static Decisions decode(JsonNode node)throws IOException {
            var r=StrictJson.object(node,Set.of("list_found","list_visible","list_enabled","detail_found","detail_visible","detail_enabled","other_decision_selected","open_list_admissible","complete_model_census","blocked_by_visible_modal","confirm_admissible","groups_count","total_model_rows","widget_state","selected_decision_key","native_can_confirm","rows","conditions_text"));
            var rows=new ArrayList<DecisionRow>();for(var raw:array(r,"rows",5)){var n=StrictJson.object(raw,Set.of("decision_key","can_open_detail","is_selected"));rows.add(new DecisionRow(CurrentLyd.DecisionKey.parse(NativeWire.text(n.get("decision_key"))),CurrentLyd.bool(n,"can_open_detail"),CurrentLyd.bool(n,"is_selected")));}
            return new Decisions(CurrentLyd.bool(r,"list_found"),CurrentLyd.bool(r,"list_visible"),CurrentLyd.bool(r,"list_enabled"),CurrentLyd.bool(r,"detail_found"),CurrentLyd.bool(r,"detail_visible"),CurrentLyd.bool(r,"detail_enabled"),CurrentLyd.bool(r,"other_decision_selected"),CurrentLyd.bool(r,"open_list_admissible"),CurrentLyd.bool(r,"complete_model_census"),CurrentLyd.bool(r,"blocked_by_visible_modal"),CurrentLyd.bool(r,"confirm_admissible"),CurrentLyd.integer(r.get("groups_count")),CurrentLyd.integer(r.get("total_model_rows")),CurrentLyd.integer(r.get("widget_state")),decision(r.get("selected_decision_key")),CurrentLyd.boolOptional(r,"native_can_confirm"),rows,CurrentLyd.nativeTextOptional(r.get("conditions_text")));
        }
    }
    public record EventOption(int authoredOptionIndex,boolean nativeCanSelect,String text,String disabledReason,
            Optional<String> sourceBoundOptionKey,Optional<CurrentLyd.EventRole> permittedRole) {
        public EventOption {StrictJson.require(authoredOptionIndex>=0,"Actual authored option index required");CurrentLyd.text(text);CurrentLyd.text(disabledReason);
            Objects.requireNonNull(sourceBoundOptionKey);Objects.requireNonNull(permittedRole);sourceBoundOptionKey.ifPresent(k->CurrentLyd.key(k,256));}
        static EventOption decode(JsonNode node)throws IOException{
            var r=StrictJson.object(node,Set.of("authored_option_index","native_can_select","text","disabled_reason","source_bound_option_key","permitted_role"));
            return new EventOption(CurrentLyd.i32(r.get("authored_option_index")),CurrentLyd.bool(r,"native_can_select"),CurrentLyd.nativeText(r.get("text")),CurrentLyd.nativeText(r.get("disabled_reason")),CurrentLyd.nativeTextOptional(r.get("source_bound_option_key")),role(r.get("permitted_role")));
        }
    }
    public record EventRow(int instanceId,int recipientCharacterId,int authoredOptionCount,String definitionKey,String opening,String description,
            boolean namedRootBound,boolean windowVisible,boolean windowEnabled,List<EventOption> options) {
        public EventRow {CurrentLyd.key(definitionKey,256);CurrentLyd.text(opening);CurrentLyd.text(description);options=List.copyOf(options);
            StrictJson.require(instanceId>0&&recipientCharacterId!=-1&&authoredOptionCount>=0&&authoredOptionCount<=64&&namedRootBound&&options.size()<=64,"Actual complete bound event row required");
            var seen=new HashSet<Integer>();
            for(var option:options){StrictJson.require(option.authoredOptionIndex()<authoredOptionCount&&seen.add(option.authoredOptionIndex()),"Distinct actual authored indices required");
                option.permittedRole().ifPresent(r->StrictJson.require(option.sourceBoundOptionKey().filter(k->r.matches(definitionKey,authoredOptionCount,option.authoredOptionIndex(),k)).isPresent(),"Role must match exact loaded definition/count/index/key; practice has no permitted role"));}
        }
        static EventRow decode(JsonNode node)throws IOException {
            var r=StrictJson.object(node,Set.of("instance_id","recipient_character_id","authored_option_count","definition_key","opening","description","named_root_bound","window_visible","window_enabled","options"));
            var options=new ArrayList<EventOption>();for(var n:array(r,"options",64))options.add(EventOption.decode(n));
            return new EventRow(CurrentLyd.i32(r.get("instance_id")),CurrentLyd.i32(r.get("recipient_character_id")),CurrentLyd.i32(r.get("authored_option_count")),NativeWire.text(r.get("definition_key")),CurrentLyd.nativeText(r.get("opening")),CurrentLyd.nativeText(r.get("description")),CurrentLyd.bool(r,"named_root_bound"),CurrentLyd.bool(r,"window_visible"),CurrentLyd.bool(r,"window_enabled"),options);
        }
    }
    public record Events(boolean censusComplete,int namedRootCount,List<EventRow> events) {
        public Events {events=List.copyOf(events);StrictJson.require(censusComplete&&namedRootCount>=0&&namedRootCount<=32&&namedRootCount==events.size(),"Actual complete event root census required");
            var ids=new HashSet<Integer>();for(var event:events)StrictJson.require(ids.add(event.instanceId()),"Duplicate actual event instance");}
        static Events decode(JsonNode node)throws IOException{var r=StrictJson.object(node,Set.of("census_complete","named_root_count","events"));var events=new ArrayList<EventRow>();for(var n:array(r,"events",32))events.add(EventRow.decode(n));return new Events(CurrentLyd.bool(r,"census_complete"),CurrentLyd.i32(r.get("named_root_count")),events);}
    }
    public record PersonalSlot(boolean isEmpty,boolean isPersonal,Optional<String> definitionKey) {
        public PersonalSlot {Objects.requireNonNull(definitionKey);if(isEmpty)StrictJson.require(!isPersonal&&definitionKey.isEmpty(),"Empty slot has no fabricated key/personal state");
            else{StrictJson.require(definitionKey.isPresent(),"Nonempty slot requires actual canonical key");definitionKey.ifPresent(k->CurrentLyd.key(k,192));}}
        static PersonalSlot decode(JsonNode node)throws IOException{var r=StrictJson.object(node,Set.of("is_empty","is_personal","definition_key"));return new PersonalSlot(CurrentLyd.bool(r,"is_empty"),CurrentLyd.bool(r,"is_personal"),CurrentLyd.nativeTextOptional(r.get("definition_key")));}
    }
    public record PersonalRow(int groupCategory,String definitionKey,String choiceToken,boolean groupCanPick,boolean isPersonal,
            Optional<Boolean> nativeCanPick,boolean selectAdmissible) {
        public PersonalRow {StrictJson.require(groupCategory>=0&&groupCategory<=6,"Actual category byte bound");CurrentLyd.key(definitionKey,192);Objects.requireNonNull(choiceToken);Objects.requireNonNull(nativeCanPick);
            if(!choiceToken.isEmpty())CurrentLyd.key(choiceToken,96);
            if(!CurrentLyd.PersonalKey.contains(definitionKey))StrictJson.require(nativeCanPick.isEmpty(),"Unqualified row NativeCanPick remains null");}
        static PersonalRow decode(JsonNode node)throws IOException{var r=StrictJson.object(node,Set.of("group_category","definition_key","choice_token","group_can_pick","is_personal","native_can_pick","select_admissible"));return new PersonalRow(CurrentLyd.i32(r.get("group_category")),NativeWire.text(r.get("definition_key")),CurrentLyd.nativeText(r.get("choice_token")),CurrentLyd.bool(r,"group_can_pick"),CurrentLyd.bool(r,"is_personal"),CurrentLyd.boolOptional(r,"native_can_pick"),CurrentLyd.bool(r,"select_admissible"));}
    }
    public record AddModal(boolean found,boolean namedRootBound,boolean visible,boolean closed,Optional<CurrentLyd.PersonalKey> personalKey,
            Optional<Boolean> nativeCanAccept,boolean acceptAdmissible) {
        public AddModal {Objects.requireNonNull(personalKey);Objects.requireNonNull(nativeCanAccept);
            if(!found)StrictJson.require(!namedRootBound&&!visible&&!closed&&personalKey.isEmpty()&&nativeCanAccept.isEmpty()&&!acceptAdmissible,"Absent modal cannot carry material facts");
            else StrictJson.require(namedRootBound&&personalKey.isPresent(),"Found modal requires exact bound personal target");}
        static AddModal decode(JsonNode node)throws IOException{var r=StrictJson.object(node,Set.of("found","named_root_bound","visible","closed","personal_key","native_can_accept","accept_admissible"));return new AddModal(CurrentLyd.bool(r,"found"),CurrentLyd.bool(r,"named_root_bound"),CurrentLyd.bool(r,"visible"),CurrentLyd.bool(r,"closed"),CurrentLydSource.personalKey(r.get("personal_key")),CurrentLyd.boolOptional(r,"native_can_accept"),CurrentLyd.bool(r,"accept_admissible"));}
    }
    public record Resources(long personalGoldRaw,long prestigeRaw,long pietyRaw,int stressPoints) {
        static Resources decode(JsonNode node)throws IOException{var r=StrictJson.object(node,Set.of("personal_gold_raw","prestige_raw","piety_raw","stress_points"));return new Resources(CurrentLyd.rawLong(r.get("personal_gold_raw")),CurrentLyd.rawLong(r.get("prestige_raw")),CurrentLyd.rawLong(r.get("piety_raw")),CurrentLyd.i32(r.get("stress_points")));}
    }
    public record Personal(boolean residentAvailable,boolean namedRootBound,boolean windowVisible,boolean windowEnabled,boolean actorBound,
            boolean isAdding,boolean modelMaterialized,boolean slotsComplete,boolean groupsComplete,boolean emptySlotFound,
            boolean actualPersonalComplete,boolean blockedByVisibleModal,boolean openAdmissible,boolean startAddAdmissible,
            Optional<Integer> slotCount,Optional<Integer> groupCount,Optional<Boolean> nativeWindowVisible,List<PersonalSlot> slots,
            List<PersonalRow> rows,List<String> actualPersonalKeys,AddModal addModal,Optional<Long> spiritualFulfillmentRaw,Optional<Resources> quotedCurrencyCosts) {
        public Personal {
            Objects.requireNonNull(slotCount);Objects.requireNonNull(groupCount);Objects.requireNonNull(nativeWindowVisible);Objects.requireNonNull(addModal);Objects.requireNonNull(spiritualFulfillmentRaw);Objects.requireNonNull(quotedCurrencyCosts);
            slots=List.copyOf(slots);rows=List.copyOf(rows);actualPersonalKeys=List.copyOf(actualPersonalKeys);
            StrictJson.require(residentAvailable&&quotedCurrencyCosts.isEmpty()&&rows.size()<=2048&&slots.size()<=64&&actualPersonalKeys.size()<=64,"Actual resident and bounded collections; currency quote is unqualified/null");
            if(windowVisible)StrictJson.require(namedRootBound&&actorBound&&nativeWindowVisible.orElse(false)&&modelMaterialized,"Visible actual window requires bound actor and materialized models");
            if(modelMaterialized)StrictJson.require(slotsComplete&&groupsComplete&&slotCount.filter(n->n>=0&&n<=64).isPresent()&&groupCount.filter(n->n>=0&&n<=7).isPresent()&&slotCount.orElseThrow()==slots.size(),"Complete actual slot/group models required");
            else StrictJson.require(!slotsComplete&&!groupsComplete&&slotCount.isEmpty()&&groupCount.isEmpty()&&slots.isEmpty()&&rows.isEmpty()&&!emptySlotFound,"Unmaterialized model remains null/absent, never guessed empty");
            StrictJson.require(emptySlotFound==slots.stream().anyMatch(PersonalSlot::isEmpty),"Actual empty slot flag differs from full slot census");
            var personalSeen=new HashSet<String>();for(var key:actualPersonalKeys){CurrentLyd.key(key,192);StrictJson.require(personalSeen.add(key),"Duplicate actual personal membership key");}
            if(!actualPersonalComplete)StrictJson.require(actualPersonalKeys.isEmpty(),"Partial membership cannot carry an apparently complete set");
            var rowKeys=new HashSet<String>();var tokens=new HashSet<String>();
            for(var row:rows){StrictJson.require(rowKeys.add(row.definitionKey())&&(row.choiceToken().isEmpty()||tokens.add(row.choiceToken())),"Duplicate semantic row key or opaque token");
                if(row.selectAdmissible())StrictJson.require(windowVisible&&windowEnabled&&actorBound&&isAdding&&modelMaterialized&&!blockedByVisibleModal&&emptySlotFound&&actualPersonalComplete
                        &&row.groupCanPick()&&!row.isPersonal()&&row.nativeCanPick().orElse(false)&&!row.choiceToken().isEmpty()&&CurrentLyd.PersonalKey.contains(row.definitionKey())&&!personalSeen.contains(row.definitionKey()),"Candidate requires full actual ADD prestate and NativeCan; no reverse implication");}
            if(openAdmissible)StrictJson.require(!windowVisible&&nativeWindowVisible.filter(v->!v).isPresent()&&!blockedByVisibleModal,"Actual Toggle open requires proven native-hidden state");
            if(startAddAdmissible)StrictJson.require(windowVisible&&windowEnabled&&actorBound&&emptySlotFound&&modelMaterialized&&!isAdding&&!blockedByVisibleModal,"Start ADD requires original actual empty-slot window");
            if(addModal.acceptAdmissible())StrictJson.require(addModal.found()&&addModal.visible()&&!addModal.closed()&&addModal.nativeCanAccept().orElse(false)&&actorBound&&actualPersonalComplete&&emptySlotFound,"ADD confirmation requires actual fresh NativeCan/actor/membership/slot");
        }
        static Personal decode(JsonNode node)throws IOException {
            var r=StrictJson.object(node,Set.of("resident_available","named_root_bound","window_visible","window_enabled","actor_bound","is_adding","model_materialized","slots_complete","groups_complete","empty_slot_found","actual_personal_complete","blocked_by_visible_modal","open_admissible","start_add_admissible","slot_count","group_count","native_window_visible","slots","rows","actual_personal_keys","add_modal","spiritual_fulfillment_raw","quoted_currency_costs"));
            var slots=new ArrayList<PersonalSlot>();for(var n:array(r,"slots",64))slots.add(PersonalSlot.decode(n));
            var rows=new ArrayList<PersonalRow>();for(var n:array(r,"rows",2048))rows.add(PersonalRow.decode(n));
            var keys=new ArrayList<String>();for(var n:array(r,"actual_personal_keys",64))keys.add(NativeWire.text(n));
            if(!r.get("quoted_currency_costs").isNull())throw new IOException("No qualified ADD currency quote; must be null");
            return new Personal(CurrentLyd.bool(r,"resident_available"),CurrentLyd.bool(r,"named_root_bound"),CurrentLyd.bool(r,"window_visible"),CurrentLyd.bool(r,"window_enabled"),CurrentLyd.bool(r,"actor_bound"),CurrentLyd.bool(r,"is_adding"),CurrentLyd.bool(r,"model_materialized"),CurrentLyd.bool(r,"slots_complete"),CurrentLyd.bool(r,"groups_complete"),CurrentLyd.bool(r,"empty_slot_found"),CurrentLyd.bool(r,"actual_personal_complete"),CurrentLyd.bool(r,"blocked_by_visible_modal"),CurrentLyd.bool(r,"open_admissible"),CurrentLyd.bool(r,"start_add_admissible"),CurrentLyd.integer(r.get("slot_count")),CurrentLyd.integer(r.get("group_count")),CurrentLyd.boolOptional(r,"native_window_visible"),slots,rows,keys,AddModal.decode(r.get("add_modal")),CurrentLyd.rawOptional(r.get("spiritual_fulfillment_raw")),Optional.empty());
        }
    }
    public record Readback(Optional<Resources> resources,Optional<Long> legitimacyRaw,Optional<Long> diplomacyXpRaw,Optional<Long> learningXpRaw,
            Optional<Long> capitalControlRaw,boolean originalCaseReadbackComplete) {
        public Readback {Objects.requireNonNull(resources);Objects.requireNonNull(legitimacyRaw);Objects.requireNonNull(diplomacyXpRaw);Objects.requireNonNull(learningXpRaw);Objects.requireNonNull(capitalControlRaw);
            StrictJson.require(resources.isPresent()&&legitimacyRaw.isEmpty()&&diplomacyXpRaw.isEmpty()&&learningXpRaw.isEmpty()&&capitalControlRaw.isEmpty()&&!originalCaseReadbackComplete,"Only four typed raw resource fields are qualified; others remain null and whole case incomplete");}
        static Readback decode(JsonNode node)throws IOException {
            var r=StrictJson.object(node,Set.of("resources","legitimacy_raw","diplomacy_xp_raw","learning_xp_raw","capital_control_raw","original_case_readback_complete"));
            return new Readback(r.get("resources").isNull()?Optional.empty():Optional.of(Resources.decode(r.get("resources"))),CurrentLyd.rawOptional(r.get("legitimacy_raw")),CurrentLyd.rawOptional(r.get("diplomacy_xp_raw")),CurrentLyd.rawOptional(r.get("learning_xp_raw")),CurrentLyd.rawOptional(r.get("capital_control_raw")),CurrentLyd.bool(r,"original_case_readback_complete"));
        }
    }
    private final CurrentLyd.Kind kind;
    private final Optional<Decisions> decisions;
    private final Optional<Events> events;
    private final Optional<Personal> personal;
    private final Optional<Readback> readback;
    private final ObjectNode validatedSource;
    private CurrentLydSource(CurrentLyd.Kind kind,Optional<Decisions> decisions,Optional<Events> events,Optional<Personal> personal,Optional<Readback> readback,ObjectNode original){
        this.kind=kind;this.decisions=decisions;this.events=events;this.personal=personal;this.readback=readback;this.validatedSource=original.deepCopy();
    }
    public CurrentLyd.Kind kind(){return kind;}public Optional<Decisions> decisions(){return decisions;}public Optional<Events> events(){return events;}public Optional<Personal> personal(){return personal;}public Optional<Readback> readback(){return readback;}
    static CurrentLydSource decode(JsonNode node)throws IOException {
        var r=StrictJson.object(node,Set.of("schema","kind","decisions","events","personal","readback"));
        if(!NativeWire.text(r.get("schema")).equals(CurrentLyd.SOURCE_SCHEMA))throw new IOException("Exact LYD Source schema required");
        var kind=CurrentLyd.Kind.parse(NativeWire.text(r.get("kind")));int present=0;
        for(var k:CurrentLyd.Kind.values())if(!r.get(k.wire()).isNull()){present++;if(k!=kind)throw new IOException("LYD branch does not match kind");}
        if(present!=1)throw new IOException("Exactly one LYD branch required");
        return new CurrentLydSource(kind,kind==CurrentLyd.Kind.DECISIONS?Optional.of(Decisions.decode(r.get("decisions"))):Optional.empty(),
                kind==CurrentLyd.Kind.EVENTS?Optional.of(Events.decode(r.get("events"))):Optional.empty(),
                kind==CurrentLyd.Kind.PERSONAL?Optional.of(Personal.decode(r.get("personal"))):Optional.empty(),
                kind==CurrentLyd.Kind.READBACK?Optional.of(Readback.decode(r.get("readback"))):Optional.empty(),r);
    }
    /** A fresh deep copy of the fully typed/exact-key-validated source; never returns a mutable internal node. */
    public ObjectNode encode(){return validatedSource.deepCopy();}
    /** Necessary public-shape conditions only, never authorization to invoke an action. */
    boolean admitsResult(CurrentLyd.Action action,Optional<CurrentLyd.DecisionKey> decision,Optional<CurrentLyd.PersonalKey> target,
            Optional<CurrentLyd.EventRole> role,Optional<Integer> instance,int actualActor){
        if(kind!=action.kind())return false;
        return switch(action){
            case OPEN_LIST->decisions.orElseThrow().openListAdmissible();
            case OPEN_DETAIL->decision.isPresent()&&decisions.orElseThrow().rows().stream().anyMatch(r->r.decisionKey()==decision.orElseThrow()&&r.canOpenDetail());
            case CONFIRM_DECISION->decision.isPresent()&&decision.orElseThrow()!=CurrentLyd.DecisionKey.BEGIN_READONLY&&decisions.orElseThrow().selectedDecisionKey().equals(decision)&&decisions.orElseThrow().confirmAdmissible();
            case CHOOSE_KNOWN_EVENT_OPTION->instance.isPresent()&&role.isPresent()&&events.orElseThrow().events().stream().anyMatch(r->r.instanceId()==instance.orElseThrow()&&r.recipientCharacterId()==actualActor&&r.namedRootBound()&&r.windowVisible()&&r.windowEnabled()&&r.options().stream().anyMatch(o->o.permittedRole().equals(role)&&o.nativeCanSelect()));
            case OPEN_PERSONAL->personal.orElseThrow().openAdmissible();
            case START_ADD_PERSONAL->personal.orElseThrow().startAddAdmissible();
            case SELECT_PERSONAL_CANDIDATE->target.isPresent()&&personal.orElseThrow().rows().stream().anyMatch(r->r.definitionKey().equals(target.orElseThrow().wire())&&r.selectAdmissible());
            case CONFIRM_PERSONAL_ADD->target.isPresent()&&personal.orElseThrow().addModal().personalKey().equals(target)&&personal.orElseThrow().addModal().acceptAdmissible();
            default->false;
        };
    }
    @Override public boolean equals(Object other){return other instanceof CurrentLydSource s&&kind==s.kind&&decisions.equals(s.decisions)&&events.equals(s.events)&&personal.equals(s.personal)&&readback.equals(s.readback);}
    @Override public int hashCode(){return Objects.hash(kind,decisions,events,personal,readback);}
    private static JsonNode array(ObjectNode r,String k,int max)throws IOException{var n=r.get(k);if(!n.isArray()||n.size()>max)throw new IOException("Actual bounded LYD array required: "+k);return n;}
    static Optional<CurrentLyd.DecisionKey> decision(JsonNode n)throws IOException{return n.isNull()?Optional.empty():Optional.of(CurrentLyd.DecisionKey.parse(NativeWire.text(n)));}
    static Optional<CurrentLyd.PersonalKey> personalKey(JsonNode n)throws IOException{return n.isNull()?Optional.empty():Optional.of(CurrentLyd.PersonalKey.parse(NativeWire.text(n)));}
    static Optional<CurrentLyd.EventRole> role(JsonNode n)throws IOException{return n.isNull()?Optional.empty():Optional.of(CurrentLyd.EventRole.parse(NativeWire.text(n)));}
}
