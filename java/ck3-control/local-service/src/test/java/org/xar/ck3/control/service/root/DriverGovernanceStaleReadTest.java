package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.governance.council.*;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.governance.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Explicit software negatives through actual contract encoders and NativeWire; no private Root or native qualification is fabricated. */
final class DriverGovernanceStaleReadTest {
    private static final String ID="software-stale-read",LEGACY="nonwar private snapshot revision is stale or malformed";
    private static ExactRef source() {return new ExactRef(Path.of("software-only/stale-source.cpp").toAbsolutePath().toString(),1,"b".repeat(64));}
    private static CrownAuthorityPolicy.Readback original()throws Exception {
        try(var input=DriverGovernanceStaleReadTest.class.getResourceAsStream("/crownauthority/original-producer-golden.json")) {
            assertNotNull(input,"required selected original Crown testresource missing");byte[] data=input.readAllBytes();
            assertEquals("1c2f7b7a9e7ba9b59b334cf340063df4dabc101d84cc688c85965e8d01e6d13c",ActionCodec.sha256(data));
            return CrownAuthorityCodec.decodeReadback(StrictJson.canonical(StrictJson.parse(data).get("cases").get(0).get("input").get("readback")));
        }
    }
    private static List<ReadContract<?>> contracts()throws Exception {
        var old=original().sourceFrame();var council=new PrivateCouncilReads(source());
        var crown=new GovernancePlanningReads(new GovernancePlanningReads.Sources(source(),source()),old.exactCk3Build(),old.exeSha256());
        return List.of(council.query(),council.gates(),crown.crown());
    }
    private static PlanningReadRequest request(ReadContract<?> contract) {
        var source=new G2Source("software-governance-stale-only",Instant.EPOCH.toString(),"software-only",source());
        var observation=new ProposalLifecycle.ObservationIdentity(source.machineId(),new GameGeneration(123,new PythonOnlyUInt64(BigInteger.ONE)),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(77),BigInteger.valueOf(7),BigInteger.valueOf(100)),"software-snapshot",BigInteger.valueOf(8),"software-episode"),1);
        var args=contract.operation().value().equals(GovernancePlanningReads.CROWN)?new OpportunityJson.Obj(java.util.Map.of()):new OpportunityJson.Obj(java.util.Map.of("position_key",new OpportunityJson.Text(CouncilModels.Position.STEWARD.key())));
        return new PlanningReadRequest(observation,source,"software-session",contract.operation(),args,Instant.parse("2026-10-24T06:30:00Z"));
    }
    private static ObjectNode negative(String error) {return StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",ID).put("ok",false).put("error",error);}
    private static NativeActionPort.AckReceived ack(ReadContract<?> contract,PlanningReadRequest request,ObjectNode frame)throws Exception {
        var prepared=contract.prepare(request,ID);byte[] outbound=NativeWire.execute(ID,prepared.step(),request.before().frame().identity().nativeRevision(),prepared.additionalFields().bytes());
        byte[] raw=StrictJson.canonical(frame);return new NativeActionPort.AckReceived(ID,false,Optional.empty(),new RawJson(raw),NativeWire.packet(raw),Optional.of(new NativeActionPort.OutboundPacket(ID,outbound)));
    }
    @Test void actualThreeEncodersAcceptOnlyExplicitPrequeueStaleNegatives()throws Exception {
        for(var contract:contracts()) {
            var request=request(contract);
            for(String error:List.of(LEGACY,LEGACY+": cause=revision_mismatch expected_revision=7 native_revision=8",LEGACY+": cause=full_snapshot_changed expected_revision=7 native_revision=7 changed_snapshot_fields=["+(char)34+"played_character_gold"+(char)34+"]")) {
                var ack=ack(contract,request,negative(error));assertTrue(RootDriverGovernancePublicService.staleRejection(ack,request,contract),error);
                assertEquals(ack.originalFrame().bytes().length+4,ack.originalPacket().length);
            }
        }
    }
    @Test void unknownFailedSourceOrNonIncreasingRevisionNeverQualifies()throws Exception {
        for(var contract:contracts()) {
            var request=request(contract);
            for(String error:List.of("unavailable",LEGACY+": cause=expected_revision_zero expected_revision=0 native_revision=8",LEGACY+": cause=previous_snapshot_missing expected_revision=7 native_revision=8",LEGACY+": cause=revision_parse_failed expected_revision=7 native_revision=8",LEGACY+": cause=current_snapshot_read_failed expected_revision=7 native_revision=8",LEGACY+": cause=revision_mismatch expected_revision=7 native_revision=7",LEGACY+": cause=revision_mismatch expected_revision=7 native_revision=6",LEGACY+": cause=revision_mismatch expected_revision=6 native_revision=8",LEGACY+": cause=revision_mismatch expected_revision=7 native_revision=18446744073709551616",LEGACY+": cause=full_snapshot_changed expected_revision=7 native_revision=7 changed_snapshot_fields=[]"))
                assertFalse(RootDriverGovernancePublicService.staleRejection(ack(contract,request,negative(error)),request,contract),error);
            var base=ack(contract,request,negative(LEGACY));
            var status=new PrivateCouncilReads(source()).status();var statusRequest=new PlanningReadRequest(request.before(),request.source(),request.sessionId(),status.operation(),new OpportunityJson.Obj(java.util.Map.of()),request.deadline());
            assertFalse(RootDriverGovernancePublicService.staleRejection(base,statusRequest,status));
            var successful=new NativeActionPort.AckReceived(ID,true,Optional.empty(),base.originalFrame(),base.originalPacket(),base.outbound());assertFalse(RootDriverGovernancePublicService.staleRejection(successful,request,contract));
            var withResult=new NativeActionPort.AckReceived(ID,false,Optional.of(new RawJson(new byte[]{'{','}'})),base.originalFrame(),base.originalPacket(),base.outbound());assertFalse(RootDriverGovernancePublicService.staleRejection(withResult,request,contract));
            var missing=new NativeActionPort.AckReceived(ID,false,Optional.empty(),base.originalFrame(),base.originalPacket());assertFalse(RootDriverGovernancePublicService.staleRejection(missing,request,contract));
            var changed=negative(LEGACY);changed.put("request_id","another-request");assertFalse(RootDriverGovernancePublicService.staleRejection(ack(contract,request,changed),request,contract));
            changed=negative(LEGACY);changed.putNull("result");assertFalse(RootDriverGovernancePublicService.staleRejection(ack(contract,request,changed),request,contract));
            changed=negative(LEGACY);changed.put("ok",true);assertFalse(RootDriverGovernancePublicService.staleRejection(ack(contract,request,changed),request,contract));
        }
    }
    @Test void exactOutboundStepFieldsAndWholePacketRemainMandatory()throws Exception {
        for(var contract:contracts()) {
            var request=request(contract);var base=ack(contract,request,negative(LEGACY));var prepared=contract.prepare(request,ID);
            for(var revision:List.of(BigInteger.valueOf(6),BigInteger.valueOf(8))) {
                byte[] wrong=NativeWire.execute(ID,prepared.step(),revision,prepared.additionalFields().bytes());
                var ack=new NativeActionPort.AckReceived(ID,false,Optional.empty(),base.originalFrame(),base.originalPacket(),Optional.of(new NativeActionPort.OutboundPacket(ID,wrong)));
                assertFalse(RootDriverGovernancePublicService.staleRejection(ack,request,contract));
            }
            byte[] another=NativeWire.execute(ID,"private-assign-councillor-v1",BigInteger.valueOf(7),prepared.additionalFields().bytes());
            var wrongStep=new NativeActionPort.AckReceived(ID,false,Optional.empty(),base.originalFrame(),base.originalPacket(),Optional.of(new NativeActionPort.OutboundPacket(ID,another)));
            assertFalse(RootDriverGovernancePublicService.staleRejection(wrongStep,request,contract));
            var extra=negative(LEGACY);extra.put("unknown",true);assertFalse(RootDriverGovernancePublicService.staleRejection(ack(contract,request,extra),request,contract));
            var nullError=negative(LEGACY);nullError.putNull("error");assertFalse(RootDriverGovernancePublicService.staleRejection(ack(contract,request,nullError),request,contract));
            String valid=new String(base.originalFrame().bytes(),java.nio.charset.StandardCharsets.UTF_8);
            // Exact form emitted by current C++ concatenation when diagnostic fields contain unescaped quotes: invalid JSON must stay unavailable.
            String malformed=valid.replace(LEGACY,LEGACY+": cause=full_snapshot_changed expected_revision=7 native_revision=7 changed_snapshot_fields=["+(char)34+"played_character_gold"+(char)34+"]");
            var badPacket=new NativeActionPort.AckReceived(ID,false,Optional.empty(),base.originalFrame(),NativeWire.packet(malformed.getBytes(java.nio.charset.StandardCharsets.UTF_8)),base.outbound());
            assertFalse(RootDriverGovernancePublicService.staleRejection(badPacket,request,contract));
            var parsed=(NativeWire.CommandResult)NativeWire.decode(base.originalPacket());assertEquals(ID,parsed.requestId());
            assertArrayEquals(base.originalFrame().bytes(),parsed.payload().value());assertEquals(NativeWire.Presence.ABSENT,parsed.result().presence());
            assertArrayEquals(base.outbound().orElseThrow().originalPacket(),NativeWire.decodeExecuteRequest(base.outbound().orElseThrow().originalPacket()).originalPacket().value());
        }
    }
    @Test void originalCouncilBindingChangesWithoutNativeGrowthButCrownStillRequiresGrowth() {
        var old=new RootDriverGovernancePublicService.ReadBinding("old",BigInteger.valueOf(8),BigInteger.valueOf(7),BigInteger.valueOf(100),true,true,BigInteger.valueOf(77),true);
        var changed=List.of(
            new RootDriverGovernancePublicService.ReadBinding("new",old.publicRevision(),old.nativeRevision(),old.dateRaw(),true,true,old.player(),true),
            new RootDriverGovernancePublicService.ReadBinding("old",BigInteger.valueOf(9),old.nativeRevision(),old.dateRaw(),true,true,old.player(),true),
            new RootDriverGovernancePublicService.ReadBinding("old",old.publicRevision(),old.nativeRevision(),BigInteger.valueOf(101),true,true,old.player(),true),
            new RootDriverGovernancePublicService.ReadBinding("old",old.publicRevision(),old.nativeRevision(),old.dateRaw(),false,true,old.player(),true),
            new RootDriverGovernancePublicService.ReadBinding("old",old.publicRevision(),old.nativeRevision(),old.dateRaw(),true,false,old.player(),true),
            new RootDriverGovernancePublicService.ReadBinding("old",old.publicRevision(),old.nativeRevision(),old.dateRaw(),true,true,BigInteger.valueOf(78),true),
            new RootDriverGovernancePublicService.ReadBinding("old",old.publicRevision(),old.nativeRevision(),old.dateRaw(),true,true,old.player(),false));
        for(String operation:List.of(CouncilPrivateCodec.QUERY,CouncilPrivateCodec.GATES)) {
            var key=new OperationKey(operation);assertFalse(RootDriverGovernancePublicService.freshReadBinding(key,old,old));
            for(var next:changed)assertTrue(RootDriverGovernancePublicService.freshReadBinding(key,old,next));
        }
        var crown=new OperationKey(GovernancePlanningReads.CROWN);
        for(var next:changed)assertFalse(RootDriverGovernancePublicService.freshReadBinding(crown,old,next));
        var advanced=new RootDriverGovernancePublicService.ReadBinding("old",old.publicRevision(),BigInteger.valueOf(8),old.dateRaw(),true,true,old.player(),true);
        assertTrue(RootDriverGovernancePublicService.freshReadBinding(crown,old,advanced));
        assertThrows(IllegalArgumentException.class,()->RootDriverGovernancePublicService.freshReadBinding(new OperationKey(GovernanceActionPreparation.CROWN),old,advanced));
    }
    @Test void actualOriginalCouncilProducerRetriesOnlyOnceAndChecksCallerRevisionOnlyInitially()throws Exception {
        String repository=System.getProperty("xar.repository.root"),python=System.getProperty("xar.python");
        assertNotNull(repository,"required original repository input missing");assertNotNull(python,"required Python oracle input missing");
        String program="""
import ast,copy,hashlib,json,sys,time,types
from pathlib import Path
from typing import Mapping
p=Path(sys.argv[1])/"ck3_autonomous_player/src/xar_autoplayer/bridge/council_private_transport_v1.py"
b=p.read_bytes()
assert len(b)==28864 and hashlib.sha256(b).hexdigest()=="89b62e3badffa378d0ef1cbb0c90ad16b939f81d4a65613ac29cbee32977edda"
t=ast.parse(b); names={"_binding","_read_identity","_source_frame","_take_snapshot","_wait_for_new_read_frame","query_council_private_v1"}
class BridgeUnavailableError(Exception): pass
class Stale(BridgeUnavailableError): pass
ns=dict(Mapping=Mapping,copy=copy,time=time,CK3_12002=types.SimpleNamespace(game_version="oracle",executable_sha256="oracle"),STEWARD_POSITION_KEY="councillor_steward",PRIVATE_QUERY_STEP="private-query-council-composition-candidates-v1",PRIVATE_GATES_STEP="private-query-council-final-gates-v1",BridgeUnavailableError=BridgeUnavailableError,_CouncilReadStaleFrameError=Stale)
ns["build_council_composition_candidates_request_v1"]=lambda **x: x
ns["normalize_council_private_query_result_v1"]=lambda *a,**k: {"status":"available"}
exec(compile(ast.fix_missing_locations(ast.Module(body=[x for x in t.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef)) and x.name in names],type_ignores=[])),str(p),"exec"),ns)
old=dict(snapshot_id="old",revision=8,native_revision=7,date_raw=100,paused=True,map_ready=True,played_character=dict(character_id=77,alive=True),episode_run_id="same",diagnostics={})
class Driver:
 command_timeout_seconds=1
 def __init__(self): self.snapshots=0;self.reads=0
 def take_snapshot(self):
  self.snapshots+=1
  return copy.deepcopy(old if self.snapshots==1 else fresh)
for step in (ns["PRIVATE_QUERY_STEP"],ns["PRIVATE_GATES_STEP"]):
 for mode in ("snapshot","public"):
  fresh=copy.deepcopy(old);fresh["snapshot_id" if mode=="snapshot" else "revision"]="fresh" if mode=="snapshot" else 9
  d=Driver()
  def read(driver,*a,**k):
   driver.reads+=1
   if driver.reads==1: raise Stale("actual first stale")
   return {}
  ns["_read_operation"]=read
  result=ns["query_council_private_v1"](d,expected_revision=8,query_step=step)
  assert d.reads==2 and d.snapshots==3 and result["queried_native_revision"]==7
  d=Driver()
  try: ns["query_council_private_v1"](d,expected_revision=99,query_step=step)
  except BridgeUnavailableError: pass
  else: raise AssertionError("initial caller mismatch accepted")
  assert d.reads==0 and d.snapshots==1
  def twice(driver,*a,**k):
   driver.reads+=1
   raise Stale("second rejection")
  ns["_read_operation"]=twice;d=Driver()
  try: ns["query_council_private_v1"](d,expected_revision=8,query_step=step)
  except Stale: pass
  else: raise AssertionError("second stale accepted")
  assert d.reads==2 and d.snapshots==2
print(json.dumps({"cases":4,"native_revision":7,"max_reads":2,"mismatch_reads":0}))
""";
        Process process=new ProcessBuilder(python,"-c",program,repository).redirectErrorStream(true).start();
        if(!process.waitFor(30,java.util.concurrent.TimeUnit.SECONDS)){process.destroyForcibly();fail("original oracle timed out");}
        String output=new String(process.getInputStream().readAllBytes(),java.nio.charset.StandardCharsets.UTF_8);
        assertEquals(0,process.exitValue(),output);var result=StrictJson.parse(output.getBytes(java.nio.charset.StandardCharsets.UTF_8));
        assertEquals(4,result.get("cases").intValue());assertEquals(2,result.get("max_reads").intValue());assertEquals(0,result.get("mismatch_reads").intValue());
    }
}
