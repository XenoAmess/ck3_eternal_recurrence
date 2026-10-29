package org.xar.ck3.control.wave2.military.losssequence;

import static org.xar.ck3.control.wave2.military.losssequence.LossSequenceModel.*;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.wave2.military.armyselector.ArmySelectorModel.Coverage;
import org.xar.ck3.control.wave2.military.armyselector.ArmySelectorModel.DataRecord;
import org.xar.ck3.control.wave2.military.armyselector.ArmySelectorModel.DataSnapshot;
import org.xar.ck3.control.wave2.military.armyselector.RaisedRegimentRefresh.PhysicalChunk;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossModel.LossSequenceSeed;

/** Stored-order four-pass conditional allocation, writer replay and shared current/max refresh. */
public final class LossSequencePolicy {
    private LossSequencePolicy() {}
    private record Key(int persistent, int chunk) {}
    private record PassOutcome(Pass pass, int overflow, boolean complete) {}
    private static final class Working {
        private final List<Regiment> regiments;
        private final List<DataRow> data;
        private final LossSequenceSeed budgets;
        private Working(Input input) {
            regiments = new ArrayList<>(input.regiments()); data = new ArrayList<>(input.data()); budgets = input.budgets();
        }
        private Input frame() { return new Input(true, true, budgets, regiments, data); }
    }

    public static Result project(Input input) {
        if (!input.available() || !input.lossInputsAvailable() || input.regiments() == null) {
            return absent(null, List.of(new MissingField("available_same_query_loss_inputs_and_regiments")));
        }
        LossSequenceSeed budgets = input.budgets();
        if (budgets == null) return absent(null, List.of(new MissingField("signed32_loss_budgets")));
        int combined = budgets.siegeLossBudget() + budgets.raidLossBudget();
        List<MissingInput> missing = new ArrayList<>();
        if (budgets.currentSupplyLossBudget() > 0 || combined > 0) {
            if (input.regiments().stream().anyMatch(row -> !Boolean.TRUE.equals(row.siegeTierObservable()))) {
                missing.add(new MissingField("per_regiment_definition_siege_tier"));
            }
            if (budgets.currentSupplyLossBudget() > 0 && input.regiments().stream().anyMatch(row -> row.nativeSupplyLossEligible() == null)) {
                missing.add(new MissingField("per_regiment_native_2a956d0"));
            }
            if (!missing.isEmpty()) return absent(budgets, missing);
        }
        Working working = new Working(input);
        boolean physicalComplete = working.regiments.stream().allMatch(row -> working.data.stream().anyMatch(
                data -> data.snapshot().regimentId() == row.regimentId() && data.snapshot().status() == Coverage.AVAILABLE));
        Map<Key, Integer> beforePhysical = new LinkedHashMap<>();
        Map<Key, PhysicalChunk> finalPhysical = new LinkedHashMap<>();
        for (DataRow data : working.data) {
            if (data.snapshot().records() == null) continue;
            for (int index = 0; index < data.snapshot().records().size(); index++) {
                if (!data.recordMetadata().get(index).available()) continue;
                DataRecord record = data.snapshot().records().get(index);
                Key key = new Key(record.persistentId(), record.chunkIndex());
                beforePhysical.put(key, record.current());
                finalPhysical.put(key, new PhysicalChunk(key.persistent(), key.chunk(), record.current(), record.maximum()));
            }
        }
        List<Pass> passes = new ArrayList<>();
        String[] prefixes = {"supply", "siege_raid"};
        int[] budgetValues = {budgets.currentSupplyLossBudget(), combined};
        int[] preferredFlags = {3, 1}; int[] residualFlags = {2, 0};
        for (int index = 0; index < prefixes.length; index++) {
            PassOutcome preferred = runPass(working, prefixes[index] + "_preferred", budgetValues[index],
                    preferredFlags[index], passes.isEmpty(), missing, finalPhysical);
            passes.add(preferred.pass());
            boolean complete = preferred.complete();
            if (complete) {
                PassOutcome residual = runPass(working, prefixes[index] + "_residual", preferred.overflow(),
                        residualFlags[index], false, missing, finalPhysical);
                passes.add(residual.pass()); complete = residual.complete();
            }
            if (!complete) return new Result(Status.PARTIAL, false, budgets, passes, missing,
                    null, null, false, null, null);
        }
        List<FinalRegiment> finalRows = new ArrayList<>();
        int finalCurrent = 0;
        for (Regiment row : working.regiments) {
            finalRows.add(new FinalRegiment(row.regimentId(), row.current(), row.maximum())); finalCurrent += row.current();
        }
        Long delta = null;
        if (physicalComplete) {
            delta = 0L;
            for (Map.Entry<Key, PhysicalChunk> entry : finalPhysical.entrySet()) {
                delta += (long) entry.getValue().current() - beforePhysical.get(entry.getKey());
            }
        }
        return new Result(Status.AVAILABLE, true, budgets, passes, missing, finalRows, finalCurrent,
                physicalComplete, physicalComplete ? List.copyOf(finalPhysical.values()) : null, delta);
    }

    /** Integrates actual caller-produced budgets with the same immutable frame; no source observation is altered. */
    public static Result projectWithDerivedBudgets(Input input, LossSequenceSeed budgets) {
        if (budgets == null) throw new IllegalArgumentException("ready derived budget seed required");
        return project(input.withBudgets(budgets));
    }

    private static PassOutcome runPass(Working working, String phase, int budget, int flags, boolean initial,
                                        List<MissingInput> missing, Map<Key, PhysicalChunk> finalPhysical) {
        if (budget <= 0) return new PassOutcome(new Pass(phase, budget, initial, flags, PassStatus.NOT_CALLED,
                null, 0, 0, 0, budget, null, List.of()), 0, true);
        boolean preferred = phase.endsWith("preferred");
        List<Integer> selectedIndices = new ArrayList<>();
        int total = 0;
        for (int index = 0; index < working.regiments.size(); index++) {
            Regiment row = working.regiments.get(index);
            if (((flags & 1) == 0 || row.siegeTier() <= 0)
                    && ((flags & 2) == 0 || Boolean.TRUE.equals(row.nativeSupplyLossEligible()))) {
                selectedIndices.add(index); total += row.current();
            }
        }
        int initialTotal = total;
        int remaining = Math.min(budget, total);
        int capped = remaining;
        int overflow = budget - capped;
        boolean complete = true;
        List<AllocationRequest> requests = new ArrayList<>();
        for (int index : selectedIndices) {
            if (remaining <= 0 || total <= 0) break;
            Regiment row = working.regiments.get(index);
            int current = row.current();
            int product = current * remaining;
            long quantity = (long) product / total;
            WriterRequest request = new WriterRequest(row.regimentId(), quantity * AssociatedChunkWriter.SCALE, AssociatedChunkWriter.SCALE);
            WriterResult writer;
            try { writer = AssociatedChunkWriter.project(working.frame(), request); }
            catch (ArithmeticException error) { writer = AssociatedChunkWriter.arithmeticFailure(request, error); }
            complete = writer.ready() && (Boolean.TRUE.equals(writer.skipped()) || writer.refresh() != null && writer.refresh().ready());
            requests.add(new AllocationRequest(row.regimentId(), current, remaining, total, product, quantity, writer));
            if (!complete) {
                List<String> inputs = new ArrayList<>(writer.missingInputs());
                if (writer.refresh() != null) inputs.addAll(writer.refresh().missingInputs());
                missing.add(new MissingStage(phase, row.regimentId(), inputs)); break;
            }
            if (!Boolean.TRUE.equals(writer.skipped())) applyWriter(working, writer, finalPhysical);
            remaining = (int) (remaining - quantity); total -= current;
        }
        return new PassOutcome(new Pass(phase, budget, initial, flags, complete ? PassStatus.AVAILABLE : PassStatus.PARTIAL,
                initialTotal, capped, preferred ? overflow : 0, preferred ? 0 : overflow, remaining, total, requests), overflow, complete);
    }

    private static void applyWriter(Working working, WriterResult writer, Map<Key, PhysicalChunk> finalPhysical) {
        Map<Key, PhysicalChunk> changes = new LinkedHashMap<>();
        for (PhysicalChunk chunk : writer.physicalChunksAfter()) changes.put(new Key(chunk.persistentId(), chunk.chunkIndex()), chunk);
        for (int index = 0; index < working.data.size(); index++) {
            DataRow row = working.data.get(index); DataSnapshot snapshot = row.snapshot();
            if (snapshot.records() == null) continue;
            List<DataRecord> records = new ArrayList<>();
            for (DataRecord record : snapshot.records()) {
                PhysicalChunk changed = changes.get(new Key(record.persistentId(), record.chunkIndex()));
                records.add(changed == null ? record : new DataRecord(record.recordIndex(), record.persistentId(),
                        record.chunkIndex(), record.state(), changed.current(), changed.maximum()));
            }
            working.data.set(index, new DataRow(new DataSnapshot(snapshot.regimentId(), snapshot.status(), snapshot.lossWriterSkipped(), records), row.recordMetadata()));
        }
        finalPhysical.putAll(changes);
        for (int index = 0; index < working.regiments.size(); index++) {
            Regiment row = working.regiments.get(index);
            if (row.regimentId() == writer.regimentId()) {
                working.regiments.set(index, row.withPair(writer.refresh().current(), writer.refresh().maximum()));
            }
        }
    }

    private static Result absent(LossSequenceSeed budgets, List<MissingInput> missing) {
        return new Result(Status.UNAVAILABLE, false, budgets, List.of(), missing, null, null, false, null, null);
    }
}
