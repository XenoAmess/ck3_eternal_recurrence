package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.routecontact.RouteContactSteps;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/** Real public codec and canonical software UNKNOWN, without inventing a Root, native clock
 * admission or full Route proof. The actual Root hook below requires qualified external inputs. */
final class RootRouteContactAdvancePublicProductsTest {
    private static final String HORIZON="advance-route-contact-horizon-v1-10-to-90-h-2-20-30";
    private static final String WINDOW="advance-route-contact-window-v1-10-to-90-days-3-h-2-20-30";
    @TempDir Path temporary;
    private static RawJson raw(String value){return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
    private static PublicPlanningCodec.ExecuteRequest caller(String value){
        return PublicPlanningCodec.decodeExecute(PublicBindings.present(raw(value)));
    }
    private static PublicPlanningCodec.ExecuteRequest caller(String step,String revision){
        return caller("{\"step\":\""+step+"\""+revision+"}");
    }
    private static RootPublicStepExecution.Action selected(List<RootPublicStepExecution.Product> products,
            PublicPlanningCodec.ExecuteRequest caller)throws IOException {
        return assertInstanceOf(RootPublicStepExecution.Action.class,RootPublicStepExecution.select(products,caller));
    }

    @Test void owningLiteralProducerPassesActualExecuteSerdeAndSelectsExactlyOneFamily()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("route-wire"),false)){
            var calls=new AtomicInteger();
            var products=RootRouteContactAdvancePublicProducts.bind(ignored->{calls.incrementAndGet();throw new AssertionError("selection grants no owner");},
                    List.of(fixture.observationSource().sourceRef()),
                    (request,frame,known,same,input)->{calls.incrementAndGet();throw new AssertionError("selection must not prepare");},
                    (actual,archive,same,input)->{calls.incrementAndGet();throw new AssertionError("selection creates no result");});
            for(int days:List.of(1,2,3)){
                var typed=new RouteContactSteps.Request(10,90,List.of(20,30),days);
                var step=RouteContactSteps.format(typed,days==1?RouteContactSteps.HORIZON:RouteContactSteps.WINDOW);
                var input=caller(step,",\"expected_revision\":\"18446744073709551615\"");
                var restored=PublicPlanningCodec.decodeExecute(PublicBindings.present(PublicPlanningCodec.encodeExecute(input)));
                assertEquals(input,restored);
                assertEquals(1,products.stream().filter(value->value.matches(restored.step())).count());
                assertEquals(days==1?"original-route-contact-horizon":"original-route-contact-window",selected(products,restored).id());
                var operation=new RootRouteContactAdvanceRuntime.Operation(restored.step());
                assertEquals(List.of("operation"),operation.arguments().members().keySet().stream().sorted().toList());
                assertEquals(step,org.xar.ck3.control.planning.opportunity.OpportunityJson.text(operation.arguments().get("operation"),"operation"));
                assertEquals(typed,RouteContactSteps.parse(restored.step().value()));
            }
            for(String other:List.of("life-advance","life-advance-one-day","battle-sentinel-advance","pause-map",
                    "advance-route-contact-horizon-v1-010-to-90-h-2-20-30",
                    "advance-route-contact-horizon-v1-10-to-90-h-2-30-20",
                    "advance-route-contact-horizon-v1-10-to-90-h-1-20-30",
                    "advance-route-contact-window-v1-10-to-90-days-1-h-2-20-30",
                    "advance-route-contact-window-v1-10-to-90-days-4-h-2-20-30")){
                var failure=assertThrows(PublicServiceFailure.class,()->RootPublicStepExecution.select(products,caller(other,"")));
                assertEquals(PublicServiceFailure.Kind.UNSUPPORTED_STEP,failure.kind());
            }
            assertEquals(0,calls.get());assertEquals(0,fixture.nativeActionWrites());assertEquals(0,fixture.nativeReadWrites());
        }
    }

    @Test void horizonRequiresOriginalRevisionAndStaleVersionsRefuseBeforeProofOrClockPreparation()throws Exception {
        var calls=new AtomicInteger();
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("route-stale"),false)){
            var products=RootRouteContactAdvancePublicProducts.bind(ignored->{},List.of(fixture.observationSource().sourceRef()),
                    (request,frame,known,same,input)->{calls.incrementAndGet();throw new IOException("actual proof producer reached");},
                    (actual,archive,same,input)->{throw new AssertionError("no actual completion");});
            var request=fixture.ready().request();
            for(String revision:List.of("",",\"expected_revision\":null")){
                var input=caller(HORIZON,revision);
                assertEquals(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,assertThrows(PublicServiceFailure.class,
                        ()->selected(products,input).preparation().prepare(request,null,null,null,input)).kind());
            }
            var drift=caller(HORIZON,",\"expected_revision\":\""+request.before().frame().revision().add(BigInteger.ONE)+"\"");
            assertEquals(PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,assertThrows(PublicServiceFailure.class,
                    ()->selected(products,drift).preparation().prepare(request,null,null,null,drift)).kind());
            assertEquals(0,calls.get());
            var current=caller(HORIZON,",\"expected_revision\":\""+request.before().frame().revision()+"\"");
            assertEquals("actual proof producer reached",assertThrows(IOException.class,
                    ()->selected(products,current).preparation().prepare(request,null,null,null,current)).getMessage());
            assertEquals(1,calls.get());
            // Original window entry permits missing/null revision; that is not proof or action qualification.
            for(String revision:List.of("",",\"expected_revision\":null")){
                var input=caller(WINDOW,revision);RootRouteContactAdvancePublicProducts.requireCaller(input);
            }
            assertEquals(0,fixture.nativeActionWrites());assertEquals(0,fixture.nativeReadWrites());
        }
    }

    @Test void clientCannotSupplyAProofClockPlanOrUnsafeNumericRevision() {
        for(String revision:List.of("true","1.0","-1","9007199254740992","\"01\"","\"18446744073709551616\"")){
            assertThrows(IllegalArgumentException.class,()->caller(HORIZON,",\"expected_revision\":"+revision));
        }
        for(String field:List.of("plan","advance_v1","route_window_proof","proof_kind","requested_horizon_days","timeline_speed"))
            assertThrows(IllegalArgumentException.class,()->caller(HORIZON,",\""+field+"\":{}"));
        assertThrows(IllegalArgumentException.class,()->caller("{\"step\":\""+HORIZON+"\",\"expected_revision\":1,\"expected_revision\":2}"));
    }

    @Test void actualCanonicalUnknownCannotBecomeAnOriginalRouteReturnOrASecondSubmission()throws Exception {
        var operation=new OperationKey(HORIZON);
        var scenario=new ActionWriterIntegrationFixture.SoftwareActionScenario(operation,"software.route-negative",
                (command,attempt,dispatch)->new ActionPorts.Pending("no original Route clock completion",
                        List.of(attempt.guard().nativeEvidence())),()->{});
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("route-unknown"),true,scenario)){
            // This real canonical primitive is deliberately not a qualified Route composite.
            // It proves retention and the public absence path, never a successful native route day.
            var command=fixture.command("route-original-unknown");var receipt=fixture.coordinator.execute(command);
            assertEquals(ActionReceipt.Outcome.UNRESOLVED,receipt.outcome());assertFalse(receipt.settled());
            var preparation=new AtomicInteger();var projection=new AtomicInteger();
            var products=RootRouteContactAdvancePublicProducts.bind(ignored->{},List.of(fixture.observationSource().sourceRef()),
                    (request,frame,known,same,input)->{preparation.incrementAndGet();throw new AssertionError("presentation cannot prepare");},
                    (actual,archive,same,input)->RootPublicStepExecution.legacyResult(actual,archive,same,input,(call,numeric)->{
                        projection.incrementAndGet();return RootRouteContactAdvanceResult.encode(numeric,call.step());
                    }));
            var input=caller(HORIZON,",\"expected_revision\":\""+command.before().frame().revision()+"\"");
            fixture.writer.locked(same->{
                var archive=fixture.archive.withSession(same);
                assertEquals(receipt,archive.loadReceipt(archive.receiptReferenceOf(receipt)));
                assertThrows(IOException.class,()->selected(products,input).result().present(receipt,archive,same,input));
                return null;
            });
            assertEquals(receipt,fixture.coordinator.execute(command));assertEquals(1,fixture.nativeActionWrites());
            assertEquals(0,projection.get());assertEquals(0,preparation.get());
        }
    }

    /** Actual Root CI supplies its admitted catalog and original history/clock inputs. No software
     * source or pure test is promoted to this qualification; absent originals mean NOT_RUN. */
    static RawJson executeActualQualified(RootApplicationSession root,RootInstalledCatalog actual,
            PublicPlanningCodec.ExecuteRequest caller,Instant deadline)throws Exception {
        assertSame(root,actual.context().actions());actual.remainingDomains().routeAdvance().requireContext(actual.context());
        var selected=assertInstanceOf(RootPublicStepExecution.Action.class,actual.publicSteps().require(caller));
        assertTrue(selected.matches(caller.step()));RootRouteContactAdvancePublicProducts.requireCaller(caller);
        var result=RootPublicStepExecution.execute(root,actual,caller,deadline);
        var numeric=RootRouteContactAdvanceResult.decode(result,caller.step());
        assertEquals(result,RootRouteContactAdvanceResult.encode(numeric,caller.step()));return result;
    }

    /** A genuinely fresh admitted Root must supply an as-yet unissued original literal. This is
     * the cold descriptor-to-current-proof case, not a warm-cache or software-Ready substitute. */
    static RawJson executeColdActualQualified(RootApplicationSession root,RootInstalledCatalog actual,
            PublicPlanningCodec.ExecuteRequest caller,Instant deadline)throws Exception {
        var operation=caller.step();var route=actual.remainingDomains().routeAdvance();route.requireContext(actual.context());
        assertTrue(actual.bindings().actualArchivedVerifier(operation).isEmpty(),"fixture must supply a truly cold original Route operation");
        var descriptor=actual.bindings().resolve(operation,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP).orElseThrow();
        assertEquals(ExecutableStepBindings.Kind.COMPOSITE,descriptor.kind());
        assertSame(route.installation().compositeFamilies().getFirst(),actual.bindings().actualCompositeFamily(operation).orElseThrow());
        assertEquals(route.sources().archivedVerifier(),actual.bindings().actualArchivedVerifier(operation).orElseThrow().definitionSource());
        ActionCommand prepared=root.withPublicPlanning(deadline,(observation,same)->{
            var ready=assertInstanceOf(org.xar.ck3.control.application.readiness.NativeReadinessCollector.PublicReady.class,observation);
            var request=RootPlanningInputsFactory.publicRequest(ready,same,deadline);
            var frame=ready.lease().frame();var known=ready.lease().driver();
            assertTrue(request.observations().actionSteps().contains(operation),"the actual fresh advertisement must include its resolved Route proof");
            RootRouteContactAdvancePublicProducts.requireCurrent(request,caller);
            var command=route.prepare(request,frame,known,same,operation,RootPublicStepExecution.actionId(request,caller));
            RootRouteContactAdvancePublicProducts.requirePrepared(request,caller,command);return command;
        });
        RawJson result=executeActualQualified(root,actual,caller,deadline);
        actual.context().withSession(same->{
            var stored=actual.context().core().journal().locked(same,locked->locked.find(prepared.actionId())).orElseThrow();
            assertEquals(prepared,stored.command());
            assertEquals(ActionCodec.bodySha256(prepared),stored.bodySha256());return null;
        });
        return result;
    }
}

