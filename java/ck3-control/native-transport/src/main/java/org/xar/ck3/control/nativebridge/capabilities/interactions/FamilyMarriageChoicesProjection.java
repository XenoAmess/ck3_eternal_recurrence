package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

/** Full ruler choices and diagnostics from the single installed typed marriage read. */
public final class FamilyMarriageChoicesProjection {
    public static final String STEP="query-arrange-marriage-choices";
    private FamilyMarriageChoicesProjection() { }
    /** Canonical arguments for this same installed read; Root supplies its actual complete context. */
    public static OpportunityJson.Obj applicationArguments(Context context) {
        return InteractionArguments.app(InteractionArguments.body(Objects.requireNonNull(context)));
    }
    public record Observation(Frame frame,List<MarriageChoice> choices,MarriageDiagnostics diagnostics,RawJson original) {
        public Observation { Objects.requireNonNull(frame); choices=List.copyOf(choices);
            Objects.requireNonNull(diagnostics); Objects.requireNonNull(original);
            need(diagnostics.complete(),"ruler marriage choices require complete native storage enumeration"); }
        public MarriageChoices typed() { return new MarriageChoices(frame,choices); }
    }
    public static Observation decodeNative(RawJson raw,Context context) {
        JsonNode n=parse(raw);
        closed(n,"step","accepted","status","query_sequence","arrange_marriage_choices","arrange_marriage_diagnostics");
        eq(n,"step",STEP); yes(n,"accepted"); eq(n,"status","available");
        List<MarriageChoice> choices=list(n,"arrange_marriage_choices",65536,row->{
            closed(row,"choice_id","played_character_id","candidate_character_id");
            long player=integer(row,"played_character_id",1,Integer.MAX_VALUE),candidate=integer(row,"candidate_character_id",1,Integer.MAX_VALUE);
            need(BigInteger.valueOf(player).equals(context.actor()),"ruler choice belongs to another actual player");
            return new MarriageChoice(text(row,"choice_id"),player,candidate);
        });
        unique(choices.stream().map(MarriageChoice::choiceId).toList(),65536);
        return new Observation(new Frame(context.revision(),context.date(),context.actor(),context.build(),positive64(n,"query_sequence")),
                choices,MarriageDiagnostics.decode(field(n,"arrange_marriage_diagnostics")),raw);
    }
    public static Observation decode(PlanningReadReceipt receipt) {
        need(receipt.contractId().equals("interactions:marriage-choices") && receipt.original().nativeOk(),
                "original unique marriage choices contract required");
        var request=receipt.request(); need(request.operation().value().equals(STEP),"ruler choices operation differs");
        Context context=InteractionArguments.context(request);
        closed(InteractionArguments.parseApp(request.arguments()),"group_context");
        for(var guard:List.of(receipt.before(),receipt.after()))
            need(guard.paused() && guard.mapReady() && guard.playerAlive() && guard.binding().observed().equals(request.before()) &&
                    guard.binding().source().equals(request.source()) && guard.binding().sessionId().equals(request.sessionId()) &&
                    guard.binding().operation().equals(request.operation()) &&
                    guard.binding().connectionGeneration().equals(context.connectionGeneration()),
                    "ruler choice read crossed actual source/session/frame");
        need(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()),
                "ruler choice actual query guard changed");
        JsonNode frame=parse(receipt.original().originalFrame());
        closed(frame,"type","protocol_version","request_id","ok","result");
        eq(frame,"type","command_result"); eq(frame,"protocol_version",BigInteger.ONE);
        eq(frame,"request_id",receipt.requestId()); yes(frame,"ok");
        need(field(frame,"result").equals(parse(receipt.original().originalResultToken().orElseThrow())),
                "ruler choice original frame differs from retained result token");
        return decodeNative(receipt.original().originalResultToken().orElseThrow(),context);
    }
    public static OpportunityJson.Obj project(PlanningReadReceipt receipt) {
        Observation validated=decode(receipt);
        var request=receipt.request(); ObjectNode result=parse(validated.original()).deepCopy(); var frame=request.before().frame();
        result.put("queried_snapshot_id",frame.snapshotId()).put("queried_revision",frame.revision())
                .put("queried_native_revision",frame.identity().nativeRevision());
        return InteractionArguments.app(result);
    }
    public static PlanningReadResult.Known<OpportunityJson.Obj> project(PlanningReadResult.Known<MarriageChoices> actual) {
        Observation value=decode(actual.receipt());
        need(value.typed().equals(actual.value()),"ruler typed choices differ from complete original native packet");
        return new PlanningReadResult.Known<>(project(actual.receipt()),actual.receipt(),actual.originalReceipt());
    }
}
