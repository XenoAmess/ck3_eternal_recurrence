import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;
import java.util.TreeMap;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.zip.GZIPOutputStream;
import java.util.zip.GZIPInputStream;

/** Configured source-only continuation; delegates complete capacity accounting and never publishes. */
public final class SourceContinuationCapacity {
 private SourceContinuationCapacity(){}
 public static final String SCHEMA="xar.source-continuation-capacity.v1";
 static final com.fasterxml.jackson.databind.ObjectMapper JSON=Source98Authority20261029A02.JSON;
 static final long CORE=8589934592L,NATIVE=536870912L,SOURCE=16777216L,GIT=33554432L,RECEIPT=131072L,OWN_LIMIT=4194304L;
 static final List<String> POINTERS=List.of("active_core_game_admission","active_scoped_admission","active_finite_quota_exception","active_root_mapping_addendum");
 static final List<String> UNCHANGED=List.of("ck3_autonomous_player/src","ck3_autonomous_player/native_bridge","mod_dynastic_esotericism/tools/src","java/ck3-save-core");
 public enum Mode { SOURCE_ONLY_CANDIDATE, ADOPTED_SOURCE_ONLY }
 public record Config(String schema,String machine_id,String source_HEAD,String source_root,F15ReadOnlyBuildBudget20261029.Pin prior_authority,F15ReadOnlyBuildBudget20261029.Pin source_facts,F15ReadOnlyBuildBudget20261029.Pin build_code_qualification,F15ReadOnlyBuildBudget20261029.Pin runtime,F15ReadOnlyBuildBudget20261029.Pin new_authority_candidate,Mode mode,long minimum_next_write_bytes,long full_window_seconds,List<F15ReadOnlyBuildBudget20261029.Pin> immutable_guards){
  public Config{immutable_guards=List.copyOf(immutable_guards);}
 }
 public record SourceBinding(String machine_id,String source_HEAD,String prior_source_HEAD,String source_root){
  public SourceBinding{need(machine_id!=null&&!machine_id.isBlank()&&source_HEAD!=null&&source_HEAD.matches("[0-9a-f]{40}")&&prior_source_HEAD!=null&&prior_source_HEAD.matches("[0-9a-f]{40}"),"Explicit machine/current/prior source");absolute(source_root);}
 }
 public record SourceFacts(String schema,String machine_id,String source_HEAD,String prior_source_HEAD,String source_root,String observed_at_utc,List<SourceSuccessorBuildAdmission.Change> changed_files,List<SourceSuccessorBuildAdmission.GitWait> original_git_waits,List<F15ReadOnlyBuildBudget20261029.Pin> code,F15ReadOnlyBuildBudget20261029.Pin inherited_code,boolean working_tree_clean,boolean native_and_sdk_and_builder_unchanged,boolean Game_execution_admitted){
  public SourceFacts{changed_files=List.copyOf(changed_files);original_git_waits=List.copyOf(original_git_waits);code=List.copyOf(code);}
 }
 public record OriginalWait(String schema,String machine_id,String source_HEAD,List<String> argv,long pid,String started_at_utc,String finished_at_utc,int exit_code,boolean timed_out,boolean actual_original_Process_waitFor,F15ReadOnlyBuildBudget20261029.Pin stdout,F15ReadOnlyBuildBudget20261029.Pin stderr){public OriginalWait{argv=List.copyOf(argv);}}
 public record FactsEvidence(String schema,String machine_id,String source_HEAD,F15ReadOnlyBuildBudget20261029.Pin source_facts,F15ReadOnlyBuildBudget20261029.Pin build_code_qualification,OriginalWait original_wait){}
 public record CapacityReceipt(String schema,String machine_id,String source_HEAD,F15ReadOnlyBuildBudget20261029.Pin authority,F15ReadOnlyBuildBudget20261029.Pin source_facts,boolean passed,boolean adopted,String observed_at_utc,String hard_deadline_utc,F15ReadOnlyBuildBudget20261029.Pin canonical_pin,F15ReadOnlyBuildBudget20261029.Pin helper,long minimum_next_write_bytes,long full_window_seconds,boolean Game_execution_admitted,long reservation_delta_bytes,long physical_credit_bytes,JsonNode scope,JsonNode core_pool,JsonNode native_pool,F15ReadOnlyBuildBudget20261029.SourceDelta source_delta,JsonNode dual_volume_capacity,JsonNode conservative_OS_policy,F15ReadOnlyBuildBudget20261029.Pin actual_collector_original_wait_gzip,long actual_collector_original_wait_raw_bytes,String actual_collector_original_wait_raw_sha256,F15ReadOnlyBuildBudget20261029.Pin facts_evidence,F15ReadOnlyBuildBudget20261029.Pin configuration){}
 static void need(boolean b,String why){if(!b)throw new IllegalArgumentException(why);}
 static Path absolute(String s){need(s!=null,"Explicit path");Path p=Path.of(s);need(p.isAbsolute()&&p.normalize().equals(p),"Normalized absolute path");return p;}
 static Path own()throws Exception{return Path.of(SourceContinuationCapacity.class.getProtectionDomain().getCodeSource().getLocation().toURI()).getParent().getParent();}
 static Path self()throws Exception{return own().resolve("src/main/java/SourceContinuationCapacity.java");}
 static F15ReadOnlyBuildBudget20261029.Pin pin(Path p)throws Exception{return F15ReadOnlyBuildBudget20261029.filePin(p);}
 static void verify(F15ReadOnlyBuildBudget20261029.Pin p)throws Exception{F15ReadOnlyBuildBudget20261029.verify(p);}
 static JsonNode read(F15ReadOnlyBuildBudget20261029.Pin p,int n)throws Exception{return Source98Authority20261029A02.read(p,n);}
 static F15ReadOnlyBuildBudget20261029.Pin parsed(JsonNode n)throws Exception{return Source98Successor20261029A01.parsed(n);}
 static long number(JsonNode n){return Source98Successor20261029A01.integer(n);}
 static String text(JsonNode n){return Source98Successor20261029A01.text(n);}
 static boolean bool(JsonNode n){need(n!=null&&n.isBoolean(),"Exact boolean");return n.booleanValue();}
 static CapacityReceipt receipt(JsonNode n)throws Exception{
  var fields=new TreeSet<String>();for(var c:CapacityReceipt.class.getRecordComponents())fields.add(c.getName());exact(n,fields);
  for(String k:List.of("scope","core_pool","native_pool","source_delta","conservative_OS_policy"))need(n.get(k)!=null&&n.get(k).isObject(),"Exact policy object "+k);need(n.get("dual_volume_capacity").isArray()&&n.get("dual_volume_capacity").size()==2,"Exact original paired volume array");
  return new CapacityReceipt(text(n.get("schema")),text(n.get("machine_id")),text(n.get("source_HEAD")),parsed(n.get("authority")),parsed(n.get("source_facts")),bool(n.get("passed")),bool(n.get("adopted")),text(n.get("observed_at_utc")),text(n.get("hard_deadline_utc")),parsed(n.get("canonical_pin")),parsed(n.get("helper")),number(n.get("minimum_next_write_bytes")),number(n.get("full_window_seconds")),bool(n.get("Game_execution_admitted")),number(n.get("reservation_delta_bytes")),number(n.get("physical_credit_bytes")),n.get("scope"),n.get("core_pool"),n.get("native_pool"),Source98Successor20261029A01.typed(n.get("source_delta"),F15ReadOnlyBuildBudget20261029.SourceDelta.class),n.get("dual_volume_capacity"),n.get("conservative_OS_policy"),parsed(n.get("actual_collector_original_wait_gzip")),number(n.get("actual_collector_original_wait_raw_bytes")),text(n.get("actual_collector_original_wait_raw_sha256")),parsed(n.get("facts_evidence")),parsed(n.get("configuration")));
 }
 static <T>T typed(JsonNode n,Class<T> c)throws Exception{if(c==CapacityReceipt.class)return c.cast(receipt(n));return Source98Successor20261029A01.typed(n,c);}
 static void put(ObjectNode n,String k,Object v){n.set(k,JSON.valueToTree(v));}
 static boolean same(F15ReadOnlyBuildBudget20261029.Pin a,F15ReadOnlyBuildBudget20261029.Pin b){return F15ReadOnlyBuildBudget20261029.same(a,b);}
 static byte[] bytes(Object n)throws Exception{return JSON.writeValueAsBytes(n);}
 static String hash(byte[] n)throws Exception{return Source98Successor20261029A01.hash(n);}
 static void flags(JsonNode n,String k,boolean value)throws Exception{Source98Successor20261029A01.flag(n,k,value);}
 static void exact(JsonNode n,Set<String> keys){need(n!=null&&n.isObject(),"Object required");Set<String> actual=new TreeSet<>();n.fieldNames().forEachRemaining(actual::add);need(actual.equals(keys),"Missing or unknown field");}
 static Path storageRoot()throws Exception{Path p=own();return p.getParent().getFileName().toString().equals("capacity-support")?p.getParent():p;}
 static long used()throws Exception{long sum=0;try(var paths=Files.walk(storageRoot())){for(Path p:paths.toList())sum=Math.addExact(sum,Files.isDirectory(p)?4096:Math.max(4096,(Files.size(p)+4095)/4096*4096));}return sum;}
 static void create(Path p,Object n,int limit)throws Exception{createBytes(p,bytes(n),limit);}
 static void createBytes(Path p,byte[] raw,int limit)throws Exception{need(p.isAbsolute()&&p.normalize().equals(p)&&p.startsWith(own())&&!Files.exists(p)&&raw.length<=limit&&used()+raw.length+RECEIPT<=OWN_LIMIT,"Unique bounded4MiB support output");Files.write(p,raw,StandardOpenOption.CREATE_NEW);}
 public static Config config(F15ReadOnlyBuildBudget20261029.Pin ref)throws Exception{
  JsonNode n=read(ref,65536);exact(n,Set.of("schema","machine_id","source_HEAD","source_root","prior_authority","source_facts","build_code_qualification","runtime","new_authority_candidate","mode","minimum_next_write_bytes","full_window_seconds","immutable_guards"));
  for(String k:List.of("machine_id","source_HEAD","source_root","schema","mode"))text(n.get(k));
  var r=new Config(text(n.get("schema")),text(n.get("machine_id")),text(n.get("source_HEAD")),text(n.get("source_root")),parsed(n.get("prior_authority")),parsed(n.get("source_facts")),parsed(n.get("build_code_qualification")),n.get("runtime").isNull()?null:parsed(n.get("runtime")),n.get("new_authority_candidate").isNull()?null:parsed(n.get("new_authority_candidate")),Mode.valueOf(text(n.get("mode"))),number(n.get("minimum_next_write_bytes")),number(n.get("full_window_seconds")),F15ReadOnlyBuildBudget20261029.pins(n.get("immutable_guards")));
  need(r.schema().equals("xar.source-continuation-capacity-config.v1")&&r.source_HEAD().matches("[0-9a-f]{40}")&&!r.machine_id().isBlank(),"Exact generic capacity configuration");absolute(r.source_root());caller(r.minimum_next_write_bytes());need(r.full_window_seconds()<=19920,"No window above original full Core19920");return r;
 }
 static void caller(long n){need(n>=0&&n<=CORE-RECEIPT,"Caller and receipt inside unchanged Core cap");}
 public static void window(Instant now,Instant deadline,long seconds){need(seconds>=0&&seconds<=19920&&now.isBefore(deadline)&&(seconds==0||now.plusSeconds(seconds).isBefore(deadline)),"Full requested unchanged window must fit strictly before original deadline");}
 static void policy(JsonNode c,String machine)throws Exception{
  need(text(c.get("machine_id")).equals(machine)&&number(c.get("fixed_core_pool_total_limit_bytes"))==CORE&&number(c.get("fixed_native_pool_total_limit_bytes"))==NATIVE&&number(c.get("source_git_increment_limit_bytes"))==SOURCE&&Instant.parse(text(c.get("hard_deadline_utc"))).equals(C35Source98Inventory200k20261030A01.END)&&text(c.get("quota_review_at_utc")).equals(text(c.get("hard_deadline_utc"))),"Unchanged inherited machine/Core8GiB/Native512MiB/source16MiB/18Z terms");
  need(number(c.get("finite_inventory_work_limit"))==200000&&number(c.get("inventory_scan_timeout_seconds"))==120,"Unchanged full200k/120s/unknown-tail contract");flags(c,"inventory_unknown_still_rejected",true);flags(c,"Game_execution_admitted",false);
 }
 static List<F15ReadOnlyBuildBudget20261029.Pin> code()throws Exception{
  var refs=new ArrayList<F15ReadOnlyBuildBudget20261029.Pin>();refs.add(pin(own().resolve("pom.xml")));try(var paths=Files.walk(own().resolve("src/main/java"))){for(Path p:paths.filter(Files::isRegularFile).sorted().toList())refs.add(pin(p));}try(var paths=Files.walk(own().resolve("target/classes"))){for(Path p:paths.filter(Files::isRegularFile).sorted().toList())refs.add(pin(p));}return List.copyOf(refs);
 }
 static List<F15ReadOnlyBuildBudget20261029.Pin> qualification(F15ReadOnlyBuildBudget20261029.Pin q)throws Exception{
  JsonNode n=read(q,262144);if(text(n.get("schema")).equals("xar.source-successor-qualified-build-support.v1")){need(number(n.get("strict_maven_compile_exit"))==0&&number(n.get("pure_checks_exit"))==0,"Original qualified facts producer");}
  else{need(text(n.get("schema")).equals("xar.source-continuation-capacity-qualified-code.v1"),"Explicit qualified generic facts producer");flags(n,"strict_maven_compile_passed",true);flags(n,"pure_passed",true);}
  var refs=F15ReadOnlyBuildBudget20261029.pins(n.get("code"));for(var p:refs)verify(p);var inherited=parsed(n.get("inherited_C35_code"));JsonNode index=read(inherited,262144);need(System.getProperty("java.class.path").endsWith(text(index.get("classpath"))),"Exact inherited qualified classpath tail and order");var dependencies=F15ReadOnlyBuildBudget20261029.pins(index.get("files"));need(dependencies.size()<=4096&&!dependencies.isEmpty(),"Finite complete inherited executable index");for(var p:dependencies)verify(p);return refs;
 }
 static String git(SourceBinding b,List<SourceSuccessorBuildAdmission.GitWait> waits,String... args)throws Exception{
  var argv=new ArrayList<String>(List.of("git","--no-optional-locks","-c","gc.auto=0","-c","maintenance.auto=false"));argv.addAll(List.of(args));Instant start=Instant.now();ProcessBuilder pb=new ProcessBuilder(argv).directory(absolute(b.source_root()).toFile());pb.environment().put("GIT_OPTIONAL_LOCKS","0");pb.environment().put("GIT_NO_LAZY_FETCH","1");
  Process child=pb.start();var output=new java.util.concurrent.atomic.AtomicReference<byte[]>();var error=new java.util.concurrent.atomic.AtomicReference<byte[]>();Thread a=Thread.ofVirtual().start(()->{try{output.set(child.getInputStream().readNBytes(262145));}catch(java.io.IOException e){output.set(new byte[262145]);}}),e=Thread.ofVirtual().start(()->{try{error.set(child.getErrorStream().readNBytes(32769));}catch(java.io.IOException x){error.set(new byte[32769]);}});
  child.getOutputStream().close();boolean done=child.waitFor(30,TimeUnit.SECONDS);if(!done){child.destroyForcibly();child.waitFor();}a.join();e.join();byte[] raw=output.get();need(raw!=null&&error.get()!=null,"Complete actual Git streams");waits.add(new SourceSuccessorBuildAdmission.GitWait(argv,child.pid(),child.exitValue(),!done,start.toString(),Instant.now().toString(),raw.length,hash(raw)));need(done&&child.exitValue()==0&&raw.length<=262144&&error.get().length<=32768,"Actual bounded original Git wait0");return new String(raw,StandardCharsets.UTF_8).strip();
 }
 static void identity(SourceBinding b,List<SourceSuccessorBuildAdmission.GitWait> waits)throws Exception{
  need(b.machine_id().equals(ExactClosedLeafCleanup20261027CandidateA03.Win.machine()),"Actual configured execution machine");
  need(git(b,waits,"rev-parse","HEAD").equals(b.source_HEAD())&&git(b,waits,"status","--porcelain").isBlank(),"Exact current configured clean source");git(b,waits,"merge-base","--is-ancestor",b.prior_source_HEAD(),b.source_HEAD());
  for(String tree:UNCHANGED)need(git(b,waits,"rev-parse",b.prior_source_HEAD()+":"+tree).equals(git(b,waits,"rev-parse",b.source_HEAD()+":"+tree)),"Original unchanged native/SDK/builder/save tree: "+tree);
 }
 public static SourceFacts produceFacts(SourceBinding b,F15ReadOnlyBuildBudget20261029.Pin qualifiedCode)throws Exception{
  var qualified=qualification(qualifiedCode);need(qualified.equals(code()),"Actual configured generic producer class/source closure");var waits=new ArrayList<SourceSuccessorBuildAdmission.GitWait>();identity(b,waits);var changes=new ArrayList<SourceSuccessorBuildAdmission.Change>();
  for(String name:git(b,waits,"diff","--name-only","--no-renames",b.prior_source_HEAD(),b.source_HEAD()).split("\\R"))if(!name.isBlank()){
   Path p=absolute(b.source_root()).resolve(name).normalize();need(p.startsWith(absolute(b.source_root()))&&!Files.isSymbolicLink(p),"Exact current source leaf");String blob=git(b,waits,"rev-parse",b.source_HEAD()+":"+name),old=git(b,waits,"ls-tree",b.prior_source_HEAD(),"--",name);
   need(git(b,waits,"hash-object","--no-filters",p.toString()).equals(blob),"Actual body equals selected current Git blob");changes.add(new SourceSuccessorBuildAdmission.Change(name,new SourceSuccessorBuildAdmission.PriorBlob(!old.isBlank(),old.isBlank()?"":old.split("\\s+")[2]),blob,pin(p)));
  }
  need(!changes.isEmpty()&&changes.size()<=64,"Finite full changed-path list");identity(b,waits);JsonNode q=read(qualifiedCode,262144);return new SourceFacts("xar.source-continuation-facts.v1",b.machine_id(),b.source_HEAD(),b.prior_source_HEAD(),b.source_root(),Instant.now().toString(),changes,waits,qualified,parsed(q.get("inherited_C35_code")),true,true,false);
 }
 static SourceFacts consumeGenericFacts(String machine,String head,F15ReadOnlyBuildBudget20261029.Pin facts,F15ReadOnlyBuildBudget20261029.Pin qualified)throws Exception{
  SourceFacts f=typed(read(facts,262144),SourceFacts.class);need(f.schema().equals("xar.source-continuation-facts.v1")&&f.machine_id().equals(machine)&&f.source_HEAD().equals(head)&&f.working_tree_clean()&&f.native_and_sdk_and_builder_unchanged()&&!f.Game_execution_admitted(),"Exact configured generic actual source facts");
  need(f.code().equals(qualification(qualified)),"Same actual facts producer qualification");verify(f.inherited_code());need(!f.original_git_waits().isEmpty()&&f.original_git_waits().size()<=1000,"Complete finite actual Git waits");for(var w:f.original_git_waits())need(w.pid()>0&&w.exit_code()==0&&!w.timed_out()&&!w.argv().isEmpty()&&w.argv().getFirst().equals("git")&&w.stdout_bytes()>=0&&w.stdout_sha256().matches("[0-9a-f]{64}")&&!Instant.parse(w.finished_at_utc()).isBefore(Instant.parse(w.started_at_utc())),"Actual original Git producer waits0");SourceBinding b=new SourceBinding(machine,head,f.prior_source_HEAD(),f.source_root());var waits=new ArrayList<SourceSuccessorBuildAdmission.GitWait>();identity(b,waits);Set<String> actual=new TreeSet<>(List.of(git(b,waits,"diff","--name-only","--no-renames",b.prior_source_HEAD(),head).split("\\R"))),claimed=new TreeSet<>();
  for(var c:f.changed_files()){need(claimed.add(c.relative_path())&&absolute(c.current_file().path()).equals(absolute(f.source_root()).resolve(c.relative_path()).normalize())&&absolute(c.current_file().path()).startsWith(absolute(f.source_root())),"Unique configured full changed paths");verify(c.current_file());String old=git(b,waits,"ls-tree",b.prior_source_HEAD(),"--",c.relative_path());need(c.before().equals(new SourceSuccessorBuildAdmission.PriorBlob(!old.isBlank(),old.isBlank()?"":old.split("\\s+")[2]))&&git(b,waits,"rev-parse",head+":"+c.relative_path()).equals(c.current_blob())&&git(b,waits,"hash-object","--no-filters",c.current_file().path()).equals(c.current_blob()),"Actual prior presence/new blob/current body");}
  need(!claimed.isEmpty()&&claimed.size()<=64&&actual.equals(claimed),"Complete actual diff, no omitted or extra source");identity(b,waits);return f;
 }
 static OriginalWait child(String machine,String head,List<String> argv,Path prefix,int timeout)throws Exception{
  need(prefix.isAbsolute()&&prefix.normalize().equals(prefix)&&prefix.startsWith(own()),"Bounded actual evidence in configured support Own");Path out=Path.of(prefix+".stdout.log"),err=Path.of(prefix+".stderr.log");need(!Files.exists(out)&&!Files.exists(err)&&used()+524288+RECEIPT<=OWN_LIMIT,"Fresh child evidence and finite peak");
  Instant started=Instant.now();ProcessBuilder pb=new ProcessBuilder(argv).directory(own().toFile());for(String k:List.of("TEMP","TMP","TMPDIR"))pb.environment().put(k,own().resolve("tmp").toString());pb.environment().put("GIT_OPTIONAL_LOCKS","0");pb.environment().put("PYTHONDONTWRITEBYTECODE","1");pb.redirectOutput(out.toFile()).redirectError(err.toFile());Process process=pb.start();process.getOutputStream().close();boolean done=process.waitFor(timeout,TimeUnit.SECONDS);if(!done){process.destroyForcibly();process.waitFor();}
  OriginalWait w=new OriginalWait("xar.source-continuation-original-wait.v1",machine,head,argv,process.pid(),started.toString(),Instant.now().toString(),process.exitValue(),!done,true,pin(out),pin(err));create(Path.of(prefix+".original-wait.json"),w,16384);need(done&&w.exit_code()==0&&w.stdout().bytes()<=262144&&w.stderr().bytes()<=65536,"Actual bounded original Process.waitFor0; failed evidence preserved");return w;
 }
 public static FactsEvidence consumeFacts(String machineId,String sourceHead,F15ReadOnlyBuildBudget20261029.Pin sourceFacts,F15ReadOnlyBuildBudget20261029.Pin buildCodeQualification,Path evidencePrefix)throws Exception{
  JsonNode f=read(sourceFacts,262144);need(text(f.get("machine_id")).equals(machineId)&&text(f.get("source_HEAD")).equals(sourceHead),"Expected caller machine and source facts");qualification(buildCodeQualification);
  List<String> argv=new ArrayList<>(List.of(Path.of(System.getProperty("java.home"),"bin/java.exe").toString(),"--enable-native-access=ALL-UNNAMED","-XX:-UsePerfData","-Djava.io.tmpdir="+own().resolve("tmp")));
  if(text(f.get("schema")).equals("xar.source-successor-build-facts.v1")){
   JsonNode q=read(buildCodeQualification,262144);need(text(q.get("schema")).equals("xar.source-successor-qualified-build-support.v1")&&F15ReadOnlyBuildBudget20261029.pins(f.get("code")).equals(F15ReadOnlyBuildBudget20261029.pins(q.get("code"))),"Exact original facts/qualification branch");Path first=null;for(var p:F15ReadOnlyBuildBudget20261029.pins(q.get("code")))if(Path.of(p.path()).getFileName().toString().equals("SourceSuccessorBuildAdmission.class"))first=Path.of(p.path()).getParent();need(first!=null,"Original facts consumer class root");JsonNode inherited=read(parsed(f.get("inherited_code")),262144);argv.addAll(List.of("-cp",first+";"+text(inherited.get("classpath")),own().resolve("src/main/java/SourceFactsReadOnlyBridge.java").toString(),sourceFacts.path(),Long.toString(sourceFacts.bytes()),sourceFacts.sha256()));
  }else{need(text(f.get("schema")).equals("xar.source-continuation-facts.v1"),"Explicit generic facts branch");argv.addAll(List.of("-cp",System.getProperty("java.class.path"),SourceContinuationCapacity.class.getName(),"--consume-generic-facts",machineId,sourceHead,sourceFacts.path(),Long.toString(sourceFacts.bytes()),sourceFacts.sha256(),buildCodeQualification.path(),Long.toString(buildCodeQualification.bytes()),buildCodeQualification.sha256()));}
  OriginalWait wait=child(machineId,sourceHead,argv,evidencePrefix,180);verify(sourceFacts);verify(buildCodeQualification);JsonNode returned=read(wait.stdout(),262144);need(Arrays.equals(canonical(returned),canonical(f)),"Exact verified facts roundtrip from independent original consumer");return new FactsEvidence("xar.source-continuation-facts-evidence.v1",machineId,sourceHead,sourceFacts,buildCodeQualification,wait);
 }
 static JsonNode ordered(JsonNode n){if(n.isObject()){ObjectNode out=JSON.createObjectNode();var names=new TreeSet<String>();n.fieldNames().forEachRemaining(names::add);for(String k:names)out.set(k,ordered(n.get(k)));return out;}if(n.isArray()){ArrayNode a=JSON.createArrayNode();for(JsonNode x:n)a.add(ordered(x));return a;}return n;}
 public static byte[] canonical(JsonNode n)throws Exception{return bytes(ordered(n));}
 static void replaceRoles(ObjectNode n,F15ReadOnlyBuildBudget20261029.Pin from,F15ReadOnlyBuildBudget20261029.Pin to)throws Exception{
  for(String k:POINTERS){need(same(parsed(n.get(k)),from),"Exact four current authority roles");put(n,k,to);}int core=0,nativeClosed=0;
  for(JsonNode x:n.path("claims")){ObjectNode row=(ObjectNode)x;String id=text(row.get("task_id"));if(id.equals("ck3-des-core-a30-20261027")){need(same(parsed(row.get("admission")),from),"Exact Core authority");put(row,"admission",to);core++;}else if(id.equals("ck3-des-native-r27-repair-20261027")){need(same(parsed(row.get("closed_with")),from),"Exact already-closed Native authority");put(row,"closed_with",to);nativeClosed++;}}
  need(core==1&&nativeClosed==1,"Exact unique Core and closed Native roles");
 }
 public static ObjectNode replaceAuthority(ObjectNode before,F15ReadOnlyBuildBudget20261029.Pin oldPin,F15ReadOnlyBuildBudget20261029.Pin newPin)throws Exception{
  need(!same(oldPin,newPin),"New explicit authority Pin");C35Source98Inventory200k20261030A01.ledger(before,oldPin);ObjectNode after=before.deepCopy();replaceRoles(after,oldPin,newPin);long registry=number(before.get("capacity_registry_revision")),storage=number(before.get("storage_revision"));after.put("capacity_registry_revision",Math.addExact(registry,1)).put("storage_revision",Math.addExact(storage,1));C35Source98Inventory200k20261030A01.ledger(after,newPin);
  ObjectNode reverse=after.deepCopy();replaceRoles(reverse,newPin,oldPin);reverse.put("capacity_registry_revision",registry).put("storage_revision",storage);need(Arrays.equals(canonical(reverse),canonical(before)),"Canonical JSON reverse proof preserves all remaining ledger fields");return after;
 }
 public static ObjectNode authorityCandidate(Config b,F15ReadOnlyBuildBudget20261029.Pin qualifiedSupport)throws Exception{
  ObjectNode old=(ObjectNode)read(b.prior_authority(),65536);policy(old,b.machine_id());need(qualification(qualifiedSupport).equals(code()),"Actual shared support qualified code");ObjectNode c=old.deepCopy();c.put("schema","xar.core-source-continuation-source-only-admission.v1").put("source_HEAD",b.source_HEAD());put(c,"previous_source_authority",b.prior_authority());put(c,"source_facts",b.source_facts());put(c,"source_continuation_build_code_qualification",b.build_code_qualification());put(c,"source_continuation_capacity_qualification",qualifiedSupport);put(c,"source_continuation_runtime",b.runtime());c.put("source_root",b.source_root()).put("source_continuation_scope","SOURCE_ONLY_NO_GAME_NO_RESERVATION_CHANGE");put(c,"helper",pin(self()));return c;
 }
 static F15ReadOnlyBuildBudget20261029.Pin authority(Config b)throws Exception{
  if(b.mode()==Mode.SOURCE_ONLY_CANDIDATE)return b.prior_authority();need(b.new_authority_candidate()!=null,"Actual adopted authority required");ObjectNode c=(ObjectNode)read(b.new_authority_candidate(),65536);policy(c,b.machine_id());need(text(c.get("schema")).equals("xar.core-source-continuation-source-only-admission.v1"),"Explicit generic source-only selected authority");need(text(c.get("source_HEAD")).equals(b.source_HEAD())&&same(parsed(c.get("source_facts")),b.source_facts())&&same(parsed(c.get("source_continuation_build_code_qualification")),b.build_code_qualification())&&same(parsed(c.get("previous_source_authority")),b.prior_authority())&&text(c.get("source_root")).equals(b.source_root()),"Actual selected new source-only authority");need(Arrays.equals(canonical(c),canonical(authorityCandidate(b,parsed(c.get("source_continuation_capacity_qualification"))))),"Complete inherited authority deepcopy plus exact source-only updates");return b.new_authority_candidate();
 }
 public static void validateFreshBinding(JsonNode fresh,String machineId,String sourceHead,F15ReadOnlyBuildBudget20261029.Pin authority,F15ReadOnlyBuildBudget20261029.Pin sourceFacts)throws Exception{
  CapacityReceipt r=typed(fresh,CapacityReceipt.class);need(r.schema().equals(SCHEMA)&&r.machine_id().equals(machineId)&&r.source_HEAD().equals(sourceHead)&&r.passed()&&r.adopted()&&same(r.authority(),authority)&&same(r.source_facts(),sourceFacts)&&!r.Game_execution_admitted()&&r.reservation_delta_bytes()==0&&r.physical_credit_bytes()==0,"Strict generic adopted fresh/machine/source/Pins/no Game");verify(r.helper());need(same(r.helper(),pin(self())),"Exact shared capacity helper");caller(r.minimum_next_write_bytes());
 }
 static void runtime(Config b)throws Exception{
  if(b.runtime()==null)return;JsonNode r=read(b.runtime(),2097152);need(text(r.get("machine_id")).equals(b.machine_id())&&Path.of(text(r.get("repo_root"))).equals(absolute(b.source_root())),"Exact runtime machine/configured source root");verify(parsed(r.get("manifest")));
 }
 public static void check(F15ReadOnlyBuildBudget20261029.Pin configuration,Path output)throws Exception{
  Config b=config(configuration);JsonNode prior=read(b.prior_authority(),65536);policy(prior,b.machine_id());Instant end=Instant.parse(text(prior.get("hard_deadline_utc")));window(Instant.now(),end,b.full_window_seconds());runtime(b);var authority=authority(b);var ledger=pin(C35Source98Inventory200k20261030A01.LEDGER);C35Source98Inventory200k20261030A01.ledger((ObjectNode)read(ledger,8192),authority);
  var refs=new ArrayList<>(b.immutable_guards());refs.addAll(qualification(b.build_code_qualification()));refs.addAll(List.of(configuration,b.prior_authority(),b.source_facts(),b.build_code_qualification()));refs.addAll(code());if(b.runtime()!=null)refs.add(b.runtime());if(b.new_authority_candidate()!=null)refs.add(b.new_authority_candidate());for(var p:refs)verify(p);
  try(var held=new FiniteSourceCapacitySuccessor20261029F15C.Leases(Source98Successor20261029A01.unique(refs))){
   Path evidence=Path.of(output+".facts");var verified=consumeFacts(b.machine_id(),b.source_HEAD(),b.source_facts(),b.build_code_qualification(),evidence);JsonNode facts=read(b.source_facts(),262144);need(text(facts.get("prior_source_HEAD")).equals(text(prior.get("source_HEAD"))),"Actual prior authority/source facts relation");if(facts.has("source_root"))need(text(facts.get("source_root")).equals(b.source_root()),"Configured facts source root");
   var base=F15ReadOnlyBuildBudget20261029.baseline();var names=new TreeSet<>(F15ReadOnlyBuildBudget20261029.sourceNames(base,refs));for(JsonNode x:facts.get("changed_files"))names.add(text(x.get("relative_path")));need(absolute(b.source_root()).equals(F15ReadOnlyBuildBudget20261029.REPO),"Existing shared sourceDelta root must match explicit configured root");var source=F15ReadOnlyBuildBudget20261029.sourceDelta(base,names);need(source.whole_git_upper_bytes()<=GIT,"Original whole Git32MiB");var original=C35CollectorLimit20261030A01.collect(names);var e=C35CollectorLimit20261030A01.evaluate(JSON.readTree(original.stdout()),source,0);need(number(e.fields().path("scope").get("remaining_headroom_bytes"))>=Math.addExact(b.minimum_next_write_bytes(),RECEIPT),"Caller plus full receipt inside original Core");Instant now=Instant.now();need(!e.observed().isAfter(now)&&now.isBefore(e.observed().plusSeconds(180)),"Actual strict180s observation");window(now,end,b.full_window_seconds());identity(new SourceBinding(b.machine_id(),b.source_HEAD(),text(prior.get("source_HEAD")),b.source_root()),new ArrayList<>());held.stable();verify(ledger);C35Source98Inventory200k20261030A01.ledger((ObjectNode)read(ledger,8192),authority);
   Path proof=Path.of(output+".facts-evidence.json");create(proof,verified,16384);byte[] raw=bytes(original);var compressed=new ByteArrayOutputStream();try(var zip=new GZIPOutputStream(compressed)){zip.write(raw);}Path archive=Path.of(output+".collector-original.json.gz");createBytes(archive,compressed.toByteArray(),98304);
   JsonNode v=e.fields();var receipt=new CapacityReceipt(SCHEMA,b.machine_id(),b.source_HEAD(),authority,b.source_facts(),true,b.mode()==Mode.ADOPTED_SOURCE_ONLY,e.observed().toString(),end.toString(),ledger,pin(self()),b.minimum_next_write_bytes(),b.full_window_seconds(),false,0,0,v.get("scope"),v.get("core_pool"),v.get("native_pool"),source,v.get("dual_volume_capacity"),v.get("conservative_OS_policy"),pin(archive),raw.length,hash(raw),pin(proof),configuration);create(output,receipt,32768);System.out.println(JSON.writeValueAsString(pin(output)));
  }
 }
 static F15ReadOnlyBuildBudget20261029.Pin arg(String[] a,int i){return new F15ReadOnlyBuildBudget20261029.Pin(a[i],Long.parseLong(a[i+1]),a[i+2]);}
 public static void main(String[] a)throws Exception{
  if(a.length==9&&a[0].equals("--consume-generic-facts")){consumeGenericFacts(a[1],a[2],arg(a,3),arg(a,6));System.out.write(Files.readAllBytes(Path.of(a[3])));return;}
  if(a.length==5&&a[0].equals("--check")){check(arg(a,1),Path.of(a[4]));return;}
  if(a.length==6&&a[0].equals("--facts")){var b=typed(JSON.readTree(Files.readAllBytes(Path.of(a[1]))),SourceBinding.class);create(Path.of(a[5]),produceFacts(b,arg(a,2)),262144);return;}
  
  throw new IllegalArgumentException("--facts BindingJSON QualifiedPin3 output | --check ConfigPin3 output; source-only/no CAS");
 }
}



