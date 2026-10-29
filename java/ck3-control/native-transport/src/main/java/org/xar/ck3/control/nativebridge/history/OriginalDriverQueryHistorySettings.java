package org.xar.ck3.control.nativebridge.history;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.NativeLaunchPlan;

/** Explicit new Java settings and separately captured legacy facts. Neither grants a storage or Game action permit. */
public final class OriginalDriverQueryHistorySettings {
    public static final int MAX_BYTES=64<<10;
    public static final String REQUEST_SCHEMA="xar.java-army-query-history-settings-request/v1";
    public static final String DOCUMENT_SCHEMA="xar.java-original-driver-query-history-settings/v1";
    public static final String PRODUCER_FILE="RootArmyQueryHistoryConfigurationProducer.java";
    public static final long LEGACY_DRIVER_BYTES=1658471;
    public static final String LEGACY_DRIVER_SHA256="eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603";
    private OriginalDriverQueryHistorySettings() { }

    public enum Origin { JAVA_CONFIGURED,LEGACY_CAPTURED }
    public enum Admission { ROOT_STORAGE }
    public sealed interface DirectorySelection permits Disabled,Directory { }
    public record Disabled() implements DirectorySelection { }
    public record Directory(Path stateDirectory) implements DirectorySelection {
        public Directory {absolute(stateDirectory);}
    }
    public sealed interface DirectoryFact permits MissingDirectory,NullDirectory,DirectoryValue { }
    public record MissingDirectory() implements DirectoryFact { }
    public record NullDirectory() implements DirectoryFact { }
    /** Original spelling is retained; a relative path without its original working directory is not admitted. */
    public record DirectoryValue(String value) implements DirectoryFact {
        public DirectoryValue {textValue(value,32767);}
    }
    public sealed interface LimitFact permits MissingLimit,NullLimit,LimitValue { }
    public record MissingLimit() implements LimitFact { }
    public record NullLimit() implements LimitFact { }
    public record LimitValue(BigInteger value) implements LimitFact {
        public LimitValue {Objects.requireNonNull(value);require(value.signum()>=0,"negative original sidecar limit");}
    }
    public sealed interface GuardFact permits MissingGuard,NullGuard,GuardValue { }
    public record MissingGuard() implements GuardFact { }
    public record NullGuard() implements GuardFact { }
    /** Source data for an original callable; this reference cannot manufacture a callable or admission authority. */
    public record GuardValue(ExactRef original) implements GuardFact {
        public GuardValue {source(original,16<<20);}
    }
    public sealed interface Configuration permits JavaConfigured,LegacyCaptured { Origin origin(); }
    public record JavaConfigured(DirectorySelection stateDirectory,long limitBytes,Admission admission) implements Configuration {
        public JavaConfigured {Objects.requireNonNull(stateDirectory);Objects.requireNonNull(admission);require(limitBytes>=0,"explicit nonnegative Java sidecar limit required");}
        @Override public Origin origin(){return Origin.JAVA_CONFIGURED;}
    }
    public record LegacyCaptured(ExactRef originalDriver,DirectoryFact stateDirectory,LimitFact limitBytes,
            GuardFact admissionGuard) implements Configuration {
        public LegacyCaptured {
            source(originalDriver,16<<20);Objects.requireNonNull(stateDirectory);Objects.requireNonNull(limitBytes);Objects.requireNonNull(admissionGuard);
            require(originalDriver.bytes()==LEGACY_DRIVER_BYTES&&originalDriver.sha256().equals(LEGACY_DRIVER_SHA256),
                    "this legacy fact contract requires its exact reviewed original constructor source");
        }
        @Override public Origin origin(){return Origin.LEGACY_CAPTURED;}
    }
    /** A standalone typed input original. No self-reference or Derived Settings/Definitions hash is embedded. */
    public record Request(String machineId,Instant observedAt,Instant reviewAt,Configuration configuration) {
        public Request {
            require(machineId!=null&&machineId.matches("[a-z0-9][a-z0-9-]{0,127}")&&!machineId.equals("unknown"),"actual request machine required");
            Objects.requireNonNull(observedAt);Objects.requireNonNull(reviewAt);Objects.requireNonNull(configuration);
            require(observedAt.isBefore(reviewAt)&&Duration.between(observedAt,reviewAt).compareTo(Duration.ofDays(7))<=0,"finite request period required");
        }
    }
    public record SourceRefs(ExactRef configurationOriginal,ExactRef producerOriginal) {
        public SourceRefs {source(configurationOriginal,MAX_BYTES);source(producerOriginal,16<<20);}
    }
    public record Document(SourceRefs sourceRefs,Request request) {
        public Document {Objects.requireNonNull(sourceRefs);Objects.requireNonNull(request);}
    }
    public sealed interface Effective permits NoStateDirectory,WithStateDirectory { }
    public record NoStateDirectory() implements Effective { }
    public record WithStateDirectory(Path stateDirectory,long limitBytes) implements Effective {
        public WithStateDirectory {absolute(stateDirectory);require(limitBytes>=0,"nonnegative actual sidecar limit required");}
    }
    public enum Problem { LEGACY_FACTS_MISSING,LEGACY_NULL_LIMIT,LEGACY_RELATIVE_DIRECTORY,LEGACY_LIMIT_RANGE,LEGACY_GUARD_UNBOUND,LEGACY_CAPTURE_UNAVAILABLE }
    public static final class UnusableSettings extends IOException {
        private static final long serialVersionUID=1L;
        private final Problem problem;
        private UnusableSettings(Problem problem,String message){super(message);this.problem=problem;}
        public Problem problem(){return problem;}
    }
    /** Source defaults are known (None/0/None), but missing capture is not evidence that a particular run used them. */
    public static Effective effective(Configuration configuration)throws UnusableSettings {
        Objects.requireNonNull(configuration);
        if(configuration instanceof JavaConfigured java) {
            if(java.stateDirectory() instanceof Disabled)return new NoStateDirectory();
            return new WithStateDirectory(((Directory)java.stateDirectory()).stateDirectory(),java.limitBytes());
        }
        var old=(LegacyCaptured)configuration;
        if(old.stateDirectory() instanceof MissingDirectory||old.limitBytes() instanceof MissingLimit||old.admissionGuard() instanceof MissingGuard)
            throw new UnusableSettings(Problem.LEGACY_FACTS_MISSING,"original Driver argument facts are missing; do not infer None or zero");
        if(old.limitBytes() instanceof NullLimit)throw new UnusableSettings(Problem.LEGACY_NULL_LIMIT,"original Driver rejects an explicit null limit");
        if(old.admissionGuard() instanceof GuardValue)
            throw new UnusableSettings(Problem.LEGACY_GUARD_UNBOUND,"captured callable source has no actual qualified Java admission binding");
        // The original constructor accepts a nonnegative Python integer even when no Store is used.
        // A long Store-size conversion is relevant only to the branch that actually creates that Store.
        if(old.stateDirectory() instanceof NullDirectory)return new NoStateDirectory();
        long limit;
        try{limit=((LimitValue)old.limitBytes()).value().longValueExact();}
        catch(ArithmeticException outside){throw new UnusableSettings(Problem.LEGACY_LIMIT_RANGE,"original limit is outside this actual Java Store's exact long domain");}
        Path directory;
        try{directory=Path.of(((DirectoryValue)old.stateDirectory()).value());}
        catch(java.nio.file.InvalidPathException invalid){throw new UnusableSettings(Problem.LEGACY_RELATIVE_DIRECTORY,"original state directory has no valid absolute Java path representation");}
        if(!directory.isAbsolute()||!directory.equals(directory.normalize()))
            throw new UnusableSettings(Problem.LEGACY_RELATIVE_DIRECTORY,"original state directory needs its actual absolute resolution; do not borrow the managed plan directory");
        return new WithStateDirectory(directory,limit);
    }

    public static byte[] encodeRequest(Request request){return StrictJson.canonical(requestNode(request),MAX_BYTES);}
    public static Request decodeRequest(byte[] bytes){return request(StrictJson.parse(bytes,MAX_BYTES));}
    public static byte[] encode(Document document){
        Objects.requireNonNull(document);var root=node().put("schema",DOCUMENT_SCHEMA);var refs=node();
        refs.set("configuration_original",refNode(document.sourceRefs().configurationOriginal()));
        refs.set("producer_original",refNode(document.sourceRefs().producerOriginal()));root.set("source_refs",refs);
        root.set("request",requestNode(document.request()));return StrictJson.canonical(root,MAX_BYTES);
    }
    public static Document decode(byte[] bytes){
        var root=object(StrictJson.parse(bytes,MAX_BYTES),Set.of("schema","source_refs","request"));
        require(text(root.get("schema")).equals(DOCUMENT_SCHEMA),"exact query-history document version required");
        var refs=object(root.get("source_refs"),Set.of("configuration_original","producer_original"));
        return new Document(new SourceRefs(ref(refs.get("configuration_original")),ref(refs.get("producer_original"))),request(root.get("request")));
    }
    private static ObjectNode requestNode(Request request){
        Objects.requireNonNull(request);var root=node().put("schema",REQUEST_SCHEMA).put("machine_id",request.machineId())
                .put("observed_at",request.observedAt().toString()).put("review_at",request.reviewAt().toString());
        var value=node().put("kind",request.configuration().origin().name());
        if(request.configuration() instanceof JavaConfigured java){
            var directory=node();if(java.stateDirectory() instanceof Disabled)directory.put("kind","DISABLED");
            else directory.put("kind","DIRECTORY").put("state_directory",((Directory)java.stateDirectory()).stateDirectory().toString());
            value.set("state_directory",directory);value.put("limit_bytes",Long.toString(java.limitBytes())).put("admission",java.admission().name());
        }else{
            var old=(LegacyCaptured)request.configuration();value.set("original_driver",refNode(old.originalDriver()));
            var directory=node();
            if(old.stateDirectory() instanceof MissingDirectory)directory.put("presence","MISSING");
            else if(old.stateDirectory() instanceof NullDirectory)directory.put("presence","NULL");
            else directory.put("presence","VALUE").put("value",((DirectoryValue)old.stateDirectory()).value());
            value.set("state_directory",directory);var limit=node();
            if(old.limitBytes() instanceof MissingLimit)limit.put("presence","MISSING");
            else if(old.limitBytes() instanceof NullLimit)limit.put("presence","NULL");
            else limit.put("presence","VALUE").put("value",((LimitValue)old.limitBytes()).value().toString());
            value.set("limit_bytes",limit);var guard=node();
            if(old.admissionGuard() instanceof MissingGuard)guard.put("presence","MISSING");
            else if(old.admissionGuard() instanceof NullGuard)guard.put("presence","NULL");
            else{guard.put("presence","VALUE");guard.set("original",refNode(((GuardValue)old.admissionGuard()).original()));}
            value.set("admission_guard",guard);
        }
        root.set("configuration",value);return root;
    }
    private static Request request(JsonNode input){
        var root=object(input,Set.of("schema","machine_id","observed_at","review_at","configuration"));
        require(text(root.get("schema")).equals(REQUEST_SCHEMA),"exact query-history request version required");
        JsonNode raw=root.get("configuration");require(raw!=null&&raw.isObject(),"typed query-history configuration required");
        String kind=text(raw.get("kind"));Configuration configuration;
        if(kind.equals("JAVA_CONFIGURED")){
            var value=object(raw,Set.of("kind","state_directory","limit_bytes","admission"));var directory=value.get("state_directory");
            require(directory!=null&&directory.isObject(),"explicit Java state-directory selection required");String mode=text(directory.get("kind"));DirectorySelection selection;
            if(mode.equals("DISABLED")){object(directory,Set.of("kind"));selection=new Disabled();}
            else{object(directory,Set.of("kind","state_directory"));require(mode.equals("DIRECTORY"),"explicit Java directory mode required");selection=new Directory(Path.of(text(directory.get("state_directory"))));}
            configuration=new JavaConfigured(selection,decimal(value.get("limit_bytes")).longValueExact(),Admission.valueOf(text(value.get("admission"))));
        }else{
            require(kind.equals("LEGACY_CAPTURED"),"explicit Java or captured legacy origin required");
            var value=object(raw,Set.of("kind","original_driver","state_directory","limit_bytes","admission_guard"));
            var directory=value.get("state_directory");String dp=presence(directory);DirectoryFact df;
            if(dp.equals("MISSING")){object(directory,Set.of("presence"));df=new MissingDirectory();}
            else if(dp.equals("NULL")){object(directory,Set.of("presence"));df=new NullDirectory();}
            else{object(directory,Set.of("presence","value"));df=new DirectoryValue(text(directory.get("value")));}
            var limit=value.get("limit_bytes");String lp=presence(limit);LimitFact lf;
            if(lp.equals("MISSING")){object(limit,Set.of("presence"));lf=new MissingLimit();}
            else if(lp.equals("NULL")){object(limit,Set.of("presence"));lf=new NullLimit();}
            else{object(limit,Set.of("presence","value"));lf=new LimitValue(decimal(limit.get("value")));}
            var guard=value.get("admission_guard");String gp=presence(guard);GuardFact gf;
            if(gp.equals("MISSING")){object(guard,Set.of("presence"));gf=new MissingGuard();}
            else if(gp.equals("NULL")){object(guard,Set.of("presence"));gf=new NullGuard();}
            else{object(guard,Set.of("presence","original"));gf=new GuardValue(ref(guard.get("original")));}
            configuration=new LegacyCaptured(ref(value.get("original_driver")),df,lf,gf);
        }
        return new Request(text(root.get("machine_id")),Instant.parse(text(root.get("observed_at"))),Instant.parse(text(root.get("review_at"))),configuration);
    }
    private static String presence(JsonNode value){require(value!=null&&value.isObject(),"explicit original field presence required");String p=text(value.get("presence"));require(Set.of("MISSING","NULL","VALUE").contains(p),"unknown original field presence");return p;}
    private static ObjectNode node(){return com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode();}
    private static ObjectNode object(JsonNode value,Set<String> keys){var result=StrictJson.object(value,keys);require(result.size()==keys.size()&&keys.stream().allMatch(result::has),"exact required query-history fields required");return result;}
    private static String text(JsonNode value){require(value!=null&&value.isTextual(),"exact JSON string required");return value.textValue();}
    private static BigInteger decimal(JsonNode value){String text=text(value);require(text.matches("0|[1-9][0-9]*")&&text.length()<=256,"canonical nonnegative decimal string required");return new BigInteger(text);}
    private static ObjectNode refNode(ExactRef ref){source(ref,16<<20);return node().put("path",ref.path()).put("bytes",Long.toString(ref.bytes())).put("sha256",ref.sha256());}
    private static ExactRef ref(JsonNode value){var n=object(value,Set.of("path","bytes","sha256"));return new ExactRef(text(n.get("path")),decimal(n.get("bytes")).longValueExact(),text(n.get("sha256")));}
    private static void textValue(String value,int maximum){require(value!=null&&value.length()<=maximum&&value.indexOf('\0')<0,"bounded original text required");}
    private static void absolute(Path directory){require(directory!=null&&directory.isAbsolute()&&directory.equals(directory.normalize()),"explicit absolute normalized state directory required");}
    private static void source(ExactRef ref,long maximum){Objects.requireNonNull(ref);require(ref.bytes()>0&&ref.bytes()<=maximum,"bounded nonempty original reference required");}
    private static void require(boolean value,String message){if(!value)throw new IllegalArgumentException(message);}

    private record HistoricalBinding(Document document,NativeLaunchPlan rootPlan,List<SharedSourceFiles.Witness> witnesses,
            SharedSourceFiles.DirectoryIdentity profileIdentity,SharedSourceFiles.DirectoryIdentity stateIdentity) {
        private HistoricalBinding { witnesses=List.copyOf(witnesses); }
    }

    /** Configuration custody only. Store admission still uses the actual Root storage guard and writer lock. */
    public static final class Bound {
        private final Configuration configuration;
        private final java.util.Optional<HistoricalBinding> historical;
        private final ExactRef original;
        private final Effective effective;
        private final List<ExactRef> sourceRefs;

        // Retained private constructor for readExact ABI compatibility
        private Bound(Document document,ExactRef original,NativeLaunchPlan rootPlan,Effective effective,
                List<ExactRef> refs,List<SharedSourceFiles.Witness> witnesses,
                SharedSourceFiles.DirectoryIdentity profileIdentity,SharedSourceFiles.DirectoryIdentity stateIdentity){
            this.configuration=document.request().configuration();
            this.historical=java.util.Optional.of(new HistoricalBinding(document,rootPlan,witnesses,profileIdentity,stateIdentity));
            this.original=original;this.effective=effective;
            this.sourceRefs=List.copyOf(refs);
        }

        // New private constructor for ordinary binding
        private Bound(JavaConfigured actualConfiguration,ExactRef actualConfig,ExactRef producerMetadata)throws UnusableSettings{
            this.configuration=actualConfiguration;
            this.historical=java.util.Optional.empty();
            this.original=actualConfig;
            this.effective=OriginalDriverQueryHistorySettings.effective(actualConfiguration);
            this.sourceRefs=List.of(actualConfig,producerMetadata);
        }

        public Configuration configuration(){return configuration;}
        public Effective effective(){return effective;}
        public Origin origin(){return configuration.origin();}
        public List<ExactRef> sourceRefs(){return sourceRefs;}
        public ExactRef original(){return original;}
        public java.util.Optional<Document> historicalDocument(){return historical.map(HistoricalBinding::document);}
        public Document document(){
            if(historical.isEmpty())throw new IllegalStateException("no historical document available for ordinary binding");
            return historical.get().document();
        }
        public Request request(){
            if(historical.isEmpty())throw new IllegalStateException("no historical request available for ordinary binding");
            return historical.get().document().request();
        }
        /** A Saved child keeps the original source authority and directories, while its request/session may change. */
        public void requireSame(NativeLaunchPlan current,Clock clock)throws IOException{
            Objects.requireNonNull(current);Objects.requireNonNull(clock);
            if(historical.isEmpty())return;
            var h=historical.get();
            if(current.sources()!=h.rootPlan().sources()||!current.profileDirectory().equals(h.rootPlan().profileDirectory())
                    ||!current.stateDirectory().equals(h.rootPlan().stateDirectory()))
                throw new IOException("query-history settings belong to another Root source authority or profile/state directory");
            current(h.document().request(),current,clock);current.sources().verify();
            current.sources().requireLoadedClass(OriginalDriverQueryHistorySettings.class);
            if(!h.profileIdentity().equals(SharedSourceFiles.nativeDirectory(current.profileDirectory()))
                    ||!h.stateIdentity().equals(SharedSourceFiles.nativeDirectory(current.stateDirectory())))
                throw new IOException("original Root profile/state directory identity changed");
            for(var witness:h.witnesses())SharedSourceFiles.assertUnchanged(witness);
            var decoded=decodeRead(original,MAX_BYTES);
            if(!h.document().equals(decoded))throw new IOException("retained query-history document changed");
            var input=read(h.document().sourceRefs().configurationOriginal(),MAX_BYTES);
            try{if(!h.document().request().equals(decodeRequest(input)))throw new IOException("original request no longer derives the retained document");}
            catch(IllegalArgumentException invalid){throw new IOException("invalid retained query-history request",invalid);}
            for(var witness:h.witnesses())SharedSourceFiles.assertUnchanged(witness);
        }
    }

    public static Bound ordinary(JavaConfigured actualConfiguration,ExactRef actualConfig,ExactRef producerMetadata) throws UnusableSettings {
        Objects.requireNonNull(actualConfiguration);
        Objects.requireNonNull(actualConfig);
        Objects.requireNonNull(producerMetadata);
        return new Bound(actualConfiguration,actualConfig,producerMetadata);
    }

    public static Bound readExact(ExactRef original,ExactRef expectedConfiguration,ExactRef expectedProducer,
            NativeLaunchPlan rootPlan,Clock clock)throws IOException{
        Objects.requireNonNull(rootPlan);Objects.requireNonNull(clock);
        source(original,MAX_BYTES);source(expectedConfiguration,MAX_BYTES);source(expectedProducer,16<<20);
        var refs=new LinkedHashSet<ExactRef>();refs.add(original);refs.add(expectedConfiguration);refs.add(expectedProducer);
        var witnesses=new ArrayList<SharedSourceFiles.Witness>();
        for(var ref:refs)witnesses.add(witness(ref));
        Document document=decodeRead(original,MAX_BYTES);
        if(!document.sourceRefs().equals(new SourceRefs(expectedConfiguration,expectedProducer)))
            throw new IOException("query-history document does not retain the actual request and selected producer");
        try{
            if(!document.request().equals(decodeRequest(read(expectedConfiguration,MAX_BYTES))))
                throw new IOException("query-history document differs from its actual standalone input request");
        }catch(IllegalArgumentException invalid){throw new IOException("invalid original query-history request",invalid);}
        requireProducer(rootPlan,expectedProducer);
        requireCapturedRuntimeFacts(document.request().configuration());
        if(document.request().configuration() instanceof LegacyCaptured legacy){
            if(refs.add(legacy.originalDriver()))witnesses.add(witness(legacy.originalDriver()));
            if(legacy.admissionGuard() instanceof GuardValue guard&&refs.add(guard.original()))witnesses.add(witness(guard.original()));
        }
        var result=new Bound(document,original,rootPlan,effective(document.request().configuration()),List.copyOf(refs),witnesses,
                SharedSourceFiles.nativeDirectory(rootPlan.profileDirectory()),SharedSourceFiles.nativeDirectory(rootPlan.stateDirectory()));
        result.requireSame(rootPlan,clock);return result;
    }
    /** A newly declared legacy-shaped request and old constructor source cannot certify an old invocation. */
    static void requireCapturedRuntimeFacts(Configuration configuration)throws UnusableSettings{
        Objects.requireNonNull(configuration);
        if(configuration instanceof LegacyCaptured)
            throw new UnusableSettings(Problem.LEGACY_CAPTURE_UNAVAILABLE,
                    "actual original Driver argument-capture producer is unavailable; a new request cannot certify historical NULL/VALUE facts");
    }
    private static void requireProducer(NativeLaunchPlan plan,ExactRef producer)throws IOException{
        Path path=Path.of(producer.path());absolute(path);
        if(!path.getFileName().toString().equals(PRODUCER_FILE))throw new IOException("exact query-history producer source role required");
        boolean found=false;
        for(var ref:plan.sources().review().completeRuntimeSources()){
            if(!Path.of(ref.path()).getFileName().toString().equals(PRODUCER_FILE))continue;
            if(!Path.of(ref.path()).equals(path)||ref.bytes()!=producer.bytes()||!ref.sha256().equals(producer.sha256()))
                throw new IOException("ambiguous or foreign query-history producer in actual launch source closure");
            found=true;
        }
        if(!found)throw new IOException("query-history producer is outside the actual launch source closure");
    }
    private static void current(Request request,NativeLaunchPlan plan,Clock clock)throws IOException{
        Instant now=clock.instant();
        if(now.isBefore(request.observedAt())||!now.isBefore(request.reviewAt())
                ||!request.machineId().equals(plan.sources().review().machineId())
                ||!request.machineId().equals(org.xar.ck3.control.build.WindowsJobProcess.currentMachineId()))
            throw new IOException("current query-history request and actual same machine required");
    }
    private static Document decodeRead(ExactRef ref,int maximum)throws IOException{
        byte[] raw=read(ref,maximum);
        try{
            Document value=decode(raw);
            if(!Arrays.equals(raw,encode(value)))throw new IOException("sole canonical query-history document encoding required");
            return value;
        }catch(IllegalArgumentException invalid){throw new IOException("invalid query-history document",invalid);}
    }
    private static SharedSourceFiles.Witness witness(ExactRef expected)throws IOException{
        Path path=Path.of(expected.path());absolute(path);var observed=SharedSourceFiles.observe(path);
        if(!Path.of(observed.source().path()).equals(path)||observed.source().bytes()!=expected.bytes()
                ||!observed.source().sha256().equals(expected.sha256()))throw new IOException("query-history source differs from its exact original reference");
        return observed;
    }
    private static byte[] read(ExactRef ref,int maximum)throws IOException{
        source(ref,maximum);var before=witness(ref);byte[] raw;
        try(var stream=Files.newInputStream(Path.of(ref.path()))){raw=stream.readNBytes(maximum+1);}
        if(raw.length!=ref.bytes())throw new IOException("query-history original changed or exceeds its finite limit");
        SharedSourceFiles.assertUnchanged(before);return raw;
    }
}
