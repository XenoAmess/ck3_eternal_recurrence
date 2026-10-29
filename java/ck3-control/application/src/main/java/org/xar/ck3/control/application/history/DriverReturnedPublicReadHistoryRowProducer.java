package org.xar.ck3.control.application.history;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Optional;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.capabilities.NativeActionSteps;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers;
import org.xar.ck3.control.application.reads.PlanningPublicReadCollection;
import org.xar.ck3.control.application.routecontact.RouteContactSteps;
import org.xar.ck3.control.application.planning.military.WarHistorySteps;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.history.DriverReturnedPublicReadHistoryMaterial.*;

/** Two normal returned public read results, never a thrown error or a successful PlanningReadReceipt. */
public final class DriverReturnedPublicReadHistoryRowProducer {
    public static final String SOURCE_FIELD="returned_public_read_history_source";
    public static final String SOURCE_SCHEMA="xar.driver-returned-public-read-history-source/v1";
    public static final String INVOCATION_SCHEMA="xar.root-returned-public-read-invocation/v1";
    private DriverReturnedPublicReadHistoryRowProducer(){ }
    public record HistorySource(Kind kind,OperationKey logicalOperation,InvocationData original,ExactRef invocation,
            ExactRef acknowledgement,ExactRef preparedRequest,NativeRequestChronology.PacketIdentity outbound,
            ExactRef fullResult,PublicNumbers publicNumbers,List<ExactRef> supportingEvidence,List<ExactRef> producerSources,List<ExactRef> projectionSources) {
        public HistorySource {
            Objects.requireNonNull(kind);Objects.requireNonNull(logicalOperation);Objects.requireNonNull(original);
            requireLogical(kind,logicalOperation);for(var ref:List.of(invocation,acknowledgement,preparedRequest,fullResult))positive(ref);
            Objects.requireNonNull(outbound);Objects.requireNonNull(publicNumbers);
            supportingEvidence=references(supportingEvidence,1,768);producerSources=references(producerSources,1,256);projectionSources=references(projectionSources,1,260);
            StrictJson.require(producerSources.containsAll(original.producerSources()),"returned read source lost original private producer closure");
        }
        public OperationKey originalCommand(){return original.originalCommand();}
        public ExactRef collectionMetadata(){return original.collectionMetadata();}
        public ExactRef beforeDriver(){return original.frames().beforeDriver();}
        public ExactRef originalKnown(){return original.frames().originalKnown();}
        public ExactRef nativeFrame(){return original.frames().nativeFrame();}
        public ExactRef driverFacts(){return original.frames().driverFacts();}
        public ExactRef caller(){return original.caller();}
        public Optional<ExactRef> epochManifest(){return original.epochManifest();}
        public long headSequence(){return original.headSequence();}
        public String headDigest(){return original.headDigest();}
        public List<ExactRef> evidence(){
            var all=new LinkedHashSet<>(supportingEvidence);all.addAll(projectionSources);all.addAll(producerSources());
            all.addAll(List.of(collectionMetadata(),beforeDriver(),originalKnown(),nativeFrame(),driverFacts(),
                    original.frames().readbackNativeFrame(),original.frames().readbackDriverFacts(),caller(),
                    invocation,acknowledgement,preparedRequest,fullResult));epochManifest().ifPresent(all::add);return List.copyOf(all);
        }
    }
    public record RawHistoryRow(long index,HistorySource source,Obj result) {
        public RawHistoryRow {
            StrictJson.safe(index,1);Objects.requireNonNull(source);Objects.requireNonNull(result);
            requireReport(source.kind(),source.logicalOperation(),result);source.publicNumbers().toPublic(result);
        }
        public String command(){return source.originalCommand().value();}
        public boolean ok(){return source.kind()==Kind.PREVIEW_DEFERRED;}
        public Obj toJson(){return new Obj(java.util.Map.of("index",number(index),"command",new Text(command()),"ok",new Bool(ok()),"result",result,SOURCE_FIELD,sourceJson(source)));}
        public byte[] encode(){return DriverJson.encode(toJson());}
        public DriverStateSnapshot.HistoryEntry historyEntry(){return new DriverStateSnapshot.HistoryEntry(index,new DriverStateSnapshot.Value(encode()));}
    }
    /** Only prepare with the identical installed private Source and actual CP19 token can mint this candidate. */
    public static final class Candidate {
        private final Source issuer;private final OriginalReturned invocation;private final RawHistoryRow row;private final ExactRef rowReference;
        private Candidate(Source issuer,OriginalReturned invocation,RawHistoryRow row,ExactRef rowReference){this.issuer=issuer;this.invocation=invocation;this.row=row;this.rowReference=rowReference;}
        public RawHistoryRow row(){return row;}public HistorySource source(){return row.source();}
        public ExactRef rowReference(){return rowReference;}public ExactRef fullResultReference(){return source().fullResult();}
        public DriverStateSnapshot.HistoryEntry historyEntry(){return row.historyEntry();}
        public long headSequence(){return source().headSequence();}public String headDigest(){return source().headDigest();}
    }
    public static Candidate prepare(Session same,OutcomeArchive bound,DriverStateAssembler authority,OriginalReturned actual,
            long nextIndex,List<ExactRef> publisherSources)throws IOException {
        Objects.requireNonNull(actual);StrictJson.safe(nextIndex,1);publisherSources=references(publisherSources,1,256);
        // Publisher.bind checks the unbound owning archive; this path receives its distinct session-bound view.
        Source issuer=Objects.requireNonNull(actual.issuer());
        Originals originals=issuer.requireOriginal(same,authority,bound,actual);
        requireHead(same,originals);issuer.requireCatalog(issuer.catalog());originals.live().requireOriginal(same,bound);
        var recorded=replayCollection(bound,issuer.catalog(),originals.collectionMetadata());
        requireLive(originals,recorded,bound);
        InvocationData data=invocationData(originals);requireMaterial(bound,originals.invocation(),invocationJson(data));
        requireFrames(bound,recorded,data.frames(),originals.before());
        Projection projection=issuer.project(recorded,data,bound);requireProjection(recorded,data,projection);
        var producers=new LinkedHashSet<>(data.producerSources());producers.addAll(publisherSources);
        StrictJson.require(issuer.sources().containsAll(data.producerSources()),"returned read did not come from its actual installed source closure");
        requireFiles(union(List.copyOf(producers),projection.sourceClosure()));
        // All originals and source-owned fixed formatting are checked before the first preservation.
        ExactRef full=bound.preserveMaterial(RawJson.fullMaterial(projection.fullResult().bytes()));requireMaterial(bound,full,projection.fullResult());
        var support=support(recorded,bound);support.addAll(producers);support.addAll(projection.sourceClosure());support.add(full);
        HistorySource source=new HistorySource(projection.kind(),projection.logicalOperation(),data,originals.invocation(),
                recorded.original(),recorded.prepared(),NativeRequestChronology.PacketIdentity.of(recorded.acknowledgement(bound).outbound().orElseThrow().originalPacket()),
                full,projection.publicNumbers(),List.copyOf(support),List.copyOf(producers),projection.sourceClosure());
        RawHistoryRow row=new RawHistoryRow(nextIndex,source,object(projection.fullResult()));
        RawJson wire=RawJson.fullMaterial(row.encode());ExactRef rowRef=bound.preserveMaterial(wire);requireMaterial(bound,rowRef,wire);
        StrictJson.require(decode(full(bound,rowRef).bytes()).equals(row),"returned public-read row/source serde changed");
        Originals rechecked=issuer.requireOriginal(same,authority,bound,actual);requireHead(same,rechecked);
        StrictJson.require(rechecked.equals(originals),"returned public-read private invocation changed during retention");
        originals.live().requireOriginal(same,bound);requireFiles(union(List.copyOf(producers),projection.sourceClosure()));
        return new Candidate(issuer,actual,row,rowRef);
    }
    public static Candidate replay(Session same,OutcomeArchive bound,DriverStateAssembler authority,Source identical,
            RootReadContractCatalog catalog,Candidate candidate)throws IOException {
        Objects.requireNonNull(candidate);StrictJson.require(candidate.issuer==identical&&candidate.invocation.issuer()==identical,"returned public-read candidate crossed its actual private issuer");
        var originals=identical.requireOriginal(same,authority,bound,candidate.invocation);requireHead(same,originals);
        StrictJson.require(invocationData(originals).equals(candidate.source().original())&&originals.invocation().equals(candidate.source().invocation()),
                "returned read private candidate invocation DATA changed");
        originals.live().requireOriginal(same,bound);requireLive(originals,replayCollection(bound,catalog,candidate.source().collectionMetadata()),bound);
        replayOriginals(bound,catalog,identical,candidate.row());requireMaterial(bound,candidate.rowReference(),RawJson.fullMaterial(candidate.row().encode()));return candidate;
    }
    /** Historical DATA replay only; canonical event membership/ancestry belongs to the sole publisher caller. */
    public static RawHistoryRow replayOriginals(OutcomeArchive bound,RootReadContractCatalog catalog,Source identical,RawHistoryRow row)throws IOException {
        Objects.requireNonNull(row);identical.requireCatalog(catalog);StrictJson.require(identical.catalog()==catalog,"returned public-read cold catalog owner differs");
        var source=row.source();var recorded=replayCollection(bound,catalog,source.collectionMetadata());
        requireMaterial(bound,source.invocation(),invocationJson(source.original()));
        requireFrames(bound,recorded,source.original().frames(),null);
        var projection=identical.project(recorded,source.original(),bound);requireProjection(recorded,source.original(),projection);
        StrictJson.require(projection.kind()==source.kind()&&projection.logicalOperation().equals(source.logicalOperation())
                &&projection.publicNumbers().equals(source.publicNumbers())&&projection.sourceClosure().equals(source.projectionSources()),
                "returned public-read source-owned formatter/number roles changed");
        requireMaterial(bound,source.fullResult(),projection.fullResult());
        StrictJson.require(row.result().equals(object(projection.fullResult()))&&source.acknowledgement().equals(recorded.original())
                &&source.preparedRequest().equals(recorded.prepared())&&source.outbound().matches(recorded.acknowledgement(bound).outbound().orElseThrow().originalPacket()),
                "returned public-read result or original ACK/outbound custody changed");
        var required=support(recorded,bound);required.addAll(source.producerSources());required.addAll(source.projectionSources());required.add(source.fullResult());
        StrictJson.require(source.supportingEvidence().equals(List.copyOf(required))&&identical.sources().containsAll(source.original().producerSources()),
                "returned public-read complete source/original closure differs");
        requireFiles(union(source.producerSources(),source.projectionSources()));
        requireMaterial(bound,bound.materialReferenceOf(RawJson.fullMaterial(row.encode())),RawJson.fullMaterial(row.encode()));return row;
    }
    private static PlanningPublicReadCollection.Recorded replayCollection(OutcomeArchive bound,RootReadContractCatalog catalog,ExactRef reference) {
        RawJson raw=small(bound,reference);var recorded=PlanningPublicReadCollection.replay(catalog,bound,raw);
        StrictJson.require(Arrays.equals(PlanningPublicReadCollection.encode(recorded).bytes(),raw.bytes()),"actual collected negative-read metadata changed");
        return recorded;
    }
    private static void requireLive(Originals value,PlanningPublicReadCollection.Recorded recorded,OutcomeArchive bound) {
        StrictJson.require(value.recorded().equals(recorded)&&value.live().request().equals(recorded.request())
                &&value.live().before().equals(recorded.before())&&value.live().prepared().equals(bound.loadRequest(recorded.prepared()))
                &&value.live().acknowledgement().equals(recorded.acknowledgement(bound))
                &&value.live().contract().contractId().equals(recorded.contractId())
                &&value.headSequence()==recorded.headSequence()&&value.headDigest().equals(recorded.headDigest()),
                "live private negative-read token differs from its complete original recorded attempt");
    }
    private static void requireProjection(PlanningPublicReadCollection.Recorded recorded,InvocationData data,Projection projection) {
        Objects.requireNonNull(projection);Obj result=object(projection.fullResult());
        StrictJson.require(projection.logicalOperation().equals(recorded.request().operation())&&projection.originalCommand().equals(data.originalCommand()),
                "returned read report changed logical operation or encoded original command");
        requireReport(projection.kind(),projection.logicalOperation(),result);
        var request=recorded.request();var frame=request.before().frame();
        requireValue(result,"queried_snapshot_id",new Text(frame.snapshotId()));requireValue(result,"queried_revision",new IntegerValue(frame.revision()));
        requireValue(result,"queried_native_revision",new IntegerValue(frame.identity().nativeRevision()));
        requireValue(result,"queried_connection_generation",new IntegerValue(recorded.before().binding().connectionGeneration()));
        requireValue(result,"queried_episode_run_id",frame.episodeRunId()==null?Nil.INSTANCE:new Text(frame.episodeRunId()));
        projection.publicNumbers().toPublic(result);
    }
    /** Two finite original recording policies; raw metadata/ok flags cannot select another route. */
    public static void requireReport(Kind kind,OperationKey logical,Obj report) {
        requireLogical(kind,logical);requireValue(report,"step",new Text(logical.value()));
        StrictJson.require(!report.members().containsKey("error"),"normal returned public read cannot contain a thrown-error result");
        requireValue(report,"accepted",new Bool(false));requireValue(report,"backend_id",new Text("native-headless"));
        if(kind==Kind.HORIZON_UNAVAILABLE) {
            requireValue(report,"schema",new Text("xar.route-contact-readonly-unavailable.v1"));requireValue(report,"status",new Text("unavailable"));
            requireValue(report,"read_only",new Bool(true));requireValue(report,"available",new Bool(false));
            requireValue(report,"business_submission",new Bool(false));requireValue(report,"replay_allowed",new Bool(false));
            requireValue(report,"route_contact_horizon",Nil.INSTANCE);
        } else {
            requireValue(report,"status",new Text("deferred"));Obj preview=OpportunityJson.object(report.get("route_preview"),"actual deferred preview");
            requireValue(preview,"status",new Text("deferred"));requireValue(preview,"reason",new Text("army_not_move_ready"));
            var selected=WarHistorySteps.parsePreview(logical.value()).orElseThrow();
            requireValue(preview,"army_id",number(selected.armyId()));requireValue(preview,"target_province_id",number(selected.targetProvinceId()));
        }
    }
    public static void requireLogical(Kind kind,OperationKey operation) {
        Objects.requireNonNull(kind);Objects.requireNonNull(operation);
        if(kind==Kind.HORIZON_UNAVAILABLE) {
            var selected=RouteContactSteps.query(operation.value());
            StrictJson.require(RouteContactSteps.format(selected,RouteContactSteps.QUERY).equals(operation.value()),"original horizon operation must roundtrip its sole parser");
        } else {
            var selected=WarHistorySteps.parsePreview(operation.value()).orElseThrow(()->new IllegalArgumentException("only the original move-preview route is eligible"));
            StrictJson.require(NativeActionSteps.preview(selected.armyId(),selected.targetProvinceId()).equals(operation.value()),"original preview operation must roundtrip its owning parser/formatter");
        }
    }
    private static void requireFrames(OutcomeArchive bound,PlanningPublicReadCollection.Recorded recorded,FrameOriginals refs,Known live) {
        var basis=RootGuardEvidence.frameBasis(recorded.before().binding(),bound);
        StrictJson.require(basis.nativeFrame().equals(refs.nativeFrame())&&basis.driverFacts().equals(refs.driverFacts()),"returned read before frame differs from original guard basis");
        var before=frame(bound,refs.nativeFrame(),refs.driverFacts());var readback=frame(bound,refs.readbackNativeFrame(),refs.readbackDriverFacts());
        var request=recorded.request();var guard=recorded.before();
        StrictJson.require(before.identity().equals(request.before())&&before.source().equals(request.source())&&before.sessionId().equals(request.sessionId())
                &&before.connectionGeneration().equals(guard.binding().connectionGeneration())&&before.observedAt().equals(guard.binding().observedAt())
                &&before.fullBindingSha256().equals(guard.originalBindingSha256())
                &&before.identity().equals(readback.identity())&&before.source().equals(readback.source())&&before.sessionId().equals(readback.sessionId())
                &&before.connectionGeneration().equals(readback.connectionGeneration())
                &&before.fullBindingSha256().equals(readback.fullBindingSha256())
                &&before.semantic().equals(readback.semantic()),"returned read crossed its actual complete paused before/readback identity");
        StrictJson.require(OpportunityJson.bool(before.semantic().get("paused"),"actual paused map")
                &&OpportunityJson.bool(before.semantic().get("map_ready"),"actual ready map")
                &&OpportunityJson.bool(OpportunityJson.object(before.semantic().get("played_character"),"actual player").get("alive"),"actual living player"),
                "returned public read requires its original paused living map");
        RawJson manifest=full(bound,refs.driverFacts()),driver=full(bound,refs.beforeDriver());
        StrictJson.require(DriverObservationEvidenceReader.currentDriverReference(refs.driverFacts(),manifest).equals(refs.beforeDriver()),"returned read before Driver reference differs from actual manifest");
        var raw=DriverObservationEvidenceReader.nativeFrame(refs.driverFacts(),manifest,bound.loadNativeFrame(refs.nativeFrame()));
        var facts=DriverObservationEvidenceReader.decode(refs.driverFacts(),manifest,driver,raw);
        var knownWire=DriverSnapshotFacts.originalKnownJson(full(bound,refs.originalKnown()).bytes());
        var presence=DriverSnapshotFacts.observationOriginalReference(knownWire);
        StrictJson.require(presence.isEmpty()||presence.orElseThrow().equals(facts.semanticFactsEvidence()),"returned read Known has another actual observation manifest");
        Known known=DriverSnapshotFacts.decodeKnownOriginal(knownWire,presence.isPresent()?java.util.Optional.of(facts):java.util.Optional.empty());
        StrictJson.require(Arrays.equals(known.driver().encode(),driver.bytes())&&facts.driverVersion()==known.stamp().driverVersion()
                &&facts.episodeEpoch()==known.stamp().episodeEpoch()&&(live==null||Arrays.equals(live.driver().encode(),known.driver().encode())&&live.stamp().equals(known.stamp())),
                "returned read actual Known/Driver/facts custody differs");
    }
    private static DriverObservationAssembler.Complete frame(OutcomeArchive bound,ExactRef nativeRef,ExactRef factsRef) {
        RawJson manifest=full(bound,factsRef);var raw=DriverObservationEvidenceReader.nativeFrame(factsRef,manifest,bound.loadNativeFrame(nativeRef));
        var facts=DriverObservationEvidenceReader.decode(factsRef,manifest,full(bound,DriverObservationEvidenceReader.currentDriverReference(factsRef,manifest)),raw);
        var joined=new DriverObservationAssembler().assemble(raw,facts,nativeRef);
        StrictJson.require(joined instanceof DriverObservationAssembler.Complete,"actual complete rejected-read before/readback originals required");return (DriverObservationAssembler.Complete)joined;
    }
    private static LinkedHashSet<ExactRef> support(PlanningPublicReadCollection.Recorded value,OutcomeArchive bound) {
        var refs=new LinkedHashSet<ExactRef>();refs.addAll(List.of(value.arguments(),value.prepared(),value.original(),value.definitionSource(),value.decoderSource()));
        var prepared=bound.loadRequest(value.prepared());refs.addAll(prepared.preparationEvidence());
        refs.add(value.before().binding().nativeEvidence());refs.add(value.before().binding().capabilityEvidence());refs.addAll(value.before().binding().supportingEvidence());return refs;
    }
    private static void requireHead(Session same,Originals value)throws IOException {
        StrictJson.require(same.head().state().sequence()==value.headSequence()&&same.head().digest().equals(value.headDigest()),"returned read private invocation escaped its actual capture head");
    }
    public static InvocationData invocationData(Originals value){return new InvocationData(value.collectionMetadata(),value.originalCommand(),value.frames(),value.caller(),value.epochManifest(),value.headSequence(),value.headDigest(),value.producerSources());}
    public static RawJson invocationJson(InvocationData data){return RawJson.fullMaterial(DriverJson.encode(invocationBody(data)));}
    private static Obj invocationBody(InvocationData data) {
        return new Obj(java.util.Map.of("schema",new Text(INVOCATION_SCHEMA),"collection_metadata",ref(data.collectionMetadata()),
                "command",new Text(data.originalCommand().value()),"frames",framesJson(data.frames()),"caller",ref(data.caller()),
                "epoch_manifest",data.epochManifest().<Value>map(DriverReturnedPublicReadHistoryRowProducer::ref).orElse(Nil.INSTANCE),"head_sequence",new Text(Long.toString(data.headSequence())),"head_digest",new Text(data.headDigest()),
                "producer_sources",array(data.producerSources())));
    }
    public static InvocationData decodeInvocation(byte[] bytes) {
        Obj row=closed(bytes,Set.of("schema","collection_metadata","command","frames","caller","epoch_manifest","head_sequence","head_digest","producer_sources"));
        requireValue(row,"schema",new Text(INVOCATION_SCHEMA));
        return new InvocationData(reference(row.get("collection_metadata")),new OperationKey(string(row,"command")),decodeFrames(row.get("frames")),
                reference(row.get("caller")),optionalReference(row.get("epoch_manifest")),decimal(row,"head_sequence"),string(row,"head_digest"),readRefs(row.get("producer_sources"),1,256));
    }
    private static Obj framesJson(FrameOriginals value){return new Obj(java.util.Map.of("before_driver",ref(value.beforeDriver()),"original_known",ref(value.originalKnown()),
            "native_frame",ref(value.nativeFrame()),"driver_facts",ref(value.driverFacts()),"readback_native_frame",ref(value.readbackNativeFrame()),"readback_driver_facts",ref(value.readbackDriverFacts())));}
    private static FrameOriginals decodeFrames(Value raw) {
        Obj row=OpportunityJson.object(raw,"returned frame originals");
        StrictJson.require(row.members().keySet().equals(Set.of("before_driver","original_known","native_frame","driver_facts","readback_native_frame","readback_driver_facts")),"closed returned frame originals required");
        return new FrameOriginals(reference(row.get("before_driver")),reference(row.get("original_known")),reference(row.get("native_frame")),reference(row.get("driver_facts")),reference(row.get("readback_native_frame")),reference(row.get("readback_driver_facts")));
    }
    public static Obj sourceJson(HistorySource source) {
        var fields=new LinkedHashMap<String,Value>();fields.put("schema",new Text(SOURCE_SCHEMA));fields.put("kind",new Text(source.kind().name()));
        fields.put("logical_operation",new Text(source.logicalOperation().value()));fields.put("invocation_data",invocationBody(source.original()));
        fields.put("invocation",ref(source.invocation()));fields.put("acknowledgement",ref(source.acknowledgement()));fields.put("prepared_request",ref(source.preparedRequest()));
        fields.put("outbound_bytes",new Text(Long.toString(source.outbound().bytes())));fields.put("outbound_sha256",new Text(source.outbound().sha256()));
        fields.put("full_result",ref(source.fullResult()));fields.put("public_number_roles",source.publicNumbers().toJson());
        fields.put("supporting_evidence",array(source.supportingEvidence()));fields.put("producer_sources",array(source.producerSources()));fields.put("projection_sources",array(source.projectionSources()));return new Obj(fields);
    }
    public static HistorySource decodeSource(Value value) {
        Obj row=OpportunityJson.object(value,SOURCE_FIELD);
        StrictJson.require(row.members().keySet().equals(Set.of("schema","kind","logical_operation","invocation_data","invocation","acknowledgement","prepared_request",
                "outbound_bytes","outbound_sha256","full_result","public_number_roles","supporting_evidence","producer_sources","projection_sources")),"closed returned public-read source required");
        requireValue(row,"schema",new Text(SOURCE_SCHEMA));
        return new HistorySource(Kind.valueOf(string(row,"kind")),new OperationKey(string(row,"logical_operation")),
                decodeInvocation(DriverJson.encode(row.get("invocation_data"))),reference(row.get("invocation")),reference(row.get("acknowledgement")),
                reference(row.get("prepared_request")),new NativeRequestChronology.PacketIdentity(decimal(row,"outbound_bytes"),string(row,"outbound_sha256")),
                reference(row.get("full_result")),PublicNumbers.fromJson(row.get("public_number_roles")),readRefs(row.get("supporting_evidence"),1,768),readRefs(row.get("producer_sources"),1,256),readRefs(row.get("projection_sources"),1,260));
    }
    public static RawHistoryRow decode(byte[] bytes) {
        Obj row=closed(bytes,Set.of("index","command","ok","result",SOURCE_FIELD));HistorySource source=decodeSource(row.get(SOURCE_FIELD));
        RawHistoryRow result=new RawHistoryRow(integer(row,"index"),source,OpportunityJson.object(row.get("result"),"complete returned public-read result"));
        StrictJson.require(string(row,"command").equals(result.command())&&row.get("ok") instanceof Bool flag&&flag.value()==result.ok(),"returned public-read command/recorded-ok policy changed");return result;
    }
    public static PublicNumbers publicNumbersFromSource(Value value){return decodeSource(value).publicNumbers();}
    private static void requireFiles(List<ExactRef> values)throws IOException {for(var value:values){var witness=SharedSourceFiles.observe(Path.of(value.path()));StrictJson.require(witness.source().bytes()==value.bytes()&&witness.source().sha256().equals(value.sha256()),"actual returned-read producer source changed");SharedSourceFiles.assertUnchanged(witness);}}
    private static List<ExactRef> union(List<ExactRef> a,List<ExactRef> b){var refs=new LinkedHashSet<ExactRef>(a);refs.addAll(b);return List.copyOf(refs);}
    private static RawJson small(OutcomeArchive bound,ExactRef ref){RawJson raw=bound.loadMaterial(ref);requireBytes(ref,raw.bytes());return raw;}
    private static RawJson full(OutcomeArchive bound,ExactRef ref){RawJson raw=bound.loadFullMaterial(ref);requireBytes(ref,raw.bytes());StrictJson.require(bound.materialReferenceOf(raw).equals(ref),"full original archive role differs");return raw;}
    private static void requireMaterial(OutcomeArchive bound,ExactRef reference,RawJson expected){StrictJson.require(Arrays.equals(full(bound,reference).bytes(),expected.bytes()),"complete returned public-read material differs");}
    private static void requireBytes(ExactRef ref,byte[] bytes){StrictJson.require(ref.bytes()==bytes.length&&DriverJson.sha256(bytes).equals(ref.sha256()),"actual original bytes/SHA differ");}
    private static Obj object(RawJson raw){return DriverJson.object(raw.bytes(),DriverJson.MAX_NATIVE_BYTES);}
    private static Obj closed(byte[] raw,Set<String> fields){Obj row=DriverJson.object(raw,DriverJson.MAX_NATIVE_BYTES);var expected=new java.util.HashSet<>(fields);if(fields.contains("epoch_manifest")&&!row.members().containsKey("epoch_manifest"))expected.remove("epoch_manifest");StrictJson.require(row.members().keySet().equals(expected),"closed returned public-read JSON fields required");return row;}
    private static void requireValue(Obj object,String name,Value expected){StrictJson.require(expected.equals(object.get(name)),"returned public-read changed original "+name);}
    private static String string(Obj row,String field){return OpportunityJson.text(row.get(field),field);}
    private static long integer(Obj row,String field){return OpportunityJson.integer(row.get(field),field).longValueExact();}
    private static long decimal(Obj row,String field){String text=string(row,field);StrictJson.require(text.matches("0|[1-9][0-9]*"),"canonical decimal original field required");return new BigInteger(text).longValueExact();}
    private static ExactRef reference(Value value){return DriverObservationEvidenceReader.reference(value);}
    private static Optional<ExactRef> optionalReference(Value value){return value==null||value==Nil.INSTANCE?Optional.empty():Optional.of(reference(value));}
    private static Obj ref(ExactRef value){return DriverJson.object(StrictJson.canonical(value.toJson()),DriverJson.MAX_NATIVE_BYTES);}
    private static Arr array(List<ExactRef> values){return new Arr(values.stream().<Value>map(DriverReturnedPublicReadHistoryRowProducer::ref).toList());}
    private static List<ExactRef> readRefs(Value value,int min,int max){return references(OpportunityJson.array(value,"returned-read refs").stream().map(DriverReturnedPublicReadHistoryRowProducer::reference).toList(),min,max);}
    private static IntegerValue number(long value){return new IntegerValue(BigInteger.valueOf(value));}
}


