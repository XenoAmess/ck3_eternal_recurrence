package org.xar.ck3.control.nativebridge.capabilities.registry;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;

/** Public roles of the two Registry read results; internal ROOT and bundle JSON stay numeric. */
public final class RegistryPublicProfile {
    public enum Profile { ENTITY_DIRECTORY, TURN_BUNDLE }
    private enum Domain { PUBLIC_REVISION, POSITIVE_U64, SIGNED_I64, SIGNED_INTEGER }
    private record Role(String path, Domain domain) { }
    private static final BigInteger SAFE = BigInteger.valueOf(9_007_199_254_740_991L);
    private static final BigInteger U64 = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private static final List<Role> DIRECTORY = List.of(
            new Role("snapshot_revision", Domain.POSITIVE_U64),
            new Role("source/query_sequence", Domain.POSITIVE_U64));
    private static final List<Role> BUNDLE = List.of(
            new Role("binding/revision", Domain.PUBLIC_REVISION),
            new Role("binding/native_revision", Domain.POSITIVE_U64),
            new Role("binding/expected_revision", Domain.PUBLIC_REVISION),
            new Role("source/query_sequence", Domain.POSITIVE_U64),
            new Role("ruler_state/value/gold/value/raw", Domain.SIGNED_I64),
            new Role("ruler_state/value/income/value/raw", Domain.SIGNED_I64),
            new Role("ruler_state/value/health_band/value/health/raw", Domain.SIGNED_I64),
            new Role("ruler_state/value/vitals/binding/snapshot_revision", Domain.POSITIVE_U64),
            new Role("ruler_state/value/vitals/health/value/raw", Domain.SIGNED_I64),
            new Role("ruler_state/value/vitals/legitimacy/value/raw", Domain.SIGNED_I64),
            new Role("realm_state/value/territory/source_frame/revision", Domain.PUBLIC_REVISION),
            new Role("realm_state/value/territory/source_frame/native_revision", Domain.POSITIVE_U64),
            new Role("realm_state/value/territory/source_frame/expected_revision", Domain.PUBLIC_REVISION),
            new Role("realm_state/value/territory/source_frame/query_sequence", Domain.POSITIVE_U64),
            new Role("realm_state/value/council/value/positions/*/progress/current/raw", Domain.SIGNED_I64),
            new Role("realm_state/value/council/value/positions/*/progress/maximum/raw", Domain.SIGNED_I64),
            new Role("war_state/value/wars/*/player_relative_war_score", Domain.SIGNED_INTEGER));
    private RegistryPublicProfile() { }

    /** Explicit profile selection is required; field names in unknown/pending payloads confer no role. */
    public static RawJson encode(Profile profile, RawJson internal) {
        ObjectNode tree = RegistryJson.object(Objects.requireNonNull(internal));
        schema(profile, tree);
        for (Role role : roles(profile)) transform(tree, role.path().split("/"), 0, role.domain(), true);
        safeNumbers(tree, "");
        return RegistryJson.encode(tree);
    }

    /** Restores only these declared roles to the original internal integer domain. No Native authority. */
    public static RawJson decode(Profile profile, RawJson external) {
        ObjectNode tree = RegistryJson.object(Objects.requireNonNull(external));
        schema(profile, tree); safeNumbers(tree, "");
        for (Role role : roles(profile)) transform(tree, role.path().split("/"), 0, role.domain(), false);
        return RegistryJson.encode(tree);
    }

    /** Public revision is an unbounded nonnegative integer, unlike native uint64 sequence/revision. */
    public static BigInteger revision(JsonNode value) {
        StrictJson.require(value != null, "missing public revision");
        if (value.isIntegralNumber()) {
            BigInteger result = value.bigIntegerValue();
            StrictJson.require(result.signum() >= 0, "nonnegative public revision required"); return result;
        }
        StrictJson.require(value.isTextual() && value.textValue().length() <= 4300
                && value.textValue().matches("0|[1-9][0-9]*"), "canonical decimal public revision required");
        return new BigInteger(value.textValue());
    }

    private static List<Role> roles(Profile profile) {
        return switch (Objects.requireNonNull(profile)) { case ENTITY_DIRECTORY -> DIRECTORY; case TURN_BUNDLE -> BUNDLE; };
    }
    private static void schema(Profile profile, ObjectNode tree) {
        String expected = switch (Objects.requireNonNull(profile)) {
            case ENTITY_DIRECTORY -> EntityDirectory.SCHEMA; case TURN_BUNDLE -> TurnBundle.SCHEMA;
        };
        StrictJson.require(tree.has("schema") && tree.get("schema").isTextual()
                && expected.equals(tree.get("schema").textValue()), "Registry public profile/schema mismatch");
        if (profile == Profile.ENTITY_DIRECTORY) required(tree, "snapshot_revision");
        else for (String name : List.of("revision", "native_revision", "expected_revision")) {
            JsonNode binding = required(tree, "binding");
            StrictJson.require(binding instanceof ObjectNode, "Registry bundle binding must be its original object");
            required((ObjectNode) binding, name);
        }
        JsonNode source = required(tree, "source");
        StrictJson.require(source instanceof ObjectNode, "Registry source must be its original object");
        required((ObjectNode) source, "query_sequence");
    }
    private static JsonNode required(ObjectNode value, String name) {
        JsonNode result = value.get(name);
        StrictJson.require(result != null && !result.isNull(), "missing/null Registry public identity role: " + name);
        return result;
    }
    private static void transform(JsonNode node, String[] path, int offset, Domain domain, boolean encode) {
        if (node == null || node.isNull()) return; // unavailable components keep their original missing/null distinction
        String step = path[offset];
        if ("*".equals(step)) {
            StrictJson.require(node.isArray(), "Registry declared role requires its original array");
            for (JsonNode item : node) transform(item, path, offset + 1, domain, encode);
            return;
        }
        StrictJson.require(node instanceof ObjectNode, "Registry declared role requires its original object");
        ObjectNode object = (ObjectNode) node;
        JsonNode value = object.get(step);
        if (offset != path.length - 1) { transform(value, path, offset + 1, domain, encode); return; }
        if (value == null || value.isNull()) return;
        BigInteger exact;
        if (encode) {
            StrictJson.require(value.isIntegralNumber(), "Registry internal role must be an exact integer: " + String.join("/", path));
            exact = value.bigIntegerValue();
        } else if (value.isTextual()) {
            String decimal = value.textValue();
            StrictJson.require(decimal.length() <= 4300 && decimal.matches(signed(domain)
                    ? "0|-?[1-9][0-9]*" : "0|[1-9][0-9]*"), "Registry public role requires canonical decimal text");
            exact = new BigInteger(decimal);
        } else {
            StrictJson.require(signed(domain) && value.isIntegralNumber(), "Registry identity role requires decimal text");
            exact = value.bigIntegerValue();
        }
        range(exact, domain);
        if (encode) {
            if (!signed(domain) || exact.abs().compareTo(SAFE) > 0) object.put(step, exact.toString());
        } else object.put(step, exact);
    }
    private static void range(BigInteger exact, Domain domain) {
        StrictJson.require(switch (domain) {
            case PUBLIC_REVISION -> exact.signum() >= 0;
            case POSITIVE_U64 -> exact.signum() > 0 && exact.compareTo(U64) <= 0;
            case SIGNED_I64 -> exact.compareTo(BigInteger.valueOf(Long.MIN_VALUE)) >= 0
                    && exact.compareTo(BigInteger.valueOf(Long.MAX_VALUE)) <= 0;
            case SIGNED_INTEGER -> true; // original CampaignProjection.War uses an exact BigInteger, with no uint64 bound
        }, "Registry public role is outside its original field domain");
    }
    private static boolean signed(Domain domain) { return domain == Domain.SIGNED_I64 || domain == Domain.SIGNED_INTEGER; }
    private static void safeNumbers(JsonNode value, String path) {
        if (value.isIntegralNumber()) StrictJson.require(value.bigIntegerValue().abs().compareTo(SAFE) <= 0,
                "undeclared unsafe Registry public number at " + path);
        if (value.isFloatingPointNumber()) StrictJson.require(Double.isFinite(value.doubleValue()), "nonfinite Registry public number at " + path);
        if (value.isObject()) value.properties().forEach(entry -> safeNumbers(entry.getValue(), path + "/" + entry.getKey()));
        else if (value.isArray()) for (int index = 0; index < value.size(); index++) safeNumbers(value.get(index), path + "/" + index);
    }
}
