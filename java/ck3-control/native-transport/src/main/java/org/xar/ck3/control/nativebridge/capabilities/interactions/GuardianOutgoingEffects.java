package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ordinary.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.effects.family.FamilySendObservation;
import org.xar.ck3.control.application.effects.family.FamilySendObservation.OriginalFrames;
import org.xar.ck3.control.application.effects.family.FamilySendWriterExclusion;
import org.xar.ck3.control.application.planning.family.EducationPayloadMaterializer;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

/** Complete sender-storage difference, linked through original preparation and the one Game writer. */
public final class GuardianOutgoingEffects {
    public static final String SCHEMA="xar.java.family-action-observation/v1";
    public static final String PREPARATION_SCHEMA="xar.java.ordinary-original-preparation/v1";
    private static final String EDUCATE="educate_child_interaction";
    private final PlanningReadPort reads;
    private final ReadContract<OrdinaryContext> query;
    private final OrdinaryClaimDomain claims;
    private final NativeEffectEvidence.FrameLoader frames;
    private final Optional<GuardianReconciliationQueries> reconciliation;
    public GuardianOutgoingEffects(PlanningReadPort actualReads,ReadContract<OrdinaryContext> actualQuery,
            OrdinaryClaimDomain actualClaims,NativeEffectEvidence.FrameLoader actualFrames) {
        reads=Objects.requireNonNull(actualReads); query=Objects.requireNonNull(actualQuery);
        claims=Objects.requireNonNull(actualClaims); frames=Objects.requireNonNull(actualFrames);
        reconciliation=Optional.empty();
        need(query.contractId().equals("interactions:ordinary-query") && query.operation().value().equals(OrdinaryInteractionCodec.QUERY_STEP),"original registered ordinary query required");
    }
    public GuardianOutgoingEffects(PlanningReadPort actualReads,ReadContract<OrdinaryContext> actualQuery,
            OrdinaryClaimDomain actualClaims,NativeEffectEvidence.FrameLoader actualFrames,GuardianReconciliationQueries actualReconciliation) {
        reads=Objects.requireNonNull(actualReads);query=Objects.requireNonNull(actualQuery);
        claims=Objects.requireNonNull(actualClaims);frames=Objects.requireNonNull(actualFrames);
        reconciliation=Optional.of(Objects.requireNonNull(actualReconciliation));
        need(query.contractId().equals("interactions:ordinary-query") && query.operation().value().equals(OrdinaryInteractionCodec.QUERY_STEP),"original registered ordinary query required");
    }
    public static boolean accepts(ActionCommand command) {
        if(!command.operation().value().equals(OrdinaryInteractionCodec.INITIATE_STEP)) return false;
        var intent=OrdinaryInitiationIntent.fromJson(command.arguments());
        return intent.interactionKey().equals(EDUCATE) && intent.education().isPresent()
                && command.expected().observerSchema().equals(SCHEMA);
    }
    /** No native fields are added: these references are durable NativeRequest metadata only. */
    public static List<ExactRef> preservePreparation(ActionCommand command,String requestId,PlanningReadReceipt read,
            OrdinaryOnceClaims.RetainedClaim claim,NativeRequest nativeRequest,Optional<ExactRef> materialization,ActionPorts.OutcomeArchive archive) {
        NativeRecordedEvidenceVerifier.requireRead(read,archive);
        ExactRef readRef=archive.preserveRead(read);
        need(readRef.equals(archive.readReferenceOf(read)),"preparation query archive identity changed");
        need(java.util.Arrays.equals(archive.loadMaterial(claim.original()).bytes(),OrdinaryOnceClaims.encodeClaim(claim.claim())),"same-store original ordinary claim is required");
        materialization.ifPresent(ref->exact(ref,archive.loadMaterial(ref).bytes()));
        var n=F.objectNode().put("schema",PREPARATION_SCHEMA).put("command_body_sha256",ActionCodec.bodySha256(command))
                .put("request_id",requestId).put("prepared_fields_sha256",ActionCodec.sha256(nativeRequest.additionalFields().bytes()));
        n.set("preflight_read",readRef.toJson()); n.set("claim",claim.original().toJson());
        if(materialization.isPresent()) n.set("education_materialization",materialization.orElseThrow().toJson()); else n.putNull("education_materialization");
        ExactRef basis=archive.preserveMaterial(encode(n));
        var closure=new ArrayList<>(List.of(basis,readRef,claim.original())); materialization.ifPresent(closure::add); return List.copyOf(closure);
    }
    public record Preparation(PlanningReadReceipt read,OrdinaryContext context,FamilyOutgoingCodec.Snapshot outgoing,
            OrdinaryOnceClaims.RetainedClaim claim,List<ExactRef> materials) {
        public Preparation { Objects.requireNonNull(read); Objects.requireNonNull(context); Objects.requireNonNull(outgoing); Objects.requireNonNull(claim); materials=List.copyOf(materials); }
    }
    /** The pre-INTENT hook consumes the one successful preparation; it neither queries nor finds a request by name. */
    public Preparation loadCurrentPreparation(ContinuityStorePort.Session same,ActionCommand command,ActionPorts.OutcomeArchive archive) {
        try {
            NativeRequest actual=ActionPreparationScope.requirePrepared(same,command);
            need(!actual.preparationEvidence().isEmpty(),"current education preparation has no original basis");
            ObjectNode basis=parse(archive.loadMaterial(actual.preparationEvidence().getFirst()));
            PlanningReadReceipt read=archive.loadRead(ExactRef.fromJson(field(basis,"preflight_read")));
            var before=RootGuardEvidence.loadFrame(read.before().binding(),archive,frames);
            return loadPreparation(same,command,text(basis,"request_id"),actual,before,archive);
        } catch(IOException failure) { throw new UncheckedIOException("actual same-writer preparation hook unavailable",failure); }
    }
    public NativeEffectRegistry.Projected observe(ContinuityStorePort.Session same,ActionCommand command,ActionState.Attempt attempt,
            NativeActionPort.DispatchOutcome dispatch,OrdinaryInitiationPreparation.ActualFrame before,
            OrdinaryInitiationPreparation.ActualFrame after,ActionPorts.OutcomeArchive archive) {
        if(!accepts(command)) return NativeEffectRegistry.Projected.pending("ordinary interaction lacks this specific independent guardian observer",List.of(after.actual().originalEvidence()));
        if(attempt.preparedRequest().preparationEvidence().isEmpty()) return NativeEffectRegistry.Projected.pending("historical ordinary preparation has no retained original query",List.of(after.actual().originalEvidence()));
        if(!ActionReconciliationScope.activeFor(command)) return NativeEffectRegistry.Projected.pending("typed guardian send requires its canonical pending reconciliation scope",List.of(after.actual().originalEvidence()));
        if(!(dispatch instanceof NativeActionPort.AckReceived ack) || !ack.nativeOk() || ack.custody().isEmpty())
            return NativeEffectRegistry.Projected.pending("family-send v1 retains UNKNOWN until actual response custody is available",List.of(after.actual().originalEvidence()));
        var pair=new OriginalFrames(before.actual(),after.actual());
        Preparation prepared=loadPreparation(same,command,attempt.requestId(),attempt.preparedRequest(),pair.before(),archive);
        need(!prepared.read().before().binding().observedAt().isAfter(attempt.submittedAt()),"guardian original before query was observed after submission");
        if(!outbound(command,attempt,dispatch,before.interaction(),prepared.context())) return NativeEffectRegistry.Projected.pending("original guardian submit packet is unavailable or contradicts queued submission",List.of(after.actual().originalEvidence()));
        GuardianReconciliationQueries.Issued<OrdinaryContext> issued;
        try {
            issued=reconciliation.orElseThrow(()->new IllegalStateException("actual guardian reconciliation query factory is not installed"))
                    .issue(ActionReconciliationScope.requireIdentity(command,attempt),command,attempt,pair.after(),ActionObservationWindow.deadline(command));
        } catch(IOException failure) { throw new UncheckedIOException("actual original guardian pending identity unavailable",failure); }
        ReadContract<OrdinaryContext> actualQuery=issued.contract();
        PlanningReadRequest actualRequest=issued.request();
        var observed=reads.read(same,actualQuery,actualRequest);
        if(!(observed instanceof PlanningReadResult.Known<OrdinaryContext> known)) return NativeEffectRegistry.Projected.pending("independent complete guardian outgoing query unavailable",List.of(after.actual().originalEvidence()));
        verifyReadFrame(known.receipt(),pair.after(),archive,frames);
        NativeEffectSnapshots.requireAfterRead(command,attempt,pair.after(),known.receipt(),query.operation());
        return project(command,attempt,dispatch,pair,prepared,known.receipt(),sameHead(same),archive);
    }
    public Preparation loadPreparation(ContinuityStorePort.Session same,ActionCommand command,String requestId,NativeRequest originalPrepared,org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete actualBefore,ActionPorts.OutcomeArchive archive) {
        need(accepts(command),"this preparation projector requires the exact education action and expected observer");
        need(actualBefore.identity().equals(command.before()) && actualBefore.source().equals(command.source()) && actualBefore.sessionId().equals(command.sessionId())
                && originalPrepared.step().equals(command.operation().value()) && originalPrepared.requiredCapability().equals(Optional.of(OrdinaryInteractionCodec.INITIATE_CAPABILITY)),"original preparation crossed the exact action/frame/source/session/capability");
        List<ExactRef> retained=originalPrepared.preparationEvidence(); need(retained.size()==4,"complete education preparation requires basis, actual query, claim and materialization");
        ObjectNode n=parse(archive.loadMaterial(retained.getFirst()));
        closed(n,"schema","command_body_sha256","request_id","prepared_fields_sha256","preflight_read","claim","education_materialization");
        eq(n,"schema",PREPARATION_SCHEMA); eq(n,"command_body_sha256",ActionCodec.bodySha256(command)); eq(n,"request_id",requestId);
        eq(n,"prepared_fields_sha256",ActionCodec.sha256(originalPrepared.additionalFields().bytes()));
        ExactRef readRef=ExactRef.fromJson(field(n,"preflight_read")),claimRef=ExactRef.fromJson(field(n,"claim")),materialRef=ExactRef.fromJson(field(n,"education_materialization"));
        need(retained.equals(List.of(retained.getFirst(),readRef,claimRef,materialRef)),"preparation metadata differs from its explicit original closure");
        for(var ref:retained) exact(ref,archive.loadMaterial(ref).bytes());
        PlanningReadReceipt read=archive.loadRead(readRef); NativeRecordedEvidenceVerifier.requireRead(read,archive);
        need(archive.readReferenceOf(read).equals(readRef) && !read.requestId().equals(requestId),"original preflight receipt identity changed or borrowed the submit request ID");
        verifyReadFrame(read,actualBefore,archive,frames);
        var c=InteractionArguments.context(read.request()); RootInteractionContextProjection.requireExact(actualBefore,c);
        var intent=OrdinaryInitiationIntent.fromJson(command.arguments()); var request=nativeIntent(intent);
        need(request.equals(InteractionArguments.ordinary(InteractionArguments.parseApp(read.request().arguments()))),"original prepared education intent differs from action body");
        OrdinaryContext context=query.decode(read); need(context.readyToInitiate(),"original preparation was not legally ready");
        var claim=claims.requireClaim(same,requestId);
        need(claim.original().equals(claimRef) && java.util.Arrays.equals(archive.loadMaterial(claimRef).bytes(),OrdinaryOnceClaims.encodeClaim(claim.claim())),"original writer claim differs from preparation");
        var identity=claim.claim().request().identity(); var binding=claim.claim().request().binding();
        need(identity.machineId().equals(command.before().machineId()) && identity.gamePid()==command.before().game().pid()
                && identity.creationFiletimeDecimal().equals(command.before().game().creationFiletime().value().toString())
                && identity.actorId()==c.actor().longValueExact() && identity.interactionKey().equals(intent.interactionKey()) && identity.recipientId()==intent.recipientId()
                && binding.snapshotId().equals(c.before().frame().snapshotId()) && binding.publicRevisionDecimal().equals(c.before().frame().revision().toString())
                && binding.nativeRevisionDecimal().equals(c.revision().toString()) && binding.dateRawDecimal().equals(c.date().toString())
                && binding.connectionGenerationDecimal().equals(c.connectionGeneration().toString()) && binding.episodeRunId().equals(c.before().frame().episodeRunId()),"durable original claim crossed Game, roles, source frame or connection");
        var education=intent.education().orElseThrow();
        var material=EducationPayloadMaterializer.prepareAndMaterialize(requestId,OrdinaryInitiationPreparation.publicQuery(read.original().originalResultToken().orElseThrow(),c),
                actualBefore.semantic(),intent.recipientId(),education.childId(),education.guardianId(),education.optionKeys());
        need(new RawJson(DriverJson.encode(material.projection())).equals(archive.loadMaterial(materialRef)),"archived prepared materialization differs from actual original query and full Driver");
        need(originalPrepared.additionalFields().equals(OrdinaryInteractionCodec.request(c,request,true)),"retained native wire fields differ from original prepared education");
        return new Preparation(read,context,GuardianOutgoingCodec.decodeReceipt(read),claim,List.of(retained.getFirst(),claimRef,materialRef));
    }
    private static NativeEffectRegistry.Projected project(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch,
            OriginalFrames pair,Preparation prepared,PlanningReadReceipt afterRead,WriterContracts.Head head,ActionPorts.OutcomeArchive archive) {
        if(!(dispatch instanceof NativeActionPort.AckReceived ack) || !ack.nativeOk() || ack.custody().isEmpty())
            return NativeEffectRegistry.Projected.pending("family-send v1 cannot synthesize original ACK custody for UNKNOWN",List.of(pair.after().originalEvidence()));
        var beforeContext=InteractionArguments.context(prepared.read().request()); var afterContext=InteractionArguments.context(afterRead.request());
        requireChronology(prepared.read(),afterRead,attempt,dispatch);
        RootInteractionContextProjection.requireExact(pair.before(),beforeContext); RootInteractionContextProjection.requireExact(pair.after(),afterContext);
        need(beforeContext.build()==Build.CROZIER4 && afterContext.build()==Build.CROZIER4 && beforeContext.date().equals(afterContext.date())
                && beforeContext.controls().paused() && afterContext.controls().paused() && afterContext.controls().alive() && afterContext.controls().mapReady(),"guardian effect requires the same paused actual4 day");
        if(!outbound(command,attempt,dispatch,beforeContext,prepared.context())) return NativeEffectRegistry.Projected.pending("original guardian submission is unbound",List.of(pair.after().originalEvidence()));
        var after=GuardianOutgoingCodec.decodeReceipt(afterRead);
        OptionalLong pending=match(prepared.context(),prepared.outgoing(),after);
        if(pending.isEmpty() || !FamilySendWriterExclusion.exclusive(head,command,attempt,prepared.read(),afterRead,pair,archive)) return NativeEffectRegistry.Projected.pending("guardian outgoing difference is absent, incomplete, ambiguous or crossed another Game submission",List.of(pair.after().originalEvidence()));
        var intent=OrdinaryInitiationIntent.fromJson(command.arguments()); var education=intent.education().orElseThrow();
        var observation=new FamilySendObservation(FamilySendObservation.Profile.GUARDIAN,command.actionId(),ActionCodec.bodySha256(command),
                attempt.requestId(),archive.referenceOf(dispatch),archive.requestReferenceOf(attempt.preparedRequest()),
                NativeEffectEvidence.basis(pair.before()),NativeEffectEvidence.basis(pair.after()),
                pair.before().identity(),pair.after().identity(),command.source(),command.sessionId(),prepared.read(),afterRead,
                attempt.preparedRequest().preparationEvidence(),pending.getAsLong(),prepared.context().terms().definitionHash(),
                FamilySendObservation.sendOnlyValues(FamilySendObservation.Profile.GUARDIAN,education.childId(),education.guardianId(),pending.getAsLong()));
        observation.validate(command,attempt,dispatch,archive);
        return new NativeEffectRegistry.Projected(new ActionPorts.FamilySendObserved(observation),Optional.empty());
    }
    /** Complete exact-role and raw authored-bank matching. Pending identity is never a host action ID. */
    public static OptionalLong match(OrdinaryContext prepared,FamilyOutgoingCodec.Snapshot before,FamilyOutgoingCodec.Snapshot after) {
        if(before.profile()!=FamilyOutgoingCodec.Profile.EDUCATE_CHILD || after.profile()!=FamilyOutgoingCodec.Profile.EDUCATE_CHILD || !before.complete() || !after.complete() || prepared.roles().sixth()!=null || prepared.educationOptions().isEmpty()
                || !prepared.educationOptions().orElseThrow().availability().available() || prepared.terms()==null) return OptionalLong.empty();
        need(prepared.frame().equals(before.frame()),"prepared authored roles/options do not belong to the original before query");
        need(before.frame().build()==Build.CROZIER4 && after.frame().build()==Build.CROZIER4 && before.frame().actor().equals(after.frame().actor())
                && before.frame().date().equals(after.frame().date()) && after.frame().revision().compareTo(before.frame().revision())>=0
                && after.frame().querySequence().compareTo(before.frame().querySequence())>0,"guardian storage lacks a distinct later same-day native query");
        long hash=prepared.terms().definitionHash();
        if(before.definitionHash().isEmpty() || after.definitionHash().isEmpty() || before.definitionHash().getAsLong()!=hash || after.definitionHash().getAsLong()!=hash) return OptionalLong.empty();
        var r=prepared.roles(); var roles=new FamilyOutgoingCodec.Roles(r.actor(),r.recipient(),r.secondaryActor(),r.secondaryRecipient(),r.intermediary());
        var options=new ArrayList<FamilyOutgoingCodec.OptionRow>();
        if(prepared.educationOptions().orElseThrow().rows().size()>4096) return OptionalLong.empty();
        for(var row:prepared.educationOptions().orElseThrow().rows()) {
            if(row.bankByte()<0 || row.bankByte()>1 || row.ordinal()!=options.size()) return OptionalLong.empty();
            options.add(new FamilyOutgoingCodec.OptionRow(row.ordinal(),row.flag(),row.bankByte()));
        }
        java.util.function.Predicate<FamilyOutgoingCodec.Candidate> exact=row->row.definitionHash()==hash && row.roles().equals(roles) && row.options().equals(options);
        if(before.candidates().stream().anyMatch(exact)) return OptionalLong.empty();
        var matching=after.candidates().stream().filter(exact).toList();
        if(matching.size()!=1 || !matching.getFirst().knownActiveRoute() || before.occupiedPendingIds().contains(matching.getFirst().pendingFullId())) return OptionalLong.empty();
        return OptionalLong.of(matching.getFirst().pendingFullId());
    }
    private static boolean outbound(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch,Context before,OrdinaryContext prepared) {
        byte[] bytes;
        if(dispatch instanceof NativeActionPort.AckReceived ack) {
            if(!ack.nativeOk() || ack.outbound().isEmpty() || ack.originalResultToken().isEmpty()) return false;
            var receipt=OrdinaryInteractionCodec.initiation(ack.originalResultToken().orElseThrow(),before,nativeIntent(OrdinaryInitiationIntent.fromJson(command.arguments())));
            if(!receipt.queueSubmitted() || !receipt.preflight().roles().equals(prepared.roles()) || !receipt.preflight().educationOptions().equals(prepared.educationOptions())) return false;
            bytes=ack.outbound().orElseThrow().originalPacket();
        } else if(dispatch instanceof NativeActionPort.Unknown unknown) bytes=unknown.originalRequestPacket(); else return false;
        if(bytes.length==0) return false;
        try {
            var wire=NativeWire.decodeExecuteRequest(bytes);
            need(wire.requestId().equals(attempt.requestId()) && wire.step().equals(command.operation().value())
                    && wire.expectedRevision().equals(Optional.of(command.before().frame().identity().nativeRevision()))
                    && wire.expectedSnapshotRevision().isEmpty()
                    && new RawJson(wire.normalizedAdditionalFields().value()).equals(attempt.preparedRequest().additionalFields()),"original guardian outbound packet differs from the durable prepared request");
            return true;
        } catch(IOException failure) { throw new UncheckedIOException("original guardian submit packet is malformed",failure); }
    }
    public NativeRecordedEvidenceVerifier.Binding archivedVerifier(ExactRef actualSource,Supplier<ContinuityStorePort.Session> current) {
        return new NativeRecordedEvidenceVerifier.Binding(new OperationKey(OrdinaryInteractionCodec.INITIATE_STEP),actualSource,(head,receipt,archive)-> {
            need(accepts(receipt.command()),"this recorded ordinary binding only proves exact guardian requests");
            var same=Objects.requireNonNull(current.get()); need(sameHead(same).digest().equals(head.digest()),"guardian replay requires the actual same writer head");
            need(receipt.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.FamilySendConfirmed,
                    "guardian sender archive requires its dedicated typed send settlement");
            var settled=(ActionState.Settled)receipt.state();
            var observed=((ActionState.FamilySendConfirmed)settled.settlement()).observation();
            need(observed.profile()==FamilySendObservation.Profile.GUARDIAN,"guardian sender archive borrowed another domain profile");
            observed.validate(receipt.command(),settled.attempt(),settled.dispatch(),archive);
            var original=observed.loadFrames(archive,frames);
            Preparation prep=loadPreparation(same,receipt.command(),settled.attempt().requestId(),settled.attempt().preparedRequest(),original.before(),archive);
            need(!prep.read().before().binding().observedAt().isAfter(settled.attempt().submittedAt()),"archived guardian before query was observed after submission");
            need(observed.beforeStorage().equals(prep.read()),"guardian original before query changed");
            PlanningReadReceipt after=observed.afterStorage(); verifyReadFrame(after,original.after(),archive,frames);
            reconciliation.orElseThrow(()->new IllegalStateException("actual guardian original query profile is not installed for archival replay"))
                    .contract().replay(after);
            NativeEffectSnapshots.requireAfterRead(receipt.command(),settled.attempt(),original.after(),after,query.operation());
            var replayed=project(receipt.command(),settled.attempt(),settled.dispatch(),original,prep,after,head,archive);
            need(replayed.result() instanceof ActionPorts.FamilySendObserved send && send.observation().equals(observed)
                    && replayed.compatibleResult().isEmpty(),"archived guardian send differs from full original domain replay");
        });
    }
    private static void verifyReadFrame(PlanningReadReceipt read,org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete actual,ActionPorts.OutcomeArchive archive,NativeEffectEvidence.FrameLoader frames) {
        NativeRecordedEvidenceVerifier.requireRead(read,archive);
        boolean reconciliation=read.request().origin() instanceof CommandOrigin.Reconciliation;
        need((reconciliation?read.request().reconciliationBefore():read.request().before()).equals(actual.identity())
                && read.request().source().equals(actual.source()) && read.request().sessionId().equals(actual.sessionId()),"guardian query original frame/source/session changed");
        for(var guard:List.of(read.before(),read.after())) {
            org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete rebuilt;
            String binding;
            if(reconciliation) {
                var identity=read.request().origin().requireReconciliation();
                need(guard.binding().origin() instanceof CommandOrigin.Reconciliation
                        && guard.binding().origin().requireReconciliation().sameGuardFrame(identity),"guardian query guard changed its actual pending identity");
                rebuilt=frames.load(new NativeEffectEvidence.FrameBasis(identity.nativeEvidence(),identity.evidence().observationManifest()),archive);
                binding=identity.bindingSha256();
            } else { rebuilt=RootGuardEvidence.loadFrame(guard.binding(),archive,frames);binding=actual.fullBindingSha256(); }
            need(NativeEffectEvidence.basis(rebuilt).equals(NativeEffectEvidence.basis(actual)) && rebuilt.fullBindingSha256().equals(actual.fullBindingSha256())
                    && guard.originalBindingSha256().equals(binding),"guardian read guard is not the exact original full Driver/native frame");
        }
    }
    private static void requireChronology(PlanningReadReceipt before,PlanningReadReceipt after,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch) {
        var first=before.original().custody().orElseThrow(()->new IllegalArgumentException("original guardian preparation query has no actual chronology"));
        var last=after.original().custody().orElseThrow(()->new IllegalArgumentException("guardian after query has no actual chronology"));
        first.verify(before);last.verify(after);
        need(first.session().equals(last.session()) && first.custodyEpoch().equals(last.custodyEpoch())
                && last.writeEntered().order().compareTo(first.responseReceived().order())>0
                && !last.writeEntered().observedAt().isBefore(attempt.submittedAt()),"guardian query chronology crossed the actual endpoint or original submission");
        if(dispatch instanceof NativeActionPort.AckReceived ack) {
            NativeRequestChronology.requireBeforeSubmission(before,attempt,ack);
            NativeRequestChronology.requireSampledAfter(after,attempt,ack);
        } else need(dispatch instanceof NativeActionPort.Unknown,"guardian effect has no original submitted dispatch");
    }
    private static WriterContracts.Head sameHead(ContinuityStorePort.Session same) { try { return same.head(); } catch(IOException e) { throw new UncheckedIOException(e); } }
    static OrdinaryRequest nativeIntent(OrdinaryInitiationIntent intent) {
        return new OrdinaryRequest(new InteractionKey(intent.interactionKey()),new CharacterId(intent.recipientId()),intent.education().map(e->new EducationIntent(Optional.of(new CharacterId(e.childId())),Optional.of(new CharacterId(e.guardianId())),Optional.of(e.optionKeys().stream().map(InteractionKey::new).toList()))));
    }
    private static void exact(ExactRef ref,byte[] raw) { need(ref.bytes()==raw.length && ref.sha256().equals(ActionCodec.sha256(raw)),"original guardian material bytes changed"); }
}

