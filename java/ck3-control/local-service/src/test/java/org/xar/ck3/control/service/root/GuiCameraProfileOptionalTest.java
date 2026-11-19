package org.xar.ck3.control.service.root;
import java.io.IOException;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.nativebridge.capabilities.gui.GuiModels;
import static org.junit.jupiter.api.Assertions.*;
class GuiCameraProfileOptionalTest {
 @Test void unreviewedBuildsNeverConstructOrOpenTheCameraObserver()throws Exception{
  AtomicInteger calls=new AtomicInteger();
  for(String sha:List.of("bb3fef106240e95ecdb6f1532982e89e9432c92a99d33db623521572f06e6f79","2F2B","0".repeat(64),"unknown")){
   assertTrue(RootGuiPresentation.observerForProfile(sha,()->{calls.incrementAndGet();throw new IOException("must never open native camera");}).isEmpty());
  }
  assertEquals(0,calls.get());
 }
 @Test void reviewedBuildKeepsTheOriginalFactoryAndItsIdenticalObserver()throws Exception{
  AtomicInteger calls=new AtomicInteger();Object actual=new Object();
  for(String sha:List.of(GuiModels.Build.CROZIER4.sha256(),GuiModels.Build.CROZIER4.sha256().toUpperCase(Locale.ROOT))){
   assertSame(actual,RootGuiPresentation.observerForProfile(sha,()->{calls.incrementAndGet();return actual;}).orElseThrow());
  }
  assertEquals(2,calls.get());
 }
 @Test void reviewedCameraFailuresAreNeverDowngradedIntoMissingCapability(){
  IOException original=new IOException("reviewed camera guard failed");
  assertSame(original,assertThrows(IOException.class,()->RootGuiPresentation.observerForProfile(GuiModels.Build.CROZIER4.sha256(),()->{throw original;})));
  assertThrows(IllegalStateException.class,()->RootGuiPresentation.observerForProfile(GuiModels.Build.CROZIER4.sha256(),()->{throw new IllegalStateException("wrong original owner");}));
 }
}
