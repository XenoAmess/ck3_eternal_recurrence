package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import org.junit.jupiter.api.Test;

/** Actual Main249 owner-result consumer only. No Started/Retained/Game/terminal evidence is fabricated. */
final class RootSavedOwnerTerminalResultTest {
    @Test void successfulOwnerLeavesTheIndependentBusinessOutcomeUntouched() {
        assertNull(RootJavaSavedBootstrapMain249.ownerTerminalResult(null,0));
        var business=new IOException("original callback failure");
        assertSame(business,RootJavaSavedBootstrapMain249.ownerTerminalResult(business,0));
        assertEquals(0,business.getSuppressed().length);
    }

    @Test void failedOwnerCannotBecomeASuccessfulMainWhenBusinessReturnedZero() {
        var failure=RootJavaSavedBootstrapMain249.ownerTerminalResult(null,1);
        assertInstanceOf(IOException.class,failure);
        assertTrue(failure.getMessage().contains("original Saved owner terminal returned failure 1"));
    }

    @Test void physicalTerminalFailureDoesNotReplaceTheOriginalBusinessCause() {
        var business=new IOException("original batch/UNKNOWN cause");
        var result=RootJavaSavedBootstrapMain249.ownerTerminalResult(business,1);
        assertSame(business,result);assertEquals("original batch/UNKNOWN cause",result.getMessage());
        assertEquals(1,result.getSuppressed().length);
        assertInstanceOf(IOException.class,result.getSuppressed()[0]);
        assertTrue(result.getSuppressed()[0].getMessage().contains("terminal returned failure 1"));
    }
}
