package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.planning.finance.FinanceStatePort;
import org.xar.ck3.control.application.planning.governance.*;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityPayload;
import org.xar.ck3.control.planning.optionalcadence.*;

/** One NEXT/FIRST-restore producer shared by the existing three registrations. Retained input is data; only Core's private proof authorizes an import. */
public final class GovernanceNextInitialization implements DomainBodies.Verifier {
    public static final String SCHEMA=GovernanceDomainInitializationInput.SCHEMA;
    private record Planned(GovernanceDomainInitializationInput input,byte[] body) {Planned {body=body.clone();}@Override public byte[] body(){return body.clone();}}
    private final RootRuntimeContext context;private final GovernanceActivityRuntime activity;private final FeastDomainRuntime feast;
    private final List<DomainBodies.Registration> registrations;
    private RootApplicationAssembly.EpisodeDomainInitializationProof authority;private ExactRef authorizedHosted;private Optional<ExactRef> authorizedSourceProof;private boolean entered;
    private RootNextEpisodeDomainReads.Captured<ActivityNativeContracts.Packet> authorizedCapture;
    GovernanceNextInitialization(RootRuntimeContext context,GovernanceActivityRuntime activity,FeastDomainRuntime feast,
            DomainBodies.Registration opening,DomainBodies.Registration feastRegistration,DomainBodies.Registration cadence) {
        this.context=Objects.requireNonNull(context);this.activity=Objects.requireNonNull(activity);this.feast=Objects.requireNonNull(feast);
        registrations=List.of(opening,feastRegistration,cadence);
        StrictJson.require(opening.slot()==DomainBodies.Slot.OPENING_GATE&&feastRegistration.slot()==DomainBodies.Slot.FEAST&&cadence.slot()==DomainBodies.Slot.OPTIONAL_CADENCE,
                "the actual unique three governance registrations are required");
    }
    public List<DomainBodies.BodyRef> initializeNext(ContinuityStorePort.Session same,RootApplicationAssembly.EpisodeDomainInitializationProof proof)throws IOException {
        context.writer().requireSession(same);Objects.requireNonNull(proof).requireCurrent(same,context);
        context.game().launchPlan().sources().requireLoadedClass(GovernanceNextInitialization.class);
        context.game().launchPlan().sources().requireLoadedClass(GovernanceDomainInitializationInput.class);
        if(entered)throw new IOException("NEXT governance initialization was already entered; inspect canonical originals before any retry");
        // Core's separate candidate-only route preserves the actual native receipt without ledger READ/history publication.
        var contract=activity.definitions().contract(ActivityNativeContracts.Query.HOSTED);
        StrictJson.require(contract.hasPureReplay(),"INCOMPLETE_NEXT_GOVERNANCE: actual HOSTED pure replay is not installed");
        var captured=proof.read(same,context,contract,
                new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(java.util.Map.of()),proof.deadline());
        var observed=captured.result();
        if(observed instanceof PlanningReadResult.Unavailable<ActivityNativeContracts.Packet> missing)throw new IOException("INCOMPLETE_NEXT_GOVERNANCE: new-player HOSTED unavailable: "+missing.reason());
        captured.requireOriginals(same,context,proof);
        var known=(PlanningReadResult.Known<ActivityNativeContracts.Packet>)observed;var archive=context.archive().withSession(same);
        StrictJson.require(known.receipt().equals(known.value().receipt())&&archive.readReferenceOf(known.receipt()).equals(known.originalReceipt()),"NEXT HOSTED packet lost its actual archived original");
        StrictJson.require(captured.frame().identity().equals(captured.semantic().frame())&&known.receipt().request().before().equals(captured.semantic().frame())
                &&captured.frame().source().equals(proof.source())&&captured.frame().sessionId().equals(proof.afterSession().sessionId()),
                "NEXT hosted capture does not retain its actual new-player semantic/frame source");
        ExactRef hostedRef=known.originalReceipt();var plans=new ArrayList<Planned>();
        for(var registration:registrations) {
            var body=available(same,registration.slot());var input=new GovernanceDomainInitializationInput(proof.kind(),body.reference(),proof.oldDomain(registration.slot()),
                    proof.baselineMaterial().witness(),proof.baselineMaterial().pair(),proof.baselineMaterial().session(),proof.savedSemantic(),
                    proof.currentSemantic(),hostedRef,captured.semantic(),captured.sourceProof(),proof.beforeSession(),proof.afterSession(),proof.source(),
                    proof.initializationHeadSequence(),proof.initializationHeadDigest());
            plans.add(new Planned(input,replay(same,input)));proof.requireCurrent(same,context);
        }
        authority=proof;authorizedHosted=hostedRef;authorizedSourceProof=captured.sourceProof();authorizedCapture=captured;entered=true;var results=new ArrayList<DomainBodies.BodyRef>();
        try {
            for(var plan:plans) {
                proof.requireCurrent(same,context);var registration=registration(plan.input().previous().slot());
                ExactRef body=context.archive().preserveArtifact(same,plan.body(),registration.maximumBodyBytes());byte[] input=plan.input().encode();
                var request=new DomainBodies.ImportRequest(registration.slot(),registration.contractSchema(),body,input,evidence(plan.input()),"next-governance-"+ActionCodec.sha256(input));
                proof.requireCurrent(same,context);var prepared=same.previewImport(request);proof.requireCurrent(same,context);
                StrictJson.require(prepared.predecessor().digest().equals(same.head().digest()),"NEXT governance preview crossed the actual locked head");
                same.commitImport(prepared);proof.requireCurrent(same,context);var actual=available(same,registration.slot());
                StrictJson.require(Arrays.equals(actual.canonicalBody(),plan.body()),"NEXT governance requires actual canonical body readback");results.add(actual.reference());
            }
            proof.requireCurrent(same,context);return List.copyOf(results);
        } finally {authority=null;authorizedHosted=null;authorizedSourceProof=null;authorizedCapture=null;}
    }
    @Override public String verify(ContinuityState ignored,Optional<DomainBodies.BodyRef> previous,DomainBodies.ImportRequest request,byte[] body)throws IOException {
        throw new IOException("NEXT governance requires the actual locked Head and Core-private domain proof");
    }
    @Override public String verify(WriterContracts.Head head,Optional<DomainBodies.BodyRef> previous,DomainBodies.ImportRequest request,byte[] body)throws IOException {
        var same=context.borrowedSession();context.writer().requireSession(same);var proof=authority;
        if(proof==null||authorizedCapture==null)throw new IOException("retained NEXT input is not a private domain-initialization authority");proof.requireCurrent(same,context);
        authorizedCapture.requireOriginals(same,context,proof);
        var input=GovernanceDomainInitializationInput.decode(request.producerInput());var registration=registration(request.slot());
        StrictJson.require(head.digest().equals(same.head().digest())&&previous.filter(input.previous()::equals).isPresent()
                &&request.slot()==input.previous().slot()&&request.contractSchema().equals(registration.contractSchema())
                &&request.evidence().equals(evidence(input))&&input.kind()==proof.kind()
                &&input.original().equals(proof.oldDomain(request.slot()))&&input.savedSession().equals(proof.baselineMaterial().session())
                &&input.savedSemantic().equals(proof.savedSemantic())&&input.currentSemantic().equals(proof.currentSemantic())
                &&input.initializationSequence()==proof.initializationHeadSequence()&&input.initializationDigest().equals(proof.initializationHeadDigest())&&input.before().equals(proof.beforeSession())&&input.after().equals(proof.afterSession())
                &&input.source().equals(proof.source())&&input.hosted().equals(authorizedHosted)&&input.sourceProof().equals(authorizedSourceProof)&&input.readSemantic().equals(authorizedCapture.semantic())
                &&input.material().equals(proof.baselineMaterial().witness())&&input.pair().equals(proof.baselineMaterial().pair()),
                "NEXT governance input crossed its actual private proof, source or original body");
        StrictJson.require(Arrays.equals(body,replay(same,input)),"NEXT governance differs from its retained original reducer");authorizedCapture.requireOriginals(same,context,proof);proof.requireCurrent(same,context);
        return ActionCodec.sha256(StrictJson.canonical(StrictJson.object().put("head",head.digest()).put("body",ActionCodec.sha256(body)).put("producer",ActionCodec.sha256(request.producerInput()))));
    }
    /** Independent historical recomputation; it reads originals and never imports or mints a live proof. */
    public byte[] replayOriginal(ContinuityStorePort.Session same,byte[] producerInput)throws IOException {return replay(same,GovernanceDomainInitializationInput.decode(producerInput));}
    private byte[] replay(ContinuityStorePort.Session same,GovernanceDomainInitializationInput input)throws IOException {
        context.writer().requireSession(same);var registration=registration(input.previous().slot());
        StrictJson.require(input.previous().contractSchema().equals(registration.contractSchema())&&input.previous().producerSources().equals(registration.producerSources()),
                "NEXT governance original source closure/schema differs");
        var material=context.savedMaterials().loadRetainedOriginal(same,SavedCheckpointMaterial.Kind.FIRST_BASELINE,input.material(),input.pair());
        StrictJson.require(material.kind()==SavedCheckpointMaterial.Kind.FIRST_BASELINE&&material.session().equals(input.savedSession())
                &&DomainBodies.reference(material.originalHead(),registration.slot()).filter(input.original()::equals).isPresent(),
                "NEXT governance old body is absent from the actual first BASELINE canonical head");
        same.requireHistoricalState(material.originalHeadSequence(),material.originalHeadDigest());
        var semantic=material.sourceSemantic();StrictJson.require(semantic.equals(input.savedSemantic()),"FIRST saved semantic original differs");
        context.semanticVerifier().verify(same,input.savedSession(),semantic);
        context.semanticVerifier().verify(same,input.after(),input.currentSemantic());
        var anchor=same.requireHistoricalState(input.initializationSequence(),input.initializationDigest());
        StrictJson.require(DomainBodies.reference(anchor,registration.slot()).filter(input.previous()::equals).isPresent(),
                "registered governance predecessor is absent from the true initialization head");
        context.semanticVerifier().verify(same,input.after(),input.readSemantic());
        var savedDriver=material.savedDriver();StrictJson.require(savedDriver.session().bridgePid()==input.savedSession().game().pid()
                &&savedDriver.session().actorId().equals(semantic.frame().frame().identity().player())
                &&savedDriver.session().episodeRunId().equals(semantic.frame().frame().episodeRunId()),"NEXT governance requires the actual saved new-player Driver");
        var archive=context.archive().withSession(same);var read=archive.loadRead(input.hosted());
        var packet=activity.definitions().contract(ActivityNativeContracts.Query.HOSTED).replay(read);
        NativeRecordedEvidenceVerifier.requireRead(read,archive);
        var current=read.request().before();var saved=input.currentSemantic().frame();
        StrictJson.require(archive.readReferenceOf(read).equals(input.hosted())&&current.game().equals(saved.game())&&current.machineId().equals(saved.machineId())
                &&current.equals(input.readSemantic().frame())
                &&current.frame().episodeRunId().equals(saved.frame().episodeRunId())&&current.frame().identity().player().equals(saved.frame().identity().player())
                &&current.frame().identity().dateRaw().equals(saved.frame().identity().dateRaw())
                &&current.frame().identity().nativeRevision().compareTo(saved.frame().identity().nativeRevision())>=0
                &&read.request().source().equals(input.source())&&read.request().sessionId().equals(input.after().sessionId()),"HOSTED original is not the actual current physical owner/source/episode/date");
        for(var guard:List.of(read.before(),read.after())) {
            RootGuardEvidence.requireHistory(guard.binding(),archive,same);
            var actual=RootGuardEvidence.loadFrame(guard.binding(),archive,context.frameLoader());
            var driverRoles=RootGuardEvidence.originalDriverSource(guard.binding(),archive);
            StrictJson.require(actual.identity().equals(input.readSemantic().frame())&&actual.source().equals(input.source())
                    &&actual.sessionId().equals(input.after().sessionId())&&RootGuardEvidence.sourceQualification(guard.binding(),archive).equals(input.sourceProof())
                    &&driverRoles.driverRef().equals(input.readSemantic().originalDriver())&&driverRoles.stampRef().equals(input.readSemantic().driverStamp())
                    &&RootGuardEvidence.frameBasis(guard.binding(),archive).nativeFrame().equals(input.readSemantic().originalNativePacket())
                    &&actual.semantic().equals(org.xar.ck3.control.application.driver.DriverJson.object(archive.loadMaterial(input.readSemantic().semantic()).bytes(),org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES)),
                    "NEXT hosted guard lost its actual full frame or source-qualification original");
            var point=RootGuardEvidence.writerPoint(guard.binding(),archive);same.requireHistoricalState(point.sequence(),point.digest());
            StrictJson.require(point.sequence()>=input.initializationSequence(),"HOSTED original cannot precede its actual initialization anchor");
        }
        if(!(packet.payload() instanceof ActivityPayload.Hosted hosted))throw new IOException("actual typed HOSTED payload is absent");
        requireNewFeastClear(hosted,input.currentSemantic().frame().frame().identity().player().longValueExact());
        byte[] old=original(same,input.original(),registration.maximumBodyBytes());
        byte[] transformed=switch(registration.slot()) {
            case OPENING_GATE -> nextOpening(old,current,input.source(),input.after().sessionId(),evidence(input));
            case OPTIONAL_CADENCE -> {
                var previous=CadenceJson.readState(old,StrictJson.text(StrictJson.parse(old).get("episode_run_id")));
                StrictJson.require(!previous.episodeRunId().equals(current.frame().episodeRunId()),"NEXT cadence cannot reuse the prior episode identity");
                yield CadenceJson.writeState(OptionalCheckCadence.forEpisode(previous,current.frame().episodeRunId()));
            }
            case FEAST -> {
                var ledger=FeastDomainRuntime.decode(old);requireOldFeastSettled(ledger);
                StrictJson.require(feast.financeBinding().decoder().reader().decode(new FinanceStatePort.Document(FinanceStatePort.Domain.FEAST,input.original().payload(),old))==FinanceStatePort.Pending.CLEAR,
                        "old canonical Feast commitment remains unresolved");
                yield FeastDomainRuntime.encode(new FeastDomainRuntime.Ledger(Optional.empty(),Optional.empty()));
            }
            default -> throw new IOException("not an owned NEXT governance slot");
        };
        byte[] registered=original(same,input.previous(),registration.maximumBodyBytes());
        requireRegisteredContinuation(input,old,registered,transformed);
        return transformed;
    }
    static byte[] nextOpening(byte[] old,ObservationIdentity actual,G2Source source,String session,List<ExactRef> evidence) {
        var prior=GovernanceOpeningDocument.decode(old);
        StrictJson.require(prior.stage()==GovernanceObservationSupplier.OpeningStage.COMPLETE||prior.preparedCommand().isEmpty()&&prior.actionReceipt().isEmpty(),
                "INCOMPLETE_NEXT_GOVERNANCE: prior opening pending/UNKNOWN cannot be cleared");
        StrictJson.require(!prior.observed().frame().episodeRunId().equals(actual.frame().episodeRunId()),"NEXT opening must use the actual distinct episode");
        return GovernanceOpeningDocument.encode(new GovernanceOpeningDocument.Document(actual,source,session,GovernanceObservationSupplier.OpeningStage.AWAIT_SUBMIT,
                Optional.empty(),Optional.empty(),evidence.stream().distinct().toList()));
    }
    static void requireOldFeastSettled(FeastDomainRuntime.Ledger old) {
        StrictJson.require(old.pending().isEmpty()&&old.resolved().flatMap(FeastDomainRuntime.Resolved::activity).filter(origin->origin.finalState().isEmpty()).isEmpty(),
                "INCOMPLETE_NEXT_GOVERNANCE: prior Feast pending/UNKNOWN or unfinished activity original must be retained");
    }
    static void requireNewFeastClear(ActivityPayload.Hosted hosted,long actor) {
        for(var row:hosted.hosted())if(row.typeKey().equals("activity_feast"))StrictJson.require(row.hostId()==actor
                &&row.completed().isPresent()&&row.invalidated().isPresent()&&(row.completed().orElseThrow()||row.invalidated().orElseThrow()),
                "INCOMPLETE_NEXT_GOVERNANCE: new-player hosted Feast is ongoing or unknown; no native adoption or clear is inferred");
    }
    private DomainBodies.Registration registration(DomainBodies.Slot slot)throws IOException {return registrations.stream().filter(value->value.slot()==slot).findFirst().orElseThrow(()->new IOException("not an owned NEXT governance slot"));}
    private DomainBodies.Available available(ContinuityStorePort.Session same,DomainBodies.Slot slot)throws IOException {
        var read=same.readDomain(slot);if(read instanceof DomainBodies.Available body)return body;throw new IOException("INCOMPLETE_NEXT_GOVERNANCE: actual prior "+slot+" body is unavailable; no empty body is substituted");
    }
    private static byte[] original(ContinuityStorePort.Session same,DomainBodies.BodyRef ref,int maximum)throws IOException {
        var pin=same.capturePin(ref.payload(),maximum);StrictJson.require(pin.identity().equals(ref.identity()),"NEXT governance old body FileID changed");
        byte[] body=same.readPinned(pin,maximum);same.verifyPin(pin);return body;
    }
    private static List<ExactRef> evidence(GovernanceDomainInitializationInput input) {var refs=new ArrayList<>(List.of(input.previous().payload(),input.original().payload(),input.material().reference(),input.pair().driver().reference(),input.pair().save().reference(),input.pair().nativeAckRef(),input.hosted()));input.sourceProof().ifPresent(refs::add);refs.addAll(input.savedSemantic().references());refs.addAll(input.currentSemantic().references());refs.addAll(input.readSemantic().references());return refs.stream().distinct().toList();}
    /** A private FIRST restore may rebind a prior NEXT entry; every changed commitment remains unresolved. */
    static void requireRegisteredContinuation(GovernanceDomainInitializationInput input,byte[] original,byte[] registered,byte[] transformed) {
        if(input.previous().equals(input.original()))StrictJson.require(Arrays.equals(original,registered),"registered original content differs");
        else if(Arrays.equals(registered,transformed))return;
        else {
            StrictJson.require(input.kind()==RootApplicationAssembly.EpisodeDomainInitializationProof.Kind.RESTORED_FIRST,
                    "NEXT cannot replace an unrelated registered governance body");
            switch(input.original().slot()) {
                case OPENING_GATE -> {
                    var prior=GovernanceOpeningDocument.decode(registered);var saved=input.savedSemantic().frame();
                    StrictJson.require(!prior.observed().game().equals(input.after().game())&&prior.observed().machineId().equals(saved.machineId())
                            &&prior.observed().frame().episodeRunId().equals(saved.frame().episodeRunId())
                            &&prior.observed().frame().identity().player().equals(saved.frame().identity().player())
                            &&prior.observed().frame().identity().dateRaw().equals(saved.frame().identity().dateRaw())
                            &&(!prior.observed().game().equals(saved.game())||prior.observed().frame().identity().nativeRevision().compareTo(saved.frame().identity().nativeRevision())>=0)
                            &&prior.source().equals(input.source())
                            &&prior.stage()==GovernanceObservationSupplier.OpeningStage.AWAIT_SUBMIT
                            &&prior.preparedCommand().isEmpty()&&prior.actionReceipt().isEmpty()&&prior.checkpoint().isEmpty()
                            &&prior.originals().containsAll(List.of(input.original().payload(),input.material().reference(),input.pair().save().reference(),input.pair().driver().reference())),
                            "FIRST restore cannot erase a changed/pending/UNKNOWN opening or cross its baseline");
                }
                case OPTIONAL_CADENCE, FEAST -> StrictJson.require(Arrays.equals(registered,transformed),
                        "FIRST restore cannot erase changed cadence or Feast originals");
                default -> throw new IllegalArgumentException("not an owned governance slot");
            }
        }
    }
}
