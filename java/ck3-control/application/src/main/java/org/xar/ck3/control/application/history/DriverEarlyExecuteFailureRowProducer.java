package org.xar.ck3.control.application.history;

import java.io.IOException;
import java.math.BigInteger;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.history.DriverEarlyExecuteFailure.*;
import org.xar.ck3.control.application.history.DriverEarlyExecuteFailure.Error;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Early failed Driver rows from the private original call. No fresh frame/Native query or action retry. */
public final class DriverEarlyExecuteFailureRowProducer {
    private DriverEarlyExecuteFailureRowProducer(){}
    public static final String SOURCE_FIELD="early_execute_failure_source";
    public static final String SOURCE_SCHEMA="xar.early-execute-failure-source/v1";
    public static final String INVOCATION_SCHEMA="xar.root-early-execute-failure/v1";
    private static final Set<String> DATA_FIELDS=Set.of("schema","command","error_origin","exception_class","exception_message","result","public_number_roles","retained","caller","epoch_manifest","unsupported_capabilities","unresolved_action","head_sequence","head_digest","producer_sources");
    public record Source(InvocationData data,ExactRef invocation) {
        public Source {Objects.requireNonNull(data);DriverEarlyExecuteFailure.positive(invocation);}
        public String command(){return data.originalCommand().value();}
        public Error error(){return data.error();}
        public RetainedData retained(){return data.retained();}
        public long headSequence(){return data.headSequence();}
        public String headDigest(){return data.headDigest();}
        public List<ExactRef> evidence(){var refs=new LinkedHashSet<>(data.producerSources());refs.addAll(List.of(invocation,data.caller()));data.epochManifest().ifPresent(refs::add);
            if(data.retained() instanceof CachedData cached){refs.add(cached.beforeDriver());refs.add(cached.originalKnown());cached.historicalSource().ifPresent(refs::add);}
            data.result().ifPresent(refs::add);data.unsupportedCapabilities().ifPresent(refs::add);data.unresolvedAction().ifPresent(refs::add);return List.copyOf(refs);}
    }
    public record RawHistoryRow(long index,Source source,Optional<Obj> result) {
        public RawHistoryRow {StrictJson.safe(index,1);Objects.requireNonNull(source);Objects.requireNonNull(result);
            StrictJson.require(source.retained() instanceof CachedData,"early row requires an actual retained cached Known; absent facts have no index");
            StrictJson.require(source.data().result().isPresent()==result.isPresent(),"actual original result presence changed");}
        public String command(){return source.command();}
        public boolean ok(){return false;}
        public String error(){return source.error().recorded();}
        public Obj toJson(){var fields=new LinkedHashMap<String,Value>();fields.put("index",integer(index));fields.put("command",text(command()));fields.put("ok",new Bool(false));fields.put("error",text(error()));result.ifPresent(value->fields.put("result",value));fields.put(SOURCE_FIELD,sourceJson(source));return new Obj(fields);}
        public byte[] encode(){return DriverJson.encode(toJson());}
        public DriverStateSnapshot.HistoryEntry historyEntry(){return new DriverStateSnapshot.HistoryEntry(index,new DriverStateSnapshot.Value(encode()));}
    }
    public sealed interface Preparation permits Candidate,DriverEarlyExecuteFailure.MissingFacts {}
    /** Only prepare can create this conclusion after the actual Assembler's registered source admits the private ticket. */
    public static final class Candidate implements Preparation {
        private final OriginalInvocation invocation;private final Cached cached;private final RawHistoryRow row;private final ExactRef reference;
        private Candidate(OriginalInvocation invocation,Cached cached,RawHistoryRow row,ExactRef reference){this.invocation=invocation;this.cached=cached;this.row=row;this.reference=reference;}
        public OriginalInvocation invocation(){return invocation;}
        public DriverEarlyExecuteFailure.Source issuer(){return invocation.issuer();}
        public DriverSnapshotFacts.Known before(){return cached.before();}
        public RawHistoryRow row(){return row;}
        public Source source(){return row.source();}
        public ExactRef rowReference(){return reference;}
        public DriverStateSnapshot.HistoryEntry historyEntry(){return row.historyEntry();}
        public long headSequence(){return source().headSequence();}
        public String headDigest(){return source().headDigest();}
    }
    public static Preparation prepare(Session same,OutcomeArchive bound,DriverStateAssembler authority,OriginalInvocation ticket,long nextIndex,List<ExactRef> publisherSources)throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(bound);Objects.requireNonNull(authority);Objects.requireNonNull(ticket);
        var issuer=Objects.requireNonNull(ticket.issuer());authority.requireEarlyExecuteFailureSource(issuer);
        var original=issuer.requireOriginal(same,authority,bound,ticket);requireHead(same,original);
        StrictJson.require(issuer.sources().containsAll(original.producerSources()),"early exception producer outside registered source closure");
        if(original.retained() instanceof Absent absent)return new DriverEarlyExecuteFailure.MissingFacts(absent.reason());
        var cached=(Cached)original.retained();StrictJson.require(nextIndex==Math.addExact((long)cached.before().driver().commandHistory().size(),1),"early failure index must append exactly once to retained complete history");
        var producers=new LinkedHashSet<>(original.producerSources());producers.addAll(publisherSources);DriverEarlyExecuteFailure.refs(List.copyOf(producers));
        var data=DriverEarlyExecuteFailure.invocationData(original);data=new InvocationData(data.originalCommand(),data.error(),data.result(),data.publicNumbers(),data.retained(),data.caller(),data.epochManifest(),data.unsupportedCapabilities(),data.unresolvedAction(),data.headSequence(),data.headDigest(),List.copyOf(producers));
        var source=new Source(data,original.invocation());var row=new RawHistoryRow(nextIndex,source,result(bound,data));
        requireOriginals(bound,row);
        StrictJson.require(Arrays.equals(cached.before().driver().encode(),bound.loadFullMaterial(cached.beforeDriver()).bytes())&&Arrays.equals(DriverSnapshotFacts.encodeKnownOriginal(cached.before()).bytes(),bound.loadFullMaterial(cached.originalKnown()).bytes()),"early failure replaced cached full Driver/Known slots");
        var reference=bound.preserveMaterial(RawJson.fullMaterial(row.encode()));StrictJson.require(decode(bound.loadFullMaterial(reference).bytes()).equals(row),"early failed row archive roundtrip changed");
        authority.requireEarlyExecuteFailureSource(issuer);var rechecked=issuer.requireOriginal(same,authority,bound,ticket);requireHead(same,rechecked);
        StrictJson.require(rechecked.invocation().equals(original.invocation())&&DriverEarlyExecuteFailure.invocationData(rechecked).equals(DriverEarlyExecuteFailure.invocationData(original))&&rechecked.retained() instanceof Cached again&&Arrays.equals(DriverSnapshotFacts.encodeKnownOriginal(again.before()).bytes(),DriverSnapshotFacts.encodeKnownOriginal(cached.before()).bytes()),"early original changed while retaining its row");return new Candidate(ticket,cached,row,reference);
    }
    private static void requireHead(Session same,Originals original)throws IOException{StrictJson.require(same.head().state().sequence()==original.headSequence()&&same.head().digest().equals(original.headDigest()),"early exception crossed its actual writer head");}
    /** Pure archived DATA replay. This never reconstructs Known, grants cold admission, or loads a Native frame by guessed locator. */
    public static RawHistoryRow replayOriginals(OutcomeArchive bound,RawHistoryRow row){requireOriginals(bound,row);return row;}
    private static void requireOriginals(OutcomeArchive bound,RawHistoryRow row){
        Objects.requireNonNull(bound);var source=row.source();var data=source.data();var cached=(CachedData)data.retained();
        var driver=org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.decodeComplete(bound.loadFullMaterial(cached.beforeDriver()).bytes());
        StrictJson.require(row.index()==Math.addExact((long)driver.commandHistory().size(),1),"early row does not append to retained complete Driver history");
        var knownWire=DriverSnapshotFacts.originalKnownJson(bound.loadFullMaterial(cached.originalKnown()).bytes());
        var known=DriverJson.object(knownWire.bytes(),DriverJson.MAX_NATIVE_BYTES);
        StrictJson.require(Arrays.equals(driver.encode(),DriverStateSnapshot.decodeComplete(DriverJson.encode(known.get("driver"))).encode()),"cached complete Driver differs from original Known bytes");
        StrictJson.require(DriverSnapshotFacts.observationOriginalReference(knownWire).equals(cached.historicalSource()),"historical semantic reference differs from original Known presence");
        // A retained semantic manifest is only historical source material. It cannot supply a new frame or replace full Known replay.
        cached.historicalSource().ifPresent(bound::loadFullMaterial);
        var stamp=OpportunityJson.object(known.get("stamp"),"cached original stamp");
        StrictJson.require(stamp.members().keySet().equals(Set.of("driver_version","episode_epoch","game","episode_run_id","driver_sha256")),"closed cached stamp required");
        safe(stamp,"driver_version",0);safe(stamp,"episode_epoch",0);
        StrictJson.require(string(stamp,"driver_sha256").equals(DriverJson.sha256(driver.encode()))&&string(stamp,"episode_run_id").equals(driver.session().episodeRunId())
                &&org.xar.ck3.control.contracts.GameGeneration.fromJson(DriverJson.toNode(stamp.get("game"))).pid()==driver.session().bridgePid(),"cached Driver/stamp identity differs");
        var invocation=decodeInvocation(bound.loadFullMaterial(source.invocation()).bytes());
        var expected=new InvocationData(data.originalCommand(),data.error(),data.result(),data.publicNumbers(),data.retained(),data.caller(),data.epochManifest(),data.unsupportedCapabilities(),data.unresolvedAction(),data.headSequence(),data.headDigest(),invocation.producerSources());
        StrictJson.require(invocation.equals(expected)&&data.producerSources().containsAll(invocation.producerSources()),"early original private invocation and row source differ");
        StrictJson.require(row.result().equals(result(bound,data)),"early error result was changed or fabricated");row.result().ifPresent(value->data.publicNumbers().orElseThrow().toPublic(value));
        var caller=DriverJson.object(bound.loadFullMaterial(data.caller()).bytes(),DriverJson.MAX_NATIVE_BYTES);StrictJson.require(source.command().equals(string(caller,"step")),"early row command differs from original caller");
        data.epochManifest().ifPresent(bound::loadFullMaterial);data.unsupportedCapabilities().ifPresent(bound::loadFullMaterial);
        data.unresolvedAction().ifPresent(ref->StrictJson.require(bound.loadReceipt(ref).outcome()==ActionReceipt.Outcome.UNRESOLVED,"early unresolved evidence is not an actual unresolved receipt"));
    }
    public static RawHistoryRow decode(byte[] original){
        var row=DriverJson.object(original,DriverJson.MAX_NATIVE_BYTES);var names=new HashSet<>(Set.of("index","command","ok","error",SOURCE_FIELD));if(row.members().containsKey("result"))names.add("result");
        StrictJson.require(row.members().keySet().equals(names)&&row.get("ok") instanceof Bool ok&&!ok.value(),"closed original early failed row required");
        var source=source(OpportunityJson.object(row.get(SOURCE_FIELD),SOURCE_FIELD));StrictJson.require(string(row,"command").equals(source.command())&&string(row,"error").equals(source.error().recorded()),"early row command/error differs from its source");
        return new RawHistoryRow(safe(row,"index",1),source,row.members().containsKey("result")?Optional.of(OpportunityJson.object(row.get("result"),"result")):Optional.empty());
    }
    public static Obj sourceJson(Source source){return invocationJson(source.data()).with("schema",text(SOURCE_SCHEMA)).with("invocation",reference(source.invocation()));}
    private static Source source(Obj row){var fields=new HashSet<>(DATA_FIELDS);fields.add("invocation");StrictJson.require(optionalEpochFields(row,fields)&&SOURCE_SCHEMA.equals(string(row,"schema")),"closed early source required");var copy=new LinkedHashMap<>(row.members());copy.remove("invocation");return new Source(invocation(new Obj(copy).with("schema",text(INVOCATION_SCHEMA))),ref(row,"invocation"));}
    public static Obj invocationJson(InvocationData data){
        var row=new LinkedHashMap<String,Value>();row.put("schema",text(INVOCATION_SCHEMA));row.put("command",text(data.originalCommand().value()));row.put("error_origin",text(data.error().origin().name()));row.put("exception_class",text(data.error().className()));
        row.put("exception_message",data.error().message().<Value>map(Text::new).orElse(Nil.INSTANCE));row.put("result",optionalRef(data.result()));row.put("public_number_roles",data.publicNumbers().<Value>map(PublicNumbers::toJson).orElse(Nil.INSTANCE));row.put("retained",retainedJson(data.retained()));
        row.put("caller",reference(data.caller()));row.put("epoch_manifest",optionalRef(data.epochManifest()));row.put("unsupported_capabilities",optionalRef(data.unsupportedCapabilities()));row.put("unresolved_action",optionalRef(data.unresolvedAction()));row.put("head_sequence",integer(data.headSequence()));row.put("head_digest",text(data.headDigest()));row.put("producer_sources",refsJson(data.producerSources()));return new Obj(row);
    }
    public static InvocationData decodeInvocation(byte[] original){return invocation(DriverJson.object(original,DriverJson.MAX_NATIVE_BYTES));}
    private static InvocationData invocation(Obj row){
        StrictJson.require(optionalEpochFields(row,DATA_FIELDS)&&INVOCATION_SCHEMA.equals(string(row,"schema")),"closed early invocation DATA required");
        var error=new Error(ErrorOrigin.valueOf(string(row,"error_origin")),string(row,"exception_class"),row.get("exception_message")==Nil.INSTANCE?Optional.empty():Optional.of(exactText(row.get("exception_message"))));
        return new InvocationData(new OperationKey(string(row,"command")),error,optionalRef(row.get("result")),row.get("public_number_roles")==Nil.INSTANCE?Optional.empty():Optional.of(PublicNumbers.fromJson(row.get("public_number_roles"))),retained(row.get("retained")),ref(row,"caller"),optionalEpoch(row.get("epoch_manifest")),optionalRef(row.get("unsupported_capabilities")),optionalRef(row.get("unresolved_action")),safe(row,"head_sequence",0),string(row,"head_digest"),readRefs(row.get("producer_sources")));
    }
    public static Obj retainedJson(RetainedData data){
        if(data instanceof AbsentData absent)return new Obj(Map.of("kind",text("absent"),"missing_reasons",new Arr(absent.reason().reasons().stream().<Value>map(Text::new).toList())));
        var cached=(CachedData)data;return new Obj(Map.of("kind",text("cached"),"before_driver",reference(cached.beforeDriver()),"original_known",reference(cached.originalKnown()),"historical_source",optionalRef(cached.historicalSource())));
    }
    public static RetainedData retained(Value value){var row=OpportunityJson.object(value,"early retained DATA");return switch(string(row,"kind")){
        case "absent"->{StrictJson.require(row.members().keySet().equals(Set.of("kind","missing_reasons")),"closed absent cached facts required");yield new AbsentData(new Missing(OpportunityJson.array(row.get("missing_reasons"),"missing reasons").stream().map(v->OpportunityJson.text(v,"reason")).toList()));}
        case "cached"->{StrictJson.require(row.members().keySet().equals(Set.of("kind","before_driver","original_known","historical_source")),"closed cached originals required");yield new CachedData(ref(row,"before_driver"),ref(row,"original_known"),optionalRef(row.get("historical_source")));}
        default->throw new IllegalArgumentException("unknown early retained facts discriminator");};}
    public static Optional<PublicNumbers> publicNumbersFromSource(Value value){return source(OpportunityJson.object(value,SOURCE_FIELD)).data().publicNumbers();}
    private static Optional<Obj> result(OutcomeArchive bound,InvocationData data){return data.result().map(ref->DriverJson.object(bound.loadFullMaterial(ref).bytes(),DriverJson.MAX_NATIVE_BYTES));}
    private static String exactText(Value value){StrictJson.require(value instanceof Text,"exact exception message text or null required");return ((Text)value).value();}
    private static String string(Obj row,String name){return OpportunityJson.text(row.get(name),name);}
    private static long safe(Obj row,String name,long minimum){long n=OpportunityJson.integer(row.get(name),name).longValueExact();StrictJson.safe(n,minimum);return n;}
    private static ExactRef ref(Obj row,String name){return DriverObservationEvidenceReader.reference(row.get(name));}
    private static Obj reference(ExactRef ref){return DriverObservationEvidenceReader.reference(ref);}
    private static Value optionalRef(Optional<ExactRef> ref){return ref.<Value>map(DriverObservationEvidenceReader::reference).orElse(Nil.INSTANCE);}
    private static Optional<ExactRef> optionalRef(Value value){return value==Nil.INSTANCE?Optional.empty():Optional.of(DriverObservationEvidenceReader.reference(value));}
    private static Optional<ExactRef> optionalEpoch(Value value){return value==null?Optional.empty():optionalRef(value);}
    private static boolean optionalEpochFields(Obj row,Set<String> fields){var expected=new HashSet<>(fields);if(!row.members().containsKey("epoch_manifest"))expected.remove("epoch_manifest");return row.members().keySet().equals(expected);}
    private static Arr refsJson(List<ExactRef> refs){return new Arr(refs.stream().<Value>map(DriverObservationEvidenceReader::reference).toList());}
    private static List<ExactRef> readRefs(Value value){return DriverEarlyExecuteFailure.refs(OpportunityJson.array(value,"producer sources").stream().map(DriverObservationEvidenceReader::reference).toList());}
    private static Text text(String value){return new Text(value);}
    private static IntegerValue integer(long value){return new IntegerValue(BigInteger.valueOf(value));}
}
