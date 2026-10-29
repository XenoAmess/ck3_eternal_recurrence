package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Full serialized Root guard DATA -> M7 historical consumer -> same-writer history port. Software only. */
final class RootM7HistoricalGuardHistoryTest {
    private static final String MACHINE = "m7-history-software";
    private static final Instant AT = Instant.parse("2026-10-24T00:00:00Z");

    @Test void actualV3SerializedBasisUsesItsOriginalHistoryPointAfterLaterSaveHeads() throws Exception {
        Fixture f = new Fixture();
        var guard = f.guard(f.basis);
        assertEquals(java.util.Optional.of(f.source), RootGuardEvidence.sourceQualification(guard, f.archive));
        RootM7HistoricalCheckpointInputs.requireOriginalGuardHistory(f.session, guard, f.archive, 7, 12);
        RootM7HistoricalCheckpointInputs.requireOriginalGuardHistory(f.session, guard, f.archive, 7, 91);
        assertEquals(2, f.historyCalls);
    }

    @Test void absentSourceMetadataSkipsLegacyDecodeButStillRequiresOriginalHistory() throws Exception {
        Fixture f = new Fixture();
        var absent = f.basis.deepCopy(); absent.remove("source_qualification");
        var explicitNull = f.basis.deepCopy(); explicitNull.putNull("source_qualification");
        for (var basis : List.of(absent, explicitNull)) {
            var original = RootM7HistoricalCheckpointInputs.readOriginalSource(f.session, f.guard(basis), f.archive, 7, 12);
            assertTrue(original.metadata().isEmpty()); assertTrue(original.proof().isEmpty()); assertTrue(original.manifest().isEmpty());
            original.verifyPins(f.session);
        }
        assertEquals(2, f.historyCalls);
        var changed = absent.deepCopy(); ((ObjectNode) changed.get("writer_point")).put("digest", "f".repeat(64));
        assertThrows(java.io.UncheckedIOException.class, () ->
                RootM7HistoricalCheckpointInputs.readOriginalSource(f.session, f.guard(changed), f.archive, 7, 12));
        assertEquals(3, f.historyCalls);
    }

    @Test void suppliedMalformedSourceCannotBecomeAbsentMetadata() throws Exception {
        Fixture f = new Fixture(); var changed = f.basis.deepCopy(); changed.put("source_qualification", true);
        assertThrows(IllegalArgumentException.class, () ->
                RootM7HistoricalCheckpointInputs.readOriginalSource(f.session, f.guard(changed), f.archive, 7, 12));
    }

    @Test void readableLegacyBasisCannotQualifyAnOriginalWriterHistory() throws Exception {
        Fixture f = new Fixture(); var legacy = f.basis.deepCopy();
        legacy.put("schema", "xar.java.root-guard-original-basis/v2"); legacy.remove("writer_point");
        var guard = f.guard(legacy);
        assertEquals(java.util.Optional.of(f.source), RootGuardEvidence.sourceQualification(guard, f.archive));
        assertThrows(IllegalArgumentException.class, () -> RootM7HistoricalCheckpointInputs.requireOriginalGuardHistory(f.session, guard, f.archive, 7, 12));
        assertEquals(0, f.historyCalls);
    }

    @Test void changedDigestCannotBeRequalifiedByRetainingIdenticalSourceBytes() throws Exception {
        Fixture f = new Fixture(); var changed = f.basis.deepCopy();
        ((ObjectNode) changed.get("writer_point")).put("digest", "f".repeat(64));
        var guard = f.guard(changed);
        assertThrows(IOException.class, () -> RootM7HistoricalCheckpointInputs.requireOriginalGuardHistory(f.session, guard, f.archive, 7, 12));
        assertEquals(1, f.historyCalls);
    }

    @Test void futureGuardPointAndSaveBeyondItsOriginalHeadRejectBeforeHistoryPort() throws Exception {
        Fixture f = new Fixture(); var guard = f.guard(f.basis);
        assertThrows(IllegalArgumentException.class, () -> RootM7HistoricalCheckpointInputs.requireOriginalGuardHistory(f.session, guard, f.archive, 2, 12));
        assertThrows(IllegalArgumentException.class, () -> RootM7HistoricalCheckpointInputs.requireOriginalGuardHistory(f.session, guard, f.archive, 7, 6));
        assertEquals(0, f.historyCalls);
    }

    @Test void strictWriterPointRejectsWrongJsonTypesMissingAndUnknownFields() throws Exception {
        Fixture f = new Fixture();
        for (ObjectNode point : List.of(StrictJson.object().put("sequence", true).put("digest", f.digest),
                StrictJson.object().put("sequence", 2.0).put("digest", f.digest),
                StrictJson.object().put("sequence", "2").put("digest", f.digest),
                StrictJson.object().put("sequence", 2).put("digest", f.digest).put("fallback", true),
                StrictJson.object().put("sequence", 2))) {
            var changed = f.basis.deepCopy(); changed.set("writer_point", point); var guard = f.guard(changed);
            assertThrows(IllegalArgumentException.class, () -> RootM7HistoricalCheckpointInputs.requireOriginalGuardHistory(f.session, guard, f.archive, 7, 12));
        }
        assertEquals(0, f.historyCalls);
    }

    private static final class Fixture {
        private final Map<ExactRef, RawJson> materials = new HashMap<>();
        private final ContinuityState historical;
        private final String digest;
        private final ObjectNode basis = StrictJson.object();
        private final ExactRef source;
        private final ObservationIdentity identity;
        private final ExactRef nativeFrame;
        private final ExactRef hello;
        private int historyCalls;
        // These narrow test proxies expose only the two read ports used here; no private authority is reflected or minted.
        private final ActionPorts.OutcomeArchive archive = ActionPorts.OutcomeArchive.class.cast(Proxy.newProxyInstance(
                getClass().getClassLoader(), new Class<?>[]{ActionPorts.OutcomeArchive.class}, (proxy, method, arguments) -> {
                    if (method.getName().equals("loadMaterial")) {
                        RawJson raw = materials.get(ExactRef.class.cast(arguments[0]));
                        if (raw == null) throw new IllegalArgumentException("original synthetic material missing");
                        return raw;
                    }
                    throw new AssertionError("historical DATA consumer attempted another archive operation: " + method.getName());
                }));
        private final ContinuityStorePort.Session session = ContinuityStorePort.Session.class.cast(Proxy.newProxyInstance(
                getClass().getClassLoader(), new Class<?>[]{ContinuityStorePort.Session.class}, (proxy, method, arguments) -> {
                    if (!method.getName().equals("requireHistoricalState")) throw new AssertionError("historical reader attempted mutation or unrelated port: " + method.getName());
                    historyCalls++;
                    if (!Long.valueOf(2).equals(arguments[0]) || !originalDigest().equals(arguments[1])) throw new IOException("not the actual original canonical ancestor");
                    return originalState();
                }));
        private String originalDigest() { return digest; }
        private ContinuityState originalState() { return historical; }
        private Fixture() throws Exception {
            var state = StrictJson.object().put("schema", "root.ck3.continuity-window/v1").put("machine_id", MACHINE)
                    .put("sequence", 2).put("window_id", 1).put("start_date_raw", 1000).put("target_date_raw", 1240)
                    .put("target_days", 10).put("status", "running").put("last_settled_cycles", 0).put("last_settled_date_raw", 1000);
            historical = ContinuityState.fromJson(state, MACHINE); digest = ContinuityJson.digest(state);
            identity = new ObservationIdentity(MACHINE, new GameGeneration(321, new PythonOnlyUInt64(new BigInteger("18446744073709551615"))),
                    new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE, BigInteger.valueOf(9), BigInteger.valueOf(53_169_072)), "original-9", BigInteger.valueOf(12), "original-episode"), 1);
            basis.put("schema", RootGuardEvidence.SCHEMA).put("operation", "save-checkpoint").put("authority_id", "software-authority");
            source = preserve(StrictJson.object().put("source", "original source qualification DATA"));
            nativeFrame = preserve(StrictJson.object().put("original", "native frame"));
            hello = preserve(StrictJson.object().put("original", "hello"));
            basis.set("native_frame", nativeFrame.toJson()); basis.set("hello", hello.toJson());
            for (String role : List.of("driver_facts", "semantic", "driver_stamp", "original_driver", "capabilities", "heartbeat"))
                basis.set(role, preserve(StrictJson.object().put("original", role)).toJson());
            basis.set("source_qualification", source.toJson());
            basis.putObject("writer_point").put("sequence", 2).put("digest", digest);
        }
        private GuardEvidence guard(ObjectNode body) throws Exception {
            return new GuardEvidence(identity, new G2Source(MACHINE, AT.toString(), "synthetic/.4", source), "original-session",
                    BigInteger.ONE, new OperationKey("save-checkpoint"), nativeFrame, hello, "software-authority", AT, AT.plusSeconds(60), List.of(preserve(body)));
        }
        private ExactRef preserve(ObjectNode body) throws Exception {
            RawJson raw = new RawJson(ControlBuild.strictMapper().writeValueAsBytes(body));
            ExactRef reference = new ExactRef(Path.of("synthetic-m7-history", ActionCodec.sha256(raw.bytes()) + ".json").toAbsolutePath().toString().replace('\\', '/'), raw.bytes().length, ActionCodec.sha256(raw.bytes()));
            materials.put(reference, raw); return reference;
        }
    }
}
