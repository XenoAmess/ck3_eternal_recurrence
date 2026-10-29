package org.xar.ck3.control.g2.context;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Actual public terminal DATA/helper deployment boundary; no Ready, token, Binding or Game is created. */
class RootNativeLoadedPublicPlanningSourcesTest {
    private static final List<String> PLANNING=List.of(
            "org.xar.ck3.control.application.planning.OriginalTerminalPlanning",
            "org.xar.ck3.control.application.planning.campaign.PublicTerminalDataContext");

    @Test void realTerminalProducerAndContextUseTheSharedLoadedBoundary()throws Exception {
        assertTrue(RootNativeRuntimeBinding.requiredRuntimeClassNames().containsAll(PLANNING));
        for(String name:PLANNING) {
            Class<?> anchor=Class.forName(name,false,RootNativeRuntimeBinding.class.getClassLoader());
            Path location=Path.of(anchor.getProtectionDomain().getCodeSource().getLocation().toURI());
            Path loaded=(Files.isDirectory(location)?location.resolve(anchor.getName().replace('.','/')+".class"):location).toRealPath();
            FileRef original=FileRef.measure(loaded);
            assertDoesNotThrow(()->RootNativeRuntimeBinding.requireLoadedRuntimeSource(name,
                    Map.of(loaded.toString(),original)),name);
        }
    }

    @Test void namingATerminalClassCannotReplaceItsAcceptedDeploymentMembership() {
        for(String name:PLANNING) {
            IOException failure=assertThrows(IOException.class,()->
                    RootNativeRuntimeBinding.requireLoadedRuntimeSource(name,Map.of()),name);
            assertTrue(failure.getMessage().contains("outside accepted deployment"));
        }
    }
}
