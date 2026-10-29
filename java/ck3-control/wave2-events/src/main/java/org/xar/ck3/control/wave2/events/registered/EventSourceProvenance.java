package org.xar.ck3.control.wave2.events.registered;

import java.io.IOException;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.registered.RegistryJson.*;

/** Original source_index.provenance semantics; lexical evidence remains separate from runtime callers. */
public final class EventSourceProvenance {
    public static final String SCHEMA="xar.ck3.vanilla-event-source-provenance";
    public static final String REVIEW="not_manually_reviewed_as_call_edges";
    public static final String CURRENT_BUILD="1.20.0.4";
    private EventSourceProvenance() { }
    public sealed interface Parameter permits Text,NonText { }
    public record Text(String value) implements Parameter { public Text { Objects.requireNonNull(value); } }
    public enum NonText implements Parameter { MISSING,NULL,WRONG_TYPE }
    public record Query(Parameter key,Parameter build) {
        public Query { Objects.requireNonNull(key);Objects.requireNonNull(build); }
        public Query(String key,String build) { this(new Text(key),new Text(build)); }
    }
    public enum Reason {
        UNSUPPORTED_BUILD("unsupported_ck3_build"),INVALID_KEY("invalid_event_definition_key"),
        INTEGRITY("source_index_integrity_error"),NOT_INDEXED("event_definition_key_not_indexed");
        private final String wire;
        Reason(String wire) { this.wire=wire; }
        public String wire() { return wire; }
    }
    public enum InvalidParameter { BUILD("build"),KEY("key");private final String wire;InvalidParameter(String wire){this.wire=wire;}public String wire(){return wire;} }
    public record Response(Optional<String> key,Optional<String> build,Optional<String> executableSha256,Optional<String> datasetSha256,
            Optional<EventSourceIndex.Entry> entry,Optional<EventSourceIndex.Reuse> reuse,Optional<Reason> reason,Optional<InvalidParameter> invalidParameter) {
        public Response {
            Objects.requireNonNull(key);Objects.requireNonNull(build);Objects.requireNonNull(executableSha256);Objects.requireNonNull(datasetSha256);
            Objects.requireNonNull(entry);Objects.requireNonNull(reuse);Objects.requireNonNull(reason);Objects.requireNonNull(invalidParameter);
            StrictJson.require(entry.isPresent()==reason.isEmpty(),"available provenance requires an actual indexed row");
            StrictJson.require(entry.isEmpty()||(datasetSha256.isPresent()&&build.isPresent()&&executableSha256.isPresent()
                    &&key.orElseThrow().equals(entry.orElseThrow().key().value())),"indexed provenance identity differs");
            StrictJson.require(reuse.isEmpty()||datasetSha256.isPresent(),"source reuse requires a validated dataset");
        }
        public boolean available() { return entry.isPresent(); }
        public ObjectValue json() {
            var result=b().set("schema",SCHEMA).set("schema_version",1).set("status",available()?"available":"unavailable")
                    .set("key",key.orElse(null)).set("build",build.orElse(null)).set("ck3_exe_sha256",executableSha256.orElse(null))
                    .set("dataset_sha256",datasetSha256.orElse(null)).set("namespace",entry.map(row->row.key().namespace()).orElse(null))
                    .set("definition",entry.<Value>map(row->row.definition().json()).orElse(RetainedJson.NULL))
                    .set("caller_candidate_resolution",entry.map(row->row.resolution().wire()).orElse(null))
                    .set("caller_candidates",arr(entry.map(row->row.candidates().stream().map(EventSourceIndex.Candidate::json).toList()).orElse(List.of())))
                    .set("caller_candidates_are_lexical_only",true).set("caller_candidates_review_status",REVIEW)
                    .set("unavailable_reason",reason.map(Reason::wire).orElse(null)).set("invalid_parameter",invalidParameter.map(InvalidParameter::wire).orElse(null)).build();
            return reuse.map(value->result.with("source_reuse_1_20_0_4",value.json())).orElse(result);
        }
    }
    @FunctionalInterface public interface Source { EventSourceIndex.Index load(String build)throws IOException; }
    public static Response query(Query query,Source source) {
        Objects.requireNonNull(query);Objects.requireNonNull(source);
        Optional<String> key=textParameter(query.key()),build=textParameter(query.build());
        Optional<String> executable=build.map(RegisteredEventKnowledge.EXE::get);
        if(executable.isEmpty())return unavailable(key,build,executable,Reason.UNSUPPORTED_BUILD,Optional.of(InvalidParameter.BUILD));
        if(key.isEmpty()||pythonBlank(key.orElseThrow()))return unavailable(key,build,executable,Reason.INVALID_KEY,Optional.of(InvalidParameter.KEY));
        EventSourceIndex.Index document;
        try {
            document=Objects.requireNonNull(source.load(build.orElseThrow()));
            StrictJson.require(document.build().value().equals(build.orElseThrow()),"source index differs from requested build");
        }catch(IOException|IllegalArgumentException failure) { return unavailable(key,build,executable,Reason.INTEGRITY,Optional.empty()); }
        Optional<EventSourceIndex.Entry> row=document.find(key.orElseThrow());
        return new Response(key,build,executable,Optional.of(document.datasetSha256()),row,document.reuse(),row.isPresent()?Optional.empty():Optional.of(Reason.NOT_INDEXED),Optional.empty());
    }
    private static Response unavailable(Optional<String> key,Optional<String> build,Optional<String> executable,Reason reason,Optional<InvalidParameter> invalid) {
        return new Response(key,build,executable,Optional.empty(),Optional.empty(),Optional.empty(),Optional.of(reason),invalid);
    }
    private static Optional<String> textParameter(Parameter value) { return value instanceof Text text?Optional.of(text.value()):Optional.empty(); }
    private static boolean pythonBlank(String value) { return value.codePoints().allMatch(EventSourceProvenance::pythonSpace); }
    private static boolean pythonSpace(int value) { return value>=0x09&&value<=0x0d||value>=0x1c&&value<=0x20||value==0x85||value==0xa0||value==0x1680||value>=0x2000&&value<=0x200a||value>=0x2028&&value<=0x2029||value==0x202f||value==0x205f||value==0x3000; }
}
