package org.xar.ck3.control.contracts.projection;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/** One immutable registration table per resident host. Every dispatched payload reaches its domain codec first. */
public final class ProjectionDispatcher {
    public record OperationProfile(ProjectionOperation operation, int inputMaximumBytes, int outputMaximumBytes) { }
    private final EnumMap<ProjectionOperation, RegisteredProjection> registrations = new EnumMap<>(ProjectionOperation.class);

    public ProjectionDispatcher(List<RegisteredProjection> ports) {
        for (RegisteredProjection port : List.copyOf(ports)) {
            Objects.requireNonNull(port);
            if (registrations.putIfAbsent(port.operation(), port) != null) {
                throw new IllegalArgumentException("duplicate projection registration: " + port.operation().wire());
            }
        }
    }

    public static ProjectionDispatcher fromCatalogs(Iterable<ProjectionPortCatalog> catalogs) {
        List<RegisteredProjection> ports = new ArrayList<>();
        for (ProjectionPortCatalog catalog : catalogs) { ports.addAll(List.copyOf(catalog.registrations())); }
        return new ProjectionDispatcher(ports);
    }

    public List<OperationProfile> profiles() {
        return registrations.values().stream().map(port -> new OperationProfile(port.operation(),
                port.inputMaximumBytes(), port.outputMaximumBytes())).toList();
    }

    public ProjectionResult dispatch(byte[] raw) {
        ProjectionCall call;
        try { call = ProjectionWire.decodeCall(raw); }
        catch (ProjectionProtocolException error) {
            return new ProjectionResult.Rejected(Optional.empty(), new ProjectionError(error.code(), error.getMessage()));
        } catch (IllegalArgumentException error) {
            return new ProjectionResult.Rejected(Optional.empty(), new ProjectionError(ProjectionError.Code.INVALID_ENVELOPE, "invalid projection envelope"));
        }
        RegisteredProjection port = registrations.get(call.identity().operation());
        if (port == null) {
            return new ProjectionResult.Rejected(Optional.of(call.identity()),
                    new ProjectionError(ProjectionError.Code.OPERATION_UNAVAILABLE, "operation has no registered domain port in this qualified host"));
        }
        return port.execute(call);
    }
}
