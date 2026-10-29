package org.xar.ck3.control.g2.context;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Actual loaded-artifact checks only; no Steam query, native API, Accepted, Binding or Game is created. */
class RootNativeLoadedSteamSourcesTest {
    private static final List<String> STEAM=List.of(
            "org.xar.ck3.control.platform.SteamOfflineProbe",
            "org.xar.ck3.control.platform.SteamOfflineProfiles",
            "org.xar.ck3.control.platform.SteamOfflineObservation",
            "org.xar.ck3.control.platform.SteamOfflineObservationCodec",
            "org.xar.ck3.control.platform.SteamOfflineCefProvider",
            "org.xar.ck3.control.platform.SteamOfflineCefWire",
            "org.xar.ck3.control.platform.Win32Host");

    @Test void allSevenRealSteamClassesIncludingPackagePrivateCefReachTheSameLoadedBoundary()throws Exception {
        for(String name:STEAM) {
            Class<?> anchor=Class.forName(name,false,RootNativeRuntimeBinding.class.getClassLoader());
            Path location=Path.of(anchor.getProtectionDomain().getCodeSource().getLocation().toURI());
            Path loaded=(Files.isDirectory(location)?location.resolve(anchor.getName().replace('.','/')+".class"):location).toRealPath();
            FileRef original=FileRef.measure(loaded);
            assertDoesNotThrow(()->RootNativeRuntimeBinding.requireLoadedRuntimeSource(name,
                    Map.of(loaded.toString(),original)),name);
        }
    }

    @Test void namingARealSteamClassCannotReplaceItsAcceptedDeploymentMembership() {
        for(String name:STEAM) {
            IOException failure=assertThrows(IOException.class,()->
                    RootNativeRuntimeBinding.requireLoadedRuntimeSource(name,Map.of()),name);
            assertTrue(failure.getMessage().contains("outside accepted deployment"));
        }
    }
}
