package org.xar.ck3.control.wave2.finance.factionalerts;

import java.math.BigInteger;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.wave2.finance.factionculture.FactionCultureModel.CultureRelation;

/** Complete immutable native v1 alert contract. This validates observations, never gameplay capability. */
public final class FactionAlertModel {
    public static final int SCALE = 100_000;
    public static final String STEP = "query-player-faction-alerts-v1";
    public static final String COUNTY_COMPONENT = "player_subrealm_geographic_counties_v1";
    public static final String COUNTY_SCOPE = "played_character_own_subrealm_including_vassals";
    public static final String COUNTY_SOURCE = "native_actor_vassal_held_counties_double_sample_v1";
    public static final String ROWS_UNAVAILABLE = "targeting_rows_native_reader_not_frozen";
    public static final String COUNTY_UNAVAILABLE = "county_exposure_native_reader_not_frozen";
    private FactionAlertModel() { }

    public enum Status {
        AVAILABLE("available"), UNAVAILABLE("unavailable");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum MaterialStatus {
        AVAILABLE("available"), UNAVAILABLE("unavailable"), UNSUPPORTED_BUILD("unsupported_build");
        private final String wire;
        MaterialStatus(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum UnavailableReason {
        READER_NOT_IMPLEMENTED("reader_not_implemented"), UNSUPPORTED_BUILD("unsupported_build"),
        REQUIRES_APPLICATION_MAIN("requires_application_main"), REQUIRES_PAUSED("requires_paused"), STATE_CHANGED("state_changed");
        private final String wire;
        UnavailableReason(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum Build {
        CK3_11906("1.19.0.6", "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"),
        CK3_12002("1.20.0.2", "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"),
        CK3_12003("1.20.0.3", "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"),
        CK3_12004("1.20.0.4", "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518");
        private final String version; private final String sha;
        Build(String version, String sha) { this.version = version; this.sha = sha; }
        public String version() { return version; }
        public String sha256() { return sha; }
        public String backendId() { return "ck3-" + version + "-native-player-faction-alerts-v1"; }
        public static Build exact(String version, String sha) {
            for (Build build : values()) if (build.version.equals(version) && build.sha.equals(Objects.requireNonNull(sha).toUpperCase(Locale.ROOT))) return build;
            throw new ContractViolationException("native source does not match a frozen exact build");
        }
    }
    public record StableKey(String value) {
        public StableKey { if (!Objects.requireNonNull(value).matches("[a-z0-9_]+")) throw new ContractViolationException("stable lowercase key required"); }
    }
    public record ExpectedFrame(int dateRaw, BigInteger nativeRevision, Optional<Build> connectedBuild) {
        public ExpectedFrame { revision(nativeRevision); Objects.requireNonNull(connectedBuild); }
    }
    public record FixedPoint(long raw, int scale) {
        public FixedPoint { if (scale <= 0) throw new ContractViolationException("positive fixed point scale required"); }
    }
    public record Readiness(boolean targetingCountReady, boolean identityReady, boolean targetingRowsReady,
                            boolean countyExposureReady, boolean stockDangerousReady, boolean sameFrameReady,
                            boolean alertReady) {
        public boolean allFalse() { return !targetingCountReady && !identityReady && !targetingRowsReady && !countyExposureReady && !stockDangerousReady && !sameFrameReady && !alertReady; }
    }
    public record Reasons(Optional<StableKey> targetingRows, Optional<StableKey> countyExposure) {
        public Reasons { Objects.requireNonNull(targetingRows); Objects.requireNonNull(countyExposure); }
    }
    public sealed interface Planner permits UnavailablePlanner, AvailablePlanner { }
    public record UnavailablePlanner() implements Planner { }
    public record AvailablePlanner(boolean present, boolean dangerous, List<Integer> dangerousFactionIds,
                                   List<Integer> watchFactionIds, List<Integer> warHandoffFactionIds,
                                   List<Integer> exposedCountyTitleIds) implements Planner {
        public AvailablePlanner {
            dangerousFactionIds = ids(dangerousFactionIds); watchFactionIds = ids(watchFactionIds);
            warHandoffFactionIds = ids(warHandoffFactionIds); exposedCountyTitleIds = ids(exposedCountyTitleIds);
        }
    }
    public record CountyMember(int countyTitleId, Optional<Integer> capitalProvinceId, Optional<Integer> holderCharacterId,
                               Optional<FixedPoint> countyOpinion, Optional<FixedPoint> nativeJoinScore,
                               Optional<Boolean> canAddCounty, Optional<Boolean> removalQueued,
                               Optional<FixedPoint> nativeLeaveThreshold, MaterialStatus opinionStatus,
                               MaterialStatus nativeFinalStatus, Optional<CultureRelation> culture) {
        public CountyMember {
            positive(countyTitleId); optionalId(capitalProvinceId); optionalCharacter(holderCharacterId);
            Objects.requireNonNull(countyOpinion); Objects.requireNonNull(nativeJoinScore); Objects.requireNonNull(canAddCounty);
            Objects.requireNonNull(removalQueued); Objects.requireNonNull(nativeLeaveThreshold); Objects.requireNonNull(opinionStatus);
            Objects.requireNonNull(nativeFinalStatus); Objects.requireNonNull(culture);
        }
    }
    public record SurrenderTitle(int titleId, int tierRaw, Optional<Integer> deJureParentTitleId,
                                 Optional<Integer> duchyTitleId, Optional<Integer> kingdomTitleId,
                                 Optional<Integer> holderCharacterId, Optional<Integer> topLiegeCharacterId) {
        public SurrenderTitle {
            positive(titleId); if (tierRaw < 1 || tierRaw > 5) throw new ContractViolationException("title tier");
            optionalId(deJureParentTitleId); optionalId(duchyTitleId); optionalId(kingdomTitleId);
            optionalCharacter(holderCharacterId); optionalCharacter(topLiegeCharacterId);
        }
    }
    public record KingdomImpact(SurrenderTitle title, List<Integer> deJureCountyTitleIds,
                                List<Integer> seizedCountyTitleIds, boolean strictMajorityFromSeizedCounties) {
        public KingdomImpact { Objects.requireNonNull(title); deJureCountyTitleIds = ids(deJureCountyTitleIds); seizedCountyTitleIds = ids(seizedCountyTitleIds); }
    }
    public record SurrenderImpact(Status status, Optional<StableKey> unavailableReason,
                                  boolean ordinaryBranchTitleSetsReady, boolean countyLossComplete, boolean kingdomOutcomeComplete,
                                  Optional<Boolean> governmentAllowsStateFaith, Optional<Boolean> leaderAtWarWithTarget,
                                  List<Integer> playerSubrealmCountyTitleIds, List<Integer> playerDirectTitleLossIds,
                                  List<Integer> playerRemainingDirectCountyTitleIds, List<SurrenderTitle> memberCounties,
                                  List<SurrenderTitle> seizedCounties, List<SurrenderTitle> seizedDuchies,
                                  List<KingdomImpact> kingdoms, List<StableKey> unresolvedBranches) {
        public SurrenderImpact {
            Objects.requireNonNull(status); Objects.requireNonNull(unavailableReason); Objects.requireNonNull(governmentAllowsStateFaith);
            Objects.requireNonNull(leaderAtWarWithTarget); playerSubrealmCountyTitleIds = ids(playerSubrealmCountyTitleIds);
            playerDirectTitleLossIds = ids(playerDirectTitleLossIds); playerRemainingDirectCountyTitleIds = ids(playerRemainingDirectCountyTitleIds);
            memberCounties = List.copyOf(memberCounties); seizedCounties = List.copyOf(seizedCounties); seizedDuchies = List.copyOf(seizedDuchies);
            kingdoms = List.copyOf(kingdoms); unresolvedBranches = List.copyOf(unresolvedBranches);
        }
    }
    public record TargetingFaction(int factionId, StableKey factionTypeKey, int targetCharacterId,
                                   Optional<Integer> leaderCharacterId, boolean leaderIsHuman,
                                   Optional<Integer> specialCharacterId, Optional<Integer> specialTitleId,
                                   boolean factionAtWar, Optional<Integer> factionWarId,
                                   FixedPoint power, FixedPoint powerThreshold, FixedPoint discontent, FixedPoint discontentPerMonth,
                                   Optional<Integer> monthsUntilMaxDiscontent, List<Integer> characterMemberIds,
                                   List<Integer> countyMemberTitleIds, boolean dangerous, StableKey dangerReason,
                                   Optional<List<CountyMember>> countyMemberObservations, Optional<SurrenderImpact> surrenderImpact) {
        public TargetingFaction {
            positive(factionId); Objects.requireNonNull(factionTypeKey); character(targetCharacterId); optionalCharacter(leaderCharacterId);
            optionalCharacter(specialCharacterId); optionalId(specialTitleId); optionalId(factionWarId);
            Objects.requireNonNull(power); Objects.requireNonNull(powerThreshold); Objects.requireNonNull(discontent); Objects.requireNonNull(discontentPerMonth);
            Objects.requireNonNull(monthsUntilMaxDiscontent); monthsUntilMaxDiscontent.ifPresent(value -> { if (value < 0) throw new ContractViolationException("negative months"); });
            characterMemberIds = characterIds(characterMemberIds); countyMemberTitleIds = ids(countyMemberTitleIds); Objects.requireNonNull(dangerReason);
            countyMemberObservations = Objects.requireNonNull(countyMemberObservations).map(List::copyOf); Objects.requireNonNull(surrenderImpact);
            if (!factionAtWar && factionWarId.isPresent()) throw new ContractViolationException("war identity requires faction war");
            if (leaderCharacterId.isEmpty() && leaderIsHuman) throw new ContractViolationException("human leader identity required");
        }
    }
    public record CountyExposure(int countyTitleId, int factionId, StableKey factionTypeKey, int targetCharacterId,
                                 FixedPoint power, FixedPoint powerThreshold, boolean dangerous, StableKey dangerReason) {
        public CountyExposure {
            positive(countyTitleId); positive(factionId); Objects.requireNonNull(factionTypeKey); character(targetCharacterId);
            Objects.requireNonNull(power); Objects.requireNonNull(powerThreshold); Objects.requireNonNull(dangerReason);
        }
    }
    public sealed interface SubrealmCounties permits CompleteCounties, IncompleteCounties { }
    public record CompleteCounties(List<Integer> countyTitleIds) implements SubrealmCounties {
        public CompleteCounties { countyTitleIds = ids(countyTitleIds); if (countyTitleIds.size() > 16384) throw new ContractViolationException("subrealm county source bound"); }
    }
    public record IncompleteCounties(String unavailableReason) implements SubrealmCounties {
        public IncompleteCounties {
            if (Objects.requireNonNull(unavailableReason).isEmpty()
                    || unavailableReason.codePointCount(0, unavailableReason.length()) > 256) throw new ContractViolationException("subrealm reason");
        }
    }
    public sealed interface Frame permits Available, Unavailable {
        BigInteger snapshotRevision(); Build provenance(); Readiness readiness(); Planner planner(); Reasons reasons();
    }
    public record Available(BigInteger snapshotRevision, int dateRaw, int playerCharacterId, int targetingFactionCount,
                            List<TargetingFaction> targetingFactions, List<CountyExposure> countyExposures,
                            Planner planner, Readiness readiness, Reasons reasons, Build provenance,
                            Optional<SubrealmCounties> subrealmCounties) implements Frame {
        public Available {
            revision(snapshotRevision); character(playerCharacterId); if (targetingFactionCount < 0) throw new ContractViolationException("targeting count");
            targetingFactions = List.copyOf(targetingFactions); countyExposures = List.copyOf(countyExposures);
            Objects.requireNonNull(planner); Objects.requireNonNull(readiness); Objects.requireNonNull(reasons);
            Objects.requireNonNull(provenance); Objects.requireNonNull(subrealmCounties);
        }
    }
    public record Unavailable(BigInteger snapshotRevision, Optional<Integer> dateRaw, UnavailableReason unavailableReason,
                              Readiness readiness, Planner planner, Reasons reasons, Build provenance) implements Frame {
        public Unavailable {
            revision(snapshotRevision); Objects.requireNonNull(dateRaw); Objects.requireNonNull(unavailableReason);
            Objects.requireNonNull(readiness); Objects.requireNonNull(planner); Objects.requireNonNull(reasons); Objects.requireNonNull(provenance);
            if (!readiness.allFalse() || !(planner instanceof UnavailablePlanner) || reasons.targetingRows().isPresent()
                    || reasons.countyExposure().isPresent()) throw new ContractViolationException("unavailable frame cannot expose claims");
        }
    }
    static List<Integer> ids(List<Integer> values) {
        List<Integer> result = List.copyOf(values); int previous = 0;
        for (int id : result) { positive(id); if (id <= previous) throw new ContractViolationException("sorted unique identities required"); previous = id; }
        return result;
    }
    static List<Integer> characterIds(List<Integer> values) {
        List<Integer> result = List.copyOf(values); Integer previous = null;
        for (int id : result) { character(id); if (previous != null && id <= previous) throw new ContractViolationException("sorted unique character identities required"); previous = id; }
        return result;
    }
    private static void character(int value) { NativeCharacterId.of(value); }
    private static void optionalCharacter(Optional<Integer> value) { Objects.requireNonNull(value).ifPresent(FactionAlertModel::character); }
    private static void positive(int value) { if (value <= 0) throw new ContractViolationException("positive int32 identity required"); }
    private static void optionalId(Optional<Integer> value) { Objects.requireNonNull(value).ifPresent(FactionAlertModel::positive); }
    private static void revision(BigInteger value) {
        if (Objects.requireNonNull(value).signum() <= 0 || value.bitLength() > 64) throw new ContractViolationException("positive uint64 revision required");
    }
}
