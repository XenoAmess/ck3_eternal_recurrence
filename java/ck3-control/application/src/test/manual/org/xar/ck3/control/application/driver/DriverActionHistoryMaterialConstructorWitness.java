// Software DATA manual: typed constructors and public erased-ABI cases; validation receipts remain separate.
package org.xar.ck3.control.application.driver;

import java.lang.invoke.MethodHandle;
import java.lang.invoke.MethodHandles;
import java.lang.invoke.MethodType;
import java.nio.charset.StandardCharsets;
import java.util.AbstractList;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.CanonicalOnly;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.CanonicalReason;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.Evidence;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.EvidenceKind;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.Legacy;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.Recording;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;

/**
 * NONBLIND original-contract manual witness; ordinary typed calls are separate
 * from explicitly authorized public MethodHandles erased-ABI calls.
 * ObjectList is collection-consistent and contains exactly its declared Objects.
 * No private lookup, issuer, Unsafe, unchecked cast, lint suppression or JUnit.
 * Software DATA only; no action receipt, archive, Native, writer or file access.
 */
public final class DriverActionHistoryMaterialConstructorWitness {
    private static final String SHA =
            "1391a85cdc98925b55469abd36c32e11da0eb258a88329bec81bced7a214d64c";
    private static final ExactRef MATERIAL = reference("material");
    private static final ExactRef PRODUCER = reference("producer");
    private static final ExactRef ZERO = new ExactRef("software/cardinality/empty", 0,
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
    private static final Evidence INDEPENDENT = new Evidence(EvidenceKind.MATERIAL, MATERIAL);
    private static final CanonicalReason REASON = CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER;
    private static final String EVIDENCE_MESSAGE =
            "independent original material is mandatory; a receipt/record alone is not Driver history material";
    private static final String PRODUCER_MESSAGE = "finite exact original producer sources required";
    private static final String NONEMPTY_MESSAGE = "nonempty original reference required";
    private static final String LEGACY_MESSAGE =
            "actual returned result or raised original error required; no invented empty result";

    private DriverActionHistoryMaterialConstructorWitness() { }

    public static void main(String[] args) throws Throwable {
        byte[] material = "software-material\n".getBytes(StandardCharsets.UTF_8);
        equal("actual software material length", 18L, (long) material.length);
        equal("actual software material SHA", SHA, DriverJson.sha256(material));
        equal("actual empty material SHA", ZERO.sha256(), DriverJson.sha256(new byte[0]));
        int passed = 0;

        List<Evidence> evidenceInput = new ArrayList<>(List.of(INDEPENDENT));
        List<ExactRef> producerInput = new ArrayList<>(List.of(PRODUCER));
        CanonicalOnly singleton = new CanonicalOnly(REASON, evidenceInput, producerInput);
        evidenceInput.clear();
        producerInput.clear();
        equal("P1 retained evidence snapshot", List.of(INDEPENDENT), singleton.evidence());
        equal("P1 retained producer snapshot", List.of(PRODUCER), singleton.producers());
        expectFailure("P1 immutable evidence", UnsupportedOperationException.class, null,
                () -> singleton.evidence().add(INDEPENDENT));
        expectFailure("P1 immutable producers", UnsupportedOperationException.class, null,
                () -> singleton.producers().clear());
        passed++;

        Legacy legacy = new Legacy(Recording.RETURNED, Optional.of(MATERIAL), Optional.empty(),
                List.of(INDEPENDENT), List.of(PRODUCER));
        equal("P2 recording", Recording.RETURNED, legacy.recording());
        equal("P2 original result", Optional.of(MATERIAL), legacy.result());
        equal("P2 evidence", List.of(INDEPENDENT), legacy.evidence());
        equal("P2 producers", List.of(PRODUCER), legacy.producers());
        passed++;

        List<Evidence> maximumEvidence = new ArrayList<>();
        for (int index = 0; index < 128; index++) {
            maximumEvidence.add(new Evidence(EvidenceKind.MATERIAL, reference("evidence/" + index)));
        }
        List<ExactRef> maximumProducers = new ArrayList<>();
        for (int index = 0; index < 64; index++) maximumProducers.add(reference("producer/" + index));
        CanonicalOnly maximum = new CanonicalOnly(REASON, maximumEvidence, maximumProducers);
        equal("P3 inclusive evidence bound/order", maximumEvidence, maximum.evidence());
        equal("P3 inclusive producer bound/order", maximumProducers, maximum.producers());
        passed++;

        expectFailure("N1 empty evidence before null producers", ContractViolationException.class,
                EVIDENCE_MESSAGE, () -> new CanonicalOnly(REASON, List.of(), null));
        passed++;
        expectFailure("N2 null evidence", NullPointerException.class, null,
                () -> new CanonicalOnly(REASON, null, List.of()));
        passed++;
        List<Evidence> nullEvidence = Collections.singletonList(null);
        expectFailure("N3 null evidence element", NullPointerException.class, null,
                () -> new CanonicalOnly(REASON, nullEvidence, List.of()));
        passed++;

        expectFailure("N5 duplicate evidence", ContractViolationException.class, EVIDENCE_MESSAGE,
                () -> new CanonicalOnly(REASON, List.of(INDEPENDENT, INDEPENDENT), List.of(PRODUCER)));
        passed++;
        Evidence receiptRole = new Evidence(EvidenceKind.ACTION_RECEIPT, MATERIAL);
        expectFailure("N6 receipt-role-only singleton", ContractViolationException.class, EVIDENCE_MESSAGE,
                () -> new CanonicalOnly(REASON, List.of(receiptRole), List.of(PRODUCER)));
        passed++;
        expectFailure("N7 empty producers", ContractViolationException.class, PRODUCER_MESSAGE,
                () -> new CanonicalOnly(REASON, List.of(INDEPENDENT), List.of()));
        passed++;
        expectFailure("N8 null producers", NullPointerException.class, null,
                () -> new CanonicalOnly(REASON, List.of(INDEPENDENT), null));
        passed++;
        List<ExactRef> nullProducer = Collections.singletonList(null);
        expectFailure("N9 null producer element", NullPointerException.class, null,
                () -> new CanonicalOnly(REASON, List.of(INDEPENDENT), nullProducer));
        passed++;
        expectFailure("N11 duplicate zero before nonempty", ContractViolationException.class, PRODUCER_MESSAGE,
                () -> new CanonicalOnly(REASON, List.of(INDEPENDENT), List.of(ZERO, ZERO)));
        passed++;
        expectFailure("N12 singleton zero late nonempty", ContractViolationException.class, NONEMPTY_MESSAGE,
                () -> new CanonicalOnly(REASON, List.of(INDEPENDENT), List.of(ZERO)));
        passed++;
        expectFailure("N13 legacy path before evidence", ContractViolationException.class, LEGACY_MESSAGE,
                () -> new Legacy(Recording.RETURNED, Optional.empty(), Optional.empty(), null, List.of()));
        passed++;

        // Public erased ABI only. Generic element declarations are not private authority.
        MethodHandle publicConstructor = MethodHandles.publicLookup().findConstructor(CanonicalOnly.class,
                MethodType.methodType(void.class, CanonicalReason.class, List.class, List.class));

        HashProbe oversizedEvidence = new HashProbe("software oversized evidence hash");
        List<Object> evidence129 = new ObjectList(129, oversizedEvidence);
        expectFailure("N4 evidence bound before foreign hash", ContractViolationException.class, EVIDENCE_MESSAGE,
                () -> erased(publicConstructor, evidence129, List.of(PRODUCER)));
        equal("N4 hash callbacks", 0, oversizedEvidence.calls);
        passed++;

        HashProbe oversizedProducer = new HashProbe("software oversized producer hash");
        List<Object> producers65 = new ObjectList(65, oversizedProducer);
        expectFailure("N10 producer bound before foreign hash", ContractViolationException.class, PRODUCER_MESSAGE,
                () -> erased(publicConstructor, List.of(INDEPENDENT), producers65));
        equal("N10 hash callbacks", 0, oversizedProducer.calls);
        passed++;

        HashProbe foreignEvidence = new HashProbe("software foreign evidence singleton hash");
        List<Object> evidenceOne = new ObjectList(1, foreignEvidence);
        expectSame("N14 evidence singleton original hash", foreignEvidence.marker,
                () -> erased(publicConstructor, evidenceOne, List.of(PRODUCER)));
        equal("N14 hash callbacks", 1, foreignEvidence.calls);
        passed++;

        HashProbe foreignProducer = new HashProbe("software foreign producer singleton hash");
        List<Object> producersOne = new ObjectList(1, foreignProducer);
        expectSame("N15 producer singleton original hash", foreignProducer.marker,
                () -> erased(publicConstructor, List.of(INDEPENDENT), producersOne));
        equal("N15 hash callbacks", 1, foreignProducer.calls);
        passed++;

        System.out.println("PASS public material constructors software DATA cases=" + passed);
    }

    private static CanonicalOnly erased(MethodHandle constructor, List<?> evidence, List<?> producers)
            throws Throwable {
        return (CanonicalOnly) constructor.invokeExact(REASON, evidence, producers);
    }

    private static ExactRef reference(String suffix) {
        return new ExactRef("software/cardinality/" + suffix, 18, SHA);
    }

    private static void equal(String label, Object expected, Object actual) {
        if (!Objects.equals(expected, actual)) {
            throw new AssertionError(label + ": expected " + expected + ", actual " + actual);
        }
    }

    @FunctionalInterface
    private interface ThrowingAction {
        void run() throws Throwable;
    }

    private static void expectFailure(String label, Class<? extends Throwable> expectedType,
            String message, ThrowingAction action) throws Throwable {
        try {
            action.run();
        } catch (Throwable failure) {
            if (failure.getClass() != expectedType) throw failure;
            if (message != null && !message.equals(failure.getMessage())) {
                throw new AssertionError(label + ": wrong original message: " + failure.getMessage(), failure);
            }
            return;
        }
        throw new AssertionError(label + ": expected " + expectedType.getName());
    }

    private static void expectSame(String label, Throwable marker, ThrowingAction action) throws Throwable {
        try {
            action.run();
        } catch (Throwable failure) {
            if (failure != marker) throw failure;
            return;
        }
        throw new AssertionError(label + ": expected original marker identity");
    }

    /** Consistent public collection: iterator/toArray inherit these exact Object elements. */
    private static final class ObjectList extends AbstractList<Object> {
        private final Object[] elements;
        private ObjectList(int size, Object value) {
            elements = new Object[size];
            Arrays.fill(elements, value);
        }
        @Override public Object get(int index) { return elements[Objects.checkIndex(index, elements.length)]; }
        @Override public int size() { return elements.length; }
    }

    private static final class HashProbe {
        private final RuntimeException marker;
        private int calls;
        private HashProbe(String message) { marker = new IllegalStateException(message); }
        @Override public int hashCode() { calls++; throw marker; }
    }
}
