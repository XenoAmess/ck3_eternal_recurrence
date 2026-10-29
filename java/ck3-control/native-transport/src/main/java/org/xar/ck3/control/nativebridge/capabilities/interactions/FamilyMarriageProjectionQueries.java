package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;

/** One five-candidate read bound to the exact original legality and its original shared campaign ROOT. */
public final class FamilyMarriageProjectionQueries {
    public static final String CONTRACT_ID="family/first-heir-candidate-alliance-projection12004/v1";
    public static final String PERMISSION="source_qualified_first_heir_candidate_alliance_projection_v1";
    public interface Originals {
        PlanningReadReceipt load(ExactRef original);
        ExactRef referenceOf(PlanningReadReceipt original);
    }
    @FunctionalInterface public interface Admission {void admit(PlanningReadRequest actual);}
    private final Originals originals;
    private final FamilyRootBinding.Originals roots;
    private final ReadContract<OpportunityJson.Obj> contract;
    public FamilyMarriageProjectionQueries(ExactRef actualNativeSource,Originals actualOriginals,
            FamilyRootBinding.Originals actualRootOriginals,Admission actualAdmission) {
        Objects.requireNonNull(actualNativeSource);need(actualNativeSource.bytes()>0,"actual native projection source required");
        originals=Objects.requireNonNull(actualOriginals);roots=Objects.requireNonNull(actualRootOriginals);Objects.requireNonNull(actualAdmission);
        contract=new ReadContract<>(CONTRACT_ID,new OperationKey(FamilyMarriageValue.Mode.FIRST_HEIR.step()),Optional.empty(),PERMISSION,
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                actualNativeSource,(request,id)->{
                    actualAdmission.admit(request);var binding=binding(request);ObjectNode fields=F.objectNode().put("legality_query_sequence",binding.legalityQuerySequence());
                    for(int index=0;index<binding.candidates().size();index++)fields.put("candidate_id_"+index,binding.candidates().get(index).characterId());
                    // The actual ReadPermit supplies expected_revision to NativeWire.execute exactly once.
                    return new NativeRequest(FamilyMarriageValue.Mode.FIRST_HEIR.step(),Optional.empty(),encode(fields));
                },this::project,this::project);
    }
    public ReadContract<OpportunityJson.Obj> contract() {return contract;}
    /** Root passes its exact held Driver context and the original reference returned by the prior read. */
    public OpportunityJson.Obj canonicalArguments(Context context,OpportunityJson.Obj flat) {
        JsonNode supplied=InteractionArguments.parseApp(flat);closed(supplied,"legality","legality_read","candidate_character_ids");
        ExactRef reference=InteractionArguments.ref(field(supplied,"legality_read"));PlanningReadReceipt original=load(reference);
        need(field(supplied,"legality").equals(OpportunityJson.toNode(FamilyHeirNativeProjection.project(original,roots))),
                "planner legality differs from exact original native legality projection");
        ObjectNode canonical=InteractionArguments.body(context);InteractionArguments.ref(canonical.putObject("legality_read"),reference);
        canonical.set("candidate_character_ids",field(supplied,"candidate_character_ids"));
        OpportunityJson.Obj arguments=InteractionArguments.app(canonical);
        binding(new PlanningReadRequest(context.before(),context.source(),context.sessionId(),contract.operation(),arguments,context.deadline()));
        return arguments;
    }
    public FamilyMarriageValue.Observation decode(PlanningReadReceipt receipt) {
        requireOriginal(receipt);FamilyMarriageValue.Binding binding=binding(receipt.request());
        JsonNode arguments=InteractionArguments.parseApp(receipt.request().arguments());
        PlanningReadReceipt legality=load(InteractionArguments.ref(field(arguments,"legality_read")));
        need(!receipt.before().binding().observedAt().isBefore(legality.after().binding().observedAt()),
                "native projection predates its actual legality read");
        return FamilyMarriageValue.decode(receipt.original().originalResultToken().orElseThrow(),binding);
    }
    public OpportunityJson.Obj project(PlanningReadReceipt receipt) {
        var observation=decode(receipt);ObjectNode projected=InteractionArguments.parseApp(FamilyMarriageValue.project(observation));
        var frame=receipt.request().before().frame();projected.put("queried_snapshot_id",frame.snapshotId()).put("queried_revision",frame.revision())
                .put("queried_native_revision",frame.identity().nativeRevision());
        return InteractionArguments.app(projected);
    }
    private FamilyMarriageValue.Binding binding(PlanningReadRequest request) {
        need(request.operation().equals(contract.operation()),"projection canonical operation differs");
        JsonNode arguments=InteractionArguments.parseApp(request.arguments());closed(arguments,"group_context","legality_read","candidate_character_ids");
        Context context=InteractionArguments.context(request);PlanningReadReceipt original=load(InteractionArguments.ref(field(arguments,"legality_read")));
        var legality=FamilyHeirNativeProjection.decode(original,roots);Context previous=legality.binding().context();
        need(legality.availability().available() && previous.before().equals(context.before()) && previous.source().equals(context.source())
                && previous.sessionId().equals(context.sessionId()) && previous.connectionGeneration().equals(context.connectionGeneration())
                && previous.build()==context.build() && previous.controls().equals(context.controls()),
                "projection requires same actual current paused legality frame/source/actor/controls");
        List<Integer> ids=list(arguments,"candidate_character_ids",5,value->{need(value.isIntegralNumber(),"candidate native int32 required");
            return range(value.bigIntegerValue(),BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();});
        need(ids.size()==5,"exactly five projection candidates required");unique(ids,5);
        List<FamilyMarriageValue.Candidate> candidates=new ArrayList<>();
        for(int id:ids) {
            var selected=legality.nativeLegalCandidates().stream().filter(candidate->candidate.character().value()==id).toList();
            need(selected.size()==1,"projection candidate is not uniquely present in original native-final legal rows");
            var candidate=selected.getFirst();candidates.add(new FamilyMarriageValue.Candidate(id,Math.toIntExact(candidate.matchmaker().value())));
        }
        return new FamilyMarriageValue.Binding(FamilyMarriageValue.Mode.FIRST_HEIR,context,legality.querySequence(),
                Math.toIntExact(legality.binding().observedFirstHeir().orElseThrow()),candidates,false,Optional.empty());
    }
    private PlanningReadReceipt load(ExactRef reference) {
        PlanningReadReceipt original=Objects.requireNonNull(originals.load(reference));
        need(originals.referenceOf(original).equals(reference),"legality original archive custody differs from its exact reference");return original;
    }
    private static void requireOriginal(PlanningReadReceipt receipt) {
        need(receipt.contractId().equals(CONTRACT_ID) && receipt.request().operation().value().equals(FamilyMarriageValue.Mode.FIRST_HEIR.step())
                && receipt.original().nativeOk(),"original unique five-candidate projection read required");
        Context context=InteractionArguments.context(receipt.request());
        for(var guard:List.of(receipt.before(),receipt.after()))
            need(guard.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP && guard.paused() && guard.mapReady() && guard.playerAlive()
                    && guard.binding().observed().equals(receipt.request().before()) && guard.binding().source().equals(receipt.request().source())
                    && guard.binding().sessionId().equals(receipt.request().sessionId()) && guard.binding().operation().equals(receipt.request().operation())
                    && guard.binding().connectionGeneration().equals(context.connectionGeneration()),"projection original read crossed source/frame/session/connection");
        need(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()),"projection original full native guard changed");
        JsonNode frame=parse(receipt.original().originalFrame());closed(frame,"type","protocol_version","request_id","ok","result");
        eq(frame,"type","command_result");eq(frame,"protocol_version",BigInteger.ONE);eq(frame,"request_id",receipt.requestId());yes(frame,"ok");
        need(field(frame,"result").equals(parse(receipt.original().originalResultToken().orElseThrow())),"projection original packet/result custody differs");
    }
}
