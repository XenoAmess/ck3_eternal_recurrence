package org.xar.ck3.control.g2.m1;

import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.context.G2CallContextProducer;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider;

/**
 * M1's trusted Root bootstrap adapter. Only the installed Root context provider
 * supplies provenance; operation input never becomes a source, clock or build.
 */
public final class M1RootRequestSupplier {
    public sealed interface Result permits Prepared, Unavailable { }
    public record Prepared(G2Request request) implements Result {
        public Prepared {
            Objects.requireNonNull(request, "prepared M1 request");
            StrictJson.require(request.milestone() == Milestone.M1, "prepared M1 request milestone required");
        }
    }
    public record Unavailable(G2CallContextProducer.Unavailable sourceFailure) implements Result {
        public Unavailable { Objects.requireNonNull(sourceFailure, "explicit Root source failure"); }
    }

    private final G2CallContextProducer.Provider root;

    /** The existing single host's Root binding is injected once by its bootstrap. */
    public M1RootRequestSupplier(G2CallContextProducer.RootBinding root) {
        this(Objects.requireNonNull(root, "existing Root context binding")::context);
    }

    /** Root passes actualG2CallContextHost::context to consume that host's existing binding. */
    public M1RootRequestSupplier(G2CallContextProducer.Provider root) {
        this.root = Objects.requireNonNull(root, "existing same-host Root context provider");
    }

    public Result prepare(M1Operation operation, byte[] originalInputJson) {
        ProjectionJson payload = Objects.requireNonNull(operation, "M1 operation").payload(originalInputJson);
        G2CallContextProducer.Result result = Objects.requireNonNull(root.context(Milestone.M1, payload),
                "explicit Root context result required");
        return switch (result) {
            case G2CallContextProducer.Available available -> {
                G2CallContextProducer.Context context = available.context();
                if (!context.payloadSha256().equals(G2RetainedNativeSourceProvider.sha256(payload.bytes()))) {
                    yield new Unavailable(new G2CallContextProducer.Unavailable(G2CallContextProducer.Reason.SOURCE_REJECTED,
                            "Root context does not bind the original M1 payload bytes"));
                }
                yield new Prepared(new G2Request(context.requestId(), Milestone.M1, context.source(), payload));
            }
            case G2CallContextProducer.Unavailable unavailable -> new Unavailable(unavailable);
        };
    }
}
