package org.xar.ck3.control.application.history;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.effects.RootGuardEvidence.WriterPoint;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.application.history.DriverPostKnownReadFailureMaterial.*;

/** One source-reproduced post-Known failure row. It is neither a failed Native attempt nor current-frame authority. */
public final class DriverPostKnownReadFailureRowProducer {
    public static final String SOURCE_FIELD="post_known_read_failure_source";
    public static final String SOURCE_SCHEMA="xar.driver-post-known-read-failure-source/v1";
    /** Original Python query_army_strengths exception branch history spelling, separate from its logical read operation. */
    public static final String ORIGINAL_COMMAND="query-army-strengths-v1";
    private DriverPostKnownReadFailureRowProducer(){ }
    public record ReadBinding(String contractId,String requestId,ExactRef read,ExactRef acknowledgement,ExactRef definitionSource,
            ExactRef decoderSource,ReadContract.PermissionMode permissionMode,ReadContract.WireProfile wireProfile,
            ReadContract.GuardMode guardMode,Optional<String> requiredCapability,String permissionKey) {
        public ReadBinding {
            StrictJson.text(contractId);StrictJson.text(requestId);StrictJson.text(permissionKey);Objects.requireNonNull(permissionMode);
            Objects.requireNonNull(wireProfile);Objects.requireNonNull(guardMode);requiredCapability=Objects.requireNonNull(requiredCapability);
            requiredCapability.ifPresent(StrictJson::text);for(var ref:List.of(read,acknowledgement,definitionSource,decoderSource))positive(ref);
            StrictJson.require(guardMode==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                    &&(permissionMode==ReadContract.PermissionMode.ADVERTISED_CAPABILITY)==requiredCapability.isPresent(),"exact original gameplay read permission binding required");
        }
    }
    public record Before(ExactRef fullDriver,ExactRef fullKnown,ExactRef manifest,ExactRef nativeFrame,WriterPoint writerPoint) {
        public Before {for(var ref:List.of(fullDriver,fullKnown,manifest,nativeFrame))positive(ref);Objects.requireNonNull(writerPoint);}
    }
    public record Source(ReadBinding finalRead,List<ReadBinding> earlierReads,Failure failure,Before before,
            ObservationIdentity sourceFrame,G2Source source,String sessionId,BigInteger connectionGeneration,
            List<ExactRef> supportingEvidence,List<ExactRef> producerSources) {
        public Source {
            Objects.requireNonNull(finalRead);earlierReads=List.copyOf(earlierReads);Objects.requireNonNull(failure);Objects.requireNonNull(before);
            Objects.requireNonNull(sourceFrame);Objects.requireNonNull(source);StrictJson.text(sessionId);
            StrictJson.require(connectionGeneration!=null&&connectionGeneration.signum()>0&&connectionGeneration.compareTo(StrictJson.UINT64_MAX)<=0,"actual connection generation required");
            supportingEvidence=refs(supportingEvidence,1,768);producerSources=refs(producerSources,1,64);
            StrictJson.require(earlierReads.size()==failure.kind().requiredEarlierReads()&&source.machineId().equals(sourceFrame.machineId()),"finite failure peer count/source required");
            var required=new LinkedHashSet<ExactRef>(producerSources);required.addAll(failure.sourceClosure());
            for(var binding:all(finalRead,earlierReads))required.addAll(List.of(binding.read(),binding.acknowledgement(),binding.definitionSource(),binding.decoderSource()));
            required.addAll(List.of(before.fullDriver(),before.fullKnown(),before.manifest(),before.nativeFrame()));
            StrictJson.require(supportingEvidence.containsAll(required),"complete failure/read/predecessor/source closure required");
        }
    }
    /** Closed error row: result is absent, not null or an invented failed Native response. */
    public record RawHistoryRow(long index,String command,boolean ok,String error,Source source) {
        public RawHistoryRow {StrictJson.safe(index,1);StrictJson.text(command);Objects.requireNonNull(source);StrictJson.require(ORIGINAL_COMMAND.equals(command)&&!ok&&source.failure().error().equals(error),"exact original failure command/error and no successful result required");}
        public ObjectNode toJson(){var row=StrictJson.object();row.put("index",index);row.put("command",command);row.put("ok",false);row.put("error",error);row.set(SOURCE_FIELD,sourceJson(source));return row;}
        public byte[] encode(){return StrictJson.canonical(toJson(),RawJson.MAXIMUM_BYTES);}
        public DriverStateSnapshot.HistoryEntry historyEntry(){return new DriverStateSnapshot.HistoryEntry(index,new DriverStateSnapshot.Value(encode()));}
    }
    /** Only the original frozen authority, identical installed contracts and actual Known values mint this candidate. */
    public static final class Candidate {
        private final RawHistoryRow row;private final ExactRef rowReference;private final DriverStateAssembler authority;private final DriverReadHistoryPublisher publisher;
        private final RootReadContractCatalog catalog;private final ReadContract<?> contract;private final PlanningReadResult.Known<?> finalKnown;
        private final List<? extends PlanningReadResult.Known<?>> earlier;private final DriverSnapshotFacts.Known before;
        private Candidate(RawHistoryRow row,ExactRef reference,DriverStateAssembler authority,DriverReadHistoryPublisher publisher,RootReadContractCatalog catalog,
                ReadContract<?> contract,PlanningReadResult.Known<?> finalKnown,List<? extends PlanningReadResult.Known<?>> earlier,DriverSnapshotFacts.Known before){
            this.row=row;rowReference=reference;this.authority=authority;this.publisher=publisher;this.catalog=catalog;this.contract=contract;this.finalKnown=finalKnown;this.earlier=List.copyOf(earlier);this.before=before;
        }
        public RawHistoryRow row(){return row;}public Source source(){return row.source();}public ExactRef rowReference(){return rowReference;}
        public DriverStateSnapshot.HistoryEntry historyEntry(){return row.historyEntry();}public ExactRef beforeKnownReference(){return source().before().fullKnown();}
        public ExactRef finalReadReference(){return source().finalRead().read();}public DriverSnapshotFacts.Known before(){return before;}
        public ReadContract<?> identicalFinal(){return contract;}public PlanningReadResult.Known<?> finalKnown(){return finalKnown;}
        public List<? extends PlanningReadResult.Known<?>> earlierKnown(){return earlier;}
    }
    private record ReadOriginal(ReadBinding binding,PlanningReadReceipt receipt,ReadContract<?> contract,List<ExactRef> support){ }
    private record BeforeOriginal(DriverSnapshotFacts.Known known,ExactRef driver,ExactRef manifest,ExactRef nativeFrame,RawJson encodedKnown){ }

    /** Every qualification precedes preservation. The real complete Known is retained first, then the unique row (at most two artifacts). */
    public static <T> Candidate prepare(ContinuityStorePort.Session same,ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,
            DriverStateAssembler authority,DriverReadHistoryPublisher publisher,ReadContract<T> identicalFinal,PlanningReadResult.Known<T> actualFinal,
            List<? extends PlanningReadResult.Known<?>> earlierKnown,DriverSnapshotFacts.Known exactCurrentBeforeKnown,
            long nextIndex,List<ExactRef> actualProducerSources)throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(authority);Objects.requireNonNull(publisher);Objects.requireNonNull(actualFinal);Objects.requireNonNull(exactCurrentBeforeKnown);
        var earlier=List.copyOf(earlierKnown);var producers=refs(actualProducerSources,1,64);StrictJson.safe(nextIndex,1);
        return authority.withFrozenFacts(same,frozen->{
            StrictJson.require(frozen.state()==exactCurrentBeforeKnown,"post-Known failure requires the identical actual frozen predecessor Known");
            publisher.requirePostKnownFailureCustody(same,authority,catalog,identicalFinal,actualFinal,earlier,exactCurrentBeforeKnown);
            StrictJson.require(nextIndex>exactCurrentBeforeKnown.driver().commandHistory().size(),"failure index precedes its actual Driver history frontier");
            WriterContracts.Head head=same.head();StrictJson.require(frozen.actions().headSha256().equals(head.digest()),"failure crossed its actual writer/actions head");
            ReadOriginal last=read(bound,catalog,identicalFinal,actualFinal.receipt(),actualFinal.originalReceipt(),same);requireValue(identicalFinal,actualFinal);
            var peers=new ArrayList<ReadOriginal>();for(var actual:earlier){var contract=installed(catalog,actual.receipt().contractId());peers.add(read(bound,catalog,contract,actual.receipt(),actual.originalReceipt(),same));requireValue(contract,actual);}
            Failure failure=reproduce(identicalFinal,last.receipt(),peers);BeforeOriginal before=before(bound,last.receipt(),exactCurrentBeforeKnown);
            StrictJson.require(RootGuardEvidence.writerPoint(last.receipt().after().binding(),bound).equals(new WriterPoint(head.state().sequence(),head.digest())),"failure final observation crossed its original writer head");
            validateBeforeWrite(last,peers,failure,before,producers);
            var sourcePins=sourcePins(same,producers,last,peers,failure);verifyHead(same,head);verifyPins(same,sourcePins);
            // Never call materialReferenceOf for a first Known artifact: Dynamic's current custody does not imply archival retention.
            ExactRef known=bound.preserveMaterial(before.encodedKnown());requireMaterial(bound,known,before.encodedKnown(),true);
            Source source=derive(last,peers,failure,before,known,new WriterPoint(head.state().sequence(),head.digest()),producers);
            RawHistoryRow row=new RawHistoryRow(nextIndex,ORIGINAL_COMMAND,false,failure.error(),source);
            RawJson encoded=new RawJson(row.encode());ExactRef reference=bound.preserveMaterial(encoded);requireMaterial(bound,reference,encoded,false);
            StrictJson.require(decode(bound.loadMaterial(reference).bytes()).equals(row),"post-Known failure changed during archive serialization");
            verifyPins(same,sourcePins);verifyHead(same,head);StrictJson.require(frozen.state()==exactCurrentBeforeKnown,"failure archival changed its frozen predecessor");
            return new Candidate(row,reference,authority,publisher,catalog,identicalFinal,actualFinal,earlier,exactCurrentBeforeKnown);
        });
    }
    /** Original private candidate revalidation; no preservation, current witness, Native query or publication. */
    public static Candidate replay(ContinuityStorePort.Session same,ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,
            DriverStateAssembler authority,DriverReadHistoryPublisher publisher,ReadContract<?> identicalFinal,PlanningReadResult.Known<?> actualFinal,
            List<? extends PlanningReadResult.Known<?>> earlierKnown,Candidate candidate)throws IOException {
        Objects.requireNonNull(candidate);StrictJson.require(candidate.authority==authority&&candidate.publisher==publisher&&candidate.catalog==catalog&&candidate.contract==identicalFinal
                &&candidate.finalKnown==actualFinal&&sameIdentities(candidate.earlier,earlierKnown),"failure candidate crossed actual authority/catalog/Known identities");
        return authority.withFrozenFacts(same,frozen->{StrictJson.require(frozen.state()==candidate.before,"failure predecessor is no longer the identical current Known");
            publisher.requirePostKnownFailureCustody(same,authority,catalog,identicalFinal,actualFinal,earlierKnown,candidate.before);
            replayOriginals(same,bound,catalog,candidate.row());requireMaterial(bound,candidate.rowReference(),new RawJson(candidate.row().encode()),false);return candidate;});
    }
    /** Read-only historical DATA replay. The authentic original head is an ancestor, never a warm Prepared or new Known permission. */
    public static RawHistoryRow replayOriginals(ContinuityStorePort.Session same,ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,RawHistoryRow row)throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(row);WriterContracts.Head current=same.head();Source source=row.source();
        var point=source.before().writerPoint();same.requireHistoricalHead(point.sequence(),point.digest());
        ReadContract<?> contract=installed(catalog,source.finalRead());PlanningReadReceipt finalReceipt=bound.loadRead(source.finalRead().read());
        ReadOriginal last=read(bound,catalog,contract,finalReceipt,source.finalRead().read(),same);
        var peers=new ArrayList<ReadOriginal>();for(var binding:source.earlierReads())peers.add(read(bound,catalog,installed(catalog,binding),bound.loadRead(binding.read()),binding.read(),same));
        Failure failure=reproduce(contract,last.receipt(),peers);
        var facts=observation(bound,source.before().manifest(),source.before().fullDriver(),source.before().nativeFrame());
        RawJson encodedKnown=bound.loadFullMaterial(source.before().fullKnown());requireMaterial(bound,source.before().fullKnown(),encodedKnown,true);
        DriverSnapshotFacts.Known known=DriverSnapshotFacts.decodeKnownOriginal(encodedKnown,Optional.of(facts));
        StrictJson.require(row.index()>known.driver().commandHistory().size()&&RootGuardEvidence.writerPoint(finalReceipt.after().binding(),bound).equals(point),"historical failure index/head differs from its actual observation frontier");
        BeforeOriginal before=before(bound,finalReceipt,known);StrictJson.require(source.before().fullDriver().equals(before.driver())
                &&source.before().manifest().equals(before.manifest())&&source.before().nativeFrame().equals(before.nativeFrame())
                &&Arrays.equals(before.encodedKnown().bytes(),encodedKnown.bytes()),"historical complete predecessor original changed");
        var pins=sourcePins(same,source.producerSources(),last,peers,failure);
        Source replayed=derive(last,peers,failure,before,source.before().fullKnown(),point,source.producerSources());
        StrictJson.require(source.equals(replayed)&&row.command().equals(ORIGINAL_COMMAND),"source-owned pure failure/read/predecessor differs from retained row");
        requireMaterial(bound,bound.materialReferenceOf(new RawJson(row.encode())),new RawJson(row.encode()),false);
        verifyPins(same,pins);verifyHead(same,current);return row;
    }
    private static Source derive(ReadOriginal last,List<ReadOriginal> peers,Failure failure,BeforeOriginal before,ExactRef known,WriterPoint point,List<ExactRef> producers){
        var evidence=new LinkedHashSet<ExactRef>();for(var item:all(last,peers))evidence.addAll(item.support());
        evidence.addAll(failure.sourceClosure());evidence.addAll(producers);evidence.addAll(List.of(before.driver(),known,before.manifest(),before.nativeFrame()));
        var receipt=last.receipt();return new Source(last.binding(),peers.stream().map(ReadOriginal::binding).toList(),failure,
                new Before(before.driver(),known,before.manifest(),before.nativeFrame(),point),receipt.request().before(),receipt.request().source(),receipt.request().sessionId(),
                receipt.before().binding().connectionGeneration(),List.copyOf(evidence),producers);
    }
    private static ReadOriginal read(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,ReadContract<?> identical,
            PlanningReadReceipt expected,ExactRef reference,ContinuityStorePort.Session same)throws IOException {
        Objects.requireNonNull(bound);Objects.requireNonNull(catalog);Objects.requireNonNull(identical);positive(reference);
        StrictJson.require(catalog.containsIdentity(identical)&&identical.hasPureReplay()&&identical.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                &&identical.wireProfile()==ReadContract.WireProfile.EXECUTE_STEP&&identical.operation().value().equals(ORIGINAL_COMMAND),"identical installed finite Army gameplay execute read required");
        var installations=catalog.installed().stream().filter(value->value.contract()==identical).toList();StrictJson.require(installations.size()==1,"one original definition/decoder installation required");
        PlanningReadReceipt receipt=bound.loadRead(reference);StrictJson.require(receipt.equals(expected)&&bound.readReferenceOf(receipt).equals(reference)
                &&receipt.contractId().equals(identical.contractId())&&receipt.request().operation().equals(identical.operation())&&receipt.request().origin() instanceof CommandOrigin.Gameplay,"actual final/peer read archive identity differs");
        NativeRecordedEvidenceVerifier.requireRead(receipt,bound);var evidence=new LinkedHashSet<ExactRef>();
        for(var guard:List.of(receipt.before(),receipt.after())) {
            StrictJson.require(guard.guardMode()==identical.guardMode()&&guard.paused()&&guard.mapReady()&&guard.playerAlive(),"failure read lost living paused gameplay guards");
            RootGuardEvidence.requireHistory(guard.binding(),bound,same);packet(bound,guard.binding().nativeEvidence());packet(bound,guard.binding().capabilityEvidence());
            evidence.add(guard.binding().nativeEvidence());evidence.add(guard.binding().capabilityEvidence());
            for(var ref:guard.binding().supportingEvidence()){requireMaterial(bound,ref,bound.loadMaterial(ref),false);evidence.add(ref);}
        }
        StrictJson.require(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()),"post-Known read crossed its complete semantic/modal binding");
        ExactRef ack=bound.referenceOf(receipt.original());var binding=new ReadBinding(identical.contractId(),receipt.requestId(),reference,ack,identical.sourceRef(),installations.getFirst().decoderSource(),
                identical.permissionMode(),identical.wireProfile(),identical.guardMode(),identical.requiredCapability(),identical.permissionKey());
        evidence.addAll(List.of(reference,ack,binding.definitionSource(),binding.decoderSource()));return new ReadOriginal(binding,receipt,identical,List.copyOf(evidence));
    }
    private static Failure reproduce(ReadContract<?> contract,PlanningReadReceipt last,List<ReadOriginal> peers) {
        Kind declared=contract.postKnownFailureKind().orElseThrow(()->new IllegalArgumentException("no source-installed finite post-Known failure verifier"));
        StrictJson.require(peers.size()==declared.requiredEarlierReads(),"exact finite failure peer count required");
        Failure actual=contract.reproducePostKnownFailure(last,peers.stream().map(ReadOriginal::receipt).toList())
                .orElseThrow(()->new IllegalArgumentException("installed pure function did not reproduce a failure"));
        StrictJson.require(actual.kind()==declared,"fixed source failure changed its declared kind");return actual;
    }
    private static void validateBeforeWrite(ReadOriginal last,List<ReadOriginal> peers,Failure failure,BeforeOriginal before,List<ExactRef> producers){
        var evidence=new LinkedHashSet<ExactRef>();for(var item:all(last,peers))evidence.addAll(item.support());evidence.addAll(failure.sourceClosure());evidence.addAll(producers);
        evidence.addAll(List.of(before.driver(),before.manifest(),before.nativeFrame()));
        StrictJson.require(evidence.size()+1<=768&&peers.size()==failure.kind().requiredEarlierReads(),"finite complete failure source must fit before any preservation");
        evidence.forEach(DriverPostKnownReadFailureRowProducer::positive);
        StrictJson.require(last.receipt().request().source().machineId().equals(last.receipt().request().before().machineId()),"failure source/frame machine changed");
        var generation=last.receipt().before().binding().connectionGeneration();StrictJson.require(generation.signum()>0&&generation.compareTo(StrictJson.UINT64_MAX)<=0,"actual failure connection generation required");
    }
    private static BeforeOriginal before(ActionPorts.OutcomeArchive bound,PlanningReadReceipt finalRead,DriverSnapshotFacts.Known actual) {
        DriverObservationFacts expected=actual.observation().orElseThrow(()->new IllegalArgumentException("complete actual Known observation is unavailable"));
        var basis=RootGuardEvidence.frameBasis(finalRead.after().binding(),bound);
        StrictJson.require(basis.driverFacts().equals(expected.semanticFactsEvidence()),"current Known is not the final read's actual after-basis observation");
        RawJson manifest=bound.loadFullMaterial(basis.driverFacts());ExactRef driver=DriverObservationEvidenceReader.currentDriverReference(basis.driverFacts(),manifest);
        DriverObservationFacts replayed=observation(bound,basis.driverFacts(),driver,basis.nativeFrame());
        StrictJson.require(replayed.equals(expected)&&Arrays.equals(replayed.driver().encode(),actual.driver().encode()),"predecessor Known lost full manifest/native/Driver identity");
        var nativeFrame=DriverObservationEvidenceReader.nativeFrame(basis.driverFacts(),manifest,bound.readOriginalPacket(basis.nativeFrame()));
        var assembled=new DriverObservationAssembler().assemble(nativeFrame,replayed,basis.nativeFrame());
        StrictJson.require(assembled instanceof DriverObservationAssembler.Complete&&((DriverObservationAssembler.Complete)assembled).identity().equals(finalRead.request().before())
                &&replayed.source().equals(finalRead.request().source()),"failure final read crossed its complete predecessor frame/source");
        RawJson fullDriver=bound.loadFullMaterial(driver);requireMaterial(bound,driver,fullDriver,true);
        StrictJson.require(Arrays.equals(fullDriver.bytes(),actual.driver().encode()),"predecessor complete Driver bytes changed");
        return new BeforeOriginal(actual,driver,basis.driverFacts(),basis.nativeFrame(),DriverSnapshotFacts.encodeKnownOriginal(actual));
    }
    private static DriverObservationFacts observation(ActionPorts.OutcomeArchive bound,ExactRef manifest,ExactRef driver,ExactRef nativeRef){
        RawJson manifestRaw=bound.loadFullMaterial(manifest),driverRaw=bound.loadFullMaterial(driver);requireMaterial(bound,manifest,manifestRaw,true);requireMaterial(bound,driver,driverRaw,true);
        byte[] nativeRaw=bound.readOriginalPacket(nativeRef);exact(nativeRef,nativeRaw);var actual=DriverObservationEvidenceReader.nativeFrame(manifest,manifestRaw,nativeRaw);
        StrictJson.require(DriverObservationEvidenceReader.currentDriverReference(manifest,manifestRaw).equals(driver),"manifest named a different full Driver");
        return DriverObservationEvidenceReader.decode(manifest,manifestRaw,driverRaw,actual);
    }
    private static List<WriterContracts.Pin> sourcePins(ContinuityStorePort.Session same,List<ExactRef> producers,ReadOriginal last,List<ReadOriginal> peers,Failure failure)throws IOException {
        var originals=new LinkedHashSet<ExactRef>(producers);originals.addAll(failure.sourceClosure());for(var read:all(last,peers))originals.addAll(List.of(read.binding().definitionSource(),read.binding().decoderSource()));
        var pins=new ArrayList<WriterContracts.Pin>();for(var ref:originals){var observed=SharedSourceFiles.observe(Path.of(ref.path()));StrictJson.require(observed.source().bytes()==ref.bytes()&&observed.source().sha256().equals(ref.sha256()),"fixed failure source bytes changed");SharedSourceFiles.assertUnchanged(observed);pins.add(same.capturePin(ref,WriterContracts.MAX_PIN_BYTES));}return List.copyOf(pins);
    }
    private static void requireValue(ReadContract<?> contract,PlanningReadResult.Known<?> actual){Object expected=contract.replay(actual.receipt());StrictJson.require(expected!=null&&expected.getClass()==actual.value().getClass()&&expected.equals(actual.value()),"actual Known differs from identical source-owned pure replay");}
    private static ReadContract<?> installed(RootReadContractCatalog catalog,String id){var matches=catalog.installed().stream().filter(value->value.contract().contractId().equals(id)).toList();StrictJson.require(matches.size()==1,"one identical installed original read required");return matches.getFirst().contract();}
    private static ReadContract<?> installed(RootReadContractCatalog catalog,ReadBinding binding){var value=installed(catalog,binding.contractId());var installation=catalog.installed().stream().filter(item->item.contract()==value).findFirst().orElseThrow();StrictJson.require(value.sourceRef().equals(binding.definitionSource())&&installation.decoderSource().equals(binding.decoderSource())&&value.permissionMode()==binding.permissionMode()&&value.wireProfile()==binding.wireProfile()&&value.guardMode()==binding.guardMode()&&value.requiredCapability().equals(binding.requiredCapability())&&value.permissionKey().equals(binding.permissionKey()),"historical local read source/decoder/permission/wire/capability binding changed");return value;}
    private static boolean sameIdentities(List<? extends PlanningReadResult.Known<?>> first,List<? extends PlanningReadResult.Known<?>> second){if(first.size()!=second.size())return false;for(int i=0;i<first.size();i++)if(first.get(i)!=second.get(i))return false;return true;}
    private static <T> List<T> all(T last,List<T> peers){var result=new ArrayList<T>();result.add(last);result.addAll(peers);return result;}
    private static void verifyHead(ContinuityStorePort.Session same,WriterContracts.Head expected)throws IOException{var actual=same.head();StrictJson.require(actual.digest().equals(expected.digest())&&actual.documents().equals(expected.documents())&&actual.absent().equals(expected.absent())&&actual.indexRepairs().equals(expected.indexRepairs())&&actual.snapshotNeedsRecovery()==expected.snapshotNeedsRecovery(),"actual writer head changed during failure retention/replay");}
    private static void verifyPins(ContinuityStorePort.Session same,List<WriterContracts.Pin> pins)throws IOException{for(var pin:pins)same.verifyPin(pin);}
    private static void packet(ActionPorts.OutcomeArchive bound,ExactRef ref){exact(ref,bound.readOriginalPacket(ref));}
    private static void exact(ExactRef ref,byte[] raw){StrictJson.require(ref.bytes()==raw.length&&ref.sha256().equals(DriverJson.sha256(raw)),"exact original bytes/SHA changed");}
    private static void requireMaterial(ActionPorts.OutcomeArchive bound,ExactRef ref,RawJson expected,boolean full){RawJson raw=full?bound.loadFullMaterial(ref):bound.loadMaterial(ref);exact(ref,raw.bytes());StrictJson.require(Arrays.equals(raw.bytes(),expected.bytes())&&bound.materialReferenceOf(raw).equals(ref),"actual immutable material namespace/content changed");}
    private static void positive(ExactRef ref){StrictJson.require(Objects.requireNonNull(ref).bytes()>0,"nonempty exact original required");}
    private static List<ExactRef> refs(List<ExactRef> values,int min,int max){var copy=List.copyOf(values);StrictJson.require(copy.size()>=min&&copy.size()<=max&&new LinkedHashSet<>(copy).size()==copy.size(),"bounded distinct original closure required");copy.forEach(DriverPostKnownReadFailureRowProducer::positive);return copy;}

    private static ObjectNode sourceJson(Source source){var row=StrictJson.object();row.put("schema",SOURCE_SCHEMA);row.set("final_read",bindingJson(source.finalRead()));var earlier=row.putArray("earlier_reads");source.earlierReads().forEach(value->earlier.add(bindingJson(value)));row.set("failure",OpportunityJson.toNode(source.failure().toJson()));
        var before=row.putObject("before");before.set("full_driver",source.before().fullDriver().toJson());before.set("full_known",source.before().fullKnown().toJson());before.set("manifest",source.before().manifest().toJson());before.set("native_frame",source.before().nativeFrame().toJson());before.putObject("writer_point").put("sequence",source.before().writerPoint().sequence()).put("digest",source.before().writerPoint().digest());
        row.set("source_frame",ProposalLifecycleCodec.observation(source.sourceFrame()));row.set("source",ProposalLifecycleCodec.source(source.source()));row.put("session_id",source.sessionId());row.put("connection_generation",source.connectionGeneration().toString());var support=row.putArray("supporting_evidence");source.supportingEvidence().forEach(value->support.add(value.toJson()));var producers=row.putArray("producer_sources");source.producerSources().forEach(value->producers.add(value.toJson()));return row;}
    private static ObjectNode bindingJson(ReadBinding value){var row=StrictJson.object();row.put("contract_id",value.contractId());row.put("request_id",value.requestId());row.set("read",value.read().toJson());row.set("acknowledgement",value.acknowledgement().toJson());row.set("definition_source",value.definitionSource().toJson());row.set("decoder_source",value.decoderSource().toJson());row.put("permission_mode",value.permissionMode().name());row.put("wire_profile",value.wireProfile().name());row.put("guard_mode",value.guardMode().name());if(value.requiredCapability().isPresent())row.put("required_capability",value.requiredCapability().orElseThrow());else row.putNull("required_capability");row.put("permission_key",value.permissionKey());return row;}
    public static RawHistoryRow decode(byte[] bytes){var row=StrictJson.object(StrictJson.parse(bytes,RawJson.MAXIMUM_BYTES),Set.of("index","command","ok","error",SOURCE_FIELD));var source=StrictJson.object(row.get(SOURCE_FIELD),Set.of("schema","final_read","earlier_reads","failure","before","source_frame","source","session_id","connection_generation","supporting_evidence","producer_sources"));StrictJson.require(SOURCE_SCHEMA.equals(text(source,"schema")),"exact post-Known source version required");
        var before=StrictJson.object(source.get("before"),Set.of("full_driver","full_known","manifest","native_frame","writer_point"));var point=StrictJson.object(before.get("writer_point"),Set.of("sequence","digest"));var earlier=new ArrayList<ReadBinding>();StrictJson.require(source.get("earlier_reads").isArray(),"explicit failure peer array required");source.get("earlier_reads").forEach(value->earlier.add(binding(value)));
        var typed=new Source(binding(source.get("final_read")),earlier,DriverPostKnownReadFailureMaterial.fromJson(DriverJson.fromNode(source.get("failure"))),new Before(ref(before,"full_driver"),ref(before,"full_known"),ref(before,"manifest"),ref(before,"native_frame"),new WriterPoint(StrictJson.integer(point.get("sequence"),0,StrictJson.MAX_SAFE_INTEGER),text(point,"digest"))),ProposalLifecycleCodec.decodeObservation(source.get("source_frame")),G2Wire.source(source.get("source")),text(source,"session_id"),new BigInteger(new org.xar.ck3.control.contracts.CrossJsDecimalUInt64(text(source,"connection_generation")).decimal()),referenceArray(source,"supporting_evidence"),referenceArray(source,"producer_sources"));
        StrictJson.require(row.get("ok").isBoolean()&&!row.get("ok").booleanValue(),"failure row ok must be actual false boolean");return new RawHistoryRow(StrictJson.integer(row.get("index"),1,StrictJson.MAX_SAFE_INTEGER),text(row,"command"),false,text(row,"error"),typed);}
    private static ReadBinding binding(com.fasterxml.jackson.databind.JsonNode value){var row=StrictJson.object(value,Set.of("contract_id","request_id","read","acknowledgement","definition_source","decoder_source","permission_mode","wire_profile","guard_mode","required_capability","permission_key"));return new ReadBinding(text(row,"contract_id"),text(row,"request_id"),ref(row,"read"),ref(row,"acknowledgement"),ref(row,"definition_source"),ref(row,"decoder_source"),ReadContract.PermissionMode.valueOf(text(row,"permission_mode")),ReadContract.WireProfile.valueOf(text(row,"wire_profile")),ReadContract.GuardMode.valueOf(text(row,"guard_mode")),row.get("required_capability").isNull()?Optional.empty():Optional.of(text(row,"required_capability")),text(row,"permission_key"));}
    private static List<ExactRef> referenceArray(ObjectNode row,String key){StrictJson.require(row.get(key).isArray(),"explicit original array required");var result=new ArrayList<ExactRef>();row.get(key).forEach(value->result.add(ExactRef.fromJson(value)));return List.copyOf(result);}
    private static ExactRef ref(ObjectNode row,String key){return ExactRef.fromJson(row.get(key));}private static String text(ObjectNode row,String key){return StrictJson.text(row.get(key));}
}
