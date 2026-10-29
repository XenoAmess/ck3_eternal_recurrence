package org.xar.ck3.control.application.history;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.history.DriverReturnedActionHistoryRowProducer.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** DATA/original custody boundaries. No test-created Source, receipt or chronology grants private Root qualification. */
final class DriverReturnedActionHistoryRowProducerTest {
    private static final Instant NOW=Instant.parse("2026-10-24T11:00:00Z");
    private static final BigInteger MAX=StrictJson.UINT64_MAX;
    private static final ExactRef CODE=ref("source-DATA-only",new byte[]{1});
    private static final String HALT="halt-army-1",SPLIT="split-army-half-2",MERGE="merge-armies-1-with-2";
    @Test void threeNormalReturnedReportsKeepTrueOkFullResultNoErrorAndExactNumberRoles(){
        for(String operation:List.of(HALT,SPLIT,MERGE)){
            Vector v=vector(operation,false);var row=v.row();
            assertTrue(row.ok());assertEquals(operation,row.command());assertFalse(row.toJson().members().containsKey("error"));
            assertEquals(v.numeric(),row.result());assertEquals(new Text("full original report"),row.result().get("original_extension"));
            assertEquals(row,DriverReturnedActionHistoryRowProducer.decode(row.encode()));assertEquals(row.index(),row.historyEntry().index());
            PublicNumbers roles=publicNumbersFromSource(row.toJson().get(SOURCE_FIELD));
            assertEquals(row.result(),roles.fromPublic(roles.toPublic(row.result())));
            assertEquals(new Text(MAX.toString()),roles.toPublic(row.result()).get("revision"));
            assertInstanceOf(IntegerValue.class,OpportunityJson.object(roles.toPublic(row.result()).get("war_action"),"war_action").get(operation.equals(HALT)?"army_id":"source_army_id"));
            assertEquals(v.source(),decodeSource(row.toJson().get(SOURCE_FIELD)));
            assertEquals(row.source().evidence().size(),new HashSet<>(row.source().evidence()).size());
            // Original normal return is ok=true even if its accepted field remains false.
            assertEquals(new Bool(false),row.result().get("accepted"));
        }
        Vector deferred=vector(HALT,true);
        assertTrue(deferred.row().ok());assertEquals(new Bool(false),deferred.numeric().get("business_submission"));
        assertEquals(deferred.row(),DriverReturnedActionHistoryRowProducer.decode(deferred.row().encode()));
    }
    @Test void falseOkExceptionsContradictoryReportsAliasesAndMissingFieldsDoNotBecomeNormalReturnedHistory(){
        Vector v=vector(MERGE,false);Obj row=v.row().toJson();Obj action=OpportunityJson.object(v.numeric().get("war_action"),"war_action");
        for(Obj changed:List.of(row.with("ok",new Bool(false)),row.with("error",new Text("not a normal return")),
                row.with("command",new Text(MERGE+":alias")),row.with("result",v.numeric().with("accepted",new Text("false"))),
                row.with("result",v.numeric().with("war_action",action.with("status",new Text("merge_applied")))),
                row.with("result",v.numeric().with("war_action",action.with("postcondition_verified",new Bool(true)))),
                row.with("result",v.numeric().with("war_action",Nil.INSTANCE))))
            assertThrows(IllegalArgumentException.class,()->DriverReturnedActionHistoryRowProducer.decode(DriverJson.encode(changed)));
        for(Value bad:List.of(new Bool(true),new Text("1"),new DecimalValue("1.0"),new IntegerValue(BigInteger.ZERO)))
            assertThrows(IllegalArgumentException.class,()->DriverReturnedActionHistoryRowProducer.decode(DriverJson.encode(row.with("index",bad))));
        var missing=new LinkedHashMap<String,Value>(row.members());missing.remove("result");
        assertThrows(IllegalArgumentException.class,()->DriverReturnedActionHistoryRowProducer.decode(DriverJson.encode(new Obj(missing))));
        assertThrows(IllegalArgumentException.class,()->requireReturnedReport(new OperationKey("query-army-strengths-v1"),v.numeric()));
        assertThrows(IllegalArgumentException.class,()->new Projection(raw(v.numeric()),new PublicNumbers(List.of()),List.of(CODE),List.of(CODE)));
        // Signed native date is retained in memory and does not become a false unsigned identity.
        var negative=action.with("submitted_date_raw",new IntegerValue(BigInteger.valueOf(-5)));
        assertDoesNotThrow(()->requireReturnedReport(new OperationKey(MERGE),v.numeric().with("war_action",negative)));
        // A true observed post in the original report does not turn its accepted=false canonical UNKNOWN into settlement.
        var originalObserved=action.with("status",new Text("merge_applied")).with("postcondition_verified",new Bool(true));
        assertDoesNotThrow(()->requireReturnedReport(new OperationKey(MERGE),v.numeric().with("war_action",originalObserved)));
        assertTrue(new RawHistoryRow(1,v.source(),v.numeric().with("war_action",originalObserved)).ok());
        assertFalse(action(MERGE,true,true,"").receipt().settled());
    }
    @Test void closedFamilySourceRequiresBasisEvidenceAndNeverAliasesOtherHistorySchemas(){
        Vector v=vector(HALT,true);Obj source=sourceJson(v.source());
        for(Obj changed:List.of(source.with("schema",new Text(DriverReturnedControlHistoryRowProducer.SOURCE_SCHEMA)),
                source.with("family",new Text("OTHER")),source.with("operation",new Text("halt-army-01")),
                source.with("projection_original",Nil.INSTANCE),source.with("projection_evidence",new Arr(List.of())),
                source.with("canonical_record",Nil.INSTANCE),source.with("outbound_bytes",new Bool(true)),
                source.with("head_sequence",new DecimalValue("3.0")),source.with("unknown",Nil.INSTANCE)))
            assertThrows(IllegalArgumentException.class,()->decodeSource(changed));
        var missing=new LinkedHashMap<String,Value>(source.members());missing.remove("projection_original");
        assertThrows(IllegalArgumentException.class,()->decodeSource(new Obj(missing)));
        assertThrows(IllegalArgumentException.class,()->DriverReturnedControlHistoryRowProducer.decode(v.row().encode()));
        assertThrows(IllegalArgumentException.class,()->DriverReadHistoryRowProducer.decode(v.row().encode()));
        assertThrows(IllegalArgumentException.class,()->DriverExecuteQueryHistoryRowProducer.decode(v.row().encode()));
        var many=new ArrayList<ExactRef>();for(int i=0;i<256;i++)many.add(new ExactRef("actual-selected-source-"+i,1,CODE.sha256()));
        assertDoesNotThrow(()->new Projection(raw(v.numeric()),v.source().publicNumbers(),many,List.of(CODE)));
        many.add(new ExactRef("overflow-source",1,CODE.sha256()));
        assertThrows(IllegalArgumentException.class,()->new Projection(raw(v.numeric()),v.source().publicNumbers(),many,List.of(CODE)));
    }
    @Test void optionalEpochManifestRoundtripsAbsentNullAndPresentWithoutCrossingStrictFields() {
        Vector v=vector(HALT,true);Obj source=sourceJson(v.source());
        var present=new HistorySource(new OperationKey(HALT),CODE,CODE,CODE,CODE,new NativeRequestChronology.PacketIdentity(4,"b".repeat(64)),
                CODE,v.source().publicNumbers(),CODE,CODE,CODE,CODE,CODE,CODE,Optional.of(CODE),CODE,3,"a".repeat(64),List.of(CODE),List.of(CODE),List.of(CODE));
        var absent=new HistorySource(new OperationKey(HALT),CODE,CODE,CODE,CODE,new NativeRequestChronology.PacketIdentity(4,"b".repeat(64)),
                CODE,v.source().publicNumbers(),CODE,CODE,CODE,CODE,CODE,CODE,Optional.<ExactRef>empty(),CODE,3,"a".repeat(64),List.of(CODE),List.of(CODE),List.of(CODE));
        assertEquals(present,decodeSource(sourceJson(present)));assertEquals(absent,decodeSource(sourceJson(absent)));
        var obj=sourceJson(absent);
        var nullEpoch=obj.with("epoch_manifest",Nil.INSTANCE);
        assertEquals(absent,decodeSource(nullEpoch));
        var missingEpoch=new LinkedHashMap<String,Value>(obj.members());missingEpoch.remove("epoch_manifest");
        assertEquals(absent,decodeSource(new Obj(missingEpoch)));
        for(Value bad:List.<Value>of(new Bool(true),new Text("epoch"),new IntegerValue(BigInteger.ONE),new Arr(List.of()),new DecimalValue("1.0"),new Obj(Map.of())))
            assertThrows(IllegalArgumentException.class,()->decodeSource(obj.with("epoch_manifest",bad)));
    }
    @Test void onlyActualAttemptAckCustodyAndTheExactHaltRefusalRemainEligibleWithoutRetry(){
        for(String operation:List.of(HALT,SPLIT,MERGE)){
            DataAction data=action(operation,true,true,"");ActionReceipt receipt=data.receipt();
            assertSame(data.attempt(),requireReturned(receipt));assertFalse(receipt.settled());assertTrue(receipt.applied().isEmpty());
            assertFalse(receipt.visibleGameplay());assertFalse(receipt.eligibleAdvance());
            assertThrows(IllegalArgumentException.class,()->ActionTransitions.validate(Optional.of(receipt),receipt.command(),receipt.bodySha256(),new ActionState.Submitting(data.attempt())));
            assertDoesNotThrow(()->ActionTransitions.validate(Optional.of(receipt),receipt.command(),receipt.bodySha256(),receipt.state()));
            assertThrows(IllegalArgumentException.class,()->requireReturned(action(operation,false,true,"").receipt()));
            var late=new ActionState.Attempt(data.attempt().requestId(),NOW.plusMillis(9),data.attempt().guard(),data.attempt().preparedRequest());
            assertThrows(IllegalArgumentException.class,()->requireReturned(receipt(data.command(),late,data.ack())));
        }
        assertDoesNotThrow(()->requireReturned(action(HALT,true,false,"CK3 halt-army command validation failed").receipt()));
        assertThrows(IllegalArgumentException.class,()->requireReturned(action(HALT,true,false,"other refusal").receipt()));
        for(String operation:List.of(SPLIT,MERGE))
            assertThrows(IllegalArgumentException.class,()->requireReturned(action(operation,true,false,"CK3 halt-army command validation failed").receipt()));
    }
    @Test void canonicalReceiptSerdeRetainsUnknownAndOriginalNativeRefusalRatherThanCreatingSettlement(){
        for(boolean nativeOk:List.of(true,false)){
            DataAction data=action(HALT,true,nativeOk,"CK3 halt-army command validation failed");DataArchive archive=new DataArchive();archive.register(data);
            ActionReceipt cold=ActionReceiptCodec.decodeReceipt(ActionReceiptCodec.encodeReceipt(data.receipt(),archive),archive);
            assertEquals(data.receipt(),cold);assertEquals(data.attempt(),requireReturned(cold));
            assertEquals(data.ack(),archive.load(archive.referenceOf(data.ack())));
            var missing=new NativeActionPort.AckReceived(data.ack().requestId(),nativeOk,data.ack().originalResultToken(),data.ack().originalFrame(),data.ack().originalPacket(),Optional.empty(),Optional.empty());
            assertThrows(IllegalArgumentException.class,()->requireReturned(receipt(data.command(),data.attempt(),missing)));
            byte[] wrong=data.ack().outbound().orElseThrow().originalPacket();wrong[0]^=1;
            var changed=new NativeActionPort.AckReceived(data.ack().requestId(),nativeOk,data.ack().originalResultToken(),data.ack().originalFrame(),data.ack().originalPacket(),
                    Optional.of(new NativeActionPort.OutboundPacket(data.ack().requestId(),wrong)),data.ack().custody());
            assertThrows(IllegalArgumentException.class,()->requireReturned(receipt(data.command(),data.attempt(),changed)));
        }
    }
    @Test void coldReplayRequiresTheActualSourceCatalogBasisAndMixedOriginalRolesWithoutNewWrites()throws Exception{
        DataAction data=action(HALT,true,true,"");DataArchive archive=new DataArchive();archive.register(data);
        var catalog=RootReadContractCatalog.staticOnly(List.of());var other=RootReadContractCatalog.staticOnly(List.of());
        var calls=new AtomicInteger();ExactRef basis=archive.preserveMaterial(raw(new Obj(Map.of("schema",new Text("software-DATA-only-no-Root-basis")))));
        Vector v=vector(HALT,false);ExactRef full=archive.preserveMaterial(raw(v.numeric()));
        Source software=new Source(){
            public ActionJournal journal(){throw new AssertionError("DATA has no journal authority");}
            public void requireOwner(DriverStateAssembler authority,ActionJournal journal,OutcomeArchive originals,RootReadContractCatalog actual){throw new AssertionError("no Root source");}
            public void requireCatalog(RootReadContractCatalog actual){StrictJson.require(actual==catalog,"foreign actual catalog");}
            public List<ExactRef> sources(){return List.of(CODE);}
            public Originals requireOriginal(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,DriverStateAssembler authority,OutcomeArchive originals,OriginalReturned token){throw new AssertionError("no private invocation");}
            public void release(OriginalReturned token){throw new AssertionError("no private invocation");}
            public Projection project(ActionReceipt receipt,OutcomeArchive originals,ExactRef actualBasis){
                calls.incrementAndGet();assertEquals(data.receipt(),receipt);assertEquals(basis,actualBasis);
                return new Projection(raw(v.numeric()),v.source().publicNumbers(),List.of(CODE),List.of(basis));
            }
        };
        HistorySource source=new HistorySource(new OperationKey(HALT),archive.receiptReferenceOf(data.receipt()),archive.record,
                archive.referenceOf(data.ack()),archive.requestReferenceOf(data.attempt().preparedRequest()),NativeRequestChronology.PacketIdentity.of(data.ack().outbound().orElseThrow().originalPacket()),
                full,v.source().publicNumbers(),CODE,CODE,CODE,CODE,CODE,CODE,CODE,basis,3,"a".repeat(64),List.of(CODE),List.of(CODE),List.of(basis));
        RawHistoryRow row=new RawHistoryRow(1,source,v.numeric());archive.preserveMaterial(RawJson.fullMaterial(row.encode()));int writes=archive.materialWrites;
        assertThrows(IllegalArgumentException.class,()->replayOriginals(archive,other,software,row));assertEquals(0,calls.get());assertEquals(writes,archive.materialWrites);
        // A receipt, report and detached basis cannot replace real before guard/Known/Native originals.
        assertThrows(IllegalArgumentException.class,()->replayOriginals(archive,catalog,software,row));assertEquals(1,calls.get());assertEquals(writes,archive.materialWrites);
        archive.materials.remove(basis);
        assertThrows(IllegalArgumentException.class,()->replayOriginals(archive,catalog,software,row));assertEquals(1,calls.get());assertEquals(writes,archive.materialWrites);
    }
    private record Vector(Obj numeric,HistorySource source,RawHistoryRow row){ }
    private static Vector vector(String operation,boolean deferred){
        var call=DriverReturnedActionHistoryMaterial.parse(new OperationKey(operation)).orElseThrow();
        var fields=new LinkedHashMap<String,Value>();fields.put("status",new Text(call instanceof DriverReturnedActionHistoryMaterial.Halt?"halt_submitted":
                call instanceof DriverReturnedActionHistoryMaterial.SplitHalf?"split_submitted":"merge_submitted"));
        fields.put(call instanceof DriverReturnedActionHistoryMaterial.Halt?"army_id":"source_army_id",new IntegerValue(BigInteger.valueOf(call.source())));
        fields.put("submitted_date_raw",new IntegerValue(BigInteger.valueOf(100)));fields.put("postcondition_verified",new Bool(false));
        if(call instanceof DriverReturnedActionHistoryMaterial.Merge merge){
            fields.put("destination_army_id",new IntegerValue(BigInteger.valueOf(merge.destination())));
            fields.put("submitted_snapshot_id",new Text("native:7"));fields.put("submitted_public_revision",new IntegerValue(MAX));
            fields.put("submitted_native_revision",new IntegerValue(BigInteger.valueOf(7)));fields.put("submitted_episode_run_id",new Text("data-episode"));
        }
        Obj numeric=new Obj(Map.of("step",new Text(operation),"accepted",new Bool(false),"backend_id",new Text("native-headless"),
                "war_action",new Obj(fields),"revision",new IntegerValue(MAX),"original_extension",new Text("full original report")));
        if(deferred){
            Obj war=new Obj(Map.of("status",new Text("halt_validator_rejected_current_route_retained"),"army_id",new IntegerValue(BigInteger.valueOf(call.source()))));
            numeric=numeric.with("schema",new Text("xar.halt-army-validator-deferred/v1")).with("status",new Text("deferred"))
                    .with("business_submission",new Bool(false)).with("replay_allowed",new Bool(false)).with("war_action",war)
                    .with("halt_rejection_evidence",new Obj(Map.of("DATA_only",new Bool(true))));
        }
        Obj exposed=numeric.with("revision",new Text(MAX.toString()));
        if(call instanceof DriverReturnedActionHistoryMaterial.Merge)
            exposed=exposed.with("war_action",OpportunityJson.object(numeric.get("war_action"),"war_action").with("submitted_public_revision",new Text(MAX.toString())));
        PublicNumbers roles=PublicNumbers.fromResults(raw(numeric),raw(exposed));ExactRef result=ref("result",DriverJson.encode(numeric));
        HistorySource source=new HistorySource(new OperationKey(operation),CODE,CODE,CODE,CODE,new NativeRequestChronology.PacketIdentity(4,"b".repeat(64)),
                result,roles,CODE,CODE,CODE,CODE,CODE,CODE,CODE,CODE,3,"a".repeat(64),List.of(CODE),List.of(CODE),List.of(CODE));
        return new Vector(numeric,source,new RawHistoryRow(1,source,numeric));
    }
    private record DataAction(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.AckReceived ack,ActionReceipt receipt){ }
    private static DataAction action(String operation,boolean custody,boolean nativeOk,String error){
        var frame=new ProposalLifecycle.ObservationIdentity("software-DATA-only",new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(133700000000000001L))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(12),BigInteger.valueOf(7),BigInteger.valueOf(100)),"native:7",MAX,"data-episode"),1);
        var source=new G2Source(frame.machineId(),NOW.toString(),"software-DATA-only",CODE);
        Obj args=new Obj(Map.of("DATA_only",new Bool(true)));
        var post=new ProposalLifecycle.ExpectedPostcondition(1,frame,source,"structural-DATA-only/v1",List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("verified"),true)));
        var command=new ActionCommand("returned-action-DATA-only",frame,source,"data-session",new OperationKey(operation),args,post,new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),NOW.plusSeconds(30));
        var guard=new GuardEvidence(frame,source,command.sessionId(),BigInteger.ONE,command.operation(),CODE,CODE,"software-DATA-only",NOW,NOW.plusSeconds(30));
        var attempt=new ActionState.Attempt("original-DATA-request",NOW.plusMillis(1),guard,new NativeRequest(operation,Optional.of("game.command.halt-army-N"),raw(args)));
        byte[] outbound=("{\"type\":\"execute_step\",\"request_id\":\""+attempt.requestId()+"\",\"step\":\""+operation+"\"}").getBytes(StandardCharsets.UTF_8);
        Obj token=new Obj(Map.of("step",new Text(operation),"accepted",new Bool(false)));
        Obj response=new Obj(Map.of("type",new Text("command_result"),"request_id",new Text(attempt.requestId()),"ok",new Bool(nativeOk)));
        response=nativeOk?response.with("result",token):response.with("error",new Text(error));
        RawJson nativeFrame=raw(response);byte[] inbound=nativeFrame.bytes();
        var transport=new NativeObservationPort.TransportSession(frame.machineId(),frame.game(),BigInteger.ONE,command.sessionId());
        var chronology=new NativeRequestChronology(transport,UUID.fromString("1c510bce-058b-4a7f-bca2-1de9a00b3abe"),attempt.requestId(),
                NativeRequestChronology.PacketIdentity.of(outbound),NativeRequestChronology.PacketIdentity.of(inbound),
                new NativeRequestChronology.Event(BigInteger.ONE,NOW.plusMillis(2)),new NativeRequestChronology.Event(BigInteger.TWO,NOW.plusMillis(3)),
                new NativeRequestChronology.Event(BigInteger.valueOf(3),NOW.plusMillis(4)));
        var ack=new NativeActionPort.AckReceived(attempt.requestId(),nativeOk,nativeOk?Optional.of(raw(token)):Optional.empty(),nativeFrame,inbound,
                custody?Optional.of(new NativeActionPort.OutboundPacket(attempt.requestId(),outbound)):Optional.empty(),custody?Optional.of(chronology):Optional.empty());
        return new DataAction(command,attempt,ack,receipt(command,attempt,ack));
    }
    private static ActionReceipt receipt(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.AckReceived ack){
        return new ActionReceipt(1,3,command,ActionCodec.bodySha256(command),new ActionState.Unknown(Optional.of(attempt),Optional.of(ack),"original normal returned DATA",List.of(CODE)));
    }
    /** In-memory original custody only; cannot mint any Session, writer transition, Native or Root authority. */
    private static final class DataArchive implements OutcomeArchive {
        private final Map<ExactRef,RawJson> materials=new HashMap<>();
        private final Map<ExactRef,NativeActionPort.DispatchOutcome> outcomes=new HashMap<>();
        private final Map<ExactRef,NativeRequest> requests=new HashMap<>();
        private final Map<ExactRef,ActionReceipt> receipts=new HashMap<>();
        private final Map<ExactRef,ActionRecord> records=new HashMap<>();
        private ExactRef record;private int materialWrites;
        void register(DataAction data){preserve(data.ack());preserveRequest(data.attempt().preparedRequest());preserveReceipt(data.receipt());record=preserveRecord(new ActionRecord(data.receipt(),Optional.empty()));}
        @Override public ExactRef preserveMaterial(RawJson raw){materialWrites++;var ref=ref("material",raw.bytes());materials.putIfAbsent(ref,raw);return ref;}
        @Override public RawJson loadMaterial(ExactRef original){return required(materials,original);}
        @Override public RawJson loadFullMaterial(ExactRef original){return required(materials,original);}
        @Override public ExactRef materialReferenceOf(RawJson raw){var ref=ref("material",raw.bytes());StrictJson.require(raw.equals(required(materials,ref)),"material missing");return ref;}
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome raw){var value=(NativeActionPort.AckReceived)raw;var ref=ref("ack",value.originalPacket());outcomes.put(ref,raw);return ref;}
        @Override public NativeActionPort.DispatchOutcome load(ExactRef original){return required(outcomes,original);}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome raw){var value=(NativeActionPort.AckReceived)raw;var ref=ref("ack",value.originalPacket());StrictJson.require(raw.equals(required(outcomes,ref)),"ACK missing");return ref;}
        @Override public ExactRef preserveRequest(NativeRequest raw){var ref=ref("request",(raw.step()+new String(raw.additionalFields().bytes(),StandardCharsets.UTF_8)).getBytes(StandardCharsets.UTF_8));requests.put(ref,raw);return ref;}
        @Override public NativeRequest loadRequest(ExactRef original){return required(requests,original);}
        @Override public ExactRef requestReferenceOf(NativeRequest raw){var ref=ref("request",(raw.step()+new String(raw.additionalFields().bytes(),StandardCharsets.UTF_8)).getBytes(StandardCharsets.UTF_8));StrictJson.require(raw.equals(required(requests,ref)),"request missing");return ref;}
        @Override public ExactRef preserveReceipt(ActionReceipt raw){var ref=ref("receipt",ActionCodec.encodeCommand(raw.command()));receipts.put(ref,raw);return ref;}
        @Override public ActionReceipt loadReceipt(ExactRef original){return required(receipts,original);}
        @Override public ExactRef receiptReferenceOf(ActionReceipt raw){var ref=ref("receipt",ActionCodec.encodeCommand(raw.command()));StrictJson.require(raw.equals(required(receipts,ref)),"receipt missing");return ref;}
        @Override public ExactRef preserveRecord(ActionRecord raw){var ref=ref("record",(raw.receipt().bodySha256()+":"+raw.receipt().sequence()).getBytes(StandardCharsets.UTF_8));records.put(ref,raw);return ref;}
        @Override public ActionRecord loadRecord(ExactRef original){return required(records,original);}
        @Override public ExactRef recordReferenceOf(ActionRecord raw){var ref=ref("record",(raw.receipt().bodySha256()+":"+raw.receipt().sequence()).getBytes(StandardCharsets.UTF_8));StrictJson.require(raw.equals(required(records,ref)),"record missing");return ref;}
        private UnsupportedOperationException unavailable(){return new UnsupportedOperationException("DATA archive has no actual Native read, writer or Root");}
        @Override public ExactRef preserveRead(PlanningReadReceipt raw){throw unavailable();}
        @Override public PlanningReadReceipt loadRead(ExactRef original){throw unavailable();}
        @Override public ExactRef readReferenceOf(PlanningReadReceipt raw){throw unavailable();}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame raw){throw unavailable();}
        @Override public byte[] loadNativeFrame(ExactRef original){throw unavailable();}
        private static <T>T required(Map<ExactRef,T> map,ExactRef ref){T value=map.get(ref);StrictJson.require(value!=null,"original DATA absent");return value;}
    }
    private static ExactRef ref(String role,byte[] bytes){return new ExactRef("software-data-only/"+role+"/"+DriverJson.sha256(bytes),bytes.length,DriverJson.sha256(bytes));}
    private static RawJson raw(Obj value){return RawJson.fullMaterial(DriverJson.encode(value));}
}
