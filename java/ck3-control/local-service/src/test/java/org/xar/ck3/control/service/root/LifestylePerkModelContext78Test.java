package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.lang.reflect.Field;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.http.HttpClient;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryDecisionSelector;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanTrace;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.application.planning.PlanningStage;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExternalFact;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExternalState;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.UnknownScope;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

import org.xar.ck3.control.application.driver.DriverJson;
import java.io.ByteArrayOutputStream;
import java.io.OutputStream;
import java.io.PrintStream;
import java.math.BigInteger;
import java.util.Base64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernanceActionPreparation;

/** B66 is a READONLY plan clue. These newly constructed public DATA commands are not the failed Runtime command. */
final class LifestylePerkModelContext78Test {
    private static final int MATERIAL=16*1024*1024,WIRE_BOUND=262144;
    private static final String SHA="164d73c437179a81f0cc211a6b7b97535325e4ed358b59a05cdefbc0e6ac0c21";
    private static final Path FIXTURE=Path.of(System.getProperty("lifestyle78.fixture",
            "src/test/resources/org/xar/ck3/control/service/root/lifestyle-perk-b66-readonly.json"));
    @Test @Timeout(45) void boundedPerkRetainsTheFullCurrentInputAndOnlyTheExactProposalEcho(@TempDir Path root) throws Exception {
        Fixture f=fixture(true);byte[] command=ActionCodec.encodeCommand(f.command());
        byte[] snapshot=OpportunityJson.encode(f.request().observations().snapshot()),history=historyBytes(f.request());
        assertTrue(history.length>1048576);
        assertDoesNotThrow(()->GovernanceActionPreparation.lifestyleFields(f.command()));
        try(Stub model=new Stub();Client client=client(model,root,f)) {
            model.reply.set(reply(f.command()));var result=client.selector.select(f.request(),f.selected());
            assertEquals(OrdinaryDecisionSelector.Choice.ACCEPT,result.choice(),result.reason());assertEquals(1,model.calls.get());
            byte[] wire=model.requests.getFirst();assertTrue(wire.length<=WIRE_BOUND);JsonNode data=userData(tree(wire));
            assertEquals("xar.model-lifestyle-perk-admission/v1",data.path("decision_context_schema").textValue());
            assertEquals("lifestyle_perk_admission/v1",data.path("decision_scope").textValue());
            assertTrue(data.path("projection_scope").textValue().contains("not lossless"));
            assertEquals(tree(command),data.get("proposal"));assertEquals(tree(snapshot),data.get("snapshot"));
            assertEquals(f.command().actionId(),data.path("proposal_id").textValue());
            assertEquals(ActionCodec.bodySha256(f.command()),data.path("body_sha256").textValue());
            assertEquals(f.request().deadline().toString(),data.path("planning_deadline").textValue());
            assertEquals(expectedFacts(f.request()),data.get("action_facts"));
            assertEquals(strings(f.request().observations().bridgeCapabilities().stream().sorted().toList()),data.get("capabilities"));
            assertEquals(strings(f.request().observations().actionSteps().stream().map(Object::toString).sorted().toList()),data.get("routable_operations"));
            assertFalse(data.has("history"));assertFalse(data.has("root_facts"));
            assertFalse(new String(wire,StandardCharsets.UTF_8).contains("irrelevant-history-marker-"));
            ExactRef full=ExactRef.fromJson(data.get("original_model_input"));assertTrue(client.materials.containsKey(full));
            JsonNode original=userData(tree(client.materials.get(full)));
            assertEquals(tree(history),original.get("history"));assertEquals(tree(snapshot),original.get("snapshot"));
            assertEquals(tree(command),original.get("proposal"));assertEquals(expectedFacts(f.request()),original.get("action_facts"));
            assertMaterials(client);assertTrue(result.evidence().isPresent());
            assertArrayEquals(command,ActionCodec.encodeCommand(f.command()));
            assertArrayEquals(snapshot,OpportunityJson.encode(f.request().observations().snapshot()));
            assertArrayEquals(history,historyBytes(f.request()));
            Fixture small=fixture(false);
            for(String fault:List.of("id","sha","extra","alternative")) {
                ObjectNode bad=reply(small.command());
                switch(fault) {
                    case "id"->bad.put("proposal_id","another-proposal");case "sha"->bad.put("body_sha256","0".repeat(64));
                    case "extra"->bad.putObject("arguments").put("target_key","different-perk");
                    case "alternative"->bad.put("decision","SELECT_ALTERNATIVE");default->throw new AssertionError(fault);
                }
                model.reply.set(bad);var waiting=client.selector.select(small.request(),small.selected());
                assertEquals(OrdinaryDecisionSelector.Choice.WAIT,waiting.choice());assertTrue(waiting.reason().startsWith("model_invalid_selection:"));
            }
            assertEquals(5,model.calls.get());model.assertHealthy();
        }
        assertFixtureUnchanged();
    }

    @Test @Timeout(45) void UnsupportedOrOversizedPerkWaitsWithoutHttpAndOtherOperationsKeepTheLegacyRoute(@TempDir Path root) throws Exception {
        Fixture f=fixture(false);
        try(Stub model=new Stub();Client client=client(model,root,f)) {
            model.reply.set(reply(f.command()));
            PlanningRequest oversized=withSnapshot(f,f.request().observations().snapshot().with("large_current_unknown",
                    new OpportunityJson.Text("retained-current-unknown:"+"x".repeat(WIRE_BOUND))));
            var bound=client.selector.select(oversized,f.selected());assertEquals(OrdinaryDecisionSelector.Choice.WAIT,bound.choice());
            assertEquals("model_lifestyle_perk_input_bound_exceeded",bound.reason());assertEquals(0,model.calls.get());
            for(var unsupported:List.of(selected(f.request(),f.command(),"unsupported_future_perk_phase",OrdinaryPolicy.Kind.ORDINARY),
                    selected(f.request(),f.command(),"lifestyle_min_perk_action",OrdinaryPolicy.Kind.FOREGROUND))) {
                var waiting=client.selector.select(f.request(),unsupported);assertEquals(OrdinaryDecisionSelector.Choice.WAIT,waiting.choice());
                assertEquals(0,model.calls.get(),"matching unsupported PERK must not fall back to the full prompt");
            }
            ActionCommand old=f.command();ActionCommand invalid=new ActionCommand(old.actionId(),old.origin(),old.source(),old.sessionId(),old.operation(),
                    old.arguments().with("target_key",new OpportunityJson.Text("not-an-advertised-original-perk")),old.expectation(),old.claims(),old.deadline());
            var invalidResult=client.selector.select(f.request(),selected(f.request(),invalid,"lifestyle_min_perk_action",OrdinaryPolicy.Kind.ORDINARY));
            assertEquals(OrdinaryDecisionSelector.Choice.WAIT,invalidResult.choice());assertEquals(0,model.calls.get());
            ActionCommand other=new ActionCommand(old.actionId()+"-other-role",old.origin(),old.source(),old.sessionId(),
                    new OperationKey("query-campaign-root-context-v1"),old.arguments(),old.expectation(),old.claims(),old.deadline());
            model.reply.set(reply(other));var legacy=client.selector.select(f.request(),selected(f.request(),other,"ordinary-public-query",OrdinaryPolicy.Kind.ORDINARY));
            assertEquals(OrdinaryDecisionSelector.Choice.ACCEPT,legacy.choice(),legacy.reason());assertEquals(1,model.calls.get());
            JsonNode original=userData(tree(model.requests.getFirst()));assertEquals(tree(historyBytes(f.request())),original.get("history"));
            assertEquals(tree(ActionCodec.encodeCommand(other)),original.get("proposal"));assertFalse(original.has("decision_context_schema"));
            model.assertHealthy();
        }
        assertFixtureUnchanged();
    }

    @Test @Timeout(45) void Http400HasOneEndAndAReadableArchivedIndexOnlyAfterSuccessfulPreservation(@TempDir Path root) throws Exception {
        Fixture f=fixture(false);byte[] error="{\"error\":{\"message\":\"controlled-local-400-body-not-a-provider-root-cause\",\"type\":\"BadRequestError\"}}".getBytes(StandardCharsets.UTF_8);
        try(Stub model=new Stub();Client client=client(model,root.resolve("preserved"),f);Progress output=new Progress()) {
            model.status=400;model.error=error;var result=client.selector.select(f.request(),f.selected());
            assertEquals(OrdinaryDecisionSelector.Choice.WAIT,result.choice());assertEquals(1,model.calls.get());assertTrue(result.evidence().isPresent());
            List<JsonNode> events=output.events();assertEquals(1,count(events,"ORDINARY_MODEL_HTTP_BEGIN"));
            assertEquals(1,count(events,"ORDINARY_MODEL_HTTP_END"));assertEquals(1,count(events,"ORDINARY_MODEL_HTTP_ARCHIVED"));
            JsonNode index=events.stream().filter(e->e.path("status").asText().equals("ORDINARY_MODEL_HTTP_ARCHIVED")).findFirst().orElseThrow();
            ExactRef request=ExactRef.fromJson(index.get("request_ref")),attempt=ExactRef.fromJson(index.get("attempt_ref"));
            assertTrue(client.materials.containsKey(request));assertTrue(client.materials.containsKey(attempt));
            assertArrayEquals(model.requests.getFirst(),client.materials.get(request));
            JsonNode recorded=tree(client.materials.get(attempt));assertEquals(400,recorded.path("status").intValue());
            assertArrayEquals(error,Base64.getDecoder().decode(recorded.path("wire_base64").textValue()));
            JsonNode decision=tree(client.materials.get(result.evidence().orElseThrow()));
            assertEquals(request,ExactRef.fromJson(decision.get("request")));assertEquals(attempt,ExactRef.fromJson(decision.path("attempts").get(0)));
            assertFalse(output.text().contains("controlled-local-400-body"));assertMaterials(client);model.assertHealthy();
        }
        try(Stub model=new Stub();Client client=client(model,root.resolve("not-preserved"),f);Progress output=new Progress()) {
            model.status=400;model.error=error;client.failAttempt=true;
            var result=client.selector.select(f.request(),f.selected());assertEquals(OrdinaryDecisionSelector.Choice.WAIT,result.choice());
            assertEquals(1,model.calls.get());assertEquals(1,count(output.events(),"ORDINARY_MODEL_HTTP_END"));
            assertEquals(0,count(output.events(),"ORDINARY_MODEL_HTTP_ARCHIVED"),"a failed attempt preserve must not publish a counterfeit durable index");
            assertTrue(client.materials.values().stream().noneMatch(b->tree(b).path("schema").asText().equals("xar.ordinary-model-http-attempt/v1")));
            model.assertHealthy();
        }
        assertFixtureUnchanged();
    }

    private record Fixture(PlanningRequest request,ActionCommand command,PlanningResult.ActionSelected selected) { }
    private static Fixture fixture(boolean largeHistory) throws IOException {
        byte[] bytes=Files.readAllBytes(FIXTURE);assertEquals(33986,bytes.length);assertEquals(SHA,ActionCodec.sha256(bytes));
        JsonNode report=tree(bytes),plan=report.get("last_plan"),detail=plan.path("final_plan").get("detail");
        var before=ProposalLifecycleCodec.decodeObservation(plan.get("before"));
        Obj query=object(detail.get("lifestyle_original_query")),decision=object(detail.get("lifestyle_decision"));
        assertEquals("a_mans_home_perk",decision.get("selected_action") instanceof Obj selected?OpportunityJson.text(selected.get("target_key"),"target"):null);
        // Fresh software DATA identity/deadline only; no old failed Runtime request or command is reconstructed.
        Instant observed=Instant.parse(report.path("observed_at_utc").textValue());
        ExactRef sourceRef=new ExactRef(FIXTURE.toAbsolutePath().toString(),bytes.length,SHA);
        var source=new G2Source(before.machineId(),observed.toString(),"1.20.0.4",sourceRef);
        Instant deadline=observed.plusSeconds(120);
        Obj args=new Obj(Map.of()).with("target_key",new OpportunityJson.Text("a_mans_home_perk"))
                .with("target_lifestyle_key",new OpportunityJson.Text("martial_lifestyle")).with("original_query",query).with("decision",decision);
        var expected=new ProposalLifecycle.ExpectedPostcondition(1,before,source,"xar.java.governance-independent-effect/v1",List.of(
                new ProposalLifecycle.ExpectedText(new ProposalLifecycle.FieldKey("lifestyle.target_key"),"a_mans_home_perk"),
                new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("lifestyle.target_perk_owned"),true),
                new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("native.gameplay_verified"),true)));
        var claims=new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(before.frame().identity().player()),Set.of("lifestyle-perk:a_mans_home_perk"));
        ActionCommand command=new ActionCommand("derived-software-b66-perk78",before,source,report.path("session_id").textValue(),
                new OperationKey(GovernanceActionPreparation.PERK),args,expected,claims,deadline);
        GovernanceActionPreparation.lifestyleFields(command);
        ObjectNode current=(ObjectNode)tree(FullJsonTree.encode(query.get("snapshot") instanceof Obj qs?DriverJson.toNode(qs):null,MATERIAL));
        current.put("paused",true);current.put("map_ready",true);current.put("revision",before.frame().revision());
        current.putObject("played_character").put("character_id",before.frame().identity().player()).put("alive",true);
        current.putArray("active_wars");current.putArray("player_armies");current.putNull("active_event");current.putNull("pending_character_interaction");
        current.putNull("native_command_history");
        current.putObject("test_current_unknown").put("status","unknown").putNull("value");
        Obj snapshot=object(current);List<Obj> history=new ArrayList<>();
        int count=largeHistory?40:2;
        for(int i=0;i<count;i++) {
            var row=StrictJson.object();row.put("index",i+1000);row.put("command","unrelated-software-read");row.put("ok",false);
            row.putObject("result").put("unknown_detail","irrelevant-history-marker-"+i+":"+"q".repeat(largeHistory?32768:128));history.add(object(row));
        }
        var fact=new ExternalFact("software-original-rejected-fact","e".repeat(64),before,ExternalState.REJECTED_CONFIRMED,
                UnknownScope.GLOBAL,Domain.lifestyle,claims,sourceRef);
        var observation=new PlanningObservation(snapshot,history,Set.of(command.operation(),new OperationKey("pause-map"),new OperationKey("query-campaign-root-context-v1")),
                Set.of("game.command.pause-map","software-perk-route-advertised"),Optional.empty(),List.of(fact),Optional.empty(),Optional.empty(),false);
        var request=new PlanningRequest(before,source,command.sessionId(),deadline,observation);
        return new Fixture(request,command,selected(request,command,"lifestyle_min_perk_action",OrdinaryPolicy.Kind.ORDINARY));
    }
    private static PlanningResult.ActionSelected selected(PlanningRequest request,ActionCommand command,String phase,OrdinaryPolicy.Kind kind) {
        var draft=new OrdinaryPolicy.Draft("java-ordinary-governance-v1",phase,"one software-derived original legal PERK",kind,Optional.of(command),
                OrdinaryPolicy.Purpose.WORLD_ACTION,Optional.of(Domain.lifestyle),command.arguments());
        var visit=new PlanTrace.StageVisit(PlanningStage.LIFESTYLE,PlanTrace.Outcome.REPLACED,"software-derived PERK",
                Optional.of(command.source().sourceRef()),Optional.of(command.arguments()));
        return new PlanningResult.ActionSelected(command,new PlanTrace(request.before(),List.of(visit),Optional.of(draft)));
    }
    private static PlanningRequest withSnapshot(Fixture f,Obj snapshot) {
        var o=f.request().observations();return new PlanningRequest(f.request().before(),f.request().source(),f.request().sessionId(),f.request().deadline(),
                new PlanningObservation(snapshot,o.history(),o.actionSteps(),o.bridgeCapabilities(),o.battleSpeedReadiness(),o.actionFacts(),o.campaignGoal(),o.crossRunPlan(),o.initialLifestyleFocusRequired()));
    }
    private static byte[] historyBytes(PlanningRequest request) {return OpportunityJson.encode(new OpportunityJson.Arr(new ArrayList<OpportunityJson.Value>(request.observations().history())));}
    private static Obj object(JsonNode node) {return DriverJson.object(FullJsonTree.encode(node,MATERIAL),MATERIAL);}
    private static JsonNode tree(byte[] raw) {return FullJsonTree.parse(raw,MATERIAL);}
    private static JsonNode userData(JsonNode wire) {return tree(wire.path("messages").get(1).path("content").textValue().getBytes(StandardCharsets.UTF_8));}
    private static ArrayNode strings(List<String> values) {var a=com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.arrayNode();values.forEach(a::add);return a;}
    private static ArrayNode expectedFacts(PlanningRequest request) {
        var a=com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.arrayNode();
        for(var fact:request.observations().actionFacts()) {
            var item=a.addObject();item.put("action_id",fact.actionId());item.put("body_sha256",fact.bodySha256());item.put("state",fact.state().name());
            item.put("unresolved",fact.unresolved());item.put("scope",fact.scope().name());item.put("domain",String.valueOf(fact.domain()));
            item.set("affected_claims",ActionCodec.claims(fact.affectedClaims()));
        }
        return a;
    }
    private static ObjectNode reply(ActionCommand command) {var o=StrictJson.object();o.put("decision","SELECT_PROPOSAL");o.put("proposal_id",command.actionId());o.put("body_sha256",ActionCodec.bodySha256(command));o.put("reason","select original prepared perk");return o;}
    private static void assertFixtureUnchanged() throws IOException {byte[] raw=Files.readAllBytes(FIXTURE);assertEquals(33986,raw.length);assertEquals(SHA,ActionCodec.sha256(raw));}
    private static void assertMaterials(Client client) throws IOException {
        for(var e:client.materials.entrySet()) {assertArrayEquals(e.getValue(),Files.readAllBytes(Path.of(e.getKey().path())));assertEquals(e.getValue().length,e.getKey().bytes());assertEquals(ActionCodec.sha256(e.getValue()),e.getKey().sha256());}
    }
    private static long count(List<JsonNode> events,String status) {return events.stream().filter(e->e.path("status").asText().equals(status)).count();}
    private static Client client(Stub model,Path root,Fixture f) throws IOException {return new Client(model,root,Clock.fixed(f.request().deadline().minusSeconds(60),ZoneOffset.UTC));}
    private static final class Client implements AutoCloseable {
        final Map<ExactRef,byte[]> materials=new LinkedHashMap<>();final RootOnlineDecisionSelector selector;boolean failAttempt;
        Client(Stub model,Path root,Clock clock) throws IOException {
            Files.createDirectories(root);
            selector=new RootOnlineDecisionSelector(new RootOrdinaryRuntimeConfiguration.DecisionProvider(model.endpoint(),"local-stub-perk-regression",Duration.ofSeconds(10),1,Duration.ZERO),clock,raw->{
                byte[] bytes=raw.bytes();if(failAttempt&&tree(bytes).path("schema").asText().equals("xar.ordinary-model-http-attempt/v1"))throw new IOException("controlled attempt preservation failure");
                Path file=root.resolve("material-"+materials.size()+".json");Files.write(file,bytes,StandardOpenOption.CREATE_NEW);
                ExactRef ref=new ExactRef(file.toAbsolutePath().toString(),bytes.length,ActionCodec.sha256(bytes));materials.put(ref,bytes);return ref;
            });
        }
        @Override public void close() throws ReflectiveOperationException {Field f=RootOnlineDecisionSelector.class.getDeclaredField("http");f.setAccessible(true);((HttpClient)f.get(selector)).close();}
    }
    private static final class Progress implements AutoCloseable {
        final PrintStream original=System.out;final ByteArrayOutputStream copy=new ByteArrayOutputStream();final PrintStream tee;
        Progress() {tee=new PrintStream(new OutputStream(){
            @Override public void write(int b){original.write(b);copy.write(b);}
            @Override public void write(byte[] b,int off,int len){original.write(b,off,len);copy.write(b,off,len);}
            @Override public void flush(){original.flush();}
        },true,StandardCharsets.UTF_8);System.setOut(tee);}
        String text(){tee.flush();return copy.toString(StandardCharsets.UTF_8);}
        List<JsonNode> events(){var result=new ArrayList<JsonNode>();for(String line:text().split("\\R"))if(line.startsWith("{"))result.add(tree(line.getBytes(StandardCharsets.UTF_8)));return result;}
        @Override public void close(){System.setOut(original);tee.close();}
    }
    private static final class Stub implements AutoCloseable {
        final HttpServer server;final ExecutorService workers=Executors.newVirtualThreadPerTaskExecutor();
        final AtomicReference<ObjectNode> reply=new AtomicReference<>();final AtomicInteger calls=new AtomicInteger();final AtomicReference<Throwable> failure=new AtomicReference<>();
        final List<byte[]> requests=new ArrayList<>();volatile int status=200;volatile byte[] error=new byte[0];
        Stub() throws IOException {server=HttpServer.create(new InetSocketAddress("127.0.0.1",0),0);server.setExecutor(workers);server.createContext("/v1/chat/completions",this::handle);server.start();}
        URI endpoint(){return URI.create("http://127.0.0.1:"+server.getAddress().getPort()+"/v1");}
        void handle(HttpExchange exchange) throws IOException {
            try {
                assertEquals("POST",exchange.getRequestMethod());byte[] raw=exchange.getRequestBody().readNBytes(MATERIAL+1);requests.add(raw);calls.incrementAndGet();tree(raw);
                if(status!=200){exchange.getResponseHeaders().set("Content-Type","application/json");exchange.sendResponseHeaders(status,error.length);exchange.getResponseBody().write(error);return;}
                exchange.getResponseHeaders().set("Content-Type","text/event-stream; charset=UTF-8");exchange.sendResponseHeaders(200,0);
                var frame=StrictJson.object();frame.putArray("choices").addObject().putObject("delta").put("content",reply.get().toString());
                exchange.getResponseBody().write(("data: "+frame+"\n\n").getBytes(StandardCharsets.UTF_8));
                var finish=StrictJson.object();var choice=finish.putArray("choices").addObject();choice.putObject("delta");choice.put("finish_reason","stop");
                exchange.getResponseBody().write(("data: "+finish+"\n\ndata: [DONE]\n\n").getBytes(StandardCharsets.UTF_8));exchange.getResponseBody().flush();
            } catch(Throwable problem){failure.compareAndSet(null,problem);if(problem instanceof IOException io)throw io;}
            finally{exchange.close();}
        }
        void assertHealthy(){assertNull(failure.get(),()->String.valueOf(failure.get()));}
        @Override public void close(){server.stop(0);workers.shutdownNow();}
    }
}
