package org.xar.ck3.control.wave2.military.actualcontact;

import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;

/** Domain ports for the one resident host; the central catalog owns wire names. */
public final class ContactProjectionPorts {
    private ContactProjectionPorts() { }

    public record Operations(ProjectionOperation inventory, ProjectionOperation routeWindow,
                             ProjectionOperation routeStep, ProjectionOperation actualScope,
                             ProjectionOperation actualQuery) {
        public Operations {
            Objects.requireNonNull(inventory); Objects.requireNonNull(routeWindow);
            Objects.requireNonNull(routeStep); Objects.requireNonNull(actualScope); Objects.requireNonNull(actualQuery);
            if (Set.of(inventory, routeWindow, routeStep, actualScope, actualQuery).size() != 5) {
                throw new IllegalArgumentException("contact operations must have distinct central registrations");
            }
        }
    }

    public static List<RegisteredProjection> registrations(Operations operations) {
        Objects.requireNonNull(operations);
        return List.of(
                port(operations.inventory(), ContactConsumerPort.Operation.INVENTORY),
                port(operations.routeWindow(), ContactConsumerPort.Operation.ROUTE_WINDOW),
                port(operations.routeStep(), ContactConsumerPort.Operation.ROUTE_STEP),
                port(operations.actualScope(), ContactConsumerPort.Operation.ACTUAL_SCOPE),
                port(operations.actualQuery(), ContactConsumerPort.Operation.ACTUAL_QUERY));
    }

    private static RegisteredProjection port(ProjectionOperation operation, ContactConsumerPort.Operation route) {
        return RegisteredProjection.of(new ContactPort(operation, route));
    }

    private record ContactPort(ProjectionOperation operation, ContactConsumerPort.Operation route)
            implements ProjectionPort<ContactConsumerPort.Request, ContactConsumerPort.Result> {
        @Override public int inputMaximumBytes() { return 65_536; }
        @Override public int outputMaximumBytes() { return 65_536; }
        @Override public ContactConsumerPort.Request decode(byte[] rawPayload) {
            ContactConsumerPort.Request input = new ContactConsumerPort.Request(route, rawPayload);
            ContactConsumerPort.validateRequest(input);
            return input;
        }
        @Override public ContactConsumerPort.Result project(ContactConsumerPort.Request input) {
            return ContactConsumerPort.apply(input);
        }
        @Override public byte[] encode(ContactConsumerPort.Result result) { return result.outputJson(); }
    }
}
