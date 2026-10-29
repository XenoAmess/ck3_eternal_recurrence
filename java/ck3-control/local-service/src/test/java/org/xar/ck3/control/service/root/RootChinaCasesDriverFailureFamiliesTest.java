package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.Objects;
import java.util.Optional;
import java.util.zip.GZIPInputStream;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesContract.Method;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesOriginalNormalizers;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesFacade;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesCodec.Family;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesModel.IncidentProfile;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesService;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/** Original Python methods produced the pinned oracle. These packets remain explicit DATA:
* no held Native READ, private Root row or gameplay qualification is claimed. */
final class RootChinaCasesDriverFailureFamiliesTest {
  private static final ExactRef DATA=new ExactRef("synthetic/china-cases-original-families",1,"a".repeat(64));
  private static final PlanningReadPort NEVER_READ=new PlanningReadPort() {
    @Override public <T> PlanningReadResult<T> read(ReadContract<T> c,PlanningReadRequest r) {
      throw new AssertionError("decoder oracle must not issue a READ");
    }
  };
  private static final ActionCoordinatorPort NEVER_ACTION=new ActionCoordinatorPort() {
    @Override public ActionReceipt execute(ActionCommand c){throw new AssertionError("READ failure cannot submit");}
    @Override public ActionReceipt reconcile(String id){throw new AssertionError("READ failure cannot reconcile");}
  };

  @Test void originalTenFamilyOracleFeedsTheRealProducerAndBothRootConsumers()throws Exception {
    byte[] bytes;
    try(var input=Objects.requireNonNull(getClass().getResourceAsStream("/china-cases-original-driver-errors64.json"))){
      bytes=input.readAllBytes();
    }
    assertEquals("92c7f8999e6f3e70f99664cc4441d904f14e170a71b8d0fd05d1d309a79aabb9",
        HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
    JsonNode oracle=StrictJson.parse(bytes);
    assertEquals(90,oracle.get("original_method_calls").intValue());
    assertEquals(10,oracle.get("families").size());
    int compared=0;
    for(JsonNode row:oracle.get("families")) {
      Family family=Family.valueOf(row.get("family").textValue());
      Fixture data=fixture(family);
      for(var it=oracle.get("common_outcomes").fields();it.hasNext();) {
        var variant=it.next();String name=variant.getKey();
        ObjectNode token=StrictJson.object().put("step",row.get("step").textValue()).put("accepted",true)
            .put("status","unavailable").put("query_sequence",9).put("snapshot_revision",31)
            .put("backend_id","original-oracle64");
        token.putNull(row.get("payload").textValue());
        switch(name) {
          case "missing_sequence_key"->token.remove("query_sequence");
          case "missing_accepted_key"->token.remove("accepted");
          case "wrong_step"->token.put("step","wrong-step");
          case "null_sequence"->token.putNull("query_sequence");
          case "bool_sequence"->token.put("query_sequence",true);
          case "float_sequence"->token.put("query_sequence",1.0);
          case "zero_sequence"->token.put("query_sequence",0);
          case "overflow_sequence"->token.put("query_sequence",BigInteger.ONE.shiftLeft(64));
          case "equal_float_revision_null_sequence"->{token.put("snapshot_revision",31.0);token.putNull("query_sequence");}
          default->fail("unrecognized original oracle mutation");
        }
        if(name.equals("float_sequence"))
          assertTrue(StrictJson.parse(raw(token).bytes()).get("query_sequence").isFloatingPointNumber());
        if(name.equals("equal_float_revision_null_sequence"))
          assertTrue(StrictJson.parse(raw(token).bytes()).get("snapshot_revision").isFloatingPointNumber());
        PlanningReadReceipt receipt=data.receipt(token);
        String expected=family==Family.B1&&name.equals("overflow_sequence")
            ?oracle.get("B1_overflow_outcome").textValue():variant.getValue().textValue();
        if(expected.equals("NORMALIZER_BOUNDARY")) {
          var fault=assertThrows(ChinaCasesFacade.OriginalDriverFailure.class,()->data.contract().decode(receipt));
          assertEquals(ChinaCasesFacade.OriginalDriverFailure.Kind.B1_NORMALIZER_REJECTED,fault.kind());
          assertEquals("native ZhongGuo B1-cycle contract rejected the frame",fault.originalMessage());
          compared++;continue;
        }
        var fault=assertThrows(ChinaCasesFacade.OriginalDriverFailure.class,()->data.contract().decode(receipt));
        assertEquals(family,fault.kind().family());
        fault.requireOriginal(data.contract(),data.request(),receipt);
        var unavailable=new PlanningReadResult.Unavailable<Object>("actual decoder DATA failure",
            Optional.of(receipt.original()),Optional.of(fault));
        var generic=RootChinaCasesPublicStepProducts.originalDriverFailure(
            unavailable,data.facade(),data.contract(),data.request()).orElseThrow();
        var direct=new ChinaCasesService.Unavailable("actual decoder DATA failure",
            Optional.of(receipt.original()),Optional.of(fault));
        var context=new ChinaCasesFacade.Context(data.request().before(),data.request().source(),
            data.request().sessionId(),BigInteger.valueOf(3),data.request().deadline());
        var mapped=RootChinaCasesPublicStepProducts.originalDirectDriverFailure(
            direct,data.facade(),family,context).orElseThrow();
        JsonNode original=row.get("errors").get(expected);
        assertEquals(original.get("error_class").textValue(),generic.kind().pythonClassName());
        assertEquals(original.get("message").textValue(),generic.getMessage());
        assertEquals(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,generic.kind());
        assertEquals(generic.kind(),mapped.kind());assertEquals(generic.getMessage(),mapped.getMessage());
        assertSame(fault,generic.getCause());assertSame(fault,mapped.getCause());
        assertTrue(generic.originalCandidate().isEmpty());assertTrue(mapped.originalCandidate().isEmpty());
        Family other=family==Family.B1?Family.CASE:Family.B1;
        assertThrows(IllegalArgumentException.class,()->RootChinaCasesPublicStepProducts
            .originalDirectDriverFailure(direct,data.facade(),other,context));
        var replay=assertThrows(IllegalArgumentException.class,()->data.contract().replay(receipt));
        assertFalse(replay instanceof ChinaCasesFacade.OriginalDriverFailure);
        compared++;
      }
    }
    assertEquals(90,compared);
  }

  @Test void actualOriginalNormalizersCoverSuccessDeepFieldsAndExactFailures()throws Exception {
    byte[] compressed;
    try(var input=Objects.requireNonNull(getClass().getResourceAsStream("/china-cases-original-normalizers65.json.gz"))){
      compressed=input.readNBytes(20481);assertTrue(compressed.length<=20480);assertEquals(-1,input.read());
    }
    assertEquals("bdb65fafe97a46f2428074919ae380b0125f34a5eaa3ab150681a1c1a5df4975",
        HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(compressed)));
    byte[] bytes;
    try(var input=new GZIPInputStream(new java.io.ByteArrayInputStream(compressed))){
      bytes=input.readNBytes(400001);assertTrue(bytes.length<=400000);assertEquals(-1,input.read());
    }
    JsonNode oracle=StrictJson.parse(bytes);assertEquals(1270,oracle.get("original_normalizer_calls").intValue());
    int compared=0,failures=0;
    for(JsonNode row:oracle.get("families")) {
      Family family=Family.valueOf(row.get("family").textValue());Fixture data=fixture(row,family);
      ObjectNode baseline=(ObjectNode)row.get("baseline").get("normalized");
      compareJsonTypes(baseline,normalize(data,family,row.get("base")),family+" baseline");compared++;
      var receipt=data.receipt(envelope(data.request(),family,row.get("base")));
      assertNotNull(data.contract().decode(receipt));
      Method method=java.util.Arrays.stream(Method.values()).filter(m->m.readOnly()&&m.family()==family).findFirst().orElseThrow();
      compareJsonTypes(baseline,StrictJson.parse(ChinaCasesCodec.encodeNumericExecutionResult(method,receipt).bytes())
          .get(payloadKey(family)),family+" real numeric consumer");
      assertTrue(StrictJson.parse(ChinaCasesCodec.encodeExecutionResult(method,receipt).bytes()).get("snapshot_revision").isTextual());
      var held=ChinaCasesOriginalNormalizers.normalize(receipt,family);
      held.fields().removeAll();compareJsonTypes(baseline,held.fields(),family+" immutable");
      for(JsonNode variant:row.get("variants")) {
        JsonNode payload=patch(row.get("base"),variant.get("patch"));
        JsonNode expected=variant.get("outcome");
        if(expected.has("message")) {
          var actualReceipt=data.receipt(envelope(data.request(),family,payload));
          var failure=assertThrows(ChinaCasesOriginalNormalizers.NormalizationFailure.class,
              ()->ChinaCasesOriginalNormalizers.normalize(actualReceipt,family));
          assertEquals(family,failure.family());assertEquals(expected.get("error_class").textValue(),failure.originalErrorClass());
          assertEquals(expected.get("message").textValue(),failure.getMessage(),family+" "+variant.get("patch"));
          var fault=assertThrows(ChinaCasesFacade.OriginalDriverFailure.class,()->data.contract().decode(actualReceipt));
          assertTrue(fault.kind().normalizer());assertEquals(family,fault.kind().family());
          assertEquals(driverPrefix(family)+(family==Family.B1?"":failure.getMessage()),fault.originalMessage());
          var unavailable=new PlanningReadResult.Unavailable<Object>("actual normalizer DATA failure",
              Optional.of(actualReceipt.original()),Optional.of(fault));
          var generic=RootChinaCasesPublicStepProducts.originalDriverFailure(
              unavailable,data.facade(),data.contract(),data.request()).orElseThrow();
          var direct=new ChinaCasesService.Unavailable("actual normalizer DATA failure",
              Optional.of(actualReceipt.original()),Optional.of(fault));
          var context=new ChinaCasesFacade.Context(data.request().before(),data.request().source(),
              data.request().sessionId(),BigInteger.valueOf(3),data.request().deadline());
          var mapped=RootChinaCasesPublicStepProducts.originalDirectDriverFailure(
              direct,data.facade(),family,context).orElseThrow();
          assertEquals("BridgeUnavailableError",generic.kind().pythonClassName());
          assertEquals(fault.originalMessage(),generic.getMessage());assertEquals(generic.getMessage(),mapped.getMessage());
          assertSame(fault,generic.getCause());assertSame(fault,mapped.getCause());
          assertTrue(generic.originalCandidate().isEmpty());assertTrue(mapped.originalCandidate().isEmpty());failures++;
        } else {
          JsonNode normalized=baseline.deepCopy();
          for(JsonNode change:expected.get("normalized_patch"))normalized=patch(normalized,change);
          compareJsonTypes(normalized,normalize(data,family,payload),family+" "+variant.get("patch"));
        }
        compared++;
      }
    }
    assertEquals(1270,compared);assertEquals(1155,failures);
  }
  private static JsonNode normalize(Fixture data,Family family,JsonNode payload) {
    var result=ChinaCasesOriginalNormalizers.normalize(data.receipt(envelope(data.request(),family,payload)),family);
    JsonNode encoded=StrictJson.parse(raw(result.fields()).bytes());
    compareJsonTypes(result.fields(),encoded,"normalized JSON serde");return encoded;
  }
  private static ObjectNode envelope(PlanningReadRequest request,Family family,JsonNode payload) {
    ObjectNode n=StrictJson.object().put("step",family.step()).put("accepted",true).put("status","available")
        .put("query_sequence",9).put("snapshot_revision",request.before().frame().identity().nativeRevision())
        .put("backend_id","actual-original-normalizer-data65");
    n.set(payloadKey(family),payload.deepCopy());return n;
  }
  private static String payloadKey(Family family) {
    return java.util.Arrays.stream(Method.values()).filter(m->m.readOnly()&&m.family()==family).findFirst().orElseThrow().payload();
  }
  private static String driverPrefix(Family family) {
    return switch(family) {
      case B1->"native ZhongGuo B1-cycle contract rejected the frame";
      case CASE->"native ZhongGuo case query returned a malformed frame: ";
      case AIOWNED->"native ZhongGuo AI-owned case query returned a malformed frame: ";
      case RESULT->"native ZhongGuo result-case query returned a malformed frame: ";
      case PIP->"native ZhongGuo B2 PIP query returned a malformed frame: ";
      case PROMOTION->"native ZhongGuo promotion/compensation frame is malformed: ";
      case AF5->"native ZhongGuo compensation AF5 frame is malformed: ";
      case PROJECTS->"native ZhongGuo projects/metrics frame is malformed: ";
      case INCIDENT->"native ZhongGuo incident query returned a malformed frame: ";
      case SCOREBOARD->"native ZhongGuo scoreboard query returned a malformed frame: ";
      case PROGRESS->throw new AssertionError("PROGRESS excluded");
    };
  }
  private static JsonNode patch(JsonNode original,JsonNode patch) {
    JsonNode result=original.deepCopy(),path=patch.get("path");
    if(path.isEmpty())return patch.get("value").deepCopy();
    JsonNode parent=result;
    for(int i=0;i<path.size()-1;i++)parent=path.get(i).isIntegralNumber()?parent.get(path.get(i).intValue()):parent.get(path.get(i).textValue());
    JsonNode last=path.get(path.size()-1);
    if(parent instanceof ObjectNode object) {
      if(patch.get("operation").textValue().equals("remove"))object.remove(last.textValue());
      else object.set(last.textValue(),patch.get("value").deepCopy());
    } else ((com.fasterxml.jackson.databind.node.ArrayNode)parent).set(last.intValue(),patch.get("value").deepCopy());
    return result;
  }
  private static void compareJsonTypes(JsonNode expected,JsonNode actual,String label) {
    assertNotNull(actual,label);assertEquals(expected.getNodeType(),actual.getNodeType(),label);
    if(expected.isNumber()) {
      assertEquals(expected.isIntegralNumber(),actual.isIntegralNumber(),label);
      if(expected.isIntegralNumber())assertEquals(expected.bigIntegerValue(),actual.bigIntegerValue(),label);
      else assertEquals(Double.doubleToLongBits(expected.doubleValue()),Double.doubleToLongBits(actual.doubleValue()),label);
    } else if(expected.isContainerNode()) {
      assertEquals(expected.size(),actual.size(),label);
      if(expected.isArray())for(int i=0;i<expected.size();i++)compareJsonTypes(expected.get(i),actual.get(i),label+"/"+i);
      else expected.fields().forEachRemaining(x->compareJsonTypes(x.getValue(),actual.get(x.getKey()),label+"/"+x.getKey()));
    } else assertEquals(expected,actual,label);
  }
  private static Fixture fixture(JsonNode row,Family family) {
    var facade=new ChinaCasesFacade(NEVER_READ,NEVER_ACTION);
    ReadContract<?> contract=facade.readContracts().stream().filter(c->c.operation().value().equals(family.step())).findFirst().orElseThrow();
    ObjectNode args=((ObjectNode)row.get("query")).deepCopy();
    if(family==Family.CASE&&args.path("owner_character_id").isNull())args.put("owner_character_id",0);
    if(family==Family.SCOREBOARD)args.put("expected_connection_generation",3);
    Instant now=Instant.now();var source=new G2Source("software-fixture",now.toString(),"normalizer-original-oracle65",DATA);
    JsonNode base=row.get("base");
    var identity=new JointBudgetSelector.Frame(base.get("player_character_id").bigIntegerValue(),
        base.get("snapshot_revision").bigIntegerValue(),base.get("date_raw").bigIntegerValue());
    var frame=new JointBudgetSelector.ProposalFrame(identity,"normalizer-original-oracle65",BigInteger.valueOf(19),"software-episode");
    var before=new ProposalLifecycle.ObservationIdentity("software-fixture",new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),frame,1);
    var request=new PlanningReadRequest(before,source,"software-session",contract.operation(),
        (OpportunityJson.Obj)OpportunityJson.parse(StrictJson.canonical(args)),now.plusSeconds(60));
    contract.prepare(request,"software-families64");return new Fixture(facade,contract,request);
  }

  private static Fixture fixture(Family family) {
    var facade=new ChinaCasesFacade(NEVER_READ,NEVER_ACTION);
    ReadContract<?> contract=facade.readContracts().stream()
        .filter(c->c.operation().value().equals(family.step())).findFirst().orElseThrow();
    ObjectNode args=StrictJson.object().put("request_nonce","4e31");
    switch(family) {
      case B1->{}
      case CASE->args.put("case_kind","zhongguo.b1.performance").put("subject_character_id",103).put("owner_character_id",0);
      case AIOWNED,PROJECTS->args.put("owner_character_id",102).put("subject_character_id",103);
      case SCOREBOARD->args.put("expected_connection_generation",3);
      case INCIDENT->args.put("owner_character_id",102).put("profile",
          IncidentProfile.values()[0].name().toLowerCase(java.util.Locale.ROOT));
      case RESULT,PIP,PROMOTION,AF5->args.put("owner_character_id",102);
      case PROGRESS->throw new AssertionError("PROGRESS is not one of original Cases10");
    }
    Instant now=Instant.now();var source=new G2Source("software-fixture",now.toString(),"original-cases-oracle",DATA);
    var identity=new JointBudgetSelector.Frame(BigInteger.valueOf(101),BigInteger.valueOf(31),BigInteger.valueOf(42));
    var frame=new JointBudgetSelector.ProposalFrame(identity,"original-oracle64",BigInteger.valueOf(19),"software-episode");
    var before=new ProposalLifecycle.ObservationIdentity("software-fixture",
        new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),frame,1);
    var request=new PlanningReadRequest(before,source,"software-session",contract.operation(),
        (OpportunityJson.Obj)OpportunityJson.parse(StrictJson.canonical(args)),now.plusSeconds(60));
    contract.prepare(request,"software-families64");return new Fixture(facade,contract,request);
  }
  private record Fixture(ChinaCasesFacade facade,ReadContract<?> contract,PlanningReadRequest request) {
    PlanningReadReceipt receipt(ObjectNode result) {
      Instant now=Instant.now();
      var guard=new GuardEvidence(request.before(),request.source(),request.sessionId(),BigInteger.valueOf(3),
          request.operation(),DATA,DATA,"software-data",now,now.plusSeconds(60));
      var binding=new PlanningReadGuard(guard,true,true,true,"b".repeat(64));
      ObjectNode ack=StrictJson.object().put("type","command_result").put("protocol_version",1)
          .put("request_id","software-families64").put("ok",true);ack.set("result",result);
      RawJson encoded=raw(ack);byte[] bytes=encoded.bytes();
      byte[] packet=ByteBuffer.allocate(bytes.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(bytes.length).put(bytes).array();
      var original=new NativeActionPort.AckReceived("software-families64",true,Optional.of(raw(result)),encoded,packet);
      return new PlanningReadReceipt(request,contract.contractId(),"software-families64",binding,binding,original);
    }
  }
  private static RawJson raw(ObjectNode value){return new RawJson(StrictJson.canonical(value));}
}
