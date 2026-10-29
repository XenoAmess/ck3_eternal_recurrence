package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Duration;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.CoaVfs;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.CoaTextRules;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaContract;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaService;

/** Sole pre-Core assembly of the four finite original CoA producers and their shared read definitions. */
public final class RootFrontendCoaSources {
    private RootFrontendCoaSources() { }

    /** The existing closed Root settings reader supplies explicit VFS read limits through its sole codec.
     * The identical selected source collector is retained by the actual Root source-products caller. */
    public static RootFrontendCoaPublicProducts.Prepared prepare(RootRuntimeDefinitions.Inputs inputs,
            RootRuntimeSelectedSources sameSelected,CoaVfs.Limits actualReadLimits,Duration actualTimeout)throws IOException {
        Objects.requireNonNull(inputs);Objects.requireNonNull(sameSelected);
        Objects.requireNonNull(actualReadLimits);Objects.requireNonNull(actualTimeout);
        if(actualTimeout.isNegative()||actualTimeout.isZero()||actualTimeout.compareTo(Duration.ofSeconds(60))>0)
            throw new IOException("the explicit actual CoA timeout must be in (0,60 seconds]");
        sameSelected.requireCurrent();
        sameSelected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootFrontendCoaSources.class);
        sameSelected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootFrontendCoaPublicProducts.class);
        sameSelected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootCoaVfs.class);
        for(Class<?> actual:List.of(FrontendCoaContract.class,FrontendCoaCodec.class,FrontendCoaService.class,CoaVfs.class,CoaTextRules.class))
            sameSelected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,actual);
        var upload=RootCoaUpload.prepare(sameSelected,actualTimeout);
        var designer=RootCoaDesigner.prepare(inputs,sameSelected);
        var framebuffer=new RootCoaFramebuffer.Prepared(inputs,sameSelected,designer.coaReads());
        var vfs=new RootCoaVfs.Prepared(actualReadLimits,actualTimeout);
        var actual=new RootFrontendCoaPublicProducts.Prepared(List.of(upload,designer,framebuffer,vfs));
        sameSelected.requireCurrent();
        return actual;
    }
}
