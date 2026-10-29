package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Set;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.writer.NativeArchiveDataCodec;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesFacade;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesContract.Method;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;

/** Actual READ DATA replay and the genuine existing software central writer/physical archive.
 * The mandatory corpus retains the original Python's entire EXECUTE report and public projection.
 * Missing actual corpus is a hard failure. Software execution confers no live capability. */
final class RootChinaCasesPublicStepProductsTest {
    private static final int DATA_MAX=8*1024*1024;
    private static final BigInteger MAX=new BigInteger("18446744073709551615");
    private static final Map<Method,String> TAILS=Map.ofEntries(
            Map.entry(Method.CASE,"b1-102-0-4e31"),Map.entry(Method.AI_OWNED,"101-102-4e31"),
            Map.entry(Method.B1,"4e31"),Map.entry(Method.RESULT,"101-4e31"),Map.entry(Method.PIP,"101-4e31"),
            Map.entry(Method.PROMOTION,"101-4e31"),Map.entry(Method.AF5,"101-4e31"),
            Map.entry(Method.PROJECTS,"101-102-4e31"),Map.entry(Method.INCIDENT,"101-x-4e31"),
            Map.entry(Method.SCOREBOARD,"N1"));
    private static final PlanningReadPort NEVER_LIVE=new PlanningReadPort() {
        @Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) {
            throw new AssertionError("pure retained DATA replay cannot perform a live READ");
        }
    };
    private static final ActionCoordinatorPort NEVER_ACTION=new ActionCoordinatorPort() {
        @Override public ActionReceipt execute(ActionCommand command) {throw new AssertionError("Cases READ cannot submit an action");}
        @Override public ActionReceipt reconcile(String id) {throw new AssertionError("Cases READ cannot reconcile an action");}
    };

    @Test void publicExecuteCodecUsesTheOriginalTenParsersAndPrimitiveArguments() {
        assertEquals(10,TAILS.size());
        for(var row:TAILS.entrySet()) {
            Method method=row.getKey();String step=method.family().step()+"-"+row.getValue();
            var request=caller(step);
            assertEquals(method,ChinaCasesCodec.executionMethod(request.step()).orElseThrow());
            assertTrue(RootChinaCasesPublicStepProducts.matches(method,request.step()));
            ObjectNode arguments=(ObjectNode)OpportunityJson.toNode(ChinaCasesCodec.executionArguments(request.step(),MAX));
            assertEquals("N1",arguments.get("request_nonce").textValue());
            if(method==Method.CASE) {
                assertEquals("zhongguo.b1.performance",arguments.get("case_kind").textValue());
                assertEquals(102,arguments.get("subject_character_id").intValue());
                assertEquals(0,arguments.get("owner_character_id").intValue());
            }
            if(method==Method.SCOREBOARD)assertEquals(MAX,arguments.get("expected_connection_generation").bigIntegerValue());
            assertEquals(StrictJson.parse(PublicPlanningCodec.encodeExecute(request).bytes()),
                    StrictJson.parse(PublicPlanningCodec.encodeExecute(PublicPlanningCodec.decodeExecute(
                            new PublicBindings.Value(PublicPlanningCodec.encodeExecute(request)))).bytes()));
        }
        assertTrue(ChinaCasesCodec.executionMethod(new OperationKey("query-zhongguo-workforce-owner-snapshot-v1-101-4e31")).isEmpty());
        assertTrue(ChinaCasesCodec.executionMethod(new OperationKey(PublicPlanningCodec.H2743_STEP)).isEmpty());
        assertFalse(RootChinaCasesPublicStepProducts.matches(Method.ACTIVATE_SCOREBOARD,new OperationKey("activate-zhongguo-scoreboard-v1")));
    }

    @Test void malformedAndAliasedEncodedArgumentsCannotReachAReadProduct() {
        for(var row:TAILS.entrySet()) {
            String base=row.getKey().family().step();
            for(String bad:List.of(base,base+"-"))
                assertTrue(ChinaCasesCodec.executionMethod(new OperationKey(bad)).isEmpty(),bad);
            if(row.getKey()!=Method.SCOREBOARD)
                assertTrue(ChinaCasesCodec.executionMethod(new OperationKey(base+"-"+row.getValue()+"-")).isEmpty());
            assertThrows(IllegalArgumentException.class,()->caller(base+"- "+row.getValue()));
        }
        for(String tail:List.of("01-102-4e31","101-101-4e31","0-102-4e31","101-102-4E31","101-102-4e3","101-102-ff"))
            assertTrue(ChinaCasesCodec.executionMethod(new OperationKey(Method.AI_OWNED.family().step()+"-"+tail)).isEmpty(),tail);
        for(String tail:List.of("101-101-4e31","101-102-4E31","101-102-4e31-","101-102-"))
            assertTrue(ChinaCasesCodec.executionMethod(new OperationKey(Method.PROJECTS.family().step()+"-"+tail)).isEmpty(),tail);
        for(String tail:List.of("101-X-4e31","101-q-4e31"))
            assertTrue(ChinaCasesCodec.executionMethod(new OperationKey(Method.INCIDENT.family().step()+"-"+tail)).isEmpty(),tail);
        ObjectNode bad=StrictJson.object().put("step",Method.B1.family().step()+"-4e31").put("expected_revision",true);
        for(ObjectNode wrong:List.of(bad,bad.deepCopy().put("expected_revision",1.0),
                bad.deepCopy().put("expected_revision",9007199254740992L),bad.deepCopy().put("expected_revision","01")))
            assertThrows(IllegalArgumentException.class,()->PublicPlanningCodec.decodeExecute(new PublicBindings.Value(PublicDataJson.encode(wrong))));
    }

    @Test void originalUnboundedPositiveProjectIdsAreNotClippedToAnInt32OrLong() {
        String owner="9".repeat(4300),subject="8".repeat(4300);
        OperationKey encoded=caller(Method.PROJECTS.family().step()+"-"+owner+"-"+subject+"-4e31").step();
        assertEquals(Method.PROJECTS,ChinaCasesCodec.executionMethod(encoded).orElseThrow());
        ObjectNode arguments=(ObjectNode)OpportunityJson.toNode(ChinaCasesCodec.executionArguments(encoded,BigInteger.ONE));
        assertEquals(new BigInteger(owner),arguments.get("owner_character_id").bigIntegerValue());
        assertEquals(new BigInteger(subject),arguments.get("subject_character_id").bigIntegerValue());
        OperationKey promotion=caller(Method.PROMOTION.family().step()+"-"+owner+"-4e31").step();
        assertEquals(new BigInteger(owner),((ObjectNode)OpportunityJson.toNode(
                ChinaCasesCodec.executionArguments(promotion,BigInteger.ONE))).get("owner_character_id").bigIntegerValue());
        assertTrue(ChinaCasesCodec.executionMethod(new OperationKey(Method.AI_OWNED.family().step()+"-2147483648-102-4e31")).isEmpty());
    }

    @Test void actualRetainedReadThroughTheInstalledDecoderAndExecuteConsumerMatchesWholePythonResults()throws Exception {
        ObjectNode manifest=object(read(manifestRef()));
        StrictJson.object(manifest,Set.of("schema","machine_id","observed_at_utc","producer_sources","cases","writer_cases"));
        assertEquals("xar.china-cases-execute-parity-fixture/v1",StrictJson.text(manifest.get("schema")));
        StrictJson.text(manifest.get("machine_id"));java.time.Instant.parse(StrictJson.text(manifest.get("observed_at_utc")));
        for(JsonNode source:array(manifest.get("producer_sources"),12,64))read(ExactRef.fromJson(source));
        var facade=new ChinaCasesFacade(NEVER_LIVE,NEVER_ACTION);
        EnumSet<Method> seen=EnumSet.noneOf(Method.class);var ids=new java.util.HashSet<String>();
        for(JsonNode value:array(manifest.get("cases"),10,128)) {
            ObjectNode cell=StrictJson.object(value,Set.of("id","method","execute_arguments","read_metadata","python_numeric_result","python_public_result"));
            String id=StrictJson.text(cell.get("id"));assertTrue(ids.add(id));
            Method method=Method.valueOf(StrictJson.text(cell.get("method")));assertTrue(method.readOnly());seen.add(method);
            var caller=PublicPlanningCodec.decodeExecute(new PublicBindings.Value(new RawJson(read(ExactRef.fromJson(cell.get("execute_arguments"))))));
            assertEquals(method,ChinaCasesCodec.executionMethod(caller.step()).orElseThrow(),id);
            var retained=NativeArchiveDataCodec.retainedFiles().readData(ExactRef.fromJson(cell.get("read_metadata")));
            PlanningReadReceipt receipt=retained.receipt();
            assertEquals(StrictJson.text(manifest.get("machine_id")),receipt.request().before().machineId(),id);
            var choices=facade.readContracts().stream().filter(c->c.operation().value().equals(method.family().step())).toList();
            assertEquals(1,choices.size(),id);
            Object replayed=choices.getFirst().replay(receipt);
            assertEquals(ChinaCasesCodec.decodeOriginal(method,receipt),replayed,id);
            assertEquals(caller.step(),ChinaCasesCodec.executionStep(method,receipt),id);
            RawJson numeric=ChinaCasesCodec.encodeNumericExecutionResult(method,receipt);
            assertEquals(object(read(ExactRef.fromJson(cell.get("python_numeric_result")))),
                    object(numeric.bytes()),id+" complete original numeric driver report");
            RawJson actual=RootChinaCasesPublicStepProducts.present(method,caller.step(),receipt);
            assertEquals(object(read(ExactRef.fromJson(cell.get("python_public_result")))),
                    object(actual.bytes()),id+" complete public EXECUTE result");
            assertTrue(object(numeric.bytes()).get("query_sequence").isIntegralNumber(),id);
            assertTrue(object(actual.bytes()).get("query_sequence").isTextual(),id);
            OperationKey unrelated=new OperationKey(method.family().step()+"-"+(method==Method.SCOREBOARD?"different":"646966666572656e74"));
            assertThrows(IllegalArgumentException.class,()->RootChinaCasesPublicStepProducts.present(method,unrelated,receipt),id);
        }
        assertEquals(TAILS.keySet(),seen,"every real Cases READ needs a retained full-result corpus entry");
    }

    @org.junit.jupiter.api.io.TempDir Path writerDirectory;

    @Test void originalSoftwarePacketsUseTheSameFacadeProjectorAndTheRealCentralWriterArchiveAndSnapshot()throws Exception {
        ObjectNode manifest=object(read(manifestRef()));
        var sources=RootChinaCasesPublicProductsTest.actualHistorySources();
        var covered=EnumSet.noneOf(Method.class);int cellIndex=0;
        for(JsonNode value:array(manifest.get("writer_cases"),10,32)) {
            ObjectNode cell=StrictJson.object(value,Set.of("id","method","execute_arguments","native_result","python_numeric_result","python_public_result"));
            String id=StrictJson.text(cell.get("id"));
            Method method=Method.valueOf(StrictJson.text(cell.get("method")));assertTrue(method.readOnly());covered.add(method);
            var caller=PublicPlanningCodec.decodeExecute(new PublicBindings.Value(new RawJson(read(ExactRef.fromJson(cell.get("execute_arguments"))))));
            assertEquals(method,ChinaCasesCodec.executionMethod(caller.step()).orElseThrow(),id);
            RawJson originalPacket=new RawJson(read(ExactRef.fromJson(cell.get("native_result"))));
            ObjectNode expectedNumeric=object(read(ExactRef.fromJson(cell.get("python_numeric_result"))));
            ObjectNode expectedPublic=object(read(ExactRef.fromJson(cell.get("python_public_result"))));
            var facade=new java.util.concurrent.atomic.AtomicReference<ChinaCasesFacade>();
            var scenario=new org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture.SoftwareReadScenario(
                    "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86",
                    "ck3-1.19.0.6-msvc-x64",source->{
                        var actual=new ChinaCasesFacade(NEVER_LIVE,NEVER_ACTION,RootChinaCasesPublicProducts.historyFactory(sources));
                        facade.set(actual);
                        return actual.readContracts().stream().filter(c->TAILS.keySet().stream()
                                .anyMatch(m->c.operation().value().equals(m.family().step()))).toList();
                    },request->{
                        assertEquals(object(OpportunityJson.encode(ChinaCasesCodec.executionArguments(caller.step(),BigInteger.valueOf(5)))),
                                object(request.additionalFields().bytes()));
                        return originalPacket; // Exact original software producer token; never a fabricated READ receipt.
                    },java.util.Optional.of("1.19.0.6"),Set.of(method.family().capability()));
            try(var fixture=new org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture(
                    writerDirectory.resolve("cases-"+cellIndex++),false,scenario)) {
                var publisher=new org.xar.ck3.control.application.driver.DriverReadHistoryPublisher(
                        fixture.driverAuthority(),fixture.archive,fixture.reads.catalog(),List.of(fixture.observationSource().sourceRef()));
                fixture.bindAdditionalTransitionAuthority(org.xar.ck3.control.continuity.writer.WriterContracts.DRIVER_READ_HISTORY_KIND,publisher);
                fixture.bindKnownReadObserver(publisher::enqueue);
                var initial=fixture.ready();var publicResult=new java.util.concurrent.atomic.AtomicReference<RawJson>();
                ReadContract<?> contract=facade.get().readContracts().stream()
                        .filter(c->c.operation().value().equals(method.family().step())).findFirst().orElseThrow();
                assertTrue(fixture.reads.catalog().containsIdentity(contract));
                fixture.writer.locked(same->{
                    initializeSoftwareDriver(fixture,same,initial.request().before());
                    fixture.collector.current(same,initial.request().before(),java.time.Instant.now().plusSeconds(20),lease->{
                        publicResult.set(centralRead(fixture,publisher,same,lease,contract,method,caller,initial.request(),expectedNumeric));
                        return null;
                    });
                    assertEquals(expectedPublic,object(publicResult.get().bytes()),id);
                    var committed=publisher.flushActualReads(same).orElseThrow();
                    assertEquals(1,committed.actual().head().sequence());assertFalse(publisher.hasPending(same));
                    fixture.collector.current(same,initial.request().before(),java.time.Instant.now().plusSeconds(20),lease->{
                        var complete=lease.driver().driver();assertEquals(1,complete.commandHistory().size(),id);
                        var entry=complete.commandHistory().getFirst();
                        var row=org.xar.ck3.control.application.history.DriverExecuteQueryHistoryRowProducer.decode(entry.originalRow().json());
                        assertEquals(caller.step().value(),row.command(),id);
                        assertEquals(method.family().step(),OpportunityJson.text(row.result().get("step"),"step"),id);
                        assertEquals(row,org.xar.ck3.control.application.history.DriverExecuteQueryHistoryRowProducer.decode(row.encode()));
                        var full=fixture.archive.withSession(same).loadFullMaterial(row.source().fullResult());
                        assertEquals(expectedNumeric,object(full.bytes()),id+" complete preserved numeric artifact");
                        int reads=fixture.scenarioReadWrites();String head=same.head().digest();
                        replayExecuteHistory(fixture,same,contract,row);
                        RawJson snapshot=org.xar.ck3.control.application.driver.PublicSnapshotCodec.encode(
                                org.xar.ck3.control.application.driver.PublicSnapshotCodec.export(lease.frame(),true));
                        ObjectNode publicSnapshot=object(snapshot.bytes());
                        assertEquals(expectedPublic,publicSnapshot.at("/native_command_history/0/result"),id);
                        assertEquals(lease.frame().semantic(),org.xar.ck3.control.application.driver.PublicSnapshotCodec.decode(snapshot));
                        assertEquals(reads,fixture.scenarioReadWrites());assertEquals(head,same.head().digest());
                        assertEquals(0,fixture.nativeActionWrites());return null;
                    });
                    return null;
                });
            }
        }
        assertEquals(TAILS.keySet(),covered,"all ten source-owned fixed contracts must join the real software writer");
    }

    private static <T>RawJson centralRead(org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture fixture,
            org.xar.ck3.control.application.driver.DriverReadHistoryPublisher publisher,
            org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
            org.xar.ck3.control.application.readiness.ReadinessAuthority.LeaseSnapshot lease,
            ReadContract<T> contract,Method method,PublicPlanningCodec.ExecuteRequest caller,
            org.xar.ck3.control.application.planning.PlanningRequest original,ObjectNode expectedNumeric) {
        var frame=lease.frame();caller.requireCurrent(original);assertEquals(original.before(),frame.identity());
        var requested=new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),
                new OperationKey(method.family().step()),ChinaCasesCodec.executionArguments(caller.step(),frame.connectionGeneration()),
                java.time.Instant.now().plusSeconds(20));
        var result=fixture.reads.read(same,contract,requested);
        if(!(result instanceof PlanningReadResult.Known<T> actual))throw new AssertionError("original software Cases READ unavailable: "+result);
        assertEquals(contract.replay(actual.receipt()),actual.value());
        var projection=assertInstanceOf(org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.ExecuteProjection.class,
                contract.projectOriginalHistoryPayload(actual.receipt()));
        assertEquals(caller.step(),projection.originalCommand());
        assertEquals(new OperationKey(method.family().step()),projection.logicalOperation());
        assertEquals(expectedNumeric,object(projection.fullResult().bytes()));
        RawJson publicResult=RootChinaCasesPublicStepProducts.present(method,caller.step(),actual.receipt());
        assertInstanceOf(org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.FullStored.class,
                publisher.enqueueRich(contract,actual,List.of(actual)));
        return publicResult;
    }
    private static <T>void replayExecuteHistory(org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture fixture,
            org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,ReadContract<T> contract,
            org.xar.ck3.control.application.history.DriverExecuteQueryHistoryRowProducer.RawHistoryRow row)throws IOException {
        var replay=org.xar.ck3.control.application.history.DriverExecuteQueryHistoryRowProducer.replayCanonical(
                fixture.archive.withSession(same),fixture.reads.catalog(),contract,row);
        assertEquals(row.source().originalReceipt(),replay.originalReceipt());
        assertEquals(contract.replay(replay.receipt()),replay.value());
    }
    private static void initializeSoftwareDriver(org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture fixture,
            org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
            org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity before)throws IOException {
        fixture.collector.current(same,before,java.time.Instant.now().plusSeconds(20),lease->{
            var configuration=new org.xar.ck3.control.application.capabilities.DynamicCapabilities.Configuration(
                    java.util.Optional.empty(),java.util.Optional.empty(),3,3,false,false);
            var presentation=new org.xar.ck3.control.application.capabilities.CapabilitySessionPresentation(false,java.util.Optional.empty(),
                    java.util.Optional.of(org.xar.ck3.control.application.capabilities.CapabilitySessionPresentation.RestoreKind.NEW_EPISODE),
                    org.xar.ck3.control.application.capabilities.CapabilitySessionPresentation.BindingState.ACTIVE_NEW,
                    java.util.Optional.empty(),java.util.Optional.empty(),java.util.Optional.empty(),java.util.Optional.empty());
            RawJson policyJson=PublicDataJson.encode(StrictJson.object().put("actual_software_start_policy",true));
            var policy=fixture.archive.preserveMaterial(policyJson);
            var produced=org.xar.ck3.control.application.driver.DriverCapabilityStateProducer.initializeNewEpisode(
                    lease.frame(),lease.driver(),configuration,presentation,policy,fixture.archive.withSession(same));
            fixture.driverAuthority().publishCapabilityInputs(same,lease.driver().stamp(),produced.expectedAuxiliarySha256(),produced);
            return null;
        });
    }

    private static PublicPlanningCodec.ExecuteRequest caller(String step) {
        return PublicPlanningCodec.decodeExecute(new PublicBindings.Value(PublicDataJson.encode(
                StrictJson.object().put("step",step).put("expected_revision","18446744073709551615"))));
    }
    private static ExactRef manifestRef() {
        return new ExactRef(required("xar.china.cases.execute.fixture.path"),
                Long.parseLong(required("xar.china.cases.execute.fixture.bytes")),required("xar.china.cases.execute.fixture.sha256"));
    }
    private static String required(String name) {
        String value=System.getProperty(name);
        if(value==null||value.isEmpty())throw new IllegalStateException("mandatory original EXECUTE corpus missing: "+name);
        return value;
    }
    private static List<JsonNode> array(JsonNode node,int minimum,int maximum) {
        assertTrue(node!=null&&node.isArray()&&node.size()>=minimum&&node.size()<=maximum);
        var values=new ArrayList<JsonNode>();node.forEach(values::add);return List.copyOf(values);
    }
    private static ObjectNode object(byte[] bytes) {
        assertTrue(bytes.length>0&&bytes.length<=DATA_MAX,"bounded original object DATA required");
        return PublicDataJson.object(new RawJson(bytes));
    }
    private static String sha(byte[] bytes)throws IOException {
        try{return HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes));}
        catch(java.security.NoSuchAlgorithmException impossible){throw new IOException("SHA-256 unavailable",impossible);}
    }
    private static byte[] read(ExactRef ref)throws IOException {
        Path path=Path.of(ref.path());
        if(!path.isAbsolute()||!path.normalize().equals(path)||ref.bytes()<1||ref.bytes()>DATA_MAX
                ||path.getFileName().toString().toLowerCase(java.util.Locale.ROOT).endsWith(".exe"))
            throw new IOException("explicit bounded original DATA/source ref required");
        if(Files.size(path)!=ref.bytes())throw new IOException("original fixture length drift");
        var before=SharedSourceFiles.observe(path);
        if(before.source().bytes()!=ref.bytes()||!before.source().sha256().equals(ref.sha256()))throw new IOException("original fixture source drift");
        byte[] bytes;try(var input=Files.newInputStream(path)){bytes=input.readNBytes(DATA_MAX+1);}
        SharedSourceFiles.assertUnchanged(before);
        if(bytes.length!=ref.bytes()||!sha(bytes).equals(ref.sha256()))
            throw new IOException("original EXECUTE fixture bytes/hash drift");
        return bytes;
    }
}
