package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionRules.*;

/** Versioned immutable plan persistence. Explicit nulls and empty signatures retain distinct meanings. */
public final class KnownPendingInteractionPlanCodec {
    public static final String SCHEMA="xar.java.known-pending-plan/v2";
    private KnownPendingInteractionPlanCodec() { }
    public static ObjectNode encode(Plan plan) {
        ObjectNode n=F.objectNode().put("schema",SCHEMA)
                .put("classification",plan.classification().key()).put("rule_id",plan.ruleId())
                .put("ordinary_gold_ready",plan.ordinaryGoldReady());
        if(plan.selected().isEmpty())n.putNull("selected_action");else n.put("selected_action",plan.selected().orElseThrow().key());
        string(n,"required_step",plan.requiredStep());string(n,"required_tool",plan.requiredTool());
        var gaps=n.putArray("blocked_reasons");plan.blockedReasons().forEach(gaps::add);
        if(plan.warId().isPresent())n.put("war_id",plan.warId().orElseThrow());else n.putNull("war_id");
        if(plan.prisonerId().isPresent())n.put("prisoner_id",plan.prisonerId().orElseThrow());else n.putNull("prisoner_id");
        if(plan.quotedGoldRaw().isPresent())n.put("quoted_gold_raw",plan.quotedGoldRaw().orElseThrow());else n.putNull("quoted_gold_raw");
        if(plan.originalWarSignature().isEmpty())n.putNull("original_war_signature");
        else {
            var wars=n.putArray("original_war_signature");
            for(WarSignature s:plan.originalWarSignature().orElseThrow()) {
                ObjectNode row=wars.addObject().put("war_id",s.warId()).put("player_side",s.side().name().toLowerCase(Locale.ROOT))
                        .put("player_relative_war_score",s.score());
                if(s.primaryLeader()==null)row.putNull("player_is_primary_war_leader");else row.put("player_is_primary_war_leader",s.primaryLeader());
                if(s.opponent()==null)row.putNull("primary_opponent_character_id");else row.put("primary_opponent_character_id",s.opponent());
                var ids=row.putArray("targeted_title_ids");s.targetedTitleIds().forEach(ids::add);
            }
        }
        return n;
    }
    public static Plan decode(JsonNode n) {
        closed(n,"schema","classification","rule_id","ordinary_gold_ready","selected_action","required_step","required_tool",
                "blocked_reasons","war_id","prisoner_id","quoted_gold_raw","original_war_signature");
        eq(n,"schema",SCHEMA);
        Classification classification=null;
        for(Classification value:Classification.values())if(value.key().equals(text(n,"classification")))classification=value;
        need(classification!=null,"known policy classification required");
        String rawAction=nullableText(n,"selected_action");Action action=null;
        if(rawAction!=null) { for(Action value:Action.values())if(value.key().equals(rawAction))action=value;need(action!=null,"exact known reply action required"); }
        List<String> reasons=list(n,"blocked_reasons",128,value->{need(value.isTextual()&&!value.textValue().isEmpty(),"exact blocker text required");return value.textValue();});
        Integer war=nullableInt32(n,"war_id");if(war!=null)need(war>0,"positive selected WarID required");
        Long prisoner=nullableId(n,"prisoner_id");if(prisoner!=null)need(prisoner>0,"positive selected prisoner required");
        BigInteger gold=field(n,"quoted_gold_raw").isNull()?null:number(n,"quoted_gold_raw",BigInteger.ZERO,I64_MAX);
        Optional<List<WarSignature>> signature=Optional.empty();
        if(!field(n,"original_war_signature").isNull()) {
            ObjectNode snapshot=F.objectNode();snapshot.set("active_wars",field(n,"original_war_signature").deepCopy());
            signature=KnownPendingInteractionEvidence.warSignature(snapshot);need(signature.isPresent(),"stored complete war signature required");
        }
        Plan result=new Plan(classification,text(n,"rule_id"),Optional.ofNullable(action),
                Optional.ofNullable(nullableText(n,"required_step")),Optional.ofNullable(nullableText(n,"required_tool")),reasons,
                Optional.ofNullable(war),Optional.ofNullable(prisoner),Optional.ofNullable(gold),signature,bool(n,"ordinary_gold_ready"));
        if(action!=null) {
            switch(classification) {
                case KNOWN_MARRIAGE,KNOWN_GRANT_VASSAL,KNOWN_CALL_ALLY -> need(action==Action.REJECT,"known reject-only policy cannot accept");
                case KNOWN_NEGOTIATE_ALLIANCE,KNOWN_PERK_ALLIANCE,KNOWN_RECEIVED_RANSOM,KNOWN_WAR_EXIT ->
                    need(action==Action.ACCEPT,"known acceptance policy must preserve its exact action");
                case EVIDENCE_INVALID,DEFINITION_UNCLASSIFIED,SPECIAL_UNCLASSIFIED -> throw new IllegalArgumentException("unclassified plan cannot submit a known reply");
                case EXPLICIT_NATIVE_REPLY -> need(result.ruleId().equals("explicit-native-reply-v1"),"explicit Native reply must retain its explicit operator scope");
                default -> { }
            }
        }
        return result;
    }
    private static void string(ObjectNode n,String key,Optional<String> value) {
        if(value.isPresent())n.put(key,value.orElseThrow());else n.putNull(key);
    }
}

