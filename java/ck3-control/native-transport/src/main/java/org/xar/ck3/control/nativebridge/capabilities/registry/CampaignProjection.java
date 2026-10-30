package org.xar.ck3.control.nativebridge.capabilities.registry;

import org.xar.ck3.control.contracts.NativeCharacterId;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/** Immutable inputs shared by the entity-directory and turn-bundle producers. No source or readiness is invented. */
public final class CampaignProjection {
    private CampaignProjection() { }
    public enum Status { AVAILABLE, UNAVAILABLE, NOT_APPLICABLE, PARTIAL;
        @com.fasterxml.jackson.annotation.JsonValue public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
    }
    public enum Relation { ANY, SELF, DIRECT_LANDED_VASSAL, ADJACENT_EXTERNAL_PROVINCE_HOLDER;
        @com.fasterxml.jackson.annotation.JsonValue public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
    }
    public record Component<T>(Status status, T value, String unavailableReason) {
        public Component {
            Objects.requireNonNull(status);
            RegistryJson.require(status == Status.AVAILABLE ? value != null && unavailableReason == null
                    : (status == Status.UNAVAILABLE || status == Status.NOT_APPLICABLE) && value == null
                    && unavailableReason != null && !unavailableReason.isEmpty(), "component value/reason/status mismatch");
        }
        public static <T> Component<T> available(T value) { return new Component<>(Status.AVAILABLE, Objects.requireNonNull(value), null); }
        public static <T> Component<T> unavailable(String reason) { return new Component<>(Status.UNAVAILABLE, null, reason); }
        public static <T> Component<T> notApplicable(String reason) { return new Component<>(Status.NOT_APPLICABLE, null, reason); }
    }
    /** Missing, JSON null and an observed object remain three different observations. */
    public sealed interface Presence<T> permits Missing, NullValue, Present { }
    public record Missing<T>() implements Presence<T> { }
    public record NullValue<T>() implements Presence<T> { }
    public record Present<T>(T value) implements Presence<T> { public Present { Objects.requireNonNull(value); } }
    public record Binding(String snapshotId, BigInteger revision, BigInteger nativeRevision, int dateRaw,
            BigInteger expectedRevision) {
        public Binding {
            RegistryJson.require(snapshotId != null && !snapshotId.isEmpty(), "snapshot identity required");
            nonnegative(revision); positive64(nativeRevision); nonnegative(expectedRevision);
            RegistryJson.require(revision.equals(expectedRevision), "public revision changed");
        }
    }
    public record Source(String capability, BigInteger querySequence, String gameVersion, String executableSha256) {
        public Source {
            RegistryJson.require("game.command.query-campaign-root-context-v1".equals(capability), "source must name campaign-root capability");
            positive64(querySequence); RegistryJson.require(gameVersion != null && !gameVersion.isEmpty(), "game version required");
            RegistryJson.require(executableSha256 != null && executableSha256.matches("[0-9A-Fa-f]{64}"), "exact executable digest required");
        }
    }
    public record Title(int titleId, int tierRaw, String tierKey) {
        public Title {
            positive(titleId);
            RegistryJson.require(tierRaw >= 1 && tierRaw <= 6
                    && List.of("barony","county","duchy","kingdom","empire","hegemony").get(tierRaw - 1).equals(tierKey), "title tier pair mismatch");
        }
    }
    public record Fixed(long raw, int scale) { public Fixed { RegistryJson.require(scale == 100_000, "native fixed-point scale required"); } }
    public record Government(String key, List<String> flags, int nativeFlagCount) {
        public Government { RegistryJson.require(key != null && !key.isEmpty(), "government key required"); flags = List.copyOf(flags);
            RegistryJson.require(nativeFlagCount == flags.size() && flags.stream().allMatch(flag -> flag != null && !flag.isEmpty()), "government flag count mismatch"); }
    }
    public enum TaskKind { GENERAL, COUNTY, COURT;
        @com.fasterxml.jackson.annotation.JsonValue public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
    }
    public sealed interface Target permits ProvinceTarget, CharacterTarget { }
    public record ProvinceTarget(int provinceId) implements Target { public ProvinceTarget { positive(provinceId); }
        @com.fasterxml.jackson.annotation.JsonProperty("kind") public String kind() { return "province"; }
    }
    public record CharacterTarget(int characterId) implements Target { public CharacterTarget { NativeCharacterId.of(characterId); }
        @com.fasterxml.jackson.annotation.JsonProperty("kind") public String kind() { return "character"; }
    }
    public enum ProgressKind { INFINITE, PERCENTAGE, VALUE;
        @com.fasterxml.jackson.annotation.JsonValue public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
    }
    public record Progress(ProgressKind kind, Fixed current, Fixed maximum) {
        public Progress {
            Objects.requireNonNull(kind);
            RegistryJson.require(kind == ProgressKind.INFINITE ? current == null && maximum == null
                    : current != null && maximum != null && current.raw() >= 0 && maximum.raw() > 0 && current.raw() <= maximum.raw(), "council progress range mismatch");
            if (kind == ProgressKind.PERCENTAGE) RegistryJson.require(maximum.raw() == 10_000_000, "percentage maximum must be 100 percent");
        }
    }
    public record CouncilPosition(String positionKey, Integer incumbentCharacterId, String taskKey, TaskKind taskType,
            Target target, Boolean frozen, Progress progress) {
        public CouncilPosition {
            RegistryJson.require(positionKey != null && !positionKey.isEmpty(), "position key required");
            if (incumbentCharacterId == null) RegistryJson.require(taskKey == null && taskType == null && target == null && frozen == null && progress == null, "vacancy invented active task");
            else {
                NativeCharacterId.of(incumbentCharacterId); RegistryJson.require(taskKey != null && !taskKey.isEmpty() && taskType != null && frozen != null && progress != null, "active council task missing");
                RegistryJson.require(switch (taskType) { case GENERAL -> target == null; case COUNTY -> target instanceof ProvinceTarget; case COURT -> target instanceof CharacterTarget; }, "council target kind mismatch");
            }
        }
    }
    public record Council(Status status, String coverageKey, int ownerCharacterId, List<CouncilPosition> positions,
            boolean auxiliaryVacanciesComplete, String unavailableReason) {
        public Council {
            character(ownerCharacterId); positions = List.copyOf(positions);
            RegistryJson.require("standard_landed_non_nomadic_core_v1".equals(coverageKey) && !auxiliaryVacanciesComplete, "council coverage mismatch");
            RegistryJson.require(status == Status.AVAILABLE ? unavailableReason == null
                    : status == Status.UNAVAILABLE && positions.isEmpty() && unavailableReason != null && !unavailableReason.isEmpty(), "council availability mismatch");
            RegistryJson.require(positions.stream().map(CouncilPosition::positionKey).distinct().count() == positions.size(), "duplicate council position");
        }
    }
    public record Related(int characterId, Relation relationshipRole, Title primaryTitle, Integer capitalProvinceId,
            Integer immediateLiegeCharacterId, int topLiegeCharacterId) {
        public Related { character(characterId); character(topLiegeCharacterId); nullablePositive(capitalProvinceId); nullableCharacter(immediateLiegeCharacterId);
            Objects.requireNonNull(primaryTitle); RegistryJson.require(relationshipRole == Relation.DIRECT_LANDED_VASSAL
                    || relationshipRole == Relation.ADJACENT_EXTERNAL_PROVINCE_HOLDER, "invalid related role"); }
    }
    public record PartitionRow(Title title, Integer firstHeirCharacterId, Integer capitalProvinceId,
            boolean primary, @com.fasterxml.jackson.annotation.JsonIgnore boolean landlessNobleFamilyNoProvince,
            @com.fasterxml.jackson.annotation.JsonIgnore String titleKey) {
        public PartitionRow {
            Objects.requireNonNull(title); nullableCharacter(firstHeirCharacterId); nullablePositive(capitalProvinceId);
            RegistryJson.require(!landlessNobleFamilyNoProvince || title.tierRaw() == 2 && capitalProvinceId == null
                    && titleKey != null && titleKey.matches("c_[A-Za-z0-9][A-Za-z0-9_]{0,1021}"), "invalid landless family geography exemption");
        }
        @com.fasterxml.jackson.annotation.JsonProperty("capital_province_kind")
        @com.fasterxml.jackson.annotation.JsonInclude(com.fasterxml.jackson.annotation.JsonInclude.Include.NON_NULL)
        public String capitalProvinceKind() { return landlessNobleFamilyNoProvince ? "landless_noble_family_no_province" : null; }
        @com.fasterxml.jackson.annotation.JsonProperty("title_key")
        @com.fasterxml.jackson.annotation.JsonInclude(com.fasterxml.jackson.annotation.JsonInclude.Include.NON_NULL)
        public String familyTitleKey() { return landlessNobleFamilyNoProvince ? titleKey : null; }
    }
    public sealed interface Root permits AvailableRoot, UnavailableRoot { Binding binding(); Source source(); }
    public record UnavailableRoot(Binding binding, Source source, String unavailableReason) implements Root {
        public UnavailableRoot { Objects.requireNonNull(binding); Objects.requireNonNull(source); RegistryJson.require(unavailableReason != null && !unavailableReason.isEmpty(), "root unavailable reason required"); }
    }
    public record AvailableRoot(Binding binding, Source source, int playerCharacterId, boolean playerCharacterAlive,
            Title primaryTitle, Integer capitalProvinceId, Integer immediateLiegeCharacterId, int topLiegeCharacterId,
            boolean independent, List<Integer> directLandedVassalCharacterIds, List<Integer> adjacentExternalProvinceHolderCharacterIds,
            List<Related> relatedCharacterContexts, Government government, Fixed playerMonthlyGoldIncome, Fixed playerHealth,
            int playerDomainSize, int playerDomainLimit, int playerTargetingFactionCount, Council council,
            List<Integer> primaryTitleSuccessionCharacterIds, List<PartitionRow> heldTitlePartition) implements Root {
        public AvailableRoot {
            Objects.requireNonNull(binding); Objects.requireNonNull(source); character(playerCharacterId); character(topLiegeCharacterId);
            nullablePositive(capitalProvinceId); nullableCharacter(immediateLiegeCharacterId);
            directLandedVassalCharacterIds = ids(directLandedVassalCharacterIds, true);
            adjacentExternalProvinceHolderCharacterIds = ids(adjacentExternalProvinceHolderCharacterIds, true);
            relatedCharacterContexts = List.copyOf(relatedCharacterContexts); primaryTitleSuccessionCharacterIds = ids(primaryTitleSuccessionCharacterIds, false);
            heldTitlePartition = List.copyOf(heldTitlePartition); Objects.requireNonNull(playerMonthlyGoldIncome); Objects.requireNonNull(playerHealth); Objects.requireNonNull(council);
            RegistryJson.require(playerDomainSize >= 0 && playerDomainLimit > 0 && playerTargetingFactionCount >= 0, "domain/faction range mismatch");
            RegistryJson.require(independent == (immediateLiegeCharacterId == null) && (independent ? topLiegeCharacterId == playerCharacterId : topLiegeCharacterId != playerCharacterId), "liege identity mismatch");
            RegistryJson.require(!Objects.equals(immediateLiegeCharacterId, playerCharacterId) && council.ownerCharacterId() == playerCharacterId, "owner identity mismatch");
            RegistryJson.require(!directLandedVassalCharacterIds.contains(playerCharacterId) && !adjacentExternalProvinceHolderCharacterIds.contains(playerCharacterId)
                    && directLandedVassalCharacterIds.stream().noneMatch(adjacentExternalProvinceHolderCharacterIds::contains), "overlapping relationship identities");
            RegistryJson.require(!primaryTitleSuccessionCharacterIds.contains(playerCharacterId)
                    && (primaryTitle != null || primaryTitleSuccessionCharacterIds.isEmpty()), "succession identity mismatch");
            RegistryJson.require(relatedCharacterContexts.stream().map(Related::characterId).distinct().count() == relatedCharacterContexts.size(), "duplicate related identities");
            List<Integer> relatedVassals = relatedCharacterContexts.stream().filter(row -> row.relationshipRole() == Relation.DIRECT_LANDED_VASSAL).map(Related::characterId).sorted().toList();
            List<Integer> relatedAdjacent = relatedCharacterContexts.stream().filter(row -> row.relationshipRole() == Relation.ADJACENT_EXTERNAL_PROVINCE_HOLDER).map(Related::characterId).sorted().toList();
            RegistryJson.require(relatedVassals.equals(directLandedVassalCharacterIds) && relatedAdjacent.equals(adjacentExternalProvinceHolderCharacterIds), "related identity coverage mismatch");
            RegistryJson.require(heldTitlePartition.stream().map(row -> row.title().titleId()).distinct().count() == heldTitlePartition.size(), "duplicate held-title identity");
            if (primaryTitle == null || primaryTitle.tierRaw() == 1) RegistryJson.require(heldTitlePartition.isEmpty(), "landless/barony player exposes realm partition");
            else {
                List<PartitionRow> primaryRows = heldTitlePartition.stream().filter(PartitionRow::primary).toList();
                Integer heir = primaryTitleSuccessionCharacterIds.isEmpty() ? null : primaryTitleSuccessionCharacterIds.getFirst();
                RegistryJson.require(primaryRows.size() == 1 && primaryRows.getFirst().title().equals(primaryTitle)
                        && Objects.equals(primaryRows.getFirst().firstHeirCharacterId(), heir), "primary partition/heir mismatch");
            }
        }
    }
    public record War(int warId, Side playerSide, Integer primaryOpponentCharacterId, BigInteger playerRelativeWarScore) {
        public War { positive(warId); Objects.requireNonNull(playerSide); nullableCharacter(primaryOpponentCharacterId); Objects.requireNonNull(playerRelativeWarScore); }
    }
    public enum Side { ATTACKER, DEFENDER;
        @com.fasterxml.jackson.annotation.JsonValue public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
    }
    /** E/I are the owning domain's immutable event and interaction records, never an untyped JSON dictionary. */
    public record Snapshot<E,I>(Binding binding, boolean paused, int playerCharacterId, boolean playerCharacterAlive,
            Component<Integer> stressPoints, Component<Fixed> gold, Presence<E> activeEvent,
            Presence<I> pendingCharacterInteraction, Presence<List<War>> activeWars, String backendId) {
        public Snapshot {
            Objects.requireNonNull(binding); NativeCharacterId.of(playerCharacterId); Objects.requireNonNull(stressPoints); Objects.requireNonNull(gold);
            if (stressPoints.status() == Status.AVAILABLE) RegistryJson.require(stressPoints.value() >= 0, "nonnegative stress required");
            Objects.requireNonNull(activeEvent); Objects.requireNonNull(pendingCharacterInteraction); Objects.requireNonNull(activeWars);
            RegistryJson.require(backendId != null && !backendId.isEmpty(), "actual snapshot backend required");
            if (activeWars instanceof Present<List<War>> present) {
                List<War> wars = List.copyOf(present.value()); RegistryJson.require(wars.stream().map(War::warId).distinct().count() == wars.size(), "duplicate wars");
                activeWars = new Present<>(wars);
            }
        }
    }
    static void character(int value) { NativeCharacterId.of(value); }
    static void nullableCharacter(Integer value) { if (value != null) character(value); }
    static void positive(int value) { RegistryJson.require(value > 0, "positive int32 required"); }
    static void nullablePositive(Integer value) { if (value != null) positive(value); }
    static void nonnegative(BigInteger value) { RegistryJson.require(value != null && value.signum() >= 0, "nonnegative exact integer required"); }
    static void positive64(BigInteger value) { RegistryJson.require(value != null && value.signum() > 0 && value.compareTo(RegistryJson.U64) <= 0, "positive uint64 required"); }
    static List<Integer> ids(List<Integer> input, boolean sorted) {
        List<Integer> result = List.copyOf(input); result.forEach(CampaignProjection::character);
        RegistryJson.require(result.stream().distinct().count() == result.size() && (!sorted || result.equals(result.stream().sorted().toList())), "identity vector ordering/uniqueness mismatch"); return result;
    }
}

