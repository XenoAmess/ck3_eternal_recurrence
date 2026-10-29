package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.interactions.TitleClaimsPublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;

/** Actual registrar to typed consumer round trip. The final software port grants no Root/native qualification. */
final class RootTitleClaimsPublicProductsTest {
    private static final Set<PublicMethod> METHODS=Set.of(PublicMethod.QUERY_TITLE_OWN_LAWS_V1,PublicMethod.QUERY_PLAYER_CLAIMS_V1,PublicMethod.QUERY_TITLE_HOLDER_V1,PublicMethod.QUERY_CURRENT_TITLE_APPOINTMENT_V1);
    @Test void fourOriginalServiceReadBindingsKeepTheirIndependentSlotsBeforeCore()throws Exception {
        var registry=new PublicBindings();var calls=new AtomicInteger();RootTitleClaimsPublicProducts.register(registry,new ExactRef("software-title-binder",1,"a".repeat(64)),request->{calls.incrementAndGet();return TitleClaimsPublicCodec.encode(request);});
        assertEquals(METHODS,Set.copyOf(registry.coverage().installed()));assertTrue(registry.lookup(PublicMethod.SET_PLAYER_CHARACTER_V1).isEmpty());registry.freeze(METHODS);
        for(var method:METHODS){String fields=method==PublicMethod.QUERY_CURRENT_TITLE_APPOINTMENT_V1?"":method==PublicMethod.QUERY_PLAYER_CLAIMS_V1?",\"title_ids\":[2,1]":",\"title_id\":0";var route=registry.lookup(method).orElseThrow();assertEquals(TitleClaimsPublicCodec.Request.class,route.requestType());var first=route.invoke(PublicBindings.present(raw("{\"expected_revision\":\"18446744073709551615\""+fields+"}")));assertEquals(first,route.invoke(PublicBindings.present(first)));}assertEquals(8,calls.get());
    }
    @Test void missingNullWrongTypesAndExtraFieldsFailBeforeAnyRuntimeRead() {
        var registry=new PublicBindings();var calls=new AtomicInteger();RootTitleClaimsPublicProducts.register(registry,new ExactRef("software-title-binder",1,"a".repeat(64)),request->{calls.incrementAndGet();throw new AssertionError("invalid public request reached runtime");});registry.freeze(METHODS);
        for(var method:METHODS){var route=registry.lookup(method).orElseThrow();assertThrows(IllegalArgumentException.class,()->route.invoke(new PublicBindings.Missing()));assertThrows(IllegalArgumentException.class,()->route.invoke(new PublicBindings.Null()));for(String value:new String[]{"{}","{\"expected_revision\":null}","{\"expected_revision\":true}","{\"expected_revision\":0,\"unexpected\":1}"})assertThrows(IllegalArgumentException.class,()->route.invoke(PublicBindings.present(raw(value))));}assertEquals(0,calls.get());
    }
    @Test void originalSetterUsesItsUniqueSharedRequestCodecAndReturnsTheActualPortResult()throws Exception {
        var registry=new PublicBindings();var calls=new AtomicInteger();var original=raw("{\"accepted\":true,\"status\":\"switched\",\"to_character_id\":2147483647,\"postcondition_verified\":true,\"actual_operator_result\":\"kept verbatim\"}");
        RootTitleClaimsPublicProducts.registerOperator(registry,new ExactRef("software-operator-binder",1,"b".repeat(64)),request->{
            calls.incrementAndGet();assertEquals(2147483647L,request.characterId());assertEquals(new java.math.BigInteger("18446744073709551615"),request.expectedRevision());return original;
        });
        assertEquals(Set.of(PublicMethod.SET_PLAYER_CHARACTER_V1),Set.copyOf(registry.coverage().installed()));registry.freeze(Set.of(PublicMethod.SET_PLAYER_CHARACTER_V1));
        var route=registry.lookup(PublicMethod.SET_PLAYER_CHARACTER_V1).orElseThrow();
        assertEquals(org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch.Request.class,route.requestType());
        assertSame(original,route.invoke(PublicBindings.present(raw("{\"character_id\":2147483647,\"expected_revision\":\"18446744073709551615\"}"))));assertEquals(1,calls.get());
        var value=org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch.decode(raw("{\"character_id\":1,\"expected_revision\":0}"));
        assertEquals(java.math.BigInteger.ZERO,value.expectedRevision());
    }
    @Test void setterMissingNullWrongTypesAndExtraFieldsDoNotReachAnyActualSwitchPort() {
        var registry=new PublicBindings();var calls=new AtomicInteger();
        RootTitleClaimsPublicProducts.registerOperator(registry,new ExactRef("software-operator-binder",1,"b".repeat(64)),request->{calls.incrementAndGet();throw new AssertionError("invalid setter argument reached actual source");});
        registry.freeze(Set.of(PublicMethod.SET_PLAYER_CHARACTER_V1));var route=registry.lookup(PublicMethod.SET_PLAYER_CHARACTER_V1).orElseThrow();
        assertThrows(IllegalArgumentException.class,()->route.invoke(new PublicBindings.Missing()));assertThrows(IllegalArgumentException.class,()->route.invoke(new PublicBindings.Null()));
        for(String text:new String[]{"{}","{\"character_id\":true,\"expected_revision\":0}","{\"character_id\":1.0,\"expected_revision\":0}","{\"character_id\":\"1\",\"expected_revision\":0}","{\"character_id\":1,\"expected_revision\":null}","{\"character_id\":1,\"expected_revision\":false}","{\"character_id\":1,\"expected_revision\":1.0}","{\"character_id\":1,\"expected_revision\":9007199254740992}","{\"character_id\":1,\"expected_revision\":\"01\"}","{\"character_id\":1,\"expected_revision\":0,\"new_action_id\":\"forged\"}"})
            assertThrows(IllegalArgumentException.class,()->route.invoke(PublicBindings.present(raw(text))));
        assertEquals(0,calls.get());
    }
    /** Whole-graph fixture must supply the real Prepared/Core/context. No replacement SourceFactory is created here. */
    public static RootTitleClaimsRuntime assertActualOperatorAggregation(RootTitleClaimsRuntime.Prepared title,
            RootSetPlayedCharacterRuntime.Prepared originalOperator,RootApplicationAssembly.Core core,
            RootRuntimeContext actualContext)throws Exception {
        title.bindCore(core);var actual=title.install(actualContext);actual.requireContext(actualContext);
        assertSame(actual,title.install(actualContext));var operator=originalOperator.install(actualContext);
        assertSame(operator.runtime(),actual.operatorSwitch());assertEquals(originalOperator.domainRegistrations(),title.domainRegistrations());
        assertEquals(java.util.List.copyOf(originalOperator.privatePermissions()),java.util.List.copyOf(title.privatePermissions()));
        assertEquals(operator.installation().actions(),actual.installation().actions());
        assertEquals(operator.installation().archived(),actual.installation().archived());
        assertEquals(operator.installation().actionFamilies(),actual.installation().actionFamilies());
        for(var family:operator.installation().readFamilies())assertTrue(actual.installation().readFamilies().stream().anyMatch(value->value==family));
        return actual;
    }
    private static RawJson raw(String value){return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
}
