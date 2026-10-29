package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.UInt64;
import org.xar.ck3.control.nativebridge.capabilities.army.LocalTargetScore12004.Scope;

/** Original 24E0360 zero-flag member sum inside the existing coordinator fold. No quantity unit. */
public final class NestedQuantitySum12004 {
    public static final int ENTRY_RVA = 0x24E0360, SIGNATURE_RAW = 0x41725267;
    public static final int OBSERVER_MAX_MEMBERS = 65_536;
    private NestedQuantitySum12004() { }

    public record Member(int ordinal, Optional<Integer> sourceHandleRaw, UInt64 selectedOperandIdentity,
                         int selectedSignatureRaw, Optional<Integer> selectedFullIdRaw, Optional<Long> amountRaw) {
        public Member {
            Objects.requireNonNull(sourceHandleRaw); positive(selectedOperandIdentity);
            Objects.requireNonNull(selectedFullIdRaw); Objects.requireNonNull(amountRaw);
            if (ordinal < 0 || ordinal >= OBSERVER_MAX_MEMBERS) throw new IllegalArgumentException("bounded ordinal");
            boolean matched = selectedSignatureRaw == SIGNATURE_RAW;
            if (matched != selectedFullIdRaw.isPresent()) throw new IllegalArgumentException("full ID is read only after signature match");
            if ((matched && selectedFullIdRaw.orElseThrow() != -1) != amountRaw.isPresent())
                throw new IllegalArgumentException("only a matched non-sentinel member contributes");
        }
    }
    public record Helper(int parentOrdinal, UInt64 secondaryOperandIdentity, UInt64 outputAddress,
                         int entryFlagsRaw, UInt64 memberStorageIdentity, int signedCountRaw,
                         Optional<UInt64> databaseIdentity, List<Member> members) {
        public Helper {
            positive(secondaryOperandIdentity); positive(outputAddress); Objects.requireNonNull(memberStorageIdentity);
            Objects.requireNonNull(databaseIdentity); members = List.copyOf(members);
            if (parentOrdinal < 0 || parentOrdinal >= OBSERVER_MAX_MEMBERS || entryFlagsRaw != 0)
                throw new IllegalArgumentException("this contract observes only the original zero-flag coordinator chain");
            if (signedCountRaw < 0 || signedCountRaw > OBSERVER_MAX_MEMBERS || members.size() != signedCountRaw)
                throw new IllegalArgumentException("complete bounded member range required");
            if ((signedCountRaw != 0) != databaseIdentity.isPresent())
                throw new IllegalArgumentException("empty path does not load the database global");
            if (signedCountRaw != 0) {
                positive(memberStorageIdentity);
                if (memberStorageIdentity.value().add(BigInteger.valueOf((long) signedCountRaw * 4)).bitLength() > 64)
                    throw new IllegalArgumentException("member range width");
                boolean readsHandle = databaseIdentity.orElseThrow().value().signum() != 0;
                for (int i = 0; i < members.size(); ++i) {
                    Member m = members.get(i);
                    if (m.ordinal() != i || m.sourceHandleRaw().isPresent() != readsHandle)
                        throw new IllegalArgumentException("dense original loop order and reached handle reads required");
                }
            }
        }
    }
    public record Facts(QuantityFold12004.Facts originalFold, List<Helper> helpers) {
        public Facts {
            Objects.requireNonNull(originalFold); helpers = List.copyOf(helpers);
            List<QuantityFold12004.Member> parents = originalFold.matchedMembers()
                    .map(QuantityFold12004.MatchedMembers::members).orElse(List.of());
            BigInteger nestedOutput = originalFold.originalOutput().call().outputAddress().value().subtract(BigInteger.valueOf(0x88));
            int cursor = 0; long totalMembers = 0;
            for (QuantityFold12004.Member member : parents) {
                if (member.amount().isEmpty()) continue;
                if (cursor >= helpers.size()) throw new IllegalArgumentException("every original nested call requires one helper trace");
                Helper helper = helpers.get(cursor++); QuantityFold12004.Amount amount = member.amount().orElseThrow();
                totalMembers += helper.signedCountRaw();
                if (totalMembers > OBSERVER_MAX_MEMBERS) throw new IllegalArgumentException("total nested observer bound");
                if (helper.parentOrdinal() != member.ordinal() || !helper.secondaryOperandIdentity().equals(amount.secondaryOperandIdentity())
                        || !helper.outputAddress().equals(amount.returnedAddress()) || !helper.outputAddress().value().equals(nestedOutput))
                    throw new IllegalArgumentException("helper trace must bind the same original member, operand and returned output address");
            }
            if (cursor != helpers.size()) throw new IllegalArgumentException("unreached helper trace");
        }
    }
    public sealed interface Observation permits Available, Incomplete { Scope scope(); }
    public record Available(Facts facts) implements Observation {
        public Available { Objects.requireNonNull(facts); }
        @Override public Scope scope() { return facts.originalFold().originalOutput().scope(); }
    }
    public record Incomplete(Scope scope, String reason) implements Observation {
        public Incomplete {
            Objects.requireNonNull(scope); Objects.requireNonNull(reason);
            if (!reason.matches("[a-z0-9_]{1,128}")) throw new IllegalArgumentException("bounded diagnostic");
        }
    }
    public sealed interface Result permits VerifiedNestedRawSum, NotReady { }
    public record VerifiedNestedRawSum(QuantityFold12004.VerifiedRawFold fold, int helperCount, int selectedCount,
                                       int contributingCount) implements Result {
        public VerifiedNestedRawSum { Objects.requireNonNull(fold); }
    }
    public record NotReady(String reason) implements Result { public NotReady { Objects.requireNonNull(reason); } }

    public static Result consume(Scope current, OriginalQuantity12004.CallKey currentCall, Observation observation) {
        Objects.requireNonNull(current); Objects.requireNonNull(currentCall); Objects.requireNonNull(observation);
        if (!current.equals(observation.scope())) return new NotReady("nested_quantity_update_or_source_changed");
        if (observation instanceof Incomplete missing) return new NotReady(missing.reason());
        Facts facts = ((Available) observation).facts();
        QuantityFold12004.Result outer = QuantityFold12004.consume(current, currentCall, new QuantityFold12004.Available(facts.originalFold()));
        if (outer instanceof QuantityFold12004.NotReady missing) return new NotReady(missing.reason());
        List<QuantityFold12004.Member> parents = facts.originalFold().matchedMembers()
                .map(QuantityFold12004.MatchedMembers::members).orElse(List.of());
        int selected = 0, included = 0;
        for (Helper helper : facts.helpers()) {
            long sum = 0;
            for (Member member : helper.members()) {
                ++selected;
                if (member.amountRaw().isPresent()) { sum += member.amountRaw().orElseThrow(); ++included; }
            }
            if (sum != parents.get(helper.parentOrdinal()).amount().orElseThrow().raw())
                return new NotReady("nested_quantity_original_output_mismatch");
        }
        return new VerifiedNestedRawSum((QuantityFold12004.VerifiedRawFold) outer, facts.helpers().size(), selected, included);
    }

    public static Observation decode(byte[] wire) {
        if (wire == null || wire.length == 0 || wire.length > 1_048_576) throw new IllegalArgumentException("bounded nested quantity wire");
        ObjectNode root = closed(parse(wire), "schema_version", "entry_rva", "scope", "status", "reason", "facts");
        if (i32(root.get("schema_version")) != 1 || i32(root.get("entry_rva")) != ENTRY_RVA)
            throw new IllegalArgumentException("exact nested quantity contract");
        Scope scope = LocalTargetScore12004.scope(root.get("scope")); String status = text(root.get("status"));
        if (status.equals("incomplete")) {
            if (!root.get("facts").isNull()) throw new IllegalArgumentException("incomplete facts must be null");
            return new Incomplete(scope, text(root.get("reason")));
        }
        if (!status.equals("available") || !root.get("reason").isNull()) throw new IllegalArgumentException("nested discriminant");
        ObjectNode f = closed(root.get("facts"), "original_fold", "helpers");
        QuantityFold12004.Observation fold = QuantityFold12004.decode(bytes(f.get("original_fold")));
        if (!(fold instanceof QuantityFold12004.Available available) || !scope.equals(fold.scope()))
            throw new IllegalArgumentException("same-scope original fold required");
        return new Available(new Facts(available.facts(), array(f.get("helpers"), NestedQuantitySum12004::helper)));
    }
    public static byte[] encode(Observation observation) {
        Objects.requireNonNull(observation); ObjectNode root = empty(); root.put("schema_version", 1); root.put("entry_rva", ENTRY_RVA);
        root.set("scope", LocalTargetScore12004.encodeScope(observation.scope()));
        if (observation instanceof Incomplete missing) {
            root.put("status", "incomplete"); root.put("reason", missing.reason()); root.putNull("facts"); return bytes(root);
        }
        root.put("status", "available"); root.putNull("reason"); Facts facts = ((Available) observation).facts(); ObjectNode f = root.putObject("facts");
        f.set("original_fold", parse(QuantityFold12004.encode(new QuantityFold12004.Available(facts.originalFold()))));
        ArrayNode helpers = f.putArray("helpers");
        for (Helper h : facts.helpers()) {
            ObjectNode n = helpers.addObject(); n.put("parent_ordinal", h.parentOrdinal()); n.put("secondary_operand_identity", h.secondaryOperandIdentity().decimal());
            n.put("output_address", h.outputAddress().decimal()); n.put("entry_flags_raw", h.entryFlagsRaw());
            n.put("member_storage_identity", h.memberStorageIdentity().decimal()); n.put("signed_count_raw", h.signedCountRaw());
            if (h.databaseIdentity().isPresent()) n.put("database_identity", h.databaseIdentity().orElseThrow().decimal()); else n.putNull("database_identity");
            ArrayNode members = n.putArray("members");
            for (Member m : h.members()) {
                ObjectNode e = members.addObject(); e.put("ordinal", m.ordinal());
                if (m.sourceHandleRaw().isPresent()) e.put("source_handle_raw", m.sourceHandleRaw().orElseThrow()); else e.putNull("source_handle_raw");
                e.put("selected_operand_identity", m.selectedOperandIdentity().decimal()); e.put("selected_signature_raw", m.selectedSignatureRaw());
                if (m.selectedFullIdRaw().isPresent()) e.put("selected_full_id_raw", m.selectedFullIdRaw().orElseThrow()); else e.putNull("selected_full_id_raw");
                if (m.amountRaw().isPresent()) e.put("amount_raw", Long.toString(m.amountRaw().orElseThrow())); else e.putNull("amount_raw");
            }
        }
        return bytes(root);
    }
    private static Helper helper(JsonNode node) {
        ObjectNode n = closed(node, "parent_ordinal", "secondary_operand_identity", "output_address", "entry_flags_raw", "member_storage_identity", "signed_count_raw", "database_identity", "members");
        Optional<UInt64> database = n.get("database_identity").isNull() ? Optional.empty() : Optional.of(pointer(n.get("database_identity")));
        return new Helper(i32(n.get("parent_ordinal")), pointer(n.get("secondary_operand_identity")), pointer(n.get("output_address")),
                i32(n.get("entry_flags_raw")), pointer(n.get("member_storage_identity")), i32(n.get("signed_count_raw")), database,
                array(n.get("members"), NestedQuantitySum12004::member));
    }
    private static Member member(JsonNode node) {
        ObjectNode n = closed(node, "ordinal", "source_handle_raw", "selected_operand_identity", "selected_signature_raw", "selected_full_id_raw", "amount_raw");
        Optional<Integer> handle = n.get("source_handle_raw").isNull() ? Optional.empty() : Optional.of(i32(n.get("source_handle_raw")));
        Optional<Integer> id = n.get("selected_full_id_raw").isNull() ? Optional.empty() : Optional.of(i32(n.get("selected_full_id_raw")));
        Optional<Long> amount = n.get("amount_raw").isNull() ? Optional.empty() : Optional.of(PairTargetScoreFactor12004.signed64(text(n.get("amount_raw"))));
        return new Member(i32(n.get("ordinal")), handle, pointer(n.get("selected_operand_identity")), i32(n.get("selected_signature_raw")), id, amount);
    }
    private static UInt64 pointer(JsonNode node) {
        String s = text(node); if (!s.matches("0|[1-9][0-9]{0,19}")) throw new IllegalArgumentException("canonical uint64 pointer");
        return new UInt64(new BigInteger(s));
    }
    private static void positive(UInt64 value) {
        Objects.requireNonNull(value); if (value.value().signum() <= 0) throw new IllegalArgumentException("positive pointer");
    }
}
