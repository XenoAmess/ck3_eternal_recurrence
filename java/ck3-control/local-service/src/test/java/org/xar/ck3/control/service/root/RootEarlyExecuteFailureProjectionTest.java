package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.history.DriverEarlyExecuteFailure;
import org.xar.ck3.control.application.history.DriverEarlyExecuteFailureRowProducer;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;
import static org.junit.jupiter.api.Assertions.*;

/** Throwable-to-DATA projection only; this creates no Root, private Source, invocation or Candidate. */
final class RootEarlyExecuteFailureProjectionTest {
    @Test void actualJavaClassAndNullableMessageArePreservedWithoutPythonAlias() {
        for(IOException original:new IOException[]{new IOException(),new IOException(""),new IOException("outer: inner\n雪")}) {
            var projected=RootPublicStepFailureOriginals.earlyError(original);
            assertEquals(DriverEarlyExecuteFailure.ErrorOrigin.ACTUAL_JAVA_FAILURE,projected.origin());
            assertEquals(IOException.class.getName(),projected.className());
            assertEquals(Optional.ofNullable(original.getMessage()),projected.message());
            assertArrayEquals(new Throwable[0],original.getSuppressed());
        }
    }
    @Test void onlyActualTypedPublicFailureKeepsItsMigratedOriginalClass() {
        var original=new PublicServiceFailure(PublicServiceFailure.Kind.UNSUPPORTED_STEP,"native original: detail",Optional.empty());
        var projected=RootPublicStepFailureOriginals.earlyError(original);
        assertEquals(DriverEarlyExecuteFailure.ErrorOrigin.MIGRATED_PUBLIC_FAULT,projected.origin());
        assertEquals(original.kind().pythonClassName(),projected.className());
        assertEquals(Optional.of(original.getMessage()),projected.message());
    }
    @Test void absentCachedFactsRemainExplicitDataWithoutHistoryIndex() {
        var reference=new ExactRef("D:/data-only/original.json",1,"a".repeat(64));
        for(Throwable original:new Throwable[]{new IOException(),new IOException(""),new IllegalArgumentException("actual Java")}) {
            var data=new DriverEarlyExecuteFailure.InvocationData(new OperationKey("query-player-china-career-v1"),
                    RootPublicStepFailureOriginals.earlyError(original),Optional.empty(),Optional.empty(),
                    new DriverEarlyExecuteFailure.AbsentData(new DriverEarlyExecuteFailure.Missing(java.util.List.of("actual cached Known absent"))),
                    reference,reference,Optional.empty(),Optional.empty(),0,"b".repeat(64),java.util.List.of(reference));
            var encoded=DriverJson.encode(DriverEarlyExecuteFailureRowProducer.invocationJson(data));
            assertEquals(data,DriverEarlyExecuteFailureRowProducer.decodeInvocation(encoded));
            assertThrows(IllegalArgumentException.class,()->new DriverEarlyExecuteFailureRowProducer.RawHistoryRow(1,
                    new DriverEarlyExecuteFailureRowProducer.Source(data,reference),Optional.empty()));
        }
    }
}
