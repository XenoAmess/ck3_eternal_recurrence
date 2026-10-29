package org.xar.ck3.control.build.runtime;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.List;
import java.util.Properties;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.ControlCi;

/** Shared source DATA codec and the adapter's real negative input boundary; no native/package positive is fabricated. */
final class RootInvocationDeploymentInputsProducerTest {
    @TempDir Path root;
    private FileRef write(String name,String value)throws IOException {
        Path path=root.resolve(name);Files.writeString(path,value,StandardOpenOption.CREATE_NEW);return FileRef.measure(path);
    }
    private ControlCi.RootInvocationInputsPlan plan()throws IOException {
        FileRef manifest=write("unqualified-manifest.json","{}"),invocation=write("unqualified-invocation.json","{}");
        FileRef source=write("unqualified-source.jar","metadata only, never an accepted class JAR");
        Instant observed=Instant.now();
        return new ControlCi.RootInvocationInputsPlan(ControlCi.ROOT_INVOCATION_INPUTS_SCHEMA,"metadata-fixture",
                observed,observed.plusSeconds(3600),manifest,invocation,root.resolve("stdout.log"),root.resolve("stderr.log"),512L<<20,
                List.of(new ControlCi.RootInvocationProductionJar(ControlCi.RootInvocationProductionRole.JAVA_RUNTIME_LAUNCH,source),
                        new ControlCi.RootInvocationProductionJar(ControlCi.RootInvocationProductionRole.ROOT_STARTUP_INVOCATION,source),
                        new ControlCi.RootInvocationProductionJar(ControlCi.RootInvocationProductionRole.ROOT_NATIVE_AUTHORITY,source)));
    }
    @Test void sharedPlanEncoderFeedsTheSoleStrictDecoderWithAllThreeRoles()throws Exception {
        var original=plan();byte[] encoded=ControlCi.encodeRootInvocationInputsPlan(original);
        var actual=ControlCi.decodeRootInvocationInputsPlan(encoded);
        assertEquals(original,actual);assertEquals(3,actual.productionJars().size());
        assertEquals(3,actual.productionJars().stream().map(ControlCi.RootInvocationProductionJar::role).distinct().count());
        assertArrayEquals(encoded,ControlCi.encodeRootInvocationInputsPlan(actual));
    }
    @Test void sharedWireRejectsMissingUnknownNullBooleanAndCrossedRoleInputs()throws Exception {
        var mapper=ControlBuild.strictMapper();
        ObjectNode original=(ObjectNode)mapper.readTree(ControlCi.encodeRootInvocationInputsPlan(plan()));
        ObjectNode bad=original.deepCopy();bad.remove("production_jars");reject(bad);
        bad=original.deepCopy();bad.put("authority_class","arbitrary.Reader");reject(bad);
        bad=original.deepCopy();bad.putNull("package_manifest_ref");reject(bad);
        bad=original.deepCopy();bad.put("schema","unknown");reject(bad);
        bad=original.deepCopy();bad.put("memory_limit_bytes",true);reject(bad);
        bad=original.deepCopy();bad.put("memory_limit_bytes",512.5);reject(bad);
        bad=original.deepCopy();((ObjectNode)bad.get("invocation_ref")).put("bytes",true);reject(bad);
        bad=original.deepCopy();((ObjectNode)bad.get("invocation_ref")).put("bytes","2");reject(bad);
        bad=original.deepCopy();((ObjectNode)bad.get("production_jars").get(2)).put("role","JAVA_RUNTIME_LAUNCH");reject(bad);
        bad=original.deepCopy();((ObjectNode)bad.get("production_jars").get(2)).put("role","future.Authority");reject(bad);
        bad=original.deepCopy();bad.put("review_at_utc","not-an-instant");reject(bad);
    }
    private static void reject(ObjectNode value)throws IOException {
        byte[] raw=ControlBuild.strictMapper().writeValueAsBytes(value);
        assertThrows(IOException.class,()->ControlCi.decodeRootInvocationInputsPlan(raw));
    }
    @Test void exactPropertiesUseOnlyCanonicalSourceTriplesAndRejectMissingOrCoercedSizes()throws Exception {
        var file=write("input-plan.json","{}");var properties=new Properties();
        String prefix=RootInvocationDeploymentInputsProducer.PROPERTY_PREFIX;
        properties.setProperty(prefix+"path",file.path());properties.setProperty(prefix+"bytes",Long.toString(file.bytes()));
        properties.setProperty(prefix+"sha256",file.sha256());
        assertEquals(file,RootInvocationDeploymentInputsProducer.configuredPlan(properties));
        for(String key:List.of("path","bytes","sha256")) {
            var missing=new Properties();missing.putAll(properties);missing.remove(prefix+key);
            assertThrows(IOException.class,()->RootInvocationDeploymentInputsProducer.configuredPlan(missing));
        }
        for(String wrong:List.of("true","1.0","01","0","65537")) {
            var invalid=new Properties();invalid.putAll(properties);invalid.setProperty(prefix+"bytes",wrong);
            assertThrows(IOException.class,()->RootInvocationDeploymentInputsProducer.configuredPlan(invalid));
        }
        var invalid=new Properties();invalid.putAll(properties);invalid.setProperty(prefix+"sha256","A".repeat(64));
        assertThrows(IOException.class,()->RootInvocationDeploymentInputsProducer.configuredPlan(invalid));
    }
    @Test void actualReaderRejectsDriftMalformedPlanAndEmptyInputBeforeAnyAuthorityImport()throws Exception {
        var original=write("bad-plan.json","{}");Files.writeString(Path.of(original.path()),"{ }",StandardOpenOption.TRUNCATE_EXISTING);
        assertThrows(IOException.class,()->RootInvocationDeploymentInputsProducer.readActual(original));
        var current=FileRef.measure(Path.of(original.path()));
        assertThrows(IOException.class,()->RootInvocationDeploymentInputsProducer.readActual(current));
        var empty=FileRef.measure(Files.createFile(root.resolve("empty")));
        assertThrows(IOException.class,()->RootInvocationDeploymentInputsProducer.readActual(empty));
    }
}
