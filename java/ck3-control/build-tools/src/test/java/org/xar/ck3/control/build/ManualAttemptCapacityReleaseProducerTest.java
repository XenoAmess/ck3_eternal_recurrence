package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.build.ManualBuildCapacityReleaseProducer.*;
import com.fasterxml.jackson.databind.JsonNode;
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

/** Source-only regressions for the shared v2 DTO and actual preparation/reader rejection boundary.
 * Temporary provenance is intentionally not a real financial release or a permission to run Maven.
 */
final class ManualAttemptCapacityReleaseProducerTest {
    @TempDir Path temporary;
    private static final Instant AT=Instant.parse("2026-10-24T00:00:00Z");
    private static final Clock CLOCK=Clock.fixed(AT.plusSeconds(10),ZoneOffset.UTC);
    private static final Set<String> SCOPES=Set.of("source_snapshot","build","private_tmp","artifacts","logs");
    private int sequence;
    private record Fixture(Config config,AttemptCapacityRelease release,IssuerDomain issuer) {}

    @Test void typedAttemptProducerReachesTheActualReaderWithCompleteSoftwareFinancialSourcesAndColdRevalidation()throws Exception {
        var fixture=readerFixture();
        var prepared=ManualBuildCapacityReleaseProducer.prepare(fixture.config(),fixture.release(),CLOCK,fixture.issuer());
        assertEquals(PreparationStatus.PREPARED_EXISTING_MANUAL_READER_ACCEPTED,prepared.status());
        assertSame(fixture.issuer(),prepared.issuer());prepared.release().verify();
        assertArrayEquals(ManualBuildCapacityReleaseProducer.encode(fixture.release()),Files.readAllBytes(fixture.config().capacityRelease()));
        ControlBuild.readLeaseAt(fixture.config(),fixture.release().machineId(),CLOCK.instant());
        assertThrows(IOException.class,()->ControlBuild.readLeaseAt(fixture.config(),fixture.release().machineId(),AT.plusSeconds(60)));
        // Cold acceptance must still read the pinned original; byte mutation cannot reuse the earlier prepared result.
        Files.writeString(Path.of(fixture.release().workpackageAccounting().financialSourceRef().path()),"changed software financial source");
        assertThrows(IOException.class,()->ControlBuild.readLeaseAt(fixture.config(),fixture.release().machineId(),CLOCK.instant()));
        prepared.release().verify();
        // This reader preflight does not perform live volume/native allocation qualification or execute Maven.
    }

    @Test void sharedAttemptDtoIsTheOnlyWireAndHasDistinctLogicalNativeAndRepositoryGrowthFields()throws Exception {
        var fixture=fixture();byte[] encoded=ManualBuildCapacityReleaseProducer.encode(fixture.release());
        var mapper=ControlBuild.strictMapper();var json=(ObjectNode)mapper.readTree(encoded);
        assertEquals(ControlBuild.ATTEMPT_RELEASE_SCHEMA,json.path("schema").textValue());
        assertEquals(WIRE_STATUS,json.path("status").textValue());
        assertEquals(fixture.config().ownerTask(),json.path("single_Maven_writer").textValue());
        assertFalse(json.has("owner_task"));assertFalse(json.has("preparation_narrative"));assertFalse(json.has("issuer_task"));
        var accounting=json.path("workpackage_accounting");
        assertEquals(SCOPES,keys(accounting.get("logical_caps_by_scope")));
        assertEquals(SCOPES,keys(accounting.get("native_caps_by_scope")));
        assertEquals(64L<<20,accounting.path("canonical_m2_growth_reservation_bytes").longValue());
        assertFalse(accounting.has("maven_repository_baseline_ref"));
        assertNotEquals(accounting.path("maximum_new_logical_bytes").longValue(),accounting.path("maximum_new_native_bytes").longValue());
        assertEquals(Set.of("path","bytes","sha256"),keys(accounting.get("financial_source_ref")));
        assertEquals(fixture.release(),mapper.readValue(encoded,AttemptCapacityRelease.class));
        assertEquals(mapper.readTree(encoded),mapper.readTree(ManualBuildCapacityReleaseProducer.encode(mapper.readValue(encoded,AttemptCapacityRelease.class))));
    }

    @Test void strictSharedDtoRejectsMissingNullWrongTypesUnknownFieldsAndOldBaselineAlias()throws Exception {
        for(String corruption:List.of("missing-authority","null-authority","bool-cap","float-cap","missing-native-cap","wrong-enum","baseline-alias","issuer-extra")) {
            var fixture=fixture();var mapper=ControlBuild.strictMapper();
            var json=(ObjectNode)mapper.readTree(ManualBuildCapacityReleaseProducer.encode(fixture.release()));
            var authority=(ObjectNode)json.get("workpackage_accounting");
            switch(corruption) {
                case "missing-authority" -> json.remove("workpackage_accounting");
                case "null-authority" -> json.putNull("workpackage_accounting");
                case "bool-cap" -> ((ObjectNode)authority.get("logical_caps_by_scope")).put("build",true);
                case "float-cap" -> ((ObjectNode)authority.get("native_caps_by_scope")).put("build",1.0);
                case "missing-native-cap" -> ((ObjectNode)authority.get("native_caps_by_scope")).remove("build");
                case "wrong-enum" -> authority.put("financial_layout","CAPACITY_SUPPLEMENT17");
                case "baseline-alias" -> authority.set("maven_repository_baseline_ref",mapper.valueToTree(fixture.issuer().authorizationSource()));
                case "issuer-extra" -> json.putObject("preparation_narrative").put("scope","not a declared v2 field");
                default -> throw new AssertionError(corruption);
            }
            assertThrows(IOException.class,()->mapper.treeToValue(json,AttemptCapacityRelease.class),corruption);
            assertFalse(Files.exists(fixture.config().capacityRelease()));
        }
    }

    @Test void foreignWriterAndUnqualifiedFinancialSourceCannotPassTheActualReaderOrOverwriteFailedCandidates()throws Exception {
        for(String corruption:List.of("writer","unqualified-financial-source")) {
            var fixture=fixture();var release=fixture.release();
            if(corruption.equals("writer")) {
                var mapper=ControlBuild.strictMapper();var json=(ObjectNode)mapper.readTree(ManualBuildCapacityReleaseProducer.encode(release));
                json.put("single_Maven_writer","foreign-software-writer");release=mapper.treeToValue(json,AttemptCapacityRelease.class);
            }
            var rejected=release;
            var failure=assertThrows(PreparationRejectedException.class,()->ManualBuildCapacityReleaseProducer.prepare(fixture.config(),rejected,CLOCK,fixture.issuer()));
            failure.retainedCandidate().verify();
            assertArrayEquals(ManualBuildCapacityReleaseProducer.encode(rejected),Files.readAllBytes(fixture.config().capacityRelease()));
            assertThrows(IOException.class,()->ControlBuild.readLeaseAt(fixture.config(),rejected.machineId(),CLOCK.instant()));
            assertThrows(FileAlreadyExistsException.class,()->ManualBuildCapacityReleaseProducer.prepare(fixture.config(),fixture.release(),CLOCK,fixture.issuer()));
            failure.retainedCandidate().verify();
        }
    }

    @Test void allOriginalSourcesAreCheckedBeforeCreatingTheAttemptFileAndClockWindowRemainsMandatory()throws Exception {
        for(String source:List.of("policy","issuer","financial","reservation")) {
            var fixture=fixture();var authority=fixture.release().workpackageAccounting();
            FileRef reference=switch(source) {
                case "policy" -> fixture.release().policyRef();case "issuer" -> fixture.issuer().authorizationSource();
                case "financial" -> authority.financialSourceRef();case "reservation" -> authority.reservationSourceRefs().getFirst();
                default -> throw new AssertionError(source);
            };
            Files.writeString(Path.of(reference.path()),"changed software source");
            assertThrows(IOException.class,()->ManualBuildCapacityReleaseProducer.prepare(fixture.config(),fixture.release(),CLOCK,fixture.issuer()));
            assertFalse(Files.exists(fixture.config().capacityRelease()));
        }
        var fixture=fixture();
        assertThrows(IOException.class,()->ManualBuildCapacityReleaseProducer.prepare(fixture.config(),fixture.release(),Clock.fixed(AT.plusSeconds(60),ZoneOffset.UTC),fixture.issuer()));
        assertFalse(Files.exists(fixture.config().capacityRelease()));
    }

    @Test void conservativeAccountingRoundtripKeepsRepositoryUnknownAndRejectsInventedZeroMeasurements()throws Exception {
        var fixture=fixture();var roots=fixture.release().workpackageAccounting().measuredRoots();
        Map<String,Long> emptyScopes=Map.of("source_snapshot",0L,"build",0L,"private_tmp",0L,"artifacts",0L,"logs",0L);
        var volume=new ControlBuild.VolumeObservation(temporary.toAbsolutePath().toString(),1_000_000,800_000,200_000,200_000,4000,900_000,1000,1000,2000);
        var accounting=new ControlBuild.WorkpackageAccounting(ControlBuild.ACCOUNTING_SCHEMA,
                ControlBuild.AccountingMode.CONSERVATIVE_VOLUME_ATTEMPT,fixture.issuer().authorizationSource(),
                fixture.release().machineId(),CLOCK.instant().toString(),roots,emptyScopes,
                ControlBuild.RepositoryAccountingState.CONSERVATIVE_VOLUME_COVERAGE,null,null,0,emptyScopes,0,List.of(volume));
        var mapper=ControlBuild.strictMapper();byte[] bytes=mapper.writeValueAsBytes(accounting);var json=mapper.readTree(bytes);
        assertTrue(json.get("maven_repository_baseline_bytes").isNull());assertTrue(json.get("maven_repository_current_bytes").isNull());
        assertEquals(accounting,mapper.readValue(bytes,ControlBuild.WorkpackageAccounting.class));
        ((ObjectNode)json).put("maven_repository_current_bytes",0);
        assertThrows(IOException.class,()->mapper.treeToValue(json,ControlBuild.WorkpackageAccounting.class));
        ((ObjectNode)json).putNull("maven_repository_current_bytes");
        ((ObjectNode)json).remove("maven_repository_baseline_bytes");
        assertThrows(IOException.class,()->mapper.treeToValue(json,ControlBuild.WorkpackageAccounting.class));
        assertFalse(Files.exists(fixture.config().capacityRelease()));
    }

    @Test void expiryDuringPreparationRetainsTheCandidateAndCannotReuseTheEntryClockForReaderEvidence()throws Exception {
        for(boolean afterReader:List.of(false,true)) {
            var fixture=readerFixture();
            var calls=new java.util.concurrent.atomic.AtomicInteger();
            Clock advancing=new Clock() {
                public java.time.ZoneId getZone(){return ZoneOffset.UTC;}
                public Clock withZone(java.time.ZoneId zone){if(!ZoneOffset.UTC.equals(zone))throw new IllegalArgumentException("UTC fixture only");return this;}
                public Instant instant(){int call=calls.getAndIncrement();return call<(afterReader?2:1)?CLOCK.instant():AT.plusSeconds(60);}
            };
            var failure=assertThrows(PreparationRejectedException.class,()->ManualBuildCapacityReleaseProducer.prepare(fixture.config(),fixture.release(),advancing,fixture.issuer()));
            failure.retainedCandidate().verify();
            assertArrayEquals(ManualBuildCapacityReleaseProducer.encode(fixture.release()),Files.readAllBytes(fixture.config().capacityRelease()));
            assertThrows(FileAlreadyExistsException.class,()->ManualBuildCapacityReleaseProducer.prepare(fixture.config(),fixture.release(),CLOCK,fixture.issuer()));
        }
    }

    private Fixture fixture()throws Exception {
        Path base=Files.createDirectory(temporary.resolve("software-attempt-"+sequence++)).toRealPath();
        Path source=Files.createDirectory(base.resolve("source")),work=Files.createDirectory(base.resolve("work"));
        var config=new Config(source,work,base.resolve("manual-v2.json"),"software-attempt","software-writer",null,base,
                "3.10.0",10,ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME,ControlBuild.SourceLimitProfile.STANDARD_8_MIB);
        Path policy=base.resolve("policy.json"),issuer=base.resolve("issuer.txt"),financial=base.resolve("financial.json"),reservation=base.resolve("reservation.json");
        Files.writeString(policy,"""
                {"schema":"xar-storage-retention-policy-v1","policy_version":"1.0.0","capacity":{
                "safety_floor_bytes":1000,"safety_ceiling_bytes":10000,"safety_volume_fraction":0.01,
                "default_project_quota_ceiling_bytes":1000000000,"default_project_quota_volume_fraction":1.0,"quota_override_max_hours":1}}
                """);
        Files.writeString(issuer,"software fixture provenance only; no real reservation or Maven authority");
        // Deliberately unqualified: no financial18 authority is invented to turn this rejection fixture into Ready.
        Files.writeString(financial,"{\"software_fixture\":\"unqualified-financial-source\"}");
        Files.writeString(reservation,"{\"software_fixture\":\"unqualified-reservation-source\"}");
        Map<String,String> roots=Map.of("maven_repository",work.resolve("m2").toString(),
                "source_snapshot",work.resolve("scratch/source-"+config.attempt()).toString(),
                "build",work.resolve("build").resolve(config.attempt()).toString(),
                "private_tmp",work.resolve("scratch/"+config.attempt()+"-tmp").toString(),
                "artifacts",work.resolve("artifacts").resolve(config.attempt()).toString(),"logs",work.resolve("logs").toString());
        Map<String,Long> caps=Map.of("source_snapshot",100000L,"build",100000L,"private_tmp",100000L,"artifacts",100000L,"logs",100000L);
        var authority=new AttemptAccountingAuthority(ControlBuild.ATTEMPT_AUTHORITY_SCHEMA,config.attempt(),ControlBuild.FinancialLayout.CAPACITY_SUPPLEMENT18,
                FileRef.measure(financial),List.of(FileRef.measure(reservation)),roots,caps,500000,caps,1000000,64L<<20);
        var volume=new CiBootstrap.VolumeBudget(1000000000,900000000,1000000,1000000,1000000,10000,100000000,1000000000,3010000);
        var release=new AttemptCapacityRelease(ControlBuild.ATTEMPT_RELEASE_SCHEMA,"software-machine",AT.toString(),AT.plusSeconds(60).toString(),
                WIRE_STATUS,config.ownerTask(),FileRef.measure(policy),List.of(base.toString()),work.resolve("m2").toString(),work.resolve("build").toString(),
                work.resolve("scratch").toString(),Map.of("m2",1000000L,"build",1000000L,"tools",1000000L,"scratch",1000000L,"artifacts",1000000L,"metadata_logs",1000000L),
                Map.of(base.toString(),volume),Map.of(),128000000,64000000,authority);
        return new Fixture(config,release,new IssuerDomain("software-owner","software-issuer",FileRef.measure(issuer),"software-only narrative","preflight test only"));
    }

    /** A complete software-only instance of the real financial18 input contract, not a copied real issuer grant. */
    private Fixture readerFixture()throws Exception {
        var fixture=fixture();var release=fixture.release();var mapper=ControlBuild.strictMapper();
        Path volumeRoot=fixture.config().workRoot().getRoot().toRealPath();
        String letter=volumeRoot.toString().substring(0,1).toUpperCase(java.util.Locale.ROOT);
        var policy=CiBootstrap.readPolicy(Files.readAllBytes(Path.of(release.policyRef().path())));
        var budget=CiBootstrap.calculate(policy,1_000_000_000L,900_000_000L,10_000_000L,90_000_000L,1_000_000L,100_000_000L);
        var references=List.of(release.policyRef(),release.workpackageAccounting().reservationSourceRefs().getFirst());
        ObjectNode financial=mapper.createObjectNode();
        financial.put("schema","xar.java-phase1.resume56-r3-financial-supplement/v1").put("machine_id",release.machineId())
                .put("status","RELEASED_EXPLICIT_ROOT_AUTHORIZED_0830_REVIEW_SUCCESSOR_WITHOUT_CAP_INCREASE")
                .put("issuer_task","/root/budget_fast_lane").put("observed_at_utc",release.observedAtUtc())
                .put("review_at_utc",release.reviewAtUtc()).put("quota_review_at_utc",release.reviewAtUtc())
                .put("shared_canonical_m2_growth_hold_once_bytes",64L<<20).put("whole_R3_cap_after_bytes",2_000_000L)
                .put(letter.equals("D")?"all_holds_including_current_R3_bytes":letter+"_other_unspent_holds_bytes",100_000_000L)
                .put(letter+"_quota_bytes",budget.effectiveProjectQuota());
        financial.set("old_heads_and_policy_refs",mapper.valueToTree(references));
        financial.putNull("current_whole_project_actual_usage_bytes");
        financial.putObject("reserves").put(letter+"_system_growth",budget.systemGrowthReserve()).put(letter+"_safety",budget.safetyReserve());
        financial.putObject("fresh_observations").put("machine_id",release.machineId()).put("observed_at_utc",release.observedAtUtc())
                .putObject(letter).put("total",budget.totalVolumeBytes()).put("used_upper",budget.currentProjectUsageConservativeUpper());
        Path source=Path.of(release.workpackageAccounting().financialSourceRef().path());Files.write(source,mapper.writeValueAsBytes(financial));
        ObjectNode json=mapper.valueToTree(release);var authority=(ObjectNode)json.get("workpackage_accounting");
        authority.set("financial_source_ref",mapper.valueToTree(FileRef.measure(source)));
        authority.set("reservation_source_refs",mapper.valueToTree(references));
        json.set("volumes",mapper.valueToTree(Map.of(volumeRoot.toString(),budget)));
        return new Fixture(fixture.config(),mapper.treeToValue(json,AttemptCapacityRelease.class),fixture.issuer());
    }
    private static Set<String> keys(JsonNode value){var keys=new HashSet<String>();value.fieldNames().forEachRemaining(keys::add);return Set.copyOf(keys);}
}
