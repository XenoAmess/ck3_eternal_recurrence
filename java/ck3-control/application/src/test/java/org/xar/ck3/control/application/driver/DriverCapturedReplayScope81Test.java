package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts.Head;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real strict wire/Driver/assembler DATA with unissued public Session and owner probes.
 * No Root, private carrier, Native/physical I/O, ledger permission, or runtime hit is represented. */
final class DriverCapturedReplayScope81Test {
    static final String WIRE="""
        {"format_version":2,"pipe_name":"test-pipe","bridge_pid":42,"episode_character_id":73,"episode_run_id":"episode-real-1",
         "last_checkpoint":null,"command_history":[
          {"index":1,"command":"query-armies","ok":true,"result":{"armies":[],"optional":null,"scale":1.0}},
          {"index":2,"command":"move-army","ok":false,"error":"original native rejection"}],
         "rollback_war_failure":{"reason":"original advisory"},"managed_restore_transaction":{"phase":"completed","lineage":["actual-parent"]},
         "succession_expectation":null,"succession_lifecycle":{"current":{"episode":"episode-real-1"}},
         "campaign_goal":{"campaign_id":"campaign-original","anchor":{"character_id":73}},
         "rollback_war_failures":[{"reason":"original advisory"}]}
        """;
    static final String STATE="""
        {"paused":true,"map_ready":true,"speed":3,"date_raw":53144328,
         "played_character":{"character_id":73,"alive":true},"active_event":null,
         "pending_character_interaction":null,"one_life_terminal_reason":null,
         "active_wars":[],"player_armies":[],"diagnostics":{"original":"retained"}}
        """;

    @Test void exactOriginalRebuildsStayInsideTheirOwnerPointAndScope() throws Exception {
        Fixture f = new Fixture();
        var strict = f.read();
        assertEquals(2, OpportunityJson.array(strict.semantic().get("native_command_history"), "history").size());
        assertEquals(new OpportunityJson.DecimalValue("1.00"), strict.semantic().get("original_metric"));
        assertEquals(new OpportunityJson.Text("campaign-original"), OpportunityJson.object(strict.semantic().get("campaign_goal"), "campaign").get("campaign_id"));
        assertEquals(f.manifestRef, DriverObservationEvidenceReader.reference(strict.semantic().get("java_driver_facts_evidence")));
        assertNotSame(strict, f.read());
        f.events.clear();
        var first = new AtomicReference<DriverObservationAssembler.Complete>();
        f.loader.inCompleteDriverDecodeScope(f.owner, f.session, f.archive, same -> {
            var one = f.read(); first.set(one);
            assertEquals(strict, one); assertSame(one, f.read());
            assertEquals(List.of("manifest", "native", "driver", "getter", "manifest", "native", "driver", "getter"), f.events);
            assertArrayEquals(DriverJson.encode(strict.semantic()), DriverJson.encode(one.semantic()));
            assertEquals(strict.identity(), one.identity()); assertEquals(strict.originalEvidence(), one.originalEvidence());
            assertEquals(strict.fullBindingSha256(), one.fullBindingSha256()); assertEquals(strict.observedAt(), one.observedAt());
            var oldRef = f.nativeRef;
            f.nativeRef = new ExactRef("memory/other-native-role.bin", oldRef.bytes(), oldRef.sha256());
            var changedRole = f.read(); assertNotSame(one, changedRole); assertEquals(f.nativeRef, changedRole.originalEvidence());
            f.nativeRef = oldRef; assertSame(one, f.read());
            var oldManifest = f.manifest; var oldManifestRef = f.manifestRef;
            f.useManifest(RawJson.fullMaterial(DriverJson.encode(DriverJson.object(oldManifest.bytes(), 65536)
                    .with("original_semantic_fields", new OpportunityJson.Obj(Map.of("retained_marker", new OpportunityJson.Text("changed")))))));
            var changedProjection = f.read(); assertNotSame(one, changedProjection);
            assertEquals(new OpportunityJson.Text("changed"), changedProjection.semantic().get("retained_marker"));
            assertFalse(changedProjection.semantic().equals(one.semantic()));
            f.manifest = oldManifest; f.manifestRef = oldManifestRef; assertSame(one, f.read());
            // Exercise bounded retention with valid differently projected originals, not a forged result.
            for (int i = 0; i < 17; i++) {
                f.useManifest(RawJson.fullMaterial(DriverJson.encode(DriverJson.object(oldManifest.bytes(), 65536)
                        .with("original_semantic_fields", new OpportunityJson.Obj(Map.of("retained_marker", new OpportunityJson.Text("entry-" + i)))))));
                assertEquals(new OpportunityJson.Text("entry-" + i), f.read().semantic().get("retained_marker"));
            }
            f.manifest = oldManifest; f.manifestRef = oldManifestRef;
            var afterEviction = f.read(); assertNotSame(one, afterEviction); assertEquals(strict, afterEviction);
            assertSame(afterEviction, f.read());
            f.head.set(head()); // Same public sequence/digest/ref, different actual object: permanently conservative miss.
            var afterPoint = f.read(); assertNotSame(afterEviction, afterPoint); assertNotSame(afterPoint, f.read());
            return null;
        });
        assertNotSame(first.get(), f.read());
        f.loader.inCompleteDriverDecodeScope(f.owner, f.session, f.archive, same -> {
            var fresh = f.read(); assertSame(fresh, f.read());
            f.persisted.set(new ExactRef("memory/new-head.json", 1, "b".repeat(64)));
            var changed = f.read(); assertNotSame(fresh, changed); assertNotSame(changed, f.read()); return null;
        });
        f.loader.inCompleteDriverDecodeScope(f.owner, f.session, f.archive, same -> {
            // Head changes inside the first strict decode callback: it cannot prime at its new point.
            f.ownerAction.set(() -> f.head.set(head()));
            var crossed = f.read(); assertEquals(strict, crossed); assertNotSame(crossed, f.read());
            var again = f.read(); assertNotSame(again, f.read()); return null;
        });
        f.loader.inCompleteDriverDecodeScope(f.owner, f.session, f.archive, same -> {
            var one = f.read(); assertSame(one, f.read());
            var sentinel = new IllegalStateException("DATA owner no longer eligible"); f.ownerFailure.set(sentinel);
            assertSame(sentinel, assertThrows(IllegalStateException.class, f::read)); f.ownerFailure.set(null);
            var after = f.read(); assertEquals(strict, after); assertNotSame(one, after); assertNotSame(after, f.read()); return null;
        });
        f.loader.inCompleteDriverDecodeScope(f.owner, f.session, f.archive, same -> {
            var one = f.read(); assertSame(one, f.read());
            f.headFailure.set(new IOException("DATA optimization freshness unavailable"));
            var after = f.read(); assertEquals(strict, after); f.headFailure.set(null);
            assertNotSame(one, after); assertNotSame(after, f.read()); return null;
        });
        f.loader.inCompleteDriverDecodeScope(f.owner, f.session, f.archive, same -> {
            var one = f.read(); assertSame(one, f.read());
            byte[] original = f.nativeBytes.clone(); f.nativeBytes[0] ^= 1;
            assertEquals("archived native framing/manifest differs", assertThrows(ContractViolationException.class, f::read).getMessage());
            f.nativeBytes = original;
            var after = f.read(); assertEquals(strict, after); assertNotSame(one, after); assertNotSame(after, f.read()); return null;
        });
        f.loader.inCompleteDriverDecodeScope(f.owner, f.session, f.archive, same -> {
            var one = f.read(); assertSame(one, f.read());
            RawJson original = f.driver;
            f.driver = RawJson.fullMaterial(new String(original.bytes(), StandardCharsets.UTF_8).replace("campaign-original", "corrupt-original").getBytes(StandardCharsets.UTF_8));
            assertEquals("archived complete Driver exact bytes/SHA differ", assertThrows(ContractViolationException.class, f::read).getMessage());
            f.driver = original;
            var after = f.read(); assertEquals(strict, after); assertNotSame(one, after); assertNotSame(after, f.read()); return null;
        });
        var originalRef = f.manifestRef; int readsBefore = f.events.size();
        f.manifestRef = new ExactRef(originalRef.path(), originalRef.bytes(), "0".repeat(64));
        assertEquals("semantic facts manifest exact bytes/SHA differ", assertThrows(ContractViolationException.class, f::read).getMessage());
        assertEquals(List.of("manifest", "native"), f.events.subList(readsBefore, f.events.size())); f.manifestRef = originalRef;
        var abort = new IOException("DATA operation aborted");
        var abortedValue = new AtomicReference<DriverObservationAssembler.Complete>();
        assertSame(abort, assertThrows(IOException.class, () -> f.loader.inCompleteDriverDecodeScope(f.owner, f.session, f.archive, same -> {
            var one = f.read(); abortedValue.set(one); assertSame(one, f.read()); throw abort;
        })));
        assertNotSame(abortedValue.get(), f.read());
        f.loader.inCompleteDriverDecodeScope(f.owner, f.session, f.archive, same -> {
            var one = f.read(); assertNotSame(abortedValue.get(), one); assertSame(one, f.read());
            var foreign = f.newSession();
            assertEquals("unissued foreign DATA Session", assertThrows(IllegalStateException.class,
                    () -> f.loader.inCompleteDriverDecodeScope(f.owner, foreign, f.archive, ignored -> { throw new AssertionError("foreign Session operation"); })).getMessage());
            assertSame(one, f.read()); return null;
        });
        assertTrue(f.ownerChecks.get() > 10); assertEquals(0, f.authorityCalls.get());
        System.out.println("CAPTURED_REPLAY_DATA_PASS fullResult/readsAndGetterEachCall/changedProjection/nativeRole/corruption/owner/preAndPostPoint/permanentMiss/boundedEviction/abortCleanup/foreignSession; actualRoot=false actualStorage=false actualRuntimeHit=false");
    }

    private static final class Fixture {
        final Object owner = new Object();
        final AtomicReference<Head> head = new AtomicReference<>(head());
        final AtomicReference<ExactRef> persisted = new AtomicReference<>(new ExactRef("memory/head.json", 1, "a".repeat(64)));
        final AtomicReference<RuntimeException> ownerFailure = new AtomicReference<>();
        final AtomicReference<IOException> headFailure = new AtomicReference<>();
        final AtomicReference<Runnable> ownerAction = new AtomicReference<>();
        final AtomicInteger ownerChecks = new AtomicInteger(), authorityCalls = new AtomicInteger();
        final List<String> events = new ArrayList<>();
        final DriverFrameEvidenceLoader loader = new DriverFrameEvidenceLoader(new DriverObservationAssembler(), true);
        final ContinuityStorePort.Session session = newSession();
        RawJson driver, manifest;
        ExactRef driverRef, manifestRef, nativeRef;
        byte[] nativeBytes;
        final OutcomeArchive archive;
        Fixture() {
            var known = DriverFactsRepository.imported(ref("driver-input", bytes(WIRE)), bytes(WIRE), 3, 7, game(), new OpportunityJson.Obj(Map.of()));
            driver = RawJson.fullMaterial(known.driver().encode()); driverRef = ref("driver", driver.bytes());
            String state = STATE.strip().replace("\"speed\":3", "\"speed\":3,\"original_metric\":1.00");
            byte[] packet = bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"snapshot-9\",\"revision\":9,\"state\":" + state + "}");
            nativeBytes = ByteBuffer.allocate(packet.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(packet.length).put(packet).array();
            var actual = new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession("test-machine", game(), BigInteger.valueOf(5), "held-session"),
                    "snapshot-9", BigInteger.valueOf(9), new RawJson(bytes(state)), nativeBytes, Instant.parse("2026-10-23T16:00:00Z"));
            nativeRef = ref("native", nativeBytes);
            useManifest(DriverObservationEvidenceReader.encode(known, actual, BigInteger.valueOf(2), 1,
                    new G2Source("test-machine", "2026-10-23T16:00:00Z", "test-source", ref("source", bytes("source"))),
                    new OpportunityJson.Obj(Map.of()), driverRef));
            loader.bindDriverDecodeOwner(owner, same -> {
                if (same != session) throw new IllegalStateException("unissued foreign DATA Session");
                ownerChecks.incrementAndGet();
                Runnable action = ownerAction.getAndSet(null); if (action != null) action.run();
                RuntimeException failure = ownerFailure.get(); if (failure != null) throw failure;
            });
            archive = (OutcomeArchive) Proxy.newProxyInstance(OutcomeArchive.class.getClassLoader(), new Class<?>[]{OutcomeArchive.class}, (proxy, method, arguments) -> {
                if (method.getName().equals("loadMaterial")) {
                    if (arguments[0].equals(manifestRef)) { events.add("manifest"); return manifest; }
                    assertEquals(driverRef, arguments[0]); events.add("driver"); return driver;
                }
                if (method.getName().equals("loadNativeFrame")) { assertEquals(nativeRef, arguments[0]); events.add("native"); return nativeBytes.clone(); }
                if (method.getName().equals("scopedDriverDecoder")) { events.add("getter"); return loader; }
                authorityCalls.incrementAndGet(); throw new AssertionError("unissued DATA archive cannot call " + method.getName());
            });
        }
        ContinuityStorePort.Session newSession() {
            return (ContinuityStorePort.Session) Proxy.newProxyInstance(ContinuityStorePort.Session.class.getClassLoader(), new Class<?>[]{ContinuityStorePort.Session.class}, (proxy, method, arguments) -> {
                if (method.getName().equals("head")) { IOException failure = headFailure.get(); if (failure != null) throw failure; return head.get(); }
                if (method.getName().equals("persistedHead")) return persisted.get();
                authorityCalls.incrementAndGet(); throw new AssertionError("unissued DATA Session cannot call " + method.getName());
            });
        }
        void useManifest(RawJson value) { manifest = value; manifestRef = ref("manifest", value.bytes()); }
        DriverObservationAssembler.Complete read() {
            RawJson body = archive.loadMaterial(manifestRef);
            byte[] packet = archive.loadNativeFrame(nativeRef);
            return assertInstanceOf(DriverObservationAssembler.Complete.class, DriverObservationEvidenceReader.replayCapturedOriginals(
                    manifestRef, body, packet, nativeRef, archive::loadMaterial, archive::scopedDriverDecoder));
        }
    }
    private static Head head() {
        byte[] raw = bytes("{\"schema\":\"root.ck3.continuity-window/v1\",\"machine_id\":\"test-machine\",\"sequence\":8,\"window_id\":1,\"start_date_raw\":100,\"target_date_raw\":124,\"target_days\":1,\"status\":\"running\",\"last_settled_cycles\":0,\"last_settled_date_raw\":100}");
        return new Head(new ContinuityState("test-machine", 8, new ContinuityState.Origin(1, 100, 124, 1), ContinuityState.Status.RUNNING, 0, 100, raw), List.of(), List.of(), List.of(), false);
    }
    private static GameGeneration game() { return new GameGeneration(42, new PythonOnlyUInt64(new BigInteger("9007199254740993"))); }
    private static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    private static ExactRef ref(String role, byte[] value) { return new ExactRef("memory/" + role + ".json", value.length, DriverJson.sha256(value)); }
}
