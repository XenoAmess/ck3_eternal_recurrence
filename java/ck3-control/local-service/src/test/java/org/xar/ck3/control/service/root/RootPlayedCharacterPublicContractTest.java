package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/** Actual public registrar and production validation; software DATA never substitutes for a native or Root issuer. */
public final class RootPlayedCharacterPublicContractTest {
    private static final OperatorPlayerSwitch.Request REQUEST=new OperatorPlayerSwitch.Request(42,BigInteger.valueOf(7));
    private static RawJson raw(String text){return new RawJson(text.getBytes(StandardCharsets.UTF_8));}
    private static PublicBindings route(RootTitleClaimsPublicProducts.CurrentOperator actual){
        var registry=new PublicBindings();
        RootTitleClaimsPublicProducts.registerOperator(registry,new ExactRef("software/operator-binder",1,"b".repeat(64)),actual);
        registry.freeze(Set.of(PublicMethod.SET_PLAYER_CHARACTER_V1));
        return registry;
    }
    private static RawJson invoke(PublicBindings actual)throws InterruptedException {
        return actual.lookup(PublicMethod.SET_PLAYER_CHARACTER_V1).orElseThrow().invoke(
                PublicBindings.present(raw("{\"character_id\":42,\"expected_revision\":7}")));
    }
    private static PublicServiceFailure unavailable(Runnable actual,String message){
        var failure=assertThrows(PublicServiceFailure.class,actual::run);
        assertEquals(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,failure.kind());assertEquals(message,failure.getMessage());
        return failure;
    }

    @Test void switchedAndAlreadyPlayedPreserveActualResultBytesAndWideStrings()throws Exception{
        for(String status:new String[]{"switched","already_played"}){
            var original=raw("{\"accepted\":true,\"status\":\""+status+"\",\"to_character_id\":42,\"postcondition_verified\":true,\"native_revision\":\"18446744073709551615\",\"ratio\":-0.0}");
            var actual=route(request->{assertEquals(REQUEST,request);return original;});
            assertSame(original,invoke(actual));
        }
    }

    @Test void malformedPostconditionsFailThroughActualProducerConsumerRegistrar(){
        for(String text:new String[]{"{}","[]","{\"accepted\":false,\"status\":\"switched\",\"to_character_id\":42,\"postcondition_verified\":true}",
                "{\"accepted\":true,\"status\":\"unknown\",\"to_character_id\":42,\"postcondition_verified\":true}",
                "{\"accepted\":true,\"status\":\"switched\",\"to_character_id\":43,\"postcondition_verified\":true}",
                "{\"accepted\":true,\"status\":\"switched\",\"to_character_id\":true,\"postcondition_verified\":true}",
                "{\"accepted\":true,\"status\":\"switched\",\"to_character_id\":42.0,\"postcondition_verified\":true}",
                "{\"accepted\":true,\"status\":\"switched\",\"to_character_id\":\"42\",\"postcondition_verified\":true}",
                "{\"accepted\":true,\"status\":\"switched\",\"to_character_id\":42}",
                "{\"accepted\":true,\"status\":\"switched\",\"to_character_id\":42,\"postcondition_verified\":1}"}){
            var calls=new AtomicInteger();var actual=route(request->{calls.incrementAndGet();return raw(text);});
            var failure=assertThrows(PublicServiceFailure.class,()->invoke(actual));
            assertEquals(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,failure.kind());
            assertEquals("played-character rebind returned a malformed postcondition",failure.getMessage());assertEquals(1,calls.get());
        }
    }

    @Test void missingTypedPortResultIsNotPublished(){
        var actual=route(request->null);
        var failure=assertThrows(PublicServiceFailure.class,()->invoke(actual));
        assertEquals(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,failure.kind());
    }

    @Test void originalSourceFaultReachesThePublicConsumerWithoutRelabeling(){
        var sourceFailure=new PublicServiceFailure(PublicServiceFailure.Kind.NATIVE_COMMAND_REJECTED,
                "native gameplay step failed: target_dead",Optional.of(new ExactRef("software/rejected-original",1,"c".repeat(64))));
        var actual=route(request->{throw sourceFailure;});
        assertSame(sourceFailure,assertThrows(PublicServiceFailure.class,
                ()->invoke(actual)));
    }

    @Test void absentCapabilityKeepsOriginalServiceUnsupportedFault(){
        var failure=assertThrows(PublicServiceFailure.class,()->RootPlayedCharacterPublicContract.requireCapability(Set.of()));
        assertEquals(PublicServiceFailure.Kind.UNSUPPORTED_STEP,failure.kind());
        assertEquals("capability_not_available: selected backend cannot rebind the played character",failure.getMessage());
    }

    @Test void pausedAndMapReadyChecksPrecedeRevisionMismatch(){
        for(String text:new String[]{"{\"paused\":false,\"map_ready\":true,\"revision\":8}",
                "{\"paused\":true,\"map_ready\":false,\"revision\":8}","{\"paused\":1,\"map_ready\":true,\"revision\":8}"})
            unavailable(()->RootPlayedCharacterPublicContract.requireBefore(REQUEST,DriverJson.object(raw(text).bytes(),4096)),
                    "played-character rebind requires a paused map-ready snapshot");
    }

    @Test void revisionMismatchRetainsOriginalExpectedAndCurrentValues(){
        var failure=assertThrows(PublicServiceFailure.class,()->RootPlayedCharacterPublicContract.requireBefore(REQUEST,
                DriverJson.object(raw("{\"paused\":true,\"map_ready\":true,\"revision\":8}").bytes(),4096)));
        assertEquals(PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,failure.kind());
        assertEquals("played-character rebind revision mismatch: expected 7, current 8",failure.getMessage());
    }

    @Test void internalUnsignedRevisionRetainsExactIntegerLaneWithoutJavascriptRounding(){
        var request=new OperatorPlayerSwitch.Request(42,new BigInteger("18446744073709551615"));
        assertDoesNotThrow(()->RootPlayedCharacterPublicContract.requireBefore(request,
                DriverJson.object(raw("{\"paused\":true,\"map_ready\":true,\"revision\":18446744073709551615}").bytes(),4096)));
        for(String token:new String[]{"true","1.0","\"7\"","-1","18446744073709551616"})
            unavailable(()->RootPlayedCharacterPublicContract.requireBefore(REQUEST,
                    DriverJson.object(raw("{\"paused\":true,\"map_ready\":true,\"revision\":"+token+"}").bytes(),4096)),
                    "played-character rebind requires an exact uint64 snapshot revision");
    }
}
