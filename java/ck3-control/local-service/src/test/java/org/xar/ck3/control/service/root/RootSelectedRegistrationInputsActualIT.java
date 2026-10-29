package org.xar.ck3.control.service.root;

import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.SharedSourceFiles;

/** Explicit actual-input suite. Stage the known owned root, real quote and independent binding first.
 * Missing genuine inputs fail, never skip; default unit tests cannot grant this chain's credit. */
public final class RootSelectedRegistrationInputsActualIT {
    @Test void actualProducerPublicationAndOriginalCaptureConsumer()throws Exception {
        String selected=System.getProperty("xar.test.selectedRegistration.ownedRoot");
        if(selected==null)throw new AssertionError("NOT_RUN_REQUIRED: actual known owned output root missing");
        Path root=Path.of(selected);
        if(!root.isAbsolute()||!root.normalize().equals(root)||!Files.isDirectory(root))
            throw new AssertionError("actual canonical owned output directory required");
        SharedSourceFiles.plainAncestors(root);SharedSourceFiles.nativeDirectory(root);
        var actual=new RootSelectedRegistrationInputsProducerTest();actual.root=root;
        actual.actualSourceBoundProducerMainQuoteCreateAndOriginalCaptureConsumerUseTheSamePhysicalOriginal();
    }
}
