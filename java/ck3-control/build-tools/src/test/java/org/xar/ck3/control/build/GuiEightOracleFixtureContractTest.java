package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Pure constructor/argv/JSON boundary tests. Placeholder refs never qualify a child, origin or runtime. */
final class GuiEightOracleFixtureContractTest {
 @TempDir Path root;
 private FileRef placeholder(String name){return new FileRef(root.resolve(name).toString(),1,"0".repeat(64));}
 private GuiEightOracleFixture.Config constructorData(){
  var sources=new ArrayList<GuiEightOracleFixture.Source>();
  for(var source:GuiEightOracleFixture.requiredSources())sources.add(new GuiEightOracleFixture.Source(source.moduleName(),source.relativePath(),new FileRef(root.resolve(source.relativePath()).toString(),1,source.sha256())));
  return new GuiEightOracleFixture.Config(GuiEightOracleFixture.CONFIG_SCHEMA,"contract-test-machine",root.toString(),placeholder("not-executed-python.exe"),sources,30,256L<<20,Instant.now().plusSeconds(3600).toString());
 }
 @Test void oneTypedConfigHasExactlyThePinnedOriginalEighteenSourceRolesAndEightMethodNames()throws Exception {
  var config=constructorData();var json=GuiEightOracleFixture.encodeConfiguration(config);
  assertEquals(config,ControlBuild.strictMapper().readValue(json,GuiEightOracleFixture.Config.class));
  assertEquals(18,config.sources().size());assertEquals(8,GuiEightOracleFixture.Method.values().length);
  assertEquals(18,config.sources().stream().map(GuiEightOracleFixture.Source::moduleName).distinct().count());
  var missing=new ArrayList<>(config.sources());missing.removeLast();
  assertThrows(IllegalArgumentException.class,()->new GuiEightOracleFixture.Config(config.schema(),config.machineId(),config.repositoryRoot(),config.python(),missing,30,config.memoryLimitBytes(),config.reviewAtUtc()));
  var swapped=new ArrayList<>(config.sources());var first=swapped.getFirst();swapped.set(0,swapped.get(1));swapped.set(1,first);
  assertThrows(IllegalArgumentException.class,()->new GuiEightOracleFixture.Config(config.schema(),config.machineId(),config.repositoryRoot(),config.python(),swapped,30,config.memoryLimitBytes(),config.reviewAtUtc()));
  Path file=root.resolve("constructor-only.json");Files.write(file,json);assertThrows(Exception.class,()->GuiEightOracleFixture.readConfiguration(FileRef.measure(file)),"constructor data must not substitute for actual source/machine qualification");
 }
 @Test void actualCanonicalParserOwnsTheCompleteUtf8ArgvAndRoundtripsWithoutShellExecution()throws Exception {
  FileRef config=placeholder("config with spaces.json"),input=placeholder("case with spaces.json");Path state=root.resolve("data state");
  var invocation=GuiEightOracleFixture.invocation(config,input,state);
  assertEquals(CanonicalPythonInvocation.Mode.INLINE_SOURCE,invocation.mode());
  assertEquals(List.of("-B","-X","utf8"),invocation.interpreterArguments());
  assertEquals(List.of(config.path(),input.path(),state.toString()),invocation.arguments());
  assertEquals(invocation,CanonicalPythonInvocation.parse(invocation.originalCommand(),state));
  assertEquals(invocation,ControlBuild.strictMapper().readValue(ControlBuild.strictMapper().writeValueAsBytes(invocation),CanonicalPythonInvocation.Invocation.class));
  assertTrue(invocation.originalCommand().length()<16384);assertTrue(invocation.inlineSource().contains("base64"));
 }
 @Test void configBoundaryRejectsBooleanAndFloatResourceNumbersBeforeAnySourceOrProcess()throws Exception {
  var config=constructorData();
  for(String token:List.of("true","30.0","null")){
   String text=new String(GuiEightOracleFixture.encodeConfiguration(config),java.nio.charset.StandardCharsets.UTF_8);
   text=text.replace("\"timeout_seconds\":30","\"timeout_seconds\":"+token);
   Path file=root.resolve("bad-"+token+".json");Files.writeString(file,text);
   assertThrows(IllegalArgumentException.class,()->GuiEightOracleFixture.readConfiguration(FileRef.measure(file)));
  }
 }
}
