package org.xar.ck3.control.g2.m5;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy;
import org.xar.ck3.control.military.projectedcontact.SourceBoundContactIndex;
import org.xar.ck3.control.wave3.military.routereroute.RouteReevaluationCodec;
import org.xar.ck3.control.wave3.military.routereroute.RouteReevaluationPlanner;
import org.xar.ck3.control.wave3.planning.military.MilitaryRouteAudit;
import org.xar.ck3.control.wave3.planning.military.OrdinaryMilitaryConsumer;

class MilitaryFrameDecisionConsumerTest {
    @Test void actualOriginalM5ProducerStillUsesExistingSharedOwnerWhenMilitaryNativeInputsAreUnknown() throws IOException {
        G2Request request = G2Wire.decodeRequest(resource("M5.request.json"));
        G2Response response = G2Wire.decodeResponse(resource("M5.actual-response.json"));
        Obj selector = selector(request);
        var owner = new M5FrameDispatcher(request.source(), object(selector.get("snapshot"), "actual original snapshot"), object(selector.get("commitments"), "actual original commitments"));
        var result = MilitaryFrameDecisionConsumer.consumeCurrent(() -> {
            assertTrue(Thread.holdsLock(owner), "actual input supplier must run under the original shared owner lock");
            return military(new SourceBoundContactIndex.Unknown("actual fixture contains no qualified native military capture"));
        }, request, response, owner);
        assertInstanceOf(OrdinaryMilitaryConsumer.Unavailable.class, result.military());
        assertEquals(result.sharedDispatch().frame(), owner.resourceSnapshot().frame());
        assertEquals(result.sharedDispatch().reservation(), owner.resourceSnapshot().reservation());
        assertFalse(result.formalActionReady()); assertFalse(result.authorizesCommandReplay());
        var repeated = MilitaryFrameDecisionConsumer.consumeCurrent(() -> military(new SourceBoundContactIndex.Unknown("still unavailable")), request, response, owner);
        if (result.sharedDispatch().reservation().isPresent()) {
            assertEquals(M5FrameDispatcher.Status.already_reserved_this_frame, repeated.sharedDispatch().status());
            assertEquals(result.sharedDispatch().reservation(), repeated.sharedDispatch().reservation());
        } else assertEquals(M5FrameDispatcher.Status.wait, repeated.sharedDispatch().status());
    }
    @Test void actualMinimalM5SnapshotCannotSupplyMissingNativeGenerationForSyntheticExternalContext() throws IOException {
        G2Request request = G2Wire.decodeRequest(resource("M5.request.json"));
        G2Response response = G2Wire.decodeResponse(resource("M5.actual-response.json")); Obj selector = selector(request);
        Obj snapshot = object(selector.get("snapshot"), "actual original snapshot");
        assertNull(snapshot.get("diagnostics"), "actual original fixture is missing native connection generation");
        String sha = "b".repeat(64);
        var synthetic = new SourceBoundContactIndex.Current(new SourceBoundContactIndex.SourceIdentity(request.source().machineId(), request.source().exactBuild(), sha, sha, sha),
                new ProjectedContactPolicy.Snapshot(new ProjectedContactPolicy.Capture(text(snapshot.get("snapshot_id"), "snapshot"), integer(snapshot.get("revision"), "public revision"), integer(snapshot.get("native_revision"), "native revision"), BigInteger.ONE, text(snapshot.get("episode_run_id"), "episode")), integer(snapshot.get("date_raw"), "date").intValueExact()),
                new SourceBoundContactIndex.HistoryIdentity("explicit-synthetic-negative-fixture", BigInteger.ZERO, BigInteger.ZERO), SourceBoundContactIndex.Invalidation.NONE);
        var owner = new M5FrameDispatcher(request.source(), snapshot, object(selector.get("commitments"), "original commitments"));
        var result = MilitaryFrameDecisionConsumer.consumeCurrent(() -> military(synthetic), request, response, owner);
        var unavailable = assertInstanceOf(OrdinaryMilitaryConsumer.Unavailable.class, result.military());
        assertEquals(OrdinaryMilitaryConsumer.Gap.CURRENT_SOURCE_UNAVAILABLE, unavailable.gap());
        assertEquals(result.sharedDispatch().reservation(), owner.resourceSnapshot().reservation());
    }
    private static Obj selector(G2Request request) {
        var operation = assertInstanceOf(M5PayloadCodec.ContextRequest.class, M5PayloadCodec.decodeOperation(request.payload().bytes()));
        return object(M5Research.assess(operation.context()).intakeAnalysis().get("selector_request"), "actual original selector request");
    }
    private static OrdinaryMilitaryConsumer.Input military(SourceBoundContactIndex.Context origin) {
        byte[] emptyLookup = "{\"commands\":[],\"snapshot\":null,\"army_id\":4,\"origin_province_id\":1,\"target_province_id\":3,\"date_raw\":null}".getBytes(StandardCharsets.UTF_8);
        var route = new RouteReevaluationCodec.Request(emptyLookup, new RouteReevaluationPlanner.Context(false, false, false, false), List.of(), List.of());
        return new OrdinaryMilitaryConsumer.Input(route, origin, List.of(), Optional.empty(), new MilitaryRouteAudit.HostileScope(List.of(), List.of(), false, false), List.of(), List.of());
    }
    private static byte[] resource(String name) throws IOException {
        try (InputStream stream = MilitaryFrameDecisionConsumerTest.class.getResourceAsStream("/militarycontact/" + name)) {
            if (stream == null) throw new IOException("actual old M5 producer fixture required: " + name);
            return stream.readAllBytes();
        }
    }
}
