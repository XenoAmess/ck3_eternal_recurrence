package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;

/** The two original child reads, with value eligibility reopened from the exact prior subject receipt. */
public final class FamilyChildMarriageQueries {
    public static final String SUBJECT_ID="family/player-child-marriage-subject/v1",VALUE_ID="family/player-child-marriage-value/v1";
    public static final String PERMISSION="allow_private_player_child_marriage_subject_query";
    public record Sources(ExactRef subjectNative,ExactRef valueNative){public Sources{for(var ref:List.of(subjectNative,valueNative))need(ref.bytes()>0,"actual child native producer source required");}}
    public interface Originals {PlanningReadReceipt loadRead(ExactRef reference);ExactRef referenceOf(PlanningReadReceipt receipt);}
    @FunctionalInterface public interface Admission {void admit(PlanningReadRequest actual);}
    private final Originals originals;
    private final ReadContract<OpportunityJson.Obj> subject,value;
    public FamilyChildMarriageQueries(Sources sources,Originals actualOriginals,Admission actualAdmission){
        Objects.requireNonNull(sources);originals=Objects.requireNonNull(actualOriginals);Objects.requireNonNull(actualAdmission);
        subject=new ReadContract<>(SUBJECT_ID,new OperationKey(FamilyChildMarriageSubject.STEP),Optional.empty(),PERMISSION,
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                sources.subjectNative(),(request,id)->{actualAdmission.admit(request);var binding=subjectBinding(request);
                    return new NativeRequest(FamilyChildMarriageSubject.STEP,Optional.empty(),encode(F.objectNode().put("subject_character_id",binding.subject()).put("diagnose_family_arrays",binding.diagnoseFamilyArrays())));
                },receipt->FamilyChildMarriageSubject.project(decodeSubject(receipt)),receipt->FamilyChildMarriageSubject.project(decodeSubject(receipt)));
        value=new ReadContract<>(VALUE_ID,new OperationKey(FamilyMarriageValue.Mode.CHILD.step()),Optional.empty(),PERMISSION,
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                sources.valueNative(),(request,id)->{actualAdmission.admit(request);var binding=valueBinding(request);
                    // NativeWire.execute injects the actual ReadPermit's expected_revision exactly once.
                    ObjectNode fields=F.objectNode().put("legality_query_sequence",binding.legalityQuerySequence()).put("subject_character_id",binding.subjectId())
                            .put("candidate_character_id",binding.candidates().getFirst().characterId()).put("request_matrilineal_option",binding.requestMatrilineal());
                    return new NativeRequest(FamilyMarriageValue.Mode.CHILD.step(),Optional.empty(),encode(fields));
                },this::projectValue,this::projectValue);
    }
    public ReadContract<OpportunityJson.Obj> subject(){return subject;}
    public ReadContract<OpportunityJson.Obj> value(){return value;}
    public static OpportunityJson.Obj canonicalSubject(Context actual,OpportunityJson.Obj flat){
        JsonNode input=InteractionArguments.parseApp(flat);object(input);var names=new java.util.HashSet<String>();input.fieldNames().forEachRemaining(names::add);
        need(names.equals(java.util.Set.of("expected_native_revision","subject_character_id"))||names.equals(java.util.Set.of("expected_native_revision","subject_character_id","diagnose_family_arrays")),"wrong child subject planning fields");
        eq(input,"expected_native_revision",actual.revision());int child=integer(input,"subject_character_id",1,Integer.MAX_VALUE);boolean diagnostic=input.has("diagnose_family_arrays")&&bool(input,"diagnose_family_arrays");
        new FamilyChildMarriageSubject.Binding(actual,child,diagnostic);ObjectNode out=InteractionArguments.body(actual).put("expected_native_revision",actual.revision()).put("subject_character_id",child).put("diagnose_family_arrays",diagnostic);
        return InteractionArguments.app(out);
    }
    public OpportunityJson.Obj canonicalValue(Context actual,OpportunityJson.Obj flat){
        JsonNode input=InteractionArguments.parseApp(flat);closed(input,"legality","subject_read","candidate_character_id","request_matrilineal_option");
        ExactRef ref=InteractionArguments.ref(field(input,"subject_read"));PlanningReadReceipt prior=load(ref);var decoded=decodeSubject(prior);
        need(field(input,"legality").equals(OpportunityJson.toNode(FamilyChildMarriageSubject.project(decoded))),"planner child legality differs from exact original child subject read");
        ObjectNode out=InteractionArguments.body(actual);InteractionArguments.ref(out.putObject("subject_read"),ref);
        out.set("candidate_character_id",field(input,"candidate_character_id"));out.set("request_matrilineal_option",field(input,"request_matrilineal_option"));
        var args=InteractionArguments.app(out);valueBinding(new PlanningReadRequest(actual.before(),actual.source(),actual.sessionId(),value.operation(),args,actual.deadline()));return args;
    }
    public static FamilyChildMarriageSubject.Observation decodeSubject(PlanningReadReceipt receipt){
        requireOriginal(receipt,SUBJECT_ID,FamilyChildMarriageSubject.STEP);return FamilyChildMarriageSubject.decode(receipt.original().originalResultToken().orElseThrow(),subjectBinding(receipt.request()));
    }
    public FamilyMarriageValue.Observation decodeValue(PlanningReadReceipt receipt){
        requireOriginal(receipt,VALUE_ID,FamilyMarriageValue.Mode.CHILD.step());var binding=valueBinding(receipt.request());
        JsonNode args=InteractionArguments.parseApp(receipt.request().arguments());PlanningReadReceipt prior=load(InteractionArguments.ref(field(args,"subject_read")));
        need(!receipt.before().binding().observedAt().isBefore(prior.after().binding().observedAt()),"child value original predates its subject read");
        return FamilyMarriageValue.decode(receipt.original().originalResultToken().orElseThrow(),binding);
    }
    public OpportunityJson.Obj projectValue(PlanningReadReceipt receipt){return FamilyMarriageValue.project(decodeValue(receipt));}
    private static FamilyChildMarriageSubject.Binding subjectBinding(PlanningReadRequest request){
        need(request.operation().value().equals(FamilyChildMarriageSubject.STEP),"child subject canonical operation differs");JsonNode args=InteractionArguments.parseApp(request.arguments());
        closed(args,"group_context","expected_native_revision","subject_character_id","diagnose_family_arrays");Context context=InteractionArguments.context(request);eq(args,"expected_native_revision",context.revision());
        return new FamilyChildMarriageSubject.Binding(context,integer(args,"subject_character_id",1,Integer.MAX_VALUE),bool(args,"diagnose_family_arrays"));
    }
    private FamilyMarriageValue.Binding valueBinding(PlanningReadRequest request){
        need(request.operation().value().equals(FamilyMarriageValue.Mode.CHILD.step()),"child value canonical operation differs");JsonNode args=InteractionArguments.parseApp(request.arguments());closed(args,"group_context","subject_read","candidate_character_id","request_matrilineal_option");
        Context current=InteractionArguments.context(request);PlanningReadReceipt prior=load(InteractionArguments.ref(field(args,"subject_read")));var subject=decodeSubject(prior);Context previous=subject.binding().context();
        need(subject.availability().available()&&subject.fields().childVerified()&&previous.before().equals(current.before())&&previous.source().equals(current.source())&&previous.sessionId().equals(current.sessionId())
                &&previous.connectionGeneration().equals(current.connectionGeneration())&&previous.build()==current.build()&&previous.controls().equals(current.controls()),"child value requires the same actual paused subject frame/source/player/session/controls");
        int candidateId=integer(args,"candidate_character_id",1,Integer.MAX_VALUE);var admitted=subject.nativeLegalCandidates().stream().filter(row->row.value().character().value()==candidateId).toList();need(admitted.size()==1,"child value candidate not unique in original native-final legal rows");
        var candidate=admitted.getFirst().value();var fields=subject.fields();var lineage=new FamilyMarriageValue.Lineage(optional(fields.house()),optional(fields.dynasty()));
        return new FamilyMarriageValue.Binding(FamilyMarriageValue.Mode.CHILD,current,subject.querySequence(),subject.binding().subject(),List.of(new FamilyMarriageValue.Candidate(candidateId,Math.toIntExact(candidate.matchmaker().value()))),bool(args,"request_matrilineal_option"),Optional.of(lineage));
    }
    private static OptionalInt optional(Integer value){return value==null?OptionalInt.empty():OptionalInt.of(value);}
    private PlanningReadReceipt load(ExactRef ref){PlanningReadReceipt receipt=Objects.requireNonNull(originals.loadRead(ref));need(originals.referenceOf(receipt).equals(ref),"child read archive custody differs from its exact reference");return receipt;}
    private static void requireOriginal(PlanningReadReceipt receipt,String contract,String step){
        need(receipt.contractId().equals(contract)&&receipt.request().operation().value().equals(step)&&receipt.request().origin() instanceof CommandOrigin.Gameplay&&receipt.original().nativeOk(),"original installed child contract read required");Context context=InteractionArguments.context(receipt.request());
        for(var guard:List.of(receipt.before(),receipt.after()))need(guard.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP&&guard.paused()&&guard.mapReady()&&guard.playerAlive()
                &&guard.binding().observed().equals(receipt.request().before())&&guard.binding().source().equals(receipt.request().source())&&guard.binding().sessionId().equals(receipt.request().sessionId())
                &&guard.binding().operation().equals(receipt.request().operation())&&guard.binding().connectionGeneration().equals(context.connectionGeneration()),"child original crossed source/frame/session/connection guard");
        need(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()),"child original native guard changed during query");JsonNode frame=parse(receipt.original().originalFrame());closed(frame,"type","protocol_version","request_id","ok","result");
        eq(frame,"type","command_result");eq(frame,"protocol_version",BigInteger.ONE);eq(frame,"request_id",receipt.requestId());yes(frame,"ok");need(field(frame,"result").equals(parse(receipt.original().originalResultToken().orElseThrow())),"child original packet/result custody differs");
    }
}
