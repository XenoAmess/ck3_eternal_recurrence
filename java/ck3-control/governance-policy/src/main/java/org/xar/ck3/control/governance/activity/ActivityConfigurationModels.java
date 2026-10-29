package org.xar.ck3.control.governance.activity;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Shared native Feast configuration observations. None of these records authorizes Start. */
public final class ActivityConfigurationModels {
    private ActivityConfigurationModels() { }
    public record Frame(BigInteger nativeRevision, BigInteger dateRaw, BigInteger actorId) {
        public Frame {
            need(nativeRevision != null && nativeRevision.signum() > 0 && nativeRevision.bitLength() <= 64, "native revision");
            need(dateRaw != null && dateRaw.signum() >= 0 && dateRaw.bitLength() <= 31, "native date");
            need(actorId != null && actorId.signum() > 0 && actorId.bitLength() <= 32, "full actor ID");
        }
    }
    public record StageOne(Frame frame, boolean shown, boolean valid, boolean canProgress, boolean ready, Obj original) {
        public StageOne { Objects.requireNonNull(frame); Objects.requireNonNull(original); need(ready == (shown && valid && canProgress), "stage one predicate"); }
    }
    public record StageTwo(Frame frame, boolean genericFeastSelected, Obj original) {
        public StageTwo { Objects.requireNonNull(frame); Objects.requireNonNull(original); need(genericFeastSelected, "stage two selected option"); }
    }
    public record ConfigurationRow(int index, Optional<Integer> phaseKind, long provinceId, boolean active) {
        public ConfigurationRow { Objects.requireNonNull(phaseKind); need(index >= 0 && index < 128 && provinceId >= 0 && provinceId <= 0xffff_ffffL, "configuration row"); phaseKind.ifPresent(value -> need(value >= 0, "phase kind")); }
    }
    public record Candidate(int provinceId, boolean canSelect) { public Candidate { need(provinceId > 0, "candidate province ID"); } }
    public record Location(Frame frame, List<ConfigurationRow> rows, Optional<Integer> activeRowIndex, boolean singleLocation,
            int previousStage, List<Candidate> candidates, boolean canProgress, Obj original) {
        public Location {
            Objects.requireNonNull(frame); rows = List.copyOf(rows); candidates = List.copyOf(candidates); Objects.requireNonNull(original); Objects.requireNonNull(activeRowIndex);
            need(rows.size() <= 128 && candidates.size() >= 1 && candidates.size() <= 8, "location bounds");
            if (activeRowIndex.isPresent()) need(activeRowIndex.orElseThrow() >= 0 && activeRowIndex.orElseThrow() < rows.size(), "active row range");
            need(previousStage >= 0 && previousStage <= 5, "previous stage");
            need(candidates.stream().map(Candidate::provinceId).distinct().count() == candidates.size(), "duplicate candidates");
            for (int index = 0; index < rows.size(); index++) need(rows.get(index).index() == index && rows.get(index).active() == (index == activeRowIndex.orElse(-1)), "active row binding");
        }
    }
    public record StageTwoGate(Frame frame, int rowCount, List<Integer> failingIndices, boolean canProgress, boolean ready, Obj original) {
        public StageTwoGate { Objects.requireNonNull(frame); failingIndices = List.copyOf(failingIndices); Objects.requireNonNull(original); need(rowCount >= 0 && rowCount <= 128, "gate row count"); need(failingIndices.stream().distinct().count() == failingIndices.size(), "gate duplicate rows"); for (int index : failingIndices) need(index >= 0 && index < rowCount, "gate row index"); need(ready == canProgress, "gate readiness"); }
    }
    private static void need(boolean condition, String reason) { if (!condition) throw new IllegalArgumentException(reason); }
}
