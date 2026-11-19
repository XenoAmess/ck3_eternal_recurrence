package org.xar.ck3.control.service.root;
import java.nio.file.Path;
import java.time.Duration;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import static org.junit.jupiter.api.Assertions.*;
class FrontendCallbackLeaseDurationTest {
 private static ExactRef input(String name){return new ExactRef(System.getProperty(name),Long.parseLong(System.getProperty(name+".bytes")),System.getProperty(name+".sha256"));}
 @Test void actualSavedConfigurationKeepsSixtySecondFreshnessButUsesThirtySecondFrontendCallback()throws Exception{
  var plan=RootProfileBootstrapCommand.readMappedSavedPlan(input("xar.frontend.lease.plan"));
  var actual=RootSavedRuntimeConfigurationInputs.readLoaded(input("xar.frontend.lease.config"),plan);
  assertEquals(Duration.ofSeconds(60),actual.freshness());assertEquals(Duration.ofSeconds(60),actual.heartbeatMaximumAge());
  assertEquals(Duration.ofSeconds(30),RootFrontendRuntime.frontendLeaseTtl(actual.freshness()));
  assertEquals(Duration.ofSeconds(60),actual.freshness());assertEquals(Duration.ofSeconds(60),actual.heartbeatMaximumAge());
 }
 @Test void shorterPositiveFreshnessIsNeverExtendedByTheCallbackLease(){
  for(Duration source:java.util.List.of(Duration.ofNanos(1),Duration.ofSeconds(7),Duration.ofSeconds(30)))assertSame(source,RootFrontendRuntime.frontendLeaseTtl(source));
  assertEquals(Duration.ofSeconds(30),RootFrontendRuntime.frontendLeaseTtl(Duration.ofDays(1)));
 }
 @Test void zeroNegativeAndMissingDurationsNeverGainAFrontendLease(){
  assertThrows(IllegalArgumentException.class,()->RootFrontendRuntime.frontendLeaseTtl(Duration.ZERO));
  assertThrows(IllegalArgumentException.class,()->RootFrontendRuntime.frontendLeaseTtl(Duration.ofNanos(-1)));
  assertThrows(NullPointerException.class,()->RootFrontendRuntime.frontendLeaseTtl(null));
 }
}
