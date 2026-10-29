package org.xar.ck3.control.wave2.military.holycost;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract;
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract.Choice;
import org.xar.ck3.control.wave2.military.holycost.HolyCostObservation.Build;
import org.xar.ck3.control.wave2.military.holycost.HolyCostObservation.CBOnlyQuote;
import org.xar.ck3.control.wave2.military.holycost.HolyCostObservation.ContextRoles;
import org.xar.ck3.control.wave2.military.holycost.HolyCostObservation.KnownQuote;
import org.xar.ck3.control.wave2.military.holycost.HolyCostObservation.Resource;
import org.xar.ck3.control.wave2.military.holycost.HolyCostObservation.UnavailableQuote;

/** Complete exact-build ordinary holy-war context normalizer; no private query, role substitution or total-price inference. */
public final class HolyCostJsonAdapter {
    public static final String SCHEMA = "player_ordinary_holy_war_declaration_context_v1";
    public static final Set<String> ORDINARY_HOLY_WAR_KEYS = Set.of("minor_religious_war", "religious_war", "major_religious_war");
    private static final Set<String> FIELDS = Set.of("schema", "read_only", "game_version", "executable_sha256", "available", "unavailable_reason",
            "capture_epoch", "public_revision", "native_revision", "date_raw", "played_character_id", "declaration_id", "selected_declaration",
            "context_actor_character_id", "context_recipient_character_id", "context_additional_role_character_id", "context_claimant_character_id",
            "recipient_uses_native_fallback", "additional_role_uses_native_fallback", "claimant_uses_native_fallback", "final_can_send", "cb_cost",
            "generic_interaction_cost_raw", "total_declaration_cost_raw", "total_cost_ready");
    private static final Set<String> SELECTED_FIELDS = Set.of("target_character_id", "casus_belli_index", "casus_belli_key",
            "configuration_index", "claimant_character_id", "target_title_ids");
    private static final Set<String> COST_FIELDS = Set.of("available", "unavailable_reason", "resource_keys", "resource_costs_raw", "raw_scale");

    private HolyCostJsonAdapter() { }

    public static Choice selectedDeclaration(JsonNode snapshot, String declarationId) {
        ObjectNode source = extensible(snapshot);
        List<Choice> choices = DeclarationContract.normalize(source.get("declarable_wars"));
        Choice selected = choices.stream().filter(choice -> choice.declarationId().equals(declarationId)).findFirst()
                .orElseThrow(() -> new IllegalArgumentException("selected ordinary holy-war declaration is absent"));
        selectedScope(selected);
        return selected;
    }

    public static ObjectNode selectedJson(Choice choice) {
        selectedScope(choice);
        ObjectNode selected = DeclarationContract.encodeChoice(choice);
        selected.remove("declaration_id"); selected.remove("source");
        return selected;
    }

    /** Declared projection of the existing enriched private-query container, retaining original token kinds. */
    public static ObjectNode projectCore(JsonNode enrichedQuery) {
        ObjectNode source = extensible(enrichedQuery);
        ObjectNode result = StrictJson.object();
        for (String field : FIELDS) {
            require(source.has(field), "enriched query lost context field " + field);
            result.set(field, source.get(field).deepCopy());
        }
        return result;
    }

    public static HolyCostObservation normalize(JsonNode value, JsonNode snapshotNode, String declarationId, JsonNode selectedDeclaration) {
        ObjectNode root = StrictJson.object(value, FIELDS);
        require(text(root.get("schema")).equals(SCHEMA), "context schema mismatch"); StrictJson.trueValue(root.get("read_only"));
        Build build = build(root.get("game_version"), root.get("executable_sha256"));
        ObjectNode snapshot = extensible(snapshotNode);
        ObjectNode diagnostics = extensible(snapshot.get("diagnostics"));
        ObjectNode hello = extensible(diagnostics.get("hello"));
        JsonNode version = hello.has("expected_ck3_version") ? hello.get("expected_ck3_version") : hello.get("game_version");
        JsonNode sha = hello.has("expected_ck3_sha256") ? hello.get("expected_ck3_sha256") : hello.get("executable_sha256");
        require(build == build(version, sha), "context belongs to a different exact snapshot build");
        boolean available = bool(root.get("available"));
        String reason = reason(root.get("unavailable_reason"), available);
        BigInteger epoch = uint64(root.get("capture_epoch"));
        BigInteger publicRevision = uint64(root.get("public_revision"));
        BigInteger nativeRevision = uint64(root.get("native_revision"));
        int date = signedInt(root.get("date_raw"));
        int actor = signedInt(root.get("played_character_id"));
        ObjectNode played = extensible(snapshot.get("played_character"));
        // Type-check expectations too: bool/float snapshot aliases cannot compare equal to native integer identities.
        require(actor == signedInt(played.get("character_id")) && date == signedInt(snapshot.get("date_raw"))
                && publicRevision.equals(uint64(snapshot.get("revision"))) && nativeRevision.equals(uint64(snapshot.get("native_revision")))
                && text(root.get("declaration_id")).equals(declarationId), "context differs from queried frame/declaration");
        Choice actual = selected(root.get("selected_declaration"), declarationId);
        Choice expected = selected(selectedDeclaration, declarationId);
        require(actual.equals(expected), "selected declaration differs from request");
        ContextRoles roles = new ContextRoles(nullableInt(root.get("context_actor_character_id")), nullableInt(root.get("context_recipient_character_id")),
                nullableInt(root.get("context_additional_role_character_id")), nullableInt(root.get("context_claimant_character_id")),
                nullableBool(root.get("recipient_uses_native_fallback")), nullableBool(root.get("additional_role_uses_native_fallback")),
                nullableBool(root.get("claimant_uses_native_fallback")));
        Boolean canSend = nullableBool(root.get("final_can_send"));
        if (available) require(roles.actorCharacterId() != null && roles.recipientCharacterId() != null && roles.additionalRoleCharacterId() != null
                && roles.claimantCharacterId() != null && roles.recipientUsesNativeFallback() != null && roles.additionalRoleUsesNativeFallback() != null
                && roles.claimantUsesNativeFallback() != null && canSend != null, "available context lost actual native role or flag");
        else require(canSend == null, "unread final gate acquired an invented boolean");
        ObjectNode rawCost = StrictJson.object(root.get("cb_cost"), COST_FIELDS);
        boolean costAvailable = bool(rawCost.get("available"));
        String costReason = reason(rawCost.get("unavailable_reason"), costAvailable);
        JsonNode keys = array(rawCost.get("resource_keys"));
        require(keys.size() == Resource.values().length, "resource key count mismatch");
        for (Resource resource : Resource.values()) require(text(keys.get(resource.ordinal())).equals(resource.wire()), "resource order mismatch");
        StrictJson.integer(rawCost.get("raw_scale"), 100_000, 100_000);
        CBOnlyQuote cost;
        JsonNode terms = rawCost.get("resource_costs_raw");
        if (costAvailable) {
            require(available && array(terms).size() == Resource.values().length, "CB quote lost selected context or ten terms");
            List<Long> costs = new ArrayList<>();
            for (JsonNode term : terms) costs.add(StrictJson.integer(term, Long.MIN_VALUE, Long.MAX_VALUE));
            cost = new KnownQuote(costs);
        } else {
            require(terms.isNull(), "unread CB quote acquired invented vector"); cost = new UnavailableQuote(costReason);
        }
        require(root.get("generic_interaction_cost_raw").isNull() && root.get("total_declaration_cost_raw").isNull()
                && !bool(root.get("total_cost_ready")), "CB-only quote misrepresented as total declaration cost");
        return new HolyCostObservation(build, text(root.get("executable_sha256")), available, reason,
                epoch, publicRevision, nativeRevision, date, actor, declarationId, actual, roles, canSend, cost);
    }

    public static ObjectNode encode(HolyCostObservation observation) {
        ObjectNode result = StrictJson.object().put("schema", SCHEMA).put("read_only", true).put("game_version", observation.build().gameVersion())
                .put("executable_sha256", observation.originalExecutableSha256()).put("available", observation.available())
                .put("unavailable_reason", observation.unavailableReason()).put("capture_epoch", observation.captureEpoch())
                .put("public_revision", observation.publicRevision()).put("native_revision", observation.nativeRevision())
                .put("date_raw", observation.dateRaw()).put("played_character_id", observation.playedCharacterId()).put("declaration_id", observation.declarationId());
        result.set("selected_declaration", selectedJson(observation.selectedDeclaration()));
        ContextRoles roles = observation.roles();
        result.put("context_actor_character_id", roles.actorCharacterId()).put("context_recipient_character_id", roles.recipientCharacterId())
                .put("context_additional_role_character_id", roles.additionalRoleCharacterId()).put("context_claimant_character_id", roles.claimantCharacterId())
                .put("recipient_uses_native_fallback", roles.recipientUsesNativeFallback()).put("additional_role_uses_native_fallback", roles.additionalRoleUsesNativeFallback())
                .put("claimant_uses_native_fallback", roles.claimantUsesNativeFallback()).put("final_can_send", observation.finalCanSend());
        ObjectNode cost = result.putObject("cb_cost").put("available", observation.cbCost().available()).put("raw_scale", 100_000);
        ArrayNode keys = cost.putArray("resource_keys"); for (Resource resource : Resource.values()) keys.add(resource.wire());
        if (observation.cbCost() instanceof KnownQuote known) {
            cost.putNull("unavailable_reason"); ArrayNode terms = cost.putArray("resource_costs_raw"); known.resourceCostsRaw().forEach(terms::add);
        } else {
            cost.put("unavailable_reason", ((UnavailableQuote) observation.cbCost()).unavailableReason()); cost.putNull("resource_costs_raw");
        }
        result.putNull("generic_interaction_cost_raw").putNull("total_declaration_cost_raw").put("total_cost_ready", false);
        return result;
    }

    private static Choice selected(JsonNode value, String declarationId) {
        ObjectNode raw = StrictJson.object(value, SELECTED_FIELDS);
        ObjectNode row = raw.deepCopy(); row.put("declaration_id", declarationId);
        List<Choice> choices = DeclarationContract.normalize(StrictJson.object().putArray("rows").add(row));
        Choice choice = choices.getFirst(); selectedScope(choice); return choice;
    }
    private static void selectedScope(Choice choice) {
        require(ORDINARY_HOLY_WAR_KEYS.contains(choice.casusBelliKey()), "selected declaration is not ordinary holy war");
        maximum(choice.targetCharacterId()); maximum(choice.casusBelliIndex()); maximum(choice.configurationIndex()); maximum(choice.claimantCharacterId());
        choice.targetTitleIds().forEach(HolyCostJsonAdapter::maximum);
    }
    private static void maximum(BigInteger value) { require(value.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0, "selected native field exceeds int32 scope"); }
    private static Build build(JsonNode version, JsonNode sha) {
        String actualVersion = text(version); String actualSha = text(sha).toUpperCase(Locale.ROOT);
        for (Build build : Build.values()) if (build.gameVersion().equals(actualVersion) && build.executableSha256().equals(actualSha)) return build;
        throw new IllegalArgumentException("ordinary holy-war exact .3/.4 build required");
    }
    private static ObjectNode extensible(JsonNode value) { require(value instanceof ObjectNode, "SDK snapshot object required"); return (ObjectNode) value; }
    private static JsonNode array(JsonNode value) { require(value != null && value.isArray(), "actual array required"); return value; }
    private static String text(JsonNode value) { require(value != null && value.isTextual(), "actual string required"); return value.textValue(); }
    private static boolean bool(JsonNode value) { require(value != null && value.isBoolean(), "actual boolean required"); return value.booleanValue(); }
    private static Boolean nullableBool(JsonNode value) { require(value != null, "nullable boolean field missing"); return value.isNull() ? null : bool(value); }
    private static int signedInt(JsonNode value) { return (int) StrictJson.integer(value, Integer.MIN_VALUE, Integer.MAX_VALUE); }
    private static Integer nullableInt(JsonNode value) { require(value != null, "nullable role field missing"); return value.isNull() ? null : signedInt(value); }
    private static BigInteger uint64(JsonNode value) { return StrictJson.integer(value, BigInteger.ONE, StrictJson.UINT64_MAX); }
    private static String reason(JsonNode value, boolean available) {
        require(value != null, "availability reason missing");
        if (available) { require(value.isNull(), "available stage reason must be null"); return null; }
        String reason = text(value); require(!reason.isEmpty(), "unavailable stage reason must be nonempty"); return reason;
    }
    private static void require(boolean condition, String reason) { StrictJson.require(condition, "ordinary holy-war cost " + reason); }
}
