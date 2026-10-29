package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.normalexit.NormalExitProtocol;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.service.mcp.NormalExitPublicCodec;

/** Normal-exit registration is supplied only by the source-qualified actual PLATFORM prepared product. */
public final class RootNormalExitPublicProducts {
    private final RootPublicHandlerProductsFactory.Context context;
    private RootNormalExitPublicProducts(RootPublicHandlerProductsFactory.Context context){this.context=Objects.requireNonNull(context);}
    public static RootPublicHandlerProductsFactory.Contribution install(RootPublicHandlerProductsFactory.Context context,
            PublicBindings registry,RootNormalExitRuntime.Prepared actual)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(registry);Objects.requireNonNull(actual);
        actual.source().requireCurrent(context);
        ExactRef source=context.source(RootNormalExitPublicProducts.class);
        context.source(NormalExitPublicCodec.class);context.source(RootNormalExitRuntime.class);
        context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,NormalExitProtocol.class);
        var product=new RootNormalExitPublicProducts(context);
        register(registry,product::observe,product::query,product::request,source);
        // RESTORE has its own dedicated Core route; PLATFORM source qualification grants only these three methods.
        return new RootPublicHandlerProductsFactory.Contribution(List.of(),List.of(),List.of());
    }
    public static RootPublicHandlerProductsFactory.Contribution unavailable(){
        String reason="actual source-qualified PLATFORM Prepared requires immutable original settings snapshot, source inventory and managed profile; no replacement/caller boolean grants process authority";
        return new RootPublicHandlerProductsFactory.Contribution(List.of(),List.of(),List.of(
                new RootRuntimePublicCatalog.DefinitionGap("observe_normal_exit_v1",reason),
                new RootRuntimePublicCatalog.DefinitionGap("query_normal_exit_context_v1",reason),
                new RootRuntimePublicCatalog.DefinitionGap("request_normal_exit_v1",reason)));
    }
    private RootNormalExitRuntime runtime(RootApplicationSession root)throws IOException{
        var installed=context.installed(root);var actual=installed.additionalDomains().driverRegistry().product(
                RootDriverRegistryPublicProducts.Kind.PLATFORM,RootNormalExitRuntime.class);
        actual.requireContext(installed.context());return actual;
    }
    public NormalExitPublicCodec.Result observe(NormalExitPublicCodec.ObserveArguments input)throws InterruptedException{
        Objects.requireNonNull(input);var deadline=context.clock().instant().plus(context.observationTimeout());
        try{return context.withCurrent(root->NormalExitPublicCodec.fromMemory(runtime(root).observe(deadline)));}
        catch(IOException failure){throw new UncheckedIOException("retained normal-exit observer unavailable; never submit a replacement confirmation",failure);}
    }
    public NormalExitPublicCodec.Result query(NormalExitPublicCodec.Query input)throws InterruptedException{
        Objects.requireNonNull(input);var deadline=context.clock().instant().plus(context.observationTimeout());
        try{return context.withCurrent(root->NormalExitPublicCodec.fromMemory(runtime(root).query(input.expectedRevision(),deadline)));}
        catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    public NormalExitPublicCodec.Result request(NormalExitPublicCodec.Request input)throws InterruptedException{
        Objects.requireNonNull(input);var deadline=context.clock().instant().plus(context.actionTimeout());
        try{return context.withCurrent(root->NormalExitPublicCodec.fromMemory(runtime(root).request(input.action(),input.expectedRevision(),input.contextSignature(),deadline)));}
        catch(IOException failure){throw new UncheckedIOException("normal-exit outcome remains retained; never replay a consumed phase",failure);}
    }
    /** Protocol-only seam. The production caller above retains the actual current installed Runtime. */
    static List<PublicBindings.BoundBinding> register(PublicBindings registry,
            PublicRoutes.Handler<NormalExitPublicCodec.ObserveArguments,NormalExitPublicCodec.Result> observe,
            PublicRoutes.Handler<NormalExitPublicCodec.Query,NormalExitPublicCodec.Result> query,
            PublicRoutes.Handler<NormalExitPublicCodec.Request,NormalExitPublicCodec.Result> request,ExactRef source){
        Objects.requireNonNull(registry);Objects.requireNonNull(source);
        return List.of(registry.register(PublicMethod.OBSERVE_NORMAL_EXIT_V1,NormalExitPublicCodec.ObserveArguments.class,NormalExitPublicCodec.Result.class,
                observe,NormalExitPublicCodec::decodeObserve,NormalExitPublicCodec::encode,target("observe",source),PublicRoutes.Status.IMPLEMENTED,"retained original process observer; zero new native submissions"),
            registry.register(PublicMethod.QUERY_NORMAL_EXIT_CONTEXT_V1,NormalExitPublicCodec.Query.class,NormalExitPublicCodec.Result.class,
                query,NormalExitPublicCodec::decodeQuery,NormalExitPublicCodec::encode,target("query",source),PublicRoutes.Status.IMPLEMENTED,"actual source-inventory and same-frame normal-exit context"),
            registry.register(PublicMethod.REQUEST_NORMAL_EXIT_V1,NormalExitPublicCodec.Request.class,NormalExitPublicCodec.Result.class,
                request,NormalExitPublicCodec::decodeRequest,NormalExitPublicCodec::encode,target("request",source),PublicRoutes.Status.IMPLEMENTED,"actual private phase claim and original native dispatch; UNKNOWN never retries"));
    }
    private static PublicRoutes.Target target(String method,ExactRef source){return new PublicRoutes.Target(RootNormalExitPublicProducts.class.getName(),method,source);}
}
