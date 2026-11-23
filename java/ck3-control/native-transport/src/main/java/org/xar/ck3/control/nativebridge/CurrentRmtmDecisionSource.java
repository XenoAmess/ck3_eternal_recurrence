package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact complete RMTM decision model DATA. This record cannot construct a private case or action preparation. */
public record CurrentRmtmDecisionSource(boolean listFound,boolean listVisible,boolean listEnabled,
        boolean detailFound,boolean detailVisible,boolean detailEnabled,boolean otherDecisionSelected,
        boolean openListAdmissible,boolean completeModelCensus,boolean blockedByVisibleModal,boolean confirmAdmissible,
        boolean caseBound,boolean confirmTooltipObserved,Optional<String> confirmTooltip,Optional<Integer> groupsCount,
        Optional<Integer> totalModelRows,Optional<Integer> widgetState,Optional<CurrentRmtmDecision.DecisionKey> selectedDecisionKey,
        Optional<Boolean> nativeCanConfirm,List<Row> rows) {
    public record Row(CurrentRmtmDecision.DecisionKey decisionKey,boolean canOpenDetail,boolean isSelected){public Row{Objects.requireNonNull(decisionKey);}}
    public CurrentRmtmDecisionSource {
        Objects.requireNonNull(confirmTooltip);Objects.requireNonNull(groupsCount);Objects.requireNonNull(totalModelRows);
        Objects.requireNonNull(widgetState);Objects.requireNonNull(selectedDecisionKey);Objects.requireNonNull(nativeCanConfirm);rows=List.copyOf(rows);
        StrictJson.require(confirmTooltipObserved==confirmTooltip.isPresent(),"Only an actual observed tooltip is present, including empty");
        confirmTooltip.ifPresent(CurrentRmtmDecisionSource::requireTooltip);
        if(selectedDecisionKey.isPresent()&&detailVisible)StrictJson.require(confirmTooltipObserved,"Visible selected detail requires official tooltip observation");
        if(!caseBound)StrictJson.require(!confirmAdmissible&&!openListAdmissible,"Unbound case is readonly DATA, not borrowed authority");
        StrictJson.require(rows.size()<=5,"Five fixed RMTM keys bound the material rows");
        if(!listFound)StrictJson.require(!listVisible&&!listEnabled&&!completeModelCensus&&rows.isEmpty()&&groupsCount.isEmpty()&&totalModelRows.isEmpty(),"Absent list cannot carry material rows/counts");
        if(!detailFound)StrictJson.require(!detailVisible&&!detailEnabled&&selectedDecisionKey.isEmpty()&&!otherDecisionSelected&&nativeCanConfirm.isEmpty()&&widgetState.isEmpty(),"Absent detail cannot carry selected material");
        StrictJson.require(completeModelCensus==(groupsCount.isPresent()&&totalModelRows.isPresent()),"Complete model/count shape differs");
        groupsCount.ifPresent(n->StrictJson.require(n>=0&&n<=64,"Actual group count bounds"));totalModelRows.ifPresent(n->StrictJson.require(n>=0&&n<=1024,"Actual full model row bounds"));
        StrictJson.require(!otherDecisionSelected||selectedDecisionKey.isEmpty(),"Other selection cannot be a known fixed key");
        if(nativeCanConfirm.isPresent())StrictJson.require(selectedDecisionKey.isPresent()&&detailVisible,"NativeCan belongs to actual visible selected detail");
        if(confirmAdmissible)StrictJson.require(detailFound&&detailVisible&&detailEnabled&&!blockedByVisibleModal&&selectedDecisionKey.isPresent()&&nativeCanConfirm.orElse(false),"Confirmation only implies actual prerequisites, never reverse permission");
        if(openListAdmissible)StrictJson.require(!listVisible&&!blockedByVisibleModal,"Official open is a toggle and requires hidden list");
        var keys=new HashSet<CurrentRmtmDecision.DecisionKey>();for(var row:rows){
            StrictJson.require(keys.add(row.decisionKey()),"Duplicate material decision row");
            StrictJson.require(row.isSelected()==(detailVisible&&selectedDecisionKey.filter(row.decisionKey()::equals).isPresent()),"Row/detail selected identity differs");
            if(row.canOpenDetail())StrictJson.require(caseBound&&listVisible&&listEnabled&&!row.isSelected()&&!blockedByVisibleModal,"Detail action requires original own RMTM case/model");
        }
    }
    private static void requireTooltip(String value){
        StrictJson.require(value.getBytes(StandardCharsets.UTF_8).length<=16384,"Complete tooltip exceeds16KiB UTF8");
        for(int i=0;i<value.length();){char c=value.charAt(i++);if(Character.isHighSurrogate(c)){StrictJson.require(i<value.length()&&Character.isLowSurrogate(value.charAt(i)),"Unpaired high surrogate");i++;}else StrictJson.require(!Character.isLowSurrogate(c),"Unpaired low surrogate");}
        // Actual CString length DATA may include NUL, controls and richtext; it is never normalized.
    }
    public static CurrentRmtmDecisionSource decode(JsonNode node)throws IOException{
        try{
            var r=StrictJson.object(node,Set.of("schema","list_found","list_visible","list_enabled","detail_found","detail_visible","detail_enabled","other_decision_selected","open_list_admissible","complete_model_census","blocked_by_visible_modal","confirm_admissible","case_bound","confirm_tooltip_observed","confirm_tooltip","groups_count","total_model_rows","widget_state","selected_decision_key","native_can_confirm","rows"));
            CurrentRmtmDecision.identity(r,"schema",CurrentRmtmDecision.SOURCE_SCHEMA);
            var a=r.get("rows");if(!a.isArray()||a.size()>5)throw new IOException("RMTM rows must be a bounded complete fixed-key array");var rows=new ArrayList<Row>();
            for(var n:a){var row=StrictJson.object(n,Set.of("decision_key","can_open_detail","is_selected"));rows.add(new Row(CurrentRmtmDecision.DecisionKey.parse(NativeWire.text(row.get("decision_key"))),b(row,"can_open_detail"),b(row,"is_selected")));}
            Optional<String> tooltip=Optional.empty();if(!r.get("confirm_tooltip").isNull()){if(!r.get("confirm_tooltip").isTextual())throw new IOException("Actual tooltip string including empty required");tooltip=Optional.of(r.get("confirm_tooltip").textValue());}
            return new CurrentRmtmDecisionSource(b(r,"list_found"),b(r,"list_visible"),b(r,"list_enabled"),b(r,"detail_found"),b(r,"detail_visible"),b(r,"detail_enabled"),b(r,"other_decision_selected"),b(r,"open_list_admissible"),b(r,"complete_model_census"),b(r,"blocked_by_visible_modal"),b(r,"confirm_admissible"),b(r,"case_bound"),b(r,"confirm_tooltip_observed"),tooltip,integer(r.get("groups_count")),integer(r.get("total_model_rows")),integer(r.get("widget_state")),CurrentRmtmDecision.key(r.get("selected_decision_key")),optBool(r,"native_can_confirm"),rows);
        }catch(IllegalArgumentException|ArithmeticException invalid){throw new IOException("Invalid exact RMTM decision Source DATA",invalid);}
    }
    public ObjectNode encode(){
        var r=StrictJson.object().put("schema",CurrentRmtmDecision.SOURCE_SCHEMA).put("list_found",listFound).put("list_visible",listVisible).put("list_enabled",listEnabled).put("detail_found",detailFound).put("detail_visible",detailVisible).put("detail_enabled",detailEnabled)
                .put("other_decision_selected",otherDecisionSelected).put("open_list_admissible",openListAdmissible).put("complete_model_census",completeModelCensus).put("blocked_by_visible_modal",blockedByVisibleModal).put("confirm_admissible",confirmAdmissible).put("case_bound",caseBound).put("confirm_tooltip_observed",confirmTooltipObserved);
        if(confirmTooltip.isPresent())r.put("confirm_tooltip",confirmTooltip.orElseThrow());else r.putNull("confirm_tooltip");
        putInt(r,"groups_count",groupsCount);putInt(r,"total_model_rows",totalModelRows);putInt(r,"widget_state",widgetState);
        if(selectedDecisionKey.isPresent())r.put("selected_decision_key",selectedDecisionKey.orElseThrow().wire());else r.putNull("selected_decision_key");putBool(r,"native_can_confirm",nativeCanConfirm);
        var a=r.putArray("rows");for(var row:rows)a.addObject().put("decision_key",row.decisionKey().wire()).put("can_open_detail",row.canOpenDetail()).put("is_selected",row.isSelected());return r;
    }
    private static boolean b(ObjectNode r,String k)throws IOException{return CurrentRmtmDecision.bool(r,k);}
    private static Optional<Boolean> optBool(ObjectNode r,String k)throws IOException{return r.get(k).isNull()?Optional.empty():Optional.of(b(r,k));}
    private static Optional<Integer> integer(JsonNode n)throws IOException{return n.isNull()?Optional.empty():Optional.of(CurrentRmtmDecision.i32(n));}
    private static void putBool(ObjectNode r,String k,Optional<Boolean> n){if(n.isPresent())r.put(k,n.orElseThrow());else r.putNull(k);}
    private static void putInt(ObjectNode r,String k,Optional<Integer> n){if(n.isPresent())r.put(k,n.orElseThrow());else r.putNull(k);}
}
