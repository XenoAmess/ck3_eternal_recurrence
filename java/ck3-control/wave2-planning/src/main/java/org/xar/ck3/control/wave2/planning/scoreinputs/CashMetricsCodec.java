package org.xar.ck3.control.wave2.planning.scoreinputs;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;

/** Data-only adapter to the actual shared cash validator and complete four-rate projection. */
public final class CashMetricsCodec {
    private CashMetricsCodec() { }

    /** Validated wrapper values retain exact JSON token categories until the shared producer consumes them. */
    public record Request(byte[] packetJson, byte[] snapshotJson) {
        public Request {
            StrictJson.require(packetJson != null && snapshotJson != null, "original packet and snapshot JSON required");
            packetJson = packetJson.clone(); snapshotJson = snapshotJson.clone();
        }
        @Override public byte[] packetJson() { return packetJson.clone(); }
        @Override public byte[] snapshotJson() { return snapshotJson.clone(); }
        public CashProjection project() { return CashProjection.fromPacket(packetJson(), snapshotJson()); }
    }

    public static Request decodeRequest(byte[] input) {
        ObjectNode request = StrictJson.object(StrictJson.parse(input), Set.of("packet", "snapshot"));
        return new Request(SdkProjectionJson.encode(request.get("packet")),
                SdkProjectionJson.encode(request.get("snapshot")));
    }
    public static CashProjection decode(byte[] input) { return decodeRequest(input).project(); }
    public static byte[] encode(CashProjection result) { return StrictJson.canonical(result.toJson()); }
    public static byte[] evaluate(byte[] input) { return encode(decode(input)); }
}
