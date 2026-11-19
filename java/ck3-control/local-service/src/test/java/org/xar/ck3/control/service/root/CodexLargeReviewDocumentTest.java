package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.TextNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.api.io.CleanupMode;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real file transport over fresh owned software fixtures; historical Scene24 material is read-only DATA. */
@org.junit.jupiter.api.condition.EnabledIfSystemProperty(named="xar.codex.document.inputs",matches=".+")
final class CodexLargeReviewDocumentTest {
    @TempDir(cleanup=CleanupMode.NEVER) Path directory;
    private record Fixture(Path root,Path queue,Path materials,PlanningRequest request,PlanningResult.ActionSelected proposal,RootOnlineDecisionSelector selector) { }
    private static OpportunityJson.IntegerValue integer(long value){return new OpportunityJson.IntegerValue(BigInteger.valueOf(value));}
    private static Fixture fixture(Path root,Duration timeout,int padding) throws Exception {
        Files.createDirectories(root);Path materials=Files.createDirectory(root.resolve("materials"));Path queue=root.resolve("queue");
        Path sourceFile=root.resolve("software-source.txt");Files.writeString(sourceFile,"owned software file transport fixture; no live qualification");
        byte[] sourceBytes=Files.readAllBytes(sourceFile);var ref=new ExactRef(sourceFile.toAbsolutePath().toString(),sourceBytes.length,ActionCodec.sha256(sourceBytes));
        OperationKey operation=new OperationKey("fixture-source-selected-query");
        var snapshot=new OpportunityJson.Obj(Map.ofEntries(Map.entry("paused",new OpportunityJson.Bool(true)),Map.entry("map_ready",new OpportunityJson.Bool(true)),
                Map.entry("revision",integer(1)),Map.entry("native_revision",integer(1)),Map.entry("date_raw",integer(24000)),
                Map.entry("snapshot_id",new OpportunityJson.Text("software-snapshot-1")),Map.entry("episode_run_id",new OpportunityJson.Text("software-episode-1")),
                Map.entry("played_character",new OpportunityJson.Obj(Map.of("character_id",integer(29829),"alive",new OpportunityJson.Bool(true)))),
                Map.entry("active_wars",new OpportunityJson.Arr(List.of())),Map.entry("player_armies",new OpportunityJson.Arr(List.of())),
                Map.entry("complete_codex_context",new OpportunityJson.Text("x".repeat(padding)))));
        var game=new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        var before=new ObservationIdentity("fixture-machine-1",game,new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.ONE,BigInteger.valueOf(24000)),"software-snapshot-1",BigInteger.ONE,"software-episode-1"),1);
        var source=new G2Source(before.machineId(),Instant.now().toString(),"software-no-native-build",ref);
        var request=new PlanningRequest(before,source,"software-file-session",Instant.now().plusSeconds(30),new PlanningObservation(snapshot,List.of(),Set.of(operation),Set.of(),
                Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
        var command=new ActionCommand("software-file-original",before,source,request.sessionId(),operation,new OpportunityJson.Obj(Map.of()),
                new ExpectedPostcondition(1,before,source,"software-file-observer/v1",List.of(new ExpectedBoolean(new FieldKey("paused"),true))),
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),request.deadline());
        var draft=new OrdinaryPolicy.Draft("software-file","review","no action is submitted",OrdinaryPolicy.Kind.ORDINARY,Optional.of(command),OrdinaryPolicy.Purpose.READ_ONLY,
                Optional.empty(),new OpportunityJson.Obj(Map.of()));
        var proposal=new PlanningResult.ActionSelected(command,new PlanTrace(before,List.of(),Optional.of(draft)));
        var selector=new RootOnlineDecisionSelector(new RootOrdinaryRuntimeConfiguration.DecisionProvider(queue.toUri(),"codex-session",timeout,1,Duration.ZERO),Clock.systemUTC(),raw->{
            byte[] bytes=raw.bytes();String sha=ActionCodec.sha256(bytes);Path file=materials.resolve(sha+".json");if(!Files.exists(file))Files.write(file,bytes);
            return new ExactRef(file.toAbsolutePath().toString(),bytes.length,sha);
        });
        return new Fixture(root,queue,materials,request,proposal,selector);
    }
    private static Path ready(Fixture fixture) throws Exception {
        long until=System.nanoTime()+TimeUnit.SECONDS.toNanos(6);
        while(System.nanoTime()<until){
            if(Files.isDirectory(fixture.queue()))try(var entries=Files.list(fixture.queue())){
                var files=entries.filter(Files::isDirectory).map(path->path.resolve("request.json"))
                        .filter(Files::isRegularFile).filter(path->Files.isRegularFile(path.getParent().resolve("ready.json"))).toList();
                if(!files.isEmpty()){assertEquals(1,files.size());return files.getFirst();}
            }
            Thread.sleep(5);
        }
        throw new IllegalStateException("owned producer did not publish its finite READY");
    }
    private static JsonNode parseTask(JsonNode node) throws Exception {
        var method=CodexSessionDecisionFiles.class.getDeclaredMethod("reviewTask",JsonNode.class);method.setAccessible(true);
        try{return (JsonNode)method.invoke(null,node);}catch(java.lang.reflect.InvocationTargetException failure){
            if(failure.getCause() instanceof Exception cause)throw cause;throw failure;
        }
    }
    @Test @Timeout(25) void freshLargeProducerPayloadUsesPublicInspectAndSingleOriginalWAIT() throws Exception {
        var f=fixture(directory.resolve("large"),Duration.ofSeconds(8),1_900_000);
        var http=RootOnlineDecisionSelector.class.getDeclaredField("http");http.setAccessible(true);assertNull(http.get(f.selector()));
        var producer=CompletableFuture.supplyAsync(()->f.selector().select(f.request(),f.proposal()));
        try {
            Path request=ready(f);byte[] originalRequest=Files.readAllBytes(request);String sha=ActionCodec.sha256(originalRequest);
            var envelope=FullJsonTree.parse(originalRequest,16384);assertTrue(envelope.path("payload").path("bytes").longValue()>1_900_000);
            var inspected=CodexSessionDecisionMain.execute(Clock.systemUTC(),"inspect",request.toString(),sha,f.materials().toString());
            Path inspection=f.root().resolve("inspection.json");Files.write(inspection,FullJsonTree.encode(inspected,262144));
            Path selection=f.root().resolve("selection.json");var pending=CodexSessionDecisionFiles.read(request,sha,f.materials(),Clock.systemUTC());
            var exact=pending.selection(CodexSessionDecisionFiles.Decision.WAIT,"bounded software observation only");
            Files.write(selection,FullJsonTree.encode(exact.toJson().put("body_sha256","0".repeat(64)),262144));
            assertThrows(RuntimeException.class,()->CodexSessionDecisionMain.execute(Clock.systemUTC(),"respond",request.toString(),sha,f.materials().toString(),selection.toString(),inspection.toString()));
            assertFalse(Files.exists(request.getParent().resolve("response.json")));
            Files.write(selection,FullJsonTree.encode(exact.toJson(),262144));
            var response=CodexSessionDecisionMain.execute(Clock.systemUTC(),"respond",request.toString(),sha,f.materials().toString(),selection.toString(),inspection.toString());
            assertEquals("xar.ordinary-codex-session-response-published/v1",response.path("schema").textValue());
            byte[] published=Files.readAllBytes(request.getParent().resolve("response.json"));
            assertThrows(Exception.class,()->CodexSessionDecisionMain.execute(Clock.systemUTC(),"respond",request.toString(),sha,f.materials().toString(),selection.toString(),inspection.toString()));
            assertArrayEquals(published,Files.readAllBytes(request.getParent().resolve("response.json")));assertArrayEquals(originalRequest,Files.readAllBytes(request));
        } finally {assertEquals(OrdinaryDecisionSelector.Choice.WAIT,producer.get(12,TimeUnit.SECONDS).choice());}
    }
    @Test void actualClosed24DocumentParsesWithoutRenewingItsRequestOrWritingItsQueue() throws Exception {
        var index=StrictJson.parse(Files.readAllBytes(Path.of(System.getProperty("xar.codex.document.inputs"))));
        var ref=ExactRef.fromJson(index.get("actual_payload24"));byte[] bytes=Files.readAllBytes(Path.of(ref.path()));
        assertEquals(ref.bytes(),bytes.length);assertEquals(ref.sha256(),ActionCodec.sha256(bytes));
        var wire=FullJsonTree.parse(bytes,FullJsonTree.MAXIMUM_BYTES);JsonNode user=null;
        for(var message:wire.get("messages"))if(message.path("role").asText().equals("user")){assertNull(user);user=message.get("content");}
        assertNotNull(user);assertTrue(user.textValue().length()>32768);JsonNode original=user;
        assertThrows(RuntimeException.class,()->StrictJson.text(original));var task=parseTask(user);
        assertEquals(index.path("actual_proposal_id").asText(),task.path("proposal_id").asText());
        assertEquals(index.path("actual_body_sha256").asText(),task.path("body_sha256").asText());
        assertEquals(16384,CodexSessionDecisionFiles.MAX_REQUEST_BYTES);assertEquals(262144,CodexSessionDecisionFiles.MAX_RESPONSE_BYTES);
        assertArrayEquals(bytes,Files.readAllBytes(Path.of(ref.path())));
    }
    @Test void documentUnicodeAndJsonStructureStayStrictAndShortReceiptTextLimitDoesNotChange() throws Exception {
        assertEquals("🙂",parseTask(TextNode.valueOf("{\"label\":\"🙂\",\"padding\":\""+"x".repeat(40000)+"\"}")).path("label").asText());
        assertThrows(Exception.class,()->parseTask(TextNode.valueOf("{\"label\":\""+Character.toString((char)0xd800)+"\"}")));
        assertThrows(Exception.class,()->parseTask(TextNode.valueOf("{\"duplicate\":1,\"duplicate\":2}")));
        assertThrows(Exception.class,()->parseTask(TextNode.valueOf("{} {}")));
        assertThrows(Exception.class,()->parseTask(TextNode.valueOf("")));
        assertThrows(Exception.class,()->parseTask(StrictJson.object()));
        assertThrows(RuntimeException.class,()->StrictJson.text("x".repeat(32769)));
    }
    @Test @Timeout(20) void freshQueuesKeepOriginalHashCustodyAndEarlierExpiry() throws Exception {
        var f=fixture(directory.resolve("tamper"),Duration.ofSeconds(2),1000);
        var producer=CompletableFuture.supplyAsync(()->f.selector().select(f.request(),f.proposal()));
        try {
            Path request=ready(f);String sha=ActionCodec.sha256(Files.readAllBytes(request));
            var pending=CodexSessionDecisionFiles.read(request,sha,f.materials(),Clock.systemUTC());
            assertThrows(RuntimeException.class,()->CodexSessionDecisionFiles.read(request,"0".repeat(64),f.materials(),Clock.systemUTC()));
            var row=FullJsonTree.parse(Files.readAllBytes(request),16384);Path payload=Path.of(row.path("payload").path("path").textValue());
            Files.write(payload,new byte[]{32},java.nio.file.StandardOpenOption.APPEND);
            assertThrows(RuntimeException.class,()->CodexSessionDecisionFiles.respond(pending,pending.selection(CodexSessionDecisionFiles.Decision.WAIT,"material changed")));
            assertFalse(Files.exists(request.getParent().resolve("response.json")));
        } finally {assertEquals(OrdinaryDecisionSelector.Choice.WAIT,producer.get(6,TimeUnit.SECONDS).choice());}
        var expired=fixture(directory.resolve("expired"),Duration.ofMillis(700),1000);
        var timeout=CompletableFuture.supplyAsync(()->expired.selector().select(expired.request(),expired.proposal()));
        Path request=ready(expired);String sha=ActionCodec.sha256(Files.readAllBytes(request));Thread.sleep(800);
        assertThrows(RuntimeException.class,()->CodexSessionDecisionFiles.read(request,sha,expired.materials(),Clock.systemUTC()));
        assertFalse(Files.exists(request.getParent().resolve("response.json")));assertEquals(OrdinaryDecisionSelector.Choice.WAIT,timeout.get(4,TimeUnit.SECONDS).choice());
    }
    /** Owned, hidden fixture producer for the single-response diagnostic watcher test. */
    public static void main(String[] args) throws Exception {
        if(args.length!=2||!args[0].equals("produce"))throw new IllegalArgumentException("closed software producer mode/root required");
        var f=fixture(Path.of(args[1]),Duration.ofSeconds(8),1_900_000);
        Files.writeString(f.root().resolve("main.BEGIN.json"),"{\"pid\":"+ProcessHandle.current().pid()+"}");
        var result=f.selector().select(f.request(),f.proposal());
        Files.writeString(f.root().resolve("main.END.json"),"{\"choice\":\""+result.choice()+"\"}");
        if(result.choice()!=OrdinaryDecisionSelector.Choice.WAIT)throw new AssertionError("software producer requires exactly one WAIT");
    }
}
