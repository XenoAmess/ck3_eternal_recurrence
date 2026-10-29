package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.NativeTransportDiagnostics.AdoptionRefusalReason;
import org.xar.ck3.control.service.root.RootOriginalDriverColdFixture.*;

/** DATA codec and actual producer refusal edges only. Positive prelaunch proof requires Root's real qualified input closure. */
final class RootOriginalDriverColdFixtureCodecTest {
    @TempDir Path root;
    private ExactRef file(String name,byte[] data)throws IOException {
        Path path=root.resolve(name);Files.write(path,data);var source=ControlBuild.FileRef.measure(path);
        return new ExactRef(source.path(),source.bytes(),source.sha256());
    }
    private Control control(ExactRef source) {
        return new Control(root.resolve("ROOT-CONTINUITY-WINDOW.json"),source,List.of(source),"0".repeat(64));
    }
    private Fixture fixture(ExactRef source) {
        return new Fixture(RootOriginalDriverColdFixture.SCHEMA,"fixture-machine",List.of(new Case("actual-source-required",
                source,source,source,source,RootOriginalDriverJournal.Status.MISSING,null,null,control(source))));
    }
    private static void properties(String prefix,ExactRef source) {
        System.setProperty(prefix,source.path());System.setProperty(prefix+".bytes",Long.toString(source.bytes()));System.setProperty(prefix+".sha256",source.sha256());
    }
    @Test void exactV2FixtureRoundTripsAndAllThreeOriginalPropertiesAreRequired()throws Exception {
        var ref=file("actual-source.json","{}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        var expected=fixture(ref);var published=file("fixture-v2.json",RootOriginalDriverColdFixture.encode(expected));
        String key=RootOriginalDriverColdFixture.COLD_PROPERTY;
        String old=System.getProperty(key),oldBytes=System.getProperty(key+".bytes"),oldSha=System.getProperty(key+".sha256");
        try{
            properties(key,published);assertEquals(expected,RootOriginalDriverColdFixture.readRequiredSystemProperties());
            System.clearProperty(key+".bytes");assertThrows(IOException.class,RootOriginalDriverColdFixture::readRequiredSystemProperties);
            properties(key,published);System.setProperty(key+".bytes","0"+published.bytes());
            assertThrows(IOException.class,RootOriginalDriverColdFixture::readRequiredSystemProperties);
            properties(key,published);System.setProperty(key+".sha256","f".repeat(64));
            assertThrows(IOException.class,RootOriginalDriverColdFixture::readRequiredSystemProperties);
        }finally{restore(key,old);restore(key+".bytes",oldBytes);restore(key+".sha256",oldSha);}
    }
    @Test void legacyMissingControlUnknownFieldsAndIntegerAliasesAreRejectedByTheSoleCodec()throws Exception {
        var ref=file("source-v2.json","{}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        var mapper=ControlBuild.strictMapper();
        var legacy=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.readTree(RootOriginalDriverColdFixture.encode(fixture(ref)));
        legacy.put("schema","xar.java-original-driver-cold-fixture/v1");
        var old=file("legacy.json",mapper.writeValueAsBytes(legacy));assertThrows(IOException.class,()->RootOriginalDriverColdFixture.readExact(old));
        var missing=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.readTree(RootOriginalDriverColdFixture.encode(fixture(ref)));
        ((com.fasterxml.jackson.databind.node.ObjectNode)missing.get("cases").get(0)).remove("control");
        var absent=file("missing-control.json",mapper.writeValueAsBytes(missing));assertThrows(IOException.class,()->RootOriginalDriverColdFixture.readExact(absent));
        var invalid=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.readTree(RootOriginalDriverColdFixture.encode(fixture(ref)));
        ((com.fasterxml.jackson.databind.node.ObjectNode)invalid.get("cases").get(0).get("launch_plan")).put("bytes",true);
        var bool=file("bool-byte-count.json",mapper.writeValueAsBytes(invalid));assertThrows(IOException.class,()->RootOriginalDriverColdFixture.readExact(bool));
        invalid=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.readTree(RootOriginalDriverColdFixture.encode(fixture(ref)));
        invalid.put("prepared",true);var unknown=file("unknown-field.json",mapper.writeValueAsBytes(invalid));
        assertThrows(IOException.class,()->RootOriginalDriverColdFixture.readExact(unknown));
    }
    @Test void observedAbsenceCannotBeSerializedAsAnAvailableEmptyDriver()throws Exception {
        var ref=file("source-contract.json","{}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        assertThrows(IllegalArgumentException.class,()->new Case("missing",ref,ref,ref,ref,RootOriginalDriverJournal.Status.MISSING,"0".repeat(64),0,control(ref)));
        assertThrows(IllegalArgumentException.class,()->new Case("available",ref,ref,ref,ref,RootOriginalDriverJournal.Status.BASE_ONLY,null,null,control(ref)));
        assertThrows(IllegalArgumentException.class,()->new Control(root.resolve("window.json"),ref,List.of(),"0".repeat(64)));
        assertThrows(IllegalArgumentException.class,()->new Control(Path.of("relative.json"),ref,List.of(ref),"0".repeat(64)));
    }
    @Test void adoptionUsesTheSameExactTripleAndRetainsCanonicalUint64BirthAndNullableReason()throws Exception {
        var ref=file("original-hello.bin",new byte[]{1,0,0,0,0});
        var cases=new ArrayList<Expected>();cases.add(new Expected("positive",ref,42,"18446744073709551615",null));
        int index=0;for(var reason:AdoptionRefusalReason.values())cases.add(new Expected("refusal-"+(++index),ref,42,"9007199254740993",reason));
        var expected=new AdoptionFixture(RootOriginalDriverColdFixture.ADOPTION_SCHEMA,"fixture-machine",cases);
        var wire=ControlBuild.strictMapper().writeValueAsBytes(expected);var source=file("adoption.json",wire);
        String key=RootOriginalDriverColdFixture.ADOPTION_PROPERTY;
        String old=System.getProperty(key),oldBytes=System.getProperty(key+".bytes"),oldSha=System.getProperty(key+".sha256");
        try{
            properties(key,source);assertEquals(expected,RootOriginalDriverColdFixture.readAdoptionRequiredSystemProperties());
            System.clearProperty(key+".sha256");assertThrows(IOException.class,RootOriginalDriverColdFixture::readAdoptionRequiredSystemProperties);
        }finally{restore(key,old);restore(key+".bytes",oldBytes);restore(key+".sha256",oldSha);}
        assertThrows(IllegalArgumentException.class,()->new Expected("rounded",ref,42,"18446744073709551616",null));
        assertThrows(IllegalArgumentException.class,()->new Expected("leading-zero",ref,42,"01",null));
        assertThrows(IllegalArgumentException.class,()->new AdoptionFixture(RootOriginalDriverColdFixture.ADOPTION_SCHEMA,"fixture-machine",List.of(cases.get(0))));
    }
    @Test void invalidPrelaunchDataCannotPublishABundleOrCreateAControlWriter()throws Exception {
        var invalidPlan=file("not-a-qualified-launch-plan.json","{}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        var control=control(invalidPlan);var target=root.resolve("must-not-exist.json");var at=Instant.now();
        var request=new RootOriginalDriverColdFixtureProducer.Request(RootOriginalDriverColdFixtureProducer.REQUEST_SCHEMA,
                WindowsJobProcess.currentMachineId(),at.minusSeconds(1).toString(),at.plusSeconds(60).toString(),
                List.of(new RootOriginalDriverColdFixtureProducer.Input("requires-actual-proof",invalidPlan,invalidPlan,invalidPlan,invalidPlan,control)),
                new RootOriginalDriverColdFixtureProducer.Publication(target,invalidPlan,control));
        var source=file("production-request.json",ControlBuild.strictMapper().writeValueAsBytes(request));
        assertThrows(IOException.class,()->RootOriginalDriverColdFixtureProducer.produce(source,Clock.systemUTC()));
        assertFalse(Files.exists(target));assertFalse(Files.exists(control.snapshotPath()));
        assertFalse(Files.exists(root.resolve("ROOT-CONTINUITY-WINDOW.lock")));
    }
    private static void restore(String name,String value){if(value==null)System.clearProperty(name);else System.setProperty(name,value);}
}
