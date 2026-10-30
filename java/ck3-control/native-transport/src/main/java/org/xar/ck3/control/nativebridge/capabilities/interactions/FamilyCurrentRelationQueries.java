package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

/** One actual query and explicit archive-only replay, both bound to the original shared Finance ROOT. */
public final class FamilyCurrentRelationQueries {
    public static final String CONTRACT_ID="family/current-first-heir-relationship12004/v2",PERMISSION="source_qualified_current_first_heir_relationship_v2";
    @FunctionalInterface public interface Admission{void admit(PlanningReadRequest actual);}
    private final FamilyRootBinding.Originals roots;
    private final FamilyRelationMaterialExports exports;
    private final ReadContract<OpportunityJson.Obj> contract;
    public FamilyCurrentRelationQueries(ExactRef actualNativeSource,FamilyRootBinding.Originals sameOriginalRoots,Admission actualAdmission,FamilyRelationMaterialExports actualExports){
        Objects.requireNonNull(actualNativeSource);need(actualNativeSource.bytes()>0,"actual current relation native definition required");roots=Objects.requireNonNull(sameOriginalRoots);exports=Objects.requireNonNull(actualExports);Objects.requireNonNull(actualAdmission);
        contract=new ReadContract<>(CONTRACT_ID,new OperationKey(FamilyCurrentRelation.STEP),Optional.empty(),PERMISSION,
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,actualNativeSource,
                (request,requestId)->{
                    actualAdmission.admit(request);binding(request);String path=exports.prepare(requestId);
                    // The real ReadPermit supplies expected_revision once. This is
                    // the same private native job, with an actual fresh export.
                    ObjectNode fields=F.objectNode().put("guardian_factory_sidecar_path",path);
                    return new NativeRequest(FamilyCurrentRelation.STEP,Optional.empty(),encode(fields));
                },this::project,this::project).withRetainedMaterialCapture(receipt->{
                    requireOriginal(receipt);
                    return new PlanningReadReceipt.RetainedMaterial(PlanningReadReceipt.RetainedMaterial.Kind.FAMILY_RELATION_EXPORT,exports.capture(receipt).reference());
                });
    }
    public ReadContract<OpportunityJson.Obj> contract(){return contract;}
    /** Existing CAS original only: no current sidecar or native I/O and no new export authority. */
    public FamilyRelationMaterialExports.Captured originalMaterials(PlanningReadReceipt actual){requireOriginal(actual);return exports.archived(actual);}
    /** The Root thin adapter supplies its actual same-lease ROOT-bound flat arguments. */
    public OpportunityJson.Obj canonical(Context actual,OpportunityJson.Obj rootBoundFlat){
        Objects.requireNonNull(actual);JsonNode supplied=InteractionArguments.parseApp(rootBoundFlat);closed(supplied,"expected_native_revision","root_binding");eq(supplied,"expected_native_revision",actual.revision());ObjectNode canonical=InteractionArguments.body(actual);canonical.set("expected_native_revision",field(supplied,"expected_native_revision"));canonical.set("root_binding",field(supplied,"root_binding"));OpportunityJson.Obj result=InteractionArguments.app(canonical);
        binding(new PlanningReadRequest(actual.before(),actual.source(),actual.sessionId(),contract.operation(),result,actual.deadline()));return result;
    }
    /** Native action preparation reuses the exact same query, without manufacturing a PlanningRequest or another ROOT query. */
    public OpportunityJson.Obj canonicalArguments(Context actual,OpportunityJson.Obj flat,ExactRef originalRootReceipt){
        var basis=roots.bind(Objects.requireNonNull(originalRootReceipt),Objects.requireNonNull(actual));need(basis.originalRootReceipt().equals(originalRootReceipt)&&basis.binding().context().equals(actual),"current relation qualified ROOT issuer changed the original or target");return canonical(actual,FamilyRootBinding.arguments(basis,flat));
    }
    /** This method is pure archival interpretation and never calls the live sidecar capture or a fresh native read. */
    public FamilyCurrentRelation.Observation decodeReceipt(PlanningReadReceipt receipt){
        requireOriginal(receipt);FamilyRootBinding.Basis actual=binding(receipt.request());var root=roots.read(actual.originalRootReceipt());need(!root.receipt().after().binding().observedAt().isAfter(receipt.before().binding().observedAt()),"current relationship predates its actual shared ROOT subject");return FamilyCurrentRelation.decode(receipt,actual,exports.archived(receipt));
    }
    public OpportunityJson.Obj project(PlanningReadReceipt receipt){return decodeReceipt(receipt).original();}
    private FamilyRootBinding.Basis binding(PlanningReadRequest request){
        need(request.operation().value().equals(FamilyCurrentRelation.STEP),"relation canonical operation differs");Context context=InteractionArguments.context(request);need(context.build()==Build.CROZIER4,"complete current relation requires exact actual4 context");ObjectNode args=InteractionArguments.parseApp(request.arguments());closed(args,"group_context","expected_native_revision","root_binding");eq(args,"expected_native_revision",context.revision());args.remove("group_context");
        var rooted=new PlanningReadRequest(request.origin(),request.source(),request.sessionId(),request.operation(),InteractionArguments.app(args),request.deadline());return FamilyRootBinding.decodeArguments(rooted,context,roots);
    }
    private void requireOriginal(PlanningReadReceipt receipt){
        Objects.requireNonNull(receipt);need(receipt.contractId().equals(CONTRACT_ID)&&receipt.request().operation().equals(contract.operation())&&receipt.original().nativeOk(),"original unique current relationship contract receipt required");Context context=InteractionArguments.context(receipt.request());
        for(var guard:List.of(receipt.before(),receipt.after()))need(guard.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP&&guard.paused()&&guard.mapReady()&&guard.playerAlive()&&guard.binding().observed().equals(receipt.request().before())&&guard.binding().source().equals(receipt.request().source())&&guard.binding().sessionId().equals(receipt.request().sessionId())&&guard.binding().operation().equals(receipt.request().operation())&&guard.binding().connectionGeneration().equals(context.connectionGeneration()),"relationship original before/after guards crossed actual source/session/frame/connection");
        need(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()),"current relationship original full paused guard changed");JsonNode frame=parse(receipt.original().originalFrame());closed(frame,"type","protocol_version","request_id","ok","result","guardian_factory_discovery_v1");FamilyRelationMaterialExports.requireCompletedExport(receipt);
    }
}
