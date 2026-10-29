package org.xar.ck3.control.contracts.evidence;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.contracts.evidence.PortableEvidence.*;

/** Exact manifest/public wire codec. No file access, registry copy or native authority. */
public final class PortableEvidenceJson {
    public static final int MANIFEST_LIMIT=2*1024*1024;
    private static final ObjectMapper MANIFEST_JSON=new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(64).maxStringLength(MANIFEST_LIMIT).maxNumberLength(1000).build()).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS).enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private PortableEvidenceJson() { }
    public static Manifest manifest(byte[] bytes,String datasetSha256) {
        ObjectNode root=StrictJson.object(manifestDocument(bytes),Set.of("ck3_build","ck3_exe_sha256","compression","evidence","schema","schema_version","statistics"));
        StrictJson.require(text(root,"schema").equals("xar.ck3.vanilla-event-portable-evidence-manifest")&&number(root,"schema_version",1,1)==1
                &&text(root,"ck3_build").equals(BUILD)&&text(root,"ck3_exe_sha256").equals(EXE_SHA256),"frozen portable manifest identity mismatch");
        ObjectNode compression=StrictJson.object(root.get("compression"),Set.of("algorithm","filename","mtime"));
        StrictJson.require(text(compression,"algorithm").equals("gzip")&&compression.get("filename").isTextual()&&compression.get("filename").textValue().isEmpty()
                &&number(compression,"mtime",0,0)==0,"deterministic gzip contract required");
        JsonNode evidence=root.get("evidence");StrictJson.require(evidence.isArray()&&evidence.size()<=10000,"bounded portable evidence array required");
        var blobs=new ArrayList<Blob>();String previous=null;long definition=0,lexical=0,analysis=0,observations=0,captured=0,refs=0,sources=0;
        for(JsonNode item:evidence){
            ObjectNode row=StrictJson.object(item,Set.of("blob_bytes","blob_path","blob_sha256","bytes","evidence_id","kind","media_type","references","sha256"));
            var id=new EvidenceId(text(row,"evidence_id"));StrictJson.require(id.value().equals(text(row,"sha256"))&&(previous==null||previous.compareTo(id.value())<0),"strict sorted distinct content ids required");previous=id.value();
            Kind kind=Kind.parse(text(row,"kind"));Media media=Media.parse(text(row,"media_type"));JsonNode raw=row.get("references");
            StrictJson.require(raw.isArray()&&!raw.isEmpty()&&raw.size()<=100000,"bounded nonempty evidence references required");
            var references=new ArrayList<Reference>();Reference prior=null;var seen=new HashSet<Reference>();
            for(JsonNode value:raw){Reference reference=reference(value);
                StrictJson.require(seen.add(reference)&&(prior==null||compare(prior,reference)<=0),"canonical ordered distinct references required");prior=reference;
                StrictJson.require(reference.origin()==(kind==Kind.SOURCE_DEFINITION?Origin.CK3_GAME:Origin.RUNTIME)&&media(reference.logicalPath())==media,"kind/origin/path/media mismatch");references.add(reference);refs++;
                switch(reference.provenance()){case DEFINITION->definition++;case LEXICAL_CANDIDATE->lexical++;case ANALYSIS->analysis++;case CAPTURED->captured++;}
            }
            if(kind==Kind.SOURCE_DEFINITION)sources++;else observations++;
            var blob=new Blob(new Metadata(id,kind,media,number(row,"bytes",0,StrictJson.MAX_SAFE_INTEGER),references),number(row,"blob_bytes",1,StrictJson.MAX_SAFE_INTEGER),text(row,"blob_sha256"));
            StrictJson.require(blob.blobPath().equals(text(row,"blob_path")),"content-addressed blob path mismatch");blobs.add(blob);
        }
        var actual=new Statistics(blobs.size(),definition,lexical,analysis,observations,captured,refs,sources);
        StrictJson.require(statistics(root.get("statistics")).equals(actual),"portable evidence statistics mismatch");return new Manifest(datasetSha256,blobs,actual);
    }
    /** Only this frozen manifest role owns 2 MiB. The generic StrictJson limits are unchanged. */
    private static JsonNode manifestDocument(byte[] bytes){
        StrictJson.require(bytes!=null&&bytes.length>0&&bytes.length<=MANIFEST_LIMIT,"bounded portable manifest bytes required");
        try{String text=StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString();
            JsonNode value=MANIFEST_JSON.readTree(text);StrictJson.require(value!=null,"portable manifest object required");return value;
        }catch(IOException failure){throw new IllegalArgumentException("invalid portable manifest JSON",failure);}
    }
    private static Statistics statistics(JsonNode input){ObjectNode row=StrictJson.object(input,Set.of("evidence","generated_definition_references","lexical_caller_candidate_references","manually_reviewed_analysis_source_references","observation_artifacts","observation_artifact_references","references","source_definitions"));
        return new Statistics(count(row,"evidence"),count(row,"generated_definition_references"),count(row,"lexical_caller_candidate_references"),count(row,"manually_reviewed_analysis_source_references"),count(row,"observation_artifacts"),count(row,"observation_artifact_references"),count(row,"references"),count(row,"source_definitions"));}
    private static Reference reference(JsonNode input){ObjectNode row=StrictJson.object(input,Set.of("caller_candidate_resolution","event_definition_key","logical_path","origin","provenance","role","source_column","source_line"));
        return new Reference(text(row,"event_definition_key"),text(row,"logical_path"),Origin.parse(text(row,"origin")),Provenance.parse(text(row,"provenance")),text(row,"role"),nullableNumber(row,"source_line"),nullableNumber(row,"source_column"),row.get("caller_candidate_resolution").isNull()?Optional.empty():Optional.of(Resolution.parse(text(row,"caller_candidate_resolution"))));}
    private static Media media(String path){int dot=path.lastIndexOf('.');String extension=dot<0?"":path.substring(dot).toLowerCase(Locale.ROOT);return switch(extension){case ".json"->Media.JSON;case ".yml",".yaml"->Media.YAML;case ".png"->Media.PNG;case ".txt",".gui",".asset",".info"->Media.TEXT;default->throw new IllegalArgumentException("unsupported evidence extension");};}
    private static int compare(Reference left,Reference right){
        for(var pair:List.of(List.of(left.eventDefinitionKey(),right.eventDefinitionKey()),List.of(left.origin().wire(),right.origin().wire()),List.of(left.provenance().wire(),right.provenance().wire()),List.of(left.role(),right.role()),List.of(left.logicalPath(),right.logicalPath()))){int value=unicode(pair.get(0),pair.get(1));if(value!=0)return value;}
        int value=Long.compare(left.sourceLine().orElse(0L),right.sourceLine().orElse(0L));return value!=0?value:Long.compare(left.sourceColumn().orElse(0L),right.sourceColumn().orElse(0L));}
    private static int unicode(String left,String right){var l=left.codePoints().iterator();var r=right.codePoints().iterator();while(l.hasNext()&&r.hasNext()){int value=Integer.compare(l.nextInt(),r.nextInt());if(value!=0)return value;}return Boolean.compare(l.hasNext(),r.hasNext());}

    public static ListCall listCall(JsonNode input){ObjectNode row=arguments(input,Set.of("event_definition_key","kind","after_evidence_id","limit","ck3_build"));
        JsonNode event=row.get("event_definition_key"),kind=row.get("kind"),cursor=row.get("after_evidence_id"),limit=row.has("limit")?row.get("limit"):StrictJson.object().put("v",50).get("v"),build=row.get("ck3_build");
        Optional<Kind> normalizedKind=Optional.empty();if(kind!=null&&kind.isTextual())try{normalizedKind=Optional.of(Kind.parse(kind.textValue()));}catch(IllegalArgumentException invalid){/* normalized null */}
        Optional<String> normalizedCursor=string(cursor).filter(value->value.matches("[a-f0-9]{64}"));Optional<Integer> normalizedLimit=integer(limit,1,100).map(Long::intValue);
        var parameters=new ListParameters(string(event),normalizedKind,normalizedCursor,normalizedLimit);
        if(build!=null&&(!build.isTextual()||!build.textValue().equals(BUILD)))return new ListRejected(parameters,Failure.UNSUPPORTED_BUILD,Parameter.BUILD);
        if(event!=null&&!event.isNull()&&(!event.isTextual()||event.textValue().strip().isEmpty()))return new ListRejected(parameters,Failure.INVALID_EVENT,Parameter.EVENT);
        if(kind!=null&&!kind.isNull()&&normalizedKind.isEmpty())return new ListRejected(parameters,Failure.INVALID_KIND,Parameter.KIND);
        if(cursor!=null&&!cursor.isNull()&&normalizedCursor.isEmpty())return new ListRejected(parameters,Failure.INVALID_CURSOR,Parameter.CURSOR);
        if(normalizedLimit.isEmpty())return new ListRejected(parameters,Failure.INVALID_LIMIT,Parameter.LIMIT);return new ListQuery(parameters);}
    public static ReadCall readCall(JsonNode input){ObjectNode row=arguments(input,Set.of("evidence_id","offset","max_bytes","ck3_build"));
        JsonNode id=row.get("evidence_id"),offset=row.has("offset")?row.get("offset"):StrictJson.object().put("v",0).get("v"),maximum=row.has("max_bytes")?row.get("max_bytes"):StrictJson.object().put("v",MAX_READ_BYTES).get("v"),build=row.get("ck3_build");
        var parameters=new ReadParameters(string(id),integer(offset,0,StrictJson.MAX_SAFE_INTEGER));
        if(build!=null&&(!build.isTextual()||!build.textValue().equals(BUILD)))return new ReadRejected(parameters,Failure.UNSUPPORTED_BUILD);
        if(id==null||!id.isTextual()||!id.textValue().matches("[a-f0-9]{64}"))return new ReadRejected(parameters,Failure.INVALID_ID);
        if(parameters.offset().isEmpty())return new ReadRejected(parameters,Failure.INVALID_OFFSET);
        var max=integer(maximum,1,MAX_READ_BYTES);if(max.isEmpty())return new ReadRejected(parameters,Failure.INVALID_MAX);
        return new ReadQuery(parameters,new EvidenceId(id.textValue()),parameters.offset().orElseThrow(),max.orElseThrow().intValue());}
    private static ObjectNode arguments(JsonNode input,Set<String> allowed){StrictJson.require(input instanceof ObjectNode,"arguments object required");ObjectNode row=(ObjectNode)input;row.fieldNames().forEachRemaining(field->StrictJson.require(allowed.contains(field),"unknown portable evidence argument"));return row;}
    private static Optional<String> string(JsonNode node){return node!=null&&node.isTextual()?Optional.of(node.textValue()):Optional.empty();}
    private static Optional<Long> integer(JsonNode node,long minimum,long maximum){return node!=null&&node.isIntegralNumber()&&node.bigIntegerValue().compareTo(java.math.BigInteger.valueOf(minimum))>=0&&node.bigIntegerValue().compareTo(java.math.BigInteger.valueOf(maximum))<=0?Optional.of(node.longValue()):Optional.empty();}

    public static ObjectNode listResult(ListResult result){ObjectNode row=base("xar.ck3.vanilla-event-evidence-list",result.failure());ListParameters query=result.parameters();
        nullable(row,"event_definition_key",query.eventDefinitionKey());nullable(row,"kind",query.kind().map(Kind::wire));nullable(row,"after_evidence_id",query.afterEvidenceId());
        if(query.limit().isPresent())row.put("limit",query.limit().orElseThrow());else row.putNull("limit");nullable(row,"dataset_sha256",result.datasetSha256());row.put("total_matches",result.totalMatches());
        var items=row.putArray("evidence");result.evidence().forEach(value->items.add(metadata(value)));nullable(row,"next_after_evidence_id",result.nextAfterEvidenceId());nullable(row,"invalid_parameter",result.invalidParameter().map(Parameter::wire));return row;}
    public static ObjectNode readResult(ReadResult result){ObjectNode row=base("xar.ck3.vanilla-event-evidence-read",result.failure());nullable(row,"evidence_id",result.parameters().evidenceId());
        if(result.parameters().offset().isPresent())row.put("offset",result.parameters().offset().orElseThrow());else row.putNull("offset");
        if(result.metadata().isPresent()){Metadata value=result.metadata().orElseThrow();row.put("sha256",value.evidenceId().value()).put("kind",value.kind().wire()).put("media_type",value.mediaType().wire()).put("historical_artifact_may_contain_nonportable_locators",value.kind()==Kind.OBSERVATION_ARTIFACT).put("total_bytes",value.bytes());}
        else for(String field:List.of("sha256","kind","media_type","historical_artifact_may_contain_nonportable_locators","total_bytes"))row.putNull(field);
        if(result.content().isPresent()){Content value=result.content().orElseThrow();row.put("content_bytes",value.bytes()).put("content_base64",value.base64()).put("eof",value.eof());}
        else for(String field:List.of("content_bytes","content_base64","eof"))row.putNull(field);return row;}
    private static ObjectNode base(String schema,Optional<Failure> failure){ObjectNode row=StrictJson.object().put("schema",schema).put("schema_version",1).put("status",failure.isEmpty()?"available":"unavailable").put("ck3_build",BUILD).put("ck3_exe_sha256",EXE_SHA256);nullable(row,"unavailable_reason",failure.map(Failure::wire));return row;}
    private static ObjectNode metadata(Metadata value){ObjectNode row=StrictJson.object().put("evidence_id",value.evidenceId().value()).put("sha256",value.evidenceId().value()).put("kind",value.kind().wire()).put("media_type",value.mediaType().wire()).put("bytes",value.bytes());var refs=row.putArray("references");value.references().forEach(reference->refs.add(reference(reference)));return row;}
    private static ObjectNode reference(Reference value){ObjectNode row=StrictJson.object().put("event_definition_key",value.eventDefinitionKey()).put("logical_path",value.logicalPath()).put("origin",value.origin().wire()).put("provenance",value.provenance().wire()).put("role",value.role());
        if(value.sourceLine().isPresent())row.put("source_line",value.sourceLine().orElseThrow());else row.putNull("source_line");if(value.sourceColumn().isPresent())row.put("source_column",value.sourceColumn().orElseThrow());else row.putNull("source_column");nullable(row,"caller_candidate_resolution",value.callerCandidateResolution().map(Resolution::wire));return row;}
    private static void nullable(ObjectNode row,String field,Optional<String> value){if(value.isPresent())row.put(field,value.orElseThrow());else row.putNull(field);}
    private static String text(ObjectNode row,String field){return StrictJson.text(row.get(field));}
    private static long number(ObjectNode row,String field,long minimum,long maximum){return StrictJson.integer(row.get(field),minimum,maximum);}
    private static long count(ObjectNode row,String field){return number(row,field,0,StrictJson.MAX_SAFE_INTEGER);}
    private static Optional<Long> nullableNumber(ObjectNode row,String field){return row.get(field).isNull()?Optional.empty():Optional.of(number(row,field,1,StrictJson.MAX_SAFE_INTEGER));}
}
