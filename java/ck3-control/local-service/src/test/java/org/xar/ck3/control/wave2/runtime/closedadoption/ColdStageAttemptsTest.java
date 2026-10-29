package org.xar.ck3.control.wave2.runtime.closedadoption;

import java.io.IOException;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class ColdStageAttemptsTest {
    @Test void knownBeforeCreateFailureDoesNotCallCreatorAndFreshAttemptCanSubmit() throws Exception {
        var actual=new ColdStageAttempts();var creates=new AtomicInteger();
        assertThrows(IOException.class,()->actual.submit(RootColdStageReview.Stage.SAVED_GAME_CREATE,
                ()->{throw new IOException("actual pre-CREATE source refusal");},creates::incrementAndGet));
        assertEquals(0,creates.get());assertEquals(ColdStageAttempts.State.READY,actual.state(RootColdStageReview.Stage.SAVED_GAME_CREATE));
        assertEquals(1,actual.submit(RootColdStageReview.Stage.SAVED_GAME_CREATE,()->{},creates::incrementAndGet));
        assertThrows(IOException.class,()->actual.submit(RootColdStageReview.Stage.SAVED_GAME_CREATE,()->{},creates::incrementAndGet));
        assertEquals(1,creates.get());
    }
    @Test void firstCreateThenUnknownCannotInvokeCreatorAgain() throws Exception {
        assertUnknownBlocksSecondSubmission(RootColdStageReview.Stage.SAVED_GAME_CREATE);
    }
    @Test void firstLoaderThenUnknownCannotInvokeLoaderAgain() throws Exception {
        assertUnknownBlocksSecondSubmission(RootColdStageReview.Stage.INJECT);
    }
    @Test void firstOwnerThenUnknownCannotInvokeOwnerAgain() throws Exception {
        assertUnknownBlocksSecondSubmission(RootColdStageReview.Stage.MCP_OWNER);
    }
    private static void assertUnknownBlocksSecondSubmission(RootColdStageReview.Stage stage) throws Exception {
        var actual=new ColdStageAttempts();var submissions=new AtomicInteger();
        assertThrows(IOException.class,()->actual.submit(stage,()->{},()->{
            submissions.incrementAndGet();throw new IOException("actual submission entered then result UNKNOWN");
        }));
        assertEquals(ColdStageAttempts.State.UNKNOWN,actual.state(stage));assertTrue(actual.submitted(stage));
        assertThrows(IOException.class,()->actual.submit(stage,()->{},submissions::incrementAndGet));
        assertEquals(1,submissions.get());
    }
}
