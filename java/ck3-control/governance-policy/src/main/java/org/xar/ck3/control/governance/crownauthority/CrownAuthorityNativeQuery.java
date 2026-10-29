package org.xar.ck3.control.governance.crownauthority;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeWire.Envelope;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeWire.Source;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.Currency;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.Readback;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.SourceFrame;

/** Same-query normalizer. The installed read coordinator must supply its actual request and before/after frames. */
public final class CrownAuthorityNativeQuery {
    private CrownAuthorityNativeQuery() { }
    public record Actor(BigInteger characterId,boolean alive,String canonicalOriginal) {
        public Actor {
            Objects.requireNonNull(characterId);StrictJson.require(characterId.signum()>0,"positive played actor required");
            ObjectNode original=object(StrictJson.parse(canonicalOriginal.getBytes(StandardCharsets.UTF_8)));
            StrictJson.require(number(original,"character_id").equals(characterId)&&bool(original,"alive")==alive,
                    "played character original differs from typed identity");
            canonicalOriginal=new String(StrictJson.canonical(original),StandardCharsets.UTF_8);
        }
        public static Actor fromOriginal(JsonNode actual) {
            ObjectNode original=object(actual);
            return new Actor(number(original,"character_id"),bool(original,"alive"),
                    new String(StrictJson.canonical(original),StandardCharsets.UTF_8));
        }
    }
    public record Snapshot(Source source,Optional<String> snapshotId,BigInteger publicRevision,BigInteger nativeRevision,
            BigInteger dateRaw,Actor playedCharacter,boolean paused,boolean mapReady) {
        public Snapshot {
            Objects.requireNonNull(source);snapshotId=Objects.requireNonNull(snapshotId);snapshotId.ifPresent(StrictJson::text);
            for(BigInteger value:java.util.List.of(publicRevision,nativeRevision))StrictJson.require(value.signum()>0,"positive source revision required");
            Objects.requireNonNull(dateRaw);Objects.requireNonNull(playedCharacter);
        }
    }
    public record RequestContext(String requestId,BigInteger expectedPublicRevision,boolean privateLawEnabled,Snapshot before) {
        public RequestContext {
            StrictJson.text(requestId);Objects.requireNonNull(before);Objects.requireNonNull(expectedPublicRevision);
            StrictJson.require(expectedPublicRevision.signum()>0&&expectedPublicRevision.equals(before.publicRevision()),
                    "public expected revision differs from actual query before frame");
        }
    }
    /** Called by the original successful READ callback, after ordinary source/custody/ACK checks. */
    public static Readback onReturned(RequestContext request,Envelope original,Snapshot after) {
        Objects.requireNonNull(request);Objects.requireNonNull(original);Objects.requireNonNull(after);
        Snapshot before=request.before();
        StrictJson.require(request.privateLawEnabled()&&before.paused()&&before.mapReady()&&before.playedCharacter().alive(),
                "private crown query requires its actual enabled paused map actor");
        StrictJson.require(original.payload() instanceof CrownAuthorityNativeWire.Query,"native crown query result required");
        StrictJson.require(original.requestId().equals(request.requestId()),"same original native request_id required");
        StrictJson.require(sameSource(before.source(),original.source())&&sameSource(before.source(),after.source()),
                "native law source differs from original request source");
        StrictJson.require(after.paused()&&after.mapReady()&&after.dateRaw().equals(before.dateRaw())
                &&after.playedCharacter().equals(before.playedCharacter()),"native law callback crossed played actor/date frame");
        var value=((CrownAuthorityNativeWire.Query)original.payload()).observation();
        var frame=value.frame();var fields=value.fields();
        StrictJson.require(fields.available()&&fields.paused()&&fields.groupKey().equals("crown_authority")
                &&frame.snapshotRevision().equals(before.nativeRevision())&&frame.dateRaw().equals(before.dateRaw())
                &&frame.playerCharacterId().equals(before.playedCharacter().characterId()),
                "native law observation differs from same request before frame");
        SourceFrame source=new SourceFrame(frame.snapshotRevision(),frame.nativeSnapshotRevision(),frame.proofEpoch(),
                frame.dateRaw(),frame.playerCharacterId(),before.source().gameVersion(),before.source().executableSha256(),
                before.snapshotId().orElse(null),before.publicRevision(),before.nativeRevision());
        return new Readback(CrownAuthorityPolicy.READ_SCHEMA,fields.available(),fields.paused(),fields.groupKey(),
                fields.activeLawKey(),fields.candidates(),fields.resources(),fields.titleSuccessors(),source,true,false);
    }
    /** Existing typed Crown consumer input. Neither frame DATA nor the selector grants an action or Root permission. */
    public static CrownAuthorityCodec.Request consumerRequest(RequestContext request,Envelope original,Snapshot after,
            Map<Currency,BigInteger> reservesRaw) {
        return new CrownAuthorityCodec.Request(onReturned(request,original,after),reservesRaw);
    }
    public static byte[] encodeContext(RequestContext value) {
        ObjectNode row=StrictJson.object();row.put("request_id",value.requestId());
        row.put("expected_public_revision",value.expectedPublicRevision());row.put("private_law_enabled",value.privateLawEnabled());
        row.set("before",write(value.before()));return StrictJson.canonical(row);
    }
    public static RequestContext decodeContext(byte[] encoded) {
        ObjectNode row=StrictJson.object(StrictJson.parse(encoded),Set.of("request_id","expected_public_revision","private_law_enabled","before"));
        return new RequestContext(text(row,"request_id"),number(row,"expected_public_revision"),
                bool(row,"private_law_enabled"),read(row.get("before")));
    }
    public static byte[] encodeSnapshot(Snapshot value){return StrictJson.canonical(write(value));}
    public static Snapshot decodeSnapshot(byte[] encoded){return read(StrictJson.parse(encoded));}
    private static Snapshot read(JsonNode value) {
        ObjectNode row=StrictJson.object(value,Set.of("source","snapshot_id","revision","native_revision","date_raw",
                "played_character","paused","map_ready"));
        ObjectNode source=StrictJson.object(row.get("source"),Set.of("game_version","executable_sha256"));
        JsonNode id=row.get("snapshot_id");StrictJson.require(id!=null,"missing explicit snapshot_id");
        return new Snapshot(new Source(text(source,"game_version"),text(source,"executable_sha256")),
                id.isNull()?Optional.empty():Optional.of(StrictJson.text(id)),number(row,"revision"),number(row,"native_revision"),
                number(row,"date_raw"),Actor.fromOriginal(row.get("played_character")),bool(row,"paused"),bool(row,"map_ready"));
    }
    private static ObjectNode write(Snapshot value) {
        ObjectNode row=StrictJson.object();ObjectNode source=row.putObject("source");
        source.put("game_version",value.source().gameVersion());source.put("executable_sha256",value.source().executableSha256());
        if(value.snapshotId().isPresent())row.put("snapshot_id",value.snapshotId().orElseThrow());else row.putNull("snapshot_id");
        row.put("revision",value.publicRevision());row.put("native_revision",value.nativeRevision());row.put("date_raw",value.dateRaw());
        row.set("played_character",StrictJson.parse(value.playedCharacter().canonicalOriginal().getBytes(StandardCharsets.UTF_8)));
        row.put("paused",value.paused());row.put("map_ready",value.mapReady());return row;
    }
    private static boolean sameSource(Source left,Source right) {
        return left.gameVersion().equals(right.gameVersion())&&left.executableSha256().equalsIgnoreCase(right.executableSha256());
    }
    private static ObjectNode object(JsonNode value){StrictJson.require(value instanceof ObjectNode,"original object required");return (ObjectNode)value;}
    private static String text(ObjectNode row,String field){return StrictJson.text(row.get(field));}
    private static BigInteger number(ObjectNode row,String field){
        JsonNode value=row.get(field);StrictJson.require(value!=null&&value.isIntegralNumber(),"actual integer required: "+field);return value.bigIntegerValue();
    }
    private static boolean bool(ObjectNode row,String field){
        JsonNode value=row.get(field);StrictJson.require(value!=null&&value.isBoolean(),"actual boolean required: "+field);return value.booleanValue();
    }
}
