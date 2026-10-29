package org.xar.ck3.control.application.planning;

import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.PlanningFixtures.*;

/** Counterfactual software vectors against the selected native signed actor contract, not native packets. */
final class PlanningObservationSignedActorTest {
    private static PlanningObservation observation(OpportunityJson.Obj actual) {
        return new PlanningObservation(actual,List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),
                Optional.empty(),Optional.empty(),false);
    }
    private static OpportunityJson.Obj withActor(OpportunityJson.Value id) {
        var actual=snapshot();
        return actual.with("played_character",OpportunityJson.object(actual.get("played_character"),"actor").with("character_id",id));
    }
    private static PlanningRequest signedRequest(int actor) {
        var base=request(snapshot(),List.of(),Set.of());
        var old=base.before();var frame=old.frame();
        var actual=new ObservationIdentity(old.machineId(),old.game(),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(actor),
                        frame.identity().nativeRevision(),frame.identity().dateRaw()),
                        frame.snapshotId(),frame.revision(),frame.episodeRunId()),1);
        return new PlanningRequest(actual,base.source(),base.sessionId(),base.deadline(),
                observation(withActor(integer(actor))));
    }
    @Test void actualRequestAndWireKeepSignedIntegerIdentityWithoutUnsignedAlias() {
        for(int actor:new int[]{Integer.MIN_VALUE,-2,0,73,Integer.MAX_VALUE}) {
            var actual=signedRequest(actor);
            var decoded=PlanningWire.decodeRequest(PlanningWire.encodeRequest(actual));
            assertEquals(actual,decoded);
            assertEquals(BigInteger.valueOf(actor),decoded.before().frame().identity().player());
            var played=OpportunityJson.object(decoded.observations().snapshot().get("played_character"),"actor");
            assertEquals(integer(actor),played.get("character_id"));
            assertTrue(DriverJson.toNode(played.get("character_id")).isIntegralNumber());
        }
    }
    @Test void wrongJsonTypesSentinelOverflowAndMissingActorRemainRejected() {
        List<OpportunityJson.Value> invalid=List.of(integer(-1),
                new OpportunityJson.IntegerValue(BigInteger.valueOf(Integer.MIN_VALUE).subtract(BigInteger.ONE)),
                new OpportunityJson.IntegerValue(BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE)),
                new OpportunityJson.Bool(true),new OpportunityJson.DecimalValue("-2.0"),
                new OpportunityJson.Text("-2"),OpportunityJson.Nil.INSTANCE);
        for(var value:invalid) assertThrows(IllegalArgumentException.class,()->observation(withActor(value)));
        var fields=new LinkedHashMap<>(OpportunityJson.object(snapshot().get("played_character"),"actor").members());
        fields.remove("character_id");
        assertThrows(IllegalArgumentException.class,()->observation(snapshot().with("played_character",new OpportunityJson.Obj(fields))));
    }
    @Test void signedSnapshotCannotBorrowAnotherFrameAndOtherIdentityDomainsStayStrict() {
        var base=request(snapshot(),List.of(),Set.of());
        assertThrows(IllegalArgumentException.class,()->new PlanningRequest(base.before(),base.source(),base.sessionId(),
                base.deadline(),observation(withActor(integer(-2)))));
        for(String field:List.of("revision","native_revision"))
            assertThrows(IllegalArgumentException.class,()->observation(withActor(integer(-2)).with(field,integer(0))));
        assertThrows(IllegalArgumentException.class,()->observation(withActor(integer(-2)).with("date_raw",integer(-1))));
        assertThrows(IllegalArgumentException.class,()->observation(withActor(integer(-2)).with("paused",integer(1))));
    }
}
