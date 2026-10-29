package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyOutgoingCodec.Snapshot;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

/** Education storage DATA around the single complete codec. Root replays the dedicated single basis; no queue ACK is a send verdict. */
public final class GuardianOutgoingCodec {
    private static final String ORDINARY_CONTRACT="interactions:ordinary-query";
    private static final String RECONCILIATION_CONTRACT="interactions:ordinary-query:reconciliation/v1";
    private GuardianOutgoingCodec() { }

    public static Snapshot decode(RawJson raw, Context context, OrdinaryRequest request) {
        OrdinaryInteractionCodec.query(raw,context,request);
        JsonNode envelope=parse(raw), payload=field(envelope,"character_interaction_ordinary_context");
        return group(field(payload,FamilyOutgoingCodec.GROUP),context,request,payload,positive64(envelope,"query_sequence"));
    }

    /** Only the two installed read profiles can retain this education original. */
    public static Snapshot decodeReceipt(PlanningReadReceipt receipt) {
        Objects.requireNonNull(receipt);
        var request=receipt.request(); boolean gameplay=request.origin() instanceof CommandOrigin.Gameplay;
        boolean reconciliation=request.origin() instanceof CommandOrigin.Reconciliation;
        need(gameplay && receipt.contractId().equals(ORDINARY_CONTRACT)
                || reconciliation && receipt.contractId().equals(RECONCILIATION_CONTRACT),
                "education storage requires its exact registered origin/contract profile");
        need(receipt.original().nativeOk() && receipt.requestId().equals(receipt.original().requestId())
                && request.operation().value().equals(OrdinaryInteractionCodec.QUERY_STEP),
                "original successful ordinary query and request identity required");
        JsonNode original=parse(receipt.original().originalFrame());
        closed(original,"type","protocol_version","request_id","ok","result");
        eq(original,"type","command_result"); eq(original,"protocol_version",BigInteger.ONE);
        eq(original,"request_id",receipt.requestId()); yes(original,"ok");
        RawJson token=receipt.original().originalResultToken().orElseThrow();
        need(field(original,"result").equals(parse(token)),"retained education token differs from the original packet");
        Context context=InteractionArguments.context(request);
        OrdinaryRequest intent=InteractionArguments.ordinary(InteractionArguments.parseApp(request.arguments()));
        for(var guard:List.of(receipt.before(),receipt.after())) {
            var binding=guard.binding();
            need(binding.operation().equals(request.operation()) && binding.source().equals(request.source())
                    && binding.sessionId().equals(request.sessionId()) && binding.connectionGeneration().equals(context.connectionGeneration()),
                    "education storage query crossed its actual source/session/connection");
            if(gameplay) {
                need(guard.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                        && binding.origin() instanceof CommandOrigin.Gameplay && guard.paused() && guard.mapReady() && guard.playerAlive()
                        && binding.observed().equals(request.before()),"education gameplay query crossed its living paused frame");
            } else {
                var actual=request.origin().requireReconciliation();
                need(guard.guardMode()==ReadContract.GuardMode.RECONCILIATION_OBSERVATION
                        && binding.origin() instanceof CommandOrigin.Reconciliation
                        && actual.sameGuardFrame(binding.origin().requireReconciliation())
                        && binding.nativeEvidence().equals(actual.nativeEvidence())
                        && binding.capabilityEvidence().equals(actual.capabilityEvidence())
                        && binding.supportingEvidence().size()==1,
                        "education reconciliation query crossed its canonical pending or physical originals");
            }
        }
        need(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()),
                "education storage query changed its complete guarded frame");
        return decode(token,context,intent);
    }

    public static RawJson encodeOriginal(RawJson original, Snapshot expected, Context context, OrdinaryRequest request) {
        need(decode(original,context,request).equals(expected),"education outgoing value differs from its original packet");
        return original;
    }

    static Snapshot group(JsonNode n, Context c, OrdinaryRequest r, JsonNode parent, BigInteger sequence) {
        need(c.build()==Build.CROZIER4 && r.interaction().value().equals(FamilyOutgoingCodec.Profile.EDUCATE_CHILD.interactionKey()),
                "education storage profile requires the actual4 education query");
        Snapshot snapshot=FamilyOutgoingCodec.decodeGroup(n,new Frame(c.revision(),c.date(),c.actor(),c.build(),sequence),
                FamilyOutgoingCodec.Profile.EDUCATE_CHILD);
        if(!snapshot.complete()) return snapshot;
        BigInteger parentHash=nullableNumber(parent,"definition_stable_hash",BigInteger.ZERO,U32);
        need(parentHash!=null && snapshot.definitionHash().orElseThrow()==parentHash.longValueExact(),
                "storage definition differs from the original owned education definition");
        need(text(parent,"status").equals("available") && bool(parent,"native_context_available")
                && bool(parent,"source_code_pins_verified") && bool(parent,"actor_binding_verified")
                && bool(parent,"recipient_binding_verified") && bool(parent,"owner_thread_verified")
                && bool(parent,"tls_verified") && bool(parent,"frame_verified"),
                "complete storage lacks the actual owner/source/frame-bound education context");
        JsonNode material=field(parent,"education_request_materialization"); eq(material,"status","available");
        need(!field(material,"child_full_id").isNull() && !field(material,"guardian_full_id").isNull()
                && !field(material,"requested_option_keys").isNull(),"complete education scope requires explicit materialized roles/options");
        JsonNode roles=field(parent,"effective_roles");
        eq(roles,"actor_id",c.actor()); eq(roles,"recipient_id",BigInteger.valueOf(r.recipient().value()));
        nil(roles,"sixth_role_id");
        return snapshot;
    }
}

