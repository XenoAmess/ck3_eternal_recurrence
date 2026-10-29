package org.xar.ck3.control.service.root;

import java.nio.charset.StandardCharsets;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.army.ContactScopeObservation;
import org.xar.ck3.control.nativebridge.capabilities.army.ContactScopePublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import static org.junit.jupiter.api.Assertions.*;

/** The actual pre-Core binding producer. Its data callbacks grant no current Root, Native or writer authority. */
final class RootContactPublicProductsTest {
    private static final ExactRef SOURCE=new ExactRef("software-contact-public-source",1,"a".repeat(64));
    @Test void exactTypedRegistrationDefersInvocationUntilTheActualRegistryFreeze()throws Exception {
        var calls=new AtomicInteger();var registry=new PublicBindings();
        RootContactPublicProducts.register(registry,SOURCE,request->{calls.incrementAndGet();return new ContactScopePublicCodec.Unavailable(new ContactScopeObservation.Projected(request.query()),"software source unavailable");},
                request->{calls.incrementAndGet();return new ContactScopePublicCodec.Unavailable(new ContactScopeObservation.Actual(request.query()),"software source unavailable");});
        assertEquals(0,calls.get());assertFalse(registry.frozen());
        var projected=registry.lookup(PublicMethod.QUERY_PROJECTED_CONTACT_SCOPE_V1).orElseThrow();
        var actual=registry.lookup(PublicMethod.QUERY_ACTUAL_CONTACT_SCOPE).orElseThrow();
        assertEquals(ContactScopePublicCodec.ProjectedRequest.class,projected.requestType());assertEquals(ContactScopePublicCodec.ActualRequest.class,actual.requestType());
        assertEquals(ContactScopePublicCodec.Response.class,actual.resultType());
        var args=arguments("{\"subject_army_id\":0,\"target_province_id\":31,\"incoming_entry_province_id\":30,\"expected_revision\":\"0\"}");
        assertThrows(IllegalArgumentException.class,()->projected.invoke(args));assertEquals(0,calls.get());
        registry.freeze(Set.of(PublicMethod.QUERY_PROJECTED_CONTACT_SCOPE_V1,PublicMethod.QUERY_ACTUAL_CONTACT_SCOPE));
        assertInstanceOf(ContactScopePublicCodec.Unavailable.class,ContactScopePublicCodec.decode(projected.invoke(args)));
        assertInstanceOf(ContactScopePublicCodec.Unavailable.class,ContactScopePublicCodec.decode(actual.invoke(arguments("{\"subject_army_id\":0,\"target_province_id\":31}"))));
        assertEquals(2,calls.get());
        assertThrows(IllegalArgumentException.class,()->actual.invoke(arguments("{\"subject_army_id\":true,\"target_province_id\":31}")));assertEquals(2,calls.get());
    }
    @Test void actualRuntimePreparationDeclaresOnlyItsRealReadSourcesAndNoInventedOrdinaryDomain() {
        var prepared=RootContactRuntime.prepare(new RootContactRuntime.Sources(SOURCE,SOURCE));
        assertEquals(SOURCE,prepared.sources().reads());assertEquals(SOURCE,prepared.sources().strictDecoder());assertTrue(prepared.domainRegistrations().isEmpty());
        assertThrows(NullPointerException.class,()->prepared.install(null));
        assertThrows(NullPointerException.class,()->RootContactPublicProducts.install(null,new PublicBindings()));
    }
    private static PublicBindings.Arguments arguments(String json){return PublicBindings.present(new RawJson(json.getBytes(StandardCharsets.UTF_8)));}
}
