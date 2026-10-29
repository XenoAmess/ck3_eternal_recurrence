package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.CompletedCycleProof;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs;

/** One cycle verifier route table. Registration neither saves nor creates a Game or a checkpoint authority. */
public final class RootCheckpointVerifierRouter implements OrdinaryCycleTransitions.CheckpointVerifier {
    private record Entry(RootCheckpointVerifier verifier,Optional<CheckpointPair> firstBaseline) {
        private Entry {Objects.requireNonNull(verifier);Objects.requireNonNull(firstBaseline);}
    }
    private final ContinuityWriter writer;
    private final Map<SessionIdentity,Entry> entries=new LinkedHashMap<>();

    public RootCheckpointVerifierRouter(ContinuityWriter actualWriter) {writer=Objects.requireNonNull(actualWriter);}

    /** Initial actual Root stage only; no replacement or inferred owner is accepted through this branch. */
    public synchronized void registerInitial(ContinuityStorePort.Session same,SessionIdentity actualOwner,
            RootCheckpointVerifier actualVerifier)throws IOException {
        writer.requireSession(same);Objects.requireNonNull(actualOwner);requireVerifier(actualVerifier);
        if(!entries.isEmpty())throw new IOException("initial checkpoint route is already registered; new episodes require actual NEXT baseline proof");
        entries.put(actualOwner,new Entry(actualVerifier,Optional.empty()));
    }

    /** Root registers a new verifier only after the private NEXT input producer proves its actual first SAVE and BASELINE. */
    public synchronized void registerNext(ContinuityStorePort.Session same,LifecycleEpisodeInputs.NextBaselineBinding actual,
            RootCheckpointVerifier actualVerifier)throws IOException {
        writer.requireSession(same);Objects.requireNonNull(actual);requireVerifier(actualVerifier);actual.requireCurrent(same);
        var before=actual.beforeOwner();var after=actual.afterOwner();var first=actual.firstCheckpoint();
        requirePairOwner(after,first.pair());
        if(!entries.containsKey(before)||before.equals(after)||!first.session().equals(after)
                ||!actual.semantic().frame().game().equals(after.game())
                ||!actual.baseline().baseline().pairRef().equals(first.pairReference()))
            throw new IOException("NEXT checkpoint route requires the registered predecessor and its actual new-owner first SAVE baseline");
        Entry existing=entries.get(after);
        if(existing!=null) {
            if(existing.verifier()!=actualVerifier||!existing.firstBaseline().equals(Optional.of(first.pair())))
                throw new IOException("an actual episode cannot replace its original checkpoint verifier or first pair");
            return;
        }
        if(entries.size()>=4096)throw new IOException("checkpoint verifier route retention bound reached; no history is silently discarded");
        entries.put(after,new Entry(actualVerifier,Optional.of(first.pair())));
    }

    /** A physical restore is a distinct private issuer branch; it cannot reuse the initial or NEXT registration path. */
    public synchronized void registerRestored(ContinuityStorePort.Session same,RestoreCheckpointService actualIssuer,
            RestoreCheckpointService.RestoreBinding actual,RootCheckpointVerifier actualVerifier)throws IOException {
        writer.requireSession(same);Objects.requireNonNull(actualIssuer);Objects.requireNonNull(actual);requireVerifier(actualVerifier);
        actualIssuer.requireRetainedOriginal(same,actual);
        var material=actual.savedMaterial();material.requireRetained(same);
        var original=material.session();var restored=actual.session();requirePairOwner(original,actual.pair());
        if(!entries.containsKey(original)||original.equals(restored)||!material.pair().equals(actual.pair())
                ||!actual.semantic().frame().game().equals(restored.game())
                ||!actual.semantic().frame().machineId().equals(restored.machineId())
                ||actual.driver().session().bridgePid()!=restored.game().pid()
                ||!actual.driver().session().actorId().equals(actual.semantic().frame().frame().identity().player())
                ||!actual.driver().session().episodeRunId().equals(actual.pair().frame().frame().episodeRunId())
                ||!actual.source().machineId().equals(restored.machineId())
                ||!original.machineId().equals(restored.machineId()))
            throw new IOException("restored checkpoint route requires the original saved session and actual private replacement binding");
        Entry existing=entries.get(restored);
        if(existing!=null) {
            if(existing.verifier()!=actualVerifier||!existing.firstBaseline().equals(Optional.of(actual.pair())))
                throw new IOException("the actual restored session cannot replace its original checkpoint route");
            return;
        }
        if(entries.size()>=4096)throw new IOException("checkpoint verifier route retention bound reached; preserve the original history");
        entries.put(restored,new Entry(actualVerifier,Optional.of(actual.pair())));
    }

    @Override public String verify(ContinuityStorePort.Session same,SessionIdentity actualOwner,CheckpointPair pair,
            CompletedCycleProof actualProof)throws IOException {
        writer.requireSession(same);requirePairOwner(actualOwner,pair);Objects.requireNonNull(actualProof);
        Entry selected;
        synchronized(this) {selected=entries.get(actualOwner);}
        if(selected==null)throw new IOException("no actual checkpoint verifier registered for the exact session and Game generation");
        requireVerifier(selected.verifier());String before=same.head().digest();
        String result=selected.verifier().verify(same,actualOwner,pair,actualProof);
        writer.requireSession(same);
        if(!same.head().digest().equals(before))throw new IOException("checkpoint route verification changed the original canonical writer");
        return result;
    }

    private void requireVerifier(RootCheckpointVerifier actual)throws IOException {
        Objects.requireNonNull(actual).requireOwner(writer);
        if(!actual.isBound())throw new IOException("checkpoint route requires the actual bound source store and capture producer");
    }
    /** Pure identity check only; passing it cannot register or qualify a verifier. */
    static void requirePairOwner(SessionIdentity owner,CheckpointPair pair)throws IOException {
        Objects.requireNonNull(owner);Objects.requireNonNull(pair);
        if(!owner.machineId().equals(pair.frame().machineId())||!owner.game().equals(pair.frame().game()))
            throw new IOException("checkpoint pair belongs to another machine or exact Game generation");
    }
}
