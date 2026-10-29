package org.xar.ck3.control.wave2.planning.scoretarget;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Strict outer request, declared field projections inside extensible saved containers. */
public final class PlayerWarDefenceCodec {
    private static final String WARS = "landed_data.wars";
    private static final String DEFENDER = "casus_belli.defender";
    private PlayerWarDefenceCodec() { }

    public static PlayerWarInput decode(byte[] raw) {
        return input(StrictJson.parse(raw));
    }

    static PlayerWarInput input(JsonNode parsed) {
        ObjectNode request = StrictJson.object(parsed, Set.of("actor", "character_fields", "wars"));
        JsonNode actor = request.get("actor");
        StrictJson.require(actor.isIntegralNumber(), "exact actor integer required; no bool/float/string coercion");
        ObjectNode character = container(request.get("character_fields"));
        ObjectNode wars = container(request.get("wars"));
        JsonNode presence = character.get("present:" + WARS);
        PlayerWarInput.CharacterWars fields = new PlayerWarInput.CharacterWars(scalar(character.get(WARS)),
                presence != null && presence.isTextual() && presence.textValue().equals("true"),
                character.has("nonunique:" + WARS), character.has("incomplete:" + WARS));
        Map<String, PlayerWarInput.WarEntry> rows = new LinkedHashMap<>();
        wars.properties().forEach(entry -> rows.put(entry.getKey(), war(entry.getValue())));
        return new PlayerWarInput(actor.bigIntegerValue(), fields, rows);
    }

    public static byte[] evaluate(byte[] raw) { return encode(PlayerWarDefence.project(decode(raw))); }

    /** Original (own_defence, audit) tuple represented by named fields, with exact audit presence. */
    public static byte[] encode(PlayerWarDefenceResult result) {
        ObjectNode output = StrictJson.object();
        ObjectNode audit = audit(result);
        if (result instanceof PlayerWarDefenceResult.Known known) { output.put("own_defence", known.ownDefence()); }
        else { output.putNull("own_defence"); }
        output.set("audit", audit);
        return StrictJson.canonical(output);
    }

    static ObjectNode audit(PlayerWarDefenceResult result) {
        ObjectNode audit = StrictJson.object();
        audit.put("method", "player_landed_war_list"); audit.put("locator", WARS);
        var ids = audit.putArray("listed_war_ids"); result.listedWarIds().forEach(ids::add);
        if (result instanceof PlayerWarDefenceResult.Known known) {
            audit.put("known", true);
            audit.put("own_defence", known.ownDefence()); audit.put("reason", "ALL_LISTED_WARS_VERIFIED");
        } else if (result instanceof PlayerWarDefenceResult.Unknown unknown) {
            audit.put("known", false); audit.put("reason", unknown.reason().name());
        }
        return audit;
    }

    private static ObjectNode container(JsonNode node) {
        StrictJson.require(node instanceof ObjectNode, "saved field container must be an object");
        return (ObjectNode) node;
    }
    public static ScalarField scalar(JsonNode node) {
        if (node == null) { return new ScalarField.Missing(); }
        if (node.isNull()) { return new ScalarField.NullValue(); }
        if (node.isTextual()) {
            if (!node.textValue().isEmpty()) { StrictJson.text(node); }
            return new ScalarField.Text(node.textValue());
        }
        ScalarField.TokenKind kind = node.isBoolean() ? ScalarField.TokenKind.BOOLEAN
                : node.isIntegralNumber() ? ScalarField.TokenKind.INTEGER
                : node.isFloatingPointNumber() ? ScalarField.TokenKind.FRACTIONAL
                : node.isArray() ? ScalarField.TokenKind.ARRAY : ScalarField.TokenKind.OBJECT;
        return new ScalarField.Other(kind);
    }
    private static PlayerWarInput.WarEntry war(JsonNode node) {
        if (node instanceof ObjectNode row) {
            return new PlayerWarInput.ObservedWar(scalar(row.get(DEFENDER)), row.has("nonunique:" + DEFENDER));
        }
        PlayerWarInput.InvalidKind kind = node.isNull() ? PlayerWarInput.InvalidKind.NULL
                : node.isBoolean() ? PlayerWarInput.InvalidKind.BOOLEAN
                : node.isIntegralNumber() ? PlayerWarInput.InvalidKind.INTEGER
                : node.isFloatingPointNumber() ? PlayerWarInput.InvalidKind.FRACTIONAL
                : node.isTextual() ? PlayerWarInput.InvalidKind.STRING : PlayerWarInput.InvalidKind.ARRAY;
        return new PlayerWarInput.InvalidWar(kind);
    }
}
