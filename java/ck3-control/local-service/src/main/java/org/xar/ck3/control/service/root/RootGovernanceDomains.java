package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.application.planning.governance.*;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.governance.council.CouncilActionCodec;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy;
import org.xar.ck3.control.nativebridge.capabilities.governance.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.application.planning.governance.GovernanceDomainDocument.*;

/** The original Council/Crown holding bodies, with one writer, actual preparation, material settlement and archive replay. */
public final class RootGovernanceDomains implements OrdinaryPlanCompletion {
    public static final String INPUT_SCHEMA="xar.java.governance-domain-publication/v1";
    public static final Set<OperationKey> OWNED=Set.of(GovernancePolicies.COUNCIL,GovernancePolicies.CORE_COUNCIL,GovernancePolicies.CROWN);
    public record Sources(ExactRef implementation,List<ExactRef> council,List<ExactRef> crown) {
        public Sources {Objects.requireNonNull(implementation);council=List.copyOf(council);crown=List.copyOf(crown);
            StrictJson.require(implementation.bytes()>0&&!council.isEmpty()&&!crown.isEmpty()&&council.size()<=64&&crown.size()<=32
                    &&council.stream().allMatch(ref->ref.bytes()>0)&&crown.stream().allMatch(ref->ref.bytes()>0),"complete actual domain producer closures required");}
    }
    private enum Kind { INITIAL,INTENT,OUTCOME,COUNCIL_MATERIAL,CROWN_MATERIAL,CROWN_APPLIED,COLD_CROWN,FOLLOW_COUNCIL,FOLLOW_CROWN }
    private record Input(Domain domain,Kind kind,Optional<ExactRef> previous,Optional<ExactRef> command,
            Optional<ExactRef> prepared,Optional<ExactRef> receipt,Optional<ExactRef> read,Optional<ExactRef> initial,List<ExactRef> preflight) {
        private Input {Objects.requireNonNull(domain);Objects.requireNonNull(kind);Objects.requireNonNull(previous);Objects.requireNonNull(command);
            Objects.requireNonNull(prepared);Objects.requireNonNull(receipt);Objects.requireNonNull(read);Objects.requireNonNull(initial);preflight=List.copyOf(preflight);
            StrictJson.require(preflight.size()<=3002,"bounded complete original preflight closure required");
            StrictJson.require(switch(kind) {
                case INITIAL->previous.isEmpty()&&command.isEmpty()&&prepared.isEmpty()&&receipt.isEmpty()&&read.isEmpty()&&initial.isPresent()&&preflight.isEmpty();
                case INTENT->previous.isPresent()&&command.isPresent()&&prepared.isPresent()&&receipt.isEmpty()&&read.isEmpty()&&initial.isEmpty();
                case OUTCOME->previous.isPresent()&&command.isEmpty()&&prepared.isEmpty()&&receipt.isPresent()&&read.isEmpty()&&initial.isEmpty()&&preflight.isEmpty();
                case COUNCIL_MATERIAL->domain==Domain.COUNCIL&&previous.isPresent()&&command.isEmpty()&&prepared.isEmpty()&&receipt.isPresent()&&read.isPresent()&&initial.isEmpty()&&preflight.isEmpty();
                case CROWN_MATERIAL->domain==Domain.CROWN&&previous.isPresent()&&command.isEmpty()&&prepared.isEmpty()&&receipt.isPresent()&&read.isPresent()&&initial.isEmpty()&&preflight.isEmpty();
                case CROWN_APPLIED->domain==Domain.CROWN&&previous.isPresent()&&command.isEmpty()&&prepared.isEmpty()&&receipt.isPresent()&&read.isEmpty()&&initial.isEmpty()&&preflight.isEmpty();
                case COLD_CROWN,FOLLOW_CROWN->domain==Domain.CROWN&&previous.isPresent()&&command.isEmpty()&&prepared.isEmpty()&&receipt.isEmpty()&&read.isPresent()&&initial.isEmpty()&&preflight.isEmpty();
                case FOLLOW_COUNCIL->domain==Domain.COUNCIL&&previous.isPresent()&&command.isEmpty()&&prepared.isEmpty()&&receipt.isEmpty()&&read.isPresent()&&initial.isEmpty()&&!preflight.isEmpty();
            },"exact governance publication branch fields required");}
    }
    private final Path writerLock;private final Sources sources;private final CrownRetryPublication retry;private final List<DomainBodies.Registration> registrations;
    @FunctionalInterface private interface CurrentInitial {void requireCurrent(ContinuityStorePort.Session same)throws IOException;}
    private record LiveInitial(ExactRef basis,CurrentInitial current) { }
    private final ThreadLocal<LiveInitial> initializing=new ThreadLocal<>();
    private GovernanceCadenceActions.Publisher actionCadence;
    private RootApplicationAssembly.Core core;private RootRuntimeContext context;private GovernanceRuntimeInstaller.Installed nativeGovernance;
    public RootGovernanceDomains(Path originalWriterLock,Sources sources,CrownRetryPublication sameRetryPublisher) {
        writerLock=Objects.requireNonNull(originalWriterLock).toAbsolutePath().normalize();this.sources=Objects.requireNonNull(sources);retry=Objects.requireNonNull(sameRetryPublisher);
        var actual=retry.registration();StrictJson.require(actual.slot()==DomainBodies.Slot.CROWN&&actual.contractSchema().equals(CROWN_SCHEMA),
                "Crown retry and full holding body must share the identical registration contract");
        registrations=List.of(registration(Domain.COUNCIL),registration(Domain.CROWN));
    }
    public List<DomainBodies.Registration> domainRegistrations() {return registrations;}
    private DomainBodies.Registration registration(Domain domain) {
        return new DomainBodies.Registration(slot(domain),schema(domain),1_048_576,closure(domain),new DomainBodies.Verifier() {
            @Override public String verify(ContinuityState ignored,Optional<DomainBodies.BodyRef> previous,DomainBodies.ImportRequest request,byte[] body)throws IOException {throw new IOException("governance qualification requires the original locked Head");}
            @Override public String verify(WriterContracts.Head head,Optional<DomainBodies.BodyRef> previous,DomainBodies.ImportRequest request,byte[] body)throws IOException {
                if(domain==Domain.CROWN&&CrownRetryPublication.INPUT_SCHEMA.equals(StrictJson.text(StrictJson.parse(request.producerInput()).get("schema"))))return retry.verify(head,previous,request,body);
                return verifyPublication(domain,head,previous,request,body);
            }
        });
    }
    public synchronized void bindCore(RootApplicationAssembly.Core actual)throws IOException {
        StrictJson.require(core==null&&actual.configuration().ledger().lock().toAbsolutePath().normalize().equals(writerLock),"governance domains bind the exact one original Core once");core=actual;
    }
    public synchronized RootDomainInstallation install(RootRuntimeContext actual,GovernanceRuntimeInstaller.Installed nativeInstalled)throws IOException {
        StrictJson.require(actual.core()==core()&&(context==null||context!=actual),"governance domains install once per actual physical Game on the same Core");
        context=Objects.requireNonNull(actual);nativeGovernance=Objects.requireNonNull(nativeInstalled);actual.requireCurrent(actual.clock().instant().plusSeconds(1));
        return new RootDomainInstallation("native-governance-domains",domainRegistrations(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),
                pendingBindings(),OWNED,List.of(),List.of(this),List.of(),List.of(),List.of());
    }
    public GovernanceStateSupplier.BodyContract<GovernanceObservationSupplier.DomainState> councilBody() {return GovernanceStateSupplier.legacyCouncil(COUNCIL_SCHEMA,sources.council());}
    public GovernanceStateSupplier.BodyContract<GovernanceObservationSupplier.DomainState> crownBody() {return GovernanceStateSupplier.legacyCrown(CROWN_SCHEMA,sources.crown());}
    public CrownRetryPublication retryPublication() {return retry;}
    public synchronized void bindActionCadencePublisher(GovernanceCadenceActions.Publisher actual) {StrictJson.require(actionCadence==null,"Civic material uses one actual OPTIONAL_CADENCE publisher");actionCadence=Objects.requireNonNull(actual);}
    private synchronized GovernanceCadenceActions.Publisher actionCadence()throws IOException {if(actionCadence==null)throw new IOException("actual Civic cadence action publisher not bound");return actionCadence;}
    public List<RootDomainIntentPreparation.Binding> pendingBindings() {
        return List.of(new RootDomainIntentPreparation.Binding("native-council-crown-pending",sources.implementation(),command->OWNED.contains(command.operation()),(same,command)->{
            try {
                requireSession(same);var actual=context();actual.requireCurrent(command.deadline());
                StrictJson.require(command.origin() instanceof CommandOrigin.Gameplay&&command.before().game().equals(actual.game().generation())
                        &&command.source().equals(actual.source())&&command.sessionId().equals(actual.game().sessionId()),"pending crossed actual physical Game/source/session");
                // This private scope exists only after the unique coordinator's actual read-only preparation succeeded.
                NativeRequest prepared=ActionPreparationScope.requirePrepared(same,command);StrictJson.require(prepared.step().equals(command.operation().value()),"actual prepared operation differs from the pending command");
                Domain domain=domain(command);var before=available(same,domain);var bound=core().archive().withSession(same);
                ExactRef commandRef=bound.preserveMaterial(new RawJson(ActionCodec.encodeCommand(command)));ExactRef preparedRef=bound.preserveRequest(prepared);
                var originals=new ArrayList<ExactRef>();if(command.operation().equals(GovernancePolicies.COUNCIL)) {
                    var scope=GovernanceActionScope.current(command);StrictJson.require(scope.session(command)==same,"Council preflight used another writer Session");
                    for(PlanningReadReceipt read:scope.preflight(command))originals.add(bound.preserveRead(read));
                    StrictJson.require(!originals.isEmpty(),"actual Council final-gate preflight originals are missing");
                }
                publish(same,new Input(domain,Kind.INTENT,Optional.of(before.reference().payload()),Optional.of(commandRef),Optional.of(preparedRef),Optional.empty(),Optional.empty(),Optional.empty(),originals));
            } catch(IOException failure) {throw new UncheckedIOException("actual Council/Crown pending publication unavailable",failure);}
        }));
    }
    public List<WriterContracts.Receipt> initialize(ContinuityStorePort.Session same,RootInitialEpisodeProof actual)throws IOException {
        requireSession(same);actual.requireCurrent(same);return initialize(same,actual.preserveOriginal(same),actual::requireCurrent,List.of(Domain.values()));
    }
    public List<WriterContracts.Receipt> initialize(ContinuityStorePort.Session same,FreshCampaignContext actual)throws IOException {
        requireSession(same);StrictJson.require(actual.context()==context(),"fresh governance belongs to another installed Game");actual.requireCurrent(same);
        var missing=new ArrayList<Domain>();
        for(Domain domain:Domain.values()) {
            var existing=same.readDomain(slot(domain));
            if(existing instanceof DomainBodies.Available available)decode(domain,available.canonicalBody());
            else {
                StrictJson.require(existing instanceof DomainBodies.Unavailable unavailable && unavailable.reason()==DomainBodies.Reason.UNIMPORTED,
                        "fresh governance may initialize only an unimported slot");
                missing.add(domain);
            }
        }
        if(missing.isEmpty())return List.of();
        return initialize(same,actual.preserveOriginal(same),actual::requireCurrent,missing);
    }
    private List<WriterContracts.Receipt> initialize(ContinuityStorePort.Session same,ExactRef original,CurrentInitial actual,List<Domain> domains)throws IOException {
        requireSession(same);actual.requireCurrent(same);var result=new ArrayList<WriterContracts.Receipt>();
        // Check every requested slot before changing any; existing bodies are never replaced.
        for(Domain domain:domains)StrictJson.require(same.readDomain(slot(domain)) instanceof DomainBodies.Unavailable unavailable
                &&unavailable.reason()==DomainBodies.Reason.UNIMPORTED,"fresh initialization cannot clear an existing/restored/unavailable domain");
        StrictJson.require(initializing.get()==null,"another original domain initializer is active");initializing.set(new LiveInitial(original,actual));
        try {for(Domain domain:domains)result.add(publish(same,new Input(domain,Kind.INITIAL,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.of(original),List.of())).orElseThrow());return List.copyOf(result);}
        finally {initializing.remove();}
    }
    @Override public ExecutionDisposition afterExecution(ActionReceipt actual) {
        if(!OWNED.contains(actual.command().operation()))return new Unchanged("another domain owns this original receipt");
        try {
            var same=session();Domain domain=domain(actual.command());var body=available(same,domain);Document old=decode(domain,body.canonicalBody());
            if(old.pending().isEmpty())return new Unchanged("no pending record; an existing result is retained");
            StrictJson.require(old.pending().orElseThrow().requestId().equals(originalId(actual.command())),"execution receipt belongs to another original pending command");
            var head=same.head();ExactRef original=core().archive().inSession(same,archive->archive.receiptReferenceOf(actual));
            var committed=publish(same,new Input(domain,Kind.OUTCOME,Optional.of(body.reference().payload()),Optional.empty(),Optional.empty(),Optional.of(original),Optional.empty(),Optional.empty(),List.of()));
            return committed.<ExecutionDisposition>map(value->new Published(head,value)).orElseGet(()->new Unchanged("original pending/UNKNOWN or identical receipt retained"));
        } catch(IOException|IllegalArgumentException|IllegalStateException failure) {return new Blocked("actual Council/Crown receipt publication unavailable: "+failure.getMessage(),List.of());}
    }
    @Override public PlanningDisposition afterPlanning(PlanningRequest original,PlanningResult planned) {
        try {
            var same=session();context().requireCurrent(original.deadline());StrictJson.require(original.before().game().equals(context().game().generation())&&original.source().equals(context().source()),"governance reconciliation crossed actual current planning Game/source");
            for(Domain domain:Domain.values()) {
                var body=available(same,domain);var old=decode(domain,body.canonicalBody());
                if(old.latest().isPresent()) {
                    var last=object(old.latest().orElseThrow());boolean material=(domain==Domain.COUNCIL?"applied":"enacted").equals(last.path("status").asText())
                            &&(domain==Domain.COUNCIL||last.path("material_result").isBoolean()&&last.path("material_result").booleanValue());
                    if(material) {
                        String id=StrictJson.text(last.get(domain==Domain.COUNCIL?"action_request_id":"action_id"));var retained=findByRequest(same,id);
                        if(retained.isPresent()) {var predecessor=same.head();var reset=actionCadence().publish(same,retained.orElseThrow());if(reset.isPresent())return new Published(predecessor,reset.orElseThrow());}
                    }
                }
                if(old.pending().isPresent()) {
                    Pending pending=old.pending().orElseThrow();Optional<ActionReceipt> canonical=findByRequest(same,pending.requestId());
                    if(domain==Domain.CROWN&&(coldContext(pending,original.before().game().pid(),original.before().frame().episodeRunId())
                            ||canonical.filter(value->!value.command().before().game().equals(original.before().game())).isPresent())) {
                        var observed=context().reads().read(same,nativeGovernance().planningReads().crown(),new PlanningReadRequest(original.before(),original.source(),original.sessionId(),nativeGovernance().planningReads().crown().operation(),new OpportunityJson.Obj(java.util.Map.of()),original.deadline()));
                        if(observed instanceof PlanningReadResult.Unavailable<?> unavailable)return new Blocked("cold Crown current-law observation unavailable: "+unavailable.reason(),List.of(body.reference().payload()));
                        var read=((PlanningReadResult.Known<?>)observed).receipt();var head=same.head();var changed=publish(same,new Input(domain,Kind.COLD_CROWN,Optional.of(body.reference().payload()),Optional.empty(),Optional.empty(),Optional.empty(),Optional.of(core().archive().withSession(same).preserveRead(read)),Optional.empty(),List.of()));
                        if(changed.isPresent())return new Published(head,changed.orElseThrow());continue;
                    }
                    if(canonical.isEmpty())return new Unchanged("original pending has no canonical Java action; do not recreate or submit it");
                    var receipt=canonical.orElseThrow();
                    if(domain==Domain.COUNCIL&&receipt.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED) {
                        var root=context().finance().definitions().read(same,FinanceReadContracts.Query.ROOT,context().reads(),original);
                        if(root instanceof PlanningReadResult.Unavailable<?> unavailable)return new Blocked("Council independent ROOT read unavailable: "+unavailable.reason(),List.of(body.reference().payload()));
                        var known=(PlanningReadResult.Known<FinanceReadContracts.Packet>)root;var head=same.head();var archive=core().archive().withSession(same);
                        var changed=publish(same,new Input(domain,Kind.COUNCIL_MATERIAL,Optional.of(body.reference().payload()),Optional.empty(),Optional.empty(),Optional.of(archive.receiptReferenceOf(receipt)),Optional.of(known.originalReceipt()),Optional.empty(),List.of()));
                        if(changed.isPresent())return new Published(head,changed.orElseThrow());
                    } else if(domain==Domain.CROWN&&receipt.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED) {
                        var head=same.head();var archive=core().archive().withSession(same);
                        var changed=publish(same,new Input(domain,Kind.CROWN_APPLIED,Optional.of(body.reference().payload()),Optional.empty(),Optional.empty(),Optional.of(archive.receiptReferenceOf(receipt)),Optional.empty(),Optional.empty(),List.of()));
                        if(changed.isPresent())return new Published(head,changed.orElseThrow());
                    } else {
                        var head=same.head();var archive=core().archive().withSession(same);var changed=publish(same,new Input(domain,Kind.OUTCOME,Optional.of(body.reference().payload()),Optional.empty(),Optional.empty(),Optional.of(archive.receiptReferenceOf(receipt)),Optional.empty(),Optional.empty(),List.of()));
                        if(changed.isPresent())return new Published(head,changed.orElseThrow());
                    }
                } else if(old.latest().isPresent()&&!hasConsumedAt(old.latest().orElseThrow(),original.before().frame().identity().nativeRevision(),original.before().frame().identity().dateRaw())) {
                    Optional<ExactRef> read;List<ExactRef> followQueries=List.of();
                    if(domain==Domain.COUNCIL) {
                        var observed=context().finance().definitions().read(same,FinanceReadContracts.Query.ROOT,context().reads(),original);
                        if(observed instanceof PlanningReadResult.Unavailable<?>)continue;read=Optional.of(((PlanningReadResult.Known<?>)observed).originalReceipt());
                        var prior=object(old.latest().orElseThrow());String position=StrictJson.text(object(object(prior.get("action_ack")).get("council_assign_councillor_ack")).get("position_key"));
                        var role=Arrays.stream(CouncilSelection.Position.values()).filter(value->value.key().equals(position)).findFirst().orElseThrow();
                        var nativeQuery=nativeGovernance().councilReads().readPrivate(original,role);
                        if(nativeQuery instanceof GovernanceObservationSupplier.Unavailable<?>)continue;
                        followQueries=((GovernanceObservationSupplier.Known<?>)nativeQuery).originals();
                    } else {
                        var contract=nativeGovernance().planningReads().crown();var observed=context().reads().read(same,contract,new PlanningReadRequest(original.before(),original.source(),original.sessionId(),contract.operation(),new OpportunityJson.Obj(java.util.Map.of()),original.deadline()));
                        if(observed instanceof PlanningReadResult.Unavailable<?>)continue;read=Optional.of(((PlanningReadResult.Known<?>)observed).originalReceipt());
                    }
                    var head=same.head();var changed=publish(same,new Input(domain,domain==Domain.COUNCIL?Kind.FOLLOW_COUNCIL:Kind.FOLLOW_CROWN,Optional.of(body.reference().payload()),Optional.empty(),Optional.empty(),Optional.empty(),read,Optional.empty(),followQueries));
                    if(changed.isPresent())return new Published(head,changed.orElseThrow());
                }
            }
            return new Unchanged("Council/Crown original state unchanged; UNKNOWN is never resubmitted");
        } catch(IOException|IllegalArgumentException|IllegalStateException failure) {return new Blocked("actual Council/Crown planning reconciliation unavailable: "+failure.getMessage(),List.of());}
    }
    private Optional<WriterContracts.Receipt> publish(ContinuityStorePort.Session same,Input input)throws IOException {
        requireSession(same);var head=same.head();var previous=DomainBodies.reference(head.state(),slot(input.domain()));byte[] output=reduce(same,head,previous,input);
        if(previous.isPresent()&&Arrays.equals(output,readBody(same,previous.orElseThrow().payload())))return Optional.empty();
        if(input.kind()==Kind.COUNCIL_MATERIAL||input.kind()==Kind.CROWN_MATERIAL||input.kind()==Kind.CROWN_APPLIED)actionCadence();
        var ref=core().archive().preserveArtifact(same,output,1_048_576);byte[] producer=encodeInput(input);var request=new DomainBodies.ImportRequest(slot(input.domain()),schema(input.domain()),ref,producer,evidence(input),"governance-domain-"+ActionCodec.sha256(producer));
        var prepared=same.previewImport(request);StrictJson.require(prepared.predecessor().digest().equals(head.digest()),"domain preview crossed the original locked head");var committed=same.commitImport(prepared);var actual=available(same,input.domain());
        StrictJson.require(committed.disposition()!=WriterContracts.Disposition.NO_CHANGE&&actual.reference().payload().equals(ref)&&Arrays.equals(actual.canonicalBody(),output),"actual domain commit and full original readback required");
        if(input.kind()==Kind.COUNCIL_MATERIAL||input.kind()==Kind.CROWN_MATERIAL||input.kind()==Kind.CROWN_APPLIED) {var receipt=core().archive().withSession(same).loadReceipt(input.receipt().orElseThrow());var reset=actionCadence().publish(same,receipt);if(reset.isPresent())return reset;}
        return Optional.of(committed);
    }
    private String verifyPublication(Domain domain,WriterContracts.Head head,Optional<DomainBodies.BodyRef> previous,DomainBodies.ImportRequest request,byte[] body)throws IOException {
        var same=session();StrictJson.require(head.digest().equals(same.head().digest())&&request.slot()==slot(domain)&&request.contractSchema().equals(schema(domain)),"governance actual head/slot/schema changed");
        var input=decodeInput(request.producerInput());StrictJson.require(input.domain()==domain&&request.evidence().equals(evidence(input)),"governance original producer evidence differs");
        byte[] expected=reduce(same,head,previous,input);StrictJson.require(Arrays.equals(expected,body),"original governance producer/reducer does not reproduce the entire body");
        return ActionCodec.sha256(StrictJson.canonical(StrictJson.object().put("head",head.digest()).put("input",ActionCodec.sha256(request.producerInput())).put("body",ActionCodec.sha256(body))));
    }
    DomainBodies.BodyRef retainedPrevious(WriterContracts.Head head,Optional<DomainBodies.BodyRef> previous,Domain domain,ExactRef originalPrevious)throws IOException {
        var before=previous.orElseThrow(()->new IOException("original prior domain body missing; absence is not CLEAR"));
        StrictJson.require(before.payload().equals(originalPrevious)&&before.slot()==slot(domain)&&before.contractSchema().equals(schema(domain))
                &&DomainBodies.reference(head.state(),slot(domain)).filter(before::equals).isPresent(),"original previous body/head member/slot/schema differs");
        return before;
    }
    boolean isDomainBodyContract(Domain domain,DomainBodies.BodyRef body) {
        return body.slot()==slot(domain)&&body.contractSchema().equals(schema(domain));
    }
    private byte[] reduce(ContinuityStorePort.Session same,WriterContracts.Head head,Optional<DomainBodies.BodyRef> previous,Input input)throws IOException {
        if(input.kind()==Kind.INITIAL) {
            StrictJson.require(previous.isEmpty(),"fresh initial body cannot replace a previous original");ExactRef basis=input.initial().orElseThrow();
            var actual=initializing.get();if(actual!=null){actual.current().requireCurrent(same);StrictJson.require(actual.basis().equals(basis),"the live original fresh input differs");}
            if(FreshCampaignContext.isOriginal(context(),same,basis))FreshCampaignContext.replayOriginal(context(),same,basis).requireInitializationPredecessor(same,head);
            else RootInitialEpisodeProof.replayOriginal(context(),same,basis).requireInitializationPredecessor(same,head);
            return encode(initial(input.domain()));
        }
        var before=retainedPrevious(head,previous,input.domain(),input.previous().orElseThrow());
        Document old=decode(input.domain(),readBody(same,before.payload()));var archive=core().archive().withSession(same);
        if(input.kind()==Kind.INTENT) {
            ActionCommand command=ActionCodec.decodeCommand(archive.loadMaterial(input.command().orElseThrow()).bytes());StrictJson.require(OWNED.contains(command.operation())&&domain(command)==input.domain()&&command.origin() instanceof CommandOrigin.Gameplay,"exact original gameplay governance command required");
            NativeRequest prepared=archive.loadRequest(input.prepared().orElseThrow());StrictJson.require(prepared.step().equals(command.operation().value()),"prepared operation differs from original command");
            for(ExactRef ref:input.preflight()) {var read=archive.loadRead(ref);NativeRecordedEvidenceVerifier.requireRead(read,archive);StrictJson.require(read.request().before().equals(command.before())&&read.request().source().equals(command.source())&&read.request().sessionId().equals(command.sessionId()),"original preflight crossed selected command frame/source/session");}
            if(command.operation().equals(GovernancePolicies.COUNCIL)) {
                StrictJson.require(!input.preflight().isEmpty(),"private Council pending lacks its real successful final preflight");
                var request=GovernanceActionPreparation.councilRequest(command,originalId(command));var role=Arrays.stream(CouncilSelection.Position.values()).filter(value->value.key().equals(request.position().key())).findFirst().orElseThrow();
                var fresh=nativeGovernance().councilReads().replayPrivate(input.preflight().stream().map(archive::loadRead).toList(),role);var chosen=org.xar.ck3.control.governance.council.CouncilCallerSubmission.isPublic(object(StrictJson.parse(OpportunityJson.encode(command.arguments()))))?CouncilCallerSelection.select(fresh,request.candidateId()):CouncilSelection.choose(fresh);
                StrictJson.require(chosen.selected().filter(value->value.nativeLegal()&&value.characterId().intValueExact()==request.candidateId()).isPresent()
                        &&fresh.incumbent().equals(request.incumbentId().isPresent()?Optional.of(BigInteger.valueOf(request.incumbentId().orElseThrow())):Optional.empty())
                        &&(chosen.outcome()==CouncilSelection.Outcome.ASSIGN_REQUIRED||chosen.outcome()==CouncilSelection.Outcome.REPLACE_REQUIRED),"actual fresh final-gates selection changed before durable pending");
            }
            RawJson pending=makePending(command,prepared);if(old.pending().isPresent())StrictJson.require(old.pending().orElseThrow().original().equals(pending),"another original pending or UNKNOWN cannot be overwritten");
            return encode(pending(old,pending));
        }
        if(input.kind()==Kind.COLD_CROWN)return encode(coldCrown(old,checkedRead(input.read().orElseThrow(),archive),archive));
        if(input.kind()==Kind.FOLLOW_COUNCIL||input.kind()==Kind.FOLLOW_CROWN)return encode(follow(old,checkedRead(input.read().orElseThrow(),archive),input.preflight(),archive));
        ActionReceipt receipt=archive.loadReceipt(input.receipt().orElseThrow());var canonical=ContinuityActionJournal.lookup(head.state(),receipt.command().actionId(),archive).orElseThrow(()->new IOException("governance result absent from surviving canonical action chain"));
        StrictJson.require(Arrays.equals(ActionReceiptCodec.encodeReceipt(receipt,archive),ActionReceiptCodec.encodeReceipt(canonical,archive)),"caller receipt differs from actual canonical latest result");
        if(input.kind()==Kind.CROWN_APPLIED)StrictJson.require(receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.Applied,"direct Crown publication cannot consume UNKNOWN, unapplied or nonprimitive receipt");
        if(old.pending().isEmpty())return encode(old);Pending pending=old.pending().orElseThrow();
        StrictJson.require(pending.requestId().equals(originalId(receipt.command()))&&domain(receipt.command())==old.domain(),"canonical result belongs to another original pending command");
        if(ActionTransitions.attempt(receipt.state()).isEmpty())return encode(old);
        var expected=decodePending(old.domain(),makePending(receipt.command(),ActionTransitions.attempt(receipt.state()).orElseThrow().preparedRequest()));
        ObjectNode original=object(pending.original());var initial=object(expected.original());
        for(String field:old.domain()==Domain.COUNCIL?List.of("episode_run_id","action_request_id","candidate_character_id","source_query","source_decision","request","pre_native_revision","pre_date_raw")
                :List.of("episode_run_id","actor_character_id","action_id","law_key","readback","choice","budgets","source_context","pre_native_revision","pre_date_raw"))StrictJson.require(Objects.equals(original.get(field),initial.get(field)),"original pending identity/body differs from canonical command: "+field);
        if(receipt.state() instanceof ActionState.RejectedBeforeDispatch)return encode(old.domain()==Domain.COUNCIL?result(old,old.latest()):result(old,Optional.of(raw(original.deepCopy().put("status","rejected_before_submit").put("material_result",false)))));
        if(receipt.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.Rejected) {
            var verifier=context().bindings().actualArchivedVerifier(receipt.command().operation()).orElseThrow(()->new IOException("actual original governance rejection replay binding missing"));
            verifier.verifier().verify(head,receipt,archive);
            if(old.domain()==Domain.COUNCIL)return encode(result(old,old.latest()));
            ObjectNode rejected=original.deepCopy().put("status","rejected_before_submit").put("material_result",false);
            rejected.set("ack",nativeResult(receipt.ack().orElseThrow()));
            return encode(result(old,Optional.of(raw(rejected))));
        }
        if(receipt.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED) {
            var verifier=context().bindings().actualArchivedVerifier(receipt.command().operation()).orElseThrow(()->new IOException("actual original governance effect replay binding missing"));verifier.verifier().verify(head,receipt,archive);
            if(old.domain()==Domain.CROWN) {
                if(input.kind()==Kind.CROWN_APPLIED) return encode(crownAppliedDirect(old,receipt,archive));
                if(input.kind()!=Kind.CROWN_MATERIAL) {
                    var retained=original.deepCopy().put("stage","receipt_pending");retained.set("ack",nativeResult(receipt.ack().orElseThrow()));return encode(pending(old,raw(retained)));
                }
                return encode(crownApplied(old,receipt,checkedRead(input.read().orElseThrow(),archive),archive));
            }
            if(input.kind()==Kind.COUNCIL_MATERIAL)return encode(councilApplied(old,receipt,checkedRead(input.read().orElseThrow(),archive),archive));
        }
        // A helper invocation or UNKNOWN reserves the original request. It grants no material/action credit.
        if(old.domain()==Domain.COUNCIL)return encode(old);
        Optional<NativeActionPort.AckReceived> ack=receipt.ack();if(ack.isEmpty())return encode(old);
        var next=original.deepCopy().put("stage","receipt_pending");next.set("ack",nativeResult(ack.orElseThrow()));return encode(pending(old,raw(next)));
    }
    public static RawJson makePending(ActionCommand command,NativeRequest actualPrepared) {
        var row=StrictJson.object().put("stage","submission_unresolved").put("episode_run_id",command.before().frame().episodeRunId()).put("pre_native_revision",command.before().frame().identity().nativeRevision()).put("pre_date_raw",command.before().frame().identity().dateRaw());
        var args=object(StrictJson.parse(OpportunityJson.encode(command.arguments())));String id=originalId(command);
        if(domain(command)==Domain.COUNCIL) {
            StrictJson.require(actualPrepared.step().equals(command.operation().value())&&actualPrepared.requiredCapability().equals(command.operation().equals(GovernancePolicies.COUNCIL)?Optional.empty():Optional.of("game.action.assign-councillor-v1")),"actual Council operation/capability differs");
            var request=GovernanceActionPreparation.councilRequest(command,id);StrictJson.require(Arrays.equals(StrictJson.canonical(StrictJson.parse(actualPrepared.additionalFields().bytes())),StrictJson.canonical(CouncilActionCodec.wireFields(request,command.operation().equals(GovernancePolicies.COUNCIL)))),"actual Council preparation differs from original selected request");
            var role=Arrays.stream(CouncilSelection.Position.values()).filter(value->value.key().equals(request.position().key())).findFirst().orElseThrow();
            var query=OpportunityJson.object(command.arguments().get("original_query"),"original Council query");var parsed=command.operation().equals(GovernancePolicies.COUNCIL)?CouncilSelection.decodeObserved(command.before(),role,query):CouncilSelection.decodeCompositionObserved(command.before(),query);var decision=org.xar.ck3.control.governance.council.CouncilCallerSubmission.isPublic(args)?CouncilCallerSelection.select(parsed,request.candidateId()):CouncilSelection.choose(parsed);
            StrictJson.require((decision.outcome()==CouncilSelection.Outcome.ASSIGN_REQUIRED||decision.outcome()==CouncilSelection.Outcome.REPLACE_REQUIRED)&&decision.selected().filter(value->value.characterId().intValueExact()==request.candidateId()).isPresent(),"original deterministic Council selection differs from pending candidate");
            row.put("action_request_id",id).put("candidate_character_id",request.candidateId());row.set("source_query",args.get("original_query"));
            var choice=StrictJson.object().put("outcome",decision.outcome().name()).put("reason",decision.reason());choice.set("selected_candidate",StrictJson.parse(OpportunityJson.encode(decision.selected().orElseThrow().original())));row.set("source_decision",choice);
            ObjectNode wire=CouncilActionCodec.wireFields(request,false);wire.put("request_id",id);row.set("request",wire);row.putNull("action_ack");
        } else {
            var readback=CrownAuthorityCodec.decodeReadback(StrictJson.canonical(args.get("readback")));boolean caller=org.xar.ck3.control.governance.crownauthority.CrownCallerSelection.isCaller(args);var choice=caller?org.xar.ck3.control.governance.crownauthority.CrownCallerSelection.callerChoice(readback,args):CrownAuthorityPolicy.choose(readback);var source=readback.sourceFrame();var before=command.before().frame();
            StrictJson.require(choice.status()==CrownAuthorityPolicy.Status.READY&&choice.lawKey().equals(StrictJson.text(args.get("law_key")))&&(caller||StrictJson.parse(CrownAuthorityCodec.encodeChoice(choice)).equals(args.get("choice"))),"original Crown source/quote/choice differs");
            StrictJson.require(source.queriedSnapshotId().equals(before.snapshotId())&&source.queriedRevision().equals(before.revision())&&source.queriedNativeRevision().equals(before.identity().nativeRevision())
                    &&source.dateRaw().equals(before.identity().dateRaw())&&source.playerCharacterId().equals(before.identity().player()),"Crown holding body crossed the actual quote's public/native frame or actor");
            var expected=StrictJson.object().put("expected_date_raw",before.identity().dateRaw()).put("expected_player_character_id",before.identity().player()).put("submitted_request_id",id)
                    .put("group_key",readback.groupKey()).put("law_key",choice.lawKey()).put("expected_native_revision",source.nativeSnapshotRevision()).put("expected_proof_epoch",source.proofEpoch());
            for(var amount:choice.budgetsRaw())expected.put("budget_"+amount.currency().wire()+"_raw",amount.amountRaw());
            StrictJson.require(actualPrepared.step().equals(GovernanceActionPreparation.CROWN)&&actualPrepared.requiredCapability().isEmpty()&&StrictJson.parse(actualPrepared.additionalFields().bytes()).equals(expected),"actual Crown preparation differs from the entire original quote/request");
            row.put("actor_character_id",command.before().frame().identity().player()).put("action_id",id).put("law_key",choice.lawKey());row.set("readback",args.get("readback"));row.set("choice",caller?StrictJson.parse(CrownAuthorityCodec.encodeChoice(choice)):args.get("choice"));
            var budgets=row.putObject("budgets");for(var amount:choice.budgetsRaw())budgets.put(amount.currency().wire(),amount.amountRaw());row.set("source_context",context(command.before().game().pid(),command.before().frame().episodeRunId()));row.putNull("ack");
        }
        return raw(row);
    }
    private Document crownAppliedDirect(Document old,ActionReceipt receipt,ActionPorts.OutcomeArchive archive)throws IOException {
        var material=NativeEffectEvidence.load(receipt,archive,context().frameLoader());
        return crownAppliedOriginal(old,receipt,material.compatibleResult());
    }
    /** Pure projection of the canonical independently replayed success; no clock or final-terms facts are inferred. */
    static Document crownAppliedOriginal(Document old,ActionReceipt receipt,RawJson nativeReceipt) {
        StrictJson.require(old.domain()==Domain.CROWN&&receipt.command().operation().equals(GovernancePolicies.CROWN)
                &&receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.Applied,
                "direct Crown material requires its original primitive APPLIED settlement");
        var pending=old.pending().orElseThrow();var original=object(pending.original());var command=receipt.command();
        StrictJson.require(pending.requestId().equals(originalId(command))&&pending.episodeRunId().equals(command.before().frame().episodeRunId())
                &&integer(original.get("actor_character_id")).equals(command.before().frame().identity().player())
                &&!coldContext(pending,command.before().game().pid(),command.before().frame().episodeRunId()),
                "direct Crown material crossed original pending action/Game/actor/episode");
        var applied=receipt.applied().orElseThrow().observation();var expected=command.expected();
        StrictJson.require(expected.values().contains(new ProposalLifecycle.ExpectedText(new ProposalLifecycle.FieldKey("crown.effective_law_key"),StrictJson.text(original.get("law_key")))),
                "direct Crown receipt must expect the original pending law");
        var choice=object(original.get("choice"));var balances=choice.get("quoted_post_balances_raw");
        StrictJson.require(balances!=null&&balances.isArray(),"original quoted post-balances required");
        for(var amount:balances) {
            StrictJson.require(amount.isArray()&&amount.size()==2,"original quoted post-balance pair required");
            String currency=StrictJson.text(amount.get(0));var balance=integer(amount.get(1));
            StrictJson.require(expected.values().contains(new ProposalLifecycle.ExpectedText(new ProposalLifecycle.FieldKey("crown.balance_"+currency+"_raw"),balance.toString())),
                    "direct Crown receipt must expect every original quoted post-balance");
        }
        StrictJson.require(applied.sessionId().equals(command.sessionId())&&applied.source().equals(command.source())
                &&ProposalLifecycle.compare(expected,applied.after(),applied.source(),applied.observerSchema(),applied.actual())==ProposalLifecycle.ObservationComparison.EXPECTED_FIELDS_MATCH,
                "direct Crown independent observation differs from original expected law/payment");
        ObjectNode resolved=original.deepCopy().put("status","enacted").put("material_result",true);
        resolved.put("stage","receipt_pending");resolved.set("ack",nativeResult(receipt.ack().orElseThrow()));
        resolved.set("native_receipt",object(nativeReceipt));
        var after=applied.after();resolved.set("post_context",context(after.game().pid(),after.frame().episodeRunId()));
        resolved.put("post_native_revision",after.frame().identity().nativeRevision()).put("post_date_raw",after.frame().identity().dateRaw());
        return result(old,Optional.of(raw(resolved)));
    }
    private Document crownApplied(Document old,ActionReceipt receipt,PlanningReadReceipt afterTerms,ActionPorts.OutcomeArchive archive)throws IOException {
        var original=object(old.pending().orElseThrow().original());var terms=nativeGovernance().crownFinalTermsRead().consumeTerms(afterTerms);var afterFrame=receipt.applied().orElseThrow().observation().after();var queried=afterTerms.request().before();
        StrictJson.require(queried.game().equals(receipt.command().before().game())&&afterTerms.request().source().equals(receipt.command().source())&&queried.frame().episodeRunId().equals(receipt.command().before().frame().episodeRunId())
                &&queried.frame().identity().nativeRevision().compareTo(afterFrame.frame().identity().nativeRevision())>=0,"Crown full final-terms query precedes the native receipt or crossed its original Game/source/episode");
        var lawGroup=terms.readback().payload().groups().stream().filter(value->value.key()==org.xar.ck3.control.wave3.governance.crownfinalterms.CrownFinalTerms.GroupKey.CROWN_AUTHORITY).findFirst().orElseThrow();
        StrictJson.require(StrictJson.text(original.get("law_key")).equals(lawGroup.activeLawKey()),"complete native final-terms post-state did not observe the submitted Crown law");
        var material=NativeEffectEvidence.load(receipt,archive,context().frameLoader());ObjectNode resolved=original.deepCopy().put("status","enacted").put("material_result",true);resolved.set("post_final_terms",StrictJson.parse(terms.completeConsume().bytes()));
        resolved.put("stage","receipt_pending");resolved.set("ack",nativeResult(receipt.ack().orElseThrow()));resolved.set("native_receipt",StrictJson.parse(material.compatibleResult().bytes()));var after=receipt.applied().orElseThrow().observation().after();resolved.set("post_context",context(after.game().pid(),after.frame().episodeRunId()));resolved.put("post_native_revision",after.frame().identity().nativeRevision()).put("post_date_raw",after.frame().identity().dateRaw());
        return result(old,Optional.of(raw(resolved)));
    }
    /** Cadence may consume only this holder's real canonical material publication, including its extra independent read. */
    public void requireMaterialSettlement(ContinuityStorePort.Session same,ActionReceipt actual)throws IOException {
        requireSession(same);StrictJson.require(OWNED.contains(actual.command().operation())&&actual.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED,"only original applied governance material can reset cadence");
        var head=same.head();var archive=core().archive().withSession(same);var canonical=ContinuityActionJournal.lookup(head.state(),actual.command().actionId(),archive).orElseThrow(()->new IOException("actual governance cadence parent absent from canonical action history"));
        StrictJson.require(Arrays.equals(ActionReceiptCodec.encodeReceipt(actual,archive),ActionReceiptCodec.encodeReceipt(canonical,archive)),"cadence supplied another original receipt");
        Domain domain=domain(actual.command());var current=decode(domain,available(same,domain).canonicalBody());var latest=object(current.latest().orElseThrow(()->new IOException("actual original governance material body missing")));
        StrictJson.require(originalId(actual.command()).equals(StrictJson.text(latest.get(domain==Domain.COUNCIL?"action_request_id":"action_id")))
                &&(domain==Domain.COUNCIL?"applied":"enacted").equals(StrictJson.text(latest.get("status")))
                &&(domain==Domain.COUNCIL||latest.get("material_result")!=null&&latest.get("material_result").isBoolean()&&latest.get("material_result").booleanValue()),"ACK/UNKNOWN/cold current-law observation cannot reset actual-action cadence");
        context().bindings().actualArchivedVerifier(actual.command().operation()).orElseThrow(()->new IOException("actual governance archive verifier missing")).verifier().verify(head,actual,archive);
        ExactRef receipt=archive.receiptReferenceOf(actual);
        var events=head.documents().stream().filter(pin->{Path path=Path.of(pin.reference().path());return path.getParent()!=null&&path.getParent().getFileName().toString().equals("ROOT-CONTINUITY-WINDOW-EVENTS");})
                .sorted(java.util.Comparator.comparing((WriterContracts.Pin pin)->Path.of(pin.reference().path()).getFileName().toString()).reversed()).toList();
        for(var pin:events) {
            var event=StrictJson.object(StrictJson.parse(same.readPinned(pin,WriterContracts.MAX_PIN_BYTES)),Set.of("sequence","at_utc","kind","details","identity","previous_sha256","after"));same.verifyPin(pin);
            if(!DomainBodies.IMPORT_KIND.equals(StrictJson.text(event.get("kind"))))continue;
            var details=GovernanceDomainDocument.object(event.get("details"));var body=DomainBodies.BodyRef.fromJson(details.get("domain_body"));if(!isDomainBodyContract(domain,body))continue;
            var source=StrictJson.object(details.get("source"),Set.of("original_body","producer_input","producer_sources","evidence"));StrictJson.require(ExactRef.fromJson(source.get("original_body")).equals(body.payload()),"canonical material event original body differs");
            var producer=archive.loadMaterial(ExactRef.fromJson(source.get("producer_input")));var json=StrictJson.parse(producer.bytes());if(!INPUT_SCHEMA.equals(StrictJson.text(json.get("schema"))))continue;var input=decodeInput(producer.bytes());
            if(input.domain()!=domain||input.kind()!=(domain==Domain.COUNCIL?Kind.COUNCIL_MATERIAL:domain==Domain.CROWN&&input.kind()==Kind.CROWN_APPLIED?Kind.CROWN_APPLIED:Kind.CROWN_MATERIAL)||!input.receipt().filter(receipt::equals).isPresent())continue;
            var bodyPin=same.capturePin(body.payload(),WriterContracts.MAX_PIN_BYTES);StrictJson.require(bodyPin.identity().equals(body.identity()),"canonical material body's original native file identity changed");same.verifyPin(bodyPin);
            var after=ContinuityState.fromJson(event.get("after"),head.state().machineId());same.requireHistoricalState(after.sequence(),org.xar.ck3.control.continuity.ContinuityJson.digest(after.toJson()));StrictJson.require(DomainBodies.reference(after,slot(domain)).filter(body::equals).isPresent(),"material publication is not in the surviving canonical domain chain");
            var old=decode(domain,readBody(same,input.previous().orElseThrow()));Document replayed;
            if(input.kind()==Kind.CROWN_APPLIED)replayed=crownAppliedDirect(old,actual,archive);
            else {var observed=checkedRead(input.read().orElseThrow(),archive);replayed=domain==Domain.COUNCIL?councilApplied(old,actual,observed,archive):crownApplied(old,actual,observed,archive);}
            StrictJson.require(Arrays.equals(encode(replayed),readBody(same,body.payload())),"actual full Council ROOT/Crown final-terms material reducer differs from canonical publication");
            var core=object(replayed.latest().orElseThrow());var fields=core.fields();while(fields.hasNext()) {var field=fields.next();StrictJson.require(Objects.equals(field.getValue(),latest.get(field.getKey())),"current governance material changed an original applied field");}return;
        }
        throw new IOException("actual canonical governance material publication/original read was not retained; no cadence credit");
    }
    private Document councilApplied(Document old,ActionReceipt receipt,PlanningReadReceipt read,ActionPorts.OutcomeArchive archive)throws IOException {
        var original=object(old.pending().orElseThrow().original());var root=root(read,archive);String position=StrictJson.text(object(original.get("request")).get("position_key"));var holder=seat(root,position);
        if(holder.isEmpty()||!integer(original.get("candidate_character_id")).equals(holder.orElseThrow().get("incumbent_character_id").isNull()?null:integer(holder.orElseThrow().get("incumbent_character_id"))))return old;
        StrictJson.require(read.request().before().game().equals(receipt.command().before().game())&&read.request().source().equals(receipt.command().source())&&read.request().before().frame().episodeRunId().equals(receipt.command().before().frame().episodeRunId())
                &&read.request().before().frame().identity().nativeRevision().compareTo(receipt.applied().orElseThrow().observation().after().frame().identity().nativeRevision())>=0,"independent Council ROOT read precedes material receipt or belongs to another Game");
        ObjectNode helper,material;
        if(receipt.command().operation().equals(GovernancePolicies.COUNCIL)) {
            var effect=receipt.applied().orElseThrow().observation();var leaf=object(StrictJson.parse(archive.loadMaterial(effect.supportingEvidence().getFirst()).bytes()));
            var compatible=archive.loadMaterial(ExactRef.fromJson(leaf.get("compatible_material")));material=StrictJson.object();material.set("council_assign_councillor_receipt",StrictJson.parse(compatible.bytes()));
            // The complete canonical verifier above already replayed all statuses. Locate its actual helper terminal ACK.
            helper=null;for(JsonNode item:leaf.get("continuations")) {var retained=org.xar.ck3.control.application.action.council.CouncilContinuationCodec.decodeEntry(archive.loadMaterial(ExactRef.fromJson(item.get("entry"))).bytes());if(retained.outcome().isPresent()) {var outcome=archive.load(retained.outcome().orElseThrow());if(outcome instanceof NativeActionPort.AckReceived ack) {var result=nativeResult(ack);if(result.has("council_assign_councillor_ack"))helper=result;}}}
            StrictJson.require(helper!=null,"canonical Council continuation lacks its original complete helper ACK");
        } else {
            var evidence=NativeEffectEvidence.load(receipt,archive,context().frameLoader());material=object(StrictJson.parse(evidence.compatibleResult().bytes()));helper=nativeResult(receipt.ack().orElseThrow());
        }
        var current=read.request().before().frame();var result=StrictJson.object().put("status","applied").put("episode_run_id",old.pending().orElseThrow().episodeRunId()).put("action_request_id",old.pending().orElseThrow().requestId()).put("candidate_character_id",integer(original.get("candidate_character_id")))
                .put("post_snapshot_id",current.snapshotId()).put("post_native_revision",current.identity().nativeRevision()).put("post_date_raw",current.identity().dateRaw()).put("next_turn_consumed",false);
        result.set("action_ack",helper);result.set("receipt",material);result.set("independent_position",holder.orElseThrow());result.set("independent_job_progress_observation",jobProgress(root,current.episodeRunId(),position,Optional.empty()));result.set("source_decision",original.get("source_decision"));return result(old,Optional.of(raw(result)));
    }
    private Document coldCrown(Document old,PlanningReadReceipt read,ActionPorts.OutcomeArchive archive)throws IOException {
        Pending pending=old.pending().orElseThrow(()->new IOException("cold Crown observation cannot replace a clear body"));var observed=read.request().before();var originalAction=findByRequest(session(),pending.requestId());
        StrictJson.require(coldContext(pending,observed.game().pid(),observed.frame().episodeRunId())||originalAction.filter(value->!value.command().before().game().equals(observed.game())).isPresent(),"same original native context requires its original material receipt, not cold law observation");
        var packet=crown(read,archive);var decoded=CrownAuthorityCodec.decodeReadback(StrictJson.canonical(packet));StrictJson.require(decoded.available(),"cold Crown current-law query unavailable");
        var original=object(pending.original());var result=original.deepCopy().put("status","cold_current_law_observed").put("material_result",false).put("episode_run_id",observed.frame().episodeRunId()).put("requested_law_key",StrictJson.text(original.get("law_key"))).put("effective_law_key",decoded.activeLawKey())
                .put("requested_law_observed",StrictJson.text(original.get("law_key")).equals(decoded.activeLawKey())).put("original_native_receipt_available",false).put("post_native_revision",observed.frame().identity().nativeRevision()).put("post_date_raw",observed.frame().identity().dateRaw());
        result.set("readback",packet);result.set("post_context",context(observed.game().pid(),observed.frame().episodeRunId()));result.putNull("native_receipt");return result(old,Optional.of(raw(result)));
    }
    private Document follow(Document old,PlanningReadReceipt read,List<ExactRef> queryRefs,ActionPorts.OutcomeArchive archive)throws IOException {
        StrictJson.require(old.pending().isEmpty()&&old.latest().isPresent(),"following observation cannot replace pending/UNKNOWN or invent an original result");var latest=object(old.latest().orElseThrow());var frame=read.request().before().frame();
        if(!frame.episodeRunId().equals(StrictJson.text(latest.get("episode_run_id"))))return old;
        if(old.domain()==Domain.COUNCIL) {
            var ack=object(object(latest.get("action_ack")).get("council_assign_councillor_ack"));String position=StrictJson.text(ack.get("position_key"));var root=root(read,archive);var seat=seat(root,position);if(seat.isEmpty())return old;
            boolean persists=!seat.orElseThrow().get("incumbent_character_id").isNull()&&integer(seat.orElseThrow().get("incumbent_character_id")).equals(integer(latest.get("candidate_character_id")));
            var role=Arrays.stream(CouncilSelection.Position.values()).filter(value->value.key().equals(position)).findFirst().orElseThrow();var queries=new ArrayList<PlanningReadReceipt>();
            for(ExactRef ref:queryRefs) {var query=checkedRead(ref,archive);StrictJson.require(query.request().before().equals(read.request().before())&&query.request().source().equals(read.request().source())&&query.request().sessionId().equals(read.request().sessionId()),"following Council root/query frame differs");queries.add(query);}
            var query=nativeGovernance().councilReads().replayPrivate(queries,role);var holder=seat.orElseThrow().get("incumbent_character_id");
            StrictJson.require(query.available()&&query.incumbent().equals(holder.isNull()?Optional.empty():Optional.of(integer(holder))),"independent following Council root and candidate query disagree");
            var next=latest.deepCopy().put("next_turn_consumed",persists).put("next_turn_snapshot_id",frame.snapshotId()).put("next_turn_native_revision",frame.identity().nativeRevision()).put("next_turn_date_raw",frame.identity().dateRaw());
            next.set("next_turn_position",seat.orElseThrow());next.set("next_turn_job_progress_observation",jobProgress(root,frame.episodeRunId(),position,old.latest()));next.set("previous_receipt_post_snapshot_id",required(object(object(latest.get("receipt")).get("council_assign_councillor_receipt")),"post_snapshot_id"));return latest(old,raw(next));
        }
        var packet=crown(read,archive);var decoded=CrownAuthorityCodec.decodeReadback(StrictJson.canonical(packet));if(!decoded.available())return old;
        var next=latest.deepCopy().put("next_turn_consumed",StrictJson.text(latest.get("law_key")).equals(decoded.activeLawKey())).put("next_turn_snapshot_id",frame.snapshotId()).put("next_turn_native_revision",frame.identity().nativeRevision()).put("next_turn_date_raw",frame.identity().dateRaw()).put("next_turn_effective_law_key",decoded.activeLawKey());next.set("next_turn_context",context(read.request().before().game().pid(),frame.episodeRunId()));return latest(old,raw(next));
    }
    private ObjectNode root(PlanningReadReceipt read,ActionPorts.OutcomeArchive archive)throws IOException {
        return decodeCouncilRoot(context().finance().definitions().contract(FinanceReadContracts.Query.ROOT),read);
    }
    static ObjectNode decodeCouncilRoot(org.xar.ck3.control.application.action.ReadContract<FinanceReadContracts.Packet> contract,PlanningReadReceipt read) {
        StrictJson.require(read.contractId().equals(contract.contractId())&&read.request().operation().equals(contract.operation()),"Council ROOT original differs from unique Finance contract");
        var packet=contract.decode(read);var result=object(org.xar.ck3.control.application.driver.DriverJson.toNode(packet.result()));var root=object(result.get("campaign_root_context"));var id=read.request().before().frame().identity();
        StrictJson.require("available".equals(StrictJson.text(root.get("status")))&&integer(root.get("snapshot_revision")).equals(id.nativeRevision())&&integer(root.get("date_raw")).equals(id.dateRaw())&&integer(root.get("player_character_id")).equals(id.player()),"independent ROOT frame/actor/source differs");return root;
    }
    private ObjectNode crown(PlanningReadReceipt read,ActionPorts.OutcomeArchive archive)throws IOException {var contract=nativeGovernance().planningReads().crown();StrictJson.require(read.contractId().equals(contract.contractId())&&read.request().operation().equals(contract.operation()),"Crown law observation differs from the actual installed source-bound contract");return object(StrictJson.parse(OpportunityJson.encode(contract.decode(read))));}
    private PlanningReadReceipt checkedRead(ExactRef ref,ActionPorts.OutcomeArchive archive) {var read=archive.loadRead(ref);StrictJson.require(archive.readReferenceOf(read).equals(ref),"original read reference changed");NativeRecordedEvidenceVerifier.requireRead(read,archive);return read;}
    private Optional<ActionReceipt> findByRequest(ContinuityStorePort.Session same,String id)throws IOException {return core().archive().inSession(same,archive->{var values=ContinuityActionJournal.receipts(uncheckedHead(same).state(),archive).stream().filter(receipt->OWNED.contains(receipt.command().operation())&&originalId(receipt.command()).equals(id)).toList();StrictJson.require(values.size()<=1,"duplicate original action request identity");return values.stream().findFirst();});}
    private static WriterContracts.Head uncheckedHead(ContinuityStorePort.Session same) {try{return same.head();}catch(IOException failure){throw new UncheckedIOException(failure);}}
    private static ObjectNode nativeResult(NativeActionPort.AckReceived ack) {var packet=StrictJson.object(StrictJson.parse(ack.originalFrame().bytes()),Set.of("type","protocol_version","request_id","ok","result"));StrictJson.require(ack.nativeOk()&&"command_result".equals(StrictJson.text(packet.get("type")))&&ack.requestId().equals(StrictJson.text(packet.get("request_id")))&&ack.originalResultToken().isPresent()&&StrictJson.parse(ack.originalResultToken().orElseThrow().bytes()).equals(packet.get("result")),"actual native ACK/token/frame differs");return object(packet.get("result"));}
    private static String diagnosticReason(PlanningReadResult.Unavailable<?> unavailable) {
        var reason = unavailable.reason();
        var original = unavailable.original();
        if (original.isEmpty() || !(original.get() instanceof NativeActionPort.AckReceived ack)) return reason;
        var sb = new StringBuilder();
        sb.append("nativeOk=").append(ack.nativeOk()).append(",requestId=").append(ack.requestId().length() <= 128 ? ack.requestId() : ack.requestId().substring(0, 128));
        var packet = ack.originalPacket();
        if (packet.length > 65540) {
            sb.append(",uninspected_large_frame=").append(packet.length);
        } else {
            try {
                var frame = org.xar.ck3.control.nativebridge.NativeWire.decode(packet);
                if (frame instanceof org.xar.ck3.control.nativebridge.NativeWire.CommandResult commandResult) {
                    var errorField = commandResult.error();
                    if (errorField.presence() == org.xar.ck3.control.nativebridge.NativeWire.Presence.ABSENT) {
                        sb.append(",error=absent");
                    } else if (errorField.presence() == org.xar.ck3.control.nativebridge.NativeWire.Presence.NULL) {
                        sb.append(",error=null");
                    } else {
                        var token = errorField.token().orElse(null);
                        if (token != null) {
                            var bytes = token.value();
                            var node = org.xar.ck3.control.nativebridge.NativeWire.parse(bytes);
                            if (node.isTextual()) {
                                var text = node.textValue();
                                sb.append(",error=").append(text.length() <= 512 ? text : text.substring(0, 512));
                            } else {
                                sb.append(",error=").append(node.getNodeType()).append(":").append(bytes.length);
                            }
                        } else {
                            sb.append(",error=unknown");
                        }
                    }
                    var wireIdMatch = commandResult.requestId().equals(ack.requestId()) ? "match" : "mismatch";
                    sb.append(",wireIdMatch=").append(wireIdMatch);
                } else {
                    sb.append(",frameType=").append(frame.getClass().getSimpleName());
                }
            } catch (java.io.IOException | RuntimeException diagnosticUnavailable) {
                sb.append(",decode_error");
            }
        }
        return sb.toString() + ":reason=" + reason;
    }
    private static String originalId(ActionCommand command) {var args=object(StrictJson.parse(OpportunityJson.encode(command.arguments())));if(org.xar.ck3.control.governance.crownauthority.CrownCallerSelection.isCaller(args))return StrictJson.text(args.get("caller_request_id"));return org.xar.ck3.control.governance.council.CouncilCallerSubmission.requestedId(args).orElseGet(()->RequestIds.forActionBody(ActionCodec.bodySha256(command)));}
    private static boolean coldContext(Pending pending,long pid,String episode) {var source=GovernanceDomainDocument.context(object(pending.original()).get("source_context"));return !integer(source.get("bridge_pid")).equals(BigInteger.valueOf(pid))||!StrictJson.text(source.get("episode_run_id")).equals(episode);}
    private static boolean hasConsumedAt(RawJson result,BigInteger revision,BigInteger date) {var row=object(result);return row.has("next_turn_native_revision")&&row.has("next_turn_date_raw")&&revision.equals(integer(row.get("next_turn_native_revision")))&&date.equals(integer(row.get("next_turn_date_raw")))
            ||row.has("post_native_revision")&&row.has("post_date_raw")&&revision.equals(integer(row.get("post_native_revision")))&&date.equals(integer(row.get("post_date_raw")));}
    private static ObjectNode context(long pid,String episode) {return StrictJson.object().put("bridge_pid",pid).put("episode_run_id",episode);}
    private static Domain domain(ActionCommand command) {StrictJson.require(OWNED.contains(command.operation()),"operation outside Council/Crown holding scope");return command.operation().equals(GovernancePolicies.CROWN)?Domain.CROWN:Domain.COUNCIL;}
    private static DomainBodies.Slot slot(Domain domain) {return domain==Domain.COUNCIL?DomainBodies.Slot.COUNCIL:DomainBodies.Slot.CROWN;}
    private static String schema(Domain domain) {return domain==Domain.COUNCIL?COUNCIL_SCHEMA:CROWN_SCHEMA;}
    private List<ExactRef> closure(Domain domain) {return domain==Domain.COUNCIL?sources.council():sources.crown();}
    private synchronized RootApplicationAssembly.Core core()throws IOException {if(core==null)throw new IOException("actual original governance Core not bound");return core;}
    private synchronized RootRuntimeContext context()throws IOException {if(context==null)throw new IOException("actual current governance Game not installed");return context;}
    private synchronized GovernanceRuntimeInstaller.Installed nativeGovernance()throws IOException {if(nativeGovernance==null)throw new IOException("actual native governance product not installed");return nativeGovernance;}
    private void requireSession(ContinuityStorePort.Session same)throws IOException {core().writer().requireSession(same);same.requireWriter(writerLock);}
    private ContinuityStorePort.Session session()throws IOException {var result=core().writer().borrowedSession();requireSession(result);return result;}
    private DomainBodies.Available available(ContinuityStorePort.Session same,Domain domain)throws IOException {requireSession(same);var read=same.readDomain(slot(domain));if(read instanceof DomainBodies.Available actual)return actual;throw new IOException("actual registered original "+domain+" body unavailable; missing/restored evidence is not CLEAR");}
    private byte[] readBody(ContinuityStorePort.Session same,ExactRef ref)throws IOException {return core().archive().readArtifact(same,ref,1_048_576);}
    private static byte[] encodeInput(Input input) {var row=StrictJson.object().put("schema",INPUT_SCHEMA).put("domain",input.domain().name()).put("kind",input.kind().name());row.set("previous",input.previous().map(ExactRef::toJson).orElse(null));row.set("command",input.command().map(ExactRef::toJson).orElse(null));row.set("prepared",input.prepared().map(ExactRef::toJson).orElse(null));row.set("receipt",input.receipt().map(ExactRef::toJson).orElse(null));row.set("read",input.read().map(ExactRef::toJson).orElse(null));row.set("initial",input.initial().map(ExactRef::toJson).orElse(null));var refs=row.putArray("preflight");input.preflight().forEach(ref->refs.add(ref.toJson()));return StrictJson.canonical(row);}
    private static Optional<ExactRef> optional(ObjectNode row,String field) {return row.get(field).isNull()?Optional.empty():Optional.of(ExactRef.fromJson(row.get(field)));}
    private static Input decodeInput(byte[] bytes) {var row=StrictJson.object(StrictJson.parse(bytes),Set.of("schema","domain","kind","previous","command","prepared","receipt","read","initial","preflight"));StrictJson.require(INPUT_SCHEMA.equals(StrictJson.text(row.get("schema")))&&row.get("preflight").isArray(),"exact governance publication source required");var refs=new ArrayList<ExactRef>();row.get("preflight").forEach(value->refs.add(ExactRef.fromJson(value)));return new Input(Domain.valueOf(StrictJson.text(row.get("domain"))),Kind.valueOf(StrictJson.text(row.get("kind"))),optional(row,"previous"),optional(row,"command"),optional(row,"prepared"),optional(row,"receipt"),optional(row,"read"),optional(row,"initial"),refs);}
    private static List<ExactRef> evidence(Input input) {var refs=new ArrayList<ExactRef>();java.util.stream.Stream.of(input.previous(),input.command(),input.prepared(),input.receipt(),input.read(),input.initial()).flatMap(Optional::stream).forEach(refs::add);refs.addAll(input.preflight());return List.copyOf(refs);}
}
