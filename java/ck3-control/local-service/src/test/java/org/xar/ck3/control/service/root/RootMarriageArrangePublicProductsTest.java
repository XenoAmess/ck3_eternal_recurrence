package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.MarriageArrangePublicCodecTest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.service.mcp.MarriageArrangePublicCodec;

/** Real registry/codec/pure-original selection. These DATA cases do not construct Root/Core/Managed or authorize a submission. */
final class RootMarriageArrangePublicProductsTest {
    private static final ExactRef SOURCE=new ExactRef("synthetic/public-arrange-source",1,"a".repeat(64));
    private static PublicBindings.Arguments args(String value){return PublicBindings.present(new RawJson(value.getBytes(StandardCharsets.UTF_8)));}
    @Test void typedServiceRegistrationAndFrozenInvocationUseOnlyArrangeAndPreserveUnknown()throws Exception {
        var registry=new PublicBindings();var calls=new AtomicInteger();
        RootMarriageArrangePublicProducts.register(registry,SOURCE,request->{
            calls.incrementAndGet();assertEquals("29829-8",request.choiceId());return new MarriageArrangePublicCodec.Reply(MarriageArrangePublicCodecTest.unknownData(),false);
        });
        var route=registry.lookup(PublicMethod.ARRANGE_MARRIAGE).orElseThrow();
        assertEquals(MarriageArrangePublicCodec.Request.class,route.requestType());assertEquals(MarriageArrangePublicCodec.Reply.class,route.resultType());
        assertEquals(0,calls.get());assertThrows(IllegalArgumentException.class,()->route.invoke(args("{\"choice_id\":\"29829-8\"}")));
        assertTrue(registry.lookup(PublicMethod.QUERY_ARRANGE_MARRIAGE_CHOICES).isEmpty());
        assertTrue(registry.lookup(PublicMethod.REPLY_PENDING_CHARACTER_INTERACTION).isEmpty());
        assertThrows(IllegalArgumentException.class,()->RootMarriageArrangePublicProducts.register(registry,SOURCE,request->new MarriageArrangePublicCodec.Reply(MarriageArrangePublicCodecTest.unknownData(),false)));
        registry.freeze(Set.of(PublicMethod.ARRANGE_MARRIAGE));
        var result=route.invoke(args("{\"choice_id\":\"29829-8\",\"expected_revision\":null}"));
        assertEquals(1,calls.get());var row=StrictJson.parse(result.bytes());assertEquals("unknown",row.path("marriage_action").get("status").textValue());
        assertFalse(row.get("send_confirmed").booleanValue());assertTrue(row.get("accepted").isNull());
        assertThrows(IllegalArgumentException.class,()->route.invoke(args("{\"choice_id\":true}")));assertEquals(1,calls.get());
    }
    @Test void actualNativeOwnerFaultCrossesTheRealTypedPublicBindingWithoutACommandOrGuessedError()throws Exception {
        var rig=new RootMarriagePublicStepProductsTest.Rig();var registry=new PublicBindings();
        RootMarriageArrangePublicProducts.register(registry,SOURCE,request->{
            RootMarriageArrangePublicProducts.prepareOriginal(rig.facade,rig.context,"actual-public-missing",new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),request.choiceId());
            throw new AssertionError("an absent original query cannot produce a command");
        });registry.freeze(Set.of(PublicMethod.ARRANGE_MARRIAGE));
        var failure=assertThrows(org.xar.ck3.control.service.mcp.PublicServiceFailure.class,()->registry.lookup(PublicMethod.ARRANGE_MARRIAGE).orElseThrow().invoke(args("{\"choice_id\":\"29829-8\",\"expected_revision\":null}")));
        assertEquals(org.xar.ck3.control.service.mcp.PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,failure.kind());
        assertEquals("BridgeUnavailableError",failure.kind().pythonClassName());
        assertEquals("native arrange-marriage choice is not in the latest query",failure.getMessage());assertTrue(failure.originalCandidate().isEmpty());
        var original=assertInstanceOf(org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionOriginalFailure.class,failure.getCause());
        original.requireProducer(rig.facade,rig.context,"29829-8");assertTrue(original.originalQuery().isEmpty());
        assertEquals(org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionOriginalFailure.CauseBranch.NO_RETAINED_QUERY,original.causeBranch());
        assertEquals(0,rig.submissions);
    }
    @Test void typedFaultMappingRejectsOtherProducersContextsAndSelectorsAndRetainsReadProvenanceOnly() {
        var rig=new RootMarriagePublicStepProductsTest.Rig();rig.query();
        var claims=new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of());
        var original=assertThrows(org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionOriginalFailure.class,
                ()->rig.facade.prepareArrangeMarriage(rig.context,"actual-absent-choice",claims,"29829-9"));
        assertEquals(org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionOriginalFailure.CauseBranch.CHOICE_ABSENT,original.causeBranch());
        assertTrue(original.originalQuery().isPresent());
        var mapped=RootMarriageArrangePublicProducts.originalFailure(original,rig.facade,rig.context,"29829-9");assertTrue(mapped.originalCandidate().isEmpty());assertSame(original,mapped.getCause());
        var other=new RootMarriagePublicStepProductsTest.Rig();
        assertThrows(IllegalArgumentException.class,()->RootMarriageArrangePublicProducts.originalFailure(original,other.facade,rig.context,"29829-9"));
        assertThrows(IllegalArgumentException.class,()->RootMarriageArrangePublicProducts.originalFailure(original,rig.facade,rig.context,"29829-8"));
        var c=rig.context;var changed=new org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.Context(c.before(),c.source(),c.sessionId(),java.math.BigInteger.TWO,
                org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.Build.CROZIER4,c.deadline().plusSeconds(1),c.controls());
        assertThrows(IllegalArgumentException.class,()->RootMarriageArrangePublicProducts.originalFailure(original,rig.facade,changed,"29829-9"));
        var javaGuard=assertThrows(IllegalArgumentException.class,()->RootMarriageArrangePublicProducts.prepareOriginal(rig.facade,rig.context,"bad-java-selector",claims,"not-a-pair"));
        assertFalse(((Throwable)javaGuard) instanceof org.xar.ck3.control.service.mcp.PublicServiceFailure);assertEquals(0,rig.submissions);
    }
    @Test void samePairUnknownSelectsTheOriginalIdentityAndOtherPairOrSourceCannotBorrowIt() {
        var original=MarriageArrangePublicCodecTest.unknownData();var command=original.command();
        var request=MarriageArrangePublicCodec.decode(args("{\"choice_id\":\"29829-8\"}"));
        assertSame(original,RootMarriageArrangePublicProducts.originalUnresolved(request,List.of(original),command.before(),command.source(),command.sessionId()).orElseThrow());
        assertTrue(RootMarriageArrangePublicProducts.originalUnresolved(request,List.of(),command.before(),command.source(),command.sessionId()).isEmpty());
        assertThrows(IllegalArgumentException.class,()->RootMarriageArrangePublicProducts.originalUnresolved(
                MarriageArrangePublicCodec.decode(args("{\"choice_id\":\"29829-9\"}")),List.of(original),command.before(),command.source(),command.sessionId()));
        assertThrows(IllegalArgumentException.class,()->RootMarriageArrangePublicProducts.originalUnresolved(request,List.of(original),command.before(),command.source(),"another-session"));
        assertThrows(IllegalArgumentException.class,()->RootMarriageArrangePublicProducts.originalUnresolved(request,List.of(original,original),command.before(),command.source(),command.sessionId()));
        assertEquals("send-data",original.command().actionId());assertFalse(original.settled());
    }
    @Test void actualCurrentSourceFailureDoesNotBecomeAnEmptySuccessOrASecondSubmission() {
        var registry=new PublicBindings();var missing=new UncheckedIOException(new IOException("actual Root/native source unavailable"));
        RootMarriageArrangePublicProducts.register(registry,SOURCE,request->{throw missing;});registry.freeze(Set.of(PublicMethod.ARRANGE_MARRIAGE));
        assertSame(missing,assertThrows(UncheckedIOException.class,()->registry.lookup(PublicMethod.ARRANGE_MARRIAGE).orElseThrow().invoke(args("{\"choice_id\":\"29829-8\"}"))));
    }
}
