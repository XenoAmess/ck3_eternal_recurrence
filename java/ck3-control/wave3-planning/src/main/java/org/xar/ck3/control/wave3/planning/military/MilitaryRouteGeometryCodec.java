package org.xar.ck3.control.wave3.planning.military;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.planning.military.MilitaryRouteGeometry.*;

/** Exact existing strategy._audit_war_route JSON domain. Invalid route remains an unavailable result. */
public final class MilitaryRouteGeometryCodec {
    public static final int MAXIMUM_BYTES = 1_048_576;
    private MilitaryRouteGeometryCodec() { }
    public sealed interface Input permits Observable, Unobservable { }
    public record Observable(List<Integer> route, int origin, int target, List<Enemy> enemies) implements Input {
        public Observable { route = List.copyOf(route); enemies = List.copyOf(enemies); }
    }
    public record Unobservable(int target) implements Input { }
    public static Input decode(byte[] raw) {
        ObjectNode root = StrictJson.object(StrictJson.parse(raw, MAXIMUM_BYTES), Set.of("route_value", "origin_province_id", "target_province_id", "enemies"));
        int target = (int) StrictJson.integer(root.get("target_province_id"), 1, Integer.MAX_VALUE);
        JsonNode route = root.get("route_value");
        if (!route.isArray()) return new Unobservable(target);
        List<Integer> provinces = new ArrayList<>();
        for (JsonNode value : route) {
            Optional<Integer> id = exactInt(value);
            if (id.isEmpty() || id.orElseThrow() <= 0) return new Unobservable(target);
            provinces.add(id.orElseThrow());
        }
        JsonNode originValue = root.get("origin_province_id");
        int origin = originValue.isNull() ? 0 : (int) StrictJson.integer(originValue, 1, Integer.MAX_VALUE);
        JsonNode rows = root.get("enemies"); StrictJson.require(rows.isArray(), "enemy rows required");
        List<Enemy> enemies = new ArrayList<>();
        for (JsonNode row : rows) {
            StrictJson.require(row.isObject(), "observed enemy object required");
            Optional<Integer> id = exactInt(row.get("army_id")).filter(value -> value >= 0);
            Optional<Integer> current = exactInt(row.get("current_province_id")).filter(value -> value > 0);
            Optional<Integer> destination = exactInt(row.get("move_target_province_id")).filter(value -> value > 0);
            List<Integer> remaining = new ArrayList<>(); JsonNode enemyRoute = row.get("route_province_ids");
            if (enemyRoute != null && enemyRoute.isArray()) for (JsonNode value : enemyRoute)
                exactInt(value).filter(province -> province > 0).ifPresent(remaining::add);
            enemies.add(new Enemy(id.orElse(null), current, destination, remaining,
                    retreating(row) ? TacticalState.RETREATING : TacticalState.OTHER));
        }
        return new Observable(provinces, origin, target, enemies);
    }
    public static byte[] project(byte[] raw) { return encode(decode(raw)); }
    public static byte[] encode(Input input) {
        if (input instanceof Unobservable invalid) {
            ObjectNode result = StrictJson.object(); result.put("status", "unavailable"); result.put("target_province_id", invalid.target());
            result.put("reason", "route_not_observable"); return StrictJson.canonical(result, MAXIMUM_BYTES);
        }
        Observable observed = (Observable) input;
        return encodeAudit(MilitaryRouteGeometry.geometry(observed.route(), observed.origin(), observed.target(), observed.enemies()));
    }
    public static byte[] encodeAudit(Audit audit) {
        ObjectNode result = StrictJson.object(); result.put("status", switch (audit.status()) {
            case SAFE -> "safe"; case UNSAFE -> "unsafe"; case ROUTE_DOES_NOT_REACH_TARGET -> "unavailable";
            case SAFE_ONE_DAY_CONTACT_HORIZON -> "safe_one_day_contact_horizon";
        });
        result.put("target_province_id", audit.targetProvinceId()); var route = result.putArray("route_province_ids"); audit.routeProvinceIds().forEach(route::add);
        if (audit.status() == Status.ROUTE_DOES_NOT_REACH_TARGET) result.put("reason", "route_does_not_reach_target");
        else {
            var conflicts = result.putArray("conflicts");
            for (Conflict value : audit.conflicts()) {
                ObjectNode row = conflicts.addObject(); row.put("kind", value.kind().name().toLowerCase(Locale.ROOT));
                if (value.enemyArmyId() == null) row.putNull("enemy_army_id"); else row.put("enemy_army_id", value.enemyArmyId());
                if (value.kind() == ConflictKind.OPPOSITE_EDGE_INTERSECTION) {
                    row.put("from_province_id", value.provinceId()); row.put("to_province_id", value.toProvinceId().orElseThrow());
                } else row.put("province_id", value.provinceId());
                value.playerHop().ifPresent(hop -> row.put("player_hop", hop)); value.enemyHop().ifPresent(hop -> row.put("enemy_hop", hop));
            }
        }
        return StrictJson.canonical(result, MAXIMUM_BYTES);
    }
    private static Optional<Integer> exactInt(JsonNode value) {
        return value != null && value.isIntegralNumber() && value.canConvertToInt() ? Optional.of(value.intValue()) : Optional.empty();
    }
    private static boolean retreating(JsonNode row) {
        if (row.path("retreating").isBoolean() && row.path("retreating").booleanValue()) return true;
        if (row.path("in_combat").isBoolean() && row.path("in_combat").booleanValue()) return false;
        JsonNode named = row.get("army_state");
        if (named != null && named.isTextual()) return named.textValue().equalsIgnoreCase("retreating");
        return exactInt(row.get("army_state_code")).filter(value -> value == 6).isPresent();
    }
}
