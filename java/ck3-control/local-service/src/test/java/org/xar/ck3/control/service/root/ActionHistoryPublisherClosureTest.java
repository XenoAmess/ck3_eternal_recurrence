package org.xar.ck3.control.service.root;
import static org.junit.jupiter.api.Assertions.*;
import java.util.*;
import java.nio.file.*;
import java.security.MessageDigest;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec;
import org.xar.ck3.control.application.driver.DriverActionHistoryPublisher;
final class ActionHistoryPublisherClosureTest {
    private static ExactRef ref(String path,char sha){return new ExactRef(path,12,String.valueOf(sha).repeat(64));}
    private static RootActionHistoryMaterialSourceFactory.Sources roles(ExactRef a,ExactRef b,ExactRef c){
        return RootActionHistoryMaterialSourceFactory.Sources.ordinary(a,b,c,Map.of(),Map.of());
    }
    @Test void sharedArchiveRolesRetainTheirOriginalRefsAndProduceOneOrderedPhysicalClosure(){
        var local=ref("local-service.jar",'a');var application=ref("application.jar",'b');
        var selected=roles(local,application,new ExactRef(application.path(),application.bytes(),application.sha256()));
        assertEquals(List.of(local,application),RootActionHistoryMaterialSourceFactory.publisherClosure(selected));
        assertSame(local,selected.implementation());assertSame(application,selected.codec());assertEquals(application,selected.publisher());
        assertThrows(UnsupportedOperationException.class,()->RootActionHistoryMaterialSourceFactory.publisherClosure(selected).add(local));
    }
    @Test void distinctPathsWithTheSamePayloadAndLegacyRoleOrderRemainDistinct(){
        var a=ref("factory.java",'a');var b=ref("codec.java",'a');var c=ref("publisher.java",'a');
        assertEquals(List.of(a,b,c),RootActionHistoryMaterialSourceFactory.publisherClosure(roles(a,b,c)));
    }
    @Test void conflictingPinsForOneSourcePathAreRejectedRatherThanInventingASecondSource(){
        var a=ref("factory.jar",'a');var b=ref("application.jar",'b');var c=ref("application.jar",'c');
        assertThrows(IllegalArgumentException.class,()->RootActionHistoryMaterialSourceFactory.publisherClosure(roles(a,b,c)));
    }
    @Test void actualWholeArchiveFactoryAndBothApplicationRolesShareTheRealGenuineCarrier()throws Exception{
        var a=actual(RootActionHistoryMaterialSourceFactory.class);var b=actual(DriverActionHistoryCodec.class);var c=actual(DriverActionHistoryPublisher.class);
        assertTrue(a.bytes()>1_048_576);assertTrue(b.bytes()>1_048_576);assertEquals(b,c);
        var selected=roles(a,b,c);assertEquals(List.of(a,b),RootActionHistoryMaterialSourceFactory.publisherClosure(selected));
        assertEquals(a,selected.implementation());assertEquals(b,selected.codec());assertEquals(c,selected.publisher());
    }
    private static ExactRef actual(Class<?> type)throws Exception{
        Path p=Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI()).toAbsolutePath().normalize();
        assertTrue(Files.isRegularFile(p),"genuine whole archive required");byte[] raw=Files.readAllBytes(p);
        return new ExactRef(p.toString(),raw.length,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
    }
}
