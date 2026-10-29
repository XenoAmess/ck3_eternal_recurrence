package org.xar.ck3.control.application.battleadvance;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Invalid archive boundary cases; synthetic inputs never grant actual transport or failure qualification. */
final class ExactDayFailureBoundaryTest {
    private static ActionCommand parent(){
        var original=BattleAdvanceFixture.parent();
        var plan=new AdvancePlan(BigInteger.valueOf(100),BigInteger.valueOf(124),1,1,"fixture_exact_sentinel",true,
                AdvancePlan.ClockMode.EXACT_SENTINEL,Optional.empty());
        return new ActionCommand("exact-boundary",original.before(),original.source(),original.sessionId(),new OperationKey("life-advance-one-day"),
                new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(Map.of(AdvancePlan.KEY,plan.json())),
                new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition(1,original.before(),original.source(),AdvancePlan.OBSERVER,plan.expected()),
                original.claims(),original.deadline());
    }
    private static ObjectNode body(ActionCommand parent){
        var row=StrictJson.object();row.put("schema",ExactDayClockFailureEvidence.SCHEMA);row.put("failure_kind","STOP_NOT_OBSERVED_BEFORE_NORMAL_STATUS");
        row.put("parent_action_id",parent.actionId());row.put("parent_body_sha256",ActionCodec.bodySha256(parent));
        row.set("plan",org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(AdvancePlan.decode(parent).json()));
        for(String field:List.of("starting","last_wait","armed","cleanup_before","cleanup_status_read","cleanup_error","original_gate"))row.putNull(field);
        row.put("action_start",0);row.put("cleanup_start",0);row.putArray("children");
        row.put("normal_status_query_attempted",false);row.put("stop_validation_attempted",false);row.putNull("stopped_status");row.put("stop_credit",false);return row;
    }
    private static ActionReceipt receipt(ActionCommand parent,ExactRef material){
        var guard=new GuardEvidence(parent.before(),parent.source(),parent.sessionId(),BigInteger.ONE,parent.operation(),BattleAdvanceFixture.REF,
                BattleAdvanceFixture.REF,"fixture-unqualified-original",BattleAdvanceFixture.NOW,parent.deadline());
        var execution=new CompositeExecution(LifeAdvanceComposite.HANDLER,BattleAdvanceFixture.NOW,guard,List.of());
        return new ActionReceipt(1,100,parent,ActionCodec.bodySha256(parent),new ActionState.CompositeUnknown(execution,"reason text grants no diagnostic",List.of(material)));
    }
    private static ExactDayClockFailureEvidence reader(){
        return new ExactDayClockFailureEvidence((basis,archive)->{throw new AssertionError("invalid header must fail before any original-frame reconstruction");});
    }
    @Test void wrongBooleanTypeMissingFieldExtraFieldAndFalseStopClaimAreRejectedBeforeFrames(){
        var parent=parent();
        for(int variant=0;variant<5;variant++){
            var row=body(parent);
            if(variant==0)row.put("normal_status_query_attempted",0);
            if(variant==1)row.remove("stop_validation_attempted");
            if(variant==2)row.put("extra_alias_stop_observed",false);
            if(variant==3)row.put("stop_credit",true);
            if(variant==4)row.put("stopped_status","ARMED");
            var archive=new Materials();var ref=archive.preserveMaterial(new RawJson(StrictJson.canonical(row)));
            assertThrows(IllegalArgumentException.class,()->reader().project(receipt(parent,ref),archive));
            assertEquals(1,archive.materialLoads);
        }
    }
    @Test void originalParentBodyAndIdDriftCannotQualifyAnExactFailure(){
        var parent=parent();
        for(String field:List.of("parent_action_id","parent_body_sha256")){
            var row=body(parent);row.put(field,field.equals("parent_body_sha256")?"a".repeat(64):"another-parent");
            var archive=new Materials();var ref=archive.preserveMaterial(new RawJson(StrictJson.canonical(row)));
            assertThrows(IllegalArgumentException.class,()->reader().project(receipt(parent,ref),archive));
        }
    }
    @Test void originalMaterialBytesAndHashAreCheckedBeforeAnySchemaDispatch(){
        var parent=parent();var archive=new Materials();RawJson raw=new RawJson(StrictJson.canonical(body(parent)));
        var good=archive.preserveMaterial(raw);
        var changed=new ExactRef(good.path(),good.bytes()+1,good.sha256());archive.values.put(changed,raw);
        assertThrows(IllegalArgumentException.class,()->reader().project(receipt(parent,changed),archive));
        var digest=new ExactRef(good.path(),good.bytes(),"c".repeat(64));archive.values.put(digest,raw);
        assertThrows(IllegalArgumentException.class,()->reader().project(receipt(parent,digest),archive));
    }
    @Test void reasonTextAndUnrecognizedSchemaNeverSelectTheTypedFailureProducer(){
        var parent=parent();var archive=new Materials();
        var raw=new RawJson(("{\"schema\":\"unrelated/v1\",\"reason\":\""+ExactDayClockFailure.MESSAGE+"\"}").getBytes(StandardCharsets.UTF_8));
        var ref=archive.preserveMaterial(raw);
        assertTrue(reader().project(receipt(parent,ref),archive).isEmpty());assertEquals(1,archive.materialLoads);
    }
    private static final class Materials implements ActionPorts.OutcomeArchive {
        final Map<ExactRef,RawJson> values=new java.util.HashMap<>();int materialLoads;
        @Override public ExactRef preserveMaterial(RawJson value){ExactRef ref=materialReferenceOf(value);values.put(ref,value);return ref;}
        @Override public RawJson loadMaterial(ExactRef ref){materialLoads++;return Optional.ofNullable(values.get(ref)).orElseThrow();}
        @Override public ExactRef materialReferenceOf(RawJson value){return new ExactRef("fixture/material-"+ActionCodec.sha256(value.bytes())+".json",value.bytes().length,ActionCodec.sha256(value.bytes()));}
        private static AssertionError unexpected(){return new AssertionError("invalid boundary must not load Native, Driver, queries, child receipts or dispatches");}
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value){throw unexpected();}
        @Override public NativeActionPort.DispatchOutcome load(ExactRef ref){throw unexpected();}
        @Override public ExactRef preserveRequest(NativeRequest value){throw unexpected();}
        @Override public NativeRequest loadRequest(ExactRef ref){throw unexpected();}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value){throw unexpected();}
        @Override public ExactRef requestReferenceOf(NativeRequest value){throw unexpected();}
        @Override public ExactRef preserveRead(PlanningReadReceipt value){throw unexpected();}
        @Override public PlanningReadReceipt loadRead(ExactRef ref){throw unexpected();}
        @Override public ExactRef readReferenceOf(PlanningReadReceipt value){throw unexpected();}
        @Override public ExactRef preserveRecord(ActionRecord value){throw unexpected();}
        @Override public ActionRecord loadRecord(ExactRef ref){throw unexpected();}
        @Override public ExactRef recordReferenceOf(ActionRecord value){throw unexpected();}
        @Override public ExactRef preserveReceipt(ActionReceipt value){throw unexpected();}
        @Override public ActionReceipt loadReceipt(ExactRef ref){throw unexpected();}
        @Override public ExactRef receiptReferenceOf(ActionReceipt value){throw unexpected();}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value){throw unexpected();}
        @Override public byte[] loadNativeFrame(ExactRef ref){throw unexpected();}
    }
}
