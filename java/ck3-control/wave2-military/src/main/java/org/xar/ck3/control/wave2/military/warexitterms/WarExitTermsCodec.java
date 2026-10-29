package org.xar.ck3.control.wave2.military.warexitterms;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.warexitterms.WarExitTerms.Claim;
import org.xar.ck3.control.wave2.military.warexitterms.WarExitTerms.DecisionStatus;
import org.xar.ck3.control.wave2.military.warexitterms.WarExitTerms.Disposition;
import org.xar.ck3.control.wave2.military.warexitterms.WarExitTerms.GoldTransfer;
import org.xar.ck3.control.wave2.military.warexitterms.WarExitTerms.MonthlyGoldIncome;
import org.xar.ck3.control.wave2.military.warexitterms.WarExitTerms.Outcome;
import org.xar.ck3.control.wave2.military.warexitterms.WarExitTerms.PrisonerRelease;
import org.xar.ck3.control.wave2.military.warexitterms.WarExitTerms.RecipientResponse;
import org.xar.ck3.control.wave2.military.warexitterms.WarExitTerms.ResourceAmount;
import org.xar.ck3.control.wave2.military.warexitterms.WarExitTerms.ResourceKind;
import org.xar.ck3.control.wave2.military.warexitterms.WarExitTerms.Truce;

/** Exact complete-union v2 wire boundary, with no bean binding or numeric coercion. */
public final class WarExitTermsCodec {
    // A legal 4096-target payload fits within this bound; the legacy map default stays unchanged.
    public static final int MAX_BYTES = 1_048_576;
    static final Set<String> FIELDS = Set.of("schema_version", "status", "war_id", "date_raw", "casus_belli",
            "supported_slice", "player_side", "primary_attacker_character_id", "primary_defender_character_id",
            "claimant_character_id", "target_title_ids", "claims", "primary_resource_balances",
            "primary_monthly_gold_income", "outcomes", "readiness", "provenance");
    private static final Set<String> READINESS = Set.of("same_frame_stable", "claim_temporary_lifecycle_verified",
            "white_peace_complete", "attacker_defeat_complete", "exit_terms_ready");
    private static final String GAME_VERSION = "1.19.0.6";
    private static final String EXE = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
    private static final String CLAIM = "D9AA37BDC45F81B4F6185B2697A3EBD09404084EA0D3CF77BBE3C1D2C962E8B1";
    private static final String EFFECTS = "A936E09F448EF715580A918165EAB89A9368AD2D3014E425C998CD9D4F0E8D7D";
    private static final String VALUES = "ED1CDB6E8BC887CF1FFFE010F1E9CA642DFD6DAF241E81F23E6B4736F7AFDF3B";
    private static final String EP3 = "D2F5FE80E7BC000A749642CD26BDE1626DBEA7409C39314B8583547AE43DB43D";

    private WarExitTermsCodec() { }

    public static WarExitTerms decode(byte[] raw) { return decodeNode(StrictJson.parse(raw, MAX_BYTES)); }
    public static WarExitTerms decode(byte[] raw, int expectedWarId) {
        WarExitTerms.positive(expectedWarId);
        WarExitTerms result = decode(raw);
        require(result.warId() == expectedWarId, "native exit-terms WarID mismatch");
        return result;
    }
    public static byte[] normalize(byte[] raw) { return encode(decode(raw)); }
    public static byte[] encode(WarExitTerms value) { return StrictJson.canonical(node(value), MAX_BYTES); }

    static WarExitTerms decodeNode(JsonNode value) {
        ObjectNode root = StrictJson.object(value, FIELDS);
        require(integer(root.get("schema_version"), 2, 2) == 2, "schema v2 required");
        literal(root.get("status"), "available"); literal(root.get("supported_slice"), WarExitTerms.SLICE);
        literal(root.get("player_side"), "attacker");
        ObjectNode cb = StrictJson.object(root.get("casus_belli"), Set.of("database_index", "canonical_key"));
        literal(cb.get("canonical_key"), "claim_cb");
        List<Integer> titles = ids(root.get("target_title_ids"));
        ArrayNode rawClaims = array(root.get("claims"), 4096);
        List<Claim> claims = new ArrayList<>();
        for (JsonNode row : rawClaims) {
            ObjectNode claim = StrictJson.object(row, Set.of("title_id", "present", "strong", "implicit", "state"));
            StrictJson.trueValue(claim.get("present"));
            Claim typed = new Claim(id(claim.get("title_id")), bool(claim.get("strong")), bool(claim.get("implicit")));
            literal(claim.get("state"), typed.state());
            claims.add(typed);
        }
        ObjectNode readiness = StrictJson.object(root.get("readiness"), READINESS);
        READINESS.forEach(field -> StrictJson.trueValue(readiness.get(field)));
        ObjectNode provenance = StrictJson.object(root.get("provenance"), Set.of("game_version", "executable_sha256",
                "claim_script_sha256", "war_effects_sha256", "war_values_sha256", "ep3_effects_sha256", "native_contract_sha256"));
        literal(provenance.get("game_version"), GAME_VERSION); literal(provenance.get("executable_sha256"), EXE);
        literal(provenance.get("claim_script_sha256"), CLAIM); literal(provenance.get("war_effects_sha256"), EFFECTS);
        literal(provenance.get("war_values_sha256"), VALUES); literal(provenance.get("ep3_effects_sha256"), EP3);
        ObjectNode outcomes = StrictJson.object(root.get("outcomes"), Set.of("white_peace", "attacker_defeat"));
        List<MonthlyGoldIncome> income = new ArrayList<>();
        for (JsonNode item : wrapped(root.get("primary_monthly_gold_income"), 2)) {
            ObjectNode row = StrictJson.object(item, Set.of("character_id", "raw", "scale"));
            income.add(new MonthlyGoldIncome(id(row.get("character_id")), raw(row)));
        }
        return new WarExitTerms(id(root.get("war_id")), integer(root.get("date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE),
                integer(cb.get("database_index"), 0, Integer.MAX_VALUE), id(root.get("primary_attacker_character_id")),
                id(root.get("primary_defender_character_id")), id(root.get("claimant_character_id")), titles, claims,
                resources(root.get("primary_resource_balances")), income, outcome(outcomes.get("white_peace")),
                outcome(outcomes.get("attacker_defeat")), StrictJson.text(provenance.get("native_contract_sha256")));
    }

    private static Outcome outcome(JsonNode value) {
        ObjectNode root = StrictJson.object(value, Set.of("claim_disposition", "recipient_response", "cb_prestige_factor",
                "primary_gold_transfers", "primary_resource_deltas", "truce", "prisoner_releases", "complete"));
        StrictJson.trueValue(root.get("complete"));
        ObjectNode disposition = StrictJson.object(root.get("claim_disposition"), Set.of("declared_title_disposition", "claim_disposition"));
        literal(disposition.get("declared_title_disposition"), "unchanged");
        ObjectNode response = StrictJson.object(root.get("recipient_response"), Set.of("native_validator_passed", "acceptance_raw",
                "acceptance_scale", "decision_status_raw", "would_accept_now", "auto_accept"));
        StrictJson.trueValue(response.get("native_validator_passed"));
        scale(response.get("acceptance_scale"));
        RecipientResponse recipient = new RecipientResponse(StrictJson.integer(response.get("acceptance_raw"), Long.MIN_VALUE, Long.MAX_VALUE),
                DecisionStatus.fromRaw(integer(response.get("decision_status_raw"), 0, 3)),
                bool(response.get("would_accept_now")), bool(response.get("auto_accept")));
        ObjectNode factor = StrictJson.object(root.get("cb_prestige_factor"), Set.of("raw", "scale"));
        List<GoldTransfer> gold = new ArrayList<>();
        for (JsonNode item : wrapped(root.get("primary_gold_transfers"), 1)) {
            ObjectNode row = StrictJson.object(item, Set.of("from_character_id", "to_character_id", "raw", "scale"));
            gold.add(new GoldTransfer(id(row.get("from_character_id")), id(row.get("to_character_id")), raw(row)));
        }
        ObjectNode truce = StrictJson.object(root.get("truce"), Set.of("owner_character_id", "toward_character_id",
                "evaluated_days", "current_date_raw", "expiry_date_raw"));
        List<PrisonerRelease> prisoners = new ArrayList<>();
        for (JsonNode item : wrapped(root.get("prisoner_releases"), 64)) {
            ObjectNode row = StrictJson.object(item, Set.of("jailer_character_id", "prisoner_character_id", "reason"));
            prisoners.add(new PrisonerRelease(id(row.get("jailer_character_id")), id(row.get("prisoner_character_id")), StrictJson.text(row.get("reason"))));
        }
        return new Outcome(Disposition.fromWire(StrictJson.text(disposition.get("claim_disposition"))), recipient, raw(factor),
                gold, resources(root.get("primary_resource_deltas")), new Truce(id(truce.get("owner_character_id")),
                id(truce.get("toward_character_id")), integer(truce.get("evaluated_days"), 0, Integer.MAX_VALUE),
                integer(truce.get("current_date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE),
                integer(truce.get("expiry_date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE)), prisoners);
    }
    private static List<ResourceAmount> resources(JsonNode value) {
        List<ResourceAmount> rows = new ArrayList<>();
        for (JsonNode item : wrapped(value, 14)) {
            ObjectNode row = StrictJson.object(item, Set.of("character_id", "resource_kind", "raw", "scale"));
            rows.add(new ResourceAmount(id(row.get("character_id")), ResourceKind.fromWire(StrictJson.text(row.get("resource_kind"))), raw(row)));
        }
        return rows;
    }
    static List<Integer> ids(JsonNode value) {
        List<Integer> result = new ArrayList<>();
        for (JsonNode item : array(value, 4096)) { result.add(id(item)); }
        return List.copyOf(result);
    }
    static int id(JsonNode value) { return integer(value, 1, Integer.MAX_VALUE); }
    static int integer(JsonNode value, int minimum, int maximum) { return (int) StrictJson.integer(value, minimum, maximum); }
    static boolean bool(JsonNode value) {
        require(value != null && value.isBoolean(), "actual JSON boolean required");
        return value.booleanValue();
    }
    static void literal(JsonNode value, String expected) { require(expected.equals(StrictJson.text(value)), "literal mismatch: " + expected); }
    private static long raw(ObjectNode value) { scale(value.get("scale")); return StrictJson.integer(value.get("raw"), Long.MIN_VALUE, Long.MAX_VALUE); }
    private static void scale(JsonNode value) { integer(value, WarExitTerms.SCALE, WarExitTerms.SCALE); }
    private static ArrayNode wrapped(JsonNode value, int maximum) {
        return array(StrictJson.object(value, Set.of("values")).get("values"), maximum);
    }
    private static ArrayNode array(JsonNode value, int maximum) {
        require(value instanceof ArrayNode && value.size() <= maximum, "bounded JSON array required");
        return (ArrayNode) value;
    }

    static ObjectNode node(WarExitTerms value) {
        require(value != null, "complete typed exit terms required");
        ObjectNode root = StrictJson.object();
        root.put("schema_version", 2); root.put("status", "available"); root.put("war_id", value.warId()); root.put("date_raw", value.dateRaw());
        ObjectNode cb = root.putObject("casus_belli"); cb.put("database_index", value.casusBelliDatabaseIndex()); cb.put("canonical_key", "claim_cb");
        root.put("supported_slice", WarExitTerms.SLICE); root.put("player_side", "attacker");
        root.put("primary_attacker_character_id", value.primaryAttackerCharacterId()); root.put("primary_defender_character_id", value.primaryDefenderCharacterId());
        root.put("claimant_character_id", value.claimantCharacterId());
        ArrayNode titles = root.putArray("target_title_ids"); value.targetTitleIds().forEach(title -> titles.add(title.intValue()));
        ArrayNode claims = root.putArray("claims");
        for (Claim claim : value.claims()) {
            ObjectNode row = claims.addObject(); row.put("title_id", claim.titleId()); row.put("present", true);
            row.put("strong", claim.strong()); row.put("implicit", claim.implicit()); row.put("state", claim.state());
        }
        root.set("primary_resource_balances", resourceNode(value.primaryResourceBalances()));
        ArrayNode income = root.putObject("primary_monthly_gold_income").putArray("values");
        for (MonthlyGoldIncome item : value.primaryMonthlyGoldIncome()) {
            ObjectNode row = income.addObject(); row.put("character_id", item.characterId()); putRaw(row, item.raw());
        }
        ObjectNode outcomes = root.putObject("outcomes"); outcomes.set("white_peace", outcomeNode(value.whitePeace()));
        outcomes.set("attacker_defeat", outcomeNode(value.attackerDefeat()));
        ObjectNode readiness = root.putObject("readiness"); READINESS.forEach(field -> readiness.put(field, true));
        ObjectNode provenance = root.putObject("provenance"); provenance.put("game_version", GAME_VERSION); provenance.put("executable_sha256", EXE);
        provenance.put("claim_script_sha256", CLAIM); provenance.put("war_effects_sha256", EFFECTS); provenance.put("war_values_sha256", VALUES);
        provenance.put("ep3_effects_sha256", EP3); provenance.put("native_contract_sha256", value.nativeContractSha256());
        return root;
    }
    private static ObjectNode outcomeNode(Outcome value) {
        ObjectNode root = StrictJson.object();
        ObjectNode disposition = root.putObject("claim_disposition"); disposition.put("declared_title_disposition", "unchanged");
        disposition.put("claim_disposition", value.claimDisposition().wire());
        ObjectNode response = root.putObject("recipient_response"); response.put("native_validator_passed", true);
        response.put("acceptance_raw", value.recipientResponse().acceptanceRaw()); response.put("acceptance_scale", WarExitTerms.SCALE);
        response.put("decision_status_raw", value.recipientResponse().decisionStatus().raw()); response.put("would_accept_now", value.recipientResponse().wouldAcceptNow());
        response.put("auto_accept", value.recipientResponse().autoAccept());
        putRaw(root.putObject("cb_prestige_factor"), value.cbPrestigeFactorRaw());
        ArrayNode gold = root.putObject("primary_gold_transfers").putArray("values");
        for (GoldTransfer transfer : value.primaryGoldTransfers()) {
            ObjectNode row = gold.addObject(); row.put("from_character_id", transfer.fromCharacterId()); row.put("to_character_id", transfer.toCharacterId()); putRaw(row, transfer.raw());
        }
        root.set("primary_resource_deltas", resourceNode(value.primaryResourceDeltas()));
        ObjectNode truce = root.putObject("truce"); truce.put("owner_character_id", value.truce().ownerCharacterId());
        truce.put("toward_character_id", value.truce().towardCharacterId()); truce.put("evaluated_days", value.truce().evaluatedDays());
        truce.put("current_date_raw", value.truce().currentDateRaw()); truce.put("expiry_date_raw", value.truce().expiryDateRaw());
        ArrayNode prisoners = root.putObject("prisoner_releases").putArray("values");
        for (PrisonerRelease prisoner : value.prisonerReleases()) {
            ObjectNode row = prisoners.addObject(); row.put("jailer_character_id", prisoner.jailerCharacterId());
            row.put("prisoner_character_id", prisoner.prisonerCharacterId()); row.put("reason", prisoner.reason());
        }
        root.put("complete", true); return root;
    }
    private static ObjectNode resourceNode(List<ResourceAmount> values) {
        ObjectNode wrapper = StrictJson.object(); ArrayNode rows = wrapper.putArray("values");
        for (ResourceAmount resource : values) {
            ObjectNode row = rows.addObject(); row.put("character_id", resource.characterId()); row.put("resource_kind", resource.resourceKind().wire()); putRaw(row, resource.raw());
        }
        return wrapper;
    }
    private static void putRaw(ObjectNode value, long raw) { value.put("raw", raw); value.put("scale", WarExitTerms.SCALE); }
}
