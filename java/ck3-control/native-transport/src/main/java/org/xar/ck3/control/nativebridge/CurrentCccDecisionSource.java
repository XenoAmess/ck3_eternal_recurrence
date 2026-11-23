package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual decision/model/tooltip DATA. Unqualified expiry remains null, never inferred from a static duration. */
public record CurrentCccDecisionSource(boolean listFound,boolean listVisible,boolean listEnabled,
        boolean detailFound,boolean detailVisible,boolean detailEnabled,boolean otherDecisionSelected,
        boolean openListAdmissible,boolean completeModelCensus,boolean blockedByVisibleModal,boolean confirmAdmissible,
        boolean caseBound,Optional<List<Boolean>> corruptionTraits,Optional<Boolean> fixtureTaxVariablePresent,
        Optional<Boolean> fixtureTaxExactHalf,boolean confirmTooltipObserved,Optional<String> confirmTooltip,
        Optional<Integer> cooldownExpiryDateRaw,boolean cooldownReadbackComplete,Optional<Integer> groupsCount,
        Optional<Integer> totalModelRows,Optional<Integer> widgetState,Optional<CurrentCccDecision.DecisionKey> selectedDecisionKey,
        Optional<Boolean> nativeCanConfirm,List<Row> rows) {
    public record Row(CurrentCccDecision.DecisionKey decisionKey,boolean canOpenDetail,boolean isSelected){public Row{Objects.requireNonNull(decisionKey);}}
    public CurrentCccDecisionSource {
        Objects.requireNonNull(corruptionTraits);Objects.requireNonNull(fixtureTaxVariablePresent);Objects.requireNonNull(fixtureTaxExactHalf);Objects.requireNonNull(confirmTooltip);
        Objects.requireNonNull(cooldownExpiryDateRaw);Objects.requireNonNull(groupsCount);Objects.requireNonNull(totalModelRows);Objects.requireNonNull(widgetState);Objects.requireNonNull(selectedDecisionKey);Objects.requireNonNull(nativeCanConfirm);
        corruptionTraits=corruptionTraits.map(List::copyOf);rows=List.copyOf(rows);
        corruptionTraits.ifPresent(v->StrictJson.require(v.size()==4,"Four exact actual corruption flags in1/2/3/4 order"));
        StrictJson.require(confirmTooltipObserved==confirmTooltip.isPresent()&&cooldownExpiryDateRaw.isEmpty()&&!cooldownReadbackComplete,"Only observed tooltip is present; cooldown expiry is unqualified/null");
        confirmTooltip.ifPresent(CurrentCccDecisionSource::requireTooltip);
        if(caseBound)StrictJson.require(corruptionTraits.isPresent()&&fixtureTaxVariablePresent.isPresent(),"Case proof requires actual fixed traits and variable-presence observations");
        else StrictJson.require(corruptionTraits.isEmpty()&&fixtureTaxVariablePresent.isEmpty()&&fixtureTaxExactHalf.isEmpty(),"Unbound case cannot invent fixture expression observations");
        if(fixtureTaxVariablePresent.orElse(false))StrictJson.require(fixtureTaxExactHalf.isPresent(),"Present actual variable requires an observed exact-half predicate");
        if(fixtureTaxExactHalf.isPresent())StrictJson.require(fixtureTaxVariablePresent.orElse(false),"Exact-half observation requires actual variable presence");
        if(selectedDecisionKey.isPresent()&&detailVisible)StrictJson.require(confirmTooltipObserved,"Actual visible selected detail needs official tooltip observation");
        if(!caseBound)StrictJson.require(!confirmAdmissible&&!openListAdmissible,"Unbound case is readonly DATA");
        StrictJson.require(rows.size()<=1,"Only one fixed CCC decision row");
        if(!listFound)StrictJson.require(!listVisible&&!listEnabled&&!completeModelCensus&&rows.isEmpty()&&groupsCount.isEmpty()&&totalModelRows.isEmpty(),"Absent list cannot carry material rows/counts");
        if(!detailFound)StrictJson.require(!detailVisible&&!detailEnabled&&selectedDecisionKey.isEmpty()&&!otherDecisionSelected&&nativeCanConfirm.isEmpty()&&widgetState.isEmpty(),"Absent detail cannot carry selected material");
        StrictJson.require(completeModelCensus==(groupsCount.isPresent()&&totalModelRows.isPresent()),"Complete model/count shape differs");
        groupsCount.ifPresent(n->StrictJson.require(n>=0&&n<=64,"Actual group count bounds"));totalModelRows.ifPresent(n->StrictJson.require(n>=0&&n<=1024,"Actual full model row bounds"));
        StrictJson.require(!otherDecisionSelected||selectedDecisionKey.isEmpty(),"Other selection cannot be the fixed key");
        if(nativeCanConfirm.isPresent())StrictJson.require(selectedDecisionKey.isPresent()&&detailVisible,"NativeCan belongs to actual visible selected detail");
        if(confirmAdmissible)StrictJson.require(detailFound&&detailVisible&&detailEnabled&&!blockedByVisibleModal&&selectedDecisionKey.isPresent()&&nativeCanConfirm.orElse(false),"Confirmation implies actual native prerequisites, never reverse permission");
        if(openListAdmissible)StrictJson.require(!listVisible&&!blockedByVisibleModal,"Official open is a toggle and requires hidden list");
        for(var row:rows){
            StrictJson.require(row.isSelected()==(detailVisible&&selectedDecisionKey.filter(row.decisionKey()::equals).isPresent()),"Row/detail selected identity differs");
            if(row.canOpenDetail())StrictJson.require(caseBound&&listVisible&&listEnabled&&!row.isSelected()&&!blockedByVisibleModal,"Detail action requires exact original native case/model context");
        }
    }
    private static void requireTooltip(String value){
        StrictJson.require(value.getBytes(StandardCharsets.UTF_8).length<=16384,"Complete tooltip UTF8 bytes exceed16KiB");
        for(int i=0;i<value.length();){char c=value.charAt(i++);if(Character.isHighSurrogate(c)){StrictJson.require(i<value.length()&&Character.isLowSurrogate(value.charAt(i)),"Unpaired high surrogate");i++;}else StrictJson.require(!Character.isLowSurrogate(c),"Unpaired low surrogate");}
        // NUL, richtext and controls are real CString header.length DATA and are deliberately preserved.
    }
    public static CurrentCccDecisionSource decode(JsonNode node)throws IOException{
        try{
            var r=StrictJson.object(node,Set.of("schema","list_found","list_visible","list_enabled","detail_found","detail_visible","detail_enabled","other_decision_selected","open_list_admissible","complete_model_census","blocked_by_visible_modal","confirm_admissible","case_bound","corruption_traits","fixture_tax_variable_present","fixture_tax_exact_half","confirm_tooltip_observed","confirm_tooltip","cooldown_expiry_date_raw","cooldown_readback_complete","groups_count","total_model_rows","widget_state","selected_decision_key","native_can_confirm","rows"));
            CurrentCccActorTransition.identity(r,"schema",CurrentCccDecision.SOURCE_SCHEMA);
            Optional<List<Boolean>> traits=Optional.empty();if(!r.get("corruption_traits").isNull()){
                var a=r.get("corruption_traits");if(!a.isArray()||a.size()!=4)throw new IOException("Exactly four corruption bools required");var values=new ArrayList<Boolean>();
                for(var n:a){if(!n.isBoolean())throw new IOException("Actual corruption boolean required");values.add(n.booleanValue());}traits=Optional.of(List.copyOf(values));
            }
            var a=r.get("rows");if(!a.isArray()||a.size()>1)throw new IOException("Fixed CCC rows must be a bounded array");var rows=new ArrayList<Row>();
            for(var n:a){var row=StrictJson.object(n,Set.of("decision_key","can_open_detail","is_selected"));rows.add(new Row(CurrentCccDecision.DecisionKey.parse(NativeWire.text(row.get("decision_key"))),CurrentCccActorTransition.bool(row,"can_open_detail"),CurrentCccActorTransition.bool(row,"is_selected")));}
            Optional<String> tooltip=Optional.empty();if(!r.get("confirm_tooltip").isNull()){if(!r.get("confirm_tooltip").isTextual())throw new IOException("Actual tooltip string including empty required");tooltip=Optional.of(r.get("confirm_tooltip").textValue());}
            return new CurrentCccDecisionSource(b(r,"list_found"),b(r,"list_visible"),b(r,"list_enabled"),b(r,"detail_found"),b(r,"detail_visible"),b(r,"detail_enabled"),b(r,"other_decision_selected"),b(r,"open_list_admissible"),b(r,"complete_model_census"),b(r,"blocked_by_visible_modal"),b(r,"confirm_admissible"),b(r,"case_bound"),traits,optBool(r,"fixture_tax_variable_present"),optBool(r,"fixture_tax_exact_half"),b(r,"confirm_tooltip_observed"),tooltip,integer(r.get("cooldown_expiry_date_raw")),b(r,"cooldown_readback_complete"),integer(r.get("groups_count")),integer(r.get("total_model_rows")),integer(r.get("widget_state")),CurrentCccDecision.key(r.get("selected_decision_key")),optBool(r,"native_can_confirm"),rows);
        }catch(IllegalArgumentException|ArithmeticException invalid){throw new IOException("Invalid exact CCC decision Source DATA",invalid);}
    }
    public ObjectNode encode(){
        var r=StrictJson.object().put("schema",CurrentCccDecision.SOURCE_SCHEMA).put("list_found",listFound).put("list_visible",listVisible).put("list_enabled",listEnabled).put("detail_found",detailFound).put("detail_visible",detailVisible).put("detail_enabled",detailEnabled)
                .put("other_decision_selected",otherDecisionSelected).put("open_list_admissible",openListAdmissible).put("complete_model_census",completeModelCensus).put("blocked_by_visible_modal",blockedByVisibleModal).put("confirm_admissible",confirmAdmissible).put("case_bound",caseBound)
                .put("confirm_tooltip_observed",confirmTooltipObserved).putNull("cooldown_expiry_date_raw").put("cooldown_readback_complete",false);
        if(corruptionTraits.isPresent()){var a=r.putArray("corruption_traits");for(boolean value:corruptionTraits.orElseThrow())a.add(value);}else r.putNull("corruption_traits");
        putBool(r,"fixture_tax_variable_present",fixtureTaxVariablePresent);putBool(r,"fixture_tax_exact_half",fixtureTaxExactHalf);
        if(confirmTooltip.isPresent())r.put("confirm_tooltip",confirmTooltip.orElseThrow());else r.putNull("confirm_tooltip");
        putInt(r,"groups_count",groupsCount);putInt(r,"total_model_rows",totalModelRows);putInt(r,"widget_state",widgetState);
        if(selectedDecisionKey.isPresent())r.put("selected_decision_key",selectedDecisionKey.orElseThrow().wire());else r.putNull("selected_decision_key");putBool(r,"native_can_confirm",nativeCanConfirm);
        var a=r.putArray("rows");for(var row:rows)a.addObject().put("decision_key",row.decisionKey().wire()).put("can_open_detail",row.canOpenDetail()).put("is_selected",row.isSelected());return r;
    }
    private static boolean b(ObjectNode r,String k)throws IOException{return CurrentCccActorTransition.bool(r,k);}
    private static Optional<Boolean> optBool(ObjectNode r,String k)throws IOException{return r.get(k).isNull()?Optional.empty():Optional.of(b(r,k));}
    private static Optional<Integer> integer(JsonNode n)throws IOException{return n.isNull()?Optional.empty():Optional.of(CurrentCccActorTransition.i32(n));}
    private static void putBool(ObjectNode r,String k,Optional<Boolean> n){if(n.isPresent())r.put(k,n.orElseThrow());else r.putNull(k);}
    private static void putInt(ObjectNode r,String k,Optional<Integer> n){if(n.isPresent())r.put(k,n.orElseThrow());else r.putNull(k);}
}
