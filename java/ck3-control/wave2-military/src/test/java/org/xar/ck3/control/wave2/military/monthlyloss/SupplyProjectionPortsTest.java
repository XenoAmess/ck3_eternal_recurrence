package org.xar.ck3.control.wave2.military.monthlyloss;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.ServiceLoader;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.*;

final class SupplyProjectionPortsTest {
    private static ProjectionOperation operation() {
        return ProjectionOperation.fromWire("military-supply-consumer");
    }
    private static RegisteredProjection port() {
        return SupplyProjectionPorts.registrations(operation()).getFirst();
    }
    private static ProjectionResult execute(String payload) {
        return port().execute(new ProjectionCall(new ProjectionCall.Identity("supply-real-port", operation()),
                ProjectionJson.object(payload.getBytes(StandardCharsets.UTF_8), 262_144)));
    }
    private static String request(String operation, String arguments) {
        return "{\"schema\":\"xar.military-supply-consumer-request/v1\",\"operation\":\""
                + operation + "\",\"arguments\":" + arguments + "}";
    }
    @Test void spi() {
        var catalogs = ServiceLoader.load(ProjectionPortCatalog.class).stream()
                .filter(value -> value.type().getName().equals("org.xar.ck3.control.wave2.military.projection.MilitaryProjectionPortCatalog"))
                .map(ServiceLoader.Provider::get).toList();
        assertEquals(1, catalogs.size());
        var ports = catalogs.getFirst().registrations().stream().filter(value -> value.operation() == operation()).toList();
        assertEquals(1, ports.size());
        assertEquals(131_072, ports.getFirst().inputMaximumBytes());
        assertEquals(131_072, ports.getFirst().outputMaximumBytes());
        assertThrows(NullPointerException.class, () -> SupplyProjectionPorts.registrations(null));
    }
    @Test void immutable() {
        var arguments = StrictJson.object(); arguments.putNull("family");
        arguments.putNull("expected_army_id"); arguments.putNull("expected_carmy_id");
        var input = new SupplyConsumerBindings.Request(SupplyConsumerBindings.Operation.NORMALIZE_SCHEDULE, arguments);
        arguments.put("external_mutation", true); input.arguments().put("another_mutation", true);
        assertEquals(3, input.arguments().size());
        assertThrows(NullPointerException.class, () -> SupplyConsumerBindings.exchange((SupplyConsumerBindings.Request) null));
        assertInstanceOf(ProjectionResult.Succeeded.class, execute(request("NORMALIZE_SCHEDULE",
                "{\"family\":null,\"expected_army_id\":null,\"expected_carmy_id\":null}")));
    }
    @Test void reject() {
        for (String payload : List.of("{}", "{\"schema\":true}", request("UNKNOWN", "{}"),
                request("SUCCESSFUL_OCCURRENCES", "null"),
                request("SUCCESSFUL_OCCURRENCES", "{\"stock\":0,\"capacity\":0}"),
                request("SUCCESSFUL_OCCURRENCES", "{\"stock\":0,\"capacity\":0,\"monthly\":0,\"extra\":null}"))) {
            var rejected = assertInstanceOf(ProjectionResult.Rejected.class, execute(payload));
            assertEquals(ProjectionError.Code.INVALID_PAYLOAD, rejected.error().code());
        }
    }
    @Test void validEnvelopesKeepDomainInputRejectionsSeparateFromProtocolErrors() {
        for (String inner : List.of("MONTHLY_BUDGETS", "LOSS_SEQUENCE", "FLEET_BUDGET", "NATIVE_NEXT_SCHEDULE", "ZERO_CALLBACK"))
            domain(inner, "{\"row\":true}");
        domain("ASSOCIATED_WRITER", "{\"row\":true,\"writer_request\":{}}");
        domain("SUPPLY_COMPONENT", "{\"result\":true,\"inputs\":{},\"losses\":{}}");
        domain("FLEET_AT_STOCK", "{\"row\":{},\"stock\":null,\"stock_basis\":false,\"post_updater_stock_used\":false,\"stock_input_name\":null}");
        domain("NORMALIZE_SCHEDULE", "{\"family\":true,\"expected_army_id\":null,\"expected_carmy_id\":null}");
        domain("PROJECT_SCHEDULE", "{\"row_or_family\":true,\"prospective_frames\":[]}");
    }
    private static void domain(String inner, String arguments) {
        var rejected = assertInstanceOf(ProjectionResult.Rejected.class, execute(request(inner, arguments)));
        assertEquals(ProjectionError.Code.DOMAIN_REJECTED, rejected.error().code(), inner);
    }
    @Test void unknown() {
        assertThrows(IllegalArgumentException.class, () -> SupplyConsumerBindings.decodeRequest(request("SUCCESSFUL_OCCURRENCES",
                "{\"stock\":0,\"stock\":1,\"capacity\":0,\"monthly\":0}").getBytes(StandardCharsets.UTF_8)));
        for (String token : List.of("true", "1.0", "1e0", "\"1\"", "9223372036854775808", "null", "[]")) {
            var success = assertInstanceOf(ProjectionResult.Succeeded.class,
                    execute(request("SUCCESSFUL_OCCURRENCES", "{\"stock\":" + token + ",\"capacity\":100,\"monthly\":-1}")));
            var value = StrictJson.parse(success.result().bytes());
            assertFalse(value.path("ready").booleanValue());
            assertEquals("current_supply_raw", value.path("required_fields").get(0).textValue());
        }
    }
}
