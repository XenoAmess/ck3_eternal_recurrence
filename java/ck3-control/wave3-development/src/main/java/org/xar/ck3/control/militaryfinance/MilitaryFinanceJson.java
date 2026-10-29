package org.xar.ck3.control.militaryfinance;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionCodec;

/** Output boundary for a typed internal research result; it adds no unvalidated input route. */
public final class MilitaryFinanceJson {
    public static final String SCHEMA = "xar.military-finance-research.v1";
    private MilitaryFinanceJson() { }
    public static byte[] encode(MilitaryFinanceResearch.Assessment assessment) {
        ObjectNode out = StrictJson.object(); out.put("schema", SCHEMA);
        out.put("game_version", MilitaryFinanceResearch.VERSION); out.put("executable_sha256", MilitaryFinanceResearch.EXE_SHA256);
        out.set("construction_decision", StrictJson.parse(WartimeConstructionCodec.encode(assessment.constructionDecision())));
        out.put("full_native_ai_chooser_reconstructed", false);
        var offers = out.putArray("offers");
        for (var offer : assessment.offers()) {
            ObjectNode row = offers.addObject(); row.set("company_id", numberRead(offer.companyId()));
            row.put("native_legality", offer.nativeLegality().name());
            if (offer.nativePayment().isPresent()) row.put("native_payment_status", offer.nativePayment().orElseThrow().raw());
            else row.putNull("native_payment_status");
            ObjectNode afford = row.putObject("generic_can_afford"); afford.put("presence", offer.genericCanAfford().presence().name());
            if (offer.genericCanAfford().known()) afford.put("value", offer.genericCanAfford().value()); else afford.putNull("value");
            row.put("shared_reserve_quote_usable", offer.sharedReserveQuoteUsable());
            optional(row, "native_contract_months", offer.nativeContractMonths());
            if (offer.conditionalCounts().isPresent()) {
                var counts = offer.conditionalCounts().orElseThrow(); ObjectNode c = row.putObject("conditional_counts");
                c.put("war_id", counts.warId()); c.put("scope", counts.scope().name());
                c.put("player", counts.player()); c.put("enemy", counts.enemy()); c.put("company_soldiers", counts.companySoldiers());
                c.put("after_company_arrival", counts.afterCompanyArrival()); c.put("observed_deficit", counts.observedDeficit());
                c.put("closes_observed_headcount_deficit", counts.closesObservedHeadcountDeficit());
                c.put("effective_combat_strength_or_win_probability", false);
            } else row.putNull("conditional_counts");
            ObjectNode arrival = row.putObject("arrival"); arrival.put("kind", offer.arrival().kind().name());
            optional(arrival, "actual_army_id", offer.arrival().actualArmyId());
            optional(arrival, "destination_province", offer.arrival().destinationProvince());
            optional(arrival, "native_forecast_days", offer.arrival().forecastDays());
            arrival.put("actual_arrival_verified", false); arrival.put("arrival_before_loss_guaranteed", false);
            row.putNull("battle_win_probability"); reasons(row, offer.reasons());
        }
        var funding = assessment.funding(); ObjectNode f = out.putObject("funding");
        f.put("need", funding.need().name()); f.put("loan_status", funding.loanStatus().name());
        f.put("cancellation_status", funding.cancellationStatus().name());
        f.put("unresolved_commitment_preserved", funding.unresolvedCommitmentPreserved());
        f.put("funding_credit_raw", 0); f.put("new_procurement_epoch_opened", false); f.put("action_submission_qualified", false);
        f.putNull("refund_quote_raw"); f.putNull("loan_principal_quote_raw"); reasons(f, funding.reasons());
        return StrictJson.canonical(out, StrictJson.EXPLICIT_MAX_BYTES);
    }
    public static ObjectNode encode(VanillaWarChestCaller12003.Projection projection) {
        ObjectNode out = StrictJson.object(); out.put("schema", "xar.vanilla-war-chest-caller12003-reference.v1");
        out.put("game_version", "1.20.0.3"); out.put("executable_sha256", VanillaWarChestCaller12003.EXE_SHA256);
        out.put("caller_start_rva", "0x19EA9C0"); out.put("caller_end_rva", "0x19EADA5");
        out.put("held_assembly_sha256", VanillaWarChestCaller12003.SOURCE_SHA256); out.put("branch", projection.branch().name());
        if (projection.goldTreasuryRatioRaw() == null) out.putNull("gold_treasury_ratio_raw"); else out.put("gold_treasury_ratio_raw", projection.goldTreasuryRatioRaw());
        var values = out.putArray("resource_targets_raw"); projection.resourceTargetsRaw().forEach(values::add);
        out.put("scale", 100000); out.put("current12004_qualified", false); out.put("full_native_ai_choice_reconstructed", false);
        out.put("future_war_cost_upper_bound", false); return out;
    }
    private static JsonNode numberRead(GiftWarCashModel.Read<BigInteger> read) {
        ObjectNode out = StrictJson.object(); out.put("presence", read.presence().name());
        if (read.known()) out.put("value", read.value()); else out.putNull("value"); return out;
    }
    private static void optional(ObjectNode out, String field, Optional<BigInteger> value) {
        if (value.isPresent()) out.put(field, value.orElseThrow()); else out.putNull(field);
    }
    private static void reasons(ObjectNode out, List<MilitaryFinanceResearch.Reason> reasons) {
        var values = out.putArray("reasons"); reasons.forEach(reason -> values.add(reason.name()));
    }
}
