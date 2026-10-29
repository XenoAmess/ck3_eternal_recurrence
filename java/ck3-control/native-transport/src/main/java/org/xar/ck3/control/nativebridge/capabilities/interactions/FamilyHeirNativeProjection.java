package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

/** Family consumer of the one installed typed heir-legality read, retaining its original receipt. */
public final class FamilyHeirNativeProjection {
    private FamilyHeirNativeProjection() { }
    /** Recheck a projected subject against the original root, rather than trusting its DTO constructor. */
    public static HeirSubject requireSubject(PlanningReadResult.Known<HeirSubject> actual,Context context) {
        var receipt=actual.receipt(); JsonNode original=parse(receipt.original().originalResultToken().orElseThrow());
        var view=F.objectNode().put("query_sequence",positive64(original,"query_sequence"))
                .put("queried_snapshot_id",receipt.request().before().frame().snapshotId())
                .put("queried_revision",receipt.request().before().frame().revision())
                .put("queried_native_revision",receipt.request().before().frame().identity().nativeRevision());
        var normalized=org.xar.ck3.control.application.capabilities.CampaignRootContextJson.normalizeNativeResult(
                InteractionArguments.app(object(original)),context.date(),context.revision());
        view.set("campaign_root_context",OpportunityJson.toNode(normalized.get("campaign_root_context")));
        var validated=subject(new PlanningReadResult.Known<>(InteractionArguments.app(view),receipt,actual.originalReceipt()),context);
        need(validated instanceof PlanningReadResult.Known<HeirSubject>,"projected subject has no actual root title heir");
        var expected=((PlanningReadResult.Known<HeirSubject>)validated).value();
        need(expected.equals(actual.value()),"projected heir subject differs from its original complete root query");
        return expected;
    }
    /** Revalidates through the same actual Root issuer; the DTO constructor cannot grant lineage custody. */
    public static HeirSubject requireSubject(PlanningReadResult.Known<HeirSubject> actual,Context context,FamilyRootBinding.Originals originals) {
        var root=java.util.Objects.requireNonNull(originals.read(actual.originalReceipt()));
        need(root.originalReceipt().equals(actual.originalReceipt())&&root.receipt().equals(actual.receipt()),
                "projected subject differs from the exact original Root receipt");
        var validated=subject(root,context,originals);
        need(validated instanceof PlanningReadResult.Known<HeirSubject>,"projected subject has no actual root title heir");
        var expected=((PlanningReadResult.Known<HeirSubject>)validated).value();
        need(expected.equals(actual.value()),"projected heir subject differs from its qualified original Root query");
        return expected;
    }
    public static PlanningReadResult<HeirSubject> subject(PlanningReadResult.Known<OpportunityJson.Obj> root,Context context) {
        return subject(root,FamilyRootBinding.fromOriginal(root,context));
    }
    public static PlanningReadResult<HeirSubject> subject(PlanningReadResult.Known<OpportunityJson.Obj> root,Context context,FamilyRootBinding.Originals originals) {
        var basis=java.util.Objects.requireNonNull(originals.bind(root.originalReceipt(),context));
        need(basis.originalRootReceipt().equals(root.originalReceipt())&&basis.binding().context().equals(context),
                "heir subject issuer changed its original Root receipt or target context");
        return subject(root,basis);
    }
    private static PlanningReadResult<HeirSubject> subject(PlanningReadResult.Known<OpportunityJson.Obj> root,FamilyRootBinding.Basis basis) {
        if(basis.binding().observedFirstHeir().isEmpty())
            return new PlanningReadResult.Unavailable<>("original_primary_title_first_heir_absent",Optional.of(root.receipt().original()));
        var subject=new HeirSubject(new CharacterId(basis.binding().observedFirstHeir().getAsLong()),
                basis.binding().rootQuerySequence(),basis.originalRootReceipt());
        return new PlanningReadResult.Known<>(subject,root.receipt(),root.originalReceipt());
    }
    public static FamilyHeirLegality.Observation decode(PlanningReadReceipt receipt,FamilyRootBinding.Originals originals) {
        need(receipt.contractId().equals("interactions:first-heir-legality") && receipt.original().nativeOk(),
                "original unique typed heir-legality contract receipt required");
        var request=receipt.request();
        need(request.operation().value().equals(FamilyHeirLegality.STEP),"family legality receipt operation differs");
        Context context=InteractionArguments.context(request);
        need(context.build()==Build.CROZIER4,"current family runtime requires actual4 source");
        JsonNode args=InteractionArguments.parseApp(request.arguments());
        closed(args,"group_context","first_heir_id","root_query_sequence","root_evidence");
        ExactRef ref=InteractionArguments.ref(field(args,"root_evidence"));
        var root=originals.read(ref); need(root.originalReceipt().equals(ref),"family root archive returned another original");
        var basis=java.util.Objects.requireNonNull(originals.bind(ref,context));
        need(basis.originalRootReceipt().equals(ref)&&basis.binding().context().equals(context),
                "family legality issuer changed its exact Root receipt or target context");
        need(basis.binding().observedFirstHeir().isPresent(),"typed family legality receipt has no actual original title heir");
        eq(args,"first_heir_id",BigInteger.valueOf(basis.binding().observedFirstHeir().orElseThrow()));
        eq(args,"root_query_sequence",basis.binding().rootQuerySequence());
        for(var guard:List.of(receipt.before(),receipt.after()))
            need(guard.paused() && guard.mapReady() && guard.playerAlive() && guard.binding().observed().equals(request.before()) &&
                    guard.binding().operation().equals(request.operation()) && guard.binding().source().equals(request.source()) &&
                    guard.binding().sessionId().equals(request.sessionId()) &&
                    guard.binding().connectionGeneration().equals(context.connectionGeneration()),
                    "family legality read crossed actual source/session/frame");
        need(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()),
                "family legality guard changed between observations");
        need(!root.receipt().after().binding().observedAt().isAfter(receipt.before().binding().observedAt()),
                "family subject original root was observed after the leaf query");
        return FamilyHeirLegality.decode(receipt.original().originalResultToken().orElseThrow(),basis.binding());
    }
    public static OpportunityJson.Obj project(PlanningReadReceipt receipt,FamilyRootBinding.Originals originals) {
        return FamilyHeirLegality.project(decode(receipt,originals));
    }
    public static PlanningReadResult.Known<OpportunityJson.Obj> project(
            PlanningReadResult.Known<HeirMarriageLegality> actual,FamilyRootBinding.Originals originals) {
        var full=decode(actual.receipt(),originals);
        var frame=new Frame(full.binding().context().revision(),full.binding().context().date(),full.binding().context().actor(),
                full.binding().context().build(),full.querySequence());
        var binding=full.binding(); var subject=new HeirSubject(new CharacterId(binding.observedFirstHeir().orElseThrow()),
                binding.rootQuerySequence(),binding.originalCampaignRoot());
        var d=full.diagnostics();
        var expected=new HeirMarriageLegality(frame,subject,full.availability(),full.candidates(),
                d.slotsScanned(),d.storageCapacity(),full.subjectRoleMismatches());
        need(expected.equals(actual.value()),"typed heir legality differs from its complete original native decode");
        return new PlanningReadResult.Known<>(FamilyHeirLegality.project(full),actual.receipt(),actual.originalReceipt());
    }
}
