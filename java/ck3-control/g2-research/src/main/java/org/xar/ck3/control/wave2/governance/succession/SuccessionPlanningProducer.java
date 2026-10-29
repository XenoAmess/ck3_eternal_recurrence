package org.xar.ck3.control.wave2.governance.succession;

import static org.xar.ck3.control.wave2.governance.succession.SuccessionModel.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Set;

/** Original Driver's pure retain/reconcile projection. The caller still owns its real lock,
 * episode CAS, persistence and all UI/continuation authority. No method performs IO. */
public final class SuccessionPlanningProducer {
    public static final String SCHEMA = "xar.java-succession-planning-producer/v1";
    private SuccessionPlanningProducer() { }

    public enum Operation { RETAIN, RECONCILE }
    public sealed interface Input permits RetainInput, ReconcileInput {
        Operation operation();
        Snapshot snapshot();
        TurnBundle bundle();
        BigInteger expectedRevision();
    }
    public record RetainInput(Snapshot snapshot, TurnBundle bundle, BigInteger expectedRevision) implements Input {
        public RetainInput {
            currentRevision(snapshot, expectedRevision);
            Objects.requireNonNull(bundle);
            check(Boolean.TRUE.equals(snapshot.paused()) && !Boolean.TRUE.equals(snapshot.terminal()),
                    "succession expectation requires the current paused living frame");
            check(snapshot.episodeCharacterId() != null && snapshot.episodeRunId() != null
                    && !snapshot.episodeRunId().isEmpty(), "succession expectation requires an active episode identity");
        }
        @Override public Operation operation() { return Operation.RETAIN; }
    }
    public record ReconcileInput(Snapshot snapshot, TurnBundle bundle, Expectation expectation,
            BigInteger expectedRevision) implements Input {
        public ReconcileInput {
            currentRevision(snapshot, expectedRevision);
            Objects.requireNonNull(bundle);
            check(expectation != null, "succession reconciliation requires a retained expectation");
        }
        @Override public Operation operation() { return Operation.RECONCILE; }
    }

    public static byte[] apply(byte[] body) { return produce(decode(body)); }

    public static Input decode(byte[] body) {
        JsonNode request = SuccessionCodec.parse(body);
        String operation = SuccessionCodec.text(SuccessionCodec.field(request, "operation"));
        check(SCHEMA.equals(SuccessionCodec.text(SuccessionCodec.field(request, "schema"))),
                "succession planning producer schema changed");
        Set<String> fields = switch (operation) {
            case "retain" -> Set.of("schema", "operation", "snapshot", "turn_bundle", "expected_revision");
            case "reconcile" -> Set.of("schema", "operation", "snapshot", "turn_bundle", "expected_revision", "expectation");
            default -> throw new IllegalArgumentException("unknown succession producer operation");
        };
        SuccessionCodec.exact(request, fields);
        JsonNode revision = SuccessionCodec.field(request, "expected_revision");
        check(revision.isIntegralNumber(), "exact expected revision integer required");
        BigInteger expected = revision.bigIntegerValue();
        uint64(expected);
        Snapshot snapshot = SuccessionCodec.snapshot(SuccessionCodec.field(request, "snapshot"));
        TurnBundle bundle = SuccessionCodec.turnBundle(SuccessionCodec.field(request, "turn_bundle"), operation.equals("retain"));
        return operation.equals("retain") ? new RetainInput(snapshot, bundle, expected)
                : new ReconcileInput(snapshot, bundle,
                        SuccessionCodec.expectation(SuccessionCodec.field(request, "expectation")), expected);
    }

    public static byte[] produce(Input input) {
        Objects.requireNonNull(input);
        if (input instanceof RetainInput retain) {
            Expectation expectation = SuccessionPolicy.freeze(retain.bundle(), retain.snapshot().episodeRunId(),
                    retain.snapshot().episodeCharacterId());
            check(expectation.binding().frame().equals(retain.snapshot().frame()),
                    "succession expectation crossed the current source frame");
            return SuccessionCodec.encodeExpectation(expectation);
        }
        ReconcileInput reconcile = (ReconcileInput) input;
        return SuccessionCodec.encodeReconciliation(SuccessionPolicy.reconcile(reconcile.expectation(),
                reconcile.snapshot(), reconcile.bundle()));
    }

    private static void currentRevision(Snapshot snapshot, BigInteger expectedRevision) {
        uint64(expectedRevision);
        check(snapshot != null && snapshot.frame() != null
                && snapshot.frame().revision().equals(expectedRevision),
                "succession producer crossed the current revision");
    }
}
