package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.build.GuiEightOracleFixture;
import org.xar.ck3.control.build.GuiEightOracleFixture.Method;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory;

/** Real registered original tool/Pydantic -> Service boundary; explicit software traps issue no Game observation. */
final class GuiEightPublicOriginalFixtureTest {
 @TempDir Path root;
 private static ObjectNode sample(Method method){
  ObjectNode value=StrictJson.object().put("expected_revision",1);
  switch(method){
   case ck3_open_faith_window_v1->value.put("faith_id",0);
   case ck3_present_faith_power_ui_v1->value.put("operation","open_holding").put("window_kind","holding").put("subject_id",1);
   case ck3_query_faith_power_ui_v1->value.put("window_kind","faith");
   case ck3_query_faith_power_tooltip_v1->value.put("window_kind","faith").put("subject_id",0).put("presentation_target","faith_core_tenet").put("presentation_index",0).put("presentation_receipt","b".repeat(32));
   case ck3_click_white_control_v1->value.put("control","age_plus_1").put("expected_before_age",30).put("intent_id","gui-original-parameter-proof");
   case ck3_click_white_numeric_control_v1->value.put("control","martial_plus_1").put("expected_before_value",6).put("expected_before_price_text","actual-before-price").put("intent_id","gui-original-parameter-proof");
   default->{ }
  }
  return value;
 }
 private static PublicMcpDirectory.ToolDescriptor original(Method method)throws Exception {
  return RootOriginalPublicTestInputs.tools().stream().filter(t->t.name().equals(method.name())).findFirst().orElseThrow(()->new IllegalStateException("NOT_RUN_REQUIRED_ACTUAL_ORIGINAL_TOOL: "+method));
 }
 private static PublicMcpDirectory.Arguments arguments(ObjectNode value){return new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,Optional.of(PublicDataJson.encode(value)));}
 @Test void allEightRealRegisteredPublicPathsRejectBooleanRevisionBeforeAnyServiceObservation()throws Exception {
  for(Method method:Method.values()){
   ObjectNode value=sample(method).put("expected_revision",true);
   var body=GuiEightOriginalOracle.invokePublic(root.resolve(method.name()),StrictJson.object().put("mode","arguments"),method,value);
   assertEquals(method,body.method());assertFalse(body.answer().path("accepted").booleanValue());assertEquals("ValidationError",body.answer().path("cause_kind").textValue());
   assertEquals(0,body.answer().path("boundary_calls").intValue());assertEquals(18,body.origins().size());
   assertEquals(PublicDataJson.object(original(method).original()).get("inputSchema"),body.inputSchema());
   var descriptor=RootPublicCatalogCodec.executableTool(original(method));assertThrows(IllegalArgumentException.class,()->descriptor.validateArguments(arguments(value)));
   for(var origin:body.origins()){origin.original().verify();assertEquals(Path.of(origin.original().path()).toRealPath(),Path.of(origin.actualFile()).toRealPath());}
  }
 }
 @Test void actualPublicPresentExcludesInternalQueryOperationAndRequiredRevisionKeepsFloatNullMissingDistinct()throws Exception {
  Method method=Method.ck3_present_faith_power_ui_v1;ObjectNode query=sample(method).put("operation","query");
  var rejected=GuiEightOriginalOracle.invokePublic(root.resolve("present-query"),StrictJson.object().put("mode","arguments"),method,query);
  assertFalse(rejected.answer().path("accepted").booleanValue());assertEquals("ValidationError",rejected.answer().path("cause_kind").textValue());
  assertThrows(IllegalArgumentException.class,()->RootPublicCatalogCodec.executableTool(original(method)).validateArguments(arguments(query)));
  Method open=Method.ck3_open_faith_window_v1;ObjectNode missing=sample(open);missing.remove("expected_revision");
  for(ObjectNode value:List.of(sample(open).put("expected_revision",1.0),sample(open).putNull("expected_revision"),missing)){
   String name=!value.has("expected_revision")?"missing":value.get("expected_revision").isNull()?"null":"float";
   var body=GuiEightOriginalOracle.invokePublic(root.resolve(name),StrictJson.object().put("mode","arguments"),open,value);
   assertFalse(body.answer().path("accepted").booleanValue());assertEquals("ValidationError",body.answer().path("cause_kind").textValue());
   assertEquals(0,body.answer().path("boundary_calls").intValue());
   assertThrows(IllegalArgumentException.class,()->RootPublicCatalogCodec.executableTool(original(open)).validateArguments(arguments(value)));
  }
 }
 @Test void optionalWhiteRevisionMissingAndNullReachTheOriginalServiceAvailabilityFaultWithoutBecomingZero()throws Exception {
  Method method=Method.ck3_query_white_rendered_text_v1;
  for(boolean explicitNull:List.of(false,true)){
   ObjectNode value=StrictJson.object();if(explicitNull)value.putNull("expected_revision");
   var body=GuiEightOriginalOracle.invokePublic(root.resolve(explicitNull?"white-null":"white-missing"),StrictJson.object().put("mode","arguments"),method,value);
   assertFalse(body.answer().path("accepted").booleanValue());assertEquals("UnsupportedStepError",body.answer().path("cause_kind").textValue());
   RootPublicCatalogCodec.executableTool(original(method)).validateArguments(arguments(value));
   var retained=PublicDataJson.object(new org.xar.ck3.control.application.action.RawJson(java.nio.file.Files.readAllBytes(Path.of(body.argumentsRef().path()))));
   assertEquals(value,retained);assertEquals(explicitNull,retained.has("expected_revision"));
  }
 }
}
