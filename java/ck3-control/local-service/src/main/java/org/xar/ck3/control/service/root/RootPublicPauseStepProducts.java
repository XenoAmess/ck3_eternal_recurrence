package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.LinkedHashSet;
import java.util.List;
import org.xar.ck3.control.application.advance.GenericPublicPauseRecovery;
import org.xar.ck3.control.application.effects.control.ControlSequenceObservation;
import org.xar.ck3.control.contracts.ExactRef;

/** The actual original pause-map facade selects its installed private parent, without an ordinary Ready precondition. */
public final class RootPublicPauseStepProducts {
    private RootPublicPauseStepProducts() { }
    public static List<RootPublicStepExecution.Product> install(RootInstalledCatalog actual)throws IOException {
        var runtime=actual.publicPause();runtime.requireContext(actual.context());
        var sources=new LinkedHashSet<ExactRef>(runtime.historyProducerSources());
        sources.add(actual.context().source().sourceRef());
        sources.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootPublicPauseRuntime.class));
        sources.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootPublicPauseStepProducts.class));
        sources.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.APPLICATION,GenericPublicPauseRecovery.class));
        sources.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.APPLICATION,ControlSequenceObservation.class));
        var product=new RootPublicStepExecution.OwnedAction("original-public-pause-with-source-bound-recovery",
                RootPublicPauseRuntime.PUBLIC_STEP::equals,runtime::requireContext,
                (root,installed,caller,deadline)->{
                    if(installed!=actual)throw new IOException("public pause crossed its actual installed catalog");
                    return runtime.execute(root,caller,deadline);
                },List.copyOf(sources));
        runtime.bindPublicProduct(actual,product);
        return List.of(product);
    }
}
