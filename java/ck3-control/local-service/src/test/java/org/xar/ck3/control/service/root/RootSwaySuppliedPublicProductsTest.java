package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Set;
import java.util.Optional;
import org.xar.ck3.control.application.planning.sway.SwayDriverCodec;
import org.xar.ck3.control.service.mcp.*;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.planning.sway.SwayObservationReads;
import org.xar.ck3.control.application.planning.sway.SwayPublicCodec;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;

/** The actual registrar/decoder path with a software final port; no Root Context/Core is fabricated. */
final class RootSwaySuppliedPublicProductsTest {
    private static final Set<PublicMethod> METHODS=Set.of(PublicMethod.QUERY_ACTIVE_SCHEME_SWAY_COMPLETION_PRIVATE_V1,PublicMethod.QUERY_ACTIVE_SCHEME_SWAY_OUTCOME_OPINION_PRIVATE_V1);
    @Test void registrationNeedsNoCoreReservesOnlyTwoActualMethodsAndUsesCanonicalTypedCodec()throws Exception {
        var registry=new PublicBindings();var calls=new AtomicInteger();
        RootSwaySuppliedPublicProducts.register(registry,new ExactRef("software:actual-helper-source",1,"a".repeat(64)),request->{calls.incrementAndGet();return SwayPublicCodec.encodeDirectRequest(request);});
        assertFalse(registry.frozen());assertEquals(METHODS,Set.copyOf(registry.coverage().installed()));
        assertTrue(registry.lookup(PublicMethod.FINISH_ACTIVE_SCHEME_SWAY_PRIVATE_V1).isEmpty());assertTrue(registry.lookup(PublicMethod.QUERY_ACTIVE_SCHEME_SWAY_COMPLETION_EXECUTION_PRIVATE_V1).isEmpty());
        registry.freeze(METHODS);
        for(var method:METHODS){var kind=method==PublicMethod.QUERY_ACTIVE_SCHEME_SWAY_COMPLETION_PRIVATE_V1?SwayObservationReads.Kind.COMPLETION:SwayObservationReads.Kind.OPINION;
            var expected=new SwayPublicCodec.DirectRequest(kind,new BigInteger("18446744073709551615"),50331650,kind==SwayObservationReads.Kind.COMPLETION?java.util.OptionalLong.of(33554443):java.util.OptionalLong.empty());
            var route=registry.lookup(method).orElseThrow();assertEquals(SwayPublicCodec.DirectRequest.class,route.requestType());assertEquals(expected,SwayPublicCodec.decodeDirect(kind,route.invoke(PublicBindings.present(SwayPublicCodec.encodeDirectRequest(expected)))));
        }assertEquals(2,calls.get());
    }
    @Test void registryRejectsOriginalMissingNullAndWrongShapeBeforeCallingAnyRuntimePort() {
        var registry=new PublicBindings();var calls=new AtomicInteger();RootSwaySuppliedPublicProducts.register(registry,new ExactRef("software:actual-helper-source",1,"a".repeat(64)),request->{calls.incrementAndGet();throw new AssertionError("invalid boundary cannot reach runtime");});registry.freeze(METHODS);
        for(var method:METHODS){var route=registry.lookup(method).orElseThrow();assertThrows(IllegalArgumentException.class,()->route.invoke(new PublicBindings.Missing()));assertThrows(IllegalArgumentException.class,()->route.invoke(new PublicBindings.Null()));
            for(String text:new String[]{"{}","{\"expected_revision\":null,\"target_character_id\":50331650}","{\"expected_revision\":true,\"target_character_id\":50331650}","{\"expected_revision\":7.0,\"target_character_id\":50331650}","{\"expected_revision\":17,\"target_character_id\":50331650,\"action_id\":\"forged\"}"})assertThrows(IllegalArgumentException.class,()->route.invoke(PublicBindings.present(new RawJson(text.getBytes(StandardCharsets.UTF_8)))));
        }assertEquals(0,calls.get());
    }
    @Test void originalThreeDriverBindingsUseActualTypedDecodersAndMcpResultEnvelopeWithoutTakingServiceSlots()throws Exception {
        var calls=new AtomicInteger();var source=new ExactRef("software:driver-helper",1,"b".repeat(64));
        var direct=RootSwaySuppliedPublicProducts.driverBindings(source,request->{calls.incrementAndGet();return SwayDriverCodec.encode(request);},request->{calls.incrementAndGet();return SwayDriverCodec.encode(request);},request->{calls.incrementAndGet();return SwayDriverCodec.encode(request);});
        assertEquals(Set.of("ck3_query_active_scheme_sway_target_private_v1","ck3_start_active_scheme_sway_private_v1","ck3_query_active_scheme_sway_receipt_private_v1"),direct.stream().map(McpExecutableDirectory.DirectBinding::name).collect(java.util.stream.Collectors.toSet()));
        assertTrue(direct.stream().allMatch(binding->binding.kind()==PublicMcpBindings.Kind.DRIVER_DIRECT&&binding.target().implementationSource().equals(source)));
        var target=direct.stream().filter(binding->binding.requestType()==SwayDriverCodec.TargetRequest.class).findFirst().orElseThrow();var request=new SwayDriverCodec.TargetRequest(new BigInteger("18446744073709551615"),50331650);
        var result=invoke(target,SwayDriverCodec.encode(request));assertEquals(request.expectedRevision().toString(),org.xar.ck3.control.contracts.StrictJson.parse(result.bytes()).at("/structuredContent/expected_revision").textValue());
        var receipt=direct.stream().filter(binding->binding.requestType()==SwayDriverCodec.ReceiptRequest.class).findFirst().orElseThrow();var identity=new SwayDriverCodec.ReceiptRequest(request.expectedRevision(),50331650,"sway-original-public",new BigInteger("18446744073709551615"));
        var returned=invoke(receipt,SwayDriverCodec.encode(identity));assertEquals(identity.preCaptureEpoch().toString(),org.xar.ck3.control.contracts.StrictJson.parse(returned.bytes()).at("/structuredContent/pre_capture_epoch").textValue());assertEquals(2,calls.get());
    }
    @Test void driverMissingNullAndWrongTypesCannotReachAnyFinalRuntimePort() {
        var calls=new AtomicInteger();var bindings=RootSwaySuppliedPublicProducts.driverBindings(new ExactRef("software:driver-helper",1,"b".repeat(64)),request->{calls.incrementAndGet();throw new AssertionError();},request->{calls.incrementAndGet();throw new AssertionError();},request->{calls.incrementAndGet();throw new AssertionError();});
        for(var binding:bindings){
            assertThrows(IllegalArgumentException.class,()->binding.decoder().decode(new PublicMcpDirectory.ToolCall(binding.name(),new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.MISSING,Optional.empty()),Optional.empty(),new McpCancellation())));
            assertThrows(IllegalArgumentException.class,()->binding.decoder().decode(new PublicMcpDirectory.ToolCall(binding.name(),new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.NULL,Optional.of(new RawJson("null".getBytes(StandardCharsets.UTF_8)))),Optional.empty(),new McpCancellation())));
            for(String text:new String[]{"{}","{\"expected_revision\":true,\"target_character_id\":50331650}","{\"readback\":{},\"action_id\":true}"})assertThrows(IllegalArgumentException.class,()->invoke(binding,new RawJson(text.getBytes(StandardCharsets.UTF_8))));
        }assertEquals(0,calls.get());
    }
    @Test void originalNotificationDriverBindingUsesTheSoleTypedCodecAndNeverFabricatesAnAction()throws Exception {
        var calls=new AtomicInteger();var source=new ExactRef("software:notification-helper",1,"c".repeat(64));
        var binding=RootSwaySuppliedPublicProducts.invalidationBinding(source,request->{calls.incrementAndGet();return SwayPublicCodec.encodeInvalidationRequest(request);});
        assertEquals("ck3_query_active_scheme_sway_completion_invalidation_reason_private_v1",binding.name());
        assertEquals(PublicMcpBindings.Kind.DRIVER_DIRECT,binding.kind());assertEquals(source,binding.target().implementationSource());
        var request=new SwayPublicCodec.InvalidationRequest(org.xar.ck3.control.contracts.StrictJson.UINT64_MAX,50331650,33554443,org.xar.ck3.control.contracts.StrictJson.UINT64_MAX);
        var result=invoke(binding,SwayPublicCodec.encodeInvalidationRequest(request));var wire=org.xar.ck3.control.contracts.StrictJson.parse(result.bytes());
        assertEquals(request.afterSequence().toString(),wire.at("/structuredContent/after_sequence").textValue());assertEquals(1,calls.get());
        for(String text:new String[]{"{}","null","{\"expected_revision\":1,\"target_character_id\":50331650,\"scheme_instance_id\":33554443,\"after_sequence\":null}","{\"expected_revision\":true,\"target_character_id\":50331650,\"scheme_instance_id\":33554443}"})
            assertThrows(IllegalArgumentException.class,()->invoke(binding,new RawJson(text.getBytes(StandardCharsets.UTF_8))));
        assertEquals(1,calls.get());
    }
    /** Mandatory real Root fixture hook. It consumes private currentOwned/session and the actual archive, never mints them. */
    public static RawJson assertActualNotificationRootAndColdArchive(RootApplicationSession actualRoot,
            org.xar.ck3.control.service.sway.SwayRuntimeInstaller actualSway,
            org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive actualArchive,
            SwayPublicCodec.InvalidationRequest request,java.time.Instant deadline)throws Exception {
        actualSway.requireOwner(actualRoot);
        return actualRoot.executePublicDecision(deadline,(frame,known,same)->{
            assertEquals(frame.identity().frame().revision(),request.expectedRevision());
            long actor=frame.identity().frame().identity().player().longValueExact();
            var query=new SwayObservationReads.InvalidationQuery(new org.xar.ck3.control.g2.m6.G2M6Contracts.NativeSubject(actor,request.targetCharacterId(),request.schemeInstanceId(),(int)(request.schemeInstanceId()>>24)),request.afterSequence());
            var observed=actualSway.readInvalidation(same,frame,query,deadline);
            var originals=actualArchive.withSession(same);var cold=originals.loadRead(originals.readReferenceOf(observed.original()));
            assertEquals(observed.original(),cold);var retained=actualSway.replayInvalidation(same,query,cold,deadline);
            assertArrayEquals(observed.normalized().bytes(),retained.normalized().bytes());
            return new RootApplicationSession.RetainPublicResult<RawJson>(SwayPublicCodec.publicNormalized(retained));
        },(receipt,archive,same)->{throw new java.io.IOException("notification fixture cannot submit an action");});
    }
    private static <Q,R> PublicMcpDirectory.CallResult invoke(McpExecutableDirectory.DirectBinding<Q,R> binding,RawJson arguments)throws Exception {
        var call=new PublicMcpDirectory.ToolCall(binding.name(),new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,Optional.of(arguments)),Optional.empty(),new McpCancellation());return binding.encoder().encode(binding.actual().invoke(binding.decoder().decode(call)));
    }

}
