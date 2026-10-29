package org.xar.ck3.control.application.driver;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.NativeSnapshotWaitPort;
import org.xar.ck3.control.application.action.ObservationProvenance;
import org.xar.ck3.control.application.advance.AdvanceObservationPort;
import org.xar.ck3.control.application.lifecycle.LifecycleObservationPort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Sole held transport projection and bounded retained-before view. Owns no transport, file or writer lifetime. */
public final class HeldDriverObservationPort implements AdvanceObservationPort {
    @FunctionalInterface public interface OriginalEvidencePort {
        ExactRef preserve(NativeObservationPort.ObservedFrame actual);
    }
    private final NativeObservationPort transport;
    private final DriverObservationFacts.Reader facts;
    private final OriginalEvidencePort evidence;
    private final DriverObservationAssembler assembler;
    private final int maximumRetainedFrames;
    private final ArrayDeque<DriverObservationAssembler.Complete> retained=new ArrayDeque<>();
    public HeldDriverObservationPort(NativeObservationPort sameHeldTransport,DriverObservationFacts.Reader actualFacts,
            OriginalEvidencePort actualEvidence,DriverObservationAssembler assembler,int maximumRetainedFrames) {
        transport=Objects.requireNonNull(sameHeldTransport);facts=Objects.requireNonNull(actualFacts);
        evidence=Objects.requireNonNull(actualEvidence);this.assembler=Objects.requireNonNull(assembler);
        StrictJson.require(maximumRetainedFrames>=1 && maximumRetainedFrames<=4096,"explicit bounded retained observation count required");
        this.maximumRetainedFrames=maximumRetainedFrames;
    }
    public DriverObservationAssembler.FullSnapshot observeFull(Instant deadline) throws InterruptedException {
        Objects.requireNonNull(deadline);
        StrictJson.require(Instant.now().isBefore(deadline),"actual observation deadline expired");
        NativeObservationPort.ObservedFrame actual=transport.observe(deadline);
        StrictJson.require(!actual.observedAt().isAfter(deadline),"native observation completed after deadline");
        ExactRef original=evidence.preserve(actual);
        DriverObservationFacts.Result read=facts.read(actual);
        if(read instanceof DriverObservationFacts.Unavailable missing) throw new IllegalStateException("incomplete actual Driver facts: "+String.join(",",missing.reasons()));
        return assembler.projectFull(actual,((DriverObservationFacts.Known)read).facts(),original);
    }
    public DriverObservationAssembler.Complete observe(Instant deadline) throws InterruptedException {
        var full=observeFull(deadline);
        return complete(full);
    }
    /**
     * Projects this exact original received frame using the same Driver/evidence owners, with no
     * transport read or cached replacement. The caller must separately verify fresh READ custody;
     * an ObservedFrame and this DATA projection alone do not qualify a post-action observation.
     */
    public DriverObservationAssembler.FullSnapshot projectFull(NativeObservationPort.ObservedFrame received,
            Instant captureUntil) throws IOException {
        Objects.requireNonNull(received);Objects.requireNonNull(captureUntil);
        StrictJson.require(Instant.now().isBefore(captureUntil),"actual received-frame projection deadline expired");
        return waited(received,captureUntil);
    }
    /** Same original projection, requiring a complete ordinary identity and retaining that exact before image. */
    public DriverObservationAssembler.Complete project(NativeObservationPort.ObservedFrame received,
            Instant captureUntil) throws IOException {
        return complete(projectFull(received,captureUntil));
    }
    private DriverObservationAssembler.Complete complete(DriverObservationAssembler.FullSnapshot full) {
        var result=assembler.assemble(full.actual(),full.facts(),full.originalEvidence());
        if(result instanceof DriverObservationAssembler.Incomplete missing) throw new IllegalStateException("incomplete actual semantic observation: "+String.join(",",missing.reasons()));
        var complete=(DriverObservationAssembler.Complete)result;
        retain(complete);
        return complete;
    }
    /** Bootstrap-only reuse of the same already observed packet and its complete Driver projection. */
    void retainVerified(DriverObservationAssembler.FullSnapshot full,DriverObservationAssembler.Complete complete) {
        Objects.requireNonNull(full);Objects.requireNonNull(complete);
        var replay=assembler.projectFull(full.actual(),full.facts(),full.originalEvidence());
        StrictJson.require(replay.semantic().equals(full.semantic())
                && replay.fullBindingSha256().equals(full.fullBindingSha256()),
                "retained full observation differs from original native/Driver projection");
        var result=assembler.assemble(full.actual(),full.facts(),full.originalEvidence());
        StrictJson.require(result instanceof DriverObservationAssembler.Complete,
                "retained original native/Driver observation is incomplete");
        StrictJson.require(((DriverObservationAssembler.Complete)result).equals(complete),
                "retained complete observation differs from original native/Driver projection");
        retain(complete);
    }
    private void retain(DriverObservationAssembler.Complete complete) {
        synchronized(retained) {
            retained.removeIf(old -> old.identity().equals(complete.identity()) && old.originalEvidence().equals(complete.originalEvidence()));
            retained.addLast(complete);
            while(retained.size()>maximumRetainedFrames)retained.removeFirst();
        }
    }
    public enum HistoryExportMode { FULL, OMITTED }
    public sealed interface SnapshotExport permits OrdinarySnapshotExport,FullSnapshotExport {
        org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj semantic();
        HistoryExportMode historyMode();long totalCount();long includedCount();
    }
    public record OrdinarySnapshotExport(DriverObservationAssembler.Complete actual,
            org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj semantic,HistoryExportMode historyMode,
            long totalCount,long includedCount) implements SnapshotExport {
        public OrdinarySnapshotExport {Objects.requireNonNull(actual);requireExport(semantic,historyMode,totalCount,includedCount);}
    }
    public record FullSnapshotExport(PublicSnapshotCodec.FullSnapshotOriginals originals,
            org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj semantic,HistoryExportMode historyMode,
            long totalCount,long includedCount) implements SnapshotExport {
        public FullSnapshotExport {Objects.requireNonNull(originals);requireExport(semantic,historyMode,totalCount,includedCount);}
    }
    private static void requireExport(org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj semantic,
            HistoryExportMode historyMode,long totalCount,long includedCount) {
        Objects.requireNonNull(semantic);Objects.requireNonNull(historyMode);
        StrictJson.require(totalCount>=0 && includedCount>=0 && includedCount<=totalCount,"finite actual snapshot history counts required");
    }
    public OrdinarySnapshotExport snapshot(Instant deadline,boolean includeNativeCommandHistory) throws InterruptedException {
        return export(observe(deadline),includeNativeCommandHistory);
    }
    /** Sole typed packet wait. An actual endpoint timeout returns current original DATA even if its public revision is unchanged. */
    public OrdinarySnapshotExport waitForChange(java.math.BigInteger afterPublicRevision,Instant waitUntil,Instant captureUntil,
            boolean includeNativeCommandHistory)throws IOException,InterruptedException {
        return export(complete(waitForChangeFull(afterPublicRevision,waitUntil,captureUntil)),includeNativeCommandHistory);
    }
    /** Death-capable actual DATA producer. A FullSnapshot is not an ordinary identity, lifecycle proof or readiness grant. */
    public DriverObservationAssembler.FullSnapshot waitForChangeFull(java.math.BigInteger afterPublicRevision,Instant waitUntil,Instant captureUntil)
            throws IOException,InterruptedException {
        Objects.requireNonNull(afterPublicRevision);Objects.requireNonNull(waitUntil);Objects.requireNonNull(captureUntil);
        StrictJson.require(afterPublicRevision.signum()>=0 && captureUntil.isAfter(waitUntil)
                && Instant.now().isBefore(captureUntil),"nonnegative revision and distinct live wait/capture deadlines required");
        if(!(transport instanceof NativeSnapshotWaitPort actualWait))
            throw new IOException("actual held transport has no typed public snapshot wait producer");
        var current=waited(actualWait.currentSnapshot(captureUntil),captureUntil);
        if(current.facts().publicRevision().compareTo(afterPublicRevision)>0)return current;
        for(;;) {
            if(!Instant.now().isBefore(captureUntil))throw new IOException("actual waited snapshot exceeded its original capture deadline");
            NativeSnapshotWaitPort.WaitResult result=Objects.requireNonNull(actualWait.waitForSnapshot(waitUntil,captureUntil));
            var actual=waited(result.frame(),captureUntil);
            if(result instanceof NativeSnapshotWaitPort.Elapsed || actual.facts().publicRevision().compareTo(afterPublicRevision)>0)
                return actual;
        }
    }
    /** One actual retained-packet read after an ACK can keep the original frame time/revision.
     * The private port-issued sample proves the call interval, never that the cached frame was born after the ACK.
     * Root still qualifies the actual transport/source/writer and the full Driver originals separately.
     */
    public record SampledFullSnapshot(DriverObservationAssembler.FullSnapshot full,NativeSnapshotWaitPort.ReadSample sample) {
        public SampledFullSnapshot {
            Objects.requireNonNull(full);Objects.requireNonNull(sample);
            StrictJson.require(full.actual()==sample.frame(),"sample projection must retain its identical actual original frame");
        }
    }
    public SampledFullSnapshot sampleCurrentFull(Instant captureUntil)throws IOException {
        Objects.requireNonNull(captureUntil);
        if(!(transport instanceof NativeSnapshotWaitPort actualPort))throw new IOException("actual held transport has no source-bound current-packet sampling producer");
        var sampled=actualPort.sampleCurrentSnapshot(captureUntil);sampled.requirePort(actualPort);
        var full=waited(sampled.frame(),captureUntil);
        sampled.requirePort(actualPort);
        return new SampledFullSnapshot(full,sampled);
    }
    private DriverObservationAssembler.FullSnapshot waited(NativeObservationPort.ObservedFrame received,Instant captureUntil)throws IOException {
        Objects.requireNonNull(received);
        StrictJson.require(!received.observedAt().isAfter(captureUntil),"actual waited packet completed after original capture deadline");
        ExactRef original=evidence.preserve(received);
        DriverObservationFacts.Result read=facts.read(received);
        if(read instanceof DriverObservationFacts.Unavailable missing)
            throw new IOException("actual waited original has incomplete current Driver facts: "+String.join(",",missing.reasons()));
        var full=assembler.projectFull(received,((DriverObservationFacts.Known)read).facts(),original);
        var ordinary=assembler.assemble(received,((DriverObservationFacts.Known)read).facts(),original);
        if(ordinary instanceof DriverObservationAssembler.Complete complete)retain(complete);
        if(!Instant.now().isBefore(captureUntil))throw new IOException("actual waited snapshot projection exceeded its original capture deadline");
        return full;
    }
    private static OrdinarySnapshotExport export(DriverObservationAssembler.Complete actual,boolean includeHistory) {
        return PublicSnapshotCodec.export(actual,includeHistory);
    }
    /** Original before image only: this operation performs no I/O or replacement observation. */
    public DriverObservationAssembler.Complete requireRetained(ObservationIdentity before,ExactRef originalEvidence) {
        Objects.requireNonNull(before);Objects.requireNonNull(originalEvidence);
        synchronized(retained) {
            return retained.stream().filter(row -> row.identity().equals(before) && row.originalEvidence().equals(originalEvidence))
                    .findFirst().orElseThrow(() -> new IllegalStateException("actual original before observation is not retained"));
        }
    }
    @Override public Frame current(ActionCommand parent,Instant deadline) {
        var complete=observeForAdvance(deadline);requireParent(parent,complete);
        return frame(complete);
    }
    @Override public Frame next(ActionCommand parent,ObservationIdentity after,Instant deadline) {
        var complete=observeForAdvance(deadline);requireParent(parent,complete);
        StrictJson.require(after.machineId().equals(complete.identity().machineId()) && after.game().equals(complete.identity().game())
                && after.frame().episodeRunId().equals(complete.identity().frame().episodeRunId())
                && complete.identity().frame().identity().nativeRevision().compareTo(after.frame().identity().nativeRevision())>0,
                "next requires a genuinely newer native revision on the same Game/episode");
        return frame(complete);
    }
    private static Frame frame(DriverObservationAssembler.Complete complete) {
        return new Frame(complete.identity(),complete.source(),complete.sessionId(),complete.semantic(),
                new ObservationProvenance.Push(complete.identity().frame().snapshotId(),
                        complete.identity().frame().identity().nativeRevision(),complete.originalEvidence()),
                complete.observedAt(),complete.originalEvidence());
    }
    private DriverObservationAssembler.Complete observeForAdvance(Instant deadline) {
        try { return observe(deadline); }
        catch(InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("actual held Advance observation interrupted; no completion or replay permission",interrupted);
        }
    }
    private static void requireParent(ActionCommand parent,DriverObservationAssembler.Complete observed) {
        StrictJson.require(parent.before().machineId().equals(observed.identity().machineId()) && parent.before().game().equals(observed.identity().game())
                && parent.before().frame().episodeRunId().equals(observed.identity().frame().episodeRunId())
                && parent.sessionId().equals(observed.sessionId()) && parent.source().equals(observed.source()),"observation crossed held parent Game/source/session/episode");
    }
    /** Same held resource, with the lifecycle domain's death-capable result type. */
    public LifecycleObservationPort lifecycle(DriverStateAssembler sameDriver) {
        StrictJson.require(facts==sameDriver,"lifecycle must share the actual Driver facts authority");
        return new LifecycleObservationPort() {
            @Override public Snapshot current(ActionCommand parent,Instant deadline) throws InterruptedException {
                return lifecycleSnapshot(parent,observeFull(deadline),sameDriver);
            }
            @Override public Snapshot next(ActionCommand parent,Snapshot previous,Instant deadline) throws InterruptedException {
                var next=current(parent,deadline);
                StrictJson.require(next.actual().session().equals(previous.actual().session())
                        && next.actual().nativeRevision().compareTo(previous.actual().nativeRevision())>0,"lifecycle next requires fresh same-held native revision");
                return next;
            }
        };
    }
    private static LifecycleObservationPort.Snapshot lifecycleSnapshot(ActionCommand parent,DriverObservationAssembler.FullSnapshot full,
            DriverStateAssembler sameDriver) {
        StrictJson.require(parent.before().machineId().equals(full.actual().session().machineId())
                && parent.before().game().equals(full.actual().session().game()) && parent.sessionId().equals(full.actual().session().sessionId())
                && parent.source().equals(full.facts().source()),"lifecycle observation crossed actual held parent");
        try {
            return sameDriver.withFrozenFacts(frozen -> {
                StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,"full lifecycle Driver unavailable");
                var known=(DriverSnapshotFacts.Known)frozen.state();
                StrictJson.require(known.stamp().driverVersion()==full.facts().driverVersion()
                        && known.stamp().episodeEpoch()==full.facts().episodeEpoch()
                        && known.observation().filter(full.facts()::equals).isPresent(),"lifecycle observation crossed frozen Driver version");
                return new LifecycleObservationPort.Snapshot(full.actual(),full.facts().source(),full.semantic(),known,full.originalEvidence());
            });
        } catch(IOException failure) { throw new UncheckedIOException(failure); }
    }
}
