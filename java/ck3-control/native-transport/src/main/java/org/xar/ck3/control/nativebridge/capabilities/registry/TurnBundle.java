package org.xar.ck3.control.nativebridge.capabilities.registry;

import java.util.List;
import java.util.Objects;
import static org.xar.ck3.control.nativebridge.capabilities.registry.CampaignProjection.*;

/** Same-frame pure aggregate; the root query remains owned by its single registered producer. */
public final class TurnBundle {
    public static final String SCHEMA = "xar.ck3.turn-bundle/v1";
    public record HealthBand(String key, Fixed health, boolean belowFine, boolean atOrBelowDeathChanceDying) { }
    public record Domain(int size, int limit, int availableCapacity, int overLimitBy) { }
    public record FactionAlert(int targetingFactionCount, boolean threatened) { }
    public record Partition(List<PartitionRow> titleHeirs, Integer primaryHeirCharacterId, List<PartitionRow> titlesToOtherHeirs,
            List<Title> titlesWithoutHeir, String riskState, boolean splitRisk) {
        public Partition { titleHeirs = List.copyOf(titleHeirs); titlesToOtherHeirs = List.copyOf(titlesToOtherHeirs); titlesWithoutHeir = List.copyOf(titlesWithoutHeir); }
    }
    public record Succession(Component<Title> primaryTitle, List<Integer> orderedPrimaryTitleSuccessorCharacterIds,
            Component<Integer> primaryTitleHeirCharacterId, Component<Boolean> noPrimaryTitleHeirAlert, Component<Partition> partition) {
        public Succession { orderedPrimaryTitleSuccessorCharacterIds = List.copyOf(orderedPrimaryTitleSuccessorCharacterIds); }
    }
    public record TerritorySource(String snapshotId, java.math.BigInteger revision, java.math.BigInteger nativeRevision,
            int dateRaw, java.math.BigInteger expectedRevision, int playerCharacterId, java.math.BigInteger querySequence) { }
    public record Territory(TerritorySource sourceFrame, Component<List<Integer>> directlyHeldGeographicCountyTitleIds,
            Component<List<Integer>> directCountiesToOtherTitleHeirs, Component<List<Integer>> playerSubrealmCountyTitleIds,
            Component<List<Integer>> successionRealmCountyLoss) { }
    public record Realm(Integer immediateLiegeCharacterId, int topLiegeCharacterId, boolean independent,
            List<Integer> directLandedVassalCharacterIds, List<Integer> adjacentExternalProvinceHolderCharacterIds,
            List<Integer> adjacentHolderTopLiegeCharacterIds, Component<Domain> domain, Component<Council> council,
            Component<FactionAlert> factionAlert, Territory territory) {
        public Realm { directLandedVassalCharacterIds = List.copyOf(directLandedVassalCharacterIds);
            adjacentExternalProvinceHolderCharacterIds = List.copyOf(adjacentExternalProvinceHolderCharacterIds);
            adjacentHolderTopLiegeCharacterIds = List.copyOf(adjacentHolderTopLiegeCharacterIds); }
    }
    public record VitalsBinding(int characterId, String snapshotId, java.math.BigInteger snapshotRevision, int dateRaw) { }
    public record Health(long raw, int scale, String band, boolean belowFine, boolean atOrBelowDeathChanceDying) { }
    public record Stress(int points, boolean atOrAboveFirstBreakThreshold) { }
    public record Legitimacy(long raw, int scale, String typeKey, int currentLevel, boolean atFloorLevel) { }
    public record VitalsReadiness(boolean identityReady, boolean healthReady, boolean stressReady,
            boolean legitimacyBalanceReady, boolean legitimacyClassificationReady, boolean vitalsReady) { }
    public record Signals(Component<String> successionPreparationPriority, Component<Boolean> avoidDiscretionaryStressGain,
            Component<Boolean> protectLegitimacyFloor) { }
    public record Vitals(String schema, Status status, VitalsBinding binding, Component<Health> health,
            Component<Stress> stress, Component<Legitimacy> legitimacy, VitalsReadiness readiness, Signals plannerSignals) { }
    public record Ruler(int characterId, boolean alive, Component<Title> primaryTitle, Component<Integer> capitalProvinceId,
            Component<Government> government, Component<Fixed> gold, Component<Fixed> income, Component<Integer> stressPoints,
            Component<HealthBand> healthBand, Vitals vitals) { }
    public record Pending<E,I>(Component<E> activeEvent, Component<I> pendingCharacterInteraction) { }
    public record Wars(int activeWarCount, List<War> wars) { public Wars { wars = List.copyOf(wars); } }
    public record Alerts(Component<Boolean> rulerDead, Component<Boolean> rulerLandless,
            @com.fasterxml.jackson.annotation.JsonProperty("ruler_stress_at_or_above_100") Component<Boolean> rulerStressAtOrAbove100,
            Component<Boolean> rulerHealthBelowFine, Component<Boolean> realmHasNoDirectLandedVassals,
            Component<Boolean> realmHasAdjacentExternalHolders, Component<Boolean> noPrimaryTitleHeir,
            Component<Boolean> successionPartitionSplit, Component<Boolean> factionThreat) { }
    public record Readiness(boolean rootIdentityReady, boolean rulerAliveAlertReady, boolean rulerStressAlertReady,
            boolean rulerHealthAlertReady, boolean rulerResourcesReady, boolean realmRelationshipAlertsReady,
            boolean realmDomainReady, boolean realmCouncilReady, boolean realmFactionAlertReady,
            boolean successionPrimaryTitleAlertReady, boolean successionPartitionReady, boolean eventPendingReady,
            boolean warSummaryReady, boolean minimumAlertsReady, boolean ready) { }
    public record BundleSource(String capability, java.math.BigInteger querySequence, String backendId) { }
    public record Result<E,I>(String schema, Status status, Binding binding, Component<Ruler> rulerState,
            Component<Realm> realmState, Component<Succession> successionState, Component<Pending<E,I>> pendingState,
            Component<Wars> warState, Component<Alerts> alerts, Readiness readiness, String unavailableReason, BundleSource source) { }
    private TurnBundle() { }

    public static <E,I> Result<E,I> build(Snapshot<E,I> snapshot, Root root) {
        Objects.requireNonNull(snapshot); Objects.requireNonNull(root);
        RegistryJson.require(snapshot.paused() && snapshot.binding().equals(root.binding()), "turn-bundle inputs must share one paused frame");
        BundleSource source = new BundleSource(root.source().capability(), root.source().querySequence(), snapshot.backendId());
        if (root instanceof UnavailableRoot unavailable) {
            String reason = unavailable.unavailableReason();
            return new Result<>(SCHEMA, Status.UNAVAILABLE, root.binding(), Component.unavailable(reason), Component.unavailable(reason),
                    Component.unavailable(reason), Component.unavailable(reason), Component.unavailable(reason), Component.unavailable(reason),
                    new Readiness(false,false,false,false,false,false,false,false,false,false,false,false,false,false,false),reason,source);
        }
        AvailableRoot value = (AvailableRoot) root;
        RegistryJson.require(snapshot.playerCharacterId() == value.playerCharacterId()
                && snapshot.playerCharacterAlive() == value.playerCharacterAlive(), "snapshot/root played-character disagreement");
        Component<Title> title = value.primaryTitle() == null ? Component.notApplicable("no_primary_landed_title") : Component.available(value.primaryTitle());
        List<Integer> successors = value.primaryTitleSuccessionCharacterIds();
        Component<Integer> heir = successors.isEmpty() ? Component.notApplicable(value.primaryTitle() == null
                ? "no_primary_landed_title" : "no_observed_primary_title_successor") : Component.available(successors.getFirst());
        Component<Boolean> noHeir = value.primaryTitle() == null ? Component.notApplicable("no_primary_landed_title") : Component.available(successors.isEmpty());
        Component<Partition> partition; Component<Boolean> split;
        if (value.primaryTitle() == null || value.primaryTitle().tierRaw() == 1) {
            String reason = value.primaryTitle() == null ? "no_primary_landed_title" : "primary_title_below_county";
            partition = Component.notApplicable(reason); split = Component.notApplicable(reason);
        } else {
            Integer primaryHeir = successors.isEmpty() ? null : successors.getFirst();
            List<PartitionRow> other = value.heldTitlePartition().stream().filter(row -> primaryHeir != null
                    && row.firstHeirCharacterId() != null && !row.firstHeirCharacterId().equals(primaryHeir)).toList();
            List<Title> noTitleHeir = value.heldTitlePartition().stream().filter(row -> row.firstHeirCharacterId() == null).map(PartitionRow::title).toList();
            boolean risk = primaryHeir != null && !other.isEmpty();
            partition = Component.available(new Partition(value.heldTitlePartition(),primaryHeir,other,noTitleHeir,
                    primaryHeir == null ? "no_primary_heir" : risk ? "split_successors" : "single_successor",risk));
            split = Component.available(risk);
        }
        Succession succession = new Succession(title,successors,heir,noHeir,partition);
        Fixed health = value.playerHealth(); String healthKey = health.raw() <= 150_000 ? "dying_or_worse" : health.raw() < 300_000 ? "below_fine" : "fine_or_better";
        Component<HealthBand> band = Component.available(new HealthBand(healthKey,health,health.raw() < 300_000,health.raw() <= 150_000));
        Component<Integer> stress = snapshot.stressPoints();
        Vitals vitals = vitals(value, snapshot, healthKey, succession);
        Ruler ruler = new Ruler(value.playerCharacterId(),value.playerCharacterAlive(),title,
                value.capitalProvinceId() == null ? Component.notApplicable("no_current_capital") : Component.available(value.capitalProvinceId()),
                value.government() == null ? Component.notApplicable("no_current_government") : Component.available(value.government()),
                snapshot.gold(),Component.available(value.playerMonthlyGoldIncome()),stress,band,vitals);
        boolean councilReady = value.council().status() == Status.AVAILABLE;
        Component<Council> council = councilReady ? Component.available(value.council()) : Component.unavailable(value.council().unavailableReason());
        List<Integer> adjacentLieges = value.relatedCharacterContexts().stream().filter(row -> row.relationshipRole() == Relation.ADJACENT_EXTERNAL_PROVINCE_HOLDER)
                .map(Related::topLiegeCharacterId).distinct().sorted().toList();
        boolean threatened = value.playerTargetingFactionCount() > 0;
        Realm realm = new Realm(value.immediateLiegeCharacterId(),value.topLiegeCharacterId(),value.independent(),
                value.directLandedVassalCharacterIds(),value.adjacentExternalProvinceHolderCharacterIds(),adjacentLieges,
                Component.available(new Domain(value.playerDomainSize(),value.playerDomainLimit(),Math.max(value.playerDomainLimit()-value.playerDomainSize(),0),
                        Math.max(value.playerDomainSize()-value.playerDomainLimit(),0))),council,
                Component.available(new FactionAlert(value.playerTargetingFactionCount(),threatened)),territory(value,partition));
        boolean pendingReady = !(snapshot.activeEvent() instanceof Missing<?>) && !(snapshot.pendingCharacterInteraction() instanceof Missing<?>);
        Pending<E,I> pending = pendingReady ? new Pending<>(pending(snapshot.activeEvent(),"no_active_event"),pending(snapshot.pendingCharacterInteraction(),"no_pending_character_interaction"))
                : new Pending<>(Component.unavailable("active_event_observation_unavailable"),Component.unavailable("pending_character_interaction_observation_unavailable"));
        boolean warReady = snapshot.activeWars() instanceof Present<?>;
        Component<Wars> wars = snapshot.activeWars() instanceof Present<List<War>> observed
                ? Component.available(new Wars(observed.value().size(),observed.value().stream().sorted(java.util.Comparator.comparingInt(War::warId)).toList()))
                : Component.unavailable("active_wars_unavailable");
        Component<Boolean> highStress = stress.status() == Status.AVAILABLE ? Component.available(stress.value() >= 100) : Component.unavailable(stress.unavailableReason());
        Alerts alerts = new Alerts(Component.available(!value.playerCharacterAlive()),Component.available(value.primaryTitle() == null),
                highStress,Component.available(health.raw() < 300_000),Component.available(value.directLandedVassalCharacterIds().isEmpty()),
                Component.available(!value.adjacentExternalProvinceHolderCharacterIds().isEmpty()),noHeir,split,Component.available(threatened));
        boolean stressReady = stress.status() == Status.AVAILABLE, resourcesReady = snapshot.gold().status() == Status.AVAILABLE;
        boolean ready = stressReady && resourcesReady && councilReady && pendingReady && warReady;
        Readiness readiness = new Readiness(true,true,stressReady,true,resourcesReady,true,true,councilReady,true,true,true,pendingReady,warReady,true,ready);
        return new Result<>(SCHEMA,ready ? Status.AVAILABLE : Status.PARTIAL,root.binding(),Component.available(ruler),Component.available(realm),
                Component.available(succession),Component.available(pending),wars,Component.available(alerts),readiness,null,source);
    }
    private static <T> Component<T> pending(Presence<T> value, String absentReason) {
        if (value instanceof Present<T> present) return Component.available(present.value());
        if (value instanceof NullValue<T>) return Component.notApplicable(absentReason);
        throw new IllegalArgumentException("missing pending observation");
    }
    private static Territory territory(AvailableRoot root, Component<Partition> partition) {
        boolean geography = partition.status() == Status.AVAILABLE;
        String geographyReason = geography ? "held_county_geography_unavailable" : partition.unavailableReason();
        boolean comparison = geography; String heirReason = "primary_title_heir_unavailable";
        java.util.ArrayList<Integer> counties = new java.util.ArrayList<>(), other = new java.util.ArrayList<>();
        if (geography) {
            Integer heir = partition.value().primaryHeirCharacterId(); comparison = heir != null;
            for (PartitionRow row : partition.value().titleHeirs()) {
                if (row.title().tierRaw() != 2 || row.landlessNobleFamilyNoProvince()) continue;
                if (row.capitalProvinceId() == null) { geography = false; continue; }
                counties.add(row.title().titleId());
                if (row.firstHeirCharacterId() == null) { comparison = false; if (heir != null) heirReason = "held_county_first_heir_unavailable"; }
                if (heir != null && row.firstHeirCharacterId() != null && !heir.equals(row.firstHeirCharacterId())) other.add(row.title().titleId());
            }
        }
        Binding b = root.binding();
        return new Territory(new TerritorySource(b.snapshotId(),b.revision(),b.nativeRevision(),b.dateRaw(),b.expectedRevision(),root.playerCharacterId(),root.source().querySequence()),
                geography ? Component.available(counties.stream().sorted().toList()) : Component.unavailable(geographyReason),
                geography && comparison ? Component.available(other.stream().sorted().toList()) : Component.unavailable(!geography ? geographyReason : heirReason),
                Component.unavailable("campaign_root_subrealm_county_membership_unavailable"),Component.unavailable("post_succession_subrealm_membership_unavailable"));
    }
    private static <E,I> Vitals vitals(AvailableRoot root, Snapshot<E,I> snapshot, String band, Succession succession) {
        Fixed fixed = root.playerHealth(); Component<Health> health = Component.available(new Health(fixed.raw(),fixed.scale(),band,fixed.raw() < 300_000,fixed.raw() <= 150_000));
        boolean stressReady = snapshot.stressPoints().status() == Status.AVAILABLE;
        Component<Stress> stress = stressReady ? Component.available(new Stress(snapshot.stressPoints().value(),snapshot.stressPoints().value() >= 100))
                : Component.unavailable(snapshot.stressPoints().unavailableReason());
        boolean risk = succession.noPrimaryTitleHeirAlert().status() == Status.AVAILABLE && succession.noPrimaryTitleHeirAlert().value()
                || succession.partition().status() == Status.AVAILABLE && succession.partition().value().splitRisk();
        String priority = "dying_or_worse".equals(band) && risk ? "critical" : "below_fine".equals(band) && risk ? "elevated" : "normal";
        Binding b = root.binding();
        return new Vitals("xar.ck3.player-vitals/v1",Status.PARTIAL,new VitalsBinding(root.playerCharacterId(),b.snapshotId(),b.nativeRevision(),b.dateRaw()),health,stress,
                Component.unavailable("player_legitimacy_state_unavailable"),new VitalsReadiness(true,true,stressReady,false,false,false),
                new Signals(Component.available(priority),stressReady ? Component.available(snapshot.stressPoints().value() >= 100) : Component.unavailable(snapshot.stressPoints().unavailableReason()),
                        Component.unavailable("player_legitimacy_state_unavailable")));
    }
}

