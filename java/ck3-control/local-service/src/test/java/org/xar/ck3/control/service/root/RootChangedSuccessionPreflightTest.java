package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.util.LinkedHashMap;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Pure original-gate DATA regressions. These never construct a Managed lease or a private preflight token. */
final class RootChangedSuccessionPreflightTest {
    private static OpportunityJson.Obj frame(){return json("{\"paused\":true,\"map_ready\":true,\"one_life_terminal_reason\":\"played_character_changed\",\"snapshot_id\":\"actual-17\",\"revision\":17,\"native_revision\":31,\"date_raw\":888,\"succession_expectation\":{},\"succession_reconciliation\":null}");}
    private static OpportunityJson.Obj json(String text){return DriverJson.object(text.getBytes(java.nio.charset.StandardCharsets.UTF_8),65536);}
    private static OpportunityJson.Obj with(OpportunityJson.Obj value,String key,OpportunityJson.Value field){var fields=new LinkedHashMap<>(value.members());if(field==null)fields.remove(key);else fields.put(key,field);return new OpportunityJson.Obj(fields);}
    private static OpportunityJson.Obj binding(){return json("{\"snapshot_id\":\"actual-17\",\"revision\":17,\"native_revision\":31,\"date_raw\":888}");}
    private static OpportunityJson.Obj compared(OpportunityJson.Obj binding){return new OpportunityJson.Obj(java.util.Map.of("successor_binding",binding));}
    @Test void onlyOriginalChangedPausedMapExpectationAndAvailableRootNeedsRead(){
        var actual=frame();assertTrue(RootChangedSuccessionPreflight.needsRead(actual,true));
        assertFalse(RootChangedSuccessionPreflight.needsRead(actual,false));
        for(String key:java.util.List.of("paused","map_ready"))for(var value:java.util.List.of(new OpportunityJson.Bool(false),OpportunityJson.Nil.INSTANCE,new OpportunityJson.Text("true")))
            assertFalse(RootChangedSuccessionPreflight.needsRead(with(actual,key,value),true));
        assertFalse(RootChangedSuccessionPreflight.needsRead(with(actual,"one_life_terminal_reason",new OpportunityJson.Text("character_dead")),true));
        assertFalse(RootChangedSuccessionPreflight.needsRead(with(actual,"one_life_terminal_reason",OpportunityJson.Nil.INSTANCE),true));
        assertFalse(RootChangedSuccessionPreflight.needsRead(with(actual,"succession_expectation",OpportunityJson.Nil.INSTANCE),true));
        assertFalse(RootChangedSuccessionPreflight.needsRead(with(actual,"succession_expectation",null),true));
        assertFalse(RootChangedSuccessionPreflight.needsRead(with(actual,"revision",new OpportunityJson.Bool(true)),true));
        assertFalse(RootChangedSuccessionPreflight.needsRead(with(actual,"revision",new OpportunityJson.Text("17")),true));
    }
    @Test void currentOriginalFourFieldsSkipReadAndEveryStaleFieldRequiresIt(){
        var bound=binding();var actual=with(frame(),"succession_reconciliation",compared(bound));
        assertFalse(RootChangedSuccessionPreflight.needsRead(actual,true));
        for(String key:java.util.List.of("snapshot_id","revision","native_revision","date_raw")){
            for(OpportunityJson.Value malformed:new OpportunityJson.Value[]{null,OpportunityJson.Nil.INSTANCE,new OpportunityJson.Bool(true),new OpportunityJson.Text("different")}){
                var stale=with(actual,"succession_reconciliation",compared(with(bound,key,malformed)));
                assertTrue(RootChangedSuccessionPreflight.needsRead(stale,true),key);
            }
        }
    }
    @Test void codecRoundTripKeepsMissingNullAndIntegerBooleanDistinct(){
        var actual=with(frame(),"succession_reconciliation",compared(binding()));
        assertEquals(actual,DriverJson.object(DriverJson.encode(actual),65536));
        var absent=with(actual,"succession_reconciliation",null);var nullable=with(actual,"succession_reconciliation",OpportunityJson.Nil.INSTANCE);
        assertNotEquals(absent,nullable);assertTrue(RootChangedSuccessionPreflight.needsRead(absent,true));assertTrue(RootChangedSuccessionPreflight.needsRead(nullable,true));
        var bool=with(binding(),"revision",new OpportunityJson.Bool(true));assertFalse(RootChangedSuccessionPreflight.currentBinding(actual,compared(bool)));
    }
    @Test void freshNativeTupleMayMakeRetainedComparisonNoncurrentWithoutRewritingIt(){
        var comparison=compared(binding());var fresh=with(with(frame(),"succession_reconciliation",comparison),"snapshot_id",new OpportunityJson.Text("actual-18"));
        assertFalse(RootChangedSuccessionPreflight.currentBinding(fresh,comparison));
        assertEquals(comparison,fresh.get("succession_reconciliation"));
        // This DATA result does not authorize Continue, a second preflight, or another Native read.
    }
}
