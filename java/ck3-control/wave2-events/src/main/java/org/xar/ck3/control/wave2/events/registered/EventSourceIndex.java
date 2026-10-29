package org.xar.ck3.control.wave2.events.registered;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.registered.RegistryJson.*;

/** Validated immutable frozen source index. Lexical locations never constitute runtime call edges. */
public final class EventSourceIndex {
    public static final String SCHEMA="xar.ck3.vanilla-event-source-index";
    private EventSourceIndex() { }
    public record Build(String value,String executableSha256) {
        public Build {
            Objects.requireNonNull(value);sha(executableSha256);
            require(executableSha256.equals(RegisteredEventKnowledge.EXE.get(value)),"unsupported exact indexed build");
        }
        public static Build of(String value) { return new Build(value,RegisteredEventKnowledge.EXE.get(value)); }
    }
    public record EventKey(String value) {
        public EventKey { require(value!=null&&value.contains("."),"indexed event key requires its namespace separator"); }
        public String namespace() { return value.substring(0,value.lastIndexOf('.')); }
    }
    public record Location(String relativePath,long line,String fileSha256) {
        public Location { path(relativePath);positive(line);sha(fileSha256); }
        public ObjectValue json() { return b().set("relative_path",relativePath).set("line",line).set("file_sha256",fileSha256).build(); }
    }
    public record Candidate(Location location,long column) {
        public Candidate { Objects.requireNonNull(location);positive(column); }
        public ObjectValue json() { return merge(location.json(),b().set("column",column).set("kind","exact-token-lexical-candidate").build()); }
    }
    public enum Resolution {
        EXTERNAL("external-definition-file"),SAME_FILE("same-definition-file-only");
        private final String wire;
        Resolution(String wire) { this.wire=wire; }
        public String wire() { return wire; }
        public static Resolution parse(String value) {
            for(var resolution:values())if(resolution.wire.equals(value))return resolution;
            throw new IllegalArgumentException("unsupported lexical candidate resolution");
        }
    }
    public record Entry(EventKey key,Location definition,Resolution resolution,List<Candidate> candidates) {
        public Entry {
            Objects.requireNonNull(key);Objects.requireNonNull(definition);Objects.requireNonNull(resolution);candidates=List.copyOf(candidates);
            require(definition.relativePath().startsWith("events/")&&!candidates.isEmpty(),"event definition and nonempty lexical candidates required");
            for(var candidate:candidates) {
                String path=candidate.location().relativePath();
                require(path.startsWith("events/")||path.startsWith("common/"),"lexical candidate outside scan roots");
                require((resolution==Resolution.SAME_FILE)==path.equals(definition.relativePath()),"lexical candidate resolution/path differs");
            }
        }
        public ObjectValue json() { return b().set("namespace",key.namespace()).set("definition",definition.json())
                .set("caller_candidate_resolution",resolution.wire()).set("caller_candidates",arr(candidates.stream().map(Candidate::json).toList())).build(); }
    }
    public record Depot(String depotId,String manifest,long sizeBytes,String previousManifest,boolean sameManifest) {
        public Depot { decimal(depotId);decimal(manifest);decimal(previousManifest);require(sizeBytes>=0&&sizeBytes<=StrictJson.MAX_SAFE_INTEGER,"safe depot byte count required"); }
        public ObjectValue json() { return b().set("depot_id",depotId).set("manifest",manifest).set("size_bytes",sizeBytes)
                .set("previous_manifest",previousManifest).set("same_manifest",sameManifest).build(); }
    }
    public record ReuseEvidence(String method,String newBuildFreeze,String newInstalledManifest,String previousBuildIdentity,
            String previousInstalledManifest,long installedStateFlags,long updateResult,long targetBuildId) {
        public ReuseEvidence {
            Objects.requireNonNull(method);path(newBuildFreeze);path(newInstalledManifest);path(previousBuildIdentity);path(previousInstalledManifest);
            safe(installedStateFlags);safe(updateResult);safe(targetBuildId);
        }
        public ObjectValue json() { return b().set("method",method).set("new_build_freeze",newBuildFreeze).set("new_installed_manifest",newInstalledManifest)
                .set("previous_build_identity",previousBuildIdentity).set("previous_installed_manifest",previousInstalledManifest)
                .set("installed_state_flags",installedStateFlags).set("update_result",updateResult).set("target_build_id",targetBuildId).build(); }
    }
    public record Reuse(String previousBuild,String previousDatasetSha256,Depot depot,ReuseEvidence evidence,
            boolean freshSourceScan,boolean runtimeCallChainRevalidated,boolean newLiveEvidence) {
        public Reuse { Build.of(previousBuild);sha(previousDatasetSha256);Objects.requireNonNull(depot);Objects.requireNonNull(evidence); }
        public ObjectValue json() { return b().set("previous_build",previousBuild).set("previous_dataset_sha256",previousDatasetSha256)
                .set("data_depot",depot.json()).set("evidence",evidence.json()).set("fresh_source_scan",freshSourceScan)
                .set("runtime_call_chain_revalidated",runtimeCallChainRevalidated).set("new_live_evidence",newLiveEvidence).build(); }
    }
    public record Index(Build build,String datasetSha256,Map<EventKey,Entry> events,Optional<Reuse> reuse) {
        public Index {
            Objects.requireNonNull(build);sha(datasetSha256);Objects.requireNonNull(reuse);
            events=Collections.unmodifiableMap(new LinkedHashMap<>(events));
            events.forEach((key,entry)->require(key.equals(entry.key()),"indexed event key/row differs"));
        }
        public Optional<Entry> find(String key) { return events.entrySet().stream().filter(row->row.getKey().value().equals(key)).map(Map.Entry::getValue).findFirst(); }
    }

    /** Runtime validation precedes construction. The source-pinned knowledge object supplies the original document. */
    public static Index decode(ObjectValue root) {
        Objects.requireNonNull(root);
        Set<String> required=Set.of("schema","schema_version","ck3_build","ck3_exe_sha256","dataset_sha256","events","audit","scan_policy");
        require(root.fields().keySet().containsAll(required)&&Set.of("schema","schema_version","ck3_build","ck3_exe_sha256","dataset_sha256","events","audit","scan_policy","source_reuse_1_20_0_4","source_additions_1_20_0_4").containsAll(root.fields().keySet()),"source index fields differ");
        require(is(root.getOrNull("schema"),SCHEMA)&&is(root.getOrNull("schema_version"),1)
                &&root.getOrNull("schema_version") instanceof IntegerValue,"strict source index schema/version required");
        Build build=new Build(string(root,"ck3_build"),string(root,"ck3_exe_sha256"));
        String digest=string(root,"dataset_sha256");sha(digest);
        require(datasetSha256(root).equals(digest),"source index dataset SHA-256 mismatch");
        ObjectValue rows=requiredObject(root,"events");List<String> keys=new ArrayList<>(rows.fields().keySet());
        require(keys.equals(keys.stream().sorted(CODE_POINTS).toList()),"source events require deterministic Unicode key order");
        Map<EventKey,Entry> events=new LinkedHashMap<>();Set<String> definitions=new LinkedHashSet<>(),candidateFiles=new LinkedHashSet<>();long candidateCount=0,external=0;
        for(var row:rows.fields().entrySet()) {
            EventKey key=new EventKey(row.getKey());ObjectValue value=requiredObject(row.getValue());
            exact(value,Set.of("namespace","definition","caller_candidate_resolution","caller_candidates"));
            require(string(value,"namespace").equals(key.namespace()),"indexed namespace differs");
            ObjectValue rawDefinition=requiredObject(value,"definition");exact(rawDefinition,Set.of("relative_path","line","file_sha256"));
            Location definition=location(rawDefinition);Resolution resolution=Resolution.parse(string(value,"caller_candidate_resolution"));
            Value raw=value.getOrNull("caller_candidates");require(raw instanceof ArrayValue,"lexical candidates must be an explicit array");
            List<Candidate> candidates=new ArrayList<>();
            for(Value candidate:((ArrayValue)raw).values()) {
                ObjectValue fields=requiredObject(candidate);
                exact(fields,Set.of("relative_path","line","file_sha256","column","kind"));
                require(is(fields.getOrNull("kind"),"exact-token-lexical-candidate"),"unsupported lexical candidate kind");
                Candidate parsed=new Candidate(location(fields),number(fields,"column",1));candidates.add(parsed);candidateFiles.add(parsed.location().relativePath());
            }
            Entry entry=new Entry(key,definition,resolution,candidates);events.put(key,entry);definitions.add(definition.relativePath());
            candidateCount+=candidates.size();if(resolution==Resolution.EXTERNAL)external++;
        }
        ObjectValue audit=requiredObject(root,"audit");Map<String,Long> expected=Map.of(
                "registered_event_count",(long)events.size(),"unique_definition_count",(long)events.size(),
                "definition_file_count",(long)definitions.size(),"missing_definition_count",0L,"ambiguous_definition_count",0L,"namespace_mismatch_count",0L,
                "caller_candidate_reference_count",candidateCount,"external_caller_event_count",external,
                "same_file_only_caller_event_count",events.size()-external,"caller_candidate_file_count",(long)candidateFiles.size());
        require(audit.fields().keySet().equals(expected.keySet()),"source index audit fields differ");
        expected.forEach((key,value)->require(number(audit,key,0)==value,"source index audit differs from indexed rows"));
        Optional<Reuse> reuse=root.contains("source_reuse_1_20_0_4")?Optional.of(reuse(requiredObject(root,"source_reuse_1_20_0_4"))):Optional.empty();
        return new Index(build,digest,events,reuse);
    }
    public static String datasetSha256(ObjectValue document) {
        try { return HexFormat.of().withUpperCase().formatHex(MessageDigest.getInstance("SHA-256").digest(
                canonical(remove(document,"dataset_sha256")).getBytes(StandardCharsets.UTF_8))); }
        catch(NoSuchAlgorithmException impossible) { throw new AssertionError(impossible); }
    }
    private static String canonical(Value value) {
        if(value instanceof ObjectValue object) {
            List<String> fields=new ArrayList<>();for(String key:object.fields().keySet().stream().sorted(CODE_POINTS).toList())
                fields.add(new String(RetainedJson.encode(RetainedJson.value(key)),StandardCharsets.UTF_8)+":"+canonical(object.get(key)));
            return "{"+String.join(",",fields)+"}";
        }
        if(value instanceof ArrayValue array)return "["+String.join(",",array.values().stream().map(EventSourceIndex::canonical).toList())+"]";
        require(!(value instanceof FloatingValue),"frozen source index has no floating point fields");
        return new String(RetainedJson.encode(value),StandardCharsets.UTF_8);
    }
    private static Reuse reuse(ObjectValue value) {
        exact(value,Set.of("previous_build","previous_dataset_sha256","data_depot","evidence","fresh_source_scan","runtime_call_chain_revalidated","new_live_evidence"));
        ObjectValue depot=requiredObject(value,"data_depot"),evidence=requiredObject(value,"evidence");
        exact(depot,Set.of("depot_id","manifest","size_bytes","previous_manifest","same_manifest"));
        exact(evidence,Set.of("method","new_build_freeze","new_installed_manifest","previous_build_identity","previous_installed_manifest","installed_state_flags","update_result","target_build_id"));
        return new Reuse(string(value,"previous_build"),string(value,"previous_dataset_sha256"),
                new Depot(string(depot,"depot_id"),string(depot,"manifest"),number(depot,"size_bytes",0),string(depot,"previous_manifest"),booleanField(depot,"same_manifest")),
                new ReuseEvidence(string(evidence,"method"),string(evidence,"new_build_freeze"),string(evidence,"new_installed_manifest"),
                        string(evidence,"previous_build_identity"),string(evidence,"previous_installed_manifest"),number(evidence,"installed_state_flags",0),
                        number(evidence,"update_result",0),number(evidence,"target_build_id",0)),
                booleanField(value,"fresh_source_scan"),booleanField(value,"runtime_call_chain_revalidated"),booleanField(value,"new_live_evidence"));
    }
    private static Location location(ObjectValue value) { return new Location(string(value,"relative_path"),number(value,"line",1),string(value,"file_sha256")); }
    private static void exact(ObjectValue object,Set<String> fields) { require(object.fields().keySet().equals(fields),"source record fields differ"); }
    private static ObjectValue requiredObject(Value value) { require(value instanceof ObjectValue,"source index object required");return (ObjectValue)value; }
    private static ObjectValue requiredObject(ObjectValue object,String key) { return requiredObject(object.getOrNull(key)); }
    private static String string(ObjectValue object,String key) { Value value=object.getOrNull(key);require(value instanceof StringValue,"source index string required: "+key);return ((StringValue)value).value(); }
    private static long number(ObjectValue object,String key,long minimum) { Value value=object.getOrNull(key);require(value instanceof IntegerValue,"exact source index integer required: "+key);BigInteger n=((IntegerValue)value).value();require(n.compareTo(BigInteger.valueOf(minimum))>=0&&n.compareTo(BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER))<=0,"safe source integer range required");return n.longValueExact(); }
    private static boolean booleanField(ObjectValue object,String key) { Value value=object.getOrNull(key);require(value instanceof BooleanValue,"exact source reuse boolean required");return ((BooleanValue)value).value(); }
    private static void path(String value) { require(value!=null&&!value.isEmpty()&&!value.contains("\\")&&!value.startsWith("/"),"nonempty POSIX relative source path required");String[] parts=value.split("/",-1);require(!parts[0].matches("[A-Za-z]:")&&!List.of(parts).contains(".."),"source path escapes relative root"); }
    private static void sha(String value) { require(value!=null&&value.matches("[0-9A-F]{64}"),"uppercase source SHA-256 required"); }
    private static void decimal(String value) { require(value!=null&&value.matches("0|[1-9][0-9]*"),"canonical identity decimal string required"); }
    private static void positive(long value) { require(value>0&&value<=StrictJson.MAX_SAFE_INTEGER,"positive safe source location required"); }
    private static void safe(long value) { require(value>=0&&value<=StrictJson.MAX_SAFE_INTEGER,"safe source metadata integer required"); }
    private static void require(boolean value,String reason) { StrictJson.require(value,reason); }
    private static final Comparator<String> CODE_POINTS=(left,right)-> {
        int a=0,b=0;while(a<left.length()&&b<right.length()) { int x=left.codePointAt(a),y=right.codePointAt(b);if(x!=y)return Integer.compare(x,y);a+=Character.charCount(x);b+=Character.charCount(y); }
        return Integer.compare(left.length()-a,right.length()-b);
    };
}
