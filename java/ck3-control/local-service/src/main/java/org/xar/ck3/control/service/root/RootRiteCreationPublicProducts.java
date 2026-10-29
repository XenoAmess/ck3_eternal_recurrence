package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.ritecreation.RiteCreationCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.service.mcp.RootMcpRiteCreation;

/** Three original conditional direct methods, supplied without a pre-Core RootSessionAccess. */
public final class RootRiteCreationPublicProducts {
    private RootRiteCreationPublicProducts() { }
    public static RootPublicHandlerProductsFactory.Contribution install(
            RootPublicHandlerProductsFactory.Context context,PublicBindings registry)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(registry);
        context.source(RootRiteCreationPublicProducts.class);
        var adapter=context.source(RootMcpRiteCreation.class);
        context.source(RootRiteCreationRuntimeFactory.class);
        context.source(RootRuntimeSelectedSources.Module.APPLICATION,RiteCreationCodec.class);
        // The sole route/decoder/encoder table invokes this typed supplier only after an actual request.
        var methods=RootMcpRiteCreation.suppliedMethods(adapter,context::ritePublicServices);
        return new RootPublicHandlerProductsFactory.Contribution(methods,List.of(),List.of());
    }
}
