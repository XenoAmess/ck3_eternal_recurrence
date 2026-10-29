package org.xar.ck3.control.service;

import jakarta.enterprise.context.ApplicationScoped;
import java.util.Objects;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.context.G2CallContextProducer;

/** Future graph only. The default binding has no provider; HTTP cannot install one. */
@ApplicationScoped
public class G2CallContextHost {
    private final G2CallContextProducer.RootBinding binding;

    public G2CallContextHost() { this(new G2CallContextProducer.RootBinding()); }

    public G2CallContextHost(G2CallContextProducer.RootBinding binding) { this.binding = Objects.requireNonNull(binding); }

    /** The unique trusted Root Java bootstrap calls this; there is no HTTP installation endpoint. */
    public void installRootProvider(G2CallContextProducer.Provider provider) { binding.install(Objects.requireNonNull(provider)); }

    public G2CallContextProducer.Result context(Milestone milestone, ProjectionJson payload) {
        return binding.context(Objects.requireNonNull(milestone), Objects.requireNonNull(payload));
    }
}
