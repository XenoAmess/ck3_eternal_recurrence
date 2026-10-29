package org.xar.ck3.control.nativebridge.capabilities.interactions;

import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.need;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.planning.warexit.WarExitEvidence;
import org.xar.ck3.control.application.planning.warexit.WarExitInboundProvider;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleaseCollectionProjection12003;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

/**
 * The original strategy.py 1319..3550 bounded player reply policy.
 * Native legality is an input, never a claim of complete native AI or material effect.
 * An unavailable known strategy remains known; a generic left reply must not replace it.
 */
public final class KnownPendingInteractionRules {
    private KnownPendingInteractionRules() { }
    public enum Action {
        ACCEPT("accept"), REJECT("reject"), ACKNOWLEDGE("acknowledge");
        private final String key;
        Action(String key) { this.key=key; }
        public String key() { return key; }
        public String step() { return key+"-pending-character-interaction"; }
    }
    public enum Classification {
        EVIDENCE_INVALID("evidence_invalid"), KNOWN_WAR_EXIT("known_war_exit"),
        KNOWN_MARRIAGE("known_marriage_special"), KNOWN_GRANT_VASSAL("known_grant_vassal_reject_only"),
        KNOWN_NEGOTIATE_ALLIANCE("known_negotiate_alliance_inbound"),
        KNOWN_PERK_ALLIANCE("known_perk_alliance_inbound"), KNOWN_CALL_ALLY("known_call_ally_busy_reject"),
        KNOWN_RECEIVED_RANSOM("known_received_ransom"), ORDINARY("ordinary_non_war"),
        DEFINITION_UNCLASSIFIED("definition_unclassified"), SPECIAL_UNCLASSIFIED("unclassified_or_special"),
        EXPLICIT_NATIVE_REPLY("explicit_native_reply");
        private final String key;
        Classification(String key) { this.key=key; }
        public String key() { return key; }
        public boolean dedicated() {
            return this!=DEFINITION_UNCLASSIFIED && this!=SPECIAL_UNCLASSIFIED && this!=EXPLICIT_NATIVE_REPLY;
        }
    }
    /** Exact stable signature used by the Python no-new-war postcondition, including observed nulls. */
    public record WarSignature(int warId, WarExitEvidence.Side side, Boolean primaryLeader,
            Integer opponent, int score, List<Integer> targetedTitleIds) {
        public WarSignature {
            need(warId>0,"positive full WarID required"); Objects.requireNonNull(side);
            need(opponent==null || opponent>=0,"observed opponent must preserve null or nonnegative ID");
            targetedTitleIds=List.copyOf(targetedTitleIds);
            targetedTitleIds.forEach(id->need(id>=0,"nonnegative full target title required"));
        }
    }
    public record Input(PendingContext context, Context held, List<WarExitEvidence.War> activeWars,
            Optional<List<WarSignature>> warSignature, Optional<ReleaseCollectionProjection12003.Observation> prisoners,
            Optional<WarExitInboundProvider.Result> inboundTerms, Set<String> availableSteps) {
        public Input {
            Objects.requireNonNull(context); Objects.requireNonNull(held); activeWars=List.copyOf(activeWars);
            warSignature=Objects.requireNonNull(warSignature).map(List::copyOf);
            Objects.requireNonNull(prisoners); Objects.requireNonNull(inboundTerms);
            availableSteps=Set.copyOf(availableSteps);
        }
    }
    public record Plan(Classification classification, String ruleId, Optional<Action> selected,
            Optional<String> requiredStep, Optional<String> requiredTool, List<String> blockedReasons,
            Optional<Integer> warId, Optional<Long> prisonerId, Optional<BigInteger> quotedGoldRaw,
            Optional<List<WarSignature>> originalWarSignature, boolean ordinaryGoldReady) {
        public Plan {
            Objects.requireNonNull(classification); need(ruleId!=null&&!ruleId.isEmpty(),"named policy rule required");
            Objects.requireNonNull(selected); Objects.requireNonNull(requiredStep); Objects.requireNonNull(requiredTool);
            blockedReasons=List.copyOf(blockedReasons); Objects.requireNonNull(warId); Objects.requireNonNull(prisonerId);
            Objects.requireNonNull(quotedGoldRaw); originalWarSignature=Objects.requireNonNull(originalWarSignature).map(List::copyOf);
            need(selected.isEmpty() || blockedReasons.isEmpty(),"blocked known policy cannot authorize a reply");
            need(!ordinaryGoldReady || selected.equals(Optional.of(Action.ACCEPT)),"gold readiness is local to actual accept");
            if(classification==Classification.EXPLICIT_NATIVE_REPLY)
                need(ruleId.equals("explicit-native-reply-v1")&&selected.isPresent()&&requiredStep.isEmpty()&&requiredTool.isEmpty()
                        &&warId.isEmpty()&&prisonerId.isEmpty()&&quotedGoldRaw.isEmpty()&&originalWarSignature.isEmpty()&&!ordinaryGoldReady,
                        "explicit operator reply grants only an independent pending lifecycle observation");
        }
        public String phase() {
            if(requiredStep.filter(value->value.startsWith("query-war-termination-options-")).isPresent())
                return "pending_raiktor_white_peace_termination_query";
            if(selected.isEmpty()) return classification==Classification.KNOWN_WAR_EXIT
                    ?"pending_war_interaction_evidence_required"
                    :classification==Classification.KNOWN_CALL_ALLY?"pending_call_ally_busy_reject_blocked"
                    :"pending_character_interaction_degraded_blocked";
            if(selected.orElseThrow()==Action.ACKNOWLEDGE)return "pending_character_interaction_acknowledge";
            return switch(classification) {
                case KNOWN_MARRIAGE -> "pending_arrange_marriage_reject_only";
                case KNOWN_GRANT_VASSAL -> "pending_grant_vassal_reject_only";
                case KNOWN_NEGOTIATE_ALLIANCE -> "pending_negotiate_alliance_accept";
                case KNOWN_PERK_ALLIANCE -> "pending_perk_alliance_accept";
                case KNOWN_CALL_ALLY -> "pending_call_ally_busy_reject";
                case KNOWN_RECEIVED_RANSOM -> "pending_received_ransom_ordinary_gold_accept";
                case KNOWN_WAR_EXIT -> "pending_raiktor_white_peace_accept";
                default -> selected.orElseThrow()==Action.REJECT?"pending_character_interaction_degraded_reject"
                        :"pending_character_interaction_degraded_unique_accept";
            };
        }
    }
    private static final Set<String> ORDINARY=Set.of("demand_hostage_interaction","spar_with_knight_interaction",
            "pay_ransom_interaction","ransom_interaction");
    private static final Set<String> WAR_EXIT=Set.of("end_war_attacker_victory_interaction",
            "end_war_attacker_white_peace_interaction","end_war_attacker_defeat_interaction");

    public static Plan evaluate(Input input) {
        PendingContext c=input.context(); List<String> blocked=new ArrayList<>();
        if(c.status()!=PendingContext.Status.AVAILABLE)
            return result(Classification.EVIDENCE_INVALID,"ordinary-reject-unique-accept-v1",null,
                    List.of("context_not_available"),input);
        if(!c.frame().revision().equals(input.held().revision()) || !c.frame().date().equals(input.held().date())
                || !c.frame().actor().equals(input.held().actor()) || c.frame().build()!=input.held().build()
                || input.held().controls().pending()==null
                || !c.instance().equals(input.held().controls().pending().instance())
                || !input.held().controls().paused())
            return result(Classification.EVIDENCE_INVALID,"ordinary-reject-unique-accept-v1",null,
                    List.of("same_paused_frame_binding_unavailable"),input);
        String key=c.definition().key();
        Classification classification=classify(c);
        String rule=rule(classification);
        switch(classification) {
            case KNOWN_MARRIAGE -> {
                PendingContext.Roles r=c.roles();
                if(r.actor()<=0 || r.recipient()<=0 || r.secondaryActor()<=0 || r.secondaryRecipient()<=0)
                    blocked.add("marriage_roles_unavailable");
                if(r.intermediary()!=-1)blocked.add("marriage_direct_recipient_route_required");
                direct(c,"marriage_direct_local_recipient_route_mismatch",blocked);
                deadline(c,60,false,"marriage_unexpired_deadline_shape_mismatch",blocked);
                if(!c.terms().specialDataPresent() || c.terms().war().available()
                        || c.terms().war().value()!=null || !"special_interaction_subtype_opaque".equals(c.terms().war().reason()))
                    blocked.add("marriage_special_payload_shape_mismatch");
                options(c,false,6,"marriage_zero_option_vector_mismatch",blocked);
                normalReply(c,"marriage_normal_reply_channel_mismatch",blocked);
                if(!blocked.isEmpty())return result(classification,rule,null,blocked,input);
                return legal(input,classification,rule,Action.REJECT,"marriage_reject_not_native_legal",
                        "legal_marriage_reject_command_unavailable");
            }
            case KNOWN_GRANT_VASSAL -> {
                boolean crozier3=c.frame().build()==Build.CROZIER3;
                if(c.definition().deterministicHash()!=1_006_648_858L || c.definition().runtimeOrdinal()!=(crozier3?296:277))
                    blocked.add("grant_vassal_exact_definition_mismatch");
                PendingContext.Roles r=c.roles();
                if(r.actor()<=0 || r.recipient()<=0 || r.secondaryActor()<=0
                        || r.actor()==r.recipient() || r.actor()==r.secondaryActor() || r.recipient()==r.secondaryActor()
                        || r.secondaryRecipient()!=-1 || r.intermediary()!=-1
                        || !BigInteger.valueOf(r.recipient()).equals(c.frame().actor()))
                    blocked.add("grant_vassal_direct_three_role_binding_mismatch");
                direct(c,"grant_vassal_direct_local_reply_mismatch",blocked);
                deadline(c,60,false,"grant_vassal_unexpired_deadline_mismatch",blocked);
                options(c,true,0,"grant_vassal_zero_send_options_mismatch",blocked);
                nonSpecial(c,"grant_vassal_nonwar_special_binding_mismatch",blocked);
                normalReply(c,"grant_vassal_normal_reply_channel_mismatch",blocked);
                if(!blocked.isEmpty())return result(classification,rule,null,blocked,input);
                return legal(input,classification,rule,Action.REJECT,"grant_vassal_reject_not_native_legal",
                        "grant_vassal_reject_command_unavailable");
            }
            case KNOWN_NEGOTIATE_ALLIANCE, KNOWN_PERK_ALLIANCE -> {
                boolean perk=classification==Classification.KNOWN_PERK_ALLIANCE;
                String prefix=perk?"perk_alliance":"negotiate_alliance";
                if(perk&&(c.definition().deterministicHash()!=328_040_944L || c.definition().runtimeOrdinal()!=4))
                    blocked.add(prefix+"_definition_identity_mismatch");
                basicDirectRoles(c,prefix+"_direct_roles_mismatch",blocked);
                direct(c,prefix+"_direct_local_route_mismatch",blocked);
                deadline(c,60,!perk,prefix+(perk?"_unexpired_deadline_mismatch":"_same_day_deadline_shape_mismatch"),blocked);
                nonSpecial(c,prefix+"_non_special_shape_mismatch",blocked);
                options(c,false,2,prefix+"_zero_option_vector_mismatch",blocked);
                if(perk) {
                    if(!completeWarScope(input)||!input.activeWars().isEmpty())blocked.add("perk_alliance_no_active_war_required");
                } else {
                    if(input.activeWars().stream().noneMatch(w->w.playerSide()==WarExitEvidence.Side.DEFENDER&&w.primaryLeader()))
                        blocked.add("negotiate_alliance_active_defensive_war_required");
                    if(input.activeWars().stream().anyMatch(w->w.opponent().filter(id->id==c.roles().actor()).isPresent()))
                        blocked.add("negotiate_alliance_actor_is_active_war_opponent");
                }
                addLegal(input,Action.ACCEPT,prefix+"_accept_not_native_legal",prefix+"_accept_command_unavailable",blocked);
                return result(classification,rule,blocked.isEmpty()?Action.ACCEPT:null,blocked,input);
            }
            case KNOWN_CALL_ALLY -> {
                // Python explicitly freezes this player counter-policy to 1.19.0.6.
                // The .4 reader being available does not migrate this eligibility.
                if(c.frame().build()!=Build.WANDERER6 || c.sourcePins().stream().noneMatch(pin->pin.name().equals("backend_id")
                        && pin.rvaOrIdentity().equals("ck3-1.19.0.6-native-pending-character-interaction-context-v1")))
                    blocked.add("call_ally_frozen_exact_build_mismatch");
                if(c.definition().deterministicHash()!=936_306_703L)blocked.add("call_ally_definition_identity_mismatch");
                basicDirectRoles(c,"call_ally_direct_roles_mismatch",blocked);
                direct(c,"call_ally_direct_local_route_mismatch",blocked);
                if(!c.target().present() || !"war".equals(c.target().typeKey()))
                    blocked.add("call_ally_stable_war_target_type_mismatch");
                // Do not decode or consume the target's raw token or typed WarID.
                options(c,true,0,"call_ally_zero_option_vector_mismatch",blocked);
                nonSpecial(c,"call_ally_non_special_shape_mismatch",blocked);
                deadline(c,null,false,"call_ally_unexpired_deadline_required",blocked);
                if(input.warSignature().isEmpty() || input.warSignature().orElseThrow().isEmpty())
                    blocked.add("call_ally_existing_active_war_required");
                if(input.activeWars().stream().anyMatch(w->w.score().filter(score->score>=100).isPresent()))
                    blocked.add("call_ally_enforce_demands_priority_not_cleared");
                addLegal(input,Action.REJECT,"call_ally_reject_not_native_legal","call_ally_reject_command_unavailable",blocked);
                return result(classification,rule,blocked.isEmpty()?Action.REJECT:null,blocked,input);
            }
            case KNOWN_RECEIVED_RANSOM -> { return ransom(input); }
            case KNOWN_WAR_EXIT -> { return whitePeace(input); }
            case DEFINITION_UNCLASSIFIED -> blocked.add("interaction_definition_not_explicitly_classified_nonwar_nonreligious");
            case SPECIAL_UNCLASSIFIED -> blocked.add("interaction_war_or_special_semantics_unclassified");
            case EVIDENCE_INVALID -> blocked.add("context_not_available");
            case EXPLICIT_NATIVE_REPLY -> blocked.add("explicit_reply_is_not_an_automatic_policy_classification");
            case ORDINARY -> {
                if(c.legality().reject().available()&&c.legality().reject().allowed())
                    return legal(input,classification,rule,Action.REJECT,"reject_not_legal","legal_reject_command_unavailable");
                boolean rejectIllegal=c.legality().reject().available()&&!c.legality().reject().allowed();
                boolean othersIllegal=c.legality().block().available()&&!c.legality().block().allowed()
                        &&c.legality().acknowledge().available()&&!c.legality().acknowledge().allowed();
                if(rejectIllegal&&c.legality().accept().available()&&c.legality().accept().allowed()&&othersIllegal)
                    return legal(input,classification,rule,Action.ACCEPT,"accept_not_legal","unique_legal_accept_command_unavailable");
                if(!rejectIllegal)blocked.add("reject_not_proven_illegal");
                if(!c.legality().accept().available()||!c.legality().accept().allowed())blocked.add("accept_not_legal");
                if(!othersIllegal)blocked.add("accept_not_unique_legal_reply");
            }
        }
        return result(classification,rule,null,blocked,input);
    }

    public static Classification classify(PendingContext c) {
        if(c.status()!=PendingContext.Status.AVAILABLE)return Classification.EVIDENCE_INVALID;
        String key=c.definition().key();
        if(c.terms().war().available())return Classification.KNOWN_WAR_EXIT;
        if(key.equals("arrange_marriage_interaction"))return Classification.KNOWN_MARRIAGE;
        if(key.equals("grant_vassal_interaction"))return Classification.KNOWN_GRANT_VASSAL;
        boolean plain=!c.terms().specialDataPresent()&&!c.terms().war().available()
                &&"special_war_binding_not_applicable".equals(c.terms().war().reason());
        if(key.equals("negotiate_alliance_interaction")&&plain)return Classification.KNOWN_NEGOTIATE_ALLIANCE;
        if(key.equals("perk_alliance_interaction"))return Classification.KNOWN_PERK_ALLIANCE;
        if(key.equals("call_ally_interaction"))return Classification.KNOWN_CALL_ALLY;
        if(key.equals("pay_ransom_interaction")||key.equals("ransom_me_interaction"))return Classification.KNOWN_RECEIVED_RANSOM;
        if(plain&&!WAR_EXIT.contains(key)&&ORDINARY.contains(key))return Classification.ORDINARY;
        return plain?Classification.DEFINITION_UNCLASSIFIED:Classification.SPECIAL_UNCLASSIFIED;
    }
    private static Plan ransom(Input input) {
        PendingContext c=input.context(); List<String> blocked=new ArrayList<>(); String required=null,tool=null;
        PendingContext.Ransom quote=c.terms().ransom().filter(PendingContext.Ransom::available).orElse(null);
        if(quote==null || !quote.ordinaryGoldReady().orElse(false) || quote.goldRaw()==null || quote.goldRaw().signum()<=0
                || !Set.of("gold","current_gold").contains(quote.optionKey())) {
            blocked.add("received_ransom_positive_ordinary_gold_input_unavailable"); required=PendingContextCodec.STEP;
        }
        Long prisonerId=quote==null?null:quote.prisoner()==null?null:quote.prisoner().longValue();
        if(input.prisoners().isEmpty()) {
            blocked.add("received_ransom_same_frame_prisoner_metadata_required");
            tool="ck3_query_player_prisoner_collection_private_v1";
        } else {
            List<ReleaseCollectionProjection12003.Row> rows=input.prisoners().orElseThrow().rows().stream()
                    .filter(row->prisonerId!=null&&row.prisonerCharacterId()==prisonerId).toList();
            if(rows.size()!=1)blocked.add("received_ransom_prisoner_not_in_current_collection");
            else {
                var row=rows.getFirst();
                if(!(row.lineage() instanceof ReleaseCollectionProjection12003.MeasuredLineage lineage)
                        || lineage.sameHouse() || lineage.sameDynasty()
                        || !(row.childRelation() instanceof ReleaseCollectionProjection12003.MeasuredChildRelation child)
                        || child.childOfPlayedCharacter()
                        || !(row.primaryTitleTier() instanceof ReleaseCollectionProjection12003.MeasuredTitleTier))
                    blocked.add("received_ransom_prisoner_qualification_failed");
            }
        }
        if(!completeWarScope(input)||!input.activeWars().isEmpty())blocked.add("received_ransom_no_war_hostage_input_required");
        addLegal(input,Action.ACCEPT,"received_ransom_accept_not_native_legal","received_ransom_accept_command_unavailable",blocked);
        return new Plan(Classification.KNOWN_RECEIVED_RANSOM,"received-ransom-ordinary-gold-v1",
                blocked.isEmpty()?Optional.of(Action.ACCEPT):Optional.empty(),Optional.ofNullable(required),Optional.ofNullable(tool),blocked,
                Optional.empty(),Optional.ofNullable(prisonerId),quote==null?Optional.empty():Optional.ofNullable(quote.goldRaw()),
                input.warSignature(),blocked.isEmpty());
    }
    private static Plan whitePeace(Input input) {
        PendingContext c=input.context(); PendingContext.War binding=c.terms().war().value(); List<String> blocked=new ArrayList<>();
        String rule="ordinary-reject-unique-accept-v1";
        if(binding==null || !c.definition().key().equals("end_war_attacker_white_peace_interaction")
                || !binding.kind().equals("end_war_white_peace_interaction") || !binding.absoluteOutcome().equals("white_peace")
                || !binding.actorRole().equals("primary_defender") || !binding.recipientRole().equals("primary_attacker"))
            return result(Classification.KNOWN_WAR_EXIT,rule,null,List.of("special_outcome_terms_unavailable"),input);
        rule="raiktor-inbound-white-peace-v1";
        List<WarExitEvidence.War> wars=input.activeWars().stream().filter(w->w.warId()==binding.warId()).toList();
        boolean match=wars.stream().anyMatch(w->w.playerSide()==WarExitEvidence.Side.ATTACKER&&w.primaryLeader()
                &&w.opponent().filter(id->id==c.roles().actor()).isPresent());
        if(!match)blocked.add("special_war_snapshot_binding_mismatch");
        if(c.roles().secondaryActor()!=-1 || c.roles().secondaryRecipient()!=-1 || c.roles().intermediary()!=-1)
            blocked.add("raiktor_white_peace_hostage_or_intermediary_present");
        if(wars.size()!=1 || wars.getFirst().playerSide()!=WarExitEvidence.Side.ATTACKER || !wars.getFirst().primaryLeader()
                || wars.getFirst().score().filter(score->score>=0&&score<100).isEmpty())
            blocked.add("raiktor_white_peace_active_war_shape_mismatch");
        if(!blocked.isEmpty())return result(Classification.KNOWN_WAR_EXIT,rule,null,blocked,input);
        if(input.inboundTerms().isEmpty() || input.inboundTerms().orElseThrow() instanceof WarExitInboundProvider.NeedRead) {
            String query="query-war-termination-options-"+binding.warId();
            if(!input.availableSteps().contains(query))blocked.add("raiktor_white_peace_termination_query_unavailable");
            return new Plan(Classification.KNOWN_WAR_EXIT,rule,Optional.empty(),Optional.of(query),Optional.empty(),blocked,
                    Optional.of(binding.warId()),Optional.empty(),Optional.empty(),input.warSignature(),false);
        }
        if(!(input.inboundTerms().orElseThrow() instanceof WarExitInboundProvider.Current current)
                || !current.before().equals(input.held().before()) || current.warId()!=binding.warId())
            blocked.add("special_war_snapshot_binding_mismatch");
        else {
            WarExitEvidence.Options options=current.options();
            if(options.playerSide()!=WarExitEvidence.Side.ATTACKER || !options.primaryLeader()
                    || options.score()!=wars.getFirst().score().orElseThrow()
                    || options.durationDays().filter(days->days>=365).isEmpty() || !options.cbPresent()
                    || options.cbKey().filter("raiktor_claim_cb"::equals).isEmpty() || !options.allowsWhitePeace()
                    || options.whitePeace().outcome()!=WarExitEvidence.Outcome.WHITE_PEACE
                    || !options.whitePeace().hostageVariant().equals("none"))
                blocked.add("raiktor_white_peace_termination_terms_mismatch");
        }
        addLegal(input,Action.ACCEPT,"raiktor_white_peace_accept_not_native_legal","raiktor_white_peace_accept_command_unavailable",blocked);
        return new Plan(Classification.KNOWN_WAR_EXIT,rule,blocked.isEmpty()?Optional.of(Action.ACCEPT):Optional.empty(),
                Optional.empty(),Optional.empty(),blocked,Optional.of(binding.warId()),Optional.empty(),Optional.empty(),input.warSignature(),false);
    }
    private static Plan legal(Input i,Classification c,String rule,Action action,String illegal,String unavailable) {
        List<String> blocked=new ArrayList<>(); addLegal(i,action,illegal,unavailable,blocked);
        return result(c,rule,blocked.isEmpty()?action:null,blocked,i);
    }
    /** A filtered projection cannot turn an unknown/malformed native war row into peace. */
    private static boolean completeWarScope(Input input) {
        if(input.warSignature().isEmpty())return false;
        List<WarSignature> signature=input.warSignature().orElseThrow();
        if(signature.size()!=input.activeWars().size())return false;
        Set<Integer> expected=new java.util.HashSet<>();
        for(WarSignature row:signature)if(!expected.add(row.warId()))return false;
        Set<Integer> actual=new java.util.HashSet<>();
        for(WarExitEvidence.War row:input.activeWars())if(!actual.add(row.warId()))return false;
        return expected.equals(actual);
    }
    private static void addLegal(Input i,Action action,String illegal,String unavailable,List<String> blocked) {
        PendingContext.Legal legal=switch(action) {
            case ACCEPT -> i.context().legality().accept(); case REJECT -> i.context().legality().reject();
            case ACKNOWLEDGE -> i.context().legality().acknowledge();
        };
        if(!legal.available()||!legal.allowed())blocked.add(illegal);
        else if(!i.availableSteps().contains(action.step()))blocked.add(unavailable);
    }
    private static Plan result(Classification classification,String rule,Action selected,List<String> blocked,Input i) {
        return new Plan(classification,rule,Optional.ofNullable(selected),Optional.empty(),Optional.empty(),blocked,
                Optional.empty(),Optional.empty(),Optional.empty(),i.warSignature(),false);
    }
    private static String rule(Classification classification) {
        return switch(classification) {
            case KNOWN_MARRIAGE -> "arrange-marriage-reject-only-v1";
            case KNOWN_GRANT_VASSAL -> "grant-vassal-reject-only-v1";
            case KNOWN_NEGOTIATE_ALLIANCE -> "negotiate-alliance-inbound-accept-v1";
            case KNOWN_PERK_ALLIANCE -> "perk-alliance-inbound-accept-v1";
            case KNOWN_CALL_ALLY -> "call-ally-busy-reject-v1";
            default -> "ordinary-reject-unique-accept-v1";
        };
    }
    private static void basicDirectRoles(PendingContext c,String reason,List<String> gaps) {
        PendingContext.Roles r=c.roles();
        if(r.actor()<=0 || r.recipient()<=0 || r.actor()==r.recipient()
                || r.secondaryActor()!=-1 || r.secondaryRecipient()!=-1 || r.intermediary()!=-1)gaps.add(reason);
    }
    private static void direct(PendingContext c,String reason,List<String> gaps) {
        PendingContext.Routing r=c.routing();
        if(r.kind()!=0 || !r.responderRole().equals("recipient") || !r.replyChannel().equals("recipient")
                || r.autoAcceptNotification() || r.player()!=c.roles().recipient())gaps.add(reason);
    }
    private static void deadline(PendingContext c,Integer exactExpiration,boolean sameDay,String reason,List<String> gaps) {
        PendingContext.Deadline d=c.deadline();
        if((exactExpiration!=null&&d.expiration()!=exactExpiration) || d.age()<0 || d.age()>=d.expiration()
                || d.remaining()!=d.expiration()-d.age() || d.remaining()<=0 || !d.boundary().equals("not_reached")
                || sameDay&&d.age()!=0)gaps.add(reason);
    }
    private static void options(PendingContext c,boolean exclusive,int count,String reason,List<String> gaps) {
        PendingContext.Options options=c.options();
        if(options.exclusive()!=exclusive || options.count()!=count || options.rows().size()!=count) { gaps.add(reason);return; }
        for(int n=0;n<count;n++)if(options.rows().get(n).nativeIndex()!=n || options.rows().get(n).selected()) { gaps.add(reason);return; }
    }
    private static void nonSpecial(PendingContext c,String reason,List<String> gaps) {
        if(c.terms().specialDataPresent() || c.terms().war().available() || c.terms().war().value()!=null
                || !"special_war_binding_not_applicable".equals(c.terms().war().reason()))gaps.add(reason);
    }
    private static void normalReply(PendingContext c,String reason,List<String> gaps) {
        PendingContext.Legal a=c.legality().acknowledge();
        if(!a.available() || a.allowed() || !"normal_reply_channel".equals(a.reason()))gaps.add(reason);
    }
}

