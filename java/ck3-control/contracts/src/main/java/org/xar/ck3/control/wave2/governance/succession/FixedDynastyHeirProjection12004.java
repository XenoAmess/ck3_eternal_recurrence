package org.xar.ck3.control.wave2.governance.succession;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004.Core;
import org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004.Observation;

/** Pure fixed-original-campaign projection. Typed inputs and a positive result are never loaded-native custody. */
public final class FixedDynastyHeirProjection12004 {
    public static final String SOURCE_KIND = "native_get_player_heir_12004_v1";
    public static final String GETTER_CLOSURE_SHA256 = "632f01555310ab57b65743a686d5653b87a08ada14ebcb7d849371027ae27660";
    public record FixedAnchor(String goalCampaignId, int originCharacterId, String baselineEpisodeRunId,
            BigInteger t0DateRaw, int foundingDynastyIdRaw, String baselineSaveSha256, String baselineSummarySha256) { }
    /** Complete original query tuple; all generation bits and independent public/native counters remain exact. */
    public record QueryBinding(String machineId, String gameBirth, BigInteger bridgePid, BigInteger connectionGeneration,
            String executableSha256, String nativeProviderSha256, String ownerSourceEpoch, String queryId,
            String snapshotId, BigInteger revision, BigInteger nativeRevision, BigInteger captureEpoch,
            BigInteger dateRaw, int actorCharacterId, String episodeRunId, String goalCampaignId,
            int originCharacterId, String baselineSaveSha256, String baselineSummarySha256) { }
    public record Captured(QueryBinding binding, Observation observation, String sourceKind, String getterSourceClosureSha256) { }
    public enum Status { UNKNOWN, POSITIVE_WITNESS }
    public enum Reason {
        INVALID_FIXED_T0_ANCHOR("invalid_fixed_T0_anchor"), QUERY_BINDING_UNAVAILABLE("query_binding_unavailable"),
        STALE_OR_CROSS_QUERY_BINDING("stale_or_cross_query_binding"), DIFFERENT_ORIGINAL_CAMPAIGN_BASELINE("different_original_campaign_baseline"),
        ORIGINAL_PLAYER_HEIR_SOURCE_UNAVAILABLE("original_player_heir_source_unavailable"), MALFORMED_NATIVE_OBSERVATION("malformed_native_observation"),
        SYNTHETIC_PROVIDER_HAS_NO_SCORING_CREDIT("synthetic_provider_has_no_scoring_credit"), NATIVE_CANDIDATE_OBSERVATION_UNAVAILABLE("native_candidate_observation_unavailable"),
        NATIVE_ACTOR_OR_FRAME_CHANGED("native_actor_or_frame_changed"), OBSERVED_NULL_IS_NOT_COMPLETE_ELIGIBLE_ABSENCE("observed_null_is_not_complete_eligible_absence"),
        CANDIDATE_IDENTITY_OR_LIVENESS_UNAVAILABLE("candidate_identity_or_liveness_unavailable"), CANDIDATE_LINEAGE_UNAVAILABLE("candidate_lineage_unavailable"),
        CANDIDATE_LINEAGE_MALFORMED("candidate_lineage_malformed"), SELECTED_CANDIDATE_OUTSIDE_FIXED_D0_INCOMPLETE_DOMAIN("selected_candidate_outside_fixed_D0_incomplete_domain"),
        ONE_LIVING_NATIVE_PLAYER_HEIR_IN_FIXED_D0("one_living_native_player_heir_in_fixed_D0");
        private final String wire;
        Reason(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record Interval(int lower, int upper) {
        public Interval { StrictJson.require(lower >= 0 && lower <= upper && upper <= 100, "bounded H interval required"); }
    }
    public record Projection(Status status, Reason reason, Integer fixedDynastyIdRaw, Integer candidateCharacterId,
            Boolean candidateSameFixedDynasty, boolean positiveSameDynastyLegalWitness, Integer k, Interval hInterval) {
        public Projection {
            Objects.requireNonNull(status); Objects.requireNonNull(reason); Objects.requireNonNull(hInterval);
            StrictJson.require(status == Status.POSITIVE_WITNESS
                    ? reason == Reason.ONE_LIVING_NATIVE_PLAYER_HEIR_IN_FIXED_D0 && fixedDynastyIdRaw != null
                        && candidateCharacterId != null && Boolean.TRUE.equals(candidateSameFixedDynasty)
                        && positiveSameDynastyLegalWitness && Integer.valueOf(1).equals(k) && hInterval.equals(new Interval(70,100))
                    : !positiveSameDynastyLegalWitness && k == null && hInterval.equals(new Interval(0,100)), "projection branch mismatch");
        }
        public boolean completeBackupDomain() { return false; }
    }
    /** Historical immutable input only; new campaigns must supply their own retained original anchor. */
    public static final FixedAnchor ROBERT_20261019_T0 = new FixedAnchor("native-31254-6271ac8cd441",31254,
            "native-31254-6271ac8cd441",BigInteger.valueOf(53144328),174,
            "381e832bb3122b1c544d5bcd505eb86b4d40456a4d37969bcf208714d0aa88f4",
            "bb5cb5593e6a4e1156dfbacf2d94aa13f10eb41735a5f215dbaad2eb2d89ada8");
    private FixedDynastyHeirProjection12004() { }
    public static Projection project(FixedAnchor anchor, Captured captured, QueryBinding current, Core currentCore) {
        Integer fixed = valid(anchor) ? anchor.foundingDynastyIdRaw() : null;
        if (fixed == null) return unknown(Reason.INVALID_FIXED_T0_ANCHOR,null,null,null);
        if (captured == null || !valid(captured.binding()) || !valid(current)) return unknown(Reason.QUERY_BINDING_UNAVAILABLE,fixed,null,null);
        if (!captured.binding().equals(current)) return unknown(Reason.STALE_OR_CROSS_QUERY_BINDING,fixed,null,null);
        if (!current.goalCampaignId().equals(anchor.goalCampaignId()) || current.originCharacterId() != anchor.originCharacterId()
                || !current.baselineSaveSha256().equals(anchor.baselineSaveSha256()) || !current.baselineSummarySha256().equals(anchor.baselineSummarySha256())
                || current.dateRaw().compareTo(anchor.t0DateRaw()) < 0) return unknown(Reason.DIFFERENT_ORIGINAL_CAMPAIGN_BASELINE,fixed,null,null);
        if (!SOURCE_KIND.equals(captured.sourceKind()) || !GETTER_CLOSURE_SHA256.equals(captured.getterSourceClosureSha256()))
            return unknown(Reason.ORIGINAL_PLAYER_HEIR_SOURCE_UNAVAILABLE,fixed,null,null);
        Observation o = captured.observation();
        if (o == null) return unknown(Reason.MALFORMED_NATIVE_OBSERVATION,fixed,null,null);
        if (o.sourceFixture()) return unknown(Reason.SYNTHETIC_PROVIDER_HAS_NO_SCORING_CREDIT,fixed,null,null);
        if (!o.available() || !o.originalGetterSourceBound() || !o.getterObserved() || !o.identityAndFrameStable()
                || nonempty(o.unavailableReason())) return unknown(Reason.NATIVE_CANDIDATE_OBSERVATION_UNAVAILABLE,fixed,null,null);
        if (!valid(currentCore) || !valid(o.before()) || !valid(o.after()) || !o.before().equals(o.after()) || !o.after().equals(currentCore)
                || !BigInteger.valueOf(currentCore.dateRaw()).equals(current.dateRaw()) || currentCore.playedCharacterId() != current.actorCharacterId()
                || o.actorCharacterId() == -1 || o.actorCharacterId() != current.actorCharacterId())
            return unknown(Reason.NATIVE_ACTOR_OR_FRAME_CHANGED,fixed,null,null);
        if (!o.candidatePresent()) return unknown(Reason.OBSERVED_NULL_IS_NOT_COMPLETE_ELIGIBLE_ABSENCE,fixed,null,null);
        int candidate = o.candidateCharacterId();
        if (candidate == -1 || candidate == current.actorCharacterId() || !o.candidateAlive()) return unknown(Reason.CANDIDATE_IDENTITY_OR_LIVENESS_UNAVAILABLE,fixed,null,null);
        if (!o.lineageAvailable()) return unknown(Reason.CANDIDATE_LINEAGE_UNAVAILABLE,fixed,candidate,null);
        if (nonempty(o.lineageUnavailableReason()) || o.candidateLineage().houseId() == -1 && o.candidateLineage().dynastyId() != -1)
            return unknown(Reason.CANDIDATE_LINEAGE_MALFORMED,fixed,candidate,null);
        boolean same = o.candidateLineage().dynastyId() == fixed;
        if (!same) return unknown(Reason.SELECTED_CANDIDATE_OUTSIDE_FIXED_D0_INCOMPLETE_DOMAIN,fixed,candidate,false);
        return new Projection(Status.POSITIVE_WITNESS,Reason.ONE_LIVING_NATIVE_PLAYER_HEIR_IN_FIXED_D0,fixed,candidate,true,true,1,new Interval(70,100));
    }
    private static Projection unknown(Reason reason, Integer fixed, Integer candidate, Boolean same) {
        return new Projection(Status.UNKNOWN,reason,fixed,candidate,same,false,null,new Interval(0,100));
    }
    private static boolean valid(FixedAnchor a) {
        return a != null && text(a.goalCampaignId()) && text(a.baselineEpisodeRunId()) && a.originCharacterId() != -1
                && a.foundingDynastyIdRaw() != -1 && natural(a.t0DateRaw(),false) && sha(a.baselineSaveSha256()) && sha(a.baselineSummarySha256())
                && (!a.baselineSummarySha256().equals(ROBERT_20261019_T0.baselineSummarySha256()) || a.equals(ROBERT_20261019_T0));
    }
    private static boolean valid(QueryBinding b) {
        return b != null && text(b.machineId()) && text(b.gameBirth()) && text(b.queryId()) && text(b.snapshotId())
                && text(b.episodeRunId()) && text(b.goalCampaignId()) && sha(b.executableSha256()) && sha(b.nativeProviderSha256())
                && sha(b.ownerSourceEpoch()) && sha(b.baselineSaveSha256()) && sha(b.baselineSummarySha256())
                && b.executableSha256().equals(NativePlayerHeirObservation12004.EXE_SHA256)
                && natural(b.bridgePid(),true) && natural(b.connectionGeneration(),true) && natural(b.revision(),false)
                && natural(b.nativeRevision(),true) && natural(b.captureEpoch(),true) && natural(b.dateRaw(),false)
                && b.actorCharacterId() != -1 && b.originCharacterId() != -1;
    }
    private static boolean valid(Core c) { return c != null && c.dateRaw() >= 0 && c.speed() >= 0 && c.localPlayerId() >= 0
            && c.paused() && c.mapReady() && c.hasPlayedCharacter() && c.playedCharacterAlive() && c.playedCharacterId() != -1; }
    private static boolean natural(BigInteger value, boolean positive) { return value != null && value.signum() >= (positive ? 1 : 0); }
    private static boolean text(String value) { return value != null && !value.strip().isEmpty()
            && !Set.of("unknown","null","none").contains(value.toLowerCase(java.util.Locale.ROOT)); }
    private static boolean sha(String value) { return value != null && value.matches("[0-9a-f]{64}"); }
    private static boolean nonempty(String value) { return value != null && !value.isEmpty(); }
    public static byte[] encode(Projection projection) {
        Objects.requireNonNull(projection); ObjectNode n = StrictJson.object();
        n.put("status", projection.status() == Status.POSITIVE_WITNESS ? "positive_witness" : "unknown").put("reason",projection.reason().wire());
        nullable(n,"fixed_dynasty_id_raw",projection.fixedDynastyIdRaw()); nullable(n,"candidate_character_id",projection.candidateCharacterId());
        if (projection.candidateSameFixedDynasty() == null) n.putNull("candidate_same_fixed_dynasty"); else n.put("candidate_same_fixed_dynasty",projection.candidateSameFixedDynasty());
        n.put("positive_same_dynasty_legal_witness",projection.positiveSameDynastyLegalWitness()); nullable(n,"k",projection.k()); n.putNull("b");
        n.putArray("H_interval").add(projection.hInterval().lower()).add(projection.hInterval().upper());
        n.put("complete_backup_domain",false).put("scope","pure_current_candidate_projection"); return StrictJson.canonical(n);
    }
    /** Same existing bridge unknown-diagnostic path; retaining a diagnostic never qualifies its absent native provider. */
    public static byte[] encodeUnqualified(FixedAnchor actualOriginalAnchor, String actualDiagnostic) {
        StrictJson.text(actualDiagnostic); StrictJson.require(actualDiagnostic.codePointCount(0,actualDiagnostic.length())<=1024,"bounded original diagnostic required");
        ObjectNode node=(ObjectNode)StrictJson.parse(encode(project(actualOriginalAnchor,null,null,null)));
        node.put("reason",actualDiagnostic); return StrictJson.canonical(node);
    }
    private static void nullable(ObjectNode node, String key, Integer value) { if (value == null) node.putNull(key); else node.put(key,value); }
}
