package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual temporary file producer -> strict data reader -> actual typed leaf settings consumers.
 * There is no Native cut, compiled C++/Python, Game, installed clock, policy result or Ready proof in this fixture. */
class RootRuntimeOriginalSettingsTest {
    @TempDir Path root;
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final Clock CLOCK=Clock.fixed(NOW,ZoneOffset.UTC);
    private RootRuntimeDomainSettings.Configuration settings(String machine)throws IOException {
        FileRef budget=write(root.resolve("budget.json"),"{\"test_policy_original\":\"budget\"}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        FileRef model=write(root.resolve("model.json"),"{\"test_policy_original\":\"model\"}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        FileRef inventory=write(root.resolve("normal-exit-inventory.json"),"{\"custody_fixture\":\"inventory\"}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        FileRef managedProfile=write(root.resolve("normal-exit-managed-profile.json"),"{\"custody_fixture\":\"profile\"}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        FileRef settingsSnapshot=write(root.resolve("original-settings-snapshot.txt"),"actual immutable settings custody fixture".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        FileRef coaLimits=write(root.resolve("coa-read-limits.json"),
                org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.CoaVfs.encodeLimits(
                        new org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.CoaVfs.Limits(65536,32768)).bytes());
        var lifecycle=new RootRuntimeDomainSettings.Lifecycle(root.resolve("state").toString(),root.resolve("saves").toString(),
                root.resolve("tutorial.ck3").toString(),root.resolve("evidence").toString(),List.of("fixture-expected-life-handler"),30000);
        return new RootRuntimeDomainSettings.Configuration(RootRuntimeDomainSettings.SCHEMA,machine,NOW.minusSeconds(1).toString(),NOW.plusSeconds(3600).toString(),
                lifecycle,root.resolve("relations").toString(),new RootRuntimeDomainSettings.FormalWar(budget,model,null,null),
                new RootRuntimeDomainSettings.Peacetime(true,true,true),new RootRuntimeDomainSettings.Offline(
                        root.resolve("offline-work").toString(),root.resolve("event-knowledge").toString(),
                        root.resolve("event-knowledge/grants.json").toString(),3,11),new RootRuntimeDomainSettings.NormalExitOriginals(
                        exact(inventory),exact(managedProfile),exact(settingsSnapshot)),new RootRuntimeDomainSettings.CoaReadLimits(coaLimits),queryHistory(machine),
                        new RootRuntimeDomainSettings.PlanFlags(true,false,true,false,true,false,true),null);
    }
    private org.xar.ck3.control.contracts.ExactRef queryHistory(String machine)throws IOException {
        var request=new org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings.Request(machine,
                NOW.minusSeconds(2),NOW.plusSeconds(3601),new org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings.JavaConfigured(
                new org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings.Disabled(),12345,
                org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings.Admission.ROOT_STORAGE));
        var raw=write(root.resolve("army-query-history-request.json"),org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings.encodeRequest(request));
        // A physical data-custody fixture only; this is never accepted as a selected/compiled NativePlan producer.
        var producer=write(root.resolve("RootArmyQueryHistoryConfigurationProducer.java"),"custody-only-source-original".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        var document=new org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings.Document(
                new org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings.SourceRefs(exact(raw),exact(producer)),request);
        return exact(write(root.resolve("army-query-history-settings.json"),org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings.encode(document)));
    }
    private RootRuntimeNativeOriginals.Configuration originals()throws IOException {
        var entries=new ArrayList<RootRuntimeNativeOriginals.Original>();
        for(var role:RootRuntimeNativeOriginals.Role.values()){
            Path path=root.resolve(Path.of(role.repositoryRelative()).getFileName());
            FileRef actual=write(path,("physical provenance fixture "+role.name()).getBytes(java.nio.charset.StandardCharsets.UTF_8));
            entries.add(new RootRuntimeNativeOriginals.Original(role,role.repositoryRelative(),actual));
        }
        return new RootRuntimeNativeOriginals.Configuration(RootRuntimeNativeOriginals.SCHEMA,WindowsJobProcess.currentMachineId(),
                NOW.minusSeconds(1).toString(),NOW.plusSeconds(3600).toString(),entries);
    }
    @Test void actualSettingsProducerReaderAndTypedLifecycleMilitaryConsumersPreserveExplicitValues()throws IOException {
        var configuration=settings(WindowsJobProcess.currentMachineId());byte[] encoded=RootRuntimeDomainSettings.encode(configuration);
        assertEquals(configuration,RootRuntimeDomainSettings.decode(encoded));
        var bound=RootRuntimeDomainSettings.readExact(write(root.resolve("domain-settings.json"),encoded),CLOCK);bound.requireCurrent(CLOCK);
        assertEquals(configuration.lifecycle().stateRoot(),bound.configuration().lifecycle().configuration().stateRoot().toString());
        assertEquals(java.time.Duration.ofMillis(30000),bound.configuration().lifecycle().configuration().actionBudget());
        assertTrue(bound.configuration().peacetime().options().enabled());assertTrue(bound.configuration().peacetime().options().giftEnabled());
        assertEquals(10,bound.retainedOriginals().size());
    }
    @Test void allActualNativeHeaderAndPythonProvenanceRolesRoundTripAndReachThePhysicalConsumer()throws IOException {
        var configuration=originals();byte[] encoded=RootRuntimeNativeOriginals.encode(configuration);
        assertEquals(configuration,RootRuntimeNativeOriginals.decode(encoded));
        var bound=RootRuntimeNativeOriginals.readExact(write(root.resolve("native-originals.json"),encoded),CLOCK);bound.requireCurrent(CLOCK);
        for(var role:RootRuntimeNativeOriginals.Role.values())assertEquals(configuration.source(role).exact(),bound.source(role));
        assertEquals(RootRuntimeNativeOriginals.Role.values().length+1,bound.retainedOriginals().size());
    }
    @Test void settingsWireRejectsFloatBooleanWrongTypesMissingExplicitNullAndUnknownFields()throws IOException {
        var configuration=settings(WindowsJobProcess.currentMachineId());
        com.fasterxml.jackson.databind.node.ObjectNode body=ControlBuild.strictMapper().valueToTree(configuration);
        body.withObject("/lifecycle").put("action_budget_millis",1.0);
        assertThrows(IOException.class,()->RootRuntimeDomainSettings.decode(wire(body)));
        body.withObject("/lifecycle").put("action_budget_millis",true);
        assertThrows(IOException.class,()->RootRuntimeDomainSettings.decode(wire(body)));
        com.fasterxml.jackson.databind.node.ObjectNode missing=ControlBuild.strictMapper().valueToTree(configuration);
        missing.withObject("/formal_war").remove("budget_override");
        assertThrows(IOException.class,()->RootRuntimeDomainSettings.decode(wire(missing)));
        com.fasterxml.jackson.databind.node.ObjectNode extra=ControlBuild.strictMapper().valueToTree(configuration);extra.put("fallback_enabled",true);
        assertThrows(IOException.class,()->RootRuntimeDomainSettings.decode(wire(extra)));
    }
    @Test void nativeRoleInventoryRejectsMissingDuplicateRoleWrongRepositoryAndJavaStandIn()throws IOException {
        var configuration=originals();var first=configuration.originals().getFirst();
        var missing=new ArrayList<>(configuration.originals());missing.removeFirst();
        assertThrows(IllegalArgumentException.class,()->new RootRuntimeNativeOriginals.Configuration(configuration.schema(),configuration.machineId(),
                configuration.observedAtUtc(),configuration.reviewAtUtc(),missing));
        var duplicate=new ArrayList<>(configuration.originals());duplicate.set(1,first);
        assertThrows(IllegalArgumentException.class,()->new RootRuntimeNativeOriginals.Configuration(configuration.schema(),configuration.machineId(),
                configuration.observedAtUtc(),configuration.reviewAtUtc(),duplicate));
        assertThrows(IllegalArgumentException.class,()->new RootRuntimeNativeOriginals.Original(first.role(),"not/the/actual/source.py",first.original()));
        FileRef java=write(root.resolve("WrongJava.java"),new byte[]{'x'});
        assertThrows(IllegalArgumentException.class,()->new RootRuntimeNativeOriginals.Original(first.role(),first.repositoryRelative(),java));
    }
    @Test void nestedPolicySameBytesReplacementCannotResetSettingsOriginalFileIdentity()throws IOException {
        var configuration=settings(WindowsJobProcess.currentMachineId());var bound=RootRuntimeDomainSettings.readExact(
                write(root.resolve("domain-settings.json"),RootRuntimeDomainSettings.encode(configuration)),CLOCK);
        replaceSameBytes(Path.of(configuration.formalWar().defaultBudget().path()));assertThrows(IOException.class,()->bound.requireCurrent(CLOCK));
    }
    @Test void nativeOriginalSameBytesReplacementCannotResetProvenanceIdentity()throws IOException {
        var configuration=originals();var bound=RootRuntimeNativeOriginals.readExact(
                write(root.resolve("native-originals.json"),RootRuntimeNativeOriginals.encode(configuration)),CLOCK);
        replaceSameBytes(Path.of(configuration.source(RootRuntimeNativeOriginals.Role.NATIVE_DISPATCHER).original().path()));
        assertThrows(IOException.class,()->bound.requireCurrent(CLOCK));
    }
    @Test void foreignAndExpiredSettingsRefusePhysicalAdmissionAndDisabledOrdinaryPoliciesAreRejected()throws IOException {
        var configuration=settings("foreign-storage-fixture");FileRef original=write(root.resolve("foreign-settings.json"),RootRuntimeDomainSettings.encode(configuration));
        assertThrows(IOException.class,()->RootRuntimeDomainSettings.readExact(original,CLOCK));
        var actual=settings(WindowsJobProcess.currentMachineId());FileRef current=write(root.resolve("current-settings.json"),RootRuntimeDomainSettings.encode(actual));
        assertThrows(IOException.class,()->RootRuntimeDomainSettings.readExact(current,Clock.fixed(NOW.plusSeconds(3601),ZoneOffset.UTC)));
        assertThrows(IllegalArgumentException.class,()->new RootRuntimeDomainSettings.Peacetime(true,false,true));
    }
    @Test void duplicateWireKeysAndUnsafeIntegerSettingsAreNotNormalizedIntoValidInputs()throws IOException {
        String duplicate="{\"schema\":\"x\",\"schema\":\"y\"}";
        assertThrows(IOException.class,()->RootRuntimeDomainSettings.decode(duplicate.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        var configuration=settings(WindowsJobProcess.currentMachineId());
        com.fasterxml.jackson.databind.node.ObjectNode body=ControlBuild.strictMapper().valueToTree(configuration);
        body.withObject("/lifecycle").put("action_budget_millis",java.math.BigInteger.valueOf(9007199254740992L));
        assertThrows(IOException.class,()->RootRuntimeDomainSettings.decode(wire(body)));
    }
    @Test void offlineSettingsReachActualWorkerConstructorAndRejectMissingOrOldSchema()throws IOException {
        var configuration=settings(WindowsJobProcess.currentMachineId());
        var bound=RootRuntimeDomainSettings.readExact(write(root.resolve("offline-settings.json"),RootRuntimeDomainSettings.encode(configuration)),CLOCK);
        var actual=bound.configuration().offline().configuration();
        assertEquals(root.resolve("offline-work"),actual.worker().workRoot());
        assertEquals(root.resolve("event-knowledge"),actual.knowledgeRoot());assertEquals(root.resolve("event-knowledge/grants.json"),actual.grantsManifest());
        var row=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(RootRuntimeDomainSettings.encode(configuration));row.remove("offline");
        assertThrows(IOException.class,()->RootRuntimeDomainSettings.decode(wire(row)));
        var old=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(RootRuntimeDomainSettings.encode(configuration));old.put("schema","xar.java-root-domain-settings/v1");
        assertThrows(IOException.class,()->RootRuntimeDomainSettings.decode(wire(old)));
        assertThrows(IllegalArgumentException.class,()->new RootRuntimeDomainSettings.Offline(root.resolve("w").toString(),
                root.resolve("k").toString(),root.resolve("k/g.json").toString(),33,11));
    }

    @Test void normalExitOriginalsAreMandatoryDistinctAndTheirPhysicalCustodyCannotDrift()throws IOException {
        var typed=settings(WindowsJobProcess.currentMachineId());var binding=RootRuntimeDomainSettings.readExact(
                write(root.resolve("domain-settings-normal-exit.json"),RootRuntimeDomainSettings.encode(typed)),CLOCK);
        assertEquals(typed.normalExit().inventory(),binding.configuration().normalExit().input().inventory());
        var wrong=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(RootRuntimeDomainSettings.encode(typed));wrong.remove("normal_exit");
        assertThrows(IOException.class,()->RootRuntimeDomainSettings.decode(wire(wrong)));
        var old=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(RootRuntimeDomainSettings.encode(typed));old.put("schema","xar.java-root-domain-settings/v2");
        assertThrows(IOException.class,()->RootRuntimeDomainSettings.decode(wire(old)));
        Files.writeString(Path.of(typed.normalExit().immutableOriginalSettingsSnapshot().path()),"changed original settings snapshot");
        assertThrows(IOException.class,()->binding.requireCurrent(CLOCK));
        assertThrows(IllegalArgumentException.class,()->new RootRuntimeDomainSettings.NormalExitOriginals(
                typed.normalExit().inventory(),typed.normalExit().inventory(),typed.normalExit().immutableOriginalSettingsSnapshot()));
    }
    @Test void soleCoaLimitsProducerReachesTypedConsumerAndRetainsItsOriginalNativeIdentity()throws IOException {
        var typed=settings(WindowsJobProcess.currentMachineId());
        var bound=RootRuntimeDomainSettings.readExact(write(root.resolve("domain-settings-coa.json"),RootRuntimeDomainSettings.encode(typed)),CLOCK);
        var actual=bound.configuration().coaReadLimits().limits();
        assertEquals(65536,actual.maximumSourceBytes());assertEquals(32768,actual.maximumArchiveBytes());
        var missing=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(RootRuntimeDomainSettings.encode(typed));missing.remove("coa_read_limits");
        assertThrows(IOException.class,()->RootRuntimeDomainSettings.decode(wire(missing)));
        var old=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(RootRuntimeDomainSettings.encode(typed));old.put("schema","xar.java-root-domain-settings/v3");
        assertThrows(IOException.class,()->RootRuntimeDomainSettings.decode(wire(old)));
        replaceSameBytes(Path.of(typed.coaReadLimits().original().path()));assertThrows(IOException.class,()->bound.requireCurrent(CLOCK));
        assertThrows(IllegalArgumentException.class,()->new RootRuntimeDomainSettings.CoaReadLimits(
                new FileRef(root.resolve("too-large-limits.json").toString(),4097,"1".repeat(64))));
    }
    @Test void queryHistoryLeafPreservesExplicitJavaInputAndAllThreeOriginalsRejectIdentityReplacement()throws IOException {
        var typed=settings(WindowsJobProcess.currentMachineId());
        var original=write(root.resolve("domain-settings-query.json"),RootRuntimeDomainSettings.encode(typed));
        var document=org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings.decode(
                Files.readAllBytes(Path.of(typed.queryHistorySettings().path())));
        assertEquals(org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings.Origin.JAVA_CONFIGURED,
                document.request().configuration().origin());
        var configured=(org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings.JavaConfigured)document.request().configuration();
        assertInstanceOf(org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings.Disabled.class,configured.stateDirectory());
        assertEquals(12345,configured.limitBytes());
        for(var ref:List.of(typed.queryHistorySettings(),document.sourceRefs().configurationOriginal(),document.sourceRefs().producerOriginal())){
            var bound=RootRuntimeDomainSettings.readExact(original,CLOCK);
            assertTrue(bound.retainedOriginals().stream().anyMatch(value->value.path().equals(ref.path())&&value.sha256().equals(ref.sha256())));
            Path path=Path.of(ref.path()),kept=path.resolveSibling("old-"+path.getFileName());
            byte[] bytes=Files.readAllBytes(path);Files.move(path,kept);Files.write(path,bytes);
            assertThrows(IOException.class,()->bound.requireCurrent(CLOCK));
            Files.delete(path);Files.move(kept,path);
        }
    }
    @Test void strictV5RequiresQueryHistoryOriginalAndEveryExplicitPlanFlagWithoutBooleanCoercion()throws IOException {
        var typed=settings(WindowsJobProcess.currentMachineId());byte[] encoded=RootRuntimeDomainSettings.encode(typed);
        assertEquals(typed.planFlags(),RootRuntimeDomainSettings.decode(encoded).planFlags());
        var node=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encoded);
        var flags=(com.fasterxml.jackson.databind.node.ObjectNode)node.get("plan_flags");
        assertEquals(7,flags.size());assertTrue(flags.get("allow_private_lifestyle_formal_trial").booleanValue());
        assertFalse(flags.get("allow_private_faction_gift_formal_trial").booleanValue());
        for(String field:List.of("allow_private_lifestyle_formal_trial","allow_private_faction_gift_formal_trial",
                "allow_private_construction_formal_trial","allow_private_family_marriage_formal_trial","allow_private_council_action",
                "allow_private_m5_joint_collector","require_initial_lifestyle_focus_before_date_advance")){
            var missing=node.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)missing.get("plan_flags")).remove(field);
            assertThrows(IOException.class,()->RootRuntimeDomainSettings.decode(wire(missing)));
            var numeric=node.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)numeric.get("plan_flags")).put(field,1);
            assertThrows(IOException.class,()->RootRuntimeDomainSettings.decode(wire(numeric)));
        }
        var missing=node.deepCopy();missing.remove("query_history_settings");
        assertThrows(IOException.class,()->RootRuntimeDomainSettings.decode(wire(missing)));
        var explicitNull=node.deepCopy();explicitNull.putNull("query_history_settings");
        assertThrows(IOException.class,()->RootRuntimeDomainSettings.decode(wire(explicitNull)));
        var old=node.deepCopy();old.put("schema","xar.java-root-domain-settings/v4");
        assertThrows(IOException.class,()->RootRuntimeDomainSettings.decode(wire(old)));
    }
    private static org.xar.ck3.control.contracts.ExactRef exact(FileRef ref){return new org.xar.ck3.control.contracts.ExactRef(ref.path(),ref.bytes(),ref.sha256());}
    private static FileRef write(Path path,byte[] bytes)throws IOException {Files.write(path,bytes);return FileRef.measure(path);}
    private static byte[] wire(com.fasterxml.jackson.databind.JsonNode body)throws IOException{return ControlBuild.strictMapper().writeValueAsBytes(body);}
    private static void replaceSameBytes(Path path)throws IOException {
        Path replacement=path.resolveSibling("replacement-"+path.getFileName());Files.copy(path,replacement);
        Files.setLastModifiedTime(replacement,Files.getLastModifiedTime(path));Files.move(replacement,path,StandardCopyOption.REPLACE_EXISTING);
    }
}
