package org.xar.ck3.control.service.root;

import org.junit.jupiter.api.Test;
import java.io.IOException;
import java.util.List;
import org.xar.ck3.control.contracts.GameLifecycle.TerminalKind;
import static org.junit.jupiter.api.Assertions.*;

/** Actual consumer of owner-result DATA only. No CreatorOwnership, CreatorExit or Started is fabricated. */
final class RootSavedCreatorOwnerResultTest {
    @Test void originalSuccessfulCleanupPreservesTheIndependentBusinessResultAndExplicitStopExitCode() {
        assertNull(RootJavaSavedBootstrapMain249.creatorOwnerResult(null,0,TerminalKind.NATURAL_EXIT,true,List.of()));
        assertNull(RootJavaSavedBootstrapMain249.creatorOwnerResult(null,125,TerminalKind.OWNER_STOP,true,List.of()));
        var original=new IOException("original business failure");
        assertSame(original,RootJavaSavedBootstrapMain249.creatorOwnerResult(original,0,TerminalKind.NATURAL_EXIT,true,List.of()));
        assertEquals(0,original.getSuppressed().length);
    }
    @Test void naturalNonzeroCannotInheritSuccessAndKeepsAnExistingBusinessPrimary() {
        var failed=RootJavaSavedBootstrapMain249.creatorOwnerResult(null,7,TerminalKind.NATURAL_EXIT,true,List.of());
        assertInstanceOf(IOException.class,failed);assertTrue(failed.getMessage().contains("failure 7"));
        var original=new IOException("original batch callback failure");
        assertSame(original,RootJavaSavedBootstrapMain249.creatorOwnerResult(original,7,TerminalKind.NATURAL_EXIT,true,List.of()));
        assertEquals(1,original.getSuppressed().length);
        assertEquals(failed.getMessage(),original.getSuppressed()[0].getMessage());
    }
    @Test void actualFailuresUnknownAndUnclosedResourcesAllRemainVisibleWithoutMintingAnyTerminalProof() {
        var original=new IOException("original publication failure");
        var cleanup=new IOException("original resource cleanup failure");
        var fatal=new AssertionError("original fatal resource failure");
        var result=RootJavaSavedBootstrapMain249.creatorOwnerResult(original,0,TerminalKind.UNKNOWN,false,List.of(cleanup,fatal));
        assertSame(original,result);assertEquals(4,result.getSuppressed().length);
        assertSame(cleanup,result.getSuppressed()[0]);
        assertSame(fatal,result.getSuppressed()[1].getCause());
        assertTrue(result.getSuppressed()[2].getMessage().contains("UNKNOWN"));
        assertTrue(result.getSuppressed()[3].getMessage().contains("unclosed"));
        assertSame(cleanup,RootJavaSavedBootstrapMain249.creatorOwnerResult(null,0,TerminalKind.NATURAL_EXIT,true,List.of(cleanup)));
    }
}
