package org.xar.ck3.control.application.history;

import java.io.IOException;
import java.math.BigInteger;
import java.util.*;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.history.DriverPublicExecuteFailureMaterial.*;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Original Driver catch rows. Only the registered private invocation can mint a live candidate. */
public final class DriverPublicExecuteFailureRowProducer {
    public static final String SOURCE_FIELD="public_execute_failure_source";
    public static final String SOURCE_SCHEMA="xar.public-execute-failure-source/v1";
    private static final Set<String> SOURCE_FIELDS=Set.of("schema","command","exception_class","exception_message","result","public_number_roles",
            "before_driver","original_known","native_frame","driver_facts","invocation","caller","epoch_manifest","unsupported_capabilities","unresolved_action","head_sequence","head_digest","producer_sources");
    private DriverPublicExecuteFailureRowProducer() { }

    public record Source(String command,OriginalError error,Optional<ExactRef> result,Optional<PublicNumbers> publicNumbers,ExactRef beforeDriver,
            ExactRef originalKnown,ExactRef nativeFrame,ExactRef driverFacts,ExactRef invocation,ExactRef caller,Optional<ExactRef> epochManifest,Optional<ExactRef> unsupportedCapabilities,Optional<ExactRef> unresolvedAction,
            long headSequence,String headDigest,List<ExactRef> producerSources) {
        public Source {
            StrictJson.text(command);Objects.requireNonNull(error);Objects.requireNonNull(result);Objects.requireNonNull(publicNumbers);
            StrictJson.require(result.isPresent()==publicNumbers.isPresent(),"actual error result requires its owning public integer roles");
            for(var ref:List.of(beforeDriver,originalKnown,nativeFrame,driverFacts,invocation,caller))positive(ref);
            Objects.requireNonNull(epochManifest).ifPresent(DriverPublicExecuteFailureRowProducer::positive);
            result.ifPresent(DriverPublicExecuteFailureRowProducer::positive);StrictJson.safe(headSequence,0);
            Objects.requireNonNull(unsupportedCapabilities);unsupportedCapabilities.ifPresent(DriverPublicExecuteFailureRowProducer::positive);
            Objects.requireNonNull(unresolvedAction);unresolvedAction.ifPresent(DriverPublicExecuteFailureRowProducer::positive);
            StrictJson.require(headDigest!=null&&headDigest.matches("[0-9a-f]{64}"),"original invocation writer digest required");
            producerSources=refs(producerSources,1,DriverPublicExecuteFailureMaterial.MAX_PRODUCER_SOURCES);
        }
        public List<ExactRef> evidence(){
            var refs=new LinkedHashSet<ExactRef>(producerSources);
            refs.addAll(List.of(beforeDriver,originalKnown,nativeFrame,driverFacts,invocation,caller));epochManifest.ifPresent(refs::add);result.ifPresent(refs::add);unsupportedCapabilities.ifPresent(refs::add);unresolvedAction.ifPresent(refs::add);
            return List.copyOf(refs);
        }
        public Source(String command,OriginalError error,Optional<ExactRef> result,Optional<PublicNumbers> publicNumbers,ExactRef beforeDriver,
                ExactRef originalKnown,ExactRef nativeFrame,ExactRef driverFacts,ExactRef invocation,ExactRef caller,ExactRef epochManifest,Optional<ExactRef> unsupportedCapabilities,
                Optional<ExactRef> unresolvedAction,long headSequence,String headDigest,List<ExactRef> producerSources) {
            this(command,error,result,publicNumbers,beforeDriver,originalKnown,nativeFrame,driverFacts,invocation,caller,Optional.of(epochManifest),unsupportedCapabilities,unresolvedAction,headSequence,headDigest,producerSources);
        }
    }
    public record RawHistoryRow(long index,Source source,Optional<Obj> result) {
        public RawHistoryRow {StrictJson.safe(index,1);Objects.requireNonNull(source);Objects.requireNonNull(result);
            StrictJson.require(source.result().isPresent()==result.isPresent(),"original result presence cannot change");}
        public String command(){return source.command();}
        public boolean ok(){return false;}
        public String error(){return source.error().recorded();}
        public Obj toJson(){
            var fields=new LinkedHashMap<String,Value>();fields.put("index",integer(index));fields.put("command",text(command()));
            fields.put("ok",new Bool(false));fields.put("error",text(error()));result.ifPresent(value->fields.put("result",value));
            fields.put(SOURCE_FIELD,sourceJson(source));return new Obj(fields);
        }
        public byte[] encode(){return DriverJson.encode(toJson());}
        public DriverStateSnapshot.HistoryEntry historyEntry(){return new DriverStateSnapshot.HistoryEntry(index,new DriverStateSnapshot.Value(encode()));}
    }
    /** The JSON decoder never constructs this live conclusion. */
    public static final class Candidate {
        private final RawHistoryRow row;private final ExactRef rowReference;
        private Candidate(RawHistoryRow row,ExactRef original){this.row=row;rowReference=original;}
        public RawHistoryRow row(){return row;}
        public Source source(){return row.source();}
        public ExactRef rowReference(){return rowReference;}
        public DriverStateSnapshot.HistoryEntry historyEntry(){return row.historyEntry();}
        public long headSequence(){return row.source().headSequence();}
        public String headDigest(){return row.source().headDigest();}
    }
    public static Candidate prepare(Session same,OutcomeArchive bound,DriverStateAssembler authority,
            OriginalInvocation invocation,long nextIndex,List<ExactRef> publisherSources)throws IOException {
        Objects.requireNonNull(invocation);Objects.requireNonNull(same);StrictJson.safe(nextIndex,1);
        var originals=invocation.issuer().requireOriginal(same,authority,bound,invocation);
        StrictJson.require(same.head().state().sequence()==originals.headSequence()&&same.head().digest().equals(originals.headDigest()),
                "failure escaped its actual original writer head");
        var producers=new LinkedHashSet<ExactRef>(originals.producerSources());producers.addAll(publisherSources);
        StrictJson.require(invocation.issuer().sources().containsAll(originals.producerSources()),"failure producer not in installed source closure");
        var source=new Source(originals.originalCommand().value(),originals.error(),originals.result(),originals.publicNumbers(),originals.beforeDriver(),
                originals.originalKnown(),originals.nativeFrame(),originals.driverFacts(),originals.invocation(),originals.caller(),originals.epochManifest(),originals.unsupportedCapabilities(),originals.unresolvedAction(),
                originals.headSequence(),originals.headDigest(),refs(List.copyOf(producers),1,DriverPublicExecuteFailureMaterial.MAX_PRODUCER_SOURCES));
        var row=new RawHistoryRow(nextIndex,source,result(bound,source));
        requireOriginals(bound,row);
        StrictJson.require(Arrays.equals(originals.before().driver().encode(),bound.loadFullMaterial(source.beforeDriver()).bytes()),
                "failure changed its actual complete Driver predecessor");
        ExactRef rowRef=bound.preserveMaterial(RawJson.fullMaterial(row.encode()));
        StrictJson.require(decode(bound.loadFullMaterial(rowRef).bytes()).equals(row),"failure row archive roundtrip changed");
        invocation.issuer().requireOriginal(same,authority,bound,invocation);
        return new Candidate(row,rowRef);
    }
    /** Historical DATA replay only. Canonical event membership and live issuer identity remain separate. */
    public static RawHistoryRow replayOriginals(OutcomeArchive bound,RawHistoryRow row){
        requireOriginals(bound,row);return row;
    }
    private static void requireOriginals(OutcomeArchive bound,RawHistoryRow row){
        var source=row.source();
        var knownWire=DriverSnapshotFacts.originalKnownJson(bound.loadFullMaterial(source.originalKnown()).bytes());
        var manifest=bound.loadFullMaterial(source.driverFacts());
        var nativeFrame=DriverObservationEvidenceReader.nativeFrame(source.driverFacts(),manifest,bound.loadNativeFrame(source.nativeFrame()));
        var facts=DriverObservationEvidenceReader.decode(source.driverFacts(),manifest,
                bound.loadFullMaterial(DriverObservationEvidenceReader.currentDriverReference(source.driverFacts(),manifest)),nativeFrame);
        var presence=DriverSnapshotFacts.observationOriginalReference(knownWire);
        StrictJson.require(presence.isEmpty()||presence.orElseThrow().equals(facts.semanticFactsEvidence()),"failure original Known observation manifest differs");
        var known=DriverSnapshotFacts.decodeKnownOriginal(knownWire,presence.isPresent()?Optional.of(facts):Optional.empty());
        StrictJson.require(Arrays.equals(known.driver().encode(),bound.loadFullMaterial(source.beforeDriver()).bytes())
                &&Arrays.equals(facts.driver().encode(),known.driver().encode())
                &&facts.driverVersion()==known.stamp().driverVersion()&&facts.episodeEpoch()==known.stamp().episodeEpoch()
                &&known.stamp().game().equals(nativeFrame.session().game()),
                "failure Native/Driver/Known originals crossed their actual episode/version");
        StrictJson.require(new DriverObservationAssembler().assemble(nativeFrame,facts,source.nativeFrame()) instanceof DriverObservationAssembler.Complete,
                "original generic Driver entry requires its actual joined actor/episode frame");
        var invocation=closed(bound.loadFullMaterial(source.invocation()).bytes(),Set.of("schema","command","exception_class","exception_message","result","public_number_roles",
                "before_driver","original_known","native_frame","driver_facts","caller","epoch_manifest","unsupported_capabilities","unresolved_action","head_sequence","head_digest","producer_sources"));
        StrictJson.require("xar.root-public-execute-driver-failure/v1".equals(string(invocation,"schema")),"original Root failure invocation version required");
        var fields=new LinkedHashMap<String,Value>(sourceJson(source).members());fields.remove("invocation");
        Obj expected=new Obj(fields).with("schema",text("xar.root-public-execute-driver-failure/v1"));
        // The invocation pins active owner sources; the row additionally carries the sole publisher's code.
        var originalProducers=readRefs(invocation.get("producer_sources"),1,DriverPublicExecuteFailureMaterial.MAX_PRODUCER_SOURCES);
        expected=expected.with("producer_sources",array(originalProducers));
        StrictJson.require(invocation.equals(expected)&&source.producerSources().containsAll(originalProducers),"failure invocation and original exception/command/result differ");
        StrictJson.require(row.result().equals(result(bound,source)),"failure lost or manufactured its actual original result");
        row.result().ifPresent(value->source.publicNumbers().orElseThrow().toPublic(value));
        // Its original bytes are retained; this DATA replay grants no current source qualification.
        source.epochManifest().ifPresent(bound::loadFullMaterial);
        var caller=DriverJson.object(bound.loadFullMaterial(source.caller()).bytes(),DriverJson.MAX_NATIVE_BYTES);
        StrictJson.require(source.command().equals(string(caller,"step")),"failure history command differs from its original public caller");
        source.unsupportedCapabilities().ifPresent(ref->{
            var caps=DriverJson.object(bound.loadFullMaterial(ref).bytes(),DriverJson.MAX_NATIVE_BYTES);
            StrictJson.require(source.error().equals(unsupportedHireError(source.command(),caps))&&row.result().isEmpty(),
                    "fixed unsupported hire changed its actual advertised branch/error or manufactured a result");
        });
        source.unresolvedAction().ifPresent(ref->{
            var actual=bound.loadReceipt(ref);
            StrictJson.require(actual.outcome()==org.xar.ck3.control.application.action.ActionReceipt.Outcome.UNRESOLVED,
                    "failure unresolved binding is not an actual retained unresolved receipt");
        });
    }
    public static RawHistoryRow decode(byte[] original){
        Obj row=DriverJson.object(original,DriverJson.MAX_NATIVE_BYTES);
        var fields=new HashSet<>(Set.of("index","command","ok","error",SOURCE_FIELD));if(row.members().containsKey("result"))fields.add("result");
        StrictJson.require(row.members().keySet().equals(fields)&&row.get("ok") instanceof Bool b&&!b.value(),"exact original failed history row fields required");
        Source source=source(OpportunityJson.object(row.get(SOURCE_FIELD),SOURCE_FIELD));
        StrictJson.require(string(row,"command").equals(source.command())&&string(row,"error").equals(source.error().recorded()),"failed history command/error differs from source");
        return new RawHistoryRow(OpportunityJson.integer(row.get("index"),"index").longValueExact(),source,
                row.members().containsKey("result")?Optional.of(OpportunityJson.object(row.get("result"),"result")):Optional.empty());
    }
    public static Obj sourceJson(Source source){
        var row=new LinkedHashMap<String,Value>();row.put("schema",text(SOURCE_SCHEMA));row.put("command",text(source.command()));
        row.put("exception_class",text(source.error().pythonClass()));row.put("exception_message",text(source.error().message()));
        row.put("result",source.result().<Value>map(DriverObservationEvidenceReader::reference).orElse(Nil.INSTANCE));
        row.put("public_number_roles",source.publicNumbers().<Value>map(PublicNumbers::toJson).orElse(Nil.INSTANCE));
        row.put("before_driver",reference(source.beforeDriver()));row.put("original_known",reference(source.originalKnown()));
        row.put("native_frame",reference(source.nativeFrame()));row.put("driver_facts",reference(source.driverFacts()));
        row.put("invocation",reference(source.invocation()));row.put("caller",reference(source.caller()));row.put("epoch_manifest",optionalReference(source.epochManifest()));
        row.put("unsupported_capabilities",source.unsupportedCapabilities().<Value>map(DriverObservationEvidenceReader::reference).orElse(Nil.INSTANCE));
        row.put("unresolved_action",source.unresolvedAction().<Value>map(DriverObservationEvidenceReader::reference).orElse(Nil.INSTANCE));
        row.put("head_sequence",integer(source.headSequence()));row.put("head_digest",text(source.headDigest()));row.put("producer_sources",array(source.producerSources()));
        return new Obj(row);
    }
    private static Source source(Obj row){
        StrictJson.require(optionalEpochFields(row,SOURCE_FIELDS)&&SOURCE_SCHEMA.equals(string(row,"schema")),"exact failed invocation source version/fields required");
        return new Source(string(row,"command"),new OriginalError(string(row,"exception_class"),message(row,"exception_message")),
                row.get("result")==Nil.INSTANCE?Optional.empty():Optional.of(DriverObservationEvidenceReader.reference(row.get("result"))),
                row.get("public_number_roles")==Nil.INSTANCE?Optional.empty():Optional.of(PublicNumbers.fromJson(row.get("public_number_roles"))),
                ref(row,"before_driver"),ref(row,"original_known"),ref(row,"native_frame"),ref(row,"driver_facts"),ref(row,"invocation"),ref(row,"caller"),optionalReference(row.get("epoch_manifest")),
                row.get("unsupported_capabilities")==Nil.INSTANCE?Optional.empty():Optional.of(DriverObservationEvidenceReader.reference(row.get("unsupported_capabilities"))),
                row.get("unresolved_action")==Nil.INSTANCE?Optional.empty():Optional.of(DriverObservationEvidenceReader.reference(row.get("unresolved_action"))),
                OpportunityJson.integer(row.get("head_sequence"),"head_sequence").longValueExact(),string(row,"head_digest"),readRefs(row.get("producer_sources"),1,DriverPublicExecuteFailureMaterial.MAX_PRODUCER_SOURCES));
    }
    public static Obj invocationJson(InvocationData data){
        var row=new LinkedHashMap<String,Value>();row.put("schema",text("xar.root-public-execute-driver-failure/v1"));
        row.put("command",text(data.originalCommand().value()));row.put("exception_class",text(data.error().pythonClass()));
        row.put("exception_message",text(data.error().message()));row.put("result",data.result().<Value>map(DriverObservationEvidenceReader::reference).orElse(Nil.INSTANCE));
        row.put("public_number_roles",data.publicNumbers().<Value>map(PublicNumbers::toJson).orElse(Nil.INSTANCE));
        row.put("before_driver",reference(data.beforeDriver()));row.put("original_known",reference(data.originalKnown()));
        row.put("native_frame",reference(data.nativeFrame()));row.put("driver_facts",reference(data.driverFacts()));row.put("caller",reference(data.caller()));
        row.put("epoch_manifest",optionalReference(data.epochManifest()));row.put("head_sequence",integer(data.headSequence()));
        row.put("unsupported_capabilities",data.unsupportedCapabilities().<Value>map(DriverObservationEvidenceReader::reference).orElse(Nil.INSTANCE));
        row.put("unresolved_action",data.unresolvedAction().<Value>map(DriverObservationEvidenceReader::reference).orElse(Nil.INSTANCE));
        row.put("head_digest",text(data.headDigest()));row.put("producer_sources",array(data.producerSources()));return new Obj(row);
    }
    public static Optional<PublicNumbers> publicNumbersFromSource(Value value){
        var actual=source(OpportunityJson.object(value,"public execute failure source"));return actual.publicNumbers();
    }
    public static boolean fixedUnsupportedHire(String step){return "hire-mercenary-v1".equals(step)||"hire-holy-order-v1".equals(step);}
    /** Exact original native_driver16179/11152/12878 branches, with their actual capability order. */
    public static OriginalError unsupportedHireError(String step,Obj actualCapabilities){
        StrictJson.require(fixedUnsupportedHire(step),"only the two original unimplemented generic hire steps have this policy");
        var actions=strings(actualCapabilities.get("action_steps"));
        String message;
        if(actions.contains(step))message="native Python bridge does not implement war step "+step;
        else if(actualCapabilities.members().containsKey("composite_action_steps")&&strings(actualCapabilities.get("composite_action_steps")).contains(step))
            message="native Python bridge does not implement composite step "+step;
        else message="native DLL does not implement gameplay step "+step;
        return new OriginalError("UnsupportedStepError",message);
    }
    private static List<String> strings(Value value){StrictJson.require(value instanceof Arr,"actual capability step list required");return ((Arr)value).items().stream().map(item->OpportunityJson.text(item,"capability step")).toList();}
    private static Optional<Obj> result(OutcomeArchive bound,Source source){return source.result().map(ref->DriverJson.object(bound.loadFullMaterial(ref).bytes(),DriverJson.MAX_NATIVE_BYTES));}
    private static Obj closed(byte[] bytes,Set<String> fields){var row=DriverJson.object(bytes,DriverJson.MAX_NATIVE_BYTES);StrictJson.require(optionalEpochFields(row,fields),"exact original invocation fields required");return fields.contains("epoch_manifest")&&!row.members().containsKey("epoch_manifest")?row.with("epoch_manifest",Nil.INSTANCE):row;}
    private static boolean optionalEpochFields(Obj row,Set<String> fields){var expected=new HashSet<>(fields);if(fields.contains("epoch_manifest")&&!row.members().containsKey("epoch_manifest"))expected.remove("epoch_manifest");return row.members().keySet().equals(expected);}
    private static Value optionalReference(Optional<ExactRef> value){return value.<Value>map(DriverObservationEvidenceReader::reference).orElse(Nil.INSTANCE);}
    private static Optional<ExactRef> optionalReference(Value value){return value==null||value==Nil.INSTANCE?Optional.empty():Optional.of(DriverObservationEvidenceReader.reference(value));}
    private static String message(Obj row,String name){StrictJson.require(row.get(name) instanceof Text,"original exception message must be text, including empty text");return ((Text)row.get(name)).value();}
    private static String string(Obj row,String name){return OpportunityJson.text(row.get(name),name);}
    private static ExactRef ref(Obj row,String name){return DriverObservationEvidenceReader.reference(row.get(name));}
    private static Obj reference(ExactRef value){return DriverObservationEvidenceReader.reference(value);}
    private static Text text(String value){return new Text(value);}
    private static IntegerValue integer(long value){return new IntegerValue(BigInteger.valueOf(value));}
    private static Arr array(List<ExactRef> refs){return new Arr(refs.stream().map(DriverObservationEvidenceReader::reference).map(Value.class::cast).toList());}
    private static List<ExactRef> readRefs(Value value,int minimum,int maximum){StrictJson.require(value instanceof Arr,"original reference list required");return refs(((Arr)value).items().stream().map(DriverObservationEvidenceReader::reference).toList(),minimum,maximum);}
    private static List<ExactRef> refs(List<ExactRef> refs,int minimum,int maximum){var copy=List.copyOf(refs);StrictJson.require(copy.size()>=minimum&&copy.size()<=maximum&&new LinkedHashSet<>(copy).size()==copy.size(),"finite distinct original references required");copy.forEach(DriverPublicExecuteFailureRowProducer::positive);return copy;}
    private static void positive(ExactRef ref){StrictJson.require(Objects.requireNonNull(ref).bytes()>0,"nonempty original reference required");}
}
