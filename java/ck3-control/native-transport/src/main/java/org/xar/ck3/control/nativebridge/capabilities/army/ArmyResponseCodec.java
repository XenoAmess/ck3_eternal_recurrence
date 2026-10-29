package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract;
import org.xar.ck3.control.warpolicy.NativeTerminationOptions;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyResponses.*;

/** Original Army producer normalization. Full raw receipts remain in the shared read archive, never in mutable domain maps. */
public final class ArmyResponseCodec {
    public static final String ACTUAL4_SHA = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private ArmyResponseCodec() { }
    public static Declarations declarations(byte[] raw, Context source) {
        ObjectNode n = parse(raw); equal(get(n, "step"), "query-declarable-wars"); yes(get(n, "accepted")); equal(get(n, "status"), "available");
        return new Declarations(BattleResponseCodec.frame(n, source), DeclarationContract.normalize(get(n, "declarable_wars")));
    }
    public static DefaultRaise defaultRaise(byte[] raw, Context source) {
        ObjectNode n = parse(raw); equal(get(n, "step"), "query-player-default-raise-v1"); yes(get(n, "accepted")); yes(get(n, "read_only")); equal(get(n, "status"), "completed"); Frame frame = BattleResponseCodec.frame(n, source);
        ObjectNode v = object(get(n, "player_default_raise")); String version = build(v); equal(get(v, "schema"), version.equals("1.20.0.4") ? "ck3_12004_player_default_raise_v1" : "ck3_12003_player_default_raise_v1");
        equal(get(v, "actor_character_id"), source.playerId()); equal(get(v, "snapshot_revision"), source.nativeRevision()); equal(get(v, "date_raw"), source.dateRaw()); String status = text(get(v, "status")); require(Set.of("available", "partial", "unavailable", "requires_paused", "invalid_request").contains(status), "default raise status");
        boolean ready = bool(get(v, "default_raise_legality_ready")); Field<Boolean> legal = nullable(v, "native_default_raise_legal", ArmyJson::bool); Field<PositiveId> province = nullable(v, "default_raise_province_id", ArmyJson::id); String failure = nonempty(get(v, "failure"));
        require(ready == (legal instanceof Present<?>) && ready == status.equals("available") && (!ready || province instanceof Present<?> && failure.equals("none")), "default raise native legality readiness mismatch");
        Availability reserve = availability(get(v, "unraised_troops_status")); boolean reserveReady = bool(get(v, "unraised_troops_ready")); Field<Integer> soldiers = nullable(v, "unraised_soldiers", ArmyJson::nonnegative); String reserveFailure = nonempty(get(v, "unraised_troops_failure"));
        require(reserve == Availability.AVAILABLE || reserve == Availability.UNAVAILABLE, "unraised status"); require(reserveReady == (reserve == Availability.AVAILABLE) && reserveReady == (soldiers instanceof Present<?>) && (reserveReady ? reserveFailure.equals("none") : !reserveFailure.equals("none")), "all-unraised reserve observation mismatch"); require(i32(get(v, "unraised_troops_scale")) == 1, "unraised soldier scale"); equal(get(v, "unraised_troops_scope"), "native_all_actor_categories");
        return new DefaultRaise(frame, id(v.get("actor_character_id")), status, ready, legal, province, failure, reserve, reserveReady, soldiers, reserveFailure);
    }
    public static Truce truce(byte[] raw, Context source, ArmyRequests.Truce request) {
        ObjectNode n = closed(parse(raw), "step", "accepted", "query_sequence", "snapshot_revision", "raiktor_actual_truce_expiry", "backend_id", "read_only", "date_raw"); equal(n.get("step"), "query-raiktor-actual-truce-expiry-v1-" + request.toward().value()); yes(n.get("accepted")); yes(n.get("read_only")); equal(n.get("backend_id"), "native-headless"); Frame frame = BattleResponseCodec.frame(n, source);
        ObjectNode v = closed(n.get("raiktor_actual_truce_expiry"), "schema_version", "backend_id", "ck3_build", "executable_sha256", "status", "snapshot_revision", "current_date_raw", "owner_character_id", "toward_character_id", "native_has_truce", "actual_expiry_observable", "expiry_date_raw", "same_frame_stable", "readiness", "temporal_semantics", "unavailable_reason");
        require(i32(v.get("schema_version")) == 1, "truce schema version"); equal(v.get("backend_id"), "ck3-1.20.0.4-native-player-truce-expiry-v1"); equal(v.get("ck3_build"), "1.20.0.4"); require(text(v.get("executable_sha256")).equalsIgnoreCase(ACTUAL4_SHA), "truce actual4 executable binding"); equal(v.get("snapshot_revision"), source.nativeRevision()); equal(v.get("current_date_raw"), source.dateRaw()); equal(v.get("owner_character_id"), source.playerId()); require(id(v.get("toward_character_id")).equals(request.toward()), "directional truce target mismatch"); equal(v.get("temporal_semantics"), "post_application_persisted_relation_state");
        boolean has = bool(v.get("native_has_truce")), observable = bool(v.get("actual_expiry_observable")), stable = bool(v.get("same_frame_stable")), ready = bool(v.get("readiness")); Field<Integer> expiry = nullable(v, "expiry_date_raw", ArmyJson::i32); Field<String> reason = nullable(v, "unavailable_reason", ArmyJson::text); String status = text(v.get("status"));
        if (status.equals("available")) require(has && observable && stable && ready && expiry instanceof Present<Integer> present && present.value() > frame.dateRaw() && reason instanceof NullValue<?>, "available persisted truce incomplete");
        else require(status.equals("no_truce") && !has && !observable && stable && !ready && expiry instanceof NullValue<?> && reason.equals(new Present<>("native_has_truce_false")), "absent persisted truce must retain the successful negative observation");
        return new Truce(frame, source.playerId().intValueExact(), request.toward(), has, observable, expiry, stable, ready, reason);
    }
    public static Gathering gathering(byte[] raw, String expectedStep) {
        var actual=ArmyGatheringCodec.decode(raw,expectedStep);
        return new Gathering(actual.accepted(),SamplingStatus.valueOf(actual.status().name()),actual.enabled(),actual.busy(),actual.clearCompleted(),
                new UInt64(actual.epoch()),new UInt64(actual.activeCaptures()),new UInt64(actual.retained()),new UInt64(actual.qualified()),
                SamplingReadiness.valueOf(actual.readiness().name()));
    }
    public static NativeTerminationOptions.NativePacket terminationOptions(byte[] raw, Context source, ArmyRequests.War request) {
        ObjectNode n = parse(raw); equal(get(n, "step"), "query-war-termination-options-" + request.war().value()); yes(get(n, "accepted")); if (n.has("snapshot_revision")) equal(n.get("snapshot_revision"), source.nativeRevision());
        return NativeTerminationOptions.normalizeNativePacket(get(n, "war_termination_options"), request.war().value());
    }
    /** Exact build matching is shared by all .3/.4 native observation DTOs. It grants no permission by itself. */
    static String build(ObjectNode n) {
        String version = text(get(n, "game_version")), sha = text(get(n, "executable_sha256"));
        require(version.equals("1.20.0.4") && sha.equalsIgnoreCase(ACTUAL4_SHA) || version.equals("1.20.0.3") && sha.equalsIgnoreCase("94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"), "native observation has mixed/unknown version and executable"); return version;
    }
}
