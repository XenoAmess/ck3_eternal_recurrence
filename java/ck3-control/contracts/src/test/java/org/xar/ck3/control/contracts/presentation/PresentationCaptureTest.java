package org.xar.ck3.control.contracts.presentation;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

class PresentationCaptureTest {
 private static final Instant NOW=Instant.parse("2026-10-27T01:00:00Z");
 static PresentationIntent intent(boolean tracking){
  var owner=new PresentationRequest.Owner("xenoamess-full-tower-eb9d2c1186","session",44,"18446744073709551614",
   PresentationRequest.EXECUTABLE_SHA256,"episode","18446744073709551613");
  var scope=new PresentationIntent.Scope("18446744073709551615",7,1000,1024,List.of(new PresentationRequest.Province(9,"b_test")));
  return new PresentationIntent("request",NOW,owner,new PresentationRequest.Frame("snapshot","9","10",42,1000),
   tracking?PresentationRequest.Mode.TRACKED_HOTSPOT:PresentationRequest.Mode.HOTSPOT,tracking?"":"b_test",tracking?Optional.of(scope):Optional.empty(),NOW.plusSeconds(10));
 }
 static byte[] header(long previous,long result){return ByteBuffer.allocate(24).order(ByteOrder.LITTLE_ENDIAN)
  .putInt(PresentationRequest.MAGIC).putInt(1).putInt(44).putInt(0).putInt((int)previous).putInt((int)result).array();}
 static PresentationIntent.Prepared prepared(PresentationIntent i){
  var t=i.tracking().map(s->new PresentationRequest.Tracking("18446744073709551614",s.generation(),s.armyId(),s.start(),s.end(),s.provinces()));
  return new PresentationIntent.Prepared(i,NOW.plusMillis(1),0,2,0,"9007199254740993","18446744073709551615",t,header(0,0));
 }
 @Test void actualRawCaptureAndTrackingRoundTripPreserveUint64StringsAndFullWire(){
  var i=intent(true);var p=prepared(i);var capture=new PresentationCapture(i,Optional.of(p),PresentationCapture.Kind.POSTED,
   OriginalOutcome.Phase.POSTED_OUTCOME_UNPERSISTED,"actual even publication",NOW.plusMillis(2),header(2,0),Optional.empty());
  var decoded=PresentationCapture.decode(capture.encode());assertArrayEquals(capture.encode(),decoded.encode());
  assertEquals("18446744073709551615",decoded.intent().tracking().orElseThrow().generation());
  byte[] request=p.requestBytes(),tracking=p.trackingBytes().orElseThrow();assertEquals(168,request.length);assertEquals(4264,tracking.length);
  var wire=ByteBuffer.wrap(tracking).order(ByteOrder.LITTLE_ENDIAN);assertEquals(2,wire.getInt());assertEquals(1,wire.getInt());
  assertEquals(-2L,wire.getLong());assertEquals(-1L,wire.getLong());assertEquals(42,wire.getInt());assertEquals(7,wire.getInt());
  assertEquals(1000,wire.getInt());assertEquals(1024,wire.getInt());assertEquals(9,wire.getInt());
 }
 @Test void captureKeepsNativeBytesImmutableAndCannotPromoteNoAttemptToPosted(){
  var i=intent(false);var p=prepared(i);byte[] after=header(2,0);
  var capture=new PresentationCapture(i,Optional.of(p),PresentationCapture.Kind.UNKNOWN,OriginalOutcome.Phase.EVEN_PUBLICATION_UNCERTAIN,
   "not a completion",NOW.plusMillis(2),after,Optional.empty());after[0]=0;
  assertEquals(PresentationRequest.MAGIC,ByteBuffer.wrap(capture.afterHeader()).order(ByteOrder.LITTLE_ENDIAN).getInt());
  byte[] copy=capture.prepared().orElseThrow().header();copy[0]=0;assertArrayEquals(header(0,0),p.header());
  assertThrows(IllegalArgumentException.class,()->new PresentationCapture(i,Optional.empty(),PresentationCapture.Kind.POSTED,
   OriginalOutcome.Phase.BEFORE_ODD,"no physical preparation",NOW,new byte[0],Optional.empty()));
  var tree=capture.toJson();tree.put("kind","NOT_ATTEMPTED");assertThrows(IllegalArgumentException.class,()->PresentationCapture.decode(StrictJson.canonical(tree)));
 }
 @Test void strictIngressRejectsWrongTypesMissingFieldsForeignOwnerAndChangedScope(){
  var i=intent(true);var n=i.toJson();n.remove("deadline");var missing=n;assertThrows(IllegalArgumentException.class,()->PresentationIntent.fromJson(missing));
  n=i.toJson();((com.fasterxml.jackson.databind.node.ObjectNode)n.get("frame")).put("revision",true);var bad=n;
  assertThrows(IllegalArgumentException.class,()->PresentationIntent.fromJson(bad));
  n=i.toJson();((com.fasterxml.jackson.databind.node.ObjectNode)n.get("tracking")).put("generation",9007199254740993L);var numeric=n;
  assertThrows(IllegalArgumentException.class,()->PresentationIntent.fromJson(numeric));
  byte[] foreign=header(0,0);ByteBuffer.wrap(foreign).order(ByteOrder.LITTLE_ENDIAN).putInt(8,45);
  assertThrows(IllegalArgumentException.class,()->new PresentationIntent.Prepared(i,NOW.plusMillis(1),0,2,0,"10000","1",prepared(i).tracking(),foreign));
  var changed=new PresentationRequest.Tracking("1",i.tracking().orElseThrow().generation(),8,1000,1024,i.tracking().orElseThrow().provinces());
  assertThrows(IllegalArgumentException.class,()->new PresentationIntent.Prepared(i,NOW.plusMillis(1),0,2,0,"10000","1",Optional.of(changed),header(0,0)));
 }
 @Test void boundedTrackingAndCoherentSamplesRejectOversizeAndPartialRegions(){
  var i=intent(true);var p=prepared(i);
  var route=new ArrayList<PresentationRequest.Province>();for(int v=1;v<=33;v++)route.add(new PresentationRequest.Province(v,"b_p"+v));
  assertThrows(IllegalArgumentException.class,()->new PresentationIntent.Scope("1",7,1000,1024,route));
  assertThrows(IllegalArgumentException.class,()->new PresentationIntent.Scope("1",7,1000,1721,List.of(new PresentationRequest.Province(9,"b_test"))));
  assertThrows(IllegalArgumentException.class,()->new PresentationCapture.NativeSample(NOW,header(2,2),new byte[65640],new byte[168],2,Optional.of(new byte[40]),Optional.empty()));
  var sample=new PresentationCapture.NativeSample(NOW.plusMillis(3),header(2,2),new byte[65640],new byte[168],2,Optional.of(new byte[40]),Optional.of(new byte[80]));
  var capture=new PresentationCapture(i,Optional.of(p),PresentationCapture.Kind.POSTED,OriginalOutcome.Phase.POSTED_OUTCOME_UNPERSISTED,
   "raw custody only",NOW.plusMillis(2),header(2,0),Optional.of(sample));
  assertArrayEquals(capture.encode(),PresentationCapture.decode(capture.encode()).encode());
  assertEquals(80,PresentationCapture.decode(capture.encode()).sample().orElseThrow().trackingResult().orElseThrow().length);
 }
}
