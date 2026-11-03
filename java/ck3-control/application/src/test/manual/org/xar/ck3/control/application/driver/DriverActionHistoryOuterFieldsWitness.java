package org.xar.ck3.control.application.driver;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.Evidence;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.EvidenceKind;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.Legacy;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.Recording;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.Source;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Arr;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Text;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Value;

/**
 * Software DATA witness for public outer-field and schema checks; validation receipts remain separate.
 * Exercises public RawJson -> decode outer fields and schema order only.
 * Logical software references bind to one real frozen body; they grant no archive authority.
 */
public final class DriverActionHistoryOuterFieldsWitness {
    private static final String V1 = "xar.java.original-action-history-source/v1";
    private static final String V2 = "xar.java.original-action-history-source/v2";
    private static final String MATERIAL = "software-material\n";
    private static final String SHA = "1391a85cdc98925b55469abd36c32e11da0eb258a88329bec81bced7a214d64c";
    private static final ExactRef REF = new ExactRef("software/fieldset/material", 18, SHA);
    private static final String CLOSED = "closed original action history source fields required";
    private static final String SCHEMA = "original action history source schema required";
    private static final String GIFT_GATE = "Gift pair cannot change its actual returned recording path";

    private DriverActionHistoryOuterFieldsWitness() { }

    public static void main(String[] args) {
        byte[] material = MATERIAL.getBytes(StandardCharsets.UTF_8);
        check(material.length == 18, "actual software body length");
        check(DriverJson.sha256(material).equals(SHA), "actual software body SHA");
        int passed = 0;

        var row = reversed(base());
        Source expected = new Source("fieldset-software", SHA, 1, REF, REF,
                ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT,
                new Legacy(Recording.RETURNED, Optional.of(REF), Optional.empty(),
                        List.of(new Evidence(EvidenceKind.MATERIAL, REF)), List.of(REF)));
        check(expected.equals(decode(row)), "P1-v1-exact14-reordered");
        passed++;

        // Exact18 reaches the real later gate. This is not valid Gift material success.
        reject("G1-gift-exact18-next-gate", giftSentinel(),
                ContractViolationException.class, GIFT_GATE);
        passed++;

        row = base();
        row.put("unexpected", Nil.INSTANCE);
        row.put("evidence", Nil.INSTANCE);
        reject("N1-v1-extra-before-body", row, ContractViolationException.class, CLOSED);
        passed++;

        row = base();
        row.remove("error");
        reject("N2-v1-missing-null-field", row, ContractViolationException.class, CLOSED);
        passed++;

        row = base();
        row.remove("error");
        row.put("unexpected", Nil.INSTANCE);
        row.put("schema", new Text("wrong"));
        reject("N3-v1-same-count-fields-before-schema", row,
                ContractViolationException.class, CLOSED);
        passed++;

        row = giftSentinel();
        row.put("unexpected", Nil.INSTANCE);
        row.put("evidence", Nil.INSTANCE);
        reject("N4-gift-extra-before-body", row, ContractViolationException.class, CLOSED);
        passed++;

        row = giftSentinel();
        row.remove("gift_originals");
        reject("N5-gift-missing-added-field", row, ContractViolationException.class, CLOSED);
        passed++;

        row = giftSentinel();
        row.remove("receipt_public_numbers");
        row.put("unexpected", Nil.INSTANCE);
        reject("N6-gift-same-count-substitution", row, ContractViolationException.class, CLOSED);
        passed++;

        row = base();
        row.put("schema", new Text(V2));
        reject("N7-gift-schema-with14", row, ContractViolationException.class, CLOSED);
        passed++;

        row = giftSentinel();
        row.put("schema", new Text(V1));
        reject("N8-v1-schema-with18", row, ContractViolationException.class, CLOSED);
        passed++;

        row = base();
        row.put("schema", new Text("wrong"));
        row.put("evidence", Nil.INSTANCE);
        reject("N9-wrong-schema-exact14-before-body", row,
                ContractViolationException.class, SCHEMA);
        passed++;

        row = base();
        row.put("schema", new Arr(List.of(new Text(V2))));
        row.put("evidence", Nil.INSTANCE);
        reject("N10-gift-looking-array-schema14", row,
                IllegalArgumentException.class, "schema must be nonempty text");
        passed++;

        row = giftSentinel();
        row.put("schema", new Arr(List.of(new Text(V2))));
        reject("N11-gift-looking-array-schema18", row, ContractViolationException.class, CLOSED);
        passed++;

        check(passed == 13, "all thirteen new outer-field cases reached");
        System.out.println("PASS DriverActionHistoryOuterFieldsWitness cases=" + passed);
    }

    private static LinkedHashMap<String, Value> base() {
        var row = new LinkedHashMap<String, Value>();
        row.put("schema", new Text(V1));
        row.put("action_id", new Text("fieldset-software"));
        row.put("body_sha256", new Text(SHA));
        row.put("durable_sequence", new IntegerValue(BigInteger.ONE));
        row.put("receipt", reference());
        row.put("record", reference());
        row.put("outcome", new Text("TERMINAL_WITHOUT_EFFECT"));
        row.put("representation", new Text("LEGACY_ROW"));
        row.put("recording", new Text("RETURNED"));
        row.put("canonical_reason", Nil.INSTANCE);
        row.put("result", reference());
        row.put("error", Nil.INSTANCE);
        row.put("evidence", new Arr(List.of(new Obj(Map.of(
                "kind", new Text("MATERIAL"), "reference", reference())))));
        row.put("producers", new Arr(List.of(reference())));
        return row;
    }

    private static LinkedHashMap<String, Value> giftSentinel() {
        var row = base();
        row.put("schema", new Text(V2));
        row.put("representation", new Text("CANONICAL_ONLY"));
        row.put("gift_originals", Nil.INSTANCE);
        row.put("receipt_result", Nil.INSTANCE);
        row.put("submit_public_numbers", Nil.INSTANCE);
        row.put("receipt_public_numbers", Nil.INSTANCE);
        return row;
    }

    private static Obj reference() {
        return new Obj(Map.of("path", new Text("software/fieldset/material"),
                "bytes", new IntegerValue(BigInteger.valueOf(18)), "sha256", new Text(SHA)));
    }

    private static LinkedHashMap<String, Value> reversed(Map<String, Value> row) {
        var entries = new ArrayList<>(row.entrySet());
        var reversed = new LinkedHashMap<String, Value>();
        for (int index = entries.size() - 1; index >= 0; index--) {
            var entry = entries.get(index);
            reversed.put(entry.getKey(), entry.getValue());
        }
        return reversed;
    }

    private static Source decode(Map<String, Value> row) {
        return DriverActionHistoryCodec.decode(new RawJson(DriverJson.encode(new Obj(row))));
    }

    private static void reject(String label, Map<String, Value> row,
            Class<? extends RuntimeException> type, String message) {
        try {
            decode(row);
        } catch (RuntimeException actual) {
            if (actual.getClass() != type || !message.equals(actual.getMessage())) {
                throw new AssertionError(label + ": unexpected exception", actual);
            }
            return;
        }
        throw new AssertionError(label + ": expected rejection");
    }

    private static void check(boolean condition, String label) {
        if (!condition) throw new AssertionError(label);
    }
}
