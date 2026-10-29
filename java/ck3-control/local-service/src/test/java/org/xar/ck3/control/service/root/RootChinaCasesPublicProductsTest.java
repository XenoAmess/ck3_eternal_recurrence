package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesFacade;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesContract.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import static org.junit.jupiter.api.Assertions.*;

/** Actual software transport/collector/archive and public consumer tests. They do not mint a managed Root/source qualification. */
final class RootChinaCasesPublicProductsTest {
    private static final String EXE="2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86";
    private static final ExactRef SOURCE=new ExactRef("software-china-cases-public-source",1,"a".repeat(64));
    @TempDir Path directory;

    /** Source DATA only; actual Root Inputs/loaded-class/Native qualification is still performed by production startup. */
    static RootChinaCasesPublicProducts.Sources actualHistorySources()throws Exception {
        String configured=System.getProperty("xar.china.cases.root.history.source-map");
        assertNotNull(configured,"complete CI must provide the actual immutable Root history source map");
        byte[] bytes;
        try(var input=Files.newInputStream(Path.of(configured))){bytes=input.readNBytes(131073);}
        assertTrue(bytes.length<=131072,"bounded actual source map required");
        ObjectNode source=StrictJson.object(PublicDataJson.object(new RawJson(bytes)).get("history_sources"),Set.of("facade","original_decoder","public_contract","public_codec","public_service","root_product"));
        var actual=new RootChinaCasesPublicProducts.Sources(ExactRef.fromJson(source.get("facade")),ExactRef.fromJson(source.get("original_decoder")),
                ExactRef.fromJson(source.get("public_contract")),ExactRef.fromJson(source.get("public_codec")),
                ExactRef.fromJson(source.get("public_service")),ExactRef.fromJson(source.get("root_product")));
        for(ExactRef expected:List.of(actual.facade(),actual.originalDecoder(),actual.publicContract(),actual.publicCodec(),actual.publicService(),actual.rootProduct())) {
            var measured=org.xar.ck3.control.build.ControlBuild.FileRef.measure(Path.of(expected.path()));
            assertEquals(Path.of(expected.path()).toRealPath(),Path.of(measured.path()).toRealPath(),"actual source path drift");
            assertEquals(expected.bytes(),measured.bytes(),"actual source length drift");assertEquals(expected.sha256(),measured.sha256(),"actual source content drift");
        }
        return actual;
    }

    @Test void sameFormalFacadeOwnsExactlyTenImmutableSourceProjectorsAndProgressRemainsOutsideCases()throws Exception {
        var sources=actualHistorySources();var factory=RootChinaCasesPublicProducts.historyFactory(sources);
        assertEquals(DriverReadHistoryRichMaterial.Kind.PUBLIC_EXECUTE_QUERY,factory.kind());
        var facade=new ChinaCasesFacade(new PlanningReadPort(){
            @Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){throw new AssertionError("construction must not read");}
        },noAction(),factory);
        assertEquals(11,facade.readContracts().size());
        for(var contract:facade.readContracts()) {
            if(contract.operation().value().equals(org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesCodec.Family.PROGRESS.step()))
                assertTrue(contract.originalHistoryKind().isEmpty());
            else assertEquals(Optional.of(DriverReadHistoryRichMaterial.Kind.PUBLIC_EXECUTE_QUERY),contract.originalHistoryKind());
        }
        assertEquals(10,facade.readContracts().stream().filter(value->value.originalHistoryKind().isPresent()).count());
        var duplicate=new RootChinaCasesPublicProducts.Sources(sources.facade(),sources.facade(),sources.publicContract(),sources.publicCodec(),sources.publicService(),sources.rootProduct());
        assertThrows(IllegalArgumentException.class,()->RootChinaCasesPublicProducts.historyFactory(duplicate));
    }

    @Test void exactElevenBindingsDeferInvocationAndRejectWrongTypesBeforeActualRootAccess()throws Exception {
        var calls=new AtomicInteger();var registry=new PublicBindings();
        RootChinaCasesPublicProducts.register(registry,SOURCE,request->{calls.incrementAndGet();throw new UncheckedIOException(new IOException("actual Root not installed in this DATA test"));},
                request->{calls.incrementAndGet();throw new UncheckedIOException(new IOException("actual Root not installed in this DATA test"));});
        assertEquals(0,calls.get());assertFalse(registry.frozen());
        Set<PublicMethod> expected=Arrays.stream(Method.values()).map(RootChinaCasesPublicProducts::publicMethod).collect(java.util.stream.Collectors.toUnmodifiableSet());
        assertEquals(11,expected.size());
        for(Method method:Method.values()) {
            var binding=registry.lookup(RootChinaCasesPublicProducts.publicMethod(method)).orElseThrow();
            assertEquals(method.readOnly()?ReadRequest.class:ActionRequest.class,binding.requestType());
            assertThrows(IllegalArgumentException.class,()->binding.invoke(arguments(method==Method.ACTIVATE_SCOREBOARD?actionArgs():readArgs(method))));
        }
        assertEquals(0,calls.get());registry.freeze(expected);
        for(Method method:Method.values()) {
            var binding=registry.lookup(RootChinaCasesPublicProducts.publicMethod(method)).orElseThrow();
            ObjectNode input=method.readOnly()?readArgs(method):actionArgs();
            assertThrows(UncheckedIOException.class,()->binding.invoke(arguments(input)));
            int actualCalls=calls.get();ObjectNode wrong=input.deepCopy().put("expected_revision",true);
            assertThrows(IllegalArgumentException.class,()->binding.invoke(arguments(wrong)));assertEquals(actualCalls,calls.get());
            ObjectNode extra=(method.readOnly()?readArgs(method):actionArgs()).put("invented_alias",0);
            assertThrows(IllegalArgumentException.class,()->binding.invoke(arguments(extra)));assertEquals(actualCalls,calls.get());
        }
        assertEquals(11,calls.get());
    }

    @Test void realOriginalB1FixtureTraversesSameCollectorNativeReadArchiveServiceAndPublicRegistry()throws Exception {
        ObjectNode original=originalB1();
        var fixtureRef=new AtomicReference<ActionWriterIntegrationFixture>();
        var payload=new AtomicReference<RawJson>();
        var scoped=new RootChinaCasesPublicProducts.ScopedQueries(()->{
            var fixture=Objects.requireNonNull(fixtureRef.get(),"actual fixture has not been bound");
            try {Session same=fixture.writer.borrowedSession();return new RootChinaCasesPublicProducts.QueryPorts(fixture.reads,fixture.archive.withSession(same),fixture.frameLoader(),same);}
            catch(IOException unavailable){throw new UncheckedIOException(unavailable);}
        });
        var historySources=actualHistorySources();
        var facade=new ChinaCasesFacade(scoped,noAction(),RootChinaCasesPublicProducts.historyFactory(historySources));var service=new ChinaCasesService(facade);
        var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario(EXE,"controlled-china-cases",ref->facade.readContracts(),
                request->{assertEquals("query-zhongguo-b1-cycle-snapshot-v1",request.step());assertEquals(Set.of("request_nonce"),request.additionalFields().objectFieldNames());return Objects.requireNonNull(payload.get());},
                Optional.of("1.19.0.6"),Set.of());
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("central"),false,scenario)) {
            fixtureRef.set(fixture);var ready=fixture.ready();
            fixture.writer.locked(same->fixture.collector.current(same,ready.request().before(),Instant.now().plusSeconds(30),lease->{
                Complete frame=lease.frame();Instant deadline=Instant.now().plusSeconds(20);
                var originalContext=new ChinaCasesFacade.Context(frame.identity(),frame.source(),frame.sessionId(),frame.connectionGeneration(),deadline);
                var originalHello=(NativeWire.Hello)NativeWire.decode(fixture.archive.withSession(same).readOriginalPacket(lease.originalHello()));
                var metadata=RootChinaCasesPublicProducts.helloContext(frame,originalContext,originalHello);
                ObjectNode nativeFrame=original.deepCopy().put("snapshot_revision",frame.identity().frame().identity().nativeRevision())
                        .put("date_raw",frame.identity().frame().identity().dateRaw()).put("player_character_id",frame.identity().frame().identity().player())
                        .put("manager_character_id",frame.identity().frame().identity().player()).put("request_nonce","portable-1");
                ObjectNode envelope=StrictJson.object().put("step",Method.B1.family().step()).put("accepted",true).put("status","available")
                        .put("query_sequence",StrictJson.UINT64_MAX).put("snapshot_revision",frame.identity().frame().identity().nativeRevision()).put("backend_id","controlled-original-b1");
                envelope.set(Method.B1.payload(),nativeFrame);payload.set(PublicDataJson.encode(envelope));
                var observed=new AtomicReference<ChinaCasesService.Known>();var registry=new PublicBindings();
                RootChinaCasesPublicProducts.register(registry,SOURCE,request-> {
                    try {
                        return scoped.within(frame,same,originalHello,()->{
                            var outcome=service.query(request,metadata);assertInstanceOf(ChinaCasesService.Known.class,outcome);
                            var known=(ChinaCasesService.Known)outcome;observed.set(known);return known.response();
                        });
                    }catch(IOException unavailable){throw new UncheckedIOException(unavailable);}
                },request->{throw new AssertionError("READ invoked action");});
                registry.freeze(Arrays.stream(Method.values()).map(RootChinaCasesPublicProducts::publicMethod).collect(java.util.stream.Collectors.toSet()));
                ObjectNode args=StrictJson.object().put("request_nonce","portable-1").put("expected_revision",frame.identity().frame().revision().toString());
                int writes=fixture.scenarioReadWrites();String head=same.head().digest();
                ObjectNode result;
                try {
                    result=PublicDataJson.object(registry.lookup(PublicMethod.QUERY_ZHONGGUO_B1_CYCLE_SNAPSHOT_V1).orElseThrow().invoke(arguments(args)));
                } catch(InterruptedException interrupted) {
                    Thread.currentThread().interrupt();
                    throw new IOException("original China-cases public READ was interrupted",interrupted);
                }
                var known=observed.get();assertEquals(writes+1,fixture.scenarioReadWrites());assertEquals(head,same.head().digest());
                assertEquals(known.receipt(),fixture.archive.withSession(same).loadRead(known.originalReceipt()));
                var originalContract=facade.readContracts().getFirst();
                assertSame(originalContract,fixture.actualReadCatalog().contracts().stream().filter(value->value.operation().equals(originalContract.operation())).findFirst().orElseThrow());
                var rich=assertInstanceOf(DriverReadHistoryRichMaterial.ExecuteProjection.class,originalContract.projectOriginalHistoryPayload(known.receipt()));
                assertEquals(known.receipt().request().operation(),rich.logicalOperation());
                assertEquals(ChinaCasesCodec.executionStep(Method.B1,known.receipt()),rich.originalCommand());
                assertEquals(DriverJson.object(ChinaCasesCodec.encodeNumericExecutionResult(Method.B1,known.receipt()).bytes(),RawJson.MAXIMUM_BYTES),DriverJson.object(rich.fullResult().bytes(),RawJson.MAXIMUM_BYTES));
                assertEquals(DriverJson.object(ChinaCasesCodec.encodeExecutionResult(Method.B1,known.receipt()).bytes(),RawJson.MAXIMUM_BYTES),rich.publicNumbers().toPublic(DriverJson.object(rich.fullResult().bytes(),RawJson.MAXIMUM_BYTES)));
                assertEquals(List.of(historySources.facade(),historySources.originalDecoder(),historySources.publicContract(),historySources.publicCodec(),historySources.publicService(),historySources.rootProduct()),rich.sourceClosure());
                assertEquals(writes+1,fixture.scenarioReadWrites());assertEquals(head,same.head().digest(),"pure projection is not canonical history publication");
                assertEquals(StrictJson.UINT64_MAX.toString(),result.get("query_sequence").textValue());assertTrue(result.get("snapshot_revision").isTextual());
                assertEquals("1.19.0.6",result.path("build").path("version").textValue());assertEquals(EXE,result.path("build").path("exe_sha256").textValue().toLowerCase(java.util.Locale.ROOT));
                assertTrue(result.get("manager_character_id").isIntegralNumber());assertTrue(result.get("invariants").isObject());assertTrue(result.get("anomalies").isArray());
                assertEquals(PublicDataJson.object(known.response().publicJson()),result);
                ChinaCasesCodec.decodeReadResult(ChinaCasesCodec.decodeRead(Method.B1,args),metadata,known.receipt(),PublicDataJson.encode(result));
                assertThrows(IllegalArgumentException.class,()->scoped.read(facade.readContracts().getFirst(),known.receipt().request()));
                var stale=args.deepCopy().put("expected_revision",frame.identity().frame().revision().add(BigInteger.ONE).toString());
                assertThrows(IllegalArgumentException.class,()->registry.lookup(PublicMethod.QUERY_ZHONGGUO_B1_CYCLE_SNAPSHOT_V1).orElseThrow().invoke(arguments(stale)));
                assertEquals(writes+1,fixture.scenarioReadWrites());
                Complete changed=new Complete(frame.identity(),frame.source(),frame.sessionId(),frame.connectionGeneration().add(BigInteger.ONE),frame.semantic(),frame.originalEvidence(),frame.observedAt(),frame.fullBindingSha256());
                assertThrows(IllegalArgumentException.class,()->RootChinaCasesPublicProducts.verifyKnown(changed,known.receipt().request(),
                        new PlanningReadResult.Known<>(org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesCodec.decodeOriginal(Method.B1,known.receipt()),known.receipt(),known.originalReceipt()),
                        fixture.archive.withSession(same),fixture.frameLoader()));
                var altered=result.deepCopy();((ObjectNode)altered.get("binding")).put("expected_revision",true);
                assertThrows(IllegalArgumentException.class,()->ChinaCasesCodec.decodeReadResult(ChinaCasesCodec.decodeRead(Method.B1,args),metadata,known.receipt(),PublicDataJson.encode(altered)));
                return null;
            }));
        }
    }

    @Test void actionCommandRetainsNativeUint64VocabularyAndDoesNotGrantAnAppliedResult()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("command"),false)) {
            var ready=fixture.ready();fixture.writer.locked(same->fixture.collector.current(same,ready.request().before(),Instant.now().plusSeconds(20),lease->{
                var frame=lease.frame();ObjectNode input=actionArgs().put("expected_revision",frame.identity().frame().revision().toString())
                        .put("expected_native_revision",frame.identity().frame().identity().nativeRevision().toString())
                        .put("expected_connection_generation",frame.connectionGeneration().toString())
                        .put("expected_player_character_id",frame.identity().frame().identity().player());
                ActionRequest request=ChinaCasesCodec.decodeAction(input);
                var command=RootChinaCasesPublicProducts.commandFor(request,frame,Instant.now().plusSeconds(20));
                assertEquals(command.actionId(),RootChinaCasesPublicProducts.commandFor(request,frame,Instant.now().plusSeconds(21)).actionId(),"a deadline refresh cannot escape the retained identical intent/UNKNOWN");
                Complete nextContext=new Complete(frame.identity(),frame.source(),frame.sessionId()+"-next",frame.connectionGeneration(),frame.semantic(),frame.originalEvidence(),frame.observedAt(),frame.fullBindingSha256());
                assertNotEquals(command.actionId(),RootChinaCasesPublicProducts.commandFor(request,nextContext,Instant.now().plusSeconds(20)).actionId(),"the same nonce is not a permanent cross-context action identity");
                assertEquals(request,RootChinaCasesPublicProducts.decodeCommand(command));assertEquals(request.nativeArguments(),command.arguments());
                assertTrue(command.arguments().members().containsKey("expected_public_revision"));assertFalse(command.arguments().members().containsKey("expected_revision"));
                assertTrue(command.expected().observerSchema().contains("independent-postcondition"));
                input.put("expected_revision",frame.identity().frame().revision().add(BigInteger.ONE).toString());
                assertThrows(IllegalArgumentException.class,()->RootChinaCasesPublicProducts.commandFor(ChinaCasesCodec.decodeAction(input),frame,Instant.now().plusSeconds(20)));
                assertEquals(0,fixture.nativeActionWrites());return null;
            }));
        }
    }

    @Test void preparationRequiresActualBoundCoreAndOnlyExactSourceRoles() {
        var sources=new RootChinaCasesPublicProducts.Sources(SOURCE,SOURCE,SOURCE,SOURCE,SOURCE,SOURCE);
        var prepared=RootChinaCasesPublicProducts.prepare(sources);assertSame(sources,prepared.sources());assertTrue(prepared.domainRegistrations().isEmpty());assertTrue(prepared.privatePermissions().isEmpty());
        assertThrows(NullPointerException.class,()->prepared.install(null));assertThrows(NullPointerException.class,()->RootChinaCasesPublicProducts.install(null,new PublicBindings()));
    }

    @Test void actualSoleCoordinatorNativePacketAndArchiveKeepPendingAckAndRejectionWithoutAnAppliedEffect()throws Exception {
        for(boolean accepted:List.of(false,true))runActualOriginalAction(accepted);
    }
    private void runActualOriginalAction(boolean accepted)throws Exception {
        String transport="game.contract.zhongguo-scoreboard-action-v1-fail-closed";
        var operation=new OperationKey("activate-zhongguo-scoreboard-v1");
        var fixtureRef=new AtomicReference<ActionWriterIntegrationFixture>();var reviewed=new AtomicReference<ExactRef>();var nativeResult=new AtomicReference<RawJson>();
        var readScenario=new ActionWriterIntegrationFixture.SoftwareReadScenario(EXE,"controlled-china-scoreboard",ref->{reviewed.set(ref);return List.of();},
                request->{throw new AssertionError("ACK-only action issued an additional domain query");},Optional.of("1.19.0.6"),Set.of(transport));
        var actionScenario=new ActionWriterIntegrationFixture.SoftwareActionScenario(operation,transport,(command,attempt,dispatch)->{
            var fixture=Objects.requireNonNull(fixtureRef.get());
            try{return RootChinaCasesPublicProducts.projectAck(command,attempt,dispatch,fixture.archive.withSession(fixture.writer.borrowedSession()),fixture.frameLoader()).result();}
            catch(IOException unavailable){throw new UncheckedIOException(unavailable);}
        },()->{},Optional.of(()->Objects.requireNonNull(nativeResult.get())),Optional.empty(),false,Optional.of(RootChinaCasesPublicProducts::preparePrimitive));
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve(accepted?"original-action-pending":"original-action-reject"),false,readScenario,List.of(actionScenario))) {
            fixtureRef.set(fixture);
            fixture.bindAdditionalArchivedVerifier(new NativeRecordedEvidenceVerifier.Binding(operation,reviewed.get(),
                    (head,receipt,archive)->RootChinaCasesPublicProducts.verifyArchived(receipt,archive,fixture.frameLoader())));
            var ready=fixture.ready();
            fixture.writer.locked(same->{
                ActionCommand command=fixture.collector.current(same,ready.request().before(),Instant.now().plusSeconds(25),lease->{
                    var frame=lease.frame();ObjectNode request=actionArgs().put("expected_revision",frame.identity().frame().revision().toString())
                            .put("expected_native_revision",frame.identity().frame().identity().nativeRevision().toString())
                            .put("expected_connection_generation",frame.connectionGeneration().toString()).put("expected_player_character_id",frame.identity().frame().identity().player())
                            .put("expected_observation_sequence","7");
                    ActionRequest typed=ChinaCasesCodec.decodeAction(request);
                    ObjectNode result=StrictJson.object().put("step",operation.value()).put("accepted",false).put("status","unavailable")
                            .put("request_nonce",typed.requestNonce()).put("action",typed.action().wire()).put("action_sequence",1)
                            .put("snapshot_revision",typed.expectedNativeRevision()).put("rejection_reason","controlled_original_fail_closed").put("production_capability_advertised",false)
                            .put("backend_id","controlled-china-scoreboard");result.putNull("action_ack");nativeResult.set(PublicDataJson.encode(result));
                    return RootChinaCasesPublicProducts.commandFor(typed,frame,Instant.now().plusSeconds(20));
                });
                if(accepted)nativeResult.set(originalScoreboard(command));
                var receipt=fixture.coordinator.execute(same,command);assertEquals(1,fixture.nativeActionWrites());
                assertTrue(receipt.applied().isEmpty());var archive=fixture.archive.withSession(same);
                var attempt=ActionTransitions.attempt(receipt.state()).orElseThrow();var ack=assertInstanceOf(NativeActionPort.AckReceived.class,ActionTransitions.dispatch(receipt.state()).orElseThrow());
                if(accepted){
                    assertInstanceOf(ActionState.Unknown.class,receipt.state());
                    var pending=RootChinaCasesPublicProducts.projectAck(command,attempt,ack,archive,fixture.frameLoader());
                    assertInstanceOf(ActionPorts.Pending.class,pending.result());assertTrue(pending.compatibleResult().isEmpty());
                    assertEquals(receipt,fixture.coordinator.execute(same,command));assertEquals(1,fixture.nativeActionWrites(),"UNKNOWN original is never replayed");
                }else{
                    var settled=assertInstanceOf(ActionState.Settled.class,receipt.state());assertInstanceOf(ActionState.Rejected.class,settled.settlement());
                    RootChinaCasesPublicProducts.verifyArchived(receipt,archive,fixture.frameLoader());
                }
                var original=RootChinaCasesPublicProducts.originalAction(command,attempt,ack,archive,fixture.frameLoader());
                assertEquals(nativeResult.get(),original.raw());assertEquals(command.arguments(),original.request().nativeArguments());
                ObjectNode publicResult=ChinaCasesCodec.encodeActionResult(original.request(),original.context(),original.raw());
                assertEquals(accepted,publicResult.get("accepted").booleanValue());assertEquals(!accepted,publicResult.get("action_ack").isNull());assertTrue(publicResult.get("snapshot_revision").isTextual());
                if(accepted)assertFalse(publicResult.get("action_ack").get("postcondition_verified").booleanValue());
                var failed=new NativeActionPort.AckReceived(ack.requestId(),false,ack.originalResultToken(),ack.originalFrame(),ack.originalPacket(),ack.outbound(),ack.custody());
                assertInstanceOf(ActionPorts.Pending.class,RootChinaCasesPublicProducts.projectAck(command,attempt,failed,archive,fixture.frameLoader()).result());
                assertThrows(IllegalArgumentException.class,()->RootChinaCasesPublicProducts.originalAction(command,attempt,failed,archive,fixture.frameLoader()));
                var replay=ActionReceiptCodec.decodeReceipt(ActionReceiptCodec.encodeReceipt(receipt,archive),archive);
                assertEquals(receipt,replay);assertEquals(1,fixture.nativeActionWrites());return null;
            });
        }
    }

    private static ObjectNode readArgs(Method method) {
        ObjectNode input=StrictJson.object().put("request_nonce","portable-1").put("expected_revision","0");
        switch(method){case CASE->input.put("case_kind","zhongguo.b1.performance");case AI_OWNED->{input.put("owner_character_id",30);input.put("subject_character_id",20);}
            case RESULT,PIP,PROJECTS->input.put("owner_character_id",30);case INCIDENT->{input.put("owner_character_id",30);input.put("profile","x");}default->{}}
        return input;
    }
    private static ObjectNode actionArgs() {
        return StrictJson.object().put("request_nonce","portable-1").put("action","open").put("expected_revision","0").put("expected_native_revision","1")
                .put("expected_connection_generation","1").put("expected_player_character_id",73).put("expected_provider_session_id","A".repeat(32))
                .put("expected_observation_sequence",StrictJson.UINT64_MAX.toString()).put("expected_observed_state_revision","1")
                .put("expected_tree_fingerprint_v1","B".repeat(64)).put("expected_semantic_fingerprint_v1","C".repeat(64))
                .put("expected_window_instance_pointer","0x100").put("expected_target_instance_pointer","0x200").put("expected_target_vtable_pointer","0x300");
    }
    private static PublicBindings.Arguments arguments(ObjectNode input){return PublicBindings.present(PublicDataJson.encode(input));}
    private static ActionCoordinatorPort noAction(){return new ActionCoordinatorPort(){
        @Override public ActionReceipt execute(ActionCommand c){throw new AssertionError("query submitted an action");}
        @Override public ActionReceipt reconcile(String id){throw new AssertionError("query reconciled an action");}
    };}
    private ObjectNode originalB1()throws Exception {
        String python=System.getProperty("xar.native.producer.python");
        if(python==null||!Path.of(python).isAbsolute())throw new IllegalStateException("NOT EXECUTED: absolute xar.native.producer.python required for original B1 fixture producer");
        Path root=Path.of(required("xar.public.original.repo.root"));if(!root.isAbsolute())throw new IOException("absolute original repository root required");
        Path contract=root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_b1_cycle_snapshot_contract.py");
        Path fixture=root.resolve("ck3_autonomous_player/tests/unit/test_zhongguo_b1_cycle_snapshot_v1_contract.py");
        requireSha(contract,"247729b653d2ecca49a894024c9ab6e6450fb74fe17bd559174eca166291f06d");
        requireSha(fixture,"d69e3c94348a8f5656398dc517e95679df982834fd2af0f5d869701297387394");
        String program="""
            import ast,json,runpy,sys
            from pathlib import Path
            scope=runpy.run_path(sys.argv[1])
            tree=ast.parse(Path(sys.argv[2]).read_text(encoding='utf-8-sig'))
            nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('typed','frame')]
            if len(nodes)!=2: raise RuntimeError('exact original B1 fixture producer functions missing')
            module=ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[]))
            exec(compile(module,sys.argv[2],'exec'),scope)
            print(json.dumps(scope['frame'](),separators=(',',':')))
            """;
        Path out=directory.resolve("original-b1.json"),err=directory.resolve("original-b1.stderr");
        Process child=new ProcessBuilder(python,"-X","utf8","-c",program,contract.toString(),fixture.toString()).redirectOutput(out.toFile()).redirectError(err.toFile()).start();
        if(!child.waitFor(20,TimeUnit.SECONDS)){child.destroyForcibly();throw new IOException("original B1 fixture producer timed out");}
        if(child.exitValue()!=0)throw new IOException("original B1 fixture producer failed: "+Files.readString(err));
        if(Files.size(out)>StrictJson.EXPLICIT_MAX_BYTES)throw new IOException("original B1 fixture exceeds its finite DATA lane");
        return PublicDataJson.object(new RawJson(Files.readAllBytes(out)));
    }
    private static void requireSha(Path path,String sha)throws IOException {
        if(!DriverJson.sha256(Files.readAllBytes(path)).equals(sha))throw new IOException("exact original B1 producer source changed: "+path);
    }
    private RawJson originalScoreboard(ActionCommand command)throws IOException {
        String python=required("xar.native.producer.python"),root=required("xar.public.original.repo.root"),manifest=required("xar.public.china.original.manifest");
        if(!Path.of(python).isAbsolute()||!Path.of(root).isAbsolute()||!Path.of(manifest).isAbsolute())throw new IOException("absolute original China fixture inputs required");
        new org.xar.ck3.control.build.ControlBuild.FileRef(manifest,Long.parseLong(required("xar.public.china.original.manifest.bytes")),required("xar.public.china.original.manifest.sha256")).verify();
        ObjectNode arguments=(ObjectNode)org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(command.arguments());arguments.set("expected_revision",arguments.remove("expected_public_revision"));
        String program="""
            import dataclasses,hashlib,json,runpy,sys
            from pathlib import Path
            root=Path(sys.argv[1]);manifest=json.loads(sys.argv[2]);arguments=json.loads(sys.argv[3])
            for item in manifest:
             data=(root/item['path']).read_bytes()
             if len(data)!=item['bytes'] or hashlib.sha256(data).hexdigest()!=item['sha256']:raise RuntimeError('original China source changed: '+item['path'])
            sys.path[:0]=[str(root/'ck3_autonomous_player/src'),str(root/'ck3_autonomous_player/tests/unit')]
            m=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_zhongguo_scoreboard_action_contract.py'))
            frame=m['_frame'](open_tab=None)
            frame.update(snapshot_revision=arguments['expected_native_revision'],date_raw=int(sys.argv[4]),player_character_id=arguments['expected_player_character_id'],
             provider_session_id=arguments['expected_provider_session_id'],observation_sequence=arguments['expected_observation_sequence'],observed_state_revision=arguments['expected_observed_state_revision'],
             tree_fingerprint_v1=arguments['expected_tree_fingerprint_v1'],semantic_fingerprint_v1=arguments['expected_semantic_fingerprint_v1'])
            window=m['_widget'](frame,'zg361_scoreboard_window');target=m['_widget'](frame,m['ENTRY']['received'])
            window['instance_pointer']=m['typed'](arguments['expected_window_instance_pointer']);target['instance_pointer']=m['typed'](arguments['expected_target_instance_pointer']);target['vtable_pointer']=m['typed'](arguments['expected_target_vtable_pointer'])
            request=m['build_zhongguo_scoreboard_action_v1_request'](**arguments)
            plan=m['plan_zhongguo_scoreboard_action_v1'](request,source_state=frame,observed_revision=request.expected_revision,observed_connection_generation=request.expected_connection_generation)
            ack=m['acknowledged_zhongguo_scoreboard_action_v1'](plan)
            result={'step':'activate-zhongguo-scoreboard-v1','accepted':True,'status':'acknowledged_verification_pending','request_nonce':request.request_nonce,'action':request.action,
             'action_sequence':9,'snapshot_revision':request.expected_native_revision,'rejection_reason':None,'action_ack':ack,'production_capability_advertised':False,'backend_id':'controlled-china-scoreboard'}
            print(json.dumps(result,separators=(',',':')))
            """;
        Path out=directory.resolve("original-scoreboard.json"),err=directory.resolve("original-scoreboard.stderr");
        Process child=new ProcessBuilder(python,"-X","utf8","-c",program,root,Files.readString(Path.of(manifest)),new String(PublicDataJson.encode(arguments).bytes(),StandardCharsets.UTF_8),command.before().frame().identity().dateRaw().toString())
                .redirectOutput(out.toFile()).redirectError(err.toFile()).start();
        try{if(!child.waitFor(20,TimeUnit.SECONDS)){child.destroyForcibly();throw new IOException("original scoreboard ACK producer timed out");}}
        catch(InterruptedException interrupted){child.destroyForcibly();Thread.currentThread().interrupt();throw new IOException("original scoreboard ACK producer interrupted",interrupted);}
        if(child.exitValue()!=0)throw new IOException("original scoreboard ACK producer failed: "+Files.readString(err));
        if(Files.size(out)>StrictJson.EXPLICIT_MAX_BYTES)throw new IOException("original scoreboard ACK exceeds its finite DATA lane");return new RawJson(Files.readAllBytes(out));
    }
    private static String required(String key){String value=System.getProperty(key);if(value==null||value.isBlank())throw new IllegalStateException("NOT EXECUTED: required original input property "+key);return value;}
}
