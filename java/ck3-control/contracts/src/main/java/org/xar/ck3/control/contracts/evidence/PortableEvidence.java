package org.xar.ck3.control.contracts.evidence;

import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;

/** Shared frozen portable DATA contract; historical source/caller evidence grants no native authority. */
public final class PortableEvidence {
    public static final String BUILD="1.19.0.6";
    public static final String EXE_SHA256="2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
    public static final int MAX_READ_BYTES=65536;
    private PortableEvidence() { }
    public enum Kind {
        SOURCE_DEFINITION("source_definition"), OBSERVATION_ARTIFACT("observation_artifact");
        private final String wire; Kind(String wire){this.wire=wire;} public String wire(){return wire;}
        public static Kind parse(String value){for(var kind:values())if(kind.wire.equals(value))return kind;throw new IllegalArgumentException("invalid evidence kind");}
    }
    public enum Origin { CK3_GAME("ck3_game"),RUNTIME("runtime");
        private final String wire; Origin(String wire){this.wire=wire;} public String wire(){return wire;}
        public static Origin parse(String value){for(var origin:values())if(origin.wire.equals(value))return origin;throw new IllegalArgumentException("invalid origin");}
    }
    public enum Provenance {
        CAPTURED("captured-observation-artifact"),DEFINITION("generated-definition-index"),
        LEXICAL_CANDIDATE("lexical-caller-candidate-not-proven-runtime-caller"),ANALYSIS("manually-reviewed-analysis-source");
        private final String wire; Provenance(String wire){this.wire=wire;} public String wire(){return wire;}
        public static Provenance parse(String value){for(var provenance:values())if(provenance.wire.equals(value))return provenance;throw new IllegalArgumentException("invalid provenance");}
    }
    public enum Resolution { EXTERNAL("external-definition-file"),SAME_FILE("same-definition-file-only");
        private final String wire; Resolution(String wire){this.wire=wire;} public String wire(){return wire;}
        public static Resolution parse(String value){for(var resolution:values())if(resolution.wire.equals(value))return resolution;throw new IllegalArgumentException("invalid resolution");}
    }
    public enum Media {
        JSON("application/json"),YAML("application/yaml; charset=utf-8"),PNG("image/png"),TEXT("text/plain; charset=utf-8");
        private final String wire; Media(String wire){this.wire=wire;} public String wire(){return wire;}
        public static Media parse(String value){for(var media:values())if(media.wire.equals(value))return media;throw new IllegalArgumentException("unsupported media");}
    }
    public enum Failure {
        UNSUPPORTED_BUILD("unsupported_ck3_build"),INVALID_EVENT("invalid_event_definition_key"),INVALID_KIND("invalid_evidence_kind"),
        INVALID_CURSOR("invalid_cursor"),INVALID_LIMIT("invalid_limit"),INTEGRITY("bundle_integrity_error"),EVENT_NOT_INDEXED("event_definition_key_not_indexed"),
        INVALID_ID("invalid_evidence_id"),INVALID_OFFSET("invalid_offset"),INVALID_MAX("invalid_max_bytes"),ID_NOT_INDEXED("evidence_id_not_indexed"),OFFSET_RANGE("offset_out_of_range");
        private final String wire; Failure(String wire){this.wire=wire;} public String wire(){return wire;}
    }
    public enum Parameter { BUILD("ck3_build"),EVENT("event_definition_key"),KIND("kind"),CURSOR("after_evidence_id"),LIMIT("limit");
        private final String wire; Parameter(String wire){this.wire=wire;} public String wire(){return wire;}
    }
    public record EvidenceId(String value) {
        public EvidenceId { StrictJson.require(value!=null&&value.matches("[a-f0-9]{64}"),"canonical lower-case content SHA required"); }
    }
    public record Reference(String eventDefinitionKey,String logicalPath,Origin origin,Provenance provenance,String role,
            Optional<Long> sourceLine,Optional<Long> sourceColumn,Optional<Resolution> callerCandidateResolution) {
        public Reference {
            StrictJson.text(eventDefinitionKey);StrictJson.text(logicalPath);StrictJson.text(role);Objects.requireNonNull(origin);Objects.requireNonNull(provenance);
            sourceLine=Objects.requireNonNull(sourceLine);sourceColumn=Objects.requireNonNull(sourceColumn);callerCandidateResolution=Objects.requireNonNull(callerCandidateResolution);
            StrictJson.require(!logicalPath.startsWith("/")&&!List.of(logicalPath.split("/",-1)).contains(".."),"unsafe logical evidence path");
            sourceLine.ifPresent(value->StrictJson.safe(value,1));sourceColumn.ifPresent(value->StrictJson.safe(value,1));
            boolean shape=switch(provenance){
                case CAPTURED -> origin==Origin.RUNTIME&&sourceLine.isEmpty()&&sourceColumn.isEmpty()&&callerCandidateResolution.isEmpty();
                case DEFINITION -> origin==Origin.CK3_GAME&&role.equals("event_definition")&&sourceLine.isPresent()&&sourceColumn.isEmpty()&&callerCandidateResolution.isEmpty();
                case LEXICAL_CANDIDATE -> origin==Origin.CK3_GAME&&role.equals("caller_candidate")&&sourceLine.isPresent()&&sourceColumn.isPresent()&&callerCandidateResolution.isPresent();
                case ANALYSIS -> origin==Origin.CK3_GAME&&role.equals("analysis_source")&&sourceLine.isEmpty()&&sourceColumn.isEmpty()&&callerCandidateResolution.isEmpty();};
            StrictJson.require(shape,"source provenance shape differs from frozen bundle");
        }
    }
    public record Metadata(EvidenceId evidenceId,Kind kind,Media mediaType,long bytes,List<Reference> references) {
        public Metadata {Objects.requireNonNull(evidenceId);Objects.requireNonNull(kind);Objects.requireNonNull(mediaType);StrictJson.safe(bytes,0);references=List.copyOf(references);StrictJson.require(!references.isEmpty(),"portable evidence references required");}
    }
    public record Blob(Metadata metadata,long blobBytes,String blobSha256) {
        public Blob {Objects.requireNonNull(metadata);StrictJson.safe(blobBytes,1);new EvidenceId(blobSha256);}
        public String blobPath(){return "blobs/"+metadata.evidenceId().value()+".gz";}
    }
    public record Statistics(long evidence,long generatedDefinitionReferences,long lexicalCallerCandidateReferences,long manuallyReviewedAnalysisSourceReferences,
            long observationArtifacts,long observationArtifactReferences,long references,long sourceDefinitions) {
        public Statistics {for(long value:new long[]{evidence,generatedDefinitionReferences,lexicalCallerCandidateReferences,manuallyReviewedAnalysisSourceReferences,observationArtifacts,observationArtifactReferences,references,sourceDefinitions})StrictJson.safe(value,0);}
    }
    public record Manifest(String datasetSha256,List<Blob> evidence,Statistics statistics) {
        public Manifest {StrictJson.require(datasetSha256!=null&&datasetSha256.matches("[A-F0-9]{64}"),"upper-case raw manifest dataset SHA required");evidence=List.copyOf(evidence);Objects.requireNonNull(statistics);}
    }
    public record ListParameters(Optional<String> eventDefinitionKey,Optional<Kind> kind,Optional<String> afterEvidenceId,Optional<Integer> limit) {
        public ListParameters {eventDefinitionKey=Objects.requireNonNull(eventDefinitionKey);kind=Objects.requireNonNull(kind);afterEvidenceId=Objects.requireNonNull(afterEvidenceId);limit=Objects.requireNonNull(limit);}
    }
    public sealed interface ListCall permits ListQuery,ListRejected {ListParameters parameters();}
    public record ListQuery(ListParameters parameters) implements ListCall {
        public ListQuery {Objects.requireNonNull(parameters);StrictJson.require(parameters.limit().filter(value->value>=1&&value<=100).isPresent(),"valid list limit required");
            parameters.eventDefinitionKey().ifPresent(value->StrictJson.require(!value.strip().isEmpty(),"nonblank event key required"));
            parameters.afterEvidenceId().ifPresent(EvidenceId::new);}
    }
    public record ListRejected(ListParameters parameters,Failure failure,Parameter invalidParameter) implements ListCall {
        public ListRejected {Objects.requireNonNull(parameters);Objects.requireNonNull(failure);Objects.requireNonNull(invalidParameter);}
    }
    public record ListResult(ListParameters parameters,Optional<String> datasetSha256,long totalMatches,List<Metadata> evidence,
            Optional<String> nextAfterEvidenceId,Optional<Failure> failure,Optional<Parameter> invalidParameter) {
        public ListResult {Objects.requireNonNull(parameters);datasetSha256=Objects.requireNonNull(datasetSha256);StrictJson.safe(totalMatches,0);evidence=List.copyOf(evidence);nextAfterEvidenceId=Objects.requireNonNull(nextAfterEvidenceId);failure=Objects.requireNonNull(failure);invalidParameter=Objects.requireNonNull(invalidParameter);
            datasetSha256.ifPresent(value->StrictJson.require(value.matches("[A-F0-9]{64}"),"canonical dataset digest required"));
            StrictJson.require(failure.isEmpty()?datasetSha256.isPresent()&&invalidParameter.isEmpty()&&totalMatches>=evidence.size()&&parameters.limit().orElse(0)>=evidence.size()
                    :datasetSha256.isEmpty()&&totalMatches==0&&evidence.isEmpty()&&nextAfterEvidenceId.isEmpty(),"list availability branch mismatch");}
    }
    public record ReadParameters(Optional<String> evidenceId,Optional<Long> offset) {
        public ReadParameters {evidenceId=Objects.requireNonNull(evidenceId);offset=Objects.requireNonNull(offset);}
    }
    public sealed interface ReadCall permits ReadQuery,ReadRejected {ReadParameters parameters();}
    public record ReadQuery(ReadParameters parameters,EvidenceId evidenceId,long offset,int maxBytes) implements ReadCall {
        public ReadQuery {Objects.requireNonNull(parameters);Objects.requireNonNull(evidenceId);StrictJson.safe(offset,0);StrictJson.require(maxBytes>0&&maxBytes<=MAX_READ_BYTES
                &&parameters.evidenceId().equals(Optional.of(evidenceId.value()))&&parameters.offset().equals(Optional.of(offset)),"bounded read parameters must preserve exact normalized originals");}
    }
    public record ReadRejected(ReadParameters parameters,Failure failure) implements ReadCall {
        public ReadRejected {Objects.requireNonNull(parameters);Objects.requireNonNull(failure);}
    }
    public record Content(String base64,int bytes,boolean eof) {public Content {Objects.requireNonNull(base64);StrictJson.require(bytes>=0&&bytes<=MAX_READ_BYTES&&java.util.Base64.getDecoder().decode(base64).length==bytes,"exact bounded base64 slice required");}}
    public record ReadResult(ReadParameters parameters,Optional<Metadata> metadata,Optional<Content> content,Optional<Failure> failure) {
        public ReadResult {Objects.requireNonNull(parameters);metadata=Objects.requireNonNull(metadata);content=Objects.requireNonNull(content);failure=Objects.requireNonNull(failure);
            StrictJson.require(failure.isEmpty()?metadata.isPresent()&&content.isPresent()&&parameters.offset().isPresent():content.isEmpty()&&(metadata.isPresent()==(failure.orElseThrow()==Failure.OFFSET_RANGE)),"read availability branch mismatch");
            if(content.isPresent()){long end=Math.addExact(parameters.offset().orElseThrow(),content.orElseThrow().bytes());StrictJson.require(end<=metadata.orElseThrow().bytes()&&content.orElseThrow().eof()==(end==metadata.orElseThrow().bytes()),"slice position/EOF mismatch");}}
    }
}
