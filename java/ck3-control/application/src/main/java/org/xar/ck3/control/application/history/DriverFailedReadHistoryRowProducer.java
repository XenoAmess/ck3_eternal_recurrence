package org.xar.ck3.control.application.history;

import java.io.IOException;
import java.math.BigInteger;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.PlanningReadCoordinator.FailedReadAttempt;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual attempted Army-query failures. Error DATA has no result, after-frame or READ-only reuse authority. */
public final class DriverFailedReadHistoryRowProducer {
    public static final String SOURCE_FIELD="failed_read_history_source";
    public static final String SOURCE_SCHEMA="xar.driver-failed-read-history-source/v1";
    public static final String ATTEMPT_SCHEMA="xar.driver-failed-read-attempt/v2";
    public static final String STEP="query-army-strengths-v1";
    private DriverFailedReadHistoryRowProducer() { }
    public record Source(DriverReadHistoryFailureMaterial.Kind kind,String contractId,String requestId,
            ExactRef attempt,ExactRef beforeDriver,ExactRef driverFacts,ExactRef nativeFrame,
            List<ExactRef> componentReceipts,List<ExactRef> supportingEvidence,List<ExactRef> producerSources) {
        public Source {
            Objects.requireNonNull(kind);StrictJson.text(contractId);StrictJson.text(requestId);
            positive(attempt);positive(beforeDriver);positive(driverFacts);positive(nativeFrame);
            componentReceipts=refs(componentReceipts,0,1);supportingEvidence=refs(supportingEvidence,4,512);
            producerSources=refs(producerSources,1,64);
        }
        public List<ExactRef> evidence() {
            var all=new LinkedHashSet<ExactRef>(producerSources);all.add(attempt);all.add(beforeDriver);all.add(driverFacts);all.add(nativeFrame);
            all.addAll(componentReceipts);all.addAll(supportingEvidence);return List.copyOf(all);
        }
    }
    public record RawHistoryRow(long index,String command,boolean ok,String error,Source source) {
        public RawHistoryRow {
            StrictJson.safe(index,1);Objects.requireNonNull(source);StrictJson.text(error);
            StrictJson.require(STEP.equals(command)&&!ok&&error.length()<=8192,"finite original failed Army-query error row required");
        }
        public Obj toJson() {
            return new Obj(Map.of("index",new IntegerValue(BigInteger.valueOf(index)),"command",new Text(command),
                    "ok",new Bool(false),"error",new Text(error),SOURCE_FIELD,sourceJson(source)));
        }
        public byte[] encode(){return OpportunityJson.encode(ordered(toJson()));}
        public DriverStateSnapshot.HistoryEntry historyEntry(){return new DriverStateSnapshot.HistoryEntry(index,new DriverStateSnapshot.Value(encode()));}
    }
    /** A private live producer conclusion, never restored by a public JSON decoder. */
    public static final class Candidate {
        private final RawHistoryRow row;private final ExactRef reference;private final long headSequence;private final String headDigest;
        private Candidate(RawHistoryRow row,ExactRef reference,long sequence,String digest){this.row=row;this.reference=reference;headSequence=sequence;headDigest=digest;}
        public RawHistoryRow row(){return row;}public Source source(){return row.source();}
        public ExactRef rowReference(){return reference;}public DriverStateSnapshot.HistoryEntry historyEntry(){return row.historyEntry();}
        public long headSequence(){return headSequence;}public String headDigest(){return headDigest;}
    }
    public record OriginalWriterHead(long sequence,String digest) {
        public OriginalWriterHead {StrictJson.safe(sequence,0);StrictJson.require(digest!=null&&digest.matches("[0-9a-f]{64}"),"original failed writer head required");}
    }
    /** Original metadata DATA for the committed event consumer; the caller must verify canonical event membership. */
    public static OriginalWriterHead originalWriterHead(ActionPorts.OutcomeArchive bound,Source source) {
        Attempt attempt=loadAttempt(bound,source);return new OriginalWriterHead(attempt.headSequence(),attempt.headDigest());
    }
    private record Original(DriverObservationAssembler.Complete frame,DriverStateSnapshot.Complete driver,ExactRef driverReference) { }
    private record Attempt(PlanningReadRequest request,PlanningReadGuard before,String reason,ExactRef arguments,
            ExactRef prepared,ExactRef original,ExactRef definition,ExactRef decoder,ReadContract.PermissionMode permissionMode,
            ReadContract.WireProfile wireProfile,Optional<String> requiredCapability,long headSequence,String headDigest) { }

    public static Candidate prepare(Session same,ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,
            ReadContract<?> identical,PlanningReadRequest actualRequest,PlanningReadResult.Unavailable<?> actual,
            FailedReadAttempt token,Known actualBefore,List<? extends PlanningReadResult.Known<?>> actualEarlierComponents,
            long nextIndex,List<ExactRef> producerSources) throws IOException {
        Objects.requireNonNull(token);Objects.requireNonNull(actual);Objects.requireNonNull(same);StrictJson.safe(nextIndex,1);
        token.requireOriginal(same,identical,actualRequest,actual,bound);
        var installed=installed(catalog,identical.contractId());
        StrictJson.require(installed.contract()==identical,"failed history requires the identical installed contract");
        requireContract(identical,actualRequest);requirePrepared(identical,token.prepared());
        ExactRef facts=actualBefore.observation().orElseThrow().semanticFactsEvidence();
        ExactRef nativeRef=DriverObservationEvidenceReader.reference(actualBefore.auxiliary().get("capability_observed_native_source"));
        Original original=loadOriginal(bound,facts,nativeRef);
        StrictJson.require(Arrays.equals(original.driver().encode(),actualBefore.driver().encode()),"failed history changed its actual complete Driver predecessor");
        requireFrame(original,actualRequest,token.before());
        List<ExactRef> components=validateLiveComponents(bound,catalog,actualEarlierComponents,actualRequest);
        List<ExactRef> sources=refs(producerSources,1,64);
        StrictJson.require(token.originalRef().equals(bound.referenceOf(token.original()))&&token.original().equals(bound.load(token.originalRef()))
                &&token.preparedRef().equals(bound.requestReferenceOf(token.prepared()))&&token.prepared().equals(bound.loadRequest(token.preparedRef())),
                "failed read lost its actual archived prepared/outcome originals");
        bound.verifyReadAttemptOriginals(actualRequest,token.requestId(),token.before(),token.prepared(),token.original());
        String error=DriverReadHistoryFailureMaterial.unavailableError(actual);StrictJson.require(error.length()<=8192&&actual.reason().length()<=2048,"finite unavailable diagnostic required");
        List<ExactRef> retained=retainedSupport(bound,catalog,token.before(),token.prepared(),token.preparedRef(),token.originalRef(),
                identical.sourceRef(),installed.decoderSource(),components);
        StrictJson.require(retained.size()<512,"failed source closure must reserve its actual arguments artifact");
        // All qualification and fixed value validation precedes the first retention write.
        ExactRef args=bound.preserveMaterial(new RawJson(OpportunityJson.encode(ordered(actualRequest.arguments()))));
        Attempt attempt=new Attempt(actualRequest,token.before(),actual.reason(),args,token.preparedRef(),token.originalRef(),
                identical.sourceRef(),installed.decoderSource(),identical.permissionMode(),identical.wireProfile(),identical.requiredCapability(),token.headSequence(),token.headDigest());
        ExactRef attemptRef=bound.preserveMaterial(new RawJson(OpportunityJson.encode(ordered(attemptJson(attempt,identical.contractId(),token.requestId())))));
        Source source=new Source(DriverReadHistoryFailureMaterial.Kind.ARMY_STRENGTHS,identical.contractId(),token.requestId(),attemptRef,
                original.driverReference(),facts,nativeRef,components,support(bound,catalog,attempt,token.prepared(),components),sources);
        RawHistoryRow row=new RawHistoryRow(nextIndex,STEP,false,error,source);
        RawJson bytes=new RawJson(row.encode());ExactRef rowRef=bound.preserveMaterial(bytes);
        StrictJson.require(rowRef.equals(bound.materialReferenceOf(bytes))&&decode(bound.loadMaterial(rowRef).bytes()).equals(row),"failed original row/archive roundtrip changed");
        token.requireOriginal(same,identical,actualRequest,actual,bound);
        return new Candidate(row,rowRef,token.headSequence(),token.headDigest());
    }

    /** Read-only historical DATA replay. Canonical membership and a live private attempt are separate obligations. */
    public static RawHistoryRow replayOriginals(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,RawHistoryRow row) {
        Objects.requireNonNull(row);Source source=row.source();
        Attempt attempt=loadAttempt(bound,source);
        var installed=installed(catalog,source.contractId());ReadContract<?> contract=installed.contract();
        requireContract(contract,attempt.request());
        StrictJson.require(contract.sourceRef().equals(attempt.definition())&&installed.decoderSource().equals(attempt.decoder()),
                "failed original changed its installed definition/decoder source");
        Original original=loadOriginal(bound,source.driverFacts(),source.nativeFrame());
        StrictJson.require(original.driverReference().equals(source.beforeDriver()),"failed original Driver reference changed");
        requireFrame(original,attempt.request(),attempt.before());
        NativeRequest prepared=bound.loadRequest(attempt.prepared());requirePrepared(contract,prepared);
        StrictJson.require(attempt.permissionMode()==contract.permissionMode()&&attempt.wireProfile()==contract.wireProfile()
                &&attempt.requiredCapability().equals(contract.requiredCapability()),"failed original local permission/profile/capability binding changed");
        NativeActionPort.DispatchOutcome outcome=bound.load(attempt.original());
        StrictJson.require(bound.requestReferenceOf(prepared).equals(attempt.prepared())&&bound.referenceOf(outcome).equals(attempt.original())
                &&source.requestId().equals(outcome.requestId()),"failed original artifact references/request identity changed");
        bound.verifyReadAttemptOriginals(attempt.request(),source.requestId(),attempt.before(),prepared,outcome);
        List<ExactRef> components=validateComponents(bound,catalog,source.componentReceipts(),attempt.request());
        StrictJson.require(components.equals(source.componentReceipts())&&support(bound,catalog,attempt,prepared,components).equals(source.supportingEvidence()),
                "failed original supporting evidence/components changed");
        var unavailable=new PlanningReadResult.Unavailable<Object>(attempt.reason(),Optional.of(outcome));
        RawHistoryRow replayed=new RawHistoryRow(row.index(),STEP,false,DriverReadHistoryFailureMaterial.unavailableError(unavailable),source);
        StrictJson.require(replayed.equals(row),"error row differs from its original deterministic unavailable surface");return replayed;
    }
    public static Candidate replay(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,Candidate candidate) {
        Objects.requireNonNull(candidate);RawJson bytes=bound.loadMaterial(candidate.rowReference());requireBytes(candidate.rowReference(),bytes.bytes());
        RawHistoryRow retained=decode(bytes.bytes());StrictJson.require(retained.equals(candidate.row()),"retained private failed row changed");
        replayOriginals(bound,catalog,retained);Attempt attempt=loadAttempt(bound,retained.source());
        StrictJson.require(attempt.headSequence()==candidate.headSequence()&&attempt.headDigest().equals(candidate.headDigest()),"failed attempt writer predecessor changed");
        return candidate;
    }
    private static List<ExactRef> validateLiveComponents(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,
            List<? extends PlanningReadResult.Known<?>> earlier,PlanningReadRequest request) {
        earlier=List.copyOf(earlier);StrictJson.require(earlier.size()<=1,"at most one actual earlier Army comparison component required");
        var references=new ArrayList<ExactRef>();
        for(var known:earlier) {
            ExactRef reference=bound.readReferenceOf(known.receipt());
            StrictJson.require(reference.equals(known.originalReceipt())&&bound.loadRead(reference).equals(known.receipt()),"earlier successful component lost its original read receipt");
            references.add(reference);
        }
        return validateComponents(bound,catalog,references,request);
    }
    private static List<ExactRef> validateComponents(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,
            List<ExactRef> references,PlanningReadRequest request) {
        references=refs(references,0,1);
        for(ExactRef reference:references) {
            PlanningReadReceipt receipt=bound.loadRead(reference);ReadContract<?> contract=installed(catalog,receipt.contractId()).contract();
            requireContract(contract,receipt.request());
            StrictJson.require(bound.readReferenceOf(receipt).equals(reference)&&receipt.request().before().equals(request.before())
                    &&receipt.request().source().equals(request.source())&&receipt.request().sessionId().equals(request.sessionId()),
                    "earlier Army component changed its actual source/frame/session");
            contract.replay(receipt);
        }
        return references;
    }
    private static RootReadContractCatalog.InstalledRead installed(RootReadContractCatalog catalog,String id) {
        var matches=catalog.installed().stream().filter(item->item.contract().contractId().equals(id)).toList();
        StrictJson.require(matches.size()==1&&catalog.containsIdentity(matches.getFirst().contract()),"one actual installed failed-read definition required");
        return matches.getFirst();
    }
    private static void requireContract(ReadContract<?> contract,PlanningReadRequest request) {
        StrictJson.require(contract.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP&&contract.hasPureReplay()
                &&contract.wireProfile()==ReadContract.WireProfile.EXECUTE_STEP
                &&contract.originalHistoryKind().filter(kind->kind==DriverReadHistoryRichMaterial.Kind.ARMY_STRENGTHS).isPresent()
                &&contract.operation().equals(request.operation())&&STEP.equals(request.operation().value())
                &&request.origin() instanceof CommandOrigin.Gameplay,"finite actual Army failed-read contract required");
    }
    private static void requirePrepared(ReadContract<?> contract,NativeRequest prepared) {
        StrictJson.require(prepared.requiredCapability().equals(contract.requiredCapability())&&STEP.equals(prepared.step())
                &&contract.wireProfile()==ReadContract.WireProfile.EXECUTE_STEP,"actual prepared read changed its installed capability/profile/native step");
    }
    private static void requireFrame(Original original,PlanningReadRequest request,PlanningReadGuard guard) {
        var frame=original.frame();
        StrictJson.require(guard.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP&&guard.paused()&&guard.mapReady()&&guard.playerAlive()
                &&guard.binding().origin().equals(request.origin())&&guard.binding().source().equals(request.source())
                &&guard.binding().sessionId().equals(request.sessionId())&&frame.identity().equals(request.before())
                &&frame.source().equals(request.source())&&frame.sessionId().equals(request.sessionId())
                &&frame.connectionGeneration().equals(guard.binding().connectionGeneration()),"failed original crossed its actual held gameplay frame/source/transport");
    }
    private static Original loadOriginal(ActionPorts.OutcomeArchive bound,ExactRef factsRef,ExactRef nativeRef) {
        RawJson manifest=bound.loadFullMaterial(factsRef);requireBytes(factsRef,manifest.bytes());
        ExactRef driverRef=DriverObservationEvidenceReader.currentDriverReference(factsRef,manifest);
        RawJson driver=bound.loadFullMaterial(driverRef);requireBytes(driverRef,driver.bytes());
        byte[] nativeBytes=bound.loadNativeFrame(nativeRef);requireBytes(nativeRef,nativeBytes);
        var raw=DriverObservationEvidenceReader.nativeFrame(factsRef,manifest,nativeBytes);
        var facts=DriverObservationEvidenceReader.decode(factsRef,manifest,driver,raw);
        var assembled=new DriverObservationAssembler().assemble(raw,facts,nativeRef);
        StrictJson.require(assembled instanceof DriverObservationAssembler.Complete,"actual complete held Driver/native original required");
        return new Original((DriverObservationAssembler.Complete)assembled,facts.driver(),driverRef);
    }

    private static Obj attemptJson(Attempt value,String contractId,String requestId) {
        StrictJson.safe(value.headSequence(),0);StrictJson.require(value.headDigest().matches("[0-9a-f]{64}"),"actual failed attempt head digest required");
        StrictJson.text(value.reason());StrictJson.require(value.reason().length()<=2048,"finite original unavailable reason required");
        var fields=new LinkedHashMap<String,Value>();fields.put("schema",new Text(ATTEMPT_SCHEMA));
        fields.put("kind",new Text(DriverReadHistoryFailureMaterial.Kind.ARMY_STRENGTHS.name()));
        fields.put("contract_id",new Text(contractId));fields.put("request_id",new Text(requestId));
        fields.put("request",node(CommandOriginCodec.planningRequest(value.request(),value.arguments())));
        fields.put("guard",node(CommandOriginCodec.planningGuard(value.before())));fields.put("reason",new Text(value.reason()));
        fields.put("prepared_ref",refJson(value.prepared()));fields.put("original_ref",refJson(value.original()));
        fields.put("head_sequence",new Text(Long.toString(value.headSequence())));fields.put("head_digest",new Text(value.headDigest()));
        fields.put("definition_source",refJson(value.definition()));fields.put("decoder_source",refJson(value.decoder()));
        fields.put("permission_mode",new Text(value.permissionMode().name()));fields.put("wire_profile",new Text(value.wireProfile().name()));
        fields.put("required_capability",value.requiredCapability().<Value>map(Text::new).orElse(Nil.INSTANCE));return new Obj(fields);
    }
    private static Attempt loadAttempt(ActionPorts.OutcomeArchive bound,Source source) {
        RawJson material=bound.loadMaterial(source.attempt());requireBytes(source.attempt(),material.bytes());
        Obj body=DriverJson.object(material.bytes(),RawJson.MAXIMUM_BYTES);
        StrictJson.require(body.members().keySet().equals(Set.of("schema","kind","contract_id","request_id","request","guard","reason",
                "prepared_ref","original_ref","head_sequence","head_digest","definition_source","decoder_source","permission_mode","wire_profile","required_capability"))
                &&new Text(ATTEMPT_SCHEMA).equals(body.get("schema"))&&new Text(source.kind().name()).equals(body.get("kind"))
                &&new Text(source.contractId()).equals(body.get("contract_id"))&&new Text(source.requestId()).equals(body.get("request_id")),
                "exact original failed attempt metadata required");
        Obj requestBody=OpportunityJson.object(body.get("request"),"original failed request");
        ExactRef argsRef=reference(requestBody.get("arguments_ref"));RawJson args=bound.loadMaterial(argsRef);requireBytes(argsRef,args.bytes());
        PlanningReadRequest request=CommandOriginCodec.planningRequest(OpportunityJson.toNode(requestBody),DriverJson.object(args.bytes(),RawJson.MAXIMUM_BYTES));
        PlanningReadGuard guard=CommandOriginCodec.planningGuard(OpportunityJson.toNode(body.get("guard")));
        String sequence=OpportunityJson.text(body.get("head_sequence"),"original head sequence");
        StrictJson.require(sequence.matches("0|[1-9][0-9]*"),"canonical original head sequence required");
        Attempt attempt=new Attempt(request,guard,OpportunityJson.text(body.get("reason"),"original unavailable reason"),argsRef,
                reference(body.get("prepared_ref")),reference(body.get("original_ref")),reference(body.get("definition_source")),
                reference(body.get("decoder_source")),ReadContract.PermissionMode.valueOf(OpportunityJson.text(body.get("permission_mode"),"original permission mode")),
                ReadContract.WireProfile.valueOf(OpportunityJson.text(body.get("wire_profile"),"original wire profile")),
                body.get("required_capability")==Nil.INSTANCE?Optional.empty():Optional.of(OpportunityJson.text(body.get("required_capability"),"original required capability")),new BigInteger(sequence).longValueExact(),OpportunityJson.text(body.get("head_digest"),"original head digest"));
        StrictJson.require(attemptJson(attempt,source.contractId(),source.requestId()).equals(body),"failed attempt metadata differs after sole-codec JSON roundtrip");
        return attempt;
    }
    private static List<ExactRef> support(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,
            Attempt value,NativeRequest prepared,List<ExactRef> components) {
        var refs=new LinkedHashSet<ExactRef>();refs.add(value.arguments());
        refs.addAll(retainedSupport(bound,catalog,value.before(),prepared,value.prepared(),value.original(),value.definition(),value.decoder(),components));
        return refs(List.copyOf(refs),4,512);
    }
    private static List<ExactRef> retainedSupport(ActionPorts.OutcomeArchive bound,RootReadContractCatalog catalog,PlanningReadGuard before,
            NativeRequest prepared,ExactRef preparedRef,ExactRef originalRef,ExactRef definition,ExactRef decoder,List<ExactRef> components) {
        var refs=new LinkedHashSet<ExactRef>();refs.add(preparedRef);refs.add(originalRef);refs.add(definition);refs.add(decoder);
        refs.addAll(prepared.preparationEvidence());addGuard(refs,before);
        for(ExactRef component:components) {
            PlanningReadReceipt read=bound.loadRead(component);var installed=installed(catalog,read.contractId());
            refs.add(component);refs.add(installed.contract().sourceRef());refs.add(installed.decoderSource());
            ExactRef outcome=bound.referenceOf(read.original());StrictJson.require(bound.load(outcome).equals(read.original()),"earlier component original outcome changed");
            refs.add(outcome);addGuard(refs,read.before());addGuard(refs,read.after());
        }
        return refs(List.copyOf(refs),3,511);
    }
    private static void addGuard(LinkedHashSet<ExactRef> refs,PlanningReadGuard guard) {
        refs.add(guard.binding().nativeEvidence());refs.add(guard.binding().capabilityEvidence());refs.addAll(guard.binding().supportingEvidence());
    }
    private static Obj sourceJson(Source source) {
        var fields=new LinkedHashMap<String,Value>();fields.put("schema",new Text(SOURCE_SCHEMA));fields.put("kind",new Text(source.kind().name()));
        fields.put("contract_id",new Text(source.contractId()));fields.put("request_id",new Text(source.requestId()));
        fields.put("attempt",refJson(source.attempt()));fields.put("before_driver",refJson(source.beforeDriver()));
        fields.put("driver_facts",refJson(source.driverFacts()));fields.put("native_frame",refJson(source.nativeFrame()));
        fields.put("component_receipts",arrayRefs(source.componentReceipts()));fields.put("supporting_evidence",arrayRefs(source.supportingEvidence()));
        fields.put("producer_sources",arrayRefs(source.producerSources()));return new Obj(fields);
    }

    /** Strict source DATA parser only. This cannot construct Candidate, FailedReadAttempt, Known or a writer permission. */
    public static RawHistoryRow decode(byte[] bytes) {
        Obj row=DriverJson.object(bytes,RawJson.MAXIMUM_BYTES);
        StrictJson.require(row.members().keySet().equals(Set.of("index","command","ok","error",SOURCE_FIELD)),"exact error history row without result required");
        Obj source=OpportunityJson.object(row.get(SOURCE_FIELD),"failed read history source");
        StrictJson.require(source.members().keySet().equals(Set.of("schema","kind","contract_id","request_id","attempt","before_driver","driver_facts",
                "native_frame","component_receipts","supporting_evidence","producer_sources"))&&new Text(SOURCE_SCHEMA).equals(source.get("schema")),
                "exact failed read history source schema required");
        Source original=new Source(DriverReadHistoryFailureMaterial.Kind.valueOf(OpportunityJson.text(source.get("kind"),"finite failed kind")),
                OpportunityJson.text(source.get("contract_id"),"failed contract id"),OpportunityJson.text(source.get("request_id"),"failed request id"),
                reference(source.get("attempt")),reference(source.get("before_driver")),reference(source.get("driver_facts")),reference(source.get("native_frame")),
                parseRefs(source.get("component_receipts")),parseRefs(source.get("supporting_evidence")),parseRefs(source.get("producer_sources")));
        return new RawHistoryRow(OpportunityJson.integer(row.get("index"),"error history index").longValueExact(),OpportunityJson.text(row.get("command"),"error command"),
                OpportunityJson.bool(row.get("ok"),"error ok"),OpportunityJson.text(row.get("error"),"original error"),original);
    }
    private static void positive(ExactRef ref){Objects.requireNonNull(ref);StrictJson.require(ref.bytes()>0,"positive original artifact/source required");}
    private static List<ExactRef> refs(List<ExactRef> values,int min,int max) {
        values=List.copyOf(values);StrictJson.require(values.size()>=min&&values.size()<=max&&new LinkedHashSet<>(values).size()==values.size(),"finite unique original reference list required");
        values.forEach(DriverFailedReadHistoryRowProducer::positive);return values;
    }
    private static Arr arrayRefs(List<ExactRef> values){return new Arr(values.stream().<Value>map(DriverFailedReadHistoryRowProducer::refJson).toList());}
    private static List<ExactRef> parseRefs(Value value){return OpportunityJson.array(value,"original references").stream().map(DriverFailedReadHistoryRowProducer::reference).toList();}
    private static Obj refJson(ExactRef value){return node(value.toJson());}
    private static Obj node(com.fasterxml.jackson.databind.JsonNode value){return DriverJson.object(StrictJson.canonical(value),RawJson.MAXIMUM_BYTES);}
    private static ExactRef reference(Value value){return DriverObservationEvidenceReader.reference(value);}
    private static void requireBytes(ExactRef ref,byte[] bytes){StrictJson.require(ref.bytes()==bytes.length&&ref.sha256().equals(DriverJson.sha256(bytes)),"original whole bytes/SHA changed");}
    private static Value ordered(Value value) {
        if(value instanceof Obj object) {
            var sorted=new TreeMap<String,Value>(object.members());var fields=new LinkedHashMap<String,Value>();
            sorted.forEach((key,item)->fields.put(key,ordered(item)));return new Obj(fields);
        }
        if(value instanceof Arr array)return new Arr(array.items().stream().map(DriverFailedReadHistoryRowProducer::ordered).toList());return value;
    }
}
