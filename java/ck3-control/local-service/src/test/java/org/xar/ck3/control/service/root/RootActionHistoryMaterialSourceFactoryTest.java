package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.Recording;
import org.xar.ck3.control.contracts.ExactRef;

/** Original recorder parity, not a synthetic Root/Managed qualification fixture. */
class RootActionHistoryMaterialSourceFactoryTest {
    @Test void returnedOriginalDoesNotBecomeAnAppliedOrAcceptedAlias(){
        // These are actual original execute_step result shapes: no accepted field for mercenary results,
        // and the gift compatible result can retain its query step rather than the submitting operation.
        Obj mercenaries=new Obj(Map.of("status",new Text("hired"),"mercenary_company_id",number(9)));
        assertEquals(Recording.RETURNED,record("hire-mercenary-company-9",mercenaries));
        Obj gift=new Obj(Map.of("step",new Text("query-faction-member-gift-v1"),"status",new Text("observed")));
        assertEquals(Recording.RETURNED,record("send-faction-gift-9",gift));
        Obj submitted=new Obj(Map.of("marriage_result",new Obj(Map.of("status",new Text("proposal_submitted")))));
        assertEquals(Recording.RETURNED,record("arrange-marriage-707-809",submitted));
        assertEquals(Recording.RETURNED,record("enforce-demands-9",new Obj(Map.of("accepted",new Bool(false),"status",new Text("pending")))));
    }
    @Test void sourceBoundOverviewAndOriginalExceptionalReturnsUseTheirActualAcceptedField(){
        Obj rejected=new Obj(Map.of("accepted",new Bool(false)));
        assertEquals(Recording.ACCEPTED_RETURN,record("query-war-declared-overview-v1",rejected));
        assertEquals(Recording.ACCEPTED_RETURN,record("close-war-declared-overview-v1",rejected));
        Obj moved=new Obj(Map.of("accepted",new Bool(false),"status",new Text("observed_after_native_error"),"native_ack_verified",new Bool(false)));
        assertEquals(Recording.ACCEPTED_RETURN,record("move-army-0-to-42",moved));
        assertEquals(Recording.RETURNED,record("move-army-0-to-42",moved.with("native_ack_verified",new Bool(true))));
        assertEquals(Recording.RETURNED,record("move-army-00-to-42",moved));
        assertEquals(Recording.RETURNED,record("move-army-0-to-2147483648",moved));
        List<String> operations=List.of("query-route-contact-horizon-v1-0-to-42-h-2-8-9","query-war-termination-options-9","query-battle-control-snapshot-v1-0");
        List<String> schemas=List.of("xar.route-contact-readonly-unavailable.v1","xar.war-termination-readonly-unavailable/v1","xar.battle-control-readonly-unavailable.v1");
        for(int index=0;index<operations.size();index++){
            Obj unavailable=new Obj(Map.of("schema",new Text(schemas.get(index)),"status",new Text("unavailable"),"accepted",new Bool(false)));
            assertEquals(Recording.ACCEPTED_RETURN,record(operations.get(index),unavailable));
            assertEquals(Recording.RETURNED,record(operations.get(index),unavailable.with("status",new Text("available"))));
            assertEquals(Recording.RETURNED,record("unrelated-operation",unavailable));
        }
        assertThrows(IllegalArgumentException.class,()->record("close-war-declared-overview-v1",new Obj(Map.of("accepted",number(1)))));
    }
    @Test void samplingSetOriginalRecorderUsesTypedAcceptedRatherThanReturnedSuccess(){
        for(String step:List.of("enable-army-observer-research-sampling-v1","disable-army-observer-research-sampling-v1")) {
            assertEquals(Recording.ACCEPTED_RETURN,record(step,new Obj(Map.of("accepted",new Bool(true)))));
            assertEquals(Recording.ACCEPTED_RETURN,record(step,new Obj(Map.of("accepted",new Bool(false),"status",new Text("incomplete")))));
            assertThrows(IllegalArgumentException.class,()->record(step,new Obj(Map.of("accepted",number(1)))));
        }
    }
    @Test void originalPolicyRolesCannotBeSubstitutedOrSilentlyRebased(){
        var driver=ref("native_driver.py",1658471,"eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603");
        var overview=ref("war_declared_overview_contract.py",11073,"86ebfb0fc5ba6a0150f28c8ac4aeceb3c65116b03d0f5175a99fc9659377ece0");
        var war=ref("war_contract.py",241556,"b1b14953f01d66c9f6720e4c92cb6b30c26eb1946b20e9b4ba932c9b5e1f7937");
        var battle=ref("battle_control_contract.py",91388,"2a5509214b8c0187bb0799a4fc10728d7ea7b7954a525af977d768de0528c3de");
        assertEquals(List.of(driver,overview,war,battle,RootFamilySendRecordingMaterial.originalContract(driver),RootActionHistoryMaterialSourceFactory.samplingOriginal(driver),RootActionHistoryMaterialSourceFactory.guiServiceOriginal(driver),RootActionHistoryMaterialSourceFactory.guiCameraOriginal(driver),RootActionHistoryMaterialSourceFactory.pilgrimageOriginal(driver),RootActionHistoryMaterialSourceFactory.closeOriginal(driver),RootActionHistoryMaterialSourceFactory.giftOriginal(driver)),new RootActionHistoryMaterialSourceFactory.RecordingPolicySources(driver,overview,war,battle).originals());
        assertThrows(IllegalArgumentException.class,()->new RootActionHistoryMaterialSourceFactory.RecordingPolicySources(overview,driver,war,battle));
        assertThrows(IllegalArgumentException.class,()->new RootActionHistoryMaterialSourceFactory.RecordingPolicySources(ref("native_driver.py",1658471,"0".repeat(64)),overview,war,battle));
    }
    private static Recording record(String step,Obj result){return RootActionHistoryMaterialSourceFactory.recording(new OperationKey(step),result);}
    private static IntegerValue number(long number){return new IntegerValue(java.math.BigInteger.valueOf(number));}
    private static ExactRef ref(String name,long bytes,String sha){return new ExactRef("D:/source-data-only/"+name,bytes,sha);}
}
