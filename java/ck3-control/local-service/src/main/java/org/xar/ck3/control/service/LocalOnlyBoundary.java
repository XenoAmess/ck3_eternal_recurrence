package org.xar.ck3.control.service;

import io.quarkus.runtime.StartupEvent;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.event.Observes;
import org.eclipse.microprofile.config.ConfigProvider;

/** Keep this first producer on the explicitly supported IPv4 loopback interface. */
@ApplicationScoped
public class LocalOnlyBoundary {
    void verifyBinding(@Observes StartupEvent event) {
        String host = ConfigProvider.getConfig().getValue("quarkus.http.host", String.class);
        if (!"127.0.0.1".equals(host)) {
            throw new IllegalStateException("CK3 control requires quarkus.http.host=127.0.0.1");
        }
    }
}
