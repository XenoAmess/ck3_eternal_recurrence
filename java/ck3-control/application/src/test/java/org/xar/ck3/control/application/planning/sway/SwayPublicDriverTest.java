package org.xar.ck3.control.application.planning.sway;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.sway.SwayFormalState.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual native serializers/issued decoder/public codec/preparation, using explicit software guards and a final archive. */
final class SwayPublicDriverTest {
    private static final ExactRef SOURCE=new ExactRef("software:public-driver-source",1,"a".repeat(64)),READ=new ExactRef("software:actual-target-read",1,"b".repeat(64));
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");private static final long TARGET=50331650;
    @Test void nativeTargetProducerFlowsThroughActualIssuedFamilyPublicQuoteStartDecoderAndNativePreparation()throws Exception {
        var definitions=new SwayRootReads(new SwayRootReads.Sources(SOURCE,SOURCE,SOURCE));var catalog=new RootReadContractCatalog(List.of(),definitions.families());definitions.attach(catalog);
        var contract=definitions.target(TARGET);var receipt=receipt(contract);var typed=contract.decode(receipt);assertEquals(SwayNativeWire.TARGET+TARGET,contract.prepare(receipt.request(),receipt.requestId()).step());
        var publicQuote=SwayDriverCodec.quote(receipt,typed,READ);var args=StrictJson.object();args.set("readback",StrictJson.parse(publicQuote.bytes(),SwayNativeWire.MAX));args.put("action_id","sway-fixture-start");
        var request=SwayDriverCodec.decodeStart(raw(args));assertEquals("16786632562036001389",StrictJson.parse(publicQuote.bytes()).get("container_generation").textValue());assertEquals(request,SwayDriverCodec.decodeStart(SwayDriverCodec.encode(request)));
        var command=command(receipt,request);var archive=new Archive(receipt);var nativeRequest=SwayNativeBindings.startPreparation(archive).prepare(command);
        assertEquals(SwayNativeWire.START+TARGET,nativeRequest.step());var fields=StrictJson.parse(nativeRequest.additionalFields().bytes());assertEquals(typed.captureEpoch(),fields.get("expected_capture_epoch").bigIntegerValue());assertEquals(typed.containerGeneration(),fields.get("expected_container_generation").bigIntegerValue());assertEquals("sway-fixture-start",fields.get("action_id").textValue());
        assertEquals(StartAdmission.PUBLIC_NATIVE_FINAL,SwayNativeBindings.startAdmission(StrictJson.parse(OpportunityJson.encode(command.arguments()))));
    }
    @Test void explicitPublicFinalBranchPreservesOriginalAboveFiftyLegalAbilityWithoutRelaxingOrdinaryStart()throws Exception {
        var contract=SwayNativeBindings.target(SOURCE,TARGET);var receipt=receipt(contract);var packet=SwayNativeFormalTest.vector("query");((ObjectNode)packet.at("/result/active_scheme_sway")).put("target_opinion_of_actor",75);
        var high=SwayNativeWire.target(SwayNativeFormalTest.bytes(packet),"fixture-read",SwayNativeFormalTest.binding(73,7,53220000),TARGET);assertFalse(high.startable(true));assertTrue(startEligible(high,true,StartAdmission.PUBLIC_NATIVE_FINAL));
        byte[] highBytes=SwayNativeFormalTest.bytes(packet);var highAck=new NativeActionPort.AckReceived("fixture-read",true,Optional.of(raw((ObjectNode)packet.get("result"))),new RawJson(highBytes),highBytes);var highReceipt=new PlanningReadReceipt(receipt.request(),receipt.contractId(),receipt.requestId(),receipt.before(),receipt.after(),highAck);
        var highQuote=new SwayDriverCodec.Quote(receipt.request().before().frame().revision(),TARGET,READ,SwayDriverCodec.quote(highReceipt,high,READ));var publicCommand=command(highReceipt,new SwayDriverCodec.StartRequest(highQuote,"sway-fixture-start"));
        assertEquals(SwayNativeWire.START+TARGET,SwayNativeBindings.startPreparation(new Archive(highReceipt)).prepare(publicCommand).step());
        var ordinaryArguments=(ObjectNode)StrictJson.parse(OpportunityJson.encode(publicCommand.arguments()));ordinaryArguments.put("schema",SwayNativeBindings.START_ARGUMENTS);var ordinaryCommand=new ActionCommand(publicCommand.actionId(),publicCommand.before(),publicCommand.source(),publicCommand.sessionId(),publicCommand.operation(),OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(ordinaryArguments)),"ordinary exact source branch"),publicCommand.expected(),publicCommand.claims(),publicCommand.deadline());
        assertThrows(IllegalArgumentException.class,()->SwayNativeBindings.startPreparation(new Archive(highReceipt)).prepare(ordinaryCommand));
        assertThrows(IllegalArgumentException.class,()->reduce(seed(),new StartIntent("sway-public-high",high,MandatoryContext.CLEAR)));
        var input=new SwayTransitionCodec.Input(SOURCE,new StartIntent("sway-public-high",high,MandatoryContext.CLEAR,StartAdmission.PUBLIC_NATIVE_FINAL),new SwayTransitionCodec.Proofs(List.of(READ),Optional.empty(),Optional.of(SOURCE)));
        byte[] encoded=SwayTransitionCodec.encode(input);assertEquals(SwayTransitionCodec.PUBLIC_START_SCHEMA,StrictJson.parse(encoded,SwayFormalCodec.MAX).get("schema").textValue());var decoded=SwayTransitionCodec.decode(encoded,seed());assertEquals(input,decoded);assertEquals("sway-public-high",reduce(seed(),decoded.change()).pending().orElseThrow().actionId());
        for(var context:List.of(MandatoryContext.MANDATORY,MandatoryContext.UNAVAILABLE))assertThrows(IllegalArgumentException.class,()->reduce(seed(),new StartIntent("sway-public-high",high,context,StartAdmission.PUBLIC_NATIVE_FINAL)));
        var wrong=(ObjectNode)StrictJson.parse(encoded,SwayFormalCodec.MAX);wrong.put("schema",SwayTransitionCodec.SCHEMA);assertThrows(IllegalArgumentException.class,()->SwayTransitionCodec.decode(SwayNativeFormalTest.bytes(wrong),seed()));
        var ordinary=new SwayTransitionCodec.Input(SOURCE,new StartIntent("sway-ordinary",contract.decode(receipt),MandatoryContext.CLEAR),input.proofs());assertEquals(SwayTransitionCodec.SCHEMA,StrictJson.parse(SwayTransitionCodec.encode(ordinary),SwayFormalCodec.MAX).get("schema").textValue());assertEquals(ordinary,SwayTransitionCodec.decode(SwayTransitionCodec.encode(ordinary),seed()));
    }
    @Test void actualAckRemainsPendingThroughPublicFormatterAndUnknownNeverInventsAnAck()throws Exception {
        var original=receipt(SwayNativeBindings.target(SOURCE,TARGET));var typed=SwayNativeBindings.target(SOURCE,TARGET).decode(original);var quote=SwayDriverCodec.quote(original,typed,READ);var args=StrictJson.object();args.set("readback",StrictJson.parse(quote.bytes(),SwayNativeWire.MAX));args.put("action_id","sway-fixture-start");var request=SwayDriverCodec.decodeStart(raw(args));var command=command(original,request);var archive=new Archive(original);
        var packet=SwayNativeFormalTest.vector("submit");byte[] bytes=SwayNativeFormalTest.bytes(packet);var dispatch=new NativeActionPort.AckReceived("fixture-submit",true,Optional.of(raw((ObjectNode)packet.get("result"))),new RawJson(bytes),bytes);var attempt=new ActionState.Attempt("fixture-submit",NOW,original.before().binding(),SwayNativeBindings.startPreparation(archive).prepare(command));
        var ackReceipt=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.AckReceived(attempt,dispatch));var publicAck=StrictJson.parse(SwayDriverCodec.startResult(ackReceipt,archive).bytes());assertEquals("submitted_verification_pending",publicAck.get("stage").textValue());assertFalse(publicAck.get("canonical_postcondition_verified").booleanValue());assertEquals("41",publicAck.get("pre_capture_epoch").textValue());assertFalse(ackReceipt.eligibleAdvance());
        var unknown=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Unknown(Optional.of(attempt),Optional.empty(),"software lost original ACK",List.of()));var result=StrictJson.parse(SwayDriverCodec.startResult(unknown,archive).bytes());assertEquals("submission_unresolved",result.get("stage").textValue());assertFalse(result.has("submit_call_count"));assertTrue(SwayDriverCodec.ack(unknown,typed).isEmpty());
        var wrongControl=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Settled(attempt,dispatch,new ActionState.ControlApplied(original,"software:unrelated-control",List.of(new ExpectedBoolean(new FieldKey("control_verified"),true)))));
        assertThrows(IllegalArgumentException.class,()->SwayDriverCodec.startResult(wrongControl,archive));
    }
    @Test void strictPublicRequestTypesRejectMissingNullBoolFloatsUnsafeValuesAndExtraFields()throws Exception {
        for(String value:List.of("null","true","1.0","9007199254740993","\"01\"","\"18446744073709551616\"","\"1\n\"")) {
            assertThrows(IllegalArgumentException.class,()->SwayDriverCodec.decodeTarget(text("{\"expected_revision\":"+value+",\"target_character_id\":50331650}")));
            assertThrows(IllegalArgumentException.class,()->SwayDriverCodec.decodeReceipt(text("{\"expected_revision\":8,\"target_character_id\":50331650,\"action_id\":\"sway-fixture-start\",\"pre_capture_epoch\":"+value+"}")));
        }
        var target=new SwayDriverCodec.TargetRequest(StrictJson.UINT64_MAX,0xffff_ffffL);assertEquals(target,SwayDriverCodec.decodeTarget(SwayDriverCodec.encode(target)));
        var receipt=new SwayDriverCodec.ReceiptRequest(StrictJson.UINT64_MAX,TARGET,"sway-fixture-start",StrictJson.UINT64_MAX);assertEquals(receipt,SwayDriverCodec.decodeReceipt(SwayDriverCodec.encode(receipt)));
        assertThrows(IllegalArgumentException.class,()->SwayDriverCodec.decodeStart(text("{\"readback\":null,\"action_id\":\"sway-fixture-start\"}")));
        assertThrows(IllegalArgumentException.class,()->SwayDriverCodec.decodeTarget(text("{\"expected_revision\":8,\"target_character_id\":50331650,\"action_id\":\"forged\"}")));
        var nativeRead=receipt(SwayNativeBindings.target(SOURCE,TARGET));var quote=SwayDriverCodec.quote(nativeRead,SwayNativeBindings.target(SOURCE,TARGET).decode(nativeRead),READ);var args=StrictJson.object();args.set("readback",StrictJson.parse(quote.bytes(),SwayNativeWire.MAX));args.put("action_id","sway-fixture-start");
        for(String defect:List.of("missing-original","bool-epoch","bad-instance","wrong-build","extra-readback")) {
            var wrong=args.deepCopy();var value=(ObjectNode)wrong.get("readback");switch(defect){case "missing-original"->value.remove("java_original_target_read");case "bool-epoch"->value.put("capture_epoch",true);case "bad-instance"->value.putArray("active_sway_instances").addObject().put("scheme_instance_id",true);case "wrong-build"->value.put("exact_ck3_build","1.20.0.3");case "extra-readback"->value.put("alias",true);default->throw new AssertionError(defect);}
            assertThrows(IllegalArgumentException.class,()->SwayDriverCodec.decodeStart(raw(wrong)),defect);
        }
    }
    @Test void originalQuoteCommandBindingRejectsCallerIdCollisionDifferentQuoteAndSourceFrame()throws Exception {
        var original=receipt(SwayNativeBindings.target(SOURCE,TARGET));var value=SwayNativeBindings.target(SOURCE,TARGET).decode(original);var quote=new SwayDriverCodec.Quote(original.request().before().frame().revision(),TARGET,READ,SwayDriverCodec.quote(original,value,READ));var request=new SwayDriverCodec.StartRequest(quote,"sway-fixture-start");var command=command(original,request);var canonical=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.IntentDurable());var archive=new Archive(original);
        SwaySelectedStart.requireOriginalCommand(canonical,request,archive);
        assertThrows(IllegalArgumentException.class,()->SwaySelectedStart.requireOriginalCommand(canonical,new SwayDriverCodec.StartRequest(quote,"sway-other-id"),archive));
        var changed=new SwayDriverCodec.Quote(quote.expectedRevision(),TARGET,new ExactRef("software:different-quote",1,"c".repeat(64)),quote.presentation());assertThrows(IllegalArgumentException.class,()->SwaySelectedStart.requireOriginalCommand(canonical,new SwayDriverCodec.StartRequest(changed,request.actionId()),archive));
        var foreign=SwayNativeFormalTest.binding(99,7,53220000).before();var wrongExpected=new ExpectedPostcondition(1,foreign,command.source(),SwayActionLifecycle.START_OBSERVER,command.expected().values());
        var wrong=new ActionCommand(command.actionId(),foreign,command.source(),command.sessionId(),command.operation(),command.arguments(),wrongExpected,command.claims(),command.deadline());
        assertThrows(IllegalArgumentException.class,()->SwayNativeBindings.startPreparation(archive).prepare(wrong));
    }
    @Test void publicPendingRoundtripRetainsOriginalUnknownIdentityAcrossIndependentNewGameObservation()throws Exception {
        var packet=SwayNativeFormalTest.vector("query");var body=(ObjectNode)packet.at("/result/active_scheme_sway");body.put("target_opinion_of_actor",75);var original=SwayNativeWire.target(SwayNativeFormalTest.bytes(packet),"fixture-read",SwayNativeFormalTest.binding(73,7,53220000),TARGET);
        var pending=reduce(seed(),new StartIntent("sway-public-unknown",original,MandatoryContext.CLEAR,StartAdmission.PUBLIC_NATIVE_FINAL));var retained=SwayFormalCodec.decode(SwayFormalCodec.encode(pending));assertEquals(original,retained.pending().orElseThrow().original());assertTrue(retained.pending().orElseThrow().acknowledgement().isEmpty());
        var restored=SwayNativeFormalTest.binding(99,1,53220024);body.put("snapshot_revision",1);body.put("date_raw",53220024);body.put("capture_epoch",1);body.put("active_scheme_count",1);body.put("matching_sway_active",true);body.put("native_complete_can_send",false);body.put("native_legal_now",false);body.putArray("active_sway_instances").addObject().put("scheme_instance_id",1).put("scheme_instance_generation",0).put("target_character_id",TARGET).put("progress",1).put("progress_goal",355).put("is_exposed",false).put("is_frozen",false);
        var actual=SwayNativeWire.target(SwayNativeFormalTest.bytes(packet),"fixture-read",restored,TARGET);var recovered=reduce(retained,new Recovered(actual));assertEquals("sway-public-unknown",recovered.resolved().orElseThrow().identity().actionId());assertEquals(Optional.of(original),recovered.resolved().orElseThrow().originalIntent());assertTrue(recovered.resolved().orElseThrow().nativeReceipt().isEmpty());assertArrayEquals(SwayFormalCodec.encode(recovered),SwayFormalCodec.encode(SwayFormalCodec.decode(SwayFormalCodec.encode(recovered))));
        // This pure reducer vector grants no restoration or canonical ActionJournal settlement; the whole Root helper owns that acceptance.
    }
    private static Ledger seed(){return new Ledger("xenoamess-full-tower-eb9d2c1186","episode:synthetic",Optional.empty(),Optional.empty(),List.of(),Optional.empty(),SOURCE);}
    private static ActionCommand command(PlanningReadReceipt original,SwayDriverCodec.StartRequest request) {
        var fields=StrictJson.object();fields.put("schema",SwayNativeBindings.PUBLIC_START_ARGUMENTS);fields.put("target_character_id",TARGET);fields.set("original_target_read",READ.toJson());var before=original.request().before();
        var expected=new ExpectedPostcondition(1,before,original.request().source(),SwayActionLifecycle.START_OBSERVER,List.of(new ExpectedBoolean(new FieldKey("sway.exact_active_observed"),true)));
        return new ActionCommand(request.actionId(),before,original.request().source(),original.request().sessionId(),new OperationKey(SwayNativeWire.START+TARGET),OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(fields)),"software public Start"),expected,new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),NOW.plusSeconds(30));
    }
    private static PlanningReadReceipt receipt(ReadContract<?> contract)throws Exception {
        var bound=SwayNativeFormalTest.binding(73,7,53220000);var source=new G2Source(bound.before().machineId(),NOW.toString(),SwayNativeWire.BUILD,SOURCE);var args=StrictJson.object();args.put("target_character_id",TARGET);
        var request=new PlanningReadRequest(bound.before(),source,bound.sessionId(),contract.operation(),OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(args)),"software target"),NOW.plusSeconds(30));var evidence=new GuardEvidence(bound.before(),source,bound.sessionId(),bound.connectionGeneration(),contract.operation(),SOURCE,SOURCE,bound.authorityId(),NOW,NOW.plusSeconds(30));var guard=new PlanningReadGuard(evidence,true,true,true,"c".repeat(64));var packet=SwayNativeFormalTest.vector("query");byte[] bytes=SwayNativeFormalTest.bytes(packet);var ack=new NativeActionPort.AckReceived("fixture-read",true,Optional.of(raw((ObjectNode)packet.get("result"))),new RawJson(bytes),bytes);return new PlanningReadReceipt(request,contract.contractId(),"fixture-read",guard,guard,ack);
    }
    private static RawJson raw(ObjectNode value){return new RawJson(StrictJson.canonical(value,SwayNativeWire.MAX));}
    private static RawJson text(String value){return new RawJson(value.getBytes(java.nio.charset.StandardCharsets.UTF_8));}
    /** A final read-only archive seam. Every unrequested operation fails; it grants no Root/file/source qualification. */
    private static final class Archive implements ActionPorts.OutcomeArchive {
        private final PlanningReadReceipt original;Archive(PlanningReadReceipt original){this.original=original;}
        @Override public PlanningReadReceipt loadRead(ExactRef ref){assertEquals(READ,ref);return original;}
        @Override public ExactRef readReferenceOf(PlanningReadReceipt read){assertEquals(original,read);return READ;}
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value){throw new AssertionError();}
        @Override public NativeActionPort.DispatchOutcome load(ExactRef ref){throw new AssertionError();}
        @Override public ExactRef preserveRequest(NativeRequest value){throw new AssertionError();}
        @Override public NativeRequest loadRequest(ExactRef ref){throw new AssertionError();}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value){throw new AssertionError();}
        @Override public ExactRef requestReferenceOf(NativeRequest value){throw new AssertionError();}
        @Override public ExactRef preserveRead(PlanningReadReceipt value){throw new AssertionError();}
        @Override public ExactRef preserveRecord(ActionRecord value){throw new AssertionError();}
        @Override public ActionRecord loadRecord(ExactRef ref){throw new AssertionError();}
        @Override public ExactRef recordReferenceOf(ActionRecord value){throw new AssertionError();}
        @Override public ExactRef preserveReceipt(ActionReceipt value){throw new AssertionError();}
        @Override public ActionReceipt loadReceipt(ExactRef ref){throw new AssertionError();}
        @Override public ExactRef receiptReferenceOf(ActionReceipt value){throw new AssertionError();}
        @Override public ExactRef preserveMaterial(RawJson value){throw new AssertionError();}
        @Override public RawJson loadMaterial(ExactRef ref){throw new AssertionError();}
        @Override public ExactRef materialReferenceOf(RawJson value){throw new AssertionError();}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value){throw new AssertionError();}
        @Override public byte[] loadNativeFrame(ExactRef ref){throw new AssertionError();}
    }
}
