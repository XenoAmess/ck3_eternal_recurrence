package org.xar.ck3.control.g2.common;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.core.io.JsonStringEncoder;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;

/** Exact outer schema; opaque domain payload/result bytes retain numeric tokens and missing/null/empty semantics. */
public final class G2Wire {
    public static final String REQUEST_SCHEMA="xar.g2-research-request/v1";
    public static final String RESPONSE_SCHEMA="xar.g2-research-response/v1";
    public static final String HTTP_ERROR_SCHEMA=G2HttpError.SCHEMA;
    public static final String HTTP_PATH="/v1/g2-research/evaluate";
    public static final String PRODUCER="java-quarkus-g2-research/v1";
    public static final String PRODUCER_VERSION="0.1.0";
    public static final int MAX_REQUEST_BYTES=ProjectionJson.MAX_BYTES+4096;
    public static final int MAX_RESPONSE_BYTES=ProjectionJson.MAX_BYTES+4096;
    public static final int MAX_ERROR_BYTES=4096;
    private static final JsonFactory FACTORY=JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build();
    private static final ObjectMapper JSON=new ObjectMapper(FACTORY);
    private static final Set<String> SOURCE_FIELDS=Set.of("machine_id","observed_at_utc","exact_build","source_ref");
    private G2Wire() { }
    private record Envelope(String requestId,Milestone milestone,G2Source source,ProjectionJson value) { }

    public static G2Request decodeRequest(byte[] raw) {
        Envelope row=decode(raw,true);return new G2Request(row.requestId(),row.milestone(),row.source(),row.value());
    }
    public static G2Response decodeResponse(byte[] raw) {
        Envelope row=decode(raw,false);return new G2Response(row.requestId(),row.milestone(),row.source(),row.value());
    }
    public static byte[] encodeRequest(G2Request request) {
        return encode(REQUEST_SCHEMA,request.requestId(),request.milestone(),request.source(),"payload",request.payload(),MAX_REQUEST_BYTES);
    }
    public static byte[] encodeResponse(G2Response response) {
        return encode(RESPONSE_SCHEMA,response.requestId(),response.milestone(),response.source(),"result",response.result(),MAX_RESPONSE_BYTES);
    }
    private static Envelope decode(byte[] raw,boolean request) {
        bounded(raw,request?MAX_REQUEST_BYTES:MAX_RESPONSE_BYTES);
        requireUtf8(raw);
        // ProjectionJson performs strict UTF-8, duplicate-key and complete-JSON validation without canonicalizing numbers.
        if(raw.length<=ProjectionJson.MAX_BYTES) ProjectionJson.object(raw,ProjectionJson.MAX_BYTES);
        String body=request?"payload":"result"; Set<String> wanted=Set.of("schema","schema_version","request_id","milestone","source",body);
        Set<String> seen=new HashSet<>();String schema=null,id=null;Milestone milestone=null;G2Source source=null;ProjectionJson value=null;boolean version=false;
        try(JsonParser parser=FACTORY.createParser(raw)) {
            if(parser.nextToken()!=JsonToken.START_OBJECT)throw malformed("G2 envelope object required");
            while(parser.nextToken()!=JsonToken.END_OBJECT) {
                if(parser.currentToken()!=JsonToken.FIELD_NAME)throw malformed("G2 field required");
                String field=parser.currentName();if(!wanted.contains(field)||!seen.add(field))throw malformed("exact G2 envelope fields required");
                JsonToken token=parser.nextToken();
                switch(field) {
                    case "schema" -> schema=text(parser);
                    case "schema_version" -> {
                        if(token!=JsonToken.VALUE_NUMBER_INT||!parser.getBigIntegerValue().equals(BigInteger.ONE))throw malformed("exact G2 version integer1 required");version=true;
                    }
                    case "request_id" -> id=text(parser);
                    case "milestone" -> milestone=Milestone.fromWire(text(parser));
                    case "source" -> source=source(JSON.readTree(parser));
                    default -> {
                        if(request&&token!=JsonToken.START_OBJECT)throw malformed("G2 payload object required");
                        if(token==null||(!token.isScalarValue()&&!token.isStructStart()))throw malformed("G2 body value required");
                        long start=parser.currentTokenLocation().getByteOffset();parser.skipChildren();parser.finishToken();long end=parser.currentLocation().getByteOffset();
                        if(start<0||end<start||end>raw.length||end-start>ProjectionJson.MAX_BYTES)throw malformed("G2 body span exceeds role budget");
                        byte[] bytes=Arrays.copyOfRange(raw,Math.toIntExact(start),Math.toIntExact(end));
                        value=request?ProjectionJson.object(bytes,ProjectionJson.MAX_BYTES):ProjectionJson.value(bytes,ProjectionJson.MAX_BYTES);
                    }
                }
            }
            if(parser.nextToken()!=null||!seen.equals(wanted)||!version||!(request?REQUEST_SCHEMA:RESPONSE_SCHEMA).equals(schema))throw malformed("exact versioned G2 envelope required");
            if(id==null||milestone==null||source==null||value==null)throw malformed("complete G2 envelope required");
            return new Envelope(id,milestone,source,value);
        } catch(G2Exception error) { throw error; }
        catch(IOException|IllegalArgumentException error) { throw malformed("invalid G2 envelope"); }
    }
    public static G2Source source(JsonNode value) {
        ObjectNode row=StrictJson.object(value,SOURCE_FIELDS);
        return new G2Source(StrictJson.text(row.get("machine_id")),StrictJson.text(row.get("observed_at_utc")),
            StrictJson.text(row.get("exact_build")),ExactRef.fromJson(row.get("source_ref")));
    }
    private static byte[] encode(String schema,String id,Milestone milestone,G2Source source,String body,ProjectionJson value,int maximum) {
        ByteArrayOutputStream out=new ByteArrayOutputStream();append(out,"{\"schema\":");quote(out,schema);
        append(out,",\"schema_version\":1,\"request_id\":");quote(out,id);append(out,",\"milestone\":");quote(out,milestone.wire());
        append(out,",\"source\":");out.writeBytes(sourceBytes(source));append(out,",\""+body+"\":");out.writeBytes(value.bytes());append(out,"}");
        byte[] raw=out.toByteArray();bounded(raw,maximum);return raw;
    }
    public static byte[] sourceBytes(G2Source source) {
        ObjectNode row=StrictJson.object();row.put("machine_id",source.machineId());row.put("observed_at_utc",source.observedAtUtc());
        row.put("exact_build",source.exactBuild());row.set("source_ref",source.sourceRef().toJson());
        try{return JSON.writeValueAsBytes(row);}catch(IOException error){throw new G2Exception(G2HttpError.Code.INTERNAL_FAILURE,"G2 source encoding failed");}
    }
    public static byte[] encodeError(G2HttpError error) {
        ByteArrayOutputStream out=new ByteArrayOutputStream();append(out,"{\"schema\":");quote(out,error.schema());append(out,",\"code\":");quote(out,error.code().name());
        append(out,",\"message\":");quote(out,error.message());append(out,"}");byte[] result=out.toByteArray();bounded(result,MAX_ERROR_BYTES);return result;
    }
    public static G2HttpError decodeError(byte[] raw) {
        bounded(raw,MAX_ERROR_BYTES);requireUtf8(raw);ProjectionJson.object(raw,MAX_ERROR_BYTES);
        try { ObjectNode row=StrictJson.object(JSON.readTree(raw),Set.of("schema","code","message"));
            return new G2HttpError(StrictJson.text(row.get("schema")),G2HttpError.Code.valueOf(StrictJson.text(row.get("code"))),StrictJson.text(row.get("message")));
        }catch(IOException|IllegalArgumentException error){throw malformed("invalid G2 HTTP error");}
    }
    public static G2HttpError decodeHttpError(byte[] raw) { return decodeError(raw); }
    private static String text(JsonParser parser)throws IOException {
        if(parser.currentToken()!=JsonToken.VALUE_STRING)throw malformed("G2 textual field required");return parser.getText();
    }
    /** A body is the original JSON token, because envelope decoding extracts precisely that token span. */
    static void requireBodyToken(ProjectionJson value) {
        byte[] raw=value.bytes();
        if(jsonWhitespace(raw[0])||jsonWhitespace(raw[raw.length-1]))
            throw malformed("G2 body must start and end at its JSON token; surrounding whitespace rejected");
    }
    private static boolean jsonWhitespace(byte value) { return value==' '||value=='\t'||value=='\r'||value=='\n'; }
    private static void bounded(byte[] raw,int maximum) {
        if(raw==null||raw.length==0)throw malformed("nonempty G2 envelope required");
        if(raw.length>maximum)throw new G2Exception(G2HttpError.Code.PAYLOAD_TOO_LARGE,"G2 envelope exceeds role budget");
    }
    private static G2Exception malformed(String message) { return new G2Exception(G2HttpError.Code.MALFORMED_REQUEST,message); }
    private static void requireUtf8(byte[] raw) {
        if(raw.length>=3&&raw[0]==(byte)0xef&&raw[1]==(byte)0xbb&&raw[2]==(byte)0xbf)throw malformed("G2 UTF-8 BOM rejected");
        for(byte value:raw)if(value==0)throw malformed("G2 raw NUL rejected");
        try { StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)); }
        catch(CharacterCodingException error){throw malformed("G2 invalid UTF-8 rejected");}
    }
    private static void append(ByteArrayOutputStream out,String text) { out.writeBytes(text.getBytes(StandardCharsets.UTF_8)); }
    private static void quote(ByteArrayOutputStream out,String value) { append(out,"\"");out.writeBytes(JsonStringEncoder.getInstance().quoteAsUTF8(value));append(out,"\""); }
}
