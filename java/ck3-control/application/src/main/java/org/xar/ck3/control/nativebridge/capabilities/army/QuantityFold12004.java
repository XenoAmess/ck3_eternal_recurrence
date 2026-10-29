package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.UInt64;
import org.xar.ck3.control.nativebridge.capabilities.army.LocalTargetScore12004.Scope;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;

/** Proven 1A1EC70 fold over original 24E0360 return qwords. No business unit or action authority. */
public final class QuantityFold12004 {
    public static final int SIGNATURE_RAW = 0x41495355;
    public static final int NESTED_CALL_RVA = 0x1A1ED80, NESTED_RETURN_RVA = 0x1A1ED85;
    public static final int OBSERVER_MAX_MEMBERS = 65_536;
    private QuantityFold12004() { }

    public record Amount(UInt64 secondaryOperandIdentity, UInt64 returnedAddress, long raw) {
        public Amount {
            positive(secondaryOperandIdentity); positive(returnedAddress);
            if (returnedAddress.value().add(BigInteger.valueOf(7)).bitLength() > 64)
                throw new IllegalArgumentException("returned qword address width");
        }
    }
    public record Member(int ordinal, UInt64 primaryOperandIdentity, int primaryField18Raw,
                         Optional<Amount> amount) {
        public Member {
            positive(primaryOperandIdentity); Objects.requireNonNull(amount);
            if (ordinal < 0 || ordinal >= OBSERVER_MAX_MEMBERS)
                throw new IllegalArgumentException("bounded ordinal");
            if ((primaryField18Raw == 0) != amount.isPresent())
                throw new IllegalArgumentException("only native field18 zero branch calls the nested helper");
        }
    }
    public record MatchedMembers(int signedCountRaw, List<Member> members) {
        public MatchedMembers {
            members = List.copyOf(members);
            if (signedCountRaw < 0 || signedCountRaw > OBSERVER_MAX_MEMBERS || members.size() != signedCountRaw)
                throw new IllegalArgumentException("complete bounded native member range required");
            for (int i = 0; i < members.size(); ++i)
                if (members.get(i).ordinal() != i) throw new IllegalArgumentException("native loop order must be dense and complete");
        }
    }
    public record Facts(OriginalQuantity12004.Facts originalOutput, int observedSignatureRaw,
                        Optional<MatchedMembers> matchedMembers) {
        public Facts {
            Objects.requireNonNull(originalOutput); Objects.requireNonNull(matchedMembers);
            if ((observedSignatureRaw == SIGNATURE_RAW) != matchedMembers.isPresent())
                throw new IllegalArgumentException("signature mismatch returns zero before reading member storage");
        }
    }
    public sealed interface Observation permits Available, Incomplete { Scope scope(); }
    public record Available(Facts facts) implements Observation {
        public Available { Objects.requireNonNull(facts); }
        @Override public Scope scope() { return facts.originalOutput().scope(); }
    }
    public record Incomplete(Scope scope, String reason) implements Observation {
        public Incomplete {
            Objects.requireNonNull(scope); Objects.requireNonNull(reason);
            if (!reason.matches("[a-z0-9_]{1,128}")) throw new IllegalArgumentException("bounded diagnostic");
        }
    }
    public enum Branch { SIGNATURE_ZERO, MATCHED_FOLD }
    public sealed interface Result permits VerifiedRawFold, NotReady { }
    public record VerifiedRawFold(long raw, Branch branch, int memberCount, int contributingCount) implements Result {
        public VerifiedRawFold { Objects.requireNonNull(branch); }
    }
    public record NotReady(String reason) implements Result { public NotReady { Objects.requireNonNull(reason); } }

    /** Java long addition reproduces x64 ADD's low64 result, including overflow. No fixed-point inference. */
    public static Result consume(Scope current, OriginalQuantity12004.CallKey currentCall, Observation observation) {
        Objects.requireNonNull(current); Objects.requireNonNull(currentCall); Objects.requireNonNull(observation);
        if (!current.equals(observation.scope())) return new NotReady("quantity_fold_update_or_source_changed");
        if (observation instanceof Incomplete missing) return new NotReady(missing.reason());
        Facts f = ((Available) observation).facts();
        OriginalQuantity12004.Result original = OriginalQuantity12004.consume(current, currentCall,
                new OriginalQuantity12004.Available(f.originalOutput()));
        if (original instanceof OriginalQuantity12004.NotReady missing) return new NotReady(missing.reason());
        long sum = 0; int count = 0, included = 0;
        Branch branch = Branch.SIGNATURE_ZERO;
        if (f.matchedMembers().isPresent()) {
            branch = Branch.MATCHED_FOLD; MatchedMembers matched = f.matchedMembers().orElseThrow();
            count = matched.signedCountRaw();
            for (Member member : matched.members()) {
                if (member.amount().isPresent()) { sum += member.amount().orElseThrow().raw(); ++included; }
            }
        }
        if (sum != f.originalOutput().outputRaw()) return new NotReady("quantity_fold_original_output_mismatch");
        return new VerifiedRawFold(sum, branch, count, included);
    }

    public static Observation decode(byte[] wire) {
        ObjectNode n = closed(parse(wire), "schema_version", "nested_call_rva", "nested_return_rva", "scope", "status", "reason", "facts");
        if (i32(n.get("schema_version")) != 1 || i32(n.get("nested_call_rva")) != NESTED_CALL_RVA
                || i32(n.get("nested_return_rva")) != NESTED_RETURN_RVA) throw new IllegalArgumentException("exact fold contract required");
        Scope scope = LocalTargetScore12004.scope(n.get("scope")); String status = text(n.get("status"));
        if (status.equals("incomplete")) {
            if (!n.get("facts").isNull()) throw new IllegalArgumentException("incomplete facts must be null");
            return new Incomplete(scope, text(n.get("reason")));
        }
        if (!status.equals("available") || !n.get("reason").isNull()) throw new IllegalArgumentException("fold discriminant");
        ObjectNode f = closed(n.get("facts"), "original_output", "observed_signature_raw", "matched_members");
        OriginalQuantity12004.Observation original = OriginalQuantity12004.decode(bytes(f.get("original_output")));
        if (!(original instanceof OriginalQuantity12004.Available available) || !scope.equals(original.scope()))
            throw new IllegalArgumentException("same-scope original output required");
        Optional<MatchedMembers> matched = Optional.empty();
        if (!f.get("matched_members").isNull()) {
            ObjectNode m = closed(f.get("matched_members"), "signed_count_raw", "members");
            matched = Optional.of(new MatchedMembers(i32(m.get("signed_count_raw")), array(m.get("members"), QuantityFold12004::member)));
        }
        return new Available(new Facts(available.facts(), i32(f.get("observed_signature_raw")), matched));
    }
    public static byte[] encode(Observation observation) {
        Objects.requireNonNull(observation);
        ObjectNode n = empty(); n.put("schema_version", 1); n.put("nested_call_rva", NESTED_CALL_RVA); n.put("nested_return_rva", NESTED_RETURN_RVA);
        n.set("scope", LocalTargetScore12004.encodeScope(observation.scope()));
        if (observation instanceof Incomplete missing) {
            n.put("status", "incomplete"); n.put("reason", missing.reason()); n.putNull("facts"); return bytes(n);
        }
        Facts f = ((Available) observation).facts(); n.put("status", "available"); n.putNull("reason");
        ObjectNode out = n.putObject("facts");
        out.set("original_output", parse(OriginalQuantity12004.encode(new OriginalQuantity12004.Available(f.originalOutput()))));
        out.put("observed_signature_raw", f.observedSignatureRaw());
        if (f.matchedMembers().isEmpty()) out.putNull("matched_members");
        else {
            MatchedMembers m = f.matchedMembers().orElseThrow(); ObjectNode match = out.putObject("matched_members");
            match.put("signed_count_raw", m.signedCountRaw()); ArrayNode members = match.putArray("members");
            for (Member member : m.members()) {
                ObjectNode e = members.addObject(); e.put("ordinal", member.ordinal());
                e.put("primary_operand_identity", member.primaryOperandIdentity().decimal()); e.put("primary_field18_raw", member.primaryField18Raw());
                if (member.amount().isEmpty()) e.putNull("amount");
                else {
                    Amount a = member.amount().orElseThrow(); ObjectNode value = e.putObject("amount");
                    value.put("secondary_operand_identity", a.secondaryOperandIdentity().decimal());
                    value.put("returned_address", a.returnedAddress().decimal()); value.put("raw", Long.toString(a.raw()));
                }
            }
        }
        return bytes(n);
    }
    private static Member member(JsonNode node) {
        ObjectNode n = closed(node, "ordinal", "primary_operand_identity", "primary_field18_raw", "amount");
        Optional<Amount> amount = Optional.empty();
        if (!n.get("amount").isNull()) {
            ObjectNode a = closed(n.get("amount"), "secondary_operand_identity", "returned_address", "raw");
            amount = Optional.of(new Amount(address(a.get("secondary_operand_identity")), address(a.get("returned_address")),
                    PairTargetScoreFactor12004.signed64(text(a.get("raw")))));
        }
        return new Member(i32(n.get("ordinal")), address(n.get("primary_operand_identity")), i32(n.get("primary_field18_raw")), amount);
    }
    private static UInt64 address(JsonNode node) {
        String s = text(node); if (!s.matches("[1-9][0-9]{0,19}")) throw new IllegalArgumentException("canonical positive address");
        return UInt64.positive(new BigInteger(s));
    }
    private static void positive(UInt64 value) {
        Objects.requireNonNull(value); if (value.value().signum() <= 0) throw new IllegalArgumentException("positive native address");
    }
}
