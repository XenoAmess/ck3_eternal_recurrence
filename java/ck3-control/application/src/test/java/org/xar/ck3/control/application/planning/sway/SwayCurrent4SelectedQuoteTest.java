package org.xar.ck3.control.application.planning.sway;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual archived Native query through SelectedStart's pure original-quote boundary. No writer session. */
final class SwayCurrent4SelectedQuoteTest {
    private static final ExactRef SOURCE=new ExactRef("software:selected-quote-source",1,"a".repeat(64));
    private static final Instant NOW=Instant.parse("2026-10-30T00:00:00Z");
    @Test void actualNativeQueryIsRecomputedBySelectedQuoteAndOriginalCommandChecks() throws Exception {
        byte[] original=originalQuery();JsonNode packet=StrictJson.parse(original),body=packet.at("/result/active_scheme_sway");
        var id=new JointBudgetSelector.Frame(body.get("actor_character_id").bigIntegerValue(),body.get("snapshot_revision").bigIntegerValue(),body.get("date_raw").bigIntegerValue());
        var frame=new JointBudgetSelector.ProposalFrame(id,"software-selected-quote-snapshot",BigInteger.valueOf(9),"software-selected-quote-episode");
        var before=new ObservationIdentity("xenoamess-full-tower-eb9d2c1186",new GameGeneration(73,new PythonOnlyUInt64(new BigInteger("134370000000000074"))),frame,1);
        var source=new G2Source(before.machineId(),NOW.toString(),SwayNativeWire.BUILD,SOURCE);
        var definition=SwayNativeBindings.target(SOURCE,0);var args=StrictJson.object();args.put("target_character_id",0);
        var request=new PlanningReadRequest(before,source,"software-selected-quote-session",definition.operation(),obj(args),NOW.plusSeconds(30));
        var evidence=new GuardEvidence(before,source,request.sessionId(),BigInteger.ONE,definition.operation(),SOURCE,SOURCE,"software-selected-quote-authority",NOW,NOW.plusSeconds(30));
        var guard=new PlanningReadGuard(evidence,true,true,true,"b".repeat(64));
        var dispatch=new NativeActionPort.AckReceived(packet.get("request_id").textValue(),true,Optional.of(raw((ObjectNode)packet.get("result"))),new RawJson(original),original);
        var read=new PlanningReadReceipt(request,definition.contractId(),dispatch.requestId(),guard,guard,dispatch);
        var readRef=new ExactRef("software:actual-selected-query-original",original.length,ActionCodec.sha256(original));
        var dispatchRef=new ExactRef("software:actual-selected-native-dispatch",original.length,ActionCodec.sha256(original));
        var archive=new Archive(readRef,dispatchRef,read);var typed=definition.decode(read);
        var quote=new SwayDriverCodec.Quote(frame.revision(),0,readRef,SwayDriverCodec.quote(read,typed,readRef));
        assertEquals(typed,SwaySelectedStart.verifyQuote(quote,archive));
        var input=new SwayDriverCodec.StartRequest(quote,"sway-selected-quote-test");
        var commandArgs=StrictJson.object();commandArgs.put("schema",SwayNativeBindings.PUBLIC_START_ARGUMENTS);commandArgs.put("target_character_id",0);commandArgs.set("original_target_read",readRef.toJson());
        var expected=new ExpectedPostcondition(1,before,source,SwayActionLifecycle.START_OBSERVER,List.of(new ExpectedBoolean(new FieldKey("sway.exact_active_observed"),true)));
        var command=new ActionCommand(input.actionId(),before,source,request.sessionId(),new OperationKey(SwayNativeWire.START+0),obj(commandArgs),expected,new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),NOW.plusSeconds(30));
        var intended=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.IntentDurable());
        SwaySelectedStart.requireOriginalCommand(intended,input,archive);assertFalse(intended.eligibleAdvance());
        ObjectNode changed=(ObjectNode)StrictJson.parse(quote.presentation().bytes());changed.put("target_opinion_of_actor",38);
        var modified=new SwayDriverCodec.Quote(quote.expectedRevision(),0,readRef,raw(changed));
        assertThrows(IllegalArgumentException.class,()->SwaySelectedStart.verifyQuote(modified,archive),"whole original quote must be recomputed");
        assertThrows(IllegalArgumentException.class,()->SwaySelectedStart.requireOriginalCommand(intended,new SwayDriverCodec.StartRequest(quote,"sway-different-original-id"),archive));
    }
    private static byte[] originalQuery() throws Exception {
        try(var in=SwayCurrent4SelectedQuoteTest.class.getResourceAsStream("/sway/m6-native-current4-action-route.json")) {
            assertNotNull(in,"actual four Native route packets are mandatory");
            for(JsonNode row:StrictJson.parse(in.readAllBytes()))if("query".equals(row.get("role").textValue())) {
                byte[] bytes=row.get("original_utf8").textValue().getBytes(StandardCharsets.UTF_8);assertEquals(row.get("sha256").textValue(),ActionCodec.sha256(bytes));return bytes;
            }
            throw new AssertionError("missing Native query");
        }
    }
    private static RawJson raw(ObjectNode row){return new RawJson(StrictJson.canonical(row,SwayNativeWire.MAX));}
    private static OpportunityJson.Obj obj(ObjectNode row){return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(row)),"actual selected quote arguments");}
    private static final class Archive implements ActionPorts.OutcomeArchive {
        private final ExactRef readRef,dispatchRef;private final PlanningReadReceipt read;
        Archive(ExactRef readRef,ExactRef dispatchRef,PlanningReadReceipt read){this.readRef=readRef;this.dispatchRef=dispatchRef;this.read=read;}
        @Override public PlanningReadReceipt loadRead(ExactRef ref){assertEquals(readRef,ref);return read;}
        @Override public ExactRef readReferenceOf(PlanningReadReceipt value){assertEquals(read,value);return readRef;}
        @Override public NativeActionPort.DispatchOutcome load(ExactRef ref){assertEquals(dispatchRef,ref);return read.original();}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value){assertEquals(read.original(),value);return dispatchRef;}
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value){throw new AssertionError();}
        @Override public ExactRef preserveRequest(NativeRequest value){throw new AssertionError();}
        @Override public NativeRequest loadRequest(ExactRef ref){throw new AssertionError();}
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
