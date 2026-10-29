package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.service.mcp.NormalExitPublicCodec;

/** Registration/serde DATA only; no fake Prepared, Core, Managed session, handle or successful exit. */
final class RootNormalExitPublicProductsTest {
    private static RawJson raw(String text){return new RawJson(text.getBytes(StandardCharsets.UTF_8));}
    @Test void missingActualPreparedContributesExactGapsAndNoRejectingReadyHandler(){
        var actual=RootNormalExitPublicProducts.unavailable();assertTrue(actual.direct().isEmpty());assertTrue(actual.diagnostics().isEmpty());
        assertEquals(Set.of("observe_normal_exit_v1","query_normal_exit_context_v1","request_normal_exit_v1"),
                actual.gaps().stream().map(RootRuntimePublicCatalog.DefinitionGap::identity).collect(java.util.stream.Collectors.toSet()));
    }
    @Test void sharedRegistryValidatesBeforeHandlerAndPreservesConsumedUnknownWithoutRetryOrExitCredit()throws Exception{
        var count=new AtomicInteger();var registry=new PublicBindings();
        var source=new ExactRef("protocol-data-only",1,"a".repeat(64));
        String unknown="{\"schema\":\"ck3-normal-exit-request-result-v1\",\"action\":\"prepare_confirmation\",\"status\":\"dispatch_unknown_claimed\",\"public_revision\":18446744073709551615,\"native_observation\":null,\"process_creation_filetime_100ns\":18446744073709551615,\"source_inventory_sha256\":\""+"b".repeat(64)+"\",\"claim_consumed\":true,\"retry_authorized\":false,\"autosave_verified\":false,\"process_exit_observed\":false,\"typed_normal_exit_observed\":false,\"request_id\":\"original\",\"claim_path\":\"retained-original\",\"uses_desktop_input\":false,\"uses_ocr\":false,\"native_submission_count\":1}";
        var bindings=RootNormalExitPublicProducts.register(registry,input->{throw new AssertionError("unrelated observer");},input->{throw new AssertionError("unrelated query");},
                input->{count.incrementAndGet();assertEquals(StrictJson.UINT64_MAX,input.expectedRevision());return NormalExitPublicCodec.fromMemory(raw(unknown));},source);
        registry.freeze(Set.of(PublicMethod.OBSERVE_NORMAL_EXIT_V1,PublicMethod.QUERY_NORMAL_EXIT_CONTEXT_V1,PublicMethod.REQUEST_NORMAL_EXIT_V1));
        assertEquals(3,bindings.size());assertTrue(registry.lookup(PublicMethod.RESTORE_CHECKPOINT).isEmpty());
        var binding=registry.lookup(PublicMethod.REQUEST_NORMAL_EXIT_V1).orElseThrow();
        String request="{\"action\":\"prepare_confirmation\",\"expected_revision\":\"18446744073709551615\",\"expected_exit_context_signature\":\""+"a".repeat(64)+"\"}";
        var result=binding.invoke(PublicBindings.present(raw(request)));var row=StrictJson.parse(result.bytes());
        assertEquals("dispatch_unknown_claimed",row.get("status").textValue());assertTrue(row.get("claim_consumed").booleanValue());
        assertFalse(row.get("retry_authorized").booleanValue());assertFalse(row.get("typed_normal_exit_observed").booleanValue());
        assertEquals("18446744073709551615",row.get("process_creation_filetime_100ns").textValue());assertEquals(1,count.get());
        for(String bad:List.of(request.replace("\"18446744073709551615\"","true"),request.replace("prepare_confirmation","query_context"),request.replace("\"expected_revision\":","\"caller_authorized\":true,\"expected_revision\":")))
            assertThrows(IllegalArgumentException.class,()->binding.invoke(PublicBindings.present(raw(bad))));
        assertEquals(1,count.get());
    }
}
