package org.xar.ck3.control.g2.context;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.time.Instant;
import java.util.Arrays;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.m7.KernelCheckpointContinuity;
import org.xar.ck3.control.g2.m7.M7NativeProjection;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal;
import org.xar.ck3.control.wave2.runtime.closedadoption.RootColdResumeSession;

/** Concrete existing-owned-arrival consumer. It starts no query, process, action, restore or writer. */
public final class RootM7ObservationProducer {
    private RootM7ObservationProducer() { }
    public static final class Observed {
        private final KernelCheckpointContinuity.Observation observation;
        private final ExactRef originalNativeRef;
        private final String originalRpcSha256;
        private final OrdinaryCampaignGoal.GoalPlan goalPlan;
        private Observed(KernelCheckpointContinuity.Observation observation,ExactRef originalNativeRef,String rpcSha) {
            this.observation=observation;this.originalNativeRef=originalNativeRef;this.originalRpcSha256=rpcSha;
            this.goalPlan=OrdinaryCampaignGoal.plan(observation.goal());
        }
        public KernelCheckpointContinuity.Observation observation() { return observation; }
        public ExactRef originalNativeRef() { return originalNativeRef; }
        public String originalRpcSha256() { return originalRpcSha256; }
        public OrdinaryCampaignGoal.GoalPlan goalPlan() { return goalPlan; }
        public boolean grantsColdAuthority() { return false; }
        public boolean actionReplayAuthorized() { return false; }
        public boolean gameActionsSubmitted() { return false; }
    }

    /** Only the real Native client can mint actual; only the real original Root lifecycle can mint game. */
    public static Observed project(RootColdResumeSession.HeldGame game,
            RootMcpSemanticClient.NativeObservation actual) throws IOException {
        Objects.requireNonNull(game);Objects.requireNonNull(actual);
        game.verify(); var session=game.session(); game.runtime().requireColdResumeSession(session);
        if(session.phase()!=RootColdResumeSession.Phase.LINEAGE_CONFIRMED)
            throw new IOException("Actual post-CAP original Root lineage required before M7 observation");
        var owner=session.nativeOwnerSession().ownedStdio(); owner.verifyActualIdentityAndSources();
        var completed=actual.completion(); var arrival=completed.actualArrival();
        byte[] rpc=completed.originalRpcLine().bytes(),row=completed.ownerRow().bytes().bytes();
        if(completed.isError() || !completed.child().equals(owner.identity())
                || !completed.sessionNonce().equals(owner.sessionNonce())
                || !arrival.identity().equals(owner.identity()) || !arrival.sessionNonce().equals(owner.sessionNonce())
                || !Arrays.equals(arrival.rawBytes(),rpc) || !Instant.now().isBefore(arrival.deadline()))
            throw new IOException("Same private original owned Native completion required");
        ExactRef original=actual.arrival().nativeObservation();
        if(original.bytes()!=row.length || !original.sha256().equals(G2RetainedNativeSourceProvider.sha256(row)))
            throw new IOException("Actual retained Native artifact differs from original owned row");
        new ControlBuild.FileRef(original.path(),original.bytes(),original.sha256()).verify();
        var inputs=session.runtimeInputs();var saved=session.savedFrame();
        JsonNode basis=StrictJson.parse(inputs.basis().bytes(),StrictJson.EXPLICIT_MAX_BYTES);
        byte[] life=StrictJson.canonical(basis.path("checkpoint").get("succession_lifecycle"));
        // NativeObservation was minted only after the admission checked its private CAP generation.
        // This extraction retains that actual value for the shared DATA parser; it is no new approval.
        JsonNode snapshot=ControlBuild.strictMapper().readTree(ProjectionJson.object(row,M7NativeProjection.MAX_BYTES).bytes())
                .path("result").path("structured_content");
        String generation=StrictJson.integer(snapshot.path("diagnostics").get("connection_generation"),
                java.math.BigInteger.ONE,StrictJson.UINT64_MAX).toString();
        var executable=game.runtime().request().gameExecutable();
        var binding=new M7NativeProjection.Binding(game.runtime().request().machineId(),inputs.sdkFreeze().sha256(),
                new G2RetainedNativeSourceProvider.GameIdentity(game.identity().pid(),game.identity().creationFiletimeDecimal()),
                new ExactRef(executable.path(),executable.bytes(),executable.sha256()),saved.episodeRunId(),saved.actorCharacterId(),
                game.pipeName(),generation,ProjectionJson.object(life,M7NativeProjection.MAX_BYTES));
        var observation=M7NativeProjection.project(row,binding);
        game.verify();owner.verifyActualIdentityAndSources();session.requireCurrent();
        return new Observed(observation,original,G2RetainedNativeSourceProvider.sha256(rpc));
    }
}
