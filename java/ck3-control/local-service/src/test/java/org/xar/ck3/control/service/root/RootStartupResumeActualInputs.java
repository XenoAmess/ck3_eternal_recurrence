package org.xar.ck3.control.service.root;

import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.service.OrdinarySessionHost;
import org.xar.ck3.control.service.mcp.McpCancellation;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory;
import org.xar.ck3.control.service.mcp.PublicMcpHost;

/** Real Main service bridge. The callback consumes the original directory and private inputs
 * before Main closes its original Game/Core. An omitted optional revision asks the real installed
 * Resume route to observe current state; it supplies no historical frame or synthetic pending cause. */
public final class RootStartupResumeActualInputs implements RootHostBatchAndCloseActualTest.ResumeInputsProducer {
    @Override public void withActualResumeInputs(RootHostBatchAndCloseActualTest.ResumeInputsWork work)throws Exception {
        Objects.requireNonNull(work);
        var request=RootStartupInputsProducer.fromEnvironment(System.getenv());
        RootStartupInputsProducer.execute(request,new OrdinarySessionHost(),new PublicMcpHost(),actual->{
            var reads=actual.readInputs();
            work.consume(new RootHostBatchAndCloseActualTest.ResumeInputs(reads.core(),reads.current(),reads.catalog(),
                    actual.directory(),actual.privateInputs(),actual.clock(),currentResumeCall()));
        });
    }
    static PublicMcpDirectory.ToolCall currentResumeCall() {
        var arguments=new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,
                Optional.of(new RawJson("{}".getBytes(StandardCharsets.UTF_8))));
        return new PublicMcpDirectory.ToolCall("ck3_resume_successor_ui_v1",arguments,Optional.empty(),new McpCancellation());
    }
}
