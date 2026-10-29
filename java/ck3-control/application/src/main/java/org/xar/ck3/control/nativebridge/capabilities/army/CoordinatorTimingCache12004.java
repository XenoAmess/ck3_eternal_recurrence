package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.OptionalInt;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.UInt64;
import org.xar.ck3.control.nativebridge.capabilities.army.LocalTargetScore12004.Scope;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;

/** Original 19FF7B4 CALL entry only. Neither a timer tick nor a selected/submitted Army action. */
public final class CoordinatorTimingCache12004 {
    public static final int CALLER_RVA = 0x19FF7B4;
    public static final int RECEIVER_RVA = 0x19FF9C0;
    private CoordinatorTimingCache12004() { }

    /** Opaque A8/B8 values are copied qwords, with no Province/Army/business identity assertion. */
    public record Fields(int flagsRaw, int countdownB0Raw, int stampB4Raw, UInt64 cachedA8Raw,
                         UInt64 cachedB8Raw, int countdownC0Raw) {
        public Fields {
            if (flagsRaw < 0 || flagsRaw > 255) throw new IllegalArgumentException("native flags byte required");
            Objects.requireNonNull(cachedA8Raw); Objects.requireNonNull(cachedB8Raw);
        }
    }
    /** Null means not demanded by the original entry path, rather than zero or an unread value. */
    public record PeriodicInputs(OptionalInt divisorRaw, OptionalInt contextStampRaw) {
        public PeriodicInputs { Objects.requireNonNull(divisorRaw); Objects.requireNonNull(contextStampRaw); }
    }
    public record Inputs(Scope scope, UInt64 moduleBaseIdentity, UInt64 originalRcxIdentity,
                         UInt64 originalRdxIdentity, int originalThirdRaw, Fields fields,
                         PeriodicInputs periodic) {
        public Inputs {
            Objects.requireNonNull(scope); Objects.requireNonNull(moduleBaseIdentity);
            Objects.requireNonNull(originalRcxIdentity); Objects.requireNonNull(originalRdxIdentity);
            Objects.requireNonNull(fields); Objects.requireNonNull(periodic);
            if (moduleBaseIdentity.value().signum() <= 0 || originalRcxIdentity.value().signum() <= 0
                    || !originalRcxIdentity.decimal().equals(scope.coordinatorIdentity()))
                throw new IllegalArgumentException("original caller/coordinator binding required");
            boolean periodicPath = admitted(fields) && fields.countdownB0Raw() > 1;
            if (periodicPath != periodic.divisorRaw().isPresent())
                throw new IllegalArgumentException("periodic divisor demand differs from original entry path");
            boolean stampPath = periodicPath && periodic.divisorRaw().orElseThrow() != 0
                    && (fields.countdownB0Raw() - 1) % periodic.divisorRaw().orElseThrow() == 0;
            if (stampPath != periodic.contextStampRaw().isPresent())
                throw new IllegalArgumentException("context stamp demand differs from original entry path");
            if (stampPath && originalRdxIdentity.value().signum() <= 0)
                throw new IllegalArgumentException("original demanded RDX context required");
        }
    }
    public sealed interface Observation permits Available, Incomplete { Scope scope(); }
    public record Available(Inputs inputs) implements Observation {
        public Available { Objects.requireNonNull(inputs); }
        @Override public Scope scope() { return inputs.scope(); }
    }
    public record Incomplete(Scope scope, String reason) implements Observation {
        public Incomplete {
            Objects.requireNonNull(scope); Objects.requireNonNull(reason);
            if (!reason.matches("[a-z0-9_]{1,128}")) throw new IllegalArgumentException("bounded diagnostic required");
        }
    }
    public enum EntryBranch {
        FLAG_MASK_RETURNS, NEGATIVE_B0_SKIPS_DECREMENT, ZERO_B0_BECOMES_NEGATIVE,
        PICK_CALLEE_REQUIRED, POSITIVE_B0_NOT_PERIODIC, PERIODIC_STAMP_UNCHANGED,
        REBUILD_CALLEE_REQUIRED, ORIGINAL_DIVIDE_FAULT
    }
    public sealed interface Result permits ObservedEntry, NotReady { }
    /** Entry classification stops before unknown callees. It predicts no C0 write, quantity, or poststate. */
    public record ObservedEntry(Inputs inputs, EntryBranch branch) implements Result {
        public ObservedEntry { Objects.requireNonNull(inputs); Objects.requireNonNull(branch); }
    }
    public record NotReady(String reason) implements Result { public NotReady { Objects.requireNonNull(reason); } }

    public static Result consume(Scope current, UInt64 currentModuleBase, Observation originalRead) {
        Objects.requireNonNull(current); Objects.requireNonNull(currentModuleBase); Objects.requireNonNull(originalRead);
        if (!current.equals(originalRead.scope())) return new NotReady("coordinator_update_or_source_changed");
        if (originalRead instanceof Incomplete missing) return new NotReady(missing.reason());
        Inputs inputs = ((Available) originalRead).inputs();
        if (!currentModuleBase.equals(inputs.moduleBaseIdentity())) return new NotReady("module_installation_changed");
        return new ObservedEntry(inputs, entryBranch(inputs));
    }

    private static boolean admitted(Fields fields) { return (fields.flagsRaw() & 0x44) == 0x44; }
    private static EntryBranch entryBranch(Inputs inputs) {
        Fields f = inputs.fields();
        if (!admitted(f)) return EntryBranch.FLAG_MASK_RETURNS;
        if (f.countdownB0Raw() < 0) return EntryBranch.NEGATIVE_B0_SKIPS_DECREMENT;
        if (f.countdownB0Raw() == 0) return EntryBranch.ZERO_B0_BECOMES_NEGATIVE;
        if (f.countdownB0Raw() == 1) return EntryBranch.PICK_CALLEE_REQUIRED;
        int divisor = inputs.periodic().divisorRaw().orElseThrow();
        if (divisor == 0) return EntryBranch.ORIGINAL_DIVIDE_FAULT;
        if ((f.countdownB0Raw() - 1) % divisor != 0) return EntryBranch.POSITIVE_B0_NOT_PERIODIC;
        return inputs.periodic().contextStampRaw().orElseThrow() == f.stampB4Raw()
                ? EntryBranch.PERIODIC_STAMP_UNCHANGED : EntryBranch.REBUILD_CALLEE_REQUIRED;
    }

    public static Observation decode(byte[] wire) {
        ObjectNode n = closed(parse(wire), "schema_version", "caller_rva", "receiver_rva", "scope", "status", "reason", "facts");
        if (i32(n.get("schema_version")) != 1 || i32(n.get("caller_rva")) != CALLER_RVA
                || i32(n.get("receiver_rva")) != RECEIVER_RVA)
            throw new IllegalArgumentException("timing/cache original entry contract required");
        Scope scope = LocalTargetScore12004.scope(n.get("scope"));
        String status = text(n.get("status"));
        if (status.equals("incomplete")) {
            if (!n.get("facts").isNull()) throw new IllegalArgumentException("incomplete facts must be explicit null");
            return new Incomplete(scope, text(n.get("reason")));
        }
        if (!status.equals("available") || !n.get("reason").isNull())
            throw new IllegalArgumentException("timing/cache observation discriminant");
        ObjectNode f = closed(n.get("facts"), "module_base_identity", "original_rcx_identity", "original_rdx_identity",
                "original_third_raw", "fields", "periodic");
        ObjectNode b = closed(f.get("fields"), "flags_raw", "countdown_b0_raw", "stamp_b4_raw", "cached_a8_raw", "cached_b8_raw", "countdown_c0_raw");
        Fields fields = new Fields(i32(b.get("flags_raw")), i32(b.get("countdown_b0_raw")), i32(b.get("stamp_b4_raw")),
                decimal(b.get("cached_a8_raw")), decimal(b.get("cached_b8_raw")), i32(b.get("countdown_c0_raw")));
        ObjectNode p = closed(f.get("periodic"), "divisor_raw", "context_stamp_raw");
        PeriodicInputs periodic = new PeriodicInputs(optionalInt(p, "divisor_raw"), optionalInt(p, "context_stamp_raw"));
        return new Available(new Inputs(scope, decimal(f.get("module_base_identity")), decimal(f.get("original_rcx_identity")),
                decimal(f.get("original_rdx_identity")), i32(f.get("original_third_raw")), fields, periodic));
    }
    public static byte[] encode(Observation observation) {
        Objects.requireNonNull(observation);
        ObjectNode n = empty(); n.put("schema_version", 1); n.put("caller_rva", CALLER_RVA); n.put("receiver_rva", RECEIVER_RVA);
        n.set("scope", LocalTargetScore12004.encodeScope(observation.scope()));
        if (observation instanceof Incomplete missing) {
            n.put("status", "incomplete"); n.put("reason", missing.reason()); n.putNull("facts"); return bytes(n);
        }
        Inputs i = ((Available) observation).inputs(); n.put("status", "available"); n.putNull("reason");
        ObjectNode f = n.putObject("facts"); f.put("module_base_identity", i.moduleBaseIdentity().decimal());
        f.put("original_rcx_identity", i.originalRcxIdentity().decimal()); f.put("original_rdx_identity", i.originalRdxIdentity().decimal());
        f.put("original_third_raw", i.originalThirdRaw());
        Fields b = i.fields(); ObjectNode fields = f.putObject("fields"); fields.put("flags_raw", b.flagsRaw());
        fields.put("countdown_b0_raw", b.countdownB0Raw()); fields.put("stamp_b4_raw", b.stampB4Raw());
        fields.put("cached_a8_raw", b.cachedA8Raw().decimal()); fields.put("cached_b8_raw", b.cachedB8Raw().decimal());
        fields.put("countdown_c0_raw", b.countdownC0Raw());
        ObjectNode p = f.putObject("periodic"); putOptionalInt(p, "divisor_raw", i.periodic().divisorRaw());
        putOptionalInt(p, "context_stamp_raw", i.periodic().contextStampRaw()); return bytes(n);
    }
    private static OptionalInt optionalInt(ObjectNode node, String field) {
        return node.get(field).isNull() ? OptionalInt.empty() : OptionalInt.of(i32(node.get(field)));
    }
    private static void putOptionalInt(ObjectNode node, String field, OptionalInt value) {
        if (value.isPresent()) node.put(field, value.orElseThrow()); else node.putNull(field);
    }
    private static UInt64 decimal(com.fasterxml.jackson.databind.JsonNode raw) {
        String value = text(raw);
        if (!value.matches("0|[1-9][0-9]{0,19}")) throw new IllegalArgumentException("canonical uint64 decimal string required");
        return new UInt64(new BigInteger(value));
    }
}
