package org.xar.ck3.control.score;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact Interval.export JSON ABI. This is a pure codec, with no HTTP or game adapter. */
public final class CampaignScoreCodec {
    private static final Set<String> INTERVAL_FIELDS = Set.of("lower", "upper", "known", "value");
    private CampaignScoreCodec() { }

    public static ScoreInterval decodeInterval(byte[] raw) { return interval(StrictJson.parse(raw)); }
    public static byte[] encodeInterval(ScoreInterval value) { return StrictJson.canonical(json(value)); }

    public static ScoreInterval interval(JsonNode node) {
        ObjectNode row = StrictJson.object(node, INTERVAL_FIELDS);
        ScoreInterval result = new ScoreInterval(decimal(row.get("lower")), decimal(row.get("upper")));
        JsonNode known = row.get("known");
        StrictJson.require(known.isBoolean() && known.booleanValue() == result.known(), "interval known flag mismatch");
        JsonNode value = row.get("value");
        if (result.known()) {
            StrictJson.require(value.isTextual() && result.lower().lexical().equals(value.textValue()), "exact interval value mismatch");
        } else { StrictJson.require(value.isNull(), "unknown interval value must be explicit null"); }
        return result;
    }

    public static ObjectNode json(ScoreInterval interval) {
        ObjectNode result = StrictJson.object();
        result.put("lower", interval.lower().lexical()); result.put("upper", interval.upper().lexical());
        result.put("known", interval.known());
        if (interval.known()) { result.put("value", interval.lower().lexical()); }
        else { result.putNull("value"); }
        return result;
    }

    public static DomainScores domainScores(JsonNode node) {
        ObjectNode row = StrictJson.object(node, Set.of("L", "E", "M", "U", "D", "H"));
        return new DomainScores(interval(row.get("L")), interval(row.get("E")), interval(row.get("M")),
                interval(row.get("U")), interval(row.get("D")), interval(row.get("H")));
    }

    /** Single domain-field producer for arithmetic and state-score consumers. */
    public static ObjectNode json(DomainScores scores) {
        ObjectNode row = StrictJson.object();
        row.set("L", json(scores.land())); row.set("E", json(scores.economy()));
        row.set("M", json(scores.military())); row.set("U", json(scores.stability()));
        row.set("D", json(scores.dynasty())); row.set("H", json(scores.heirs()));
        return row;
    }

    public static MonthlyHistory history(JsonNode node) {
        ObjectNode row = StrictJson.object(node, Set.of("samples", "endpoint"));
        JsonNode samples = row.get("samples");
        StrictJson.require(samples.isArray() && samples.size() == 360, "exactly 360 fixed month slots required");
        List<ScoreInterval> parsed = new ArrayList<>(360);
        samples.forEach(sample -> parsed.add(interval(sample)));
        return new MonthlyHistory(parsed, interval(row.get("endpoint")));
    }

    public static ScoreDecimal decimal(JsonNode node) { return ScoreDecimal.parse(StrictJson.text(node)); }
}
