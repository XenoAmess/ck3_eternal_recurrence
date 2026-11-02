package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.capabilities.DriverRuntimeCapabilities;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.UInt64;
import org.xar.ck3.control.nativebridge.capabilities.army.DeclarationOpportunityCooldown;
import org.xar.ck3.control.nativebridge.capabilities.army.DeclarationOpportunityCooldown.*;

/** Public DATA fixtures only. No canonical writer, physical file or Game authority is constructed. */
final class DriverPersistentView355Test {
    @Test
    void publicReplayRetainsEachOriginalReadAndProofFailure() {
        var f = DriverCapabilityStateProducerTest.fresh();
        var frame = f.frame();
        Frame identity = DeclarationOpportunityCooldown.frame(frame);
        Snapshot snapshot = DeclarationOpportunityCooldown.snapshot(toNode(frame.semantic()));
        Reduction initial = DeclarationOpportunityCooldown.view(DeclarationOpportunityCooldown.initial(identity), snapshot, identity);
        Obj frameRefs = new Obj(Map.of("manifest", frame.semantic().get("java_driver_facts_evidence"),
                "native", ref(frame.originalEvidence())));
        // Synthetic archived DATA for the real public replay boundary, never a claimed physical capture.
        Obj input = new Obj(Map.of("configured_path", new Text("D:/pure-data355/" + DeclarationOpportunityCooldown.LEGACY_FILENAME),
                "observed_at", new Text("2026-11-02T00:00:00Z"), "original", Nil.INSTANCE,
                "saved", Nil.INSTANCE, "baseline_receipts", new Arr(List.of())));
        Obj first = proof("INITIAL", Nil.INSTANCE, frameRefs, input, initial);
        ExactRef firstRef = f.archive().preserveMaterial(new RawJson(DriverJson.encode(first)));
        Reduction view = DeclarationOpportunityCooldown.view(initial.state(), snapshot, identity);
        Obj next = proof("VIEW", ref(firstRef), frameRefs, Nil.INSTANCE, view);
        ExactRef nextRef = f.archive().preserveMaterial(new RawJson(DriverJson.encode(next)));
        Obj auxiliary = auxiliary(nextRef, view);

        ExactRef manifest = DriverObservationEvidenceReader.reference(frameRefs.get("manifest"));
        ExactRef driver = DriverObservationEvidenceReader.currentDriverReference(manifest, f.archive().loadMaterial(manifest));
        var calls = new ArrayList<String>();
        ActionPorts.OutcomeArchive observed = (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(
                getClass().getClassLoader(), new Class<?>[] {ActionPorts.OutcomeArchive.class}, (proxy, method, args) -> {
                    if (method.getName().equals("loadMaterial")) calls.add("M:" + ((ExactRef) args[0]).sha256());
                    if (method.getName().equals("loadNativeFrame")) calls.add("N:" + ((ExactRef) args[0]).sha256());
                    try { return method.invoke(f.archive(), args); }
                    catch (InvocationTargetException error) { throw error.getCause(); }
                });
        assertDoesNotThrow(() -> DriverPersistentPlanningState.replay(auxiliary, observed));
        List<String> originals = List.of("M:" + nextRef.sha256(), "M:" + firstRef.sha256(),
                "M:" + manifest.sha256(), "N:" + frame.originalEvidence().sha256(), "M:" + driver.sha256(),
                "M:" + manifest.sha256(), "N:" + frame.originalEvidence().sha256(), "M:" + driver.sha256());
        assertEquals(originals, calls, "each historical proof still rebuilds from its original reads in order");

        ExactRef badInput = f.archive().preserveMaterial(new RawJson(DriverJson.encode(next.with("input", new Bool(true)))));
        var unexpected = assertThrows(IllegalArgumentException.class,
                () -> DriverPersistentPlanningState.replay(auxiliary(badInput, view), f.archive()));
        assertEquals("view source has unexpected input", unexpected.getMessage());
        ExactRef wrongState = f.archive().preserveMaterial(new RawJson(DriverJson.encode(next.with("state", new Bool(true)))));
        var mismatch = assertThrows(IllegalArgumentException.class,
                () -> DriverPersistentPlanningState.replay(auxiliary(wrongState, view), f.archive()));
        assertEquals("cooldown pure source replay differs", mismatch.getMessage());

        byte[] originalNative = f.archive().nativeFrames.get(frame.originalEvidence());
        byte[] changed = originalNative.clone();
        changed[changed.length - 1] ^= 1;
        f.archive().nativeFrames.put(frame.originalEvidence(), changed);
        try {
            var drift = assertThrows(IllegalArgumentException.class,
                    () -> DriverPersistentPlanningState.replay(auxiliary, f.archive()));
            assertEquals("archived native framing/manifest differs", drift.getMessage());
        } finally { f.archive().nativeFrames.put(frame.originalEvidence(), originalNative); }
    }

    @Test
    void repeatedViewIsStableAcrossOwnershipPendingWarAndDeadlineBranches() {
        var q = new UInt64(BigInteger.valueOf(7));
        var pending = new Pending(q, Optional.of("query"), BigInteger.ONE, BigInteger.valueOf(90), BigInteger.valueOf(100));
        var foreign = new Pending(q, Optional.empty(), BigInteger.ONE, BigInteger.valueOf(90), BigInteger.valueOf(101));
        WarId war = new TextWarId("W");
        var states = List.of(
                state(1, "E", 0, Optional.empty(), Optional.empty(), Optional.empty()),
                state(2, "OTHER", 2, Optional.of(BigInteger.valueOf(110)), Optional.of(pending), Optional.of(war)),
                state(1, "E", 0, Optional.of(BigInteger.valueOf(110)), Optional.of(pending), Optional.empty()),
                state(1, "E", 2, Optional.of(BigInteger.valueOf(100)), Optional.empty(), Optional.of(war)),
                state(1, "E", 1, Optional.empty(), Optional.of(pending), Optional.of(war)),
                state(1, "E", 1, Optional.empty(), Optional.of(foreign), Optional.empty()),
                state(1, "E", 1, Optional.empty(), Optional.of(pending), Optional.of(new NumericWarId(BigInteger.ZERO))));
        var wars = Optional.of(List.of(new War(war, true)));
        var verified = new Continuity(true, Optional.of("war_started"), true, true, Optional.of(war));
        var zero = new NumericWarId(BigInteger.ZERO);
        var snapshots = List.of(Snapshot.empty(), new Snapshot(true, Optional.of(List.of()), false, false, Optional.empty()),
                new Snapshot(true, wars, false, false, Optional.empty()),
                new Snapshot(true, wars, false, false, Optional.of(verified)),
                new Snapshot(false, Optional.empty(), true, true, Optional.of(verified)),
                new Snapshot(true, wars, false, false, Optional.of(new Continuity(false, Optional.of("war_started"), true, true, Optional.of(war)))),
                new Snapshot(true, Optional.of(List.of(new War(war, false))), false, false, Optional.of(verified)),
                new Snapshot(true, Optional.of(List.of(new War(zero, true))), false, false,
                        Optional.of(new Continuity(true, Optional.of("war_started"), true, true, Optional.of(zero)))));
        for (long date : List.of(90L, 100L, 110L)) for (long bridge : List.of(100L, 101L)) {
            Frame current = new Frame(BigInteger.ONE, "E", BigInteger.valueOf(date), BigInteger.TEN,
                    BigInteger.valueOf(bridge), Optional.of("current"));
            for (State state : states) for (Snapshot snapshot : snapshots) {
                Reduction once = DeclarationOpportunityCooldown.view(state, snapshot, current);
                Reduction twice = DeclarationOpportunityCooldown.view(once.state(), snapshot, current);
                assertEquals(twice, once);
                assertArrayEquals(StrictJson.canonical(DeclarationOpportunityCooldown.encode(twice.state())),
                        StrictJson.canonical(DeclarationOpportunityCooldown.encode(once.state())));
                assertArrayEquals(StrictJson.canonical(DeclarationOpportunityCooldown.encodeView(twice.view())),
                        StrictJson.canonical(DeclarationOpportunityCooldown.encodeView(once.view())));
            }
        }
    }

    private static State state(long actor, String episode, int rounds, Optional<BigInteger> deadline,
            Optional<Pending> pending, Optional<WarId> war) {
        return new State(BigInteger.valueOf(actor), episode, rounds, deadline, pending,
                Optional.of(new UInt64(BigInteger.valueOf(5))), war);
    }

    private static Obj proof(String mode, Value previous, Obj frame, Value input, Reduction value) {
        return new Obj(Map.of("schema", new Text("xar.driver-persistent-planning-source/v2"), "mode", new Text(mode),
                "previous", previous, "frame", frame, "input", input, "state", node(DeclarationOpportunityCooldown.encode(value.state())),
                "view", node(DeclarationOpportunityCooldown.encodeView(value.view())), "processed", new Arr(List.of())));
    }

    private static Obj auxiliary(ExactRef source, Reduction value) {
        return new Obj(Map.of(DriverPersistentPlanningState.COOLDOWN_SOURCE, ref(source),
                DriverPersistentPlanningState.COOLDOWN_STATE, node(DeclarationOpportunityCooldown.encode(value.state())),
                DeclarationOpportunityCooldown.VIEW_KEY, node(DeclarationOpportunityCooldown.encodeView(value.view()))));
    }

    private static Obj node(com.fasterxml.jackson.databind.JsonNode value) {
        return object(parse(StrictJson.canonical(value)), "typed cooldown DATA");
    }

    private static Obj ref(ExactRef value) { return DriverRuntimeCapabilities.referenceJson(value); }
}
