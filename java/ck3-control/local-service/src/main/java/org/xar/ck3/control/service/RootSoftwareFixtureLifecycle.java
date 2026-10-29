package org.xar.ck3.control.service;

import io.quarkus.runtime.StartupEvent;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.event.Observes;
import java.io.IOException;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.build.RootSoftwareFixtureHandoff;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.context.DeferredRootSoftwareFixtureProvider;

/** Optional trusted startup only; default Root binding remains empty. */
@ApplicationScoped
public class RootSoftwareFixtureLifecycle {
    private final Optional<String> origin;
    private final Optional<String> pending;
    public RootSoftwareFixtureLifecycle() {
        this(Optional.ofNullable(System.getProperty("xar.root.software-fixture.origin")),
                Optional.ofNullable(System.getProperty(RootSoftwareFixtureHandoff.PROPERTY)));
    }
    public RootSoftwareFixtureLifecycle(Optional<String> origin) { this(origin, Optional.empty()); }
    public RootSoftwareFixtureLifecycle(Optional<String> origin, Optional<String> pending) {
        this.origin = Objects.requireNonNull(origin); this.pending = Objects.requireNonNull(pending);
        if (origin.isPresent() && pending.isPresent()) throw new IllegalArgumentException("one explicit Root software startup mode required");
    }
    void start(@Observes StartupEvent event, G2CallContextHost host) throws IOException {
        if (pending.isPresent()) host.installRootProvider(DeferredRootSoftwareFixtureProvider.load(reference(pending.orElseThrow())));
        else if (origin.isPresent()) host.installRootProvider(org.xar.ck3.control.g2.context.G2SoftwareFixtureSourceProvider.load(reference(origin.orElseThrow())));
    }
    private static ExactRef reference(String json) {
        return ExactRef.fromJson(StrictJson.parse(json.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
    }
}
