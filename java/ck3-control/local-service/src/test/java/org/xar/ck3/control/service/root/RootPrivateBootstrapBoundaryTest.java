package org.xar.ck3.control.service.root;

import java.io.IOException;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.continuity.OriginalLegacyResume;
import static org.junit.jupiter.api.Assertions.*;

final class RootPrivateBootstrapBoundaryTest {
    @Test void onlyAcceptedActualColdRouteCanReachCanonicalCommit() {
        for(var route:OriginalLegacyResume.Route.values()) {
            if(route==OriginalLegacyResume.Route.COLD_CHECKPOINT)assertDoesNotThrow(()->RootPrivateBootstrap.requireRoute(route,false));
            else assertThrows(IOException.class,()->RootPrivateBootstrap.requireRoute(route,false));
            assertThrows(IOException.class,()->RootPrivateBootstrap.requireRoute(route,true));
        }
        assertThrows(IOException.class,()->RootPrivateBootstrap.requireRoute(null,false));
    }
    @Test void capabilitiesHaveNoPublicConstructorOrDataDecoder() {
        for(Class<?> type:java.util.List.of(RootPrivateBootstrap.Prepared.class,RootPrivateBootstrap.Original.class,
                org.xar.ck3.control.platform.RootProcessAttach.Custody.class))assertEquals(0,type.getConstructors().length);
        for(var method:org.xar.ck3.control.platform.ColdBootstrapJson.class.getMethods())
            assertFalse(method.getReturnType()==RootPrivateBootstrap.Original.class||method.getReturnType()==RootPrivateBootstrap.Prepared.class);
    }
}
