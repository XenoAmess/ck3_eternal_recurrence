package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

/** Family planning projection of the one installed ordinary read, never another native producer. */
public final class FamilyEducationNativeProjection {
    private FamilyEducationNativeProjection() { }
    public static OrdinaryRequest intent(Context context, OpportunityJson.Obj familyArguments) {
        need(context.build()==Build.CROZIER4,"family education requires actual current4 source");
        ObjectNode args=InteractionArguments.parseApp(familyArguments);
        Set<String> keys=Set.of("interaction_key","recipient_id","expected_revision");
        for(String optional:List.of("child_full_id","guardian_full_id","requested_option_keys"))
            if(args.has(optional)) keys=union(keys,optional);
        closed(args,keys); eq(args,"interaction_key","educate_child_interaction");
        eq(args,"expected_revision",context.before().frame().revision());
        need(args.has("child_full_id")==args.has("guardian_full_id"),"family education pair must be provided together");
        Optional<CharacterId> child=args.has("child_full_id")?Optional.of(new CharacterId(id(args,"child_full_id"))):Optional.empty();
        Optional<CharacterId> guardian=args.has("guardian_full_id")?Optional.of(new CharacterId(id(args,"guardian_full_id"))):Optional.empty();
        Optional<List<InteractionKey>> options=args.has("requested_option_keys")?Optional.of(list(args,"requested_option_keys",4096,n->{
            need(n.isTextual(),"family education option must be a canonical string"); return new InteractionKey(n.textValue());
        })):Optional.empty();
        return new OrdinaryRequest(new InteractionKey("educate_child_interaction"),new CharacterId(id(args,"recipient_id")),
                Optional.of(new EducationIntent(child,guardian,options)));
    }
    /** The same canonical arguments consumed by InteractionCapabilities.Installation.ordinary. */
    public static OpportunityJson.Obj applicationArguments(Context context, OpportunityJson.Obj familyArguments) {
        OrdinaryRequest intent=intent(context,familyArguments);
        ObjectNode body=InteractionArguments.body(context); InteractionArguments.ordinary(body,intent);
        return InteractionArguments.app(body);
    }
    public static OpportunityJson.Obj project(PlanningReadReceipt receipt) {
        // This also requires the one real contract ID and original before/after
        // source/session/frame guards, including the required versioned group.
        GuardianOutgoingCodec.decodeReceipt(receipt);
        var request=receipt.request(); var frame=request.before().frame();
        ObjectNode value=parse(receipt.original().originalResultToken().orElseThrow()).deepCopy();
        value.put("queried_snapshot_id",frame.snapshotId()).put("queried_revision",frame.revision())
                .put("queried_native_revision",frame.identity().nativeRevision())
                .put("ordinary_interaction_context_ready",text(value,"status").equals("available"));
        return InteractionArguments.app(value);
    }
    public static PlanningReadResult.Known<OpportunityJson.Obj> project(PlanningReadResult.Known<OrdinaryContext> actual) {
        var receipt=actual.receipt(); var request=receipt.request();
        Context context=InteractionArguments.context(request);
        OrdinaryRequest intent=InteractionArguments.ordinary(InteractionArguments.parseApp(request.arguments()));
        need(OrdinaryInteractionCodec.query(receipt.original().originalResultToken().orElseThrow(),context,intent).equals(actual.value()),
                "family typed ordinary result differs from its original receipt");
        return new PlanningReadResult.Known<>(project(receipt),receipt,actual.originalReceipt());
    }
}
