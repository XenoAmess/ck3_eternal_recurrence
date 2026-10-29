package org.xar.ck3.control.application.driver;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.StreamReadConstraints;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Pure replay of the real semantic producer manifest. It performs no archive, writer or native operations. */
public final class DriverObservationEvidenceReader {
    public static final String SCHEMA="xar.java-driver-observation-evidence/v1";
    private static final Set<String> FIELDS=Set.of("schema","driver_ref","driver_version","episode_epoch","transport",
            "snapshot_id","native_revision","native_state_sha256","native_packet_sha256","native_packet_bytes","observed_at",
            "public_revision","observation_version","source","original_semantic_fields");
    private static final JsonFactory TOKENS=JsonFactory.builder().streamReadConstraints(StreamReadConstraints.builder()
            .maxNestingDepth(64).maxStringLength(DriverJson.MAX_NATIVE_BYTES).maxNumberLength(1000).build()).build();
    private DriverObservationEvidenceReader() { }

    public static RawJson encode(DriverSnapshotFacts.Known known,NativeObservationPort.ObservedFrame actual,
            BigInteger publicRevision,long observationVersion,G2Source source,OpportunityJson.Obj semantic,ExactRef currentDriver) {
        Objects.requireNonNull(known);Objects.requireNonNull(actual);Objects.requireNonNull(source);Objects.requireNonNull(semantic);
        byte[] driver=known.driver().encode();
        requireExact(currentDriver,driver,"complete Driver version");
        StrictJson.require(known.stamp().game().equals(actual.session().game())
                && known.driver().session().bridgePid()==actual.session().game().pid()
                && source.machineId().equals(actual.session().machineId()),"semantic producer crossed actual Game/source");
        Map<String,OpportunityJson.Value> row=new LinkedHashMap<>();
        row.put("schema",text(SCHEMA));row.put("driver_ref",reference(currentDriver));
        row.put("driver_version",integer(known.stamp().driverVersion()));row.put("episode_epoch",integer(known.stamp().episodeEpoch()));
        row.put("transport",session(actual.session()));row.put("snapshot_id",text(actual.snapshotId()));
        row.put("native_revision",new OpportunityJson.IntegerValue(actual.nativeRevision()));
        row.put("native_state_sha256",text(DriverJson.sha256(actual.state().bytes())));
        row.put("native_packet_sha256",text(DriverJson.sha256(actual.originalPacket())));
        row.put("native_packet_bytes",integer(actual.originalPacket().length));row.put("observed_at",text(actual.observedAt().toString()));
        row.put("public_revision",new OpportunityJson.IntegerValue(publicRevision));row.put("observation_version",integer(observationVersion));
        row.put("source",source(source));row.put("original_semantic_fields",semantic);
        return RawJson.fullMaterial(DriverJson.encode(new OpportunityJson.Obj(row)));
    }

    public static DriverObservationFacts decode(ExactRef manifestReference,RawJson manifest,RawJson fullDriver,
            NativeObservationPort.ObservedFrame actual) {
        Objects.requireNonNull(fullDriver);Objects.requireNonNull(actual);
        var row=checkedManifest(manifestReference,manifest);
        requireExact(reference(row.get("driver_ref")),fullDriver.bytes(),"archived complete Driver");
        var driver=DriverStateSnapshot.decodeComplete(fullDriver.bytes());
        StrictJson.require(actual.session().equals(session(row.get("transport")))
                && actual.snapshotId().equals(string(row,"snapshot_id"))
                && actual.nativeRevision().equals(OpportunityJson.integer(row.get("native_revision"),"native_revision"))
                && actual.observedAt().equals(Instant.parse(string(row,"observed_at")))
                && DriverJson.sha256(actual.state().bytes()).equals(string(row,"native_state_sha256"))
                && DriverJson.sha256(actual.originalPacket()).equals(string(row,"native_packet_sha256"))
                && actual.originalPacket().length==longInteger(row,"native_packet_bytes",1),"archived semantic facts crossed actual native packet/session");
        G2Source source=source(row.get("source"));
        StrictJson.require(driver.session().bridgePid()==actual.session().game().pid()
                && source.machineId().equals(actual.session().machineId()),"archived Driver/source crossed actual Game");
        return new DriverObservationFacts(driver,longInteger(row,"driver_version",0),longInteger(row,"episode_epoch",0),actual.session(),
                actual.snapshotId(),actual.nativeRevision(),string(row,"native_state_sha256"),
                OpportunityJson.integer(row.get("public_revision"),"public_revision"),longInteger(row,"observation_version",1),source,
                OpportunityJson.object(row.get("original_semantic_fields"),"original_semantic_fields"),manifestReference);
    }

    /** Reconstructs the original received frame using exact token byte offsets; lexical numeric tokens are retained. */
    public static NativeObservationPort.ObservedFrame nativeFrame(ExactRef manifestReference,RawJson manifest,byte[] framedNative) {
        var row=checkedManifest(manifestReference,manifest);
        StrictJson.require(framedNative!=null && framedNative.length>=5 && framedNative.length<=DriverJson.MAX_NATIVE_BYTES+4,
                "bounded archived original native frame required");
        int length=ByteBuffer.wrap(framedNative,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt();
        StrictJson.require(length>0 && length==framedNative.length-4
                && framedNative.length==longInteger(row,"native_packet_bytes",1)
                && DriverJson.sha256(framedNative).equals(string(row,"native_packet_sha256")),"archived native framing/manifest differs");
        byte[] packet=Arrays.copyOfRange(framedNative,4,framedNative.length);
        var envelope=DriverJson.object(packet,DriverJson.MAX_NATIVE_BYTES);
        StrictJson.require("state_snapshot".equals(string(envelope,"type"))
                && BigInteger.ONE.equals(OpportunityJson.integer(envelope.get("protocol_version"),"protocol_version"))
                && string(envelope,"snapshot_id").equals(string(row,"snapshot_id"))
                && OpportunityJson.integer(envelope.get("revision"),"revision").equals(OpportunityJson.integer(row.get("native_revision"),"native_revision")),
                "archived native envelope differs from semantic manifest");
        byte[] state=stateToken(packet);
        StrictJson.require(DriverJson.sha256(state).equals(string(row,"native_state_sha256")),"original native state token differs from manifest");
        return new NativeObservationPort.ObservedFrame(session(row.get("transport")),string(row,"snapshot_id"),
                OpportunityJson.integer(row.get("native_revision"),"native_revision"),new RawJson(state),framedNative,Instant.parse(string(row,"observed_at")));
    }

    public static ExactRef currentDriverReference(ExactRef manifestReference,RawJson manifest) {
        return reference(checkedManifest(manifestReference,manifest).get("driver_ref"));
    }
    public static OpportunityJson.Obj reference(ExactRef ref) {
        Objects.requireNonNull(ref);
        return new OpportunityJson.Obj(Map.of("path",text(ref.path()),"bytes",integer(ref.bytes()),"sha256",text(ref.sha256())));
    }
    public static ExactRef reference(OpportunityJson.Value value) {
        var ref=OpportunityJson.object(value,"exact reference");
        StrictJson.require(ref.members().keySet().equals(Set.of("path","bytes","sha256")),"exact reference fields required");
        return new ExactRef(string(ref,"path"),longInteger(ref,"bytes",0),string(ref,"sha256"));
    }
    private static OpportunityJson.Obj checkedManifest(ExactRef reference,RawJson manifest) {
        Objects.requireNonNull(manifest);requireExact(reference,manifest.bytes(),"semantic facts manifest");
        var row=DriverJson.object(manifest.bytes(),DriverJson.MAX_NATIVE_BYTES);
        StrictJson.require(row.members().keySet().equals(FIELDS) && SCHEMA.equals(string(row,"schema")),"exact semantic evidence manifest contract required");
        return row;
    }
    private static void requireExact(ExactRef ref,byte[] wire,String description) {
        Objects.requireNonNull(ref);Objects.requireNonNull(wire);
        StrictJson.require(ref.bytes()==wire.length && ref.sha256().equals(DriverJson.sha256(wire)),description+" exact bytes/SHA differ");
    }
    private static OpportunityJson.Obj session(NativeObservationPort.TransportSession session) {
        return new OpportunityJson.Obj(Map.of("machine_id",text(session.machineId()),"pid",integer(session.game().pid()),
                "creation_filetime",text(new CrossJsDecimalUInt64(session.game().creationFiletime().value().toString()).decimal()),
                "connection_generation",text(new CrossJsDecimalUInt64(session.connectionGeneration().toString()).decimal()),"session_id",text(session.sessionId())));
    }
    private static NativeObservationPort.TransportSession session(OpportunityJson.Value value) {
        var row=OpportunityJson.object(value,"transport");
        StrictJson.require(row.members().keySet().equals(Set.of("machine_id","pid","creation_filetime","connection_generation","session_id")),"exact transport evidence fields required");
        var birth=new BigInteger(new CrossJsDecimalUInt64(string(row,"creation_filetime")).decimal());
        var connection=new BigInteger(new CrossJsDecimalUInt64(string(row,"connection_generation")).decimal());
        return new NativeObservationPort.TransportSession(string(row,"machine_id"),new GameGeneration(longInteger(row,"pid",1),new PythonOnlyUInt64(birth)),connection,string(row,"session_id"));
    }
    private static OpportunityJson.Obj source(G2Source source) {
        return new OpportunityJson.Obj(Map.of("machine_id",text(source.machineId()),"observed_at_utc",text(source.observedAtUtc()),
                "exact_build",text(source.exactBuild()),"source_ref",reference(source.sourceRef())));
    }
    private static G2Source source(OpportunityJson.Value value) {
        var row=OpportunityJson.object(value,"source");
        StrictJson.require(row.members().keySet().equals(Set.of("machine_id","observed_at_utc","exact_build","source_ref")),"exact source evidence fields required");
        return new G2Source(string(row,"machine_id"),string(row,"observed_at_utc"),string(row,"exact_build"),reference(row.get("source_ref")));
    }
    private static byte[] stateToken(byte[] packet) {
        try(JsonParser parser=TOKENS.createParser(packet)) {
            StrictJson.require(parser.nextToken()==JsonToken.START_OBJECT,"native envelope object required");
            while(parser.nextToken()!=JsonToken.END_OBJECT) {
                String key=parser.currentName();parser.nextToken();
                if("state".equals(key)) {
                    long start=parser.currentTokenLocation().getByteOffset();parser.skipChildren();parser.finishToken();long end=parser.currentLocation().getByteOffset();
                    StrictJson.require(start>=0 && end>start && end<=packet.length,"exact native state token byte boundaries required");
                    return Arrays.copyOfRange(packet,Math.toIntExact(start),Math.toIntExact(end));
                }
                parser.skipChildren();
            }
            throw new IllegalArgumentException("original native state token absent");
        } catch(IOException failure) { throw new IllegalArgumentException("original native state token unavailable",failure); }
    }
    private static String string(OpportunityJson.Obj row,String field) { return OpportunityJson.text(row.get(field),field); }
    private static long longInteger(OpportunityJson.Obj row,String field,long minimum) {
        long value=OpportunityJson.integer(row.get(field),field).longValueExact();StrictJson.safe(value,minimum);return value;
    }
    private static OpportunityJson.Text text(String value) { return new OpportunityJson.Text(value); }
    private static OpportunityJson.IntegerValue integer(long value) { return new OpportunityJson.IntegerValue(BigInteger.valueOf(value)); }
}
