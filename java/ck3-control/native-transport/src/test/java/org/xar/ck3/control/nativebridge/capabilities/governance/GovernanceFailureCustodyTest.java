package org.xar.ck3.control.nativebridge.capabilities.governance;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.governance.council.CouncilCodec;
import org.xar.ck3.control.governance.crownauthority.*;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Retained queries feed real normalizers/preparers and immutable custody consumers. Rejection/default variants are synthetic; no native qualification. */
final class GovernanceFailureCustodyTest {
    private static final String SHA="AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
    private static final ExactRef REF=new ExactRef("software-source-no-runtime-qualification",1,"a".repeat(64));
    private static final Instant T=Instant.parse("2026-10-23T20:00:00Z");
    private static ObjectNode fixture(String path)throws Exception {String root=System.getProperty("xar.repository.root");assertNotNull(root);return (ObjectNode)StrictJson.parse(Files.readAllBytes(Path.of(root,path)));}
    private static ActionCommand command(String operation,Obj args,int actor,int nativeRevision,int date) {
        return command(operation,args,actor,nativeRevision,date,"public:100",100);
    }
    private static ActionCommand command(String operation,Obj args,int actor,int nativeRevision,int date,String snapshot,int publicRevision) {
        var source=new G2Source("xenoamess-full-tower-eb9d2c1186",T.toString(),"1.20.0.2",REF);
        var observed=new ObservationIdentity(source.machineId(),new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(actor),BigInteger.valueOf(nativeRevision),BigInteger.valueOf(date)),snapshot,BigInteger.valueOf(publicRevision),"custody-software-episode"),1);
        return new ActionCommand("governance-custody-software",observed,source,"custody-software-session",new OperationKey(operation),args,
                new ExpectedPostcondition(org.xar.ck3.control.g2.planning.ProposalLifecycle.POSTCONDITION_VERSION,observed,source,NativeGovernanceEffects.SCHEMA,List.of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"),true))),new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),T.plusSeconds(30));
    }
    private static GuardEvidence guard(ActionCommand command,OperationKey op) {return new GuardEvidence(command.before(),command.source(),command.sessionId(),BigInteger.ONE,op,REF,REF,"software-custody-authority",T,T.plusSeconds(30));}
    private static NativeActionPort.AckReceived ack(ActionCommand command,String id,NativeRequest request,ObjectNode result,long order) throws Exception {
        var full=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);full.set("result",result);
        byte[] bytes=StrictJson.canonical(full),incoming=NativeWire.packet(bytes),outgoing=NativeWire.execute(id,request.step(),command.before().frame().identity().nativeRevision(),request.additionalFields().bytes());
        var session=new NativeObservationPort.TransportSession(command.before().machineId(),command.before().game(),BigInteger.ONE,command.sessionId());
        var chronology=new NativeRequestChronology(session,UUID.fromString("e08f634f-e4d0-4ab9-b319-a37f37922893"),id,NativeRequestChronology.PacketIdentity.of(outgoing),NativeRequestChronology.PacketIdentity.of(incoming),
                new NativeRequestChronology.Event(BigInteger.valueOf(order),T.plusMillis(order)),new NativeRequestChronology.Event(BigInteger.valueOf(order+1),T.plusMillis(order+1)),new NativeRequestChronology.Event(BigInteger.valueOf(order+2),T.plusMillis(order+2)));
        return new NativeActionPort.AckReceived(id,true,Optional.of(new RawJson(StrictJson.canonical(result))),new RawJson(bytes),incoming,Optional.of(new NativeActionPort.OutboundPacket(id,outgoing)),Optional.of(chronology));
    }
    private static GovernanceActionPreparation preparation() {return new GovernanceActionPreparation("1.20.0.2",SHA,(same,c,id)->{throw new AssertionError("no live private Council scope");},(same,c)->{throw new AssertionError("no replacement LIFE read");});}
    private static ActionCommand crown() throws Exception {
        var original=(ObjectNode)fixture("ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_realm_law_action/wire-law-crown-query.json").get("result");
        var first=command(GovernanceActionPreparation.CROWN,new Obj(java.util.Map.of()),16777217,40,53169072);
        var request=new PlanningReadRequest(first.before(),first.source(),first.sessionId(),new OperationKey(GovernancePlanningReads.CROWN),new Obj(java.util.Map.of()),first.deadline());
        var normalized=GovernancePlanningReads.crown(original,request,"1.20.0.2",SHA);var choice=CrownAuthorityPolicy.choose(CrownAuthorityCodec.decodeReadback(StrictJson.canonical(normalized)));
        return command(GovernanceActionPreparation.CROWN,new Obj(java.util.Map.of()).with("readback", parse(StrictJson.canonical(normalized))).with("law_key", new Text(choice.lawKey())).with("choice", parse(CrownAuthorityCodec.encodeChoice(choice))),16777217,40,53169072);
    }
    private static ObjectNode rejectedCrown(ActionCommand command,String id,String failure) {
        var result=StrictJson.object().put("step",command.operation().value()).put("accepted",true).put("private_build",true).put("advertised",false).put("backend_id","native-headless").put("game_version","1.20.0.2").put("executable_sha256",SHA).put("read_only",false).put("status","rejected_before_submit").putNull("observation").putNull("receipt");
        var value=result.putObject("ack").put("submitted_request_id",id).put("verification_pending",false).put("failure",failure).put("player_character_id",-1).put("group_key","crown_authority").put("previous_effective_law_key","").put("requested_law_key",text(command.arguments().get("law_key"),"law"));
        for(String key:List.of("pre_public_revision","pre_native_revision","pre_proof_epoch","pre_date_raw"))value.put(key,0);
        value.putArray("charges");value.putObject("title_successors").put("primary_title_id",-1).putArray("held_titles");return result;
    }
    @Test void retainedQuoteAndRealRequestFeedStrictRejectionAndTheSameArchivedDomainVerifier()throws Exception {
        var command=crown();String id="original-crown-software";var request=preparation().prepare(command,id);var attempt=new ActionState.Attempt(id,T,guard(command,command.operation()),request);
        var archive=new Archive();var dispatch=ack(command,id,request,rejectedCrown(command,id,"state_changed_before_submit"),10);archive.preserve(dispatch);
        var projected=NativeGovernanceEffects.originalRejection(command,attempt,dispatch,archive).orElseThrow();var rejected=assertInstanceOf(ActionPorts.RejectionObserved.class,projected.result()).rejection();
        var receipt=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Settled(attempt,dispatch,rejected));
        assertEquals(ActionReceipt.Outcome.REJECTED_CONFIRMED,receipt.outcome());assertFalse(receipt.visibleGameplay());assertFalse(receipt.eligibleAdvance());
        var binding=NativeGovernanceEffects.archivedVerifier(command.operation(),REF,(basis,a)->{throw new AssertionError("rejection must not manufacture a gameplay after-frame");},NativeGovernanceEffects.readContracts(REF,REF,REF),(c,a,r,ar)->{throw new AssertionError("Crown does not use LIFE preflight");});
        assertDoesNotThrow(()->binding.verifier().verify(null,receipt,archive));
        var wrong=new ActionReceipt(1,2,command,receipt.bodySha256(),new ActionState.Settled(attempt,dispatch,new ActionState.Rejected(id,rejected.reason()+"changed",rejected.originalEvidence())));
        assertThrows(IllegalArgumentException.class,()->binding.verifier().verify(null,wrong,archive));
    }
    @Test void catchFailureIsUnresolvedAndWrongBooleanOrOriginalPacketCannotClearPending()throws Exception {
        var command=crown();String id="original-crown-software";var request=preparation().prepare(command,id);var attempt=new ActionState.Attempt(id,T,guard(command,command.operation()),request);var archive=new Archive();
        var ambiguous=ack(command,id,request,rejectedCrown(command,id,"working_storage_unavailable"),10);archive.preserve(ambiguous);
        assertInstanceOf(ActionPorts.Pending.class,NativeGovernanceEffects.originalRejection(command,attempt,ambiguous,archive).orElseThrow().result());
        var wrong=rejectedCrown(command,id,"state_changed_before_submit");((ObjectNode)wrong.get("ack")).put("verification_pending",0);var bad=ack(command,id,request,wrong,10);archive.preserve(bad);
        assertThrows(IllegalArgumentException.class,()->NativeGovernanceEffects.originalRejection(command,attempt,bad,archive));
        var original=ack(command,id,request,rejectedCrown(command,id,"state_changed_before_submit"),10);
        var stripped=new NativeActionPort.AckReceived(id,true,original.originalResultToken(),original.originalFrame(),original.originalPacket(),original.outbound());archive.preserve(stripped);
        assertThrows(IllegalArgumentException.class,()->NativeGovernanceEffects.originalRejection(command,attempt,stripped,archive));
    }
    @Test void coldLifeReplaysTheActualPreservedLeafAndOriginalReadWithoutCallingTheReadPort()throws Exception {
        var first=command(GovernanceActionPreparation.PERK,new Obj(java.util.Map.of()),29829,3,53220000);var definitions=new GovernancePlanningReads(new GovernancePlanningReads.Sources(REF,REF),"1.20.0.2",SHA);
        var query=new PlanningReadRequest(first.before(),first.source(),first.sessionId(),definitions.formal().operation(),new Obj(java.util.Map.of()),first.deadline());
        var result=StrictJson.object().put("step",GovernancePlanningReads.FORMAL).put("private_build",true).put("advertised",false).put("status","available").put("formal_precondition_status","ready").put("episode_run_id",first.before().frame().episodeRunId());
        result.set("snapshot",fixture("ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_lifestyle_state_zero_points.json"));
        // Synthetic final-legal variant of the retained zero-point snapshot, for the strict encoder/custody unit test only.
        ObjectNode snapshot=assertInstanceOf(ObjectNode.class,result.get("snapshot"));((ObjectNode)snapshot.get("readiness")).put("legal_perk_candidates_ready",true);
        var legal=snapshot.putObject("legal_perk_candidates").put("status","available");legal.putArray("items").addObject().put("key","cutting_corners_perk").put("lifestyle_key","stewardship_lifestyle");
        var normalized=GovernancePlanningReads.life(result,query,GovernancePlanningReads.FORMAL);
        var command=command(GovernanceActionPreparation.PERK,new Obj(java.util.Map.of()).with("target_key", new Text("cutting_corners_perk")).with("target_lifestyle_key", new Text("stewardship_lifestyle")).with("original_query", parse(StrictJson.canonical(normalized))).with("decision", new Obj(java.util.Map.of())),29829,3,53220000);
        var readGuard=new PlanningReadGuard(guard(command,query.operation()),true,true,true,"b".repeat(64));
        var response=ack(command,"real-original-read-software",definitions.formal().prepare(query,"real-original-read-software"),result,1);
        var read=new PlanningReadReceipt(query,definitions.formal().contractId(),response.requestId(),readGuard,readGuard,response);var archive=new Archive();archive.preserve(response);archive.preserveRead(read);
        ExactRef leaf=NativeLifestyleReadPort.preserveOriginals(command,"original-life-software",List.of(read),archive);
        var prepared=new NativeRequest(GovernanceActionPreparation.PERK,Optional.empty(),GovernanceActionPreparation.lifestyleFields(command),List.of(leaf));
        var attempt=new ActionState.Attempt("original-life-software",T.plusSeconds(1),guard(command,command.operation()),prepared);
        var cold=new NativeLifestyleReadPort(new PlanningReadPort(){@Override public <T> PlanningReadResult<T> read(ReadContract<T> c,PlanningReadRequest r){throw new AssertionError("cold replay cannot query");}},definitions,archive);
        assertEquals(List.of(read),cold.originals(command,attempt,archive));assertDoesNotThrow(()->cold.verify(command,attempt,List.of(read),archive));
        var missing=new ActionState.Attempt(attempt.requestId(),attempt.submittedAt(),attempt.guard(),new NativeRequest(prepared.step(),prepared.requiredCapability(),prepared.additionalFields()));
        assertThrows(IllegalArgumentException.class,()->cold.originals(command,missing,archive));
        var crossed=new ActionState.Attempt("another-original-life",attempt.submittedAt(),attempt.guard(),prepared);assertThrows(IllegalArgumentException.class,()->cold.originals(command,crossed,archive));
        var stripped=new NativeActionPort.AckReceived(response.requestId(),true,response.originalResultToken(),response.originalFrame(),response.originalPacket(),response.outbound());
        var withoutCustody=new PlanningReadReceipt(query,definitions.formal().contractId(),stripped.requestId(),readGuard,readGuard,stripped);
        archive.preserve(stripped);archive.preserveRead(withoutCustody);
        assertThrows(IllegalArgumentException.class,()->cold.verify(command,attempt,List.of(withoutCustody),archive));
        archive.preserve(response);archive.preserveRead(read);
        assertDoesNotThrow(()->cold.verify(command,attempt,List.of(read),archive));
    }
    @Test void retainedCouncilHelperTerminalAndNativeZeroFrameRejectionUseTheSameStrictDecoder()throws Exception {
        var full=fixture("ck3_autonomous_player/tests/fixtures/native_12002/governance/council-private-ack.json");
        var result=(ObjectNode)full.get("result");
        var expected=new org.xar.ck3.control.governance.council.CouncilActionCodec.Request("assign-13",
                new org.xar.ck3.control.governance.council.CouncilModels.Frame("native:13",BigInteger.valueOf(13),BigInteger.valueOf(13),53175816,16777217),
                org.xar.ck3.control.governance.council.CouncilModels.Position.STEWARD,16777232,java.util.OptionalInt.of(16777218));
        assertEquals(org.xar.ck3.control.governance.council.CouncilActionCodec.AckStatus.HELPER_INVOKED_VERIFICATION_PENDING,
                CouncilContinuationPolicy.decodeHelperTerminal(new RawJson(StrictJson.canonical(result)),expected).status());
        var rejected=result.deepCopy().put("status","rejected_before_submit").put("snapshot_revision",0);
        var helper=(ObjectNode)rejected.get("council_assign_councillor_ack");
        helper.put("status","rejected_before_submit").put("failure","state_changed_before_submit").put("pre_snapshot_id","").put("pre_public_revision",0).put("pre_native_revision",0).put("pre_date_raw",0)
                .put("owner_character_id",-1).put("active_task_id",-1).put("had_incumbent",false).put("previous_incumbent_character_id",-1).put("route","none")
                .put("native_helper_invoked",false).put("queue_acceptance_observed",false).put("verification_pending",false);
        var decoded=CouncilContinuationPolicy.decodeHelperTerminal(new RawJson(StrictJson.canonical(rejected)),expected);
        assertEquals(org.xar.ck3.control.governance.council.CouncilActionCodec.AckStatus.REJECTED_BEFORE_SUBMIT,decoded.status());
        assertEquals(org.xar.ck3.control.governance.council.CouncilActionCodec.HelperDisposition.REJECTED_WITHOUT_INVOCATION,decoded.disposition());
        assertFalse(decoded.helperInvoked());assertFalse(decoded.verificationPending());
        var wrong=rejected.deepCopy().put("snapshot_revision",13);assertThrows(IllegalArgumentException.class,()->CouncilContinuationPolicy.decodeHelperTerminal(new RawJson(StrictJson.canonical(wrong)),expected));
        ((ObjectNode)rejected.get("council_assign_councillor_ack")).put("verification_pending",0);
        assertThrows(IllegalArgumentException.class,()->CouncilContinuationPolicy.decodeHelperTerminal(new RawJson(StrictJson.canonical(rejected)),expected));
    }
    private static ObjectNode councilRejected(ObjectNode actual,String id,String failure,String nativeReason) {
        ObjectNode result=actual.deepCopy().put("status","rejected_before_submit").put("snapshot_revision",0);
        var helper=(ObjectNode)result.get("council_assign_councillor_ack");
        helper.put("action_request_id",id).put("status","rejected_before_submit").put("failure",failure).put("pre_snapshot_id","")
                .put("pre_public_revision",0).put("pre_native_revision",0).put("pre_date_raw",0).put("owner_character_id",-1)
                .put("active_task_id",-1).put("had_incumbent",false).put("previous_incumbent_character_id",-1).put("route","none")
                .put("native_helper_invoked",false).put("queue_acceptance_observed",false).put("verification_pending",false).put("native_reason_key",nativeReason);
        return result;
    }
    @Test void sourceDefinedRejectPendingAndCatchRoutesRemainDifferentFromExplicitNoninvocation()throws Exception {
        var actual=(ObjectNode)fixture("ck3_autonomous_player/tests/fixtures/native_12002/governance/council-private-ack.json").get("result");
        var expected=new org.xar.ck3.control.governance.council.CouncilActionCodec.Request("assign-13",
                new org.xar.ck3.control.governance.council.CouncilModels.Frame("native:13",BigInteger.valueOf(13),BigInteger.valueOf(13),53175816,16777217),
                org.xar.ck3.control.governance.council.CouncilModels.Position.STEWARD,16777232,java.util.OptionalInt.of(16777218));
        var clean=councilRejected(actual,expected.requestId(),"native_helper_not_invoked","");
        assertEquals(org.xar.ck3.control.governance.council.CouncilActionCodec.HelperDisposition.REJECTED_WITHOUT_INVOCATION,
                CouncilContinuationPolicy.decodeHelperTerminal(new RawJson(StrictJson.canonical(clean)),expected).disposition());
        var previous=councilRejected(actual,expected.requestId(),"callbacks_unavailable","pending_assignment_unresolved");
        assertEquals(org.xar.ck3.control.governance.council.CouncilActionCodec.HelperDisposition.PRIOR_ASSIGNMENT_UNRESOLVED,
                CouncilContinuationPolicy.decodeHelperTerminal(new RawJson(StrictJson.canonical(previous)),expected).disposition());
        var caught=councilRejected(actual,expected.requestId(),"native_helper_not_invoked","action_executor_exception");
        assertEquals(org.xar.ck3.control.governance.council.CouncilActionCodec.HelperDisposition.DISPATCH_UNRESOLVED,
                CouncilContinuationPolicy.decodeHelperTerminal(new RawJson(StrictJson.canonical(caught)),expected).disposition());
        for (String field:List.of("native_helper_invoked","queue_acceptance_observed","verification_pending")) {
            var wrong=clean.deepCopy();((ObjectNode)wrong.get("council_assign_councillor_ack")).put(field,true);
            assertThrows(IllegalArgumentException.class,()->CouncilContinuationPolicy.decodeHelperTerminal(new RawJson(StrictJson.canonical(wrong)),expected));
        }
        var route=clean.deepCopy();((ObjectNode)route.get("council_assign_councillor_ack")).put("route","assign_vacant");
        assertThrows(IllegalArgumentException.class,()->CouncilContinuationPolicy.decodeHelperTerminal(new RawJson(StrictJson.canonical(route)),expected));
        ((ObjectNode)previous.get("council_assign_councillor_ack")).put("failure","state_changed_before_submit");
        assertThrows(IllegalArgumentException.class,()->CouncilContinuationPolicy.decodeHelperTerminal(new RawJson(StrictJson.canonical(previous)),expected));
        ((ObjectNode)caught.get("council_assign_councillor_ack")).put("failure","callbacks_unavailable");
        assertThrows(IllegalArgumentException.class,()->CouncilContinuationPolicy.decodeHelperTerminal(new RawJson(StrictJson.canonical(caught)),expected));
    }
    @Test void publicCouncilProducerAndArchiveConsumerCannotSettleRetainedPriorAssignmentOrCatch()throws Exception {
        var raw=(ObjectNode)fixture("ck3_autonomous_player/tests/fixtures/native_12002/governance/council-query.json").get("result").get("council_composition_candidates");
        var frame=new org.xar.ck3.control.governance.council.CouncilModels.Frame("native:council12002",BigInteger.valueOf(8),BigInteger.valueOf(7),53178264,16777217);
        var decoded=CouncilCodec.decodeNative(StrictJson.canonical(raw),frame,org.xar.ck3.control.governance.council.CouncilModels.Position.STEWARD,"1.20.0.2",SHA);
        var args=new Obj(java.util.Map.of()).with("position_key", new Text("councillor_steward")).with("candidate_character_id", new IntegerValue(BigInteger.valueOf(16777232))).with("original_query", parse(CouncilCodec.encode(decoded))).with("expected_has_incumbent", new Bool(true)).with("expected_incumbent_character_id", new IntegerValue(BigInteger.valueOf(16777218)));
        var command=command(org.xar.ck3.control.governance.council.CouncilActionCodec.ASSIGN,args,frame.ownerId(),7,frame.dateRaw(),frame.snapshotId(),8);
        String id="public-council-original";var prepared=preparation().prepare(command,id);var attempt=new ActionState.Attempt(id,T,guard(command,command.operation()),prepared);
        var actual=(ObjectNode)fixture("ck3_autonomous_player/tests/fixtures/native_12002/governance/council-ack.json").get("result");
        var archive=new Archive();
        for (String[] unresolved:List.of(new String[]{"callbacks_unavailable","pending_assignment_unresolved"},new String[]{"native_helper_not_invoked","action_executor_exception"})) {
            var outcome=ack(command,id,prepared,councilRejected(actual,id,unresolved[0],unresolved[1]),10);archive.preserve(outcome);
            var projected=NativeGovernanceEffects.originalRejection(command,attempt,outcome,archive).orElseThrow();assertInstanceOf(ActionPorts.Pending.class,projected.result());
            var forged=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Settled(attempt,outcome,
                    new ActionState.Rejected(id,"native_council_rejected_before_submit:"+unresolved[0],archive.referenceOf(outcome))));
            var binding=NativeGovernanceEffects.archivedVerifier(command.operation(),REF,(basis,ar)->{throw new AssertionError("rejection must not query a replacement frame");},NativeGovernanceEffects.readContracts(REF,REF,REF),(c,a,r,ar)->{throw new AssertionError("Council cannot use LIFE evidence");});
            assertThrows(IllegalArgumentException.class,()->binding.verifier().verify(null,forged,archive));
        }
        var clean=ack(command,id,prepared,councilRejected(actual,id,"state_changed_before_submit",""),10);archive.preserve(clean);
        var rejected=assertInstanceOf(ActionPorts.RejectionObserved.class,NativeGovernanceEffects.originalRejection(command,attempt,clean,archive).orElseThrow().result());
        assertEquals("native_council_rejected_before_submit:state_changed_before_submit",rejected.rejection().reason());
    }
    @Test void originalGovernanceReadGroupsRequireEndpointOrderEvenAfterChronologyJsonRoundtrip()throws Exception {
        var command=command(GovernanceActionPreparation.PERK,new Obj(java.util.Map.of()),29829,3,53220000);var operation=new OperationKey(GovernancePlanningReads.FORMAL);
        var query=new PlanningReadRequest(command.before(),command.source(),command.sessionId(),operation,new Obj(java.util.Map.of()),command.deadline());
        var guard=new PlanningReadGuard(guard(command,operation),true,true,true,"b".repeat(64));var request=new NativeRequest(operation.value(),Optional.empty(),new RawJson(new byte[]{'{','}'}));
        var first=ack(command,"ordered-read-1",request,StrictJson.object().put("status","software-order-only"),1);
        var second=ack(command,"ordered-read-2",request,StrictJson.object().put("status","software-order-only"),4);
        var restored=NativeRequestChronologyCodec.decode(StrictJson.parse(StrictJson.canonical(NativeRequestChronologyCodec.encode(second.custody().orElseThrow()))));
        var cold=new NativeActionPort.AckReceived(second.requestId(),true,second.originalResultToken(),second.originalFrame(),second.originalPacket(),second.outbound(),Optional.of(restored));
        var one=new PlanningReadReceipt(query,"software-order-contract",first.requestId(),guard,guard,first);
        var two=new PlanningReadReceipt(query,"software-order-contract",cold.requestId(),guard,guard,cold);
        assertDoesNotThrow(()->GovernanceReadChronology.requireOrderedReads(List.of(one,two)));
        assertThrows(IllegalArgumentException.class,()->GovernanceReadChronology.requireOrderedReads(List.of(two,one)));
        assertThrows(IllegalArgumentException.class,()->GovernanceReadChronology.requireOrderedReads(List.of(one,one)));
        var stripped=new NativeActionPort.AckReceived(second.requestId(),true,second.originalResultToken(),second.originalFrame(),second.originalPacket(),second.outbound());
        var missing=new PlanningReadReceipt(query,"software-order-contract",stripped.requestId(),guard,guard,stripped);
        assertThrows(IllegalArgumentException.class,()->GovernanceReadChronology.requireOrderedReads(List.of(one,missing)));
        var changed=NativeRequestChronologyCodec.encode(restored).put("custody_epoch","f5413ed5-eac4-42f2-8536-4bfe56c5676c");
        var crossed=new NativeActionPort.AckReceived(second.requestId(),true,second.originalResultToken(),second.originalFrame(),second.originalPacket(),second.outbound(),Optional.of(NativeRequestChronologyCodec.decode(changed)));
        var otherEpoch=new PlanningReadReceipt(query,"software-order-contract",crossed.requestId(),guard,guard,crossed);
        assertThrows(IllegalArgumentException.class,()->GovernanceReadChronology.requireOrderedReads(List.of(one,otherEpoch)));
    }
    private static final class Archive implements ActionPorts.OutcomeArchive {
        private final Map<ExactRef,RawJson> materials=new HashMap<>();private final Map<ExactRef,NativeActionPort.DispatchOutcome> outcomes=new HashMap<>();private final Map<ExactRef,PlanningReadReceipt> reads=new HashMap<>();
        private static ExactRef ref(byte[] body){return new ExactRef("software-original/"+ActionCodec.sha256(body),body.length,ActionCodec.sha256(body));}
        @Override public ExactRef preserveMaterial(RawJson body){var ref=ref(body.bytes());materials.put(ref,body);return ref;}
        @Override public RawJson loadMaterial(ExactRef ref){return Objects.requireNonNull(materials.get(ref));}
        @Override public ExactRef materialReferenceOf(RawJson body){var ref=ref(body.bytes());assertEquals(body,loadMaterial(ref));return ref;}
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value){var ack=(NativeActionPort.AckReceived)value;var ref=ref(ack.originalPacket());outcomes.put(ref,value);return ref;}
        @Override public NativeActionPort.DispatchOutcome load(ExactRef ref){return Objects.requireNonNull(outcomes.get(ref));}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value){return outcomes.entrySet().stream().filter(e->e.getValue().equals(value)).map(Map.Entry::getKey).findFirst().orElseThrow();}
        @Override public ExactRef preserveRead(PlanningReadReceipt value){var ref=ref(value.original().originalPacket());reads.put(ref,value);return ref;}
        @Override public PlanningReadReceipt loadRead(ExactRef ref){return Objects.requireNonNull(reads.get(ref));}
        @Override public ExactRef readReferenceOf(PlanningReadReceipt value){return reads.entrySet().stream().filter(e->e.getValue().equals(value)).map(Map.Entry::getKey).findFirst().orElseThrow();}
        private static <T>T unused(){throw new AssertionError("unrelated archive path");}
        @Override public ExactRef preserveRequest(NativeRequest v){return unused();}@Override public NativeRequest loadRequest(ExactRef r){return unused();}@Override public ExactRef requestReferenceOf(NativeRequest v){return unused();}
        @Override public ExactRef preserveRecord(ActionRecord v){return unused();}@Override public ActionRecord loadRecord(ExactRef r){return unused();}@Override public ExactRef recordReferenceOf(ActionRecord v){return unused();}
        @Override public ExactRef preserveReceipt(ActionReceipt v){return unused();}@Override public ActionReceipt loadReceipt(ExactRef r){return unused();}@Override public ExactRef receiptReferenceOf(ActionReceipt v){return unused();}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame v){return unused();}@Override public byte[] loadNativeFrame(ExactRef r){return unused();}
    }
}
