package org.xar.ck3.control.contracts.projection;

import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class ProjectionHostContextTest {
    private static final byte[] PAYLOAD = "{}".getBytes(StandardCharsets.UTF_8);

    @Test void fixedContextRejectsUnknownMachineRelativeAndOverlappingRoots() {
        Path state = Path.of("fixture-state").toAbsolutePath();
        Path stock = Path.of("fixture-stock").toAbsolutePath();
        assertThrows(IllegalArgumentException.class, () -> new EventSourceReadContext("unknown", state, stock));
        assertThrows(IllegalArgumentException.class, () -> new EventSourceReadContext("fixture-machine", Path.of("relative"), stock));
        assertThrows(IllegalArgumentException.class, () -> new EventSourceReadContext("fixture-machine", state, state.resolve("stock")));
        var context = new ProjectionHostContext(Optional.of(new EventSourceReadContext("fixture-machine", state, stock)));
        assertEquals(state.normalize(), context.eventSources().orElseThrow().stateRoot());
    }

    @Test void existingPureCatalogUsesItsOriginalSingleRegistrationPath() {
        AtomicInteger invocations = new AtomicInteger();
        ProjectionPortCatalog catalog = () -> { invocations.incrementAndGet(); return List.of(); };
        assertTrue(catalog.registrations(ProjectionHostContext.empty()).isEmpty());
        assertEquals(1, invocations.get());
    }

    @Test void contextualUnavailableKeepsItsIdentityAndCannotBecomeABusinessRefusal() {
        var port = new ProjectionPort<ProjectionJson, ProjectionJson>() {
            public ProjectionOperation operation() { return ProjectionOperation.EVENTS_UNHANDLED_PLAN_SOURCE_REVIEWED; }
            public ProjectionJson decode(byte[] raw) { return ProjectionJson.object(raw, 65536); }
            public ProjectionJson project(ProjectionJson input) {
                throw new ProjectionProtocolException(ProjectionError.Code.OPERATION_UNAVAILABLE, "source roots drifted");
            }
            public byte[] encode(ProjectionJson result) { return result.bytes(); }
        };
        var identity = new ProjectionCall.Identity("context-unavailable", port.operation());
        var result = assertInstanceOf(ProjectionResult.Rejected.class, RegisteredProjection.of(port)
                .execute(new ProjectionCall(identity, ProjectionJson.object(PAYLOAD, 65536))));
        assertEquals(ProjectionError.Code.OPERATION_UNAVAILABLE, result.error().code());
        assertEquals(Optional.of(identity), result.identity());
        var roundTrip = assertInstanceOf(ProjectionResult.Rejected.class, ProjectionWire.decodeResult(ProjectionWire.encodeResult(result)));
        assertEquals(result, roundTrip);
    }
}
