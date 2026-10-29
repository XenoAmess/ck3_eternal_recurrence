package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.Base64;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** One Java producer for the original eight registered MCP paths, using the existing canonical owned process. */
public final class GuiEightOracleFixture {
 private GuiEightOracleFixture() { }
 public static final String PROPERTY="xar.gui.eight.oracle.config";
 public static final String CONFIG_SCHEMA="xar.gui-eight-original-config/v1",CASE_SCHEMA="xar.gui-eight-original-case/v1";
 public enum Method { ck3_open_faith_window_v1,ck3_present_faith_power_ui_v1,ck3_query_faith_power_ui_v1,ck3_query_faith_power_tooltip_v1,ck3_click_white_control_v1,ck3_click_white_numeric_control_v1,ck3_query_white_player_business_variables_v1,ck3_query_white_rendered_text_v1 }
 public record SourceSpec(String moduleName,String relativePath,String sha256) { }
 public record Source(String moduleName,String relativePath,FileRef original) {
  public Source { Objects.requireNonNull(moduleName);Objects.requireNonNull(relativePath);Objects.requireNonNull(original); }
 }
 public record Config(String schema,String machineId,String repositoryRoot,FileRef python,List<Source> sources,long timeoutSeconds,long memoryLimitBytes,String reviewAtUtc) {
  public Config {
   require(CONFIG_SCHEMA.equals(schema)&&machineId!=null&&machineId.matches("[a-z0-9][a-z0-9-]{0,63}")&&!machineId.equals("unknown"),"exact GUI original config machine/schema required");
   GuiEightFixtureCodec.absolute(repositoryRoot);Objects.requireNonNull(python);sources=List.copyOf(sources);
   require(timeoutSeconds>=1&&timeoutSeconds<=120&&memoryLimitBytes>=(64L<<20)&&memoryLimitBytes<=(1536L<<20),"bounded original process required");Instant.parse(reviewAtUtc);
   require(sources.size()==requiredSources().size(),"complete exact original source set required");
   for(int i=0;i<sources.size();i++){Source a=sources.get(i);SourceSpec b=requiredSources().get(i);require(a.moduleName().equals(b.moduleName())&&a.relativePath().equals(b.relativePath())&&a.original().sha256().equals(b.sha256()),"original source role/order/SHA differs");}
  }
 }
 public record Case(String schema,Method method,FileRef argumentsRef,FileRef scenarioRef) {
  public Case { require(CASE_SCHEMA.equals(schema),"exact GUI case schema required");Objects.requireNonNull(method);Objects.requireNonNull(argumentsRef);Objects.requireNonNull(scenarioRef); }
 }
 public record Origin(String moduleName,FileRef original,String actualFile) { }
 public record Body(String schema,Method method,FileRef argumentsRef,FileRef scenarioRef,List<Origin> origins,JsonNode inputSchema,JsonNode answer) {
  public Body { require("xar.gui-eight-original-body/v1".equals(schema),"exact original body schema required");Objects.requireNonNull(method);Objects.requireNonNull(argumentsRef);Objects.requireNonNull(scenarioRef);origins=List.copyOf(origins);require(inputSchema!=null&&inputSchema.isObject()&&answer!=null&&answer.isObject(),"actual registered schema and original outcome required"); }
 }
 public record Product(String schema,String machineId,FileRef configRef,FileRef caseRef,CanonicalPythonInvocation.Invocation originalInvocation,FileRef processRef,FileRef bodyRef) { }
 public static List<SourceSpec> requiredSources() { return List.of(new SourceSpec("xar_autoplayer.bridge.native_driver","ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py","eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603"),new SourceSpec("xar_autoplayer.bridge.mcp_server","ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py","b7569231226484b0bdd98c40ace14a82672b2138a0aab77711e559a4d9b8ccbc"),new SourceSpec("xar_autoplayer.bridge.service","ck3_autonomous_player/src/xar_autoplayer/bridge/service.py","a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e"),new SourceSpec("xar_autoplayer.bridge.ingame_ui_contract","ck3_autonomous_player/src/xar_autoplayer/bridge/ingame_ui_contract.py","74608d05074a48e1139a17fea360e34cf65cb01144d0a9a0e1dcf4ca49065ed4"),new SourceSpec("xar_autoplayer.bridge.religion_presentation_ui_contract","ck3_autonomous_player/src/xar_autoplayer/bridge/religion_presentation_ui_contract.py","af30af13603793d49952f5c6240c2755d8502913c2aa25e61e0f9a9b9759a0e5"),new SourceSpec("xar_autoplayer.bridge.clerical_preview_ui_contract","ck3_autonomous_player/src/xar_autoplayer/bridge/clerical_preview_ui_contract.py","61325fc2fc05ea7c6d15f96768141c70128f4958f865ec6786f90934fd58c370"),new SourceSpec("xar_autoplayer.bridge.white_control_action_driver","ck3_autonomous_player/src/xar_autoplayer/bridge/white_control_action_driver.py","9477daeb15d0901e74d80aa9a1bca4b027b64bbb2917115e1b1d95faa21abd6c"),new SourceSpec("xar_autoplayer.bridge.white_control_action_contract","ck3_autonomous_player/src/xar_autoplayer/bridge/white_control_action_contract.py","cb4b9ac3b9dbe73a9f74848b920506b108d8c96553bf62cdfc213f52b6c62027"),new SourceSpec("xar_autoplayer.bridge.white_numeric_control_action_driver","ck3_autonomous_player/src/xar_autoplayer/bridge/white_numeric_control_action_driver.py","869f12043503c61f96a2e5cded909b44cfef733ebec4d47ed95ce27aa9e7b036"),new SourceSpec("xar_autoplayer.bridge.white_numeric_control_action_contract","ck3_autonomous_player/src/xar_autoplayer/bridge/white_numeric_control_action_contract.py","8978437d2dc4c3dbb07c6b9582d8ea96408390e7f39367cc38f5b03c8e279e01"),new SourceSpec("xar_autoplayer.bridge.white_player_business_variables_contract","ck3_autonomous_player/src/xar_autoplayer/bridge/white_player_business_variables_contract.py","d2d7d198b74d27532692a599d04f3f2a170c3e3412d2b7602ff6f8c955d4b4a9"),new SourceSpec("xar_autoplayer.bridge.white_rendered_text_contract","ck3_autonomous_player/src/xar_autoplayer/bridge/white_rendered_text_contract.py","1ff2a965110c8ba735f4069a8435813ee05fa29e245365aa120b11996842c0c1"),new SourceSpec("xar_autoplayer.bridge.ingame_decisions_open_contract","ck3_autonomous_player/src/xar_autoplayer/bridge/ingame_decisions_open_contract.py","86559e259b64c541909e75835f016822a8bb6fd7c4febb5a822f23fa1dad863d"),new SourceSpec("xar_autoplayer.bridge.version_identity","ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py","9f7665ed680238f6904bc3ef22e1d67ef9b4ccd047e699542d5dbaff24b01086"),new SourceSpec("test_ingame_ui_navigation_v1","ck3_autonomous_player/tests/unit/test_ingame_ui_navigation_v1.py","878f239b24591b30e4830403c6bc912688ebea8edfa55d20c970402bdc1ea847"),new SourceSpec("test_faith_power_presentation_ui_v6","ck3_autonomous_player/tests/unit/test_faith_power_presentation_ui_v6.py","322736b920ac89b346d1550b64732c6885524135c7081a2947316a886164b9a4"),new SourceSpec("test_clerical_preview_presentation_a06","ck3_autonomous_player/tests/unit/test_clerical_preview_presentation_a06.py","e58d0aa3bf6f7c908c1d26bb501f4fda0f3040ec09f6627918c52e49dc2717eb"),new SourceSpec("test_tooltip_stack_clear_a02","ck3_autonomous_player/tests/unit/test_tooltip_stack_clear_a02.py","cc2f6e697b3eb405a2874ce0dd3477c284ec1fdc29f9cb082fe6786fa7217a46")); }
 public static byte[] encodeConfiguration(Config value)throws IOException{return ControlBuild.strictMapper().writeValueAsBytes(value);}
 public static Config readConfiguration(FileRef ref)throws IOException{return GuiEightFixtureCodec.configuration(ref);}
 public static Case readCase(FileRef ref)throws IOException{return GuiEightFixtureCodec.caseInput(ref);}
 public static Body readProduced(FileRef ref)throws IOException{return GuiEightFixtureCodec.produced(ref);}
 public static FileRef produce(FileRef configRef,FileRef caseRef,Path output,FreshSdkFixtureStage.ResourceGuard resources)throws IOException,InterruptedException {
  Objects.requireNonNull(resources);Config config=readConfiguration(configRef);Case actual=readCase(caseRef);GuiEightFixtureCodec.current(config);
  output=GuiEightFixtureCodec.freshDataRoot(output);resources.revalidate(8192);Files.createDirectory(output);Path state=output.resolve("python-state");Files.createDirectory(state);
  var invocation=invocation(configRef,caseRef,state);Map<String,String> env=new TreeMap<>(String.CASE_INSENSITIVE_ORDER);env.putAll(System.getenv());
  env.putAll(CanonicalOracleEnvironment.bind(Path.of(config.repositoryRoot()),Path.of(config.python().path()),env));
  env.put("PYTHONDONTWRITEBYTECODE","1");env.put("XAR_AUTOPLAYER_STATE_DIR",state.toString());env.put("XAR_PROJECT_STORAGE_ROOT",state.toString());
  Instant deadline=Instant.now().plusSeconds(config.timeoutSeconds());require(deadline.isBefore(Instant.parse(config.reviewAtUtc())),"original GUI config expired before complete child timeout");
  var run=CanonicalColdWarmStage.execute(1,invocation,CanonicalColdWarmStage.BootstrapMode.NONE,null,config.python(),Path.of(config.repositoryRoot()),output.resolve("process"),env,config.memoryLimitBytes(),Duration.ofSeconds(config.timeoutSeconds()),deadline,resources);
  FileRef process=GuiEightFixtureCodec.write(output.resolve("process.json"),run,resources);
  if(run.state()!=CanonicalColdWarmStage.CommandState.PASS)throw new IOException("Original GUI process did not pass; actual terminal retained: "+process.path());
  FileRef result=GuiEightFixtureCodec.write(output.resolve("gui-eight-fixture.json"),new Product("xar.gui-eight-original-product/v1",config.machineId(),configRef,caseRef,invocation,process,run.stdoutRef()),resources);
  readProduced(result);return result;
 }
 static CanonicalPythonInvocation.Invocation invocation(FileRef config,FileRef actual,Path state)throws IOException {
  String body="import base64;exec(compile(base64.b64decode('"+Base64.getEncoder().encodeToString(GuiEightOriginalProgram.source().getBytes(StandardCharsets.UTF_8))+"'),'<gui-eight-original>','exec'))";
  return CanonicalPythonInvocation.parse("python -B -X utf8 -c "+quote(body)+" "+quote(config.path())+" "+quote(actual.path())+" "+quote(state.toString()),state);
 }
 private static String quote(String value){require(value!=null&&!value.contains("\"")&&!value.contains("\n")&&!value.contains("\r"),"finite literal original argv word required");return "\""+value+"\"";}
 static void require(boolean okay,String message){if(!okay)throw new IllegalArgumentException(message);}
}
