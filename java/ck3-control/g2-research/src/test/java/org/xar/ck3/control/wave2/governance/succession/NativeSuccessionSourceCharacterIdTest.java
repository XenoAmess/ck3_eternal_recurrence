package org.xar.ck3.control.wave2.governance.succession;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.governance.succession.SuccessionModel.*;
import static org.xar.ck3.control.wave2.governance.succession.NativeSuccessionObservation12004.EXECUTABLE_SHA256;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider.*;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleCodec;
/** Existing MemoryRoot byte producer parameterized by exact character roles -> actual public Source.read.
 * All artifacts live in memory. This grants no Native RPC, filesystem/source qualification or live succession. */
final class NativeSuccessionSourceCharacterIdTest {
    private static final String MACHINE = "unit-machine";
    private static final String SHA = "a".repeat(64);
    private static final SuccessionLifecycleBinding LIFE = new SuccessionLifecycleBinding(
            SuccessionLifecycleBinding.Profile.ORDINARY_VERIFIED_MOD_ABSENCE,
            "absent_by_verified_xar_mod_not_loaded", SHA);


    private static NativeSuccessionSource12004.Result read(MemoryRoot root){return NativeSuccessionSource12004.read(root,root.limits,root.request);}
    /** Test-only producer hook for the independent actual M7 -> Source -> observation/report consumer. */
    static NativeSuccessionObservation12004.Frame sourceProducedFrame(int actor,int heir,JsonNode originalGoal){
        var result=read(new MemoryRoot(actor,heir,originalGoal));
        if(result instanceof NativeSuccessionSource12004.Observed observed)return observed.frame();
        throw new AssertionError("actual retained Source rejected producer input: "+result);
    }
    private static void observed(int actor,int heir){
        var root=new MemoryRoot(actor,heir);var result=read(root);
        var value=assertInstanceOf(NativeSuccessionSource12004.Observed.class,result,result::toString).frame();
        assertEquals(actor,value.snapshot().actor().characterId());assertEquals(actor,value.snapshot().episodeCharacterId());
        assertEquals(heir,value.bundle().primaryHeirCharacterId());
        assertEquals(actor,StrictJson.parse(root.bytes.get(root.request.rootResult())).path("campaign_root_context").path("player_character_id").intValue());
    }
    @Test void actualRetainedProducerAcceptsEverySignedPlayedActorIncludingZero(){
        assertAll(java.util.stream.IntStream.of(0,-2,Integer.MIN_VALUE,Integer.MAX_VALUE).mapToObj(actor->
                (org.junit.jupiter.api.function.Executable)()->observed(actor,3)));
    }
    @Test void actualRetainedProducerAcceptsEverySignedPrimaryHeirIncludingZero(){
        assertAll(java.util.stream.IntStream.of(0,-2,Integer.MIN_VALUE,Integer.MAX_VALUE).mapToObj(heir->
                (org.junit.jupiter.api.function.Executable)()->observed(2,heir)));
    }
    @Test void ordinaryPositiveProducerStillWorksAndValidDifferentRolesCannotCross(){
        observed(2,3);var actor=new MemoryRoot(2,3);actor.rootActor(StrictJson.parse("3".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        assertInstanceOf(NativeSuccessionSource12004.Rejected.class,read(actor));
        var heir=new MemoryRoot(2,3);heir.rootHeir(StrictJson.parse("4".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        assertInstanceOf(NativeSuccessionSource12004.Rejected.class,read(heir));
    }
    @Test void absentBooleanFloatTextNullOverflowAndUintAliasesAreRejectedAtBothCharacterRoles(){
        record Malformed(String wire,int wouldAlias){}
        for(var malformed:List.of(new Malformed("-1",2),new Malformed("-2147483649",Integer.MAX_VALUE),
                new Malformed("2147483648",Integer.MIN_VALUE),new Malformed("4294967294",-2),
                new Malformed("true",1),new Malformed("2.0",2),new Malformed("\"2\"",2),new Malformed("null",0))){
            String wire=malformed.wire();
            JsonNode token=wire.equals("2.0")?com.fasterxml.jackson.databind.node.DoubleNode.valueOf(2.0):StrictJson.parse(wire.getBytes(java.nio.charset.StandardCharsets.UTF_8));
            var actor=new MemoryRoot(malformed.wouldAlias(),3);actor.rootActor(token);assertInstanceOf(NativeSuccessionSource12004.Rejected.class,read(actor),wire);
            var heir=new MemoryRoot(7,malformed.wouldAlias());heir.rootHeir(token);assertInstanceOf(NativeSuccessionSource12004.Rejected.class,read(heir),wire);
        }
        var missing=new MemoryRoot(2,3);missing.rootActor(null);assertInstanceOf(NativeSuccessionSource12004.Rejected.class,read(missing));
    }
    @Test void titleAndQueryRolesKeepTheirOwnPositiveAndUnsignedBoundaries(){
        for(int title:new int[]{0,-2}){var root=new MemoryRoot(2,3);root.titleId(title);assertInstanceOf(NativeSuccessionSource12004.Rejected.class,read(root));}
        for(String wire:List.of("0","-1","18446744073709551616")){
            var root=new MemoryRoot(2,3);root.query(StrictJson.parse(wire.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            assertInstanceOf(NativeSuccessionSource12004.Rejected.class,read(root));
        }
        var maximum=new MemoryRoot(2,3);maximum.query(com.fasterxml.jackson.databind.node.BigIntegerNode.valueOf(StrictJson.UINT64_MAX));
        assertInstanceOf(NativeSuccessionSource12004.Observed.class,read(maximum));
    }
    private static TitleRow row(int title, int heir, boolean primary) {
        ObjectNode metadata = StrictJson.object().put("title_id", title).put("tier_raw", 3);
        return new TitleRow(new Title(title, BigInteger.valueOf(3), new WireObject(StrictJson.canonical(metadata))), heir, primary);
    }
    private static Session session(String episode) {
        return new Session(MACHINE, "same-root-session", new GameIdentity(4242, "133000000000000000"), episode, "1",
                new ExactRef("C:/unit/ck3.exe", 1, EXECUTABLE_SHA256), "340282366920938463463374607431768211000", "133000000000000000");
    }
    private static final class MemoryRoot implements RootOwnedSources {
        private final Map<ExactRef, byte[]> bytes = new HashMap<>();
        private final Session session = session("before");
        private final G2RetainedNativeSourceProvider.Limits limits = new G2RetainedNativeSourceProvider.Limits(1048576, 131072);
        private NativeSuccessionSource12004.Request request;
        private final RetainedArtifact artifact;
        private final boolean available;
        MemoryRoot(int actor,int heir) {this(actor,heir,null);}
        MemoryRoot(int actor,int heir,JsonNode originalGoal) {
            this.available = true;
            List<TitleRow> producedRows=List.of(row(10,heir,true),row(11,4,false));
            ObjectNode snapshot = StrictJson.object().put("snapshot_id", "native:1").put("revision", 1).put("native_revision", 1)
                    .put("date_raw", 101).put("episode_run_id", "before").put("episode_character_id", actor)
                    .put("paused", true).put("map_ready", true).put("one_life_terminal", false).put("backend_id", "native-headless");
            snapshot.putNull("one_life_terminal_reason").putNull("active_event").putNull("pending_character_interaction");
            snapshot.putObject("played_character").put("character_id", actor).put("alive", true);
            if(originalGoal!=null)snapshot.set("campaign_goal",originalGoal.deepCopy());
            snapshot.set("succession_lifecycle", StrictJson.parse(SuccessionLifecycleCodec.encode(LIFE), 16384));
            ObjectNode diagnostics = snapshot.putObject("diagnostics").put("bridge_pid", 4242).put("connection_generation", 1);
            diagnostics.putObject("hello").put("pid", 4242).put("connection_generation", 1).put("ck3_build_match", true)
                    .put("expected_ck3_version", "1.20.0.4").put("expected_ck3_sha256", EXECUTABLE_SHA256);
            ObjectNode binding = StrictJson.object().put("snapshot_id", "native:1").put("revision", 1).put("native_revision", 1).put("date_raw", 101);
            ObjectNode bundle = StrictJson.object().put("schema", "xar.ck3.turn-bundle/v1").put("status", "partial");
            bundle.set("binding", binding);
            ObjectNode ruler = bundle.putObject("ruler_state").put("status", "available").putObject("value").put("character_id", actor).put("alive", true);
            ObjectNode government = StrictJson.object().put("key", "feudal_government");
            ruler.putObject("government").put("status", "available").set("value", government);
            ObjectNode succession = bundle.putObject("succession_state").put("status", "available").putObject("value");
            succession.putObject("primary_title_heir_character_id").put("status", "available").put("value", heir);
            ObjectNode partition = succession.putObject("partition").put("status", "available").putObject("value").put("risk_state", "split_successors");
            var titleRows = partition.putArray("title_heirs");
            for (TitleRow row : producedRows) {
                ObjectNode wire = titleRows.addObject().put("first_heir_character_id", row.firstHeirCharacterId()).put("primary", row.primary());
                wire.set("title", StrictJson.parse(row.title().original().bytes()));
            }
            bundle.putObject("source").put("capability", "game.command.query-campaign-root-context-v1").put("query_sequence", 1).put("backend_id", "native-headless");
            ObjectNode rootResult = StrictJson.object().put("status", "available").put("query_sequence", 1); rootResult.set("binding", binding);
            ObjectNode root = rootResult.putObject("campaign_root_context").put("status", "available").put("snapshot_revision", 1)
                    .put("date_raw", 101).put("player_character_id", actor).put("player_character_alive", true);
            root.set("held_title_partition", titleRows); root.putArray("primary_title_succession_character_ids").add(heir);
            root.set("government", government); root.putObject("readiness").put("held_title_partition_ready", true);
            request = new NativeSuccessionSource12004.Request(store("root", rootResult), store("bundle", bundle));
            ObjectNode result = StrictJson.object().put("is_error", false).put("result_type", "complete");
            result.putObject("meta"); result.putArray("content"); result.set("structured_content", snapshot);
            ObjectNode owner = StrictJson.object().put("started_at_utc", "2026-10-23T00:00:59Z")
                    .put("ended_at_utc", "2026-10-23T00:01:00Z").put("elapsed_seconds", 1)
                    .put("mcp_result_projection_json_utf8_bytes", StrictJson.canonical(result).length);
            owner.putObject("request").put("sequence", 1).put("tool", "unit-snapshot").putObject("arguments");
            owner.set("result", result);
            ObjectNode measurement = StrictJson.object().put("schema", "xar.resume56-current-game-files-readonly-observation/v1")
                    .put("machine_id", MACHINE).put("observed_at_utc", "2026-10-23T00:00:00Z");
            var observations = measurement.putArray("observations");
            observations.addObject().put("label", "game_exe").put("stable_during_read", true).put("path", session.executable().path())
                    .put("bytes", 1).put("sha256", EXECUTABLE_SHA256).put("file_id_decimal", session.executableFileId()).put("mtime_ns_decimal", session.executableMtimeNs());
            observations.addObject().put("label", "launcher_settings").put("stable_during_read", true).put("raw_version", "1.20.0.4");
            artifact = new RetainedArtifact(session, store("owner", owner), store("measurement", measurement), "unit-snapshot");
        }
        void rootActor(JsonNode token){
            ObjectNode result=(ObjectNode)StrictJson.parse(bytes.get(request.rootResult()),SuccessionCodec.MAX_BYTES);
            ObjectNode root=(ObjectNode)result.get("campaign_root_context");if(token==null)root.remove("player_character_id");else root.set("player_character_id",token);
            request=new NativeSuccessionSource12004.Request(storeMalformedWire("root",result),request.turnBundle());
        }
        void rootHeir(JsonNode token){
            ObjectNode result=(ObjectNode)StrictJson.parse(bytes.get(request.rootResult()),SuccessionCodec.MAX_BYTES);
            ((com.fasterxml.jackson.databind.node.ArrayNode)result.path("campaign_root_context").get("primary_title_succession_character_ids")).set(0,token);
            request=new NativeSuccessionSource12004.Request(storeMalformedWire("root",result),request.turnBundle());
        }
        void titleId(int title){
            ObjectNode result=(ObjectNode)StrictJson.parse(bytes.get(request.rootResult()),SuccessionCodec.MAX_BYTES);
            ObjectNode bundle=(ObjectNode)StrictJson.parse(bytes.get(request.turnBundle()),SuccessionCodec.MAX_BYTES);
            ((ObjectNode)result.path("campaign_root_context").path("held_title_partition").get(0).get("title")).put("title_id",title);
            ((ObjectNode)bundle.path("succession_state").path("value").path("partition").path("value").path("title_heirs").get(0).get("title")).put("title_id",title);
            request=new NativeSuccessionSource12004.Request(store("root",result),store("bundle",bundle));
        }
        void query(JsonNode token){
            ObjectNode result=(ObjectNode)StrictJson.parse(bytes.get(request.rootResult()),SuccessionCodec.MAX_BYTES);
            ObjectNode bundle=(ObjectNode)StrictJson.parse(bytes.get(request.turnBundle()),SuccessionCodec.MAX_BYTES);
            result.set("query_sequence",token);((ObjectNode)bundle.get("source")).set("query_sequence",token);
            request=new NativeSuccessionSource12004.Request(store("root",result),store("bundle",bundle));
        }
        /** Preserve malformed input tokens verbatim so the real public Source, rather than the fixture writer, rejects them. */
        private ExactRef storeMalformedWire(String name,JsonNode node){
            try{
                byte[] body=new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsBytes(node);
                ExactRef reference=new ExactRef("C:/unit/"+name+".json",body.length,G2RetainedNativeSourceProvider.sha256(body));
                bytes.put(reference,body);return reference;
            }catch(com.fasterxml.jackson.core.JsonProcessingException failure){throw new AssertionError(failure);}
        }
        private ExactRef store(String name, JsonNode node) {
            byte[] body = StrictJson.canonical(node, 1048576);
            ExactRef reference = new ExactRef("C:/unit/" + name + ".json", body.length, G2RetainedNativeSourceProvider.sha256(body));
            bytes.put(reference, body); return reference;
        }
        @Override public Optional<Session> currentSession() { return available ? Optional.of(session) : Optional.empty(); }
        @Override public Optional<RetainedArtifact> selectedSource(Milestone milestone, ProjectionJson payload) {
            return available && milestone == Milestone.M3 ? Optional.of(artifact) : Optional.empty();
        }
        @Override public byte[] readExact(ExactRef reference, int maximumBytes) throws IOException {
            byte[] body = bytes.get(reference);
            if (body == null || body.length > maximumBytes) { throw new IOException("unit source missing/oversized"); }
            return body.clone();
        }
    }
}
