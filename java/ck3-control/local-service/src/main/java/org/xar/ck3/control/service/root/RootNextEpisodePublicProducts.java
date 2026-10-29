package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.LifecycleExpectedPostcondition.Operation;
import org.xar.ck3.control.application.session.SessionController;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.service.mcp.LifecyclePublicCodec;

/** Pre-Core protocol registration; invocation retains Root's actual terminal Controller and NEXT publication. */
public final class RootNextEpisodePublicProducts {
    private final RootPublicHandlerProductsFactory.Context context;
    private RootNextEpisodePublicProducts(RootPublicHandlerProductsFactory.Context context) {this.context=Objects.requireNonNull(context);}

    public static RootPublicHandlerProductsFactory.Contribution install(RootPublicHandlerProductsFactory.Context context,
            PublicBindings registry)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(registry);
        ExactRef implementation=context.source(RootNextEpisodePublicProducts.class);
        context.source(RootApplicationSession.class);
        context.source(RootEpisodeContinuationRuntime.class);
        context.source(RootRuntimeSelectedSources.Module.APPLICATION,SessionController.class);
        context.source(LifecyclePublicCodec.class);
        var actual=new RootNextEpisodePublicProducts(context);
        register(registry,actual::startNextEpisode,implementation);
        return new RootPublicHandlerProductsFactory.Contribution(List.of(),List.of(),List.of());
    }

    public LifecyclePublicCodec.Payload startNextEpisode(LifecyclePublicCodec.Request input)throws InterruptedException {
        Objects.requireNonNull(input);var deadline=context.clock().instant().plus(context.actionTimeout());
        try {
            return context.withCurrent(root->{
                var installed=context.installed(root).remainingDomains().lifecycle();
                return root.executePublicLifecycle(installed,Operation.START_NEXT_EPISODE,input.expected(),deadline,
                        (receipt,archive,same)->LifecyclePublicCodec.present(Operation.START_NEXT_EPISODE,receipt,archive));
            });
        }catch(IOException failure){
            throw new UncheckedIOException("actual current Root NEXT unavailable; retain the original outcome and never replay from this error",failure);
        }
    }

    /** Same strict protocol boundary used by production registration; the handler alone grants no Root/native authority. */
    static PublicBindings.BoundBinding register(PublicBindings registry,
            PublicRoutes.Handler<LifecyclePublicCodec.Request,LifecyclePublicCodec.Payload> actual,ExactRef implementation) {
        Objects.requireNonNull(registry);Objects.requireNonNull(actual);Objects.requireNonNull(implementation);
        return registry.register(PublicMethod.START_NEXT_EPISODE,LifecyclePublicCodec.Request.class,LifecyclePublicCodec.Payload.class,actual,
                LifecyclePublicCodec::decodeRequest,LifecyclePublicCodec::encode,
                new PublicRoutes.Target(RootNextEpisodePublicProducts.class.getName(),"startNextEpisode",implementation),
                PublicRoutes.Status.IMPLEMENTED,
                "same current Root terminal Controller checks the exact requested operation/public revision before submission; original NEXT, first SAVE/BASELINE and Host publication remain Core-owned");
    }
}
