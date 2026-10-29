package org.xar.ck3.control.application.driver;

import java.io.IOException;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.service.root.RootRestoreMaterials;

/** Genuine private Root integration only. No Managed Game, ColdAdoption, Stage or commit can be minted here. */
public final class RootWarmNativeCampaignActualAssertions {
    private RootWarmNativeCampaignActualAssertions(){ }

    /** Run only with the actual already committed ordinary or FIRST physical restore and its original Stage. */
    public static DriverBootstrap.Adopted adoptAndRetry(DriverBootstrap.Staged actualStage,
            RootRestoreMaterials.ColdAdoption actualCold,DriverBootstrap.Seed finalSeed,
            WriterContracts.Prepared prepared,WriterContracts.Receipt committed,ContinuityStorePort.Session same,
            DriverBootstrap.ExactArtifactReader originals,DriverBootstrap.HistoryCoverageReader history,
            Instant firstDeadline,Instant retryDeadline)throws IOException,InterruptedException {
        Objects.requireNonNull(actualStage);Objects.requireNonNull(actualCold);Objects.requireNonNull(same);
        String head=same.head().digest();same.requireCommitted(prepared,committed);
        var originalProducer=actualStage.producer();
        var adopted=DriverBootstrap.adoptRestored(actualStage,finalSeed,prepared,committed,same,originals,history,firstDeadline);
        actualStage.requireNativeCampaignProjectionPublished(originalProducer,actualCold,same,finalSeed,prepared,committed);
        require(adopted.producer()==originalProducer&&adopted.authority()==actualStage.authority(),
                "actual warm restore replaced its sole producer or repository");
        require(adopted.first().identity().observationVersion()==DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION,
                "actual warm restore's first postcommit SEM lost profile four");
        adopted.repository().locked(state->{
            require(state instanceof DriverSnapshotFacts.Known known
                    &&known.driver().successionLifecycle() instanceof DriverStateSnapshot.NullValue
                    &&known.stamp().driverSha256().equals(finalSeed.fullDriver().sha256()),
                    "actual warm restore replaced the canonical null-lifecycle Driver");return null;
        });
        // The same original commit is retried. Production must keep its actual CAS result and public revision owner.
        var retried=DriverBootstrap.adoptRestored(actualStage,finalSeed,prepared,committed,same,originals,history,retryDeadline);
        require(retried.producer()==originalProducer&&retried.repository()==adopted.repository()
                &&retried.seed().equals(finalSeed)&&head.equals(same.head().digest()),
                "warm adoption retry changed its original producer, complete Driver, or canonical writer head");
        return retried;
    }

    /** Foreign objects must be genuine objects from another capture; DATA or reflective constructors are forbidden. */
    public static void requireForeignCaptureRefused(DriverBootstrap.Staged actualStage,
            RootRestoreMaterials.ColdAdoption genuineForeignCold,DriverBootstrap.Seed finalSeed,
            WriterContracts.Prepared prepared,WriterContracts.Receipt committed,ContinuityStorePort.Session same)throws IOException {
        String head=same.head().digest();boolean refused=false;
        try {actualStage.requireNativeCampaignProjectionPublished(actualStage.producer(),genuineForeignCold,same,finalSeed,prepared,committed);}
        catch(IOException|IllegalArgumentException expected){refused=true;}
        require(refused&&head.equals(same.head().digest()),"foreign genuine capture acquired another Stage's actual publication");
    }
    /** Call after real attachment commit but before Bootstrap's CAS. ACK/receipt alone must not promote a Stage. */
    public static void requireBeforePublicationRefused(DriverBootstrap.Staged actualStage,
            RootRestoreMaterials.ColdAdoption actualCold,DriverBootstrap.Seed finalSeed,
            WriterContracts.Prepared prepared,WriterContracts.Receipt committed,ContinuityStorePort.Session same)throws IOException {
        same.requireCommitted(prepared,committed);String head=same.head().digest();boolean refused=false;
        try {actualStage.requireNativeCampaignProjectionPublished(actualStage.producer(),actualCold,same,finalSeed,prepared,committed);}
        catch(IOException|IllegalArgumentException expected){refused=true;}
        require(refused&&head.equals(same.head().digest()),"a receipt without the actual CAS promoted a private restore Stage");
    }
    /** An altered version is unqualified DATA even when all original references and the genuine receipt are retained. */
    public static void requireChangedVersionRefused(DriverBootstrap.Staged actualStage,
            RootRestoreMaterials.ColdAdoption actualCold,DriverBootstrap.Seed finalSeed,
            WriterContracts.Prepared prepared,WriterContracts.Receipt committed,ContinuityStorePort.Session same)throws IOException {
        var changed=new DriverBootstrap.Seed(finalSeed.fullDriver(),finalSeed.originalHistoryBasis(),
                Math.addExact(finalSeed.driverVersion(),1),finalSeed.episodeEpoch(),finalSeed.expectedSession(),finalSeed.auxiliary(),finalSeed.loop());
        String head=same.head().digest();boolean refused=false;
        try {actualStage.requireNativeCampaignProjectionPublished(actualStage.producer(),actualCold,same,changed,prepared,committed);}
        catch(IOException|IllegalArgumentException expected){refused=true;}
        require(refused&&head.equals(same.head().digest()),"changed public Seed version acquired an original private committed projection");
    }
    private static void require(boolean condition,String message){if(!condition)throw new AssertionError(message);}
}
