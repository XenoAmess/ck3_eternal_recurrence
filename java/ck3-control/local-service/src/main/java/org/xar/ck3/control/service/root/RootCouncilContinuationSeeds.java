package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.council.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.application.action.council.CouncilContinuationModel.*;

/** Canonical original continuation custody. A decoded State or an absent restore attachment never creates an empty seed. */
public final class RootCouncilContinuationSeeds implements CouncilContinuationPorts.SeedAuthority {
    public static final String SCHEMA="xar.java.council-continuation-original-manifest/v1";
    private final Path lock;private final List<ExactRef> producerSources;
    @FunctionalInterface private interface CurrentInitial {void requireCurrent(ContinuityStorePort.Session same)throws IOException;}
    private record FreshHeld(ExactRef manifest,CurrentInitial actual) { }
    private Optional<FreshHeld> fresh=Optional.empty();
    private RootApplicationAssembly.Core core;private RootRuntimeContext context;
    public RootCouncilContinuationSeeds(Path originalWriterLock,List<ExactRef> exactContinuationProducers) {
        lock=Objects.requireNonNull(originalWriterLock).toAbsolutePath().normalize();producerSources=List.copyOf(exactContinuationProducers);
        StrictJson.require(!producerSources.isEmpty()&&producerSources.size()<=64&&producerSources.stream().allMatch(ref->ref.bytes()>0),"actual complete continuation producer closure required");
    }
    public synchronized void bindCore(RootApplicationAssembly.Core actual)throws IOException {
        StrictJson.require((core==null||core==actual)&&actual.configuration().ledger().lock().toAbsolutePath().normalize().equals(lock),"continuation originals belong to the exact original Core/writer");core=actual;
    }
    public synchronized void installContext(RootRuntimeContext actual)throws IOException {StrictJson.require(actual.core()==core(),"continuation seed cannot adopt another Core");context=Objects.requireNonNull(actual);fresh=Optional.empty();}
    public ExactRef preserveFresh(ContinuityStorePort.Session same,RootInitialEpisodeProof actual)throws IOException {
        requireSession(same);actual.requireCurrent(same);
        return preserveFresh(same,"FRESH_INITIAL_ENTRY",actual.preserveOriginal(same),actual::requireCurrent);
    }
    public ExactRef preserveFresh(ContinuityStorePort.Session same,FreshCampaignContext actual)throws IOException {
        requireSession(same);StrictJson.require(actual.context()==context(),"fresh continuation belongs to another installed Game");actual.requireCurrent(same);
        return preserveFresh(same,"FRESH_CAMPAIGN",actual.preserveOriginal(same),actual::requireCurrent);
    }
    private ExactRef preserveFresh(ContinuityStorePort.Session same,String kind,ExactRef basis,CurrentInitial actual)throws IOException {
        requireSession(same);actual.requireCurrent(same);StrictJson.require(same.readDomain(DomainBodies.Slot.COUNCIL_CONTINUATION) instanceof DomainBodies.Unavailable unavailable
                &&unavailable.reason()==DomainBodies.Reason.UNIMPORTED,"a fresh seed cannot replace an existing or restored continuation original");
        var row=StrictJson.object().put("schema",SCHEMA).put("kind",kind);row.set("initial_basis",basis.toJson());row.putNull("historical_state");row.putNull("body");var ref=archive(same).preserveMaterial(new RawJson(StrictJson.canonical(row)));synchronized(this){fresh=Optional.of(new FreshHeld(ref,actual));}return ref;
    }
    /** Capture this same writer's actual body before SAVE; callers store this exact manifest as an original attachment. */
    public ExactRef preserveCanonical(ContinuityStorePort.Session same)throws IOException {
        requireSession(same);var read=same.readDomain(DomainBodies.Slot.COUNCIL_CONTINUATION);if(!(read instanceof DomainBodies.Available actual))throw new IOException("original continuation domain unavailable; no substitute manifest");
        requireBody(actual.reference());var head=same.head();var bound=archive(same);ExactRef state=bound.preserveMaterial(new RawJson(ContinuityJson.canonical(head.state().toJson())));
        // Validate every active/completed original before publishing its wrapper, without issuing or collecting anything.
        State decoded=CouncilContinuationCodec.decodeState(actual.canonicalBody());verifyClosure(same,head,decoded,bound,new HashSet<>(),0);
        var row=StrictJson.object().put("schema",SCHEMA).put("kind","CANONICAL_ORIGINAL");row.putNull("initial_basis");row.set("historical_state",state.toJson());row.set("body",actual.reference().toJson());return bound.preserveMaterial(new RawJson(StrictJson.canonical(row)));
    }
    @Override public State readCompleteOriginal(ContinuityStorePort.Session same,WriterContracts.Head actualHead,ExactRef manifest,ActionPorts.OutcomeArchive originalArchive)throws IOException {
        requireSession(same);StrictJson.require(same.head().digest().equals(actualHead.digest())&&same.head().documents().equals(actualHead.documents()),"continuation seed requires the actual original locked Head");
        var bound=archive(same);RawJson bytes=bound.loadMaterial(manifest);StrictJson.require(bound.materialReferenceOf(bytes).equals(manifest),"complete original manifest bytes differ");
        var row=StrictJson.object(StrictJson.parse(bytes.bytes()),Set.of("schema","kind","initial_basis","historical_state","body"));StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))),"bare decoded continuation State is not an original manifest");
        String kind=StrictJson.text(row.get("kind"));
        if("FRESH_INITIAL_ENTRY".equals(kind)||"FRESH_CAMPAIGN".equals(kind)) {
            StrictJson.require(row.get("historical_state").isNull()&&row.get("body").isNull(),"fresh initial seed cannot contain a restored body");
            FreshHeld held;synchronized(this){held=fresh.orElse(null);}if(held!=null&&held.manifest().equals(manifest))held.actual().requireCurrent(same);
            ExactRef basis=ExactRef.fromJson(row.get("initial_basis"));
            if("FRESH_CAMPAIGN".equals(kind))FreshCampaignContext.replayOriginal(context(),same,basis).requireInitializationPredecessor(same,actualHead);
            else RootInitialEpisodeProof.replayOriginal(context(),same,basis).requireInitializationPredecessor(same,actualHead);
            return new State(actualHead.state().machineId(),Optional.empty(),List.of(),Optional.empty());
        }
        StrictJson.require("CANONICAL_ORIGINAL".equals(StrictJson.text(row.get("kind")))&&row.get("initial_basis").isNull(),"known canonical original continuation manifest required");
        ExactRef history=ExactRef.fromJson(row.get("historical_state"));var historicalRaw=bound.loadMaterial(history);StrictJson.require(bound.materialReferenceOf(historicalRaw).equals(history),"original historical state bytes differ");
        var historical=ContinuityState.fromJson(org.xar.ck3.control.continuity.ContinuityJson.parseObject(historicalRaw.bytes(),org.xar.ck3.control.continuity.ContinuityJson.LEDGER_MAX_BYTES),actualHead.state().machineId());same.requireHistoricalState(historical.sequence(),ContinuityJson.digest(historical.toJson()));
        var body=DomainBodies.BodyRef.fromJson(row.get("body"));requireBody(body);StrictJson.require(DomainBodies.reference(historical,DomainBodies.Slot.COUNCIL_CONTINUATION).filter(body::equals).isPresent(),"manifest body was not in the actual surviving canonical historical state");
        var pin=same.capturePin(body.payload(),MAX_BODY_BYTES);StrictJson.require(pin.identity().equals(body.identity()),"original continuation body native file identity differs");byte[] original=same.readPinned(pin,MAX_BODY_BYTES);same.verifyPin(pin);
        State state=CouncilContinuationCodec.decodeState(original);verifyClosure(same,actualHead,state,bound,new HashSet<>(),0);return state;
    }
    private void verifyClosure(ContinuityStorePort.Session same,WriterContracts.Head head,State state,ActionPorts.OutcomeArchive archive,Set<ExactRef> seen,int depth)throws IOException {
        State current=state;for(int count=depth;;count++) {
        StrictJson.require(count<=4096&&seen.size()<=100_000&&current.machineId().equals(head.state().machineId())&&current.active().isPresent()==!current.records().isEmpty(),"bounded original same-machine complete continuation closure required");
        var records=new ArrayList<Retained>();long previousSequence=0;
        for(ExactRef ref:current.records()) {
            StrictJson.require(seen.add(ref)&&seen.size()<=100_000,"continuation closure repeats an immutable row or exceeds its explicit bound");var raw=archive.loadMaterial(ref);StrictJson.require(archive.materialReferenceOf(raw).equals(ref),"original continuation row bytes changed");Entry entry=CouncilContinuationCodec.decodeEntry(raw.bytes());var request=entry.request();
            StrictJson.require(current.active().filter(request.scope()::equals).isPresent()&&request.issuedSequence()>previousSequence,"original scope/order differs from complete retained manifest");previousSequence=request.issuedSequence();
            var parent=archive.loadReceipt(request.originalParentReceipt());ContinuityActionJournal.requireHistoricalReceipt(head.state(),parent,archive);
            StrictJson.require(parent.command().actionId().equals(request.scope().parentActionId())&&parent.bodySha256().equals(request.scope().parentBodySha256())
                    &&parent.command().operation().value().equals("private-assign-councillor-v1")&&ActionTransitions.attempt(parent.state()).filter(value->value.requestId().equals(request.scope().originalAttemptRequestId())).isPresent(),"original continuation parent/attempt identity differs");
            var prepared=archive.loadRequest(request.preparedRequest());StrictJson.require(prepared.step().equals(request.stage().step())&&prepared.additionalFields().objectFieldNames().isEmpty(),"original fixed continuation preparation differs");
            for(ExactRef evidence:request.supportingEvidence()) {var material=archive.loadMaterial(evidence);StrictJson.require(archive.materialReferenceOf(material).equals(evidence),"original continuation preflight material missing/changed");}
            if(entry.status()!=Status.ISSUED) {
                var custody=entry.issued().orElseThrow();var issuedRaw=archive.loadMaterial(custody.record());StrictJson.require(archive.materialReferenceOf(issuedRaw).equals(custody.record()),"original issued row changed");var issued=CouncilContinuationCodec.decodeEntry(issuedRaw.bytes());StrictJson.require(issued.status()==Status.ISSUED&&issued.request().equals(request),"original result erased its issued custody");
                var outcome=archive.load(entry.outcome().orElseThrow());StrictJson.require(outcome.requestId().equals(request.requestId())&&(entry.status()==Status.ACK)==(outcome instanceof NativeActionPort.AckReceived ack&&ack.outbound().isPresent()),"original continuation ACK/UNKNOWN changed; no recovery replay permitted");
                for(ExactRef evidence:List.of(custody.record(),custody.domainPayload())) {var material=archive.loadMaterial(evidence);StrictJson.require(archive.materialReferenceOf(material).equals(evidence),"complete original issued body missing/changed");}
                var eventPin=same.capturePin(custody.event(),MAX_BODY_BYTES);StrictJson.require(head.documents().contains(eventPin),"issued original event is absent from the surviving canonical chain");same.readPinned(eventPin,MAX_BODY_BYTES);same.verifyPin(eventPin);
            }
            records.add(new Retained(ref,entry));
        }
        if(current.completedScopeChain().isPresent()) {
            ExactRef closed=current.completedScopeChain().orElseThrow();StrictJson.require(seen.add(closed),"completed continuation chain is cyclic");var raw=archive.loadMaterial(closed);StrictJson.require(archive.materialReferenceOf(raw).equals(closed),"original completed-scope bytes changed");
            var row=StrictJson.object(StrictJson.parse(raw.bytes()),Set.of("schema","previous_state","settled_parent"));StrictJson.require("xar.java-council-closed-scope/v1".equals(StrictJson.text(row.get("schema"))),"complete original closed-scope record required");
            ExactRef previous=ExactRef.fromJson(row.get("previous_state"));StrictJson.require(seen.add(previous),"completed continuation state is cyclic");var prior=archive.loadMaterial(previous);StrictJson.require(archive.materialReferenceOf(prior).equals(previous),"original prior continuation state changed");
            State old=CouncilContinuationCodec.decodeState(prior.bytes());var parent=archive.loadReceipt(ExactRef.fromJson(row.get("settled_parent")));ContinuityActionJournal.requireHistoricalReceipt(head.state(),parent,archive);
            var priorRows=old.records().stream().map(ref->new Retained(ref,CouncilContinuationCodec.decodeEntry(archive.loadMaterial(ref).bytes()))).toList();
            var rotated=CouncilContinuationReducer.rotate(old,priorRows,parent,closed);StrictJson.require(rotated.completedScopeChain().equals(current.completedScopeChain()),"completed scope does not replay through the original real reducer");current=old;
        } else return;
        }
    }
    private void requireBody(DomainBodies.BodyRef body)throws IOException {StrictJson.require(body.slot()==DomainBodies.Slot.COUNCIL_CONTINUATION&&body.contractSchema().equals(CouncilContinuationModel.SCHEMA)&&body.producerSources().equals(producerSources),"complete original continuation contract/source closure differs");for(ExactRef ref:producerSources) {var same=core().writer().borrowedSession();var pin=same.capturePin(ref,WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);}}
    private ActionPorts.OutcomeArchive archive(ContinuityStorePort.Session same)throws IOException {requireSession(same);return core().archive().withSession(same);}
    private void requireSession(ContinuityStorePort.Session same)throws IOException {core().writer().requireSession(same);same.requireWriter(lock);}
    private synchronized RootApplicationAssembly.Core core()throws IOException {if(core==null)throw new IOException("actual continuation original Core not bound");return core;}
    private synchronized RootRuntimeContext context()throws IOException {if(context==null)throw new IOException("actual continuation fresh-entry context not installed");return context;}
}
