package org.xar.ck3.control.wave2.military.losssequence;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.wave2.military.armyselector.ArmySelectorModel.DataSnapshot;
import org.xar.ck3.control.wave2.military.armyselector.RaisedRegimentRefresh;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossModel.LossSequenceSeed;

/** Conditional associated-DATA projection contracts. No record grants native writer authority. */
public final class LossSequenceModel {
    private LossSequenceModel() {}
    public enum Status { AVAILABLE, PARTIAL, UNAVAILABLE }
    public enum WriterStatus { AVAILABLE, UNAVAILABLE, ARITHMETIC_ERROR }
    public enum PassStatus { AVAILABLE, PARTIAL, NOT_CALLED }
    public record Regiment(int regimentId, Integer current, Integer maximum, Boolean siegeTierObservable,
                           Integer siegeTier, Boolean nativeSupplyLossEligible) {
        public Regiment withPair(int newCurrent, int newMaximum) {
            return new Regiment(regimentId, newCurrent, newMaximum, siegeTierObservable, siegeTier, nativeSupplyLossEligible);
        }
    }
    public record RecordMetadata(boolean available, Integer associatedRegimentId) {}
    /** Shared refresh snapshot carries current/max/state once; metadata adds only writer association/status. */
    public record DataRow(DataSnapshot snapshot, List<RecordMetadata> recordMetadata) {
        public DataRow {
            Objects.requireNonNull(snapshot);
            recordMetadata = recordMetadata == null ? null : List.copyOf(recordMetadata);
            if (snapshot.records() != null && (recordMetadata == null || snapshot.records().size() != recordMetadata.size())) {
                throw new IllegalArgumentException("DATA writer metadata must align with ordered refresh records");
            }
        }
    }
    public record Input(boolean available, boolean lossInputsAvailable, LossSequenceSeed budgets,
                        List<Regiment> regiments, List<DataRow> data) {
        public Input {
            regiments = regiments == null ? null : List.copyOf(regiments); data = List.copyOf(data);
        }
        public Input withBudgets(LossSequenceSeed seed) { return new Input(available, true, seed, regiments, data); }
    }
    public record WriterRequest(int regimentId, long quantityRaw, int quantityScale) {
        public WriterRequest { if (quantityScale != 100_000) throw new IllegalArgumentException("writer_quantity_scale must be 100000"); }
    }
    public record Write(int pass, int recordIndex, int persistentId, int chunkIndex, int currentBefore,
                        int effectiveCurrent, long selectedQuantityRaw, int currentAfter) {}
    public record WriterResult(WriterStatus status, int regimentId, Boolean skipped,
                               RaisedRegimentRefresh.Result refresh, List<String> missingInputs,
                               List<Write> writes, List<RaisedRegimentRefresh.PhysicalChunk> physicalChunksAfter,
                               Long remainingQuantityRaw, Long physicalCurrentDelta, String arithmeticError) {
        public WriterResult {
            Objects.requireNonNull(status); missingInputs = List.copyOf(missingInputs); writes = List.copyOf(writes);
            physicalChunksAfter = List.copyOf(physicalChunksAfter);
        }
        public boolean ready() { return status == WriterStatus.AVAILABLE; }
    }
    public record AllocationRequest(int regimentId, int currentRead, int remainingBudgetBefore,
                                    int remainingEligibleBefore, int multiplySigned32, long requestedSoldiers,
                                    WriterResult writer) {}
    public record Pass(String phase, int requestBudget, boolean initialStage, int filterFlags,
                       PassStatus status, Integer eligibleTotal, int cappedBudget, int callerOverflow,
                       int unallocatedOverflow, int remainingBudget, Integer remainingEligible,
                       List<AllocationRequest> requests) {
        public Pass { requests = List.copyOf(requests); }
    }
    public sealed interface MissingInput permits MissingField, MissingStage {}
    public record MissingField(String input) implements MissingInput { public MissingField { Objects.requireNonNull(input); } }
    public record MissingStage(String phase, int regimentId, List<String> inputs) implements MissingInput {
        public MissingStage { inputs = List.copyOf(inputs); }
    }
    public record FinalRegiment(int regimentId, int current, int maximum) {}
    public record Result(Status status, boolean ready, LossSequenceSeed budgets, List<Pass> passes,
                         List<MissingInput> missingInputs, List<FinalRegiment> finalRegiments,
                         Integer finalCurrentSoldiers, boolean physicalChunksReady,
                         List<RaisedRegimentRefresh.PhysicalChunk> physicalChunksAfter,
                         Long physicalCurrentDelta) {
        public Result {
            passes = List.copyOf(passes); missingInputs = List.copyOf(missingInputs);
            finalRegiments = finalRegiments == null ? null : List.copyOf(finalRegiments);
            physicalChunksAfter = physicalChunksAfter == null ? null : List.copyOf(physicalChunksAfter);
        }
        public boolean actualLoss() { return false; }
    }
}
