package org.xar.ck3.control.wave2.runtime.performancewindows;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.MathContext;
import java.math.RoundingMode;
import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Arithmetic over sealed historical projections. No clock, live reader, SAVE credit or speedup verdict. */
public final class HistoricalPerformanceWindows {
    public static final String SCHEMA = "xar.sealed-performance-window-projection.v1";
    public static final int SOURCE_MAX_BYTES = 1_048_576;
    public static final String SCOPE = "new arithmetic from sealed historical small evidence; no new runtime timings";
    private HistoricalPerformanceWindows() { }

    public enum SourceRole {
        P49_SETTLED("p49-settled-performance.json"),
        P49_STAGES("p49-stage-slice.json"),
        P63("p63-r6-performance-and-normal-sdk-close-2026-10-18.json"),
        P67("p67-p68-combat-query-archive-performance-2026-10-18.json");
        private final String filename;
        SourceRole(String filename) { this.filename = filename; }
        public String filename() { return filename; }
        public String relativePath() { return "docs/ck3-native-ai/evidence/" + filename; }
    }

    public record SourceInput(SourceRole role, byte[] bytes) {
        public SourceInput {
            Objects.requireNonNull(role, "role");
            StrictJson.require(bytes != null && bytes.length > 0 && bytes.length <= SOURCE_MAX_BYTES,
                    "only bounded sealed source bytes admitted");
            bytes = bytes.clone();
        }
        @Override public byte[] bytes() { return bytes.clone(); }
        @Override public boolean equals(Object other) {
            return other instanceof SourceInput value && role == value.role && Arrays.equals(bytes, value.bytes);
        }
        @Override public int hashCode() { return 31 * role.hashCode() + Arrays.hashCode(bytes); }
    }

    public record SourceReference(String path, int bytes, String sha256) {
        public SourceReference {
            StrictJson.text(path);
            StrictJson.require(bytes > 0 && bytes <= SOURCE_MAX_BYTES, "bounded source reference required");
            StrictJson.require(sha256 != null && sha256.matches("[0-9a-f]{64}"), "exact lowercase SHA-256 required");
        }
    }

    /** Execution labels supplied by the owner; they do not reassign historical source machines. */
    public record Context(String machineId, String observedUtc, String reviewUtc) {
        public Context {
            StrictJson.text(machineId); StrictJson.utc(observedUtc); StrictJson.utc(reviewUtc);
        }
    }

    public sealed interface MachineMarker permits MissingMachine, NullMachine, NamedMachine { }
    public record MissingMachine() implements MachineMarker { }
    public record NullMachine() implements MachineMarker { }
    public record NamedMachine(String value) implements MachineMarker {
        public NamedMachine { StrictJson.text(value); }
    }

    /** Retain declared extra evidence fields without promoting them to domain/qualification inputs. */
    public record AutoGroup(BigInteger count, double autoSeconds, BigInteger gameDays, ObjectNode sourceValue) {
        public AutoGroup {
            nonnegative(count); nonnegative(gameDays); seconds(autoSeconds);
            Objects.requireNonNull(sourceValue, "sourceValue");
            JsonNode sourceCount = sourceValue.get("count"); JsonNode sourceDays = sourceValue.get("game_days");
            JsonNode sourceElapsed = sourceValue.get("auto_seconds");
            StrictJson.require(sourceCount != null && sourceCount.isIntegralNumber() && count.equals(sourceCount.bigIntegerValue())
                    && sourceDays != null && sourceDays.isIntegralNumber() && gameDays.equals(sourceDays.bigIntegerValue()),
                    "copied group integer fields must match their typed projection");
            StrictJson.require(sourceElapsed != null && sourceElapsed.isNumber()
                    && Double.compare(sourceElapsed.doubleValue(), autoSeconds) == 0,
                    "copied group elapsed must match its typed projection");
            sourceValue = sourceValue.deepCopy();
        }
        @Override public ObjectNode sourceValue() { return sourceValue.deepCopy(); }
    }

    public record SettledWindow(MachineMarker machine, BigInteger gameDays, double wallSeconds,
                                BigInteger turns, BigInteger zeroDateTurns, double autoSeconds,
                                double rpcBusyUnionSeconds, double unattributedGapSeconds,
                                Map<String, AutoGroup> groups) {
        public SettledWindow {
            Objects.requireNonNull(machine, "machine"); nonnegative(gameDays); positive(turns);
            nonnegative(zeroDateTurns); seconds(wallSeconds); seconds(autoSeconds); seconds(rpcBusyUnionSeconds);
            StrictJson.require(Double.isFinite(unattributedGapSeconds), "finite unattributed gap required");
            StrictJson.require(zeroDateTurns.compareTo(turns) <= 0, "zero-date turns cannot exceed turns");
            groups = Collections.unmodifiableMap(new LinkedHashMap<>(groups));
        }
    }

    public record StageStats(BigInteger count, double sumSeconds, double maxSeconds) {
        public StageStats { nonnegative(count); seconds(sumSeconds); seconds(maxSeconds); }
    }

    public record StageSlice(MachineMarker machine, String lowerSourceClock, String upperSourceClock,
                             double dateChangedWaitSeconds, double sameDateWaitSeconds,
                             double planUniqueWallSeconds, double nativeWaitWithinPlanSeconds,
                             double semanticSnapshotWithinPlanSeconds, StageStats persistence,
                             StageStats stream, StageStats serialization) {
        public StageSlice {
            Objects.requireNonNull(machine, "machine"); StrictJson.text(lowerSourceClock); StrictJson.text(upperSourceClock);
            seconds(dateChangedWaitSeconds); seconds(sameDateWaitSeconds); seconds(planUniqueWallSeconds);
            seconds(nativeWaitWithinPlanSeconds); seconds(semanticSnapshotWithinPlanSeconds);
            Objects.requireNonNull(persistence, "persistence"); Objects.requireNonNull(stream, "stream");
            Objects.requireNonNull(serialization, "serialization");
            StrictJson.require(persistence.sumSeconds() > 0, "nonzero persistence denominator required");
        }
    }

    /** Existing producer forwards these historical windows; no live or same-state A/B assertion is added. */
    public static final class CopiedRateWindow {
        private final ObjectNode sourceValue;
        private CopiedRateWindow(ObjectNode sourceValue) { this.sourceValue = sourceValue.deepCopy(); }
        public ObjectNode sourceValue() { return sourceValue.deepCopy(); }
    }
    static CopiedRateWindow copiedRateWindow(ObjectNode validatedSource) { return new CopiedRateWindow(validatedSource); }

    public record Inputs(Context context, List<SourceReference> sources, SettledWindow settled,
                         StageSlice stages, String p63MachineId, CopiedRateWindow r6, CopiedRateWindow r5) {
        public Inputs {
            Objects.requireNonNull(context, "context"); sources = List.copyOf(sources);
            StrictJson.require(sources.size() == SourceRole.values().length, "all four historical sources required");
            Objects.requireNonNull(settled, "settled"); Objects.requireNonNull(stages, "stages");
            StrictJson.text(p63MachineId); Objects.requireNonNull(r6, "r6"); Objects.requireNonNull(r5, "r5");
        }
    }

    public static final class Projection {
        private final Inputs inputs;
        private final Map<String, AutoGroup> zeroDateGroups;
        private final double zeroDateAutoSeconds;
        private final double progressAutoSeconds;
        private final double zeroDateTurnFraction;
        private final double streamFractionOfPersistence;
        private Projection(Inputs inputs, Map<String, AutoGroup> zeroDateGroups, double zeroDateAutoSeconds,
                           double progressAutoSeconds, double zeroDateTurnFraction, double streamFractionOfPersistence) {
            this.inputs = Objects.requireNonNull(inputs, "inputs");
            this.zeroDateGroups = Collections.unmodifiableMap(new LinkedHashMap<>(zeroDateGroups));
            seconds(zeroDateAutoSeconds); seconds(progressAutoSeconds); seconds(zeroDateTurnFraction); seconds(streamFractionOfPersistence);
            this.zeroDateAutoSeconds = zeroDateAutoSeconds; this.progressAutoSeconds = progressAutoSeconds;
            this.zeroDateTurnFraction = zeroDateTurnFraction; this.streamFractionOfPersistence = streamFractionOfPersistence;
        }
        public Inputs inputs() { return inputs; }
        public Map<String, AutoGroup> zeroDateGroups() { return zeroDateGroups; }
        public double zeroDateAutoSeconds() { return zeroDateAutoSeconds; }
        public double progressAutoSeconds() { return progressAutoSeconds; }
        public double zeroDateTurnFraction() { return zeroDateTurnFraction; }
        public double streamFractionOfPersistence() { return streamFractionOfPersistence; }
    }

    public static Projection project(Inputs inputs) {
        Objects.requireNonNull(inputs, "inputs");
        LinkedHashMap<String, AutoGroup> zeroGroups = new LinkedHashMap<>();
        BigInteger zeroCount = BigInteger.ZERO;
        double zeroSeconds = 0.0;
        double progressSeconds = 0.0;
        for (Map.Entry<String, AutoGroup> entry : inputs.settled().groups().entrySet()) {
            AutoGroup group = entry.getValue();
            if (group.gameDays().signum() == 0) {
                zeroGroups.put(entry.getKey(), group);
                zeroCount = zeroCount.add(group.count());
                zeroSeconds += group.autoSeconds();
            } else { progressSeconds += group.autoSeconds(); }
        }
        StrictJson.require(zeroCount.equals(inputs.settled().zeroDateTurns()), "zero-date row count differs");
        StrictJson.require(Math.abs(zeroSeconds + progressSeconds - inputs.settled().autoSeconds()) < 1e-7,
                "AUTO group elapsed sum differs");
        // Exact integer ratio converted once to binary64; source numeric tokens have at most 1000 digits.
        double fraction = new BigDecimal(inputs.settled().zeroDateTurns()).divide(
                new BigDecimal(inputs.settled().turns()), new MathContext(1_100, RoundingMode.HALF_EVEN)).doubleValue();
        return new Projection(inputs, zeroGroups, zeroSeconds, progressSeconds, fraction,
                inputs.stages().stream().sumSeconds() / inputs.stages().persistence().sumSeconds());
    }

    static void nonnegative(BigInteger value) {
        StrictJson.require(value != null && value.signum() >= 0, "nonnegative exact integer required");
    }
    private static void positive(BigInteger value) {
        StrictJson.require(value != null && value.signum() > 0, "positive exact integer required");
    }
    static void seconds(double value) {
        StrictJson.require(Double.isFinite(value) && value >= 0, "finite nonnegative seconds required");
    }
}
