import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import java.util.concurrent.TimeUnit;

/** Mechanical original process recording. No capacity, lifecycle or business admission is granted. */
public final class OriginalCommandRecorder {
    private static final ObjectMapper JSON=new ObjectMapper()
            .enable(com.fasterxml.jackson.core.JsonParser.Feature.STRICT_DUPLICATE_DETECTION)
            .enable(com.fasterxml.jackson.databind.DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    public record Config(String machine_id,String source_HEAD,Path repo_root,Path runtime,Path output_root,
                         String label,List<String> argv,Integer timeout_seconds) {
        public Config {
            need(machine_id!=null&&machine_id.matches("[a-z0-9-]+"),"explicit machine");
            need(source_HEAD!=null&&source_HEAD.matches("[0-9a-f]{40}"),"exact source HEAD");
            for(Path path:List.of(repo_root,runtime,output_root))
                need(path.isAbsolute()&&path.normalize().equals(path),"absolute normalized roots");
            need(label!=null&&label.matches("[A-Za-z0-9_-]+"),"unique simple label");
            argv=List.copyOf(argv);need(!argv.isEmpty(),"nonempty argv");
            for(String item:argv)need(item!=null&&!item.isEmpty(),"nonempty argv strings");
            need(timeout_seconds==null||timeout_seconds>=1&&timeout_seconds<=1200,"bounded timeout or delegated public supervision");
        }
    }
    private OriginalCommandRecorder() { }
    private static void need(boolean value,String message){if(!value)throw new IllegalArgumentException(message);}
    private static String text(JsonNode value,String key){
        JsonNode node=value.path(key);need(node.isTextual()&&!node.textValue().isBlank(),"literal text "+key);return node.textValue();
    }
    public static Config decode(JsonNode value) {
        Set<String> fields=Set.of("machine_id","source_HEAD","repo_root","runtime","output_root","label","argv","timeout_seconds");
        Set<String> actual=new java.util.HashSet<>();value.fieldNames().forEachRemaining(actual::add);
        need(value.isObject()&&actual.equals(fields),"exact recorder request fields");
        JsonNode timeout=value.get("timeout_seconds");
        need(timeout.isNull()||timeout.isIntegralNumber()&&timeout.canConvertToInt(),"literal integral timeout or explicit null");
        need(value.path("argv").isArray(),"argv array");List<String> argv=new ArrayList<>();
        for(JsonNode item:value.path("argv")){need(item.isTextual()&&!item.textValue().isEmpty(),"argv text");argv.add(item.textValue());}
        return new Config(text(value,"machine_id"),text(value,"source_HEAD"),Path.of(text(value,"repo_root")),
                Path.of(text(value,"runtime")),Path.of(text(value,"output_root")),text(value,"label"),argv,timeout.isNull()?null:timeout.intValue());
    }
    public static ObjectNode encode(Config config) {
        ObjectNode wire=JSON.createObjectNode().put("machine_id",config.machine_id()).put("source_HEAD",config.source_HEAD())
                .put("repo_root",config.repo_root().toString()).put("runtime",config.runtime().toString())
                .put("output_root",config.output_root().toString()).put("label",config.label());
        wire.set("argv",JSON.valueToTree(config.argv()));
        if(config.timeout_seconds()==null)wire.putNull("timeout_seconds");else wire.put("timeout_seconds",config.timeout_seconds());
        return wire;
    }
    private static ObjectNode pin(Path path)throws Exception {
        byte[] bytes=Files.readAllBytes(path);
        return JSON.createObjectNode().put("path",path.toString()).put("bytes",bytes.length)
                .put("sha256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
    }
    private static void write(Path path,ObjectNode value)throws Exception {
        byte[] bytes=JSON.writeValueAsBytes(value);need(bytes.length<=32768,"bounded recorder receipt");
        Files.write(path,bytes,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
    }
    public static int execute(Path request)throws Exception {
        request=request.toAbsolutePath().normalize();need(Files.size(request)<=32768,"bounded request");
        Config input=decode(JSON.readTree(Files.readAllBytes(request)));
        need(request.getParent().equals(input.output_root()),"request must be in explicit output root");
        for(Path root:List.of(input.repo_root(),input.runtime(),input.output_root()))
            need(Files.isDirectory(root)&&root.toRealPath().equals(root),"actual ordinary roots");
        JsonNode runtime=JSON.readTree(Files.readAllBytes(input.runtime().resolve("runtime.json")));
        need(input.machine_id().equals(text(runtime,"machine_id"))&&Path.of(text(runtime,"repo_root")).equals(input.repo_root()),
                "actual runtime machine/repository binding");
        List<String> command=input.argv();boolean delegated=input.timeout_seconds()==null;
        if(delegated){
            Path entry=input.runtime().resolve("source/tools/ck3_mod_acceptance.py");int found=-1;
            for(int i=0;i<command.size();i++){
                try{if(Path.of(command.get(i)).toAbsolutePath().normalize().equals(entry))found=i;}
                catch(java.nio.file.InvalidPathException invalid){/* Not a path selector. */ }
            }
            need(found>=0&&found+1<command.size()&&List.of("allocate","run").contains(command.get(found+1)),
                    "only this runtime public allocate/run delegates original case supervision");
        }
        if(!List.of("java","javac","python").contains(command.getFirst()))
            need(Path.of(command.getFirst()).toAbsolutePath().normalize().equals(Path.of(text(runtime,"python")).toAbsolutePath().normalize()),
                    "exact existing runtime Python executable");
        Path own=input.output_root();String label=input.label();
        Path stdout=own.resolve(label+".stdout.log"),stderr=own.resolve(label+".stderr.log"),
                receipt=own.resolve(label+".original-wait.actual.json"),startedFile=own.resolve(label+".started.json");
        need(!Files.exists(stdout)&&!Files.exists(stderr)&&!Files.exists(receipt)&&!Files.exists(startedFile),"never replay existing command");
        Files.createFile(stdout);Files.createFile(stderr);Instant start=Instant.now();long clock=System.nanoTime();
        ProcessBuilder builder=new ProcessBuilder(command).directory(input.repo_root().toFile()).redirectOutput(stdout.toFile()).redirectError(stderr.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1");builder.environment().put("PYTHONIOENCODING","utf-8");
        Process process=builder.start();
        ObjectNode fact=JSON.createObjectNode().put("schema","xar.resume-original-command-wait.v1")
                .put("machine_id",input.machine_id()).put("source_HEAD",input.source_HEAD()).put("pid",process.pid())
                .put("cwd",input.repo_root().toString()).put("started_at_utc",start.toString());
        fact.set("argv",JSON.valueToTree(command));fact.set("request",pin(request));
        fact.put("timeout_scope",delegated?"Frozen public run owns its validated case budgets and shutdown":"Bounded non-Game operator command");
        write(startedFile,fact);System.out.println(JSON.writeValueAsString(fact));
        boolean complete;
        if(delegated){process.waitFor();complete=true;}else complete=process.waitFor(input.timeout_seconds(),TimeUnit.SECONDS);
        if(!complete){process.descendants().forEach(child->child.destroyForcibly());process.destroyForcibly();}
        int exit=process.waitFor();
        fact.put("exit_code",exit).put("actual_original_popen_wait",true).put("timed_out",!complete)
                .put("capture_implementation","Java ProcessBuilder and original Process.waitFor")
                .put("finished_at_utc",Instant.now().toString()).put("elapsed_seconds",(System.nanoTime()-clock)/1_000_000_000.0);
        fact.set("stdout",pin(stdout));fact.set("stderr",pin(stderr));write(receipt,fact);
        System.out.println(JSON.writeValueAsString(fact));return complete?exit:124;
    }
    public static void main(String[] args)throws Exception {
        need(args.length==1,"one unique explicit recorder request");System.exit(execute(Path.of(args[0])));
    }
}
