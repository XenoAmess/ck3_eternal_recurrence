package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.ArrayList;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.atomic.AtomicReference;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesDefinitions;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesExecutor;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesInstaller;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesEffects;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesRequests.Primitive;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendrules.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendrules.FrontendRulesContract.*;

/** Actual Python methods -> existing Java Executor/Effects -> physical archive/replay -> same public binding.
 * Packet and process edges are controlled software inputs. This fixture constructs no Root/Game authority. */
final class RootFrontendRulesPublicProductsTest {
    @Test void incompleteOriginalEightDrawFallbackBlocksCompleteMigration() {
        var gaps=RootFrontendRulesPublicProducts.definitionGaps();assertEquals(1,gaps.size());
        assertEquals(Method.PREPARE_RULER.publicName(),gaps.getFirst().identity());assertTrue(gaps.getFirst().reason().contains("UNKNOWN"));
    }
    @Test void crozier4MissingRandomAdmissionIsExplicitUnavailableWithoutBlanketDisablingNewGame()throws Exception {
        ObjectNode original=original();try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("unsupported4"),false)) {
            fixture.writer.locked(borrowed->fixture.archive.inSession(borrowed,archive->{
                try {
                    Software same=new Software(fixture,borrowed,archive,original);var identity=same.identity();
                    var available=List.of(org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesRequests.Primitive.ROUTE,org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesRequests.Primitive.TREE,org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesRequests.Primitive.NEW_GAME);
                    var lease=new FrontendAuthority.LeaseSnapshot(identity,same.source,ack("controlled-route",StrictJson.object().put("step","query-frontend-gui-route-v1").put("accepted",true).put("status","bookmarks")),identity.nativeEvidence(),available.stream().map(v->v.operation()).collect(java.util.stream.Collectors.toSet()),available.stream().map(v->v.capability()).collect(java.util.stream.Collectors.toSet()),NOW,NOW.plusSeconds(30));
                    var selected=new FrontendRulesService(new FrontendRulesDefinitions(Build.CK3_12004,same.sourceRef),archive);
                    var unavailable=assertThrows(FrontendRulesService.Unavailable.class,()->selected.requireAvailable(new Empty(Method.PREPARE_RULER),lease));assertEquals(Build.CK3_12004,unavailable.build());assertEquals(Method.PREPARE_RULER,unavailable.method());assertEquals(2,unavailable.missing().size());
                    selected.requireAvailable(new Empty(Method.NEW_GAME),lease);assertEquals(0,same.submitted.get());return null;
                }catch(IOException error){throw new IllegalStateException(error);}
            }));
        }
    }
    @TempDir Path temporary;
    @Test void freshRobertPreparationFromMainMenuUsesOriginalNewGameAndIndependentlySelectedModel()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("fresh-robert-menu"),false)) {
            fixture.writer.locked(borrowed->fixture.archive.inSession(borrowed,archive->{
                try {
                    Software same=new Software(fixture,borrowed,archive,StrictJson.object(),Build.CK3_12004);
                    same.frontend=true;same.freshRobert=true;same.frontendRoute=Route.MAIN_MENU;
                    var selected=same.service.prepareFreshRobert(same.invocation());
                    assertEquals(List.of(Primitive.NEW_GAME.operation(),Primitive.SELECT_1066_BOOKMARK.operation(),Primitive.SELECT_1066.operation()),same.frontendActions.stream().map(v->v.command().operation()).toList());
                    assertEquals("activate-frontend-select-bookmark-1066-v1",Primitive.SELECT_1066_BOOKMARK.operation().value());
                    assertEquals("game.command.activate-frontend-select-bookmark-1066-v1",Primitive.SELECT_1066_BOOKMARK.capability());
                    assertEquals("bookmark_rags_to_riches_duke_robert",selected.candidate().characterNameKey());
                    assertEquals(53144328,selected.candidate().dateRaw());assertTrue(same.bookmark1066Selected);assertTrue(same.bookmarkSelected);assertTrue(same.freshModelReads>=6);
                    assertEquals(selected.receipt(),archive.loadRead(selected.originalReceipt()));
                    for(ActionReceipt action:same.frontendActions) {
                        FrontendRulesContract.confirmed(action);assertEquals(action,archive.loadReceipt(archive.preserveReceipt(action)));
                        var settled=(ActionState.Settled)action.state();var prepared=settled.attempt().preparedRequest();
                        assertEquals(StrictJson.object(),FrontendRulesCodec.object(prepared.additionalFields()));
                        assertEquals(prepared,archive.loadRequest(archive.preserveRequest(prepared)));
                        assertTrue(same.installed.actions().stream().anyMatch(v->v.effect().operation().equals(action.command().operation())&&v.requiredCapability().equals(prepared.requiredCapability())));
                        assertEquals(1,same.installed.routeAdmissions().stream().filter(v->v.operation().equals(action.command().operation())).count());
                        same.installed.archivedVerifiers().stream().filter(v->v.operation().equals(action.command().operation())).findFirst().orElseThrow().verifier().verify(borrowed.head(),action,archive);
                    }
                    return null;
                }catch(IOException|InterruptedException error){throw new IllegalStateException(error);}
            }));
        }
    }
    @Test void freshRobertAlreadySelectedStillReadsTheModelWithoutAnotherMutation()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("fresh-robert-selected"),false)) {
            fixture.writer.locked(borrowed->fixture.archive.inSession(borrowed,archive->{
                try {
                    Software same=new Software(fixture,borrowed,archive,StrictJson.object(),Build.CK3_12004);
                    same.frontend=true;same.freshRobert=true;same.bookmark1066Selected=true;same.bookmarkSelected=true;
                    var selected=same.service.prepareFreshRobert(same.invocation());
                    assertEquals(0,same.submitted.get());assertTrue(same.freshModelReads>=2);
                    assertEquals("bookmark_rags_to_riches_duke_robert",selected.candidate().characterNameKey());
                    assertEquals(selected.receipt(),archive.loadRead(selected.originalReceipt()));return null;
                }catch(IOException|InterruptedException error){throw new IllegalStateException(error);}
            }));
        }
    }
    @Test void observed1066BookmarkStillSelectsRobertWithoutReselectingTheBookmark()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("fresh-1066-bookmark"),false)) {
            fixture.writer.locked(borrowed->fixture.archive.inSession(borrowed,archive->{
                try {
                    Software same=new Software(fixture,borrowed,archive,StrictJson.object(),Build.CK3_12004);
                    same.frontend=true;same.freshRobert=true;same.bookmark1066Selected=true;
                    var selected=same.service.prepareFreshRobert(same.invocation());
                    assertEquals(List.of(Primitive.SELECT_1066.operation()),same.frontendActions.stream().map(v->v.command().operation()).toList());
                    assertEquals("bookmark_rags_to_riches_duke_robert",selected.candidate().characterNameKey());return null;
                }catch(IOException|InterruptedException error){throw new IllegalStateException(error);}
            }));
        }
    }
    @Test void unconfirmedNewGameStopsBeforeSelectionAndNeverResubmits()throws Exception { unconfirmedFreshPreparation(Primitive.NEW_GAME); }
    @Test void unconfirmed1066BookmarkStopsBeforeRobertAndNeverResubmits()throws Exception { unconfirmedFreshPreparation(Primitive.SELECT_1066_BOOKMARK); }
    @Test void unconfirmedRobertSelectionStopsBeforeTheOriginalStartAndNeverResubmits()throws Exception { unconfirmedFreshPreparation(Primitive.SELECT_1066); }
    private void unconfirmedFreshPreparation(Primitive unresolved)throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("fresh-unconfirmed-"+unresolved.name()),false)) {
            fixture.writer.locked(borrowed->fixture.archive.inSession(borrowed,archive->{
                try {
                    Software same=new Software(fixture,borrowed,archive,StrictJson.object(),Build.CK3_12004);
                    same.frontend=true;same.freshRobert=true;same.frontendRoute=Route.MAIN_MENU;
                    same.unconfirmedFreshNewGame=unresolved==Primitive.NEW_GAME;same.unconfirmedFreshBookmark=unresolved==Primitive.SELECT_1066_BOOKMARK;same.unconfirmedFreshSelection=unresolved==Primitive.SELECT_1066;
                    var time=new AtomicReference<>(NOW);same.invocationClock=new Clock() {
                        @Override public java.time.ZoneId getZone(){return ZoneOffset.UTC;}
                        @Override public Clock withZone(java.time.ZoneId zone){assertEquals(ZoneOffset.UTC,zone);return this;}
                        @Override public Instant instant(){return time.get();}
                    };
                    same.afterFreshDispatch=()->{if(same.last.state() instanceof ActionState.AckReceived)time.set(NOW.plusSeconds(31));};
                    assertThrows(IOException.class,()->same.service.prepareFreshRobert(same.invocation()));
                    assertEquals(unresolved==Primitive.NEW_GAME?1:unresolved==Primitive.SELECT_1066_BOOKMARK?2:3,same.submitted.get());assertInstanceOf(ActionState.AckReceived.class,same.last.state());
                    assertEquals(unresolved.operation(),same.last.command().operation());
                    assertEquals(same.last,archive.loadReceipt(archive.preserveReceipt(same.last)));return null;
                }catch(IOException error){throw new IllegalStateException(error);}
            }));
        }
    }
    private static final Instant NOW=Instant.parse("2026-10-24T03:00:00Z");
    private static final String MACHINE="action-writer-software-fixture";
    private static final GameGeneration GAME=new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static final String PYTHON="""
        import ast,hashlib,json,pathlib,runpy,sys
        root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
        expected={
          'ck3_autonomous_player/tests/unit/test_frontend_game_rules_control_contract.py':'48336a205afb0e7886bc4bca0b74e5017413c7d29cc5826de23030d666ee58a1',
          'ck3_autonomous_player/src/xar_autoplayer/bridge/frontend_gui_route_contract.py':'a1c938b59aab6ac1e18889bf874e14708615ec4fc4fb6b4069c58c626e94c2c9',
          'ck3_autonomous_player/src/xar_autoplayer/bridge/frontend_game_rules_contract.py':'4480efed4a1a660362796e9d8909e31040957e8465b6766fba75fa3d199cb8d5',
          'ck3_autonomous_player/src/xar_autoplayer/bridge/frontend_game_rules_control_contract.py':'d1f47238c98c91280fb9f8bfca58e75d637981d0358b41f9ea3900bbedd98533'}
        for name,sha in expected.items():
          if hashlib.sha256((root/name).read_bytes()).hexdigest()!=sha:raise RuntimeError('original frontend oracle drift: '+name)
        source=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_frontend_game_rules_control_contract.py'))
        gui=runpy.run_path(str(root/'ck3_autonomous_player/src/xar_autoplayer/bridge/frontend_gui_route_contract.py'))
        h=source['driver_harness']();selected=h.select_frontend_game_rule_v1('zg361_enabled','zg361_on','zg361_off')
        closed=h.apply_and_hide_frontend_game_rules_v1()
        mcp=root/'ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py'
        declarations=[{'name':n.name,'line':n.lineno,'end_line':n.end_lineno} for n in ast.walk(ast.parse(mcp.read_text(encoding='utf-8-sig'))) if isinstance(n,ast.FunctionDef) and n.name.startswith('ck3_')]
        protocol={'step':gui['ACTIVATE_FRONTEND_SELECT_SUPPORTED_1066_CHARACTER_V1_STEP'],'capability':gui['ACTIVATE_FRONTEND_SELECT_SUPPORTED_1066_CHARACTER_V1_CAPABILITY']}
        print(json.dumps({'before':source['values'](),'window':source['window'](),'selected':selected,'closed':closed,'declarations':declarations,'selected_protocol':protocol},separators=(',',':')))
        """;

    @Test void actual1066ProtocolFeedsExecutorEffectsAllInstalledConsumersAndPhysicalReplay()throws Exception {
        ObjectNode original=original();String step=original.path("selected_protocol").path("step").textValue(),capability=original.path("selected_protocol").path("capability").textValue();
        assertEquals("select-frontend-supported-1066-character-v1",step);assertEquals("game.command.activate-frontend-select-supported-1066-character-v1",capability);
        assertEquals(step,Primitive.SELECT_1066.operation().value());assertEquals(capability,Primitive.SELECT_1066.capability());
        assertEquals(Primitive.SELECT_1066,FrontendRulesEffects.primitive(new OperationKey(step)));
        OperationKey oldWrongStep=new OperationKey("activate-frontend-select-supported-1066-character-v1");
        assertThrows(IllegalArgumentException.class,()->FrontendRulesEffects.primitive(oldWrongStep));
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("1066-protocol"),false)) {
            fixture.writer.locked(borrowed->fixture.archive.inSession(borrowed,archive->{
                try {
                    Software same=new Software(fixture,borrowed,archive,original);var call=same.invocation();
                    var selected=assertInstanceOf(FrontendRulesExecutor.Submitted.class,call.executor().selectSupported1066Character(call.initial(),"bookmark_rags_to_riches_duke_robert"));
                    var receipt=selected.receipt();assertEquals(new OperationKey(step),receipt.command().operation());assertEquals(1,same.submitted.get());
                    var settled=assertInstanceOf(ActionState.Settled.class,receipt.state());assertInstanceOf(ActionState.FrontendApplied.class,settled.settlement());
                    NativeRequest prepared=settled.attempt().preparedRequest();assertEquals(step,prepared.step());assertEquals(Optional.of(capability),prepared.requiredCapability());assertEquals(StrictJson.object(),FrontendRulesCodec.object(prepared.additionalFields()));
                    assertEquals(Primitive.SELECT_1066.emptyRequest(),prepared);ExactRef requestRef=archive.preserveRequest(prepared);assertEquals(prepared,archive.loadRequest(requestRef));
                    var action=same.installed.actions().stream().filter(v->v.effect().operation().equals(receipt.command().operation())).findFirst().orElseThrow();assertEquals(Optional.of(capability),action.requiredCapability());
                    assertEquals(prepared,action.effect().preparation().prepare(receipt.command()));
                    assertEquals(1,same.installed.routeAdmissions().stream().filter(v->v.operation().equals(receipt.command().operation())).count());
                    assertTrue(same.installed.actions().stream().noneMatch(v->v.effect().operation().equals(oldWrongStep)));assertTrue(same.installed.archivedVerifiers().stream().noneMatch(v->v.operation().equals(oldWrongStep)));assertTrue(same.installed.routeAdmissions().stream().noneMatch(v->v.operation().equals(oldWrongStep)));
                    ExactRef retained=archive.preserveReceipt(receipt);var replayed=archive.loadReceipt(retained);assertEquals(receipt,replayed);
                    same.installed.archivedVerifiers().stream().filter(v->v.operation().equals(receipt.command().operation())).findFirst().orElseThrow().verifier().verify(borrowed.head(),replayed,archive);
                    var wrongAck=ack(settled.attempt().requestId(),StrictJson.object().put("step",oldWrongStep.value()).put("accepted",true).put("status","acknowledged_verification_pending"));
                    assertThrows(IllegalArgumentException.class,()->same.installed.effects().observe(receipt.command(),settled.attempt(),wrongAck));
                    var again=same.invocation();assertInstanceOf(FrontendRulesExecutor.AlreadyObserved.class,again.executor().selectSupported1066Character(again.initial(),"bookmark_rags_to_riches_duke_robert"));assertEquals(1,same.submitted.get());return null;
                }catch(IOException error){throw new IllegalStateException(error);}
            }));
        }
    }

    @Test void actualProducerExecutorEffectsArchiveAndAllPublicConsumersAgree()throws Exception {
        ObjectNode original=original();
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("producer"),false)) {
            fixture.writer.locked(borrowed->fixture.archive.inSession(borrowed,archive->{
                try {
                    Software same=new Software(fixture,borrowed,archive,original);
                    var request=(Select)FrontendRulesCodec.decode(Method.SELECT_RULE,arguments("{\"rule_key\":\"zg361_enabled\",\"expected_current_setting_key\":\"zg361_on\",\"desired_setting_key\":\"zg361_off\"}"));
                    Response produced=same.service.execute(request,same.invocation());Selected selected=assertInstanceOf(Selected.class,produced);
                    assertEquals(1,same.submitted.get());ObjectNode expected=(ObjectNode)original.get("selected").deepCopy();canonicalBinding(expected,"before");canonicalBinding(expected,"observation");
                    ObjectNode actual=FrontendRulesCodec.object(FrontendRulesCodec.encode(selected));
                    // Query counters belong to each actual coordinator; compare each independently to its own original receipt.
                    ((ObjectNode)expected.get("before")).put("query_sequence",selected.before().actual().value().querySequence().toString());
                    ((ObjectNode)expected.get("observation")).put("query_sequence",selected.observation().actual().value().querySequence().toString());
                    assertEquals(expected,actual);assertFalse(actual.path("applied_settings_proven").booleanValue());
                    ExactRef retained=archive.preserveReceipt(selected.action());assertEquals(selected.action(),archive.loadReceipt(retained));
                    var verifier=same.installed.archivedVerifiers().stream().filter(v->v.operation().equals(selected.action().command().operation())).findFirst().orElseThrow();
                    verifier.verifier().verify(borrowed.head(),archive.loadReceipt(retained),archive);
                    assertEquals(selected.observation().receipt(),archive.loadRead(selected.observation().actual().originalReceipt()));
                    PublicBindings registry=new PublicBindings();var bindings=RootFrontendRulesPublicProducts.register(registry,ignored->produced,same.sourceRef);registry.freeze(methods());
                    var binding=bindings.stream().filter(v->v.info().method()==PublicMethod.SELECT_FRONTEND_GAME_RULE_V1).findFirst().orElseThrow();
                    assertEquals(actual,FrontendRulesCodec.object(binding.invoke(new PublicBindings.Value(FrontendRulesCodec.encodeRequest(request)))));
                    assertEquals(request,FrontendRulesCodec.decode(Method.SELECT_RULE,new PublicBindings.Value(FrontendRulesCodec.encodeRequest(request))));
                    assertTrue(registry.lookup(PublicMethod.SUBMIT_FRONTEND_FIXTURE_ROBERT_START_V1).isEmpty());assertTrue(registry.lookup(PublicMethod.SUBMIT_FRONTEND_FIXTURE_SCENARIO_START_V1).isEmpty());
                    return null;
                }catch(IOException|InterruptedException error){throw new IllegalStateException(error);}
            }));
        }
    }
    @Test void actualSdkDescriptorsResolveExactlyFifteenOriginalMethodsAndTheRealCodec()throws Exception {
        var descriptors=RootOriginalPublicTestInputs.tools();var selected=descriptors.stream().filter(d->java.util.Arrays.stream(Method.values()).anyMatch(m->m.publicName().equals(d.name()))).toList();
        assertEquals(15,selected.size(),"mandatory original SDK capture must contain every original frontend method");
        ObjectNode original=original();try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("sdk"),false)) {
            fixture.writer.locked(borrowed->fixture.archive.inSession(borrowed,archive->{
                try {
                    Software same=new Software(fixture,borrowed,archive,original);PublicBindings registry=new PublicBindings();
                    var bindings=RootFrontendRulesPublicProducts.register(registry,request->{try{return same.service.execute(request,same.invocation());}catch(IOException error){throw new java.io.UncheckedIOException(error);}},same.sourceRef);registry.freeze(methods());
                    Path originalSource=Path.of(System.getProperty("xar.repository.root")).resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py").toAbsolutePath().normalize();byte[] originalBytes=Files.readAllBytes(originalSource);var originalPin=new ExactRef(originalSource.toString(),originalBytes.length,ActionCodec.sha256(originalBytes));
                    var declarations=selected.stream().map(d->{JsonNode declaration=null;for(JsonNode row:original.get("declarations"))if(d.name().equals(row.path("name").textValue())) {assertNull(declaration,"ambiguous original MCP declaration");declaration=row;}assertNotNull(declaration,"actual original MCP AST declaration required");return new McpCoverage.Declaration(d.name(),originalPin,declaration.path("line").intValue(),declaration.path("end_line").intValue(),"original server.tool frontend declaration",List.of());}).toList();
                    var decisions=selected.stream().map(d->new McpCoverage.Decision(d.name(),McpCoverage.Admission.ADMITTED,same.sourceRef,"controlled same native producer; software scope only")).toList();
                    PublicMcpBindings destination=new PublicMcpBindings(new McpCoverage.Catalog(declarations),decisions);
                    for(var descriptor:selected) {
                        var expected=PublicMcpNativeAdapter.expectedServiceMethod(descriptor.name());assertEquals(expected,RootFrontendRulesPublicProducts.publicMethod(java.util.Arrays.stream(Method.values()).filter(m->m.publicName().equals(descriptor.name())).findFirst().orElseThrow()));
                        PublicMcpNativeAdapter.register(destination,descriptor,bindings.stream().filter(v->v.info().method()==expected).findFirst().orElseThrow());
                    }
                    var directory=destination.freezeSoftwareScope();assertEquals(15,registry.coverage().installed().size());
                    var call=new PublicMcpDirectory.ToolCall(Method.SELECTIONS.publicName(),new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,Optional.of(raw("{}"))),Optional.empty(),new McpCancellation());
                    assertNotNull(directory.invoke(call));assertEquals(0,same.submitted.get());return null;
                }catch(Exception error){throw new IllegalStateException(error);}
            }));
        }
    }
    @Test void originalArgumentProfilesRejectMissingNullBoolFloatExtraAndUnsafeNumbers() {
        for(Method method:Method.values()) {
            if(method.emptyArguments()) {
                assertEquals(new Empty(method),FrontendRulesCodec.decode(method,new PublicBindings.Missing()));
                assertEquals(new Empty(method),FrontendRulesCodec.decode(method,arguments("{}")));
            }else assertThrows(IllegalArgumentException.class,()->FrontendRulesCodec.decode(method,new PublicBindings.Missing()));
            assertThrows(IllegalArgumentException.class,()->FrontendRulesCodec.decode(method,new PublicBindings.Null()));
            assertThrows(IllegalArgumentException.class,()->FrontendRulesCodec.decode(method,arguments("{\"unexpected\":true}")));
        }
        for(String token:List.of("true","1.0","null","-1","9007199254740992","\"01\"","\"18446744073709551616\""))assertThrows(IllegalArgumentException.class,()->FrontendRulesCodec.decode(Method.LOADED_FEATURES,arguments("{\"expected_revision\":"+token+"}")));
        var maximum=(Features)FrontendRulesCodec.decode(Method.LOADED_FEATURES,arguments("{\"expected_revision\":\"18446744073709551615\"}"));assertEquals(PublicUnsigned64.MAXIMUM,maximum.expectedRevision());
        assertEquals(maximum,FrontendRulesCodec.decode(Method.LOADED_FEATURES,new PublicBindings.Value(FrontendRulesCodec.encodeRequest(maximum))));
        for(String key:List.of("","bad-key","../rule"))assertThrows(IllegalArgumentException.class,()->new Select(new ScriptKey(key),new ScriptKey("on"),new ScriptKey("off")));
        assertThrows(IllegalArgumentException.class,()->FrontendRulesCodec.decode(Method.START_1066,arguments("{\"character_name_key\":\"unqualified_character\"}")));
        assertThrows(IllegalArgumentException.class,()->FrontendRulesCodec.decode(Method.ROUTE,arguments("{\"x\":0,\"x\":1}")));
    }
    @Test void actualNativeUnavailableReadRetainsUnknownAndWrongTypedProjectionFails()throws Exception {
        ObjectNode original=original();try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("unavailable"),false)) {
            fixture.writer.locked(borrowed->fixture.archive.inSession(borrowed,archive->{
                try {
                    Software same=new Software(fixture,borrowed,archive,original);ObjectNode unavailable=(ObjectNode)original.get("before").deepCopy();unavailable.put("ready",false);unavailable.put("selection_count",0);unavailable.put("unavailable_reason","bookmarks_route_unavailable");unavailable.putArray("selections");
                    var receipt=same.read(same.definitions.selections(),unavailable);var known=new PlanningReadResult.Known<>(same.definitions.selections().decode(receipt),receipt,archive.preserveRead(receipt));
                    var response=new ReadResponse(Method.SELECTIONS,new Selections(known,false));ObjectNode encoded=FrontendRulesCodec.object(FrontendRulesCodec.encode(response));assertFalse(encoded.path("ready").booleanValue());assertEquals(0,encoded.path("selections").size());
                    assertThrows(IllegalArgumentException.class,()->new ReadResponse(Method.APPLIED_RULES,response.observation()));
                    assertThrows(IOException.class,()->same.service.loadedFeatures(new Features(BigInteger.ONE),new PlanningReadResult.Unavailable<>("actual source unavailable",Optional.empty())));
                    return null;
                }catch(IOException error){throw new IllegalStateException(error);}
            }));
        }
    }
    @Test void actualApplyAndHideUsesIndependentClosureAndNeverClaimsAppliedSettings()throws Exception {
        ObjectNode original=original();try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("closure"),false)) {
            fixture.writer.locked(borrowed->fixture.archive.inSession(borrowed,archive->{
                try {
                    Software same=new Software(fixture,borrowed,archive,original);
                    same.service.execute(new Select(new ScriptKey("zg361_enabled"),new ScriptKey("zg361_on"),new ScriptKey("zg361_off")),same.invocation());
                    Closed closed=(Closed)same.service.execute(new Empty(Method.APPLY_HIDE),same.invocation());ObjectNode encoded=FrontendRulesCodec.object(FrontendRulesCodec.encode(closed));
                    assertTrue(encoded.path("window_closed_proven").booleanValue());assertFalse(encoded.path("applied_settings_proven").booleanValue());assertFalse(encoded.path("acknowledgement").path("window_closed_proven").booleanValue());
                    assertEquals(2,same.submitted.get());assertEquals(original.path("closed").path("acknowledgement"),encoded.get("acknowledgement"));
                    var replay=same.installed.archivedVerifiers().stream().filter(v->v.operation().equals(closed.action().command().operation())).findFirst().orElseThrow();replay.verifier().verify(borrowed.head(),archive.loadReceipt(archive.preserveReceipt(closed.action())),archive);
                    ReadResponse window=(ReadResponse)same.service.execute(new Empty(Method.WINDOW),same.invocation());assertTrue(FrontendRulesCodec.object(FrontendRulesCodec.encode(window)).path("window_closed_proven").booleanValue());return null;
                }catch(IOException|InterruptedException error){throw new IllegalStateException(error);}
            }));
        }
    }
    @Test void actualConnectionIdentitySurvivesAboveTwoTo53AndDetachedSourceIsRejected()throws Exception {
        ObjectNode original=original();try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("large-identity"),false)) {
            fixture.writer.locked(borrowed->fixture.archive.inSession(borrowed,archive->{
                try {
                    Software same=new Software(fixture,borrowed,archive,original);same.generation=PublicUnsigned64.MAXIMUM;
                    ReadResponse response=(ReadResponse)same.service.execute(new Empty(Method.SELECTIONS),same.invocation());Selections selected=(Selections)response.observation();
                    ObjectNode encoded=FrontendRulesCodec.object(FrontendRulesCodec.encode(response));assertEquals("18446744073709551615",encoded.path("binding").path("connection_generation").textValue());
                    var actual=selected.actual().value();var detached=new RuleSelections(new Source(new Binding(123,BigInteger.ONE),actual.source().build()),actual.querySequence(),actual.ready(),actual.unavailableReason(),actual.selections(),actual.appliedSettingsProven());
                    var spoofed=new ReadResponse(Method.SELECTIONS,new Selections(new PlanningReadResult.Known<>(detached,selected.receipt(),selected.actual().originalReceipt()),false));assertThrows(IllegalArgumentException.class,()->FrontendRulesCodec.encode(spoofed));
                    assertEquals(selected.receipt(),archive.loadRead(selected.actual().originalReceipt()));return null;
                }catch(IOException|InterruptedException error){throw new IllegalStateException(error);}
            }));
        }
    }
    @Test void publicResponseRejectsAcknowledgementSubstitutionAndOriginalCustodyTampering()throws Exception {
        ObjectNode original=original();try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("custody"),false)) {
            fixture.writer.locked(borrowed->fixture.archive.inSession(borrowed,archive->{
                try {
                    Software same=new Software(fixture,borrowed,archive,original);Selected result=(Selected)same.service.execute(new Select(new ScriptKey("zg361_enabled"),new ScriptKey("zg361_on"),new ScriptKey("zg361_off")),same.invocation());
                    ObjectNode wrong=FrontendRulesCodec.object(result.acknowledgement());wrong.put("native_next_calls",2);
                    var substituted=new Selected(result.action(),result.request(),result.before(),result.windowBefore(),FrontendRulesCodec.raw(wrong),result.observation());assertThrows(IllegalArgumentException.class,()->FrontendRulesCodec.encode(substituted));
                    ExactRef originalRead=result.observation().actual().originalReceipt();Files.writeString(Path.of(originalRead.path()),"tampered",StandardCharsets.UTF_8);
                    assertThrows(RuntimeException.class,()->archive.loadRead(originalRead));assertEquals(1,same.submitted.get());return null;
                }catch(IOException|InterruptedException error){throw new IllegalStateException(error);}
            }));
        }
    }
    @Test void actualPublicPrepareUsesSoleHelperWholeServiceArchiveCodecAndOriginalPythonMethod()throws Exception {
        ObjectNode original=original();try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("prepare-public"),false)) {
            fixture.writer.locked(borrowed->fixture.archive.inSession(borrowed,archive->{
                try {
                    Software same=new Software(fixture,borrowed,archive,original);same.frontend=true;
                    PublicBindings registry=new PublicBindings();AtomicReference<Prepared> produced=new AtomicReference<>();
                    var bindings=RootFrontendRulesPublicProducts.register(registry,request->{
                        try {var result=same.service.execute(request,same.invocation());produced.set((Prepared)result);return result;}
                        catch(IOException error){throw new java.io.UncheckedIOException(error);}
                    },same.sourceRef);registry.freeze(methods());
                    var binding=bindings.stream().filter(v->v.info().method()==RootFrontendRulesPublicProducts.publicMethod(Method.PREPARE_RULER)).findFirst().orElseThrow();
                    RawJson wire=binding.invoke(new PublicBindings.Missing());Prepared result=produced.get();assertNotNull(result);
                    assertEquals(2,same.submitted.get());assertEquals(1,result.selections().size());assertEquals(2,same.frontendActions.size());
                    assertEquals(NOW.plusSeconds(2),result.selections().getFirst().command().deadline());
                    ObjectNode encoded=FrontendRulesCodec.object(wire);assertEquals(encoded,FrontendRulesCodec.object(FrontendRulesCodec.encode(result)));
                    assertEquals(1,encoded.path("selection_attempt_count").intValue());assertEquals(1,encoded.path("selection_acknowledgements").size());
                    assertEquals(originalPrepare(result),encoded,"actual original driver method and full public prepare differ");
                    for(ActionReceipt action:same.frontendActions) {
                        var replay=archive.loadReceipt(archive.preserveReceipt(action));assertEquals(action,replay);
                        same.installed.archivedVerifiers().stream().filter(v->v.operation().equals(action.command().operation())).findFirst().orElseThrow().verifier().verify(borrowed.head(),replay,archive);
                    }
                    assertEquals(result.lobbyInspection().receipt(),archive.loadRead(result.lobbyInspection().actual().originalReceipt()));
                    assertFalse(RootFrontendRulesPublicProducts.definitionGaps().isEmpty(),"positive first draw does not close missing selected/ineligible producer");return null;
                }catch(Exception error){throw new IllegalStateException(error);}
            }));
        }
    }
    @Test void actualServiceUnknownRandomAckStopsWithoutSecondDrawAndPreservesCanonicalReceipt()throws Exception {
        ObjectNode original=original();try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("prepare-unknown"),false)) {
            fixture.writer.locked(borrowed->fixture.archive.inSession(borrowed,archive->{
                try {
                    Software same=new Software(fixture,borrowed,archive,original);same.frontend=true;same.designerReady=false;
                    PublicBindings registry=new PublicBindings();var bindings=RootFrontendRulesPublicProducts.register(registry,request->{
                        try{return same.service.execute(request,same.invocation());}catch(IOException error){throw new java.io.UncheckedIOException(error);}
                    },same.sourceRef);registry.freeze(methods());
                    var binding=bindings.stream().filter(v->v.info().method()==RootFrontendRulesPublicProducts.publicMethod(Method.PREPARE_RULER)).findFirst().orElseThrow();
                    var failure=assertThrows(java.io.UncheckedIOException.class,()->binding.invoke(new PublicBindings.Missing()));
                    var stopped=assertInstanceOf(FrontendCustomRulerPreparation.UnresolvedStop.class,failure.getCause());
                    assertEquals(0,stopped.drawsCompleted());assertEquals(2,same.submitted.get());assertEquals(2,same.frontendActions.size());assertSame(same.last,stopped.action());
                    assertInstanceOf(ActionState.AckReceived.class,stopped.action().state());assertTrue(stopped.action().ack().isPresent());
                    assertEquals(stopped.action(),archive.loadReceipt(archive.preserveReceipt(stopped.action())));
                    assertEquals(Primitive.SELECT_RANDOM.operation(),stopped.action().command().operation());return null;
                }catch(IOException error){throw new IllegalStateException(error);}
            }));
        }
    }
    @Test void actualServiceMissingRandomTargetStopsAfterPickWithoutSubmittingADraw()throws Exception {
        ObjectNode original=original();try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("prepare-no-target"),false)) {
            fixture.writer.locked(borrowed->fixture.archive.inSession(borrowed,archive->{
                try {
                    Software same=new Software(fixture,borrowed,archive,original);same.frontend=true;same.randomTargetAvailable=false;
                    var stopped=assertThrows(FrontendCustomRulerPreparation.UnavailableStop.class,()->same.service.execute(new Empty(Method.PREPARE_RULER),same.invocation()));
                    assertEquals(0,stopped.drawsCompleted());assertEquals(1,same.submitted.get());assertEquals(1,same.frontendActions.size());return null;
                }catch(IOException error){throw new IllegalStateException(error);}
            }));
        }
    }
    private static Set<PublicMethod> methods() { return java.util.Arrays.stream(Method.values()).map(RootFrontendRulesPublicProducts::publicMethod).collect(java.util.stream.Collectors.toSet()); }
    private static void canonicalBinding(ObjectNode root,String field) {ObjectNode row=(ObjectNode)root.get(field);((ObjectNode)row.get("binding")).put("connection_generation","1");row.put("query_sequence",row.get("query_sequence").asText());}
    private static PublicBindings.Arguments arguments(String json) { return new PublicBindings.Value(raw(json)); }
    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }
    private static ObjectNode original()throws Exception {
        String root=System.getProperty("xar.repository.root"),python=System.getProperty("xar.python");assertNotNull(root,"mandatory original workspace; missing input is NOT RUN, never skip");assertNotNull(python,"mandatory actual compatibility interpreter");
        Process process=new ProcessBuilder(python,"-X","utf8","-c",PYTHON,root).redirectErrorStream(true).start();
        try {assertTrue(process.waitFor(30,TimeUnit.SECONDS),"actual original producer timeout");byte[] bytes=process.getInputStream().readNBytes(1_048_577);assertEquals(0,process.exitValue(),new String(bytes,StandardCharsets.UTF_8));return FrontendRulesCodec.object(new RawJson(bytes));}
        finally {if(process.isAlive())process.destroyForcibly();}
    }
    private static NativeActionPort.AckReceived ack(String request,JsonNode result) {
        ObjectNode body=StrictJson.object();body.put("type","command_result");body.put("protocol_version",1);body.put("request_id",request);body.put("ok",true);body.set("result",result);
        byte[] json=StrictJson.canonical(body);byte[] packet=ByteBuffer.allocate(json.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(json.length).put(json).array();return new NativeActionPort.AckReceived(request,true,Optional.of(new RawJson(StrictJson.canonical(result))),new RawJson(json),packet);
    }
    /** Controlled native model inputs; identity is independently checked by the actual existing decoder. */
    private static ObjectNode bookmarkModel(boolean selected) {
        ObjectNode model=StrictJson.object().put("accepted",true).put("status","identity_ready").put("candidate_identity_ready",true).put("selected_bookmark_group_key","bm_group_1066").put("selected_bookmark_key","bm_1066_rags_to_riches").put("selected_date_raw",57400000).put("selected_date_low_raw",57400000).put("supported_1066_candidate_index",0).put("selected_character_index",selected?0:-1).put("supported_1066_government_key","feudal_government").put("supported_1066_feudal",true).put("supported_1066_date_matches",true);
        model.putArray("candidate_keys").add("bookmark_rags_to_riches_duke_robert");return model;
    }
    private static ObjectNode frontendRouteBody(Route route) {
        return StrictJson.object().put("step","query-frontend-gui-route-v1").put("accepted",true).put("status",route.wire()).put("backend_id","native-headless");
    }
    private static ObjectNode frontendTreeBody(boolean available,boolean ready) {
        ObjectNode tree=StrictJson.object().put("step","inspect-frontend-gui-tree-v1").put("accepted",true).put("status",available?"available":"unavailable")
            .put("scope_root_name","lobbyview").put("root_available",available).put("truncated",false).put("backend_id","native-headless");
        var widgets=tree.putArray("widgets");if(available)frontendWidget(widgets.addObject(),"4/0/1/0/1");if(available&&ready)frontendWidget(widgets.addObject(),"3/0/2/3");
        tree.put("widget_count",widgets.size());return tree;
    }
    private static void frontendWidget(ObjectNode widget,String path) {
        widget.put("runtime_name","").put("child_path",path).put("depth",path.split("/").length).put("child_count",0).put("vtable_rva",1).put("effective_visible",true).put("enabled",true);
    }
    /** Execute the exact original driver method AST, not a reimplementation of its orchestration. */
    private static ObjectNode originalPrepare(Prepared result)throws Exception {
        String root=System.getProperty("xar.repository.root"),python=System.getProperty("xar.python");
        assertNotNull(root,"mandatory original workspace");assertNotNull(python,"mandatory independent original interpreter");
        ObjectNode input=StrictJson.object();input.set("before",FrontendRulesCodec.original(result.pickAny().before().receipt()));input.set("after",FrontendRulesCodec.original(result.pickAny().after().receipt()));
        input.set("target",FrontendRulesCodec.original(result.selectionTarget().receipt()));input.set("lobby",FrontendRulesCodec.original(result.lobbyInspection().receipt()));
        input.set("pick",FrontendRulesCodec.object(result.pickAny().acknowledgement()));input.set("draw",FrontendRulesCodec.object(result.selectionAcknowledgements().getFirst()));
        String script="""
            import ast,hashlib,json,pathlib,sys
            sys.dont_write_bytecode=True
            root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            source=root/'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py'
            if hashlib.sha256(source.read_bytes()).hexdigest()!='eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603':raise RuntimeError('actual original driver drift')
            contract=root/'ck3_autonomous_player/src/xar_autoplayer/bridge/frontend_gui_route_contract.py'
            if hashlib.sha256(contract.read_bytes()).hexdigest()!='a1c938b59aab6ac1e18889bf874e14708615ec4fc4fb6b4069c58c626e94c2c9':raise RuntimeError('actual original normalizer drift')
            import xar_autoplayer.bridge.frontend_gui_route_contract as g
            from xar_autoplayer.bridge.driver import BridgeUnavailableError
            parsed=ast.parse(source.read_text(encoding='utf-8-sig'))
            found=[n for n in ast.walk(parsed) if isinstance(n,ast.FunctionDef) and n.name=='activate_frontend_prepare_custom_ruler_v1']
            if len(found)!=1:raise RuntimeError('original method missing or ambiguous')
            node=found[0];ns=dict(vars(g));ns['BridgeUnavailableError']=BridgeUnavailableError
            exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),ns)
            value=json.load(sys.stdin);calls=[]
            class Harness:
                def query_frontend_gui_route_v1(self):
                    calls.append('before');return g.normalize_frontend_gui_route_v1(value['before'])
                def _execute_primitive_step(self,step,**kwargs):
                    if kwargs!={'expected_revision':0,'required_capability':g.ACTIVATE_FRONTEND_PICK_ANY_CHARACTER_V1_CAPABILITY if step==g.ACTIVATE_FRONTEND_PICK_ANY_CHARACTER_V1_STEP else g.ACTIVATE_FRONTEND_SELECT_RANDOM_PLAYABLE_V1_CAPABILITY,'allow_frontend_revision_zero':True}:raise RuntimeError('original primitive arguments changed')
                    if step==g.ACTIVATE_FRONTEND_PICK_ANY_CHARACTER_V1_STEP:calls.append('pick');return value['pick']
                    if step!=g.ACTIVATE_FRONTEND_SELECT_RANDOM_PLAYABLE_V1_STEP:raise RuntimeError('unexpected primitive')
                    calls.append('draw');return value['draw']
                def _wait_for_frontend_gui_route_v1(self,route):
                    if route!='lobby':raise RuntimeError('unexpected route')
                    calls.append('after');return g.normalize_frontend_gui_route_v1(value['after'])
                def _wait_for_frontend_gui_tree_v1(self,predicate,description,**kwargs):
                    designer=predicate is g.frontend_lobby_default_ruler_designer_ready_v1
                    if kwargs!=({'timeout_seconds':2.0} if designer else {}):raise RuntimeError('original observation timeout changed')
                    calls.append('designer' if designer else 'target');tree=g.normalize_frontend_gui_tree_inspection_v1(value['lobby' if designer else 'target'])
                    if not predicate(tree):raise RuntimeError('actual controlled positive observation does not satisfy original predicate')
                    return tree
            result=ns['activate_frontend_prepare_custom_ruler_v1'](Harness())
            if calls!=['before','pick','after','target','draw','designer']:raise RuntimeError('actual original first-draw sequence changed')
            print(json.dumps(result,separators=(',',':')))
            """;
        ProcessBuilder builder=new ProcessBuilder(python,"-B","-X","utf8","-c",script,root).directory(Path.of(root).toFile()).redirectErrorStream(true);
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1");Process child=builder.start();
        try {
            var output=CompletableFuture.supplyAsync(()->{try{return child.getInputStream().readNBytes(1_048_577);}catch(IOException error){throw new java.io.UncheckedIOException(error);}});
            try(var stdin=child.getOutputStream()){stdin.write(StrictJson.canonical(input));}
            assertTrue(child.waitFor(30,TimeUnit.SECONDS),"actual original method timeout");byte[] bytes=output.get(5,TimeUnit.SECONDS);
            assertEquals(0,child.exitValue(),new String(bytes,StandardCharsets.UTF_8));assertTrue(bytes.length<=1_048_576);
            return FrontendRulesCodec.object(new RawJson(bytes));
        }finally {if(child.isAlive())child.destroyForcibly();}
    }
    private static final class Software {
        final ActionWriterIntegrationFixture fixture;final ContinuityStorePort.Session borrowed;final ActionPorts.OutcomeArchive archive;final ExactRef sourceRef;final G2Source source;final FrontendRulesDefinitions definitions;final FrontendRulesInstaller installed;final FrontendRulesService service;
        final ObjectNode original;final AtomicInteger submitted=new AtomicInteger();int sequence=1;boolean selected;boolean closed;boolean bookmarkSelected;BigInteger generation=BigInteger.ONE;ActionReceipt last;
        boolean frontend,randomSelected,designerReady=true,randomTargetAvailable=true;Route frontendRoute=Route.BOOKMARKS;
        boolean freshRobert,bookmark1066Selected,unconfirmedFreshNewGame,unconfirmedFreshBookmark,unconfirmedFreshSelection;int freshModelReads;
        Clock invocationClock=Clock.fixed(NOW,ZoneOffset.UTC);Runnable afterFreshDispatch=()->{};
        final List<ActionReceipt> frontendActions=new ArrayList<>();
        Software(ActionWriterIntegrationFixture fixture,ContinuityStorePort.Session borrowed,ActionPorts.OutcomeArchive archive,ObjectNode original)throws IOException {
            this(fixture,borrowed,archive,original,Build.CK3_12003);
        }
        Software(ActionWriterIntegrationFixture fixture,ContinuityStorePort.Session borrowed,ActionPorts.OutcomeArchive archive,ObjectNode original,Build build)throws IOException {
            this.fixture=fixture;this.borrowed=borrowed;this.archive=archive;this.original=original;
            Path sourceFile=fixture.root.resolve("reviewed-fixture-source.txt");byte[] bytes=Files.readAllBytes(sourceFile);sourceRef=new ExactRef(sourceFile.toString(),bytes.length,ActionCodec.sha256(bytes));source=new G2Source(MACHINE,NOW.toString(),build.version(),sourceRef);definitions=new FrontendRulesDefinitions(build,sourceRef);
            installed=new FrontendRulesInstaller(definitions,reads,archive,sourceRef,sourceRef);service=new FrontendRulesService(definitions,archive);
        }
        final PlanningReadPort reads=new PlanningReadPort() {
            @Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) {
                try {JsonNode value;
                    if(freshRobert) {
                        value=contract==definitions.route()?frontendRouteBody(frontendRoute):bookmarkModel(bookmarkSelected);
                        if(contract==definitions.bookmark()) {
                            freshModelReads++;ObjectNode model=(ObjectNode)value;
                            if(bookmark1066Selected)model.put("selected_date_raw",53144328).put("selected_date_low_raw",53144328);
                            else {model.put("status","unavailable").put("candidate_identity_ready",false).put("selected_bookmark_group_key","bm_group_867").put("selected_bookmark_key","bm_867_adventurers").put("selected_date_raw",51394920).put("selected_date_low_raw",51394920).put("supported_1066_candidate_index",-1).put("selected_character_index",-1).put("supported_1066_feudal",false).put("supported_1066_date_matches",false);model.putNull("supported_1066_government_key");model.putArray("candidate_keys").add("bookmark_adventurers_rurik_rurikid");}
                        }
                    }
                    else value=frontend?(contract==definitions.route()?frontendRouteBody(frontendRoute):frontendTreeBody(randomTargetAvailable,randomSelected&&designerReady)):contract==definitions.bookmark()?bookmarkModel(bookmarkSelected):contract==definitions.window()?(closed?original.get("closed").get("window_observation"):original.get("window")):selected?original.get("selected").get("observation"):original.get("before");
                    PlanningReadReceipt receipt=Software.this.read(contract,value);return new PlanningReadResult.Known<>(contract.decode(receipt),receipt,archive.preserveRead(receipt));}
                catch(IOException error){throw new IllegalStateException(error);}
            }
        };
        final ActionCoordinatorPort actions=new ActionCoordinatorPort() {
            @Override public ActionReceipt execute(ActionCommand command) {
                submitted.incrementAndGet();var prepared=installed.effects().prepare(command);var attempt=new ActionState.Attempt("software-native-action-"+sequence,NOW,guard(command.origin().requireFrontend(),command.operation()),prepared);
                if(frontend) {
                    if(freshRobert) {
                        if(command.operation().equals(Primitive.NEW_GAME.operation())) {if(!unconfirmedFreshNewGame)frontendRoute=Route.BOOKMARKS;}
                        else if(command.operation().equals(Primitive.SELECT_1066_BOOKMARK.operation())) {if(!unconfirmedFreshBookmark)bookmark1066Selected=true;}
                        else {assertEquals(Primitive.SELECT_1066.operation(),command.operation());assertTrue(bookmark1066Selected);if(!unconfirmedFreshSelection)bookmarkSelected=true;}
                    }else if(command.operation().equals(Primitive.PICK_ANY.operation()))frontendRoute=Route.LOBBY;else {assertEquals(Primitive.SELECT_RANDOM.operation(),command.operation());randomSelected=true;}
                    var dispatch=ack(attempt.requestId(),StrictJson.object().put("step",command.operation().value()).put("accepted",true).put("status","acknowledged_verification_pending").put("backend_id","native-headless"));
                    archive.preserve(dispatch);ActionState state;
                    try {var observed=installed.effects().observe(command,attempt,dispatch);state=new ActionState.Settled(attempt,dispatch,new ActionState.FrontendApplied(((ActionPorts.FrontendObserved)observed.result()).observation()));}
                    catch(IllegalArgumentException missingIndependentDesigner) {state=new ActionState.AckReceived(attempt,dispatch);}
                    last=new ActionReceipt(1,submitted.get(),command,ActionCodec.bodySha256(command),state);archive.preserveReceipt(last);frontendActions.add(last);if(freshRobert)afterFreshDispatch.run();return last;
                }
                JsonNode nativeResult;if(command.operation().equals(Primitive.SELECT_1066.operation())){bookmarkSelected=true;nativeResult=StrictJson.object().put("step",command.operation().value()).put("accepted",true).put("status","acknowledged_verification_pending");}else if(command.operation().value().equals("select-frontend-game-rule-v1")){selected=true;nativeResult=original.get("selected").get("acknowledgement");}else {closed=true;nativeResult=original.get("closed").get("acknowledgement");}
                var dispatch=ack(attempt.requestId(),nativeResult);archive.preserve(dispatch);var projected=installed.effects().observe(command,attempt,dispatch);var actual=((ActionPorts.FrontendObserved)projected.result()).observation();
                last=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Settled(attempt,dispatch,new ActionState.FrontendApplied(actual)));archive.preserveReceipt(last);return last;
            }
            @Override public ActionReceipt reconcile(String actionId) {assertEquals(last.command().actionId(),actionId);return last;}
        };
        FrontendRulesService.Invocation invocation()throws IOException {var context=new FrontendRulesExecutor.Context("software-public",identity(),source,NOW.plusSeconds(30));return new FrontendRulesService.Invocation(new FrontendRulesExecutor(installed,reads,actions,archive),actions,context,(actual,key)->{throw new AssertionError("selection fixture cannot start a Game");},invocationClock);}
        <T>PlanningReadReceipt read(ReadContract<T> contract,JsonNode result)throws IOException {
            FrontendIdentity identity=identity();var evidence=guard(identity,contract.operation());var permission=new PlanningReadGuard(evidence,FrontendGuardBinding.digest(identity));var request=new PlanningReadRequest(new CommandOrigin.Frontend(identity),source,identity.frontendSessionId(),contract.operation(),new OpportunityJson.Obj(Map.of()),NOW.plusSeconds(30));
            var receipt=new PlanningReadReceipt(request,contract.contractId(),"software-read-"+sequence,permission,permission,ack("software-read-"+sequence,result));archive.preserveRead(receipt);return receipt;
        }
        FrontendIdentity identity()throws IOException {int current=++sequence;ObjectNode route=StrictJson.object().put("route","bookmarks").put("fixture_sequence",current);ExactRef packet=fixture.archive.preserveArtifact(borrowed,ack("software-route-"+current,route).originalPacket(),4096);ExactRef hello=fixture.archive.preserveArtifact(borrowed,ack("software-hello",StrictJson.object().put("fixture_notice","hello")).originalPacket(),4096);return new FrontendIdentity(MACHINE,GAME,"frontend-test",generation,123,new FrontendFrame.Menu(BigInteger.valueOf(current)),packet,hello);}
        GuardEvidence guard(FrontendIdentity identity,OperationKey operation) {return new GuardEvidence(new CommandOrigin.Frontend(identity),source,identity.frontendSessionId(),identity.connectionGeneration(),operation,identity.nativeEvidence(),identity.capabilityEvidence(),"controlled-frontend-public-software",NOW,NOW.plusSeconds(60));}
    }
}
