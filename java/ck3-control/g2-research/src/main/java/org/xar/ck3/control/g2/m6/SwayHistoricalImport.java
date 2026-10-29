package org.xar.ck3.control.g2.m6;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeSwayActionId;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Episode;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Identity;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Stamp;

/**
 * Historical ledger parsing, with no current-source rebind or credit grant.
 * Complete original JSON stays immutable, including previous interventions.
 * Historical stamps deliberately have no invented machine, Game birth or
 * ObservationIdentity. The application adapter must use its actual restore
 * authority and guarded fresh reads before continuing an original identity.
 * A historical TRUE consumption flag may suppress duplicate following work;
 * it cannot establish a new terminal, cause, material gain or current proof.
 */
public final class SwayHistoricalImport {
    public static final int MAX_BYTES = M6SourceProducer.MAX_BYTES;
    private static final int MAX_EPISODES = 256;
    private static final int MAX_DEPTH = 32;

    private SwayHistoricalImport() {}

    public enum Plane {
        INSTANCE("latest_instance_observation"), PHASE("phase_intervention"),
        MATERIAL("material_intervention"), FIRST_GAIN("first_named_gain_intervention"),
        TERMINAL("terminal_intervention"), STOP("stop_intervention");
        private final String field;
        Plane(String field) { this.field = field; }
        public String field() { return field; }
    }

    public enum Flag { MISSING, FALSE, TRUE }

    public record HistoricalConsumption(Flag flag, Optional<Stamp> following) {
        public HistoricalConsumption {
            Objects.requireNonNull(flag, "flag");
            Objects.requireNonNull(following, "following");
        }
        public boolean markedConsumed() { return flag == Flag.TRUE; }
    }

    public sealed interface HistoricalField permits Missing, ExplicitNull, Retained {}
    public record Missing() implements HistoricalField {}
    public record ExplicitNull() implements HistoricalField {}
    public record Retained(ProjectionJson original, HistoricalConsumption consumption,
            Optional<Stamp> originalSource) implements HistoricalField {
        public Retained {
            Objects.requireNonNull(original, "original");
            Objects.requireNonNull(consumption, "consumption");
            Objects.requireNonNull(originalSource, "originalSource");
        }
    }

    public record History(Identity identity, ProjectionJson originalResolved,
            HistoricalConsumption startConsumption, Map<Plane, HistoricalField> planes,
            Optional<List<History>> previous) {
        public History {
            Objects.requireNonNull(identity, "identity");
            Objects.requireNonNull(originalResolved, "originalResolved");
            Objects.requireNonNull(startConsumption, "startConsumption");
            planes = Map.copyOf(planes);
            if (!planes.keySet().equals(Set.of(Plane.values()))) {
                throw new IllegalArgumentException("complete historical plane presence contract required");
            }
            previous = Objects.requireNonNull(previous, "previous").map(List::copyOf);
        }

        public HistoricalField plane(Plane plane) { return planes.get(Objects.requireNonNull(plane)); }
    }

    /**
     * Parses a resolved object, not an invented current campaign packet.
     * The top-level original bytes are preserved exactly. Nested rows remain
     * JSON-domain copies, with original integer tokens and absent/null states.
     */
    public static History parse(ProjectionJson originalResolved) {
        Objects.requireNonNull(originalResolved, "originalResolved");
        JsonNode root = StrictJson.parse(originalResolved.bytes(), MAX_BYTES);
        return parse(root, originalResolved, new HashSet<>(), 0);
    }

    /**
     * Identity-only episode for an adapter that has separately established a
     * real restore binding. It carries no imported Start/gain/terminal credit.
     * Call the existing SwayLifecycle reducer with actual fresh guarded planes.
     */
    public static Episode identityOnlyEpisode(History history) {
        Objects.requireNonNull(history, "history");
        return new Episode(history.identity(), Optional.empty(), Optional.empty(),
                Optional.empty(), history.originalResolved());
    }

    public static List<History> flatten(History history) {
        Objects.requireNonNull(history, "history");
        List<History> result = new ArrayList<>();
        flatten(history, result);
        return List.copyOf(result);
    }

    private static void flatten(History history, List<History> result) {
        result.add(history);
        history.previous().ifPresent(rows -> rows.forEach(row -> flatten(row, result)));
    }

    private static History parse(JsonNode root, ProjectionJson original,
            Set<String> actions, int depth) {
        object(root);
        StrictJson.require(depth <= MAX_DEPTH && actions.size() < MAX_EPISODES,
                "historical intervention graph exceeds finite bound");
        String action = text(root, "action_id");
        Identity identity = originalIdentity(root, action);
        StrictJson.require(actions.add(action), "repeated historical action identity");
        Episode identityOnly = new Episode(identity, Optional.empty(), Optional.empty(),
                Optional.empty(), original);
        // Reuse the unique original receipt/build/identity source validator.
        // Empty planes cannot produce a current terminal or material observation.
        M6TerminalSourceComposition.compose(identityOnly, M6TerminalSourceComposition.Inputs.unqueried());
        EnumMap<Plane, HistoricalField> planes = new EnumMap<>(Plane.class);
        for (Plane plane : Plane.values()) {
            JsonNode row = root.get(plane.field());
            if (row == null) planes.put(plane, new Missing());
            else if (row.isNull()) planes.put(plane, new ExplicitNull());
            else {
                object(row);
                StrictJson.require(observedIdentity(row, action, plane).equals(identity),
                        "historical plane belongs to another original instance");
                validateBooleanFields(row);
                validateNamedFields(row);
                planes.put(plane, new Retained(json(row), consumption(row),
                        optionalStamp(row, "source_native_revision", "source_date_raw")));
            }
        }
        Optional<List<History>> previous = Optional.empty();
        if (root.has("previous_interventions")) {
            JsonNode raw = root.get("previous_interventions");
            StrictJson.require(raw.isArray(), "previous_interventions must be an array, not null");
            List<History> children = new ArrayList<>();
            for (JsonNode child : raw) children.add(parse(child, json(child), actions, depth + 1));
            previous = Optional.of(List.copyOf(children));
        }
        return new History(identity, original, consumption(root), planes, previous);
    }

    private static Identity originalIdentity(JsonNode root, String action) {
        JsonNode receipt = root.get("native_receipt");
        JsonNode source = receipt == null || receipt.isNull()
                ? root.get("recovered_instance_observation") : receipt;
        if ((receipt == null || receipt.isNull()) && source == null) {
            source = root.get("applied_instance_observation");
        }
        object(source);
        return new Identity(action, integer(root, "actor_character_id", 1, 0xFFFF_FFFEL),
                integer(root, "target_character_id", 1, 0xFFFF_FFFEL),
                integer(source, "scheme_instance_id", 0, 0xFFFF_FFFEL),
                Math.toIntExact(integer(source, "scheme_instance_generation", 0, 255)));
    }

    private static Identity observedIdentity(JsonNode row, String action, Plane plane) {
        if (plane == Plane.STOP) {
            // The stop producer submits its own action. Its original_action_id
            // binds the existing Sway episode; neither ID aliases the other.
            String stopAction = NativeSwayActionId.require(text(row, "action_id"),
                    NativeSwayActionId.Kind.SELECTED_STOP);
            StrictJson.require(!stopAction.equals(action), "historical stop action identity differs");
            StrictJson.require(text(row, "original_action_id").equals(action),
                    "historical stop refers to another original action");
        } else if (row.has("action_id")) {
            StrictJson.require(text(row, "action_id").equals(action),
                    "historical plane action differs");
        }
        return new Identity(action, integer(row, "actor_character_id", 1, 0xFFFF_FFFEL),
                integer(row, "target_character_id", 1, 0xFFFF_FFFEL),
                integer(row, "scheme_instance_id", 0, 0xFFFF_FFFEL),
                Math.toIntExact(integer(row, "scheme_instance_generation", 0, 255)));
    }

    private static HistoricalConsumption consumption(JsonNode row) {
        Flag flag = Flag.MISSING;
        if (row.has("next_turn_consumed")) {
            flag = bool(row, "next_turn_consumed") ? Flag.TRUE : Flag.FALSE;
        }
        return new HistoricalConsumption(flag,
                optionalStamp(row, "following_native_revision", "following_date_raw"));
    }

    private static Optional<Stamp> optionalStamp(JsonNode row, String revision, String date) {
        if (!row.has(revision) && !row.has(date)) return Optional.empty();
        StrictJson.require(row.has(revision) && row.has(date), "partial historical stamp");
        return Optional.of(new Stamp(StrictJson.integer(row.get(revision), BigInteger.ONE,
                StrictJson.UINT64_MAX), Math.toIntExact(integer(row, date,
                Integer.MIN_VALUE, Integer.MAX_VALUE))));
    }

    private static void validateBooleanFields(JsonNode row) {
        for (String field : List.of("postcondition_verified", "instance_terminal_outcome_observed",
                "terminal_cause_observed", "tracked_instance_active", "incremental_named_gain_observed",
                "material_effect_observed", "native_terminal_state_observed", "executing_input_observed",
                "dedicated_benefit_observed", "dedicated_setback_observed")) {
            if (row.has(field)) bool(row, field);
        }
    }

    private static void validateNamedFields(JsonNode row) {
        for (String field : List.of("scheme_sway_opinion", "sway_blocker_opinion",
                "previous_scheme_sway_opinion")) {
            JsonNode value = row.get(field);
            if (value == null || value.isNull()) continue;
            StrictJson.object(value, Set.of("observed", "present", "value"));
            boolean observed = bool(value, "observed"), present = bool(value, "present");
            Optional<BigInteger> points = value.get("value").isNull() ? Optional.empty()
                    : Optional.of(StrictJson.integer(value.get("value"),
                            BigInteger.valueOf(Integer.MIN_VALUE), BigInteger.valueOf(Integer.MAX_VALUE)));
            StrictJson.require(present == points.isPresent() && (!present || observed),
                    "historical named observation/presence/value mismatch");
            new G2M6Contracts.NamedValue(observed, present, points);
        }
    }

    private static ProjectionJson json(JsonNode value) {
        // Role-limited JSON copy preserves large original proof strings that
        // exceed StrictJson's small business-text canonicalization limit.
        return ProjectionJson.object(value.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8), MAX_BYTES);
    }
    private static void object(JsonNode value) {
        StrictJson.require(value != null && value.isObject(), "historical object required");
    }
    private static String text(JsonNode value, String field) {
        object(value);
        JsonNode node = value.get(field);
        StrictJson.require(node != null && node.isTextual(), "historical text required: " + field);
        return StrictJson.text(node.textValue());
    }
    private static boolean bool(JsonNode value, String field) {
        object(value);
        JsonNode node = value.get(field);
        StrictJson.require(node != null && node.isBoolean(), "historical boolean required: " + field);
        return node.booleanValue();
    }
    private static long integer(JsonNode value, String field, long minimum, long maximum) {
        object(value);
        return StrictJson.integer(value.get(field), minimum, maximum);
    }
}
