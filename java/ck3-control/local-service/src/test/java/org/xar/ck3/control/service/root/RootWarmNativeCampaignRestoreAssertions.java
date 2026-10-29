package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.InterruptedIOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Arrays;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;

/** Genuine public warm restoration only. All private inputs come from the actual Root fixture. */
public final class RootWarmNativeCampaignRestoreAssertions {
    private RootWarmNativeCampaignRestoreAssertions(){ }

    /** Called after each real public restoration, before this same original SAVE is restored again. */
    public static void requireActualRoot(RootApplicationSession actual,RestoreCheckpointService.RestoreBinding binding,
            RootInstalledCatalog catalog,RootFrozenRunProfile.FrozenRunProfile original,Instant originalDeadline)
            throws IOException,InterruptedException {
        Objects.requireNonNull(actual);Objects.requireNonNull(binding);Objects.requireNonNull(catalog);Objects.requireNonNull(original);
        var context=catalog.context();var adopted=actual.driver();var producer=adopted.producer();
        require(!actual.isRetired()&&context.actions()==actual&&context.adopted()==adopted
                &&context.writer()==actual.writer()&&context.archive()==actual.archive()
                &&context.game().generation().equals(actual.identity().game())&&binding.session().equals(actual.identity()),
                "actual warm fixture crossed its published Root, catalog, Driver or private binding");
        require(adopted.first().identity().observationVersion()==DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION
                &&binding.semantic().frame().observationVersion()==DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION
                &&binding.savedMaterial().sourceSemantic().frame().observationVersion()==DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION
                &&binding.savedMaterial().savedDriver().successionLifecycle() instanceof DriverStateSnapshot.NullValue,
                "genuine native_campaign warm path lost saved profile four/null or its first postcommit SEM");
        // This is the service's real historical source, minted after its original attachment/publication.
        actual.writer().locked(same->{
            var origin=binding.requireReboundOrigin(same);origin.requireOriginal(same);
            var pair=binding.originalReadPair();var archive=actual.archive().withSession(same);
            var firstOutcome=archive.load(pair.firstAck());var secondOutcome=archive.load(pair.secondAck());
            require(firstOutcome instanceof NativeActionPort.AckReceived&&secondOutcome instanceof NativeActionPort.AckReceived,
                    "actual public restoration lost its two independently received READ ACKs");
            var first=(NativeActionPort.AckReceived)firstOutcome;var second=(NativeActionPort.AckReceived)secondOutcome;
            first.custody().orElseThrow().verify(first);second.custody().orElseThrow().verify(second);
            require(!first.requestId().equals(second.requestId())&&first.nativeOk()&&second.nativeOk()
                    &&first.custody().orElseThrow().session().equals(second.custody().orElseThrow().session())
                    &&second.custody().orElseThrow().writeEntered().order().compareTo(first.custody().orElseThrow().responseReceived().order())>0,
                    "public restore must send its second independent READ only after the first original ACK");
            for(var ref:pair.references())require(binding.originalAttachment().evidence().stream().anyMatch(pin->pin.reference().equals(ref)),
                    "actual canonical restore attachment did not pin an original READ role");
            require(!Arrays.equals(archive.loadNativeFrame(pair.firstNative()),archive.loadNativeFrame(pair.secondNative())),
                    "public restoration used the same cached native packet twice");
            require(origin==context.requireRestoredOrigin(same)&&origin.newSavedDayCredit()==0&&origin.newCycleCredit()==0,
                    "actual warm source changed its retained issuer or granted new credit");
            producer.requireNativeCampaignProjectionOrigin(original);producer.requireNativeCampaignRestoredProjection(same,origin);return null;
        });
        BigInteger firstRevision=inspect(actual,binding,catalog,original,originalDeadline,null);
        require(actual.driver()==adopted&&actual.driver().producer()==producer,"first warm inspection replaced its actual producer");

        // A real later independent READ, without another restore, CAS, source binding or fabricated observation.
        NativeFreshSnapshotPort actualPort=context.transport();var result=actualPort.readFreshFullState(originalDeadline);
        if(!(result instanceof NativeFreshSnapshotPort.Received received)) {
            var unavailable=(NativeFreshSnapshotPort.Unavailable)result;
            context.withSession(same->{
                var archive=context.archive().withSession(same);archive.preserve(unavailable.dispatch());
                if(unavailable.originalFrame().isPresent())archive.preserveNativeFrame(unavailable.originalFrame().orElseThrow());return null;
            });
            throw new IOException("ACTUAL_WARM_LATER_READ_UNAVAILABLE: original dispatch retained without replay: "+unavailable.reason());
        }
        NativeFreshSnapshotPort.verifyOriginal(received.acknowledgement(),received.originalFrame(),received.snapshotReceived());
        context.withSession(same->{
            var archive=context.archive().withSession(same);archive.preserve(received.acknowledgement());
            archive.preserveNativeFrame(received.originalFrame());return null;
        });
        BigInteger laterRevision=inspect(actual,binding,catalog,original,originalDeadline,received.originalFrame());
        require(laterRevision.compareTo(firstRevision)>=0&&actual.driver()==adopted&&actual.driver().producer()==producer,
                "actual later warm READ reset the sole producer or public revision owner");
        // Retains the complete original saved Driver and all existing Source35 JSON/type/identity regressions.
        RootOrdinaryRestoreCustodyAssertions.requireActualReboundOrigin(actual,binding);
        RootOrdinaryRestoreCustodyAssertions.requireActualFamilyRebound(actual,binding,catalog,originalDeadline);
        // This runs only after both physical inspections have unwound. The native-campaign null
        // branch retains its separate warm semantics and grants no positive M7 ordinary-goal credit.
        if(binding.savedMaterial().savedDriver().campaignGoal() instanceof DriverStateSnapshot.Value)
            RootM7RestoredOrdinaryPlanAssertions.requireActual(actual,binding,catalog,originalDeadline);
    }

    private static BigInteger inspect(RootApplicationSession actual,RestoreCheckpointService.RestoreBinding binding,
            RootInstalledCatalog catalog,RootFrozenRunProfile.FrozenRunProfile original,Instant deadline,ObservedFrame expected)
            throws IOException {
        var context=catalog.context();context.requireCurrent(deadline);
        return context.withSession(same->{
            String head=same.head().digest();var producer=actual.driver().producer();var origin=context.requireRestoredOrigin(same);
            return catalog.remainingDomains().lifecycle().physical().withSnapshot(same,deadline,lease->{
                lease.assertCurrent(same);var full=lease.fullSnapshot();var known=lease.factsKnown();
                var complete=lease.ordinary().orElseThrow(()->new IOException("genuine warm living full observation unavailable"));
                require(complete.identity().observationVersion()==DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION
                        &&full.facts().observationVersion()==DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION
                        &&known.driver().successionLifecycle() instanceof DriverStateSnapshot.NullValue,
                        "actual warm current full Driver/SEM silently selected ordinary lifecycle data");
                if(expected!=null)require(full.actual().session().equals(expected.session())
                        &&full.actual().snapshotId().equals(expected.snapshotId())&&full.actual().nativeRevision().equals(expected.nativeRevision())
                        &&Arrays.equals(full.actual().originalPacket(),expected.originalPacket()),
                        "actual later warm full observation substituted a cached or different native packet");
                require(binding.session().equals(actual.identity())&&context.actions()==actual&&context.adopted()==actual.driver(),
                        "actual warm physical scope crossed the retained public restoration");
                producer.requireNativeCampaignProjectionOrigin(original);producer.requireNativeCampaignRestoredProjection(same,origin);
                try {
                    RootWarmNativeCampaignPlanningAssertions.assertActualRestored(catalog,original,actual.capabilityRuntime(),same,full,known);
                } catch(IOException failure){throw failure;}
                catch(InterruptedException interrupted){
                    Thread.currentThread().interrupt();var failure=new InterruptedIOException("genuine warm constructor verification interrupted");
                    failure.initCause(interrupted);throw failure;
                } catch(Exception failure){throw new IOException("genuine warm constructor verification failed",failure);}
                origin.requireOriginal(same);lease.assertCurrent(same);
                require(context.requireRestoredOrigin(same)==origin&&actual.driver().producer()==producer&&head.equals(same.head().digest()),
                        "actual warm original/read/planning checks changed private custody or canonical head");
                return complete.identity().frame().revision();
            });
        });
    }
    private static void require(boolean condition,String message){if(!condition)throw new AssertionError(message);}
}
