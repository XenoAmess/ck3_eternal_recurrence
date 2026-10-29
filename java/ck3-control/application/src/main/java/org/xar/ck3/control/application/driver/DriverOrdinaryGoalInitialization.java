package org.xar.ck3.control.application.driver;

import java.util.Arrays;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Pure candidate DATA for the sole Driver owner. Never imports, restores, publishes or submits. */
final class DriverOrdinaryGoalInitialization {
    private DriverOrdinaryGoalInitialization() { }

    static Optional<DriverStateSnapshot.Complete> prepare(DriverSnapshotFacts.Known before,
            DriverObservationFacts observed,NativeObservationPort.ObservedFrame actual) {
        Objects.requireNonNull(before);Objects.requireNonNull(observed);Objects.requireNonNull(actual);
        var old=before.driver();
        if(!(old.campaignGoal() instanceof DriverStateSnapshot.NullValue))return Optional.empty();
        if(!(old.successionLifecycle() instanceof DriverStateSnapshot.Value lifecycle))return Optional.empty();
        var binding=DriverJson.object(lifecycle.json(),DriverJson.MAX_NATIVE_BYTES);
        if(!new OpportunityJson.Text("ordinary_campaign_succession").equals(binding.get("lifecycle")))return Optional.empty();
        StrictJson.require(observed.driverVersion()==before.stamp().driverVersion()
                && observed.episodeEpoch()==before.stamp().episodeEpoch()
                && Arrays.equals(observed.driver().encode(),old.encode())
                && observed.transport().equals(actual.session())
                && observed.transport().game().equals(before.stamp().game())
                && observed.snapshotId().equals(actual.snapshotId()) && observed.nativeRevision().equals(actual.nativeRevision())
                && observed.nativeStateSha256().equals(DriverJson.sha256(actual.state().bytes())),
                "ordinary goal requires the actual accepted full Driver/Native observation");
        var raw=DriverObservationAssembler.originalNativeState(actual);
        StrictJson.require(new OpportunityJson.Bool(true).equals(raw.get("paused"))
                &&new OpportunityJson.Bool(true).equals(raw.get("map_ready")),"ordinary goal requires an actual paused playable map");
        var player=OpportunityJson.object(raw.get("played_character"),"actual ordinary player");
        var actor=OpportunityJson.integer(player.get("character_id"),"actual ordinary player character_id");
        StrictJson.require(new OpportunityJson.Bool(true).equals(player.get("alive"))
                &&actor.equals(old.session().actorId()),"ordinary goal requires the bound living episode actor");
        long actorId=actor.longValueExact();StrictJson.safe(actorId,1);
        var goal=OrdinaryCampaignGoal.newGoal(old.session().episodeRunId(),actorId);
        return Optional.of(new DriverStateSnapshot.Complete(old.session(),old.commandHistory(),old.lastCheckpoint(),
                old.rollbackWarFailure(),old.managedRestoreTransaction(),old.successionExpectation(),old.successionLifecycle(),
                new DriverStateSnapshot.Value(GoalCodec.encodeGoal(goal)),old.rollbackWarFailures()));
    }
}
