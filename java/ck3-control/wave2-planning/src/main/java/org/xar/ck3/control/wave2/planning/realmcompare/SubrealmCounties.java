package org.xar.ck3.control.wave2.planning.realmcompare;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertModel;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionSubrealmCodec;

/** The exact optional county component, never a full faction query qualification. */
public record SubrealmCounties(boolean complete, int actorCharacterId, BigInteger nativeRevision,
        int dateRaw, List<Integer> countyTitleIds, String unavailableReason) {
    public static final String COMPONENT = FactionSubrealmCodec.COMPONENT;
    public static final String SCOPE = FactionSubrealmCodec.SCOPE;
    public static final String SOURCE = FactionSubrealmCodec.SOURCE;

    public SubrealmCounties {
        require(actorCharacterId > 0 && nativeRevision != null && nativeRevision.signum() > 0
                && nativeRevision.compareTo(StrictJson.UINT64_MAX) <= 0, "component owner/revision required");
        if (complete) {
            require(countyTitleIds != null && countyTitleIds.size() <= 16_384 && unavailableReason == null,
                    "complete component requires its exact bounded set");
            countyTitleIds = List.copyOf(countyTitleIds);
            int previous = 0;
            for (int identity : countyTitleIds) {
                require(identity > previous, "county IDs must be sorted unique positive full IDs");
                previous = identity;
            }
        } else {
            require(countyTitleIds == null && unavailableReason != null && !unavailableReason.isEmpty()
                    && unavailableReason.codePointCount(0, unavailableReason.length()) <= 256,
                    "incomplete component cannot expose a partial set");
            StrictJson.text(unavailableReason);
        }
    }

    public static SubrealmCounties parse(JsonNode raw, int actor, BigInteger nativeRevision, int dateRaw) {
        return switch (FactionSubrealmCodec.parse(raw, actor, nativeRevision, dateRaw)) {
            case FactionAlertModel.CompleteCounties full -> new SubrealmCounties(true, actor, nativeRevision, dateRaw, full.countyTitleIds(), null);
            case FactionAlertModel.IncompleteCounties missing -> new SubrealmCounties(false, actor, nativeRevision, dateRaw, null, missing.unavailableReason());
        };
    }

    public ObjectNode toJson() {
        FactionAlertModel.SubrealmCounties component = complete ? new FactionAlertModel.CompleteCounties(countyTitleIds)
                : new FactionAlertModel.IncompleteCounties(unavailableReason);
        return FactionSubrealmCodec.toJson(component, actorCharacterId, nativeRevision, dateRaw);
    }

    static BigInteger integer(JsonNode value, String field, BigInteger minimum, BigInteger maximum) {
        if (value == null || !value.isIntegralNumber() || value.bigIntegerValue().compareTo(minimum) < 0
                || value.bigIntegerValue().compareTo(maximum) > 0) {
            throw refused(field + " must be an integer in [" + minimum + ", " + maximum + "]");
        }
        return value.bigIntegerValue();
    }
    static boolean text(JsonNode value, String expected) { return value != null && value.isTextual() && expected.equals(value.textValue()); }
    static ContractViolationException refused(String reason) { return new ContractViolationException(reason); }
}
