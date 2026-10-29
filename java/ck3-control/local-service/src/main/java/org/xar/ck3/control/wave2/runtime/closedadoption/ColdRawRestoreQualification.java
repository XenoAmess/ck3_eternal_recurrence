package org.xar.ck3.control.wave2.runtime.closedadoption;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Optional;
import java.util.UUID;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import org.xar.ck3.control.wave2.runtime.savedproof.ColdRestoreMeasurement;
import org.xar.ck3.control.wave2.runtime.savedproof.SavedCheckpointMeasurementCoordinator;
import org.xar.ck3.control.wave2.runtime.savedproof.SavedProofReadTicket;
import org.xar.ck3.control.wave2.runtime.savedproof.WindowsSavedProofIdentityReader;

/** Actual post-HELLO producer: an independent new Root read release, new SDK worker and new Root review. */
final class ColdRawRestoreQualification {
    private final Thread thread=Thread.currentThread();
    private final ClosedInputsSessionAuthority authority;
    private final RootColdResumeSession session;
    private final int preparedSequence;
    private final RootColdResumeSession.RawColdFrame frame;
    private final SavedCheckpointMeasurementCoordinator measured;
    private final SavedProofReadTicket ticket;
    private final FileStatIdentity releaseIdentity;
    private final RecoveryEvidence readRequest;
    private final FileStatIdentity requestIdentity;
    private final RootColdStageReview.Reviewed reviewed;
    private final RawRestoreAdmissionReducer.Preview preview;
    private final Optional<RootColdResumeSession.CapabilitiesCompletion> capabilities;
    private ColdRawRestoreQualification(ClosedInputsSessionAuthority authority,RootColdResumeSession session,int sequence,
            RootColdResumeSession.RawColdFrame frame,SavedCheckpointMeasurementCoordinator measured,
            SavedProofReadTicket ticket,FileStatIdentity releaseIdentity,RootColdStageReview.Reviewed reviewed,
            RawRestoreAdmissionReducer.Preview preview,Optional<RootColdResumeSession.CapabilitiesCompletion> capabilities,RecoveryEvidence readRequest,FileStatIdentity requestIdentity) {
        this.authority=authority;this.session=session;this.preparedSequence=sequence;this.frame=frame;
        this.measured=measured;this.ticket=ticket;this.releaseIdentity=releaseIdentity;this.reviewed=reviewed;this.preview=preview;this.capabilities=capabilities;this.readRequest=readRequest;this.requestIdentity=requestIdentity;
    }
    static ColdRawRestoreQualification begin(ClosedInputsSessionAuthority authority,RootColdResumeSession session,int sequence,
            RootColdResumeSession.RawColdFrame frame,OriginalWriterTransaction.RetainedSession retained) throws IOException,InterruptedException {
        return beginPhase(authority,session,sequence,frame,retained,Optional.empty(),Optional.empty(),session.actualInjectionCompletedAt(),"RAW-RESTORE",RootColdStageReview.Stage.RAW_PREFLIGHT);
    }
    static ColdRawRestoreQualification beginCapabilities(ClosedInputsSessionAuthority authority,RootColdResumeSession session,int sequence,
            RootColdResumeSession.CapabilitiesCompletion actual,OriginalWriterTransaction.RetainedSession retained,
            ColdRawRestoreQualification bootstrap) throws IOException,InterruptedException {
        StrictJson.require(bootstrap.session==session && bootstrap.reviewed.consumed() && bootstrap.capabilities.isEmpty(),"same actual once bootstrap preview before fresh capabilities poststate qualification");
        StrictJson.require(bootstrap.frame.equals(session.retainedRawFrame()),"same actual consumed raw ticket frame");
        return beginPhase(authority,session,sequence,bootstrap.frame,retained,Optional.of(actual),Optional.of(bootstrap.ticket.nonce()),session.actualCapabilitiesCompletedAt(),"POST-CAP",RootColdStageReview.Stage.CAPABILITIES_POSTSTATE);
    }
    private static ColdRawRestoreQualification beginPhase(ClosedInputsSessionAuthority authority,RootColdResumeSession session,int sequence,
            RootColdResumeSession.RawColdFrame frame,OriginalWriterTransaction.RetainedSession retained,
            Optional<RootColdResumeSession.CapabilitiesCompletion> capabilities,Optional<String> previousReadNonce,Instant after,String stem,RootColdStageReview.Stage stage)
            throws IOException,InterruptedException {
        SavedProofReadTicket original=retained.originalReadTicket();
        authority.requireNativeOwnerInputs(sequence); session.requireCurrent();
        Path directory=session.ownedDirectory(),release=directory.resolve(stem+"-SDK-READ-TICKET.json");
        StrictJson.require(!Files.exists(release,LinkOption.NOFOLLOW_LINKS),"new post-HELLO Root read release must follow this actual raw challenge");
        var requested=StrictJson.object();requested.put("schema","xar.root-post-hello-read-request/v1");
        Instant requestedAt=Instant.now();
        requested.put("machine_id",authority.machineId());requested.put("created_at_utc",requestedAt.toString());
        requested.put("read_boundary_utc",after.toString());requested.put("stage",stage.name());
        capabilities.ifPresent(value->requested.set("actual_capabilities_completion",value.toJson()));
        requested.put("deadline_utc",authority.deadline().toString());requested.put("new_read_ticket_path",release.toString());
        requested.set("original_read_ticket_ref",original.release().reference().toJson());
        requested.set("basis_ref",authority.basisRef().toJson());requested.set("raw_frame",frame.toJson());
        requested.put("scope","NEW_ROOT_SINGLE_DRIVER_READ_AND_ORIGINAL_SDK_SAVE_HASH_THEN_INDEPENDENT_REVIEW");
        var readRequest=publish(directory.resolve(stem+"-SDK-READ-REQUEST.json"),StrictJson.canonical(requested));
        var requestIdentity=new WindowsSavedProofIdentityReader().stat(Path.of(readRequest.reference().path()));
        while (!Files.exists(release,LinkOption.NOFOLLOW_LINKS)) {
            authority.requireNativeOwnerInputs(sequence);session.requireCurrent();Thread.sleep(100);
        }
        var identities=new WindowsSavedProofIdentityReader();FileStatIdentity releaseIdentity=identities.stat(release);
        RecoveryEvidence releaseEvidence=read(release);StrictJson.require(releaseIdentity.equals(identities.stat(release)),"new Root release native identity");
        SavedProofReadTicket ticket=SavedProofReadTicket.parse(releaseEvidence);
        StrictJson.require(previousReadNonce.isEmpty() || !ticket.nonce().equals(previousReadNonce.orElseThrow()),"post-CAP read uses a distinct new Root nonce");
        validateNewTicket(original,ticket,after.isAfter(requestedAt)?after:requestedAt,authority.deadline(),directory,Instant.now(),stem);
        // This default coordinator runs the actual fixed frozen-SDK worker. No injectable runner or JSON proof loader.
        var measured=retained.newColdRestoreMeasurementCoordinator();ColdRestoreMeasurement result=measured.measureColdRestoreOnce(ticket);
        var preview=RawRestoreAdmissionReducer.preview(session.restoreInputs().basis(),result.checkpoint().canonicalReceipt(),
                result.lineage(),result.checkpoint().driverIdentity(),frame);
        if(capabilities.isPresent()){requirePostCapabilities(preview);}
        var raw=publish(directory.resolve(stem+"-PREVIEW.json"),previewJson(authority,frame,result,preview,capabilities));
        var spec=session.nativeOwnerSession().ownedStdio().spec();
        var pins=new ArrayList<ExactRef>();
        spec.programSourceRefs().forEach(ref->pins.add(new ExactRef(ref.path(),ref.bytes(),ref.sha256())));
        pins.add(readRequest.reference());pins.add(ticket.release().reference());pins.add(result.checkpoint().canonicalCheckpointProof());
        pins.add(result.checkpoint().originalTransportObservation().reference());pins.add(raw.reference());
        Instant deadline=ticket.reviewAt().isBefore(spec.deadline())?ticket.reviewAt():spec.deadline();
        var command=new RootColdStageReview.PlannedCommand(spec.command(),
                new ExactRef(spec.executableRef().path(),spec.executableRef().bytes(),spec.executableRef().sha256()),pins,deadline);
        var challenge=RootColdStageReview.create(authority,sequence,directory,UUID.randomUUID().toString().replace("-",""),
                stage,command,Optional.of(session.heldGame().identity()));
        RootColdStageReview.Reviewed reviewed;
        while (true) {
            measured.requireCurrentColdRestoreCached();session.requireCurrent();
            var actual=RootColdStageReview.poll(challenge);if(actual.isPresent()){reviewed=actual.orElseThrow();break;}
            Thread.sleep(100);
        }
        var context=new ColdRawRestoreQualification(authority,session,sequence,frame,measured,ticket,releaseIdentity,reviewed,preview,capabilities,readRequest,requestIdentity);
        context.requireCurrent();return context;
    }
    static void validateNewTicket(SavedProofReadTicket original,SavedProofReadTicket next,Instant injected,
            Instant authorityDeadline,Path directory,Instant now) {
        validateNewTicket(original,next,injected,authorityDeadline,directory,now,"RAW-RESTORE");
    }
    private static void validateNewTicket(SavedProofReadTicket original,SavedProofReadTicket next,Instant injected,
            Instant authorityDeadline,Path directory,Instant now,String stem) {
        StrictJson.require(!next.nonce().equals(original.nonce()) && !next.release().reference().equals(original.release().reference())
                && !next.observedAt().isBefore(injected) && !next.observedAt().isAfter(now) && now.isBefore(next.reviewAt())
                && !next.reviewAt().isAfter(authorityDeadline),"genuine new Root read release after actual injector/HELLO boundary within the original authority");
        StrictJson.require(next.machineId().equals(original.machineId()) && next.driverPath().equals(original.driverPath())
                && next.save().equals(original.save()) && next.saveIdentity().equals(original.saveIdentity())
                && next.sdkRoot().equals(original.sdkRoot()) && next.sdkFreeze().equals(original.sdkFreeze())
                && next.validatorSource().equals(original.validatorSource()) && next.pipeName().equals(original.pipeName())
                && next.pythonExecutable().equals(original.pythonExecutable()),"same original source/SAVE/pipe/interpreter tuple with freshly measured current Driver identity");
        StrictJson.require(next.outputRoot().equals(directory.resolve("raw-sdk-"+next.nonce()))
                && next.release().reference().path().equals(directory.resolve(stem+"-SDK-READ-TICKET.json").toString()),
                "fresh Root-owned bounded read ticket and SDK output child");
    }
    RawRestoreAdmissionReducer.Preview requireCurrent() throws IOException {
        StrictJson.require(Thread.currentThread()==thread,"same actual post-HELLO measurement thread");
        authority.requireNativeOwnerInputs(preparedSequence);session.requireCurrent();reviewed.requireCurrent();
        var identities=new WindowsSavedProofIdentityReader();
        StrictJson.require(releaseIdentity.equals(identities.stat(Path.of(ticket.release().reference().path())))
                && java.util.Arrays.equals(read(Path.of(ticket.release().reference().path())).bytes(),ticket.release().bytes()),
                "actual new Root read release retains its exact bytes/native identity");
        StrictJson.require(requestIdentity.equals(identities.stat(Path.of(readRequest.reference().path())))
                && read(Path.of(readRequest.reference().path())).reference().equals(readRequest.reference()),"actual independent read request retains its exact bytes and native identity");
        var current=measured.requireCurrentColdRestoreCached();
        var fresh=RawRestoreAdmissionReducer.preview(session.restoreInputs().basis(),current.checkpoint().canonicalReceipt(),
                current.lineage(),current.checkpoint().driverIdentity(),frame);
        if(capabilities.isPresent()) {
            requirePostCapabilities(fresh);var actual=capabilities.orElseThrow();
            StrictJson.require(actual.owner().equals(session.nativeOwnerSession().ownedStdio().identity())
                    && actual.game().equals(session.heldGame().identity()) && actual.pipeName().equals(frame.pipeName())
                    && actual.connectionGeneration().equals(frame.connectionGeneration()),"same actual capabilities completion owner/Game/pipe/generation");
        }
        StrictJson.require(fresh.equals(preview),"same actual independent reducer preview before its once ticket consumption");return fresh;
    }
    void consumeReviewInsideLock() throws IOException { requireCurrent();reviewed.consumeImmediatelyBeforeSubmission(); }
    ExactRef approvalRef() { return reviewed.approvalRef(); }
    void requireTicket(RootColdResumeSession actual,RootColdResumeSession.RawColdFrame raw,ExactRef approval) throws IOException {
        StrictJson.require(capabilities.isEmpty() && actual==session && frame.equals(raw) && reviewed.consumed() && approval.equals(reviewed.approvalRef()),
                "exact private actual raw qualification and original locked Root review"); requireCurrent();
    }
    void requireCapabilitiesTicket(RootColdResumeSession actual,RootColdResumeSession.CapabilitiesCompletion completed,ExactRef approval) throws IOException {
        StrictJson.require(actual==session && capabilities.orElseThrow().equals(completed) && reviewed.consumed()
                && approval.equals(reviewed.approvalRef()),"exact private capabilities poststate context and original locked independent Root review");requireCurrent();
    }
    private static void requirePostCapabilities(RawRestoreAdmissionReducer.Preview preview) {
        StrictJson.require(preview.branch()==RawRestoreAdmissionReducer.DriverBranch.ACTUAL_CURRENT_GAME_HEADER,
                "post-CAP actual Driver header must name the held current Game while preserving the original episode/checkpoint");
    }
    private static byte[] previewJson(ClosedInputsSessionAuthority authority,RootColdResumeSession.RawColdFrame frame,
            ColdRestoreMeasurement measurement,RawRestoreAdmissionReducer.Preview preview,Optional<RootColdResumeSession.CapabilitiesCompletion> capabilities) {
        var value=StrictJson.object();value.put("schema","xar.root-post-hello-raw-preview/v1");value.put("machine_id",authority.machineId());
        value.put("observed_at_utc",Instant.now().toString());value.set("basis_ref",authority.basisRef().toJson());
        value.set("actual_measurement_ref",measurement.checkpoint().canonicalCheckpointProof().toJson());
        value.set("actual_transport_ref",measurement.checkpoint().originalTransportObservation().reference().toJson());
        capabilities.ifPresent(actual->value.set("actual_capabilities_completion",actual.toJson()));
        value.set("driver_lineage",measurement.lineage().toJson());value.set("raw_frame",frame.toJson());value.put("driver_branch",preview.branch().name());
        value.put("old_episode_run_id",preview.episodeRunId());value.put("saved_date_raw",preview.savedDateRaw());
        value.put("elapsed_game_days_from_original_T0",preview.elapsedGameDays());value.put("new_game_day_credit",0);
        value.put("new_ordinary_cycle_credit",0);value.put("grants_warm_attachment",false);value.put("original_actions_replayed",false);
        return StrictJson.canonical(value);
    }
    private static RecoveryEvidence publish(Path path,byte[] bytes) throws IOException {
        Files.write(path,bytes,StandardOpenOption.CREATE_NEW);RecoveryEvidence result=read(path);
        StrictJson.require(java.util.Arrays.equals(result.bytes(),bytes),"complete create-new metadata publication");return result;
    }
    private static RecoveryEvidence read(Path path) throws IOException {
        String name=path.toString().replace('\\','/').toLowerCase(java.util.Locale.ROOT);
        StrictJson.require(!name.endsWith("/driver-state.json") && !name.endsWith(".ck3") && !name.endsWith(".sav"),"small Root metadata only");
        var identities=new WindowsSavedProofIdentityReader();var before=identities.stat(path);
        StrictJson.require(before.bytes().signum()>0 && before.bytes().longValueExact()<=RecoveryEvidence.MAX_BYTES,"finite actual Root metadata");
        byte[] bytes;try(var input=Files.newInputStream(path)){bytes=input.readNBytes(RecoveryEvidence.MAX_BYTES+1);}
        StrictJson.require(bytes.length==before.bytes().longValueExact() && before.equals(identities.stat(path)),"stable complete native metadata identity");
        return new RecoveryEvidence(new ExactRef(path.toString(),bytes.length,RecoveryEvidence.sha256(bytes)),bytes);
    }
}
