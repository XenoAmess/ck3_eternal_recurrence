package org.xar.ck3.control.application.driver;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Public constructor DATA only. No Native, writer, Managed frame or source authority. */
public final class KnownConstructorCompatibilityWitness {
    private KnownConstructorCompatibilityWitness() { }

    public static void main(String[] args) {
        if (args.length == 1 && "baseline321".equals(args[0])) {
            baseline321MustReturnWithOneEncode();
            return;
        }
        check(args.length == 0, "this witness has one original-compatibility expectation");
        changingActorMustRejectAfterBothLateEncodes();
        secondEncodeFailureMustRemainObservable();
        thirdEncodeFailureMustRemainObservable();
        standardActorMustRetainSameDriver();
        System.out.println("PASS cases=4 same_driver=true script_callbacks=3,2,3 standard_returned=true authority=false");
    }

    private static void standardActorMustRetainSameDriver() {
        GameGeneration game = new GameGeneration(17, new PythonOnlyUInt64(BigInteger.ONE));
        DriverStateSnapshot.Complete driver = driver(BigInteger.valueOf(73));
        DriverSnapshotFacts.Stamp stamp = new DriverSnapshotFacts.Stamp(7, 2, game,
                "software-known-episode", DriverJson.sha256(driver.encode()));
        ExactRef semantic = reference("software-data/semantic.json", "{}");
        ExactRef history = reference("software-data/history-basis.json", "[]");
        G2Source source = new G2Source("software-only", "1970-01-01T00:00:00Z",
                "known-public-data", semantic);
        NativeObservationPort.TransportSession transport = new NativeObservationPort.TransportSession(
                "software-only", game, BigInteger.ONE, "software-known-session");
        DriverObservationFacts observation = new DriverObservationFacts(driver, 7, 2, transport,
                "software-known-snapshot", BigInteger.ONE,
                DriverJson.sha256("{}".getBytes(StandardCharsets.UTF_8)), BigInteger.ONE, 1,
                source, new OpportunityJson.Obj(Map.of()), semantic);
        DriverSnapshotFacts.Known known = new DriverSnapshotFacts.Known(driver, stamp, history,
                List.of(), new OpportunityJson.Obj(Map.of()), Optional.empty(), Optional.of(observation));
        check(known.driver() == driver, "standard actor constructor changed its supplied driver");
        check(known.observation().orElseThrow() == observation,
                "standard actor constructor changed its supplied observation");
    }

    private static void baseline321MustReturnWithOneEncode() {
        Fixture fixture = fixture(new String[] {"73", "74", "73"}, 0, null);
        DriverSnapshotFacts.Known returned = constructKnown(fixture);
        check(returned.driver() == fixture.driver(), "baseline321 returned another driver");
        check(fixture.actor().calls() == 1,
                "baseline321 must expose its actual single encode; stringify calls="
                        + fixture.actor().calls());
        System.out.println("PASS baseline_only=true baseline=321 returned=true actor_calls=1 authority=false");
    }

    private static void changingActorMustRejectAfterBothLateEncodes() {
        Fixture fixture = fixture(new String[] {"73", "74", "73"}, 0, null);
        try {
            constructKnown(fixture);
            throw new AssertionError("original semantic mismatch was accepted; stringify calls="
                    + fixture.actor().calls());
        } catch (ContractViolationException expected) {
            check("semantic facts crossed Driver version".equals(expected.getMessage()),
                    "wrong original failure before semantic comparison");
        }
        check(fixture.actor().calls() == 3,
                "both late encodes must finish before original mismatch; stringify calls="
                        + fixture.actor().calls());
    }

    private static void secondEncodeFailureMustRemainObservable() {
        ScriptFailure sentinel = new ScriptFailure("second actor stringify");
        Fixture fixture = fixture(new String[] {"73"}, 2, sentinel);
        requireScriptFailure(fixture, sentinel, 2);
    }

    private static void thirdEncodeFailureMustRemainObservable() {
        ScriptFailure sentinel = new ScriptFailure("third actor stringify");
        Fixture fixture = fixture(new String[] {"73", "73"}, 3, sentinel);
        requireScriptFailure(fixture, sentinel, 3);
    }

    private static void requireScriptFailure(Fixture fixture, ScriptFailure sentinel,
            int expectedCalls) {
        Throwable observed = null;
        try {
            constructKnown(fixture);
        } catch (RuntimeException | Error failure) {
            observed = failure;
        }
        check(observed != null, "original late encode failure was skipped; stringify calls="
                + fixture.actor().calls());
        check(containsIdentity(observed, sentinel),
                "an unrelated failure cannot stand in for the scripted actor callback");
        check(fixture.actor().calls() == expectedCalls,
                "wrong original stringify position; calls=" + fixture.actor().calls());
    }

    private static boolean containsIdentity(Throwable observed, Throwable sentinel) {
        Throwable cursor = observed;
        for (int depth = 0; cursor != null && depth < 32; depth++) {
            if (cursor == sentinel) return true;
            Throwable next = cursor.getCause();
            if (next == cursor) return false;
            cursor = next;
        }
        return false;
    }

    private static DriverSnapshotFacts.Known constructKnown(Fixture fixture) {
        check(fixture.observation().driver() == fixture.driver(),
                "this regression requires the identical public Complete object");
        return new DriverSnapshotFacts.Known(fixture.driver(), fixture.stamp(),
                fixture.historyBasis(), List.of(), new OpportunityJson.Obj(Map.of()),
                Optional.empty(), Optional.of(fixture.observation()));
    }

    private static Fixture fixture(String[] tokens, int throwAt, ScriptFailure failure) {
        GameGeneration game = new GameGeneration(17, new PythonOnlyUInt64(BigInteger.ONE));
        // Compute stamp from a separate stable object before constructing the script actor.
        DriverStateSnapshot.Complete stable = driver(BigInteger.valueOf(73));
        DriverSnapshotFacts.Stamp stamp = new DriverSnapshotFacts.Stamp(7, 2, game,
                "software-known-episode", DriverJson.sha256(stable.encode()));
        ScriptedActor actor = new ScriptedActor(tokens, throwAt, failure);
        DriverStateSnapshot.Complete mutable = driver(actor);
        ExactRef semantic = reference("software-data/semantic.json", "{}");
        ExactRef history = reference("software-data/history-basis.json", "[]");
        G2Source source = new G2Source("software-only", "1970-01-01T00:00:00Z",
                "known-public-data", semantic);
        NativeObservationPort.TransportSession transport = new NativeObservationPort.TransportSession(
                "software-only", game, BigInteger.ONE, "software-known-session");
        DriverObservationFacts observation = new DriverObservationFacts(mutable, 7, 2, transport,
                "software-known-snapshot", BigInteger.ONE,
                DriverJson.sha256("{}".getBytes(StandardCharsets.UTF_8)), BigInteger.ONE, 1,
                source, new OpportunityJson.Obj(Map.of()), semantic);
        check(actor.calls() == 0, "fixture consumed script before the public Known constructor");
        return new Fixture(actor, mutable, stamp, observation, history);
    }

    private static DriverStateSnapshot.Complete driver(BigInteger actor) {
        DriverStateSnapshot.NullValue nil = new DriverStateSnapshot.NullValue();
        return new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session(
                "software-known-pipe", 17, actor, "software-known-episode"), List.of(),
                nil, nil, nil, nil, nil, nil, nil);
    }

    private static ExactRef reference(String path, String literal) {
        byte[] body = literal.getBytes(StandardCharsets.UTF_8);
        return new ExactRef(path, body.length, DriverJson.sha256(body));
    }

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    private record Fixture(ScriptedActor actor, DriverStateSnapshot.Complete driver,
            DriverSnapshotFacts.Stamp stamp, DriverObservationFacts observation,
            ExactRef historyBasis) { }

    /** Legal BigInteger subclass: inherited numeric value73; only stringification has a script. */
    public static final class ScriptedActor extends BigInteger {
        private static final long serialVersionUID = 1L;
        private final String[] tokens;
        private final int throwAt;
        private final ScriptFailure failure;
        private int calls;

        private ScriptedActor(String[] tokens, int throwAt, ScriptFailure failure) {
            super("73");
            this.tokens = tokens.clone();
            this.throwAt = throwAt;
            this.failure = failure;
        }

        @Override public String toString() {
            int call = ++calls;
            if (call == throwAt) throw failure;
            if (call > tokens.length) throw new AssertionError("unexpected actor stringify call " + call);
            return tokens[call - 1];
        }

        private int calls() { return calls; }
    }

    public static final class ScriptFailure extends AssertionError {
        private static final long serialVersionUID = 1L;
        private ScriptFailure(String message) { super(message); }
    }
}
