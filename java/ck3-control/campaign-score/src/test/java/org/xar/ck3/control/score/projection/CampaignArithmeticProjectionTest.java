package org.xar.ck3.control.score.projection;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.ServiceLoader;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.*;
import org.xar.ck3.control.score.CampaignArithmeticCodec;

final class CampaignArithmeticProjectionTest {
    private static final String PREFIX = "{\"schema\":\"g2.campaign-score-arithmetic/v1\","
            + "\"profile\":\"python-decimal-default-28-half-even/v1\",\"operation\":\"display\",\"input\":";

    @Test void registeredWirePreservesTiesSignedZeroAndExactOutputKind() {
        for (String value : List.of("1.005", "1.015", "-0.0001", "1E+2")) {
            byte[] raw = bytes(PREFIX + "{\"lower\":\"" + value + "\",\"upper\":\"" + value + "\",\"places\":2}}");
            ProjectionResult.Succeeded succeeded = assertInstanceOf(ProjectionResult.Succeeded.class, dispatch(raw));
            assertArrayEquals(CampaignArithmeticCodec.evaluate(raw), succeeded.result().bytes());
            assertTrue(StrictJson.parse(succeeded.result().bytes()).isTextual(), "display result remains JSON scalar");
        }
    }

    @Test void rawTokenTypesProfileMismatchAndDomainQuantizeFailureRemainDifferent() {
        for (String token : List.of("true", "1.0", "null", "\"2\"")) {
            ProjectionResult.Rejected rejected = assertInstanceOf(ProjectionResult.Rejected.class,
                    dispatch(bytes(PREFIX + "{\"lower\":\"1\",\"upper\":\"2\",\"places\":" + token + "}}")));
            assertEquals(ProjectionError.Code.INVALID_PAYLOAD, rejected.error().code());
        }
        byte[] wrong = bytes((PREFIX + "{\"lower\":\"1\",\"upper\":\"2\",\"places\":2}}")
                .replace("python-decimal-default-28-half-even/v1", "python-ROUND_UP"));
        assertEquals(ProjectionError.Code.INVALID_PAYLOAD,
                assertInstanceOf(ProjectionResult.Rejected.class, dispatch(wrong)).error().code());
        byte[] domain = bytes(PREFIX + "{\"lower\":\"1E+80\",\"upper\":\"1E+80\",\"places\":2}}");
        assertEquals(ProjectionError.Code.DOMAIN_REJECTED,
                assertInstanceOf(ProjectionResult.Rejected.class, dispatch(domain)).error().code());
    }

    private static ProjectionResult dispatch(byte[] raw) {
        ProjectionDispatcher dispatcher = ProjectionDispatcher.fromCatalogs(ServiceLoader.load(ProjectionPortCatalog.class));
        ProjectionCall call = new ProjectionCall(new ProjectionCall.Identity("arithmetic-wire-test",
                ProjectionOperation.CAMPAIGN_ARITHMETIC_EVALUATE), ProjectionJson.object(raw, 65536));
        assertArrayEquals(raw, call.payload().bytes()); return dispatcher.dispatch(ProjectionWire.encodeCall(call));
    }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}
