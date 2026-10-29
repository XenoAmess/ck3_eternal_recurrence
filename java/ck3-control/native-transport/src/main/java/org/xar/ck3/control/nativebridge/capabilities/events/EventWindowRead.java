package org.xar.ck3.control.nativebridge.capabilities.events;

import static org.xar.ck3.control.nativebridge.capabilities.events.EventWindowCodec.*;
import static org.xar.ck3.control.nativebridge.capabilities.events.EventWindowModels.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.planning.events.EventPolicies;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** The single native collector contract used by CORE, event policies and the public query facade. */
public final class EventWindowRead {
    public static final String STEP="query-current-event-window-context-v1";
    public static final String CAPABILITY="game.command.query-current-event-window-context-v1";
    private static final List<String> MIRRORS=List.of("schema","schema_version","date_raw","current_event_instance_id","window_match_count","unavailable_reason","event_definition_key","calculated_event_id","runtime_stats_ordinal","root_scope","saved_scopes","options","readiness","provenance");
    private EventWindowRead() { }
    /** Root verifies current build/capability, actual collector authority and lifecycle under its writer lock. */
    @FunctionalInterface public interface Admission { void verify(PlanningReadRequest request); }
    public static ReadContract<EventPolicies.ReadPublication> contract(ExactRef source, Admission admission) {
        Objects.requireNonNull(source); Objects.requireNonNull(admission);
        return new ReadContract<>("native/event-window-v1",new OperationKey(STEP),Optional.of(CAPABILITY),CAPABILITY,
            ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,
            (request,requestId)->{ verifySource(source); admission.verify(request); int event=activeEvent(request);
                return new NativeRequest(STEP,Optional.of(CAPABILITY),raw(JsonNodeFactory.instance.objectNode().put("event_instance_id",event))); },
            EventWindowRead::decode,EventWindowRead::decode);
    }
    /** Source snapshot is the complete semantic snapshot; no separately supplied event ID can override it. */
    public static int activeEvent(PlanningReadRequest request) {
        need(request.operation().value().equals(STEP),"event collector operation differs");
        ObjectNode snapshot=snapshot(request); var before=request.before().frame();
        yes(snapshot,"paused");
        need(text(snapshot,"snapshot_id").equals(before.snapshotId()),"event collector snapshot ID differs");
        need(number(snapshot,"revision",BigInteger.ZERO,BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE)).equals(before.revision()),"event collector public revision differs");
        need(number(snapshot,"native_revision",BigInteger.ONE,BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE)).equals(before.identity().nativeRevision()),"event collector native revision differs");
        need(BigInteger.valueOf(i32(snapshot,"date_raw")).equals(before.identity().dateRaw()),"event collector date differs");
        return integer(field(snapshot,"active_event"),"instance_id",1,Integer.MAX_VALUE);
    }
    private static EventPolicies.ReadPublication decode(PlanningReadReceipt receipt) {
        need(receipt.contractId().equals("native/event-window-v1"),"event original belongs to another installed read contract");
        for(var guard:List.of(receipt.before(),receipt.after()))
            need(guard.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP && guard.paused() && guard.mapReady() && guard.playerAlive(),"event original is outside the paused living-map read scope");
        var before=receipt.request().before().frame();int event=activeEvent(receipt.request());
        Binding binding=new Binding(connectedBuild(receipt),before.identity().nativeRevision(),before.identity().dateRaw().intValueExact(),event);
        ObjectNode result=originalResult(receipt.original(),receipt.requestId(),binding);
        exact(result,"step accepted status query_sequence snapshot_revision current_event_window_context backend_id");
        eq(result,"step",STEP); yes(result,"accepted"); eq(result,"backend_id","native-headless");
        need(number(result,"snapshot_revision",BigInteger.ONE,BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE)).equals(before.identity().nativeRevision()),"event envelope native revision differs");
        number(result,"query_sequence",BigInteger.ONE,BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE));
        Context context=EventWindowCodec.decode(raw(field(result,"current_event_window_context")),binding);
        eq(result,"status",context instanceof Available?"available":"unavailable");
        ObjectNode normalized=parse(EventWindowCodec.encode(context)); ObjectNode published=result.deepCopy();
        for (String key:MIRRORS) published.set(key,normalized.get(key).deepCopy());
        published.put("current_event_window_context_ready",context.readiness().optionPresentation());
        published.put("current_event_effect_indicators_ready",context.readiness().effectIndicators());
        published.put("queried_snapshot_id",before.snapshotId()).put("queried_revision",before.revision()).put("queried_native_revision",before.identity().nativeRevision());
        published.put("scope","exact-current-event-window");
        ObjectNode source=published.putObject("source").put("snapshot_id",before.snapshotId()).put("revision",before.revision()).put("native_revision",before.identity().nativeRevision()).put("date_raw",before.identity().dateRaw()).put("paused",true);
        JsonNode backend=snapshot(receipt.request()).get("backend_id"); if (backend==null) source.putNull("backend_id"); else { need(backend.isTextual() || backend.isNull(),"semantic backend must be string/null"); source.set("backend_id",backend.deepCopy()); }
        published.putObject("binding").put("snapshot_id",before.snapshotId()).put("revision",before.revision()).put("native_revision",before.identity().nativeRevision()).put("date_raw",before.identity().dateRaw()).put("expected_revision",before.revision()).put("event_instance_id",event);
        return new EventPolicies.ReadPublication(OpportunityJson.object(OpportunityJson.parse(raw(published).bytes()),"validated event publication"),Optional.empty());
    }
    private static Build connectedBuild(PlanningReadReceipt receipt) {
        try {
            byte[] before=original(receipt.before().binding().capabilityEvidence());
            byte[] after=original(receipt.after().binding().capabilityEvidence());
            need(Arrays.equals(before,after),"event query crossed the original connected hello");
            return connectedBuild(before,receipt.request().before().game().pid(),receipt.before().binding().connectionGeneration());
        } catch (IOException failure) { throw new IllegalArgumentException("event original hello unavailable",failure); }
    }
    /** Pure boundary validation; these bytes do not mint a live Root lease or option submission permission. */
    static Build connectedBuild(byte[] packet,long gamePid,BigInteger connectionGeneration) {
        try {
            var frame=NativeWire.decode(packet);
            need(frame instanceof NativeWire.Hello,"event guard must retain actual native hello"); var hello=(NativeWire.Hello)frame;
            need(hello.pid()==gamePid && hello.connectionGeneration().equals(connectionGeneration) && hello.buildMatch() && hello.adapterStatus().equals("ready") && hello.capabilities().contains(CAPABILITY),"event original hello Game/session/capability differs");
            for (Build build:Build.values()) if (build.sha256().equalsIgnoreCase(hello.gameSha256())) {
                need(hello.adapterId().equals("ck3-"+build.version()+"-msvc-x64"),"event adapter/executable version differs"); return build;
            }
            throw new IllegalArgumentException("event connected executable is unknown");
        } catch (IOException failure) { throw new IllegalArgumentException("event original hello unavailable",failure); }
    }
    /** Match the actual outbound query, complete return packet, payload, and exact result token before interpreting presentation. */
    static ObjectNode originalResult(NativeActionPort.AckReceived ack,String requestId,Binding binding) {
        try {
            need(ack.nativeOk() && ack.requestId().equals(requestId),"event original ACK identity/status differs");
            var frame=NativeWire.decode(ack.originalPacket());
            need(frame instanceof NativeWire.CommandResult,"event original packet is not a command result");
            var returned=(NativeWire.CommandResult)frame;
            need(returned.nativeOk() && returned.requestId().equals(requestId)
                    && Arrays.equals(returned.payload().value(),ack.originalFrame().bytes()),"event original packet/payload/identity differs");
            need(returned.result().presence()==NativeWire.Presence.VALUE && returned.result().token().isPresent()
                    && ack.originalResultToken().isPresent()
                    && Arrays.equals(returned.result().token().orElseThrow().value(),ack.originalResultToken().orElseThrow().bytes()),"event original result token differs from its actual packet");
            var outbound=ack.outbound().orElseThrow(()->new IllegalArgumentException("event original outbound query is unavailable"));
            var sent=NativeWire.decodeExecuteRequest(outbound.originalPacket());
            need(sent.requestId().equals(requestId) && sent.step().equals(STEP)
                    && sent.expectedRevision().filter(binding.nativeRevision()::equals).isPresent(),"event actual outbound query/expected revision differs");
            ObjectNode fields=parse(new RawJson(sent.normalizedAdditionalFields().value()));exact(fields,"event_instance_id");
            need(integer(fields,"event_instance_id",1,Integer.MAX_VALUE)==binding.eventInstanceId(),"event actual outbound instance differs");
            return parse(ack.originalResultToken().orElseThrow());
        } catch(IOException failure) {throw new IllegalArgumentException("event original wire is unavailable",failure);}
    }
    private static byte[] original(ExactRef ref) throws IOException {
        need(ref.bytes()>0 && ref.bytes()<=NativeWire.MAXIMUM_FRAME_BYTES+4L,"bounded actual event source required");
        var witness=SharedSourceFiles.observe(Path.of(ref.path())); need(witness.source().bytes()==ref.bytes() && witness.source().sha256().equals(ref.sha256()),"event source bytes/SHA changed");
        byte[] bytes=Files.readAllBytes(Path.of(ref.path()));
        try { need(bytes.length==ref.bytes() && HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)).equals(ref.sha256()),"event source changed while reading"); }
        catch (NoSuchAlgorithmException failure) { throw new IllegalStateException(failure); }
        SharedSourceFiles.assertUnchanged(witness); return bytes;
    }
    private static void verifySource(ExactRef ref) { try { original(ref); } catch (IOException failure) { throw new IllegalArgumentException("event collector source unavailable",failure); } }
    private static ObjectNode snapshot(PlanningReadRequest request) { return parse(new RawJson(OpportunityJson.encode(request.arguments()))); }
    static RawJson raw(JsonNode node) { return new RawJson(node.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8)); }
}
