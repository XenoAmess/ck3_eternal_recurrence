package org.xar.ck3.control.wave2.governance.heirlineage;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.heirpreference.HeirPreferenceCodec;
import org.xar.ck3.control.wave2.governance.heirlineage.HeirLineagePolicy.AvailablePreview;
import org.xar.ck3.control.wave2.governance.heirlineage.HeirLineagePolicy.CharacterId;
import org.xar.ck3.control.wave2.governance.heirlineage.HeirLineagePolicy.Context;
import org.xar.ck3.control.wave2.governance.heirlineage.HeirLineagePolicy.DynastyId;
import org.xar.ck3.control.wave2.governance.heirlineage.HeirLineagePolicy.Opportunity;
import org.xar.ck3.control.wave2.governance.heirlineage.HeirLineagePolicy.Preview;
import org.xar.ck3.control.wave2.governance.heirlineage.HeirLineagePolicy.PreviewObservation;
import org.xar.ck3.control.wave2.governance.heirlineage.HeirLineagePolicy.PreviewQuery;
import org.xar.ck3.control.wave2.governance.heirlineage.HeirLineagePolicy.UnavailablePreview;

/** Consumer of original observed previews; no native channel, Game action or ledger ownership. */
public final class HeirLineageConsumerPort {
    private HeirLineageConsumerPort() { }

    public record Evaluation(byte[] result, List<PreviewQuery> queries) {
        public Evaluation {
            result = result.clone();
            queries = List.copyOf(queries);
        }
        @Override public byte[] result() { return result.clone(); }
    }

    /** Returns the old tuple as {choice,observations}; it does not grant source/submit qualification. */
    public static byte[] consume(byte[] input) { return evaluate(input).result(); }

    public static Evaluation evaluate(byte[] input) {
        ObjectNode request = StrictJson.object(StrictJson.parse(input),
                Set.of("snapshot", "legality", "projection", "choices", "previews"));
        StrictJson.canonical(request);
        ObjectNode snapshot = object(request.get("snapshot"));
        ObjectNode legality = object(request.get("legality"));
        ObjectNode projection = object(request.get("projection"));
        ArrayNode rows = array(projection.get("rows"));
        Context context = new Context(nonnegative(snapshot.get("revision")),
                nonnegative(snapshot.get("native_revision")), integer(snapshot.get("date_raw")),
                character(legality.get("observed_first_heir_character_id")));
        ObjectNode preferenceInput = StrictJson.object();
        preferenceInput.set("choices", request.get("choices"));
        preferenceInput.set("rows", rows);
        ArrayNode orderedChoices = array(StrictJson.parse(HeirPreferenceCodec.prioritize(
                StrictJson.canonical(preferenceInput))));
        Map<CharacterId, ObjectNode> rowById = new HashMap<>();
        for (JsonNode raw : rows) {
            ObjectNode row = object(raw);
            rowById.put(character(row.get("candidate_character_id")), row);
        }
        List<Opportunity> opportunities = new ArrayList<>();
        for (int ordinal = 0; ordinal < orderedChoices.size(); ordinal++) {
            CharacterId candidate = character(orderedChoices.get(ordinal).get("candidate_character_id"));
            ObjectNode row = rowById.get(candidate);
            StrictJson.require(row != null, "a selected choice requires its existing rich row");
            opportunities.add(new Opportunity(ordinal, candidate, character(row.get("heir_character_id")),
                    bool(row.get("matrilineal_option_selected")),
                    bool(row.get("effective_matrilineal_if_accepted")), dynasty(row.get("played_dynasty_id"))));
        }
        Map<CharacterId, ObjectNode> previewById = new HashMap<>();
        for (JsonNode raw : array(request.get("previews"))) {
            ObjectNode observation = object(raw);
            CharacterId candidate = character(object(observation.get("native_child_house_preview"))
                    .get("candidate_character_id"));
            StrictJson.require(previewById.put(candidate, observation) == null,
                    "duplicate preview candidate is ambiguous");
        }
        List<ObjectNode> consumed = new ArrayList<>();
        List<PreviewQuery> queries = new ArrayList<>();
        var selection = HeirLineagePolicy.chooseInPreferenceOrder(context, opportunities, query -> {
            ObjectNode observed = previewById.get(query.candidate());
            StrictJson.require(observed != null, "requested native preview is not present; observation required");
            ObjectNode preview = object(observed.get("native_child_house_preview"));
            StrictJson.require(character(preview.get("subject_character_id")).equals(query.subject()),
                    "observed native preview differs from requested subject");
            StrictJson.require(bool(preview.get("requested_matrilineal_option")) == query.requestMatrilinealOption(),
                    "observed native preview differs from requested option");
            Preview normalized;
            String status = text(preview.get("status"));
            String reason = textAllowEmpty(preview.get("reason"));
            if (status.equals("available")) {
                normalized = new AvailablePreview(bool(preview.get("selected_matrilineal_option")),
                        bool(preview.get("effective_matrilineal_if_accepted")),
                        bool(preview.get("complete_can_send")), dynasty(preview.get("dynasty_id")));
            } else {
                StrictJson.require(status.equals("unavailable"), "requested preview status must be available or unavailable");
                normalized = new UnavailablePreview(reason);
            }
            PreviewObservation observation = new PreviewObservation(nonnegative(observed.get("queried_native_revision")),
                    integer(object(observed.get("frame")).get("date_raw")),
                    character(preview.get("subject_character_id")), character(preview.get("candidate_character_id")), normalized);
            consumed.add(observed);
            queries.add(query);
            return observation;
        });
        ObjectNode output = StrictJson.object();
        if (selection.orderedOrdinal().isPresent()) {
            ObjectNode chosen = object(orderedChoices.get(selection.orderedOrdinal().getAsInt())).deepCopy();
            chosen.put("dynasty_continuity_source", "native_child_house_preview");
            chosen.set("native_child_house_preview", consumed.get(consumed.size() - 1).deepCopy());
            output.set("choice", chosen);
        } else {
            output.putNull("choice");
        }
        ArrayNode observations = output.putArray("observations");
        for (int ordinal = 0; ordinal < selection.attempts().size(); ordinal++) {
            var attempt = selection.attempts().get(ordinal);
            ObjectNode result = observations.addObject();
            result.put("candidate_character_id", attempt.request().candidate().value());
            result.put("reason", attempt.reason());
            result.set("observation", consumed.get(ordinal).deepCopy());
        }
        return new Evaluation(StrictJson.canonical(output), queries);
    }

    private static ObjectNode object(JsonNode value) {
        StrictJson.require(value instanceof ObjectNode, "object required");
        return (ObjectNode) value;
    }
    private static ArrayNode array(JsonNode value) {
        StrictJson.require(value instanceof ArrayNode && value.size() <= 5, "bounded existing five-row array required");
        return (ArrayNode) value;
    }
    private static BigInteger integer(JsonNode value) {
        StrictJson.require(value != null && value.isIntegralNumber(), "exact integer token required");
        return value.bigIntegerValue();
    }
    private static BigInteger nonnegative(JsonNode value) {
        BigInteger number = integer(value);
        StrictJson.require(number.signum() >= 0, "nonnegative revision required");
        return number;
    }
    private static CharacterId character(JsonNode value) {
        BigInteger id = integer(value);
        StrictJson.require(id.signum() > 0 && id.compareTo(BigInteger.ONE.shiftLeft(32)) < 0,
                "full uint32 character ID required");
        return new CharacterId(id.longValueExact());
    }
    private static Optional<DynastyId> dynasty(JsonNode value) {
        StrictJson.require(value != null, "nullable dynasty field is required");
        if (value.isNull()) { return Optional.empty(); }
        BigInteger id = integer(value);
        StrictJson.require(id.signum() >= 0, "nonnegative dynasty ID required");
        return Optional.of(new DynastyId(id));
    }
    private static boolean bool(JsonNode value) {
        StrictJson.require(value != null && value.isBoolean(), "actual boolean token required");
        return value.booleanValue();
    }
    private static String text(JsonNode value) { return StrictJson.text(value); }
    private static String textAllowEmpty(JsonNode value) {
        StrictJson.require(value != null && value.isTextual(), "native reason string required");
        if (!value.textValue().isEmpty()) { StrictJson.text(value.textValue()); }
        return value.textValue();
    }
}
