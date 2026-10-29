package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;

/** Requires a genuine privately issued cold origin and its actual borrowed writer; fabricates no runtime. */
public final class RootColdReboundContextAssertions {
    private RootColdReboundContextAssertions(){ }
    public static void assertActualBound(RootRuntimeContext context,RootColdReboundRuntime.ColdReboundOrigin original,Session same)throws IOException {
        context.writer().requireSession(same);assertSame(context,original.context());original.requireOriginal(same);
        String head=same.head().digest();
        context.bindColdReboundOrigin(same,original);assertSame(original,context.requireColdReboundOrigin(same));
        context.bindColdReboundOrigin(same,original);assertSame(original,context.requireColdReboundOrigin(same));
        assertThrows(IOException.class,()->context.requireRestoredOrigin(same));
        assertEquals(0,original.newSavedDayCredit());assertEquals(0,original.newCycleCredit());
        assertEquals(head,same.head().digest());
        assertEquals(0,RootColdReboundRuntime.ColdReboundOrigin.class.getConstructors().length);
    }
    public static void assertRejectsForeignContext(RootRuntimeContext actualOther,RootColdReboundRuntime.ColdReboundOrigin original,Session same)throws IOException {
        actualOther.writer().requireSession(same);assertNotSame(actualOther,original.context());String head=same.head().digest();
        assertThrows(IllegalArgumentException.class,()->actualOther.bindColdReboundOrigin(same,original));assertEquals(head,same.head().digest());
    }
}
