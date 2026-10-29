package org.xar.ck3.control.g2.common;

import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.List;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.projection.ProjectionJson;

/** Finite direct boundary checks; the default JUnit adapter executes this same real producer/engine/wire chain. */
public final class G2CommonVerification {
    private G2CommonVerification() { }
    public static void main(String[] args) {
        G2Source source=new G2Source("fixture-machine-01","2026-10-22T20:00:00Z","1.20.0.4",new ExactRef("fixture/input.json",2,"a".repeat(64)));
        int checks=0;
        for(Milestone milestone:Milestone.values()) {
            byte[] raw=utf8("{\"float\":1.2300,\"negative_zero\":-0.0,\"file_id\":\"18446744073709551615\",\"missing_distinction\":[null,[],{}]}");
            G2Request request=new G2Request("case:"+milestone,milestone,source,ProjectionJson.object(raw,8192));
            require(request.equals(G2Wire.decodeRequest(G2Wire.encodeRequest(request))),"request value roundtrip");
            G2Domain domain=new G2Domain() {
                public Milestone milestone(){return milestone;}
                public G2Response evaluate(G2Request input){return new G2Response(input.requestId(),milestone,input.source(),ProjectionJson.value(input.payload().bytes(),8192));}
            };
            G2Response response=new G2ResearchEngine(List.of(domain)).evaluate(request);
            require(response.equals(G2Wire.decodeResponse(G2Wire.encodeResponse(response))),"response value roundtrip");
            require(Arrays.equals(raw,response.result().bytes()),"raw token preservation");checks+=3;
        }
        for(String value:List.of("null","[]","{}","1.2300","-0.0","\"18446744073709551615\"")) {
            G2Response response=new G2Response("value",Milestone.M0,source,ProjectionJson.value(utf8(value),8192));
            require(response.equals(G2Wire.decodeResponse(G2Wire.encodeResponse(response))),"all JSON result kinds");checks++;
        }
        G2Request request=new G2Request("negative",Milestone.M0,source,ProjectionJson.object(utf8("{}"),8192));
        String valid=new String(G2Wire.encodeRequest(request),StandardCharsets.UTF_8);
        for(String invalid:List.of(
                valid.replace("\"schema_version\":1","\"schema_version\":true"),
                valid.replace("\"schema_version\":1","\"schema_version\":1.0"),
                valid.replace("\"schema_version\":1","\"schema_version\":\"1\""),
                valid.replace("\"bytes\":2","\"bytes\":true"),
                valid.replace("\"bytes\":2","\"bytes\":2.0"),
                valid.replace("\"bytes\":2","\"bytes\":\"2\""),
                valid.replace("\"payload\":{}","\"payload\":null"),
                valid.replace("\"payload\":{}","\"payload\":[]"),
                valid.replace("\"payload\":{}","\"payload\":{},\"extra\":true"),
                valid.replace("\"payload\":{}","\"payload\":{},\"payload\":{}"),
                valid.replace("\"source_ref\":", "\"unknown_source_ref\":"),
                valid.replace("G2-M0","G2-M8"),valid+"{}")) {
            rejected(()->G2Wire.decodeRequest(utf8(invalid)));checks++;
        }
        byte[] normal=utf8(valid),bom=new byte[normal.length+3];bom[0]=(byte)0xef;bom[1]=(byte)0xbb;bom[2]=(byte)0xbf;System.arraycopy(normal,0,bom,3,normal.length);
        rejected(()->G2Wire.decodeRequest(bom));checks++;
        rejected(()->G2Wire.decodeRequest(valid.getBytes(StandardCharsets.UTF_16LE)));checks++;
        for(G2HttpError.Code code:G2HttpError.Code.values()) {
            G2HttpError error=new G2HttpError(G2HttpError.SCHEMA,code,"bounded reason");
            require(error.equals(G2Wire.decodeError(G2Wire.encodeError(error))),"error roundtrip");checks++;
        }
        G2Domain wrong=new G2Domain() {
            public Milestone milestone(){return Milestone.M0;}
            public G2Response evaluate(G2Request input){return new G2Response("different",Milestone.M0,input.source(),ProjectionJson.value(utf8("null"),8192));}
        };
        rejected(()->new G2ResearchEngine(List.of(wrong)).evaluate(request));checks++;
        rejected(()->new G2ResearchEngine(List.of()).evaluate(request));checks++;
        rejected(()->new G2ResearchEngine(List.of(wrong,wrong)));checks++;
        // Exercise the envelope-above8MiB lane; its outer UTF-8/BOM validation must remain identical.
        int count=ProjectionJson.MAX_BYTES-32;byte[] large=utf8("{\"text\":\""+"x".repeat(count)+"\"}");
        G2Request largeRequest=new G2Request("large",Milestone.M0,source,ProjectionJson.object(large,ProjectionJson.MAX_BYTES));
        byte[] largeWire=G2Wire.encodeRequest(largeRequest);require(largeWire.length>ProjectionJson.MAX_BYTES,"large-envelope lane reached");
        require(largeRequest.equals(G2Wire.decodeRequest(largeWire)),"large request retained");checks++;
        byte[] largeBom=new byte[largeWire.length+3];largeBom[0]=(byte)0xef;largeBom[1]=(byte)0xbb;largeBom[2]=(byte)0xbf;System.arraycopy(largeWire,0,largeBom,3,largeWire.length);
        rejected(()->G2Wire.decodeRequest(largeBom));checks++;
        System.out.println("G2_COMMON_PASS checks="+checks);
    }
    private static byte[] utf8(String value){return value.getBytes(StandardCharsets.UTF_8);}
    private static void require(boolean condition,String message){if(!condition)throw new AssertionError(message);}
    private static void rejected(Runnable command){try{command.run();}catch(IllegalArgumentException expected){return;}throw new AssertionError("expected typed rejection");}
}
