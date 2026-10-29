package org.xar.ck3.control.wave2.events.choiceplanning;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.stream.StreamSupport;
import org.junit.jupiter.api.Test;

/** Actual batch27 retained rows and same-window backend inventories, reconstructed into
 * EventPolicies' mandatory wrapper. The full original PlanningRequest was not persisted;
 * metadata records that boundary. No Root authority, Known, Native transport or action is made. */
final class ChoicePlanningRetainedHistoryTest {
    private static final String RESOURCE="/org/xar/ck3/control/wave2/events/choiceplanning/fixtures/";
    private static final String OVERRIDE="xar.choicePlanningRegressionFixtureDir";
    private static final ObjectMapper JSON=new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build());

    @Test void completeActualRowsReachTypedConsumerWhileExternalBudgetRemainsStrict()throws Exception {
        byte[] wire=resource("batch27-retained-history-wrapper.json");
        JsonNode metadata=JSON.readTree(resource("batch27-retained-history-metadata.json"));
        assertEquals(metadata.path("wrapper_bytes").intValue(),wire.length);
        assertEquals(metadata.path("wrapper_sha256").textValue(),sha256(wire));
        assertTrue(wire.length>65536);
        ObjectNode wrapper=(ObjectNode)JSON.readTree(wire);String before=JSON.writeValueAsString(wrapper);
        var input=ChoicePlanningJson.decode(wrapper);
        assertEquals(metadata.path("history_rows").intValue(),input.commands().size());
        for(int index=0;index<input.commands().size();index++) {
            String expected=JSON.writeValueAsString(wrapper.path("commands").get(index));
            String retained=input.commands().get(index).original().json();
            assertEquals(expected,retained,"complete original row "+index+" must retain every field and its order");
            byte[] bytes=retained.getBytes(StandardCharsets.UTF_8);
            assertEquals(metadata.path("row_bytes").get(index).intValue(),bytes.length);
            assertEquals(metadata.path("row_sha256").get(index).textValue(),sha256(bytes));
        }
        var snapshot=input.snapshot().orElseThrow();var frame=snapshot.frame().orElseThrow();
        JsonNode expected=metadata.path("expected_frame");
        assertEquals(Long.parseLong(expected.path("game_pid").textValue()),frame.gamePid());
        assertEquals(expected.path("snapshot_id").textValue(),frame.snapshotId());
        assertEquals(expected.path("episode_run_id").textValue(),frame.episodeRunId());
        assertEquals(integer(expected,"revision"),frame.revision());assertEquals(integer(expected,"native_revision"),frame.nativeRevision());
        assertEquals(integer(expected,"date_raw"),frame.dateRaw());assertEquals(integer(expected,"actor_character_id"),frame.actorCharacterId());
        assertEquals(integer(expected,"connection_generation"),frame.connectionGeneration());
        assertFalse(snapshot.activeEventPresent());assertFalse(snapshot.pendingInteractionPresent());assertTrue(snapshot.hint().isEmpty());
        assertEquals(strings(wrapper.path("action_steps")),input.actionSteps());
        assertEquals(strings(wrapper.path("bridge_capabilities")),input.bridgeCapabilities());
        assertEquals(metadata.path("backend_action_steps").intValue(),input.actionSteps().size());
        assertEquals(metadata.path("backend_bridge_capabilities").intValue(),input.bridgeCapabilities().size());
        assertInstanceOf(ChoicePlanningModel.NoCandidate.class,new MandatoryChoicePlanner().plan(input));
        assertEquals(before,JSON.writeValueAsString(wrapper),"typed consumption must not trim or mutate original rows/snapshot fields");
        var external=assertThrows(IllegalArgumentException.class,()->ChoicePlanningJson.decode(wire));
        assertEquals("bounded UTF-8 planning request required",external.getMessage());
        ObjectNode unknown=wrapper.deepCopy();unknown.put("unexpected_internal_permission",true);
        assertThrows(IllegalArgumentException.class,()->ChoicePlanningJson.decode(unknown));
        ObjectNode nonfinite=wrapper.deepCopy();((ObjectNode)nonfinite.path("commands").get(0)).put("controlled_bad_geometry",Double.NaN);
        var domain=assertThrows(IllegalArgumentException.class,()->ChoicePlanningJson.decode(nonfinite));
        assertEquals("finite JSON geometry number required",domain.getMessage());
        System.out.println("CHOICE_PORTABLE_FIXTURE="+(System.getProperty(OVERRIDE)==null?"classpath":"explicit override")
                +"; wrapper="+wire.length+"; completeRows="+input.commands().size()+"; raw-cap/field/domain controls retained; noKnown/noNative");
    }
    private static byte[] resource(String name)throws IOException {
        String directory=System.getProperty(OVERRIDE);
        if(directory!=null&&!directory.isBlank())return Files.readAllBytes(Path.of(directory).resolve(name));
        try(InputStream input=ChoicePlanningRetainedHistoryTest.class.getResourceAsStream(RESOURCE+name)) {
            if(input==null)throw new IOException("Missing mandatory planning regression resource: "+RESOURCE+name);
            return input.readAllBytes();
        }
    }
    private static BigInteger integer(JsonNode object,String field){return new BigInteger(object.path(field).textValue());}
    private static Set<String> strings(JsonNode rows){return StreamSupport.stream(rows.spliterator(),false).map(JsonNode::textValue).collect(Collectors.toSet());}
    private static String sha256(byte[] bytes)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));}
}
