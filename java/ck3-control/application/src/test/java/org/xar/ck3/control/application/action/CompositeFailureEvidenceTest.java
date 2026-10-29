package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.advance.GenericPublicPauseRecovery;
import org.xar.ck3.control.application.effects.control.ControlSequenceObservation;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Software DATA exercises the actual shared receipt writer/reader. It does not mint a Root or native authority. */
final class CompositeFailureEvidenceTest {
    private static final Instant T=Instant.parse("2026-10-24T12:00:00Z");
    private static ExactRef ref(String value){byte[] b=value.getBytes(StandardCharsets.UTF_8);return new ExactRef("software/"+ActionCodec.sha256(b),b.length,ActionCodec.sha256(b));}
    private static RawJson raw(String text){return new RawJson(text.getBytes(StandardCharsets.UTF_8));}
    private static ActionCommand parent(){
        var identity=new ObservationIdentity("pause-codec-software",new GameGeneration(12,new PythonOnlyUInt64(BigInteger.ONE)),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE,BigInteger.ONE,BigInteger.valueOf(1000)),
                        "software-native",BigInteger.ONE,"software-episode"),1);
        var source=new G2Source(identity.machineId(),T.toString(),"1.20.0.4",ref("source"));
        return new ActionCommand("software-pause-parent",identity,source,"software-session",ControlSequenceObservation.OPERATION,new Obj(Map.of()),
                GenericPublicPauseRecovery.expected(identity,source),new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),T.plusSeconds(30));
    }
    private static CompositeExecution execution(ActionCommand parent){
        var guard=new GuardEvidence(parent.before(),parent.source(),parent.sessionId(),BigInteger.ONE,parent.operation(),
                ref("native"),ref("hello"),"software-no-qualification",T,T.plusSeconds(30));
        return new CompositeExecution("software-parent-handler",T,guard,List.of(new CompositeExecution.Child("software-child","a".repeat(64))));
    }
    private static ActionReceipt receipt(List<ExactRef> evidence){
        var parent=parent();var execution=execution(parent);
        return new ActionReceipt(1,3,parent,ActionCodec.bodySha256(parent),new ActionState.CompositeSettled(execution,
                new ActionState.CompositeRejected("native pause-map recovery stopped: no fresh semantic frame after rejected pause",execution.children(),evidence)));
    }
    @Test void actualReceiptCodecPreservesNewFailureOriginalAndRefusesMissingOrChangedMaterial(){
        var archive=new Archive();var proof=archive.preserveMaterial(raw("{\"actual\":\"original failure report\"}"));
        var original=receipt(List.of(proof));byte[] bytes=ActionReceiptCodec.encodeReceipt(original,archive);
        assertEquals(ActionReceiptCodec.COMPOSITE_FAILURE_EVIDENCE_SCHEMA,StrictJson.parse(bytes).get("schema").textValue());
        assertEquals(original,ActionReceiptCodec.decodeReceipt(bytes,archive));
        assertEquals(List.of(proof),ActionEffects.supportingEvidence(((ActionState.CompositeSettled)original.state()).settlement()));
        archive.materials.remove(proof);assertThrows(NoSuchElementException.class,()->ActionReceiptCodec.decodeReceipt(bytes,archive));
        archive.materials.put(proof,raw("{\"actual\":\"altered failure report\"}"));
        assertThrows(IllegalArgumentException.class,()->ActionReceiptCodec.decodeReceipt(bytes,archive));
    }
    @Test void historicalEmptyEvidenceRetainsItsOriginalSchemaAndStrictNewVersionCannotHideFields(){
        var archive=new Archive();var legacy=receipt(List.of());byte[] before=ActionReceiptCodec.encodeReceipt(legacy,archive);
        assertEquals(ActionReceiptCodec.EVOLVED_SCHEMA,StrictJson.parse(before).get("schema").textValue());
        assertEquals(legacy,ActionReceiptCodec.decodeReceipt(before,archive));
        assertArrayEquals(before,ActionReceiptCodec.encodeReceipt(ActionReceiptCodec.decodeReceipt(before,archive),archive));
        var proof=archive.preserveMaterial(raw("{\"report\":true}"));byte[] modern=ActionReceiptCodec.encodeReceipt(receipt(List.of(proof)),archive);
        var row=(ObjectNode)StrictJson.parse(modern);row.put("schema",ActionReceiptCodec.EVOLVED_SCHEMA);
        assertThrows(IllegalArgumentException.class,()->ActionReceiptCodec.decodeReceipt(StrictJson.canonical(row),archive));
        var missing=(ObjectNode)StrictJson.parse(modern);((ObjectNode)missing.get("state").get("settlement")).remove("evidence");
        assertThrows(IllegalArgumentException.class,()->ActionReceiptCodec.decodeReceipt(StrictJson.canonical(missing),archive));
        for(var wrong:List.of(StrictJson.object(),StrictJson.object().nullNode(),StrictJson.object().textNode("bad"))){
            var changed=(ObjectNode)StrictJson.parse(modern);((ObjectNode)changed.get("state").get("settlement")).set("evidence",wrong);
            assertThrows(IllegalArgumentException.class,()->ActionReceiptCodec.decodeReceipt(StrictJson.canonical(changed),archive));
        }
    }
    @Test void sourceResultAndSettlementCopyUniqueEvidenceAndKeepOldTwoArgumentCompatibility(){
        var children=execution(parent()).children();var original=new ArrayList<ExactRef>();original.add(ref("report"));
        var observed=new ActionPorts.CompositeRejectionObserved("known native rejection",children,original);
        var settled=new ActionState.CompositeRejected(observed.reason(),observed.children(),observed.evidence());
        original.clear();assertEquals(1,settled.evidence().size());
        assertThrows(UnsupportedOperationException.class,()->settled.evidence().clear());
        assertTrue(new ActionPorts.CompositeRejectionObserved("legacy",children).evidence().isEmpty());
        assertTrue(new ActionState.CompositeRejected("legacy",children).evidence().isEmpty());
        assertThrows(IllegalArgumentException.class,()->new ActionState.CompositeRejected("bad",children,List.of(ref("x"),ref("x"))));
        assertThrows(NullPointerException.class,()->new ActionState.CompositeRejected("bad",children,null));
        var value=receipt(settled.evidence());assertFalse(value.visibleGameplay());assertFalse(value.eligibleAdvance());
        assertEquals(ActionReceipt.Outcome.REJECTED_CONFIRMED,value.outcome());
    }
    @Test void failureProofCannotBeReusedByAnUnrelatedCompositeOperation(){
        var parent=parent();var execution=execution(parent);var failure=new ActionState.CompositeRejected("known negative",execution.children(),List.of(ref("report")));
        ActionEffects.validateComposite(parent,execution,failure);
        var unrelated=new ActionCommand(parent.actionId(),parent.origin(),parent.source(),parent.sessionId(),new OperationKey("unrelated-parent"),
                parent.arguments(),parent.expectation(),parent.claims(),parent.deadline());
        assertThrows(IllegalArgumentException.class,()->ActionEffects.validateComposite(unrelated,execution,failure));
    }
    private static final class Archive implements ActionPorts.OutcomeArchive {
        final Map<ExactRef,RawJson> materials=new HashMap<>();
        public ExactRef preserveMaterial(RawJson value){var ref=new ExactRef("software/material/"+ActionCodec.sha256(value.bytes()),value.bytes().length,ActionCodec.sha256(value.bytes()));materials.put(ref,value);return ref;}
        public RawJson loadMaterial(ExactRef ref){return Optional.ofNullable(materials.get(ref)).orElseThrow();}
        public RawJson loadFullMaterial(ExactRef ref){return loadMaterial(ref);}
        public ExactRef materialReferenceOf(RawJson value){return materials.entrySet().stream().filter(e->e.getValue().equals(value)).map(Map.Entry::getKey).findFirst().orElseThrow();}
        public ExactRef preserve(NativeActionPort.DispatchOutcome value){throw unused();}
        public NativeActionPort.DispatchOutcome load(ExactRef ref){throw unused();}
        public ExactRef preserveRequest(NativeRequest value){throw unused();}
        public NativeRequest loadRequest(ExactRef ref){throw unused();}
        public ExactRef referenceOf(NativeActionPort.DispatchOutcome value){throw unused();}
        public ExactRef requestReferenceOf(NativeRequest value){throw unused();}
        public ExactRef preserveRead(PlanningReadReceipt value){throw unused();}
        public PlanningReadReceipt loadRead(ExactRef ref){throw unused();}
        public ExactRef readReferenceOf(PlanningReadReceipt value){throw unused();}
        public ExactRef preserveRecord(ActionRecord value){throw unused();}
        public ActionRecord loadRecord(ExactRef ref){throw unused();}
        public ExactRef recordReferenceOf(ActionRecord value){throw unused();}
        public ExactRef preserveReceipt(ActionReceipt value){throw unused();}
        public ActionReceipt loadReceipt(ExactRef ref){throw unused();}
        public ExactRef receiptReferenceOf(ActionReceipt value){throw unused();}
        public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value){throw unused();}
        public byte[] loadNativeFrame(ExactRef ref){throw unused();}
        private UnsupportedOperationException unused(){return new UnsupportedOperationException("test did not authorize physical or canonical side effects");}
    }
}
