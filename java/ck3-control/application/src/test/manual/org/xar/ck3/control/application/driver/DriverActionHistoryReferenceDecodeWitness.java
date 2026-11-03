// Public DATA manual witness; original software qualification is recorded separately.
package org.xar.ck3.control.application.driver;

import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionReceipt.Outcome;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.CanonicalOnly;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.CanonicalReason;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.Evidence;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.EvidenceKind;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.Legacy;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.OriginalMaterial;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.Recording;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.Source;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;

/**
 * NONBLIND design-known manual witness through public decode only.
 * The five pinned originals are software DATA, not canonical receipts, records,
 * actions, archive membership, current authority or a writer/issuer qualification.
 * Malformed references exist only in raw JSON; no invalid typed ExactRef is made.
 * No source encoder, private helper, reflection, Proxy, JUnit or filesystem I/O.
 */
public final class DriverActionHistoryReferenceDecodeWitness {
    private static final String ORIGINALS =
            "software/reference-data/";
    private static final String BODY_SHA =
            "a7d609f154a1bfe42834559544932ac08e3fd5997e16e5bcf8e5a20f279a5b9f";
    private static final ExactRef RECEIPT = new ExactRef(ORIGINALS + "receipt-data.json", 38,
            "f25270a988ac11ba77bd57014696a5bdef8c7c498f130cafa3b521d7ea30b4aa");
    private static final ExactRef RECORD = new ExactRef(ORIGINALS + "record-data.json", 37,
            "af6d6c9e95fb2379a4b08a396d71d56792bdd02369e1fb66c503d089881a0517");
    private static final ExactRef MATERIAL = new ExactRef(ORIGINALS + "material-data.json", 39,
            "9c4742dd181f1b9a07e90d2620e0a96cb53c817dacddd11339fb45fd145f84fd");
    private static final ExactRef PRODUCER = new ExactRef(ORIGINALS + "producer-data.json", 39,
            "27273167d60fdd88ae26b25696f54559f9ab27827bc0cb13f98d5f20220474b4");

    private DriverActionHistoryReferenceDecodeWitness() { }

    public static void main(String[] args) {
        verifyActualPayloads();
        String receipt = referenceWire(RECEIPT);
        String record = referenceWire(RECORD);
        String evidence = reorderedReferenceWire(MATERIAL);
        String producer = referenceWire(PRODUCER);
        int passed = 0;

        Source canonicalExpected = expected(new CanonicalOnly(
                CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER, evidence(), List.of(PRODUCER)));
        equal("P1 canonical four reference sites", canonicalExpected,
                decode(canonical(receipt, record, evidence, producer)));
        passed++;

        Source legacyExpected = expected(new Legacy(Recording.RETURNED,
                Optional.of(MATERIAL), Optional.empty(), evidence(), List.of(PRODUCER)));
        equal("P2 legacy optional result reference", legacyExpected,
                decode(legacy(referenceWire(MATERIAL))));
        passed++;

        expectFailure("N1 evidence reference object", IllegalArgumentException.class,
                "reference must be an object", false,
                () -> decode(canonical(receipt, record, "[]", producer)));
        passed++;

        String extraProducer = "{\"path\":\"\",\"bytes\":-1,\"sha256\":\"\",\"extra\":true}";
        expectFailure("N2 producer fields before values", ContractViolationException.class,
                "exact JSON fields required: ", true,
                () -> decode(canonical(receipt, record, evidence, extraProducer)));
        passed++;

        String emptyPath = "{\"path\":\"\",\"bytes\":-1,\"sha256\":\"\"}";
        expectFailure("N3 receipt path before bytes", ContractViolationException.class,
                "nonempty bounded text required", false,
                () -> decode(canonical(emptyPath, record, evidence, producer)));
        passed++;

        String decimalBytes = "{\"path\":\"software/bad.json\",\"bytes\":1.0,\"sha256\":\"\"}";
        expectFailure("N4 record integer token before SHA", ContractViolationException.class,
                "exact JSON integer required; no boolean, float or string", false,
                () -> decode(canonical(receipt, decimalBytes, evidence, producer)));
        passed++;

        String outsideSafeRange =
                "{\"path\":\"software/bad.json\",\"bytes\":9007199254740992,\"sha256\":\"\"}";
        expectFailure("N5 evidence safe range before SHA", ContractViolationException.class,
                "integer outside contract range", false,
                () -> decode(canonical(receipt, record, outsideSafeRange, producer)));
        passed++;

        String badSha = "{\"path\":\"software/bad.json\",\"bytes\":1,\"sha256\":\"z\"}";
        expectFailure("N6 receipt lowercase SHA", ContractViolationException.class,
                "lowercase SHA-256 required", false,
                () -> decode(canonical(badSha, record, evidence, producer)));
        passed++;

        String zeroResult = "{\"path\":\"software/bad.json\",\"bytes\":0,\"sha256\":\""
                + MATERIAL.sha256() + "\"}";
        expectFailure("N7 zero result outer nonempty", ContractViolationException.class,
                "nonempty original reference required", false,
                () -> decode(legacy(zeroResult)));
        passed++;

        String duplicatePath = "{\"path\":\"software/first.json\",\"path\":\"software/second.json\","
                + "\"bytes\":" + RECEIPT.bytes() + ",\"sha256\":\"" + RECEIPT.sha256() + "\"}";
        expectFailure("N8 duplicate raw entry", IllegalArgumentException.class,
                "invalid UTF-8/duplicate/token Native JSON", false,
                () -> decode(canonical(duplicatePath, record, evidence, producer)));
        passed++;

        System.out.println("PASS public reference decode software DATA cases=" + passed);
    }

    private static void verifyActualPayloads() {
        payload("receipt", "{\"software_data\":\"receipt-role-only\"}\n", RECEIPT);
        payload("record", "{\"software_data\":\"record-role-only\"}\n", RECORD);
        payload("material", "{\"software_data\":\"material-role-only\"}\n", MATERIAL);
        payload("producer", "{\"software_data\":\"producer-role-only\"}\n", PRODUCER);
        byte[] body = bytes("{\"software_action\":\"DATA_ONLY\"}\n");
        equal("actual body bytes", 32L, (long) body.length);
        equal("actual body SHA", BODY_SHA, DriverJson.sha256(body));
    }

    private static void payload(String label, String original, ExactRef reference) {
        byte[] actual = bytes(original);
        equal(label + " actual bytes", reference.bytes(), (long) actual.length);
        equal(label + " actual SHA", reference.sha256(), DriverJson.sha256(actual));
    }

    private static Source expected(OriginalMaterial material) {
        return new Source("software-action", BODY_SHA, 1, RECEIPT, RECORD,
                Outcome.TERMINAL_WITHOUT_EFFECT, material);
    }

    private static List<Evidence> evidence() {
        return List.of(new Evidence(EvidenceKind.MATERIAL, MATERIAL));
    }

    private static Source decode(String literal) {
        return DriverActionHistoryCodec.decode(new RawJson(bytes(literal)));
    }

    private static String canonical(String receipt, String record, String evidence, String producer) {
        return wire("CANONICAL_ONLY", "null", "\"DIRECT_API_WITHOUT_LEGACY_RECORDER\"", "null",
                receipt, record, evidence, producer);
    }

    private static String legacy(String result) {
        return wire("LEGACY_ROW", "\"RETURNED\"", "null", result,
                referenceWire(RECEIPT), referenceWire(RECORD),
                reorderedReferenceWire(MATERIAL), referenceWire(PRODUCER));
    }

    // Literal fixture assembly only; expected results use public typed constructors above.
    private static String wire(String representation, String recording, String reason, String result,
            String receipt, String record, String evidence, String producer) {
        return """
                {"schema":"xar.java.original-action-history-source/v1","action_id":"software-action",
                 "body_sha256":"%s","durable_sequence":1,"receipt":%s,"record":%s,
                 "outcome":"TERMINAL_WITHOUT_EFFECT","representation":"%s","recording":%s,
                 "canonical_reason":%s,"result":%s,"error":null,
                 "evidence":[{"kind":"MATERIAL","reference":%s}],"producers":[%s]}
                """.formatted(BODY_SHA, receipt, record, representation, recording, reason, result, evidence, producer);
    }

    private static String referenceWire(ExactRef reference) {
        return "{\"path\":\"" + reference.path() + "\",\"bytes\":" + reference.bytes()
                + ",\"sha256\":\"" + reference.sha256() + "\"}";
    }

    private static String reorderedReferenceWire(ExactRef reference) {
        return "{\"sha256\":\"" + reference.sha256() + "\",\"bytes\":" + reference.bytes()
                + ",\"path\":\"" + reference.path() + "\"}";
    }

    private static byte[] bytes(String value) {
        return value.getBytes(StandardCharsets.UTF_8);
    }

    private static void equal(String label, Object expected, Object actual) {
        if (!Objects.equals(expected, actual)) {
            throw new AssertionError(label + ": expected " + expected + ", actual " + actual);
        }
    }

    private static void expectFailure(String label, Class<? extends RuntimeException> expectedType,
            String message, boolean prefix, Runnable action) {
        try {
            action.run();
        } catch (RuntimeException failure) {
            if (failure.getClass() != expectedType) {
                throw new AssertionError(label + ": wrong exception type", failure);
            }
            String actual = failure.getMessage();
            boolean matches = prefix ? actual != null && actual.startsWith(message) : message.equals(actual);
            if (!matches) {
                throw new AssertionError(label + ": wrong exception message: " + actual, failure);
            }
            return;
        }
        throw new AssertionError(label + ": expected " + expectedType.getName());
    }
}
