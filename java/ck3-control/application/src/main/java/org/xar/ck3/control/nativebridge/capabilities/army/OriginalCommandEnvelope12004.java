package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.UInt64;
import org.xar.ck3.control.nativebridge.capabilities.army.LocalTargetScore12004.Scope;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;

/** Original 1A1CF68 command fields only. Embedded mode2, wrapper argument7 and helper argument1
 *  are distinct facts. An observed command does not grant submission, execution or Game credit. */
public final class OriginalCommandEnvelope12004 {
    public static final int CALLER_RVA = 0x1A1CF68, WRAPPER_RVA = 0x1A18890;
    public static final int OBSERVER_MAX_PATH = 65_536;
    private OriginalCommandEnvelope12004() { }
    public record CallKey(UInt64 moduleBaseIdentity, UInt64 unitOperandIdentity,
                          UInt64 candidateOperandIdentity, UInt64 commandAddress, UInt64 databaseIdentity) {
        public CallKey {
            positive(moduleBaseIdentity); positive(unitOperandIdentity); positive(candidateOperandIdentity); positive(commandAddress); positive(databaseIdentity);
            if (commandAddress.value().add(BigInteger.valueOf(0x4F)).bitLength() > 64)
                throw new IllegalArgumentException("command address span");
            if (databaseIdentity.value().add(BigInteger.valueOf(0x14F)).bitLength() > 64)
                throw new IllegalArgumentException("database address span");
        }
    }
    public record Facts(Scope scope, CallKey call, int unitFullIdRaw, int candidateFullIdRaw, int candidateCapacityRaw,
                        int embeddedModeRaw, int wrapperArgumentRaw, int helperResultRaw,
                        List<Integer> pathFullIdsRaw, int pathLastFullIdRaw,
                        int trailingModeRaw, int trailingOneRaw) {
        public Facts {
            Objects.requireNonNull(scope); Objects.requireNonNull(call); pathFullIdsRaw = List.copyOf(pathFullIdsRaw);
            if (unitFullIdRaw == -1 || candidateFullIdRaw <= 0 || candidateFullIdRaw >= candidateCapacityRaw)
                throw new IllegalArgumentException("actual caller raw identity branch");
            if (embeddedModeRaw != 2 || wrapperArgumentRaw != 7 || trailingModeRaw != 2 || trailingOneRaw != 1)
                throw new IllegalArgumentException("distinct original literal fields required");
            if (pathFullIdsRaw.size() > OBSERVER_MAX_PATH)
                throw new IllegalArgumentException("bounded original complete path");
            int last = pathFullIdsRaw.isEmpty() ? 0 : pathFullIdsRaw.getLast();
            if (last != pathLastFullIdRaw) throw new IllegalArgumentException("original copied path last element");
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
            if (!reason.matches("[a-z0-9_]{1,128}")) throw new IllegalArgumentException("bounded diagnostic");
        }
    }
    public sealed interface Result permits ObservedEnvelope, NotReady { }
    public record ObservedEnvelope(Facts facts) implements Result { public ObservedEnvelope { Objects.requireNonNull(facts); } }
    public record NotReady(String reason) implements Result { public NotReady { Objects.requireNonNull(reason); } }
    public static Result consume(Scope current, CallKey currentOriginalCall, Observation read) {
        Objects.requireNonNull(current); Objects.requireNonNull(currentOriginalCall); Objects.requireNonNull(read);
        if (!current.equals(read.scope())) return new NotReady("command_original_update_or_source_changed");
        if (read instanceof Incomplete missing) return new NotReady(missing.reason());
        Facts facts = ((Available) read).facts();
        if (!currentOriginalCall.equals(facts.call())) return new NotReady("command_original_occurrence_changed");
        return new ObservedEnvelope(facts);
    }
    public static Observation decode(byte[] wire) {
        ObjectNode n = closed(parse(wire), "schema_version", "caller_rva", "wrapper_rva", "scope", "status", "reason", "facts");
        if (i32(n.get("schema_version")) != 1 || i32(n.get("caller_rva")) != CALLER_RVA || i32(n.get("wrapper_rva")) != WRAPPER_RVA)
            throw new IllegalArgumentException("exact original command contract");
        Scope scope = LocalTargetScore12004.scope(n.get("scope")); String status = text(n.get("status"));
        if (status.equals("incomplete")) {
            if (!n.get("facts").isNull()) throw new IllegalArgumentException("incomplete facts must be null");
            return new Incomplete(scope, text(n.get("reason")));
        }
        if (!status.equals("available") || !n.get("reason").isNull()) throw new IllegalArgumentException("command discriminant");
        ObjectNode f = closed(n.get("facts"), "call", "unit_full_id_raw", "candidate_full_id_raw", "candidate_capacity_raw", "embedded_mode_raw", "wrapper_argument_raw",
                "helper_result_raw", "path_full_ids_raw", "path_last_full_id_raw", "trailing_mode_raw", "trailing_one_raw");
        ObjectNode c = closed(f.get("call"), "module_base_identity", "unit_operand_identity", "candidate_operand_identity", "command_address", "database_identity");
        CallKey key = new CallKey(address(c.get("module_base_identity")), address(c.get("unit_operand_identity")),
                address(c.get("candidate_operand_identity")), address(c.get("command_address")), address(c.get("database_identity")));
        return new Available(new Facts(scope, key, i32(f.get("unit_full_id_raw")), i32(f.get("candidate_full_id_raw")), i32(f.get("candidate_capacity_raw")),
                i32(f.get("embedded_mode_raw")), i32(f.get("wrapper_argument_raw")), i32(f.get("helper_result_raw")),
                array(f.get("path_full_ids_raw"), ArmyJson::i32), i32(f.get("path_last_full_id_raw")),
                i32(f.get("trailing_mode_raw")), i32(f.get("trailing_one_raw"))));
    }
    public static byte[] encode(Observation observation) {
        Objects.requireNonNull(observation); ObjectNode n = empty();
        n.put("schema_version", 1); n.put("caller_rva", CALLER_RVA); n.put("wrapper_rva", WRAPPER_RVA);
        n.set("scope", LocalTargetScore12004.encodeScope(observation.scope()));
        if (observation instanceof Incomplete missing) {
            n.put("status", "incomplete"); n.put("reason", missing.reason()); n.putNull("facts"); return bytes(n);
        }
        Facts f = ((Available) observation).facts(); CallKey k = f.call(); n.put("status", "available"); n.putNull("reason");
        ObjectNode out = n.putObject("facts"); ObjectNode call = out.putObject("call");
        call.put("module_base_identity", k.moduleBaseIdentity().decimal()); call.put("unit_operand_identity", k.unitOperandIdentity().decimal());
        call.put("candidate_operand_identity", k.candidateOperandIdentity().decimal()); call.put("command_address", k.commandAddress().decimal());
        call.put("database_identity", k.databaseIdentity().decimal());
        out.put("unit_full_id_raw", f.unitFullIdRaw()); out.put("candidate_full_id_raw", f.candidateFullIdRaw());
        out.put("candidate_capacity_raw", f.candidateCapacityRaw());
        out.put("embedded_mode_raw", f.embeddedModeRaw()); out.put("wrapper_argument_raw", f.wrapperArgumentRaw());
        out.put("helper_result_raw", f.helperResultRaw()); ArrayNode path = out.putArray("path_full_ids_raw");
        for (int id : f.pathFullIdsRaw()) path.add(id);
        out.put("path_last_full_id_raw", f.pathLastFullIdRaw()); out.put("trailing_mode_raw", f.trailingModeRaw());
        out.put("trailing_one_raw", f.trailingOneRaw()); return bytes(n);
    }
    private static UInt64 address(JsonNode node) {
        String s = text(node); if (!s.matches("[1-9][0-9]{0,19}")) throw new IllegalArgumentException("canonical positive address");
        return UInt64.positive(new BigInteger(s));
    }
    private static void positive(UInt64 value) {
        Objects.requireNonNull(value); if (value.value().signum() <= 0) throw new IllegalArgumentException("positive native address");
    }
}
