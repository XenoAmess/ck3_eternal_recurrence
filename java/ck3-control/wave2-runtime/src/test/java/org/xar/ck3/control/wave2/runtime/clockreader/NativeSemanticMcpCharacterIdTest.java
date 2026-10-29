package org.xar.ck3.control.wave2.runtime.clockreader;

import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.util.RawValue;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.LateOutcome.*;
import org.xar.ck3.control.reconciliation.NativeSemanticCodec;
import static org.junit.jupiter.api.Assertions.*;

/** The real MCP row consumer decodes both original representations; this fixture grants no Queue authority. */
class NativeSemanticMcpCharacterIdTest {
    private static final String SHA="1".repeat(64);
    private static final long SEQUENCE=11560;
    private static CrossJsDecimalUInt64 u(long value){return new CrossJsDecimalUInt64(Long.toString(value));}
    private static Scope scope(){
        return new Scope("synthetic-machine-not-runtime",new ProcessIdentity(12345,u(1000)),new ProcessIdentity(23456,u(2000)),
                new ProcessIdentity(34567,u(3000)),"synthetic-session",new SourceBinding(SHA,SHA,SHA,SHA,SHA),1,40526,
                "synthetic-episode",new WorldIdentity(u(111),u(222)));
    }
    private static Evidence evidence(){
        return new Evidence(scope(),scope(),SEQUENCE,new ContentEvidenceRef(SHA,1,"synthetic-native-mcp-row"),200,
                Instant.parse("2026-10-22T13:29:59.200Z"),u(900100));
    }
    private static ObjectNode original() throws Exception {
        try(var input=NativeSemanticMcpCharacterIdTest.class.getResourceAsStream("/clockreader/synthetic-late-semantic.json")) {
            assertNotNull(input,"actual retained clock-reader input is required; no skip");byte[] bytes=input.readAllBytes();
            assertEquals("afb8eea7474a8d932d0f4ed6bf1179ffbf0c6136bac0617c968378191727bbd7",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
            return (ObjectNode)StrictJson.parse(bytes);
        }
    }
    private static byte[] body(ObjectNode row){return row.toString().getBytes(StandardCharsets.UTF_8);}
    private static byte[] mcp(byte[] structured,byte[] text){
        ObjectNode row=StrictJson.object();ObjectNode request=row.putObject("request");request.put("sequence",SEQUENCE);
        request.put("tool",ClockMcpRowDecoder.SEMANTIC_TOOL);request.putObject("arguments");
        ObjectNode result=row.putObject("result");result.put("result_type","complete");result.put("is_error",false);
        result.putArray("content").addObject().put("type","text").put("text",new String(text,StandardCharsets.UTF_8));
        // Preserve each actual numeric token spelling through the production raw-slicing boundary.
        result.putRawValue("structured_content",new RawValue(new String(structured,StandardCharsets.UTF_8)));
        return body(row);
    }
    private static SemanticRead read(byte[] structured,byte[] text){
        return assertInstanceOf(SemanticRead.class,ClockMcpRowDecoder.decode(mcp(structured,text),ReadKind.CURRENT_SEMANTIC_FRAME,evidence(),16_384));
    }

    @Test void signedObservedActorsPassBothActualMcpRepresentationsAndRetainTheirOriginalSign() throws Exception {
        for(int value:new int[]{Integer.MIN_VALUE,-2147418112,-2,0,1,40526,Integer.MAX_VALUE}) {
            ObjectNode frame=original();frame.put("episode_character_id",value);((ObjectNode)frame.get("played_character")).put("character_id",value);
            byte[] nativeBody=body(frame);SemanticRead result=read(nativeBody,nativeBody);
            assertEquals(value,result.semantic().actorId());assertEquals(value,result.semantic().playedActorId());
            assertEquals(NativeSemanticCodec.decode(nativeBody,16_384),result.semantic());
            byte[] canonical=StrictJson.canonical(frame,16_384);
            assertEquals(result,read(canonical,canonical),"representation roundtrip does not change identity or retained Evidence");
        }
    }

    @Test void malformedTypeOrOutOfRangeInEitherRepresentationCannotNormalizeIntoAValidActor() throws Exception {
        for(boolean played:new boolean[]{false,true})for(String token:List.of("-1","2147483648","-2147483649","4294967294","true","false","0.0","-2.0","40526.0","40526e0","\"-2\"","\"40526\"","null")) {
            ObjectNode malformed=original();ObjectNode target=played?(ObjectNode)malformed.get("played_character"):malformed;
            target.putRawValue(played?"character_id":"episode_character_id",new RawValue(token));
            int sameValue=switch(token){case "true"->1;case "false","0.0"->0;case "-2.0","\"-2\""->-2;default->40526;};
            ObjectNode nominal=original();(played?(ObjectNode)nominal.get("played_character"):nominal).put(played?"character_id":"episode_character_id",sameValue);
            // Equal numerical values expose a lossy token conversion instead of passing only on value disagreement.
            byte[] bad=body(malformed),valid=body(nominal);
            assertThrows(ContractViolationException.class,()->read(bad,valid),"structured "+played+"="+token);
            assertThrows(ContractViolationException.class,()->read(valid,bad),"text "+played+"="+token);
        }
    }

    @Test void independentlyValidSignedRepresentationsMustStillAgreeExactly() throws Exception {
        ObjectNode negative=original();negative.put("episode_character_id",-2);((ObjectNode)negative.get("played_character")).put("character_id",-2);
        ObjectNode zero=original();zero.put("episode_character_id",0);((ObjectNode)zero.get("played_character")).put("character_id",0);
        assertThrows(ContractViolationException.class,()->read(body(negative),body(zero)));
        assertThrows(ContractViolationException.class,()->read(body(zero),body(negative)));
        assertEquals(-2,read(body(negative),body(negative)).semantic().actorId());
    }
}
