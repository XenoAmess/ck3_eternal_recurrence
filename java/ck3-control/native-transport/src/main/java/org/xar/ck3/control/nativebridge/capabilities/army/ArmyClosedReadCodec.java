package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Locale;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyClosedReads.*;

/** Closed original-producer schemas. Raw numeric Native evidence and public decimal64 encoding are distinct. */
public final class ArmyClosedReadCodec {
    private ArmyClosedReadCodec() { }
    public static Observation decode(ArmyCalls.Call call, Context context, PlanningReadReceipt receipt) {
        ArmyNativeReadEvidence.result(context, receipt);
        return decodeToken(call, context, receipt.original().originalResultToken().orElseThrow().bytes());
    }
    /** Pure codec entry, also used by producer fixtures; it never grants read or submission authority. */
    public static Observation decodeToken(ArmyCalls.Call call, Context context, byte[] raw) {
        call.revision().requireCurrent(context.before().frame().revision());
        return switch (call.method()) {
            case QUERY_PLAYER_DEFAULT_RAISE_V1 -> defaultRaise(raw, context);
            case QUERY_PLAYER_TRUCE_EXPIRY_V1 -> truce(raw, context, (ArmyCalls.Truce) call);
            case QUERY_ARMY_GATHERING_RESEARCH_SAMPLING_V1 -> new Gathering(ArmyResponseCodec.gathering(raw, "query-army-gathering-research-sampling-v1"));
            default -> throw new IllegalArgumentException("Army read producer is not migrated by this decoder");
        };
    }
    private static QueryFrame queryFrame(ObjectNode result, Context context) {
        equal(get(result, "snapshot_revision"), context.nativeRevision()); equal(get(result, "date_raw"), context.dateRaw());
        return new QueryFrame(positive(get(result, "query_sequence")), positive(get(result, "snapshot_revision")), i32(get(result, "date_raw")));
    }
    private static DefaultRaise defaultRaise(byte[] raw, Context context) {
        ObjectNode n = closed(parse(raw), "step", "accepted", "status", "read_only", "query_sequence", "snapshot_revision", "date_raw", "player_default_raise");
        equal(n.get("step"), "query-player-default-raise-v1"); yes(n.get("accepted")); yes(n.get("read_only")); equal(n.get("status"), "completed");
        QueryFrame frame = queryFrame(n, context);
        var observed = org.xar.ck3.control.contracts.DefaultRaiseObservation.parse(n.get("player_default_raise"),
                new org.xar.ck3.control.contracts.DefaultRaiseObservation.Expected(context.source().exactBuild(), context.playerId(), context.nativeRevision(), context.dateRaw()));
        var raising = observed.raising(); var reserve = observed.reserve();
        Field<Boolean> legal = raising.legal().<Field<Boolean>>map(Present::new).orElseGet(NullValue::new);
        Field<PositiveId> province = raising.provinceId().<Field<PositiveId>>map(id -> new Present<>(new PositiveId(id))).orElseGet(NullValue::new);
        Field<Integer> soldiers = reserve.unraisedSoldiers().<Field<Integer>>map(Present::new).orElseGet(NullValue::new);
        return new DefaultRaise(frame, new Build(observed.gameVersion(), observed.executableSha256()), RaiseStatus.valueOf(raising.status().name()), observed.actor(),
                raising.ready(), legal, province, raising.failure(), reserve.ready() ? ReserveStatus.AVAILABLE : ReserveStatus.UNAVAILABLE,
                reserve.ready(), soldiers, reserve.failure());
    }

    private static Truce truce(byte[] raw, Context context, ArmyCalls.Truce call) {
        // The original complete persisted-relation contract is already strict on every envelope and DTO field.
        var value = ArmyResponseCodec.truce(raw, context, new ArmyRequests.Truce(call.toward()));
        ObjectNode root = parse(raw); ObjectNode v = object(root.get("raiktor_actual_truce_expiry"));
        require(context.source().exactBuild().equals("1.20.0.4"), "truce result belongs to another connected build");
        return new Truce(queryFrame(root, context), new Build(text(v.get("ck3_build")), text(v.get("executable_sha256"))),
                value.owner(), value.toward(), value.hasTruce() ? TruceStatus.AVAILABLE : TruceStatus.NO_TRUCE,
                value.hasTruce(), value.actualExpiryObservable(), value.expiryDateRaw(), value.sameFrameStable(), value.readiness(), value.unavailableReason());
    }
    /** Original object fields with the declared mixed integer contract; native packets are retained unchanged. */
    public static RawJson encode(Observation observation, Context context) { return publicValue(nativeValue(observation, context), context); }
    /** Production presenter reads nullable diagnostics from the actual same-frame semantic packet, never a guessed identity. */
    public static RawJson encode(Observation observation, Context context, org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj actualSemantic) {
        ObjectNode snapshot = object(org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(actualSemantic));
        equal(get(snapshot, "snapshot_id"), context.before().frame().snapshotId()); equal(get(snapshot, "revision"), context.before().frame().revision());
        equal(get(snapshot, "native_revision"), context.nativeRevision()); equal(get(snapshot, "date_raw"), context.dateRaw());
        ObjectNode n = nativeValue(observation, context);
        if (observation instanceof DefaultRaise) {
            var episode = snapshot.get("episode_run_id"); if (episode != null && !episode.isNull()) text(episode);
            n.set("queried_episode_run_id", episode == null ? empty().nullNode() : episode.deepCopy());
            var diagnostics = snapshot.get("diagnostics");
            var connection = diagnostics != null && diagnostics.isObject() ? diagnostics.get("connection_generation") : null;
            var pid = diagnostics != null && diagnostics.isObject() ? diagnostics.get("bridge_pid") : null;
            if (connection != null && !connection.isNull()) u64(connection);
            if (pid != null && !pid.isNull()) range(pid, BigInteger.ZERO, BigInteger.valueOf(4_294_967_295L));
            n.set("queried_connection_generation", connection == null ? empty().nullNode() : connection.deepCopy());
            n.set("queried_bridge_pid", pid == null ? empty().nullNode() : pid.deepCopy());
        }
        return publicValue(n, context);
    }
    private static RawJson publicValue(ObjectNode n, Context context) {
        return ArmyPublicWire.encode(org.xar.ck3.control.application.driver.DriverJson.object(bytes(n),
                org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES), context);
    }
    private static ObjectNode nativeValue(Observation observation, Context context) {
        ObjectNode n = empty();
        switch (observation) {
            case DefaultRaise v -> {
                envelope(n, "query-player-default-raise-v1", v.frame()).put("status", "completed");
                ObjectNode p = empty().put("schema", v.build().version().equals("1.20.0.4") ? "ck3_12004_player_default_raise_v1" : "ck3_12003_player_default_raise_v1")
                        .put("game_version", v.build().version()).put("executable_sha256", v.build().executableSha256())
                        .put("status", wire(v.status())).put("snapshot_revision", v.frame().nativeRevision().value()).put("date_raw", v.frame().dateRaw()).put("actor_character_id", v.actor())
                        .put("default_raise_legality_ready", v.legalityReady()).put("failure", v.failure()).put("unraised_troops_status", wire(v.reserveStatus()))
                        .put("unraised_troops_ready", v.reserveReady()).put("unraised_troops_failure", v.reserveFailure()).put("unraised_troops_scale", 1).put("unraised_troops_scope", "native_all_actor_categories");
                nullableBool(p, "native_default_raise_legal", v.legal()); nullableId(p, "default_raise_province_id", v.province()); nullableInt(p, "unraised_soldiers", v.soldiers()); n.set("player_default_raise", p);
            }
            case Truce v -> {
                envelope(n, "query-raiktor-actual-truce-expiry-v1-" + v.toward().value(), v.frame()).put("backend_id", "native-headless");
                ObjectNode p = empty().put("schema_version", 1).put("backend_id", "ck3-1.20.0.4-native-player-truce-expiry-v1").put("ck3_build", v.build().version())
                        .put("executable_sha256", v.build().executableSha256()).put("status", wire(v.status())).put("snapshot_revision", v.frame().nativeRevision().value())
                        .put("current_date_raw", v.frame().dateRaw()).put("owner_character_id", v.owner()).put("toward_character_id", v.toward().value())
                        .put("native_has_truce", v.hasTruce()).put("actual_expiry_observable", v.expiryObservable()).put("same_frame_stable", v.stable()).put("readiness", v.readiness()).put("temporal_semantics", "post_application_persisted_relation_state");
                nullableInt(p, "expiry_date_raw", v.expiryDateRaw()); nullableText(p, "unavailable_reason", v.unavailableReason()); n.set("raiktor_actual_truce_expiry", p); n.set("player_truce_expiry_v1", p.deepCopy());
            }
            case Gathering v -> {
                var s = v.state(); n.put("step", "query-army-gathering-research-sampling-v1").put("accepted", s.accepted()).put("status", wire(s.status())).put("backend_id", "native-headless");
                n.set("army_gathering_research_sampling_v1", empty().put("capture_enabled", s.enabled()).put("busy", s.busy()).put("clear_completed", s.clearCompleted())
                        .put("epoch", s.epoch().value()).put("active_captures", s.activeCaptures().value()).put("retained_records", s.retained().value()).put("qualified_records", s.qualified().value()).put("readiness", wire(s.readiness())));
            }
        }
        if (observation instanceof Gathering) n.put("queried_date_raw", context.dateRaw());
        return n;
    }
    /** Public representation is restored before the same complete original Native-domain validator executes. */
    public static Observation decodePublic(ArmyCalls.Call call, Context context, RawJson publicResult) {
        ObjectNode n = object(org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(ArmyPublicWire.decode(publicResult, context)));
        if (call.method() == PublicMethod.QUERY_PLAYER_TRUCE_EXPIRY_V1) {
            require(get(n, "player_truce_expiry_v1").equals(get(n, "raiktor_actual_truce_expiry")), "public truce differs from its original observation");
            n.remove("player_truce_expiry_v1");
        }
        if (call.method() == PublicMethod.QUERY_PLAYER_DEFAULT_RAISE_V1)
            n.remove(java.util.List.of("queried_episode_run_id", "queried_connection_generation", "queried_bridge_pid"));
        if (call.method() == PublicMethod.QUERY_ARMY_GATHERING_RESEARCH_SAMPLING_V1) {
            equal(get(n, "queried_date_raw"), context.dateRaw()); n.remove("queried_date_raw");
        }
        return decodeToken(call, context, bytes(n));
    }
    private static ObjectNode envelope(ObjectNode n, String step, QueryFrame f) { return n.put("step", step).put("accepted", true).put("read_only", true).put("query_sequence", f.sequence().value()).put("snapshot_revision", f.nativeRevision().value()).put("date_raw", f.dateRaw()); }
    private static String wire(Enum<?> value) { return value.name().toLowerCase(Locale.ROOT); }
    private static void nullableBool(ObjectNode n, String key, Field<Boolean> value) { if (value instanceof Present<Boolean> p) n.put(key, p.value()); else if (value instanceof NullValue<?>) n.putNull(key); else throw new IllegalArgumentException("required nullable field absent"); }
    private static void nullableInt(ObjectNode n, String key, Field<Integer> value) { if (value instanceof Present<Integer> p) n.put(key, p.value()); else if (value instanceof NullValue<?>) n.putNull(key); else throw new IllegalArgumentException("required nullable field absent"); }
    private static void nullableId(ObjectNode n, String key, Field<PositiveId> value) { if (value instanceof Present<PositiveId> p) n.put(key, p.value().value()); else if (value instanceof NullValue<?>) n.putNull(key); else throw new IllegalArgumentException("required nullable field absent"); }
    private static void nullableText(ObjectNode n, String key, Field<String> value) { if (value instanceof Present<String> p) n.put(key, p.value()); else if (value instanceof NullValue<?>) n.putNull(key); else throw new IllegalArgumentException("required nullable field absent"); }
}
