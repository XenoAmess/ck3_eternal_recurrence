package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.UUID;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.driver.DriverBootstrap;
import org.xar.ck3.control.application.history.LegacyResumeMigration;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.OriginalLegacyResume;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.platform.ColdBootstrapJson;
import org.xar.ck3.control.platform.JavaGameLifecycle;
import org.xar.ck3.control.platform.ManagedGameSession;
import org.xar.ck3.control.platform.RootProcessAttach;

/** Fresh private capability from actual physical custody AND the existing canonical cold reducer.
 * Old daemon objects and JSON receipts are never constructors for this producer. */
public final class RootPrivateBootstrap {
    private RootPrivateBootstrap() { }
    public static Prepared prepare(RootRuntimeContext context,JavaGameLifecycle owner,JavaGameLifecycle.Started originalStart,
            CheckpointPair pair,RootLegacyResumeRuntime actualResume,Path freshEvidenceRoot,Instant deadline)
            throws IOException,InterruptedException {
        Objects.requireNonNull(context);Objects.requireNonNull(actualResume);Objects.requireNonNull(originalStart);
        if(context.game()!=originalStart.session())throw new IOException("Cold bootstrap crossed the actual retained Root Game");
        actualResume.requireOwner(context.core(),context.game(),context.source());sources(context);context.requireCurrent(deadline);
        RootProcessAttach.Custody physical=RootProcessAttach.retain(owner,originalStart,pair,freshEvidenceRoot,deadline);
        try{return new Prepared(context,actualResume,physical);}catch(RuntimeException failure){try{physical.close();}catch(IOException cleanup){failure.addSuppressed(cleanup);}throw failure;}
    }
    public static final class Prepared implements AutoCloseable {
        private final RootRuntimeContext context;
        private final RootLegacyResumeRuntime actualResume;
        private final RootProcessAttach.Custody physical;
        private RootLegacyResumeRuntime.Prepared checked;
        private ContinuityStorePort.Session originalSession;
        private WriterContracts.Receipt actualReceipt;
        private Phase phase=Phase.PHYSICAL_PREPARED;
        private boolean accepted,closed;
        private Prepared(RootRuntimeContext context,RootLegacyResumeRuntime actualResume,RootProcessAttach.Custody physical) {
            this.context=context;this.actualResume=actualResume;this.physical=physical;
        }
        public RootRuntimeContext context(){return context;}
        public ManagedGameSession game(){return context.game();}
        public RootLegacyResumeRuntime actualResume(){return actualResume;}
        public Instant deadline(){return physical.deadline();}
        public CheckpointPair pair(){return physical.pair();}
        /** Core calls this inside its existing writer lock immediately before the sole real commit. */
        void requireBeforeCommit(ContinuityStorePort.Session same,RootLegacyResumeRuntime.Prepared actual)throws IOException {
            if(closed||accepted||checked!=null)throw new IOException("Cold bootstrap preparation is closed, consumed or already entered");
            context.writer().requireSession(same);context.requireCurrent(deadline());sources(context);physical.requireCurrent();
            actualResume.requireOwner(context.core(),game(),context.source());
            requireRoute(actual.delta().route(),actual.rejectedCold().isPresent());
            actual.requireOwner(same,context.transport(),context.source(),context.archive());
            actual.requireColdBootstrapPair(same,pair());
            if(!actual.originalNative().session().game().equals(game().generation())
                    ||!actual.originalNative().session().sessionId().equals(game().sessionId()))
                throw new IOException("Private cold reducer observed a different actual Game or native session");
            physical.requireCurrent();checked=actual;originalSession=same;phase=Phase.PRECOMMIT_ACCEPTED;
        }
        /** Package-private: the sole Core must first insert the real adopter result into its private set. */
        void recordCommitted(ContinuityStorePort.Session same,RootLegacyResumeRuntime.Prepared actual,
                WriterContracts.Receipt receipt)throws IOException {
            if(closed||accepted||checked!=actual||same!=originalSession)throw new IOException("Cold commit escaped its exact entered writer attempt");
            actual.requireCommitted(same,receipt);actualReceipt=receipt;phase=Phase.CANONICAL_COMMITTED;
        }
        Original acceptCommitted(ContinuityStorePort.Session same,RootLegacyResumeRuntime.Prepared actual,
                WriterContracts.Receipt receipt,DriverBootstrap.Adopted adopted)throws IOException {
            if(closed||accepted||checked!=actual||same!=originalSession)throw new IOException("Cold bootstrap lost its exact precommit attempt or writer Session");
            context.writer().requireSession(same);context.core().requireColdOriginalAdopted(this,adopted);
            actual.requireCommitted(same,receipt);physical.requireCurrent();sources(context);
            actualReceipt=receipt;phase=Phase.CANONICAL_COMMITTED_AND_ADOPTED;
            if(!adopted.session().game().equals(game().generation())||!adopted.session().sessionId().equals(game().sessionId()))
                throw new IOException("Actual Core Driver adopter returned a different Game/session");
            var data=new ColdBootstrapJson.AdoptionData("xar.java-cold-canonical-bootstrap/v1",UUID.randomUUID().toString(),
                    physical.evidence(),receipt.eventIdentity(),receipt.head().sequence(),ContinuityJson.digest(receipt.head().toJson()),
                    actual.delta().fullDriver(),context.clock().instant().toString());
            Path path=physical.evidenceDirectory().resolve("canonical-bootstrap.json");
            Files.write(path,ColdBootstrapJson.encodeAdoption(data),StandardOpenOption.CREATE_NEW);
            SharedSourceFiles.Witness witness=SharedSourceFiles.observe(path);
            Original result=new Original(context,physical,adopted,actual.request(),receipt,data,witness);
            result.requireOriginal(same);physical.releasePreparation();accepted=true;phase=Phase.CAPABILITY_RETURNED;return result;
        }
        /** Core records the actual entered phase before propagating failure; a committed edge is never called a retry. */
        void recordFailure(Throwable failure)throws IOException {
            Objects.requireNonNull(failure);String detail=failure.getMessage()==null?"":failure.getMessage();
            var record=new FailureData("xar.java-cold-canonical-failure/v1",game().machineId(),game().sessionId(),phase,
                    failure.getClass().getName(),detail.substring(0,Math.min(detail.length(),2048)),
                    actualReceipt==null?null:actualReceipt.head().sequence(),actualReceipt==null?null:actualReceipt.eventIdentity(),
                    actualReceipt==null?null:ContinuityJson.digest(actualReceipt.head().toJson()),context.clock().instant().toString());
            byte[] bytes=ControlBuild.strictMapper().writeValueAsBytes(record);
            if(bytes.length>ColdBootstrapJson.MAX_BYTES)throw new IOException("Cold canonical failure proof exceeds finite limit");
            Files.write(physical.evidenceDirectory().resolve("canonical-failure.json"),bytes,StandardOpenOption.CREATE_NEW);
        }
        /** Failed preparation closure leaves the actual Game under its existing lifecycle owner. */
        @Override public void close()throws IOException {if(!closed){closed=true;if(!accepted)physical.close();}}
    }
    private enum Phase { PHYSICAL_PREPARED, PRECOMMIT_ACCEPTED, CANONICAL_COMMITTED, CANONICAL_COMMITTED_AND_ADOPTED, CAPABILITY_RETURNED }
    private record FailureData(String schema,String machineId,String sessionId,Phase phase,String exceptionType,String detail,
            Long actualCommittedSequence,String actualEventIdentity,String actualHeadDigest,String observedAtUtc) { }
    /** New private issuer, minted only after this new daemon's canonical cold commit and real Driver adoption. */
    public static final class Original {
        private final RootRuntimeContext context;
        private final RootProcessAttach.Custody physical;
        private final DriverBootstrap.Adopted adopted;
        private final WriterContracts.Request request;
        private final WriterContracts.Receipt receipt;
        private final ColdBootstrapJson.AdoptionData data;
        private final SharedSourceFiles.Witness witness;
        private Original(RootRuntimeContext context,RootProcessAttach.Custody physical,DriverBootstrap.Adopted adopted,
                WriterContracts.Request request,WriterContracts.Receipt receipt,ColdBootstrapJson.AdoptionData data,SharedSourceFiles.Witness witness) {
            this.context=context;this.physical=physical;this.adopted=adopted;this.request=request;this.receipt=receipt;this.data=data;this.witness=witness;
        }
        public RootRuntimeContext context(){return context;}
        public ManagedGameSession game(){return context.game();}
        public CheckpointPair pair(){return physical.pair();}
        public DriverBootstrap.Adopted adopted(){return adopted;}
        public WriterContracts.Request migrationRequest(){return request;}
        public WriterContracts.Receipt commitReceipt(){return receipt;}
        public ExactRef evidence(){var ref=witness.source();return new ExactRef(ref.path(),ref.bytes(),ref.sha256());}
        public ColdBootstrapJson.AdoptionData data(){return data;}
        /** Historical provenance survives later legitimate writes; it grants no current Native readiness. */
        public void requireOriginal(ContinuityStorePort.Session same)throws IOException {
            context.writer().requireSession(same);
            same.requireHistoricalHead(data.committedSequence(),data.committedHeadDigest());physical.requireEvidence();
            if(!witness.equals(SharedSourceFiles.observe(Path.of(witness.source().path()))))throw new IOException("Original private cold canonical evidence changed");
            if(!receipt.eventIdentity().equals(data.eventIdentity())||receipt.head().sequence()!=data.committedSequence()
                    ||!ContinuityJson.digest(receipt.head().toJson()).equals(data.committedHeadDigest()))
                throw new IOException("Original cold receipt differs from its actually committed canonical prefix");
        }
        public void requireCurrent(ContinuityStorePort.Session same,RootRuntimeContext identical)throws IOException {
            if(context!=identical)throw new IOException("Cold private bootstrap belongs to another actual Root context");
            requireOriginal(same);context.requireCurrent(physical.deadline());sources(context);physical.requireCurrent();requireOriginal(same);
        }
    }
    static void requireRoute(OriginalLegacyResume.Route route,boolean rejected)throws IOException {
        if(route!=OriginalLegacyResume.Route.COLD_CHECKPOINT||rejected)
            throw new IOException("Cold private bootstrap requires the real complete checkpoint route; rejection/new-episode and same-PID routes cannot grant it");
    }
    /** Sole actual loaded-class roster; configuration maps each class through getNestHost to its real source. */
    public static List<Class<?>> requiredSourceTypes() {
        java.util.LinkedHashSet<Class<?>> types=new java.util.LinkedHashSet<>(List.of(RootPrivateBootstrap.class,Prepared.class,Original.class,RootProcessAttach.class,
                RootProcessAttach.Custody.class,ColdBootstrapJson.class,ColdBootstrapJson.PhysicalData.class,ColdBootstrapJson.AdoptionData.class,
                RootLegacyResumeRuntime.class,RootLegacyResumeRuntime.Prepared.class,RootColdCheckpointValidator.class,
                RootColdCheckpointValidator.Expected.class,RootColdCheckpointValidator.Verified.class,LegacyResumeMigration.class,
                LegacyResumeMigration.FrozenLifecycle.class,LegacyResumeMigration.BoundLifecycle.class,LegacyResumeMigration.ExplicitNativeCampaign.class,
                Phase.class,FailureData.class));
        // The platform owner's private Failure is an actual guarded class, not a made-up $Failure.java target.
        java.util.Collections.addAll(types,RootProcessAttach.class.getDeclaredClasses());
        return List.copyOf(types);
    }
    private static void sources(RootRuntimeContext context)throws IOException {
        context.game().launchPlan().sources().verify();
        for(Class<?> type:requiredSourceTypes())context.game().launchPlan().sources().requireLoadedClass(type);
    }
}
