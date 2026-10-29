package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.GuiEightOracleFixture;
import org.xar.ck3.control.build.GuiEightOracleFixture.Method;
import org.xar.ck3.control.contracts.StrictJson;

/** Existing scenario adapter only; the single shared Java producer owns original invocation and origin checks. */
final class GuiEightOriginalOracle {
 private GuiEightOriginalOracle() { }
 static ObjectNode invoke(Path state,ObjectNode input)throws Exception {
  String mode=input.path("mode").textValue();Method method;ObjectNode args=StrictJson.object();
  args.set("expected_revision",input.path("snapshot").get("revision"));
  if("faith".equals(mode)){
   String operation=input.path("operation").textValue();
   if(!(input.get("options") instanceof ObjectNode options))throw new IOException("exact original Faith options required");
   if("open_faith".equals(operation)){method=Method.ck3_open_faith_window_v1;args.set("faith_id",input.get("subject"));}
   else {method="query".equals(operation)?options.has("presentation_index")?Method.ck3_query_faith_power_tooltip_v1:Method.ck3_query_faith_power_ui_v1:Method.ck3_present_faith_power_ui_v1;
    args.set("window_kind",input.get("kind"));args.set("subject_id",input.get("subject"));args.setAll(options.deepCopy());
    if(method==Method.ck3_present_faith_power_ui_v1)args.put("operation",operation);
   }
  }else if("white_read".equals(mode))method=input.path("business").booleanValue()?Method.ck3_query_white_player_business_variables_v1:Method.ck3_query_white_rendered_text_v1;
  else if("white_action".equals(mode)){
   boolean numeric=input.path("numeric").booleanValue();method=numeric?Method.ck3_click_white_numeric_control_v1:Method.ck3_click_white_control_v1;
   args.put("control",numeric?input.path("control").textValue():"age_plus_1").set("intent_id",input.get("intent"));
   if(numeric)args.put("expected_before_value",6).put("expected_before_price_text","arbitrary-before-price");else args.put("expected_before_age",30);
  }else throw new IOException("declared original scenario mode required");
  var body=invokePublic(state,input,method,args);
  if(body.answer() instanceof ObjectNode answer)return answer;
  throw new IOException("actual original answer object required");
 }
 static GuiEightOracleFixture.Body invokePublic(Path state,ObjectNode scenario,Method method,ObjectNode arguments)throws Exception {
  var configRef=config();var config=GuiEightOracleFixture.readConfiguration(configRef);Files.createDirectories(state);
  Path real=state.toRealPath();String system=System.getenv("SystemDrive");
  if(system==null||real.getRoot().equals(Path.of(system+"/").toRealPath().getRoot()))throw new IOException("actual GUI fixture state must use data volume");
  var args=write(real.resolve("arguments.json"),ControlBuild.strictMapper().writeValueAsBytes(arguments));
  var input=write(real.resolve("scenario.json"),ControlBuild.strictMapper().writeValueAsBytes(scenario));
  var request=write(real.resolve("case.json"),ControlBuild.strictMapper().writeValueAsBytes(new GuiEightOracleFixture.Case(GuiEightOracleFixture.CASE_SCHEMA,method,args,input)));
  var result=GuiEightOracleFixture.produce(configRef,request,real.resolve("produced"),pending->{
   // This is the test's pin/review/output guard. The containing CI Job/resource admission remains external.
   configRef.verify();request.verify();
   if(pending<0||pending>((2L<<20)+4096)||!Instant.now().isBefore(Instant.parse(config.reviewAtUtc())))throw new IOException("finite current original fixture output/review required");
  });
  return GuiEightOracleFixture.readProduced(result);
 }
 private static ControlBuild.FileRef write(Path path,byte[] bytes)throws IOException {
  if(bytes.length<1||bytes.length>(1<<20))throw new IOException("finite original scenario material required");
  Files.write(path,bytes,StandardOpenOption.CREATE_NEW);return ControlBuild.FileRef.measure(path);
 }
 private static ControlBuild.FileRef config()throws IOException {
  String path=System.getProperty(GuiEightOracleFixture.PROPERTY),size=System.getProperty(GuiEightOracleFixture.PROPERTY+".bytes"),sha=System.getProperty(GuiEightOracleFixture.PROPERTY+".sha256");
  if(path==null||size==null||sha==null||!size.matches("[1-9][0-9]{0,8}"))throw new IOException("NOT_RUN_REQUIRED: "+GuiEightOracleFixture.PROPERTY+"/.bytes/.sha256");
  var ref=new ControlBuild.FileRef(path,Long.parseLong(size),sha);ref.verify();return ref;
 }
}
