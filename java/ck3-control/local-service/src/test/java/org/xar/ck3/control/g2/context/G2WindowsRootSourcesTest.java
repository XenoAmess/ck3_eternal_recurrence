package org.xar.ck3.control.g2.context;

import java.nio.file.Path;
import org.junit.jupiter.api.Test;

/** Persistent Maven route. Missing explicit finite output configuration is a failure, never a skip. */
final class G2WindowsRootSourcesTest {
    @Test void realWindowsSourceAndSyntheticNativeProducerChain() throws Exception {
        String root = System.getProperty("xar.rootContext.testRoot");
        if (root == null || root.isBlank()) { throw new IllegalStateException("xar.rootContext.testRoot is required for the complete Windows context step"); }
        G2WindowsRootSourcesChecks.main(new String[] {Path.of(root).toAbsolutePath().normalize().toString()});
    }
}
