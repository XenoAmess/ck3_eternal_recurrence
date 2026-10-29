package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.nio.file.Files;
import java.util.Base64;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.OriginalMcpCapture.Role;
import static org.junit.jupiter.api.Assertions.*;

/** Pure wire/typed serde only. These small software vectors are not an original SDK capture or execution release. */
final class OriginalMcpCaptureTest {
    private static final com.fasterxml.jackson.databind.ObjectMapper JSON=ControlBuild.strictMapper();
    private static ObjectNode object(){return JSON.createObjectNode();}
    private static ObjectNode extent(byte[] bytes){return object().put("bytes",bytes.length).put("sha256",OriginalMcpCapture.sha256(bytes));}
    private static byte[] body(){return "{\"schema\":\"xar.original-mcp-declarations/v2\",\"sources\":[],\"declarations\":[]}".getBytes(StandardCharsets.UTF_8);}
    private static ObjectNode frame(byte[] bytes){
        return object().put("kind","document").put("role","catalog").put("bytes",bytes.length).put("sha256",OriginalMcpCapture.sha256(bytes))
            .put("base64",Base64.getEncoder().encodeToString(bytes));
    }
    private static byte[] wire(ObjectNode value){return value.toString().getBytes(StandardCharsets.UTF_8);}
    private static ObjectNode summary(){
        byte[] bytes=body();var n=object().put("schema","xar.original-mcp-memory-measurement/v1").put("machine_id","software-fixture-machine")
            .put("observed_at_utc","2026-10-24T03:00:00Z").put("python_executable",Path.of(".").toAbsolutePath().normalize().resolve("python.exe").toString())
            .put("python_version","software-vector").put("declaration_count",3).put("unconditional_declarations",1).put("conditional_declarations",2)
            .put("actual_registered_tools",2).put("actual_resources",2).put("sdk_descriptor_serde_count",4).put("sdk_wrong_type_missing_field_rejections",6)
            .put("source_prepost_match",true).put("python_writes",0).put("native_peer_observed",false).put("java_admission","NOT_PRODUCED")
            .put("status","MEASURED_ORIGINAL_REGISTRATION_ONLY_NOT_JAVA_OR_GAME");
        n.putObject("configuration_ref").put("path",Path.of(".").toAbsolutePath().normalize().resolve("actual-config.json").toString()).put("bytes",1).put("sha256","a".repeat(64));
        n.putObject("distribution_versions").put("mcp","2.0.0").put("mcp-types","actual-shape").put("pydantic","actual-shape");
        n.putObject("capture_transport_observation").put("actual_pipe","\\\\.\\pipe\\xar_original_mcp_capture_"+"a".repeat(32))
            .put("actual_uncreated_state",Path.of(".").toAbsolutePath().normalize().resolve("readonly-"+"a".repeat(32)).toString()).put("actual_listener_closed",true);
        var docs=n.putObject("documents");for(Role role:Role.values())docs.set(role.wire(),extent(bytes));
        n.putArray("actual_registered_identities").add("tool_one").add("tool_two");n.putArray("unregistered_conditional_identities").add("conditional_tool");return n;
    }
    @Test void exactFiveRoleProtocolKeepsEveryOriginalByteAndChecksExtentAndCanonicalBase64()throws Exception{
        byte[] bytes=body();var expected=OriginalMcpCapture.extent(bytes);
        assertArrayEquals(bytes,OriginalMcpCapture.decodeDocument(wire(frame(bytes)),Role.CATALOG,expected));
        var copy=frame(bytes);copy.put("bytes",bytes.length+1);assertThrows(IllegalArgumentException.class,()->OriginalMcpCapture.decodeDocument(wire(copy),Role.CATALOG,expected));
        var wrong=frame(bytes);wrong.put("sha256","b".repeat(64));assertThrows(IllegalArgumentException.class,()->OriginalMcpCapture.decodeDocument(wire(wrong),Role.CATALOG,expected));
        var kind=frame(bytes);kind.put("role","tools");assertThrows(IllegalArgumentException.class,()->OriginalMcpCapture.decodeDocument(wire(kind),Role.CATALOG,expected));
        var encoded=frame(bytes);encoded.put("base64","%%%");assertThrows(java.io.IOException.class,()->OriginalMcpCapture.decodeDocument(wire(encoded),Role.CATALOG,expected));
        var altered=frame(bytes);altered.put("base64",Base64.getEncoder().encodeToString("{}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class,()->OriginalMcpCapture.decodeDocument(wire(altered),Role.CATALOG,expected));
        var extra=frame(bytes);extra.put("authority",true);assertThrows(IllegalArgumentException.class,()->OriginalMcpCapture.decodeDocument(wire(extra),Role.CATALOG,expected));
        for(String field:List.of("kind","role","bytes","sha256","base64")){
            var absent=frame(bytes);absent.remove(field);assertThrows(IllegalArgumentException.class,()->OriginalMcpCapture.decodeDocument(wire(absent),Role.CATALOG,expected),field);
        }
        for(JsonNode value:List.of(object().put("n",true).get("n"),object().put("n",1.0).get("n"),object().put("n","1").get("n"),object().putNull("n").get("n"))){
            var malformed=frame(bytes);malformed.set("bytes",value);assertThrows(IllegalArgumentException.class,()->OriginalMcpCapture.decodeDocument(wire(malformed),Role.CATALOG,expected));
        }
    }
    @Test void MeasurementUniverseActualSubsetResourcesAndJavaAdmissionRemainDifferentAndRoundTrip()throws Exception{
        var n=summary();var typed=OriginalMcpCapture.parseSummary(n);
        assertEquals(3,typed.counts().declarations());assertEquals(2,typed.counts().registeredTools());assertEquals(2,typed.counts().resources());
        assertEquals(typed,JSON.readValue(JSON.writeValueAsBytes(typed),OriginalMcpCapture.Summary.class));
        assertEquals(typed,OriginalMcpCapture.parseSummary(OriginalMcpCapture.parse(wire(n),131072)));
        assertTrue(typed.documents().maximumWireBytes()>typed.documents().catalog().bytes()*5);
        var admission=summary();admission.put("java_admission","ADMITTED");assertThrows(IllegalArgumentException.class,()->OriginalMcpCapture.parseSummary(admission));
        var peer=summary();peer.put("native_peer_observed",true);assertThrows(IllegalArgumentException.class,()->OriginalMcpCapture.parseSummary(peer));
        var serde=summary();serde.put("sdk_wrong_type_missing_field_rejections",5);assertThrows(IllegalArgumentException.class,()->OriginalMcpCapture.parseSummary(serde));
        var wrong=summary();wrong.put("actual_registered_tools",3);assertThrows(IllegalArgumentException.class,()->OriginalMcpCapture.parseSummary(wrong));
        var duplicate=summary();duplicate.withArray("actual_registered_identities").set(1,object().put("v","tool_one").get("v"));
        assertThrows(IllegalArgumentException.class,()->OriginalMcpCapture.parseSummary(duplicate));
        var bool=summary();bool.put("declaration_count",true);assertThrows(IllegalArgumentException.class,()->OriginalMcpCapture.parseSummary(bool));
        var fractional=summary();fractional.put("declaration_count",3.0);assertThrows(IllegalArgumentException.class,()->OriginalMcpCapture.parseSummary(fractional));
        var missing=summary();missing.remove("capture_transport_observation");assertThrows(IllegalArgumentException.class,()->OriginalMcpCapture.parseSummary(missing));
        var extra=summary();extra.put("faked_bound",true);assertThrows(IllegalArgumentException.class,()->OriginalMcpCapture.parseSummary(extra));
    }
    @Test void strictJsonAndTypedExtentsRejectDuplicateUnknownNullBoolAndUnboundedInputs(){
        assertThrows(java.io.IOException.class,()->OriginalMcpCapture.parse("{\"bytes\":1,\"bytes\":1}".getBytes(StandardCharsets.UTF_8),1024));
        assertThrows(IllegalArgumentException.class,()->new OriginalMcpCapture.Extent(0,"a".repeat(64)));
        assertThrows(IllegalArgumentException.class,()->new OriginalMcpCapture.Extent((16L<<20)+1,"a".repeat(64)));
        assertThrows(IllegalArgumentException.class,()->new OriginalMcpCapture.Transport("\\\\.\\pipe\\existing-game-pipe",Path.of(".").toAbsolutePath().toString(),true));
        assertThrows(IllegalArgumentException.class,()->new OriginalMcpCapture.Transport("\\\\.\\pipe\\xar_original_mcp_capture_"+"a".repeat(32),Path.of(".").toAbsolutePath().toString(),false));
    }
    @Test void typedPlanSerdeNeverCoercesFloatBooleanOrNativeIdentityNumbers()throws Exception{
        Path root=Path.of(".").toAbsolutePath().normalize();var input=new ControlBuild.FileRef(root.resolve("data-only-input").toString(),1,"a".repeat(64));
        var request=new ControlBuild.FileRef(root.resolve("request02").toString(),OriginalMcpCapture.REQUEST_BYTES,OriginalMcpCapture.REQUEST_SHA);
        var plan=new OriginalMcpCapture.Plan(OriginalMcpCapture.PLAN_SCHEMA,"software-fixture-machine","2026-10-24T03:00:00Z","2026-10-24T04:30:00Z",
            request,input,input,root.toString(),root.toString(),new SharedSourceFiles.DirectoryIdentity("1","2","3"),input,60,512L<<20,2L<<20,131072);
        assertEquals(plan,OriginalMcpCapture.decodePlan(OriginalMcpCapture.encodePlan(plan)));
        ObjectNode original=(ObjectNode)JSON.readTree(OriginalMcpCapture.encodePlan(plan));
        for(String key:List.of("timeoutSeconds","memoryLimitBytes","maximumSessionNativeBytes","maximumStderrBytes")){
            var wrong=original.deepCopy();wrong.put(key,true);assertThrows(java.io.IOException.class,()->OriginalMcpCapture.decodePlan(wire(wrong)),key);
            var fraction=original.deepCopy();fraction.put(key,1.0);assertThrows(java.io.IOException.class,()->OriginalMcpCapture.decodePlan(wire(fraction)),key);
        }
        var identity=original.deepCopy();((ObjectNode)identity.get("sessionParentIdentity")).put("fileIdDecimal",2);
        assertThrows(java.io.IOException.class,()->OriginalMcpCapture.decodePlan(wire(identity)),"FileID must remain a decimal string");
        var missing=original.deepCopy();missing.remove("selectedConfigurationRef");assertThrows(java.io.IOException.class,()->OriginalMcpCapture.decodePlan(wire(missing)));
    }

    private static Path fixtureRoot(){return Path.of(".").toAbsolutePath().normalize();}
    private static ControlBuild.FileRef producer(){return new ControlBuild.FileRef(fixtureRoot().resolve("RootSelectedRegistrationConfiguration.java").toString(),41401,"a".repeat(64));}
    private static ObjectNode reference(ControlBuild.FileRef ref){return object().put("path",ref.path()).put("bytes",ref.bytes()).put("sha256",ref.sha256());}
    private static ObjectNode configuration(OriginalMcpCapture.SelectedIntent intent) {
        var cfg=object().put("schema",OriginalMcpCapture.CONFIGURATION_SCHEMA).put("machine_id","software-fixture-machine")
                .put("observed_at_utc","2026-10-24T03:00:00Z").put("review_at_utc","2026-10-24T04:30:00Z").put("intent",intent.name());
        cfg.set("configuration_producer",reference(producer()));var sources=cfg.putArray("source_inputs");
        for(var role:OriginalMcpCapture.ConfigurationSourceRole.values())
            sources.addObject().put("role",role.name()).set("original_ref",reference(new ControlBuild.FileRef(fixtureRoot().resolve(role.name()+".data").toString(),1,"b".repeat(64))));
        var ctor=cfg.putObject("constructor_keywords").put("route_contact_timeline_speed",3).put("allow_route_contact_high_speed_ab",false)
                .put("allow_stationary_objective_hold_sentinel_canary",true).put("allow_war_daily_watch_v1",true)
                .put("episode_projection",intent.nativeCampaign()?"native_campaign":"one_life");
        // Opaque consumer transport only; sole Root lifecycle codec/Bound qualification is tested by its owner.
        if(intent.nativeCampaign())ctor.putNull("succession_lifecycle_binding");
        else ctor.putObject("succession_lifecycle_binding").put("schema","software-opaque-lifecycle-vector/v1");
        var flags=cfg.putObject("registration_attributes");for(var flag:OriginalMcpCapture.RegistrationAttribute.values())flags.put(flag.wire(),true);
        if(intent.fixture()){
            var binding=cfg.putObject("fixture_policy").put("policy_sha256","c".repeat(64)).put("preparation_sha256","d".repeat(64));
            if(intent==OriginalMcpCapture.SelectedIntent.EXPLICIT_SCENARIO_FIXTURE){
                binding.put("profile_id","faith-and-power-e01-abbasid-867");
                binding.putObject("frontend_target").put("bookmark_key","bm_xar_faith_h01_867").put("character_name_key","bookmark_xar_faith_h01_abbasid")
                        .put("government_key","clan_government").put("start_date_raw",51394920).put("bookmark_group_key","bm_group_867");
            }
            cfg.put("profile_directory",fixtureRoot().resolve("actual-profile").toString());
        }else{cfg.putNull("fixture_policy");if(intent.saved())cfg.put("profile_directory",fixtureRoot().resolve("actual-saved-profile").toString());else cfg.putNull("profile_directory");}
        return cfg;
    }
    private static OriginalMcpCapture.SelectedConfiguration selection(ObjectNode cfg)throws Exception {
        return OriginalMcpCapture.decodeSelectedConfiguration(wire(cfg),"software-fixture-machine",producer());
    }
    private static void rejectsSelection(ObjectNode cfg) {
        assertThrows(IllegalArgumentException.class,()->selection(cfg));
    }
    @Test void selectedV4AllFiveIntentsKeepExactOriginalConstructorFlagsAndToolBranches()throws Exception {
        assertEquals(79,OriginalMcpCapture.RegistrationAttribute.values().length);
        for(var intent:OriginalMcpCapture.SelectedIntent.values()){
            var typed=selection(configuration(intent));assertEquals(intent,typed.intent());assertEquals(9,typed.sources().size());
            assertEquals(3,typed.constructorArguments().routeContactTimelineSpeed());assertFalse(typed.constructorArguments().allowRouteContactHighSpeedAb());
            assertTrue(typed.constructorArguments().stationaryObjectiveHoldCanaryRequested());assertTrue(typed.constructorArguments().warDailyWatchEnabled());
            assertEquals(intent.nativeCampaign()?OriginalMcpCapture.Projection.NATIVE_CAMPAIGN:OriginalMcpCapture.Projection.ONE_LIFE,typed.constructorArguments().projection());
            assertEquals(intent.fixture(),typed.fixture().isPresent());
            if(intent.fixture())assertEquals(intent==OriginalMcpCapture.SelectedIntent.EXPLICIT_SCENARIO_FIXTURE,typed.fixture().orElseThrow().binding().scenarioTarget().isPresent());
            var actual=new java.util.ArrayList<String>();actual.add("ck3_take_snapshot");if(intent.fixture())actual.add(intent.selectedFixtureTool());
            OriginalMcpCapture.verifySelectedTools(typed,actual);
            for(var other:List.of(OriginalMcpCapture.SelectedIntent.EXPLICIT_ROBERT_FIXTURE,OriginalMcpCapture.SelectedIntent.EXPLICIT_SCENARIO_FIXTURE)){
                var wrong=new java.util.ArrayList<>(actual);
                if(intent==other)wrong.remove(other.selectedFixtureTool());else wrong.add(other.selectedFixtureTool());
                assertThrows(IllegalArgumentException.class,()->OriginalMcpCapture.verifySelectedTools(typed,wrong));
            }
            var duplicate=new java.util.ArrayList<>(actual);duplicate.add("ck3_take_snapshot");assertThrows(IllegalArgumentException.class,()->OriginalMcpCapture.verifySelectedTools(typed,duplicate));
        }
    }
    @Test void selectedV4RejectsLegacyMissingNullWrongKindsScalarCoercionAndHiddenOrdinaryFlags()throws Exception {
        var ordinary=OriginalMcpCapture.SelectedIntent.FRESH_ROBERT_1066_ALL_ORDINARY;
        var robert=OriginalMcpCapture.SelectedIntent.EXPLICIT_ROBERT_FIXTURE;
        var scenario=OriginalMcpCapture.SelectedIntent.EXPLICIT_SCENARIO_FIXTURE;
        for(String version:List.of("v1","v2","v3")){
            var old=configuration(ordinary);old.put("schema","xar.original-mcp-current-configuration/"+version);rejectsSelection(old);
        }
        var foreign=configuration(ordinary);foreign.put("machine_id","another-machine");rejectsSelection(foreign);
        var producer=configuration(ordinary);((ObjectNode)producer.get("configuration_producer")).put("sha256","e".repeat(64));rejectsSelection(producer);
        for(var intent:OriginalMcpCapture.SelectedIntent.values()){
            for(String key:List.of("fixture_policy","profile_directory","intent","constructor_keywords","registration_attributes","source_inputs")){
                var missing=configuration(intent);missing.remove(key);rejectsSelection(missing);
            }
            var projection=configuration(intent);((ObjectNode)projection.get("constructor_keywords")).put("episode_projection",intent.nativeCampaign()?"one_life":"native_campaign");rejectsSelection(projection);
            for(String key:List.of("allow_route_contact_high_speed_ab","allow_stationary_objective_hold_sentinel_canary","allow_war_daily_watch_v1")){
                var wrong=configuration(intent);((ObjectNode)wrong.get("constructor_keywords")).put(key,1);rejectsSelection(wrong);
            }
            for(JsonNode value:List.of(object().put("v",true).get("v"),object().put("v",3.0).get("v"),object().put("v","3").get("v"))){
                var wrong=configuration(intent);((ObjectNode)wrong.get("constructor_keywords")).set("route_contact_timeline_speed",value);rejectsSelection(wrong);
            }
            var speed=configuration(intent);((ObjectNode)speed.get("constructor_keywords")).put("route_contact_timeline_speed",4);rejectsSelection(speed);
            ((ObjectNode)speed.get("constructor_keywords")).put("allow_route_contact_high_speed_ab",true);assertEquals(4,selection(speed).constructorArguments().routeContactTimelineSpeed());
            var extra=configuration(intent);((ObjectNode)extra.get("constructor_keywords")).put("state_dir",fixtureRoot().toString());rejectsSelection(extra);
            var role=configuration(intent);((ObjectNode)role.withArray("source_inputs").get(1)).put("role","ROOT_INTENT");rejectsSelection(role);
            for(var flag:OriginalMcpCapture.RegistrationAttribute.values()){
                var disabled=configuration(intent);((ObjectNode)disabled.get("registration_attributes")).put(flag.wire(),false);rejectsSelection(disabled);
            }
        }
        for(String key:List.of("fixture_policy","profile_directory")){
            var absent=configuration(robert);absent.putNull(key);rejectsSelection(absent);
            var inverted=configuration(ordinary);inverted.set(key,configuration(robert).get(key));rejectsSelection(inverted);
        }
        var wrongKind=configuration(robert);wrongKind.set("fixture_policy",configuration(scenario).get("fixture_policy"));rejectsSelection(wrongKind);
        var otherKind=configuration(scenario);otherKind.set("fixture_policy",configuration(robert).get("fixture_policy"));rejectsSelection(otherKind);
        var target=configuration(scenario);((ObjectNode)target.get("fixture_policy").get("frontend_target")).put("start_date_raw",51394920.0);rejectsSelection(target);
        var profile=configuration(scenario);((ObjectNode)profile.get("fixture_policy")).put("profile_id","unapproved-profile");rejectsSelection(profile);
        var relative=configuration(robert);relative.put("profile_directory","relative/profile");rejectsSelection(relative);
        var digest=configuration(robert);((ObjectNode)digest.get("fixture_policy")).put("policy_sha256","C".repeat(64));rejectsSelection(digest);
    }
    @Test void requestV3PinsHistoricalInventoryAndCurrentProducerWithoutCreatingAliasOrExecution()throws Exception {
        var root=fixtureRoot();var inventory=new ControlBuild.FileRef(root.resolve("MEASUREMENT-REQUEST02.json").toString(),OriginalMcpCapture.REQUEST_BYTES,OriginalMcpCapture.REQUEST_SHA);
        var sourceMap=new ControlBuild.FileRef(root.resolve("CONFIG-SOURCE75.json").toString(),1314,"f".repeat(64));
        var originalProducer=new ControlBuild.FileRef(root.resolve("run_ck3_12002_mcp_live.py").toString(),322681,"f25af27d0221260a95b45fc5dcf417d25d733c8dbbdba7be866146643b75f1ee");
        var binding=new OriginalMcpCapture.RequestBinding("software-fixture-machine",inventory,producer(),sourceMap,originalProducer);
        byte[] raw=OriginalMcpCapture.encodeRequest(binding);assertEquals(binding,OriginalMcpCapture.decodeRequest(raw));
        ObjectNode encoded=(ObjectNode)JSON.readTree(raw);
        var old=encoded.deepCopy();old.put("schema","xar.original-mcp-root-memory-measurement-request/v2");assertThrows(IllegalArgumentException.class,()->OriginalMcpCapture.decodeRequest(wire(old)));
        for(String field:List.of("inventory_request_ref","selected_configuration_producer_ref","selected_configuration_source_map_ref","original_fixture_producer_ref")){
            var absent=encoded.deepCopy();absent.remove(field);assertThrows(IllegalArgumentException.class,()->OriginalMcpCapture.decodeRequest(wire(absent)));
            var wrong=encoded.deepCopy();((ObjectNode)wrong.get(field)).put("bytes",true);assertThrows(IllegalArgumentException.class,()->OriginalMcpCapture.decodeRequest(wire(wrong)));
        }
        var historical=encoded.deepCopy();((ObjectNode)historical.get("inventory_request_ref")).put("sha256","a".repeat(64));assertThrows(IllegalArgumentException.class,()->OriginalMcpCapture.decodeRequest(wire(historical)));
        var source=encoded.deepCopy();((ObjectNode)source.get("original_fixture_producer_ref")).put("bytes",322680);assertThrows(IllegalArgumentException.class,()->OriginalMcpCapture.decodeRequest(wire(source)));
        assertThrows(IllegalArgumentException.class,()->OriginalMcpCapture.originalCaptureProgram("{}".getBytes(StandardCharsets.UTF_8)));
    }


    @Test void selectedV4UsesExplicitNullOnlyForNativeCampaignAndNeverInfersOrdinaryBinding()throws Exception {
        for(var intent:OriginalMcpCapture.SelectedIntent.values()){
            var cfg=configuration(intent);var typed=selection(cfg);var args=typed.constructorArguments();
            assertEquals(intent.nativeCampaign(),args.lifecycle().canonicalJson().equals("null"));
            var missing=cfg.deepCopy();((ObjectNode)missing.get("constructor_keywords")).remove("succession_lifecycle_binding");rejectsSelection(missing);
            var crossed=cfg.deepCopy();var ctor=(ObjectNode)crossed.get("constructor_keywords");
            if(intent.nativeCampaign())ctor.putObject("succession_lifecycle_binding").put("schema","software-opaque-lifecycle-vector/v1");
            else ctor.putNull("succession_lifecycle_binding");
            rejectsSelection(crossed);
            for(JsonNode wrong:List.of(object().put("v",true).get("v"),object().put("v",1).get("v"),object().put("v","null").get("v"),object().putArray("v"))){
                var scalar=cfg.deepCopy();((ObjectNode)scalar.get("constructor_keywords")).set("succession_lifecycle_binding",wrong);rejectsSelection(scalar);
            }
        }
        var nullWire=new OriginalMcpCapture.LifecycleArgument("null");
        assertThrows(IllegalArgumentException.class,()->new OriginalMcpCapture.ConstructorArguments(1,false,false,false,OriginalMcpCapture.Projection.ONE_LIFE,nullWire));
        var binding=new OriginalMcpCapture.LifecycleArgument("{\"schema\":\"software-opaque-lifecycle-vector/v1\"}");
        assertThrows(IllegalArgumentException.class,()->new OriginalMcpCapture.ConstructorArguments(1,false,false,false,OriginalMcpCapture.Projection.NATIVE_CAMPAIGN,binding));
    }


    @Test void savedV4KeepsExplicitCurrentProfileAndNoFixtureBindingOrInferredProjection()throws Exception {
        for(var intent:List.of(OriginalMcpCapture.SelectedIntent.SAVED_GAME_ALL_ORDINARY,OriginalMcpCapture.SelectedIntent.SAVED_NATIVE_CAMPAIGN)){
            var cfg=configuration(intent);var typed=selection(cfg);assertTrue(typed.fixture().isEmpty());assertTrue(typed.profileDirectory().isPresent());
            assertEquals(fixtureRoot().resolve("actual-saved-profile"),typed.profileDirectory().orElseThrow());
            assertEquals(intent==OriginalMcpCapture.SelectedIntent.SAVED_NATIVE_CAMPAIGN,typed.constructorArguments().lifecycle().canonicalJson().equals("null"));
            OriginalMcpCapture.verifySelectedTools(typed,List.of("ck3_take_snapshot"));
            var missing=cfg.deepCopy();missing.remove("profile_directory");rejectsSelection(missing);
            var nullProfile=cfg.deepCopy();nullProfile.putNull("profile_directory");rejectsSelection(nullProfile);
            var relative=cfg.deepCopy();relative.put("profile_directory","old-or-guessed-profile");rejectsSelection(relative);
            var boolProfile=cfg.deepCopy();boolProfile.put("profile_directory",true);rejectsSelection(boolProfile);
            var invented=cfg.deepCopy();invented.set("fixture_policy",configuration(OriginalMcpCapture.SelectedIntent.EXPLICIT_ROBERT_FIXTURE).get("fixture_policy"));rejectsSelection(invented);
            var fresh=cfg.deepCopy();fresh.put("intent",OriginalMcpCapture.SelectedIntent.FRESH_ROBERT_1066_ALL_ORDINARY.name());rejectsSelection(fresh);
            var actual=cfg.deepCopy();Path exact=fixtureRoot().resolve("another-explicit-current-profile");actual.put("profile_directory",exact.toString());assertEquals(exact,selection(actual).profileDirectory().orElseThrow());
            // The prior fresh-only DTO constructor cannot guess a Saved profile from a null fixture.
            assertThrows(IllegalArgumentException.class,()->new OriginalMcpCapture.SelectedConfiguration(typed.machineId(),typed.observedAtUtc(),typed.reviewAtUtc(),
                    typed.intent(),typed.producer(),typed.sources(),typed.constructorArguments(),typed.fixture()));
        }
        assertFalse(selection(configuration(OriginalMcpCapture.SelectedIntent.FRESH_ROBERT_1066_ALL_ORDINARY)).profileDirectory().isPresent());
        for(var intent:List.of(OriginalMcpCapture.SelectedIntent.EXPLICIT_ROBERT_FIXTURE,OriginalMcpCapture.SelectedIntent.EXPLICIT_SCENARIO_FIXTURE)){
            var selected=selection(configuration(intent));assertEquals(selected.fixture().orElseThrow().profileDirectory(),selected.profileDirectory().orElseThrow());
        }
    }

    @Test void actualLiteralMetadataLoopKeepsFullInventoryAndComputedOrRegisteringLoopsRemainRejected(@TempDir Path temporary)throws Exception {
        String metadataLoop="""
            for name in ("ck3_query_grant_title_picker_v1", "ck3_prepare_grant_title_picker_v1",
                         "ck3_select_grant_title_picker_v1", "ck3_send_grant_title_picker_v1"):
                _forbid_unknown_tool_arguments_v1(server, name)
            """.indent(4);
        var variants=List.of(
            new InventoryVector("actual-original",null),
            new InventoryVector("computed-iterable","""
                for name in get_tool_names():
                    _forbid_unknown_tool_arguments_v1(server, name)
                """.indent(4)),
            new InventoryVector("variable-iterable","""
                for name in tool_names:
                    _forbid_unknown_tool_arguments_v1(server, name)
                """.indent(4)),
            new InventoryVector("dynamic-register",metadataLoop.replace("_forbid_unknown_tool_arguments_v1(server, name)","server.tool()(ck3_query_grant_title_picker_v1)")),
            new InventoryVector("mixed-side-effect",metadataLoop.replace("_forbid_unknown_tool_arguments_v1(server, name)","_forbid_unknown_tool_arguments_v1(server, name)\n        side_effect()")),
            new InventoryVector("assignment-side-effect",metadataLoop.replace("_forbid_unknown_tool_arguments_v1(server, name)","_forbid_unknown_tool_arguments_v1(server, name)\n        unexpected = True")),
            new InventoryVector("nested-control",metadataLoop.replace("_forbid_unknown_tool_arguments_v1(server, name)","if True:\n            _forbid_unknown_tool_arguments_v1(server, name)")),
            new InventoryVector("nonempty-else",metadataLoop+"    else:\n        _forbid_unknown_tool_arguments_v1(server, name)\n")
        );
        byte[] request=fixtureBytes("original-request02.json");
        String parser=OriginalMcpCapture.originalCaptureProgram(request);
        for(var vector:variants){
            Path work=temporary.resolve(vector.name());Files.createDirectories(work);
            Path source=work.resolve("source");
            for(String filename:List.of("mcp_server.py","rite_creation_action_mcp_v1.py","army_observer_research_sampling_control.py","private_auto_scalar_ab_control_v1.py")){
                Path target=source.resolve("xar_autoplayer/bridge").resolve(filename);Files.createDirectories(target.getParent());
                byte[] original=fixtureBytes("original-sources/"+filename+".txt");
                JsonNode expected=JSON.readTree(request).get("registration_source_refs");
                var matching=new java.util.ArrayList<JsonNode>();for(JsonNode ref:expected)if(ref.get("path").textValue().endsWith("/"+filename))matching.add(ref);
                assertEquals(1,matching.size(),"one original fixture source role required");
                assertEquals(matching.getFirst().get("bytes").longValue(),original.length);
                assertEquals(matching.getFirst().get("sha256").textValue(),OriginalMcpCapture.sha256(original));
                String text=new String(original,StandardCharsets.UTF_8);
                if(filename.equals("mcp_server.py")&&vector.replacement()!=null){
                    int at=text.indexOf(metadataLoop);assertTrue(at>=0&&at==text.lastIndexOf(metadataLoop),"actual original metadata loop must have one exact source anchor");
                    text=text.substring(0,at)+vector.replacement()+text.substring(at+metadataLoop.length());
                }
                Files.writeString(target,text);
            }
            Path requestFile=work.resolve("request.json");Files.write(requestFile,request);
            Path baseline=work.resolve("historical-catalog.json");Files.write(baseline,fixtureBytes("historical-catalog320.json"));
            Path script=work.resolve("inventory-vector.py");Files.writeString(script,parser+INVENTORY_VECTOR);
            Path stdout=work.resolve("stdout.json"),stderr=work.resolve("stderr.log");
            var command=new ProcessBuilder(System.getProperty("xar.rootContext.pythonExecutable","python"),"-B",script.toString(),requestFile.toString(),source.toString(),baseline.toString());
            command.environment().put("PYTHONDONTWRITEBYTECODE","1");command.redirectOutput(stdout.toFile());command.redirectError(stderr.toFile());
            var process=command.start();
            if(!process.waitFor(10,TimeUnit.SECONDS)){process.destroyForcibly();process.waitFor();fail("finite original AST vector timed out: "+vector.name());}
            JsonNode actual=JSON.readTree(Files.readAllBytes(stdout));assertNotNull(actual,vector.name()+": "+Files.readString(stderr));
            if(vector.replacement()==null){
                assertEquals(0,process.exitValue(),actual.toString());assertEquals("PARSED_ORIGINAL_INVENTORY_ONLY",actual.get("status").textValue());
                assertEquals(323,actual.get("declarations").intValue());assertEquals(194,actual.get("unconditional").intValue());
                assertEquals(129,actual.get("conditional").intValue());assertEquals(2,actual.get("resources").intValue());
                assertEquals(1,actual.get("metadata_helper_edges").intValue(),"the real metadata call remains in the existing delegated source graph");
            }else{
                assertEquals(2,process.exitValue(),vector.name()+": "+actual);assertEquals("REJECTED_REGISTRATION_LOOP",actual.get("status").textValue());
                assertEquals("new registration loop/context/match requires source research",actual.get("reason").textValue());
            }
        }
    }
    private record InventoryVector(String name,String replacement){ }
    private static byte[] fixtureBytes(String name)throws Exception {
        try(var input=OriginalMcpCaptureTest.class.getResourceAsStream("/mcp-inventory/"+name)){
            assertNotNull(input,"real frozen original inventory fixture missing: "+name);return input.readAllBytes();
        }
    }
    private static final String INVENTORY_VECTOR="""

        request=object_value(parse(pathlib.Path(sys.argv[1]).read_bytes()))
        root=pathlib.Path(sys.argv[2])
        request['python_source_root']=str(root)
        refs=[]
        for module in request['reviewed_registration_modules']:
            path=root.joinpath(*module.split('.')).with_suffix('.py')
            raw=path.read_bytes()
            refs.append({'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
        request['registration_source_refs']=refs
        baseline_path=pathlib.Path(sys.argv[3])
        baseline=object_value(parse(baseline_path.read_bytes()))
        by_name={pathlib.Path(ref['path']).name:ref for ref in refs}
        baseline['sources']=[by_name[pathlib.Path(old['path']).name] for old in baseline['sources']]
        baseline_raw=encoded(baseline)
        baseline_path.write_bytes(baseline_raw)
        request['historical_catalog_ref']={'path':str(baseline_path),'bytes':len(baseline_raw),'sha256':hashlib.sha256(baseline_raw).hexdigest()}
        try:
            actual=original_inventory(request)
            catalog=object_value(parse(actual.catalog))
            proof=object_value(parse(actual.proof))
            metadata_edges=[edge for edge in proof['delegation_edges'] if edge['caller_scope']=='register_stock_grant_title_picker_tools' and edge['callee_scope']=='_forbid_unknown_tool_arguments_v1']
            print(encoded({'status':'PARSED_ORIGINAL_INVENTORY_ONLY','declarations':len(catalog['declarations']),'unconditional':proof['unconditional'],'conditional':proof['conditional'],'resources':len(proof['resources']),'metadata_helper_edges':len(metadata_edges)}).decode('utf-8'))
        except ValueError as failure:
            print(encoded({'status':'REJECTED_REGISTRATION_LOOP','reason':str(failure)}).decode('utf-8'))
            sys.exit(2)
        """;
    @Test void asyncioCaptureAuditClosesTheEmittedBridgeAndKeepsOriginalDenials(@TempDir Path temporary)throws Exception {
        String program=OriginalMcpCapture.originalCaptureProgram(fixtureBytes("original-request02.json"));
        for(String mode:List.of("normal","before_sdk_import","callback_failure")){
            Path work=temporary.resolve(mode);Files.createDirectories(work);
            Path script=work.resolve("actual-async-boundary.py");Files.writeString(script,program+ASYNC_AUDIT_VECTOR);
            var actual=runPython(script,List.of(mode,work.toString()),work);
            assertEquals(0,actual.exitCode(),actual.stderr());var result=JSON.readTree(actual.stdout());
            assertEquals("INERT_ORIGINAL_ASYNC_BOUNDARY_ONLY",result.get("scope").textValue());
            assertTrue(result.get("loop_closed").booleanValue());assertFalse(result.get("sdk_loaded").booleanValue());
            assertEquals(mode,result.get("mode").textValue());
            if(mode.equals("normal")){
                assertEquals(List.of("connect","bind","subprocess","write"),JSON.convertValue(result.get("denied"),new com.fasterxml.jackson.core.type.TypeReference<List<String>>(){}));
                assertEquals("INERT_TOOLS",result.get("result").get(0).get(0).textValue());
                assertEquals("INERT_RESOURCES",result.get("result").get(1).get(0).textValue());
            }else assertTrue(result.get("failure_unwound").booleanValue());
        }
    }
    @Test void asyncioCaptureRunnerConsumesTheSameCompleteEditList(@TempDir Path temporary)throws Exception {
        byte[] request=fixtureBytes("original-request02.json");
        var wireMethod=OriginalMcpCapture.class.getDeclaredMethod("boundaryEditWire",byte[].class);wireMethod.setAccessible(true);
        String edits=assertInstanceOf(String.class,wireMethod.invoke(null,new Object[]{request}));
        var runnerField=OriginalMcpCapture.class.getDeclaredField("RUNNER");runnerField.setAccessible(true);
        String runner=assertInstanceOf(String.class,runnerField.get(null));
        Path original=temporary.resolve("original-request.json");Files.write(original,request);
        var envelope=object().put("schema",OriginalMcpCapture.CURRENT_REQUEST_SCHEMA);
        envelope.putObject("inventory_request_ref").put("path",original.toString());
        envelope.putObject("selected_configuration_producer_ref").put("softwareVectorOnly",true);
        Path envelopeFile=temporary.resolve("runner-envelope.json");Files.write(envelopeFile,wire(envelope));
        Path script=temporary.resolve("actual-process-runner.py");Files.writeString(script,runner);
        var actual=runPython(script,List.of(envelopeFile.toString(),temporary.resolve("unused-config.json").toString(),"1","a".repeat(64),"SOFTWARE_UNKNOWN_PHASE",edits),temporary);
        assertEquals(1,actual.exitCode());assertTrue(actual.stderr().contains("ValueError: unknown exact original capture phase"),actual.stderr());
        // Reaching the real phase dispatch proves the actual emitted Runner accepted and applied the shared edit wire.
    }
    private record PythonResult(int exitCode,String stdout,String stderr){ }
    private static PythonResult runPython(Path script,List<String> arguments,Path work)throws Exception {
        var argv=new java.util.ArrayList<String>();argv.add(System.getProperty("xar.rootContext.pythonExecutable","python"));argv.add("-B");argv.add(script.toString());argv.addAll(arguments);
        Path stdout=work.resolve("python.stdout"),stderr=work.resolve("python.stderr");
        var command=new ProcessBuilder(argv);command.environment().put("PYTHONDONTWRITEBYTECODE","1");command.environment().put("PYTHONIOENCODING","utf-8");
        command.redirectOutput(stdout.toFile());command.redirectError(stderr.toFile());var process=command.start();
        if(!process.waitFor(10,TimeUnit.SECONDS)){process.destroyForcibly();process.waitFor();fail("finite original async boundary vector timed out");}
        return new PythonResult(process.exitValue(),Files.readString(stdout),Files.readString(stderr));
    }
    private static final String ASYNC_AUDIT_VECTOR="""

        import socket,subprocess
        mode=sys.argv[1]
        work=pathlib.Path(sys.argv[2])
        loops=[]
        denied=[]
        token=object()
        configuration=object()
        def denied_call(label,operation,prefix):
            try:
                operation()
            except RuntimeError as failure:
                if not str(failure).startswith(prefix): raise
                denied.append(label)
            else:
                raise AssertionError('original audit allowed '+label)
        def connect():
            with socket.socket() as client:
                client.connect(('127.0.0.1',9))
        def bind():
            with socket.socket() as listener:
                listener.bind(('127.0.0.1',0))
        class InertServer:
            async def list_tools(self):
                if mode=='callback_failure': raise RuntimeError('INERT_CALLBACK_FAILURE')
                denied_call('connect',connect,'capture denied side effect: socket.connect')
                denied_call('bind',bind,'capture denied side effect: socket.bind')
                denied_call('subprocess',lambda:subprocess.Popen([sys.executable,'-c','raise SystemExit(0)']),'capture denied side effect: subprocess.Popen')
                denied_call('write',lambda:(work/'never-written').open('wb'),'capture denies filesystem write:')
                return ['INERT_TOOLS']
            async def list_resources(self):
                return ['INERT_RESOURCES']
        def controlled_original(request,configuration_ref,capture_runner):
            if request is not token or configuration_ref is not configuration: raise AssertionError('capture bridge changed actual arguments')
            loops.append(capture_runner.get_loop())
            sys.addaudithook(no_mutation)
            if mode=='before_sdk_import': raise ImportError('INERT_IMPORT_FAILURE')
            return capture_runner.run(actual_lists(InertServer()))
        # Only the expensive source/SDK body is the controlled dependency. The actual Java-emitted capture bridge,
        # the unchanged original audit hook, original actual_lists helper and installed Runner all execute.
        _capture_original_with_loop=controlled_original
        failure_unwound=False
        try:
            result=capture(token,configuration)
        except (ImportError,RuntimeError) as failure:
            expected='INERT_IMPORT_FAILURE' if mode=='before_sdk_import' else 'INERT_CALLBACK_FAILURE'
            if str(failure)!=expected: raise
            failure_unwound=True
            result=None
        if (mode=='normal')==failure_unwound: raise AssertionError('capture bridge outcome differs')
        if len(loops)!=1 or not loops[0].is_closed(): raise AssertionError('actual emitted bridge leaked its initialized loop')
        if (work/'never-written').exists(): raise AssertionError('original audit allowed write')
        print(encoded({'scope':'INERT_ORIGINAL_ASYNC_BOUNDARY_ONLY','mode':mode,'loop_closed':loops[0].is_closed(),'sdk_loaded':False,'denied':denied,'failure_unwound':failure_unwound,'result':result}).decode('utf-8'))
        """;

    @Test void currentFiniteExecutionReleaseDoesNotRequireHistoricalBuildQualification(@TempDir Path temporary)throws Exception {
        assertAll("historical build metadata does not qualify a current bounded execution",
                ()->assertDoesNotThrow(()->invokeExecutionAdmission(executionReleaseFixture(temporary.resolve("obsolete-build"),false,row->{}))),
                ()->assertDoesNotThrow(()->invokeExecutionAdmission(executionReleaseFixture(temporary.resolve("missing-history"),true,row->{}))));
    }
    @Test void currentExecutionReleaseStillEnforcesItsActualFiniteScope(@TempDir Path temporary)throws Exception {
        for(String defect:List.of("machine","request","directory","memory","timeout-type","expired","future","producer-ref-type","build-ref-type")) {
            var plan=executionReleaseFixture(temporary.resolve(defect),true,row->{
                switch(defect) {
                    case "machine"->row.put("machine_id","foreign-software-machine");
                    case "request"->row.set("original_request_ref",row.get("selected_configuration_ref"));
                    case "directory"->row.put("session_parent",temporary.resolve("another-session").toString());
                    case "memory"->row.put("memory_limit_bytes",(64L<<20)+1);
                    case "timeout-type"->row.put("timeout_seconds",5.0);
                    case "expired"->row.put("review_at_utc",java.time.Instant.now().minusSeconds(1).toString());
                    case "future"->row.put("observed_at_utc",java.time.Instant.now().plusSeconds(300).toString());
                    case "producer-ref-type"->row.put("producer_source_ref",true);
                    case "build-ref-type"->row.putNull("whole_build_receipt_ref");
                    default->throw new AssertionError(defect);
                }
            });
            assertThrows(IllegalArgumentException.class,()->invokeExecutionAdmission(plan),defect);
        }
    }
    private static OriginalMcpCapture.Plan executionReleaseFixture(Path root,boolean missingHistory,
            java.util.function.Consumer<ObjectNode> change)throws Exception {
        Files.createDirectory(root);String first=java.time.Instant.now().minusSeconds(30).toString();
        String last=java.time.Instant.now().plusSeconds(3600).toString();
        var request=new ControlBuild.FileRef(root.resolve("request.json").toString(),1,"a".repeat(64));
        var selected=new ControlBuild.FileRef(root.resolve("selected.json").toString(),1,"b".repeat(64));
        var python=new ControlBuild.FileRef(root.resolve("python.exe").toString(),1,"c".repeat(64));
        var identity=new SharedSourceFiles.DirectoryIdentity("1","2","3");
        Path allocated=root.resolve("allocation-data.json");Files.writeString(allocated,"{}");
        var allocation=ControlBuild.FileRef.measure(allocated);
        ControlBuild.FileRef source,build;
        if(missingHistory) {
            source=new ControlBuild.FileRef(root.resolve("OriginalMcpCapture.java").toString(),1,"d".repeat(64));
            build=new ControlBuild.FileRef(root.resolve("whole-build.json").toString(),1,"e".repeat(64));
        } else {
            Path sourcePath=root.resolve("OriginalMcpCapture.java"),buildPath=root.resolve("whole-build.json");
            Files.writeString(sourcePath,"// historical source metadata only");Files.writeString(buildPath,"{}");
            source=ControlBuild.FileRef.measure(sourcePath);build=ControlBuild.FileRef.measure(buildPath);
        }
        var release=object().put("schema","xar.original-mcp-capture-execution-release/v1")
                .put("status","RELEASED_ROOT_ORIGINAL_MCP_CAPTURE_NO_GAME").put("machine_id","software-fixture-machine")
                .put("issuer","/root/budget_fast_lane").put("owner","/root").put("observed_at_utc",first).put("review_at_utc",last)
                .put("session_parent",root.toString()).put("timeout_seconds",5).put("memory_limit_bytes",64L<<20)
                .put("maximum_session_native_bytes",2L<<20).put("maximum_stderr_bytes",4096);
        release.set("original_request_ref",reference(request));release.set("selected_configuration_ref",reference(selected));
        release.set("python_executable_ref",reference(python));
        release.set("session_parent_identity",object().put("volumeSerialDecimal",identity.volumeSerialDecimal())
                .put("fileIdDecimal",identity.fileIdDecimal()).put("creationFiletimeDecimal",identity.creationFiletimeDecimal()));
        release.set("producer_source_ref",reference(source));release.set("whole_build_receipt_ref",reference(build));
        for(String field:List.of("own_archive_actual_ref","policy_ref","standing_ref"))release.set(field,reference(allocation));
        change.accept(release);Path releasePath=root.resolve("release.json");Files.write(releasePath,wire(release));
        return new OriginalMcpCapture.Plan(OriginalMcpCapture.PLAN_SCHEMA,"software-fixture-machine",first,last,
                request,selected,python,root.toString(),root.toString(),identity,ControlBuild.FileRef.measure(releasePath),
                5,64L<<20,2L<<20,4096);
    }
    private static void invokeExecutionAdmission(OriginalMcpCapture.Plan plan)throws Exception {
        var method=OriginalMcpCapture.class.getDeclaredMethod("admitExecution",OriginalMcpCapture.Plan.class,List.class);
        method.setAccessible(true);
        try {method.invoke(null,plan,new java.util.ArrayList<SharedSourceFiles.Witness>());}
        catch(java.lang.reflect.InvocationTargetException wrapped) {
            if(wrapped.getCause() instanceof Exception failure)throw failure;
            if(wrapped.getCause() instanceof Error failure)throw failure;
            throw new IllegalStateException(wrapped.getCause());
        }
    }
}

