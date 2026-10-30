package org.xar.ck3.control.application.capabilities;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertModel;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertsBoundary;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertsCodec;

/** One pure faction decoder/selection key shared by live transport and cold Driver replay.
 * Wars/backend must come from the independently loaded original before-frame. No I/O here.
 */
public final class FactionReadReplay {
    private FactionReadReplay() { }
    public record Context(ObservationIdentity before,G2Source source,String sessionId,Instant deadline,
                          RawJson activeWars,String snapshotBackendId) {
        public Context {
            Objects.requireNonNull(before);Objects.requireNonNull(source);StrictJson.text(sessionId);
            Objects.requireNonNull(deadline);Objects.requireNonNull(activeWars);StrictJson.text(snapshotBackendId);
            StrictJson.require(before.machineId().equals(source.machineId()),"faction source observation drift");
            StrictJson.require(source.exactBuild().equals("1.20.0.4"),"current exact faction source required");
            StrictJson.require(parse(activeWars.bytes()).isArray(),"original same-frame active_wars array required");
            before.frame().identity().dateRaw().intValueExact();
            org.xar.ck3.control.contracts.NativeCharacterId.of(before.frame().identity().player());
            uint64(before.frame().identity().nativeRevision(),true);
        }
        public BigInteger nativeRevision(){return before.frame().identity().nativeRevision();}
        public int dateRaw(){return before.frame().identity().dateRaw().intValueExact();}
        public int player(){return before.frame().identity().player().intValueExact();}
    }
    public record Decoded(BigInteger querySequence,FactionAlertModel.Frame frame,RawJson normalizedAlert,
                          RawJson originalResult,String originalResultSha256) implements FactionReadObservation {
        public Decoded {
            uint64(querySequence,true);Objects.requireNonNull(frame);Objects.requireNonNull(normalizedAlert);
            Objects.requireNonNull(originalResult);Objects.requireNonNull(originalResultSha256);
            StrictJson.require(digest(originalResult.bytes()).equals(originalResultSha256),"original faction result digest mismatch");
        }
    }
    public static Decoded copyOf(FactionReadObservation actual) {
        Objects.requireNonNull(actual);
        return new Decoded(actual.querySequence(),actual.frame(),actual.normalizedAlert(),actual.originalResult(),actual.originalResultSha256());
    }
    public static RawJson key(Context c,BigInteger expectedRevision) {
        selection(c,expectedRevision);var f=c.before().frame();
        ObjectNode n=StrictJson.object().put("machine_id",c.before().machineId()).put("session_id",c.sessionId())
                .put("snapshot_id",f.snapshotId()).put("public_revision",f.revision().toString()).put("native_revision",c.nativeRevision().toString())
                .put("date_raw",c.dateRaw()).put("player",c.player()).put("deadline",c.deadline().toString()).put("episode",f.episodeRunId())
                .put("observation_version",c.before().observationVersion()).put("source_observed_at_utc",c.source().observedAtUtc())
                .put("exact_build",c.source().exactBuild()).put("active_wars_sha256",digest(c.activeWars().bytes())).put("snapshot_backend_id",c.snapshotBackendId());
        n.set("game",c.before().game().toJson());n.set("source_ref",c.source().sourceRef().toJson());
        n.set("arguments",arguments(expectedRevision));return new RawJson(StrictJson.canonical(n));
    }
    public static String contractId(Context c,BigInteger expectedRevision) {
        return "player-faction-alerts-v1-"+digest(key(c,expectedRevision).bytes());
    }
    public static Decoded replayArchived(PlanningReadReceipt receipt,RawJson originalActiveWars,String snapshotBackendId) {
        var request=Objects.requireNonNull(receipt).request();
        var args=object(OpportunityJson.encode(request.arguments()),Set.of("expected_revision"));
        JsonNode value=args.get("expected_revision");
        StrictJson.require(value!=null&&value.isTextual()&&value.textValue().matches("0|[1-9][0-9]{0,19}"),"canonical faction expected revision required");
        BigInteger expected=uint64(new BigInteger(value.textValue()),false);
        return decode(new Context(request.before(),request.source(),request.sessionId(),request.deadline(),originalActiveWars,snapshotBackendId),expected,receipt);
    }
    public static Decoded decode(Context c,BigInteger expectedRevision,PlanningReadReceipt receipt) {
        Objects.requireNonNull(receipt);selection(c,expectedRevision);
        PlanningReadRequest expected=new PlanningReadRequest(c.before(),c.source(),c.sessionId(),new OperationKey(FactionAlertModel.STEP),
                OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(arguments(expectedRevision))),"faction named arguments"),c.deadline());
        StrictJson.require(receipt.request().equals(expected),"faction contract crossed complete selection or arguments");
        StrictJson.require(contractId(c,expectedRevision).equals(receipt.contractId()),"faction receipt contract crossed complete selection");
        for(var guard:List.of(receipt.before(),receipt.after()))
            StrictJson.require(guard.binding().observed().equals(c.before())&&guard.binding().source().equals(c.source())
                    &&guard.binding().sessionId().equals(c.sessionId())&&guard.paused()&&guard.mapReady()&&guard.playerAlive(),
                    "faction read requires the same actual living paused map");
        StrictJson.require(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()),"faction modal/semantic guard drift");
        StrictJson.require(receipt.original().nativeOk()&&receipt.original().originalResultToken().isPresent(),"successful original faction result token required");
        byte[] packet=receipt.original().originalPacket();
        StrictJson.require(packet.length>=5&&ByteBuffer.wrap(packet,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt()==packet.length-4
                &&Arrays.equals(Arrays.copyOfRange(packet,4,packet.length),receipt.original().originalFrame().bytes()),
                "faction original packet length/payload differs from retained full original frame");
        return decodeOriginal(c,expectedRevision,receipt.requestId(),receipt.original().originalFrame(),receipt.original().originalResultToken().orElseThrow());
    }
    public static Decoded decodeOriginal(Context c,BigInteger expectedRevision,String requestId,RawJson fullOriginal,RawJson resultToken) {
        selection(c,expectedRevision);StrictJson.text(requestId);Objects.requireNonNull(resultToken);
        ObjectNode original=object(fullOriginal.bytes(),Set.of("type","protocol_version","request_id","ok","result"));
        equal(original.get("type"),"command_result");equal(original.get("protocol_version"),BigInteger.ONE);
        equal(original.get("request_id"),requestId);JsonNode ok=original.get("ok");
        StrictJson.require(ok!=null&&ok.isBoolean()&&ok.booleanValue(),"faction true flag required");
        ObjectNode result=object(original.get("result"),FactionAlertsBoundary.CURRENT_NATIVE_RESULT_FIELDS);
        StrictJson.require(parse(resultToken.bytes()).equals(result),"faction token differs from full original frame");
        return decodeToken(c,expectedRevision,resultToken);
    }
    public static Decoded decodeToken(Context c,BigInteger expectedRevision,RawJson raw) {
        selection(c,expectedRevision);Objects.requireNonNull(raw);
        var current=FactionAlertsBoundary.normalizeCurrentNativeResult(raw.bytes(),
                new FactionAlertModel.ExpectedFrame(c.dateRaw(),c.nativeRevision(),Optional.of(FactionAlertModel.Build.CK3_12004)),c.activeWars().bytes());
        var projection=current.projection();var frame=projection.frame();
        if(frame instanceof FactionAlertModel.Available available)StrictJson.require(available.playerCharacterId()==c.player(),"native faction actor drift");
        return new Decoded(current.querySequence(),frame,new RawJson(projection.normalizedAlertJson()),raw,digest(raw.bytes()));
    }
    /** Finite public body projection. ExpectedFrame binds date/native/build; containing owner checks actor.
     * Restored numeric values remain DATA and carry no receipt/source or freshness permission.
     */
    public static RawJson encodeSemanticBody(RawJson originalNumeric,FactionAlertModel.ExpectedFrame expected) {
        Objects.requireNonNull(originalNumeric);Objects.requireNonNull(expected);
        ObjectNode body=body(parse(FactionAlertsCodec.normalize(originalNumeric.bytes(),expected).json()));
        body.put("snapshot_revision",integer(body.get("snapshot_revision")).toString());
        JsonNode counties=body.get("player_subrealm_geographic_counties_v1");
        if(counties!=null){ObjectNode component=body(counties);component.put("snapshot_revision",integer(component.get("snapshot_revision")).toString());}
        return new RawJson(StrictJson.canonical(body,FactionAlertsCodec.MAX_BYTES));
    }
    public static RawJson decodeSemanticBody(RawJson publicBody,FactionAlertModel.ExpectedFrame expected) {
        Objects.requireNonNull(publicBody);Objects.requireNonNull(expected);ObjectNode body=body(parse(publicBody.bytes()));
        body.put("snapshot_revision",decimal(body.get("snapshot_revision")));
        JsonNode counties=body.get("player_subrealm_geographic_counties_v1");
        if(counties!=null){ObjectNode component=body(counties);component.put("snapshot_revision",decimal(component.get("snapshot_revision")));}
        return new RawJson(FactionAlertsCodec.normalize(StrictJson.canonical(body,FactionAlertsCodec.MAX_BYTES),expected).json());
    }
    private static ObjectNode body(JsonNode value){StrictJson.require(value instanceof ObjectNode,"faction object required");return (ObjectNode)value;}
    private static BigInteger integer(JsonNode value){StrictJson.require(value!=null&&value.isIntegralNumber(),"exact original faction integer required");return uint64(value.bigIntegerValue(),true);}
    private static BigInteger decimal(JsonNode value){StrictJson.require(value!=null&&value.isTextual()&&value.textValue().matches("0|[1-9][0-9]{0,19}"),"canonical faction decimal64 required");return uint64(new BigInteger(value.textValue()),true);}
    private static ObjectNode arguments(BigInteger expected){return StrictJson.object().put("expected_revision",expected.toString());}
    private static void selection(Context c,BigInteger expected){Objects.requireNonNull(c);uint64(expected,false);StrictJson.require(expected.equals(c.before().frame().revision()),"faction selection revision drift");}
    private static JsonNode parse(byte[] raw){return StrictJson.parse(raw,FactionAlertsCodec.MAX_BYTES);}
    private static ObjectNode object(byte[] raw,Set<String> fields){return object(parse(raw),fields);}
    private static ObjectNode object(JsonNode raw,Set<String> fields){StrictJson.require(raw instanceof ObjectNode,"faction object required");ObjectNode n=(ObjectNode)raw;var keys=new java.util.HashSet<String>();n.fieldNames().forEachRemaining(keys::add);StrictJson.require(keys.equals(fields),"wrong, missing or extra faction envelope fields");return n;}
    private static void equal(JsonNode n,String value){StrictJson.require(n!=null&&n.isTextual()&&n.textValue().equals(value),"faction text/frame mirror drift");}
    private static void equal(JsonNode n,BigInteger value){StrictJson.require(n!=null&&n.isIntegralNumber()&&uint64(n.bigIntegerValue(),false).equals(value),"faction numeric/frame mirror drift");}
    private static BigInteger uint64(BigInteger n,boolean positive){StrictJson.require(n!=null&&n.signum()>=(positive?1:0)&&n.bitLength()<=64,"faction uint64 range");return n;}
    private static String digest(byte[] bytes){try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));}catch(NoSuchAlgorithmException impossible){throw new IllegalStateException("SHA256 unavailable",impossible);}}
}
