package org.xar.ck3.control.contracts.offline;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** One wire contract for the explicit read references in incident before indexes.
 * These are retained DATA references. Decoding never reads a file, follows a receipt's nested
 * references or grants a successful read, action, source review or runtime admission. */
public final class IncidentReadIndex {
    private static final String V1="xar.episode-incident-before-index/v1";
    private static final String V2="xar.episode-incident-before-index/v2";
    private static final String V3="xar.episode-incident-before-index/v3";
    private static final String FAILED="xar.failed-read-originals/v1";
    private IncidentReadIndex(){ }

    public sealed interface Value permits None,KnownReceipt,FailedQuery {
        List<ExactRef> references();
    }
    public enum None implements Value {
        INSTANCE;
        @Override public List<ExactRef> references(){return List.of();}
    }
    /** V2 retains exactly the producer's receipt reference, without a recursive payload closure. */
    public record KnownReceipt(ExactRef original) implements Value {
        public KnownReceipt{Objects.requireNonNull(original);}
        @Override public List<ExactRef> references(){return List.of(original);}
    }
    /** V3 retains only this explicitly declared outcome/request/optional observation/dependency set. */
    public record FailedQuery(ExactRef originalOutcome,ExactRef preparedRequest,Optional<ExactRef> observedFailure,
            List<ExactRef> dependencies) implements Value {
        public FailedQuery{
            Objects.requireNonNull(originalOutcome);Objects.requireNonNull(preparedRequest);
            Objects.requireNonNull(observedFailure);dependencies=List.copyOf(dependencies);
        }
        @Override public List<ExactRef> references(){
            var refs=new LinkedHashSet<ExactRef>(List.of(originalOutcome,preparedRequest));
            observedFailure.ifPresent(refs::add);refs.addAll(dependencies);return List.copyOf(refs);
        }
    }

    /** Strict version/read-field decoder. The caller validates its complete index metadata and I/O. */
    public static Value decode(JsonNode original){
        StrictJson.require(original instanceof ObjectNode,"Actual before-index JSON object required");
        var row=(ObjectNode)original;String schema=StrictJson.text(row.get("schema"));
        if(V1.equals(schema)){
            StrictJson.require(!row.has("original_read_ref")&&!row.has("failed_read_originals"),
                    "Legacy before index cannot claim read originals");return None.INSTANCE;
        }
        StrictJson.require("planning_diagnostic".equals(StrictJson.text(row.get("capture_stage")))
                &&row.get("action_id")!=null&&row.get("action_id").isNull(),
                "Read-original index requires its no-command diagnostic version");
        if(V2.equals(schema)){
            StrictJson.require(!row.has("failed_read_originals")&&row.path("original_read_ref").isObject(),
                    "Private receipt index requires only its non-null original read reference");
            return new KnownReceipt(ExactRef.fromJson(row.get("original_read_ref")));
        }
        StrictJson.require(V3.equals(schema)&&!row.has("original_read_ref")&&row.path("failed_read_originals").isObject(),
                "Failed query index requires its original outcome/request pair");
        ObjectNode refs=StrictJson.object(row.get("failed_read_originals"),
                Set.of("schema","original_outcome_ref","prepared_request_ref","observed_failure_ref","dependency_refs"));
        StrictJson.require(FAILED.equals(StrictJson.text(refs.get("schema"))),"Versioned failed-read originals required");
        JsonNode observed=refs.get("observed_failure_ref"),dependencies=refs.get("dependency_refs");
        StrictJson.require(observed!=null&&(observed.isNull()||observed.isObject()),
                "Failed read observed proof must be explicit null or a reference");
        StrictJson.require(dependencies!=null&&dependencies.isArray(),"Failed read dependencies must be an explicit reference array");
        var originals=new ArrayList<ExactRef>();for(JsonNode ref:dependencies)originals.add(ExactRef.fromJson(ref));
        return new FailedQuery(ExactRef.fromJson(refs.get("original_outcome_ref")),ExactRef.fromJson(refs.get("prepared_request_ref")),
                observed.isNull()?Optional.empty():Optional.of(ExactRef.fromJson(observed)),originals);
    }

    /** Adds exactly one version's read fields to a fresh copy of the producer's existing metadata. */
    public static ObjectNode encode(Value original,ObjectNode metadata){
        Objects.requireNonNull(original);Objects.requireNonNull(metadata);
        StrictJson.require(!metadata.has("original_read_ref")&&!metadata.has("failed_read_originals"),
                "Fresh before-index metadata cannot contain another read branch");
        String schema=original instanceof KnownReceipt?V2:original instanceof FailedQuery?V3:V1;
        StrictJson.require(!metadata.has("schema")||schema.equals(StrictJson.text(metadata.get("schema"))),
                "Before-index metadata cannot change its versioned read branch");
        ObjectNode row=metadata.deepCopy();row.put("schema",schema);
        if(original instanceof KnownReceipt known)row.set("original_read_ref",known.original().toJson());
        else if(original instanceof FailedQuery failed){
            ObjectNode refs=StrictJson.object().put("schema",FAILED);
            refs.set("original_outcome_ref",failed.originalOutcome().toJson());
            refs.set("prepared_request_ref",failed.preparedRequest().toJson());
            failed.observedFailure().ifPresentOrElse(ref->refs.set("observed_failure_ref",ref.toJson()),()->refs.putNull("observed_failure_ref"));
            var dependencies=refs.putArray("dependency_refs");failed.dependencies().forEach(ref->dependencies.add(ref.toJson()));
            row.set("failed_read_originals",refs);
        }
        StrictJson.require(original.equals(decode(row)),"Incident read-index fields changed during encoding");return row;
    }

    /** The existing exact whole-index field set, extended only by its declared v2 or v3 read branch. */
    public static Set<String> indexFields(Value original,boolean diagnostic){
        Objects.requireNonNull(original);
        StrictJson.require(diagnostic||original==None.INSTANCE,"Read originals require a no-command diagnostic index");
        var fields=new LinkedHashSet<>(Set.of("schema","session_id","origin","source","incident_id","kind","action_id","arguments_sha256","before_ref"));
        if(diagnostic){fields.add("capture_stage");fields.add("original_frame_ref");}
        if(original instanceof KnownReceipt)fields.add("original_read_ref");
        else if(original instanceof FailedQuery)fields.add("failed_read_originals");
        return Set.copyOf(fields);
    }
}
