package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/** Real software coordinator/archive inputs cannot manufacture the private Root invocation bridge.
 * No Managed Root or private issuer is constructed; the actual Root positive remains mandatory. */
final class RootPublicStepInvocationBridgeTest {
    @TempDir Path directory;
    @Test void realUnknownReceiptAndTypedCallerCannotSubstituteForTheTrackedRootInvocation()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("actual-unknown-no-root-ticket"),true)) {
            var command=fixture.command("no-private-root-invocation");var actual=fixture.coordinator.execute(command);
            assertEquals(ActionReceipt.Outcome.UNRESOLVED,actual.outcome());assertEquals(1,fixture.nativeActionWrites());
            var caller=PublicPlanningCodec.decodeExecute(new PublicBindings.Value(new RawJson(
                    ("{\"step\":\""+command.operation().value()+"\",\"expected_revision\":\"0\"}").getBytes(StandardCharsets.UTF_8))));
            byte[] ledger=fixture.ledgerBytes();
            fixture.writer.locked(same->{
                assertThrows(IOException.class,()->RootPublicStepFailureOriginals.requirePreparedInvocation(actual,same,caller));
                assertThrows(IOException.class,()->RootPublicStepFailureOriginals.requireReadInvocation(null,null,null,same,caller));
                var original=new PublicServiceFailure(PublicServiceFailure.Kind.NATIVE_COMMAND_RESULT_TIMEOUT,"actual unqualified error DATA",Optional.empty());
                assertSame(original,RootPublicStepFailureOriginals.recordActionDriverFailure(actual,fixture.archive.withSession(same),same,
                        caller,original,Optional.empty(),Optional.empty()));
                return null;
            });
            assertArrayEquals(ledger,fixture.ledgerBytes());assertEquals(1,fixture.nativeActionWrites());
        }
    }
}
