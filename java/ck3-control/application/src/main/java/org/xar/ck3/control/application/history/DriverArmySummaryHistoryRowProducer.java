package org.xar.ck3.control.application.history;

import java.io.IOException;
import java.math.BigInteger;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.*;

/** Original successful Army compact history. Artifact retention alone grants no canonical/current authority. */
public final class DriverArmySummaryHistoryRowProducer {
    public static final String SOURCE_FIELD="army_summary_history_source";
    public static final String SOURCE_SCHEMA="xar.driver-army-summary-history-source/v1";
    public static final String OPERATION="query-army-strengths-v1";
    public static final String CAPABILITY="game.command.query-army-strengths-v1";
    private DriverArmySummaryHistoryRowProducer() { }
    public record ReadBinding(String contractId,ExactRef read,ExactRef definitionSource,ExactRef decoderSource) {
        public ReadBinding {
            StrictJson.text(contractId);for(ExactRef ref:List.of(read,definitionSource,decoderSource))positive(ref);
        }
    }
    public record Source(ReadBinding original,List<ReadBinding> components,ObservationIdentity sourceFrame,G2Source source,
            String sessionId,BigInteger connectionGeneration,BigInteger querySequence,Obj arguments,ExactRef storageOriginal,
            PublicNumbers publicNumbers,List<ExactRef> supportingEvidence,List<ExactRef> producerSources) {
        public Source {
            Objects.requireNonNull(original);components=List.copyOf(components);Objects.requireNonNull(sourceFrame);Objects.requireNonNull(source);
            StrictJson.text(sessionId);u64(connectionGeneration,true);u64(querySequence,true);Objects.requireNonNull(arguments);positive(storageOriginal);
            Objects.requireNonNull(publicNumbers);supportingEvidence=references(supportingEvidence,1,512);producerSources=references(producerSources,1,64);
            StrictJson.require(components.size()>=1&&components.size()<=2&&components.contains(original)
                    &&new LinkedHashSet<>(components).size()==components.size()&&source.machineId().equals(sourceFrame.machineId()),
                    "one final Army read and at most one real comparison component from its exact source required");
        }
        public ExactRef originalReceipt(){return original.read();}
        public ExactRef definitionSource(){return original.definitionSource();}
        public ExactRef decoderSource(){return original.decoderSource();}
        public List<ExactRef> componentReceipts(){return components.stream().map(ReadBinding::read).toList();}
        public List<ExactRef> evidence() {
            var refs=new LinkedHashSet<ExactRef>(supportingEvidence);refs.addAll(producerSources);refs.add(storageOriginal);
            for(ReadBinding binding:components){refs.add(binding.read());refs.add(binding.definitionSource());refs.add(binding.decoderSource());}
            return List.copyOf(refs);
        }
    }
    public record RawHistoryRow(long index,String command,boolean ok,Obj result,Source source) {
        public RawHistoryRow {
            StrictJson.safe(index,1);Objects.requireNonNull(result);Objects.requireNonNull(source);
            StrictJson.require(ok&&OPERATION.equals(command),"finite successful original Army summary row required");requireSummary(result,source);
        }
        public Obj toJson(){return new Obj(java.util.Map.of("index",number(index),"command",new Text(command),"ok",new Bool(ok),"result",result,SOURCE_FIELD,sourceJson(source)));}
        public byte[] encode(){return OpportunityJson.encode(ordered(toJson()));}
        public DriverStateSnapshot.HistoryEntry historyEntry(){return new DriverStateSnapshot.HistoryEntry(index,new DriverStateSnapshot.Value(encode()));}
    }
    /** Only this original installed projector/archive path mints the live candidate. */
    public static final class Candidate {
        private final RawHistoryRow row;private final ExactRef rowReference;private final ArmySummaryPlan plan;private final SummaryProjection captured;
        private Candidate(RawHistoryRow row,ExactRef rowReference,ArmySummaryPlan plan,SummaryProjection captured){this.row=row;this.rowReference=rowReference;this.plan=plan;this.captured=captured;}
        public RawHistoryRow row(){return row;}
        public Source source(){return row.source();}
        public DriverStateSnapshot.HistoryEntry historyEntry(){return row.historyEntry();}
        public ExactRef rowReference(){return rowReference;}
        public ExactRef readReference(){return source().originalReceipt();}
        public ExactRef definitionSource(){return source().definitionSource();}
        public ExactRef decoderSource(){return source().decoderSource();}
    }
    private record Originals(PlanningReadReceipt receipt,ReadBinding original,List<ReadBinding> components,LinkedHashSet<ExactRef> support,ArmySummaryPlan plan) { }

    /** Validate every original before the first storage capture; disabled capture never invokes a full projection. */
    public static Candidate prepare(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,ReadContract<?> identical,
            PlanningReadResult.Known<?> actual,List<? extends PlanningReadResult.Known<?>> components,long nextIndex,List<ExactRef> producerSources) throws IOException {
        Objects.requireNonNull(actual);StrictJson.safe(nextIndex,1);producerSources=references(producerSources,1,64);
        List<ExactRef> refs=components.stream().map(value->{
            StrictJson.require(bound.loadRead(value.originalReceipt()).equals(value.receipt()),"Army summary component lost its actual archived receipt");return value.originalReceipt();
        }).toList();
        Originals originals=originals(bound,catalog,identical,actual.receipt(),actual.originalReceipt(),refs);
        requireKnownValue(identical,actual);
        for(var component:components) {
            ReadBinding binding=originals.components().stream().filter(value->value.read().equals(component.originalReceipt())).findFirst().orElseThrow();
            requireKnownValue(installed(catalog,binding),component);
        }
        SummaryProjection captured=originals.plan().captureOriginal();originals.plan().requireOriginal(captured);
        requireSummaryProjection(captured,originals.receipt());
        // Retain only finite original metadata, never a second full result or a raw sidecar namespace alias.
        ExactRef storage=bound.preserveMaterial(captured.storageOriginal());
        requireMaterial(bound,storage,captured.storageOriginal());
        RawHistoryRow row=derive(bound,originals,captured,storage,nextIndex,producerSources);
        RawJson encoded=new RawJson(row.encode());ExactRef reference=bound.preserveMaterial(encoded);
        requireMaterial(bound,reference,encoded);
        StrictJson.require(decode(bound.loadMaterial(reference).bytes()).equals(row),"original summary row/source changed in archive roundtrip");
        originals.plan().requireOriginal(captured);return new Candidate(row,reference,originals.plan(),captured);
    }
    /** Live revalidation reuses the same private capture; archived reconstruction below never calls capture. */
    public static Candidate replay(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,ReadContract<?> identical,
            PlanningReadResult.Known<?> actual,Candidate candidate) throws IOException {
        Objects.requireNonNull(candidate);
        StrictJson.require(actual.originalReceipt().equals(candidate.readReference())&&actual.receipt().equals(bound.loadRead(candidate.readReference())),
                "summary replay changed its actual final Known/receipt");
        requireKnownValue(identical,actual);candidate.plan.requireOriginal(candidate.captured);
        replayRow(bound,catalog,identical,candidate.row());
        requireMaterial(bound,candidate.rowReference(),new RawJson(candidate.row().encode()));
        candidate.plan.requireOriginal(candidate.captured);return candidate;
    }
    /** Exact old read identity/value only. This DATA result grants no current witness or Native/source authority. */
    public static <T> PlanningReadResult.Known<T> replayCanonical(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,
            ReadContract<T> identical,RawHistoryRow row) throws IOException {
        replayRow(bound,catalog,identical,row);PlanningReadReceipt receipt=bound.loadRead(row.source().originalReceipt());
        return new PlanningReadResult.Known<>(identical.replay(receipt),receipt,row.source().originalReceipt());
    }
    public static RawHistoryRow replayOriginals(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,RawHistoryRow row) throws IOException {
        return replayRow(bound,catalog,installed(catalog,row.source().original()),row);
    }
    private static RawHistoryRow replayRow(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,ReadContract<?> identical,RawHistoryRow row) throws IOException {
        Source source=row.source();PlanningReadReceipt receipt=bound.loadRead(source.originalReceipt());
        Originals originals=originals(bound,catalog,identical,receipt,source.originalReceipt(),source.componentReceipts());
        RawJson stored=bound.loadMaterial(source.storageOriginal());requireMaterial(bound,source.storageOriginal(),stored);
        SummaryProjection projection=originals.plan().replayOriginal(stored);requireSummaryProjection(projection,receipt);
        RawHistoryRow replayed=derive(bound,originals,projection,source.storageOriginal(),row.index(),source.producerSources());
        StrictJson.require(replayed.equals(row),"summary differs from the identical installed readonly original replay");return row;
    }
    private static RawHistoryRow derive(ActionPorts.OutcomeArchive bound,Originals originals,SummaryProjection projection,
            ExactRef storage,long index,List<ExactRef> producerSources) {
        requireMaterial(bound,storage,projection.storageOriginal());
        var support=new LinkedHashSet<ExactRef>(originals.support());support.addAll(projection.sourceClosure());support.addAll(producerSources);support.add(storage);
        for(ExactRef material:projection.materialEvidence()) {
            RawJson value=bound.loadMaterial(material);requireMaterial(bound,material,value);support.add(material);
        }
        PlanningReadReceipt receipt=originals.receipt();Obj result=DriverJson.object(projection.summary().bytes(),RawJson.MAXIMUM_BYTES);
        Source source=new Source(originals.original(),originals.components(),receipt.request().before(),receipt.request().source(),
                receipt.request().sessionId(),receipt.before().binding().connectionGeneration(),sequence(receipt),receipt.request().arguments(),storage,
                projection.publicNumbers(),List.copyOf(support),producerSources);
        return new RawHistoryRow(index,OPERATION,true,result,source);
    }

    private static Originals originals(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,ReadContract<?> identical,
            PlanningReadReceipt expected,ExactRef reference,List<ExactRef> componentRefs) {
        Objects.requireNonNull(bound);Objects.requireNonNull(catalog);Objects.requireNonNull(identical);
        StrictJson.require(catalog.containsIdentity(identical)&&identical.hasPureReplay()
                &&identical.originalHistoryKind().equals(Optional.of(Kind.ARMY_STRENGTHS))
                &&identical.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP&&identical.wireProfile()==ReadContract.WireProfile.EXECUTE_STEP
                &&identical.permissionMode()==ReadContract.PermissionMode.ADVERTISED_CAPABILITY
                &&identical.requiredCapability().equals(Optional.of(CAPABILITY))&&identical.operation().value().equals(OPERATION),
                "identical source-installed finite Army summary contract required");
        PlanningReadReceipt receipt=bound.loadRead(reference);
        StrictJson.require(receipt.equals(expected)&&bound.readReferenceOf(receipt).equals(reference),"actual archived final read identity differs");
        ReadBinding original=binding(catalog,identical,receipt,reference);requireReceipt(receipt,identical);
        StrictJson.require(componentRefs.size()>=1&&componentRefs.size()<=2&&componentRefs.contains(reference)
                &&new LinkedHashSet<>(componentRefs).size()==componentRefs.size(),"actual final receipt and at most one distinct comparison read required");
        var support=new LinkedHashSet<ExactRef>();var bindings=new java.util.ArrayList<ReadBinding>();
        ArmySummaryPlan finalPlan=plan(identical,receipt);
        for(ExactRef componentRef:componentRefs) {
            PlanningReadReceipt component=bound.loadRead(componentRef);
            ReadContract<?> componentContract=component.contractId().equals(identical.contractId())?identical:
                    identical.originalContract(component.contractId()).orElseThrow(()->new IllegalArgumentException("original Army comparison contract unavailable"));
            StrictJson.require(bound.readReferenceOf(component).equals(componentRef)&&catalog.containsIdentity(componentContract)
                    &&component.request().before().equals(receipt.request().before())&&component.request().source().equals(receipt.request().source())
                    &&component.request().sessionId().equals(receipt.request().sessionId())
                    &&component.before().binding().connectionGeneration().equals(receipt.before().binding().connectionGeneration()),
                    "Army summary components crossed their original frame/source/session/connection");
            requireReceipt(component,componentContract);ReadBinding item=binding(catalog,componentContract,component,componentRef);
            bindings.add(item);support.add(componentRef);support.add(item.definitionSource());support.add(item.decoderSource());
            // Pure plan construction is permitted here; neither component nor final storage capture is invoked.
            support.addAll((componentRef.equals(reference)?finalPlan:plan(componentContract,component)).sourceClosure());
            for(var guard:List.of(component.before(),component.after())) {
                support.add(guard.binding().nativeEvidence());support.add(guard.binding().capabilityEvidence());support.addAll(guard.binding().supportingEvidence());
            }
        }
        return new Originals(receipt,original,List.copyOf(bindings),support,finalPlan);
    }
    private static ReadBinding binding(RootReadContractCatalog catalog,ReadContract<?> contract,PlanningReadReceipt receipt,ExactRef reference) {
        var found=catalog.installed().stream().filter(value->value.contract()==contract).toList();
        StrictJson.require(found.size()==1&&receipt.contractId().equals(contract.contractId()),"one identical installed Army definition/decoder required");
        return new ReadBinding(contract.contractId(),reference,contract.sourceRef(),found.getFirst().decoderSource());
    }
    private static ReadContract<?> installed(RootReadContractCatalog catalog,ReadBinding source) {
        var found=catalog.installed().stream().filter(value->value.contract().contractId().equals(source.contractId())).toList();
        StrictJson.require(found.size()==1&&found.getFirst().contract().sourceRef().equals(source.definitionSource())
                &&found.getFirst().decoderSource().equals(source.decoderSource()),"summary original definition/decoder is no longer identical");
        return found.getFirst().contract();
    }
    /** Finite Army value comparison only, not a generic ReadContract equality admission rule. */
    private static void requireKnownValue(ReadContract<?> contract,PlanningReadResult.Known<?> actual) {
        StrictJson.require(contract.originalHistoryKind().equals(Optional.of(Kind.ARMY_STRENGTHS)),"finite Army claim comparison required");
        Object replayed=contract.replay(actual.receipt()),claimed=actual.value();
        StrictJson.require(replayed!=null&&claimed!=null&&replayed.getClass()==claimed.getClass()&&replayed.equals(claimed),
                "actual finite Army Known value differs from its identical original pure decoder");
    }
    private static ArmySummaryPlan plan(ReadContract<?> contract,PlanningReadReceipt receipt) {
        HistoryProjection payload=contract.projectOriginalHistoryPayload(receipt);
        StrictJson.require(payload instanceof ArmySummaryPlan,"Army compact history requires its installed lazy summary plan, not an eager full result");
        return (ArmySummaryPlan)payload;
    }
    private static void requireReceipt(PlanningReadReceipt receipt,ReadContract<?> contract) {
        StrictJson.require(receipt.contractId().equals(contract.contractId())&&receipt.request().operation().equals(contract.operation())
                &&contract.operation().value().equals(OPERATION)&&contract.originalHistoryKind().equals(Optional.of(Kind.ARMY_STRENGTHS))
                &&contract.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP&&contract.wireProfile()==ReadContract.WireProfile.EXECUTE_STEP
                &&contract.requiredCapability().equals(Optional.of(CAPABILITY))&&contract.permissionMode()==ReadContract.PermissionMode.ADVERTISED_CAPABILITY
                &&receipt.request().origin() instanceof CommandOrigin.Gameplay,"summary read changed its finite gameplay contract/permission");
        for(var guard:List.of(receipt.before(),receipt.after()))StrictJson.require(guard.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                &&guard.paused()&&guard.mapReady()&&guard.playerAlive()&&guard.binding().origin().equals(receipt.request().origin()),
                "original summary read crossed its living paused gameplay source");
        StrictJson.require(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()),
                "original summary read crossed complete semantic/modal binding");
        contract.replay(receipt);sequence(receipt);
    }
    private static BigInteger sequence(PlanningReadReceipt receipt) {
        RawJson actual=receipt.original().originalResultToken().orElseThrow(()->new IllegalArgumentException("original Army read token missing"));
        Obj result=DriverJson.object(actual.bytes(),DriverJson.MAX_NATIVE_BYTES);
        StrictJson.require(new Text(OPERATION).equals(result.get("step"))&&new Bool(true).equals(result.get("accepted")),"original Army query token differs");
        BigInteger value=OpportunityJson.integer(result.get("query_sequence"),"actual native query sequence");u64(value,true);return value;
    }
    private static void requireSummaryProjection(SummaryProjection projection,PlanningReadReceipt receipt) {
        Obj result=DriverJson.object(projection.summary().bytes(),RawJson.MAXIMUM_BYTES);
        StrictJson.require(new IntegerValue(sequence(receipt)).equals(result.get("query_sequence"))
                &&new Text(receipt.request().before().frame().snapshotId()).equals(result.get("queried_snapshot_id"))
                &&new IntegerValue(receipt.request().before().frame().revision()).equals(result.get("queried_revision"))
                &&new IntegerValue(receipt.request().before().frame().identity().nativeRevision()).equals(result.get("queried_native_revision")),
                "original summary replaced actual query sequence or guarded source metadata");
    }

    private static void requireSummary(Obj result,Source source) {
        StrictJson.require(new Text("xar.ck3.army-query-history-summary.v1").equals(result.get("history_summary_schema"))
                &&new Text(OPERATION).equals(result.get("step"))&&new Bool(true).equals(result.get("accepted")),"finite original numeric Army summary required");
        StrictJson.text(OpportunityJson.text(result.get("status"),"original summary status"));
        List<Value> rows=OpportunityJson.array(result.get("armies"),"original compact Army rows");
        StrictJson.require(OpportunityJson.integer(result.get("army_count"),"actual summary count").equals(BigInteger.valueOf(rows.size())),"summary row count differs");
        OpportunityJson.bool(result.get("full_result_preserved"),"actual original preservation result");source.publicNumbers().toPublic(result);
        StrictJson.require(new IntegerValue(source.querySequence()).equals(result.get("query_sequence"))
                &&new Text(source.sourceFrame().frame().snapshotId()).equals(result.get("queried_snapshot_id"))
                &&new IntegerValue(source.sourceFrame().frame().revision()).equals(result.get("queried_revision"))
                &&new IntegerValue(source.sourceFrame().frame().identity().nativeRevision()).equals(result.get("queried_native_revision")),
                "summary's existing original metadata differs from its receipt source");
    }
    private static final Set<String> SOURCE_KEYS=Set.of("schema","kind","original","components","source_frame","source","session_id",
            "connection_generation","query_sequence","arguments","storage_original","public_number_roles","supporting_evidence","producer_sources");
    private static Obj sourceJson(Source source) {
        var value=new java.util.LinkedHashMap<String,Value>();value.put("schema",new Text(SOURCE_SCHEMA));value.put("kind",new Text("ARMY_STRENGTHS_SUMMARY"));
        value.put("original",bindingJson(source.original()));value.put("components",new Arr(source.components().stream().<Value>map(DriverArmySummaryHistoryRowProducer::bindingJson).toList()));
        value.put("source_frame",DriverJson.object(StrictJson.canonical(ProposalLifecycleCodec.observation(source.sourceFrame())),DriverJson.MAX_NATIVE_BYTES));
        value.put("source",DriverJson.object(StrictJson.canonical(ProposalLifecycleCodec.source(source.source())),DriverJson.MAX_NATIVE_BYTES));
        value.put("session_id",new Text(source.sessionId()));value.put("connection_generation",new IntegerValue(source.connectionGeneration()));
        value.put("query_sequence",new IntegerValue(source.querySequence()));value.put("arguments",source.arguments());value.put("storage_original",refJson(source.storageOriginal()));
        value.put("public_number_roles",source.publicNumbers().toJson());value.put("supporting_evidence",refsJson(source.supportingEvidence()));
        value.put("producer_sources",refsJson(source.producerSources()));return new Obj(value);
    }
    private static Obj bindingJson(ReadBinding binding) {
        return new Obj(java.util.Map.of("contract_id",new Text(binding.contractId()),"read",refJson(binding.read()),
                "definition_source",refJson(binding.definitionSource()),"decoder_source",refJson(binding.decoderSource())));
    }
    /** Closed source header and explicit owning roles, before public identity decimals are restored. */
    public static PublicNumbers publicNumbersFromSource(Value value) {
        Obj source=sourceHeader(value);return PublicNumbers.fromJson(source.get("public_number_roles"));
    }
    private static Obj sourceHeader(Value value) {
        Obj source=OpportunityJson.object(value,"Army summary source");
        StrictJson.require(source.members().keySet().equals(SOURCE_KEYS)&&new Text(SOURCE_SCHEMA).equals(source.get("schema"))
                &&new Text("ARMY_STRENGTHS_SUMMARY").equals(source.get("kind")),"exact finite Army summary source schema required");return source;
    }

    public static RawHistoryRow decode(byte[] bytes) {
        Obj row=DriverJson.object(bytes,RawJson.MAXIMUM_BYTES);
        StrictJson.require(row.members().keySet().equals(Set.of("index","command","ok","result",SOURCE_FIELD)),"exact complete original Army summary row required");
        Obj source=sourceHeader(row.get(SOURCE_FIELD));
        Source typed=new Source(readBinding(source.get("original")),OpportunityJson.array(source.get("components"),"actual summary components").stream().map(DriverArmySummaryHistoryRowProducer::readBinding).toList(),
                ProposalLifecycleCodec.decodeObservation(OpportunityJson.toNode(source.get("source_frame"))),G2Wire.source(OpportunityJson.toNode(source.get("source"))),
                OpportunityJson.text(source.get("session_id"),"summary session"),OpportunityJson.integer(source.get("connection_generation"),"original connection generation"),
                OpportunityJson.integer(source.get("query_sequence"),"original query sequence"),OpportunityJson.object(source.get("arguments"),"actual summary arguments"),reference(source.get("storage_original")),
                PublicNumbers.fromJson(source.get("public_number_roles")),refs(source.get("supporting_evidence")),refs(source.get("producer_sources")));
        return new RawHistoryRow(OpportunityJson.integer(row.get("index"),"original history index").longValueExact(),OpportunityJson.text(row.get("command"),"summary command"),
                OpportunityJson.bool(row.get("ok"),"summary ok"),OpportunityJson.object(row.get("result"),"original numeric compact result"),typed);
    }
    private static ReadBinding readBinding(Value value) {
        Obj binding=OpportunityJson.object(value,"actual original summary read binding");
        StrictJson.require(binding.members().keySet().equals(Set.of("contract_id","read","definition_source","decoder_source")),"exact summary read binding fields required");
        return new ReadBinding(OpportunityJson.text(binding.get("contract_id"),"original contract"),reference(binding.get("read")),reference(binding.get("definition_source")),reference(binding.get("decoder_source")));
    }
    private static List<ExactRef> refs(Value value){return OpportunityJson.array(value,"exact original summary references").stream().map(DriverArmySummaryHistoryRowProducer::reference).toList();}
    private static Arr refsJson(List<ExactRef> refs){return new Arr(refs.stream().<Value>map(DriverArmySummaryHistoryRowProducer::refJson).toList());}
    private static Obj refJson(ExactRef ref){return DriverJson.object(StrictJson.canonical(ref.toJson()),DriverJson.MAX_NATIVE_BYTES);}
    private static ExactRef reference(Value value){return DriverObservationEvidenceReader.reference(value);}
    private static void requireMaterial(ActionPorts.OutcomeArchive bound,ExactRef reference,RawJson expected) {
        RawJson retained=bound.loadMaterial(reference);
        StrictJson.require(reference.bytes()==retained.bytes().length&&reference.sha256().equals(DriverJson.sha256(retained.bytes()))
                &&java.util.Arrays.equals(retained.bytes(),expected.bytes())&&bound.materialReferenceOf(retained).equals(reference),
                "original summary archive material bytes/hash/namespace changed");
    }
    private static List<ExactRef> references(List<ExactRef> values,int min,int max) {
        values=List.copyOf(values);StrictJson.require(values.size()>=min&&values.size()<=max&&new LinkedHashSet<>(values).size()==values.size(),"bounded distinct exact summary references required");
        values.forEach(DriverArmySummaryHistoryRowProducer::positive);return values;
    }
    private static void positive(ExactRef ref){Objects.requireNonNull(ref);StrictJson.require(ref.bytes()>0,"nonempty actual summary artifact/source required");}
    private static void u64(BigInteger value,boolean positive){StrictJson.require(value!=null&&value.signum()>=(positive?1:0)&&value.compareTo(StrictJson.UINT64_MAX)<=0,"exact original uint64 required");}
    private static IntegerValue number(long value){return new IntegerValue(BigInteger.valueOf(value));}
    private static Value ordered(Value value) {
        if(value instanceof Obj object) {
            var fields=new java.util.LinkedHashMap<String,Value>();new java.util.TreeMap<>(object.members()).forEach((key,item)->fields.put(key,ordered(item)));return new Obj(fields);
        }
        if(value instanceof Arr array)return new Arr(array.items().stream().map(DriverArmySummaryHistoryRowProducer::ordered).toList());return value;
    }
}
