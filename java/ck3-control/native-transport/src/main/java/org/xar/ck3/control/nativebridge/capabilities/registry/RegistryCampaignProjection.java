package org.xar.ck3.control.nativebridge.capabilities.registry;

import org.xar.ck3.control.contracts.NativeCharacterId;

import com.fasterxml.jackson.annotation.JsonValue;
import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import org.xar.ck3.control.application.capabilities.CampaignRootContextJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.registry.CampaignProjection.*;

/** Typed consumer of the sole strict campaign-root producer and the same complete Driver snapshot. */
public final class RegistryCampaignProjection {
    private RegistryCampaignProjection() { }

    /** The pending domain payload is already immutable JSON; its original object remains the public value. */
    public record PendingObject(Obj original) {
        public PendingObject { Objects.requireNonNull(original); }
        @JsonValue public JsonNode json() { return OpportunityJson.toNode(original); }
    }

    public static Root root(Obj nativeResult, Binding binding) {
        Objects.requireNonNull(nativeResult); Objects.requireNonNull(binding);
        Obj normalized = CampaignRootContextJson.normalizeNativeResult(nativeResult,
                BigInteger.valueOf(binding.dateRaw()), binding.nativeRevision());
        Obj root = object(normalized.get("campaign_root_context"), "normalized campaign root");
        Obj provenance = object(root.get("provenance"), "root provenance");
        Source source = new Source("game.command.query-campaign-root-context-v1",
                integer(normalized.get("query_sequence"), "original root query sequence"),
                text(provenance.get("game_version"), "root build"),
                text(provenance.get("executable_sha256"), "root executable"));
        if (text(root.get("status"), "root status").equals("unavailable"))
            return new UnavailableRoot(binding, source, text(root.get("unavailable_reason"), "root reason"));
        return new AvailableRoot(binding, source, character(root.get("player_character_id")),
                bool(root.get("player_character_alive"), "root alive"), title(root.get("primary_title")),
                nullableId(root.get("capital_province_id")), nullableCharacter(root.get("immediate_liege_character_id")),
                character(root.get("top_liege_character_id")), bool(root.get("independent"), "root independent"),
                ids(root.get("direct_landed_vassal_character_ids")), ids(root.get("adjacent_external_province_holder_character_ids")),
                array(root.get("related_character_contexts"), "related contexts").stream().map(RegistryCampaignProjection::related).toList(),
                government(root.get("government")), fixed(root.get("player_monthly_gold_income")), fixed(root.get("player_health")),
                int32(root.get("player_domain_size")), int32(root.get("player_domain_limit")), int32(root.get("player_targeting_faction_count")),
                council(root.get("council")), ids(root.get("primary_title_succession_character_ids")),
                array(root.get("held_title_partition"), "held partition").stream().map(RegistryCampaignProjection::partition).toList());
    }

    public static Snapshot<PendingObject,PendingObject> snapshot(Obj snapshot, Binding binding) {
        Objects.requireNonNull(snapshot); Objects.requireNonNull(binding);
        require(new Text(binding.snapshotId()).equals(snapshot.get("snapshot_id"))
                && new IntegerValue(binding.revision()).equals(snapshot.get("revision"))
                && new IntegerValue(binding.nativeRevision()).equals(snapshot.get("native_revision"))
                && new IntegerValue(BigInteger.valueOf(binding.dateRaw())).equals(snapshot.get("date_raw")),
                "registry aggregate snapshot changed its complete public/native/date identity");
        Obj played = object(snapshot.get("played_character"), "actual played character");
        Value stress = played.get("stress_points");
        Component<Integer> stressPoints = stress instanceof IntegerValue value && value.value().signum() >= 0
                && value.value().compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0
                ? Component.available(value.value().intValueExact()) : Component.unavailable("played_character_stress_unavailable");
        Value wallet = snapshot.get("played_character_gold");
        Component<Fixed> gold = wallet instanceof Obj ? Component.available(fixed(wallet))
                : Component.unavailable("played_character_gold_unavailable");
        Presence<List<War>> wars = snapshot.get("active_wars") instanceof Arr observed
                ? new Present<>(observed.items().stream().map(RegistryCampaignProjection::war).toList())
                : snapshot.get("active_wars") == Nil.INSTANCE ? new NullValue<>() : new Missing<>();
        return new Snapshot<>(binding, bool(snapshot.get("paused"), "actual snapshot paused"), character(played.get("character_id")),
                bool(played.get("alive"), "actual played character alive"), stressPoints, gold,
                pending(snapshot, "active_event"), pending(snapshot, "pending_character_interaction"), wars,
                text(snapshot.get("backend_id"), "actual snapshot backend"));
    }

    private static Presence<PendingObject> pending(Obj snapshot, String key) {
        if (!snapshot.members().containsKey(key)) return new Missing<>();
        Value value = snapshot.get(key);
        return value == Nil.INSTANCE ? new NullValue<>() : new Present<>(new PendingObject(object(value, key)));
    }
    private static War war(Value value) {
        Obj row = object(value, "actual war summary");
        return new War(id(row.get("war_id")), enumValue(Side.class, row.get("player_side")),
                nullableCharacter(row.get("primary_opponent_character_id")), integer(row.get("player_relative_war_score"), "war score"));
    }
    private static Related related(Value value) {
        Obj row = object(value, "related character");
        return new Related(character(row.get("character_id")), enumValue(Relation.class, row.get("relationship_role")),
                title(row.get("primary_title")), nullableId(row.get("capital_province_id")),
                nullableCharacter(row.get("immediate_liege_character_id")), character(row.get("top_liege_character_id")));
    }
    private static PartitionRow partition(Value value) {
        Obj row = object(value, "held title partition row");
        boolean family = new Text("landless_noble_family_no_province").equals(row.get("capital_province_kind"));
        return new PartitionRow(Objects.requireNonNull(title(row.get("title"))), nullableCharacter(row.get("first_heir_character_id")),
                nullableId(row.get("capital_province_id")), bool(row.get("primary"), "partition primary"), family,
                family ? text(row.get("title_key"), "family title key") : null);
    }
    private static Title title(Value value) {
        if (value == Nil.INSTANCE) return null;
        Obj row = object(value, "title");
        return new Title(id(row.get("title_id")), int32(row.get("tier_raw")), text(row.get("tier_key"), "title tier"));
    }
    private static Government government(Value value) {
        if (value == Nil.INSTANCE) return null;
        Obj row = object(value, "government");
        return new Government(text(row.get("key"), "government key"), array(row.get("flags"), "government flags").stream()
                .map(flag -> text(flag, "government flag")).toList(), int32(row.get("native_flag_count")));
    }
    private static Council council(Value value) {
        Obj row = object(value, "council");
        return new Council(enumValue(Status.class, row.get("status")), text(row.get("coverage_key"), "council coverage"),
                character(row.get("owner_character_id")), array(row.get("positions"), "council positions").stream()
                .map(RegistryCampaignProjection::position).toList(), bool(row.get("auxiliary_vacancies_complete"), "council auxiliary coverage"),
                nullableText(row.get("unavailable_reason")));
    }
    private static CouncilPosition position(Value value) {
        Obj row = object(value, "council position"); Integer incumbent = nullableCharacter(row.get("incumbent_character_id"));
        if (incumbent == null) return new CouncilPosition(text(row.get("position_key"), "council position"), null, null, null, null, null, null);
        Value rawTarget = row.get("target"); Target target = null;
        if (rawTarget != Nil.INSTANCE) {
            Obj observed = object(rawTarget, "council target"); String kind = text(observed.get("kind"), "target kind");
            target = kind.equals("province") ? new ProvinceTarget(id(observed.get("province_id")))
                    : new CharacterTarget(character(observed.get("character_id")));
        }
        Obj progress = object(row.get("progress"), "council progress");
        ProgressKind kind = enumValue(ProgressKind.class, progress.get("kind"));
        return new CouncilPosition(text(row.get("position_key"), "council position"), incumbent,
                text(row.get("task_key"), "council task"), enumValue(TaskKind.class, row.get("task_type")), target,
                bool(row.get("frozen"), "task frozen"), new Progress(kind,
                kind == ProgressKind.INFINITE ? null : fixed(progress.get("current")),
                kind == ProgressKind.INFINITE ? null : fixed(progress.get("maximum"))));
    }
    private static Fixed fixed(Value value) {
        Obj row = object(value, "native fixed point");
        require(row.members().keySet().equals(java.util.Set.of("raw", "scale")), "exact native fixed point fields required");
        return new Fixed(integer(row.get("raw"), "native fixed raw").longValueExact(), int32(row.get("scale")));
    }
    private static List<Integer> ids(Value value) { return array(value, "character identities").stream().map(RegistryCampaignProjection::character).toList(); }
    private static int int32(Value value) { return integer(value, "int32").intValueExact(); }
    private static int id(Value value) { int result = int32(value); require(result > 0, "positive int32 identity required"); return result; }
    private static int character(Value value) { return NativeCharacterId.of(integer(value, "native character identity")).value(); }
    private static Integer nullableCharacter(Value value) { return value == Nil.INSTANCE ? null : character(value); }
    private static Integer nullableId(Value value) { return value == Nil.INSTANCE ? null : id(value); }
    private static String nullableText(Value value) { return value == Nil.INSTANCE ? null : text(value, "optional reason"); }
    private static <E extends Enum<E>> E enumValue(Class<E> type, Value value) {
        String exact = text(value, "finite enum");
        for (E candidate : type.getEnumConstants()) if (candidate.name().toLowerCase(Locale.ROOT).equals(exact)) return candidate;
        throw new IllegalArgumentException("unknown " + type.getSimpleName() + ": " + exact);
    }
}
