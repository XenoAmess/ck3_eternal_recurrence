package org.xar.ck3.control.wave2.military.losssequence;

import static org.xar.ck3.control.wave2.military.losssequence.LossSequenceModel.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.wave2.military.armyselector.ArmySelectorModel.Coverage;
import org.xar.ck3.control.wave2.military.armyselector.ArmySelectorModel.DataRecord;
import org.xar.ck3.control.wave2.military.armyselector.RaisedRegimentRefresh;
import org.xar.ck3.control.wave2.military.armyselector.RaisedRegimentRefresh.PhysicalChunk;

/** Complete associated 26341B0 pure replay, with the distinct trapping IDIV contract. */
public final class AssociatedChunkWriter {
    public static final int SCALE = 100_000;
    private static final long FAST_DIVIDE_BOUND = 0x53E2D6238DA3L;
    private AssociatedChunkWriter() {}
    private record Key(int persistentId, int chunkIndex) {}
    private record Chunk(int current, int maximum, int state) {}

    /** Native signed IDIV traps on zero denominator and on a signed64 quotient overflow. */
    public static long signedDivide(long numerator, long denominator) {
        if (denominator == 0) throw new ArithmeticException("native signed IDIV denominator is zero");
        if (numerator == Long.MIN_VALUE && denominator == -1) {
            throw new ArithmeticException("native signed64 IDIV quotient overflow");
        }
        return numerator / denominator;
    }

    /** Unlike the LAND rate divider, zero traps and abs(MIN) is mathematically positive. */
    public static long nativeQDivide(long numerator, long denominator) {
        if (numerator >= -FAST_DIVIDE_BOUND && numerator <= FAST_DIVIDE_BOUND) {
            return signedDivide(numerator * SCALE, denominator);
        }
        if (BigInteger.valueOf(denominator).abs().compareTo(BigInteger.valueOf(10_000_000_000L)) >= 0) {
            return signedDivide(numerator, signedDivide(denominator, SCALE));
        }
        long multiple = signedDivide(numerator, SCALE) * SCALE;
        long remainder = numerator - multiple;
        long whole = signedDivide(multiple, denominator);
        long residual = multiple - whole * denominator;
        return signedDivide(remainder * SCALE, denominator) + signedDivide(residual * SCALE, denominator) + whole * SCALE;
    }

    public static WriterResult project(Input input, WriterRequest request) {
        Regiment strength = input.regiments() == null ? null : input.regiments().stream()
                .filter(row -> row.regimentId() == request.regimentId()).findFirst().orElse(null);
        DataRow data = input.data().stream().filter(row -> row.snapshot().regimentId() == request.regimentId()).findFirst().orElse(null);
        if (strength == null || data == null) return missing(request, "matching_native_regiment_and_DATA");
        Boolean skipped = data.snapshot().lossWriterSkipped();
        if (skipped == null) return missing(request, "native_loss_writer_skipped");
        if (skipped) return new WriterResult(WriterStatus.AVAILABLE, request.regimentId(), true, null,
                List.of(), List.of(), List.of(), request.quantityRaw(), 0L, null);
        List<DataRecord> records = data.snapshot().records();
        if (data.snapshot().status() != Coverage.AVAILABLE || records == null) return missing(request, "complete_available_DATA");
        if (data.recordMetadata().stream().anyMatch(row -> row.associatedRegimentId() == null
                || row.associatedRegimentId() != request.regimentId())) {
            return missing(request, "observed_associated_chunk_army_regiment_id");
        }
        Map<Key, Chunk> chunks = new LinkedHashMap<>();
        List<Key> order = new ArrayList<>();
        for (DataRecord row : records) {
            if (row.current() == null || row.maximum() == null || row.state() == null) {
                return missing(request, "complete_chunk_current_maximum_state");
            }
            Key key = new Key(row.persistentId(), row.chunkIndex());
            Chunk values = new Chunk(row.current(), row.maximum(), row.state());
            if (chunks.containsKey(key) && !chunks.get(key).equals(values)) {
                throw new org.xar.ck3.control.contracts.projection.ProjectionDomainRejection("aliased DATA physical chunk inputs differ in the same frame");
            }
            chunks.put(key, values); order.add(key);
        }
        long before = chunks.values().stream().mapToLong(Chunk::current).sum();
        long remaining = request.quantityRaw();
        List<Write> writes = new ArrayList<>();
        if (strength.current() == null) return missing(request, "native_ArRg_current_soldiers");
        if (strength.current() != 0) {
            for (int pass = 1; pass <= 2; pass++) {
                if (pass == 2 && remaining < 0) break;
                for (int index = 0; index < order.size(); index++) {
                    Key key = order.get(index); Chunk chunk = chunks.get(key);
                    int current = chunk.current();
                    int effective = chunk.state() == 3 && current == 0 ? chunk.maximum() : current;
                    if (pass == 1 && effective == 0) continue;
                    long cap = (long) effective * SCALE;
                    long selected;
                    if (pass == 1) {
                        selected = cap == 0 ? cap : Math.min(nativeQDivide(effective * request.quantityRaw(), cap), cap);
                        selected = Math.min(selected, remaining);
                    } else selected = Math.min(cap, remaining);
                    int after = (int) (current - signedDivide(selected, SCALE));
                    chunks.put(key, new Chunk(after, chunk.maximum(), chunk.state()));
                    writes.add(new Write(pass, index, key.persistentId(), key.chunkIndex(), current, effective, selected, after));
                    remaining -= selected;
                    if (remaining <= 0) break;
                }
            }
        }
        List<PhysicalChunk> after = new ArrayList<>();
        chunks.forEach((key, chunk) -> after.add(new PhysicalChunk(key.persistentId(), key.chunkIndex(), chunk.current(), chunk.maximum())));
        long delta = chunks.values().stream().mapToLong(Chunk::current).sum() - before;
        return new WriterResult(WriterStatus.AVAILABLE, request.regimentId(), false,
                RaisedRegimentRefresh.project(data.snapshot(), after), List.of(), writes, after, remaining, delta, null);
    }

    static WriterResult arithmeticFailure(WriterRequest request, ArithmeticException error) {
        return new WriterResult(WriterStatus.ARITHMETIC_ERROR, request.regimentId(), null, null,
                List.of("native_signed_division_result"), List.of(), List.of(), null, null, error.getMessage());
    }
    private static WriterResult missing(WriterRequest request, String field) {
        return new WriterResult(WriterStatus.UNAVAILABLE, request.regimentId(), null, null,
                List.of(field), List.of(), List.of(), null, null, null);
    }
}
