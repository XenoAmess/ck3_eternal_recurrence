package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import org.xar.ck3.control.platform.ManagedGameSession;

/** Assertions for the existing genuine Root/Game fixture; this helper never creates or adopts a Game. */
public final class RootManagedPresentationSourceAssertions {
    private RootManagedPresentationSourceAssertions() { }

    /** Invoke after the actual shared launch producer accepted its original HELLO. No pipe or mapping is opened. */
    public static ManagedGameSession.NativePhysicalSourceAccess assertActualManaged(ManagedGameSession actual)throws IOException {
        actual.verify();
        var access=actual.presentationAccess();access.requireOwner(actual);
        assertSame(access,actual.presentationAccess(),"one private attachment per original managed Game");
        var config=access.actualConfig();var guard=access.actualGuard();
        assertSame(config,access.actualConfig(),"retain the original Config object, including across repeated physical queries");
        assertSame(guard,access.actualGuard(),"retain the original suspended callback guard, without a replacement verifier");
        assertEquals(actual.generation(),config.game());assertEquals(actual.machineId(),config.machineId());
        assertEquals(actual.sessionId(),config.sessionId());assertEquals(actual.launchPlan().pipeName(),config.pipeName());
        assertEquals(actual.launchPlan().bridgeVersion(),config.expectedBridgeVersion());
        assertEquals(actual.launchPlan().adapterId(),config.expectedAdapterId());
        assertEquals(actual.launchPlan().sources().review().gameExecutable().sha256().toLowerCase(java.util.Locale.ROOT),
                config.expectedGameSha256().toLowerCase(java.util.Locale.ROOT));
        guard.verify(actual.generation());actual.verify();return access;
    }

    /** Both arguments must come from actual shared launch results; a stopped previous Game is a valid foreign input. */
    public static void assertForeignManagedRejected(ManagedGameSession actual,ManagedGameSession foreign)throws IOException {
        assertNotSame(actual,foreign,"two actual original launch results required for the foreign-owner regression");
        var access=assertActualManaged(actual);
        assertThrows(IOException.class,()->access.requireOwner(foreign));
        assertSame(access,actual.presentationAccess());
    }

    /** Invoke only after the fixture's actual shared lifecycle close, retaining the pre-close attachment. */
    public static void assertClosedManagedRejected(ManagedGameSession closed,
            ManagedGameSession.NativePhysicalSourceAccess retained) {
        assertThrows(IOException.class,closed::presentationAccess);
        assertThrows(IOException.class,retained::actualConfig);
        assertThrows(IOException.class,retained::actualGuard);
        assertThrows(IOException.class,()->retained.requireOwner(closed));
    }
}
