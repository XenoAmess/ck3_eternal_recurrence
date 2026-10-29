package org.xar.ck3.control.wave3.planning.scorestate;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.EnumMap;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.score.CampaignScoreCodec;
import org.xar.ck3.control.score.DomainScores;

/** New strict envelope, projected legacy metric packets, exact legacy score export. */
public final class StateScoreCodec {
    private StateScoreCodec() { }
    public static StateScoreInput decode(byte[] raw) {
        ObjectNode row = StrictJson.object(StrictJson.parse(raw), Set.of("current", "baseline"));
        return new StateScoreInput(packet(row.get("current")), packet(row.get("baseline")));
    }
    public static MetricPacket packet(JsonNode node) {
        StrictJson.require(node != null && node.isObject(), "metric packet object required");
        EnumMap<MetricName, MetricRow> rows = new EnumMap<>(MetricName.class);
        for (MetricName name : MetricName.values()) {
            JsonNode value = node.get(name.wire());
            if (value != null) { rows.put(name, row(value)); }
        }
        return new MetricPacket(rows);
    }
    private static MetricRow row(JsonNode value) {
        if (value.isNull()) { return new MetricRow.NullValue(); }
        if (!value.isObject()) { return new MetricRow.NonObject(kind(value)); }
        return new MetricRow.Fields(scalar(value.get("availability")), scalar(value.get("unit")),
                scalar(value.get("value")), scalar(value.get("lower")), scalar(value.get("upper")));
    }
    private static MetricScalar scalar(JsonNode value) {
        if (value == null) { return new MetricScalar.Missing(); }
        if (value.isNull()) { return new MetricScalar.NullValue(); }
        if (value.isTextual()) { return new MetricScalar.Text(value.textValue()); }
        if (value.isIntegralNumber()) { return new MetricScalar.IntegerValue(value.bigIntegerValue()); }
        return new MetricScalar.Unsupported(kind(value));
    }
    private static MetricScalar.TokenKind kind(JsonNode value) {
        if (value.isArray()) { return MetricScalar.TokenKind.ARRAY; }
        if (value.isObject()) { return MetricScalar.TokenKind.OBJECT; }
        if (value.isBoolean()) { return MetricScalar.TokenKind.BOOLEAN; }
        if (value.isTextual()) { return MetricScalar.TokenKind.STRING; }
        if (value.isIntegralNumber()) { return MetricScalar.TokenKind.INTEGER; }
        return MetricScalar.TokenKind.FRACTIONAL;
    }
    public static ObjectNode json(DomainScores scores) {
        return CampaignScoreCodec.json(scores);
    }
    public static byte[] encode(DomainScores scores) { return StrictJson.canonical(json(scores)); }
}
