package org.xar.ck3.control.vanilla.schemesway;

import java.math.BigInteger;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.vanilla.schemesway.OrdinarySwaySchedule.*;
import org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public final class OrdinarySwayBuildSourceDataTest {
    private static final String SUPPORTED_SHA = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    private static final String SUPPORTED_LABEL = "1.20.0.4";
    private static final String SUPPORTED_SHA_UPPER = SUPPORTED_SHA.toUpperCase(Locale.ROOT);
    private static final String SUPPORTED_SHA_LOWER = SUPPORTED_SHA.toLowerCase(Locale.ROOT);

    private static G2Source makeSource(String build) {
        return new G2Source("test-machine", "2026-11-05T00:00:00Z", build, new ExactRef("/test/ref", 100L, "a".repeat(64)));
    }

    private static Frame makeFrame() {
        return new Frame("snap1", BigInteger.valueOf(4), BigInteger.valueOf(9), BigInteger.valueOf(53144520), 73L, true, true, true, Context.CLEAR);
    }

    private static Root makeRoot() {
        return new Root(true, 73L, true, BigInteger.valueOf(9), BigInteger.valueOf(53144520), Optional.of(List.of(74L)));
    }

    private static Request makeRequest(G2Source source) {
        return new Request(source, Optional.of(makeFrame()), Step.LIFE_ADVANCE, Optional.of(makeRoot()), Ledger.empty(), Optional.empty(), false);
    }

    private static Captured makeCaptured(G2Source source) {
        Wrapper wrapper = new Wrapper("snap1", BigInteger.valueOf(4));
        Capabilities caps = new Capabilities(true, true, true);
        return new Captured(source, wrapper, Step.LIFE_ADVANCE, Optional.of(makeFrame()), Optional.of(makeRoot()), caps);
    }

    @Test
    public void supportedBuildLabelsAndRuntimeFingerprintKeepOriginalSourceAndStage() {
        assertEquals(SUPPORTED_LABEL, ExactCk3Build.CK3_12004.version());
        assertEquals(SUPPORTED_SHA, ExactCk3Build.CK3_12004.executableSha256());
        assertTrue(ExactCk3Build.CK3_12004.matches(SUPPORTED_LABEL, SUPPORTED_SHA_UPPER));
        G2Source[] sources = {makeSource(SUPPORTED_LABEL), makeSource(SUPPORTED_SHA_UPPER), makeSource(SUPPORTED_SHA_LOWER)};
        Request[] requests = new Request[sources.length];
        OrdinarySwayService service = new OrdinarySwayService();
        for (int index = 0; index < sources.length; index++) {
            G2Source source = sources[index];
            ExactRef ref = source.sourceRef();
            String build = source.exactBuild(), machine = source.machineId(), time = source.observedAtUtc();
            Request request = makeRequest(source); requests[index] = request;
            assertSame(source, request.source()); assertSame(ref, request.source().sourceRef());
            assertEquals(build, request.source().exactBuild());
            assertEquals(machine, request.source().machineId()); assertEquals(time, request.source().observedAtUtc());
            Frame frame = request.frame().orElseThrow();
            Captured captured = new Captured(source, new Wrapper(frame.snapshotId(), frame.publicRevision()),
                    Step.LIFE_ADVANCE, request.frame(), request.root(), new Capabilities(true, true, true));
            assertSame(source, captured.source());
            int[] calls = {0};
            StageResult result = service.stage(captured, () -> {
                calls[0]++;
                return Optional.of(new Inputs(request.ledger(), request.state()));
            });
            assertEquals(1, calls[0]); assertEquals(StageReason.STAGED, result.reason());
            assertTrue(result.error().isEmpty());
            Staged staged = result.staged().orElseThrow(); assertSame(frame, staged.frame());
            Decision decision = result.decision().orElseThrow(); assertSame(decision, staged.decision());
            assertEquals(Optional.of(Job.QUERY_SELECTED_TARGET), decision.job());
            assertEquals(Optional.of(74L), decision.targetCharacterId());
            assertEquals(73L, decision.state().orElseThrow().actorCharacterId());
            assertFalse(decision.submitAllowed()); assertFalse(decision.nativeAiRankClaimed());
            assertFalse(decision.terminalOrUsefulGainClaimed());
            assertSame(source, request.source()); assertSame(ref, source.sourceRef());
            assertEquals(build, source.exactBuild()); assertEquals(machine, source.machineId()); assertEquals(time, source.observedAtUtc());
        }
        assertNotEquals(requests[0], requests[1]); assertNotEquals(requests[0], requests[2]); assertNotEquals(requests[1], requests[2]);
    }

    @Test
    public void unknownAndUnsupportedBuildsKeepTheOriginalGuardAndNoStagedJob() {
        String[] badBuilds = {
            "1.19.0.6",
            "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
            "a".repeat(64),
            SUPPORTED_SHA.substring(0, 63) + "0",
            SUPPORTED_SHA.substring(1),
            SUPPORTED_SHA + "0",
            "0" + SUPPORTED_SHA,
            SUPPORTED_SHA + " ",
            " " + SUPPORTED_SHA,
            "1.20.0.40",
            " 1.20.0.4",
            "1.20.0.4 ",
            "CK3_12004"
        };

        for (String bad : badBuilds) {
            G2Source source = makeSource(bad);
            ExactRef ref = source.sourceRef();
            IllegalArgumentException ex = null;
            try {
                makeRequest(source);
            } catch (IllegalArgumentException e) {
                ex = e;
            }
            assertNotNull(ex, "Expected exception for build: " + bad);
            assertEquals("scheduler source must identify exact supported build", ex.getMessage());
            assertEquals(bad, source.exactBuild());
            assertEquals("test-machine", source.machineId());
            assertEquals("2026-11-05T00:00:00Z", source.observedAtUtc());
            assertEquals("/test/ref", source.sourceRef().path());
            assertSame(ref, source.sourceRef());
        }

        OrdinarySwayService service = new OrdinarySwayService();
        int[] callCount = {0};
        InputPort port = new InputPort() {
            public Optional<Inputs> loadInputs() throws Unavailable {
                callCount[0]++;
                return Optional.of(new Inputs(Ledger.empty(), Optional.empty()));
            }
        };

        for (String bad : badBuilds) {
            G2Source source = makeSource(bad);
            ExactRef ref = source.sourceRef();
            Captured captured = makeCaptured(source); assertSame(source, captured.source());
            callCount[0] = 0;
            StageResult res = service.stage(captured, port);
            assertEquals(StageReason.INPUTS_UNAVAILABLE, res.reason());
            assertEquals(1, callCount[0]);
            assertFalse(res.staged().isPresent());
            assertFalse(res.decision().isPresent());
            assertTrue(res.error().isPresent());
            assertEquals("scheduler source must identify exact supported build", res.error().orElseThrow());
            assertSame(source, captured.source()); assertSame(ref, source.sourceRef());
            assertEquals(bad, source.exactBuild()); assertEquals("test-machine", source.machineId());
            assertEquals("2026-11-05T00:00:00Z", source.observedAtUtc());
        }
    }
}