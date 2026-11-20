package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.util.Arrays;
import org.junit.jupiter.api.Test;

/** CLI DATA only: no Game, private Running, public Directory, or COMPLETE admission is constructed. */
class RootLoadedSavedPublicInvocationTest {
    private static final String HASH = "a".repeat(64);
    private static String[] triple(String name) { return new String[]{"D:/actual/" + name + ".json", "1", HASH}; }
    private static String[] concat(String[]... pieces) {
        return Arrays.stream(pieces).flatMap(Arrays::stream).toArray(String[]::new);
    }
    private static String[] invocation(boolean control) {
        return concat(new String[]{RootLoadedSavedResumeMain250.PUBLIC_ATTACHMENT}, triple("owner"), triple("resume"),
                control ? triple("selected-or-two-cycle-control") : new String[0], triple("public-definitions"));
    }

    @Test void explicitRouteRetainsOriginalExactSixAndNineWithoutReinterpretingControl() throws Exception {
        for (boolean control : new boolean[]{false, true}) {
            String[] raw = invocation(control);
            var parsed = RootLoadedSavedResumeMain250.publicInvocation(raw);
            assertArrayEquals(Arrays.copyOfRange(raw, 1, raw.length - 3), parsed.businessArguments());
            assertEquals("D:/actual/public-definitions.json", parsed.definitions().path());
            assertEquals(1, parsed.definitions().bytes()); assertEquals(HASH, parsed.definitions().sha256());
            assertEquals(control, RootLoadedSavedResumeMain250.checkpointControlReference(parsed.businessArguments()).isPresent());
            assertEquals(RootQuarkusEntrypoint.Application.LOADED_SAVED_PUBLIC, RootQuarkusEntrypoint.select(raw));
        }
        assertEquals(RootQuarkusEntrypoint.Application.ROOT_STARTUP, RootQuarkusEntrypoint.select(triple("startup")));
        assertEquals(RootQuarkusEntrypoint.Application.ROOT_STARTUP,
                RootQuarkusEntrypoint.select(concat(triple("startup"), triple("saved-route"))));
        assertEquals(RootQuarkusEntrypoint.Application.PUBLIC_HOST,
                RootQuarkusEntrypoint.select(concat(triple("owner"), triple("resume"), triple("control"))));
    }

    @Test void exactDataIsDefensivelyRetainedAndDoesNotOfferAnUnmarkedPublicRoute() throws Exception {
        String[] input = invocation(true);
        var parsed = RootLoadedSavedResumeMain250.publicInvocation(input);
        input[1] = "D:/changed.json";
        String[] returned = parsed.businessArguments(); returned[0] = "D:/other.json";
        assertEquals("D:/actual/owner.json", parsed.businessArguments()[0]);
        assertFalse(RootLoadedSavedResumeMain250.isPublicInvocation(parsed.businessArguments()));
        assertThrows(IOException.class, () -> RootLoadedSavedResumeMain250.publicInvocation(parsed.businessArguments()));
    }

    @Test void malformedTriplesAndAmbiguousCountsFailBeforeAnyBusinessInvocation() {
        assertThrows(IOException.class, () -> RootLoadedSavedResumeMain250.publicInvocation(RootLoadedSavedResumeMain250.PUBLIC_ATTACHMENT));
        for (int index : new int[]{2, 5, 8, 11}) {
            String[] raw = invocation(true); raw[index] = "01";
            assertThrows(IOException.class, () -> RootLoadedSavedResumeMain250.publicInvocation(raw));
        }
        String[] trailing = concat(invocation(false), new String[]{"extra"});
        assertThrows(IOException.class, () -> RootLoadedSavedResumeMain250.publicInvocation(trailing));
        assertThrows(IllegalArgumentException.class, () -> RootQuarkusEntrypoint.select(trailing));
    }
}
