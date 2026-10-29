package org.xar.ck3.control.g2.context;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.history.DriverEarlyExecuteFailure;
import org.xar.ck3.control.application.history.DriverEarlyExecuteFailureRowProducer;
import org.xar.ck3.control.application.history.DriverPublicExecuteFailureMaterial;
import org.xar.ck3.control.application.history.DriverPublicExecuteFailureRowProducer;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.service.root.RootPublicStepFailureOriginals;

/** Only the real loaded-artifact membership boundary is exercised; no Accepted/Binding/Game is created. */
class RootNativeLoadedHistorySourcesTest {
    private static final List<Class<?>> HISTORY=List.of(DriverPublicExecuteFailureMaterial.class,
            DriverPublicExecuteFailureRowProducer.class,DriverEarlyExecuteFailure.class,
            DriverEarlyExecuteFailureRowProducer.class,RootPublicStepFailureOriginals.class);

    @Test void fiveActualHistoryCodeSourcesReachTheSameProductionClassloaderBoundary()throws Exception {
        for(Class<?> anchor:HISTORY) {
            Path location=Path.of(anchor.getProtectionDomain().getCodeSource().getLocation().toURI());
            Path loaded=(Files.isDirectory(location)?location.resolve(anchor.getName().replace('.','/')+".class"):location).toRealPath();
            FileRef original=FileRef.measure(loaded);
            assertDoesNotThrow(()->RootNativeRuntimeBinding.requireLoadedRuntimeSource(anchor.getName(),
                    Map.of(loaded.toString(),original)),anchor.getName());
        }
    }

    @Test void theSameProductionBoundaryRejectsMissingDeploymentAndMissingActualClass() {
        for(Class<?> anchor:HISTORY) {
            IOException failure=assertThrows(IOException.class,()->
                    RootNativeRuntimeBinding.requireLoadedRuntimeSource(anchor.getName(),Map.of()),anchor.getName());
            assertTrue(failure.getMessage().contains("outside accepted deployment"));
        }
        IOException missing=assertThrows(IOException.class,()->RootNativeRuntimeBinding.requireLoadedRuntimeSource(
                "org.xar.ck3.control.application.history.MissingActualHistorySource",Map.of()));
        assertEquals("Exact loaded Native Root code source unavailable",missing.getMessage());
        assertInstanceOf(ClassNotFoundException.class,missing.getCause());
    }
}
