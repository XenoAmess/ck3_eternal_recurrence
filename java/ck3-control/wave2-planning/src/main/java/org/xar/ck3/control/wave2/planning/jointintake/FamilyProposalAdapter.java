package org.xar.ck3.control.wave2.planning.jointintake;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.wave2.planning.jointintake.IntakeWire.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalCodec;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalProposals;
import org.xar.ck3.control.wave2.planning.jointintake.IntakeModel.Frame;

/** Real family producer adapters; owning family policy still determines approval and value. */
final class FamilyProposalAdapter {
    private FamilyProposalAdapter() { }
    static Obj adapt(Frame frame, Obj plan) {
        if (new Text(BetrothalProposals.SUBMIT_STEP).equals(plan.get("selected_step"))) {
            byte[] request = OpportunityJson.encode(obj(f("schema", new Text(BetrothalCodec.ADAPT_SCHEMA)), f("frame", frameNode(frame)), f("plan", plan)));
            return OpportunityJson.object(OpportunityJson.parse(BetrothalCodec.encodeOpportunity(BetrothalProposals.adapt(BetrothalCodec.decodeAdapt(request)))), "betrothal opportunity");
        }
        equalsValue(plan.get("selected_step"), new Text("submit-observed-first-heir-marriage-v1-private"), "first-heir formal step");
        Obj choice = object(plan.get("family_marriage_choice"), "family choice"), legality = object(plan.get("family_marriage_legality"), "family legality"), diagnostic = object(plan.get("family_marriage_private_diagnostic"), "family diagnostic");
        equalsValue(legality.get("status"), new Text("available"), "family legal status");
        for (Obj row : List.of(legality, diagnostic)) equalsValue(row.get("native_revision"), number(frame.nativeRevision()), "family native revision");
        equalsValue(diagnostic.get("date_raw"), number(frame.dateRaw()), "family date"); equalsValue(diagnostic.get("episode_run_id"), new Text(frame.episodeRunId()), "family episode");
        positive(legality.get("query_sequence"), "family legality sequence");
        equalsValue(diagnostic.get("legality_query_sequence"), legality.get("query_sequence"), "family legality sequence");
        BigInteger candidate = positive(choice.get("candidate_character_id"), "family candidate"); equalsValue(diagnostic.get("selected_candidate_character_id"), number(candidate), "family selected candidate");
        List<Value> rows = array(diagnostic.get("rows"), "family diagnostic rows"); require(rows.size() == 5, "five-row family proof required");
        Obj row = unique(rows, candidate), nativeRow = unique(array(legality.get("native_legal_candidates"), "legal candidates"), candidate);
        BigInteger actor = frame.playedCharacterId(), heir = positive(row.get("heir_character_id"), "family heir"), recipient = positive(row.get("recipient_character_id"), "family recipient");
        require(!heir.equals(actor) && !recipient.equals(actor) && !recipient.equals(heir) && !candidate.equals(actor) && !candidate.equals(heir), "family role collision");
        equalsValue(row.get("status"), new Text("available"), "family row status"); equalsValue(row.get("actor_character_id"), number(actor), "family actor");
        for (Obj proof : List.of(legality, diagnostic)) equalsValue(proof.get("observed_first_heir_character_id"), number(heir), "first heir binding");
        equalsValue(row.get("rejection_reasons"), new Arr(List.of()), "family rejection reasons"); equalsValue(row.get("heir_spouse_count"), number(BigInteger.ZERO), "heir spouse count");
        require(missingOrNull(row.get("heir_betrothed_character_id")) && missingOrNull(row.get("heir_primary_spouse_character_id")), "heir already partnered");
        equalsValue(row.get("grand_wedding_option_selected"), new Bool(false), "grand wedding");
        equalsValue(nativeRow.get("played_character_id"), number(actor), "native family actor"); equalsValue(nativeRow.get("subject_character_id"), number(heir), "native family subject");
        equalsValue(nativeRow.get("recipient_matchmaker_character_id"), number(recipient), "native family recipient");
        equalsValue(nativeRow.get("complete_can_send"), new Bool(true), "native can send"); equalsValue(nativeRow.get("recipient_answer_allows_send"), new Bool(true), "native answer allows send");
        BigInteger answer = integer(nativeRow.get("recipient_answer_status_raw"), "native recipient answer"); require(answer.equals(BigInteger.ZERO) || answer.equals(BigInteger.ONE), "unsupported recipient answer");
        BigInteger acceptance = positive(nativeRow.get("recipient_ai_accept_raw"), "native recipient acceptance"); equalsValue(choice.get("recipient_ai_accept_raw"), number(acceptance), "family acceptance changed");
        equalsValue(choice.get("predicted_outcome_if_accepted"), row.get("predicted_outcome_if_accepted"), "family outcome changed");
        boolean alliance = false;
        for (Value value : array(row.get("possible_alliance_pairs"), "family alliance pairs")) if (value instanceof Obj pair
                && number(actor).equals(pair.get("first_character_id")) && number(recipient).equals(pair.get("second_character_id"))
                && new Bool(false).equals(pair.get("already_allied")) && new Bool(true).equals(pair.get("both_have_realm_data"))
                && new Bool(true).equals(pair.get("would_attempt_if_accepted"))) alliance = true;
        String outcome = text(row.get("predicted_outcome_if_accepted"), "family outcome");
        String expectedValue = switch (outcome) {
            case "marriage" -> "unpartnered_first_heir_adult_marriage_opportunity";
            case "betrothal" -> alliance ? "bounded_first_heir_betrothal_and_realm_alliance_attempt" : "bounded_first_heir_external_dynasty_betrothal_opportunity";
            default -> throw new org.xar.ck3.control.contracts.projection.ProjectionDomainRejection("unsupported family outcome");
        };
        equalsValue(choice.get("value"), new Text(expectedValue), "family owning value changed"); equalsValue(choice.get("realm_alliance_attempt_if_accepted"), new Bool(alliance), "family alliance claim changed");
        List<String> unpriced = new ArrayList<>();
        for (Value value : array(choice.get("unpriced"), "family unpriced")) {
            require(value instanceof Text, "unpriced obligation text required"); unpriced.add(((Text) value).value());
        }
        require(new HashSet<>(unpriced).containsAll(Set.of("child_dynasty_result", "alliance_result", "alliance_war_obligation", "betrothal_break_cost")), "family long-term obligations absent");
        Value costs = presentOrNull(choice, "immediate_generic_costs");
        if (costs != Nil.INSTANCE) {
            Obj observed = object(costs, "family immediate costs"); equalsValue(row.get("generic_costs"), costs, "family immediate cost proof");
            equalsValue(observed.get("raw_scale"), number(BigInteger.valueOf(100000)), "family cost scale"); equalsValue(observed.get("payer_role"), new Text("actor"), "family cost payer");
            equalsValue(observed.get("application_timing"), new Text("on_send"), "family cost timing");
            for (String key : List.of("gold_raw", "treasury_or_gold_raw")) equalsValue(observed.get(key), number(BigInteger.ZERO), "ordinary family immediate gold");
            for (String key : List.of("prestige_raw", "piety_raw", "influence_raw")) integer(observed.get(key), key);
        }
        List<BigInteger> characters = new ArrayList<>(new HashSet<>(List.of(heir, candidate, recipient))); characters.sort(BigInteger::compareTo);
        return proposal(frame, "marriage:first-heir:" + heir + ":" + candidate + ":" + recipient, "marriage", "first-heir-marriage-formal-v1", BigInteger.ZERO, BigInteger.ZERO,
                Nil.INSTANCE, 0, List.of(), alliance ? List.of(recipient) : List.of(), characters, List.of("first-heir-marriage:" + heir), obj(f("heir_character_id", number(heir)),
                        f("candidate_character_id", number(candidate)), f("recipient_character_id", number(recipient)), f("predicted_outcome_if_accepted", new Text(outcome)), f("value", new Text(expectedValue)),
                        f("recipient_ai_accept_raw", number(acceptance)), f("heir_adult_measure_raw", presentOrNull(row, "heir_adult_measure_raw")), f("candidate_adult_measure_raw", presentOrNull(row, "candidate_adult_measure_raw")),
                        f("realm_alliance_attempt_if_accepted", new Bool(alliance)), f("alliance_established", Nil.INSTANCE), f("unpriced", strings(unpriced)), f("ordinary_marriage_immediate_gold_claim_raw", number(BigInteger.ZERO)),
                        f("immediate_generic_costs", costs), f("stock_prestige_piety_influence_cost", new Text(costs == Nil.INSTANCE ? "not_observed" : "observed_same_frame_unpriced_by_joint_selector"))), Nil.INSTANCE);
    }
    private static Obj unique(List<Value> values, BigInteger candidate) {
        List<Value> matches = values.stream().filter(value -> value instanceof Obj row && number(candidate).equals(row.get("candidate_character_id"))).toList();
        require(matches.size() == 1, "family candidate not unique in current proof"); return object(matches.getFirst(), "family row");
    }

    // Local input aliases deliberately leave shared parser/encoder and internal result invariants unmarked.
    private static void require(boolean condition, String reason) { IntakeWire.domain(condition, reason); }
    private static Obj object(Value value, String name) { return IntakeWire.inputObject(value, name); }
    private static List<Value> array(Value value, String name) { return IntakeWire.inputArray(value, name); }
    private static String text(Value value, String name) { return IntakeWire.inputText(value, name); }
    private static BigInteger integer(Value value, String name) { return IntakeWire.inputInteger(value, name); }
    private static BigInteger nonnegative(Value value, String name) { return IntakeWire.inputNonnegative(value, name); }
    private static boolean bool(Value value, String name) { return IntakeWire.inputBool(value, name); }
}
