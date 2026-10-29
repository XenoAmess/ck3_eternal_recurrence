package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Optional;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyDeclarationCollection.Scope;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyDeclarationCollection.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Strict four-state original Python contract, with lossless v3 public integer projection at the service boundary. */
public final class ArmyDeclarationCollectionCodec {
    private ArmyDeclarationCollectionCodec() { }
    public static Binding binding(Complete actual) {
        ObjectNode n = object(OpportunityJson.toNode(actual.semantic()));
        ObjectNode played = object(get(n, "played_character")), diagnostic = object(get(n, "diagnostics"));
        Binding result = new Binding(text(get(n,"snapshot_id")),integer(get(n,"revision")),integer(get(n,"native_revision")),
                text(get(n,"episode_run_id")),i32(get(n,"date_raw")),bool(get(n,"paused")),bool(get(n,"map_ready")),
                i32(get(played,"character_id")),i64(get(diagnostic,"bridge_pid")),integer(get(diagnostic,"connection_generation")));
        var frame = actual.identity().frame();
        require(result.snapshotId().equals(frame.snapshotId()) && result.publicRevision().equals(frame.revision())
                && result.nativeRevision().equals(frame.identity().nativeRevision()) && result.episode().equals(frame.episodeRunId())
                && BigInteger.valueOf(result.dateRaw()).equals(frame.identity().dateRaw())
                && BigInteger.valueOf(result.playerCharacterId()).equals(frame.identity().player())
                && result.bridgePid() == actual.identity().game().pid() && result.connectionGeneration().equals(actual.connectionGeneration())
                && actual.source().machineId().equals(actual.identity().machineId()), "collection binding differs from its complete current Driver source");
        return result;
    }
    public static Obj encode(Result result) {
        ObjectNode n = empty().put("schema",SCHEMA).put("request_id",result.scope().requestId()).put("status",result.status().wire())
                .put("native_resubmitted",false).put("cache_restored",result instanceof Available);
        n.set("original_binding",node(result.scope().originalBinding())); n.set("current_binding",node(result.scope().currentBinding()));
        if (result instanceof Stale value) value.nativeResultFrame().ifPresent(frame -> n.set("native_result_frame",parse(frame.bytes())));
        else if (result instanceof NativeRejected value) n.set("native_result_frame",parse(value.nativeResultFrame().bytes()));
        else if (result instanceof Available value) {
            n.set("native_result_frame",parse(value.nativeResultFrame().bytes()));
            ObjectNode published = object(OpportunityJson.toNode(value.declarations().normalizedResult())).deepCopy();
            published.put("backend_id","native-headless"); n.set("declaration_result",published);
        }
        return immutable(n);
    }
    public static Result decode(Obj encoded) {
        ObjectNode n = object(OpportunityJson.toNode(encoded));
        Status status = Status.fromWire(text(get(n,"status")));
        String optional = status == Status.STALE ? "native_result_frame" : "";
        String required = "schema request_id status original_binding current_binding native_resubmitted cache_restored";
        if (status == Status.NATIVE_REJECTED || status == Status.AVAILABLE) required += " native_result_frame";
        if (status == Status.AVAILABLE) required += " declaration_result";
        shape(n,required,optional); equal(get(n,"schema"),SCHEMA);
        require(!bool(get(n,"native_resubmitted")) && bool(get(n,"cache_restored")) == (status == Status.AVAILABLE), "collection status cannot invent resubmission or cache publication");
        Scope scope = new Scope(text(get(n,"request_id")),binding(object(get(n,"original_binding"))),binding(object(get(n,"current_binding"))));
        Result result = switch (status) {
            case PENDING -> new Pending(scope);
            case STALE -> new Stale(scope,n.has("native_result_frame")?Optional.of(new RawJson(bytes(get(n,"native_result_frame")))):Optional.empty());
            case NATIVE_REJECTED -> new NativeRejected(scope,new RawJson(bytes(get(n,"native_result_frame"))));
            case AVAILABLE -> {
                RawJson frame = new RawJson(bytes(get(n,"native_result_frame")));
                var original = declarations(object(get(parse(frame.bytes()),"result")));
                ObjectNode published = object(OpportunityJson.toNode(original.normalizedResult())).deepCopy(); published.put("backend_id","native-headless");
                require(published.equals(object(get(n,"declaration_result"))),"declaration_result differs from original normalization and the actual backend projection");
                yield new Available(scope,frame,original);
            }
        };
        require(encode(result).equals(encoded), "noncanonical collection field or integer domain");
        return result;
    }
    static boolean requireFrame(String requestId, RawJson frame) {
        try {
            var decoded = NativeWire.decode(NativeWire.packet(frame.bytes()));
            require(decoded instanceof NativeWire.CommandResult, "late result is not an original command_result frame");
            var result = (NativeWire.CommandResult) decoded;
            require(result.requestId().equals(requestId), "late declaration result request identity mismatch");
            return result.nativeOk();
        } catch (IOException invalid) { throw new IllegalArgumentException("malformed original late declaration frame",invalid); }
    }
    static void requireDeclarations(Scope scope, RawJson frame, ArmyWarReadCodec.Declarations expected) {
        ObjectNode raw = object(get(parse(frame.bytes()),"result"));
        if (raw.has("snapshot_revision")) equal(raw.get("snapshot_revision"),scope.originalBinding().nativeRevision());
        require(declarations(raw).equals(expected), "published declarations differ from the complete original late result");
    }
    private static ArmyWarReadCodec.Declarations declarations(ObjectNode raw) {
        ObjectNode n = raw.deepCopy(); equal(get(n,"step"),"query-declarable-wars"); yes(get(n,"accepted")); equal(get(n,"status"),"available");
        UInt64 sequence = positive(get(n,"query_sequence"));
        var choices = DeclarationContract.normalize(get(n,"declarable_wars")); n.set("declarable_wars",DeclarationContract.encode(choices));
        return new ArmyWarReadCodec.Declarations(choices,sequence,immutable(n));
    }
    private static Binding binding(ObjectNode n) {
        shape(n,"snapshot_id revision native_revision episode_run_id date_raw paused map_ready player_character_id bridge_pid connection_generation","");
        return new Binding(text(get(n,"snapshot_id")),integer(get(n,"revision")),integer(get(n,"native_revision")),text(get(n,"episode_run_id")),
                i32(get(n,"date_raw")),bool(get(n,"paused")),bool(get(n,"map_ready")),i32(get(n,"player_character_id")),i64(get(n,"bridge_pid")),integer(get(n,"connection_generation")));
    }
    private static ObjectNode node(Binding b) {
        return empty().put("snapshot_id",b.snapshotId()).put("revision",b.publicRevision()).put("native_revision",b.nativeRevision())
                .put("episode_run_id",b.episode()).put("date_raw",b.dateRaw()).put("paused",b.paused()).put("map_ready",b.mapReady())
                .put("player_character_id",b.playerCharacterId()).put("bridge_pid",b.bridgePid()).put("connection_generation",b.connectionGeneration());
    }
    private static Obj immutable(ObjectNode n) { return DriverJson.object(bytes(n),DriverJson.MAX_NATIVE_BYTES); }
    private static void shape(ObjectNode n, String required, String optional) {
        var mandatory = new java.util.HashSet<>(java.util.List.of(required.split(" ")));
        var allowed = new java.util.HashSet<>(mandatory);
        if (!optional.isEmpty()) allowed.addAll(java.util.List.of(optional.split(" ")));
        require(names(n).containsAll(mandatory) && allowed.containsAll(names(n)), "wrong, missing or invented declaration collection fields");
    }
}
