package org.xar.ck3.control.application.planning.military;

import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.military.commander.CommanderQuality;

/** A separate observation-only contract. Its factual input grants no ordinary readiness or submission authority. */
public final class CommanderReconciliationCollector {
    private CommanderReconciliationCollector() { }
    public record Input(ReconciliationIdentity identity,OpportunityJson.Obj snapshot) {
        public Input {
            Objects.requireNonNull(identity);Objects.requireNonNull(snapshot);
            var frame=identity.factual().frame();
            StrictJson.require(OpportunityJson.bool(snapshot.get("paused"),"paused")
                    &&OpportunityJson.text(snapshot.get("snapshot_id"),"snapshot_id").equals(frame.snapshotId())
                    &&OpportunityJson.integer(snapshot.get("revision"),"revision").equals(frame.revision())
                    &&OpportunityJson.integer(snapshot.get("native_revision"),"native_revision").equals(frame.identity().nativeRevision())
                    &&OpportunityJson.integer(snapshot.get("date_raw"),"date_raw").equals(frame.identity().dateRaw()),
                    "commander reconciliation facts differ from their actual full frame");
        }
    }
    public record Selection(Input input,int army) {
        public Selection {Objects.requireNonNull(input);StrictJson.require(army>=0,"public Army ID must be nonnegative");requireSubject(input,army);}
    }
    public record Issued(ReadContract<CommanderObservationCollector.Observation> contract,PlanningReadRequest request) {
        public Issued {Objects.requireNonNull(contract);Objects.requireNonNull(request);StrictJson.require(contract.guardMode()==ReadContract.GuardMode.RECONCILIATION_OBSERVATION&&contract.operation().equals(request.operation()),"actual reconciliation contract/request required");}
    }
    public static OperationKey operation(int army){StrictJson.require(army>=0,"public Army ID must be nonnegative");return CommanderObservationCollector.operation(army,Optional.empty());}
    public static OpportunityJson.Obj arguments(int army){operation(army);return new OpportunityJson.Obj(java.util.Map.of("army_id",new OpportunityJson.IntegerValue(BigInteger.valueOf(army))));}
    public static RawJson key(Selection selection) {
        var n=StrictJson.object().put("identity",selection.input().identity().bindingSha256()).put("army_id",selection.army())
                .put("snapshot_sha256",DriverJson.sha256(DriverJson.encode(selection.input().snapshot())));
        return new RawJson(StrictJson.canonical(n));
    }
    private static String id(Selection selection){return "commander-reconciliation-"+selection.army()+"-"+DriverJson.sha256(key(selection).bytes());}
    public static ReadContract<CommanderObservationCollector.Observation> contract(Selection selected,ExactRef actualSource) {
        Objects.requireNonNull(actualSource);var operation=operation(selected.army());
        return new ReadContract<>(id(selected),operation,Optional.of(CommanderQuality.QUERY_CAPABILITY),
                "commander_candidates_current_army",ReadContract.PermissionMode.ADVERTISED_CAPABILITY,
                ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.RECONCILIATION_OBSERVATION,actualSource,
                (request,requestId)->{requireRequest(selected,request);return new NativeRequest(operation.value(),CommanderQuality.QUERY_CAPABILITY,new RawJson(new byte[]{'{','}'}));},
                receipt->admit(selected,receipt),receipt->admit(selected,receipt));
    }
    public static PlanningReadRequest request(Selection selection,Instant actualDeadline) {
        return PlanningReadRequest.newReconciliation(selection.input().identity(),operation(selection.army()),arguments(selection.army()),actualDeadline);
    }
    private static void requireRequest(Selection selected,PlanningReadRequest request) {
        var actual=request.origin().requireReconciliation();var expected=selected.input().identity();
        StrictJson.require(actual.sameGuardFrame(expected)&&request.reconciliationBefore().equals(expected.factual())
                &&request.source().equals(expected.source())&&request.sessionId().equals(expected.sessionId())
                &&request.operation().equals(operation(selected.army()))&&request.arguments().equals(arguments(selected.army())),
                "commander reconciliation request crossed canonical pending/frame/source/subject");
    }
    public static CommanderObservationCollector.Observation admit(Selection selected,PlanningReadReceipt receipt) {
        requireRequest(selected,receipt.request());var identity=selected.input().identity();var operation=operation(selected.army());
        StrictJson.require(receipt.contractId().equals(id(selected))&&receipt.before().guardMode()==ReadContract.GuardMode.RECONCILIATION_OBSERVATION
                &&receipt.after().guardMode()==ReadContract.GuardMode.RECONCILIATION_OBSERVATION,
                "commander reconciliation cannot consume an ordinary read");
        for(var guard:List.of(receipt.before(),receipt.after())) {
            var binding=guard.binding();
            StrictJson.require(binding.origin().requireReconciliation().sameGuardFrame(identity)
                    &&binding.source().equals(identity.source())&&binding.sessionId().equals(identity.sessionId())
                    &&binding.connectionGeneration().equals(identity.connectionGeneration())&&binding.operation().equals(operation),
                    "commander reconciliation receipt crossed its actual scope");
        }
        StrictJson.require(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256())
                &&receipt.original().nativeOk()&&receipt.original().originalResultToken().isPresent(),
                "commander reconciliation lacks unchanged full guards and original successful native result");
        var raw=DriverJson.object(receipt.original().originalResultToken().orElseThrow().bytes(),DriverJson.MAX_NATIVE_BYTES);
        // A successful exact advertised-capability guard establishes this single query capability only.
        return CommanderObservationCollector.normalizeObserved(selected.input().snapshot(),identity.factual(),selected.army(),raw,
                Set.of(CommanderQuality.QUERY_CAPABILITY),Optional.empty());
    }
    private static void requireSubject(Input input,int army) {
        var armies=OpportunityJson.array(input.snapshot().get("player_armies"),"player_armies");
        boolean found=false;
        for(var value:armies) {
            var row=OpportunityJson.object(value,"player Army");
            if(new OpportunityJson.IntegerValue(BigInteger.valueOf(army)).equals(row.get("army_id"))
                    &&new OpportunityJson.Bool(true).equals(row.get("controllable"))) {StrictJson.require(!found,"duplicate controllable Army");found=true;}
        }
        StrictJson.require(found,"commander reconciliation subject is outside actual controllable Army scope");
    }
}
