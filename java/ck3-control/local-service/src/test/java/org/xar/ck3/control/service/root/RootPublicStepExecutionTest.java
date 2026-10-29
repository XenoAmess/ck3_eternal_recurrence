package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/** Selection is DATA; no Root, Managed process, source qualification or private token is fabricated. */
final class RootPublicStepExecutionTest {
    @TempDir Path temp;
    private static PublicPlanningCodec.ExecuteRequest caller(String step) {
        return new PublicPlanningCodec.ExecuteRequest(new OperationKey(step),new PublicPlanningCodec.RevisionMissing(),new PublicPlanningCodec.FrameMissing());
    }
    @Test void allProductKindsRetainStableUniqueMetadataWithoutInvocation()throws Exception {
        var firstPath=java.nio.file.Files.write(temp.resolve("first.jar"),new byte[]{1});
        var secondPath=java.nio.file.Files.write(temp.resolve("second.jar"),new byte[]{2});
        var first=new org.xar.ck3.control.contracts.ExactRef(firstPath.toAbsolutePath().toString(),1,org.xar.ck3.control.application.action.ActionCodec.sha256(java.nio.file.Files.readAllBytes(firstPath)));
        var second=new org.xar.ck3.control.contracts.ExactRef(secondPath.toAbsolutePath().toString(),1,org.xar.ck3.control.application.action.ActionCodec.sha256(java.nio.file.Files.readAllBytes(secondPath)));
        java.util.function.Predicate<OperationKey> selector=step->false;
        RootPublicStepExecution.OwnerGuard owner=context->{throw new AssertionError("metadata cannot qualify a Root");};
        RootPublicStepExecution.ReadWork read=(p,f,k,s,c,a)->{throw new AssertionError("no read during construction");};
        RootPublicStepExecution.ActionPreparation prepare=(p,f,k,s,c)->{throw new AssertionError("no preparation during construction");};
        RootPublicStepExecution.ActionResult present=(r,a,s,c)->{throw new AssertionError("no result during construction");};
        RootPublicStepExecution.LifecycleWork lifecycle=(r,i,c,d)->{throw new AssertionError("no lifecycle during construction");};
        var input=new java.util.ArrayList<>(List.of(second,first,second,first));
        List<RootPublicStepExecution.Product> products=List.of(
                new RootPublicStepExecution.Read("read",selector,owner,read,input),
                new RootPublicStepExecution.Action("action",selector,owner,prepare,present,input),
                new RootPublicStepExecution.Lifecycle("lifecycle",selector,owner,lifecycle,input),
                new RootPublicStepExecution.OwnedAction("owned",selector,owner,lifecycle,input));
        input.clear();
        for(var product:products){
            assertEquals(List.of(second,first),product.sources());
            assertThrows(UnsupportedOperationException.class,()->product.sources().add(first));
        }
        var excess=java.util.Collections.nCopies(org.xar.ck3.control.application.history.DriverPublicExecuteFailureMaterial.MAX_PRODUCER_SOURCES+1,first);
        assertThrows(IllegalArgumentException.class,()->new RootPublicStepExecution.Read("r",selector,owner,read,excess));
        assertThrows(IllegalArgumentException.class,()->new RootPublicStepExecution.Action("a",selector,owner,prepare,present,excess));
        assertThrows(IllegalArgumentException.class,()->new RootPublicStepExecution.Lifecycle("l",selector,owner,lifecycle,excess));
        assertThrows(IllegalArgumentException.class,()->new RootPublicStepExecution.OwnedAction("o",selector,owner,lifecycle,excess));
    }
    @Test void realCollectorFrameAndPublicRequestSerdeFeedTheSingleActionIdentityRecipe()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(temp.resolve("writer"),false)) {
            var original=fixture.ready().request();var caller=caller("pause-map");
            String first=RootPublicStepExecution.actionId(original,caller);
            var restored=PublicPlanningCodec.decodeExecute(new PublicBindings.Value(PublicPlanningCodec.encodeExecute(caller)));
            assertEquals(first,RootPublicStepExecution.actionId(original,restored));
            assertNotEquals(first,RootPublicStepExecution.actionId(original,caller("resume-map")));
            var stale=new PublicPlanningCodec.ExecuteRequest(caller.step(),new PublicPlanningCodec.RevisionValue(
                    original.before().frame().revision().add(BigInteger.ONE)),caller.expectedH2743Frame());
            assertThrows(IllegalArgumentException.class,()->RootPublicStepExecution.actionId(original,stale));
            assertEquals(0,fixture.nativeActionWrites());
        }
    }
    @Test void selectionKeepsReadsSeparateFromActionsAndDoesNotInvokeAProducerOrGuard()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(temp.resolve("writer"),false)) {
            var refs=List.of(fixture.observationSource().sourceRef());var invoked=new AtomicInteger();
            RootPublicStepExecution.OwnerGuard guard=context->{invoked.incrementAndGet();throw new AssertionError("pure selection cannot qualify a Root");};
            var read=new RootPublicStepExecution.Read("test-source-read",step->step.value().equals("query-source-fixture"),guard,
                    (original,frame,known,same,caller,archive)->{invoked.incrementAndGet();throw new AssertionError("selection cannot read Native");},refs);
            var action=new RootPublicStepExecution.Action("test-source-action",step->step.value().equals("pause-map"),guard,
                    (original,frame,known,same,caller)->{invoked.incrementAndGet();throw new AssertionError("selection cannot prepare");},
                    (actual,archive,same,caller)->{invoked.incrementAndGet();throw new AssertionError("selection cannot present");},refs);
            assertSame(read,RootPublicStepExecution.select(List.of(read,action),caller("query-source-fixture")));
            assertSame(action,RootPublicStepExecution.select(List.of(read,action),caller("pause-map")));
            assertThrows(java.io.IOException.class,()->RootPublicStepExecution.select(List.of(action,action),caller("pause-map")));
            assertEquals(0,invoked.get());assertEquals(0,fixture.nativeActionWrites());assertEquals(0,fixture.nativeReadWrites());
        }
    }
    @Test void originalTypedFacadeDenialsAndUnsupportedGenericHireHaveTheStandardPublicFailureKind()throws Exception {
        for(String step:List.of("center-map-on-landed-title-v1","navigate-ingame-ui-v1","query-ingame-ui-window-v1",
                "hire-mercenary-v1","hire-holy-order-v1")) {
            var error=assertThrows(PublicServiceFailure.class,()->RootPublicStepExecution.select(List.of(),caller(step)));
            assertEquals(PublicServiceFailure.Kind.UNSUPPORTED_STEP,error.kind());assertTrue(error.originalCandidate().isEmpty());
        }
    }
    @Test void h2743CannotBeRoutedThroughAnActionEvenWithACompleteBeforeFrame()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(temp.resolve("writer"),false)) {
            var frame=new PublicPlanningCodec.H2743Frame("native:19",BigInteger.valueOf(19),BigInteger.valueOf(19),53217264,29829,
                    "native-29829-2bc2d599f7f9",16777231,BigInteger.ONE);
            var caller=new PublicPlanningCodec.ExecuteRequest(new OperationKey(PublicPlanningCodec.H2743_STEP),
                    new PublicPlanningCodec.RevisionValue(BigInteger.valueOf(19)),new PublicPlanningCodec.FrameValue(frame));
            var product=new RootPublicStepExecution.Action("wrong-h2743-action",step->step.equals(caller.step()),
                    context->{throw new AssertionError("no qualification during selection");},
                    (original,current,known,same,input)->{throw new AssertionError("no H2743 dispatch");},
                    (actual,archive,same,input)->{throw new AssertionError("no fake receipt result");},List.of(fixture.observationSource().sourceRef()));
            assertThrows(java.io.IOException.class,()->RootPublicStepExecution.select(List.of(product),caller));
            assertEquals(0,fixture.nativeActionWrites());
        }
    }
}
