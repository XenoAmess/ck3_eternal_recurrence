package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Current loaded CWar inputs only. Declared targets never substitute for the full settlement's territorial scope. */
public final class WarCurrentClaimInputs {
    public static final String DOMAIN = "war_current_claim_inputs_v1";
    public static final String SCHEMA = "xar.ck3.war-current-claim-inputs/v1";
    public static final String VERSION = "1.20.0.4";
    public static final String EXE = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    private WarCurrentClaimInputs() { }
    public enum ClaimState {
        ABSENT("absent"), STRONG_EXPLICIT("strong_explicit"), STRONG_IMPLICIT("strong_implicit"), WEAK_EXPLICIT("weak_explicit"), WEAK_IMPLICIT("weak_implicit");
        private final String wire;
        ClaimState(String wire) { this.wire=wire; }
        public String wire() { return wire; }
        public static ClaimState decode(String wire) { for (var value : values()) if (value.wire.equals(wire)) return value; throw new IllegalArgumentException("unknown native effective-claim state"); }
    }
    /** Engine getter includes implicit/inheritance fallback; this is not a raw direct-claim array row. */
    public record Claim(boolean present, Optional<Boolean> strong, Optional<Boolean> implicit, ClaimState state) {
        public Claim {
            Objects.requireNonNull(strong); Objects.requireNonNull(implicit); Objects.requireNonNull(state);
            require(present == strong.isPresent() && present == implicit.isPresent(), "native effective-claim presence and flags disagree");
            String wanted=present ? (strong.orElseThrow() ? "strong_" : "weak_") + (implicit.orElseThrow() ? "implicit" : "explicit") : "absent";
            require(state.wire().equals(wanted), "native effective-claim flags/state disagree");
        }
    }
    public record Target(int titleId, Claim effectiveClaim, int titleTier, Optional<FullId> holder,
            Optional<FullId> immediateLiege, Optional<FullId> topLiege, boolean holderInPlayerRealm) {
        public Target { require(titleId >= 0 && titleTier >= 1 && titleTier <= 6, "current target title/tier outside native range");
            Objects.requireNonNull(effectiveClaim); Objects.requireNonNull(holder); Objects.requireNonNull(immediateLiege); Objects.requireNonNull(topLiege);
            require(holder.isPresent() || immediateLiege.isEmpty() && topLiege.isEmpty() && !holderInPlayerRealm, "unheld target invented a holder relationship"); }
    }
    public record Observation(int warId, int casusBelliIndex, FullId actor, FullId attacker, FullId defender, FullId claimant,
            int dateRaw, BigInteger nativeRevision, List<Target> targets, Obj original) {
        public Observation { require(warId > 0 && casusBelliIndex >= 0 && casusBelliIndex < 10000, "native war/CB range differs");
            Objects.requireNonNull(actor); Objects.requireNonNull(attacker); Objects.requireNonNull(defender); Objects.requireNonNull(claimant);
            Objects.requireNonNull(nativeRevision); targets = List.copyOf(targets); Objects.requireNonNull(original);
            require(!attacker.equals(defender) && !targets.isEmpty() && targets.size() <= 4096, "complete current declared targets and distinct primaries required"); }
        /** Present possession only; neither list predicts settlement transfer or complete loss. */
        public List<Integer> playerHeldDeclaredTargets() { return targets.stream().filter(target -> target.holder().filter(actor::equals).isPresent()).map(Target::titleId).toList(); }
        public List<Integer> playerRealmDeclaredTargets() { return targets.stream().filter(Target::holderInPlayerRealm).map(Target::titleId).toList(); }
        public boolean completeSettlementTerms() { return false; }
        public boolean additionalTerritoryEffectsEvaluated() { return false; }
        public boolean loadedScriptSourceVerified() { return false; }
        public boolean actionAuthority() { return false; }
    }
    public static Observation normalize(ObjectNode raw, int selectedWar, Context expected) {
        require(expected.source().exactBuild().equals(VERSION), "current claim inputs require actual4 source context");
        ObjectNode n = closed(raw, "schema", "schema_version", "status", "read_only", "game_version", "executable_sha256",
                "claim_observation_semantics", "war_id", "casus_belli", "actor_character_id", "primary_attacker_character_id", "primary_defender_character_id",
                "claimant_character_id", "date_raw", "native_revision", "target_title_ids", "claims", "title_holders",
                "same_frame_stable", "complete_settlement_terms", "additional_territory_effects_evaluated", "loaded_script_source_verified");
        equal(get(n, "schema"), SCHEMA); require(i32(get(n, "schema_version")) == 1, "current claim input schema differs");
        equal(get(n, "status"), "observed"); yes(get(n, "read_only")); yes(get(n, "same_frame_stable"));
        require(!bool(get(n, "complete_settlement_terms")) && !bool(get(n, "additional_territory_effects_evaluated"))
                && !bool(get(n, "loaded_script_source_verified")), "current raw inputs cannot assert complete settlement or loaded script provenance");
        equal(get(n, "claim_observation_semantics"), "native-effective-character-claim-getter-v1");
        equal(get(n, "game_version"), VERSION); require(text(get(n, "executable_sha256")).equalsIgnoreCase(EXE), "current claim input EXE differs");
        require(i32(get(n, "war_id")) == selectedWar && selectedWar > 0, "current claim input selected WarID differs");
        int date = i32(get(n, "date_raw")); require(BigInteger.valueOf(date).equals(expected.dateRaw()), "current claim input date differs");
        BigInteger nativeRevision = positive(get(n, "native_revision")).value(); require(nativeRevision.equals(expected.nativeRevision()), "current claim input native revision differs");
        FullId actor = full(get(n, "actor_character_id")); require(BigInteger.valueOf(actor.value()).equals(expected.playerId()), "current claim input actor differs");
        FullId attacker = full(get(n, "primary_attacker_character_id")), defender = full(get(n, "primary_defender_character_id")), claimant = full(get(n, "claimant_character_id"));
        ObjectNode cb = closed(get(n, "casus_belli"), "database_index", "canonical_key"); equal(get(cb, "canonical_key"), "raiktor_claim_cb");
        int index = i32(get(cb, "database_index")); require(index >= 0 && index < 10000, "current claim input CB index differs");
        var ids = array(get(n, "target_title_ids"), value -> value); var claims = array(get(n, "claims"), value -> value); var holders = array(get(n, "title_holders"), value -> value);
        require(!ids.isEmpty() && ids.size() <= 4096 && claims.size() == ids.size() && holders.size() == ids.size(), "current target/claim/holder collections are incomplete");
        var seen = new HashSet<Integer>(); var targets = new ArrayList<Target>();
        for (int i = 0; i < ids.size(); i++) {
            int title = i32(ids.get(i)); require(title >= 0 && seen.add(title), "invalid or repeated current target title");
            ObjectNode claim = object(claims.get(i)); boolean present = bool(get(claim, "present"));
            claim = present ? closed(claim, "title_id", "present", "strong", "implicit", "state") : closed(claim, "title_id", "present", "state");
            require(i32(get(claim, "title_id")) == title, "current claim row order differs");
            Optional<Boolean> strong = present ? Optional.of(bool(get(claim, "strong"))) : Optional.empty();
            Optional<Boolean> implicit = present ? Optional.of(bool(get(claim, "implicit"))) : Optional.empty();
            String state = text(get(claim, "state")); String wanted = present ? (strong.orElseThrow() ? "strong_" : "weak_") + (implicit.orElseThrow() ? "implicit" : "explicit") : "absent";
            require(state.equals(wanted), "current claim flags/state disagree");
            ObjectNode holder = closed(holders.get(i), "title_id", "title_tier_raw", "holder_character_id", "holder_immediate_liege_character_id", "holder_top_liege_character_id", "holder_in_player_realm");
            require(i32(get(holder, "title_id")) == title, "current holder row order differs");
            targets.add(new Target(title, new Claim(present, strong, implicit, ClaimState.decode(state)), i32(get(holder, "title_tier_raw")),
                    optionalFull(get(holder, "holder_character_id")), optionalFull(get(holder, "holder_immediate_liege_character_id")),
                    optionalFull(get(holder, "holder_top_liege_character_id")), bool(get(holder, "holder_in_player_realm"))));
        }
        return new Observation(selectedWar, index, actor, attacker, defender, claimant, date, nativeRevision, targets,
                DriverJson.object(bytes(n), DriverJson.MAX_NATIVE_BYTES));
    }
    public static ObjectNode encode(Observation observed) { return object(OpportunityJson.toNode(observed.original())); }
    private static Optional<FullId> optionalFull(com.fasterxml.jackson.databind.JsonNode value) {
        return value.isNull() ? Optional.empty() : Optional.of(full(value));
    }
}
