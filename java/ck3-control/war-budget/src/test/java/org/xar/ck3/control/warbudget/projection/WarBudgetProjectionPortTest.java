package org.xar.ck3.control.warbudget.projection;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.charset.StandardCharsets;
import java.util.ServiceLoader;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionDispatcher;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.ProjectionWire;
import org.xar.ck3.control.warbudget.WarBudgetCodec;

final class WarBudgetProjectionPortTest {
    private static final byte[] PRIORITY = ("{\"schema\":\"g2.war-budget-request/v1\","
            + "\"operation\":\"priority_emergency_level_v1\",\"arguments\":{\"war\":{}}}")
            .getBytes(StandardCharsets.UTF_8);

    @Test void serviceLoadedCatalogDispatchesThroughTheActualTypedDomainAndRetainsScalarOutput() {
        ProjectionDispatcher dispatcher = ProjectionDispatcher.fromCatalogs(ServiceLoader.load(ProjectionPortCatalog.class));
        ProjectionCall call = call(PRIORITY);
        ProjectionResult.Succeeded result = assertInstanceOf(ProjectionResult.Succeeded.class,
                dispatcher.dispatch(ProjectionWire.encodeCall(call)));
        assertEquals(call.identity(), result.identity());
        assertArrayEquals(WarBudgetCodec.evaluate(PRIORITY), result.result().bytes());
        assertTrue(!result.result().isObject(), "priority remains an original scalar, not an invented object wrapper");
        ProjectionDispatcher.OperationProfile profile = dispatcher.profiles().stream()
                .filter(item -> item.operation() == ProjectionOperation.WAR_BUDGET_EVALUATE).findFirst().orElseThrow();
        assertEquals(65_536, profile.inputMaximumBytes()); assertEquals(16_384, profile.outputMaximumBytes());
        assertNotNull(getClass().getResource("/META-INF/services/org.xar.ck3.control.contracts.projection.ProjectionPortCatalog"));
    }

    @Test void malformedDomainPayloadAndOversizedRoleAreRejectedByTheRegisteredBoundary() {
        ProjectionDispatcher dispatcher = ProjectionDispatcher.fromCatalogs(ServiceLoader.load(ProjectionPortCatalog.class));
        byte[] missing = "{\"schema\":\"g2.war-budget-request/v1\"}".getBytes(StandardCharsets.UTF_8);
        ProjectionResult.Rejected invalid = assertInstanceOf(ProjectionResult.Rejected.class,
                dispatcher.dispatch(ProjectionWire.encodeCall(call(missing))));
        assertEquals(ProjectionError.Code.INVALID_PAYLOAD, invalid.error().code());
        byte[] oversized = ("{" + " ".repeat(65_536) + new String(PRIORITY, StandardCharsets.UTF_8).substring(1))
                .getBytes(StandardCharsets.UTF_8);
        ProjectionResult.Rejected refused = assertInstanceOf(ProjectionResult.Rejected.class,
                dispatcher.dispatch(ProjectionWire.encodeCall(call(oversized))));
        assertEquals(ProjectionError.Code.PAYLOAD_TOO_LARGE, refused.error().code());
    }

    private static ProjectionCall call(byte[] raw) {
        return new ProjectionCall(new ProjectionCall.Identity("budget-port-test", ProjectionOperation.WAR_BUDGET_EVALUATE),
                ProjectionJson.object(raw, ProjectionJson.MAX_BYTES));
    }
}
