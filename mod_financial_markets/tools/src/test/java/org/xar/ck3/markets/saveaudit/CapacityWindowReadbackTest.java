package org.xar.ck3.markets.saveaudit;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.UnaryOperator;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.markets.acceptance.FollowupContracts;
import org.xar.ck3.markets.acceptance.FollowupObservationScripts;
import org.xar.ck3.markets.acceptance.FixtureEmitter;
import org.xar.ck3.save.Clausewitz;
import org.xar.ck3.save.FilePins;
import org.xar.ck3.save.ProducerSources;
import org.xar.ck3.save.SaveContracts.Pin;
import org.xar.ck3.save.SaveJson;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** Production-consumer tests using explicitly source-derived software ASTs, never actual395 Game evidence. */
final class CapacityWindowReadbackTest {
    private static final String ACTOR="31254", HOLDER="34232", OBSERVER="1000", EXCHANGE="10", ACCOUNT="11", COIN="12";
    private static final long NATIVE=53145696, FINANCIAL=56, SCRIPT=389404;
    private static final FollowupContracts.Request OBSERVATION=new FollowupContracts.Request(2,FollowupContracts.Profile.AI_CAPACITY,1,
            new FollowupContracts.ActorBinding(FollowupContracts.ActorMode.CURRENT_PLAYER,null),
            new FollowupContracts.Targets("2","55",null,null,null,null),null,FollowupContracts.ScaleTier.SMOKE);
    private static final CapacityWindowReadback.Binding BINDING=new CapacityWindowReadback.Binding(OBSERVATION,ACTOR,OBSERVER,EXCHANGE);
    private static final List<CapacityWindowReadback.Snapshot> SOURCE_DERIVED_WINDOW=sourceDerivedWindow();

    @Test void sourceDerived395RecordsPassOnlyTheExactThirtyWarmAnd365MeasuredIntegrityPath() throws Exception {
        CapacityWindowReadback.Chain result=CapacityWindowReadback.interpret(BINDING,window());
        assertEquals(395,result.days().size()); assertEquals(365,result.days().stream().filter(CapacityWindowReadback.Day::measured).count());
        assertFalse(result.days().get(29).measured()); assertTrue(result.days().get(30).measured());
        assertEquals(FINANCIAL+395,result.days().getLast().financialDay()); assertEquals(SCRIPT+395,result.days().getLast().scriptDate());
    }

    @Test void observedZeroIsRetainedButMissingRequiredSourceFailsWithoutSubstitution() throws Exception {
        List<CapacityWindowReadback.Snapshot> zero=mutateDay(window(),395,200,"xfma_active_coin_count",number(0));
        assertEquals(BigInteger.ZERO,CapacityWindowReadback.interpret(BINDING,zero).days().get(199).sources().get("active_coin_count").value());
        List<CapacityWindowReadback.Snapshot> missing=removeDayVariable(window(),395,200,"xfma_active_coin_count");
        assertThrows(IllegalArgumentException.class,()->CapacityWindowReadback.interpret(BINDING,missing));
    }

    @Test void unavailableOptionalValueRemainsAbsentAndCannotAcquireAnInventedZero() throws Exception {
        List<CapacityWindowReadback.Snapshot> absent=mutateDay(window(),395,200,"xfma_fee_cents_available",number(0));
        absent=removeDayVariable(absent,395,200,"xfma_fee_cents");
        CapacityWindowReadback.Observation value=CapacityWindowReadback.interpret(BINDING,absent).days().get(199).sources().get("fee_cents");
        assertFalse(value.available()); assertTrue(value.values().isEmpty());
        assertEquals(value,SaveJson.read(SaveJson.write(value),CapacityWindowReadback.Observation.class));
        List<CapacityWindowReadback.Snapshot> invented=mutateDay(absent,395,200,"xfma_fee_cents",number(0));
        assertThrows(IllegalArgumentException.class,()->CapacityWindowReadback.interpret(BINDING,invented));
    }

    @Test void financialScriptAndNativeCalendarGapsAreIndependentlyRejected() throws Exception {
        for(String field:List.of("xfma_financial_day","xfma_source_script_date","xfma_previous_record_financial_day","xfma_previous_source_script_date")) {
            List<CapacityWindowReadback.Snapshot> broken=mutateDay(window(),395,200,field,number(1));
            assertThrows(IllegalArgumentException.class,()->CapacityWindowReadback.interpret(BINDING,broken),field);
        }
        List<CapacityWindowReadback.Snapshot> gap=window(); CapacityWindowReadback.Snapshot last=gap.getLast();
        gap.set(2,new CapacityWindowReadback.Snapshot(395,last.nativeDateRaw()+24,last.actor(),last.globals(),last.stories()));
        assertThrows(IllegalArgumentException.class,()->CapacityWindowReadback.interpret(BINDING,gap));
    }

    @Test void coherentlyShiftedFinancialAndNativeOriginsStillRequireTheirRealBoundedDateDomains() throws Exception {
        assertEquals(1,CapacityWindowReadback.interpret(BINDING,shiftFinancialOrigin(0)).days().getFirst().financialDay());
        assertEquals(1_000_000_000L,CapacityWindowReadback.interpret(BINDING,shiftFinancialOrigin(1_000_000_000L-395)).days().getLast().financialDay());
        for(long invalid:List.of(-1L,1_000_000_000L-394)) {
            List<CapacityWindowReadback.Snapshot> coherent=shiftFinancialOrigin(invalid);
            assertThrows(IllegalArgumentException.class,()->CapacityWindowReadback.interpret(BINDING,coherent));
        }
        long lastNativeOrigin=Integer.MAX_VALUE-395L*24;
        assertEquals(lastNativeOrigin,CapacityWindowReadback.interpret(BINDING,shiftNativeOrigin(lastNativeOrigin)).nativeOrigin());
        CapacityWindowReadback.verifyNativeIntervals(nativeReport(395,lastNativeOrigin),lastNativeOrigin,ACTOR);
        for(long invalid:List.of(-1L,0L,lastNativeOrigin+1)) {
            List<CapacityWindowReadback.Snapshot> coherent=shiftNativeOrigin(invalid);
            assertThrows(IllegalArgumentException.class,()->CapacityWindowReadback.interpret(BINDING,coherent));
            assertThrows(IllegalArgumentException.class,()->CapacityWindowReadback.verifyNativeIntervals(nativeReport(395,invalid),invalid,ACTOR));
        }
    }

    @Test void originalD30PrefixRejectsChangedUnknownAstEvenWhenAllKnownCountersStillAgree() throws Exception {
        List<CapacityWindowReadback.Snapshot> rows=window(); CapacityWindowReadback.Snapshot last=rows.getLast();
        Map<String,CapacityWindowReadback.Story> stories=new LinkedHashMap<>(last.stories());
        CapacityWindowReadback.Story prior=stories.get(dayId(1));
        List<Clausewitz.Entry> entries=new ArrayList<>(prior.ast().entries()); entries.add(entry("unrecognized_preserved_field",new Clausewitz.Atom("changed")));
        stories.put(prior.id(),story(prior.id(),new Clausewitz.Block(entries)));
        rows.set(2,new CapacityWindowReadback.Snapshot(395,last.nativeDateRaw(),last.actor(),last.globals(),stories));
        assertNotEquals(prior.witness(),stories.get(prior.id()).witness());
        assertThrows(IllegalArgumentException.class,()->CapacityWindowReadback.interpret(BINDING,rows));
    }

    @Test void changedActorEpochObserverOriginOrWatchedTargetCannotBorrowAnotherWindow() throws Exception {
        for(String field:List.of("xfma_start_day","xfma_start_date","xfma_capacity_protocol","xfma_ready")) {
            List<CapacityWindowReadback.Snapshot> broken=mutateObserver(window(),2,field,number(2));
            assertThrows(IllegalArgumentException.class,()->CapacityWindowReadback.interpret(BINDING,broken),field);
        }
        for(String field:List.of("xfma_account","xfma_coin","xfma_holder_before")) {
            List<CapacityWindowReadback.Snapshot> broken=mutateObserver(window(),2,field,reference(field.equals("xfma_holder_before")?"char":"story","99"));
            assertThrows(IllegalArgumentException.class,()->CapacityWindowReadback.interpret(BINDING,broken),field);
        }
        var wrongEpoch=new FollowupContracts.Request(2,FollowupContracts.Profile.AI_CAPACITY,2,OBSERVATION.actor(),OBSERVATION.targets(),null,OBSERVATION.scaleTier());
        assertThrows(IllegalArgumentException.class,()->CapacityWindowReadback.interpret(new CapacityWindowReadback.Binding(wrongEpoch,ACTOR,OBSERVER,EXCHANGE),window()));
    }

    @Test void incompleteDenominatorsAllocationFailureWrongTypesAndUnrelatedBusinessStoriesFail() throws Exception {
        for(String field:List.of("xfma_capacity_day_records","xfma_capacity_warmup_records","xfma_capacity_measured_records","xfma_daily_samples","xfma_measured_samples")) {
            List<CapacityWindowReadback.Snapshot> broken=mutateObserver(window(),2,field,number(14));
            assertThrows(IllegalArgumentException.class,()->CapacityWindowReadback.interpret(BINDING,broken));
        }
        assertThrows(IllegalArgumentException.class,()->CapacityWindowReadback.interpret(BINDING,mutateObserver(window(),2,"xfma_capacity_record_allocation_failed",number(1))));
        assertThrows(IllegalArgumentException.class,()->CapacityWindowReadback.interpret(BINDING,mutateDay(window(),395,200,"xfma_record_id",reference("story","200"))));
        List<CapacityWindowReadback.Snapshot> rows=window(); CapacityWindowReadback.Snapshot last=rows.getLast();
        Map<String,CapacityWindowReadback.Story> extra=new LinkedHashMap<>(last.stories()); extra.put("999",story("999",body("story_cycle = xfm_debt_claim owner = "+ACTOR)));
        rows.set(2,new CapacityWindowReadback.Snapshot(395,last.nativeDateRaw(),last.actor(),last.globals(),extra));
        assertThrows(IllegalArgumentException.class,()->CapacityWindowReadback.interpret(BINDING,rows));
    }

    @Test void sourceAvailabilityWorkConsistencyFractionsAndSignedEncodingRemainStrict() throws Exception {
        for(String field:List.of("xfma_registered_coin_count_available","xfma_required_sources_complete","xfma_work_without_decision_available"))
            assertThrows(IllegalArgumentException.class,()->CapacityWindowReadback.interpret(BINDING,mutateDay(window(),395,200,field,number(0))));
        assertThrows(IllegalArgumentException.class,()->CapacityWindowReadback.interpret(BINDING,mutateDay(window(),395,200,"xfma_ai_decisions_today",number(100))));
        assertThrows(IllegalArgumentException.class,()->CapacityWindowReadback.interpret(BINDING,mutateDay(window(),395,200,"xfma_record_id",body("type = value identity = 20000001"))));
        assertThrows(IllegalArgumentException.class,()->CapacityWindowReadback.interpret(BINDING,mutateDay(window(),395,200,"xfma_active_coin_count",number(-1))));
    }

    @Test void actualProductionEmitterStillDefinesExactlyTheConsumedSourceAndRequiredAvailabilityCatalogs() {
        String effects=new String(FollowupObservationScripts.render(OBSERVATION).get("common/scripted_effects/xfma_ai_capacity_e1_observe.txt"),StandardCharsets.UTF_8);
        Clausewitz.Block daily=Clausewitz.parse(effects).block("xfma_ai_capacity_e1_capacity_day_effect");
        Set<String> observed=new HashSet<>(); collectAvailable(daily,observed);
        Set<String> expected=new HashSet<>(CapacityWindowReadback.FIELDS);expected.add("work_without_decision"); assertEquals(expected,observed);
        Set<String> required=new HashSet<>(); collectRequired(daily,required); assertEquals(CapacityWindowReadback.REQUIRED,required);
        assertTrue(effects.contains("var:xfma_window_day > 30")); assertTrue(effects.contains("var:xfma_capacity_day_records < 395"));
    }

    @Test void sourceDerivedNativeHostRowsRequireAll395ActualHourIntervalsAndNeverAccept14Or120Days() throws Exception {
        ObjectNode report=nativeReport(395); CapacityWindowReadback.verifyNativeIntervals(report,NATIVE,ACTOR);
        for(int days:List.of(14,120,394)) assertThrows(IllegalArgumentException.class,()->CapacityWindowReadback.verifyNativeIntervals(nativeReport(days),NATIVE,ACTOR));
        ObjectNode row=(ObjectNode)report.withArray("steps").get(200); ((ObjectNode)row.path("result").path("after")).put("date_raw",NATIVE+24L*202);
        assertThrows(IllegalArgumentException.class,()->CapacityWindowReadback.verifyNativeIntervals(report,NATIVE,ACTOR));
    }

    @Test void realStrictJsonBoundaryRejectsBoolOrdinalAndUnknownRequestFields() throws Exception {
        assertThrows(IOException.class,()->SaveJson.read("{\"offset\":true,\"archiveReceipt\":null,\"rawReadbacks\":[]}".getBytes(StandardCharsets.UTF_8),CapacityWindowReadback.CheckpointInput.class));
        assertThrows(IllegalArgumentException.class,()->new CapacityWindowReadback.CheckpointInput(120,pin("archive.json"),List.of(pin("raw.json"))));
        assertThrows(IOException.class,()->SaveJson.read("{\"schemaVersion\":1,\"unknownWindow\":395}".getBytes(StandardCharsets.UTF_8),CapacityWindowReadback.Request.class));
    }

    @Test void actualFixtureRequestParserRetainsItsExplicitNullableTargetContract(@TempDir Path temporary) throws Exception {
        Path file=temporary.resolve("source-derived-observer-request.json");Files.write(file,SaveJson.write(OBSERVATION));
        assertEquals(OBSERVATION,FixtureEmitter.readInput(file));
        ObjectNode wrong=(ObjectNode)SaveJson.read(SaveJson.write(OBSERVATION),JsonNode.class);wrong.put("observationEpoch",true);
        Files.write(file,SaveJson.write(wrong));assertThrows(IOException.class,()->FixtureEmitter.readInput(file));
    }

    @Test void existingRawTokenEnvelopeFlowsThroughTheRealBoundedMetadataExtractorWithoutOpeningASave(@TempDir Path temporary) throws Exception {
        // Only one source-derived D0 envelope, not a fabricated actual395 input or original execution.
        Scope scope=scope();String pipe="source-derived-inert-pipe";
        ObjectNode frozen=scope.frozen().deepCopy();frozen.withArray("argv").add("--bridge-pipe").add(pipe);
        Path state=temporary.resolve("state");frozen.put("state_dir",state.toString());Pin frozenPin=write(temporary.resolve("frozen.json"),frozen);
        CapacityWindowReadback.Request base=scope.request();
        var request=new CapacityWindowReadback.Request(base.schemaVersion(),base.machineId(),base.runId(),base.repository(),ACTOR,OBSERVER,EXCHANGE,
                base.currentContext(),frozenPin,base.preparedCase(),base.fixtureManifest(),base.observerRequest(),base.originalD0Review(),base.originalHostReport(),base.exactReaderSource(),base.exactReaderCompilation(),base.checkpoints());
        Pin noSave=new Pin(temporary.resolve("archive/xar_checkpoint.ck3").toString(),4,"0".repeat(64));
        ObjectNode result=object();result.put("accepted",true);result.put("step","save-checkpoint");result.putObject("materialization").put("available",true);
        ObjectNode checkpoint=result.putObject("checkpoint");checkpoint.put("status","saved");checkpoint.put("date_raw",NATIVE);checkpoint.put("size",4);checkpoint.put("sha256",noSave.sha256());
        String source=state.resolve("profile/save games/xar_checkpoint.ck3").toString();checkpoint.put("path",source);
        ObjectNode host=object();host.put("pipe",pipe);host.putArray("steps").addObject().set("result",result);
        Pin hostPin=write(temporary.resolve("source-derived-original-report.json"),host);
        ObjectNode archive=object();archive.put("schema","ck3-financial-checkpoint-archive-v1");archive.put("machine_id",base.machineId());archive.put("date_raw",NATIVE);
        archive.put("exact_copy",true);archive.put("same_file",false);archive.put("requested_source_path",source);archive.put("result_json_pointer","/steps/0/result");
        archive.set("archive",json(noSave));archive.set("original_checkpoint_receipt",json(hostPin));archive.set("original_checkpoint_result",result);
        Pin archivePin=write(temporary.resolve("ARCHIVE.actual.json"),archive);
        Path repo=Path.of(System.getProperty("xfm.source")).toAbsolutePath().normalize().getParent();
        ProducerSources.Binding parser=ProducerSources.verify(repo);
        List<Pin> dependencies=List.of(pin("source-derived-savecore.jar"),pin("source-derived-databind.jar"),pin("source-derived-core.jar"),pin("source-derived-annotations.jar"));
        ObjectNode raw=object();raw.put("schemaVersion",2);raw.put("machineId",base.machineId());raw.put("status","UNQUALIFIED_EXACT_STORY_DIAGNOSTIC");
        raw.put("inputUnchangedAtGuards",true);raw.put("fullStreamPasses",1);raw.put("financialCertified",false);raw.put("sourceLayoutQualified",false);raw.put("actualGameAcceptance",false);
        ObjectNode facts=actualUnavailableFactsFixture();
        // Reuse the actual producer DTO shape; this envelope's file extent remains software-authored.
        facts.put("realPath",noSave.path());facts.put("bytes",4);facts.put("creationTime","source-derived-time");facts.put("modifiedTime","source-derived-time");
        raw.put("completeStreamSha256",noSave.sha256());raw.put("completeStreamBytes","4");raw.set("before",facts);raw.set("after",facts);
        raw.set("parserBinding",json(parser));raw.put("exactStoryProjections",4);raw.put("combinedSelectedTokenBytes",2000);raw.put("actorTablePathObserved",true);
        ObjectNode limits=raw.putObject("limits");limits.put("maxStreamBytes",CapacityWindowReadback.STREAM);limits.put("maxRecordBytes",CapacityWindowReadback.RECORD);
        limits.put("maxCaptures",64);limits.put("maxTableRecords",200000);limits.put("maxSelectedTokenBytes",CapacityWindowReadback.RAW);limits.put("maxReportBytes",CapacityWindowReadback.RAW);
        ObjectNode rawRequest=raw.putObject("request");rawRequest.put("schemaVersion",2);rawRequest.put("machineId",base.machineId());rawRequest.put("repository",base.repository());rawRequest.put("expectedDateRaw",NATIVE);
        rawRequest.set("archiveReceipt",json(archivePin));rawRequest.set("save",json(noSave));rawRequest.set("readerSource",json(base.exactReaderSource()));
        rawRequest.putArray("actorIds").add(ACTOR);ArrayNode ids=rawRequest.putArray("storyIds");ArrayNode cp=rawRequest.putArray("classpath");for(Pin dependency:dependencies)cp.add(json(dependency));
        CapacityWindowReadback.Snapshot d0=window().getFirst();ArrayNode stories=raw.putArray("stories");
        for(var story:d0.stories().values()) {
            ids.add(story.id());ObjectNode row=stories.addObject();row.put("id",story.id());row.putArray("path").add("stories").add("active").add(story.id());
            row.put("producerCanonicalTokenSha256",story.witness().producerTokenSha256());row.set("lexemeAst",json(story.ast()));row.put("clausewitzTokens",story.ast().render());
        }
        ObjectNode actor=raw.putArray("actors").addObject();actor.put("id",ACTOR);actor.put("clausewitzTokens",d0.actor().render());
        ArrayNode projections=raw.putArray("projections");projections.addObject().put("name","globals").put("clausewitzTokens",d0.globals().render());
        projections.addObject().put("name","metadata_full").put("clausewitzTokens",body("version = \"1.21.0\" save_game_version = 19 meta_date = 1066.1.1").render());
        Pin rawPin=write(temporary.resolve("source-derived-raw.json"),raw);
        var actual=CapacityWindowReadback.readCheckpoint(request,new CapacityWindowReadback.CheckpointInput(0,archivePin,List.of(rawPin)),parser,dependencies,new ArrayList<>());
        assertEquals(d0.stories(),actual.stories());assertFalse(Files.exists(Path.of(noSave.path())));
        ObjectNode available=raw.deepCopy();
        for(String endpoint:List.of("before","after")) {
            ObjectNode present=(ObjectNode)available.get(endpoint);present.put("providerFileKeyStatus","AVAILABLE");present.put("providerFileKey","software-authored-provider-key");
        }
        Pin availablePin=write(temporary.resolve("source-derived-available-key.json"),available);
        assertEquals(d0.stories(),CapacityWindowReadback.readCheckpoint(request,new CapacityWindowReadback.CheckpointInput(0,archivePin,List.of(availablePin)),parser,dependencies,new ArrayList<>()).stories());
        for(String defect:List.of("unavailable-null","unavailable-nonempty","unavailable-missing","available-empty","available-null")) {
            ObjectNode malformed=raw.deepCopy();
            for(String endpoint:List.of("before","after")) {
                ObjectNode invalid=(ObjectNode)malformed.get(endpoint);
                switch(defect) {
                    case "unavailable-null" -> invalid.putNull("providerFileKey");
                    case "unavailable-nonempty" -> invalid.put("providerFileKey","not-the-producer-unavailable-value");
                    case "unavailable-missing" -> invalid.remove("providerFileKey");
                    case "available-empty" -> invalid.put("providerFileKeyStatus","AVAILABLE");
                    case "available-null" -> {invalid.put("providerFileKeyStatus","AVAILABLE");invalid.putNull("providerFileKey");}
                    default -> throw new IllegalArgumentException(defect);
                }
            }
            Pin malformedPin=write(temporary.resolve("source-derived-"+defect+".json"),malformed);
            IllegalArgumentException rejected=assertThrows(IllegalArgumentException.class,()->CapacityWindowReadback.readCheckpoint(request,new CapacityWindowReadback.CheckpointInput(0,archivePin,List.of(malformedPin)),parser,dependencies,new ArrayList<>()),defect);
            assertTrue(rejected.getMessage().contains("explicit file-key availability required"),defect);
        }
        ObjectNode tooMany=raw.deepCopy();for(int i=0;i<13;i++)((ArrayNode)tooMany.path("request").get("storyIds")).add(Integer.toString(9000+i));
        Pin bad=write(temporary.resolve("source-derived-too-many.json"),tooMany);
        assertThrows(IllegalArgumentException.class,()->CapacityWindowReadback.readCheckpoint(request,new CapacityWindowReadback.CheckpointInput(0,archivePin,List.of(bad)),parser,dependencies,new ArrayList<>()));
    }

    @Test void frozenPublicCaseManifestMountedClosureAndActorAreValidatedByProductionScopeConsumer() throws Exception {
        Scope scope=scope(); CapacityWindowReadback.verifyScopeIdentity(scope.request(),scope.context(),scope.frozen(),scope.prepared(),scope.manifest(),OBSERVATION);
        for(String key:List.of("cell","run_id")) {
            ObjectNode wrong=scope.frozen().deepCopy();wrong.put(key,"different-business");
            assertThrows(IllegalArgumentException.class,()->CapacityWindowReadback.verifyScopeIdentity(scope.request(),scope.context(),wrong,scope.prepared(),scope.manifest(),OBSERVATION));
        }
        ObjectNode wrong=scope.frozen().deepCopy();((ObjectNode)wrong.get("files")).remove(Path.of(pin("state").path()).resolve("profile/mod-content/fixture/_xfma_request.json").toString());
        assertThrows(IllegalArgumentException.class,()->CapacityWindowReadback.verifyScopeIdentity(scope.request(),scope.context(),wrong,scope.prepared(),scope.manifest(),OBSERVATION));
    }

    private record Scope(CapacityWindowReadback.Request request,ObjectNode context,ObjectNode frozen,ObjectNode prepared,ObjectNode manifest) { }
    private static ObjectNode actualUnavailableFactsFixture() throws IOException {
        try(var input=CapacityWindowReadbackTest.class.getResourceAsStream("/org/xar/ck3/markets/saveaudit/raw-exact-stories-unavailable-facts.json")) {
            assertTrue(input!=null,"actual producer DTO fixture must be packaged with the test");
            JsonNode fixture=SaveJson.read(input.readAllBytes(),JsonNode.class);
            assertEquals(fixture.get("before"),fixture.get("after"));
            assertEquals("UNAVAILABLE",fixture.path("before").path("providerFileKeyStatus").textValue());
            assertTrue(fixture.path("before").path("providerFileKey").isTextual());
            assertEquals("",fixture.path("before").path("providerFileKey").textValue());
            return ((ObjectNode)fixture.get("before")).deepCopy();
        }
    }
    private static Scope scope() throws IOException {
        Pin prepared=pin("prepared.json"),frozen=pin("frozen.json"),manifest=pin("manifest.json"),observer=pin("fixture/_xfma_request.json");
        var request=new CapacityWindowReadback.Request(1,"source-derived-software","source-derived-run",Path.of(System.getProperty("xfm.source")).toAbsolutePath().normalize().getParent().toString(),ACTOR,OBSERVER,EXCHANGE,
                pin("context.json"),frozen,prepared,manifest,observer,pin("review.json"),pin("report.json"),pin("RawExactStories.java"),pin("compiled.json"),
                List.of(new CapacityWindowReadback.CheckpointInput(0,pin("D0.json"),List.of(pin("D0-raw.json"))),new CapacityWindowReadback.CheckpointInput(30,pin("D30.json"),List.of(pin("D30-raw.json"))),new CapacityWindowReadback.CheckpointInput(395,pin("D395.json"),List.of(pin("D395-raw.json")))));
        ObjectNode context=object(),f=object(),p=object(),m=object(),inputs=object();
        inputs.set("prebuilt_fixture_manifest",json(manifest));
        context.put("schema","ck3-mod-acceptance-run-context-v1");context.put("run_id",request.runId());context.put("product","financial-markets");context.put("case","ai-capacity");
        context.set("prepared_case",json(prepared));context.set("frozen_argv",json(frozen));context.set("case_inputs",inputs);p.set("case_inputs",inputs);
        f.put("run_id",request.runId());f.put("mod_key","financial-markets");f.put("cell","ai-capacity");f.put("state_dir",pin("state").path());
        f.putArray("argv").add("--saved-campaign-player-id").add(ACTOR);
        ObjectNode files=f.putObject("files");files.set(prepared.path(),content(prepared));
        files.set(Path.of(pin("state").path()).resolve("profile/mod-content/fixture/_xfma_request.json").toString(),content(observer));
        m.put("schema","ck3-mod-acceptance-prebuilt-fixture-v1");m.put("product","financial-markets");m.put("case_id","ai-capacity");m.put("machine_id",request.machineId());
        m.put("fixture_root",Path.of(observer.path()).getParent().toString());ObjectNode inventory=m.putObject("files");inventory.set("_xfma_request.json",content(observer));
        for(var source:FollowupObservationScripts.render(OBSERVATION).entrySet()) {
            Pin member=new Pin(Path.of(observer.path()).getParent().resolve(source.getKey()).toString(),source.getValue().length,FilePins.sha256(source.getValue()));
            inventory.set(source.getKey(),content(member));
            files.set(Path.of(pin("state").path()).resolve("profile/mod-content/fixture").resolve(source.getKey()).toString(),content(member));
        }
        return new Scope(request,context,f,p,m);
    }

    private static List<CapacityWindowReadback.Snapshot> window() { return new ArrayList<>(SOURCE_DERIVED_WINDOW); }
    private static List<CapacityWindowReadback.Snapshot> sourceDerivedWindow() {
        try { return buildWindow(); }
        catch(IOException failure) { throw new ExceptionInInitializerError(failure); }
    }
    private static List<CapacityWindowReadback.Snapshot> buildWindow() throws IOException {
        List<CapacityWindowReadback.Snapshot> rows=new ArrayList<>();
        for(int n:List.of(0,30,395)) {
            Map<String,CapacityWindowReadback.Story> stories=new LinkedHashMap<>();stories.put(OBSERVER,story(OBSERVER,observer(n)));
            if(n==0) {
                stories.put(ACCOUNT,story(ACCOUNT,withVariables("xfm_finance_account",Map.of("xfm_account_id",number(2),"xfm_holder",reference("char",HOLDER)))));
                stories.put(COIN,story(COIN,withVariables("xfm_finance_coin",Map.of("xfm_coin_id",number(55)))));
                stories.put(EXCHANGE,story(EXCHANGE,withVariables("xfm_finance_exchange",Map.of("xfm_day",number(FINANCIAL),"xfm_last_date",number(SCRIPT)))));
            }
            for(int i=1;i<=n;i++) stories.put(dayId(i),story(dayId(i),day(i)));
            Clausewitz.Block actor=body("alive_data = "+variables(Map.of("xfma_ai_capacity_e1_armed",number(1),"xfma_ai_capacity_e1_story",reference("story",OBSERVER))).render());
            Clausewitz.Block globals=variables(Map.of("xfm_exchange",reference("story",EXCHANGE))).block("variables");
            rows.add(new CapacityWindowReadback.Snapshot(n,NATIVE+24L*n,actor,globals,stories));
        }
        return rows;
    }
    private static Clausewitz.Block observer(int n) {
        Map<String,Clausewitz.Block> fields=new LinkedHashMap<>();
        fields.put("xfma_start_day",number(FINANCIAL));fields.put("xfma_start_date",number(SCRIPT));fields.put("xfma_ready",number(1));fields.put("xfma_capacity_protocol",number(1));
        fields.put("xfma_account",reference("story",ACCOUNT));fields.put("xfma_coin",reference("story",COIN));fields.put("xfma_holder_before",reference("char",HOLDER));
        for(String key:List.of("xfma_capacity_day_records","xfma_daily_samples"))fields.put(key,number(n));
        fields.put("xfma_capacity_warmup_records",number(Math.min(n,30)));
        for(String key:List.of("xfma_capacity_measured_records","xfma_measured_samples"))fields.put(key,number(Math.max(n-30,0)));
        for(String key:List.of("xfma_capacity_skipped_financial_days","xfma_capacity_missing_source_days","xfma_capacity_invalid_work_days"))fields.put(key,number(0));
        for(String key:List.of("xfma_last_sample_day","xfma_capacity_last_record_day","xfma_capacity_last_attempt_day"))fields.put(key,number(FINANCIAL+n));
        fields.put("xfma_capacity_last_source_date",number(SCRIPT+n));
        Clausewitz.Block result=withVariables("xfma_ai_capacity_e1_observer",fields);
        if(n==0)return result;
        StringBuilder list=new StringBuilder("{ name = xfma_capacity_days ");for(int i=1;i<=n;i++)list.append(" item = ").append(reference("story",dayId(i)).render());list.append(" }");
        List<Clausewitz.Entry> entries=new ArrayList<>(result.entries());entries.add(entry("variable_lists",body(list.toString())));return new Clausewitz.Block(entries);
    }
    private static Clausewitz.Block day(int ordinal) {
        Map<String,Clausewitz.Block> values=new LinkedHashMap<>();
        values.put("xfma_record_protocol",number(1));values.put("xfma_record_id",number(ordinal));values.put("xfma_window_day",number(ordinal));
        values.put("xfma_observer",reference("story",OBSERVER));values.put("xfma_exchange_source",reference("story",EXCHANGE));
        values.put("xfma_financial_day",number(FINANCIAL+ordinal));values.put("xfma_previous_record_financial_day",number(FINANCIAL+ordinal-1));
        values.put("xfma_source_script_date",number(SCRIPT+ordinal));values.put("xfma_previous_source_script_date",number(SCRIPT+ordinal-1));
        values.put("xfma_measured_sample",number(ordinal>30?1:0));values.put("xfma_skipped_financial_days_before",number(0));values.put("xfma_required_sources_complete",number(1));
        for(String field:CapacityWindowReadback.FIELDS) {values.put("xfma_"+field+"_available",number(1));values.put("xfma_"+field,number(field.equals("last_date")?SCRIPT+ordinal:100));}
        values.put("xfma_ai_work_today",number(8));values.put("xfma_ai_decisions_today",number(3));values.put("xfma_work_without_decision_available",number(1));values.put("xfma_work_without_decision",number(5));
        return withVariables("xfma_ai_capacity_day_record",values);
    }
    private static List<CapacityWindowReadback.Snapshot> shiftFinancialOrigin(long origin) throws IOException {
        List<CapacityWindowReadback.Snapshot> shifted=window();
        for(int at=0;at<shifted.size();at++) {
            CapacityWindowReadback.Snapshot snapshot=shifted.get(at);
            Map<String,CapacityWindowReadback.Story> stories=new LinkedHashMap<>(snapshot.stories());
            Clausewitz.Block observer=replaceVariable(stories.get(OBSERVER).ast(),"xfma_start_day",number(origin));
            for(String field:List.of("xfma_last_sample_day","xfma_capacity_last_record_day","xfma_capacity_last_attempt_day"))
                observer=replaceVariable(observer,field,number(origin+snapshot.offset()));
            stories.put(OBSERVER,story(OBSERVER,observer));
            if(snapshot.offset()==0)stories.put(EXCHANGE,story(EXCHANGE,replaceVariable(stories.get(EXCHANGE).ast(),"xfm_day",number(origin))));
            for(int ordinal=1;ordinal<=snapshot.offset();ordinal++) {
                String id=dayId(ordinal);Clausewitz.Block record=stories.get(id).ast();
                record=replaceVariable(record,"xfma_financial_day",number(origin+ordinal));
                record=replaceVariable(record,"xfma_previous_record_financial_day",number(origin+ordinal-1));
                stories.put(id,story(id,record));
            }
            shifted.set(at,new CapacityWindowReadback.Snapshot(snapshot.offset(),snapshot.nativeDateRaw(),snapshot.actor(),snapshot.globals(),stories));
        }
        return shifted;
    }
    private static List<CapacityWindowReadback.Snapshot> shiftNativeOrigin(long origin) {
        List<CapacityWindowReadback.Snapshot> shifted=window();
        for(int at=0;at<shifted.size();at++) {
            CapacityWindowReadback.Snapshot snapshot=shifted.get(at);
            shifted.set(at,new CapacityWindowReadback.Snapshot(snapshot.offset(),origin+24L*snapshot.offset(),snapshot.actor(),snapshot.globals(),snapshot.stories()));
        }
        return shifted;
    }
    private static List<CapacityWindowReadback.Snapshot> mutateDay(List<CapacityWindowReadback.Snapshot> rows,int offset,int ordinal,String key,Clausewitz.Block value) throws IOException {
        return changeStory(rows,offset,dayId(ordinal),body->replaceVariable(body,key,value));
    }
    private static List<CapacityWindowReadback.Snapshot> removeDayVariable(List<CapacityWindowReadback.Snapshot> rows,int offset,int ordinal,String key) throws IOException {
        return changeStory(rows,offset,dayId(ordinal),body->replaceVariable(body,key,null));
    }
    private static List<CapacityWindowReadback.Snapshot> mutateObserver(List<CapacityWindowReadback.Snapshot> rows,int index,String key,Clausewitz.Block value) throws IOException {
        return changeStory(rows,rows.get(index).offset(),OBSERVER,body->replaceVariable(body,key,value));
    }
    private static List<CapacityWindowReadback.Snapshot> changeStory(List<CapacityWindowReadback.Snapshot> rows,int offset,String id,UnaryOperator<Clausewitz.Block> change) throws IOException {
        int at=List.of(0,30,395).indexOf(offset);CapacityWindowReadback.Snapshot source=rows.get(at);
        Map<String,CapacityWindowReadback.Story> stories=new LinkedHashMap<>(source.stories());stories.put(id,story(id,change.apply(stories.get(id).ast())));
        rows.set(at,new CapacityWindowReadback.Snapshot(offset,source.nativeDateRaw(),source.actor(),source.globals(),stories));return rows;
    }
    private static Clausewitz.Block replaceVariable(Clausewitz.Block source,String key,Clausewitz.Block value) {
        Map<String,Clausewitz.Block> fields=new LinkedHashMap<>(CapacityWindowReadback.variables(source));fields.remove(key);if(value!=null)fields.put(key,value);
        List<Clausewitz.Entry> entries=new ArrayList<>();for(Clausewitz.Entry entry:source.entries())if(!entry.key().equals("variables"))entries.add(entry);
        entries.add(entry("variables",variables(fields).block("variables")));return new Clausewitz.Block(entries);
    }
    private static CapacityWindowReadback.Story story(String id,Clausewitz.Block ast) throws IOException {
        String hash=FilePins.sha256(SaveJson.write(ast));return new CapacityWindowReadback.Story(id,ast,new CapacityWindowReadback.Witness(id,hash,hash));
    }
    private static Clausewitz.Block withVariables(String type,Map<String,Clausewitz.Block> fields) {
        return body("story_cycle = "+type+" owner = "+ACTOR+" "+variables(fields).body());
    }
    private static Clausewitz.Block variables(Map<String,Clausewitz.Block> fields) {
        StringBuilder source=new StringBuilder("variables = { data = { ");fields.forEach((key,value)->source.append("{ flag = ").append(key).append(" data = ").append(value.render()).append(" } "));
        return body(source.append("} }").toString());
    }
    private static Clausewitz.Block number(long value) {
        BigInteger raw=BigInteger.valueOf(value).multiply(BigInteger.valueOf(100000));if(raw.signum()<0)raw=raw.add(BigInteger.ONE.shiftLeft(64));
        return body("type = value"+(value==0?"":" identity = "+raw));
    }
    private static Clausewitz.Block reference(String type,String id) {return body("type = "+type+" identity = "+id);}
    private static Clausewitz.Block body(String source) {return Clausewitz.parse(source);}
    private static Clausewitz.Entry entry(String name,Clausewitz.Value value) {return new Clausewitz.Entry(name,"=",value);}
    private static String dayId(int ordinal) {return Integer.toString(2000+ordinal);}
    private static void collectAvailable(Clausewitz.Block block,Set<String> result) {
        for(Clausewitz.Entry entry:block.entries()) {
            if(entry.key().equals("set_variable") && entry.value() instanceof Clausewitz.Block set) {
                String name=set.atom("name","");if(name.startsWith("xfma_") && name.endsWith("_available"))result.add(name.substring(5,name.length()-10));
            }
            if(entry.value() instanceof Clausewitz.Block child)collectAvailable(child,result);
        }
    }
    private static void collectRequired(Clausewitz.Block block,Set<String> result) {
        for(Clausewitz.Entry entry:block.entries())if(entry.value() instanceof Clausewitz.Block child) {
            if(entry.key().equals("if") && child.named("set_variable").stream().anyMatch(row->row.value() instanceof Clausewitz.Block set && set.atom("name","").equals("xfma_required_sources_complete") && set.atom("value","").equals("1")))
                for(Clausewitz.Entry term:child.block("limit").block("AND").entries())result.add(term.key().substring("var:xfma_".length(),term.key().length()-"_available".length()));
            collectRequired(child,result);
        }
    }
    private static ObjectNode nativeReport(int count) throws IOException {return nativeReport(count,NATIVE);}
    private static ObjectNode nativeReport(int count,long origin) throws IOException {
        ObjectNode report=object();ArrayNode steps=report.putArray("steps");
        for(int i=1;i<=count;i++) {
            ObjectNode row=steps.addObject();row.put("id","source-derived-native-day-"+i);row.put("ok",true);row.putObject("plan").put("kind","advance_day").put("days",1);
            ObjectNode result=row.putObject("result");result.put("requested_days",1);result.put("requested_interval_complete",true);result.putNull("event_boundary");result.put("elapsed_hours",24);
            result.set("before",frame(origin+24L*(i-1),2L*i));result.set("after",frame(origin+24L*i,2L*i+1));
        }
        return report;
    }
    private static ObjectNode frame(long date,long revision) throws IOException {
        ObjectNode frame=object();frame.put("schema","ck3_1210_full_state_v1");frame.put("game_version","1.21.0");
        frame.put("executable_sha256","2f2b236a16223891c2da8b167f5f3738d2ae3e6d69de1b4fbe190a5402998acc");
        frame.put("adapter_id","ck3-1.21.0-msvc-x64");frame.put("source","injected-dll-named-pipe");frame.put("native_revision",revision);
        frame.put("date_raw",date);frame.put("paused",true);frame.put("map_ready",true);frame.putObject("played_character").put("character_id",Long.parseLong(ACTOR)).put("alive",true);return frame;
    }
    private static ObjectNode object() throws IOException {return (ObjectNode)SaveJson.read("{}".getBytes(StandardCharsets.UTF_8),JsonNode.class);}
    private static JsonNode json(Object value) throws IOException {return SaveJson.read(SaveJson.write(value),JsonNode.class);}
    private static ObjectNode content(Pin pin) throws IOException {ObjectNode value=object();value.put("bytes",pin.bytes());value.put("sha256",pin.sha256());return value;}
    private static Pin pin(String relative) {return new Pin(Path.of("source-derived-fixture").toAbsolutePath().normalize().resolve(relative).toString(),1,"0".repeat(64));}
    private static Pin write(Path path,JsonNode data) throws IOException {Files.write(path,SaveJson.write(data));return FilePins.pin(path);}
}
