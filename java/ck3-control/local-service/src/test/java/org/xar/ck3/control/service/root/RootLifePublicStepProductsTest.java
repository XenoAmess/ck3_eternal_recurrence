package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/** Strict public protocol and actual software canonical UNKNOWN. No installed Life/Core, Ready,
 * successful clock result or native permission is fabricated by these tests. The whole-Root hook
 * below needs the actual admitted runtime; its absence is NOT_RUN, not a successful fixture. */
final class RootLifePublicStepProductsTest {
    @TempDir Path temporary;
    private static RawJson raw(String text){return new RawJson(text.getBytes(StandardCharsets.UTF_8));}
    private static PublicPlanningCodec.ExecuteRequest caller(String text){
        return PublicPlanningCodec.decodeExecute(PublicBindings.present(raw(text)));
    }
    private static RootPublicStepExecution.Action selected(List<RootPublicStepExecution.Product> products,
            PublicPlanningCodec.ExecuteRequest caller)throws IOException {
        return assertInstanceOf(RootPublicStepExecution.Action.class,RootPublicStepExecution.select(products,caller));
    }

    @Test void actualExecuteSerdeSelectsOnlyTheTwoOriginalLifeStepsWithoutInvokingAnOwnerOrPlanner()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("protocol"),false)) {
            var invoked=new AtomicInteger();
            var products=RootLifePublicStepProducts.bind(ignored->{invoked.incrementAndGet();throw new AssertionError("selection grants no Root ownership");},
                    List.of(fixture.observationSource().sourceRef()),
                    (original,frame,known,same,input)->{invoked.incrementAndGet();throw new AssertionError("selection must not prepare or choose a step");},
                    (actual,archive,same,input)->{invoked.incrementAndGet();throw new AssertionError("selection creates no result");});
            assertEquals(2,products.size());
            for(String step:List.of("life-advance","life-advance-one-day")) {
                for(String suffix:List.of("",",\"expected_revision\":null",",\"expected_revision\":9007199254740991",",\"expected_revision\":\"18446744073709551615\"")) {
                    var input=caller("{\"step\":\""+step+"\""+suffix+"}");
                    var restored=PublicPlanningCodec.decodeExecute(PublicBindings.present(PublicPlanningCodec.encodeExecute(input)));
                    assertEquals(input,restored);assertTrue(selected(products,restored).matches(input.step()));
                }
            }
            for(String other:List.of("life-advance:x","life-advance-one-day-2","advance-days:1","route-contact-window-advance-v1",
                    "battle-decision-epoch-advance","committed-route-sentinel-advance","war-objective-hold-sentinel-advance","pause-map")) {
                var input=caller("{\"step\":\""+other+"\"}");
                var unsupported=assertThrows(PublicServiceFailure.class,()->RootPublicStepExecution.select(products,input));
                assertEquals(PublicServiceFailure.Kind.UNSUPPORTED_STEP,unsupported.kind());
            }
            assertEquals(0,invoked.get());assertEquals(0,fixture.nativeActionWrites());assertEquals(0,fixture.nativeReadWrites());
        }
    }

    @Test void malformedFieldsAndCurrentRevisionDriftRefuseBeforeTheSoleLifePreparationDelegate()throws Exception {
        var calls=new AtomicInteger();
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("stale"),false)) {
            var request=fixture.ready().request();var source=fixture.observationSource().sourceRef();
            var originalError=new PublicServiceFailure(PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,
                    "original Life entry changed",Optional.of(source));
            var products=RootLifePublicStepProducts.bind(ignored->{},List.of(source),
                    (original,frame,known,same,input)->{calls.incrementAndGet();throw originalError;},
                    (actual,archive,same,input)->{throw new AssertionError("no original Life result exists");});
            for(String text:List.of("{\"step\":\"life-advance\",\"expected_revision\":true}",
                    "{\"step\":\"life-advance\",\"expected_revision\":1.0}",
                    "{\"step\":\"life-advance\",\"expected_revision\":-1}",
                    "{\"step\":\"life-advance\",\"expected_revision\":9007199254740992}",
                    "{\"step\":\"life-advance\",\"expected_revision\":\"01\"}",
                    "{\"step\":\"life-advance\",\"plan\":{}}",
                    "{\"step\":\"life-advance\",\"advance_v1\":{}}",
                    "{\"step\":\"life-advance\",\"maximum_target_date_raw\":1000}",
                    "{\"step\":\"life-advance\",\"expected_revision\":1,\"expected_revision\":2}"))
                assertThrows(IllegalArgumentException.class,()->caller(text));
            var stale=caller("{\"step\":\"life-advance\",\"expected_revision\":\""+request.before().frame().revision().add(BigInteger.ONE)+"\"}");
            var product=selected(products,stale);
            assertThrows(IllegalArgumentException.class,()->product.preparation().prepare(request,null,null,null,stale));assertEquals(0,calls.get());
            var current=caller("{\"step\":\"life-advance\"}");
            assertSame(originalError,assertThrows(PublicServiceFailure.class,()->selected(products,current).preparation().prepare(request,null,null,null,current)));
            assertEquals(1,calls.get());assertEquals(0,fixture.nativeActionWrites());assertEquals(0,fixture.nativeReadWrites());
            var wrong=caller("{\"step\":\"life-advance-one-day\"}");
            assertThrows(IOException.class,()->product.preparation().prepare(request,null,null,null,wrong));assertEquals(1,calls.get());
        }
    }

    @Test void actualCanonicalUnknownHasNoOriginalLifeReturnAndPresentationNeverResubmits()throws Exception {
        var operation=new OperationKey("life-advance");
        var software=new ActionWriterIntegrationFixture.SoftwareActionScenario(operation,"software.life-origin-negative",
                (command,attempt,dispatch)->new ActionPorts.Pending("software has no actual Life clock completion",List.of(attempt.guard().nativeEvidence())),()->{});
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("unknown"),true,software)) {
            // This genuine primitive software command cannot impersonate the installed Life composite.
            var command=fixture.command("actual-life-unresolved");var receipt=fixture.coordinator.execute(command);
            assertFalse(receipt.settled());assertTrue(receipt.applied().isEmpty());assertEquals(1,fixture.nativeActionWrites());
            var projected=new AtomicInteger();var prepared=new AtomicInteger();
            var products=RootLifePublicStepProducts.bind(ignored->{},List.of(fixture.observationSource().sourceRef()),
                    (original,frame,known,same,input)->{prepared.incrementAndGet();throw new AssertionError("presentation cannot prepare");},
                    (actual,archive,same,input)->RootPublicStepExecution.legacyResult(actual,archive,same,input,(call,numeric)->{
                        projected.incrementAndGet();return RootLifeAdvancePublicResult.encode(numeric);
                    }));
            var input=caller("{\"step\":\"life-advance\"}");var product=selected(products,input);
            fixture.writer.locked(same->{
                var archive=fixture.archive.withSession(same);assertEquals(receipt,archive.loadReceipt(archive.receiptReferenceOf(receipt)));
                assertThrows(IOException.class,()->product.result().present(receipt,archive,same,input));
                assertThrows(IOException.class,()->product.result().present(receipt,archive,same,caller("{\"step\":\"life-advance-one-day\"}")));
                return null;
            });
            assertEquals(0,projected.get());assertEquals(0,prepared.get());
            assertEquals(receipt,fixture.coordinator.execute(command));assertEquals(1,fixture.nativeActionWrites());
        }
    }

    /** Existing actual Root CI must supply these admitted originals. This callback does not mint them. */
    static RawJson executeActualQualified(RootApplicationSession root,RootInstalledCatalog installed,
            PublicPlanningCodec.ExecuteRequest caller,Instant deadline)throws Exception {
        assertSame(root,installed.context().actions());assertTrue(org.xar.ck3.control.application.advance.LifeAdvanceComposite.accepts(caller.step().value()));
        var product=assertInstanceOf(RootPublicStepExecution.Action.class,installed.publicSteps().require(caller));
        assertEquals("original-life:"+caller.step().value(),product.id());
        RawJson result=RootPublicStepExecution.execute(root,installed,caller,deadline);
        var restored=RootLifeAdvancePublicResult.decode(result);
        assertEquals(result,RootLifeAdvancePublicResult.encode(restored));return result;
    }
}
