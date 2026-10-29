package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.routecontact.RouteContactSteps;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;
import org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module;

/** The two original Route Contact EXECUTE families. A selector parses the original literal only;
 * its owning runtime derives canonical fresh proofs and uses the same installed clock/coordinator. */
public final class RootRouteContactAdvancePublicProducts {
    private RootRouteContactAdvancePublicProducts() { }

    public static List<RootPublicStepExecution.Product> install(RootInstalledCatalog actual)throws IOException {
        Objects.requireNonNull(actual);
        var context=actual.context();var route=actual.remainingDomains().routeAdvance();
        route.requireContext(context);
        var sources=new LinkedHashSet<ExactRef>(route.requiredSources());
        for(Class<?> type:List.of(RootRouteContactAdvanceRuntime.class,RootRouteContactAdvancePublicProducts.class,
                RootRouteContactAdvanceResult.class,RootPublicStepExecution.class,RootPublicStepFailureOriginals.class,
                RootLifeAdvancePublicResult.class,RootBattleAdvancePublicResult.class))
            sources.add(actual.publicStepSource(Module.LOCAL_SERVICE,type));
        sources.add(actual.publicStepSource(Module.APPLICATION,RouteContactSteps.class));
        RootPublicStepExecution.OwnerGuard owner=same->{
            if(same!=context||actual.context()!=context||actual.remainingDomains().routeAdvance()!=route)
                throw new IOException("Route EXECUTE lost its identical installed Root and domain owner");
            route.requireContext(same);
        };
        return bind(owner,List.copyOf(sources),(request,frame,known,same,caller)->{
            context.writer().requireSession(same);owner.requireContext(context);
            var prepared=route.prepare(request,frame,known,same,caller.step(),RootPublicStepExecution.actionId(request,caller));
            requirePrepared(request,caller,prepared);return prepared;
        },(receipt,archive,same,caller)->{
            context.writer().requireSession(same);owner.requireContext(context);requireCaller(caller);
            var partial=route.failure(receipt,archive,same);
            if(partial.isPresent()) {
                var original=partial.orElseThrow();
                PublicServiceFailure.Kind kind=switch(original.kind()) {
                    case STEP_POSTCONDITION_ERROR -> PublicServiceFailure.Kind.STEP_POSTCONDITION_ERROR;
                };
                var failure=new PublicServiceFailure(kind,original.message(),Optional.of(original.domainEvidence()));
                org.xar.ck3.control.application.action.RawJson exposed;
                try {exposed=RootRouteContactAdvanceResult.encode(original.numericPartial(),caller.step());}
                catch(RuntimeException formatterFailure) {
                    // An unavailable Service representation cannot invent a false Driver row.
                    // The real original failure and partial archive remain, with no new submission.
                    failure.addSuppressed(formatterFailure);throw failure;
                }
                throw RootPublicStepFailureOriginals.recordActionDriverFailure(receipt,archive,same,caller,failure,
                        Optional.of(original.numericPartial()),Optional.of(exposed));
            }
            return RootPublicStepExecution.legacyResult(receipt,archive,same,caller,(originalCall,numeric)->{
                var owning=route.original(receipt,archive,same);
                StrictJson.require(DriverJson.object(owning.bytes(),org.xar.ck3.control.application.action.RawJson.MAXIMUM_BYTES)
                        .equals(DriverJson.object(numeric.bytes(),org.xar.ck3.control.application.action.RawJson.MAXIMUM_BYTES)),
                        "Route public result differs from its actual owning archive replay");
                return RootRouteContactAdvanceResult.encode(numeric,caller.step());
            });
        });
    }

    /** Typed wire adapter only. Tests may exercise the common selector/serde seam through these
     * callbacks, but no callback can mint a Root, Ready, native proof, permit or canonical result. */
    static List<RootPublicStepExecution.Product> bind(RootPublicStepExecution.OwnerGuard owner,List<ExactRef> sources,
            RootPublicStepExecution.ActionPreparation preparation,RootPublicStepExecution.ActionResult result) {
        Objects.requireNonNull(owner);Objects.requireNonNull(preparation);Objects.requireNonNull(result);sources=List.copyOf(sources);
        var products=new ArrayList<RootPublicStepExecution.Product>();
        for(boolean window:List.of(false,true))
            products.add(new RootPublicStepExecution.Action(window?"original-route-contact-window":"original-route-contact-horizon",
                    operation->matches(operation,window),owner,(request,frame,known,same,caller)->{
                        try {
                            requireCaller(caller);StrictJson.require(matches(caller.step(),window),"Route EXECUTE crossed its parsed family");
                            requireCurrent(request,caller);
                            var command=Objects.requireNonNull(preparation.prepare(request,frame,known,same,caller));
                            requirePrepared(request,caller,command);return command;
                        }catch(PublicServiceFailure actualDriverFailure){
                            if(!RootPublicStepFailureOriginals.inGenericDriverCall(caller))throw actualDriverFailure;
                            throw RootPublicStepFailureOriginals.recordDriverFailure(request,frame,known,same,caller,
                                    actualDriverFailure,Optional.empty(),Optional.empty());
                        }
                    },(receipt,archive,same,caller)->{
                        requireCaller(caller);StrictJson.require(matches(caller.step(),window)
                                &&receipt.command().operation().equals(caller.step()),"Route result crossed the actual caller operation");
                        return Objects.requireNonNull(result.present(receipt,archive,same,caller));
                    },sources,RootPublicStepExecution.ActionValidation.OWNER_ORDERED));
        return List.copyOf(products);
    }
    static boolean matches(OperationKey operation,boolean window) {
        try {return (RouteContactSteps.parse(Objects.requireNonNull(operation).value()).days()>1)==window;}
        catch(IllegalArgumentException malformed){return false;}
    }
    static void requireCaller(PublicPlanningCodec.ExecuteRequest caller)throws IOException {
        Objects.requireNonNull(caller);var parsed=RouteContactSteps.parse(caller.step().value());
        if(caller.h2743()||caller.expectedH2743Frame() instanceof PublicPlanningCodec.FrameValue)
            throw new IOException("Route EXECUTE does not accept a foreign H2743 before-frame claim");
        if(parsed.days()==1&&!(caller.expectedRevision() instanceof PublicPlanningCodec.RevisionValue))
            throw new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,
                    "route-contact one-day advance requires expected_revision",Optional.empty());
    }
    static void requireCurrent(PlanningRequest request,PublicPlanningCodec.ExecuteRequest caller)throws IOException {
        requireCaller(caller);
        if(caller.expectedRevision() instanceof PublicPlanningCodec.RevisionValue revision
                &&!revision.value().equals(request.before().frame().revision())) {
            boolean window=RouteContactSteps.parse(caller.step().value()).days()>1;
            throw new PublicServiceFailure(PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,
                    window?"route window starting revision changed":"route-contact one-day advance revision mismatch: expected "
                            +revision.value()+", current "+request.before().frame().revision(),Optional.empty());
        }
        caller.requireCurrent(request);
    }
    static void requirePrepared(PlanningRequest request,PublicPlanningCodec.ExecuteRequest caller,ActionCommand actual) {
        var parsed=RouteContactSteps.parse(caller.step().value());
        StrictJson.require(actual.actionId().equals(RootPublicStepExecution.actionId(request,caller))
                &&actual.before().equals(request.before())&&actual.source().equals(request.source())
                &&actual.sessionId().equals(request.sessionId())&&actual.operation().equals(caller.step())
                &&actual.deadline().equals(request.deadline())
                &&actual.arguments().equals(new RootRouteContactAdvanceRuntime.Operation(caller.step()).arguments())
                &&parsed.days()>=1&&parsed.days()<=3,
                "Route public preparation changed caller identity, parsed arguments, source, frame or deadline");
    }
}

