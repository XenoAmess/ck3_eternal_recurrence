package org.xar.ck3.control.application.history;

import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.planning.finance.GiftResolvedEvidence;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.giftoutcome.GiftOutcomeModel;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Finite logical observation DATA, never a fabricated Native receipt or a world-effect confirmation. */
public final class DriverObservedHistoryRowProducer {
    public static final String SOURCE_SCHEMA="xar.driver-observed-history-source/v1";
    public static final String SOURCE_FIELD="observed_history_source";
    public enum Kind { GIFT_RESOLVED }
    private DriverObservedHistoryRowProducer() { }
    public record ReadBinding(String contractId,ExactRef read,ExactRef definitionSource,ExactRef decoderSource) {
        public ReadBinding {
            StrictJson.text(contractId);Objects.requireNonNull(read);Objects.requireNonNull(definitionSource);Objects.requireNonNull(decoderSource);
            StrictJson.require(read.bytes()>0&&definitionSource.bytes()>0&&decoderSource.bytes()>0,"complete original observation read binding required");
        }
    }
    public record Source(Kind kind,String requestId,ObservationIdentity frame,ExactRef driverFacts,ExactRef nativeFrame,
                         ExactRef beforeDriver,ExactRef fullResult,ReadBinding pair,Optional<ReadBinding> alert,List<ExactRef> producerSources) {
        public Source {
            Objects.requireNonNull(kind);StrictJson.text(requestId);Objects.requireNonNull(frame);Objects.requireNonNull(driverFacts);
            Objects.requireNonNull(nativeFrame);Objects.requireNonNull(beforeDriver);Objects.requireNonNull(fullResult);Objects.requireNonNull(pair);
            alert=Objects.requireNonNull(alert);producerSources=List.copyOf(producerSources);
            StrictJson.require(driverFacts.bytes()>0&&nativeFrame.bytes()>0&&beforeDriver.bytes()>0&&fullResult.bytes()>0
                    &&!producerSources.isEmpty()&&producerSources.size()<=64&&producerSources.stream().allMatch(ref->ref.bytes()>0)
                    &&new LinkedHashSet<>(producerSources).size()==producerSources.size(),"complete exact observed source closure required");
        }
        public ExactRef pairReference(){return pair.read();}
        public Optional<ExactRef> alertReference(){return alert.map(ReadBinding::read);}
        public List<ExactRef> evidence() {
            var refs=new LinkedHashSet<ExactRef>(producerSources);refs.add(driverFacts);refs.add(nativeFrame);refs.add(beforeDriver);refs.add(fullResult);
            for(ReadBinding read:bindings(this)){refs.add(read.read());refs.add(read.definitionSource());refs.add(read.decoderSource());}
            return List.copyOf(refs);
        }
    }
    public record RawHistoryRow(long index,String command,boolean ok,Obj result,Source source) {
        public RawHistoryRow {
            StrictJson.safe(index,1);Objects.requireNonNull(result);Objects.requireNonNull(source);
            StrictJson.require(ok&&GiftResolvedEvidence.OPERATION.value().equals(command)
                    &&new Text(GiftOutcomeModel.SCHEMA).equals(result.get("schema"))&&new Text("observed").equals(result.get("status"))
                    &&new Text(source.requestId()).equals(result.get("request_id"))&&new Bool(false).equals(result.get("attributed_to_gift")),
                    "only the original logical Gift Observed result belongs to this finite producer");
        }
        public Obj toJson() {return new Obj(java.util.Map.of("index",new IntegerValue(java.math.BigInteger.valueOf(index)),
                "command",new Text(command),"ok",new Bool(ok),"result",result,SOURCE_FIELD,sourceJson(source)));}
        public byte[] encode() {return OpportunityJson.encode(ordered(toJson()));}
        public DriverStateSnapshot.HistoryEntry historyEntry() {return new DriverStateSnapshot.HistoryEntry(index,new DriverStateSnapshot.Value(encode()));}
    }
    /** Private producer result; source DATA alone cannot mint a canonical transition. */
    public static final class Candidate {
        private final RawHistoryRow row;private final ExactRef rowReference;
        private Candidate(RawHistoryRow row,ExactRef rowReference){this.row=row;this.rowReference=rowReference;}
        public RawHistoryRow row(){return row;}
        public Source source(){return row.source();}
        public DriverStateSnapshot.HistoryEntry historyEntry(){return row.historyEntry();}
        public ExactRef rowReference(){return rowReference;}
        public ExactRef fullResultReference(){return row.source().fullResult();}
    }
    private record Original(Complete frame,DriverStateSnapshot.Complete driver,ExactRef driverFacts,ExactRef nativeFrame,ExactRef driverReference) { }

    public static Candidate prepareGiftResolved(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,
            GiftResolvedEvidence.Inputs actual,RawJson claimed,long nextHistoryIndex,List<ExactRef> actualProducerSources) {
        Objects.requireNonNull(bound);Objects.requireNonNull(catalog);Objects.requireNonNull(actual);Objects.requireNonNull(claimed);
        ExactRef manifest=DriverObservationEvidenceReader.reference(actual.frame().semantic().get("java_driver_facts_evidence"));
        Original original=loadOriginal(bound,manifest,actual.frame().originalEvidence());requireActual(actual,original);
        RawHistoryRow row=derive(bound,catalog,actual,nextHistoryIndex,original,actualProducerSources,ArtifactMode.PRESERVE_COMPLETE,Optional.of(claimed));
        StrictJson.require(DriverJson.object(claimed.bytes(),RawJson.MAXIMUM_BYTES).equals(row.result()),
                "claimed Gift result differs from the owning complete original pure query");
        ExactRef full=bound.materialReferenceOf(new RawJson(OpportunityJson.encode(ordered(row.result()))));
        StrictJson.require(full.equals(row.source().fullResult()),"observed full-result artifact reference changed");requireResultArtifact(bound,row);
        RawJson encoded=new RawJson(row.encode());ExactRef ref=bound.preserveMaterial(encoded);
        StrictJson.require(ref.equals(bound.materialReferenceOf(encoded))&&decode(bound.loadMaterial(ref).bytes()).equals(row),
                "observed original row/archive/serialization changed");return new Candidate(row,ref);
    }
    public static Candidate replay(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,
            GiftResolvedEvidence.Inputs actual,Candidate original) {
        Objects.requireNonNull(original);RawHistoryRow replayed=replayCanonical(bound,catalog,original.row());
        Original retained=loadOriginal(bound,replayed.source().driverFacts(),replayed.source().nativeFrame());requireActual(actual,retained);
        StrictJson.require(replayed.source().requestId().equals(actual.requestId())
                &&bound.readReferenceOf(actual.pair()).equals(replayed.source().pairReference())
                &&actual.alert().map(bound::readReferenceOf).equals(replayed.source().alertReference())
                &&decode(bound.loadMaterial(original.rowReference()).bytes()).equals(replayed),"private observed source changed during replay");
        return original;
    }
    /** Historical DATA replay from exact archived Driver/SEM/native/read originals. No current Known is constructed. */
    public static RawHistoryRow replayCanonical(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,RawHistoryRow original) {
        Source source=original.source();Original retained=loadOriginal(bound,source.driverFacts(),source.nativeFrame());
        StrictJson.require(retained.driverReference().equals(source.beforeDriver())&&retained.frame().identity().equals(source.frame()),
                "observed source changed its actual original full Driver/frame");
        PlanningReadReceipt pair=bound.loadRead(source.pairReference());Optional<PlanningReadReceipt> alert=source.alertReference().map(bound::loadRead);
        var actual=new GiftResolvedEvidence.Inputs(retained.frame(),retained.driver(),pair,alert,source.requestId());
        RawHistoryRow replayed=derive(bound,catalog,actual,original.index(),retained,source.producerSources());
        requireResultArtifact(bound,replayed);StrictJson.require(replayed.equals(original),"observed row differs from its exact original pure producer");return replayed;
    }
    private enum ArtifactMode { REQUIRE_RETAINED, PRESERVE_COMPLETE }
    private static RawHistoryRow derive(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,
            GiftResolvedEvidence.Inputs actual,long index,Original original,List<ExactRef> producerSources) {
        return derive(bound,catalog,actual,index,original,producerSources,ArtifactMode.REQUIRE_RETAINED,Optional.empty());
    }
    private static RawHistoryRow derive(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,
            GiftResolvedEvidence.Inputs actual,long index,Original original,List<ExactRef> producerSources,
            ArtifactMode mode,Optional<RawJson> claimed) {
        StrictJson.safe(index,1);producerSources=List.copyOf(producerSources);
        StrictJson.require(!producerSources.isEmpty()&&producerSources.size()<=64&&producerSources.stream().allMatch(ref->ref.bytes()>0)
                &&new LinkedHashSet<>(producerSources).size()==producerSources.size(),"complete exact observed producer sources required before retention");
        requireActual(actual,original);ReadBinding pair=binding(bound,catalog,actual.pair());
        Optional<ReadBinding> alert=actual.alert().map(value->binding(bound,catalog,value));
        ReadContract<?> pairContract=installed(catalog,pair);
        Optional<ReadContract<?>> alertContract=alert.map(value->installed(catalog,value));
        var projected=GiftResolvedEvidence.recompute(actual,pairContract,alertContract);
        Obj result=DriverJson.object(projected.result().bytes(),RawJson.MAXIMUM_BYTES);
        StrictJson.require(projected.operation().equals(GiftResolvedEvidence.OPERATION)
                &&new Text(GiftOutcomeModel.SCHEMA).equals(result.get("schema"))&&new Text("observed").equals(result.get("status"))
                &&new Text(actual.requestId()).equals(result.get("request_id"))&&new Bool(false).equals(result.get("attributed_to_gift")),
                "owning logical observed outcome changed its original schema/status/request identity");
        claimed.ifPresent(value->StrictJson.require(DriverJson.object(value.bytes(),RawJson.MAXIMUM_BYTES).equals(result),
                "claimed Gift result differs from the complete original pure producer before retention"));
        RawJson complete=new RawJson(OpportunityJson.encode(ordered(result)));
        // The archive's reference lookup requires prior retention. Every source/value check above remains pure.
        ExactRef full=mode==ArtifactMode.PRESERVE_COMPLETE?bound.preserveMaterial(complete):bound.materialReferenceOf(complete);
        Source source=new Source(Kind.GIFT_RESOLVED,actual.requestId(),actual.frame().identity(),original.driverFacts(),original.nativeFrame(),
                original.driverReference(),full,pair,alert,producerSources);
        return new RawHistoryRow(index,projected.operation().value(),true,result,source);
    }
    private static ReadBinding binding(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,PlanningReadReceipt read) {
        ExactRef reference=bound.readReferenceOf(read);
        StrictJson.require(bound.loadRead(reference).equals(read),"logical observation lost its exact original read receipt");
        var found=catalog.installed().stream().filter(value->value.contract().contractId().equals(read.contractId())).toList();
        StrictJson.require(found.size()==1,"one exact installed original observation decoder required");
        var foundBinding=found.getFirst();ReadContract<?> contract=foundBinding.contract();
        StrictJson.require(catalog.containsIdentity(contract)&&contract.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                &&contract.hasPureReplay()&&contract.operation().equals(read.request().operation()),"original observation read contract changed");
        contract.replay(read);
        return new ReadBinding(contract.contractId(),reference,contract.sourceRef(),foundBinding.decoderSource());
    }
    private static ReadContract<?> installed(RootReadContractCatalog catalog,ReadBinding binding) {
        var found=catalog.installed().stream().filter(value->value.contract().contractId().equals(binding.contractId())).toList();
        StrictJson.require(found.size()==1&&found.getFirst().contract().sourceRef().equals(binding.definitionSource())
                &&found.getFirst().decoderSource().equals(binding.decoderSource()),"observation source changed its installed contract/decoder");
        return found.getFirst().contract();
    }
    private static Original loadOriginal(ActionPorts.OutcomeArchive bound,ExactRef manifestRef,ExactRef nativeRef) {
        RawJson manifest=bound.loadFullMaterial(manifestRef);requireBytes(manifestRef,manifest.bytes());
        ExactRef driverRef=DriverObservationEvidenceReader.currentDriverReference(manifestRef,manifest);
        RawJson driver=bound.loadFullMaterial(driverRef);requireBytes(driverRef,driver.bytes());
        byte[] nativeBytes=bound.loadNativeFrame(nativeRef);requireBytes(nativeRef,nativeBytes);
        var raw=DriverObservationEvidenceReader.nativeFrame(manifestRef,manifest,nativeBytes);
        var facts=DriverObservationEvidenceReader.decode(manifestRef,manifest,driver,raw);
        var joined=new DriverObservationAssembler().assemble(raw,facts,nativeRef);
        StrictJson.require(joined instanceof Complete,"logical observation needs the actual original full Driver/native producer");
        return new Original((Complete)joined,facts.driver(),manifestRef,nativeRef,driverRef);
    }
    private static void requireActual(GiftResolvedEvidence.Inputs actual,Original original) {
        StrictJson.require(actual.frame().equals(original.frame())&&Arrays.equals(actual.driver().encode(),original.driver().encode()),
                "logical observation crossed its complete archived native/Driver source");
    }
    private static void requireResultArtifact(ActionPorts.OutcomeArchive bound,RawHistoryRow row) {
        RawJson material=bound.loadMaterial(row.source().fullResult());requireBytes(row.source().fullResult(),material.bytes());
        StrictJson.require(bound.materialReferenceOf(material).equals(row.source().fullResult())
                &&DriverJson.object(material.bytes(),RawJson.MAXIMUM_BYTES).equals(row.result()),"observed complete result artifact changed");
    }
    private static void requireBytes(ExactRef reference,byte[] bytes) {
        StrictJson.require(reference.bytes()==bytes.length&&reference.sha256().equals(DriverJson.sha256(bytes)),"observed original bytes/SHA differ");
    }
    private static List<ReadBinding> bindings(Source source) {
        return source.alert().map(value->List.of(source.pair(),value)).orElseGet(()->List.of(source.pair()));
    }
    private static Obj readJson(ReadBinding read) {
        return new Obj(java.util.Map.of("contract_id",new Text(read.contractId()),"read",refJson(read.read()),
                "definition_source",refJson(read.definitionSource()),"decoder_source",refJson(read.decoderSource())));
    }
    private static Obj sourceJson(Source source) {
        var fields=new java.util.LinkedHashMap<String,Value>();fields.put("schema",new Text(SOURCE_SCHEMA));fields.put("kind",new Text(source.kind().name()));
        fields.put("request_id",new Text(source.requestId()));fields.put("frame",DriverJson.object(StrictJson.canonical(ProposalLifecycleCodec.observation(source.frame())),DriverJson.MAX_NATIVE_BYTES));
        fields.put("driver_facts",refJson(source.driverFacts()));fields.put("native_frame",refJson(source.nativeFrame()));
        fields.put("before_driver",refJson(source.beforeDriver()));fields.put("full_result",refJson(source.fullResult()));
        fields.put("pair",readJson(source.pair()));fields.put("alert",source.alert().<Value>map(DriverObservedHistoryRowProducer::readJson).orElse(Nil.INSTANCE));
        fields.put("producer_sources",new Arr(source.producerSources().stream().<Value>map(DriverObservedHistoryRowProducer::refJson).toList()));
        return new Obj(fields);
    }
    public static RawHistoryRow decode(byte[] bytes) {
        Obj row=DriverJson.object(bytes,RawJson.MAXIMUM_BYTES);
        StrictJson.require(row.members().keySet().equals(Set.of("index","command","ok","result",SOURCE_FIELD)),"exact logical observed history row required");
        Obj source=OpportunityJson.object(row.get(SOURCE_FIELD),"original observed source");
        StrictJson.require(source.members().keySet().equals(Set.of("schema","kind","request_id","frame","driver_facts","native_frame","before_driver",
                "full_result","pair","alert","producer_sources"))&&new Text(SOURCE_SCHEMA).equals(source.get("schema")),"exact original observed source schema required");
        Source original=new Source(Kind.valueOf(OpportunityJson.text(source.get("kind"),"observed kind")),
                OpportunityJson.text(source.get("request_id"),"observed request"),ProposalLifecycleCodec.decodeObservation(OpportunityJson.toNode(source.get("frame"))),
                reference(source.get("driver_facts")),reference(source.get("native_frame")),reference(source.get("before_driver")),reference(source.get("full_result")),
                readBinding(source.get("pair")),source.get("alert")==Nil.INSTANCE?Optional.empty():Optional.of(readBinding(source.get("alert"))),
                OpportunityJson.array(source.get("producer_sources"),"original observed producer sources").stream().map(DriverObservedHistoryRowProducer::reference).toList());
        return new RawHistoryRow(OpportunityJson.integer(row.get("index"),"observed history index").longValueExact(),
                OpportunityJson.text(row.get("command"),"observed command"),OpportunityJson.bool(row.get("ok"),"observed ok"),
                OpportunityJson.object(row.get("result"),"observed original result"),original);
    }
    private static ReadBinding readBinding(Value value) {
        Obj row=OpportunityJson.object(value,"original observed read binding");
        StrictJson.require(row.members().keySet().equals(Set.of("contract_id","read","definition_source","decoder_source")),"exact original observed read binding required");
        return new ReadBinding(OpportunityJson.text(row.get("contract_id"),"original observation contract"),reference(row.get("read")),
                reference(row.get("definition_source")),reference(row.get("decoder_source")));
    }
    private static Obj refJson(ExactRef reference){return DriverJson.object(StrictJson.canonical(reference.toJson()),DriverJson.MAX_NATIVE_BYTES);}
    private static ExactRef reference(Value value){return DriverObservationEvidenceReader.reference(value);}
    private static Value ordered(Value value) {
        if(value instanceof Obj object) {
            var sorted=new java.util.TreeMap<String,Value>(object.members());var fields=new java.util.LinkedHashMap<String,Value>();
            sorted.forEach((key,item)->fields.put(key,ordered(item)));return new Obj(fields);
        }
        if(value instanceof Arr array)return new Arr(array.items().stream().map(DriverObservedHistoryRowProducer::ordered).toList());
        return value;
    }
}
