package org.xar.ck3.control.governance.development;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilModels;

/** Distinguishes current native material from the historical AI/action fixture profile. */
public final class DevelopmentModels {
    private DevelopmentModels() { }
    public record Frame(BigInteger nativeRevision, int dateRaw) {
        public Frame { CouncilModels.uint64(nativeRevision, true); }
    }
    public record Provenance(String gameVersion, String executableSha256, String backendId,
            String readerMode, String nextReverseEngineeringEntry) {
        public Provenance {
            StrictJson.text(gameVersion); StrictJson.text(executableSha256); StrictJson.text(backendId);
            StrictJson.text(readerMode); StrictJson.text(nextReverseEngineeringEntry);
        }
    }
    public sealed interface Observation permits Material, Legacy, Unavailable {
        Frame frame(); Provenance provenance(); CouncilModels.JsonBody original();
    }
    public enum Profile { NATIVE_MATERIAL, LEGACY_AI_FIXTURE }
    public enum ProgressKind { INFINITE, PERCENTAGE, VALUE }
    public record Progress(ProgressKind kind, Optional<CouncilModels.Fixed> current, Optional<CouncilModels.Fixed> maximum) {
        public Progress {
            Objects.requireNonNull(kind); Objects.requireNonNull(current); Objects.requireNonNull(maximum);
            StrictJson.require((kind == ProgressKind.INFINITE) == current.isEmpty() && current.isPresent() == maximum.isPresent(), "task progress presence mismatch");
            if (current.isPresent()) {
                long raw = current.orElseThrow().raw(), max = maximum.orElseThrow().raw();
                StrictJson.require(raw >= 0 && max > 0 && raw <= max, "task progress outside source range");
                StrictJson.require(kind != ProgressKind.PERCENTAGE || max == 10_000_000L, "percentage task maximum differs from 100 percent");
            }
        }
    }
    public sealed interface Target permits General, County, Court { }
    public record General() implements Target { }
    public record County(int provinceId) implements Target { public County { StrictJson.require(provinceId > 0, "county province ID required"); } }
    public record Court(long characterId) implements Target { public Court { unsignedId(characterId); } }
    public record Binding(long stewardId, String taskKey, Target target, boolean frozen, Progress progress) {
        public Binding { unsignedId(stewardId); stable(taskKey); Objects.requireNonNull(target); Objects.requireNonNull(progress); }
    }
    public record MaterialCandidate(long countyTitleId, int capitalProvinceId, long holderId,
            boolean playerCapital, boolean directlyHeld, long nativeCollectionOrdinal, boolean nativeTargetValid,
            CouncilModels.Fixed monthlyRate, CouncilModels.Fixed currentProgress, CouncilModels.Fixed maximumProgress) {
        public MaterialCandidate {
            unsignedId(countyTitleId); unsignedId(holderId); StrictJson.require(capitalProvinceId > 0, "candidate province ID required");
            StrictJson.require(nativeCollectionOrdinal >= 0 && nativeCollectionOrdinal <= 0xffff_ffffL, "native collection ordinal outside uint32");
            Objects.requireNonNull(monthlyRate); Objects.requireNonNull(currentProgress); Objects.requireNonNull(maximumProgress);
        }
    }
    public record Material(Frame frame, Provenance provenance, long playerId, long stewardId, boolean shown,
            boolean valid, Optional<String> taskFailureReason, Binding currentBinding,
            List<MaterialCandidate> candidates, CouncilModels.JsonBody original) implements Observation {
        public Material {
            Objects.requireNonNull(frame); Objects.requireNonNull(provenance); unsignedId(playerId); unsignedId(stewardId);
            Objects.requireNonNull(taskFailureReason); Objects.requireNonNull(currentBinding); candidates = List.copyOf(candidates); Objects.requireNonNull(original);
            StrictJson.require(currentBinding.stewardId() == stewardId, "current binding has another Steward");
            StrictJson.require(shown && valid ? taskFailureReason.isEmpty()
                    : taskFailureReason.equals(Optional.of(!shown ? "task_not_shown" : "task_invalid")) && candidates.isEmpty(),
                    "task visibility/legality/failure reason mismatch");
        }
    }
    public record LegacyCandidate(int countyTitleId, int capitalProvinceId, int holderId,
            boolean playerCapital, boolean directlyHeld, int developmentLevelRaw, long developmentProgressRaw,
            long monthlyRateRaw, int maximumDevelopmentLevelRaw, String terrainKey,
            boolean sameCulture, boolean culturalAcceptanceThresholdPassed) {
        public LegacyCandidate {
            StrictJson.require(countyTitleId > 0 && capitalProvinceId > 0 && holderId > 0
                    && developmentLevelRaw >= 0 && maximumDevelopmentLevelRaw >= 0, "legacy candidate identity/range mismatch"); stable(terrainKey);
        }
    }
    public record Legacy(Frame frame, Provenance provenance, int playerId, int stewardId, boolean shown,
            boolean valid, Optional<String> taskFailureReason, long increaseDevelopmentValueRaw, long currentGoldRaw,
            boolean noAiIncreaseDevelopment, boolean hasActiveImproveDirective, List<LegacyCandidate> candidates,
            CouncilModels.JsonBody original) implements Observation {
        public Legacy {
            Objects.requireNonNull(frame); Objects.requireNonNull(provenance); StrictJson.require(playerId > 0 && stewardId > 0, "legacy player/steward IDs required");
            Objects.requireNonNull(taskFailureReason); candidates = List.copyOf(candidates); Objects.requireNonNull(original);
            StrictJson.require(shown && valid ? taskFailureReason.isEmpty() : taskFailureReason.isPresent() && candidates.isEmpty(), "legacy task visibility/failure mismatch");
        }
    }
    public record Unavailable(Frame frame, Provenance provenance, Profile profile, Optional<Integer> observedDateRaw,
            String reason, CouncilModels.JsonBody original) implements Observation {
        public Unavailable {
            Objects.requireNonNull(frame); Objects.requireNonNull(provenance); Objects.requireNonNull(profile); Objects.requireNonNull(observedDateRaw);
            stable(reason); Objects.requireNonNull(original);
            StrictJson.require(observedDateRaw.isEmpty() || observedDateRaw.orElseThrow() == frame.dateRaw(), "unavailable observed date drift");
        }
    }
    public static void unsignedId(long value) { StrictJson.require(value > 0 && value <= 0xffff_ffffL, "full uint32 native identity required"); }
    public static String stable(String value) { StrictJson.require(value != null && value.matches("[a-z0-9_]+"), "stable key required"); return value; }
}
