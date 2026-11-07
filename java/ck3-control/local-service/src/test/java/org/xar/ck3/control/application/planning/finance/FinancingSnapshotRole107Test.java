package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.Method;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.feastbudget.FeastBudgetPolicy;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.warbudget.OrdinaryWarPriority;
import org.xar.ck3.control.wave2.finance.holyloan.LoanFinancingCodec;
import org.xar.ck3.control.wave2.planning.warcashprovenance.EmergencyFinancingAssessment;
import org.xar.ck3.control.wave2.planning.warcashprovenance.EmergencyFinancingAssessmentCodec;
import org.xar.ck3.control.wave2.planning.warcashprovenance.FinancingGapCodec;
import org.xar.ck3.control.wave2.planning.warcashprovenance.WarFinancingCapabilityGap;

/** Pure registered software READ packets and retained producer vectors; no live source, writer or funds authority.
 * The 139-row extension is unrelated unconsumed DATA, not a claim of this fixture's historical FinanceCurrent.
 */
final class FinancingSnapshotRole107Test {
    private static final int LIMIT=FullJsonTree.MAXIMUM_BYTES;
    private static final ExactRef REF=new ExactRef("P107-pure-software-read-definition",1,"a".repeat(64));
    private static final Instant DEADLINE=Instant.parse("2030-01-01T00:00:00Z");
    private static final G2Source SOURCE=new G2Source("p107-software-data","2026-11-08T00:00:00Z","1.20.0.4",REF);
    private static JsonNode loanOriginal;
    private static Arr unrelatedHistory;

    @BeforeAll static void retainedInputs()throws Exception {
        String[] lines=new String(gzip("/holyloan/original-v1.jsonl.gz"),StandardCharsets.UTF_8).split("\\R");
        assertEquals(314,FullJsonTree.parse(lines[940].getBytes(StandardCharsets.UTF_8),LIMIT).path("ordinal").intValue());
        JsonNode original=FullJsonTree.parse(lines[941].getBytes(StandardCharsets.UTF_8),LIMIT);
        assertEquals("financing",original.path("operation").textValue());loanOriginal=original.get("arguments");
        var driver=DriverStateSnapshot.decodeComplete(gzip("/org/xar/ck3/control/application/checkpoint/encoding102/driver1475.json.gz"));
        var rows=new ArrayList<OpportunityJson.Value>();
        for(int i=0;i<139;i++)rows.add(json(driver.commandHistory().get(i).originalRow().json()));
        unrelatedHistory=new Arr(rows);
        assertTrue(DriverJson.encode(unrelatedHistory).length>3_000_000);
    }

    @Test void publicGapAndEmergencyKeepTypedValuesWhileUnconsumedHistoryLeavesTheReceiptLane()throws Exception {
        PlanningRequest small=request();OriginalReads reads=new OriginalReads(json(FullJsonTree.encode(loanOriginal.get("cash_resources"),LIMIT)));
        var collector=collector(reads,small);var current=current(collector,small);
        byte[] currentRoot=DriverJson.encode(current.root()),priority=current.priority().toJson();
        byte[] ledger=DriverJson.encode(current.state().ledger(FinanceStatePort.Domain.CONSTRUCTION).orElseThrow().original());
        Obj smallGap=OrdinaryFinanceCollector.financingGap(small,current);
        Obj originalGap=smallGap.with("snapshot",small.observations().snapshot());
        var expected=FinancingGapCodec.decode(DriverJson.encode(originalGap));
        PlanningRequest large=withSnapshot(small,small.observations().snapshot().with("native_command_history",unrelatedHistory)
                .with("unknown_current_fact",obj("preserve_in_original",new Text("P107-not-role-data"))));
        byte[] before=DriverJson.encode(large.observations().snapshot());
        Obj largeGap=OrdinaryFinanceCollector.financingGap(large,current);
        assertEquals(expected,FinancingGapCodec.decode(DriverJson.encode(largeGap)));
        assertArrayEquals(FinancingGapCodec.encode(WarFinancingCapabilityGap.observe(expected)),
                FinancingGapCodec.encode(WarFinancingCapabilityGap.observe(FinancingGapCodec.decode(DriverJson.encode(largeGap)))));
        assertTrue(DriverJson.encode(largeGap.with("snapshot",large.observations().snapshot())).length>65536);
        assertThrows(IllegalArgumentException.class,()->FinancingGapCodec.decode(DriverJson.encode(largeGap.with("snapshot",large.observations().snapshot()))));
        assertTrue(DriverJson.encode(largeGap).length<65536);
        for(Value pending:List.of(Nil.INSTANCE,obj("status",new Text("no_pending_action")),
                obj("status",new Text("UNKNOWN"),"kind",new Text("HOLY_ORDER_LOAN"),"action_id",new Text("P107-original"),"procurement_epoch",new Text("same-epoch")))) {
            Obj reference=OrdinaryFinanceCollector.financingRequest(originalGap,Optional.empty(),pending);
            Obj actual=OrdinaryFinanceCollector.financingRequest(largeGap,Optional.empty(),pending);
            assertArrayEquals(EmergencyFinancingAssessmentCodec.evaluate(DriverJson.encode(reference)),EmergencyFinancingAssessmentCodec.evaluate(DriverJson.encode(actual)));
        }
        var prior=new OrdinaryPolicy.Draft("original-war","original-phase","original-reason",OrdinaryPolicy.Kind.ORDINARY,
                Optional.empty(),OrdinaryPolicy.Purpose.DATE_ADVANCE,Optional.empty(),obj("unknown_plan",new Text("kept")));
        var annotated=OrdinaryFinancePolicies.financingObservation(prior,largeGap,new OrdinaryFinanceCollector.Unavailable<>(new OrdinaryFinanceCollector.Missing("explicit missing CASH")));
        assertEquals(prior.command(),annotated.command());assertEquals(prior.phase(),annotated.phase());assertEquals(prior.reason(),annotated.reason());
        assertEquals(prior.detail().get("unknown_plan"),annotated.detail().get("unknown_plan"));
        var assessed=EmergencyFinancingAssessmentCodec.decodeResult(DriverJson.encode(annotated.detail().get("emergency_financing_assessment")));
        assertEquals(0,assessed.unreceivedFundingCreditedRaw());assertFalse(assessed.submitPlanned());assertFalse(assessed.optionalConstructionMayUseProspectiveFunding());
        assertArrayEquals(before,DriverJson.encode(large.observations().snapshot()));
        assertArrayEquals(currentRoot,DriverJson.encode(current.root()));assertArrayEquals(priority,current.priority().toJson());
        assertArrayEquals(ledger,DriverJson.encode(current.state().ledger(FinanceStatePort.Domain.CONSTRUCTION).orElseThrow().original()));
        assertEquals(small.observations().bridgeCapabilities(),large.observations().bridgeCapabilities());
        System.out.println("P107-public-gap-bytes full="+DriverJson.encode(largeGap.with("snapshot",large.observations().snapshot())).length+" role="+DriverJson.encode(largeGap).length);
    }

    @Test void realLoanFromCashKeepsPositiveProjectionOriginalPacketAndBuildPresenceFailures()throws Exception {
        PlanningRequest small=request();OriginalReads reads=new OriginalReads(json(FullJsonTree.encode(loanOriginal.get("cash_resources"),LIMIT)));
        var collector=collector(reads,small);var cash=assertInstanceOf(OrdinaryFinanceCollector.Cash.class,assertInstanceOf(OrdinaryFinanceCollector.Known.class,collector.cash(small)).value());
        byte[] packet=cash.original().originalFrame(),snapshot=DriverJson.encode(small.observations().snapshot());
        var base=observed(OrdinaryFinanceCollector.loanFromCash(small,new OrdinaryFinanceCollector.Known<>(cash)));
        assertInstanceOf(LoanFinancingCodec.Projected.class,base.input());
        Obj oldSmall=base.request().with("snapshot",small.observations().snapshot());
        var reference=LoanFinancingCodec.decodeAndProject(DriverJson.encode(oldSmall));
        assertArrayEquals(LoanFinancingCodec.encode(reference),LoanFinancingCodec.encode(base.input()));
        PlanningRequest large=withSnapshot(small,small.observations().snapshot().with("native_command_history",unrelatedHistory));
        byte[] largeBefore=DriverJson.encode(large.observations().snapshot());
        var result=observed(OrdinaryFinanceCollector.loanFromCash(large,new OrdinaryFinanceCollector.Known<>(cash)));
        var projected=assertInstanceOf(LoanFinancingCodec.Projected.class,result.input());
        var originalProjected=assertInstanceOf(LoanFinancingCodec.Projected.class,reference);
        assertEquals(originalProjected.planningFrame(),projected.planningFrame());assertEquals(originalProjected.observation(),projected.observation());
        assertArrayEquals(LoanFinancingCodec.encode(reference),LoanFinancingCodec.encode(result.input()));
        assertSame(cash.original(),result.original());assertEquals(1,reads.cashCalls);
        assertArrayEquals(packet,cash.original().originalFrame());assertArrayEquals(snapshot,DriverJson.encode(small.observations().snapshot()));
        assertArrayEquals(largeBefore,DriverJson.encode(large.observations().snapshot()));
        assertThrows(IllegalArgumentException.class,()->LoanFinancingCodec.decodeAndProject(DriverJson.encode(result.request().with("snapshot",large.observations().snapshot()))));
        Obj diagnostics=object(small.observations().snapshot().get("diagnostics"),"diagnostics"),hello=object(diagnostics.get("hello"),"hello");
        hello=hello.with("game_version",hello.get("expected_ck3_version")).with("executable_sha256",hello.get("expected_ck3_sha256"));
        for(String field:List.of("expected_ck3_version","expected_ck3_sha256")) {
            var changed=withSnapshot(large,large.observations().snapshot().with("diagnostics",diagnostics.with("hello",hello.with(field,Nil.INSTANCE))));
            var refused=observed(OrdinaryFinanceCollector.loanFromCash(changed,new OrdinaryFinanceCollector.Known<>(cash)));
            assertEquals(new LoanFinancingCodec.Refused(LoanFinancingCodec.Reason.CASH_UNQUALIFIED),refused.input());
            Obj originalSmallSnapshot=small.observations().snapshot().with("diagnostics",diagnostics.with("hello",hello.with(field,Nil.INSTANCE)));
            assertArrayEquals(LoanFinancingCodec.encode(LoanFinancingCodec.decodeAndProject(DriverJson.encode(refused.request().with("snapshot",originalSmallSnapshot)))),LoanFinancingCodec.encode(refused.input()));
        }
        Obj source=object(result.request().get("cash_source_frame"),"source");
        Obj sourceExtra=result.request().with("cash_source_frame",source.with("unknown_extra",new Bool(true)));
        assertEquals(new LoanFinancingCodec.Refused(LoanFinancingCodec.Reason.FRAME_UNQUALIFIED),LoanFinancingCodec.decodeAndProject(DriverJson.encode(sourceExtra)));
        Obj resources=object(result.request().get("cash_resources"),"cash");
        assertEquals(new LoanFinancingCodec.Refused(LoanFinancingCodec.Reason.FRAME_UNQUALIFIED),LoanFinancingCodec.decodeAndProject(DriverJson.encode(result.request().with("cash_resources",resources.with("queried_revision",new DecimalValue("9.0"))))));
        System.out.println("P107-public-loan-bytes full="+DriverJson.encode(result.request().with("snapshot",large.observations().snapshot())).length+" role="+DriverJson.encode(result.request()).length);
    }

    @Test void rolePreservesOriginalGoldenTypedInputsAndInvalidMemberSemantics()throws Exception {
        JsonNode corpus=FullJsonTree.parse(resource("/warcashprovenance/golden.json"),LIMIT);
        int checked=0;
        for(JsonNode vector:corpus.path("cases")) {
            Obj original=json(vector.path("request_json").textValue().getBytes(StandardCharsets.UTF_8));
            Obj projected=original.with("snapshot",project(object(original.get("snapshot"),"snapshot")));
            if(vector.has("expected_exception")) {
                var before=assertThrows(IllegalArgumentException.class,()->FinancingGapCodec.decode(DriverJson.encode(original)));
                var after=assertThrows(IllegalArgumentException.class,()->FinancingGapCodec.decode(DriverJson.encode(projected)));
                assertEquals(before.getClass(),after.getClass());assertEquals(before.getMessage(),after.getMessage());
            } else assertEquals(FinancingGapCodec.decode(DriverJson.encode(original)),FinancingGapCodec.decode(DriverJson.encode(projected)),vector.path("name").textValue());
            checked++;
        }
        assertEquals(31,checked);
        Obj sample=json(corpus.path("cases").get(0).path("request_json").textValue().getBytes(StandardCharsets.UTF_8));
        Obj snapshot=object(sample.get("snapshot"),"snapshot");
        for(Value malformed:List.of(new DecimalValue("41.0"),new Text("41"),new Bool(false))) {
            Obj original=sample.with("snapshot",snapshot.with("played_character_id",malformed));
            assertThrows(IllegalArgumentException.class,()->FinancingGapCodec.decode(DriverJson.encode(original)));
            assertThrows(IllegalArgumentException.class,()->FinancingGapCodec.decode(DriverJson.encode(original.with("snapshot",project(object(original.get("snapshot"),"snapshot"))))));
        }
        Obj topOnly=snapshot.with("played_character_id",new IntegerValue(BigInteger.valueOf(41))).with("played_character",obj("character_id",Nil.INSTANCE));
        assertTrue(FinancingGapCodec.decode(DriverJson.encode(sample.with("snapshot",project(topOnly)))).currentMaximumMaintenanceRaw().isEmpty());
        Obj wars=snapshot.with("active_wars",new Arr(List.of(Nil.INSTANCE,obj("unknown",new Text("discard only unconsumed")),obj("war_id",new DecimalValue("7.0")),obj("war_id",new Text("7")),obj("war_id",n(7)),obj("war_id",n(7)),obj("war_id",n(-1)))));
        var typed=FinancingGapCodec.decode(DriverJson.encode(sample.with("snapshot",project(wars))));
        assertEquals(Set.of(BigInteger.valueOf(7),BigInteger.valueOf(-1)),typed.activeWarIds());
        assertEquals(FinancingGapCodec.decode(DriverJson.encode(sample.with("snapshot",wars))),typed);
    }

    private static PlanningRequest request() {
        Obj snapshot=json(FullJsonTree.encode(loanOriginal.get("snapshot"),LIMIT)).with("player_armies",new Arr(List.of()))
                .with("active_event",Nil.INSTANCE).with("pending_character_interaction",Nil.INSTANCE);
        Obj actor=object(snapshot.get("played_character"),"actor"),diagnostics=object(snapshot.get("diagnostics"),"diagnostics");
        var identity=new JointBudgetSelector.Frame(integer(actor.get("character_id"),"actor"),integer(snapshot.get("native_revision"),"native"),integer(snapshot.get("date_raw"),"date"));
        var frame=new JointBudgetSelector.ProposalFrame(identity,text(snapshot.get("snapshot_id"),"snapshot"),integer(snapshot.get("revision"),"revision"),text(snapshot.get("episode_run_id"),"episode"));
        var before=new ObservationIdentity(SOURCE.machineId(),new GameGeneration(integer(diagnostics.get("bridge_pid"),"pid").intValueExact(),new PythonOnlyUInt64(BigInteger.ONE)),frame,1);
        return new PlanningRequest(before,SOURCE,"P107-component",DEADLINE,new PlanningObservation(snapshot,List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
    }
    private static PlanningRequest withSnapshot(PlanningRequest old,Obj snapshot) {
        var o=old.observations();return new PlanningRequest(old.before(),old.source(),old.sessionId(),old.deadline(),new PlanningObservation(snapshot,o.history(),o.actionSteps(),o.bridgeCapabilities(),o.battleSpeedReadiness(),o.actionFacts(),o.campaignGoal(),o.crossRunPlan(),o.initialLifestyleFocusRequired()));
    }
    private static FinanceReadContracts definitions() {return new FinanceReadContracts(query->new FinanceReadContracts.Registration(REF,new FinanceReadContracts.Permission(Optional.empty(),query.operation().value(),ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP)));}
    private static OrdinaryFinanceCollector collector(OriginalReads reads,PlanningRequest request) {
        byte[] body="{\"pending\":null}".getBytes(StandardCharsets.UTF_8);
        var reference=new ExactRef("P107-authored-construction-body",body.length,ActionCodec.sha256(body));
        var document=new FinanceStatePort.Document(FinanceStatePort.Domain.CONSTRUCTION,reference,body);
        var state=new FinanceStatePort(input->new FinanceStatePort.Head(input.before(),REF,List.of(document),List.of(),Optional.empty()),
                List.of(new FinanceStatePort.ReaderBinding(FinanceStatePort.Domain.CONSTRUCTION,REF,original->FinanceStatePort.Pending.CLEAR)));
        return new OrdinaryFinanceCollector(definitions(),reads,state);
    }
    private static OrdinaryFinanceCollector.Current current(OrdinaryFinanceCollector collector,PlanningRequest request)throws Exception {
        Obj root=json(FullJsonTree.parse(resource("/warcashprovenance/golden.json"),LIMIT).path("cases").get(0).path("request_json").textValue().getBytes(StandardCharsets.UTF_8));root=object(root.get("root"),"root");
        var packet=assertInstanceOf(FinanceReadContracts.Packet.class,assertInstanceOf(OrdinaryFinanceCollector.Known.class,collector.query(FinanceReadContracts.Query.MERCENARIES,request)).value());
        var market=NativeMercenaryMarket.decode(packet,request);
        var state=assertInstanceOf(FinanceStatePort.Known.class,collector.state(request)).snapshot();
        var spending=new FeastBudgetPolicy.Observed(new FeastBudgetPolicy.Frame(request.before().frame().identity().player(),request.before().frame().identity().nativeRevision(),request.before().frame().identity().dateRaw(),request.before().frame().snapshotId()),1,null,null);
        var priority=OrdinaryWarPriority.observe(new OrdinaryWarPriority.Input(DriverJson.encode(request.observations().snapshot()),DriverJson.encode(root)));
        return new OrdinaryFinanceCollector.Current(root,spending,obj(),market,priority,state,List.of(packet.receipt()));
    }
    private static final class OriginalReads implements PlanningReadPort {
        final Obj cash;int cashCalls;
        OriginalReads(Obj cash){this.cash=cash;}
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest input) {
            Obj result;
            if(input.operation().equals(FinanceReadContracts.Query.CASH.operation())) {cashCalls++;result=obj("step",new Text(input.operation().value()),"accepted",new Bool(true),"war_cash_current_resources",cash);}
            else {
                assertEquals(FinanceReadContracts.Query.MERCENARIES.operation(),input.operation());
                Obj market=obj("schema",new Text("ck3_12004_player_mercenary_context_v1"),"game_version",new Text("1.20.0.4"),"executable_sha256",new Text(loanOriginal.path("cash_resources").path("executable_sha256").textValue()),
                        "actor_character_id",new IntegerValue(input.before().frame().identity().player()),"date_raw",new IntegerValue(input.before().frame().identity().dateRaw()),"capture_epoch",n(1),"read_only",new Bool(true),"native_hire_mode",n(1),"available",new Bool(true),"unavailable_reason",Nil.INSTANCE,"rows",new Arr(List.of()));
                result=obj("step",new Text(input.operation().value()),"accepted",new Bool(true),"snapshot_revision",new IntegerValue(input.before().frame().identity().nativeRevision()),"player_mercenary_context",market);
            }
            byte[] frame=DriverJson.encode(obj("type",new Text("command_result"),"protocol_version",n(1),"request_id",new Text("P107-software-read"),"ok",new Bool(true),"result",result));
            byte[] packet=ByteBuffer.allocate(frame.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(frame.length).put(frame).array();
            var ack=new NativeActionPort.AckReceived("P107-software-read",true,Optional.of(new RawJson(DriverJson.encode(result))),new RawJson(frame),packet);
            var binding=new GuardEvidence(input.before(),input.source(),input.sessionId(),BigInteger.TWO,input.operation(),REF,REF,"P107-software-read-owner",DEADLINE.minusSeconds(30),DEADLINE);
            var guard=new PlanningReadGuard(binding,true,true,true,"b".repeat(64));
            var receipt=new PlanningReadReceipt(input,contract.contractId(),ack.requestId(),guard,guard,ack);
            return new PlanningReadResult.Known<>(contract.decode(receipt),receipt,REF);
        }
    }
    private static Obj project(Obj snapshot)throws Exception {Method method=OrdinaryFinanceCollector.class.getDeclaredMethod("financingSnapshot",Obj.class);method.setAccessible(true);return (Obj)method.invoke(null,snapshot);}
    private static OrdinaryFinanceCollector.LoanObservation observed(OrdinaryFinanceCollector.Read<OrdinaryFinanceCollector.LoanObservation> value){return assertInstanceOf(OrdinaryFinanceCollector.LoanObservation.class,assertInstanceOf(OrdinaryFinanceCollector.Known.class,value).value());}
    private static Obj json(byte[] bytes){return DriverJson.object(bytes,LIMIT);}
    private static IntegerValue n(long value){return new IntegerValue(BigInteger.valueOf(value));}
    private static byte[] resource(String path)throws Exception {try(var input=FinancingSnapshotRole107Test.class.getResourceAsStream(path)){assertNotNull(input,path);return input.readAllBytes();}}
    private static byte[] gzip(String path)throws Exception {try(var raw=FinancingSnapshotRole107Test.class.getResourceAsStream(path)){assertNotNull(raw,path);try(var input=new GZIPInputStream(raw)){byte[] value=input.readNBytes(8*1024*1024);assertEquals(-1,input.read());return value;}}}
}
