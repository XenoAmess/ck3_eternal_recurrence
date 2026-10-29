package org.xar.ck3.control.events.mandatorychoice;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import org.xar.ck3.control.contracts.index.OrderedCandidateIndex;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.ChoiceEntry;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.FrameBinding;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.Mode;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.NativeChoice;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.NativeWindow;

/** Runs the original Python producer, then the actual Java codec/policy and indexed consumer. */
public final class IndexedNativeChoicesProducerTestMain {
    private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);
    private static final String PRODUCER_SHA = "e78a9b2a80f2dc08137546868ebd2350af11c987aaf8db9b434b5485cd1e6fd7";
    private static final String CORPUS_SHA = "2c7a1631dd15b54e2a2193354dc31308491319e8afdb7fcc45f8d6551d6d3649";
    private static final String ORACLE = """
            import json,runpy,sys
            policy=runpy.run_path(sys.argv[1])
            rows=json.load(sys.stdin)
            outputs=[]
            for row in rows:
                name='select_unknown_mandatory_choice_v1' if row['mode']=='unknown' else 'select_existing_native_choice_v1'
                outputs.append(policy[name](row['input'],expected_frame=row['expected_frame']))
            json.dump(outputs,sys.stdout,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
            """;
    private record Scope(String sourceSha256, String snapshot, BigInteger revision, BigInteger ownerVersion) { }
    private IndexedNativeChoicesProducerTestMain() { }
    private static void check(boolean condition, String reason) { if (!condition) { throw new AssertionError(reason); } }
    private static byte[] pinned(Path source, String sha) throws Exception {
        byte[] raw = Files.readAllBytes(source);
        check(raw.length > 0 && raw.length <= 1_048_576, "finite oracle source/corpus");
        check(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)).equals(sha), "source/corpus drift: " + source);
        return raw;
    }
    private static void stale(Runnable operation, String reason) {
        try { operation.run(); } catch (IllegalStateException expected) { return; }
        throw new AssertionError(reason);
    }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 3) { throw new IllegalArgumentException("original producer path, retained corpus path and qualified default Python executable required"); }
        Path producer = Path.of(arguments[0]).toAbsolutePath();
        Path corpus = Path.of(arguments[1]).toAbsolutePath();
        Path pythonExecutable = Path.of(arguments[2]);
        check(pythonExecutable.isAbsolute() && Files.isRegularFile(pythonExecutable), "actual qualified Python executable path required");
        byte[] producerBefore = pinned(producer, PRODUCER_SHA), corpusBefore = pinned(corpus, CORPUS_SHA);
        JsonNode retained = JSON.readTree(corpusBefore);
        ArrayNode cases = retained.get("cases").deepCopy();
        check(cases.size() == 17, "all retained original17 vectors required");
        ObjectNode sameLabel = (ObjectNode) cases.get(0).deepCopy();
        sameLabel.put("name", "index_same_display_label_preserves_two_distinct_identities");
        ArrayNode labelChoices = (ArrayNode) sameLabel.get("input").get("choices");
        ((ObjectNode) labelChoices.get(0)).put("label", "same"); ((ObjectNode) labelChoices.get(1)).put("label", "same");
        cases.add(sameLabel);
        ObjectNode nonchoice = (ObjectNode) cases.get(0).deepCopy(); nonchoice.put("name", "index_null_nonchoice_complete_membership");
        ((ArrayNode) nonchoice.get("input").get("choices")).addNull(); cases.add(nonchoice);
        ObjectNode big = (ObjectNode) cases.get(0).deepCopy(); big.put("name", "index_uint64_identity_exact");
        ((ObjectNode) big.get("input").get("choices").get(0)).put("choice_id", new BigInteger("18446744073709551615")); cases.add(big);
        ObjectNode zero = (ObjectNode) cases.get(0).deepCopy(); zero.put("name", "index_signedzero_source_bits");
        ((ObjectNode) zero.get("input").get("choices").get(0).get("bounds")).put("top", -0.0); cases.add(zero);
        ObjectNode missingLabel = (ObjectNode) cases.get(0).deepCopy(); missingLabel.put("name", "index_missing_null_labels_distinct");
        ((ObjectNode) missingLabel.get("input").get("choices").get(0)).remove("label");
        ((ObjectNode) missingLabel.get("input").get("choices").get(1)).putNull("label"); cases.add(missingLabel);
        for (String axis : List.of("top", "left")) {
            ObjectNode signedOrder = (ObjectNode) cases.get(0).deepCopy();
            signedOrder.put("name", "index_signedzero_order_" + axis);
            ((ObjectNode) signedOrder.get("input").get("choices").get(0).get("bounds")).put(axis, 0.0);
            ((ObjectNode) signedOrder.get("input").get("choices").get(1).get("bounds")).put(axis, -0.0);
            cases.add(signedOrder);
        }
        Process oracle = new ProcessBuilder(pythonExecutable.toString(), "-X", "utf8", "-I", "-B", "-c", ORACLE, producer.toString())
                .redirectError(ProcessBuilder.Redirect.INHERIT).start();
        byte[] oracleRaw;
        try {
            try (var input = oracle.getOutputStream()) { JSON.writeValue(input, cases); }
            oracleRaw = oracle.getInputStream().readNBytes(1_048_577);
            check(oracleRaw.length <= 1_048_576, "finite original producer output");
            check(oracle.waitFor(30, TimeUnit.SECONDS), "original producer deadline");
            check(oracle.exitValue() == 0, "original producer exit");
        } finally {
            if (oracle.isAlive()) { oracle.destroyForcibly(); oracle.waitFor(30, TimeUnit.SECONDS); }
        }
        JsonNode actualOriginal = JSON.readTree(oracleRaw);
        check(actualOriginal.isArray() && actualOriginal.size() == cases.size(), "complete original output arity");
        for (int caseIndex = 0; caseIndex < cases.size(); caseIndex++) {
            JsonNode vector = cases.get(caseIndex); byte[] raw = JSON.writeValueAsBytes(vector.get("input"));
            NativeWindow window = MandatoryChoiceCodec.decode(raw);
            var active = new AtomicBoolean(true);
            var scope = new Scope(PRODUCER_SHA, window.frame().snapshotId(), window.frame().revision(), BigInteger.ONE);
            OrderedCandidateIndex.ScopeGuard<Scope> guard = expected -> {
                if (!active.get() || expected != scope) { throw new IllegalStateException("original scope revoked"); }
            };
            IndexedNativeChoices<Scope> indexed = IndexedNativeChoices.build(scope, guard, window);
            List<OrderedCandidateIndex.Slot<MandatoryChoiceModel.ChoiceIdentity, ChoiceEntry>> entries = indexed.entries();
            check(entries.size() == vector.get("input").get("choices").size(), "all native choices/nonchoices retained");
            for (int index = 0; index < entries.size(); index++) {
                check(entries.get(index).position() == index && entries.get(index).value() == window.choices().get(index),
                        "native original position/object retained");
                if (entries.get(index).value() instanceof NativeChoice choice) {
                    check(indexed.matching(choice.identity()).stream().anyMatch(slot -> slot.position() == choice.inputIndex()),
                            "every duplicate identity retained in lookup");
                }
            }
            Optional<FrameBinding> expected = vector.get("expected_frame").isNull() ? Optional.empty()
                    : Optional.of(MandatoryChoiceCodec.decodeFrame(JSON.writeValueAsBytes(vector.get("expected_frame"))));
            Mode mode = vector.get("mode").asText().equals("unknown") ? Mode.UNKNOWN_MANDATORY : Mode.EXISTING_NATIVE_DOMAIN;
            JsonNode indexedOutput = JSON.readTree(MandatoryChoiceCodec.encodeDecision(indexed.select(expected, mode)));
            check(indexedOutput.equals(actualOriginal.get(caseIndex)), "real producer differential: " + vector.get("name"));
            check(indexedOutput.equals(JSON.readTree(MandatoryChoiceCodec.select(raw, mode, expected))), "actual Java consumer parity");
            check(!indexed.select(expected, mode).replayAllowed(), "recommendation cannot grant replay");
            active.set(false);
            stale(indexed::entries, "UNKNOWN invalidates complete catalogue lookup");
            stale(() -> indexed.select(expected, mode), "UNKNOWN cannot select again");
        }
        check(java.util.Arrays.equals(producerBefore, pinned(producer, PRODUCER_SHA)), "original producer postguard");
        check(java.util.Arrays.equals(corpusBefore, pinned(corpus, CORPUS_SHA)), "retained corpus postguard");
        System.out.println("INDEXED_NATIVE_CHOICES_PRODUCER_PASS vectors=" + cases.size() + " original17=17 added7=7 signedzero_order=2 source_prepost=MATCH");
    }
}
