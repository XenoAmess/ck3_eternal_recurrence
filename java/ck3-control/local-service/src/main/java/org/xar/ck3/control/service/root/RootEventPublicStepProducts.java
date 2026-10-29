package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.math.BigInteger;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.effects.NativeEventEffects;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.events.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.events.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/** Original EXECUTE event branches over the identical installed Root event owner.
 * Products return DATA or an owner-prepared command; the sole Root dispatcher submits outside its held read scope. */
public final class RootEventPublicStepProducts {
    private RootEventPublicStepProducts(){ }

    public static List<RootPublicStepExecution.Product> install(RootInstalledCatalog actual)throws IOException {
        Objects.requireNonNull(actual);RootRuntimeContext context=actual.context();
        EventRuntimeInstaller events=actual.remainingDomains().events();
        var selected=actual.definitions().remainingDomains().eventsPrepared().sources();
        ReadContract<EventPolicies.ReadPublication> window=events.eventWindowContract();
        var closure=new LinkedHashSet<ExactRef>();
        closure.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootEventPublicStepProducts.class));
        closure.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,EventOptionPublicResponse.class));
        closure.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,PublicServiceFailure.class));
        closure.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.APPLICATION,PublicEventSelection.class));
        closure.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.APPLICATION,NativeEventPostconditionPort.class));
        ExactRef publicService=selected.windowService();
        closure.add(publicService);
        closure.add(actual.publicStepSource(RootRuntimeSelectedSources.Module.CONTRACTS,PublicUnsigned64.class));
        closure.addAll(List.of(selected.installer(),selected.windowRead(),selected.windowDecoder(),selected.windowService(),
                selected.policies(),selected.registeredCore(),selected.nativeEffects(),selected.nativeEffectsDecoder(),selected.actionPreparation()));
        List<ExactRef> sources=List.copyOf(closure);
        RootPublicStepExecution.OwnerGuard owner=identical->{
            StrictJson.require(identical==context&&actual.context()==context&&actual.remainingDomains()==context.remainingDomains()
                    &&actual.remainingDomains().events()==events&&events.eventWindowContract()==window,
                    "event EXECUTE products lost their identical installed Root/event/window owner");
            actual.remainingDomains().requireContext(identical);
            StrictJson.require(context.readCatalog().containsIdentity(window),"event EXECUTE window is absent from the installed read catalog");
        };
        var read=new RootPublicStepExecution.Read("original-current-event-window-v1",RootEventPublicStepProducts::selectsRead,owner,
                (original,frame,known,same,caller,archive)->{
                    context.writer().requireSession(same);requireHeld(original,frame,known);context.requireCurrent(original.deadline());
                    return readOriginal(context.reads(),window,original,caller,archive);
                },sources,RootPublicStepExecution.ReadValidation.OWNER_ORDERED);
        var action=new RootPublicStepExecution.Action("original-event-option-v1",RootEventPublicStepProducts::selectsOption,owner,
                (original,frame,known,same,caller)->{
                    context.writer().requireSession(same);requireHeld(original,frame,known);
                    EventActionPreparation.OptionNumber option=EventActionPreparation.option(caller.step());
                    int instance=optionFrame(original,window,caller,option);
                    // Existing actual owner reads the same original window, validates its exact displayed row,
                    // retains source/material/expected proof, and runs the installed typed native preparer.
                    ActionCommand command=events.preparePublicSelection(original,option.value(),Optional.of(instance));
                    StrictJson.require(command.operation().equals(caller.step()),"event EXECUTE owner changed the exact original step");
                    EventActionPreparation.prepare(command);return command;
                },(receipt,archive,same,caller)->{
                    context.writer().requireSession(same);
                    StrictJson.require(receipt.command().operation().equals(caller.step()),"event EXECUTE result crossed its original step");
                    return presentOriginal(receipt,archive,events.publicSelectionResult(receipt));
                },sources,RootPublicStepExecution.ActionValidation.OWNER_ORDERED);
        return List.of(read,action);
    }

    /** Shared canonical native operation parser. Unrelated interaction/notification steps are never selected. */
    static boolean selectsOption(OperationKey step){
        Objects.requireNonNull(step);try{EventActionPreparation.option(step);return true;}
        catch(IllegalArgumentException unavailable){return false;}
    }
    static boolean selectsRead(OperationKey step){return EventWindowRead.STEP.equals(Objects.requireNonNull(step).value());}

    /** Actual typed READ producer used inside Root's original held Complete/Known/writer callback. */
    static RawJson readOriginal(PlanningReadPort reads,ReadContract<EventPolicies.ReadPublication> window,
            PlanningRequest original,PublicPlanningCodec.ExecuteRequest caller,ActionPorts.OutcomeArchive archive){
        Objects.requireNonNull(reads);Objects.requireNonNull(window);Objects.requireNonNull(original);Objects.requireNonNull(caller);Objects.requireNonNull(archive);
        StrictJson.require(selectsRead(caller.step())&&window.operation().equals(caller.step()),"exact installed event READ required");
        if(!original.observations().bridgeCapabilities().contains(EventWindowRead.CAPABILITY))
            throw new PublicServiceFailure(PublicServiceFailure.Kind.UNSUPPORTED_STEP,"native DLL cannot query the current event window",Optional.empty());
        PlanningReadRequest request=windowRequest(original,window);activeEvent(request);requireRevision(original,caller);
        PlanningReadResult<EventPolicies.ReadPublication> received=reads.read(window,request);
        if(!(received instanceof PlanningReadResult.Known<EventPolicies.ReadPublication> known))
            return EventWindowService.encode(new EventWindowService.Response(received));
        StrictJson.require(known.receipt().request().equals(request)&&known.receipt().contractId().equals(window.contractId())
                &&archive.readReferenceOf(known.receipt()).equals(known.originalReceipt()),"event EXECUTE READ changed its exact original request/receipt");
        NativeRecordedEvidenceVerifier.requireRead(known.receipt(),archive);
        EventPolicies.ReadPublication decoded=window.decode(known.receipt());
        StrictJson.require(decoded.equals(known.value()),"event EXECUTE READ differs from the installed original decoder");
        return EventWindowService.encode(new EventWindowService.Response(new PlanningReadResult.Known<>(decoded,known.receipt(),known.originalReceipt())));
    }
    static RawJson presentOriginal(ActionReceipt actual,ActionPorts.OutcomeArchive archive,Optional<RawJson> verified){
        StrictJson.require(selectsOption(actual.command().operation())&&NativeEventEffects.supports(actual.command().operation()),
                "event EXECUTE cannot present an interaction or unrelated action");
        return EventOptionPublicResponse.capture(actual,archive,verified).original();
    }
    /** Original cheap pre-dispatch checks precede the caller revision; this performs no native read. */
    static int optionFrame(PlanningRequest original,ReadContract<EventPolicies.ReadPublication> window,
            PublicPlanningCodec.ExecuteRequest caller,EventActionPreparation.OptionNumber option){
        var snapshot=original.observations().snapshot();
        if(!new OpportunityJson.Bool(true).equals(snapshot.get("map_ready")))
            throw fault(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,"native event selection requires a map-ready snapshot");
        if(!new OpportunityJson.Bool(true).equals(snapshot.get("paused")))
            throw fault(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,"native event selection requires a paused snapshot");
        int instance=activeEvent(windowRequest(original,window));
        var event=OpportunityJson.object(snapshot.get("active_event"),"actual native event");
        if(!(event.get("option_count") instanceof OpportunityJson.IntegerValue count)
                ||count.value().signum()<=0||BigInteger.valueOf(option.value()).compareTo(count.value())>0)
            throw fault(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,"selected native event option is outside the active event");
        requireRevision(original,caller);return instance;
    }
    private static int activeEvent(PlanningReadRequest original){
        try{return EventWindowRead.activeEvent(original);}
        catch(IllegalArgumentException invalid){
            var failure=fault(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,"CK3 has no positive full active event ID");failure.initCause(invalid);throw failure;
        }
    }
    private static void requireRevision(PlanningRequest original,PublicPlanningCodec.ExecuteRequest caller){
        if(caller.expectedRevision() instanceof PublicPlanningCodec.RevisionValue value
                &&!value.value().equals(original.before().frame().revision()))
            throw fault(PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,"event execute revision mismatch: expected "+value.value()+", current "+original.before().frame().revision());
        caller.requireCurrent(original);
    }
    private static PublicServiceFailure fault(PublicServiceFailure.Kind kind,String message){return new PublicServiceFailure(kind,message,Optional.empty());}
    private static PlanningReadRequest windowRequest(PlanningRequest original,ReadContract<EventPolicies.ReadPublication> window){
        return new PlanningReadRequest(original.before(),original.source(),original.sessionId(),window.operation(),original.observations().snapshot(),original.deadline());
    }
    private static void requireHeld(PlanningRequest original,Complete frame,Known known){
        Objects.requireNonNull(original);Objects.requireNonNull(frame);Objects.requireNonNull(known);
        StrictJson.require(original.before().equals(frame.identity())&&original.source().equals(frame.source())&&original.sessionId().equals(frame.sessionId())
                &&known.stamp().game().equals(frame.identity().game())&&known.driver().session().actorId().equals(frame.identity().frame().identity().player())
                &&known.driver().session().episodeRunId().equals(frame.identity().frame().episodeRunId()),
                "event EXECUTE must retain its actual held Complete/Known/player/episode frame");
    }
}
