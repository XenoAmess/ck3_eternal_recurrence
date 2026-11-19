package org.xar.ck3.control.service.root;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.ArrayList;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.interactions.GrantPickerControlEffects;
import org.xar.ck3.control.nativebridge.capabilities.interactions.GrantTitleCodec;
import static org.junit.jupiter.api.Assertions.*;
class GrantImplementationClosureTest {
 private static ExactRef owner(Class<?> type)throws Exception{
  Path p=Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI());
  assertTrue(Files.isRegularFile(p));byte[] raw=Files.readAllBytes(p);
  return new ExactRef(p.toString(),raw.length,ActionCodec.sha256(raw));
 }
 @Test void actualWholeJarRolesRetainTwoExactArchivesInsteadOfThreeDuplicatedRefs()throws Exception{
  ExactRef service=owner(RootRuntimeContext.class),effects=owner(GrantPickerControlEffects.class),decoder=owner(GrantTitleCodec.class);
  assertEquals(effects,decoder);assertNotEquals(service,effects);
  assertEquals(List.of(service,effects),RootGrantLegacyClaims.implementationClosure(List.of(service,effects,decoder)));
 }
 @Test void distinctLegacyRefsOrderAndExactPinsAreNeverMergedByPayload(){
  var a=new ExactRef("D:/own/a.java",4,"a".repeat(64));var b=new ExactRef("D:/own/b.java",4,"a".repeat(64));var c=new ExactRef("D:/own/c.java",5,"c".repeat(64));
  var roles=new ArrayList<>(List.of(a,b,c,b,a));var actual=RootGrantLegacyClaims.implementationClosure(roles);
  assertEquals(List.of(a,b,c),actual);roles.clear();assertEquals(List.of(a,b,c),actual);
  assertThrows(UnsupportedOperationException.class,()->actual.add(a));
 }
 @Test void conflictingPinsAtTheSameActualPathNeverChooseOneRoleSilently(){
  var original=new ExactRef("D:/own/source.jar",4,"a".repeat(64));
  assertThrows(IllegalArgumentException.class,()->RootGrantLegacyClaims.implementationClosure(List.of(original,new ExactRef(original.path(),4,"b".repeat(64)))));
  assertThrows(IllegalArgumentException.class,()->RootGrantLegacyClaims.implementationClosure(List.of(original,new ExactRef(original.path(),5,original.sha256()))));
 }
}
