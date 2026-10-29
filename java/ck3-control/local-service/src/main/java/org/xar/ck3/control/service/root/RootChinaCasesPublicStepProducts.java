package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesFacade;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesCodec.Family;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesService;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesContract.Method;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;
import org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module;

/** Original generic EXECUTE READs use the identical installed Cases contracts and sole decoder.
 * Dedicated MCP payloads and canonical action receipts are not substituted for the driver result. */
public final class RootChinaCasesPublicStepProducts {
    private RootChinaCasesPublicStepProducts() { }

    public static List<RootPublicStepExecution.Product> install(RootInstalledCatalog actual)throws IOException {
        Objects.requireNonNull(actual);
        RootRuntimeContext context=actual.context();
        RootChinaCasesPublicProducts.Installed installed=actual.additionalDomains().chinaCases();
        RootChinaCasesPublicProducts.Prepared prepared=actual.definitions().additionalDomains().chinaCases();
        StrictJson.require(installed.context()==context,"Cases step products require the identical installed Root context");
        var originals=prepared.sources();
        List<ExactRef> sources=List.of(originals.facade(),originals.originalDecoder(),originals.publicContract(),
                originals.publicCodec(),originals.publicService(),originals.rootProduct(),
                actual.publicStepSource(Module.LOCAL_SERVICE,RootChinaCasesPublicStepProducts.class),
                actual.publicStepSource(Module.LOCAL_SERVICE,PublicServiceFailure.class));
        List<Method> methods=Arrays.stream(Method.values()).filter(Method::readOnly).toList();
        StrictJson.require(methods.size()==10,"exact ten original Cases READ methods required");
        var products=new ArrayList<RootPublicStepExecution.Product>();
        for(Method method:methods) {
            // Obtain the actual object from this facade. A matching name cannot create another contract.
            ReadContract<?> contract=contract(installed,method);
            products.add(new RootPublicStepExecution.Read("china-cases-execute/"+method.family().step(),
                    step->matches(method,step),
                    same->requireInstalled(actual,installed,prepared,same),
                    (original,frame,known,same,caller,archive)->
                            read(actual,installed,prepared,method,contract,original,frame,known,same,caller,archive),
                    sources));
        }
        return List.copyOf(products);
    }

    static boolean matches(Method method,OperationKey encoded) {
        Objects.requireNonNull(method);Objects.requireNonNull(encoded);
        return method.readOnly()&&ChinaCasesCodec.executionMethod(encoded).filter(method::equals).isPresent();
    }
    private static ReadContract<?> contract(RootChinaCasesPublicProducts.Installed installed,Method method)throws IOException {
        var operation=new OperationKey(method.family().step());
        List<ReadContract<?>> matches=installed.service().originalFacade().readContracts().stream()
                .filter(candidate->candidate.operation().equals(operation)).toList();
        if(matches.size()!=1)throw new IOException("Cases step lacks its unique identical original READ contract: "+operation.value());
        ReadContract<?> original=matches.getFirst();
        if(installed.installation().reads().stream().noneMatch(selected->selected.contract()==original))
            throw new IOException("Cases step contract is absent from the actual installed business inventory");
        return original;
    }
    private static void requireInstalled(RootInstalledCatalog actual,RootChinaCasesPublicProducts.Installed installed,
            RootChinaCasesPublicProducts.Prepared prepared,RootRuntimeContext same)throws IOException {
        if(actual.context()!=same||installed.context()!=same||actual.additionalDomains().chinaCases()!=installed
                ||actual.definitions().additionalDomains().chinaCases()!=prepared)
            throw new IOException("Cases step crossed its actual installed product, Prepared or Root context");
    }

    private static <T>RawJson read(RootInstalledCatalog actual,RootChinaCasesPublicProducts.Installed installed,
            RootChinaCasesPublicProducts.Prepared prepared,Method method,ReadContract<T> contract,
            PlanningRequest original,Complete frame,Known known,Session same,
            PublicPlanningCodec.ExecuteRequest caller,OutcomeArchive archive)throws IOException {
        RootRuntimeContext context=actual.context();
        requireInstalled(actual,installed,prepared,context);
        caller.requireCurrent(original);
        if(!matches(method,caller.step()))throw new IOException("Cases READ differs from the caller's original encoded step");
        requireScope(context,original,frame,known,same);
        PlanningReadRequest requested=new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),
                new OperationKey(method.family().step()),
                ChinaCasesCodec.executionArguments(caller.step(),frame.connectionGeneration()),original.deadline());
        PlanningReadResult<T> result=context.reads().read(same,contract,requested);
        if(!(result instanceof PlanningReadResult.Known<T> observed)) {
            var unavailable=(PlanningReadResult.Unavailable<T>)result;
            Optional<PublicServiceFailure> originalFailure=originalDriverFailure(unavailable,
                    installed.service().originalFacade(),contract,requested);
            if(originalFailure.isPresent())throw originalFailure.orElseThrow();
            throw new IOException("actual original Cases EXECUTE READ unavailable: "+unavailable.reason());
        }
        RootChinaCasesPublicProducts.verifyKnown(frame,requested,observed,archive,context.frameLoader());
        for(var guard:List.of(observed.receipt().before(),observed.receipt().after()))
            if(!Arrays.equals(context.transport().originalHello().packet().value(),
                    archive.readOriginalPacket(guard.binding().capabilityEvidence())))
                throw new IOException("Cases EXECUTE original HELLO differs from the held source");
        if(!Objects.equals(contract.replay(observed.receipt()),observed.value()))
            throw new IOException("Cases EXECUTE value differs from the actual retained contract replay");
        RawJson publicResult=present(method,caller.step(),observed.receipt());
        // The sole publisher requires this identical installed projection contract and actual Known.
        // It performs the original encoded-command/numeric-report relation; no leaf history writer exists.
        actual.readHistory().enqueueRich(contract,observed,List.of(observed));
        requireScope(context,original,frame,known,same);
        requireInstalled(actual,installed,prepared,context);
        return publicResult;
    }

    /** Only a live decoder's exact source-owned finite failure can enter original Driver history.
     * An Unavailable reason or another domain's marker never supplies an original error class. */
    static Optional<PublicServiceFailure> originalDriverFailure(PlanningReadResult.Unavailable<?> unavailable,
            ChinaCasesFacade producer,ReadContract<?> contract,PlanningReadRequest request) {
        Objects.requireNonNull(unavailable);
        if(!(unavailable.decodeFailure().orElse(null) instanceof ChinaCasesFacade.OriginalDriverFailure actual))
            return Optional.empty();
        actual.requireProducer(producer,contract,request);
        return Optional.of(mapOriginalDriverFailure(actual));
    }
    /** The direct MCP path retains the same original native cause through its own service outcome. */
    static Optional<PublicServiceFailure> originalDirectDriverFailure(ChinaCasesService.Unavailable unavailable,
            ChinaCasesFacade producer,Family family,ChinaCasesFacade.Context context) {
        Objects.requireNonNull(unavailable);
        if(!(unavailable.decodeFailure().orElse(null) instanceof ChinaCasesFacade.OriginalDriverFailure actual))
            return Optional.empty();
        Objects.requireNonNull(producer).requireDirectOriginalFailure(actual,family,context);
        return Optional.of(mapOriginalDriverFailure(actual));
    }
    private static PublicServiceFailure mapOriginalDriverFailure(ChinaCasesFacade.OriginalDriverFailure actual) {
        var kind=switch(actual.kind()) {
            case B1_MALFORMED_ENVELOPE,B1_QUERY_SEQUENCE_MISSING,CASE_MALFORMED_ENVELOPE,CASE_QUERY_SEQUENCE_MISSING,AIOWNED_MALFORMED_ENVELOPE,AIOWNED_QUERY_SEQUENCE_MISSING,RESULT_MALFORMED_ENVELOPE,RESULT_QUERY_SEQUENCE_MISSING,PIP_MALFORMED_ENVELOPE,PIP_QUERY_SEQUENCE_MISSING,PROMOTION_MALFORMED_ENVELOPE,PROMOTION_QUERY_SEQUENCE_MISSING,AF5_MALFORMED_ENVELOPE,AF5_QUERY_SEQUENCE_MISSING,PROJECTS_MALFORMED_ENVELOPE,PROJECTS_QUERY_SEQUENCE_MISSING,INCIDENT_MALFORMED_ENVELOPE,INCIDENT_QUERY_SEQUENCE_MISSING,SCOREBOARD_MALFORMED_ENVELOPE,SCOREBOARD_QUERY_SEQUENCE_MISSING,B1_NORMALIZER_REJECTED,CASE_NORMALIZER_REJECTED,AIOWNED_NORMALIZER_REJECTED,RESULT_NORMALIZER_REJECTED,PIP_NORMALIZER_REJECTED,PROMOTION_NORMALIZER_REJECTED,AF5_NORMALIZER_REJECTED,PROJECTS_NORMALIZER_REJECTED,INCIDENT_NORMALIZER_REJECTED,SCOREBOARD_NORMALIZER_REJECTED->PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE;
        };
        StrictJson.require(kind.pythonClassName().equals(actual.originalErrorClass()),"actual original Cases fault class changed");
        // The process-local cause is never encoded or treated as a persisted failure candidate.
        var mapped=new PublicServiceFailure(kind,actual.originalMessage(),Optional.empty());
        mapped.initCause(actual);return mapped;
    }

    static RawJson present(Method method,OperationKey encoded,PlanningReadReceipt original) {
        Objects.requireNonNull(original);
        StrictJson.require(matches(method,encoded),"retained Cases READ does not belong to its original encoded step");
        StrictJson.require(original.request().operation().equals(new OperationKey(method.family().step()))
                &&original.request().arguments().equals(ChinaCasesCodec.executionArguments(
                        encoded,original.before().binding().connectionGeneration()))
                &&ChinaCasesCodec.executionStep(method,original).equals(encoded),
                "Cases encoded command, primitive operation and original native arguments differ");
        return ChinaCasesCodec.encodeExecutionResult(method,original);
    }

    private static void requireScope(RootRuntimeContext context,PlanningRequest original,Complete frame,
            Known known,Session same)throws IOException {
        context.writer().requireSession(same);context.requireCurrent(original.deadline());
        var root=context.core().sessionAccess().current();
        if(!root.ownedBy(context.core())||root.isRetired()||context.actions()!=root||context.adopted()!=root.driver()
                ||root.writer()!=context.writer()||root.archive()!=context.archive())
            throw new IOException("Cases EXECUTE crossed the actual current Root, writer or Driver");
        StrictJson.require(original.before().equals(frame.identity())&&original.source().equals(frame.source())
                &&original.sessionId().equals(frame.sessionId())&&frame.source().equals(context.source())
                &&frame.sessionId().equals(root.identity().sessionId())&&known.observation().isPresent(),
                "Cases EXECUTE needs its identical held ordinary planning frame");
        var facts=known.observation().orElseThrow();
        StrictJson.require(facts.source().equals(frame.source())
                &&facts.publicRevision().equals(frame.identity().frame().revision())
                &&facts.nativeRevision().equals(frame.identity().frame().identity().nativeRevision())
                &&facts.snapshotId().equals(frame.identity().frame().snapshotId())
                &&facts.transport().connectionGeneration().equals(frame.connectionGeneration()),
                "Cases actual Known facts differ from the held planning frame");
    }
}
