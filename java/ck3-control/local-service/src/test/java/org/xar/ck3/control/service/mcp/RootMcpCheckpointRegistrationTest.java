package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.CheckpointResult;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.service.root.RootCheckpointPublicCalls;

/** Production registration path with controlled typed DATA output; no Root or Host authority is manufactured. */
final class RootMcpCheckpointRegistrationTest {
    private static final ExactRef SOURCE=new ExactRef(Path.of("reviewed-registration-data").toAbsolutePath().toString(),1,"a".repeat(64));
    @Test void realRegistryInstallsOnlySaveAndTheOriginalFullScopeStillRejectsMissingRestore(){
        var registry=new PublicBindings();var bindings=RootMcpCheckpoint.bindSaveOnly(registry,SOURCE,request->{throw new AssertionError("registration cannot execute");});
        assertEquals(1,bindings.size());assertTrue(registry.lookup(PublicMethod.SAVE_CHECKPOINT).isPresent());
        assertTrue(registry.lookup(PublicMethod.RESTORE_CHECKPOINT).isEmpty());assertFalse(registry.frozen());
        assertTrue(registry.coverage().unimplemented().contains(PublicMethod.RESTORE_CHECKPOINT));
        assertThrows(Exception.class,()->registry.freeze(Set.of(PublicMethod.SAVE_CHECKPOINT,PublicMethod.RESTORE_CHECKPOINT)));
    }
    @Test void installedSaveUsesTheSharedDecoderAndUnknownEncoderWithoutRegisteringRestore()throws Exception{
        var calls=new AtomicInteger();var registry=new PublicBindings();
        RootMcpCheckpoint.bindSaveOnly(registry,SOURCE,request->{
            calls.incrementAndGet();assertTrue(request.effectiveExpectedRevision().isEmpty());
            return new RootCheckpointPublicCalls.SaveCall(new CheckpointResult.Unknown("data-save","actual state unresolved",Optional.empty()),Optional.empty(),Optional.empty());
        });
        registry.freeze(Set.of(PublicMethod.SAVE_CHECKPOINT));
        var save=registry.lookup(PublicMethod.SAVE_CHECKPOINT).orElseThrow();
        var wrong=new PublicBindings.Value(new RawJson("{\"expected_revision\":true}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        assertThrows(Exception.class,()->save.invoke(wrong));assertEquals(0,calls.get());
        var result=StrictJson.parse(save.invoke(new PublicBindings.Missing()).bytes());
        assertEquals(1,calls.get());assertEquals("unknown",result.get("status").textValue());
        assertFalse(result.has("checkpoint"));assertTrue(registry.lookup(PublicMethod.RESTORE_CHECKPOINT).isEmpty());
    }
}
