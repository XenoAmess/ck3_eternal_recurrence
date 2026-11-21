package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Observed finite keyed census. Missing or lazy models stay explicitly unmaterialized. */
public record CurrentCuratedDecisionsSource(boolean listFound,boolean listVisible,boolean listEnabled,
        boolean detailFound,boolean detailVisible,boolean detailEnabled,boolean otherDecisionSelected,
        boolean openListAdmissible,boolean completeModelCensus,boolean blockedByVisibleModal,boolean confirmAdmissible,
        Optional<Integer> groupsCount,Optional<Integer> totalModelRows,Optional<Integer> widgetState,
        Optional<CurrentCuratedDecisions.DecisionKey> selectedDecisionKey,Optional<Boolean> nativeCanConfirm,List<Row> rows) {
    public record Row(CurrentCuratedDecisions.DecisionKey decisionKey,boolean canOpenDetail,boolean isSelected) {
        public Row{Objects.requireNonNull(decisionKey);}
    }
    public CurrentCuratedDecisionsSource {
        Objects.requireNonNull(groupsCount);Objects.requireNonNull(totalModelRows);Objects.requireNonNull(widgetState);Objects.requireNonNull(selectedDecisionKey);Objects.requireNonNull(nativeCanConfirm);rows=List.copyOf(rows);
        StrictJson.require(rows.size()<=9,"At most nine fixed curated rows");
        if(!listFound)StrictJson.require(!listVisible&&!listEnabled&&!completeModelCensus&&rows.isEmpty()&&groupsCount.isEmpty()&&totalModelRows.isEmpty(),"Absent list cannot carry a materialized census");
        if(!detailFound)StrictJson.require(!detailVisible&&!detailEnabled&&selectedDecisionKey.isEmpty()&&!otherDecisionSelected&&nativeCanConfirm.isEmpty()&&widgetState.isEmpty(),"Absent detail cannot carry its material facts");
        StrictJson.require(completeModelCensus==(groupsCount.isPresent()&&totalModelRows.isPresent()),"Complete census/count roles differ");
        if(!completeModelCensus)StrictJson.require(groupsCount.isEmpty()&&totalModelRows.isEmpty()&&rows.isEmpty(),"Unmaterialized census retains null counts and no invented rows");
        groupsCount.ifPresent(n->StrictJson.require(n>=0&&n<=64,"Actual group count out of range"));totalModelRows.ifPresent(n->StrictJson.require(n>=0&&n<=1024,"Actual total row count out of range"));
        StrictJson.require(!otherDecisionSelected||selectedDecisionKey.isEmpty(),"An unreviewed selected decision cannot masquerade as a fixed key");
        if(nativeCanConfirm.isPresent())StrictJson.require(selectedDecisionKey.isPresent()&&detailVisible,"NativeCan requires the actual visible selected fixed detail");
        if(confirmAdmissible)StrictJson.require(detailFound&&detailVisible&&detailEnabled&&!blockedByVisibleModal&&selectedDecisionKey.isPresent()&&nativeCanConfirm.orElse(false),"Confirmation lacks actual Native admission");
        if(openListAdmissible)StrictJson.require(!listVisible&&!blockedByVisibleModal,"Opening list contradicts actual visible/modal state");
        var seen=new HashSet<CurrentCuratedDecisions.DecisionKey>();
        for(var row:rows){StrictJson.require(seen.add(row.decisionKey()),"Duplicate actual curated row key");
            StrictJson.require(row.isSelected()==(detailVisible&&selectedDecisionKey.filter(row.decisionKey()::equals).isPresent()),"Selected keyed row differs from actual detail");
            if(row.canOpenDetail())StrictJson.require(listVisible&&listEnabled&&!row.isSelected()&&!blockedByVisibleModal,"Row open permission lacks actual list context");}
    }
    public boolean admits(CurrentCuratedDecisions.Action action,Optional<CurrentCuratedDecisions.DecisionKey> decision) {
        Objects.requireNonNull(action);Objects.requireNonNull(decision);
        return switch(action){case QUERY->false;case OPEN_LIST->decision.isEmpty()&&openListAdmissible;
            case OPEN_DETAIL->completeModelCensus&&decision.isPresent()&&rows.stream().anyMatch(r->r.decisionKey()==decision.orElseThrow()&&r.canOpenDetail());
            case CONFIRM->decision.isPresent()&&confirmAdmissible&&selectedDecisionKey.equals(decision);};
    }
    static CurrentCuratedDecisionsSource decode(JsonNode raw)throws IOException {
        var n=StrictJson.object(raw,Set.of("schema","list_found","list_visible","list_enabled","detail_found","detail_visible","detail_enabled","other_decision_selected","open_list_admissible","complete_model_census","blocked_by_visible_modal","confirm_admissible","groups_count","total_model_rows","widget_state","selected_decision_key","native_can_confirm","rows"));
        if(!NativeWire.text(n.get("schema")).equals(CurrentCuratedDecisions.SOURCE_SCHEMA))throw new IOException("Exact curated source schema required");
        if(!n.get("rows").isArray())throw new IOException("Actual keyed rows required");var rows=new java.util.ArrayList<Row>();
        if(n.get("rows").size()>9)throw new IOException("Too many curated rows");
        for(var rawRow:n.get("rows")){var r=StrictJson.object(rawRow,Set.of("decision_key","can_open_detail","is_selected"));rows.add(new Row(CurrentCuratedDecisions.DecisionKey.parse(NativeWire.text(r.get("decision_key"))),bool(r,"can_open_detail"),bool(r,"is_selected")));}
        Optional<Boolean> can=n.get("native_can_confirm").isNull()?Optional.empty():Optional.of(bool(n,"native_can_confirm"));
        return new CurrentCuratedDecisionsSource(bool(n,"list_found"),bool(n,"list_visible"),bool(n,"list_enabled"),bool(n,"detail_found"),bool(n,"detail_visible"),bool(n,"detail_enabled"),bool(n,"other_decision_selected"),bool(n,"open_list_admissible"),bool(n,"complete_model_census"),bool(n,"blocked_by_visible_modal"),bool(n,"confirm_admissible"),number(n,"groups_count"),number(n,"total_model_rows"),number(n,"widget_state"),n.get("selected_decision_key").isNull()?Optional.empty():Optional.of(CurrentCuratedDecisions.DecisionKey.parse(NativeWire.text(n.get("selected_decision_key")))),can,rows);
    }
    public ObjectNode encode(){var n=StrictJson.object().put("schema",CurrentCuratedDecisions.SOURCE_SCHEMA).put("list_found",listFound).put("list_visible",listVisible).put("list_enabled",listEnabled)
            .put("detail_found",detailFound).put("detail_visible",detailVisible).put("detail_enabled",detailEnabled).put("other_decision_selected",otherDecisionSelected).put("open_list_admissible",openListAdmissible)
            .put("complete_model_census",completeModelCensus).put("blocked_by_visible_modal",blockedByVisibleModal).put("confirm_admissible",confirmAdmissible);
        setNumber(n,"groups_count",groupsCount);setNumber(n,"total_model_rows",totalModelRows);setNumber(n,"widget_state",widgetState);
        if(selectedDecisionKey.isPresent())n.put("selected_decision_key",selectedDecisionKey.orElseThrow().wire());else n.putNull("selected_decision_key");
        if(nativeCanConfirm.isPresent())n.put("native_can_confirm",nativeCanConfirm.orElseThrow());else n.putNull("native_can_confirm");
        var a=n.putArray("rows");for(var r:rows)a.addObject().put("decision_key",r.decisionKey().wire()).put("can_open_detail",r.canOpenDetail()).put("is_selected",r.isSelected());return n;}
    private static Optional<Integer> number(ObjectNode n,String k)throws IOException{return n.get(k).isNull()?Optional.empty():Optional.of(NativeWire.integer(n.get(k),BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact());}
    private static void setNumber(ObjectNode n,String k,Optional<Integer> v){if(v.isPresent())n.put(k,v.orElseThrow());else n.putNull(k);}
    private static boolean bool(ObjectNode n,String k)throws IOException {var v=n.get(k);if(v==null||!v.isBoolean())throw new IOException("Actual curated bool required: "+k);return v.booleanValue();}
}
