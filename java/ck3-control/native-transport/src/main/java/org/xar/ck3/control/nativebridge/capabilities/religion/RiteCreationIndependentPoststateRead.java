package org.xar.ck3.control.nativebridge.capabilities.religion;

import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.OptionalLong;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.ritecreation.RiteCreationContract.Outcome;
import org.xar.ck3.control.application.ritecreation.RiteCreationContract.Scope;
import org.xar.ck3.control.application.ritecreation.RiteCreationIndependentPoststate;
import static org.xar.ck3.control.application.ritecreation.RiteCreationContract.need;

/** Registered original receipt -> sole context codec -> independent diagnostics.
 * This adapter sends nothing and never issues action or business acceptance. */
public final class RiteCreationIndependentPoststateRead {
    private RiteCreationIndependentPoststateRead(){ }
    public static final class Retained {
        private final Complete snapshot;
        private final PlanningReadReceipt receipt;
        private final Scope scope;
        private final RiteCreationIndependentPoststate.DiagnosticSnapshot diagnostic;
        private final RiteCreationIndependentPoststate.Observation observation;
        private Retained(Complete snapshot,PlanningReadReceipt receipt,Scope scope,
                RiteCreationIndependentPoststate.DiagnosticSnapshot diagnostic,
                RiteCreationIndependentPoststate.Observation observation){
            this.snapshot=snapshot;this.receipt=receipt;this.scope=scope;this.diagnostic=diagnostic;this.observation=observation;
        }
        public Complete snapshot(){return snapshot;}
        public PlanningReadReceipt receipt(){return receipt;}
        public Scope scope(){return scope;}
        public RiteCreationIndependentPoststate.Observation observation(){return observation;}
    }
    /** Scope is independently verified by the existing campaign/episode owner, never by this data adapter. */
    public static Retained decode(Complete actual,Scope independentlyVerifiedScope,PlanningReadReceipt receipt){
        Objects.requireNonNull(actual);Objects.requireNonNull(independentlyVerifiedScope);Objects.requireNonNull(receipt);
        need(receipt.request().before().equals(actual.identity())
                &&receipt.request().source().equals(actual.source())
                &&receipt.request().sessionId().equals(actual.sessionId()),"poststate receipt differs from actual Complete identity/source/session");
        for(var guard:java.util.List.of(receipt.before(),receipt.after())){
            need(guard.binding().observed().equals(actual.identity())
                    &&guard.binding().connectionGeneration().equals(actual.connectionGeneration())
                    &&guard.paused()&&guard.mapReady()&&guard.playerAlive(),"poststate receipt guard differs from actual paused owner/frame");
        }
        var diagnostic=RiteCreationIndependentPoststate.snapshot(actual,independentlyVerifiedScope);
        var decoded=PlayerReligionContextRead.decode(receipt);
        // Context contains only finite integer/text/bool/null fields; Jackson's existing JSON writer preserves them.
        // Do not pass this potentially large original through the unrelated 1 MiB StrictJson lane.
        var original=new RawJson(PlayerReligionContextRead.flattened(decoded).toString().getBytes(StandardCharsets.UTF_8));
        var observation=RiteCreationIndependentPoststate.observe(diagnostic,original);
        return new Retained(actual,receipt,independentlyVerifiedScope,diagnostic,observation);
    }
    public static RiteCreationIndependentPoststate.Result evaluate(Retained before,Retained after,Outcome expected,OptionalLong quotedPietyCostRaw){
        Objects.requireNonNull(before);Objects.requireNonNull(after);
        need(before.snapshot.identity().machineId().equals(after.snapshot.identity().machineId())
                &&before.snapshot.sessionId().equals(after.snapshot.sessionId())
                &&before.scope.equals(after.scope),"poststate actual machine/session/scope changed");
        return RiteCreationIndependentPoststate.evaluate(before.diagnostic,after.diagnostic,before.observation,after.observation,expected,quotedPietyCostRaw);
    }
}

