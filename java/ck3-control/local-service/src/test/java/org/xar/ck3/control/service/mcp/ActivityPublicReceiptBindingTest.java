package org.xar.ck3.control.service.mcp;

import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts;
import static org.junit.jupiter.api.Assertions.*;

/** Two actual original producer packets cannot be spliced into another public read's Known DTO. */
final class ActivityPublicReceiptBindingTest {
    @TempDir Path temporary;
    @Test void actualPacketAndOuterReadReceiptMustBelongToTheSameOriginalQuery()throws Exception {
        var cases=RootMcpActivityReadsTest.originalCases();
        var first=RootMcpActivityReadsTest.actualPacket(cases.get(0),temporary.resolve("first"));
        var second=RootMcpActivityReadsTest.actualPacket(cases.get(1),temporary.resolve("second"));
        var spliced=new PlanningReadResult.Known<>(first,second.receipt(),second.receipt().before().binding().nativeEvidence());
        assertThrows(IllegalArgumentException.class,()->RootMcpActivityReads.present(ActivityNativeContracts.Query.GUEST_OPINION,spliced));
        assertNotEquals(first.receipt(),second.receipt());
    }
}
