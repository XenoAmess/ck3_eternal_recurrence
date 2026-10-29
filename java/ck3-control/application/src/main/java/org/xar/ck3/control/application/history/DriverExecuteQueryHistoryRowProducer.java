package org.xar.ck3.control.application.history;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.*;

/** Exact original execute-query report DATA; only the owning Root can publish canonical/current history. */
public final class DriverExecuteQueryHistoryRowProducer {
    public static final String SOURCE_FIELD="execute_query_history_source";
    public static final String SOURCE_SCHEMA="xar.driver-execute-query-history-source/v1";
    private DriverExecuteQueryHistoryRowProducer(){ }

    public record ReadBinding(String contractId,String requestId,ExactRef read,ExactRef acknowledgement,
            ExactRef definitionSource,ExactRef decoderSource,ReadContract.PermissionMode permissionMode,
            ReadContract.WireProfile wireProfile,Optional<String> requiredCapability,String permissionKey) {
        public ReadBinding {
            StrictJson.text(contractId);StrictJson.text(requestId);
            for(ExactRef reference:List.of(read,acknowledgement,definitionSource,decoderSource))positive(reference);
            Objects.requireNonNull(permissionMode);Objects.requireNonNull(wireProfile);requiredCapability=Objects.requireNonNull(requiredCapability);
            requiredCapability.ifPresent(StrictJson::text);StrictJson.text(permissionKey);
            StrictJson.require(wireProfile==ReadContract.WireProfile.EXECUTE_STEP
                    &&(permissionMode==ReadContract.PermissionMode.ADVERTISED_CAPABILITY)==requiredCapability.isPresent(),
                    "original execute-query local permission/wire contract differs");
        }
    }
    public record Source(ReadBinding original,OperationKey logicalOperation,OperationKey originalCommand,
            ObservationIdentity sourceFrame,G2Source source,String sessionId,BigInteger connectionGeneration,
            Optional<BigInteger> querySequence,Obj arguments,ExactRef fullResult,PublicNumbers publicNumbers,
            List<ExactRef> supportingEvidence,List<ExactRef> producerSources,List<ExactRef> projectionSources) {
        public Source {
            Objects.requireNonNull(original);Objects.requireNonNull(logicalOperation);Objects.requireNonNull(originalCommand);
            Objects.requireNonNull(sourceFrame);Objects.requireNonNull(source);StrictJson.text(sessionId);unsigned(connectionGeneration,true);
            querySequence=Objects.requireNonNull(querySequence);querySequence.ifPresent(value->unsigned(value,true));
            Objects.requireNonNull(arguments);positive(fullResult);Objects.requireNonNull(publicNumbers);
            supportingEvidence=references(supportingEvidence,1,512);producerSources=references(producerSources,1,64);
            projectionSources=references(projectionSources,1,260);
            StrictJson.require(source.machineId().equals(sourceFrame.machineId())
                    &&supportingEvidence.containsAll(producerSources)&&supportingEvidence.containsAll(projectionSources)
                    &&supportingEvidence.containsAll(List.of(original.read(),original.acknowledgement(),original.definitionSource(),original.decoderSource(),fullResult)),
                    "complete original execute-query source and its exact closure required");
        }
        public ExactRef originalReceipt(){return original.read();}
        public ExactRef definitionSource(){return original.definitionSource();}
        public ExactRef decoderSource(){return original.decoderSource();}
        public List<ExactRef> evidence(){return supportingEvidence;}
    }
    public record RawHistoryRow(long index,String command,boolean ok,Obj result,Source source) {
        public RawHistoryRow {
            StrictJson.safe(index,1);StrictJson.text(command);Objects.requireNonNull(result);Objects.requireNonNull(source);
            StrictJson.require(ok&&command.equals(source.originalCommand().value()),"successful original execute command required");
            DriverExecuteReadHistoryRegistry.requireRow(source.logicalOperation(),source.originalCommand(),result);
            source.publicNumbers().toPublic(result);
            if(result.members().containsKey("query_sequence"))StrictJson.require(sequence(result).equals(source.querySequence()),
                    "report replaced its actual original native query sequence");
        }
        public Obj toJson(){return new Obj(java.util.Map.of("index",number(index),"command",new Text(command),"ok",new Bool(ok),"result",result,SOURCE_FIELD,sourceJson(source)));}
        public byte[] encode(){return OpportunityJson.encode(ordered(toJson()));}
        public DriverStateSnapshot.HistoryEntry historyEntry(){return new DriverStateSnapshot.HistoryEntry(index,new DriverStateSnapshot.Value(encode()));}
    }
    /** Only the identical source-owned pure projection and retained original archive path mint this candidate. */
    public static final class Candidate {
        private final RawHistoryRow row;
        private final ExactRef rowReference;
        private final RootReadContractCatalog catalog;
        private final ReadContract<?> contract;
        private Candidate(RawHistoryRow row,ExactRef rowReference,RootReadContractCatalog catalog,ReadContract<?> contract){
            this.row=row;this.rowReference=rowReference;this.catalog=catalog;this.contract=contract;
        }
        public RawHistoryRow row(){return row;}
        public Source source(){return row.source();}
        public DriverStateSnapshot.HistoryEntry historyEntry(){return row.historyEntry();}
        public ExactRef rowReference(){return rowReference;}
        public ExactRef fullResultReference(){return source().fullResult();}
        public ExactRef readReference(){return source().originalReceipt();}
        public ExactRef definitionSource(){return source().definitionSource();}
        public ExactRef decoderSource(){return source().decoderSource();}
    }
    private record Originals(PlanningReadReceipt receipt,ReadBinding binding,ExecuteProjection projection,
            LinkedHashSet<ExactRef> support){ }

    /** All source/value/receipt/guard validation precedes the first preservation. Full report is stored first. */
    public static Candidate prepare(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,ReadContract<?> identical,
            PlanningReadResult.Known<?> actual,long nextIndex,List<ExactRef> actualProducerSources)throws IOException {
        Objects.requireNonNull(actual);StrictJson.safe(nextIndex,1);actualProducerSources=references(actualProducerSources,1,64);
        Originals originals=originals(bound,catalog,identical,actual.receipt(),actual.originalReceipt());
        requireKnownValue(identical,actual);requireSourceFiles(originals,actualProducerSources);requireSourceShape(originals,actualProducerSources);
        ExecuteProjection projection=originals.projection();
        // materialReferenceOf is a lookup only. Never use it before the first real preserve.
        ExactRef full=bound.preserveMaterial(projection.fullResult());requireMaterial(bound,full,projection.fullResult());
        RawHistoryRow row=derive(originals,full,nextIndex,actualProducerSources);
        RawJson encoded=new RawJson(row.encode());ExactRef reference=bound.preserveMaterial(encoded);requireMaterial(bound,reference,encoded);
        StrictJson.require(decode(bound.loadMaterial(reference).bytes()).equals(row),"execute-query row/source changed in archive serialization");
        requireSourceFiles(originals,actualProducerSources);return new Candidate(row,reference,catalog,identical);
    }
    /** Revalidates the original private candidate. No artifact preservation, Native request or current qualification. */
    public static Candidate replay(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,ReadContract<?> identical,
            PlanningReadResult.Known<?> actual,Candidate candidate)throws IOException {
        Objects.requireNonNull(candidate);Objects.requireNonNull(actual);
        StrictJson.require(candidate.catalog==catalog&&candidate.contract==identical
                &&actual.originalReceipt().equals(candidate.readReference())&&actual.receipt().equals(bound.loadRead(candidate.readReference())),
                "execute-query candidate crossed its identical installed catalog/contract or original receipt");
        requireKnownValue(identical,actual);replayRow(bound,catalog,identical,candidate.row());
        requireMaterial(bound,candidate.rowReference(),new RawJson(candidate.row().encode()));return candidate;
    }
    /** Exact old value and receipt only. This result supplies neither freshness nor an executable/writer permit. */
    public static <T> PlanningReadResult.Known<T> replayCanonical(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,
            ReadContract<T> identical,RawHistoryRow original)throws IOException {
        replayRow(bound,catalog,identical,original);PlanningReadReceipt receipt=bound.loadRead(original.source().originalReceipt());
        return new PlanningReadResult.Known<>(identical.replay(receipt),receipt,original.source().originalReceipt());
    }
    /** Source and material reconstruction only; this method never queries, preserves or publishes. */
    public static RawHistoryRow replayOriginals(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,RawHistoryRow row)throws IOException {
        return replayRow(bound,catalog,installed(catalog,row.source().original()),row);
    }
    private static RawHistoryRow replayRow(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,ReadContract<?> identical,
            RawHistoryRow original)throws IOException {
        Objects.requireNonNull(original);Source source=original.source();
        StrictJson.require(installed(catalog,source.original())==identical,"cold execute-query replay requires the exact source-installed local contract");
        PlanningReadReceipt receipt=bound.loadRead(source.originalReceipt());
        Originals originals=originals(bound,catalog,identical,receipt,source.originalReceipt());requireSourceFiles(originals,source.producerSources());
        requireMaterial(bound,source.fullResult(),originals.projection().fullResult());
        RawHistoryRow replayed=derive(originals,source.fullResult(),original.index(),source.producerSources());
        StrictJson.require(replayed.equals(original),"complete original execute-query report/source differs from installed pure replay");
        RawJson encoded=new RawJson(original.encode());requireMaterial(bound,bound.materialReferenceOf(encoded),encoded);return original;
    }
    private static RawHistoryRow derive(Originals originals,ExactRef full,long index,List<ExactRef> producerSources) {
        PlanningReadReceipt receipt=originals.receipt();ExecuteProjection projection=originals.projection();
        var support=new LinkedHashSet<ExactRef>(originals.support());support.addAll(projection.sourceClosure());support.addAll(producerSources);support.add(full);
        Source source=new Source(originals.binding(),projection.logicalOperation(),projection.originalCommand(),receipt.request().before(),receipt.request().source(),
                receipt.request().sessionId(),receipt.before().binding().connectionGeneration(),sequence(nativeResult(receipt)),receipt.request().arguments(),full,
                projection.publicNumbers(),List.copyOf(support),producerSources,projection.sourceClosure());
        return new RawHistoryRow(index,projection.originalCommand().value(),true,DriverJson.object(projection.fullResult().bytes(),RawJson.MAXIMUM_BYTES),source);
    }
    private static Originals originals(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,ReadContract<?> identical,
            PlanningReadReceipt expected,ExactRef reference) {
        Objects.requireNonNull(bound);Objects.requireNonNull(catalog);Objects.requireNonNull(identical);positive(reference);
        StrictJson.require(catalog.containsIdentity(identical)&&identical.hasPureReplay()
                &&identical.originalHistoryKind().equals(Optional.of(Kind.PUBLIC_EXECUTE_QUERY))
                &&identical.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP&&identical.wireProfile()==ReadContract.WireProfile.EXECUTE_STEP,
                "identical installed finite execute-query gameplay contract and pure projector required");
        var installed=catalog.installed().stream().filter(value->value.contract()==identical).toList();
        StrictJson.require(installed.size()==1,"exactly one installed execute-query definition/decoder required");
        PlanningReadReceipt receipt=bound.loadRead(reference);
        StrictJson.require(receipt.equals(expected)&&bound.readReferenceOf(receipt).equals(reference)
                &&receipt.contractId().equals(identical.contractId())&&receipt.request().operation().equals(identical.operation()),
                "actual archived execute-query receipt/contract differs");
        NativeRecordedEvidenceVerifier.requireRead(receipt,bound);
        StrictJson.require(receipt.request().origin() instanceof CommandOrigin.Gameplay,"frontend/private reconciliation cannot become ordinary execute-query history");
        var support=new LinkedHashSet<ExactRef>();
        for(PlanningReadGuard guard:List.of(receipt.before(),receipt.after())) {
            StrictJson.require(guard.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP&&guard.paused()&&guard.mapReady()&&guard.playerAlive()
                    &&guard.binding().origin().equals(receipt.request().origin())&&guard.binding().observed().equals(receipt.request().before()),
                    "execute-query original guard crossed its living paused gameplay frame");
            requirePacket(bound,guard.binding().nativeEvidence());requirePacket(bound,guard.binding().capabilityEvidence());
            support.add(guard.binding().nativeEvidence());support.add(guard.binding().capabilityEvidence());
            for(ExactRef material:guard.binding().supportingEvidence()) {RawJson raw=bound.loadMaterial(material);requireMaterial(bound,material,raw);support.add(material);}
        }
        StrictJson.require(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()),"execute-query crossed complete semantic/modal binding");
        var payload=identical.projectOriginalHistoryPayload(receipt);
        StrictJson.require(payload instanceof ExecuteProjection,"execute-query history requires its explicit source-owned ExecuteProjection");
        ExecuteProjection projection=(ExecuteProjection)payload;DriverExecuteReadHistoryRegistry.require(receipt,projection);
        Obj report=DriverJson.object(projection.fullResult().bytes(),RawJson.MAXIMUM_BYTES),nativeResult=nativeResult(receipt);
        if(nativeResult.members().containsKey("snapshot_revision"))StrictJson.require(OpportunityJson.integer(nativeResult.get("snapshot_revision"),"native snapshot revision")
                .equals(receipt.request().before().frame().identity().nativeRevision()),"execute-query native revision differs from original guard");
        Optional<BigInteger> sequence=sequence(nativeResult);
        if(report.members().containsKey("query_sequence"))StrictJson.require(sequence(report).equals(sequence),"execute-query report replaced actual native query sequence");
        ExactRef acknowledgement=bound.referenceOf(receipt.original());
        ReadBinding binding=new ReadBinding(identical.contractId(),receipt.requestId(),reference,acknowledgement,identical.sourceRef(),installed.getFirst().decoderSource(),
                identical.permissionMode(),identical.wireProfile(),identical.requiredCapability(),identical.permissionKey());
        support.add(reference);support.add(acknowledgement);support.add(binding.definitionSource());support.add(binding.decoderSource());
        return new Originals(receipt,binding,projection,support);
    }
    private static ReadContract<?> installed(RootReadContractCatalog catalog,ReadBinding source) {
        Objects.requireNonNull(catalog);var found=catalog.installed().stream().filter(value->value.contract().contractId().equals(source.contractId())).toList();
        StrictJson.require(found.size()==1&&found.getFirst().contract().sourceRef().equals(source.definitionSource())
                &&found.getFirst().decoderSource().equals(source.decoderSource()),"original execute-query definition/decoder closure is unavailable");
        requireContract(found.getFirst().contract(),source);return found.getFirst().contract();
    }
    private static void requireContract(ReadContract<?> contract,ReadBinding source) {
        Objects.requireNonNull(contract);
        StrictJson.require(contract.contractId().equals(source.contractId())&&contract.sourceRef().equals(source.definitionSource())
                &&contract.permissionMode()==source.permissionMode()&&contract.wireProfile()==source.wireProfile()
                &&contract.requiredCapability().equals(source.requiredCapability())&&contract.permissionKey().equals(source.permissionKey()),
                "original execute-query local contract permission/capability/wire binding changed");
    }
    private static void requireKnownValue(ReadContract<?> identical,PlanningReadResult.Known<?> actual) {
        Object decoded=identical.replay(actual.receipt()),claimed=actual.value();
        StrictJson.require(decoded!=null&&claimed!=null&&decoded.getClass()==claimed.getClass()&&decoded.equals(claimed),
                "actual execute-query Known value differs from identical pure source decoder");
    }
    private static void requireSourceFiles(Originals originals,List<ExactRef> producers)throws IOException {
        var refs=new LinkedHashSet<ExactRef>(producers);refs.addAll(originals.projection().sourceClosure());
        refs.add(originals.binding().definitionSource());refs.add(originals.binding().decoderSource());
        for(ExactRef ref:refs) {
            var observed=SharedSourceFiles.observe(Path.of(ref.path()));
            StrictJson.require(observed.source().bytes()==ref.bytes()&&observed.source().sha256().equals(ref.sha256()),"original execute-query producer/source bytes changed");
            SharedSourceFiles.assertUnchanged(observed);
        }
    }
    private static void requireSourceShape(Originals originals,List<ExactRef> producers) {
        var support=new LinkedHashSet<ExactRef>(originals.support());support.addAll(originals.projection().sourceClosure());support.addAll(producers);
        StrictJson.require(support.size()<512,"execute-query closure must reserve its full-result artifact slot before any preservation");
        support.forEach(DriverExecuteQueryHistoryRowProducer::positive);
        var request=originals.receipt().request();unsigned(originals.receipt().before().binding().connectionGeneration(),true);
        StrictJson.require(request.source().machineId().equals(request.before().machineId()),"execute-query source/frame machine differs");
    }
    private static Obj nativeResult(PlanningReadReceipt receipt){return DriverJson.object(receipt.original().originalResultToken().orElseThrow(()->new IllegalArgumentException("original execute-query native result token absent")).bytes(),RawJson.MAXIMUM_BYTES);}
    private static Optional<BigInteger> sequence(Obj result) {
        if(!result.members().containsKey("query_sequence"))return Optional.empty();
        BigInteger value=OpportunityJson.integer(result.get("query_sequence"),"actual native query sequence");unsigned(value,true);return Optional.of(value);
    }
    private static void requirePacket(ActionPorts.OutcomeArchive bound,ExactRef reference) {
        positive(reference);byte[] bytes=bound.readOriginalPacket(reference);
        StrictJson.require(reference.bytes()==bytes.length&&reference.sha256().equals(DriverJson.sha256(bytes)),"original guard native/HELLO packet bytes or hash changed");
    }
    private static void requireMaterial(ActionPorts.OutcomeArchive bound,ExactRef reference,RawJson expected) {
        RawJson retained=bound.loadMaterial(reference);
        StrictJson.require(reference.bytes()==retained.bytes().length&&reference.sha256().equals(DriverJson.sha256(retained.bytes()))
                &&Arrays.equals(retained.bytes(),expected.bytes())&&bound.materialReferenceOf(retained).equals(reference),
                "original execute-query material namespace/bytes/hash changed");
    }

    private static final Set<String> SOURCE_KEYS=Set.of("schema","kind","original","logical_operation","original_command","source_frame","source","session_id",
            "connection_generation","query_sequence","arguments","full_result","public_number_roles","supporting_evidence","producer_sources","projection_sources");
    private static Obj sourceJson(Source source) {
        var fields=new java.util.LinkedHashMap<String,Value>();fields.put("schema",new Text(SOURCE_SCHEMA));fields.put("kind",new Text(Kind.PUBLIC_EXECUTE_QUERY.name()));
        fields.put("original",bindingJson(source.original()));fields.put("logical_operation",new Text(source.logicalOperation().value()));fields.put("original_command",new Text(source.originalCommand().value()));
        fields.put("source_frame",DriverJson.object(StrictJson.canonical(ProposalLifecycleCodec.observation(source.sourceFrame())),DriverJson.MAX_NATIVE_BYTES));
        fields.put("source",DriverJson.object(StrictJson.canonical(ProposalLifecycleCodec.source(source.source())),DriverJson.MAX_NATIVE_BYTES));
        fields.put("session_id",new Text(source.sessionId()));fields.put("connection_generation",new IntegerValue(source.connectionGeneration()));
        fields.put("query_sequence",source.querySequence().<Value>map(IntegerValue::new).orElse(Nil.INSTANCE));fields.put("arguments",source.arguments());fields.put("full_result",refJson(source.fullResult()));
        fields.put("public_number_roles",source.publicNumbers().toJson());fields.put("supporting_evidence",refsJson(source.supportingEvidence()));
        fields.put("producer_sources",refsJson(source.producerSources()));fields.put("projection_sources",refsJson(source.projectionSources()));return new Obj(fields);
    }
    private static Obj bindingJson(ReadBinding binding) {
        var fields=new java.util.LinkedHashMap<String,Value>();fields.put("contract_id",new Text(binding.contractId()));fields.put("request_id",new Text(binding.requestId()));
        fields.put("read",refJson(binding.read()));fields.put("acknowledgement",refJson(binding.acknowledgement()));fields.put("definition_source",refJson(binding.definitionSource()));
        fields.put("decoder_source",refJson(binding.decoderSource()));fields.put("permission_mode",new Text(binding.permissionMode().name()));fields.put("wire_profile",new Text(binding.wireProfile().name()));
        fields.put("required_capability",binding.requiredCapability().<Value>map(Text::new).orElse(Nil.INSTANCE));fields.put("permission_key",new Text(binding.permissionKey()));return new Obj(fields);
    }
    /** Exact source header and original formatter roles only; no public identity conversion or authority is invented. */
    public static PublicNumbers publicNumbersFromSource(Value value){return PublicNumbers.fromJson(sourceHeader(value).get("public_number_roles"));}
    private static Obj sourceHeader(Value value) {
        Obj source=OpportunityJson.object(value,"execute-query history source");
        StrictJson.require(source.members().keySet().equals(SOURCE_KEYS)&&new Text(SOURCE_SCHEMA).equals(source.get("schema"))
                &&new Text(Kind.PUBLIC_EXECUTE_QUERY.name()).equals(source.get("kind")),"exact finite execute-query source schema required");return source;
    }
    public static RawHistoryRow decode(byte[] encoded) {
        Obj row=DriverJson.object(encoded,RawJson.MAXIMUM_BYTES);
        StrictJson.require(row.members().keySet().equals(Set.of("index","command","ok","result",SOURCE_FIELD)),"exact complete original execute-query history row required");
        Obj source=sourceHeader(row.get(SOURCE_FIELD));Value query=source.get("query_sequence");
        Source typed=new Source(readBinding(source.get("original")),new OperationKey(OpportunityJson.text(source.get("logical_operation"),"logical operation")),
                new OperationKey(OpportunityJson.text(source.get("original_command"),"original command")),
                ProposalLifecycleCodec.decodeObservation(OpportunityJson.toNode(source.get("source_frame"))),G2Wire.source(OpportunityJson.toNode(source.get("source"))),
                OpportunityJson.text(source.get("session_id"),"original session"),OpportunityJson.integer(source.get("connection_generation"),"original connection generation"),
                query==Nil.INSTANCE?Optional.empty():Optional.of(OpportunityJson.integer(query,"actual native query sequence")),OpportunityJson.object(source.get("arguments"),"original arguments"),
                reference(source.get("full_result")),PublicNumbers.fromJson(source.get("public_number_roles")),refs(source.get("supporting_evidence")),refs(source.get("producer_sources")),refs(source.get("projection_sources")));
        return new RawHistoryRow(OpportunityJson.integer(row.get("index"),"original index").longValueExact(),OpportunityJson.text(row.get("command"),"original command"),
                OpportunityJson.bool(row.get("ok"),"original ok"),OpportunityJson.object(row.get("result"),"complete original report"),typed);
    }
    private static ReadBinding readBinding(Value value) {
        Obj object=OpportunityJson.object(value,"execute-query original binding");
        StrictJson.require(object.members().keySet().equals(Set.of("contract_id","request_id","read","acknowledgement","definition_source","decoder_source",
                "permission_mode","wire_profile","required_capability","permission_key")),"exact execute-query original binding fields required");
        Value capability=object.get("required_capability");
        return new ReadBinding(OpportunityJson.text(object.get("contract_id"),"original contract"),OpportunityJson.text(object.get("request_id"),"original request"),reference(object.get("read")),
                reference(object.get("acknowledgement")),reference(object.get("definition_source")),reference(object.get("decoder_source")),
                ReadContract.PermissionMode.valueOf(OpportunityJson.text(object.get("permission_mode"),"original local permission mode")),
                ReadContract.WireProfile.valueOf(OpportunityJson.text(object.get("wire_profile"),"original wire profile")),
                capability==Nil.INSTANCE?Optional.empty():Optional.of(OpportunityJson.text(capability,"original required capability")),OpportunityJson.text(object.get("permission_key"),"original local permission key"));
    }
    private static List<ExactRef> refs(Value value){return OpportunityJson.array(value,"exact execute-query references").stream().map(DriverExecuteQueryHistoryRowProducer::reference).toList();}
    private static Arr refsJson(List<ExactRef> references){return new Arr(references.stream().<Value>map(DriverExecuteQueryHistoryRowProducer::refJson).toList());}
    private static Obj refJson(ExactRef reference){return DriverJson.object(StrictJson.canonical(reference.toJson()),DriverJson.MAX_NATIVE_BYTES);}
    private static ExactRef reference(Value value){return DriverObservationEvidenceReader.reference(value);}
    private static List<ExactRef> references(List<ExactRef> values,int minimum,int maximum) {
        values=List.copyOf(values);StrictJson.require(values.size()>=minimum&&values.size()<=maximum&&new LinkedHashSet<>(values).size()==values.size(),"bounded distinct execute-query source references required");
        values.forEach(DriverExecuteQueryHistoryRowProducer::positive);return values;
    }
    private static void positive(ExactRef reference){Objects.requireNonNull(reference);StrictJson.require(reference.bytes()>0,"nonempty exact original reference required");}
    private static void unsigned(BigInteger value,boolean positive){StrictJson.require(value!=null&&value.signum()>=(positive?1:0)&&value.compareTo(StrictJson.UINT64_MAX)<=0,"exact original uint64 required");}
    private static IntegerValue number(long value){return new IntegerValue(BigInteger.valueOf(value));}
    private static Value ordered(Value value) {
        if(value instanceof Obj object){var fields=new java.util.LinkedHashMap<String,Value>();new java.util.TreeMap<>(object.members()).forEach((name,item)->fields.put(name,ordered(item)));return new Obj(fields);}
        if(value instanceof Arr array)return new Arr(array.items().stream().map(DriverExecuteQueryHistoryRowProducer::ordered).toList());return value;
    }
}
