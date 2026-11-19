package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.planning.OrdinaryPolicy.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/** Pure owner callback boundary; no RootContext, canonical history, Native client or Game. */
@org.junit.jupiter.api.condition.EnabledIfSystemProperty(named="xar.holywar.cpp.full.ref",matches=".+")
final class HolyWarDefenderCapabilityBoundaryTest {
    private static Obj snapshot()throws Exception {
        var ref=ExactRef.fromJson(StrictJson.parse(Files.readAllBytes(Path.of(System.getProperty("xar.holywar.cpp.full.ref")))));
        byte[] bytes=Files.readAllBytes(Path.of(ref.path()));assertEquals(ref.bytes(),bytes.length);assertEquals(ref.sha256(),ActionCodec.sha256(bytes));
        var full=StrictJson.parse(bytes);var state=((com.fasterxml.jackson.databind.node.ObjectNode)full.get("state")).deepCopy();
        state.set("snapshot_id",full.get("snapshot_id"));state.set("revision",full.get("revision"));state.set("native_revision",full.get("revision"));
        return (Obj)OpportunityJson.parse(StrictJson.canonical(state));
    }
    private static Draft previous() {
        return new Draft("actual-observation-policy","initial_lifestyle_focus_already_present","existing focus retained",Kind.OPENING_FOCUS,
                Optional.empty(),Purpose.READ_ONLY,Optional.of(Domain.lifestyle),new Obj(Map.of("opening_required_gate_intent",new Text("consume_verified_existing_focus_on_following_turn"))));
    }
    @Test void absentExactCapabilityAnnotatesUnavailableAndNeverReadsOrChangesTheChosenDraft()throws Exception {
        for(var caps:Set.of(Set.<String>of(),Set.of("game.command.query-declarable-wars-other"))) {
            var calls=new AtomicInteger();var before=previous();
            var result=RootHolyWarPlanningPolicies.observeDefenderCatalogue(snapshot(),caps,before,()->{calls.incrementAndGet();throw new AssertionError("unadvertised canonical source must never be read");});
            assertEquals(0,calls.get());assertInstanceOf(Annotate.class,result);var after=((Annotate)result).retained();
            assertEquals(before.policy(),after.policy());assertEquals(before.phase(),after.phase());assertEquals(before.reason(),after.reason());
            assertEquals(before.kind(),after.kind());assertEquals(before.command(),after.command());assertEquals(before.purpose(),after.purpose());assertEquals(before.domain(),after.domain());
            assertEquals(before.detail().get("opening_required_gate_intent"),after.detail().get("opening_required_gate_intent"));
            var annotation=(Obj)after.detail().get("ordinary_holy_war_candidate_observation");assertEquals(new Text("native_catalogue_unavailable"),annotation.get("status"));
            assertEquals(new Bool(false),annotation.get("automatic_declaration_enabled"));assertEquals(new Bool(true),annotation.get("read_only"));
            assertNull(annotation.get("candidate_rows"));assertNull(annotation.get("candidate_count"));
        }
    }
    @Test void exactAdvertisedCapabilityPreservesOriginalCallbackAndFailure()throws Exception {
        var calls=new AtomicInteger();var expected=new NotApplicable("actual source callback sentinel");
        var result=RootHolyWarPlanningPolicies.observeDefenderCatalogue(snapshot(),Set.of("game.command.query-declarable-wars"),previous(),()->{calls.incrementAndGet();return expected;});
        assertSame(expected,result);assertEquals(1,calls.get());var original=new IOException("original canonical source failure");
        assertSame(original,assertThrows(IOException.class,()->RootHolyWarPlanningPolicies.observeDefenderCatalogue(snapshot(),Set.of("game.command.query-declarable-wars"),previous(),()->{throw original;})));
    }
}
