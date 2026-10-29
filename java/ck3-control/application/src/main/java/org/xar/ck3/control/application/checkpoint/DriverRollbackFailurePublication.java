package org.xar.ck3.control.application.checkpoint;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.history.DriverHistoryProjection;
import org.xar.ck3.control.application.history.RollbackWarFailures;
import org.xar.ck3.control.application.history.RollbackWarFailures.Failure;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Value;

/** Complete-Driver storage projection for the sole pure rollback advisory producer. Grants no replay or action authority. */
public final class DriverRollbackFailurePublication {
    private DriverRollbackFailurePublication() { }
    public static DriverStateSnapshot.Complete project(DriverStateSnapshot.Complete restored,
            DriverStateSnapshot.Complete abandoned,Obj actualRestoredSnapshot,Optional<Obj> abandonedSnapshot,
            int completedRestoreEpochLimit) {
        Objects.requireNonNull(restored);Objects.requireNonNull(abandoned);Objects.requireNonNull(actualRestoredSnapshot);Objects.requireNonNull(abandonedSnapshot);
        StrictJson.require(restored.session().episodeRunId().equals(abandoned.session().episodeRunId())
                &&restored.session().actorId().equals(abandoned.session().actorId()),"rollback advisory cannot cross actual actor/episode");
        Obj checkpoint=object(restored.lastCheckpoint(),"actual restored checkpoint");
        Obj abandonedCheckpoint=object(abandoned.lastCheckpoint(),"actual abandoned checkpoint");
        StrictJson.require(DriverHistoryProjection.checkpointIdentity(checkpoint).isPresent()
                &&DriverHistoryProjection.checkpointIdentity(checkpoint).equals(DriverHistoryProjection.checkpointIdentity(abandonedCheckpoint)),
                "rollback advisory must retain exact physical SAVE identity");
        requireSnapshot(actualRestoredSnapshot,restored,Optional.of(DriverHistoryProjection.checkpointIdentity(checkpoint).orElseThrow().dateRaw()),true);
        abandonedSnapshot.ifPresent(snapshot->requireSnapshot(snapshot,abandoned,Optional.empty(),false));
        List<Obj> restoredRows=rows(restored),originalRows=rows(abandoned);
        StrictJson.require(!restoredRows.isEmpty()&&DriverHistoryProjection.provenRestore(restoredRows.getLast(),checkpoint),
                "rollback advisory is published only after actual completed restore history");
        Obj actualResult=OpportunityJson.object(restoredRows.getLast().get("result"),"actual restored result");
        var process=DriverHistoryProjection.processReplacement(actualResult.get("lifecycle"))
                .orElseThrow(()->new IllegalArgumentException("actual restore replacement pair absent"));
        StrictJson.require(process.previousPid().longValueExact()==abandoned.session().bridgePid()
                &&process.pid().longValueExact()==restored.session().bridgePid(),"advisory belongs to another actual process replacement");
        Optional<Failure> current=RollbackWarFailures.deriveCurrent(originalRows,checkpoint,actualRestoredSnapshot,
                restored.session().episodeRunId(),abandonedSnapshot,completedRestoreEpochLimit);
        List<Failure> completed=RollbackWarFailures.deriveCompleted(originalRows,checkpoint,actualRestoredSnapshot,
                restored.session().episodeRunId(),completedRestoreEpochLimit);
        List<Failure> failures=RollbackWarFailures.bounded(current.stream().toList(),retained(restored),completed);
        DriverStateSnapshot.Slot singular=failures.isEmpty()?new DriverStateSnapshot.NullValue():
                new DriverStateSnapshot.Value(OpportunityJson.encode(RollbackWarFailures.encode(failures.getFirst())));
        var array=new OpportunityJson.Arr(failures.stream().<Value>map(RollbackWarFailures::encode).toList());
        var plural=new DriverStateSnapshot.Value(OpportunityJson.encode(array));
        return new DriverStateSnapshot.Complete(restored.session(),restored.commandHistory(),restored.lastCheckpoint(),singular,
                restored.managedRestoreTransaction(),restored.successionExpectation(),restored.successionLifecycle(),restored.campaignGoal(),plural);
    }
    private static List<Failure> retained(DriverStateSnapshot.Complete restored) {
        if(restored.rollbackWarFailures() instanceof DriverStateSnapshot.Value plural) {
            List<Value> values=OpportunityJson.array(value(plural.json()),"actual rollback advisory array");
            var failures=new ArrayList<Failure>();for(Value value:values)
                failures.add(RollbackWarFailures.decode(value).orElseThrow(()->new IllegalArgumentException("persisted rollback advisory failed typed validation")));
            return List.copyOf(failures);
        }
        if(restored.rollbackWarFailure() instanceof DriverStateSnapshot.Value singular)
            return List.of(RollbackWarFailures.decode(value(singular.json()))
                    .orElseThrow(()->new IllegalArgumentException("persisted legacy rollback advisory failed typed validation")));
        return List.of();
    }
    private static Obj object(DriverStateSnapshot.Slot slot,String context) {
        StrictJson.require(slot instanceof DriverStateSnapshot.Value,context+" must be present and nonnull");
        return DriverJson.object(((DriverStateSnapshot.Value)slot).json(),DriverJson.MAX_NATIVE_BYTES);
    }
    private static List<Obj> rows(DriverStateSnapshot.Complete driver) {
        return driver.commandHistory().stream().map(row->DriverJson.object(row.originalRow().json(),DriverJson.MAX_NATIVE_BYTES)).toList();
    }
    private static Value value(byte[] original) {
        byte[] prefix="{\"value\":".getBytes(StandardCharsets.UTF_8);byte[] wrapped=new byte[prefix.length+original.length+1];
        System.arraycopy(prefix,0,wrapped,0,prefix.length);System.arraycopy(original,0,wrapped,prefix.length,original.length);wrapped[wrapped.length-1]='}';
        return DriverJson.object(wrapped,DriverJson.MAX_NATIVE_BYTES).get("value");
    }
    private static void requireSnapshot(Obj snapshot,DriverStateSnapshot.Complete driver,Optional<BigInteger> date,boolean restored) {
        Obj player=OpportunityJson.object(snapshot.get("played_character"),"actual played character");
        Obj diagnostics=OpportunityJson.object(snapshot.get("diagnostics"),"actual native diagnostics");
        StrictJson.require(OpportunityJson.text(snapshot.get("episode_run_id"),"episode_run_id").equals(driver.session().episodeRunId())
                &&OpportunityJson.integer(player.get("character_id"),"character_id").equals(driver.session().actorId())
                &&OpportunityJson.integer(diagnostics.get("bridge_pid"),"bridge_pid").equals(BigInteger.valueOf(driver.session().bridgePid())),
                "rollback snapshot crossed actual full Driver process/actor/episode");
        BigInteger observed=OpportunityJson.integer(snapshot.get("date_raw"),"date_raw");
        date.ifPresent(expected->StrictJson.require(expected.equals(observed),"actual restored date differs from exact saved checkpoint"));
        if(restored)StrictJson.require(OpportunityJson.bool(snapshot.get("paused"),"paused")&&OpportunityJson.bool(snapshot.get("map_ready"),"map_ready"),
                "restored rollback advisory requires actual paused ready map");
    }
}
