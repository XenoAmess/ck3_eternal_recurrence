package org.xar.ck3.control.service.root;
import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.*;
import java.nio.file.Path;
import java.time.Instant;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.contracts.presentation.*;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.NativePresentationTransport;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiService;

/** Controlled original binary DATA through the production consumer, not a native/Game qualification. */
final class RootGuiPresentationTest {
 @TempDir Path root;
 private static ActionCommand command(ActionCommand original,PresentationRequest.Mode mode){
  var fields=StrictJson.object().put("mode",mode.name());
  return new ActionCommand("physical-"+mode.name(),original.before(),original.source(),original.sessionId(),RootGuiPresentation.OPERATION,GuiService.arguments(fields),
   new ExpectedPostcondition(1,original.before(),original.source(),RootGuiPresentation.OBSERVER,List.of(new ExpectedBoolean(new FieldKey("camera.presentation_complete"),true))),original.claims(),original.deadline());
 }
 private static byte[] header(PresentationRequest.Owner owner,long request,long result){
  return ByteBuffer.allocate(24).order(ByteOrder.LITTLE_ENDIAN).putInt(PresentationRequest.MAGIC).putInt(1).putInt((int)owner.processId()).putInt(0).putInt((int)request).putInt((int)result).array();
 }
 private static PresentationRequest prepare(ActionCommand command,ActionPorts.OutcomeArchive archive){
  var owner=new PresentationRequest.Owner(command.source().machineId(),command.sessionId(),command.before().game().pid(),command.before().game().creationFiletime().value().toString(),PresentationRequest.EXECUTABLE_SHA256,command.before().frame().episodeRunId(),"5");
  byte[] raw=header(owner,0,0);var original=new PresentationOriginals.OriginalArtifact(PresentationOriginals.ArtifactRole.HEADER,raw);var href=archive.preservePresentationArtifact(original);
  var inspection=new NativePresentationTransport.Inspection(owner,Instant.now(),0,0,"18446744073709441615","18446744073709551614",raw);
  var proof=RootGuiPresentation.inspectionBody(command,inspection,href,List.of(command.source().sourceRef()));var pref=archive.preserveMaterial(proof);
  assertEquals(proof,archive.loadMaterial(pref));return RootGuiPresentation.prepareOriginal(command,inspection,List.of(pref,href));
 }
 private static PresentationObservation observation(PresentationRequest request,PresentationObservation.Status status,long resultSequence,float target,ActionPorts.OutcomeArchive archive){
  var raw=ByteBuffer.allocate(65640).order(ByteOrder.LITTLE_ENDIAN);raw.putInt((int)request.requestSequence()).putInt(status.wireCode()).putInt(request.frame().actor()).putInt(request.frame().dateRaw()).putInt(1).putInt(1280).putInt(720).putInt(2);
  raw.putInt(0).putInt(0).putInt(100).putInt(100);for(int i=0;i<6;i++)raw.putFloat(target+i);for(int i=0;i<6;i++)raw.putFloat(target+i);raw.putInt(100).putInt(1).putInt(101);
  byte[] header=header(request.owner(),request.requestSequence(),resultSequence),diagnostics=new byte[168];
  var h=archive.preservePresentationArtifact(new PresentationOriginals.OriginalArtifact(PresentationOriginals.ArtifactRole.HEADER,header));
  var r=archive.preservePresentationArtifact(new PresentationOriginals.OriginalArtifact(PresentationOriginals.ArtifactRole.RESULT,raw.array()));
  var d=archive.preservePresentationArtifact(new PresentationOriginals.OriginalArtifact(PresentationOriginals.ArtifactRole.DIAGNOSTICS,diagnostics));
  var capture=new PresentationObservation.Capture(request.owner(),request.preparedAt().plusSeconds(resultSequence+1),request.requestSequence(),resultSequence,resultSequence,h,r,d);
  var actual=PresentationObservation.fromOriginal(request,capture,header,raw.array(),diagnostics);
  var ref=archive.preservePresentationObservation(actual);assertEquals(actual,archive.loadPresentationObservation(ref));return actual;
 }
 @Test void actualInspectionProducerToSharedWireAndOriginalArchiveRetainsExact64BitIdentity()throws Exception{
  try(var fixture=new ActionWriterIntegrationFixture(root.resolve("physical-wire"),false)){
   var original=fixture.command("physical-wire");fixture.writer.locked(same->{var archive=fixture.archive.withSession(same);var request=prepare(command(original,PresentationRequest.Mode.REALM),archive);
    assertEquals(request,PresentationRequest.decode(request.encode()));assertEquals(1,request.physicalRequestCount());assertEquals(0,request.nativePipeRequestCount());
    assertEquals("18446744073709451615",request.expiresUptimeMs());assertEquals("18446744073709551614",request.hwnd());assertEquals(168,request.nativeBytes().length);
    var wire=ByteBuffer.wrap(request.nativeBytes()).order(ByteOrder.LITTLE_ENDIAN);assertEquals(1,wire.getInt(0));assertEquals(request.frame().actor(),wire.getInt(4));assertEquals(new BigInteger(request.hwnd()).longValue(),wire.getLong(24));
    var wrong=request.toJson();wrong.withObject("/owner").put("connection_generation",5);assertThrows(IllegalArgumentException.class,()->PresentationRequest.fromJson(wrong));
    var odd=request.toJson().put("request_sequence",3);assertThrows(IllegalArgumentException.class,()->PresentationRequest.fromJson(odd));return null;
   });assertEquals(0,fixture.nativeActionWrites());
  }
 }
 @Test void signedActorWireToStatusBinding(){
  for(int actor:new int[]{Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE}){
   var frame=new PresentationRequest.Frame("signed","1","1",NativeCharacterId.fromJson(NativeCharacterId.of(actor).toJson()).value(),1000);
   var binding=new org.xar.ck3.control.nativebridge.capabilities.gui.GuiCameraCapabilities.Binding(2,frame.actor(),1000,"software");assertEquals(actor,binding.actor());
  }
  assertThrows(IllegalArgumentException.class,()->new org.xar.ck3.control.nativebridge.capabilities.gui.GuiCameraCapabilities.Binding(2,-1,1000,"software"));
 }
 @Test void independentResultMustMatchModeAndRetainFirstNativeTargetAcrossCanonicalObservations()throws Exception{
  try(var fixture=new ActionWriterIntegrationFixture(root.resolve("physical-after"),false)){
   var original=fixture.command("physical-after");fixture.writer.locked(same->{var archive=fixture.archive.withSession(same);var realm=prepare(command(original,PresentationRequest.Mode.REALM),archive);
    var stale=observation(realm,PresentationObservation.Status.SETTLED,0,1,archive);assertInstanceOf(PresentationObservation.Pending.class,stale);assertFalse(RootGuiPresentation.completion(realm,stale,archive));
    var first=observation(realm,PresentationObservation.Status.SUBMITTED,2,1,archive);var changed=observation(realm,PresentationObservation.Status.SETTLED,4,9,archive);var settled=observation(realm,PresentationObservation.Status.SETTLED,4,1,archive);
    assertFalse(RootGuiPresentation.completion(realm,first,archive));assertFalse(RootGuiPresentation.completion(realm,List.of(first,changed),archive));assertTrue(RootGuiPresentation.completion(realm,List.of(first,settled),archive));
    var bounds=observation(realm,PresentationObservation.Status.BOUNDS_AVAILABLE,6,1,archive);assertFalse(RootGuiPresentation.completion(realm,bounds,archive));
    var query=prepare(command(original,PresentationRequest.Mode.QUERY),archive);assertTrue(RootGuiPresentation.completion(query,observation(query,PresentationObservation.Status.BOUNDS_AVAILABLE,2,1,archive),archive));
    assertFalse(RootGuiPresentation.completion(query,observation(query,PresentationObservation.Status.SETTLED,2,1,archive),archive));return null;
   });assertEquals(0,fixture.nativeActionWrites());
  }
 }
}
