package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.lifecycle.LifecycleChild;
import org.xar.ck3.control.application.session.ContinuityBatchJournal;
import org.xar.ck3.control.application.lifecycle.LifecyclePublication;
import org.xar.ck3.control.application.lifecycle.LifecycleProofCodec;
import org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs;
import org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.application.planning.campaign.M7CheckpointInputs;
import org.xar.ck3.control.continuity.EpisodeWindow;
import org.xar.ck3.control.g2.m7.KernelCheckpointContinuity;

/** Assertions over the sole Root fixture's actual private outputs; never creates a permit, SAVE or fixture. */
public final class M7RootEpisodeChainAssertions {
    private M7RootEpisodeChainAssertions() { }

    /** Same original native DATA producer as the standalone regression; it creates no private Root inputs. */
    public static M7FormalLawNativeFixture.Inputs requireFormalLawNativeDataInputs() throws IOException {
        return M7FormalLawNativeFixture.retainOriginals();
    }

    /** Call at the original pre-import phase, while the current full saved Driver and first pair remain exact. */
    public static void beforeDomainImports(RootEpisodeChainFixture.BeforeImports actual,
            M7CheckpointInputs.Saved actualFirstKernel) throws IOException {
        requireFormalLawNativeDataInputs();
        var same=actual.sameWriter();
        var first=actual.firstCheckpoint();
        var baseline=actual.baseline();
        var binding=actual.baselineBinding();
        var domain=actual.nextProof();
        String head=same.head().digest();
        domain.requireCurrent(same,actual.context());
        baseline.firstVerifier().requireIssued(same,first);
        binding.requireCurrent(same);
        same.requireEpisodeWindowActive(baseline.committedBaseline());
        var material=domain.baselineMaterial();
        material.requirePhysical(same);

        assertSame(actual.begun(),baseline.begun());
        assertSame(first,baseline.firstCheckpoint());
        assertSame(first,binding.firstCheckpoint());
        assertEquals(first.begin(),actual.begun().committedBegin());
        assertEquals(baseline.committedBaseline(),binding.baseline());
        assertEquals(first.baseline(),baseline.committedBaseline().baseline());
        assertEquals(first.pairReference(),baseline.committedBaseline().baseline().pairRef());
        assertEquals(first.pair(),material.pair());
        assertEquals(first.session(),material.session());
        assertEquals(binding.afterOwner(),domain.afterSession());
        assertNotEquals(binding.beforeOwner().game(),binding.afterOwner().game());
        assertArrayEquals(actual.begun().openingBinding().driver().encode(),first.originalDriver().encode());
        assertArrayEquals(first.savedDriver().encode(),binding.driver().encode());
        assertArrayEquals(first.savedDriver().encode(),material.savedDriver().encode());
        assertArrayEquals(first.savedDriver().encode(),domain.firstSavedDriver().encode());
        assertEquals(binding.semantic(),material.sourceSemantic());
        assertEquals(binding.semantic(),domain.savedSemantic());
        assertEquals(M7CheckpointInputs.CheckpointKind.FIRST,actualFirstKernel.kind());
        assertEquals(first.pair(),actualFirstKernel.pair());
        assertEquals(material.firstMaterial().witness(),actualFirstKernel.materialWitness());
        assertEquals(first.originalHeadDigest(),actualFirstKernel.originalHeadDigest());
        actualFirstKernel.observation().ifPresent(observation -> {
            assertEquals(first.session().machineId(),observation.machineId());
            assertEquals(first.session().game().pid(),observation.game().pid());
            assertEquals(first.session().game().creationFiletime().value().toString(),observation.game().creationFiletime());
            assertEquals(first.pair().frame().frame().episodeRunId(),observation.episodeRunId());
            assertEquals(first.pair().frame().frame().identity().player().longValueExact(),observation.actorCharacterId());
            assertEquals(observation,KernelCheckpointContinuity.decodeObservation(KernelCheckpointContinuity.encodeObservation(observation)));
        });
        assertTrue(binding.semantic().observedAt().isAfter(first.canonicalSave().applied().orElseThrow().observation().observedAt()));
        assertEquals(EpisodeWindow.Phase.ACTIVE,EpisodeWindow.state(same.head().state()).orElseThrow().phase());
        assertEquals(0,binding.savedDayCredit());
        assertEquals(0,binding.completedCycleCredit());
        assertEquals(0,actualFirstKernel.savedDayCredit());
        assertEquals(head,same.head().digest());
        // An empty campaign-goal projection grants no CrossRun acceptance; its separate actual reader remains required.
    }

    /** Actual private Binding only: call from the genuine pending-finalization fixture, never mint one here. */
    public static void afterNaturalPendingFinalization(ContinuityStorePort.Session same,
            LifecycleEpisodeInputs producer, LifecycleEpisodeInputs.Binding actual,
            DriverStateSnapshot.Complete actualCausalOriginal, DriverSnapshotFacts.Known actualPublishedFinalBeforeMetadata) throws IOException {
        requireFormalLawNativeDataInputs();
        String head=same.head().digest();
        producer.requireCurrent(same,actual);
        assertInstanceOf(LifecycleTransitionProof.ContinueSuccessor.class,actual.proof());
        ActionReceipt parent=actual.parent();
        var details=actual.publication().detailsObject();
        var delta=details.get("delta");var stamp=details.get("driver_snapshot");
        assertEquals(LifecycleChild.Phase.SUCCESSOR_PENDING_FINALIZED.name(),StrictJson.text(details.get("phase")));
        ExactRef casBefore=ExactRef.fromJson(delta.get("original_driver_ref"));
        ExactRef causal=ExactRef.fromJson(delta.get("causal_original_driver_ref"));
        ExactRef adopted=ExactRef.fromJson(delta.get("adopted_driver_ref"));
        assertEquals(parent.command().lifecycleBefore().evidence().originalDriver(),causal);
        assertEquals(causal,actual.predecessorDriverReference());
        assertEquals(casBefore.sha256(),StrictJson.text(stamp.get("before_sha256")));
        assertEquals(casBefore.sha256(),StrictJson.text(stamp.get("after_sha256")));
        assertEquals(casBefore.sha256(),adopted.sha256());
        assertEquals(stamp.get("expected_epoch"),stamp.get("next_epoch"));
        assertEquals(actualPublishedFinalBeforeMetadata.stamp().driverSha256(),casBefore.sha256());
        assertEquals(actualPublishedFinalBeforeMetadata.stamp().driverVersion(),StrictJson.integer(stamp.get("expected_version"),0,StrictJson.MAX_SAFE_INTEGER));
        assertTrue(actual.driverStamp().driverVersion()>actualPublishedFinalBeforeMetadata.stamp().driverVersion());
        assertEquals(actualPublishedFinalBeforeMetadata.stamp().game(),actual.driverStamp().game());
        assertEquals(actualPublishedFinalBeforeMetadata.stamp().episodeEpoch(),actual.driverStamp().episodeEpoch());
        assertEquals(actualPublishedFinalBeforeMetadata.stamp().episodeEpoch(),StrictJson.integer(stamp.get("next_epoch"),0,StrictJson.MAX_SAFE_INTEGER));
        assertArrayEquals(actualCausalOriginal.encode(),actual.predecessorDriver().encode());
        assertArrayEquals(actualPublishedFinalBeforeMetadata.driver().encode(),actual.driver().encode());
        assertNotEquals(actualCausalOriginal.session().actorId(),actual.driver().session().actorId());
        assertNotEquals(actualCausalOriginal.session().episodeRunId(),actual.driver().session().episodeRunId());
        assertEquals(parent.command().lifecycleBefore().subject().characterId(),actual.predecessorDriver().session().actorId());
        assertEquals(parent.command().lifecycleBefore().subject().episodeRunId(),actual.predecessorDriver().session().episodeRunId());
        assertEquals(actual.beforeOwner(),actual.afterOwner());
        assertEquals(0,actual.savedDayCredit());assertEquals(0,actual.completedCycleCredit());
        assertEquals(head,same.head().digest());
    }
    /** The genuine cold Root/M3 fixture supplies this private proof; DATA alone never enters this seam. */
    public static void afterRecordedNaturalPendingFinalization(ContinuityStorePort.Session same,
            LifecycleEpisodeInputs producer, LifecycleEpisodeInputs.Binding actual,
            DriverStateSnapshot.Complete actualCausalOriginal, DriverSnapshotFacts.Known actualPublishedFinalBeforeMetadata) throws IOException {
        String head=same.head().digest();
        afterNaturalPendingFinalization(same,producer,actual,actualCausalOriginal,actualPublishedFinalBeforeMetadata);
        var publication=assertInstanceOf(LifecyclePublication.RecordedEvent.class,actual.publication());
        var privateProof=assertInstanceOf(LifecycleTransitionProof.ContinueSuccessor.class,actual.proof());
        assertSame(privateProof.publication(),publication);
        assertTrue(publication.warmCommit().isEmpty());
        assertThrows(IllegalStateException.class,actual::commit);
        assertThrows(IllegalStateException.class,privateProof::commit);
        assertEquals(publication.eventSequence(),publication.after().sequence());
        assertEquals(Math.addExact(publication.before().sequence(),1),publication.eventSequence());
        assertEquals(publication.eventIdentity(),actual.commitDigest());
        assertFalse(publication.committedDocuments().isEmpty());
        assertTrue(publication.proofDocuments().containsAll(publication.committedDocuments()));
        for(var pin:publication.proofDocuments()) same.verifyPin(pin);
        byte[] encoded=privateProof.encode();
        var recorded=LifecycleProofCodec.decodeRecorded(encoded);
        recorded.validateParent(actual.parent().command());
        assertFalse(recorded instanceof LifecycleTransitionProof.Base);
        assertEquals(privateProof.originalEvidence(),recorded.originalEvidence());
        assertArrayEquals(encoded,recorded.encode());
        assertArrayEquals(privateProof.encodedResult(),recorded.encodedResult());
        assertArrayEquals(publication.after().canonicalBytes(),same.requireHistoricalState(
                publication.after().sequence(),org.xar.ck3.control.continuity.ContinuityJson.digest(publication.after().toJson())).canonicalBytes());
        assertEquals(head,same.head().digest());
    }
    /**
     * The real late READ/BATCH fixture supplies every private output. Successful current
     * consumption with a later Driver version is the counterexample to reusing an exact-post Base.
     */
    public static void afterAdmittedReadOrBatchCurrent(ContinuityStorePort.Session same,
            LifecycleEpisodeInputs producer, LifecycleEpisodeInputs.CurrentAdoptionBinding current,
            ContinuityBatchJournal actualJournal, ContinuityBatchJournal.AdmittedEpisode actualAdmitted,
            DriverSnapshotFacts.Known actualCurrentKnown) throws IOException {
        // The unchanged Host callback also receives the actual separately issued transport-current role.
        // Its child rechecks the private ticket/source before asserting finalized transport/frontier facts.
        if(current.historical().transportEvidence().isPresent()) {
            afterTransportedCurrent(same,producer,current,actualJournal,actualAdmitted,actualCurrentKnown);
            return;
        }
        requireFormalLawNativeDataInputs();
        String head=same.head().digest();
        producer.requireCurrentAdoption(same,current);
        current.requireCurrent(same);
        current.historical().requireCurrent(same);
        actualJournal.requireHistoricalEpisodeAdoption(same,actualAdmitted);
        assertSame(current.historical().recorded(),current.recorded());
        assertEquals(current.recorded().parent(),current.parent());
        assertEquals(current.owner(),actualAdmitted.owner());
        assertEquals(current.parent(),actualAdmitted.parent());
        assertEquals(current.historical().origin(),actualAdmitted.origin());
        assertFalse(actualAdmitted.newBinding());
        assertEquals(0,actualAdmitted.newSavedDayCredit());
        assertEquals(0,actualAdmitted.newCompletedCycleCredit());
        assertEquals(0,current.savedDayCredit());
        assertEquals(0,current.completedCycleCredit());
        assertEquals(actualCurrentKnown.stamp(),current.driverStamp());
        assertArrayEquals(actualCurrentKnown.driver().encode(),current.driver().encode());
        assertEquals(current.historical().frame().game(),current.semantic().frame().game());
        assertEquals(current.historical().frame().frame().episodeRunId(),current.semantic().frame().frame().episodeRunId());
        assertEquals(current.historical().frame().frame().identity().player(),current.semantic().frame().frame().identity().player());
        assertTrue(current.semantic().frame().frame().identity().dateRaw().compareTo(
                current.historical().frame().frame().identity().dateRaw())>=0);
        var originalStamp=current.recorded().publication().detailsObject().get("driver_snapshot");
        long originalVersion=StrictJson.integer(originalStamp.get("expected_version"),0,StrictJson.MAX_SAFE_INTEGER);
        assertTrue(current.driverStamp().driverVersion()>Math.addExact(originalVersion,1),
                "actual fixture must exercise a legitimate Driver continuation beyond the original exact-post version");
        assertEquals(StrictJson.integer(originalStamp.get("next_epoch"),0,StrictJson.MAX_SAFE_INTEGER),current.driverStamp().episodeEpoch());
        assertTrue(current.writerHeadSequence()>current.historical().admissionSequence());
        byte[] historicalBytes=current.recorded().proof().encode();
        var decoded=LifecycleProofCodec.decodeRecorded(historicalBytes);
        assertFalse(decoded instanceof LifecycleTransitionProof.Base);
        assertArrayEquals(historicalBytes,decoded.encode());
        assertEquals(head,current.writerHeadDigest());
        assertEquals(head,same.head().digest());
    }

    /** The actual NS/M3 held scope and canonical transport producer must supply every private input. */
    public static void afterTransportedCurrent(ContinuityStorePort.Session same,LifecycleEpisodeInputs producer,
            LifecycleEpisodeInputs.CurrentAdoptionBinding current,ContinuityBatchJournal actualJournal,
            ContinuityBatchJournal.AdmittedEpisode actualAdmitted,DriverSnapshotFacts.Known actualCurrentKnown) throws IOException {
        requireFormalLawNativeDataInputs();
        String head=same.head().digest();
        producer.requireCurrentAdoption(same,current);current.requireCurrent(same);current.historical().requireCurrent(same);
        actualJournal.requireHistoricalEpisodeAdoption(same,actualAdmitted);
        var transport=current.historical().transportEvidence().orElseThrow(
                ()->new IOException("MISSING_ACTUAL_TRANSPORT_CURRENT: actual canonical transport ticket is required"));
        assertEquals(org.xar.ck3.control.application.session.SameGameTransportContinuity.Purpose.FINALIZED_METADATA_ONLY,
                transport.purpose());
        assertEquals(transport.afterOwner(),current.owner());
        assertEquals(transport.beforeOwner().machineId(),current.owner().machineId());
        assertEquals(transport.beforeOwner().game(),current.owner().game());
        assertEquals(transport.canonicalParent(),current.recorded().parent());
        assertSame(current.historical().recorded(),current.recorded());
        assertEquals(current.recorded().parent().command().sessionId(),current.parent().command().sessionId());
        assertEquals(current.owner(),actualAdmitted.owner());assertEquals(current.parent(),actualAdmitted.parent());
        assertEquals(current.historical().origin(),actualAdmitted.origin());assertFalse(actualAdmitted.newBinding());
        assertEquals(actualCurrentKnown.stamp(),current.driverStamp());
        assertArrayEquals(actualCurrentKnown.driver().encode(),current.driver().encode());
        assertEquals(current.owner().sessionId(),actualCurrentKnown.observation().orElseThrow().transport().sessionId());
        assertEquals(StrictJson.integer(current.recorded().publication().detailsObject().get("driver_snapshot").get("next_epoch"),
                0,StrictJson.MAX_SAFE_INTEGER),current.driverStamp().episodeEpoch());
        assertThrows(IllegalArgumentException.class,()->producer.bindAdmittedCurrent(same,current.historical(),current.semantic()),
                "the original-session API must still refuse an actual transported ticket");
        var frontier=actualJournal.currentSavedFrontier(same,current.owner(),actualAdmitted.proof());
        assertEquals(frontier.checkpointRequired(),actualAdmitted.checkpointRequired());
        assertEquals(frontier.pair(),actualAdmitted.savedFrontier());
        assertEquals(0,current.savedDayCredit());assertEquals(0,current.completedCycleCredit());
        assertEquals(0,actualAdmitted.newSavedDayCredit());assertEquals(0,actualAdmitted.newCompletedCycleCredit());
        byte[] historicalBytes=current.recorded().proof().encode();
        var recorded=LifecycleProofCodec.decodeRecorded(historicalBytes);
        assertFalse(recorded instanceof LifecycleTransitionProof.Base);assertArrayEquals(historicalBytes,recorded.encode());
        assertEquals(head,current.writerHeadDigest());assertEquals(head,same.head().digest());
    }

}
