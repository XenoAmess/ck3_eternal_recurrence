package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.HashSet;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import static org.xar.ck3.control.build.GuiEightOracleFixture.*;

/** Narrow dynamic JSON boundary for the single GUI original fixture contract. */
final class GuiEightFixtureCodec {
 private GuiEightFixtureCodec() { }
 static Path absolute(String raw){require(raw!=null&&!raw.isBlank()&&raw.chars().noneMatch(c->c<32||c==127),"plain original path required");Path p=Path.of(raw);require(p.isAbsolute()&&p.equals(p.normalize()),"absolute normalized path required");return p;}
 private static byte[] bytes(FileRef ref)throws IOException {
  require(ref!=null&&ref.bytes()>0&&ref.bytes()<=(2L<<20),"bounded exact original material required");Path p=absolute(ref.path());SharedSourceFiles.plainAncestors(p);ref.verify();byte[] raw=Files.readAllBytes(p);ref.verify();require(raw.length==ref.bytes(),"original material length drift");return raw;
 }
 private static JsonNode object(FileRef ref,Set<String> names)throws IOException {
  JsonNode n=ControlBuild.strictMapper().readTree(bytes(ref));require(n.isObject(),"exact fixture object required");Set<String> actual=new HashSet<>();n.fieldNames().forEachRemaining(actual::add);require(actual.equals(names),"unknown or missing fixture field");return n;
 }
 private static void reference(JsonNode node){
  require(node!=null&&node.isObject()&&node.size()==3&&node.has("path")&&node.has("bytes")&&node.has("sha256")&&node.get("path").isTextual()&&node.get("sha256").isTextual(),"strict exact original FileRef required");
  integer(node.get("bytes"),1,Long.MAX_VALUE);
 }
 private static void method(JsonNode node){require(node!=null&&node.isTextual(),"exact public method string required");GuiEightOracleFixture.Method.valueOf(node.textValue());}
 private static void integer(JsonNode n,long minimum,long maximum){require(n!=null&&n.isIntegralNumber()&&n.canConvertToLong()&&n.longValue()>=minimum&&n.longValue()<=maximum,"strict bounded fixture integer required");}
 static Config configuration(FileRef ref)throws IOException {
  JsonNode n=object(ref,Set.of("schema","machine_id","repository_root","python","sources","timeout_seconds","memory_limit_bytes","review_at_utc"));
  integer(n.get("timeout_seconds"),1,120);integer(n.get("memory_limit_bytes"),64L<<20,1536L<<20);
  reference(n.get("python"));require(n.path("sources").isArray(),"exact source list required");for(JsonNode source:n.get("sources"))reference(source.get("original"));
  Config value=ControlBuild.strictMapper().treeToValue(n,Config.class);current(value);return value;
 }
 static Case caseInput(FileRef ref)throws IOException {
  JsonNode n=object(ref,Set.of("schema","method","arguments_ref","scenario_ref"));method(n.get("method"));reference(n.get("arguments_ref"));reference(n.get("scenario_ref"));Case value=ControlBuild.strictMapper().treeToValue(n,Case.class);
  JsonNode args=ControlBuild.strictMapper().readTree(bytes(value.argumentsRef())),scenario=ControlBuild.strictMapper().readTree(bytes(value.scenarioRef()));
  require(args.isObject()&&scenario.isObject()&&scenario.path("mode").isTextual()&&Set.of("faith","white_action","white_read","arguments").contains(scenario.path("mode").textValue()),"bounded original argument/scenario objects required");return value;
 }
 static void current(Config config)throws IOException {
  require(config.machineId().equals(WindowsJobProcess.currentMachineId())&&Instant.now().isBefore(Instant.parse(config.reviewAtUtc())),"current actual fixture machine/review required");Path repo=absolute(config.repositoryRoot()).toRealPath();config.python().verify();
  for(Source source:config.sources()){
   Path actual=absolute(source.original().path()).toRealPath(),expected=repo.resolve(source.relativePath()).normalize();
   require(expected.startsWith(repo)&&actual.equals(expected.toRealPath()),"original source crossed its declared actual repository");source.original().verify();
  }
 }
 static Path freshDataRoot(Path output)throws IOException {
  Path p=absolute(output.toString());SharedSourceFiles.plainAncestors(p);require(!Files.exists(p)&&Files.isDirectory(p.getParent()),"fresh fixture output with existing data-volume parent required");
  String system=System.getenv("SystemDrive");require(system!=null&&!p.getParent().toRealPath().getRoot().equals(Path.of(system+"/").toRealPath().getRoot()),"GUI original fixture output must use a data volume");return p;
 }
 static FileRef write(Path p,Object value,FreshSdkFixtureStage.ResourceGuard resources)throws IOException {
  byte[] raw=ControlBuild.strictMapper().writeValueAsBytes(value);require(raw.length>0&&raw.length<=(2L<<20),"finite original fixture document required");resources.revalidate(raw.length+4096L);SharedSourceFiles.plainAncestors(p);Files.write(p,raw,StandardOpenOption.CREATE_NEW);return FileRef.measure(p);
 }
 static Body produced(FileRef ref)throws IOException {
  JsonNode n=object(ref,Set.of("schema","machine_id","config_ref","case_ref","original_invocation","process_ref","body_ref"));for(String field:Set.of("config_ref","case_ref","process_ref","body_ref"))reference(n.get(field));Product product=ControlBuild.strictMapper().treeToValue(n,Product.class);
  require("xar.gui-eight-original-product/v1".equals(product.schema()),"exact original fixture product required");Config config=configuration(product.configRef());Case actual=caseInput(product.caseRef());
  require(config.machineId().equals(product.machineId()),"fixture product machine differs");Path parent=absolute(ref.path()).getParent();require(absolute(product.processRef().path()).equals(parent.resolve("process.json")),"fixture process role crossed");
  var run=ControlBuild.strictMapper().readValue(bytes(product.processRef()),CanonicalColdWarmStage.CommandActual.class);
  var expected=GuiEightOracleFixture.invocation(product.configRef(),product.caseRef(),parent.resolve("python-state"));
  require(run.state()==CanonicalColdWarmStage.CommandState.PASS&&run.result()!=null&&run.result().passed()&&run.invocation().equals(expected)&&product.originalInvocation().equals(expected)&&run.stdoutRef().equals(product.bodyRef())&&run.observation()!=null&&run.observation().exitCode()==0&&run.observation().error()==null,"actual canonical invocation/terminal/body binding required");
  Path processRoot=parent.resolve("process");
  require(absolute(run.inputRef().path()).equals(processRoot.resolve("input.json"))&&absolute(run.stdoutRef().path()).equals(processRoot.resolve("stdout.log"))&&absolute(run.stderrRef().path()).equals(processRoot.resolve("stderr.log"))&&absolute(run.observationRef().path()).equals(processRoot.resolve("observation.json")),"actual canonical child evidence roles differ");
  require(run.arguments().equals(CanonicalColdWarmStage.arguments(expected,CanonicalColdWarmStage.BootstrapMode.NONE,processRoot.resolve("input.json"))),"actual owned child argv differs");
  run.inputRef().verify();run.stdoutRef().verify();run.stderrRef().verify();run.observationRef().verify();
  var observation=ControlBuild.strictMapper().readValue(bytes(run.observationRef()),CanonicalColdWarmStage.Observation.class);
  require(observation.equals(run.observation())&&"xar.canonical-python-observation/v1".equals(observation.schema())&&observation.bootstrapMode()==CanonicalColdWarmStage.BootstrapMode.NONE&&observation.bootstrapEvidence()==null,"actual independent canonical observer differs");
  var input=ControlBuild.strictMapper().readValue(bytes(run.inputRef()),CanonicalColdWarmStage.PythonInput.class);
  require("xar.canonical-python-input/v1".equals(input.schema())&&input.invocation().equals(expected)&&input.bootstrapMode()==CanonicalColdWarmStage.BootstrapMode.NONE&&input.bootstrapRef()==null&&absolute(input.observationPath()).equals(absolute(run.observationRef().path())),"actual canonical observer input changed");
  JsonNode original=object(product.bodyRef(),Set.of("schema","method","arguments_ref","scenario_ref","origins","input_schema","answer"));
  method(original.get("method"));reference(original.get("arguments_ref"));reference(original.get("scenario_ref"));require(original.path("origins").isArray(),"actual origin array required");
  for(JsonNode origin:original.get("origins"))reference(origin.get("original"));
  Body body=ControlBuild.strictMapper().treeToValue(original,Body.class);
  require(body.method()==actual.method()&&body.argumentsRef().equals(actual.argumentsRef())&&body.scenarioRef().equals(actual.scenarioRef())&&body.origins().size()==config.sources().size(),"actual public method/material/origin closure differs");
  for(int i=0;i<config.sources().size();i++){Source source=config.sources().get(i);Origin origin=body.origins().get(i);require(origin.moduleName().equals(source.moduleName())&&origin.original().equals(source.original())&&absolute(origin.actualFile()).toRealPath().equals(absolute(source.original().path()).toRealPath()),"actual module __file__/original FileRef differs");}
  JsonNode answer=body.answer();require(answer.path("accepted").isBoolean(),"actual original outcome discriminant required");
  if(answer.get("accepted").booleanValue())require(answer.path("public").isObject()&&!answer.has("error"),"actual original result required");else require(answer.path("error").isTextual()&&answer.path("error_kind").isTextual()&&!answer.has("public"),"actual original fault required");
  current(config);product.caseRef().verify();ref.verify();return body;
 }
}
