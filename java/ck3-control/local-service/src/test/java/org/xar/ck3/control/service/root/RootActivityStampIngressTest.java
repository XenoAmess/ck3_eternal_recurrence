package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m6.ActivityFinalState;
import org.xar.ck3.control.g2.m6.ActivityFinalStateCodec;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Original transport/Packet/archive/FrameLoader regression of independent flags and the active +408 writer. */
final class RootActivityStampIngressTest {
    @TempDir Path temporary;
    private static final BigInteger INITIAL = new BigInteger("9007199254740993");

    @Test void activeStampCanChangeFinalNeedsNoStampChangeAndPurgeRetainsTheOriginalFinal() throws Exception {
        var installed = new AtomicReference<ActivityNativeContracts.Installation>();
        var calls = new AtomicInteger();
        var scenario = new ActionWriterIntegrationFixture.SoftwareReadScenario(
                ActivityFinalIngressData.SOFTWARE_PROFILE_SHA, ActivityFinalIngressData.SOFTWARE_PROFILE_ADAPTER,
                source -> {
                    var contracts = ActivityFinalIngressData.installation(source); installed.set(contracts);
                    return List.of(contracts.contract(ActivityNativeContracts.Query.HOSTED));
                }, request -> {
                    assertEquals(ActivityNativeContracts.Query.HOSTED.step(), request.step());
                    int ordinal = calls.incrementAndGet();
                    assertTrue(ordinal <= 4, "cold replay must not query the native source again");
                    return ordinal == 4 ? missing() : result(ordinal >= 3, false,
                            Optional.of(ordinal == 1 ? INITIAL : INITIAL.add(BigInteger.ONE)));
                });
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("active-stamp"), false, scenario)) {
            PlanningRequest request = fixture.ready().request();
            fixture.writer.locked(same -> {
                var bridge = new RootActivityFinalReadBridge(installed.get(), fixture.archive, fixture.frameLoader());
                var identity = new ActivityFinalState.Identity("canonical-start-software-stamp",
                        ActivityFinalIngressData.FULL_ID, 73, "activity_feast");
                var state = ActivityFinalState.empty(identity, request.before());
                state = bridge.observe(state, read(fixture, installed.get(), same, request), request.before(), same).state();
                assertEquals(ActivityFinalState.Kind.ACTIVE, state.currentKind());
                assertEquals(INITIAL, flags(state).rawCompletionStamp().orElseThrow());
                assertTrue(state.firstFinal().isEmpty());
                state = bridge.observe(state, read(fixture, installed.get(), same, request), request.before(), same).state();
                assertEquals(ActivityFinalState.Kind.ACTIVE, state.currentKind());
                assertEquals(INITIAL.add(BigInteger.ONE), flags(state).rawCompletionStamp().orElseThrow());
                assertFalse(state.observedFinalAt(request.before())); assertTrue(state.firstFinal().isEmpty());
                byte[] active = ActivityFinalStateCodec.encode(state);
                assertArrayEquals(active, ActivityFinalStateCodec.encode(bridge.restore(active, same)));
                assertEquals(2, calls.get());
                state = bridge.observe(state, read(fixture, installed.get(), same, request), request.before(), same).state();
                assertEquals(ActivityFinalState.Kind.FINAL_UNATTRIBUTED, state.currentKind());
                assertTrue(state.observedFinalAt(request.before()));
                assertEquals(INITIAL.add(BigInteger.ONE), flags(state).rawCompletionStamp().orElseThrow());
                assertTrue(flags(state).completed()); assertFalse(flags(state).invalidated());
                assertFalse(state.firstFinal().orElseThrow().terminalCauseObserved());
                assertFalse(state.firstFinal().orElseThrow().benefitObserved());
                byte[] finished = ActivityFinalStateCodec.encode(state);
                assertArrayEquals(finished, ActivityFinalStateCodec.encode(bridge.restore(finished, same)));
                assertEquals(3, calls.get());
                var retained = state.firstFinal().orElseThrow();
                state = bridge.observe(state, read(fixture, installed.get(), same, request), request.before(), same).state();
                assertEquals(ActivityFinalState.Kind.UNKNOWN, state.currentKind());
                assertFalse(state.observedFinalAt(request.before()));
                assertEquals(retained, state.firstFinal().orElseThrow());
                byte[] purged = ActivityFinalStateCodec.encode(state);
                var cold = bridge.restore(purged, same);
                assertArrayEquals(purged, ActivityFinalStateCodec.encode(cold));
                assertEquals(retained, cold.firstFinal().orElseThrow());
                assertEquals(4, calls.get()); assertEquals(0, fixture.nativeActionWrites());
                return null;
            });
        }
    }


    @Test void invalidatedFlagWithoutAStampRemainsAnUnattributedOriginalObservation() throws Exception {
        var installed = new AtomicReference<ActivityNativeContracts.Installation>();
        var calls = new AtomicInteger();
        var scenario = new ActionWriterIntegrationFixture.SoftwareReadScenario(
                ActivityFinalIngressData.SOFTWARE_PROFILE_SHA, ActivityFinalIngressData.SOFTWARE_PROFILE_ADAPTER,
                source -> {
                    var contracts = ActivityFinalIngressData.installation(source); installed.set(contracts);
                    return List.of(contracts.contract(ActivityNativeContracts.Query.HOSTED));
                }, request -> {
                    calls.incrementAndGet();
                    return result(false, true, Optional.empty());
                });
        try (var fixture = new ActionWriterIntegrationFixture(temporary.resolve("invalidated-no-stamp"), false, scenario)) {
            PlanningRequest request = fixture.ready().request();
            fixture.writer.locked(same -> {
                var bridge = new RootActivityFinalReadBridge(installed.get(), fixture.archive, fixture.frameLoader());
                var identity = new ActivityFinalState.Identity("canonical-start-software-invalidated",
                        ActivityFinalIngressData.FULL_ID, 73, "activity_feast");
                var observed = bridge.observe(ActivityFinalState.empty(identity, request.before()),
                        read(fixture, installed.get(), same, request), request.before(), same);
                assertEquals(ActivityFinalState.Kind.FINAL_UNATTRIBUTED, observed.state().currentKind());
                assertFalse(flags(observed.state()).completed()); assertTrue(flags(observed.state()).invalidated());
                assertTrue(flags(observed.state()).rawCompletionStamp().isEmpty());
                var first = observed.state().firstFinal().orElseThrow();
                assertFalse(first.terminalCauseObserved()); assertFalse(first.benefitObserved());
                assertFalse(first.actionAuthorized());
                byte[] encoded = ActivityFinalStateCodec.encode(observed.state());
                assertTrue(StrictJson.parse(encoded).at("/first_final/instance/raw_stamp").isNull());
                assertArrayEquals(encoded, ActivityFinalStateCodec.encode(bridge.restore(encoded, same)));
                assertEquals(1, calls.get()); assertEquals(0, fixture.nativeActionWrites());
                return null;
            });
        }
    }

    private static ActivityFinalState.Flags flags(ActivityFinalState.State state) {
        return assertInstanceOf(ActivityFinalState.Flags.class, state.latest().orElseThrow().instance());
    }
    private static ActivityNativeContracts.Packet read(ActionWriterIntegrationFixture fixture,
            ActivityNativeContracts.Installation installed, Session same, PlanningRequest request) {
        var read = new PlanningReadRequest(request.before(), request.source(), request.sessionId(),
                ActivityNativeContracts.Query.HOSTED.operation(), new OpportunityJson.Obj(Map.of()),
                Instant.now().plusSeconds(20));
        var known = assertInstanceOf(PlanningReadResult.Known.class,
                fixture.reads.read(same, installed.contract(ActivityNativeContracts.Query.HOSTED), read));
        return assertInstanceOf(ActivityNativeContracts.Packet.class, known.value());
    }
    private static RawJson result(boolean completed, boolean invalidated, Optional<BigInteger> stamp) {
        ObjectNode original = (ObjectNode)StrictJson.parse(ActivityFinalIngressData.result().bytes());
        ObjectNode row = (ObjectNode)original.at("/activity_feast_hosted_post/hosted_activities/0");
        row.put("native_completed", completed).put("native_invalidated", invalidated)
                .put("native_completion_stamp_observed", stamp.isPresent());
        if (stamp.isPresent()) row.put("native_completion_stamp_raw", stamp.orElseThrow());
        else row.putNull("native_completion_stamp_raw");
        return new RawJson(StrictJson.canonical(original));
    }
    private static RawJson missing() {
        ObjectNode original = (ObjectNode) StrictJson.parse(ActivityFinalIngressData.result().bytes());
        ((ObjectNode) original.get(ActivityNativeContracts.Query.HOSTED.payloadKey())).putArray("hosted_activities");
        return new RawJson(StrictJson.canonical(original));
    }
}

