package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.charset.StandardCharsets;
import org.xar.ck3.control.build.OriginalMcpCapture;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleCodec;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.nativebridge.capabilities.frontendfixture.FrontendFixturePolicy;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding;
import static org.xar.ck3.control.service.root.RootSelectedRegistrationConfiguration.*;

/** Configuration data producer/serde and actual Windows physical-read boundaries. No fixture constructs Bound, a Native plan or Java admission.
 * The physical settings -> actual FrozenProfile -> Bound -> public exclusion integration needs the full Root graph. */
class RootSelectedRegistrationConfigurationTest {
    @TempDir Path root;
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private Configuration value(){
        var refs=new ArrayList<SourceInput>();for(var role:SourceRole.values())refs.add(new SourceInput(role,ref(role.name()+".json")));
        return new Configuration("software-configuration-fixture",NOW,NOW.plusSeconds(3600),Intent.FRESH_ROBERT_1066_ALL_ORDINARY,
                ref("RootSelectedRegistrationConfiguration.java"),refs,new ConstructorKeywords(3,false,false,true,
                    new SuccessionLifecycleBinding(SuccessionLifecycleBinding.Profile.ORDINARY_FROZEN_OFF,"prepared-environment-manifest","1".repeat(64))));
    }
    private ExactRef ref(String name){return new ExactRef(root.resolve(name).toString(),7,"2".repeat(64));}
    private com.fasterxml.jackson.databind.node.ObjectNode json(){return (com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encode(value()),MAXIMUM_BYTES);}
    private void reject(com.fasterxml.jackson.databind.JsonNode changed)throws Exception {
        byte[] actual=ControlBuild.strictMapper().writeValueAsBytes(changed);
        assertThrows(IllegalArgumentException.class,()->decode(actual));
    }
    @Test void soleEncoderProducesClosedActualCaptureShapeAndAll79OrdinaryFlags() {
        Configuration actual=value();assertEquals(actual,decode(encode(actual)));var body=json();
        assertEquals(79,RegistrationFlag.values().length);assertEquals(79,body.get("registration_attributes").size());
        for(var flag:RegistrationFlag.values())assertTrue(body.get("registration_attributes").get(flag.wire()).booleanValue());
        assertTrue(body.get("fixture_policy").isNull());assertTrue(body.get("profile_directory").isNull());
        assertEquals(9,body.get("source_inputs").size());assertEquals(6,body.get("constructor_keywords").size());
        assertFalse(body.get("registration_attributes").has("submit_regular_maa_create_private_v1"));
        assertFalse(body.get("registration_attributes").has("case_declared_read_only_mcp_tools"));
    }
    @Test void missingFalseNullOrNumericOrdinaryFlagsCannotConcealAnUnmigratedTool()throws Exception {
        String key=RegistrationFlag.PLAYER_RITE_CREATION_ACTIONS.wire();var body=json();
        ((com.fasterxml.jackson.databind.node.ObjectNode)body.get("registration_attributes")).remove(key);reject(body);
        body=json();((com.fasterxml.jackson.databind.node.ObjectNode)body.get("registration_attributes")).put(key,false);reject(body);
        body=json();((com.fasterxml.jackson.databind.node.ObjectNode)body.get("registration_attributes")).putNull(key);reject(body);
        body=json();((com.fasterxml.jackson.databind.node.ObjectNode)body.get("registration_attributes")).put(key,1);reject(body);
    }
    @Test void methodsAllowlistBusinessFixtureAndUnknownInputsCannotBeIntroducedBySerde()throws Exception {
        var body=json();((com.fasterxml.jackson.databind.node.ObjectNode)body.get("registration_attributes")).put("submit_regular_maa_create_private_v1",true);reject(body);
        body=json();((com.fasterxml.jackson.databind.node.ObjectNode)body.get("registration_attributes")).putArray("case_declared_read_only_mcp_tools");reject(body);
        body=json();body.putObject("fixture_policy").put("profile_id","fake-business-fixture");reject(body);
        body=json();body.put("profile_directory",root.toString());reject(body);
        body=json();body.put("nonwar_only",true);reject(body);
        body=json();((com.fasterxml.jackson.databind.node.ObjectNode)body.withArray("source_inputs").get(1)).put("role",SourceRole.ROOT_INTENT.name());reject(body);
    }
    @Test void routeSpeedMustBeIntegerAndLifecycleMustBeExplicit()throws Exception {
        for(var bad:List.of(com.fasterxml.jackson.databind.node.BooleanNode.TRUE,com.fasterxml.jackson.databind.node.DecimalNode.valueOf(new java.math.BigDecimal("3.0")))) {
            var body=json();((com.fasterxml.jackson.databind.node.ObjectNode)body.get("constructor_keywords")).set("route_contact_timeline_speed",bad);reject(body);
        }
        var body=json();((com.fasterxml.jackson.databind.node.ObjectNode)body.get("constructor_keywords")).remove("succession_lifecycle_binding");reject(body);
        assertThrows(IllegalArgumentException.class,()->new ConstructorKeywords(4,false,false,true,value().constructorKeywords().lifecycle()));
        assertThrows(IllegalArgumentException.class,()->new ConstructorKeywords(3,false,false,true,SuccessionLifecycleBinding.unknown()));
    }
    @Test void precedingRootIntentIsStrictFreshRobertAllOrdinaryAndDoesNotReferenceFinalDefinitions() {
        var intent=new IntentRequest("software-configuration-fixture",NOW,NOW.plusSeconds(3600),Intent.FRESH_ROBERT_1066_ALL_ORDINARY);
        assertEquals(intent,decodeIntent(encodeIntent(intent)));var body=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encodeIntent(intent),MAXIMUM_BYTES);
        assertFalse(body.has("runtime_definitions"));assertFalse(body.has("final_startup"));
        body.put("ordinary_production_capabilities","NONWAR_ONLY");assertThrows(IllegalArgumentException.class,()->decodeIntent(StrictJson.canonical(body,MAXIMUM_BYTES)));
        assertFalse(Arrays.stream(Bound.class.getConstructors()).findAny().isPresent());
        assertFalse(Arrays.stream(Exclusion.class.getConstructors()).findAny().isPresent());
    }
    private Configuration fixture(Intent intent) {
        Configuration ordinary=value();var binding=new FrontendFixturePolicy.Binding("3".repeat(64),"4".repeat(64),
                intent==Intent.EXPLICIT_SCENARIO_FIXTURE?Optional.of(FrontendFixturePolicy.SCENARIO_TARGET):Optional.empty());
        return new Configuration(ordinary.machineId(),ordinary.observedAt(),ordinary.reviewAt(),intent,ordinary.configurationProducer(),
                ordinary.sourceInputs(),new ConstructorKeywords(3,false,false,true,Optional.empty()),Optional.of(new FixtureSelection(binding,root.resolve("profile"))));
    }
    @Test void explicitPolicyVariantsRoundTripAndSelectExactlyTheirOriginalTool() {
        for(Intent intent:List.of(Intent.EXPLICIT_ROBERT_FIXTURE,Intent.EXPLICIT_SCENARIO_FIXTURE)) {
            Configuration value=fixture(intent);assertEquals(value,decode(encode(value)));
            var wire=StrictJson.parse(encode(value),MAXIMUM_BYTES);assertEquals("native_campaign",wire.get("constructor_keywords").get("episode_projection").textValue());
            assertEquals(intent.fixtureKind(),value.fixture().orElseThrow().binding().kind());
            var request=new IntentRequest(value.machineId(),NOW,NOW.plusSeconds(3600),intent,Optional.of(ref("fixture-policy.json")),Optional.of(root.resolve("profile")));
            assertEquals(request,decodeIntent(encodeIntent(request)));
        }
    }
    @Test void fixturePolicyProfileProjectionAndIntentCannotBeLostOrCrossed()throws Exception {
        for(String key:List.of("fixture_policy","profile_directory")) {
            var wire=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encode(fixture(Intent.EXPLICIT_ROBERT_FIXTURE)),MAXIMUM_BYTES);
            wire.remove(key);reject(wire);
            wire=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encode(fixture(Intent.EXPLICIT_ROBERT_FIXTURE)),MAXIMUM_BYTES);
            wire.putNull(key);reject(wire);
        }
        var wire=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encode(fixture(Intent.EXPLICIT_SCENARIO_FIXTURE)),MAXIMUM_BYTES);
        wire.put("intent",Intent.EXPLICIT_ROBERT_FIXTURE.name());reject(wire);
        wire=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encode(fixture(Intent.EXPLICIT_ROBERT_FIXTURE)),MAXIMUM_BYTES);
        ((com.fasterxml.jackson.databind.node.ObjectNode)wire.get("constructor_keywords")).put("episode_projection","one_life");reject(wire);
        assertThrows(IllegalArgumentException.class,()->new IntentRequest("software-configuration-fixture",NOW,NOW.plusSeconds(3600),Intent.EXPLICIT_ROBERT_FIXTURE));
    }
    @Test void selectedIntentRejectsMissingNullOrForeignFixtureAndOldSchema() {
        var request=new IntentRequest("software-configuration-fixture",NOW,NOW.plusSeconds(3600),Intent.EXPLICIT_SCENARIO_FIXTURE,
                Optional.of(ref("fixture-policy.json")),Optional.of(root.resolve("profile")));
        var wire=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encodeIntent(request),MAXIMUM_BYTES);
        wire.putNull("fixture_policy");assertThrows(IllegalArgumentException.class,()->decodeIntent(StrictJson.canonical(wire,MAXIMUM_BYTES)));
        var old=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encodeIntent(request),MAXIMUM_BYTES);
        old.put("schema","xar.java-root-selected-intent/v1");assertThrows(IllegalArgumentException.class,()->decodeIntent(StrictJson.canonical(old,MAXIMUM_BYTES)));
        var ordinary=json();ordinary.put("schema","xar.original-mcp-current-configuration/v1");assertThrows(IllegalArgumentException.class,()->decode(StrictJson.canonical(ordinary,MAXIMUM_BYTES)));
    }

    @Test void fixtureNullLifecycleIsRequiredAndCannotMasqueradeAsOrdinaryOrModAbsence()throws Exception {
        for(Intent intent:Intent.values()) {
            Configuration original=variant(intent);
            var wire=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encode(original),MAXIMUM_BYTES);
            var constructor=(com.fasterxml.jackson.databind.node.ObjectNode)wire.get("constructor_keywords");
            if(intent.nativeCampaign())constructor.set("succession_lifecycle_binding",StrictJson.parse(SuccessionLifecycleCodec.encode(value().constructorKeywords().lifecycle().orElseThrow()),SuccessionLifecycleCodec.MAX_BYTES));
            else constructor.putNull("succession_lifecycle_binding");
            reject(wire);rejectCapture(wire,original);
            wire=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encode(original),MAXIMUM_BYTES);
            ((com.fasterxml.jackson.databind.node.ObjectNode)wire.get("constructor_keywords")).remove("succession_lifecycle_binding");reject(wire);rejectCapture(wire,original);
            for(String schema:List.of("xar.original-mcp-current-configuration/v1","xar.original-mcp-current-configuration/v2","xar.original-mcp-current-configuration/v3")) {
                wire=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encode(original),MAXIMUM_BYTES);wire.put("schema",schema);reject(wire);rejectCapture(wire,original);
            }
        }
    }

    @Test void actualCapturedElifExcludesOnlyItsFalseBranchAndNeverHidesTheSelectedProducer() {
        // Exact condition spelling read from original catalog 53514B / 159fa20d0887c04d6c77dd97da9d2ee155cdb6ccf0bd7791011b9e711c5a1aed.
        String scenario="isinstance(fixture_binding, dict) and fixture_binding.get(\"profile_id\") is not None";
        String present="fixture_binding is not None";String other="NOT("+scenario+")";
        var declaration=new org.xar.ck3.control.service.mcp.McpCoverage.Declaration("ck3_submit_frontend_fixture_robert_start_v1",ref("mcp_server.py"),4589,4591,"create_server",List.of(other,present));
        assertEquals(present,fixtureFalseClause(value(),declaration));
        assertNull(fixtureFalseClause(fixture(Intent.EXPLICIT_ROBERT_FIXTURE),declaration));
        assertEquals(other,fixtureFalseClause(fixture(Intent.EXPLICIT_SCENARIO_FIXTURE),declaration));
        var missing=new org.xar.ck3.control.service.mcp.McpCoverage.Declaration(declaration.name(),declaration.source(),4589,4591,"create_server",List.of(present));
        assertNull(fixtureFalseClause(fixture(Intent.EXPLICIT_SCENARIO_FIXTURE),missing));
    }

    private Configuration variant(Intent intent) {
        if(intent.fixture())return fixture(intent);if(!intent.saved())return value();
        var ordinary=value();return new Configuration(ordinary.machineId(),ordinary.observedAt(),ordinary.reviewAt(),intent,
                ordinary.configurationProducer(),ordinary.sourceInputs(),new ConstructorKeywords(2,false,false,true,
                    intent.nativeCampaign()?Optional.empty():ordinary.constructorKeywords().lifecycle()),Optional.empty(),Optional.of(root.resolve("saved-profile")));
    }
    @Test void actualSavedIntentEncoderPreservesItsExplicitProfileWithoutSelectingFixture()throws Exception {
        for(Intent intent:List.of(Intent.SAVED_GAME_ALL_ORDINARY,Intent.SAVED_NATIVE_CAMPAIGN)) {
            var request=new IntentRequest(value().machineId(),NOW,NOW.plusSeconds(3600),intent,Optional.empty(),Optional.of(root.resolve("saved-profile")));
            assertEquals(request,decodeIntent(encodeIntent(request)));
            var wire=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encodeIntent(request),MAXIMUM_BYTES);
            assertTrue(wire.get("fixture_policy").isNull());assertEquals(root.resolve("saved-profile").toString(),wire.get("profile_directory").textValue());
            wire.putNull("profile_directory");assertThrows(IllegalArgumentException.class,()->decodeIntent(StrictJson.canonical(wire,MAXIMUM_BYTES)));
            assertThrows(IllegalArgumentException.class,()->new IntentRequest(value().machineId(),NOW,NOW.plusSeconds(3600),intent));
            var config=variant(intent);assertEquals(config,decode(encode(config)));
            var invalid=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encode(config),MAXIMUM_BYTES);
            invalid.putNull("profile_directory");reject(invalid);rejectCapture(invalid,config);
        }
    }
    private Configuration captureValue(Intent intent) {
        Configuration actual=variant(intent);
        var knobs=new ConstructorKeywords(intent.saved()?2:intent==Intent.FRESH_ROBERT_1066_ALL_ORDINARY?1:intent==Intent.EXPLICIT_ROBERT_FIXTURE?4:5,
                intent.fixture(),intent==Intent.EXPLICIT_ROBERT_FIXTURE,intent==Intent.EXPLICIT_SCENARIO_FIXTURE,actual.constructorKeywords().lifecycle());
        return new Configuration(actual.machineId(),actual.observedAt(),actual.reviewAt(),actual.intent(),actual.configurationProducer(),actual.sourceInputs(),knobs,actual.fixture(),actual.savedProfileDirectory());
    }
    private OriginalMcpCapture.SelectedConfiguration capture(Configuration actual)throws Exception {
        var p=actual.configurationProducer();
        return OriginalMcpCapture.decodeSelectedConfiguration(encode(actual),actual.machineId(),new ControlBuild.FileRef(p.path(),p.bytes(),p.sha256()));
    }
    private void rejectCapture(com.fasterxml.jackson.databind.node.ObjectNode wire,Configuration actual)throws Exception {
        byte[] complete=StrictJson.canonical(wire,MAXIMUM_BYTES);var p=actual.configurationProducer();
        assertThrows(IllegalArgumentException.class,()->OriginalMcpCapture.decodeSelectedConfiguration(complete,actual.machineId(),new ControlBuild.FileRef(p.path(),p.bytes(),p.sha256())));
    }
    @Test void actualRootEncoderFeedsSoleCaptureDecoderForAllFiveVariantsAndEveryConstructorField()throws Exception {
        assertEquals(java.util.Arrays.stream(RegistrationFlag.values()).map(RegistrationFlag::wire).collect(java.util.stream.Collectors.toSet()),
                java.util.Arrays.stream(OriginalMcpCapture.RegistrationAttribute.values()).map(OriginalMcpCapture.RegistrationAttribute::wire).collect(java.util.stream.Collectors.toSet()));
        for(Intent intent:Intent.values()) {
            Configuration actual=captureValue(intent);var decoded=capture(actual);var expected=actual.constructorKeywords();var got=decoded.constructorArguments();
            assertEquals(intent.name(),decoded.intent().name());assertEquals(actual.machineId(),decoded.machineId());
            assertEquals(actual.observedAt().toString(),decoded.observedAtUtc());assertEquals(actual.reviewAt().toString(),decoded.reviewAtUtc());
            assertEquals(expected.routeContactTimelineSpeed(),got.routeContactTimelineSpeed());assertEquals(expected.allowRouteContactHighSpeedAb(),got.allowRouteContactHighSpeedAb());
            assertEquals(expected.stationaryObjectiveHoldCanaryRequested(),got.stationaryObjectiveHoldCanaryRequested());assertEquals(expected.warDailyWatchEnabled(),got.warDailyWatchEnabled());
            assertEquals(intent.nativeCampaign()?"native_campaign":"one_life",got.projection().wire());
            if(intent.nativeCampaign())assertEquals("null",got.lifecycle().canonicalJson());
            else assertEquals(expected.lifecycle().orElseThrow(),SuccessionLifecycleCodec.decode(got.lifecycle().canonicalJson().getBytes(StandardCharsets.UTF_8)));
            assertEquals(SourceRole.values().length,decoded.sources().size());
            for(var role:SourceRole.values()) {var source=actual.source(role);var observed=decoded.sources().stream().filter(row->row.role().name().equals(role.name())).findFirst().orElseThrow().original();
                assertEquals(new ControlBuild.FileRef(source.path(),source.bytes(),source.sha256()),observed);}
            assertEquals(actual.fixture().isPresent(),decoded.fixture().isPresent());
            assertEquals(intent.saved()?actual.savedProfileDirectory():actual.fixture().map(FixtureSelection::profileDirectory),decoded.profileDirectory());
            if(intent.fixture()) {var selection=decoded.fixture().orElseThrow();var original=actual.fixture().orElseThrow();
                assertEquals(original.profileDirectory(),selection.profileDirectory());assertEquals(original.binding().policySha256(),selection.binding().policySha256());
                assertEquals(original.binding().preparationSha256(),selection.binding().preparationSha256());assertEquals(intent==Intent.EXPLICIT_SCENARIO_FIXTURE,selection.binding().scenarioTarget().isPresent());}
            var registered=intent.fixture()?List.of(decoded.intent().selectedFixtureTool()):List.<String>of();
            assertDoesNotThrow(()->OriginalMcpCapture.verifySelectedTools(decoded,registered));
            if(intent.fixture())assertThrows(IllegalArgumentException.class,()->OriginalMcpCapture.verifySelectedTools(decoded,List.of()));
        }
    }
    @Test void captureConsumerRejectsEveryMissingFalseNullOrNumericFlagFromActualRootEncoding()throws Exception {
        Configuration actual=captureValue(Intent.FRESH_ROBERT_1066_ALL_ORDINARY);
        for(var flag:RegistrationFlag.values())for(int fault=0;fault<4;fault++) {
            var wire=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encode(actual),MAXIMUM_BYTES);var flags=(com.fasterxml.jackson.databind.node.ObjectNode)wire.get("registration_attributes");
            switch(fault){case 0->flags.remove(flag.wire());case 1->flags.put(flag.wire(),false);case 2->flags.putNull(flag.wire());default->flags.put(flag.wire(),1);}
            rejectCapture(wire,actual);
        }
    }
    @Test void captureConsumerRejectsCrossedFixtureProjectionOldVersionAndWrongScalarTypes()throws Exception {
        for(Intent intent:Intent.values()) {
            Configuration actual=captureValue(intent);
            for(var bad:List.of(com.fasterxml.jackson.databind.node.BooleanNode.TRUE,com.fasterxml.jackson.databind.node.DecimalNode.valueOf(new java.math.BigDecimal("3.0")),com.fasterxml.jackson.databind.node.TextNode.valueOf("3"))) {
                var wire=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encode(actual),MAXIMUM_BYTES);
                ((com.fasterxml.jackson.databind.node.ObjectNode)wire.get("constructor_keywords")).set("route_contact_timeline_speed",bad);rejectCapture(wire,actual);
            }
            var wire=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encode(actual),MAXIMUM_BYTES);
            wire.put("schema","xar.original-mcp-current-configuration/v1");rejectCapture(wire,actual);
            if(intent.fixture())for(String required:List.of("fixture_policy","profile_directory")) {
                wire=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encode(actual),MAXIMUM_BYTES);wire.remove(required);rejectCapture(wire,actual);
                wire=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encode(actual),MAXIMUM_BYTES);wire.putNull(required);rejectCapture(wire,actual);
            }
            wire=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encode(actual),MAXIMUM_BYTES);
            ((com.fasterxml.jackson.databind.node.ObjectNode)wire.get("constructor_keywords")).put("episode_projection",intent.nativeCampaign()?"one_life":"native_campaign");rejectCapture(wire,actual);
        }
        Configuration scenario=captureValue(Intent.EXPLICIT_SCENARIO_FIXTURE);
        var wire=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encode(scenario),MAXIMUM_BYTES);
        ((com.fasterxml.jackson.databind.node.ObjectNode)wire.get("fixture_policy").get("frontend_target")).put("start_date_raw",true);rejectCapture(wire,scenario);
        wire=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(encode(scenario),MAXIMUM_BYTES);wire.put("intent",Intent.EXPLICIT_ROBERT_FIXTURE.name());rejectCapture(wire,scenario);
    }

    @Test void actualWindowsPhysicalReadKeepsTheSelectedForwardReferenceThroughBothCodecs()throws Exception {
        assertTrue(System.getProperty("os.name").startsWith("Windows"),"actual Windows source custody is required; no skipped substitute");
        Path source=root.resolve("RootSelectedRegistrationConfiguration.java");byte[] body="actual selected producer source".getBytes(StandardCharsets.UTF_8);
        Files.write(source,body);ExactRef expected=forwardPhysicalRef(source);
        var measured=ControlBuild.FileRef.measure(source);
        assertNotEquals(expected.path(),measured.path(),"exercise the real forward identity versus Windows observation boundary");
        assertEquals(Path.of(expected.path()),Path.of(measured.path()));
        var retained=new ArrayList<SharedSourceFiles.Witness>();
        assertArrayEquals(body,RootSelectedRegistrationConfiguration.read(expected,MAXIMUM_BYTES,retained));
        assertEquals(1,retained.size());SharedSourceFiles.assertUnchanged(retained.getFirst());
        Configuration original=value();var actual=new Configuration(original.machineId(),original.observedAt(),original.reviewAt(),original.intent(),
                expected,original.sourceInputs(),original.constructorKeywords());
        assertEquals(expected,decode(encode(actual)).configurationProducer(),"physical observation must not rewrite the selected identity");
        assertEquals(expected.path(),capture(actual).producer().path(),"the original capture consumer retains the identical selected JSON reference");
    }
    @Test void actualPhysicalReadRejectsChangedContentEvenWhenItsLengthStillMatches()throws IOException {
        Path source=root.resolve("content.java");Files.writeString(source,"original body",StandardCharsets.UTF_8);ExactRef expected=forwardPhysicalRef(source);
        Files.writeString(source,"tampered body",StandardCharsets.UTF_8);assertEquals(expected.bytes(),Files.size(source));
        var retained=new ArrayList<SharedSourceFiles.Witness>();
        assertThrows(IllegalArgumentException.class,()->RootSelectedRegistrationConfiguration.read(expected,MAXIMUM_BYTES,retained));
        assertTrue(retained.isEmpty(),"changed content must not enter retained source custody");
    }
    @Test void actualPhysicalReadRetainsNativeIdentityAgainstSameBytesReplacement()throws IOException {
        Path source=root.resolve("identity.java"),replacement=root.resolve("replacement.java");
        Files.writeString(source,"actual selected producer source",StandardCharsets.UTF_8);ExactRef expected=forwardPhysicalRef(source);
        var retained=new ArrayList<SharedSourceFiles.Witness>();
        RootSelectedRegistrationConfiguration.read(expected,MAXIMUM_BYTES,retained);var original=retained.getFirst();
        Files.copy(source,replacement);Files.setLastModifiedTime(replacement,Files.getLastModifiedTime(source));
        Files.move(replacement,source,StandardCopyOption.REPLACE_EXISTING);
        assertNotEquals(original.nativeFile().identityKey(),SharedSourceFiles.nativeFile(source).identityKey(),"fixture must replace the actual native file identity");
        assertThrows(IOException.class,()->SharedSourceFiles.assertUnchanged(original));
    }
    private static ExactRef forwardPhysicalRef(Path source)throws IOException {
        var actual=ControlBuild.FileRef.measure(source);
        return new ExactRef(actual.path().replace('\\','/'),actual.bytes(),actual.sha256());
    }

}
