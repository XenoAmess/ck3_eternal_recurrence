package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernancePublicService;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/** Software registration/decoder/fault consumer only. Synthetic handler faults cannot mint a private Factory, Core or native permission. */
final class RootGovernanceDevelopmentPublicBindingTest {
    private static final PublicMethod METHOD=PublicMethod.CHANGE_STEWARD_DEVELOP_COUNTY_TASK_V1;
    private static final ExactRef SOURCE=new ExactRef("synthetic-public-service-binding.java",1,"a".repeat(64));
    private static final String QUALIFICATION="Software boundary only; no native executor, permission or result observer.";
    private static RawJson raw(String text) {return new RawJson(text.getBytes(StandardCharsets.UTF_8));}
    private static String arguments(String revision) {
        return "{\"councillor_character_id\":33554449,\"target_county_title_id\":67108874,\"expected_revision\":"+revision+",\"replace_existing_task\":true}";
    }
    @Test void canonicalChangeRequestReachesTheTypedServiceOnceAndPreservesEveryOriginalFault()throws Exception {
        for(var kind:PublicServiceFailure.Kind.values()) {
            var calls=new AtomicInteger();var registry=new PublicBindings();
            var original=new PublicServiceFailure(kind,"actual service message retained verbatim",Optional.of(SOURCE));
            var binding=RootGovernancePublicProducts.registerAction(registry,request->{
                calls.incrementAndGet();assertEquals(new GovernancePublicService.ChangeRequest(33554449,67108874,new BigInteger("18446744073709551615"),true),request);
                throw original;
            },SOURCE,QUALIFICATION);
            registry.freeze(Set.of(METHOD));
            assertEquals(GovernancePublicService.ChangeRequest.class,binding.requestType());assertEquals(RawJson.class,binding.resultType());
            assertEquals(PublicRoutes.Status.IMPLEMENTED,binding.info().status());assertTrue(binding.info().scope().contains("NativeReady=false"));
            var target=binding.info().target().orElseThrow();assertEquals(RootStewardDevelopmentPublicAction.Factory.class.getName(),target.actualClass());
            assertEquals("invoke",target.actualMethod());assertEquals(SOURCE,target.implementationSource());
            var actual=assertThrows(PublicServiceFailure.class,()->binding.invoke(PublicBindings.present(raw(arguments("\"18446744073709551615\"")))));
            assertSame(original,actual);assertEquals(kind,actual.kind());assertEquals(Optional.of(SOURCE),actual.originalCandidate());assertEquals(1,calls.get());
            assertTrue(registry.lookup(PublicMethod.QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1).isEmpty());
            assertTrue(registry.lookup(PublicMethod.QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1).isEmpty());
        }
    }
    @Test void malformedPublicArgumentsFailBeforeTheUnsupportedServiceOrAnyCandidateRead()throws Exception {
        var calls=new AtomicInteger();var registry=new PublicBindings();
        var binding=RootGovernancePublicProducts.registerAction(registry,request->{calls.incrementAndGet();throw new AssertionError("invalid request reached service");},SOURCE,QUALIFICATION);
        registry.freeze(Set.of(METHOD));
        assertThrows(IllegalArgumentException.class,()->binding.invoke(new PublicBindings.Missing()));
        assertThrows(IllegalArgumentException.class,()->binding.invoke(new PublicBindings.Null()));
        for(String revision:List.of("0","true","1.0","9007199254740992","null","\"01\"","\"18446744073709551616\""))
            assertThrows(IllegalArgumentException.class,()->binding.invoke(PublicBindings.present(raw(arguments(revision)))));
        for(String invalid:List.of("{}",arguments("1").replace("33554449","\"33554449\""),arguments("1").replace("67108874","2147483648"),
                arguments("1").replace("}",",\"unknown\":1}"),arguments("1").replace("true","null")))
            assertThrows(IllegalArgumentException.class,()->binding.invoke(PublicBindings.present(raw(invalid))));
        assertEquals(0,calls.get());
    }
}
