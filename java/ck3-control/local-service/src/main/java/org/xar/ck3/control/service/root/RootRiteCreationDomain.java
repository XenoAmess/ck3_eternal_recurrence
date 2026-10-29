package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.ritecreation.RiteCreationState;
import org.xar.ck3.control.application.ritecreation.RiteCreationDomainState;
import org.xar.ck3.control.application.ritecreation.RiteCreationState.*;
import org.xar.ck3.control.application.ritecreation.RiteCreationContract.*;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.*;
import static org.xar.ck3.control.application.ritecreation.RiteCreationCodec.*;

/** The one canonical writer owns every Rite once intent, including the complete old UNKNOWN history. */
final class RootRiteCreationDomain {
    private static final int MAX=ContinuityJson.DOMAIN_MAX_BYTES;
    private final List<ExactRef> sources;
    private RootApplicationAssembly.Core core;
    private DomainBodies.Registration registration;
    private final ThreadLocal<Transition> active=new ThreadLocal<>();
    RootRiteCreationDomain(List<ExactRef> sources){this.sources=List.copyOf(sources);StrictJson.require(!this.sources.isEmpty(),"complete Rite domain producer closure required");}
    synchronized void bindCore(RootApplicationAssembly.Core actual){StrictJson.require(core==null,"Rite Core is once bound");core=Objects.requireNonNull(actual);}
    private RootApplicationAssembly.Core core(){StrictJson.require(core!=null,"Rite Core is unbound");return core;}
    synchronized DomainBodies.Registration registration(){
        if(registration!=null)return registration;
        registration=new DomainBodies.Registration(DomainBodies.Slot.RITE_CREATION,RiteCreationDomainState.SCHEMA,MAX,sources,new DomainBodies.Verifier(){
            @Override public String verify(ContinuityState head,Optional<DomainBodies.BodyRef> previous,DomainBodies.ImportRequest request,byte[] raw)throws IOException{throw new IOException("Rite import requires the original full Head and live canonical writer Session");}
            @Override public String verify(WriterContracts.Head head,Optional<DomainBodies.BodyRef> previous,DomainBodies.ImportRequest request,byte[] raw)throws IOException{
                Session same=core().writer().borrowedSession();core().writer().requireSession(same);
                Transition transition=Objects.requireNonNull(active.get(),"Rite import needs its actual scoped producer");
                StrictJson.require(head.digest().equals(same.head().digest())&&request.slot()==DomainBodies.Slot.RITE_CREATION&&request.contractSchema().equals(RiteCreationDomainState.SCHEMA)
                        &&Arrays.equals(request.producerInput(),transition.input().bytes())&&request.evidence().equals(transition.evidence()),"Rite import changed original head/input/evidence");
                byte[] expected=transition.replay(same,readFull(same,previous)).encode().bytes();
                StrictJson.require(Arrays.equals(raw,expected),"actual Rite reducer did not produce the complete proposed body");return digest(head.digest(),request.producerInput(),raw);
            }
        });return registration;
    }
    State read(Session same)throws IOException{return fullState(same).javaState();}
    RiteCreationDomainState fullState(Session same)throws IOException{return readFull(same,DomainBodies.reference(same.head().state(),DomainBodies.Slot.RITE_CREATION)).orElseThrow(()->new IOException("Rite original full v2 once body absent; cold restore never assumes empty claims"));}
    private Optional<RiteCreationDomainState> readFull(Session same,Optional<DomainBodies.BodyRef> expected)throws IOException{
        core().writer().requireSession(same);var actual=same.readDomain(DomainBodies.Slot.RITE_CREATION);
        if(expected.isEmpty()){StrictJson.require(actual instanceof DomainBodies.Unavailable missing&&missing.reason()==DomainBodies.Reason.UNIMPORTED,"absent Rite body is not a missing or changed original");return Optional.empty();}
        if(!(actual instanceof DomainBodies.Available body))throw new IOException("original full Rite once body unavailable");
        StrictJson.require(body.reference().equals(expected.orElseThrow())&&body.reference().contractSchema().equals(RiteCreationDomainState.SCHEMA)&&body.head().equals(same.persistedHead()),"Rite body/schema/head changed");
        for(var pin:body.headSources())same.verifyPin(pin);var pin=same.capturePin(body.reference().payload(),MAX);
        StrictJson.require(pin.identity().equals(body.reference().identity()),"original Rite body native file identity changed");byte[] bytes=same.readPinned(pin,MAX);
        StrictJson.require(Arrays.equals(bytes,body.canonicalBody()),"Rite canonical full body differs from original bytes");same.verifyPin(pin);RiteCreationDomainState decoded=RiteCreationDomainState.decode(new RawJson(bytes));RootRiteCreationLegacyArchive.requireOriginalClosure(core().archive(),same,decoded);return Optional.of(decoded);
    }
    @FunctionalInterface interface Replay{State apply(Session same,Optional<State> previous)throws IOException;}
    @FunctionalInterface interface FullReplay{RiteCreationDomainState apply(Session same,Optional<RiteCreationDomainState> previous)throws IOException;}
    private record Transition(RawJson input,List<ExactRef> evidence,FullReplay producer){
        private Transition{Objects.requireNonNull(input);evidence=List.copyOf(evidence);Objects.requireNonNull(producer);StrictJson.require(!evidence.isEmpty()&&evidence.size()<=64,"bounded complete original Rite producer evidence required");}
        RiteCreationDomainState replay(Session same,Optional<RiteCreationDomainState> previous)throws IOException{return producer.apply(same,previous);}
    }
    DomainBodies.BodyRef publish(Session same,RawJson input,List<ExactRef> evidence,Replay replay)throws IOException{
        return publishFull(same,input,evidence,(original,previous)->{State actual=replay.apply(original,previous.map(RiteCreationDomainState::javaState));return previous.map(v->v.withJava(actual)).orElseGet(()->new RiteCreationDomainState(actual,Optional.empty()));});
    }
    DomainBodies.BodyRef publishFull(Session same,RawJson input,List<ExactRef> evidence,FullReplay replay)throws IOException{
        core().writer().requireSession(same);StrictJson.require(active.get()==null,"Rite imports cannot nest");Transition transition=new Transition(input,evidence,replay);
        var head=same.head();var previous=readFull(same,DomainBodies.reference(head.state(),DomainBodies.Slot.RITE_CREATION));RawJson next=transition.replay(same,previous).encode();
        StrictJson.require(next.bytes().length<=MAX,"complete Rite domain exceeds original registered bound");
        if(previous.isPresent()&&next.equals(previous.orElseThrow().encode()))return DomainBodies.reference(head.state(),DomainBodies.Slot.RITE_CREATION).orElseThrow();
        var archive=core().archive().withSession(same);ExactRef body=archive.preserveMaterial(next);StrictJson.require(archive.loadMaterial(body).equals(next),"Rite full body archive readback differs");
        var request=new DomainBodies.ImportRequest(DomainBodies.Slot.RITE_CREATION,RiteCreationDomainState.SCHEMA,body,input.bytes(),evidence,"rite:"+digest(head.digest(),input.bytes(),next.bytes()));
        active.set(transition);try{same.commitImport(same.previewImport(request));}finally{active.remove();}
        return DomainBodies.reference(same.head().state(),DomainBodies.Slot.RITE_CREATION).orElseThrow();
    }
    DomainBodies.BodyRef initializeFresh(RootRuntimeContext context,Session same,RootInitialEpisodeProof proof,RootRiteCreationRuntimeFactory.ScopeProvider scopes)throws IOException{
        var input=empty().put("kind","actual_fresh_rite_basis").put("episode",proof.episodeId());input.set("start_receipt",context.archive().withSession(same).receiptReferenceOf(proof.actualStart()).toJson());
        return publish(same,raw(input),proof.evidence(),(original,old)->{
            requireContext(context,original);proof.requireCurrent(original);proof.requireInitializationPredecessor(original,original.head());
            StrictJson.require(old.isEmpty()&&proof.source().equals(context.source())&&proof.sessionId().equals(context.game().sessionId()),"fresh Rite initialization cannot erase an old domain or cross Game");
            core().actions().withFrozen(original,lease->{StrictJson.require(lease.snapshot().actions().stream().allMatch(receipt->receipt.command().origin() instanceof CommandOrigin.Frontend&&receipt.settled()),"fresh Rite initialization follows no unresolved/gameplay intent");lease.assertCurrent();return null;});
            return RiteCreationState.initialize(State.empty(),new Basis(Initialization.FRESH,new EpisodeScope(proof.episodeId()),proof.currentObservation().frame().identity().player().intValueExact(),proof.evidence()));
        });
    }
    DomainBodies.BodyRef initializeFresh(RootRuntimeContext context,Session same,FreshCampaignContext proof)throws IOException{
        requireContext(context,same);proof.requireCurrent(same);proof.requireInitializationPredecessor(same,same.head());
        var existing=same.readDomain(DomainBodies.Slot.RITE_CREATION);
        if(existing instanceof DomainBodies.Available known){
            var retained=fullState(same).javaState().basis().orElseThrow(()->new IOException("retained Rite domain has no initialized basis"));
            StrictJson.require(retained.kind()==Initialization.FRESH&&retained.scope().equals(new EpisodeScope(proof.episodeId()))
                    &&retained.actor()==proof.currentObservation().frame().identity().player().intValueExact(),"retained Rite basis differs from the actual fresh campaign");
            proof.requireCurrent(same);return known.reference();
        }
        if(!(existing instanceof DomainBodies.Unavailable missing)||missing.reason()!=DomainBodies.Reason.UNIMPORTED)
            throw new IOException("fresh Rite cannot replace an unavailable existing body");
        ExactRef basis=proof.preserveOriginal(same);
        var input=empty().put("kind","fresh_campaign_rite_basis").put("episode",proof.episodeId());input.set("fresh_campaign",basis.toJson());
        var refs=new LinkedHashSet<ExactRef>(proof.evidence());refs.add(basis);
        return publish(same,raw(input),List.copyOf(refs),(original,old)->{
            requireContext(context,original);proof.requireCurrent(original);proof.requireInitializationPredecessor(original,original.head());
            StrictJson.require(proof.context()==context&&old.isEmpty(),"fresh Rite cannot replace an existing domain");
            return RiteCreationState.initialize(State.empty(),new Basis(Initialization.FRESH,new EpisodeScope(proof.episodeId()),
                    proof.currentObservation().frame().identity().player().intValueExact(),List.copyOf(refs)));
        });
    }
    DomainBodies.BodyRef initializeNext(RootRuntimeContext context,Session same,RootApplicationAssembly.EpisodeDomainInitializationProof proof)throws IOException{
        proof.requireCurrent(same,context);var refs=new LinkedHashSet<ExactRef>(proof.savedSemantic().references());refs.addAll(proof.currentSemantic().references());refs.add(proof.baselineMaterial().reference());refs.add(proof.oldDomain(DomainBodies.Slot.RITE_CREATION).payload());
        var input=empty().put("kind","actual_rite_episode_carry").put("initialization_kind",proof.kind().name());input.set("baseline",proof.baselineMaterial().reference().toJson());input.set("saved_semantic",proof.savedSemantic().semantic().toJson());input.set("current_semantic",proof.currentSemantic().semantic().toJson());
        var result=publish(same,raw(input),List.copyOf(refs),(original,old)->{
            requireContext(context,original);proof.requireCurrent(original,context);State actual=old.orElseThrow(()->new IOException("NEXT/FIRST Rite requires the actual existing complete once body"));
            return RiteCreationState.initialize(actual,new Basis(Initialization.valueOf(proof.kind().name()),new EpisodeScope(proof.currentDriver().session().episodeRunId()),proof.currentDriver().session().actorId().intValueExact(),List.copyOf(refs)));
        });proof.requireCurrent(same,context);return result;
    }
    void requireContext(RootRuntimeContext context,Session same)throws IOException{StrictJson.require(context.core()==core()&&context.borrowedSession()==same,"Rite producer requires its actual Core and original writer Session");core().writer().requireSession(same);context.game().verify();}
    private static String digest(String head,byte[] input,byte[] output){byte[] prefix=head.getBytes(java.nio.charset.StandardCharsets.US_ASCII),all=new byte[prefix.length+input.length+output.length];System.arraycopy(prefix,0,all,0,prefix.length);System.arraycopy(input,0,all,prefix.length,input.length);System.arraycopy(output,0,all,prefix.length+input.length,output.length);return ActionCodec.sha256(all);}
}
