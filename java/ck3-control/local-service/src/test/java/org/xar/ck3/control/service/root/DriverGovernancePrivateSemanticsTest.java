package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.io.IOException;
import java.time.Instant;
import java.util.List;
import java.util.Set;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import java.nio.file.Path;
import java.util.OptionalInt;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilActionCodec;
import org.xar.ck3.control.governance.council.CouncilModels;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec;

/** Retained original .2 data plus explicitly mutated boundary fixtures. No private Core or native permit is minted. */
final class DriverGovernancePrivateSemanticsTest {
    private static ObjectNode original()throws Exception {
        try(var input=DriverGovernancePrivateSemanticsTest.class.getResourceAsStream("/crownauthority/original-producer-golden.json")) {
            assertNotNull(input,"required selected original Crown testresource missing");
            byte[] original=input.readAllBytes();assertEquals("1c2f7b7a9e7ba9b59b334cf340063df4dabc101d84cc688c85965e8d01e6d13c",org.xar.ck3.control.application.action.ActionCodec.sha256(original));
            return (ObjectNode)StrictJson.parse(original).get("cases").get(0).get("input").get("readback");
        }
    }
    private static RawJson raw(ObjectNode node) {return new RawJson(StrictJson.canonical(node));}
    @Test void emptyCouncilCallerIdentityRetainsItsPublicTokenAndSelectsTheOriginalDefaultBranch() {
        var args=StrictJson.object().put("candidate_character_id",2).put("expected_revision","1").put("action_request_id","");args.set("query",StrictJson.object());
        var empty=DriverGovernancePublicCodec.assign(raw(args));assertTrue(DriverGovernancePublicInput.explicitCouncilId(empty.actionId()).isEmpty());
        assertEquals(empty,DriverGovernancePublicCodec.assign(DriverGovernancePublicCodec.encode(empty)));assertEquals("",StrictJson.parse(DriverGovernancePublicCodec.encode(empty).bytes()).get("action_request_id").textValue());
        args.putNull("action_request_id");var nil=DriverGovernancePublicCodec.assign(raw(args));assertNotEquals(empty,nil);assertTrue(DriverGovernancePublicInput.explicitCouncilId(nil.actionId()).isEmpty());
        args.remove("action_request_id");var missing=DriverGovernancePublicCodec.assign(raw(args));assertNotEquals(nil,missing);assertTrue(DriverGovernancePublicInput.explicitCouncilId(missing.actionId()).isEmpty());
    }
    @Test void callerTokenRepresentationDoesNotConferNativeRequestEligibility() {
        var args=StrictJson.object().put("candidate_character_id",2).put("expected_revision","1").put("action_request_id","invalid token");args.set("query",StrictJson.object());
        var input=DriverGovernancePublicCodec.assign(raw(args));assertEquals("invalid token",DriverGovernancePublicInput.explicitCouncilId(input.actionId()).orElseThrow());
        var frame=new CouncilModels.Frame("native:1",BigInteger.ONE,BigInteger.ONE,0,1);
        assertThrows(IllegalArgumentException.class,()->new CouncilActionCodec.Request("invalid token",frame,CouncilModels.Position.STEWARD,2,OptionalInt.empty()));
    }
    @Test void crownPendingAckUsesOriginalNativeOwnerLawGroupRevisionDateAndTitles()throws Exception {
        var original=original();var readback=CrownAuthorityCodec.decodeReadback(StrictJson.canonical(original));var source=readback.sourceFrame();
        var ack=StrictJson.object().put("verification_pending",true).put("player_character_id",source.playerCharacterId()).put("requested_law_key","crown_authority_2")
                .put("group_key",readback.groupKey()).put("pre_public_revision",source.queriedNativeRevision()).put("pre_date_raw",source.dateRaw());ack.set("title_successors",original.get("title_successors"));
        RootDriverGovernancePublicService.requireCrownPendingAck(ack,readback,"crown_authority_2");
        for(String field:java.util.List.of("player_character_id","pre_public_revision","pre_date_raw")) {
            var wrong=ack.deepCopy();wrong.put(field,0);assertThrows(IllegalArgumentException.class,()->RootDriverGovernancePublicService.requireCrownPendingAck(wrong,readback,"crown_authority_2"));
        }
        for(String field:java.util.List.of("requested_law_key","group_key")) {
            var wrong=ack.deepCopy();wrong.put(field,"wrong");assertThrows(IllegalArgumentException.class,()->RootDriverGovernancePublicService.requireCrownPendingAck(wrong,readback,"crown_authority_2"));
        }
        var wrong=ack.deepCopy();wrong.put("verification_pending",false);assertThrows(IllegalArgumentException.class,()->RootDriverGovernancePublicService.requireCrownPendingAck(wrong,readback,"crown_authority_2"));
        var noTitles=ack.deepCopy();noTitles.remove("title_successors");assertThrows(IllegalArgumentException.class,()->RootDriverGovernancePublicService.requireCrownPendingAck(noTitles,readback,"crown_authority_2"));
    }
    @Test void explicitProtocolHeaderRequiresTheActualConfiguredProducerAndMatchingOriginalArguments()throws Exception {
        var data=CrownAuthorityCodec.decodeReadback(StrictJson.canonical(original()));
        var source=new org.xar.ck3.control.g2.common.G2Source("software-governance-only",java.time.Instant.EPOCH.toString(),data.sourceFrame().exactCk3Build(),new org.xar.ck3.control.contracts.ExactRef("synthetic-source-only",1,"a".repeat(64)));
        var frame=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity(source.machineId(),new org.xar.ck3.control.contracts.GameGeneration(123,new org.xar.ck3.control.contracts.PythonOnlyUInt64(BigInteger.ONE)),
                new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame(new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(data.sourceFrame().playerCharacterId(),data.sourceFrame().queriedNativeRevision(),data.sourceFrame().dateRaw()),data.sourceFrame().queriedSnapshotId(),data.sourceFrame().queriedRevision(),"software-episode"),1);
        var fields=StrictJson.object().put("position_key",CouncilModels.Position.STEWARD.key()).put("candidate_character_id",2).put("expected_has_incumbent",false).put("expected_incumbent_character_id",-1)
                .put("public_submission_schema",org.xar.ck3.control.governance.council.CouncilCallerSubmission.SCHEMA).put("caller_request_id","original-caller-id");fields.set("original_query",StrictJson.object());
        var expected=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition(1,frame,source,"xar.java.governance-independent-effect/v1",java.util.List.of(new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedText(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("council.position_key"),CouncilModels.Position.STEWARD.key())));
        var originalProducer=new org.xar.ck3.control.contracts.ExactRef(Path.of("software-fixture/RootDriverGovernancePublicService.java").toAbsolutePath().toString(),1,"b".repeat(64));
        var identity=new org.xar.ck3.control.application.action.ExplicitOriginalProtocolId(org.xar.ck3.control.application.action.ExplicitOriginalProtocolId.Contract.PUBLIC_COUNCIL_ASSIGNMENT,"original-caller-id",originalProducer);
        var command=new org.xar.ck3.control.application.action.ActionCommand("software-manual-council",new org.xar.ck3.control.application.action.CommandOrigin.Gameplay(frame),source,"software-session",new org.xar.ck3.control.application.action.OperationKey(CouncilActionCodec.PRIVATE_ASSIGN),
                (org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj)org.xar.ck3.control.planning.opportunity.OpportunityJson.parse(StrictJson.canonical(fields)),new org.xar.ck3.control.application.action.CommandExpectation.Gameplay(expected),new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims(java.util.Set.of(),java.util.Set.of(),java.util.Set.of(),java.util.Set.of()),java.time.Instant.parse("2026-10-24T00:00:30Z"),identity);
        var configured=new org.xar.ck3.control.nativebridge.capabilities.governance.GovernanceActionPreparation(data.sourceFrame().exactCk3Build(),data.sourceFrame().exeSha256(),(same,value,id)->{throw new AssertionError("policy validation cannot query");},(same,value)->{throw new AssertionError("policy validation cannot query");},java.util.Optional.of(originalProducer));
        configured.requireProtocolIdentity(command);assertEquals(command,org.xar.ck3.control.application.action.ActionCodec.decodeCommand(org.xar.ck3.control.application.action.ActionCodec.encodeCommand(command)));
        var unconfigured=new org.xar.ck3.control.nativebridge.capabilities.governance.GovernanceActionPreparation(data.sourceFrame().exactCk3Build(),data.sourceFrame().exeSha256(),(same,value,id)->{throw new AssertionError("policy validation cannot query");},(same,value)->{throw new AssertionError("policy validation cannot query");});
        assertThrows(IllegalArgumentException.class,()->unconfigured.requireProtocolIdentity(command));
        var derived=new org.xar.ck3.control.application.action.ActionCommand(command.actionId(),command.origin(),command.source(),command.sessionId(),command.operation(),command.arguments(),command.expectation(),command.claims(),command.deadline());
        assertThrows(IllegalArgumentException.class,()->configured.requireProtocolIdentity(derived));
        var wrongSource=new org.xar.ck3.control.application.action.ExplicitOriginalProtocolId(identity.contract(),identity.value(),new org.xar.ck3.control.contracts.ExactRef(Path.of("software-fixture/other.java").toAbsolutePath().toString(),1,"c".repeat(64)));
        var changed=new org.xar.ck3.control.application.action.ActionCommand(command.actionId(),command.origin(),command.source(),command.sessionId(),command.operation(),command.arguments(),command.expectation(),command.claims(),command.deadline(),wrongSource);
        assertThrows(IllegalArgumentException.class,()->configured.requireProtocolIdentity(changed));
    }
    @Test void retainedNativeDataAndExplicitWidthMutationsCrossTheSolePublicResultContract()throws Exception {
        var nativeData=original().deepCopy();nativeData.put("queried_revision",new BigInteger("18446744073709551615"));
        ((ObjectNode)nativeData.get("resources").get(0)).put("amount_raw",Long.MIN_VALUE);
        ((ObjectNode)nativeData.get("candidates").get(1).get("costs").get(0)).put("cost_raw",Long.MAX_VALUE);
        var publicData=DriverGovernancePublicProjection.output(raw(nativeData),DriverGovernancePublicProjection.Shape.CROWN);var node=StrictJson.parse(publicData.bytes());
        assertEquals("18446744073709551615",node.get("queried_revision").textValue());assertEquals(Long.toString(Long.MIN_VALUE),node.get("resources").get(0).get("amount_raw").textValue());
        assertEquals(Long.toString(Long.MAX_VALUE),node.get("candidates").get(1).get("costs").get(0).get("cost_raw").textValue());assertTrue(node.get("player_character_id").isIntegralNumber());
        assertEquals(raw(nativeData),DriverGovernancePublicProjection.input(publicData,DriverGovernancePublicProjection.Shape.CROWN));
        var descriptor=RootOriginalPublicTestInputs.tools().stream().filter(value->value.name().equals("ck3_query_realm_law_crown_action_private_v1")).findFirst().orElseThrow();
        descriptor.validateResult(org.xar.ck3.control.service.mcp.PublicMcpDirectory.CallResult.fromBusinessJson(publicData));
    }
    private static final ExactRef DATA_SOURCE=new ExactRef("software-governance-packet-only",1,"b".repeat(64));
    /** Software exact-byte archive only. It cannot issue a Session, guard, read, action or current qualification. */
    private static final class PacketArchive implements ActionPorts.OutcomeArchive {
        private final byte[] bytes;private final ExactRef reference;private int packetReads;
        PacketArchive(byte[] original){bytes=original.clone();reference=new ExactRef("software-only/hello-packet",bytes.length,ActionCodec.sha256(bytes));}
        @Override public byte[] readOriginalPacket(ExactRef ref){assertEquals(reference,ref);assertEquals(ref.sha256(),ActionCodec.sha256(bytes));packetReads++;return bytes.clone();}
        private static <T>T no(){throw new AssertionError("packet DATA fixture has no query, action, writer or material permission");}
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome x){return no();}
        @Override public NativeActionPort.DispatchOutcome load(ExactRef x){return no();}
        @Override public ExactRef preserveRequest(NativeRequest x){return no();}
        @Override public NativeRequest loadRequest(ExactRef x){return no();}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome x){return no();}
        @Override public ExactRef requestReferenceOf(NativeRequest x){return no();}
        @Override public ExactRef preserveRead(PlanningReadReceipt x){return no();}
        @Override public PlanningReadReceipt loadRead(ExactRef x){return no();}
        @Override public ExactRef readReferenceOf(PlanningReadReceipt x){return no();}
        @Override public ExactRef preserveRecord(ActionRecord x){return no();}
        @Override public ActionRecord loadRecord(ExactRef x){return no();}
        @Override public ExactRef recordReferenceOf(ActionRecord x){return no();}
        @Override public ExactRef preserveReceipt(ActionReceipt x){return no();}
        @Override public ActionReceipt loadReceipt(ExactRef x){return no();}
        @Override public ExactRef receiptReferenceOf(ActionReceipt x){return no();}
        @Override public ExactRef preserveMaterial(RawJson x){return no();}
        @Override public RawJson loadMaterial(ExactRef x){throw new AssertionError("complete HELLO packet must never use the JSON material lane");}
        @Override public ExactRef materialReferenceOf(RawJson x){return no();}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame x){return no();}
        @Override public byte[] loadNativeFrame(ExactRef x){return no();}
    }
    private static Complete packetFrame(ObjectNode snapshot) {
        var source=new org.xar.ck3.control.g2.common.G2Source("software-packet-only",Instant.EPOCH.toString(),"1.20.0.2",DATA_SOURCE);
        var frame=new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame(
            new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(snapshot.get("played_character").get("character_id").bigIntegerValue(),snapshot.get("native_revision").bigIntegerValue(),snapshot.get("date_raw").bigIntegerValue()),
            snapshot.get("snapshot_id").textValue(),snapshot.get("revision").bigIntegerValue(),"software-episode");
        var identity=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity(source.machineId(),new org.xar.ck3.control.contracts.GameGeneration(123,new org.xar.ck3.control.contracts.PythonOnlyUInt64(BigInteger.ONE)),frame,1);
        return new Complete(identity,source,"software-session",BigInteger.ONE,(OpportunityJson.Obj)OpportunityJson.parse(StrictJson.canonical(snapshot)),DATA_SOURCE,Instant.EPOCH,"a".repeat(64));
    }
    private static GuardEvidence packetGuard(Complete frame,ExactRef hello) {
        return new GuardEvidence(frame.identity(),frame.source(),frame.sessionId(),frame.connectionGeneration(),new OperationKey(DriverGovernanceReadDefinitions.GOVERNMENT),DATA_SOURCE,hello,"software-only-not-source-authority",Instant.EPOCH,Instant.EPOCH.plusSeconds(30));
    }
    private static ObjectNode governmentOriginal()throws Exception {
        try(var input=DriverGovernancePrivateSemanticsTest.class.getResourceAsStream("/governmentquery/original-producer-golden.json")) {
            assertNotNull(input,"required selected Government original producer resource missing");byte[] bytes=input.readAllBytes();
            assertEquals("3cd1a0f01d6fedda56ce9c16cd7f01aa3ab98bd85b74290682ade5fafe733869",ActionCodec.sha256(bytes));return (ObjectNode)StrictJson.parse(bytes);
        }
    }
    private static byte[] helloPacket(ObjectNode snapshot)throws Exception {
        var hello=((ObjectNode)snapshot.get("diagnostics").get("hello")).deepCopy();
        hello.put("type","hello").put("protocol_version",1).put("pid",123).put("connection_generation",1).put("bridge_version","software-packet-only")
            .put("game_adapter_id","software-data").put("game_adapter_status","available").put("ck3_build_match",true);hello.putArray("capabilities");
        return NativeWire.packet(StrictJson.canonical(hello));
    }
    @Test void originalGovernmentProjectionCrossesFullHelloPacketLaneAndActualPublicResultContract()throws Exception {
        var original=governmentOriginal();var consume=((ObjectNode)original.get("base_consume")).deepCopy();
        var before=(ObjectNode)consume.get("before_snapshot");var after=(ObjectNode)consume.get("after_snapshot");
        var packet=helloPacket(before);var archive=new PacketArchive(packet);
        assertTrue(NativeWire.decode(packet) instanceof NativeWire.Hello);
        consume.set("before_snapshot",DriverGovernanceReadDefinitions.snapshot(packetFrame(before),packetGuard(packetFrame(before),archive.reference),archive));
        consume.set("after_snapshot",DriverGovernanceReadDefinitions.snapshot(packetFrame(after),packetGuard(packetFrame(after),archive.reference),archive));
        var binding=RootDriverGovernancePublicService.readBinding(packetFrame(before));
        assertEquals(before.get("revision").bigIntegerValue(),binding.publicRevision());assertEquals(before.get("native_revision").bigIntegerValue(),binding.nativeRevision());
        for(String field:List.of("date_raw","played_character")) {
            var crossed=consume.deepCopy();var post=(ObjectNode)crossed.get("after_snapshot");
            if(field.equals("date_raw"))post.put("date_raw",before.get("date_raw").intValue()+1);else ((ObjectNode)post.get("played_character")).put("alive",false);
            assertThrows(IllegalArgumentException.class,()->org.xar.ck3.control.wave3.governance.governmentquery.GovernmentQueryCodec.consume(StrictJson.canonical(crossed)));
        }
        byte[] bytes=org.xar.ck3.control.wave3.governance.governmentquery.GovernmentQueryCodec.consume(StrictJson.canonical(consume));
        byte[] expected=org.xar.ck3.control.wave3.governance.governmentquery.GovernmentQueryCodec.consume(StrictJson.canonical(original.get("base_consume")));
        assertEquals(StrictJson.parse(expected),StrictJson.parse(bytes));assertEquals(2,archive.packetReads);
        var encoded=DriverGovernancePublicProjection.output(new RawJson(bytes),DriverGovernancePublicProjection.Shape.GOVERNMENT);
        assertEquals(new RawJson(bytes),DriverGovernancePublicProjection.input(encoded,DriverGovernancePublicProjection.Shape.GOVERNMENT));
        var descriptor=RootOriginalPublicTestInputs.tools().stream().filter(value->value.name().equals("ck3_query_government_runtime_adapter_private_v1")).findFirst().orElseThrow();
        var result=org.xar.ck3.control.service.mcp.PublicMcpDirectory.CallResult.fromBusinessJson(encoded);descriptor.validateResult(result);
        var envelope=StrictJson.parse(result.bytes());assertEquals(StrictJson.parse(encoded.bytes()),envelope.get("structuredContent"));
        assertEquals(envelope.get("structuredContent"),StrictJson.parse(envelope.get("content").get(0).get("text").textValue().getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class,()->StrictJson.parse(packet,packet.length),"framed packet must not be treated as ordinary JSON material");
    }
    @Test void wrongPacketRoleMalformedFramingAndWrongOriginalRefNeverBecomeGovernmentHello()throws Exception {
        var base=(ObjectNode)governmentOriginal().get("base_consume").get("before_snapshot");var valid=helloPacket(base);
        var snapshot=StrictJson.object().put("type","state_snapshot").put("protocol_version",1).put("snapshot_id","data").put("revision",1);snapshot.putObject("state");
        for(byte[] packet:List.of(NativeWire.packet(StrictJson.canonical(snapshot)),java.util.Arrays.copyOf(valid,valid.length-1),java.util.Arrays.copyOfRange(valid,4,valid.length))) {
            var archive=new PacketArchive(packet);assertThrows(IOException.class,()->DriverGovernanceReadDefinitions.originalHello(archive.reference,archive));
        }
        var archive=new PacketArchive(valid);var changed=new ExactRef(archive.reference.path(),archive.reference.bytes(),"c".repeat(64));
        assertThrows(AssertionError.class,()->DriverGovernanceReadDefinitions.originalHello(changed,archive));
        var noBuild=base.deepCopy();((ObjectNode)noBuild.get("diagnostics").get("hello")).put("expected_ck3_version","different");
        var wrong=new PacketArchive(helloPacket(noBuild));var consume=((ObjectNode)governmentOriginal().get("base_consume")).deepCopy();
        consume.set("before_snapshot",DriverGovernanceReadDefinitions.snapshot(packetFrame(noBuild),packetGuard(packetFrame(noBuild),wrong.reference),wrong));
        assertThrows(IllegalArgumentException.class,()->org.xar.ck3.control.wave3.governance.governmentquery.GovernmentQueryCodec.consume(StrictJson.canonical(consume)));
    }
    @Test void crownMissingResultKeepsOriginalErrorAndUnknownReceiptWithoutResubmitting()throws Exception {
        var data=(ObjectNode)governmentOriginal().get("base_consume").get("before_snapshot");var frame=packetFrame(data);
        var expected=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition(1,frame.identity(),frame.source(),"software-only/v1",List.of(new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("paused"),true)));
        var command=new ActionCommand("software-crown-unknown",frame.identity(),frame.source(),frame.sessionId(),new OperationKey(org.xar.ck3.control.nativebridge.capabilities.governance.GovernanceActionPreparation.CROWN),new OpportunityJson.Obj(java.util.Map.of()),expected,new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),Instant.EPOCH.plusSeconds(30));
        var receipt=new ActionReceipt(1,3,command,ActionCodec.bodySha256(command),new ActionState.Unknown(Optional.empty(),Optional.empty(),"actual no-result DATA vector",List.of(DATA_SOURCE)));
        var archive=new PacketArchive(helloPacket(data));byte[] canonical=ActionReceiptCodec.encodeReceipt(receipt,archive);
        var error=assertThrows(org.xar.ck3.control.service.mcp.PublicServiceFailure.class,()->RootDriverGovernancePublicService.crownAck(receipt));
        assertEquals(org.xar.ck3.control.service.mcp.PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,error.kind());assertEquals(originalCrownMissingResult(),error.getMessage());assertTrue(error.originalCandidate().isEmpty());
        assertArrayEquals(canonical,ActionReceiptCodec.encodeReceipt(receipt,archive));assertEquals(receipt,ActionReceiptCodec.decodeReceipt(canonical,archive));
        var guard=new GuardEvidence(command.before(),command.source(),command.sessionId(),BigInteger.ONE,command.operation(),archive.reference,DATA_SOURCE,"software-only",Instant.EPOCH,Instant.EPOCH.plusSeconds(30));
        var attempt=new ActionState.Attempt("new-attempt",Instant.EPOCH,guard,new NativeRequest(command.operation().value(),Optional.empty(),new RawJson(new byte[]{'{','}'})));
        assertThrows(IllegalArgumentException.class,()->ActionTransitions.validate(Optional.of(receipt),command,receipt.bodySha256(),new ActionState.Submitting(attempt)));
        assertEquals(0,archive.packetReads);assertTrue(receipt.state() instanceof ActionState.Unknown);assertFalse(receipt.settled());
    }
    private static String originalCrownMissingResult()throws Exception {
        String repository=System.getProperty("xar.repository.root"),python=System.getProperty("xar.python");
        assertNotNull(repository,"required original repository input missing");assertNotNull(python,"required original Python oracle input missing");
        String program="""
import ast,hashlib,json,sys,types,uuid
from pathlib import Path
from typing import Mapping
p=Path(sys.argv[1])/"ck3_autonomous_player/src/xar_autoplayer/bridge/realm_law_formal_private_transport.py"
b=p.read_bytes()
assert len(b)==15534 and hashlib.sha256(b).hexdigest()=="6f54b30fde3c068bbb5427bd1d9b36cda2326b5487cb42dbfa30d687c105e6a9"
t=ast.parse(b)
class BridgeUnavailableError(Exception): pass
ns=dict(Mapping=Mapping,uuid=uuid,BridgeUnavailableError=BridgeUnavailableError)
exec(compile(ast.fix_missing_locations(ast.Module(body=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name=="_send"],type_ignores=[])),str(p),"exec"),ns)
sent=[]
class Endpoint:
 def send(self,packet): sent.append(packet)
class State:
 def wait_for_command_result(self,*args): return None
before=dict(native_revision=7,date_raw=100,played_character=dict(character_id=77))
driver=types.SimpleNamespace(endpoint=Endpoint(),state=State())
try: ns["_send"](driver,before,step="private-enact-realm-law-crown-v1",fields={},timeout_seconds=1)
except BridgeUnavailableError as error:
 assert len(sent)==1
 print(json.dumps(dict(error=str(error),class_name=type(error).__name__,sends=len(sent))))
else: raise AssertionError("original missing result accepted")
""";
        Process process=new ProcessBuilder(python,"-c",program,repository).redirectErrorStream(true).start();
        if(!process.waitFor(30,java.util.concurrent.TimeUnit.SECONDS)){process.destroyForcibly();fail("original Crown oracle timed out");}
        String output=new String(process.getInputStream().readAllBytes(),java.nio.charset.StandardCharsets.UTF_8);assertEquals(0,process.exitValue(),output);
        var result=StrictJson.parse(output.getBytes(java.nio.charset.StandardCharsets.UTF_8));assertEquals("BridgeUnavailableError",result.get("class_name").textValue());assertEquals(1,result.get("sends").intValue());return result.get("error").textValue();
    }
}
