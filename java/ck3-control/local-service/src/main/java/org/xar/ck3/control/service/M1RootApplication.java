package org.xar.ck3.control.service;

import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import java.util.Objects;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.context.G2CallContextProducer;
import org.xar.ck3.control.g2.m1.M1Operation;
import org.xar.ck3.control.g2.m1.M1RootRequestSupplier;

/** Programmatic M1 entry in the existing single host; no HTTP provider-installation route. */
@ApplicationScoped
public class M1RootApplication {
    public sealed interface Result permits Evaluated, Unavailable { }
    public record Evaluated(G2Response response) implements Result {
        public Evaluated { Objects.requireNonNull(response); }
    }
    public record Unavailable(G2CallContextProducer.Unavailable sourceFailure) implements Result {
        public Unavailable { Objects.requireNonNull(sourceFailure); }
    }

    private final M1RootRequestSupplier supplier;
    private final G2ResearchHost research;

    @Inject public M1RootApplication(G2CallContextHost context, G2ResearchHost research) {
        this.supplier = new M1RootRequestSupplier(Objects.requireNonNull(context)::context);
        this.research = Objects.requireNonNull(research);
    }

    /**
     * Root calls within its qualified same-thread source scope. A scope cannot
     * be borrowed across HTTP workers; missing scope remains unavailable.
     */
    public Result evaluate(M1Operation operation, byte[] originalInputJson) {
        return switch (supplier.prepare(operation, originalInputJson)) {
            case M1RootRequestSupplier.Prepared prepared -> new Evaluated(research.evaluate(prepared.request()));
            case M1RootRequestSupplier.Unavailable unavailable -> new Unavailable(unavailable.sourceFailure());
        };
    }
}
