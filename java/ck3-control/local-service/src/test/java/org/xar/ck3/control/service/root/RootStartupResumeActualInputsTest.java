package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.ServiceLoader;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory;

/** This suite proves discovery and the actual shared optional-input codec; real Main/Directory
 * execution remains the mandatory RootHostBatchAndCloseActualTest, never a software Core factory. */
public final class RootStartupResumeActualInputsTest {
    @Test public void persistentServiceDiscoversTheSingleRealStartupProducer() {
        var providers=ServiceLoader.load(RootHostBatchAndCloseActualTest.ResumeInputsProducer.class).stream().toList();
        assertEquals(1,providers.size());
        assertEquals(RootStartupResumeActualInputs.class,providers.getFirst().type());
    }
    @Test public void currentResumePreservesOmittedOptionalRevisionThroughTheSharedCodec() {
        var call=RootStartupResumeActualInputs.currentResumeCall();
        assertEquals("ck3_resume_successor_ui_v1",call.name());
        assertEquals(PublicMcpDirectory.Presence.VALUE,call.arguments().presence());
        var input=PublicBindings.present(call.arguments().original().orElseThrow());
        var request=RootDriverLifecyclePublicCodec.resume(input);
        assertTrue(request.original().expected().isEmpty());
        var output=(PublicBindings.Value)RootDriverLifecyclePublicCodec.encode(request);
        assertEquals("{}",new String(output.original().bytes(),StandardCharsets.UTF_8));
        assertTrue(call.meta().isEmpty());
    }
}
