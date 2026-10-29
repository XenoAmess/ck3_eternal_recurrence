package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.UInt64;
import org.xar.ck3.control.nativebridge.capabilities.army.LocalTargetScore12004.Scope;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;

/** One original CALL19FFAD1/return19FFAD6 raw output. The quantity unit and callee effects are unknown. */
public final class OriginalQuantity12004 {
    public static final int CALLER_RVA = 0x19FFAD1, RETURN_RVA = 0x19FFAD6;
    private OriginalQuantity12004() { }
    /** Loop storage slots distinguish occurrences; these opaque addresses are not Army/Province IDs. */
    public record CallKey(UInt64 moduleBaseIdentity, UInt64 outerSlotIdentity, UInt64 innerSlotIdentity,
                          UInt64 unitOperandIdentity, UInt64 outputAddress) {
        public CallKey {
            for (UInt64 value : new UInt64[]{moduleBaseIdentity, outerSlotIdentity, innerSlotIdentity, unitOperandIdentity, outputAddress}) {
                Objects.requireNonNull(value);
                if (value.value().signum() <= 0) throw new IllegalArgumentException("original positive address required");
            }
            if (outputAddress.value().add(BigInteger.valueOf(7)).bitLength() > 64)
                throw new IllegalArgumentException("original output qword exceeds native address width");
        }
    }
    public record Facts(Scope scope, CallKey call, int originalModeRaw, long outputRaw) {
        public Facts {
            Objects.requireNonNull(scope); Objects.requireNonNull(call);
            if (originalModeRaw != 0) throw new IllegalArgumentException("only actual coordinator zero-mode caller is bound");
        }
    }
    public sealed interface Observation permits Available, Incomplete { Scope scope(); }
    public record Available(Facts facts) implements Observation {
        public Available { Objects.requireNonNull(facts); }
        @Override public Scope scope() { return facts.scope(); }
    }
    public record Incomplete(Scope scope, String reason) implements Observation {
        public Incomplete {
            Objects.requireNonNull(scope); Objects.requireNonNull(reason);
            if (!reason.matches("[a-z0-9_]{1,128}")) throw new IllegalArgumentException("bounded original-read diagnostic required");
        }
    }
    public sealed interface Result permits ObservedRawOutput, NotReady { }
    public record ObservedRawOutput(CallKey call, long raw) implements Result { public ObservedRawOutput { Objects.requireNonNull(call); } }
    public record NotReady(String reason) implements Result { public NotReady { Objects.requireNonNull(reason); } }
    /** Caller supplies its independently current complete occurrence. No value is cached or aggregated. */
    public static Result consume(Scope current, CallKey originalCurrentCall, Observation read) {
        Objects.requireNonNull(current); Objects.requireNonNull(originalCurrentCall); Objects.requireNonNull(read);
        if (!current.equals(read.scope())) return new NotReady("quantity_original_update_or_source_changed");
        if (read instanceof Incomplete missing) return new NotReady(missing.reason());
        Facts facts = ((Available) read).facts();
        if (!originalCurrentCall.equals(facts.call())) return new NotReady("quantity_original_occurrence_changed");
        return new ObservedRawOutput(facts.call(), facts.outputRaw());
    }
    public static Observation decode(byte[] wire) {
        ObjectNode n = closed(parse(wire), "schema_version", "caller_rva", "return_rva", "scope", "status", "reason", "facts");
        if (i32(n.get("schema_version")) != 1 || i32(n.get("caller_rva")) != CALLER_RVA || i32(n.get("return_rva")) != RETURN_RVA)
            throw new IllegalArgumentException("exact original quantity occurrence contract required");
        Scope scope = LocalTargetScore12004.scope(n.get("scope")); String status = text(n.get("status"));
        if (status.equals("incomplete")) {
            if (!n.get("facts").isNull()) throw new IllegalArgumentException("incomplete facts must be explicit null");
            return new Incomplete(scope, text(n.get("reason")));
        }
        if (!status.equals("available") || !n.get("reason").isNull()) throw new IllegalArgumentException("quantity observation discriminant");
        ObjectNode f = closed(n.get("facts"), "call", "original_mode_raw", "output_raw");
        ObjectNode c = closed(f.get("call"), "module_base_identity", "outer_slot_identity", "inner_slot_identity", "unit_operand_identity", "output_address");
        CallKey call = new CallKey(address(c.get("module_base_identity")), address(c.get("outer_slot_identity")),
                address(c.get("inner_slot_identity")), address(c.get("unit_operand_identity")), address(c.get("output_address")));
        return new Available(new Facts(scope, call, i32(f.get("original_mode_raw")), PairTargetScoreFactor12004.signed64(text(f.get("output_raw")))));
    }
    public static byte[] encode(Observation observation) {
        Objects.requireNonNull(observation);
        ObjectNode n = empty(); n.put("schema_version", 1); n.put("caller_rva", CALLER_RVA); n.put("return_rva", RETURN_RVA);
        n.set("scope", LocalTargetScore12004.encodeScope(observation.scope()));
        if (observation instanceof Incomplete missing) {
            n.put("status", "incomplete"); n.put("reason", missing.reason()); n.putNull("facts"); return bytes(n);
        }
        Facts f = ((Available) observation).facts(); CallKey k = f.call();
        n.put("status", "available"); n.putNull("reason"); ObjectNode facts = n.putObject("facts");
        ObjectNode call = facts.putObject("call"); call.put("module_base_identity", k.moduleBaseIdentity().decimal());
        call.put("outer_slot_identity", k.outerSlotIdentity().decimal()); call.put("inner_slot_identity", k.innerSlotIdentity().decimal());
        call.put("unit_operand_identity", k.unitOperandIdentity().decimal()); call.put("output_address", k.outputAddress().decimal());
        facts.put("original_mode_raw", f.originalModeRaw()); facts.put("output_raw", Long.toString(f.outputRaw())); return bytes(n);
    }
    private static UInt64 address(JsonNode node) {
        String value = text(node);
        if (!value.matches("[1-9][0-9]{0,19}")) throw new IllegalArgumentException("canonical positive uint64 address string required");
        return UInt64.positive(new BigInteger(value));
    }
}
