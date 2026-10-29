package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.FileAlreadyExistsException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.AttemptAccountingAuthority;
import org.xar.ck3.control.build.ControlBuild.AttemptCapacityRelease;
import org.xar.ck3.control.build.ControlBuild.Config;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.ManualBuildCapacityReleaseProducer.IssuerDomain;

/** Real entry adapter -> sole typed producer -> actual reader, under temporary software financial fixtures only. */
final class ManualCapacityReleaseMainTest {
    @TempDir Path temporary;
    private int sequence;
    private record Fixture(Config config,FileRef configRef,FileRef releaseRef,FileRef issuerRef,Clock clock) {}

    /** Runs the same two persistent bodies without another encoder or test engine. Never reuse a case root. */
    public static void main(String[] args)throws Exception {
        if(args==null||args.length!=1)throw new IOException("Expected one fresh absolute case root");
        Path root=Path.of(args[0]);Path parent=root.getParent();
        if(!root.isAbsolute()||!root.normalize().equals(root)||parent==null
                ||!Files.isDirectory(parent,java.nio.file.LinkOption.NOFOLLOW_LINKS)||!parent.toRealPath().equals(parent))
            throw new IOException("Fresh canonical case root under an existing ordinary parent required");
        Files.createDirectory(root);
        var positive=new ManualCapacityReleaseMainTest();positive.temporary=Files.createDirectory(root.resolve("actual-producer-reader"));
        positive.actualCliAdapterReadsOnlyPinnedSharedDtosAndPublishesTheRealPureThreeReference();
        var strict=new ManualCapacityReleaseMainTest();strict.temporary=Files.createDirectory(root.resolve("strict-refusal"));
        strict.exactHashesStrictTypesV1AliasForeignMachineAndMalformedArgumentsFailBeforeAnyCandidate();
        System.out.println("2 PASS");
        if(System.out.checkError())throw new IOException("Persistent test completion output failed");
    }

    @Test void actualCliAdapterReadsOnlyPinnedSharedDtosAndPublishesTheRealPureThreeReference()throws Exception {
        for(int seconds:List.of(10,900,ControlBuild.maximumBuildTimeoutSeconds(ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME)))
            actualCliAdapterReadsOnlyPinnedSharedDtosAndPublishesTheRealPureThreeReference(seconds,ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME);
        for(int seconds:List.of(901,ControlBuild.maximumBuildTimeoutSeconds(ControlBuild.TargetKind.SERVICE_FAST_JAR)))
            actualCliAdapterReadsOnlyPinnedSharedDtosAndPublishesTheRealPureThreeReference(seconds,ControlBuild.TargetKind.SERVICE_FAST_JAR);
    }

    private void actualCliAdapterReadsOnlyPinnedSharedDtosAndPublishesTheRealPureThreeReference(int seconds,ControlBuild.TargetKind targetKind)throws Exception {
        var fixture=fixture(seconds,targetKind);
        FileRef result=ManualCapacityReleaseMain.prepareArguments(arguments(fixture.configRef(),fixture.releaseRef(),fixture.issuerRef()),fixture.clock());
        result.verify();assertEquals(fixture.config().capacityRelease().toString(),result.path());
        var mapper=ControlBuild.strictMapper();var release=mapper.readValue(Files.readAllBytes(fixture.config().capacityRelease()),AttemptCapacityRelease.class);
        assertEquals(ControlBuild.ATTEMPT_RELEASE_SCHEMA,release.schema());
        assertEquals(WindowsJobProcess.currentMachineId(),release.machineId());
        assertEquals(mapper.readValue(Files.readAllBytes(Path.of(fixture.releaseRef().path())),AttemptCapacityRelease.class),release);
        fixture.releaseRef().verify();
        ControlBuild.readLeaseAt(fixture.config(),release.machineId(),fixture.clock().instant());
        ObjectNode wire=mapper.valueToTree(result);var fields=new HashSet<String>();wire.fieldNames().forEachRemaining(fields::add);
        assertEquals(Set.of("path","bytes","sha256"),fields);assertEquals(result,mapper.treeToValue(wire,FileRef.class));
        byte[] original=Files.readAllBytes(fixture.config().capacityRelease());
        assertThrows(FileAlreadyExistsException.class,()->ManualCapacityReleaseMain.prepare(fixture.configRef(),fixture.releaseRef(),fixture.issuerRef(),fixture.clock()));
        assertArrayEquals(original,Files.readAllBytes(fixture.config().capacityRelease()));
    }

    @Test void exactHashesStrictTypesV1AliasForeignMachineAndMalformedArgumentsFailBeforeAnyCandidate()throws Exception {
        for(String corruption:List.of("config-hash","config-unknown","release-v1","release-machine","issuer-bool","issuer-null","args-count","bytes-lexeme","timeout-overflow","service-timeout","timeout-bool","timeout-null","timeout-float")) {
            var fixture=fixture();FileRef config=fixture.configRef(),release=fixture.releaseRef(),issuer=fixture.issuerRef();
            var mapper=ControlBuild.strictMapper();
            switch(corruption) {
                case "config-hash" -> config=new FileRef(config.path(),config.bytes(),"0".repeat(64));
                case "config-unknown" -> {var json=(ObjectNode)mapper.readTree(Files.readAllBytes(Path.of(config.path())));json.put("unrecognized",true);config=write(Path.of(config.path()),json);}
                case "timeout-overflow","service-timeout","timeout-bool","timeout-null","timeout-float" -> {
                    var json=(ObjectNode)mapper.readTree(Files.readAllBytes(Path.of(config.path())));
                    switch(corruption) {
                        case "timeout-overflow" -> json.put("timeout_seconds",ControlBuild.maximumBuildTimeoutSeconds(ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME)+1);
                        case "service-timeout" -> {json.put("target_kind","SERVICE_FAST_JAR");json.put("timeout_seconds",ControlBuild.maximumBuildTimeoutSeconds(ControlBuild.TargetKind.SERVICE_FAST_JAR)+1);}
                        case "timeout-bool" -> json.put("timeout_seconds",true);
                        case "timeout-null" -> json.putNull("timeout_seconds");
                        case "timeout-float" -> json.put("timeout_seconds",3600.5);
                        default -> throw new AssertionError(corruption);
                    }
                    config=write(Path.of(config.path()),json);
                }
                case "release-v1" -> {var json=(ObjectNode)mapper.readTree(Files.readAllBytes(Path.of(release.path())));json.put("schema","xar.java-phase1.manual-capacity-release/v1");release=write(Path.of(release.path()),json);}
                case "release-machine" -> {var json=(ObjectNode)mapper.readTree(Files.readAllBytes(Path.of(release.path())));json.put("machine_id","foreign-software-machine");release=write(Path.of(release.path()),json);}
                case "issuer-bool" -> {var json=(ObjectNode)mapper.readTree(Files.readAllBytes(Path.of(issuer.path())));((ObjectNode)json.get("authorization_source")).put("bytes",true);issuer=write(Path.of(issuer.path()),json);}
                case "issuer-null" -> {Files.writeString(Path.of(issuer.path()),"null");issuer=FileRef.measure(Path.of(issuer.path()));}
                default -> { }
            }
            String[] args=arguments(config,release,issuer);
            if(corruption.equals("args-count"))args=java.util.Arrays.copyOf(args,10);
            if(corruption.equals("bytes-lexeme"))args[1]="+"+args[1];
            var actual=args;
            assertThrows(IOException.class,()->ManualCapacityReleaseMain.prepareArguments(actual,fixture.clock()),corruption);
            assertFalse(Files.exists(fixture.config().capacityRelease()),corruption);
        }
    }

    private Fixture fixture()throws Exception { return fixture(10,ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME); }

    private Fixture fixture(int timeoutSeconds,ControlBuild.TargetKind targetKind)throws Exception {
        Path base=Files.createDirectory(temporary.resolve("software-issuer-"+sequence++)).toRealPath();
        Path source=Files.createDirectory(base.resolve("source")),work=Files.createDirectory(base.resolve("work"));
        var config=new Config(source,work,base.resolve("issued-v2.json"),"software-cli-issuer","software-writer",null,base,
                "3.10.0",timeoutSeconds,targetKind,ControlBuild.SourceLimitProfile.STANDARD_8_MIB);
        Instant observed=Instant.now().minusSeconds(1),review=observed.plusSeconds(300);
        String machine=WindowsJobProcess.currentMachineId();var mapper=ControlBuild.strictMapper();
        Path policy=base.resolve("policy.json"),authorization=base.resolve("software-authorization.txt"),reservation=base.resolve("reservation.json");
        Files.writeString(policy,"""
                {"schema":"xar-storage-retention-policy-v1","policy_version":"1.0.0","capacity":{
                "safety_floor_bytes":1000,"safety_ceiling_bytes":10000,"safety_volume_fraction":0.01,
                "default_project_quota_ceiling_bytes":1000000000,"default_project_quota_volume_fraction":1.0,"quota_override_max_hours":1}}
                """);
        Files.writeString(authorization,"software fixture only; no real budget, Maven or delegation authority");
        Files.writeString(reservation,"{\"software_fixture\":true}");
        FileRef policyRef=FileRef.measure(policy);var reservations=List.of(policyRef,FileRef.measure(reservation));
        var budget=CiBootstrap.calculate(CiBootstrap.readPolicy(Files.readAllBytes(policy)),1_000_000_000L,900_000_000L,10_000_000L,90_000_000L,1_000_000L,100_000_000L);
        Path volume=work.getRoot().toRealPath();String letter=volume.toString().substring(0,1).toUpperCase(java.util.Locale.ROOT);
        ObjectNode financial=mapper.createObjectNode();
        financial.put("schema","xar.java-phase1.resume56-r3-financial-supplement/v1").put("machine_id",machine)
                .put("status","RELEASED_EXPLICIT_ROOT_AUTHORIZED_0830_REVIEW_SUCCESSOR_WITHOUT_CAP_INCREASE").put("issuer_task","/root/budget_fast_lane")
                .put("observed_at_utc",observed.toString()).put("review_at_utc",review.toString()).put("quota_review_at_utc",review.toString())
                .put("shared_canonical_m2_growth_hold_once_bytes",64L<<20).put("whole_R3_cap_after_bytes",2_000_000L)
                .put(letter.equals("D")?"all_holds_including_current_R3_bytes":letter+"_other_unspent_holds_bytes",100_000_000L).put(letter+"_quota_bytes",budget.effectiveProjectQuota());
        financial.putNull("current_whole_project_actual_usage_bytes");financial.set("old_heads_and_policy_refs",mapper.valueToTree(reservations));
        financial.putObject("reserves").put(letter+"_system_growth",budget.systemGrowthReserve()).put(letter+"_safety",budget.safetyReserve());
        financial.putObject("fresh_observations").put("machine_id",machine).put("observed_at_utc",observed.toString()).putObject(letter)
                .put("total",budget.totalVolumeBytes()).put("used_upper",budget.currentProjectUsageConservativeUpper());
        FileRef financialRef=write(base.resolve("financial.json"),financial);
        Map<String,String> roots=Map.of("maven_repository",work.resolve("m2").toString(),"source_snapshot",work.resolve("scratch/source-"+config.attempt()).toString(),
                "build",work.resolve("build/"+config.attempt()).toString(),"private_tmp",work.resolve("scratch/"+config.attempt()+"-tmp").toString(),
                "artifacts",work.resolve("artifacts/"+config.attempt()).toString(),"logs",work.resolve("logs").toString());
        Map<String,Long> caps=Map.of("source_snapshot",100000L,"build",100000L,"private_tmp",100000L,"artifacts",100000L,"logs",100000L);
        var authority=new AttemptAccountingAuthority(ControlBuild.ATTEMPT_AUTHORITY_SCHEMA,config.attempt(),ControlBuild.FinancialLayout.CAPACITY_SUPPLEMENT18,
                financialRef,reservations,roots,caps,500000,caps,1000000,64L<<20);
        var release=new AttemptCapacityRelease(ControlBuild.ATTEMPT_RELEASE_SCHEMA,machine,observed.toString(),review.toString(),ManualBuildCapacityReleaseProducer.WIRE_STATUS,
                config.ownerTask(),policyRef,List.of(base.toString()),work.resolve("m2").toString(),work.resolve("build").toString(),work.resolve("scratch").toString(),
                Map.of("m2",1000000L,"build",1000000L,"tools",1000000L,"scratch",1000000L,"artifacts",1000000L,"metadata_logs",1000000L),
                Map.of(volume.toString(),budget),Map.of(),128000000,64000000,authority);
        var issuer=new IssuerDomain("software-owner","software-issuer",FileRef.measure(authorization),"software-fixture-only","no execution authority");
        return new Fixture(config,write(base.resolve("config-input.json"),config),write(base.resolve("release-input.json"),release),
                write(base.resolve("issuer-input.json"),issuer),Clock.fixed(observed.plusMillis(100),ZoneOffset.UTC));
    }
    private static FileRef write(Path target,Object value)throws Exception {
        Files.write(target,ControlBuild.strictMapper().writeValueAsBytes(value));return FileRef.measure(target);
    }
    private static String[] arguments(FileRef config,FileRef release,FileRef issuer) {
        return new String[]{config.path(),Long.toString(config.bytes()),config.sha256(),release.path(),Long.toString(release.bytes()),release.sha256(),issuer.path(),Long.toString(issuer.bytes()),issuer.sha256()};
    }
}
