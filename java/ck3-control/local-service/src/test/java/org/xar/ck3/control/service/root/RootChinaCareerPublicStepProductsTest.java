package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.ArrayList;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.history.DriverExecuteQueryHistoryRowProducer;
import java.util.Optional;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.china_career.CareerJson;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacareer.*;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacareer.ChinaCareerContract.*;

/** Source-bound original Service EXECUTE -> actual driver/parser/normalizer -> registered READ replay -> public result.
 * Software protocol DATA grants no Root, source, native dispatch or Game qualification. */
public final class RootChinaCareerPublicStepProductsTest {
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final ExactRef REF=new ExactRef("software-protocol-DATA-not-Root-qualification",1,"a".repeat(64));

    @Test void actualOriginalExecuteRosterReachesExistingTypedContractsAndCompletePublicResults()throws Exception {
        JsonNode oracle=oracle();assertTrue(oracle.get("rows").size()>=15);
        var registration=new ChinaCareerService.Registration(REF);
        for(JsonNode row:oracle.get("rows")) {
            Kind kind=kind(row.get("kind").textValue());Frame frame=frame(row,false);
            OperationKey step=new OperationKey(row.get("legacy_step").textValue());
            var parsed=RootChinaCareerPublicStepProducts.parse(kind,step);
            assertTrue(RootChinaCareerPublicStepProducts.claims(kind,step));
            for(Kind other:Kind.values())if(other!=kind)assertFalse(RootChinaCareerPublicStepProducts.claims(other,step));
            Request request=parsed.request(frame.publicRevision());
            assertEquals(step.value(),ChinaCareerCodec.encodedLegacyStep(request,frame));
            var contract=registration.contract(kind);PlanningReadRequest read=planning(request,frame);
            var decoded=decode(contract,read,row.get("primitive"),frame,row.get("request_fields"));
            assertEquals(row.get("result"),ChinaCareerCodec.object(ChinaCareerCodec.numericExecuteResult(decoded,raw((ObjectNode)row.get("primitive")))));
            assertEquals(step.value(),ChinaCareerCodec.encodedExecuteStep(decoded));
            RawJson actual=RootChinaCareerPublicStepProducts.present(parsed,frame,decoded,raw((ObjectNode)row.get("primitive")));
            assertEquals(publicProjection((ObjectNode)row.get("result"),kind),ChinaCareerCodec.object(actual),kind.name());
            assertEquals(ChinaCareerCodec.object(actual),NativeWire.parse(actual.bytes()));
            assertEquals(actual,new RawJson(StrictJson.canonical(NativeWire.parse(actual.bytes()),StrictJson.EXPLICIT_MAX_BYTES)));
            assertEquals(row.get("frame"),ChinaCareerCodec.object(decoded.originalFrame()));
            assertFalse(ChinaCareerCodec.object(actual).has("binding"),"dedicated MCP tool wrapper must not replace original EXECUTE report");
        }
    }
    @Test void originalMalformedAndUnsupportedBranchesKeepExactTypedErrorsAndFiniteRoster()throws Exception {
        JsonNode oracle=oracle();assertEquals(6,oracle.get("unsupported").size());
        for(JsonNode row:oracle.get("bad_steps")) {
            Kind kind=kind(row.get("kind").textValue());OperationKey step=new OperationKey(row.get("step").textValue());
            var failure=assertThrows(PublicServiceFailure.class,()->RootChinaCareerPublicStepProducts.parse(kind,step));
            assertEquals(row.get("python_error").textValue(),failure.kind().pythonClassName());
            assertEquals(row.get("message").textValue(),failure.getMessage());
        }
        for(JsonNode row:oracle.get("unsupported")) {
            Frame frame=frame(row,false);ObjectNode hello=(ObjectNode)NativeWire.parse(Arrays.copyOfRange(frame.originalHello().packet().value(),4,frame.originalHello().packet().value().length));
            hello.putArray("capabilities");NativeWire.Hello absent=(NativeWire.Hello)NativeWire.decode(NativeWire.packet(StrictJson.canonical(hello)));
            var failure=assertThrows(PublicServiceFailure.class,()->RootChinaCareerPublicStepProducts.requireCapability(kind(row.get("kind").textValue()),absent));
            assertEquals(row.get("python_error").textValue(),failure.kind().pythonClassName());assertEquals(row.get("message").textValue(),failure.getMessage());
        }
        for(String other:List.of("query-zhongguo-incident-snapshot-v1-123-61","query-zhongguo-case-snapshot-v1-any","activate-review-now-v1"))
            for(Kind kind:Kind.values())assertFalse(RootChinaCareerPublicStepProducts.claims(kind,new OperationKey(other)));
    }
    @Test void knownUint64RolesRemainExactAndWrongNativeTypesCannotReachPublicSerde()throws Exception {
        for(JsonNode original:oracle().get("rows")) {
            Kind kind=kind(original.get("kind").textValue());ObjectNode row=((ObjectNode)original).deepCopy();
            ((ObjectNode)row.get("snapshot")).put("revision",StrictJson.UINT64_MAX).put("native_revision",StrictJson.UINT64_MAX);
            ((ObjectNode)row.get("snapshot").get("diagnostics")).put("connection_generation",StrictJson.UINT64_MAX);
            ((ObjectNode)row.get("frame")).put("snapshot_revision",StrictJson.UINT64_MAX);
            ObjectNode envelope=(ObjectNode)row.get("primitive");envelope.put("snapshot_revision",StrictJson.UINT64_MAX).put("query_sequence",StrictJson.UINT64_MAX).set(kind.payload(),row.get("frame"));
            Frame frame=frame(row,true);var parsed=RootChinaCareerPublicStepProducts.parse(kind,new OperationKey(row.get("legacy_step").textValue()));Request input=parsed.request(frame.publicRevision());
            var contract=new ChinaCareerService.Registration(REF).contract(kind);var read=planning(input,frame);
            NativeObservation decoded=decode(contract,read,envelope,frame,row.get("request_fields"));
            RawJson actual=RootChinaCareerPublicStepProducts.present(parsed,frame,decoded,raw(envelope));ObjectNode result=ChinaCareerCodec.object(actual);
            for(String field:List.of("query_sequence","snapshot_revision","queried_revision","queried_native_revision","queried_connection_generation"))assertEquals(StrictJson.UINT64_MAX.toString(),result.get(field).textValue());
            assertEquals(StrictJson.UINT64_MAX.toString(),result.get(kind.payload()).get("snapshot_revision").textValue());
            for(String field:List.of("query_sequence","snapshot_revision")) {
                assertThrows(IllegalArgumentException.class,()->RootChinaCareerPublicStepProducts.present(parsed,frame,decoded,raw(envelope.deepCopy().put(field,true))));
                ObjectNode missing=envelope.deepCopy();missing.remove(field);
                assertThrows(IllegalArgumentException.class,()->RootChinaCareerPublicStepProducts.present(parsed,frame,decoded,raw(missing)));
            }
            assertThrows(IllegalArgumentException.class,()->RootChinaCareerPublicStepProducts.present(parsed,frame,decoded,raw(envelope.deepCopy().put("accepted",false))));
            ObjectNode wrong=envelope.deepCopy().put("snapshot_revision",1.0);
            assertThrows(IllegalArgumentException.class,()->RootChinaCareerPublicStepProducts.present(parsed,frame,decoded,raw(wrong)));
            ObjectNode extra=envelope.deepCopy().put("available",true);
            assertThrows(IllegalArgumentException.class,()->RootChinaCareerPublicStepProducts.present(parsed,frame,decoded,raw(extra)));
        }
    }

    @Test void actualRegisteredNativeProducerFeedsWholeHistoryArtifactAndColdReplayWithoutNewPreservation()throws Exception {
        var sources=RootSourceHelperFiles.java(List.of(ChinaCareerService.class,ChinaCareerCodec.class),RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT);
        ExactRef service=sources.get(0).sourceRef(),codec=sources.get(1).sourceRef();
        var producers=new ArrayList<ExactRef>(List.of(service,codec));
        producers.add(RootSourceHelperFiles.java(RootChinaCareerPublicStepProducts.class,RootRuntimeSelectedSources.Module.LOCAL_SERVICE).sourceRef());
        producers.add(RootSourceHelperFiles.java(DriverExecuteQueryHistoryRowProducer.class,RootRuntimeSelectedSources.Module.APPLICATION).sourceRef());
        var registration=new ChinaCareerService.Registration(service,codec);
        for(JsonNode row:oracle().get("rows")) {
            Kind kind=kind(row.get("kind").textValue());Frame frame=frame(row,false);var archive=new SoftwareArchive();
            var parsed=RootChinaCareerPublicStepProducts.parse(kind,new OperationKey(row.get("legacy_step").textValue()));
            Request input=parsed.request(frame.publicRevision());PlanningReadRequest request=planning(input,frame,service);
            ReadContract<NativeObservation> contract=registration.contract(kind);
            var catalog=new RootReadContractCatalog(List.of(new RootReadContractCatalog.InstalledRead(contract,codec)),List.of());
            ObjectNode snapshot=StrictJson.object().put("type","state_snapshot").put("protocol_version",1)
                    .put("snapshot_id",frame.snapshotId()).put("revision",frame.nativeRevision());snapshot.set("state",row.get("snapshot"));
            byte[] packet=NativeWire.packet(StrictJson.canonical(snapshot));assertNotNull(NativeWire.decode(packet));
            ExactRef nativeOriginal=archive.ref("native-packet-DATA",packet);archive.packets.put(nativeOriginal,packet);
            archive.packets.put(frame.helloOriginal(),frame.originalHello().packet().value());
            ExactRef support=archive.preserveMaterial(raw(StrictJson.object().put("guard_basis","software DATA, no current or writer qualification")));
            PlanningReadReceipt receipt=protocolReceipt(contract,request,row.get("primitive"),frame,row.get("request_fields"),nativeOriginal,List.of(support));
            archive.preserve(receipt.original());ExactRef read=archive.preserveRead(receipt);
            var known=new PlanningReadResult.Known<>(contract.decode(receipt),receipt,read);int before=archive.materialWrites.size();
            var candidate=DriverExecuteQueryHistoryRowProducer.prepare(archive,catalog,contract,known,1,producers);
            assertEquals(before+2,archive.materialWrites.size());
            assertEquals(row.get("result"),NativeWire.parse(archive.loadMaterial(candidate.fullResultReference()).bytes()));
            assertEquals(new RawJson(candidate.row().encode()),archive.materialWrites.get(before+1));
            assertEquals(row.get("legacy_step").textValue(),candidate.row().command());
            assertEquals(kind.step(),org.xar.ck3.control.planning.opportunity.OpportunityJson.text(candidate.row().result().get("step"),"logical report step"));
            assertEquals(candidate.row(),DriverExecuteQueryHistoryRowProducer.decode(candidate.row().encode()));
            assertSame(candidate,DriverExecuteQueryHistoryRowProducer.replay(archive,catalog,contract,known,candidate));
            assertEquals(before+2,archive.materialWrites.size());
            var cold=new SoftwareArchive();cold.materials.putAll(archive.materials);cold.outcomes.putAll(archive.outcomes);cold.reads.putAll(archive.reads);
            archive.packets.forEach((ref,bytes)->cold.packets.put(ref,bytes.clone()));
            var decoded=DriverExecuteQueryHistoryRowProducer.decode(candidate.row().encode());
            assertEquals(known,DriverExecuteQueryHistoryRowProducer.replayCanonical(cold,catalog,contract,decoded));
            assertTrue(cold.materialWrites.isEmpty(),"cold replay must not preserve a replacement full report or row");
            var foreign=new ChinaCareerService.Registration(service,codec).contract(kind);
            assertThrows(IllegalArgumentException.class,()->DriverExecuteQueryHistoryRowProducer.prepare(archive,catalog,foreign,known,2,producers));
            cold.outcomes.remove(candidate.source().original().acknowledgement());
            assertThrows(IllegalArgumentException.class,()->DriverExecuteQueryHistoryRowProducer.replayCanonical(cold,catalog,contract,decoded));
            assertTrue(cold.materialWrites.isEmpty());assertEquals(before+2,archive.materialWrites.size());
        }
    }

    /** Only an actual managed catalog may call this; no fabricated Core or fixture context is accepted here. */
    public static void assertActualInstalled(RootInstalledCatalog catalog)throws Exception {
        var actual=catalog.publicSteps().products().stream().filter(product->product.id().startsWith("original.execute.china-career.")).toList();
        assertEquals(6,actual.size());
        for(var product:actual){assertInstanceOf(RootPublicStepExecution.Read.class,product);product.requireContext(catalog.context());assertFalse(product.sources().isEmpty());}
        for(var contract:catalog.additionalDomains().chinaCareer().service().registration().all())
            assertTrue(catalog.bindings().readCatalog().containsIdentity(contract));
    }
    private static Kind kind(String kind){return switch(kind){case "owner"->Kind.OWNER;case "career"->Kind.CAREER_HC;case "collective"->Kind.COLLECTIVE;case "normal"->Kind.NORMAL_EXIT;case "governance"->Kind.MANAGER_GOVERNANCE;case "selector"->Kind.MANAGER_SELECTOR;default->throw new IllegalArgumentException("unknown actual original kind");};}
    private static Frame frame(JsonNode row,boolean maximum)throws Exception {
        JsonNode snapshot=row.get("snapshot"),token=row.get("frame");BigInteger generation=snapshot.get("diagnostics").get("connection_generation").bigIntegerValue();
        ObjectNode hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",123).put("connection_generation",generation)
                .put("bridge_version",CareerJson.BRIDGE).put("expected_ck3_sha256",CareerJson.EXE_SHA256).put("game_adapter_id",CareerJson.ADAPTER).put("game_adapter_status","ready").put("ck3_build_match",true);
        for(Kind kind:Kind.values())hello.withArray("capabilities").add(kind.capability());
        byte[] packet=NativeWire.packet(StrictJson.canonical(hello));var identity=NativeRequestChronology.PacketIdentity.of(packet);
        return new Frame(snapshot.get("snapshot_id").textValue(),snapshot.get("revision").bigIntegerValue(),token.get("snapshot_revision").bigIntegerValue(),generation,
                snapshot.get("date_raw").intValue(),token.get("player_character_id").intValue(),true,true,"original-oracle-episode",
                (NativeWire.Hello)NativeWire.decode(packet),new ExactRef("software-DATA/original-HELLO",identity.bytes(),identity.sha256()));
    }
    private static PlanningReadRequest planning(Request input,Frame frame) {return planning(input,frame,REF);}
    private static PlanningReadRequest planning(Request input,Frame frame,ExactRef actualSource) {
        var source=new G2Source("software-China-career-EXECUTE-DATA",NOW.toString(),CareerJson.VERSION,actualSource);
        var before=new ObservationIdentity(source.machineId(),new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(frame.playerId()),frame.nativeRevision(),BigInteger.valueOf(frame.dateRaw())),frame.snapshotId(),frame.publicRevision(),frame.episode()),1);
        return new PlanningReadRequest(before,source,"software-only-session",new OperationKey(input.kind().step()),ChinaCareerService.arguments(input,frame),NOW.plusSeconds(30));
    }
    private static NativeObservation decode(ReadContract<NativeObservation> contract,PlanningReadRequest request,JsonNode envelope,Frame frame,JsonNode originalFields)throws Exception {
        var receipt=protocolReceipt(contract,request,envelope,frame,originalFields,REF,List.of());
        NativeObservation decoded=contract.decode(receipt);
        assertEquals(decoded,contract.replay(receipt));
        assertEquals(org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.Kind.PUBLIC_EXECUTE_QUERY,contract.originalHistoryKind().orElseThrow());
        var material=assertInstanceOf(org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.ExecuteProjection.class,contract.projectOriginalHistoryPayload(receipt));
        assertEquals(request.operation(),material.logicalOperation());
        assertEquals(new OperationKey(ChinaCareerCodec.encodedExecuteStep(decoded)),material.originalCommand());
        assertEquals(ChinaCareerCodec.numericExecuteResult(decoded,raw((ObjectNode)envelope)),material.fullResult());
        assertEquals(org.xar.ck3.control.application.driver.DriverJson.object(ChinaCareerCodec.publicExecuteResult(decoded,raw((ObjectNode)envelope)).bytes(),RawJson.MAXIMUM_BYTES),
                material.publicNumbers().toPublic(org.xar.ck3.control.application.driver.DriverJson.object(material.fullResult().bytes(),RawJson.MAXIMUM_BYTES)));
        return decoded;
    }
    private static PlanningReadReceipt protocolReceipt(ReadContract<NativeObservation> contract,PlanningReadRequest request,JsonNode envelope,
            Frame frame,JsonNode originalFields,ExactRef nativeOriginal,List<ExactRef> supporting)throws Exception {
        String id="actual-original-EXECUTE-software-read";NativeRequest actual=contract.prepare(request,id);
        assertEquals(originalFields,ChinaCareerCodec.object(actual.additionalFields()));byte[] outbound=NativeWire.execute(id,actual.step(),frame.nativeRevision(),actual.additionalFields().bytes());
        ObjectNode wire=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);wire.set("result",envelope);
        byte[] bytes=StrictJson.canonical(wire,StrictJson.EXPLICIT_MAX_BYTES);
        var evidence=new GuardEvidence(request.before(),request.source(),request.sessionId(),frame.generation(),request.operation(),nativeOriginal,frame.helloOriginal(),"software-DATA-not-qualification",NOW,NOW.plusSeconds(30),supporting);
        var guard=new PlanningReadGuard(evidence,true,true,true,"b".repeat(64));
        var ack=new NativeActionPort.AckReceived(id,true,Optional.of(raw((ObjectNode)envelope)),new RawJson(bytes),NativeWire.packet(bytes),Optional.of(new NativeActionPort.OutboundPacket(id,outbound)));
        return new PlanningReadReceipt(request,contract.contractId(),id,guard,guard,ack);    }
    private static ObjectNode publicProjection(ObjectNode original,Kind kind) {
        ObjectNode row=original.deepCopy();for(String name:List.of("snapshot_revision","query_sequence","queried_revision","queried_native_revision","queried_connection_generation"))row.put(name,row.get(name).bigIntegerValue().toString());
        ObjectNode payload=(ObjectNode)row.get(kind.payload());payload.put("snapshot_revision",payload.get("snapshot_revision").bigIntegerValue().toString());return row;
    }
    private static RawJson raw(ObjectNode row){return new RawJson(StrictJson.canonical(row,StrictJson.EXPLICIT_MAX_BYTES));}
    private static String required(String key){String value=System.getProperty(key);if(value==null||value.isBlank())throw new IllegalStateException("NOT_RUN_REQUIRED: "+key+" must name the actual original oracle environment");return value;}
    private static byte[] bounded(InputStream input,int maximum)throws IOException {try(input;var output=new ByteArrayOutputStream()){byte[] bytes=new byte[4096];for(int count;(count=input.read(bytes))!=-1;){if(output.size()+count>maximum)throw new IOException("bounded source oracle output exceeded");output.write(bytes,0,count);}return output.toByteArray();}}
    private static JsonNode oracle()throws Exception {
        Path repository=Path.of(required("xar.repository.root")).toRealPath();String python=Path.of(required("xar.python")).toRealPath().toString();
        var witnesses=new java.util.ArrayList<SharedSourceFiles.Witness>();
        for(JsonNode source:NativeWire.parse(INDEX.getBytes(StandardCharsets.UTF_8)).get("oracle_sources")){
            var witness=SharedSourceFiles.observe(repository.resolve(source.get("path").textValue()));assertEquals(source.get("bytes").longValue(),witness.source().bytes());assertEquals(source.get("sha256").textValue(),witness.source().sha256());witnesses.add(witness);
        }
        Process process=new ProcessBuilder(python,"-I","-B","-X","utf8","-c",ORACLE,repository.toString(),INDEX).directory(repository.toFile()).start();
        try(var executor=Executors.newVirtualThreadPerTaskExecutor()){
            var stdout=executor.submit(()->bounded(process.getInputStream(),4*1024*1024));var stderr=executor.submit(()->bounded(process.getErrorStream(),1024*1024));process.getOutputStream().close();
            try{if(!process.waitFor(60,TimeUnit.SECONDS))throw new IOException("original EXECUTE oracle timeout");byte[] result=stdout.get(10,TimeUnit.SECONDS);assertEquals(0,process.exitValue(),new String(stderr.get(10,TimeUnit.SECONDS),StandardCharsets.UTF_8));return NativeWire.parse(result);}
            finally{if(process.isAlive()){process.destroyForcibly();assertTrue(process.waitFor(10,TimeUnit.SECONDS));}for(var witness:witnesses)SharedSourceFiles.assertUnchanged(witness);}
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
    private static final String INDEX = """
{"repository_root":".","oracle_sources":[{"path":"ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_workforce_owner_snapshot_contract.py","bytes":7926,"sha256":"2678b31a11e25db5cb1aa59c948f8a7efb74b6c067770dd5308fbd916cc7bb78"},{"path":"ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_career_hc_workforce_postcondition_contract.py","bytes":14671,"sha256":"398210553c74fdefa800b77f1287570598e4c2c4c73be35f243bec889bc14c76"},{"path":"ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_workforce_collective_snapshot_contract.py","bytes":31932,"sha256":"e91ac95ec075959610060db0b5335201b5d0d952da931a2495aa1ba4ce7faa31"},{"path":"ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_workforce_normal_exit_snapshot_contract.py","bytes":36181,"sha256":"60261c642d5500f2e465986e64cd43389e5bfeff6cecfa8ca91d2da8abb08eb3"},{"path":"ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_manager_subordinate_selector_contract.py","bytes":8166,"sha256":"26e5e2ce6ddc13c496ac497c476de3ebf935788b386ae6fdf5a58c049332a7b7"},{"path":"ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_manager_governance_snapshot_contract.py","bytes":33526,"sha256":"c7f07a53c4752cc11e859e47176124e092a791b8d87880ee3882ac88f31e767a"},{"path":"ck3_autonomous_player/tests/unit/test_zhongguo_career_hc_workforce_postcondition_v1_contract.py","bytes":13034,"sha256":"2e8a7e40b2396433bdefe0e0112a193a6819808008fff8fc4d5d2e3d254d448d"},{"path":"ck3_autonomous_player/tests/unit/test_zhongguo_workforce_collective_snapshot_v1_contract.py","bytes":16814,"sha256":"46a9e66c4cbb11e92e8d1f31b54f3c65dd954b214281419c2aca87606570fd38"},{"path":"ck3_autonomous_player/tests/unit/test_zhongguo_workforce_normal_exit_snapshot_contract.py","bytes":29212,"sha256":"95787785286752ba5fca2ce2a725b77f2f52fd14b6c2388d370ecdbe9afcd56d"},{"path":"ck3_autonomous_player/tests/unit/test_zhongguo_manager_subordinate_selector_contract.py","bytes":14358,"sha256":"c2feb72f22a683d869d111eb3d684d342476bfa5dab163e903d170bc140d4aba"},{"path":"ck3_autonomous_player/tests/unit/test_zhongguo_manager_governance_snapshot_contract.py","bytes":27889,"sha256":"1c9cdd6dc5b3644e27cc039dd8a6058a04462f0e09471ea828d716721c5698e9"},{"path":"ck3_autonomous_player/tests/fixtures/zhongguo_workforce_owner_snapshot_v1.json","bytes":24976,"sha256":"1b733ce9f6bce9c15e730e8fe31c98b87ea6bec8f1de20737b804c7bff12c12c"},{"path":"ck3_autonomous_player/src/xar_autoplayer/bridge/service.py","bytes":897392,"sha256":"a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e"},{"path":"ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py","bytes":1658471,"sha256":"eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603"},{"path":"ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py","bytes":283568,"sha256":"b7569231226484b0bdd98c40ace14a82672b2138a0aab77711e559a4d9b8ccbc"},{"path":"ck3_autonomous_player/src/xar_autoplayer/bridge/driver.py","bytes":20803,"sha256":"eed449063debf1a84216a350f0178d64a9a6602bbfcc266298a810a9bb736fb6"},{"path":"ck3_autonomous_player/tests/unit/test_zhongguo_workforce_collective_snapshot_v1_bridge.py","bytes":16879,"sha256":"5a6fb0a79b9d9e9898a1a4adcdf1426d514dc157a76135c7cf8124b7f7785c7c"},{"path":"ck3_autonomous_player/tests/unit/test_zhongguo_workforce_normal_exit_snapshot_v1_bridge.py","bytes":16773,"sha256":"cb7afea0eca5ced8ee2a6c4da3e902027a067326b4a2e88241e204105d8ba0aa"},{"path":"ck3_autonomous_player/tests/unit/test_zhongguo_workforce_owner_snapshot_v1_bridge.py","bytes":9986,"sha256":"e98b63b1a5ae476f31eb47a45f02f86ecc1c1f78b0a89568f45fdd8492c5922c"}],"methods":[{"kind":"owner","public_method":"query_zhongguo_workforce_owner_snapshot_v1","driver_method":"_execute_zhongguo_workforce_owner_snapshot_v1_query","parse_query":"parse_query_zhongguo_workforce_owner_snapshot_v1_step","contract_module":"zhongguo_workforce_owner_snapshot_contract","fixture_file":null,"step":"query-zhongguo-workforce-owner-snapshot-v1","capability":"game.command.query-zhongguo-workforce-owner-snapshot-v1","payload":"zhongguo_workforce_owner_snapshot","response":"OwnerCareerFrames.Owner","service_range":[11174,11348],"driver_range":[19790,19930]},{"kind":"career","public_method":"query_zhongguo_career_hc_workforce_postcondition_v1","driver_method":"_execute_zhongguo_career_hc_workforce_v1_query","parse_query":"parse_query_zhongguo_career_hc_workforce_v1_step","contract_module":"zhongguo_career_hc_workforce_postcondition_contract","fixture_file":"test_zhongguo_career_hc_workforce_postcondition_v1_contract.py","step":"query-zhongguo-career-hc-workforce-postcondition-v1","capability":"game.command.query-zhongguo-career-hc-workforce-postcondition-v1","payload":"zhongguo_career_hc_workforce_postcondition","response":"OwnerCareerFrames.Career","service_range":[11555,11736],"driver_range":[20077,20217]},{"kind":"collective","public_method":"query_zhongguo_workforce_collective_snapshot_v1","driver_method":"_execute_zhongguo_workforce_collective_snapshot_v1_query","parse_query":"parse_query_zhongguo_workforce_collective_snapshot_v1_step","contract_module":"zhongguo_workforce_collective_snapshot_contract","fixture_file":"test_zhongguo_workforce_collective_snapshot_v1_contract.py","step":"query-zhongguo-workforce-collective-snapshot-v1","capability":"game.command.query-zhongguo-workforce-collective-snapshot-v1","payload":"zhongguo_workforce_collective_snapshot","response":"CollectiveWorkforceFrame","service_range":[11740,12029],"driver_range":[20223,20382]},{"kind":"normal","public_method":"query_zhongguo_workforce_normal_exit_snapshot_v1","driver_method":"_execute_zhongguo_workforce_normal_exit_snapshot_v1_query","parse_query":"parse_query_zhongguo_workforce_normal_exit_snapshot_v1_step","contract_module":"zhongguo_workforce_normal_exit_snapshot_contract","fixture_file":"test_zhongguo_workforce_normal_exit_snapshot_contract.py","step":"query-zhongguo-workforce-normal-exit-snapshot-v1","capability":"game.command.query-zhongguo-workforce-normal-exit-snapshot-v1","payload":"zhongguo_workforce_normal_exit_snapshot","response":"NormalExitWorkforceFrame","service_range":[12031,12318],"driver_range":[20384,20543]},{"kind":"selector","public_method":"query_zhongguo_manager_subordinate_selector_v1","driver_method":"_execute_zhongguo_manager_subordinate_selector_v1_query","parse_query":"parse_query_zhongguo_manager_subordinate_selector_v1_step","contract_module":"zhongguo_manager_subordinate_selector_contract","fixture_file":"test_zhongguo_manager_subordinate_selector_contract.py","step":"query-zhongguo-manager-subordinate-selector-v1","capability":"game.command.query-zhongguo-manager-subordinate-selector-v1","payload":"zhongguo_manager_subordinate_selector","response":"ManagerSelectorFrame","service_range":[12609,12738],"driver_range":[20852,20987]},{"kind":"governance","public_method":"query_zhongguo_manager_governance_snapshot_v1","driver_method":"_execute_zhongguo_manager_governance_snapshot_v1_query","parse_query":"parse_query_zhongguo_manager_governance_snapshot_v1_step","contract_module":"zhongguo_manager_governance_snapshot_contract","fixture_file":"test_zhongguo_manager_governance_snapshot_contract.py","step":"query-zhongguo-manager-governance-snapshot-v1","capability":"game.command.query-zhongguo-manager-governance-snapshot-v1","payload":"zhongguo_manager_governance_snapshot","response":"ManagerGovernanceFrame","service_range":[12740,13033],"driver_range":[20691,20850]}]}
""";
    private static final String ORACLE="""
from __future__ import annotations
import ast,copy,hashlib,importlib,json,sys,types
from pathlib import Path
repo=Path(sys.argv[1]).resolve(); manifest=json.loads(sys.argv[2]); base=repo/'ck3_autonomous_player'
def verify():
 for ref in manifest['oracle_sources']:
  p=repo/ref['path']; data=p.read_bytes()
  if len(data)!=ref['bytes'] or hashlib.sha256(data).hexdigest()!=ref['sha256']:raise RuntimeError('original source drift: '+str(p))
verify();sys.path.insert(0,str(base/'src'))
native=importlib.import_module('xar_autoplayer.bridge.native_driver')
service_module=importlib.import_module('xar_autoplayer.bridge.service')
driver_class=native.NativeHeadlessGameplayDriver; service_class=service_module.GameplayBridgeService
for function,path in ((driver_class._execute_step_unrecorded,base/'src/xar_autoplayer/bridge/native_driver.py'),(service_class.execute_step,base/'src/xar_autoplayer/bridge/service.py')):
 if Path(function.__code__.co_filename).resolve()!=path.resolve():raise RuntimeError('actual EXECUTE function source substituted')
def fixture(path,contract):
 env=dict(vars(contract),copy=copy,json=json,Path=Path,sys=sys,__file__=str(path)); nodes=[]
 for node in ast.parse(path.read_text(encoding='utf-8-sig')).body:
  if isinstance(node,ast.ClassDef):break
  if isinstance(node,(ast.Assign,ast.AnnAssign,ast.FunctionDef)):nodes.append(node)
 exec(compile(ast.fix_missing_locations(ast.Module(body=ast.parse('from __future__ import annotations').body+nodes,type_ignores=[])),str(path),'exec'),env)
 return env
rows=[];bad_steps=[];unsupported=[]
for method in manifest['methods']:
 kind=method['kind'];contract=importlib.import_module('xar_autoplayer.bridge.'+method['contract_module']); constants={}
 if kind=='owner':frames=list(json.loads((base/'tests/fixtures/zhongguo_workforce_owner_snapshot_v1.json').read_text(encoding='utf-8-sig'))['frames'].values())
 else:
  constants=fixture(base/'tests/unit'/method['fixture_file'],contract)
  if kind=='career':frames=[constants['frame']()]
  elif kind=='collective':frames=[constants['frame'](route=r,history_count=h) for r in (1,2,3) for h in (0,1,3)]
  elif kind=='normal':frames=[constants['frame'](s) for s in ('offered','pending','accepted','migrating','sealed','rehire')]
  elif kind=='selector':frames=[constants['_frame'](),constants['_frame'](status='unavailable')]
  else:frames=[constants['_frame']()]
 for index,frame in enumerate(frames):
  public=constants.get('PUBLIC_REVISION',7);player=frame['player_character_id'];captured={}
  snapshot=dict(paused=True,map_ready=True,snapshot_id='original-oracle-frame',revision=public,native_revision=frame['snapshot_revision'],date_raw=frame['date_raw'],played_character=dict(character_id=player,alive=True),episode_run_id='original-oracle-episode',diagnostics=dict(connection_generation=4))
  def primitive(step,**kwargs):
   if kwargs['expected_revision']!=public:raise RuntimeError('actual original expected revision changed')
   envelope=dict(step=step,accepted=True,status=frame['status'],query_sequence=1,snapshot_revision=frame['snapshot_revision'],backend_id='native-headless',**{method['payload']:copy.deepcopy(frame)})
   captured.update(primitive=copy.deepcopy(envelope),request_fields=copy.deepcopy(kwargs['request_fields']));return envelope
  driver=types.SimpleNamespace(take_snapshot=lambda:copy.deepcopy(snapshot),_execute_primitive_step=primitive,capabilities=lambda:dict(bridge_capabilities=[method['capability']]))
  for entry in manifest['methods']:
   setattr(driver,entry['driver_method'],types.MethodType(getattr(driver_class,entry['driver_method']),driver))
  driver.execute_step=lambda step,**kwargs:driver_class._execute_step_unrecorded(driver,step,**kwargs)
  service=types.SimpleNamespace(driver=driver)
  builder=getattr(contract,method['parse_query'].removeprefix('parse_'))
  kwargs=dict(request_nonce=frame['request_nonce'])
  if kind!='selector':kwargs['owner_character_id']=frame.get('requested_owner_character_id',player)
  if kind=='governance':kwargs['subject_character_id']=frame['subject_character_id']
  legacy=builder(**kwargs)
  result=service_class.execute_step(service,legacy,expected_revision=public)
  rows.append(dict(kind=kind,frame=copy.deepcopy(frame),snapshot=copy.deepcopy(snapshot),legacy_step=legacy,result=result,**captured))
  if index==0:
   driver.capabilities=lambda:dict(bridge_capabilities=[])
   try:service_class.execute_step(service,legacy,expected_revision=public)
   except native.UnsupportedStepError as error:unsupported.append(dict(kind=kind,frame=frame,snapshot=snapshot,python_error=type(error).__name__,message=str(error)))
   else:raise RuntimeError('original unsupported branch did not reject')
   driver.capabilities=lambda:dict(bridge_capabilities=[method['capability']])
   if kind=='selector':tails=['','0','FF','00','c3a9','2d','61-62']
   elif kind=='governance':tails=['','1-0-61','01-1-61','1-1-0','1-1-00','2147483648-1-61']
   else:tails=['','1-0','01-61','0-61','2147483648-61','1-FF','1-00']
   for tail in tails:
    bad=method['step']+'-'+tail
    if getattr(contract,method['parse_query'])(bad) is not None:raise RuntimeError('oracle invalid parser case unexpectedly valid')
    try:service_class.execute_step(service,bad,expected_revision=public)
    except native.UnsupportedStepError as error:bad_steps.append(dict(kind=kind,step=bad,python_error=type(error).__name__,message=str(error)))
    else:raise RuntimeError('original malformed branch did not reject')
verify();json.dump(dict(rows=rows,bad_steps=bad_steps,unsupported=unsupported),sys.stdout,separators=(',',':'))
""";
}
