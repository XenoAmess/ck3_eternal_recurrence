package org.xar.ck3.control.wave2.military.projection;

import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.*;
import static org.junit.jupiter.api.Assertions.*;

/** Host04 classification only; original whole oracle modules and all county 18/43 cases remain mandatory. */
final class HolyHost04BoundaryTest {
    private static byte[] raw(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static ProjectionCall call(ProjectionOperation operation, String body) {
        return new ProjectionCall(new ProjectionCall.Identity("military-host04", operation),
                ProjectionJson.object(raw(body), 131072));
    }
    private static void code(RegisteredProjection port, String body, ProjectionError.Code expected) {
        assertEquals(expected, assertInstanceOf(ProjectionResult.Rejected.class,
                port.execute(call(port.operation(), body))).error().code());
    }
    @Test void movementInputGuardsRemainDecodeFailures() {
        for (var port : MovementProjectionPorts.registrations()) {
            code(port, "{}", ProjectionError.Code.INVALID_PAYLOAD);
        }
    }
    @Test void outerWireErrorsRemainDecodeFailures() {
        var port = RegisteredProjection.of(new HolyConsumerPorts.HirePort(ProjectionOperation.MILITARY_HOLY_HIRE));
        for (String body : new String[]{"{}", "{\"operation\":true,\"request\":{}}",
                "{\"operation\":\"REQUEST\",\"request\":{}}",
                "{\"operation\":\"query\",\"stage\":\"retry\",\"request\":{}}"}) {
            code(port, body, ProjectionError.Code.INVALID_PAYLOAD);
        }
    }
    @Test void everyHolyInnerBranchUsesExplicitDomainGuards() {
        var ports = HolyConsumerPorts.registrations(new HolyConsumerPorts.Operations(
                ProjectionOperation.MILITARY_HOLY_REINFORCEMENT, ProjectionOperation.MILITARY_HOLY_HIRE));
        String[] reinf = {"\"choose\"", "\"plan\",\"stage\":\"prepare\"",
                "\"plan\",\"stage\":\"fold\"", "\"postcondition\",\"stage\":\"validate\"",
                "\"postcondition\",\"stage\":\"prepare\"", "\"postcondition\",\"stage\":\"fold\""};
        String[] hire = {"\"request\"", "\"ack\"", "\"query\",\"stage\":\"context\"",
                "\"query\",\"stage\":\"envelope\""};
        for (String branch : reinf) { code(ports.get(0), "{\"operation\":" + branch + ",\"request\":{}}", ProjectionError.Code.DOMAIN_REJECTED); }
        for (String branch : hire) { code(ports.get(1), "{\"operation\":" + branch + ",\"request\":{}}", ProjectionError.Code.DOMAIN_REJECTED); }
        for (String token : new String[]{"true", "1.0", "\"1\"", "null"}) {
            code(ports.get(1), "{\"operation\":\"request\",\"request\":{\"schema\":\"xar.ck3.holy-hire-request-input.v1\",\"holy_order_id\":" + token
                    + ",\"expected_revision\":1}}", ProjectionError.Code.DOMAIN_REJECTED);
        }
    }
    @Test void algorithmAndSerializerBugsRemainInternal() {
        for (boolean serializer : new boolean[]{false, true}) {
            var port = new ProjectionPort<byte[], byte[]>() {
                public ProjectionOperation operation() { return ProjectionOperation.MILITARY_HOLY_HIRE; }
                public int inputMaximumBytes() { return 131072; }
                public int outputMaximumBytes() { return 131072; }
                public byte[] decode(byte[] value) { return value; }
                public byte[] project(byte[] value) {
                    if (serializer) { return StrictJson.canonical(StrictJson.parse(raw("1.0"))); }
                    throw new IllegalArgumentException("internal algorithm fault");
                }
                public byte[] encode(byte[] value) { return value; }
            };
            code(RegisteredProjection.of(port), "{}", ProjectionError.Code.PROJECTION_FAILED);
        }
    }
}
