package org.xar.ck3.control.application.history;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.history.DriverExecuteQueryHistoryRowProducer.*;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Software source-owned DATA projector/archive only. No actual Native service, writer or Root permit is supplied. */
final class DriverExecuteQueryHistoryRowProducerTest {
    @TempDir Path temporary;
    @Test void installedPureProjectorRetainsWholeReportBeforeRowAndColdReplayNeverQueriesOrPreserves()throws Exception {
        for(boolean career:List.of(false,true)) {
            Fixture f=fixture("whole-"+career,career,true);int before=f.archive.materialWrites.size();
            Candidate actual=prepare(f);assertEquals(before+2,f.archive.materialWrites.size());
            assertEquals(f.project(f.receipt).fullResult(),f.archive.materialWrites.get(before));
            assertEquals(new RawJson(actual.row().encode()),f.archive.materialWrites.get(before+1));
            assertNotEquals(actual.row().command(),f.operation.value());assertEquals(new Text(f.operation.value()),actual.row().result().get("step"));
            assertEquals(new Text("full original body retained"),actual.row().result().get("unrelated_original_extension"));
            assertEquals(f.receipt.requestId(),actual.source().original().requestId());assertEquals(f.readReference,actual.readReference());
            assertEquals(f.source,actual.definitionSource());assertEquals(f.decoder,actual.decoderSource());
            assertTrue(actual.source().supportingEvidence().containsAll(List.of(f.nativeReference,f.helloReference,f.supportReference,f.readReference,f.ackReference,actual.fullResultReference(),f.source,f.decoder)));
            assertEquals(actual.row(),DriverExecuteQueryHistoryRowProducer.decode(actual.row().encode()));
            assertEquals(actual.row().index(),actual.historyEntry().index());
            assertEquals(actual,DriverExecuteQueryHistoryRowProducer.replay(f.archive,f.catalog,f.contract,f.known,actual));
            assertEquals(actual.row(),DriverExecuteQueryHistoryRowProducer.replayOriginals(f.archive,f.catalog,actual.row()));
            PlanningReadResult.Known<SoftwareValue> old=DriverExecuteQueryHistoryRowProducer.replayCanonical(f.archive,f.catalog,f.contract,actual.row());
            assertEquals(f.known,old);assertEquals(before+2,f.archive.materialWrites.size());assertEquals(0,f.liveDecoderCalls.get());assertEquals(0,f.nativeRequests.get());
            PublicNumbers roles=DriverExecuteQueryHistoryRowProducer.publicNumbersFromSource(actual.row().toJson().get(DriverExecuteQueryHistoryRowProducer.SOURCE_FIELD));
            Obj exposed=roles.toPublic(actual.row().result());assertEquals(new Text(StrictJson.UINT64_MAX.toString()),exposed.get("native_report_counter"));
            assertEquals(new Text(StrictJson.UINT64_MAX.toString()),exposed.get("query_sequence"));assertEquals(actual.row().result(),roles.fromPublic(exposed));
            assertEquals(actual.row().result(),DriverJson.object(f.archive.loadMaterial(actual.fullResultReference()).bytes(),RawJson.MAXIMUM_BYTES));
        }
    }
    @Test void missingNativeSequenceStaysExplicitNullAndPublicSourceHeaderRemainsClosed()throws Exception {
        Fixture f=fixture("no-sequence",false,false);Candidate actual=prepare(f);assertEquals(Optional.empty(),actual.source().querySequence());
        Obj body=actual.row().toJson(),source=OpportunityJson.object(body.get(DriverExecuteQueryHistoryRowProducer.SOURCE_FIELD),"source");
        assertEquals(Nil.INSTANCE,source.get("query_sequence"));assertFalse(actual.row().result().members().containsKey("query_sequence"));
        assertEquals(actual.row(),DriverExecuteQueryHistoryRowProducer.decode(actual.row().encode()));
        for(Obj changed:List.of(source.with("kind",new Text("ARMY_STRENGTHS")),source.with("schema",new Text("xar.driver-rich-read-history-source/v1")),source.with("unknown_extension",Nil.INSTANCE))) {
            assertThrows(IllegalArgumentException.class,()->DriverExecuteQueryHistoryRowProducer.publicNumbersFromSource(changed));
            assertThrows(IllegalArgumentException.class,()->DriverExecuteQueryHistoryRowProducer.decode(OpportunityJson.encode(body.with(DriverExecuteQueryHistoryRowProducer.SOURCE_FIELD,changed))));
        }
        var missing=new LinkedHashMap<String,Value>(source.members());missing.remove("query_sequence");
        assertThrows(IllegalArgumentException.class,()->DriverExecuteQueryHistoryRowProducer.decode(OpportunityJson.encode(body.with(DriverExecuteQueryHistoryRowProducer.SOURCE_FIELD,new Obj(missing)))));
        for(Value wrong:List.of(new Bool(true),new Text("1"),new DecimalValue("1.0"),new IntegerValue(BigInteger.ZERO),new IntegerValue(StrictJson.UINT64_MAX.add(BigInteger.ONE))))
            assertThrows(IllegalArgumentException.class,()->DriverExecuteQueryHistoryRowProducer.decode(OpportunityJson.encode(body.with(DriverExecuteQueryHistoryRowProducer.SOURCE_FIELD,source.with("query_sequence",wrong)))));
    }
    @Test void foreignCatalogContractKnownValueSourceAndGuardOriginalsFailBeforeFirstNewMaterial()throws Exception {
        Fixture f=fixture("foreign",false,true);int before=f.archive.materialWrites.size();
        ReadContract<SoftwareValue> duplicate=f.contract();
        assertThrows(IllegalArgumentException.class,()->DriverExecuteQueryHistoryRowProducer.prepare(f.archive,f.catalog,duplicate,f.known,1,List.of(f.source)));
        assertThrows(IllegalArgumentException.class,()->DriverExecuteQueryHistoryRowProducer.prepare(f.archive,RootReadContractCatalog.staticOnly(List.of(duplicate)),f.contract,f.known,1,List.of(f.source)));
        var changedValue=new PlanningReadResult.Known<>(new SoftwareValue(raw(nativeResult(f.receipt).with("unrelated_original_extension",new Text("changed")))),f.receipt,f.readReference);
        assertThrows(IllegalArgumentException.class,()->DriverExecuteQueryHistoryRowProducer.prepare(f.archive,f.catalog,f.contract,changedValue,1,List.of(f.source)));
        assertThrows(IllegalArgumentException.class,()->DriverExecuteQueryHistoryRowProducer.prepare(f.archive,f.catalog,f.contract,f.known,1,List.of()));
        ExactRef wrongSource=new ExactRef(f.source.path(),f.source.bytes(),"f".repeat(64));
        assertThrows(IllegalArgumentException.class,()->DriverExecuteQueryHistoryRowProducer.prepare(f.archive,f.catalog,f.contract,f.known,1,List.of(wrongSource)));
        byte[] saved=f.archive.packets.remove(f.helloReference);
        assertThrows(IllegalArgumentException.class,()->prepare(f));f.archive.packets.put(f.helloReference,saved);
        f.archive.packets.put(f.nativeReference,"foreign snapshot".getBytes(StandardCharsets.UTF_8));
        assertThrows(IllegalArgumentException.class,()->prepare(f));
        assertEquals(before,f.archive.materialWrites.size());assertEquals(0,f.liveDecoderCalls.get());assertEquals(0,f.nativeRequests.get());
    }
    @Test void coldReplayRequiresBothArtifactsOriginalReadAckAndNamespaceWithoutWritingReplacement()throws Exception {
        Fixture f=fixture("cold-missing",true,true);Candidate actual=prepare(f);int writes=f.archive.materialWrites.size();
        RawJson full=f.archive.materials.remove(actual.fullResultReference());assertThrows(IllegalArgumentException.class,()->DriverExecuteQueryHistoryRowProducer.replayOriginals(f.archive,f.catalog,actual.row()));f.archive.materials.put(actual.fullResultReference(),full);
        RawJson row=f.archive.materials.remove(actual.rowReference());assertThrows(IllegalArgumentException.class,()->DriverExecuteQueryHistoryRowProducer.replayOriginals(f.archive,f.catalog,actual.row()));f.archive.materials.put(actual.rowReference(),row);
        PlanningReadReceipt read=f.archive.reads.remove(f.readReference);assertThrows(IllegalArgumentException.class,()->DriverExecuteQueryHistoryRowProducer.replayOriginals(f.archive,f.catalog,actual.row()));f.archive.reads.put(f.readReference,read);
        NativeActionPort.DispatchOutcome ack=f.archive.outcomes.remove(f.ackReference);assertThrows(IllegalArgumentException.class,()->DriverExecuteQueryHistoryRowProducer.replayOriginals(f.archive,f.catalog,actual.row()));f.archive.outcomes.put(f.ackReference,ack);
        ExactRef foreign=new ExactRef("foreign-same-bytes/"+actual.fullResultReference().sha256(),actual.fullResultReference().bytes(),actual.fullResultReference().sha256());
        Source s=actual.source();var support=new ArrayList<>(s.supportingEvidence());support.remove(s.fullResult());support.add(foreign);
        Source changed=new Source(s.original(),s.logicalOperation(),s.originalCommand(),s.sourceFrame(),s.source(),s.sessionId(),s.connectionGeneration(),s.querySequence(),s.arguments(),foreign,s.publicNumbers(),support,s.producerSources(),s.projectionSources());
        RawHistoryRow foreignRow=new RawHistoryRow(actual.row().index(),actual.row().command(),true,actual.row().result(),changed);
        assertThrows(IllegalArgumentException.class,()->DriverExecuteQueryHistoryRowProducer.replayOriginals(f.archive,f.catalog,foreignRow));
        assertEquals(writes,f.archive.materialWrites.size());assertEquals(0,f.liveDecoderCalls.get());assertEquals(0,f.nativeRequests.get());
    }
    @Test void fullReportLogicalStepAndEncodedArgumentsCannotBeAliasedOrReplacedByAnArbitraryQuery()throws Exception {
        Fixture f=fixture("operation-roles",false,true);Candidate actual=prepare(f);RawHistoryRow row=actual.row();Source source=row.source();
        assertThrows(IllegalArgumentException.class,()->new RawHistoryRow(row.index(),source.logicalOperation().value(),true,row.result(),source));
        assertThrows(IllegalArgumentException.class,()->new RawHistoryRow(row.index(),row.command(),false,row.result(),source));
        assertThrows(IllegalArgumentException.class,()->new RawHistoryRow(row.index(),row.command(),true,row.result().with("step",new Text(row.command())),source));
        assertThrows(IllegalArgumentException.class,()->new RawHistoryRow(row.index(),row.command(),true,row.result().with("query_sequence",new IntegerValue(BigInteger.ONE)),source));
        Obj body=row.toJson(),header=OpportunityJson.object(body.get(DriverExecuteQueryHistoryRowProducer.SOURCE_FIELD),"source");
        Obj unknown=header.with("logical_operation",new Text("query-zhongguo-unregistered-v1"));
        assertThrows(IllegalArgumentException.class,()->DriverExecuteQueryHistoryRowProducer.decode(OpportunityJson.encode(body.with(DriverExecuteQueryHistoryRowProducer.SOURCE_FIELD,unknown))));
        var mutated=row.result().with("unrelated_original_extension",new Text("truncated or substituted"));
        RawHistoryRow changed=new RawHistoryRow(row.index(),row.command(),true,mutated,source);
        assertThrows(IllegalArgumentException.class,()->DriverExecuteQueryHistoryRowProducer.replayOriginals(f.archive,f.catalog,changed));
        assertThrows(IllegalArgumentException.class,()->DriverReadHistoryRowProducer.decode(row.encode()));
        assertThrows(IllegalArgumentException.class,()->DriverArmySummaryHistoryRowProducer.decode(row.encode()));
    }
    @Test void originalProducerSourceAndSupportingMaterialDriftRemainColdFailures()throws Exception {
        Fixture f=fixture("source-drift",false,true);Candidate actual=prepare(f);int writes=f.archive.materialWrites.size();
        RawJson retained=f.archive.materials.put(f.supportReference,raw(new Obj(Map.of("guard_basis",new Text("foreign")))));
        assertThrows(IllegalArgumentException.class,()->DriverExecuteQueryHistoryRowProducer.replayOriginals(f.archive,f.catalog,actual.row()));f.archive.materials.put(f.supportReference,retained);
        Files.writeString(Path.of(f.source.path()),"changed source producer");
        assertThrows(IllegalArgumentException.class,()->DriverExecuteQueryHistoryRowProducer.replayOriginals(f.archive,f.catalog,actual.row()));
        assertEquals(writes,f.archive.materialWrites.size());assertEquals(0,f.nativeRequests.get());
    }
    @Test void coldCatalogCannotChangeLocalPermissionCapabilityOrKeyBeforePureProjection()throws Exception {
        Fixture f=fixture("local-permission",false,true);Candidate actual=prepare(f);int writes=f.archive.materialWrites.size(),projections=f.projectionCalls.get();
        for(ReadContract<SoftwareValue> changed:List.of(f.contract(ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,"software-execute-query-data"),
                f.contract(ReadContract.PermissionMode.ADVERTISED_CAPABILITY,"another-local-permission-key"))) {
            var foreign=new RootReadContractCatalog(List.of(new RootReadContractCatalog.InstalledRead(changed,f.decoder)),List.of());
            assertThrows(IllegalArgumentException.class,()->DriverExecuteQueryHistoryRowProducer.replayOriginals(f.archive,foreign,actual.row()));
            assertThrows(IllegalArgumentException.class,()->DriverExecuteQueryHistoryRowProducer.replayCanonical(f.archive,foreign,changed,actual.row()));
        }
        assertEquals(writes,f.archive.materialWrites.size());assertEquals(projections,f.projectionCalls.get());assertEquals(0,f.nativeRequests.get());
        Obj body=actual.row().toJson(),source=OpportunityJson.object(body.get(DriverExecuteQueryHistoryRowProducer.SOURCE_FIELD),"source");
        Obj original=OpportunityJson.object(source.get("original"),"original local binding");
        for(Obj changed:List.of(original.with("permission_mode",new Text("UNKNOWN")),original.with("required_capability",new Bool(true)),
                original.with("wire_profile",new Text(ReadContract.WireProfile.G2_PRIVATE_QUERY.name()))))
            assertThrows(IllegalArgumentException.class,()->DriverExecuteQueryHistoryRowProducer.decode(OpportunityJson.encode(body.with(DriverExecuteQueryHistoryRowProducer.SOURCE_FIELD,source.with("original",changed)))));
    }

    private Candidate prepare(Fixture f)throws IOException{return DriverExecuteQueryHistoryRowProducer.prepare(f.archive,f.catalog,f.contract,f.known,1,List.of(f.source,f.decoder));}
    private Fixture fixture(String name,boolean career,boolean sequence)throws IOException {
        Path root=Files.createDirectory(temporary.resolve(name));Path source=Files.writeString(root.resolve("software-owning-source.txt"),"fixed pure DATA decoder/projector; not an installed Native source");
        Path decoder=Files.writeString(root.resolve("software-decoder-source.txt"),"fixed typed software response DATA");
        return new Fixture(reference(source),reference(decoder),career,sequence);
    }
    private record SoftwareValue(RawJson original){ }
    private static final class Fixture {
        private final ExactRef source,decoder,nativeReference,helloReference,supportReference,readReference,ackReference;
        private final boolean career;private final OperationKey operation;
        private final SoftwareArchive archive=new SoftwareArchive();
        private final AtomicInteger liveDecoderCalls=new AtomicInteger(),nativeRequests=new AtomicInteger(),projectionCalls=new AtomicInteger();
        private final ReadContract<SoftwareValue> contract;private final RootReadContractCatalog catalog;
        private final PlanningReadReceipt receipt;private final PlanningReadResult.Known<SoftwareValue> known;
        private Fixture(ExactRef source,ExactRef decoder,boolean career,boolean sequence) {
            this.source=source;this.decoder=decoder;this.career=career;
            operation=new OperationKey(career?"query-zhongguo-workforce-owner-snapshot-v1":"query-zhongguo-b1-cycle-snapshot-v1");
            contract=contract();catalog=new RootReadContractCatalog(List.of(new RootReadContractCatalog.InstalledRead(contract,decoder)),List.of());
            var frame=new ObservationIdentity("execute-query-software-only",new GameGeneration(23456,new PythonOnlyUInt64(StrictJson.UINT64_MAX)),
                    new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(12),BigInteger.valueOf(21),BigInteger.valueOf(53290200)),"software-snapshot",BigInteger.valueOf(19),"software-episode"),1);
            var g2=new G2Source(frame.machineId(),"2026-10-24T09:00:00Z","software-only",source);Instant observed=Instant.parse("2026-10-24T09:00:00Z");
            Obj args=new Obj(Map.of("request_nonce",new Text("a1")));if(career)args=args.with("owner_id",new IntegerValue(BigInteger.valueOf(12)));
            var request=new PlanningReadRequest(frame,g2,"software-session",operation,args,observed.plusSeconds(30));
            nativeReference=archive.packet("native","unqualified software native snapshot bytes");helloReference=archive.packet("hello","unqualified software HELLO bytes");
            supportReference=archive.preserveMaterial(raw(new Obj(Map.of("guard_basis",new Text("software DATA, no writer ancestry claim")))));
            var guardEvidence=new GuardEvidence(frame,g2,"software-session",StrictJson.UINT64_MAX,operation,nativeReference,helloReference,"software-only-authority",observed,request.deadline(),List.of(supportReference));
            var guard=new PlanningReadGuard(guardEvidence,true,true,true,"1".repeat(64));
            Obj original=new Obj(Map.of("step",new Text(operation.value()),"snapshot_revision",new IntegerValue(BigInteger.valueOf(21)),"accepted",new Bool(true),"status",new Text("software-data"),
                    "unrelated_original_extension",new Text("full original body retained"),"request_nonce",new Text("a1"),"native_report_counter",new IntegerValue(StrictJson.UINT64_MAX)));
            if(sequence)original=original.with("query_sequence",new IntegerValue(StrictJson.UINT64_MAX));if(career)original=original.with("owner_id",new IntegerValue(BigInteger.valueOf(12)));
            RawJson token=raw(original);RawJson ackFrame=raw(new Obj(Map.of("type",new Text("command_result"),"request_id",new Text("original-software-read"),"ok",new Bool(true),"result",original)));
            var ack=new NativeActionPort.AckReceived("original-software-read",true,Optional.of(token),ackFrame,ackFrame.bytes());
            ackReference=archive.preserve(ack);receipt=new PlanningReadReceipt(request,contract.contractId(),ack.requestId(),guard,guard,ack);
            readReference=archive.preserveRead(receipt);known=new PlanningReadResult.Known<>(decodeOriginal(receipt),receipt,readReference);
        }
        private ReadContract<SoftwareValue> contract() {
            return contract(ReadContract.PermissionMode.ADVERTISED_CAPABILITY,"software-execute-query-data");
        }
        private ReadContract<SoftwareValue> contract(ReadContract.PermissionMode mode,String permissionKey) {
            Optional<String> capability=mode==ReadContract.PermissionMode.ADVERTISED_CAPABILITY?Optional.of("game.command."+operation.value()):Optional.empty();
            var base=new ReadContract<SoftwareValue>("software-execute-query-"+(career?"career":"cases"),operation,capability,permissionKey,
                    mode,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,
                    (request,id)->{nativeRequests.incrementAndGet();throw new AssertionError("history producer must not prepare a Native request");},
                    original->{liveDecoderCalls.incrementAndGet();throw new AssertionError("history producer must not call live decode");},this::decodeOriginal);
            return base.withOriginalHistoryProjection(Kind.PUBLIC_EXECUTE_QUERY,(original,typed)->{
                assertEquals(decodeOriginal(original),typed);return project(original);
            });
        }
        private SoftwareValue decodeOriginal(PlanningReadReceipt original) {
            Obj token=nativeResult(original);
            StrictJson.require(new Text(operation.value()).equals(token.get("step"))&&original.request().arguments().get("request_nonce").equals(token.get("request_nonce")),"software typed decoder rejected original operation/nonce");
            if(career)StrictJson.require(original.request().arguments().get("owner_id").equals(token.get("owner_id")),"software typed decoder rejected original owner");
            return new SoftwareValue(raw(token));
        }
        private ExecuteProjection project(PlanningReadReceipt original) {
            projectionCalls.incrementAndGet();
            Obj report=DriverJson.object(decodeOriginal(original).original().bytes(),RawJson.MAXIMUM_BYTES);
            String nonce=OpportunityJson.text(original.request().arguments().get("request_nonce"),"software nonce");
            String tail=java.util.HexFormat.of().formatHex(nonce.getBytes(StandardCharsets.US_ASCII));
            if(career)tail=OpportunityJson.integer(original.request().arguments().get("owner_id"),"software owner").toString()+"-"+tail;
            OperationKey encoded=new OperationKey(operation.value()+"-"+tail);
            Obj publicReport=report.with("native_report_counter",new Text(StrictJson.UINT64_MAX.toString()));
            if(report.members().containsKey("query_sequence"))publicReport=publicReport.with("query_sequence",new Text(StrictJson.UINT64_MAX.toString()));
            return new ExecuteProjection(operation,encoded,raw(report),PublicNumbers.fromResults(raw(report),raw(publicReport)),List.of(source,decoder));
        }
    }
    /** In-memory custody test double only; it cannot mint a Session, Native receipt or Root qualification. */
    private static final class SoftwareArchive implements ActionPorts.OutcomeArchive {
        private final Map<ExactRef,RawJson> materials=new HashMap<>();private final Map<ExactRef,PlanningReadReceipt> reads=new HashMap<>();
        private final Map<ExactRef,NativeActionPort.DispatchOutcome> outcomes=new HashMap<>();private final Map<ExactRef,byte[]> packets=new HashMap<>();
        private final List<RawJson> materialWrites=new ArrayList<>();
        private ExactRef ref(String kind,byte[] bytes){return new ExactRef("software-data-only/"+kind+"/"+DriverJson.sha256(bytes),bytes.length,DriverJson.sha256(bytes));}
        private ExactRef packet(String role,String text){byte[] bytes=text.getBytes(StandardCharsets.UTF_8);ExactRef reference=ref(role,bytes);packets.put(reference,bytes);return reference;}
        @Override public byte[] readOriginalPacket(ExactRef reference){byte[] bytes=packets.get(reference);if(bytes==null)throw new IllegalArgumentException("software original packet missing");return bytes.clone();}
        @Override public ExactRef preserveMaterial(RawJson value){ExactRef reference=ref("material",value.bytes());materialWrites.add(value);materials.putIfAbsent(reference,value);return reference;}
        @Override public RawJson loadMaterial(ExactRef reference){RawJson value=materials.get(reference);if(value==null)throw new IllegalArgumentException("software original material missing");return value;}
        @Override public ExactRef materialReferenceOf(RawJson value){ExactRef reference=ref("material",value.bytes());if(!value.equals(materials.get(reference)))throw new IllegalArgumentException("software material was not preserved");return reference;}
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value){var ack=(NativeActionPort.AckReceived)value;ExactRef reference=ref("ack",ack.originalPacket());outcomes.put(reference,value);return reference;}
        @Override public NativeActionPort.DispatchOutcome load(ExactRef reference){var value=outcomes.get(reference);if(value==null)throw new IllegalArgumentException("software original ACK missing");return value;}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value){var ack=(NativeActionPort.AckReceived)value;ExactRef reference=ref("ack",ack.originalPacket());if(!value.equals(outcomes.get(reference)))throw new IllegalArgumentException("software ACK was not preserved");return reference;}
        @Override public ExactRef preserveRead(PlanningReadReceipt value){ExactRef reference=ref("read",readBytes(value));reads.put(reference,value);return reference;}
        @Override public PlanningReadReceipt loadRead(ExactRef reference){var value=reads.get(reference);if(value==null)throw new IllegalArgumentException("software original read missing");return value;}
        @Override public ExactRef readReferenceOf(PlanningReadReceipt value){ExactRef reference=ref("read",readBytes(value));if(!value.equals(reads.get(reference)))throw new IllegalArgumentException("software read was not preserved");return reference;}
        private byte[] readBytes(PlanningReadReceipt value){return (value.contractId()+"\n"+value.requestId()+"\n"+DriverJson.sha256(value.original().originalPacket())).getBytes(StandardCharsets.UTF_8);}
        private UnsupportedOperationException unavailable(){return new UnsupportedOperationException("software DATA archive cannot submit, mutate a writer or fabricate a current authority");}
        @Override public ExactRef preserveRequest(NativeRequest value){throw unavailable();}
        @Override public NativeRequest loadRequest(ExactRef reference){throw unavailable();}
        @Override public ExactRef requestReferenceOf(NativeRequest value){throw unavailable();}
        @Override public ExactRef preserveRecord(ActionRecord value){throw unavailable();}
        @Override public ActionRecord loadRecord(ExactRef reference){throw unavailable();}
        @Override public ExactRef recordReferenceOf(ActionRecord value){throw unavailable();}
        @Override public ExactRef preserveReceipt(ActionReceipt value){throw unavailable();}
        @Override public ActionReceipt loadReceipt(ExactRef reference){throw unavailable();}
        @Override public ExactRef receiptReferenceOf(ActionReceipt value){throw unavailable();}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value){throw unavailable();}
        @Override public byte[] loadNativeFrame(ExactRef reference){throw unavailable();}
    }
    private static Obj nativeResult(PlanningReadReceipt receipt){return DriverJson.object(receipt.original().originalResultToken().orElseThrow().bytes(),RawJson.MAXIMUM_BYTES);}
    private static RawJson raw(Obj value){return new RawJson(OpportunityJson.encode(value));}
    private static ExactRef reference(Path path)throws IOException{byte[] bytes=Files.readAllBytes(path);return new ExactRef(path.toAbsolutePath().normalize().toString(),bytes.length,DriverJson.sha256(bytes));}
}
