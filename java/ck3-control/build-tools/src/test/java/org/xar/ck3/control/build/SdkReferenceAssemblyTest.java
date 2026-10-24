package org.xar.ck3.control.build;
import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SdkSourceAssembly.*;
final class SdkReferenceAssemblyTest {
 @TempDir Path directory;
 private FileRef leaf(String name,String text) throws Exception {return FileRef.measure(Files.writeString(directory.resolve(name),text));}
 @Test void sharedLeafActuallyWritesAndRejectsDriftOrOverwrite() throws Exception {
  byte[] bytes="exact-reference-source".getBytes(StandardCharsets.UTF_8);Path target=directory.resolve("nested/module.py");
  var actual=SdkSourceAssembly.exactLeaf(bytes,Digest.of(bytes),target);
  assertArrayEquals(bytes,Files.readAllBytes(target));assertEquals(Digest.of(bytes).sha256(),actual.source().sha256());
  assertThrows(java.io.IOException.class,()->SdkSourceAssembly.exactLeaf(bytes,Digest.of(bytes),target));
  Path drift=directory.resolve("drift.py");
  assertThrows(java.io.IOException.class,()->SdkSourceAssembly.exactLeaf(bytes,Digest.of(new byte[]{1}),drift));
  assertFalse(Files.exists(drift));
 }
 @Test void completeReferenceWireCannotBecomeAnOrdinarySdkOrPreparedReceipt() throws Exception {
  FileRef pin=leaf("input","source");String machine=WindowsJobProcess.currentMachineId();
  var source=new OutputSource("module.py",SourceRole.SUPPORT_RESOURCE,pin);
  var actual=new ReferenceActual("xar.sdk-reference-actual/v1",machine,ReferencePurpose.REFERENCE_ORACLE_ONLY,
   Instant.now().toString(),"REFERENCE_INPUTS_ASSEMBLED_NOT_IMPORTED",pin,directory.toString(),directory.resolve("src").toString(),
   List.of(source),List.of(directory.toString()),List.of(new SelectedImportRoute("module","module.py",ImportSourceLocation.FRESH_GRAPH,pin,true)),
   Digest.of("source".getBytes(StandardCharsets.UTF_8)).sha256(),pin,4096,false,false,false);
  Path receipt=Files.write(directory.resolve("reference.json"),ControlBuild.strictMapper().writeValueAsBytes(actual));
  assertThrows(java.io.IOException.class,()->SdkSourceAssembly.readActual(FileRef.measure(receipt)));
  assertThrows(IllegalArgumentException.class,()->new ReferenceActual(actual.schema(),machine,actual.purpose(),actual.observedAtUtc(),
   actual.status(),pin,actual.graphRoot(),actual.sdkRoot(),actual.actualSourceClosure(),actual.importRoots(),actual.selectedImportRoutes(),
   actual.sourceSetSha256(),pin,4096,false,false,true));
 }
 @Test void selectionDistinguishesRealParentAndAbsenceWithAllRefsIndependentlyValid() throws Exception {
  FileRef before=leaf("before","old"),after=leaf("after","new"),wrong=leaf("wrong","other"),audit=leaf("audit","{}");
  Source existing=new Source("module.py",SourceRole.SDK_SOURCE,InputOrigin.FROZEN_SDK_SOURCE,before,List.of());
  ReferenceSelection selected=new ReferenceSelection("module.py",ReferenceInputKind.ORIGINAL_PRODUCER_SOURCE,before,after,audit);
  SdkSourceAssembly.verifyReferenceParent(selected,existing,false);
  assertThrows(java.io.IOException.class,()->SdkSourceAssembly.verifyReferenceParent(
   new ReferenceSelection("module.py",selected.kind(),wrong,after,audit),existing,false));
  Source added=new Source("module.py",SourceRole.SHARED_TRANSPORT,InputOrigin.STAGED_NEW_SOURCE,after,List.of());
  SdkSourceAssembly.verifyReferenceParent(new ReferenceSelection("module.py",ReferenceInputKind.COMPATIBILITY_ADAPTER,null,after,audit),added,true);
  assertThrows(java.io.IOException.class,()->SdkSourceAssembly.verifyReferenceParent(selected,added,true));
  assertThrows(NullPointerException.class,()->new ReferenceSelection("module.py",ReferenceInputKind.ORIGINAL_PRODUCER_SOURCE,null,after,audit));
 }
 @Test void realTypedGrantRejectsWrongOwnerAndExpiredPermitBeforeReviewWrite() throws Exception {
  FileRef input=leaf("input","{}");String machine=WindowsJobProcess.currentMachineId();Path output=directory.resolve("view"),review=directory.resolve("review.json");
  var request=new ReferenceRequest("xar.sdk-reference-request/v1",machine,"/root/sdk_reference_test",ReferencePurpose.LEGACY_REFERENCE_ONLY,
   input,input,null,output.toString(),List.of(directory.toString()),List.of(),List.of(),List.of());
  Instant now=Instant.now();var volume=new CiBootstrap.VolumeBudget(1000000,900000,100000,0,1,1,0,1000000,100002);
  var wrongOwner=new ControlBuild.CapacityRelease("xar.java-control.capacity-release/v1",machine,now.minusSeconds(5).toString(),now.plusSeconds(90).toString(),
   "RELEASED","/root/another_task",input,List.of(directory.toString()),System.getProperty("java.io.tmpdir"),Map.of("artifacts",1048576L),
   Map.of(directory.getRoot().toString(),volume),Map.of(),536870912,268435456);
  FileRef release=FileRef.measure(Files.write(directory.resolve("release.json"),ControlBuild.strictMapper().writeValueAsBytes(wrongOwner)));
  var permit=new WritePermit(machine,output.toString(),now.plusSeconds(60).toString(),65536,4096,4096,release);
  FileRef permitRef=FileRef.measure(Files.write(directory.resolve("permit.json"),ControlBuild.strictMapper().writeValueAsBytes(permit)));
  var error=assertThrows(java.io.IOException.class,()->new SdkSourceAssembly.ReferenceGate(permitRef,request,review));
  assertTrue(error.getMessage().contains("owner/machine/root/window"));assertFalse(Files.exists(review));assertFalse(Files.exists(output));
  var correctOwner=new ControlBuild.CapacityRelease(wrongOwner.schema(),machine,wrongOwner.observedAtUtc(),wrongOwner.reviewAtUtc(),
   wrongOwner.status(),request.ownerTask(),input,wrongOwner.approvedOutputRoots(),wrongOwner.temporaryRoot(),wrongOwner.parts(),
   wrongOwner.volumes(),wrongOwner.quotaOverrides(),wrongOwner.memoryLimitBytes(),wrongOwner.mavenHeapBytes());
  FileRef correctRelease=FileRef.measure(Files.write(directory.resolve("correct-release.json"),ControlBuild.strictMapper().writeValueAsBytes(correctOwner)));
  var expired=new WritePermit(machine,output.toString(),now.minusSeconds(1).toString(),65536,4096,4096,correctRelease);
  FileRef expiredRef=FileRef.measure(Files.write(directory.resolve("expired-permit.json"),ControlBuild.strictMapper().writeValueAsBytes(expired)));
  var expiryError=assertThrows(java.io.IOException.class,()->new SdkSourceAssembly.ReferenceGate(expiredRef,request,review));
  assertTrue(expiryError.getMessage().contains("owner/machine/root/window"));
  assertFalse(Files.exists(review));assertFalse(Files.exists(output));
  String other=directory.getRoot().equals(Path.of("C:/"))?"D:/":"C:/";
  var missingVolume=new ControlBuild.CapacityRelease(correctOwner.schema(),machine,correctOwner.observedAtUtc(),correctOwner.reviewAtUtc(),
   correctOwner.status(),request.ownerTask(),input,List.of(directory.toString(),System.getProperty("java.io.tmpdir"),System.getProperty("jna.tmpdir")),
   correctOwner.temporaryRoot(),correctOwner.parts(),Map.of(other,volume),Map.of(),correctOwner.memoryLimitBytes(),correctOwner.mavenHeapBytes());
  FileRef missingRelease=FileRef.measure(Files.write(directory.resolve("missing-volume-release.json"),ControlBuild.strictMapper().writeValueAsBytes(missingVolume)));
  var missingPermit=new WritePermit(machine,output.toString(),now.plusSeconds(60).toString(),65536,4096,4096,missingRelease);
  FileRef missingRef=FileRef.measure(Files.write(directory.resolve("missing-volume-permit.json"),ControlBuild.strictMapper().writeValueAsBytes(missingPermit)));
  var missingError=assertThrows(java.io.IOException.class,()->new SdkSourceAssembly.ReferenceGate(missingRef,request,review));
  assertTrue(missingError.getMessage().contains("volume budget missing"));assertFalse(Files.exists(review));assertFalse(Files.exists(output));
 }
}
