package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.service.root.FormalReleaseTestFixture;
import org.xar.ck3.control.service.root.RootProfileBootstrapInputs;

/** The genuine private preparation must retain the same physical-output policy through the actual LS quote. */
final class RootFormalStorageCustodyTest {
    @Test void actualLsQuoteRejectsStorageConfigurationDriftWithoutProducingPayloadOrIssuerOutputs()throws Exception {
        try(var fixture=FormalReleaseTestFixture.create(FormalReleaseProducer.Mode.PUBLISH_RELEASE)){
            var actual=fixture.actual();var stage=RootProfileBootstrapInputs.formalRelease(actual);
            assertTrue(stage.formalAssetPeakUpperBytes()>0);
            assertFalse(Files.exists(actual.request().productionRoot()));
            assertFalse(Files.exists(actual.request().manifestTarget()));
            String key=ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK,original=System.getProperty(key);
            boolean captured=ProjectStoragePolicy.configuration(System::getProperty,System::getenv).forbidSystemVolumeBulk();
            try {
                // Only this test JVM property changes. The source Snapshot is already bound; no process,
                // output directory/file creation or independent issuer request is attempted while it differs.
                System.setProperty(key,Boolean.toString(!captured));
                assertThrows(IOException.class,actual::verifyOriginals);
                assertThrows(IOException.class,stage::formalAssetPeakUpperBytes);
                assertThrows(IOException.class,()->RootProfileBootstrapInputs.formalRelease(actual));
                assertFalse(Files.exists(actual.request().productionRoot()));
                assertFalse(Files.exists(actual.request().manifestTarget()));
            } finally {
                if(original==null)System.clearProperty(key);else System.setProperty(key,original);
            }
            actual.verifyOriginals();
        }
    }
}
