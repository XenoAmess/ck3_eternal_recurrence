package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.service.mcp.CheckpointPublicCodec;

/** The original private restore route remains queryable after its old Root is retired. */
public final class RootRestoreCheckpointPublicProducts {
    private final RootPublicHandlerProductsFactory.Context context;
    private RootRestoreCheckpointPublicProducts(RootPublicHandlerProductsFactory.Context actual){context=Objects.requireNonNull(actual);}
    public static RootPublicHandlerProductsFactory.Contribution install(RootPublicHandlerProductsFactory.Context context,
            PublicBindings registry)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(registry);
        ExactRef source=context.source(RootRestoreCheckpointPublicProducts.class);
        context.source(RootSessionAccess.class);context.source(RootCheckpointPublicCalls.class);context.source(CheckpointPublicCodec.class);
        var actual=new RootRestoreCheckpointPublicProducts(context);
        register(registry,actual::restoreCheckpoint,source);
        return new RootPublicHandlerProductsFactory.Contribution(List.of(),List.of(),List.of());
    }
    public RawJson restoreCheckpoint(RootCheckpointPublicCalls.Request input)throws InterruptedException {
        Objects.requireNonNull(input);var deadline=context.clock().instant().plus(context.actionTimeout());
        try {
            // The first call still needs the actual saved pair/current physical qualification.
            // A retained UNKNOWN is queried by the same private runtime without resolving ordinary current/Ready.
            return CheckpointPublicCodec.restore(context.restoreCheckpointPublic(input,deadline));
        }catch(IOException failure){throw new UncheckedIOException(
                "original restore remains retained; this public adapter neither retries nor creates another restore authority",failure);}
    }
    /** Protocol boundary only; production supplies the identical Core route above. */
    static PublicBindings.BoundBinding register(PublicBindings registry,
            PublicRoutes.Handler<RootCheckpointPublicCalls.Request,RawJson> actual,ExactRef source) {
        Objects.requireNonNull(registry);Objects.requireNonNull(actual);Objects.requireNonNull(source);
        return registry.register(PublicMethod.RESTORE_CHECKPOINT,RootCheckpointPublicCalls.Request.class,RawJson.class,actual,
                CheckpointPublicCodec::decode,value->Objects.requireNonNull(value),
                new PublicRoutes.Target(RootRestoreCheckpointPublicProducts.class.getName(),"restoreCheckpoint",source),
                PublicRoutes.Status.IMPLEMENTED,
                "same actual Core restore resources and private retained attempt; full source/revision admission on first call, UNKNOWN query without replacement dispatch");
    }
}
