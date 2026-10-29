package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.UInt64;
import org.xar.ck3.control.nativebridge.capabilities.army.LocalTargetScore12004.Scope;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;

/** Original 1A08EE9 quantization and 1A08F7F append operands, never a complete pair score or action. */
public final class PairTargetScoreTerminal12004 {
    public static final int APPEND_CALL_RVA = 0x1A08F7F;
    public static final long SCALE = 100_000;
    public static final int RECORD_REASON_ALLOCATOR_RVA = 0x54DEB88;
    private PairTargetScoreTerminal12004() { }

    /** Native pointer identities are scoped addresses, not public army/province IDs. Reasons stay opaque. */
    public record PairKey(UInt64 stackEntryIdentity, UInt64 stackObjectIdentity, int stackIndex,
                          UInt64 provinceIdentity, int kindRaw, UInt64 reasonVectorIdentity) {
        public PairKey {
            pointer(stackEntryIdentity); pointer(stackObjectIdentity); pointer(provinceIdentity); pointer(reasonVectorIdentity);
            if (kindRaw < 0 || kindRaw > 255) throw new IllegalArgumentException("native unsigned kind byte required");
        }
    }
    public record Facts(Scope scope, PairKey pair, long originalRbxRaw, int originalScoreArgument) {
        public Facts { Objects.requireNonNull(scope); Objects.requireNonNull(pair); }
    }
    public sealed interface Observation permits Available, Incomplete { Scope scope(); }
    public record Available(Facts facts) implements Observation {
        public Available { Objects.requireNonNull(facts); }
        @Override public Scope scope() { return facts.scope(); }
    }
    public record Incomplete(Scope scope, String reason) implements Observation {
        public Incomplete { Objects.requireNonNull(scope); diagnostic(reason); }
    }
    public sealed interface Result permits ObservedAppendOperands, ObservedAppendRecord, NotReady { }
    public record ObservedAppendOperands(PairKey pair, long originalRbxRaw, long snappedRaw, int integerScore) implements Result {
        public ObservedAppendOperands { Objects.requireNonNull(pair); }
    }
    public record NotReady(String reason) implements Result { public NotReady { diagnostic(reason); } }

    /** Java long multiplication has the original low64 wrap. The second division must remain after it. */
    private static long snap(long raw) {
        long quotient = raw / SCALE;
        long snapped = quotient * SCALE;
        if (raw != snapped) snapped = (quotient + (raw > 0 ? 1 : 0)) * SCALE;
        return snapped;
    }
    /** Requires the current original pair identity as well as the same coordinator/update source. */
    public static Result consume(Scope current, PairKey currentOriginalPair, Observation originalRead) {
        Objects.requireNonNull(current); Objects.requireNonNull(currentOriginalPair); Objects.requireNonNull(originalRead);
        if (!current.equals(originalRead.scope())) return new NotReady("coordinator_update_or_source_changed");
        if (originalRead instanceof Incomplete missing) return new NotReady(missing.reason());
        Facts facts = ((Available) originalRead).facts();
        if (!currentOriginalPair.equals(facts.pair())) return new NotReady("original_pair_or_reason_source_changed");
        long snapped = snap(facts.originalRbxRaw());
        int integerScore = (int) (snapped / SCALE);
        if (integerScore != facts.originalScoreArgument()) return new NotReady("original_terminal_score_argument_mismatch");
        return new ObservedAppendOperands(facts.pair(), facts.originalRbxRaw(), snapped, integerScore);
    }

    public static Observation decode(byte[] wire) {
        ObjectNode n = closed(parse(wire), "schema_version", "stage_rva", "scope", "status", "reason", "facts");
        if (i32(n.get("schema_version")) != 1 || i32(n.get("stage_rva")) != APPEND_CALL_RVA)
            throw new IllegalArgumentException("exact terminal stage required");
        Scope scope = LocalTargetScore12004.scope(n.get("scope"));
        String status = text(n.get("status"));
        if (status.equals("incomplete")) {
            if (!n.get("facts").isNull()) throw new IllegalArgumentException("incomplete facts must be explicit null");
            return new Incomplete(scope, text(n.get("reason")));
        }
        if (!status.equals("available") || !n.get("reason").isNull()) throw new IllegalArgumentException("terminal discriminant differs");
        ObjectNode f = closed(n.get("facts"), "pair", "original_rbx_raw", "original_score_argument");
        ObjectNode p = closed(f.get("pair"), "stack_entry_identity", "stack_object_identity", "stack_index", "province_identity", "kind_raw", "reason_vector_identity");
        PairKey pair = new PairKey(identity(text(p.get("stack_entry_identity"))), identity(text(p.get("stack_object_identity"))),
            i32(p.get("stack_index")), identity(text(p.get("province_identity"))), i32(p.get("kind_raw")), identity(text(p.get("reason_vector_identity"))));
        return new Available(new Facts(scope, pair, PairTargetScoreFactor12004.signed64(text(f.get("original_rbx_raw"))), i32(f.get("original_score_argument"))));
    }
    public static byte[] encode(Observation observation) {
        Objects.requireNonNull(observation);
        ObjectNode n = empty(); n.put("schema_version", 1); n.put("stage_rva", APPEND_CALL_RVA);
        n.set("scope", LocalTargetScore12004.encodeScope(observation.scope()));
        if (observation instanceof Incomplete missing) {
            n.put("status", "incomplete"); n.put("reason", missing.reason()); n.putNull("facts"); return bytes(n);
        }
        Facts f = ((Available) observation).facts(); n.put("status", "available"); n.putNull("reason");
        ObjectNode facts = n.putObject("facts"); facts.put("original_rbx_raw", Long.toString(f.originalRbxRaw()));
        facts.put("original_score_argument", f.originalScoreArgument()); PairKey key = f.pair(); ObjectNode p = facts.putObject("pair");
        p.put("stack_entry_identity", key.stackEntryIdentity().decimal()); p.put("stack_object_identity", key.stackObjectIdentity().decimal());
        p.put("stack_index", key.stackIndex()); p.put("province_identity", key.provinceIdentity().decimal());
        p.put("kind_raw", key.kindRaw()); p.put("reason_vector_identity", key.reasonVectorIdentity().decimal());
        return bytes(n);
    }
    private static UInt64 identity(String value) {
        if (!value.matches("[1-9][0-9]{0,19}")) throw new IllegalArgumentException("canonical positive uint64 pointer string required");
        return UInt64.positive(new BigInteger(value));
    }
    private static void pointer(UInt64 value) {
        Objects.requireNonNull(value);
        if (value.value().signum() <= 0) throw new IllegalArgumentException("nonnull native pointer identity required");
    }
    private static void diagnostic(String value) {
        Objects.requireNonNull(value);
        if (!value.matches("[a-z0-9_]{1,128}")) throw new IllegalArgumentException("bounded diagnostic required");
    }

    public record VectorStorage(UInt64 dataIdentity, int capacity, int count, UInt64 allocatorIdentity) {
        public VectorStorage {
            Objects.requireNonNull(dataIdentity); pointer(allocatorIdentity);
            if (capacity < 0 || count < 0 || count > capacity || capacity > 0 && dataIdentity.value().signum() == 0)
                throw new IllegalArgumentException("native vector storage bounds differ");
        }
    }
    public record VectorHeader(UInt64 address, VectorStorage storage) {
        public VectorHeader { pointer(address); Objects.requireNonNull(storage); }
    }
    public record PairRecordHeader(UInt64 address, UInt64 stackObjectIdentity, int stackIndex, int kindRaw,
                                   int score, VectorHeader reasons, UInt64 provinceIdentity, int selectedRaw) {
        public PairRecordHeader {
            pointer(address); pointer(stackObjectIdentity); pointer(provinceIdentity); Objects.requireNonNull(reasons);
            if (kindRaw < 0 || kindRaw > 255 || selectedRaw < 0 || selectedRaw > 255)
                throw new IllegalArgumentException("original record unsigned byte required");
        }
    }
    public record AppendFacts(Scope scope, Available originalCall, VectorHeader before,
                              VectorHeader originalReasons, VectorHeader originalReasonsAfter, VectorHeader after, UInt64 moduleBaseIdentity, UInt64 returnedIdentity, PairRecordHeader record) {
        public AppendFacts {
            Objects.requireNonNull(scope); Objects.requireNonNull(originalCall); Objects.requireNonNull(before);
            Objects.requireNonNull(originalReasons); Objects.requireNonNull(originalReasonsAfter); Objects.requireNonNull(after); pointer(moduleBaseIdentity); pointer(returnedIdentity); Objects.requireNonNull(record);
        }
    }
    public sealed interface AppendObservation permits AppendAvailable, AppendIncomplete { Scope scope(); }
    public record AppendAvailable(AppendFacts facts) implements AppendObservation {
        public AppendAvailable { Objects.requireNonNull(facts); }
        @Override public Scope scope() { return facts.scope(); }
    }
    public record AppendIncomplete(Scope scope, String reason) implements AppendObservation {
        public AppendIncomplete { Objects.requireNonNull(scope); diagnostic(reason); }
    }
    public enum AppendBranch { EXISTING_STORAGE, REALLOCATION_PATH }
    public enum ReasonVerification { HEADER_COUNT_AND_SOURCE_MOVE_ONLY }
    public record ObservedAppendRecord(PairKey pair, VectorHeader before, VectorHeader after,
                                       PairRecordHeader record, AppendBranch branch, ReasonVerification reasonVerification) implements Result {
        public ObservedAppendRecord {
            Objects.requireNonNull(pair); Objects.requireNonNull(before); Objects.requireNonNull(after);
            Objects.requireNonNull(record); Objects.requireNonNull(branch); Objects.requireNonNull(reasonVerification);
        }
    }
    /** Direct append/constructor field effects only. Allocator and reason contents are never simulated. */
    public static Result consumeAppend(Scope current, PairKey currentOriginalPair, UInt64 currentModuleBase, AppendObservation originalAfterRead) {
        Objects.requireNonNull(current); Objects.requireNonNull(currentOriginalPair); pointer(currentModuleBase); Objects.requireNonNull(originalAfterRead);
        if (!current.equals(originalAfterRead.scope())) return new NotReady("coordinator_update_or_source_changed");
        if (originalAfterRead instanceof AppendIncomplete missing) return new NotReady(missing.reason());
        AppendFacts f = ((AppendAvailable) originalAfterRead).facts();
        if (!currentModuleBase.equals(f.moduleBaseIdentity())) return new NotReady("original_append_module_identity_changed");
        Result terminal = consume(current, currentOriginalPair, f.originalCall());
        if (terminal instanceof NotReady missing) return missing;
        ObservedAppendOperands call = (ObservedAppendOperands) terminal;
        BigInteger vectorAddress = new BigInteger(current.coordinatorIdentity()).add(BigInteger.valueOf(0x7828));
        if (!f.before().address().value().equals(vectorAddress) || !f.after().address().equals(f.before().address()) ||
            !f.originalReasons().address().equals(currentOriginalPair.reasonVectorIdentity()))
            return new NotReady("original_append_vector_source_changed");
        VectorStorage before = f.before().storage(), after = f.after().storage();
        if (before.count() == Integer.MAX_VALUE || after.count() != before.count() + 1 ||
            !after.allocatorIdentity().equals(before.allocatorIdentity())) return new NotReady("original_append_count_or_allocator_changed");
        AppendBranch branch = before.count() == before.capacity() ? AppendBranch.REALLOCATION_PATH : AppendBranch.EXISTING_STORAGE;
        if (branch == AppendBranch.EXISTING_STORAGE &&
            (after.capacity() != before.capacity() || !after.dataIdentity().equals(before.dataIdentity())))
            return new NotReady("original_append_existing_storage_changed");
        if (branch == AppendBranch.REALLOCATION_PATH && after.capacity() <= before.capacity())
            return new NotReady("original_append_growth_capacity_not_observed");
        BigInteger returned = after.dataIdentity().value().add(BigInteger.valueOf(64L * (after.count() - 1)));
        PairRecordHeader record = f.record();
        if (returned.bitLength() > 64 || !f.returnedIdentity().value().equals(returned) || !record.address().equals(f.returnedIdentity()))
            return new NotReady("original_append_returned_slot_changed");
        BigInteger allocator = currentModuleBase.value().add(BigInteger.valueOf(RECORD_REASON_ALLOCATOR_RVA));
        if (allocator.bitLength() > 64 || !record.reasons().storage().allocatorIdentity().value().equals(allocator))
            return new NotReady("original_record_allocator_source_changed");
        PairKey pair = call.pair();
        if (!record.stackObjectIdentity().equals(pair.stackObjectIdentity()) || record.stackIndex() != pair.stackIndex() ||
            record.kindRaw() != pair.kindRaw() || record.score() != call.integerScore() || !record.provinceIdentity().equals(pair.provinceIdentity()) || record.selectedRaw() != 0)
            return new NotReady("original_append_record_fields_or_selection_changed");
        if (!record.reasons().address().value().equals(returned.add(BigInteger.valueOf(0x18))) ||
            record.reasons().storage().count() != f.originalReasons().storage().count())
            return new NotReady("original_append_reason_header_changed");
        VectorStorage reasonBefore = f.originalReasons().storage(), reasonAfter = f.originalReasonsAfter().storage();
        if (!f.originalReasonsAfter().address().equals(f.originalReasons().address()) || reasonAfter.count() != 0 ||
            !reasonAfter.allocatorIdentity().equals(reasonBefore.allocatorIdentity())) return new NotReady("original_reason_source_not_consumed");
        if (reasonBefore.allocatorIdentity().equals(record.reasons().storage().allocatorIdentity())) {
            if (reasonAfter.dataIdentity().value().signum() != 0 || reasonAfter.capacity() != 0 ||
                !record.reasons().storage().dataIdentity().equals(reasonBefore.dataIdentity()) || record.reasons().storage().capacity() != reasonBefore.capacity())
                return new NotReady("original_reason_same_allocator_move_changed");
        } else if (!reasonAfter.dataIdentity().equals(reasonBefore.dataIdentity()) || reasonAfter.capacity() != reasonBefore.capacity())
            return new NotReady("original_reason_different_allocator_source_changed");
        return new ObservedAppendRecord(pair, f.before(), f.after(), record, branch, ReasonVerification.HEADER_COUNT_AND_SOURCE_MOVE_ONLY);
    }
    public static AppendObservation decodeAppend(byte[] wire) {
        ObjectNode n = closed(parse(wire), "schema_version", "stage_rva", "scope", "status", "reason", "facts");
        if (i32(n.get("schema_version")) != 1 || i32(n.get("stage_rva")) != APPEND_CALL_RVA + 5)
            throw new IllegalArgumentException("exact append return stage required");
        Scope scope = LocalTargetScore12004.scope(n.get("scope")); String status = text(n.get("status"));
        if (status.equals("incomplete")) {
            if (!n.get("facts").isNull()) throw new IllegalArgumentException("incomplete append facts must be explicit null");
            return new AppendIncomplete(scope, text(n.get("reason")));
        }
        if (!status.equals("available") || !n.get("reason").isNull()) throw new IllegalArgumentException("append status differs");
        ObjectNode f = closed(n.get("facts"), "original_call", "before", "original_reasons", "original_reasons_after", "after", "module_base_identity", "returned_identity", "record");
        Observation call = decode(bytes(f.get("original_call")));
        if (!(call instanceof Available available)) throw new IllegalArgumentException("append facts demand original available call");
        ObjectNode p = closed(f.get("record"), "address", "stack_object_identity", "stack_index", "kind_raw", "score", "reasons", "province_identity", "selected_raw");
        PairRecordHeader record = new PairRecordHeader(identity(text(p.get("address"))), identity(text(p.get("stack_object_identity"))),
            i32(p.get("stack_index")), i32(p.get("kind_raw")), i32(p.get("score")), vector(p.get("reasons")),
            identity(text(p.get("province_identity"))), i32(p.get("selected_raw")));
        return new AppendAvailable(new AppendFacts(scope, available, vector(f.get("before")), vector(f.get("original_reasons")),
            vector(f.get("original_reasons_after")), vector(f.get("after")), identity(text(f.get("module_base_identity"))), identity(text(f.get("returned_identity"))), record));
    }
    public static byte[] encodeAppend(AppendObservation observation) {
        Objects.requireNonNull(observation); ObjectNode n = empty(); n.put("schema_version",1); n.put("stage_rva",APPEND_CALL_RVA+5);
        n.set("scope",LocalTargetScore12004.encodeScope(observation.scope()));
        if (observation instanceof AppendIncomplete missing) {
            n.put("status","incomplete"); n.put("reason",missing.reason()); n.putNull("facts"); return bytes(n);
        }
        AppendFacts f = ((AppendAvailable) observation).facts(); n.put("status","available"); n.putNull("reason"); ObjectNode facts=n.putObject("facts");
        facts.set("original_call",parse(encode(f.originalCall()))); facts.set("before",encodeVector(f.before())); facts.set("original_reasons",encodeVector(f.originalReasons()));
        facts.set("original_reasons_after",encodeVector(f.originalReasonsAfter())); facts.put("module_base_identity",f.moduleBaseIdentity().decimal()); facts.set("after",encodeVector(f.after())); facts.put("returned_identity",f.returnedIdentity().decimal()); PairRecordHeader r=f.record(); ObjectNode p=facts.putObject("record");
        p.put("address",r.address().decimal()); p.put("stack_object_identity",r.stackObjectIdentity().decimal()); p.put("stack_index",r.stackIndex());
        p.put("kind_raw",r.kindRaw()); p.put("score",r.score()); p.set("reasons",encodeVector(r.reasons()));
        p.put("province_identity",r.provinceIdentity().decimal()); p.put("selected_raw",r.selectedRaw()); return bytes(n);
    }
    private static VectorHeader vector(com.fasterxml.jackson.databind.JsonNode raw) {
        ObjectNode n=closed(raw,"address","data_identity","capacity","count","allocator_identity");
        String data=text(n.get("data_identity"));
        if (!data.matches("0|[1-9][0-9]{0,19}")) throw new IllegalArgumentException("canonical uint64 vector data identity required");
        return new VectorHeader(identity(text(n.get("address"))),new VectorStorage(new UInt64(new BigInteger(data)),i32(n.get("capacity")),i32(n.get("count")),identity(text(n.get("allocator_identity")))));
    }
    private static ObjectNode encodeVector(VectorHeader vector) {
        ObjectNode n=empty(); n.put("address",vector.address().decimal()); n.put("data_identity",vector.storage().dataIdentity().decimal());
        n.put("capacity",vector.storage().capacity()); n.put("count",vector.storage().count()); n.put("allocator_identity",vector.storage().allocatorIdentity().decimal()); return n;
    }
}
