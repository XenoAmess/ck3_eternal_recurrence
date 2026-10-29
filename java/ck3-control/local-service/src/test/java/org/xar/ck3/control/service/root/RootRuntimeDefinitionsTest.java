package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Clock;
import java.time.Instant;
import java.time.Duration;
import java.time.ZoneOffset;
import java.util.Arrays;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.zip.GZIPOutputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SingleWinnerSourceIndex;
import org.xar.ck3.control.build.SourceGraphSdkIndexProducer;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadlineCodec;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.g2.m7.schedule.OrdinaryCampaignSchedule;
import org.xar.ck3.control.planning.campaigncadence.CampaignCalendar;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityActionRoutes;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarExitTruceReads;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernanceActionPreparation;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.CoaVfs;

/** Exercises strict data/source boundaries. Fixture custody never becomes an installed runtime, lease or Game permission. */
final class RootRuntimeDefinitionsTest {
    @TempDir Path temporary;
    private static final String MACHINE="definition-fixture-machine";
    private static final String OBSERVED="2026-10-24T00:00:00Z",REVIEW="2026-10-24T01:00:00Z";
    private static final String SHA="a".repeat(64);
    private static final Clock CLOCK=Clock.fixed(Instant.parse("2026-10-24T00:30:00Z"),ZoneOffset.UTC);

    @Test void completeTypedConfigurationRoundTripsAndEveryRequiredRoleAndNullableFieldIsExplicit()throws Exception {
        Configuration producer=configuration();byte[] packet=RootRuntimeDefinitions.encodeConfiguration(producer);
        Configuration consumer=RootRuntimeDefinitions.decodeConfiguration(packet);
        assertEquals(producer,consumer);assertArrayEquals(packet,RootRuntimeDefinitions.encodeConfiguration(consumer));
        var root=(ObjectNode)StrictJson.parse(packet,RootRuntimeDefinitions.MAXIMUM_BYTES);
        assertTrue(root.get("cross_run").get("original_one_life_history").has("original_ref"));
        assertTrue(root.get("cross_run").get("original_one_life_history").get("original_ref").isNull());
        var missingLease=root.deepCopy();missingLease.remove("storage_lease_ref");reject(missingLease);
        var missingRole=root.deepCopy();((com.fasterxml.jackson.databind.node.ArrayNode)missingRole.get("sources")).remove(0);reject(missingRole);
        var duplicateRole=root.deepCopy();((ObjectNode)duplicateRole.get("sources").get(1)).set("role",duplicateRole.get("sources").get(0).get("role"));reject(duplicateRole);
        var foreignKind=root.deepCopy();((ObjectNode)foreignKind.get("sources").get(0)).put("kind","JAVA");reject(foreignKind);
        var missingOriginal=root.deepCopy();((ObjectNode)missingOriginal.get("cross_run").get("original_one_life_history")).remove("original_ref");reject(missingOriginal);
        var nullOriginalData=root.deepCopy();nullOriginalData.putNull("original_data");reject(nullOriginalData);
        var unknown=root.deepCopy();unknown.put("provided_factory",true);reject(unknown);
        var floatTimeout=root.deepCopy();((ObjectNode)floatTimeout.get("army")).put("command_read_timeout_ms",1.0);reject(floatTimeout);
        var boolIdentity=root.deepCopy();((ObjectNode)boolIdentity.get("frontend")).put("retained_frames",true);reject(boolIdentity);
        var unknownActivity=root.deepCopy();((ObjectNode)unknownActivity.get("activity").get("reads").get(0)).put("query","UNKNOWN");reject(unknownActivity);
        var missingFamily=root.deepCopy();missingFamily.remove("family");reject(missingFamily);
        var missingPair=root.deepCopy();((ObjectNode)missingPair.get("family")).remove("matrilineal_pair");reject(missingPair);
        var disabledFamily=root.deepCopy();((ObjectNode)disabledFamily.get("family")).put("family_enabled",false);reject(disabledFamily);
        var floatPair=root.deepCopy();var pair=((ObjectNode)floatPair.get("family")).putObject("matrilineal_pair");pair.put("subject_character_id",1.0);pair.put("candidate_character_id",2);reject(floatPair);
        assertThrows(IllegalArgumentException.class,()->new MatrilinealPair(1,1));
        assertEquals(new MatrilinealPair(1,2),new MatrilinealPair(1,2));
        var unknownPublic=root.deepCopy();((com.fasterxml.jackson.databind.node.ArrayNode)unknownPublic.get("public_catalog").get("required_services")).set(0,StrictJson.object());reject(unknownPublic);
        assertThrows(Exception.class,()->RootRuntimeDefinitions.decodeConfiguration("{\"schema\":1,\"schema\":2}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
    }
    @Test void typedFinalInputProducerPreservesTheWholeConfigurationAndRevalidatesMandatoryOriginals()throws Exception {
        Configuration original=configuration();
        Path application=temporary.resolve("final-application.json");Files.writeString(application,"{\"actual_fixture\":true}\n");
        FileRef applicationRef=measure(application);
        var exactData=new java.util.ArrayList<>(original.originalData());
        DataPin changed=writeData(DataRole.ORIGINAL_DRIVER_RUN_PROFILE,"rebound-run-profile.json","{}\n".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        for(int index=0;index<exactData.size();index++)if(exactData.get(index).role()==changed.role())exactData.set(index,changed);
        Configuration produced=RootRuntimeDefinitions.rebindInputs(original,applicationRef,exactData);
        assertEquals(applicationRef,produced.applicationRef());assertNotEquals(applicationRef,original.applicationRef());
        assertEquals(changed.originalRef(),produced.data(changed.role()));
        var expected=(ObjectNode)StrictJson.parse(RootRuntimeDefinitions.encodeConfiguration(original),RootRuntimeDefinitions.MAXIMUM_BYTES);
        expected.set("application_ref",ControlBuild.strictMapper().valueToTree(applicationRef));
        expected.set("original_data",ControlBuild.strictMapper().valueToTree(exactData));
        assertArrayEquals(StrictJson.canonical(expected,RootRuntimeDefinitions.MAXIMUM_BYTES),RootRuntimeDefinitions.encodeConfiguration(produced));
        assertEquals(produced,RootRuntimeDefinitions.decodeConfiguration(RootRuntimeDefinitions.encodeConfiguration(produced)));
        var missing=new java.util.ArrayList<>(exactData);missing.removeIf(row->row.role()==DataRole.ORIGINAL_DRIVER_RUN_PROFILE);
        assertThrows(IllegalArgumentException.class,()->RootRuntimeDefinitions.rebindInputs(original,applicationRef,missing));
        int retained=produced.originalData().size();exactData.clear();assertEquals(retained,produced.originalData().size());
        // This producer preserves exact refs only; fixture document content grants no runtime or import permission.
    }
    @Test void runtimeLeaseIsDistinctFromSourceBudgetAndExpiryOrMachineMismatchRejects()throws Exception {
        FileRef ref=pin(temporary.resolve("issuer.json"));
        StorageLease lease=new StorageLease(LEASE_SCHEMA,"ROOT_GAME_RUNTIME",MACHINE,"/root",OBSERVED,REVIEW,ref,ref,ref,ref,
                1048576,List.of(new RootBudget(temporary.toString(),65536)),List.of(new VolumeThreshold(temporary.toString(),0,0)));
        byte[] raw=StrictJson.canonical(ControlBuild.strictMapper().valueToTree(lease),RootRuntimeDefinitions.MAXIMUM_BYTES);
        assertEquals(lease,RootRuntimeDefinitions.decodeStorageLease(raw));
        var buildCard=(ObjectNode)StrictJson.parse(raw,RootRuntimeDefinitions.MAXIMUM_BYTES);buildCard.put("purpose","ROOT_BUILD");
        assertThrows(Exception.class,()->RootRuntimeDefinitions.decodeStorageLease(StrictJson.canonical(buildCard,RootRuntimeDefinitions.MAXIMUM_BYTES)));
        var missing=buildCard.deepCopy();missing.remove("runtime_binding_ref");
        assertThrows(Exception.class,()->RootRuntimeDefinitions.decodeStorageLease(StrictJson.canonical(missing,RootRuntimeDefinitions.MAXIMUM_BYTES)));
        assertDoesNotThrow(()->RootRuntimeDefinitions.requireCurrent(MACHINE,OBSERVED,REVIEW,MACHINE,CLOCK,"runtime lease"));
        assertThrows(IOException.class,()->RootRuntimeDefinitions.requireCurrent(MACHINE,OBSERVED,"2026-10-24T00:01:00Z",MACHINE,CLOCK,"runtime lease"));
        assertThrows(IOException.class,()->RootRuntimeDefinitions.requireCurrent(MACHINE,OBSERVED,REVIEW,"other-machine",CLOCK,"runtime lease"));
        assertThrows(IOException.class,()->RootRuntimeDefinitions.requireCurrent(MACHINE,"2026-10-24T00:31:00Z",REVIEW,MACHINE,CLOCK,"runtime lease"));
    }
    @Test void optionalOriginalRollbackProofUsesCurrentVersionAndAllMandatoryOriginalsRemainRequired()throws Exception {
        Configuration producer=configuration();
        Configuration complete=RootRuntimeDefinitions.decodeConfiguration(RootRuntimeDefinitions.encodeConfiguration(producer));
        FileRef proof=pin(temporary.resolve("required.json"));
        assertEquals(Optional.of(proof),complete.optionalData(DataRole.ROLLBACK_PROOF));
        assertThrows(IllegalArgumentException.class,()->complete.data(DataRole.ROLLBACK_PROOF));
        assertThrows(IllegalArgumentException.class,()->complete.optionalData(DataRole.FAMILY_DOMAIN));
        var root=(ObjectNode)StrictJson.parse(RootRuntimeDefinitions.encodeConfiguration(producer),RootRuntimeDefinitions.MAXIMUM_BYTES);
        assertEquals("xar.java.root-runtime-definitions/v7",root.get("schema").textValue());
        var originals=(com.fasterxml.jackson.databind.node.ArrayNode)root.get("original_data");
        int rollback=-1;
        for(int index=0;index<originals.size();index++)if("ROLLBACK_PROOF".equals(originals.get(index).get("role").textValue()))rollback=index;
        assertTrue(rollback>=0);originals.remove(rollback);
        byte[] absentPacket=StrictJson.canonical(root,RootRuntimeDefinitions.MAXIMUM_BYTES);
        Configuration absent=RootRuntimeDefinitions.decodeConfiguration(absentPacket);
        assertEquals(Optional.empty(),absent.optionalData(DataRole.ROLLBACK_PROOF));
        assertEquals(complete.data(DataRole.FAMILY_DOMAIN),absent.data(DataRole.FAMILY_DOMAIN));
        assertArrayEquals(absentPacket,RootRuntimeDefinitions.encodeConfiguration(absent));
        for(int index=0;index<originals.size();index++) {
            var missing=root.deepCopy();((com.fasterxml.jackson.databind.node.ArrayNode)missing.get("original_data")).remove(index);reject(missing);
        }
        var legacy=root.deepCopy();legacy.put("schema","xar.java.root-runtime-definitions/v1");reject(legacy);
        var priorVersion=root.deepCopy();priorVersion.put("schema","xar.java.root-runtime-definitions/v2");reject(priorVersion);
        var priorDataVersion=root.deepCopy();priorDataVersion.put("schema","xar.java.root-runtime-definitions/v3");reject(priorDataVersion);
        var priorEpisodeVersion=root.deepCopy();priorEpisodeVersion.put("schema","xar.java.root-runtime-definitions/v4");reject(priorEpisodeVersion);
        var priorTruceVersion=root.deepCopy();priorTruceVersion.put("schema","xar.java.root-runtime-definitions/v5");reject(priorTruceVersion);
        var priorUncapturedVersion=root.deepCopy();priorUncapturedVersion.put("schema","xar.java.root-runtime-definitions/v6");reject(priorUncapturedVersion);
        var explicitNull=root.deepCopy();((com.fasterxml.jackson.databind.node.ArrayNode)explicitNull.get("original_data")).addNull();reject(explicitNull);
        var duplicate=root.deepCopy();((com.fasterxml.jackson.databind.node.ArrayNode)duplicate.get("original_data")).add(originals.get(0).deepCopy());reject(duplicate);
        var unknown=root.deepCopy();((com.fasterxml.jackson.databind.node.ArrayNode)unknown.get("original_data")).addObject().put("role","SAVED_MATERIAL").set("original_ref",ControlBuild.strictMapper().valueToTree(proof));reject(unknown);
        var withProof=(ObjectNode)StrictJson.parse(RootRuntimeDefinitions.encodeConfiguration(producer),RootRuntimeDefinitions.MAXIMUM_BYTES);
        var rollbackRow=(ObjectNode)((com.fasterxml.jackson.databind.node.ArrayNode)withProof.get("original_data")).get(rollback);
        rollbackRow.putNull("original_ref");reject(withProof);
        var wrongType=(ObjectNode)StrictJson.parse(RootRuntimeDefinitions.encodeConfiguration(producer),RootRuntimeDefinitions.MAXIMUM_BYTES);
        ((ObjectNode)wrongType.get("original_data").get(rollback).get("original_ref")).put("bytes",true);reject(wrongType);
        var missingRef=(ObjectNode)StrictJson.parse(RootRuntimeDefinitions.encodeConfiguration(producer),RootRuntimeDefinitions.MAXIMUM_BYTES);
        ((ObjectNode)missingRef.get("original_data").get(rollback)).remove("original_ref");reject(missingRef);
    }
    @Test void familyOriginalDomainsHaveExplicitCurrentRolesAndRejectTheUnmappedHistoricalNames()throws Exception {
        Configuration selected=configuration();byte[] packet=RootRuntimeDefinitions.encodeConfiguration(selected);
        for(DataRole current:List.of(DataRole.FAMILY_DOMAIN,DataRole.CHILD_MATRILINEAL_DOMAIN,DataRole.DEFAULT_MARRIAGE_DOMAIN)) {
            assertEquals(pin(temporary.resolve("required.json")),selected.data(current));
            for(String historical:List.of("FAMILY_MARRIAGE","FAMILY_HEIR","FAMILY_SECRETS")) {
                var root=(ObjectNode)StrictJson.parse(packet,RootRuntimeDefinitions.MAXIMUM_BYTES);boolean found=false;
                for(var original:root.get("original_data"))if(current.name().equals(original.get("role").textValue())) {
                    ((ObjectNode)original).put("role",historical);found=true;
                }
                assertTrue(found);reject(root);
            }
        }
        assertEquals(selected,RootRuntimeDefinitions.decodeConfiguration(packet));
    }
    @Test void additionalRuntimeSourcesRequireTheirOwnJavaPinsRatherThanReconciliationAliases()throws Exception {
        Configuration producer=configuration();
        byte[] packet=RootRuntimeDefinitions.encodeConfiguration(producer);
        Configuration consumer=RootRuntimeDefinitions.decodeConfiguration(packet);
        for(SourceRole role:List.of(SourceRole.FINANCE_GIFT_PROCESS_IDENTITY,SourceRole.ARMY_WAR_READS,SourceRole.ARMY_WAR_DECODER,
                SourceRole.ARMY_WAR_EXIT_TRUCE_DEFINITION)) {
            assertEquals(SourceKind.JAVA,expectedKind(role));
            assertTrue(consumer.source(role).path().endsWith(role.name()+".java"));
            var root=(ObjectNode)StrictJson.parse(packet,RootRuntimeDefinitions.MAXIMUM_BYTES);
            var sources=(com.fasterxml.jackson.databind.node.ArrayNode)root.get("sources");int at=-1;
            for(int index=0;index<sources.size();index++)if(role.name().equals(sources.get(index).get("role").textValue()))at=index;
            assertTrue(at>=0);
            var foreign=root.deepCopy();((ObjectNode)foreign.get("sources").get(at)).put("kind","NATIVE");reject(foreign);
            var missing=root.deepCopy();((com.fasterxml.jackson.databind.node.ArrayNode)missing.get("sources")).remove(at);reject(missing);
            var aliased=root.deepCopy();((ObjectNode)aliased.get("sources").get(at)).put("role",SourceRole.ARMY_RECONCILIATION_DECODER.name());reject(aliased);
        }
    }
    @Test void truceReconciliationSourcesConsumeTheirOwnMandatoryDefinitionAndTheExistingClosedDecoder()throws Exception {
        Configuration consumer=RootRuntimeDefinitions.decodeConfiguration(RootRuntimeDefinitions.encodeConfiguration(configuration()));
        var actualSources=new ArmyWarExitTruceReads.Sources(consumer.source(SourceRole.ARMY_WAR_EXIT_TRUCE_DEFINITION),
                consumer.source(SourceRole.ARMY_CLOSED_DECODER));
        assertSame(consumer.source(SourceRole.ARMY_WAR_EXIT_TRUCE_DEFINITION),actualSources.definition());
        assertSame(consumer.source(SourceRole.ARMY_CLOSED_DECODER),actualSources.decoder());
        assertNotEquals(consumer.source(SourceRole.ARMY_RECONCILIATION_DEFINITION),actualSources.definition());
        var root=(ObjectNode)StrictJson.parse(RootRuntimeDefinitions.encodeConfiguration(consumer),RootRuntimeDefinitions.MAXIMUM_BYTES);
        int at=-1;
        for(int index=0;index<root.get("sources").size();index++)if("ARMY_WAR_EXIT_TRUCE_DEFINITION".equals(root.get("sources").get(index).get("role").textValue()))at=index;
        assertTrue(at>=0);
        var wrong=root.deepCopy();((ObjectNode)wrong.get("sources").get(at).get("selected").get("source_ref")).put("bytes",true);reject(wrong);
        var wrongTarget=root.deepCopy();((ObjectNode)wrongTarget.get("sources").get(at).get("selected")).put("target_relative",
                "native-transport/src/main/java/fixture/OrdinaryGameplay.java");reject(wrongTarget);
        // These exact source selections construct only the typed Sources value, never a catalog or reconciliation permission.
    }
    @Test void actualOriginalDriverRunProfileProducerFlowsThroughTheMandatoryRoleReaderWithoutDefaultingLegacyImport()throws Exception {
        Path environment=temporary.resolve("run-profile-environment.json");Files.writeString(environment,"{}\n");
        ExactRef environmentRef=exact(measure(environment));
        // This reference exercises configuration data only; no policy original, PreparedFixture or Game permission is claimed.
        var fixturePolicyRef=new ExactRef(temporary.resolve("fixture-policy-source.json").toString(),37,"b".repeat(64));
        var startupCaseRef=new ExactRef(temporary.resolve("startup-case-source.json").toString(),41,"c".repeat(64));
        List<RootFrozenRunProfile.ImportMode> modes=List.of(new RootFrozenRunProfile.DisabledFreshRobert(),
                new RootFrozenRunProfile.Enabled(temporary.resolve("managed-state")),new RootFrozenRunProfile.DisabledFreshFixture(fixturePolicyRef),
                new RootFrozenRunProfile.DisabledFreshFixture(fixturePolicyRef,Optional.of(startupCaseRef)),
                new RootFrozenRunProfile.EnabledNativeCampaign(temporary.resolve("managed-native-state")));
        for(int index=0;index<modes.size();index++) {
            boolean fixture=modes.get(index) instanceof RootFrozenRunProfile.DisabledFreshFixture;
            boolean savedNative=modes.get(index) instanceof RootFrozenRunProfile.EnabledNativeCampaign;
            var produced=new RootFrozenRunProfile.Request(MACHINE,Instant.parse(OBSERVED),Instant.parse(REVIEW),
                    "fixture-request","fixture-session",environmentRef,
                    fixture||savedNative?RootFrozenRunProfile.LifecycleMode.NATIVE_CAMPAIGN:RootFrozenRunProfile.LifecycleMode.ROGUE_ONE_LIFE,
                    false,modes.get(index));
            byte[] packet=RootFrozenRunProfile.encode(produced);
            DataPin actual=writeData(DataRole.ORIGINAL_DRIVER_RUN_PROFILE,"run-profile-"+index+".json",packet);
            Configuration selected=selectData(configuration(),actual);FileRef reference=selected.data(DataRole.ORIGINAL_DRIVER_RUN_PROFILE);
            var decoded=RootFrozenRunProfile.decode(RootRuntimeDefinitions.readData(new DataPin(DataRole.ORIGINAL_DRIVER_RUN_PROFILE,reference)));
            assertEquals(produced,decoded);assertArrayEquals(packet,RootFrozenRunProfile.encode(decoded));
            for(String version:List.of("v1","v2","v3")) {
                var previousSchema=(ObjectNode)StrictJson.parse(packet);previousSchema.put("schema","xar.java-original-driver-import-run-profile/"+version);
                DataPin staleProfile=writeData(DataRole.ORIGINAL_DRIVER_RUN_PROFILE,"old-profile-schema-"+version+"-"+index+".json",StrictJson.canonical(previousSchema));
                assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.decode(RootRuntimeDefinitions.readData(staleProfile)));
            }
            if(fixture) {
                assertEquals(fixturePolicyRef,((RootFrozenRunProfile.DisabledFreshFixture)decoded.legacyImport()).policySource());
                var expectedCase=((RootFrozenRunProfile.DisabledFreshFixture)modes.get(index)).startupCaseSource();
                assertEquals(expectedCase,((RootFrozenRunProfile.DisabledFreshFixture)decoded.legacyImport()).startupCaseSource());
                var fixtureWire=(ObjectNode)StrictJson.parse(packet);assertTrue(fixtureWire.get("legacy_import").has("startup_case_source"));
                assertEquals(expectedCase.isEmpty(),fixtureWire.get("legacy_import").get("startup_case_source").isNull());
                for(String invalid:List.of("missing","null","boolean","float","string")) {
                    var changed=(ObjectNode)StrictJson.parse(packet);var input=(ObjectNode)changed.get("legacy_import");
                    switch(invalid) {
                        case "missing"->input.remove("policy_source");
                        case "null"->input.putNull("policy_source");
                        case "boolean"->((ObjectNode)input.get("policy_source")).put("bytes",true);
                        case "float"->((ObjectNode)input.get("policy_source")).put("bytes",37.0);
                        case "string"->((ObjectNode)input.get("policy_source")).put("bytes","37");
                        default->throw new AssertionError("unknown regression input");
                    }
                    byte[] malformed=ControlBuild.strictMapper().writeValueAsBytes(changed);
                    assertTrue(malformed.length>0&&malformed.length<=RootFrozenRunProfile.MAXIMUM_REQUEST_BYTES);
                    if("float".equals(invalid))assertTrue(StrictJson.parse(malformed).at("/legacy_import/policy_source/bytes").isFloatingPointNumber());
                    DataPin invalidPolicy=writeData(DataRole.ORIGINAL_DRIVER_RUN_PROFILE,"invalid-fixture-policy-"+index+"-"+invalid+".json",malformed);
                    assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.decode(RootRuntimeDefinitions.readData(invalidPolicy)));
                }
                for(String invalid:List.of("missing","boolean","float","string")) {
                    var changed=(ObjectNode)StrictJson.parse(packet);var input=(ObjectNode)changed.get("legacy_import");
                    switch(invalid) {
                        case "missing"->input.remove("startup_case_source");
                        case "boolean"->input.put("startup_case_source",true);
                        case "float"->input.put("startup_case_source",41.0);
                        case "string"->input.put("startup_case_source",startupCaseRef.path());
                        default->throw new AssertionError("unknown regression input");
                    }
                    byte[] malformed=ControlBuild.strictMapper().writeValueAsBytes(changed);
                    assertTrue(malformed.length>0&&malformed.length<=RootFrozenRunProfile.MAXIMUM_REQUEST_BYTES);
                    if("float".equals(invalid))assertTrue(StrictJson.parse(malformed).at("/legacy_import/startup_case_source").isFloatingPointNumber());
                    DataPin invalidCase=writeData(DataRole.ORIGINAL_DRIVER_RUN_PROFILE,"invalid-startup-case-"+index+"-"+invalid+".json",malformed);
                    assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.decode(RootRuntimeDefinitions.readData(invalidCase)));
                }
                for(String invalid:List.of("rogue_one_life","ordinary_campaign_succession")) {
                    var wrongLifecycle=(ObjectNode)StrictJson.parse(packet);wrongLifecycle.put("lifecycle",invalid);
                    DataPin invalidLifecycle=writeData(DataRole.ORIGINAL_DRIVER_RUN_PROFILE,"fixture-wrong-lifecycle-"+index+"-"+invalid+".json",StrictJson.canonical(wrongLifecycle));
                    assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.decode(RootRuntimeDefinitions.readData(invalidLifecycle)));
                }
                var wrongPact=(ObjectNode)StrictJson.parse(packet);wrongPact.put("ordinary_campaign_no_pact",true);
                DataPin invalidPact=writeData(DataRole.ORIGINAL_DRIVER_RUN_PROFILE,"fixture-wrong-pact-"+index+".json",StrictJson.canonical(wrongPact));
                assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.decode(RootRuntimeDefinitions.readData(invalidPact)));
            }
            if(savedNative) {
                var saved=(RootFrozenRunProfile.EnabledNativeCampaign)decoded.legacyImport();
                assertEquals(temporary.resolve("managed-native-state"),saved.stateDirectory());
                var savedWire=(ObjectNode)StrictJson.parse(packet);var savedImport=savedWire.get("legacy_import");
                assertEquals("ENABLED_NATIVE_CAMPAIGN",savedImport.get("kind").textValue());assertEquals(2,savedImport.size());
                assertFalse(savedImport.has("policy_source"));assertFalse(savedImport.has("startup_case_source"));
                for(String invalid:List.of("missing","null","boolean","float","relative","fixture-policy","fixture-case")) {
                    var changed=(ObjectNode)StrictJson.parse(packet);var input=(ObjectNode)changed.get("legacy_import");
                    switch(invalid) {
                        case "missing"->input.remove("state_directory");
                        case "null"->input.putNull("state_directory");
                        case "boolean"->input.put("state_directory",true);
                        case "float"->input.put("state_directory",1.0);
                        case "relative"->input.put("state_directory","relative-state");
                        case "fixture-policy"->input.putNull("policy_source");
                        case "fixture-case"->input.putNull("startup_case_source");
                        default->throw new AssertionError("unknown regression input");
                    }
                    byte[] malformed=ControlBuild.strictMapper().writeValueAsBytes(changed);
                    assertTrue(malformed.length>0&&malformed.length<=RootFrozenRunProfile.MAXIMUM_REQUEST_BYTES);
                    if("float".equals(invalid))assertTrue(StrictJson.parse(malformed).at("/legacy_import/state_directory").isFloatingPointNumber());
                    DataPin invalidSaved=writeData(DataRole.ORIGINAL_DRIVER_RUN_PROFILE,"invalid-saved-native-"+invalid+".json",malformed);
                    assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.decode(RootRuntimeDefinitions.readData(invalidSaved)));
                }
                for(String invalid:List.of("rogue_one_life","ordinary_campaign_succession")) {
                    var changed=(ObjectNode)StrictJson.parse(packet);changed.put("lifecycle",invalid);
                    DataPin invalidSaved=writeData(DataRole.ORIGINAL_DRIVER_RUN_PROFILE,"saved-native-wrong-lifecycle-"+invalid+".json",StrictJson.canonical(changed));
                    assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.decode(RootRuntimeDefinitions.readData(invalidSaved)));
                }
                var changed=(ObjectNode)StrictJson.parse(packet);changed.put("ordinary_campaign_no_pact",true);
                DataPin invalidSaved=writeData(DataRole.ORIGINAL_DRIVER_RUN_PROFILE,"saved-native-wrong-pact.json",StrictJson.canonical(changed));
                assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.decode(RootRuntimeDefinitions.readData(invalidSaved)));
            }
            var missing=(ObjectNode)StrictJson.parse(packet);missing.remove("legacy_import");
            DataPin missingMode=writeData(DataRole.ORIGINAL_DRIVER_RUN_PROFILE,"missing-import-"+index+".json",StrictJson.canonical(missing));
            assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.decode(RootRuntimeDefinitions.readData(missingMode)));
            var wrong=(ObjectNode)StrictJson.parse(packet);wrong.put("ordinary_campaign_no_pact",1);
            DataPin wrongMode=writeData(DataRole.ORIGINAL_DRIVER_RUN_PROFILE,"wrong-import-"+index+".json",StrictJson.canonical(wrong));
            assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.decode(RootRuntimeDefinitions.readData(wrongMode)));
            var unknown=(ObjectNode)StrictJson.parse(packet);((ObjectNode)unknown.get("legacy_import")).put("kind","EMPTY_SEED");
            DataPin unknownMode=writeData(DataRole.ORIGINAL_DRIVER_RUN_PROFILE,"unknown-import-"+index+".json",StrictJson.canonical(unknown));
            assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.decode(RootRuntimeDefinitions.readData(unknownMode)));
            Files.writeString(Path.of(actual.originalRef().path()),"{}\n");assertThrows(IOException.class,()->RootRuntimeDefinitions.readData(actual));
        }
        // decode retains explicit configuration only. The private FrozenRunProfile requires the actual same plan/policy readExact path.
    }
    @Test void prisonerCurrentEpisodeLedgerIsMandatoryInBothTheSourceRoleAndTheSharedDomainClosure()throws Exception {
        Configuration producer=configuration();ExactRef expected=producer.source(SourceRole.PRISONER_EPISODE_LEDGER);
        assertTrue(producer.closure(ClosureRole.PRISONER_DOMAIN).contains(expected));
        byte[] packet=RootRuntimeDefinitions.encodeConfiguration(producer);
        Configuration decoded=RootRuntimeDefinitions.decodeConfiguration(packet);
        assertEquals(expected,decoded.source(SourceRole.PRISONER_EPISODE_LEDGER));
        var root=(ObjectNode)StrictJson.parse(packet,RootRuntimeDefinitions.MAXIMUM_BYTES);
        int closureAt=-1,sourceAt=-1;
        for(int index=0;index<root.get("closures").size();index++)if("PRISONER_DOMAIN".equals(root.get("closures").get(index).get("role").textValue()))closureAt=index;
        assertTrue(closureAt>=0);
        var sources=(com.fasterxml.jackson.databind.node.ArrayNode)root.get("closures").get(closureAt).get("sources");
        for(int index=0;index<sources.size();index++)if(expected.path().equals(sources.get(index).get("source_ref").get("path").textValue()))sourceAt=index;
        assertTrue(sourceAt>=0);
        var missing=root.deepCopy();((com.fasterxml.jackson.databind.node.ArrayNode)missing.get("closures").get(closureAt).get("sources")).remove(sourceAt);reject(missing);
        var changed=root.deepCopy();((ObjectNode)changed.get("closures").get(closureAt).get("sources").get(sourceAt).get("source_ref")).put("sha256","b".repeat(64));reject(changed);
    }
    @Test void actualFullGraphExporterFeedsSdkReaderAndOriginalInputWithoutAHandwrittenIndex()throws Exception {
        // The complete CI must supply actual shared producer artifacts. Absence is a hard NOT_RUN prerequisite failure.
        FileRef input=requiredIndexFixture("xar.sourceIndex.actualInput"),plan=requiredIndexFixture("xar.sourceIndex.actualPlan");
        Clock clock=Clock.fixed(Instant.now(),ZoneOffset.UTC);String machine=WindowsJobProcess.currentMachineId();
        Path output=temporary.resolve("actual-sdk-index");
        var request=new SourceGraphSdkIndexProducer.Request(SourceGraphSdkIndexProducer.REQUEST_SCHEMA,machine,input,plan,output.toString());
        Path requestPath=temporary.resolve("actual-index-export-request.json");
        Files.write(requestPath,ControlBuild.strictMapper().writeValueAsBytes(request));
        var exported=SourceGraphSdkIndexProducer.export(measure(requestPath),machine,clock);
        var artifact=exported.receipt().index();
        SingleWinnerSourceIndex produced=SourceGraphSdkIndexProducer.readIndex(artifact,machine,clock);
        SourceIndex sdkInput=new SourceIndex(artifact.compressedRef(),artifact.uncompressedBytes(),artifact.uncompressedSha256());
        List<SelectedSource> converted=RootRuntimeDefinitions.readSourceIndex(sdkInput,machine,clock);
        assertEquals(produced.selectedFiles().stream().map(row->new SelectedSource(row.targetRelative(),exact(row.sourceRef()))).toList(),converted);
        assertEquals(input,RootRuntimeDefinitions.sourceIndexOriginalInput(sdkInput));
        assertEquals(input,produced.inputRef());assertFalse(produced.parentPomOrderOnlySupersedesInput02());
        assertEquals(converted.size(),exported.receipt().javaWinnerFiles());
        assertEquals(exported.receipt().finalFiles(),exported.receipt().javaWinnerFiles()+exported.receipt().excludedNonJavaFiles());
        assertTrue(converted.stream().allMatch(row->row.targetRelative().endsWith(".java")&&row.sourceRef().bytes()>0));
        assertEquals(SourceGraphSdkIndexProducer.STATUS,produced.status());
        assertEquals(converted,RootRuntimeDefinitions.readSourceIndex(sdkInput,"foreign-sdk-index-machine",clock));
        assertEquals(converted,RootRuntimeDefinitions.readSourceIndex(sdkInput,machine,Clock.fixed(clock.instant().minusSeconds(1),ZoneOffset.UTC)));
        SourceIndex wrong=new SourceIndex(sdkInput.compressedRef(),sdkInput.uncompressedBytes(),"0".repeat(64));
        assertThrows(IOException.class,()->RootRuntimeDefinitions.readSourceIndex(wrong,machine,clock));
        assertThrows(IllegalArgumentException.class,()->new SourceIndex(sdkInput.compressedRef(),sdkInput.uncompressedBytes(),"A".repeat(64)));
        // An ancestry accessor returns recorded metadata without reopening the historical ancestry file.
        assertEquals(input,RootRuntimeDefinitions.sourceIndexOriginalInput(sdkInput));
        // DATA composition preserves the declared groups; source graph export is an explicit separate operation.
        Configuration fixture=configuration();var physical=productionPhysical(fixture,sdkInput,converted);
        var domains=new RootRuntimeDefinitionConfigurationAssembler.DeclaredDomainInputs(fixture.governance(),fixture.finance(),fixture.army(),
                fixture.prisoners(),fixture.family(),fixture.frontend(),fixture.interactions(),fixture.activity(),fixture.crossRun(),
                fixture.incidents(),fixture.publicCatalog(),fixture.startup());
        var made=RootRuntimeDefinitionConfigurationAssembler.productionConfiguration(physical,domains,machine,
                clock.instant(),clock.instant().plusSeconds(600),clock);
        var consumer=RootRuntimeDefinitions.decodeConfiguration(RootRuntimeDefinitions.encodeConfiguration(made));
        assertEquals(made,consumer);assertEquals(physical.sources(),consumer.sources());
        assertEquals(physical.closures(),consumer.closures());assertEquals(physical.originalData(),consumer.originalData());
        assertEquals(sdkInput,consumer.sourceIndex());assertEquals(domains.startup(),consumer.startup());
    }
    private static SelectedSource indexClass(List<SelectedSource> winners,String name) {
        var found=winners.stream().filter(row->row.targetRelative().endsWith("/src/main/java/"+name.replace('.','/')+".java")).toList();
        assertEquals(1,found.size(),name);return found.getFirst();
    }
    private static Configuration withoutConfiguredTarget(byte[] packet,String target)throws IOException {
        var changed=(ObjectNode)StrictJson.parse(packet,RootRuntimeDefinitions.MAXIMUM_BYTES);
        for(var closure:changed.get("closures")) {
            var rows=(com.fasterxml.jackson.databind.node.ArrayNode)closure.get("sources");
            for(int index=rows.size()-1;index>=0;index--)if(target.equals(rows.get(index).get("target_relative").textValue()))rows.remove(index);
        }
        return RootRuntimeDefinitions.decodeConfiguration(StrictJson.canonical(changed,RootRuntimeDefinitions.MAXIMUM_BYTES));
    }
    private static RootRuntimeDefinitionConfigurationAssembler.PhysicalOriginals productionPhysical(Configuration fixture,SourceIndex index,List<SelectedSource> winners) {
        var sway=new java.util.ArrayList<SelectedSource>();
        for(String name:List.of("org.xar.ck3.control.service.root.RootPublicPauseRuntime","org.xar.ck3.control.service.root.RootPublicPauseStepProducts",
                "org.xar.ck3.control.service.root.RootPublicPausePublicResult","org.xar.ck3.control.service.root.RootPublicPauseArchiveClassifier",
                "org.xar.ck3.control.application.advance.GenericPublicPauseRecovery","org.xar.ck3.control.application.effects.control.ControlSequenceObservation"))
            sway.add(indexClass(winners,name));
        sway.add(fixture.sources().stream().filter(row->row.role()==SourceRole.FRONTEND_ORIGINAL_DRIVER).findFirst().orElseThrow().selected());
        var closures=fixture.closures().stream().map(row->row.role()==ClosureRole.SWAY?new ProducerClosure(row.role(),sway):row).toList();
        return new RootRuntimeDefinitionConfigurationAssembler.PhysicalOriginals(fixture.applicationRef(),fixture.storageLeaseRef(),fixture.nativeLaunchPlanRef(),
                fixture.runtimePackageRequestRef(),index,fixture.sources(),closures,fixture.originalData());
    }
    private SourceIndex writeIndexFixture(String name,ObjectNode graph)throws Exception {
        byte[] raw=ControlBuild.strictMapper().writeValueAsBytes(graph);Path compressed=temporary.resolve(name+".json.gz");
        try(var output=new GZIPOutputStream(Files.newOutputStream(compressed))){output.write(raw);}
        return new SourceIndex(measure(compressed),raw.length,hash(raw));
    }
    @Test void everyNewRuntimeDataOriginalIsMandatoryAndRetainsItsExactProducerRef()throws Exception {
        byte[] packet=RootRuntimeDefinitions.encodeConfiguration(configuration());
        Configuration decoded=RootRuntimeDefinitions.decodeConfiguration(packet);
        for(DataRole role:runtimeDataRoles()) {
            assertEquals(pin(temporary.resolve("required.json")),decoded.data(role));
            var root=(ObjectNode)StrictJson.parse(packet,RootRuntimeDefinitions.MAXIMUM_BYTES);
            var originals=(com.fasterxml.jackson.databind.node.ArrayNode)root.get("original_data");int at=-1;
            for(int index=0;index<originals.size();index++)if(role.name().equals(originals.get(index).get("role").textValue()))at=index;
            assertTrue(at>=0);
            var missing=root.deepCopy();((com.fasterxml.jackson.databind.node.ArrayNode)missing.get("original_data")).remove(at);reject(missing);
            var nil=root.deepCopy();((ObjectNode)nil.get("original_data").get(at)).putNull("original_ref");reject(nil);
            var wrong=root.deepCopy();((ObjectNode)wrong.get("original_data").get(at).get("original_ref")).put("bytes",true);reject(wrong);
            var duplicated=root.deepCopy();((com.fasterxml.jackson.databind.node.ArrayNode)duplicated.get("original_data")).add(originals.get(at).deepCopy());reject(duplicated);
        }
        assertArrayEquals(packet,RootRuntimeDefinitions.encodeConfiguration(decoded));
    }
    @Test void runtimeDataPhysicalReadsUseTheSamePerRoleBoundAsTheTypedEnvelope()throws Exception {
        for(DataRole role:List.of(DataRole.FAMILY_DOMAIN,DataRole.CHILD_MATRILINEAL_DOMAIN,DataRole.DEFAULT_MARRIAGE_DOMAIN))
            assertEquals(org.xar.ck3.control.continuity.ContinuityJson.DOMAIN_MAX_BYTES,maximumDataBytes(role));
        assertEquals(RootFrozenRunProfile.MAXIMUM_REQUEST_BYTES,maximumDataBytes(DataRole.ORIGINAL_DRIVER_RUN_PROFILE));
        assertEquals(org.xar.ck3.control.build.OriginalMcpCapture.CONTROL_MAX,maximumDataBytes(DataRole.ORIGINAL_MCP_CAPTURE_RECEIPT));
        assertEquals(4096,maximumDataBytes(DataRole.LIFE_SETTINGS));
        assertEquals(4096,maximumDataBytes(DataRole.ADVANCE_TIMINGS));
        assertEquals(65536,maximumDataBytes(DataRole.CAMPAIGN_DEADLINE));
        assertEquals(65536,maximumDataBytes(DataRole.REMAINING_DOMAIN_SETTINGS));
        assertEquals(1<<20,maximumDataBytes(DataRole.NATIVE_DOMAIN_ORIGINALS));
        assertEquals(org.xar.ck3.control.contracts.evidence.PortableEvidenceJson.MANIFEST_LIMIT,
                maximumDataBytes(DataRole.PORTABLE_EVENT_EVIDENCE_MANIFEST));
        for(DataRole role:runtimeDataRoles()) {
            Path path=temporary.resolve(role.name()+".json");Files.writeString(path,"{\"actual_original\":true}\n");
            FileRef actual=measure(path);DataPin pin=new DataPin(role,actual);
            assertArrayEquals(Files.readAllBytes(path),RootRuntimeDefinitions.readData(pin));
            long tooLarge=(long)maximumDataBytes(role)+1;
            assertThrows(IllegalArgumentException.class,()->new DataPin(role,new FileRef(path.toString(),tooLarge,SHA)));
            Files.writeString(path,"{\"actual_original\":false}\n");
            assertThrows(IOException.class,()->RootRuntimeDefinitions.readData(pin));
        }
    }
    @Test void actualCampaignDeadlineProducerFlowsThroughThePhysicalRoleReaderIntoTheUniqueConsumer()throws Exception {
        var expected=CampaignDeadline.configure(new CampaignDeadline.Founding("definition-campaign","1066.9.15",
                java.math.BigInteger.valueOf(CampaignCalendar.dateToRaw("1066.9.15")),360),
                OrdinaryCampaignSchedule::calendar,Optional.empty());
        byte[] produced=CampaignDeadlineCodec.encodeConfiguration(expected);
        DataPin original=writeData(DataRole.CAMPAIGN_DEADLINE,"actual-deadline.json",produced);
        Configuration selected=selectData(configuration(),original);
        FileRef reference=selected.data(DataRole.CAMPAIGN_DEADLINE);
        var retained=new RootCampaignPoliciesFactory.BoundDeadline(exact(reference),RootRuntimeDefinitions.readData(new DataPin(DataRole.CAMPAIGN_DEADLINE,reference)));
        assertEquals(expected,retained.configuration());
        var wrong=(ObjectNode)StrictJson.parse(produced);wrong.put("months",true);
        DataPin malformed=writeData(DataRole.CAMPAIGN_DEADLINE,"wrong-deadline.json",StrictJson.canonical(wrong));
        assertThrows(IllegalArgumentException.class,()->new RootCampaignPoliciesFactory.BoundDeadline(
                exact(malformed.originalRef()),RootRuntimeDefinitions.readData(malformed)));
        Files.writeString(Path.of(original.originalRef().path()),"{}\n");
        assertThrows(IOException.class,()->RootRuntimeDefinitions.readData(original));
    }
    @Test void actualLifeSettingsProducerFlowsThroughThePhysicalRoleReaderAndExactBoundConsumer()throws Exception {
        RawJson produced=RootAdvanceRuntimeFacts.Settings.encode(true,true,true);
        DataPin original=writeData(DataRole.LIFE_SETTINGS,"actual-life-settings.json",produced.bytes());
        Configuration selected=selectData(configuration(),original);FileRef reference=selected.data(DataRole.LIFE_SETTINGS);
        var retained=RootAdvanceRuntimeFacts.Settings.decode(exact(reference),
                new RawJson(RootRuntimeDefinitions.readData(new DataPin(DataRole.LIFE_SETTINGS,reference))));
        assertEquals(exact(reference),retained.original());
        assertTrue(retained.crownQueryEnabled());assertTrue(retained.crownPausedQueryEnabled());assertTrue(retained.warDailyWatchEnabled());
        var wrong=(ObjectNode)StrictJson.parse(produced.bytes());wrong.put("war_daily_watch_enabled",1);
        DataPin malformed=writeData(DataRole.LIFE_SETTINGS,"wrong-life-settings.json",StrictJson.canonical(wrong));
        assertThrows(IllegalArgumentException.class,()->RootAdvanceRuntimeFacts.Settings.decode(
                exact(malformed.originalRef()),new RawJson(RootRuntimeDefinitions.readData(malformed))));
        Files.writeString(Path.of(original.originalRef().path()),"{}\n");
        assertThrows(IOException.class,()->RootRuntimeDefinitions.readData(original));
    }
    @Test void actualAdvanceTimingProducerFlowsThroughThePhysicalRoleReaderIntoTheUniqueConsumer()throws Exception {
        RawJson produced=RootAdvanceInfrastructureFactory.Timings.encode(16,Duration.ofSeconds(1),Duration.ofSeconds(2));
        DataPin original=writeData(DataRole.ADVANCE_TIMINGS,"actual-advance-timings.json",produced.bytes());
        Configuration selected=selectData(configuration(),original);FileRef reference=selected.data(DataRole.ADVANCE_TIMINGS);
        var retained=RootAdvanceInfrastructureFactory.Timings.decode(exact(reference),
                new RawJson(RootRuntimeDefinitions.readData(new DataPin(DataRole.ADVANCE_TIMINGS,reference))));
        assertEquals(exact(reference),retained.original());assertEquals(16,retained.maximumFrames());
        assertEquals(Duration.ofSeconds(1),retained.commandTimeout());assertEquals(Duration.ofSeconds(2),retained.advanceTimeout());
        var wrong=(ObjectNode)StrictJson.parse(produced.bytes());wrong.put("maximum_frames",true);
        DataPin malformed=writeData(DataRole.ADVANCE_TIMINGS,"wrong-advance-timings.json",StrictJson.canonical(wrong));
        assertThrows(IllegalArgumentException.class,()->RootAdvanceInfrastructureFactory.Timings.decode(
                exact(malformed.originalRef()),new RawJson(RootRuntimeDefinitions.readData(malformed))));
        Files.writeString(Path.of(original.originalRef().path()),"{}\n");
        assertThrows(IOException.class,()->RootRuntimeDefinitions.readData(original));
    }
    @Test void actualNativeProvenanceProducerFlowsThroughTheRoleReaderWithoutJavaSourceStandIns()throws Exception {
        var originals=new java.util.ArrayList<RootRuntimeNativeOriginals.Original>();
        for(var role:RootRuntimeNativeOriginals.Role.values()) {
            Path path=temporary.resolve(role.name()).resolve(Path.of(role.repositoryRelative()).getFileName());
            Files.createDirectory(path.getParent());Files.writeString(path,"finite source provenance fixture "+role.name()+"\n");
            originals.add(new RootRuntimeNativeOriginals.Original(role,role.repositoryRelative(),measure(path)));
        }
        Clock clock=Clock.systemUTC();String now=clock.instant().toString(),review=clock.instant().plusSeconds(3600).toString();
        var producer=new RootRuntimeNativeOriginals.Configuration(RootRuntimeNativeOriginals.SCHEMA,
                org.xar.ck3.control.build.WindowsJobProcess.currentMachineId(),now,review,originals);
        DataPin original=writeData(DataRole.NATIVE_DOMAIN_ORIGINALS,"actual-native-originals.json",RootRuntimeNativeOriginals.encode(producer));
        Configuration selected=selectData(configuration(),original);FileRef reference=selected.data(DataRole.NATIVE_DOMAIN_ORIGINALS);
        assertEquals(producer,RootRuntimeNativeOriginals.decode(RootRuntimeDefinitions.readData(new DataPin(DataRole.NATIVE_DOMAIN_ORIGINALS,reference))));
        var bound=RootRuntimeNativeOriginals.readExact(reference,clock);assertEquals(producer,bound.configuration());
        assertEquals(originals.size()+1,bound.retainedOriginals().size());bound.requireCurrent(clock);
        var first=originals.getFirst();
        assertThrows(IllegalArgumentException.class,()->new RootRuntimeNativeOriginals.Original(first.role(),first.repositoryRelative(),
                pin(temporary.resolve("JavaTarget.java"))));
        Path actual=Path.of(first.original().path());var time=Files.getLastModifiedTime(actual);
        byte[] changed=Files.readAllBytes(actual);changed[0]='!';Files.write(actual,changed);Files.setLastModifiedTime(actual,time);
        assertThrows(IOException.class,()->bound.requireCurrent(clock));
        // This test never supplies a NativeLaunchPlan or invokes requireQualifiedCut: provenance grants no Native permission.
    }
    @Test void actualDomainSettingsProducerFlowsThroughTheRoleReaderAndRetainsItsPolicyOriginals()throws Exception {
        Clock clock=Clock.systemUTC();
        var producer=actualDomainSettingsFixture(temporary.resolve("domain-settings"),clock);
        DataPin original=writeData(DataRole.REMAINING_DOMAIN_SETTINGS,"actual-domain-settings.json",RootRuntimeDomainSettings.encode(producer));
        Configuration selected=selectData(configuration(),original);FileRef reference=selected.data(DataRole.REMAINING_DOMAIN_SETTINGS);
        assertEquals(producer,RootRuntimeDomainSettings.decode(RootRuntimeDefinitions.readData(new DataPin(DataRole.REMAINING_DOMAIN_SETTINGS,reference))));
        var retained=RootRuntimeDomainSettings.readExact(reference,clock);assertEquals(producer,retained.configuration());
        assertEquals(10,retained.retainedOriginals().size());retained.requireCurrent(clock);
        assertNull(producer.stockRead());assertNull(retained.configuration().stockRead());
        assertTrue(retained.retainedOriginals().containsAll(producer.normalExit().originals()));
        assertTrue(retained.retainedOriginals().contains(producer.coaReadLimits().original()));
        assertEquals(new CoaVfs.Limits(65536,32768),retained.configuration().coaReadLimits().limits());
        var input=retained.configuration().normalExit().input();
        assertEquals(producer.normalExit().inventory(),input.inventory());
        assertEquals(producer.normalExit().originalManagedProfile(),input.originalManagedProfile());
        assertEquals(producer.normalExit().immutableOriginalSettingsSnapshot(),input.immutableOriginalSettingsSnapshot());
        Path budget=Path.of(producer.formalWar().defaultBudget().path());
        Files.writeString(budget,"{\"fixture\":\"changed-original\"}\n");assertDoesNotThrow(()->retained.requireCurrent(clock));assertEquals(producer,retained.configuration());
        // No inventory inspect/accept or ManagedGameSession is invoked: these references retain metadata only.
    }
    @Test void normalExitSourceMetadataSurvivesContentDriftAndSameBytesNativeReplacement()throws Exception {
        Clock clock=Clock.systemUTC();
        for(int role=0;role<3;role++)for(boolean replacement:List.of(false,true)) {
            String variant="normal-exit-"+role+"-"+replacement;
            var producer=actualDomainSettingsFixture(temporary.resolve(variant),clock);
            DataPin data=writeData(DataRole.REMAINING_DOMAIN_SETTINGS,variant+".json",RootRuntimeDomainSettings.encode(producer));
            FileRef selected=selectData(configuration(),data).data(DataRole.REMAINING_DOMAIN_SETTINGS);
            assertEquals(producer,RootRuntimeDomainSettings.decode(RootRuntimeDefinitions.readData(new DataPin(DataRole.REMAINING_DOMAIN_SETTINGS,selected))));
            var retained=RootRuntimeDomainSettings.readExact(selected,clock);retained.requireCurrent(clock);
            FileRef original=producer.normalExit().originals().get(role);Path path=Path.of(original.path());
            byte[] bytes=Files.readAllBytes(path);var time=Files.getLastModifiedTime(path);
            var nativeBefore=org.xar.ck3.control.build.SharedSourceFiles.nativeFile(path);
            if(replacement) {
                // Keep the original alive at a different name so its FileID cannot be recycled into the replacement.
                Files.move(path,path.resolveSibling(path.getFileName()+".retained-original"));
                Files.write(path,bytes,java.nio.file.StandardOpenOption.CREATE_NEW);
                Files.setLastModifiedTime(path,time);
                assertEquals(original,measure(path));
                assertNotEquals(nativeBefore.identityKey(),org.xar.ck3.control.build.SharedSourceFiles.nativeFile(path).identityKey());
            } else {
                byte[] changed=bytes.clone();changed[0]^=1;Files.write(path,changed);Files.setLastModifiedTime(path,time);
                assertEquals(original.bytes(),Files.size(path));assertEquals(time,Files.getLastModifiedTime(path));
                assertEquals(nativeBefore.identityKey(),org.xar.ck3.control.build.SharedSourceFiles.nativeFile(path).identityKey());
                assertNotEquals(original.sha256(),measure(path).sha256());
            }
            assertDoesNotThrow(()->retained.requireCurrent(clock),variant);
            // A new settings read retains source metadata without qualifying those historical files.
            assertEquals(producer,RootRuntimeDomainSettings.readExact(selected,clock).configuration(),variant);
        }
    }
    @Test void physicalSettingsRoleDoesNotFallbackFromOldSchemaOrMissingNormalExitOriginals()throws Exception {
        var producer=actualDomainSettingsFixture(temporary.resolve("strict-normal-exit"),Clock.systemUTC());
        var valid=(ObjectNode)StrictJson.parse(RootRuntimeDomainSettings.encode(producer),RootRuntimeDomainSettings.MAXIMUM_BYTES);
        var malformed=new java.util.ArrayList<ObjectNode>();
        for(String version:List.of("xar.java-root-domain-settings/v2","xar.java-root-domain-settings/v3","xar.java-root-domain-settings/v4","xar.java-root-domain-settings/v5")) {
            var historical=valid.deepCopy();historical.put("schema",version);malformed.add(historical);
        }
        var missingHistory=valid.deepCopy();missingHistory.remove("query_history_settings");malformed.add(missingHistory);
        var nullHistory=valid.deepCopy();nullHistory.putNull("query_history_settings");malformed.add(nullHistory);
        var boolHistory=valid.deepCopy();((ObjectNode)boolHistory.get("query_history_settings")).put("bytes",true);malformed.add(boolHistory);
        var missingFlags=valid.deepCopy();missingFlags.remove("plan_flags");malformed.add(missingFlags);
        var nullFlags=valid.deepCopy();nullFlags.putNull("plan_flags");malformed.add(nullFlags);
        var missing=valid.deepCopy();missing.remove("normal_exit");malformed.add(missing);
        var explicitNull=valid.deepCopy();explicitNull.putNull("normal_exit");malformed.add(explicitNull);
        var missingCoa=valid.deepCopy();missingCoa.remove("coa_read_limits");malformed.add(missingCoa);
        var nullCoa=valid.deepCopy();nullCoa.putNull("coa_read_limits");malformed.add(nullCoa);
        var wrongCoaBytes=valid.deepCopy();((ObjectNode)wrongCoaBytes.get("coa_read_limits").get("original")).put("bytes",true);malformed.add(wrongCoaBytes);
        for(String field:List.of("inventory","original_managed_profile","immutable_original_settings_snapshot")) {
            var missingRef=valid.deepCopy();((ObjectNode)missingRef.get("normal_exit")).remove(field);malformed.add(missingRef);
            var wrongBytes=valid.deepCopy();((ObjectNode)wrongBytes.get("normal_exit").get(field)).put("bytes",true);malformed.add(wrongBytes);
        }
        int index=0;
        for(var wrong:malformed) {
            DataPin data=writeData(DataRole.REMAINING_DOMAIN_SETTINGS,"invalid-normal-exit-"+(index++)+".json",StrictJson.canonical(wrong));
            FileRef selected=selectData(configuration(),data).data(DataRole.REMAINING_DOMAIN_SETTINGS);
            assertThrows(Exception.class,()->RootRuntimeDomainSettings.decode(
                    RootRuntimeDefinitions.readData(new DataPin(DataRole.REMAINING_DOMAIN_SETTINGS,selected))));
        }
    }
    @Test void queryHistoryDocumentRemainsRequiredWhileRequestAndProducerArePassiveData()throws Exception {
        Clock clock=Clock.systemUTC();
        for(int role=0;role<3;role++)for(boolean replacement:List.of(false,true)) {
            String variant="query-history-"+role+"-"+replacement;
            var producer=actualDomainSettingsFixture(temporary.resolve(variant),clock);
            DataPin data=writeData(DataRole.REMAINING_DOMAIN_SETTINGS,variant+".json",RootRuntimeDomainSettings.encode(producer));
            FileRef selected=selectData(configuration(),data).data(DataRole.REMAINING_DOMAIN_SETTINGS);
            var retained=RootRuntimeDomainSettings.readExact(selected,clock);
            var document=OriginalDriverQueryHistorySettings.decode(Files.readAllBytes(Path.of(producer.queryHistorySettings().path())));
            var refs=List.of(producer.queryHistorySettings(),document.sourceRefs().configurationOriginal(),document.sourceRefs().producerOriginal());
            assertEquals(10,retained.retainedOriginals().size());
            for(var ref:refs)assertTrue(retained.retainedOriginals().contains(new FileRef(ref.path(),ref.bytes(),ref.sha256())));
            assertEquals(document.request(),OriginalDriverQueryHistorySettings.decodeRequest(
                    Files.readAllBytes(Path.of(document.sourceRefs().configurationOriginal().path()))));
            assertEquals(OriginalDriverQueryHistorySettings.Origin.JAVA_CONFIGURED,document.request().configuration().origin());
            var selectedRef=refs.get(role);Path path=Path.of(selectedRef.path());
            byte[] bytes=Files.readAllBytes(path);var time=Files.getLastModifiedTime(path);
            var nativeBefore=org.xar.ck3.control.build.SharedSourceFiles.nativeFile(path);
            if(replacement){
                Files.move(path,path.resolveSibling(path.getFileName()+".retained-original"));
                Files.write(path,bytes,java.nio.file.StandardOpenOption.CREATE_NEW);Files.setLastModifiedTime(path,time);
                assertEquals(selectedRef,exact(measure(path)));
                assertNotEquals(nativeBefore.identityKey(),org.xar.ck3.control.build.SharedSourceFiles.nativeFile(path).identityKey());
            }else{
                bytes[0]^=1;Files.write(path,bytes);Files.setLastModifiedTime(path,time);
                assertEquals(nativeBefore.identityKey(),org.xar.ck3.control.build.SharedSourceFiles.nativeFile(path).identityKey());
                assertNotEquals(selectedRef.sha256(),measure(path).sha256());
            }
            assertDoesNotThrow(()->retained.requireCurrent(clock),variant);
            if(!replacement&&role==0)assertThrows(IOException.class,()->RootRuntimeDomainSettings.readExact(selected,clock),variant);
            else assertEquals(producer,RootRuntimeDomainSettings.readExact(selected,clock).configuration(),variant);
            // Required document content and passive source metadata only. The temporary provenance source is not an actual NativePlan producer;
            // this test never invokes OriginalDriverQueryHistorySettings.readExact or mints a Native Bound.
        }
    }
    @Test void actualPlanFlagsRemainSevenExplicitStrictDataValuesWithoutPermissionDefaults()throws Exception {
        Clock clock=Clock.systemUTC();var producer=actualDomainSettingsFixture(temporary.resolve("plan-flags"),clock);
        DataPin data=writeData(DataRole.REMAINING_DOMAIN_SETTINGS,"actual-plan-flags.json",RootRuntimeDomainSettings.encode(producer));
        FileRef selected=selectData(configuration(),data).data(DataRole.REMAINING_DOMAIN_SETTINGS);
        var bound=RootRuntimeDomainSettings.readExact(selected,clock);var flags=bound.configuration().planFlags();
        assertEquals(new RootRuntimeDomainSettings.PlanFlags(true,false,true,false,true,false,true),flags);
        assertTrue(flags.lifestyleFormalTrial());assertFalse(flags.factionGiftFormalTrial());assertTrue(flags.constructionFormalTrial());
        assertFalse(flags.familyMarriageFormalTrial());assertTrue(flags.councilAction());assertFalse(flags.m5JointCollector());
        assertTrue(flags.initialLifestyleFocusRequired());
        var valid=(ObjectNode)StrictJson.parse(RootRuntimeDomainSettings.encode(producer),RootRuntimeDomainSettings.MAXIMUM_BYTES);
        ObjectNode wireFlags=(ObjectNode)valid.get("plan_flags");assertEquals(7,wireFlags.size());
        var fields=new ArrayList<String>();wireFlags.fieldNames().forEachRemaining(fields::add);int index=0;
        for(String field:fields)for(int kind=0;kind<3;kind++){
            var wrong=valid.deepCopy();var changed=(ObjectNode)wrong.get("plan_flags");
            if(kind==0)changed.remove(field);else if(kind==1)changed.put(field,0);else changed.put(field,"false");
            DataPin bad=writeData(DataRole.REMAINING_DOMAIN_SETTINGS,"invalid-plan-flag-"+(index++)+".json",StrictJson.canonical(wrong));
            assertThrows(IOException.class,()->RootRuntimeDomainSettings.decode(RootRuntimeDefinitions.readData(bad)));
        }
        // These seven profile facts never issue private permissions or a Game capability.
    }

    @Test void actualCoaVfsLimitDataSurvivesSameBytesReplacementAndKeepsSoleCodec()throws Exception {
        Clock clock=Clock.systemUTC();var producer=actualDomainSettingsFixture(temporary.resolve("actual-coa-limits"),clock);
        DataPin data=writeData(DataRole.REMAINING_DOMAIN_SETTINGS,"actual-coa-limits-settings.json",RootRuntimeDomainSettings.encode(producer));
        FileRef selected=selectData(configuration(),data).data(DataRole.REMAINING_DOMAIN_SETTINGS);
        assertEquals(producer,RootRuntimeDomainSettings.decode(RootRuntimeDefinitions.readData(new DataPin(DataRole.REMAINING_DOMAIN_SETTINGS,selected))));
        var retained=RootRuntimeDomainSettings.readExact(selected,clock);retained.requireCurrent(clock);
        FileRef limits=retained.configuration().coaReadLimits().original();
        assertTrue(retained.retainedOriginals().contains(limits));
        var expected=new CoaVfs.Limits(65536,32768);assertEquals(expected,retained.configuration().coaReadLimits().limits());
        Path path=Path.of(limits.path());byte[] bytes=Files.readAllBytes(path);var time=Files.getLastModifiedTime(path);
        var nativeBefore=org.xar.ck3.control.build.SharedSourceFiles.nativeFile(path);
        Files.move(path,path.resolveSibling(path.getFileName()+".retained-original"));
        Files.write(path,bytes,java.nio.file.StandardOpenOption.CREATE_NEW);Files.setLastModifiedTime(path,time);
        assertEquals(limits,measure(path));
        assertNotEquals(nativeBefore.identityKey(),org.xar.ck3.control.build.SharedSourceFiles.nativeFile(path).identityKey());
        // The value codec still decodes these same bytes; a historical identity replacement does not invalidate retained DATA.
        assertEquals(expected,retained.configuration().coaReadLimits().limits());
        assertDoesNotThrow(()->retained.requireCurrent(clock));
    }
    @Test void stockConfigurationExplicitNullAndConfiguredPairPinsUseTheSamePhysicalDataReader()throws Exception {
        Clock clock=Clock.systemUTC();
        var baseline=actualDomainSettingsFixture(temporary.resolve("stock-unconfigured"),clock);
        var wire=StrictJson.parse(RootRuntimeDomainSettings.encode(baseline),RootRuntimeDomainSettings.MAXIMUM_BYTES);
        assertTrue(wire.has("stock_read"));assertTrue(wire.get("stock_read").isNull());
        DataPin baselineData=writeData(DataRole.REMAINING_DOMAIN_SETTINGS,"stock-unconfigured.json",RootRuntimeDomainSettings.encode(baseline));
        Configuration baselineConfiguration=selectData(configuration(),baselineData);
        var baselineBound=RootRuntimeDomainSettings.readExact(baselineConfiguration.data(DataRole.REMAINING_DOMAIN_SETTINGS),clock);
        baselineBound.requireCurrent(clock);assertNull(baselineBound.configuration().stockRead());
        assertEquals(10,baselineBound.retainedOriginals().size());
        var producer=actualStockSettingsFixture(temporary.resolve("stock-configured"),clock);
        DataPin data=writeData(DataRole.REMAINING_DOMAIN_SETTINGS,"stock-configured.json",RootRuntimeDomainSettings.encode(producer));
        Configuration configured=selectData(baselineConfiguration,data);
        FileRef selected=configured.data(DataRole.REMAINING_DOMAIN_SETTINGS);
        assertEquals(producer,RootRuntimeDomainSettings.decode(RootRuntimeDefinitions.readData(new DataPin(DataRole.REMAINING_DOMAIN_SETTINGS,selected))));
        var bound=RootRuntimeDomainSettings.readExact(selected,clock);bound.requireCurrent(clock);
        assertEquals(12,bound.retainedOriginals().size());
        assertTrue(bound.retainedOriginals().containsAll(producer.stockRead().originals()));
        assertEquals(producer.stockRead(),bound.configuration().stockRead());
        assertEquals(new RootH2743StockPredicateAdmission.Limits(16,4096,4096,4096),bound.configuration().stockRead().limits());
        // Explicitly replacing the role with the prior null branch cannot mutate either retained consumer.
        Configuration rebound=selectData(configured,baselineData);
        assertEquals(baselineConfiguration,rebound);assertNull(RootRuntimeDomainSettings.decode(
                RootRuntimeDefinitions.readData(new DataPin(DataRole.REMAINING_DOMAIN_SETTINGS,rebound.data(DataRole.REMAINING_DOMAIN_SETTINGS)))).stockRead());
        bound.requireCurrent(clock);baselineBound.requireCurrent(clock);
        assertEquals(producer.stockRead(),bound.configuration().stockRead());
        // Actual pair/pins bytes and identity custody only: do not call Stock admission, configuration() or Native Bound.
    }
    @Test void stockWireRequiresAnExplicitNullableFieldAndStrictPairPinsAndFiniteLimits()throws Exception {
        var producer=actualStockSettingsFixture(temporary.resolve("stock-strict-wire"),Clock.systemUTC());
        var valid=(ObjectNode)StrictJson.parse(RootRuntimeDomainSettings.encode(producer),RootRuntimeDomainSettings.MAXIMUM_BYTES);
        var malformed=new ArrayList<ObjectNode>();
        var absent=valid.deepCopy();absent.remove("stock_read");malformed.add(absent);
        var old=valid.deepCopy();old.put("schema","xar.java-root-domain-settings/v5");malformed.add(old);
        var wrongBranch=valid.deepCopy();wrongBranch.put("stock_read",true);malformed.add(wrongBranch);
        for(String field:List.of("pair","pins")) {
            var missing=valid.deepCopy();((ObjectNode)missing.get("stock_read")).remove(field);malformed.add(missing);
            var nil=valid.deepCopy();((ObjectNode)nil.get("stock_read")).putNull(field);malformed.add(nil);
            var wrong=valid.deepCopy();((ObjectNode)wrong.get("stock_read").get(field)).put("bytes",true);malformed.add(wrong);
        }
        var noLimits=valid.deepCopy();((ObjectNode)noLimits.get("stock_read")).remove("limits");malformed.add(noLimits);
        var nilLimits=valid.deepCopy();((ObjectNode)nilLimits.get("stock_read")).putNull("limits");malformed.add(nilLimits);
        for(String field:List.of("maximum_files","maximum_source_bytes","maximum_document_bytes","maximum_read_bytes")) {
            var absentLimit=valid.deepCopy();((ObjectNode)absentLimit.get("stock_read").get("limits")).remove(field);malformed.add(absentLimit);
            var nullLimit=valid.deepCopy();((ObjectNode)nullLimit.get("stock_read").get("limits")).putNull(field);malformed.add(nullLimit);
            var floatLimit=valid.deepCopy();((ObjectNode)floatLimit.get("stock_read").get("limits")).put(field,1.0);malformed.add(floatLimit);
            var booleanLimit=valid.deepCopy();((ObjectNode)booleanLimit.get("stock_read").get("limits")).put(field,true);malformed.add(booleanLimit);
            var zeroLimit=valid.deepCopy();((ObjectNode)zeroLimit.get("stock_read").get("limits")).put(field,0);malformed.add(zeroLimit);
        }
        var tooManyFiles=valid.deepCopy();((ObjectNode)tooManyFiles.get("stock_read").get("limits")).put("maximum_files",8193);malformed.add(tooManyFiles);
        var tooLargeDocument=valid.deepCopy();((ObjectNode)tooLargeDocument.get("stock_read").get("limits")).put("maximum_document_bytes",16777217);malformed.add(tooLargeDocument);
        var aliasedPins=valid.deepCopy();((ObjectNode)aliasedPins.get("stock_read")).set("pins",aliasedPins.get("stock_read").get("pair").deepCopy());malformed.add(aliasedPins);
        var relative=valid.deepCopy();((ObjectNode)relative.get("stock_read")).put("native_source_checkout","relative-checkout");malformed.add(relative);
        int index=0;
        for(var bad:malformed) {
            byte[] malformedWire=ControlBuild.strictMapper().writeValueAsBytes(bad);
            assertTrue(malformedWire.length>0&&malformedWire.length<=RootRuntimeDomainSettings.MAXIMUM_BYTES);
            var transported=StrictJson.parse(malformedWire);
            for(String field:List.of("maximum_files","maximum_source_bytes","maximum_document_bytes","maximum_read_bytes"))
                if(bad.path("stock_read").path("limits").path(field).isFloatingPointNumber())
                    assertTrue(transported.at("/stock_read/limits/"+field).isFloatingPointNumber());
            DataPin data=writeData(DataRole.REMAINING_DOMAIN_SETTINGS,"invalid-stock-"+(index++)+".json",malformedWire);
            assertThrows(IOException.class,()->RootRuntimeDomainSettings.decode(RootRuntimeDefinitions.readData(data)));
        }
    }
    @Test void configuredStockSourceMetadataSurvivesContentAndNativeIdentityDrift()throws Exception {
        Clock clock=Clock.systemUTC();
        for(int role=0;role<2;role++)for(boolean replacement:List.of(false,true)) {
            String variant="stock-original-"+role+"-"+replacement;
            var producer=actualStockSettingsFixture(temporary.resolve(variant),clock);
            DataPin data=writeData(DataRole.REMAINING_DOMAIN_SETTINGS,variant+".json",RootRuntimeDomainSettings.encode(producer));
            FileRef selected=selectData(configuration(),data).data(DataRole.REMAINING_DOMAIN_SETTINGS);
            var retained=RootRuntimeDomainSettings.readExact(selected,clock);retained.requireCurrent(clock);
            FileRef original=producer.stockRead().originals().get(role);Path path=Path.of(original.path());
            byte[] bytes=Files.readAllBytes(path);var time=Files.getLastModifiedTime(path);
            var before=org.xar.ck3.control.build.SharedSourceFiles.nativeFile(path);
            if(replacement) {
                Files.move(path,path.resolveSibling(path.getFileName()+".retained-original"));
                Files.write(path,bytes,java.nio.file.StandardOpenOption.CREATE_NEW);Files.setLastModifiedTime(path,time);
                assertEquals(original,measure(path));
                assertNotEquals(before.identityKey(),org.xar.ck3.control.build.SharedSourceFiles.nativeFile(path).identityKey());
            } else {
                bytes[0]^=1;Files.write(path,bytes);Files.setLastModifiedTime(path,time);
                assertEquals(before.identityKey(),org.xar.ck3.control.build.SharedSourceFiles.nativeFile(path).identityKey());
                assertNotEquals(original.sha256(),measure(path).sha256());
            }
            assertDoesNotThrow(()->retained.requireCurrent(clock),variant);
            assertEquals(producer,RootRuntimeDomainSettings.readExact(selected,clock).configuration(),variant);
            // Keeping the old file alive prevents FileID recycling. No Stock producer/parser/admission is invoked.
        }
    }
    @Test void boundedDataAndSourceMetadataRejectTamperingWithoutHistoricalQualification()throws Exception {
        Path actual=temporary.resolve("Actual.java");Files.writeString(actual,"package fixture; final class Actual {}\n");FileRef actualRef=measure(actual);
        assertArrayEquals(Files.readAllBytes(actual),RootRuntimeDefinitions.read(actualRef,4096));
        Path input=temporary.resolve("input.json");Files.writeString(input,"{}\n");
        SelectedSource winner=new SelectedSource("local-service/src/main/java/fixture/Actual.java",exact(actualRef));
        var graph=StrictJson.object();graph.put("schema","xar.java.single-winner-source-index/v1");graph.put("machine_id",MACHINE);
        graph.put("owner","/root/source_graph");graph.put("observed_at_utc",OBSERVED);graph.put("status","SOURCE_ONLY_NOT_RUNTIME_QUALIFICATION");
        graph.set("input_ref",ControlBuild.strictMapper().valueToTree(measure(input)));graph.put("parent_pom_order_only_supersedes_input02",true);
        graph.set("selected_files",ControlBuild.strictMapper().valueToTree(List.of(winner)));
        byte[] decoded=StrictJson.canonical(graph,RootRuntimeDefinitions.MAXIMUM_BYTES);Path compressed=temporary.resolve("index.json.gz");
        try(var output=new GZIPOutputStream(Files.newOutputStream(compressed))){output.write(decoded);}
        SourceIndex source=new SourceIndex(measure(compressed),decoded.length,hash(decoded));
        assertEquals(List.of(winner),RootRuntimeDefinitions.readSourceIndex(source,MACHINE,CLOCK));
        assertEquals(measure(input),RootRuntimeDefinitions.sourceIndexOriginalInput(source));
        assertThrows(IOException.class,()->RootRuntimeDefinitions.readSourceIndex(new SourceIndex(source.compressedRef(),decoded.length,"0".repeat(64)),MACHINE,CLOCK));
        assertEquals(List.of(winner),RootRuntimeDefinitions.readSourceIndex(source,"other-machine",CLOCK));
        for(String invalidMachine:List.of("-noncanonical-machine","a".repeat(129))) {
            var wrongMachine=graph.deepCopy();wrongMachine.put("machine_id",invalidMachine);
            byte[] wire=StrictJson.canonical(wrongMachine,RootRuntimeDefinitions.MAXIMUM_BYTES);
            Path gzip=temporary.resolve("invalid-machine-"+invalidMachine.length()+".gz");
            try(var output=new GZIPOutputStream(Files.newOutputStream(gzip))){output.write(wire);}
            SourceIndex malformedMachine=new SourceIndex(measure(gzip),wire.length,hash(wire));
            assertThrows(IOException.class,()->RootRuntimeDefinitions.readSourceIndex(malformedMachine,invalidMachine,CLOCK));
            assertThrows(IOException.class,()->RootRuntimeDefinitions.sourceIndexOriginalInput(malformedMachine));
        }
        assertDoesNotThrow(()->RootRuntimeDefinitions.verifySources(configuration(),List.of(winner)));
        Files.writeString(actual,"tampered");assertThrows(IOException.class,()->RootRuntimeDefinitions.read(actualRef,4096));
        var duplicate=graph.deepCopy();((com.fasterxml.jackson.databind.node.ArrayNode)duplicate.get("selected_files")).add(ControlBuild.strictMapper().valueToTree(winner));
        byte[] duplicateBytes=StrictJson.canonical(duplicate,RootRuntimeDefinitions.MAXIMUM_BYTES);Path bad=temporary.resolve("duplicate.gz");
        try(var output=new GZIPOutputStream(Files.newOutputStream(bad))){output.write(duplicateBytes);}
        assertThrows(IOException.class,()->RootRuntimeDefinitions.readSourceIndex(new SourceIndex(measure(bad),duplicateBytes.length,hash(duplicateBytes)),MACHINE,CLOCK));
        Files.writeString(input,"ancestry drift\n");
        assertEquals(ControlBuild.strictMapper().treeToValue(graph.get("input_ref"),FileRef.class),RootRuntimeDefinitions.sourceIndexOriginalInput(source));
    }
    @Test void configuredSourceInventoryIncludesEveryAdditionalFinanceAndActivityProducerAndIsImmutable()throws Exception {
        var encoded=(ObjectNode)StrictJson.parse(RootRuntimeDefinitions.encodeConfiguration(configuration()),RootRuntimeDefinitions.MAXIMUM_BYTES);
        var required=new java.util.ArrayList<SelectedSource>();
        var finance=encoded.get("finance");
        for(int index=0;index<finance.get("reads").size();index++) {
            SelectedSource selected=inventorySource("finance-read-"+index);required.add(selected);
            ((ObjectNode)finance.get("reads").get(index)).set("definition",ControlBuild.strictMapper().valueToTree(selected));
        }
        SelectedSource gift=inventorySource("finance-gift-cold");required.add(gift);
        ((ObjectNode)finance).set("gift_cold_definition",ControlBuild.strictMapper().valueToTree(gift));
        for(String group:List.of("reads","mutations"))for(int index=0;index<encoded.get("activity").get(group).size();index++) {
            SelectedSource selected=inventorySource("activity-"+group+"-"+index);required.add(selected);
            ((ObjectNode)encoded.get("activity").get(group).get(index)).set("definition",ControlBuild.strictMapper().valueToTree(selected));
        }
        Configuration config=RootRuntimeDefinitions.decodeConfiguration(StrictJson.canonical(encoded,RootRuntimeDefinitions.MAXIMUM_BYTES));
        List<SelectedSource> inventory=RootRuntimeDefinitions.configuredSources(config);
        assertTrue(inventory.containsAll(required));
        for(SourcePin source:config.sources())assertTrue(inventory.contains(source.selected()));
        for(ProducerClosure closure:config.closures())assertTrue(inventory.containsAll(closure.sources()));
        assertEquals(config.sources().size()+config.closures().stream().mapToInt(row->row.sources().size()).sum()+required.size(),inventory.size());
        assertThrows(UnsupportedOperationException.class,()->inventory.add(gift));
    }
    @Test void fixedEventSourcesReuseActualEvidenceCodecAndPreserveRootsAndGrants()throws Exception {
        Path state=temporary.resolve("state"),stock=temporary.resolve("stock");Files.createDirectory(state);Files.createDirectory(stock);
        var root=StrictJson.object();root.put("schema","xar.java-event-source-read-context/v1");root.put("machine_id",MACHINE);
        root.put("state_root",state.toString());root.put("stock_game_root",stock.toString());
        var evidence=root.putObject("evidence_grants");evidence.put("schema","xar.projection-evidence-grants/v1");
        var row=evidence.putArray("grants").addObject();row.put("role","event-source-facts");row.put("path",temporary.resolve("facts.json").toString());
        row.put("bytes",1);row.put("sha256",SHA);row.put("origin_machine_id",MACHINE);
        var actual=RootRuntimeDefinitions.decodeEventSources(StrictJson.canonical(root,1<<20));
        assertEquals(MACHINE,actual.machineId());assertEquals(state,actual.stateRoot());assertEquals(stock,actual.stockGameRoot());assertEquals(1,actual.evidenceGrants().size());
        var missing=root.deepCopy();missing.remove("evidence_grants");assertThrows(IllegalArgumentException.class,()->RootRuntimeDefinitions.decodeEventSources(StrictJson.canonical(missing,1<<20)));
        var empty=root.deepCopy();((com.fasterxml.jackson.databind.node.ArrayNode)empty.get("evidence_grants").get("grants")).removeAll();
        assertTrue(RootRuntimeDefinitions.decodeEventSources(StrictJson.canonical(empty,1<<20)).evidenceGrants().isEmpty());
        var wrong=root.deepCopy();((ObjectNode)wrong.get("evidence_grants").get("grants").get(0)).put("bytes",true);assertThrows(IllegalArgumentException.class,()->RootRuntimeDefinitions.decodeEventSources(StrictJson.canonical(wrong,1<<20)));
        var alias=root.deepCopy();alias.put("stock_game_root",state.resolve("nested").toString());assertThrows(IllegalArgumentException.class,()->RootRuntimeDefinitions.decodeEventSources(StrictJson.canonical(alias,1<<20)));
    }
    @Test void completeSourceIndexAboveOneMiBUsesItsOwnBoundedStrictRecordDecoder()throws Exception {
        Path input=temporary.resolve("large-input.json");Files.writeString(input,"{}\n");FileRef pin=measure(input);
        var graph=StrictJson.object();graph.put("schema","xar.java.single-winner-source-index/v1");graph.put("machine_id",MACHINE);
        graph.put("owner","/root/source_graph");graph.put("observed_at_utc",OBSERVED);graph.put("status","SOURCE_ONLY");
        graph.set("input_ref",ControlBuild.strictMapper().valueToTree(pin));graph.put("parent_pom_order_only_supersedes_input02",true);
        var rows=graph.putArray("selected_files");
        for(int index=0;index<6000;index++)rows.add(ControlBuild.strictMapper().valueToTree(new SelectedSource(
                "local-service/src/main/java/fixture/CompleteSource"+index+".java",new ExactRef(temporary.resolve("CompleteSource"+index+".java").toString(),1,SHA))));
        byte[] large=ControlBuild.strictMapper().writeValueAsBytes(graph);assertTrue(large.length>StrictJson.EXPLICIT_MAX_BYTES);
        assertTrue(large.length<RootRuntimeDefinitions.MAXIMUM_INDEX_BYTES);Path compressed=temporary.resolve("large-index.gz");
        try(var output=new GZIPOutputStream(Files.newOutputStream(compressed))){output.write(large);}
        assertEquals(6000,RootRuntimeDefinitions.readSourceIndex(new SourceIndex(measure(compressed),large.length,hash(large)),MACHINE,CLOCK).size());
        ((ObjectNode)rows.get(5999).get("source_ref")).put("bytes",1.0);
        byte[] malformed=ControlBuild.strictMapper().writeValueAsBytes(graph);Path bad=temporary.resolve("large-wrong-number.gz");
        try(var output=new GZIPOutputStream(Files.newOutputStream(bad))){output.write(malformed);}
        assertThrows(IOException.class,()->RootRuntimeDefinitions.readSourceIndex(new SourceIndex(measure(bad),malformed.length,hash(malformed)),MACHINE,CLOCK));
    }
    @Test void explicitHistoryAbsenceIsCheckedAndNeverActsAsFreshEntryAdmission()throws Exception {
        Path path=temporary.resolve("strategy").resolve("one-life-history.json");Files.createDirectory(path.getParent());
        assertDoesNotThrow(()->RootRuntimeDefinitions.verifyOriginalHistory(new OriginalHistory(path.toString(),null)));
        Files.writeString(path,"{}\n");assertThrows(IOException.class,()->RootRuntimeDefinitions.verifyOriginalHistory(new OriginalHistory(path.toString(),null)));
        assertDoesNotThrow(()->RootRuntimeDefinitions.verifyOriginalHistory(new OriginalHistory(path.toString(),measure(path))));
    }
    private void reject(ObjectNode root)throws IOException {
        // Preserve malformed JSON number types at the byte boundary; the valid canonical encoder intentionally rejects floats.
        byte[] malformed=ControlBuild.strictMapper().writeValueAsBytes(root);
        assertThrows(Exception.class,()->RootRuntimeDefinitions.decodeConfiguration(malformed));
    }
    private Configuration configuration() {
        FileRef input=pin(temporary.resolve("required.json"));Build build=new Build("1.20.0.4",SHA);
        List<SourcePin> sources=Arrays.stream(SourceRole.values()).map(role->{SourceKind kind=expectedKind(role);String suffix=switch(kind){case JAVA->".java";case NATIVE->".cpp";case ORIGINAL_PYTHON->".py";case STOCK_SCRIPT->".txt";};
            String target=role==SourceRole.ARMY_WAR_EXIT_TRUCE_DEFINITION?ARMY_WAR_EXIT_TRUCE_TARGET:"local-service/src/main/java/fixture/"+role.name()+suffix;
            return new SourcePin(role,kind,new SelectedSource(target,new ExactRef(temporary.resolve(role.name()+suffix).toString(),1,SHA)));}).toList();
        SelectedSource java=sources.stream().filter(source->source.kind()==SourceKind.JAVA).findFirst().orElseThrow().selected();
        SelectedSource episodeLedger=sources.stream().filter(row->row.role()==SourceRole.PRISONER_EPISODE_LEDGER).findFirst().orElseThrow().selected();
        List<ProducerClosure> closures=Arrays.stream(ClosureRole.values()).map(role->new ProducerClosure(role,
                role==ClosureRole.PRISONER_DOMAIN?List.of(java,episodeLedger):List.of(java))).toList();
        List<DataPin> data=Arrays.stream(DataRole.values()).map(role->new DataPin(role,input)).toList();
        ReadPermission privateRead=new ReadPermission(null,"fixture-permission",PermissionMode.SOURCE_QUALIFIED_PRIVATE,WireProfile.EXECUTE_STEP);
        List<FinanceRead> finance=Arrays.stream(FinanceQuery.values()).map(query->new FinanceRead(query,java,privateRead)).toList();
        ActivityInputs activity=new ActivityInputs(Arrays.stream(ActivityNativeContracts.Query.values()).map(query->new ActivityQuery(query,java)).toList(),Arrays.stream(ActivityActionRoutes.Kind.values()).map(kind->new ActivityMutation(kind,java)).toList());
        return new Configuration(SCHEMA,MACHINE,OBSERVED,REVIEW,input,input,input,input,new SourceIndex(input,1,SHA),sources,closures,data,
                new GovInputs(build,"fixture-governance",List.copyOf(GovernanceActionPreparation.OPERATIONS),10,3),new FinanceInputs(finance,java,privateRead),
                new ArmyInputs(1000,2000,"fixture-army"),new PrisonerInputs(build,"fixture-prisoners"),new FamilyInputs(true,true,true,true,null),new FrontendInputs(build,1000,1000,8,32,"fixture-frontend"),
                new InteractionInputs(build,List.of(0L),List.of(List.of(0)),List.of(0)),activity,
                new CrossRunInputs(new OriginalHistory(temporary.resolve("strategy").resolve("one-life-history.json").toString(),null)),
                new IncidentInputs(temporary.resolve("incidents").toString(),temporary.resolve("scans").toString(),65536),
                new PublicInputs(1000,2000,List.of(PublicMethod.values()[0])),new StartupInputs(16,1000,"fixture-startup"));
    }
    private FileRef pin(Path path){return new FileRef(path.toString(),1,SHA);}
    @Test void uncapturedReceiptShapeNeverCreatesAnActualOriginalMcpSourceSet()throws Exception {
        DataPin original=writeData(DataRole.ORIGINAL_MCP_CAPTURE_RECEIPT,"uncaptured-original-mcp.json","{}\n".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        assertArrayEquals(Files.readAllBytes(Path.of(original.originalRef().path())),RootRuntimeDefinitions.readData(original));
        assertThrows(IOException.class,()->RootOriginalMcpCapture.readRetained(original.originalRef()));
    }
    @Test void actualCapturedProducerReceiptFlowsThroughSdkRoleIntoTheUniqueFourModuleReader()throws Exception {
        FileRef receipt=requiredIndexFixture("xar.original.mcp.capture.receipt");
        DataPin original=new DataPin(DataRole.ORIGINAL_MCP_CAPTURE_RECEIPT,receipt);
        Configuration selected=selectData(configuration(),original);
        assertArrayEquals(Files.readAllBytes(Path.of(receipt.path())),RootRuntimeDefinitions.readData(
                new DataPin(DataRole.ORIGINAL_MCP_CAPTURE_RECEIPT,selected.data(DataRole.ORIGINAL_MCP_CAPTURE_RECEIPT))));
        var retained=RootOriginalMcpCapture.readRetained(selected.data(DataRole.ORIGINAL_MCP_CAPTURE_RECEIPT));
        retained.requireCurrent(Clock.systemUTC());var actual=retained.sourceSet();actual.verify();
        for(var module:org.xar.ck3.control.build.OriginalMcpCapture.OriginalModule.values()) {
            var source=actual.get(module);assertEquals(module,source.module());
            assertEquals(Optional.of(source),actual.lookup(source.original()));assertEquals(source,actual.requireOriginal(source.original()));
            var wrong=new FileRef(source.original().path(),source.original().bytes(),"0".repeat(64));
            assertEquals(Optional.empty(),actual.lookup(wrong));assertThrows(IOException.class,()->actual.requireOriginal(wrong));
        }
        retained.requireUnchanged();
        // This is actual registration DATA/source custody. No Java admission, Game or Native permission is produced.
    }
    @Test void receiptDataDecodesRecordedAssignmentsWithoutReplayingTheCapturedCallgraph()throws Exception {
        FileRef receipt=requiredIndexFixture("xar.original.mcp.capture.receipt");var retained=RootOriginalMcpCapture.readRetained(receipt);
        var root=(ObjectNode)ControlBuild.strictMapper().readTree(RootOriginalMcpCapture.encodeActual(retained.actual()));
        var table=(ObjectNode)root.get("source_set");var server=(ObjectNode)table.get("mcp_server").deepCopy();
        var rite=(ObjectNode)table.get("rite_creation_action_mcp_v1").deepCopy();
        rite.put("module","MCP_SERVER");server.put("module","RITE_CREATION_ACTION_MCP_V1");
        table.set("mcp_server",rite);table.set("rite_creation_action_mcp_v1",server);
        byte[] replaced=ControlBuild.strictMapper().writeValueAsBytes(root);
        // DATA decoding preserves the record. Explicit capture/source-join verification is tested separately and grants no permission here.
        var decoded=RootOriginalMcpCapture.decodeActual(replaced);assertDoesNotThrow(()->decoded.sourceSet().verify());
        Path altered=temporary.resolve("actual-receipt-with-wrong-source-roles.json");Files.write(altered,replaced);
        assertEquals(decoded,RootOriginalMcpCapture.readRetained(measure(altered)).actual());
    }
    private static FileRef requiredIndexFixture(String prefix)throws IOException {
        String path=requiredIndexProperty(prefix+".path"),size=requiredIndexProperty(prefix+".bytes"),sha=requiredIndexProperty(prefix+".sha256");
        long bytes;
        try{bytes=Long.parseLong(size);}catch(NumberFormatException invalid){throw new IOException("NOT_RUN: actual source fixture byte count is invalid",invalid);}
        if(bytes<1||!Long.toString(bytes).equals(size))throw new IOException("NOT_RUN: canonical positive actual fixture byte count required");
        FileRef result=new FileRef(path,bytes,sha);file(result,RootRuntimeDefinitions.MAXIMUM_INDEX_BYTES);result.verify();return result;
    }
    private static String requiredIndexProperty(String name)throws IOException {
        String value=System.getProperty(name);
        if(value==null||value.isBlank())throw new IOException("NOT_RUN: complete actual producer-to-SDK regression requires property "+name);
        return value;
    }
    private DataPin writeData(DataRole role,String name,byte[] produced)throws Exception {
        Path path=temporary.resolve(name);Files.write(path,produced);return new DataPin(role,measure(path));
    }
    private RootRuntimeDomainSettings.Configuration actualStockSettingsFixture(Path root,Clock clock)throws Exception {
        var b=actualDomainSettingsFixture(root,clock);Path pair=root.resolve("stock-pair.json"),pins=root.resolve("stock-pins.json");
        Files.writeString(pair,"custody-only stock pair original");Files.writeString(pins,"custody-only stock pins original");
        var stock=new RootRuntimeDomainSettings.StockRead(exact(measure(pair)),exact(measure(pins)),
                root.resolve("native-source-checkout").toString(),new RootH2743StockPredicateAdmission.Limits(16,4096,4096,4096));
        return new RootRuntimeDomainSettings.Configuration(b.schema(),b.machineId(),b.observedAtUtc(),b.reviewAtUtc(),
                b.lifecycle(),b.familyRelationExportRoot(),b.formalWar(),b.peacetime(),b.offline(),b.normalExit(),
                b.coaReadLimits(),b.queryHistorySettings(),b.planFlags(),stock);
    }
    private RootRuntimeDomainSettings.Configuration actualDomainSettingsFixture(Path root,Clock clock)throws Exception {
        Files.createDirectories(root);
        Path budget=root.resolve("formal-budget.json"),model=root.resolve("formal-model.json");
        Files.writeString(budget,"{\"fixture\":\"budget-original\"}\n");Files.writeString(model,"{\"fixture\":\"model-original\"}\n");
        Path inventory=root.resolve("normal-exit-source-inventory-v1.json"),profile=root.resolve("original-managed-profile.json"),
                settings=root.resolve("immutable-original-settings.txt");
        // Nonempty explicit physical data exercises custody. These are not claimed as a valid inventory or Managed profile.
        Files.writeString(inventory,"custody-only inventory fixture\n");Files.writeString(profile,"custody-only profile fixture\n");
        Files.writeString(settings,"custody-only original settings fixture\n");
        Path coaLimits=root.resolve("coa-vfs-source-read-limits.json");
        Files.write(coaLimits,CoaVfs.encodeLimits(new CoaVfs.Limits(65536,32768)).bytes());
        var observed=clock.instant();var review=observed.plusSeconds(3600);
        var queryRequest=new OriginalDriverQueryHistorySettings.Request(WindowsJobProcess.currentMachineId(),observed,review,
                new OriginalDriverQueryHistorySettings.JavaConfigured(new OriginalDriverQueryHistorySettings.Directory(root.resolve("query-history-state")),
                        4096,OriginalDriverQueryHistorySettings.Admission.ROOT_STORAGE));
        Path rawRequest=root.resolve("army-query-history-raw-request.json"),producerSource=root.resolve("query-history-data-custody-source.txt"),
                queryDocument=root.resolve("army-query-history-document.json");
        Files.write(rawRequest,OriginalDriverQueryHistorySettings.encodeRequest(queryRequest));
        Files.writeString(producerSource,"custody-only producer-source fixture, not a NativeLaunchPlan runtime member");
        var document=new OriginalDriverQueryHistorySettings.Document(new OriginalDriverQueryHistorySettings.SourceRefs(
                exact(measure(rawRequest)),exact(measure(producerSource))),queryRequest);
        Files.write(queryDocument,OriginalDriverQueryHistorySettings.encode(document));
        // Sole NT codecs produce real data; this provenance fixture is never supplied to NT.readExact/Native Bound.
        return new RootRuntimeDomainSettings.Configuration(RootRuntimeDomainSettings.SCHEMA,
                WindowsJobProcess.currentMachineId(),observed.toString(),review.toString(),
                new RootRuntimeDomainSettings.Lifecycle(root.resolve("state").toString(),root.resolve("save games").toString(),
                        root.resolve("tutorial").toString(),root.resolve("evidence").toString(),List.of("fixture.clock"),1000),
                root.resolve("relations").toString(),new RootRuntimeDomainSettings.FormalWar(measure(budget),measure(model),null,null),
                new RootRuntimeDomainSettings.Peacetime(true,true,true),
                new RootRuntimeDomainSettings.Offline(root.resolve("offline-work").toString(),root.resolve("offline-knowledge").toString(),
                        root.resolve("offline-grants.json").toString(),2,16),
                new RootRuntimeDomainSettings.NormalExitOriginals(exact(measure(inventory)),exact(measure(profile)),exact(measure(settings))),
                new RootRuntimeDomainSettings.CoaReadLimits(measure(coaLimits)),exact(measure(queryDocument)),
                new RootRuntimeDomainSettings.PlanFlags(true,false,true,false,true,false,true),null);
    }
    private Configuration selectData(Configuration base,DataPin original)throws Exception {
        var data=new ArrayList<>(base.originalData());boolean replaced=false;
        for(int index=0;index<data.size();index++)if(original.role()==data.get(index).role()) {
            data.set(index,original);replaced=true;
        }
        assertTrue(replaced);
        Configuration produced=RootRuntimeDefinitions.rebindInputs(base,base.applicationRef(),data);
        Configuration consumed=RootRuntimeDefinitions.decodeConfiguration(RootRuntimeDefinitions.encodeConfiguration(produced));
        assertEquals(produced,consumed);assertTrue(consumed.originalData().contains(original));
        for(DataPin retained:base.originalData())if(retained.role()!=original.role())assertTrue(consumed.originalData().contains(retained));
        data.clear();assertEquals(base.originalData().size(),consumed.originalData().size());
        return consumed;
    }
    private static List<DataRole> runtimeDataRoles(){return List.of(DataRole.LIFE_SETTINGS,DataRole.ADVANCE_TIMINGS,
            DataRole.CAMPAIGN_DEADLINE,DataRole.REMAINING_DOMAIN_SETTINGS,DataRole.NATIVE_DOMAIN_ORIGINALS,
            DataRole.PORTABLE_EVENT_EVIDENCE_MANIFEST,DataRole.ORIGINAL_DRIVER_RUN_PROFILE,DataRole.ORIGINAL_MCP_CAPTURE_RECEIPT,
            DataRole.FAMILY_DOMAIN,DataRole.CHILD_MATRILINEAL_DOMAIN,DataRole.DEFAULT_MARRIAGE_DOMAIN);}
    private SelectedSource inventorySource(String name){return new SelectedSource("local-service/src/main/java/fixture/"+name+".java",new ExactRef(temporary.resolve(name+".java").toString(),1,SHA));}
    private static ExactRef exact(FileRef ref){return new ExactRef(ref.path(),ref.bytes(),ref.sha256());}
    private static FileRef measure(Path path)throws Exception{return new FileRef(path.toString(),Files.size(path),hash(Files.readAllBytes(path)));}
    private static String hash(byte[] bytes)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));}
}
