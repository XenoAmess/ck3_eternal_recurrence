package org.xar.ck3.control.contracts.projection;

import java.util.Objects;
import java.util.Optional;

/** Server assembly supplies capabilities; call JSON never creates either scope. */
public record ProjectionHostContext(Optional<EventSourceReadContext> eventSources, Optional<ProjectionArtifactInputScope> artifactInputs) {
    public ProjectionHostContext(Optional<EventSourceReadContext> eventSources) { this(eventSources, Optional.empty()); }
    public ProjectionHostContext { Objects.requireNonNull(eventSources); Objects.requireNonNull(artifactInputs); }
    public static ProjectionHostContext empty() { return new ProjectionHostContext(Optional.empty(), Optional.empty()); }
}
