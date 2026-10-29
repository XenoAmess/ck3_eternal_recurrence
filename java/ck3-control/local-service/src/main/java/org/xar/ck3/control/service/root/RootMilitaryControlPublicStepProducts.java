package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.publicmethods.gui.MilitaryControlActions;
import org.xar.ck3.control.nativebridge.publicmethods.gui.MilitaryControlContract;
import org.xar.ck3.control.nativebridge.publicmethods.gui.MilitaryReceiverProof;

/** Original exact fixed military EXECUTE routes; preparation and observation belong to their installed producer. */
public final class RootMilitaryControlPublicStepProducts {
    private RootMilitaryControlPublicStepProducts() { }
    public static List<RootPublicStepExecution.Product> install(RootInstalledCatalog actual)throws IOException {
        Objects.requireNonNull(actual);var context=actual.context();var runtime=actual.militaryControls();runtime.requireContext(context);
        var closure=new LinkedHashSet<ExactRef>();closure.add(context.source().sourceRef());
        closure.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootMilitaryControlStepRuntime.class));
        closure.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootMilitaryControlPublicStepProducts.class));
        for(Class<?> source:List.of(MilitaryControlActions.class,MilitaryControlContract.class,MilitaryReceiverProof.class))
            closure.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,source));
        List<ExactRef> sources=List.copyOf(closure);var products=new ArrayList<RootPublicStepExecution.Product>();
        for(var control:MilitaryControlContract.Control.values())products.add(new RootPublicStepExecution.Action(
                "original-execute-fixed-military-"+control.operation().value(),control.operation()::equals,runtime::requireContext,
                (original,frame,known,same,caller)->runtime.prepare(control,original,frame,known,same,caller),runtime::present,sources));
        return List.copyOf(products);
    }
}
