package org.xar.ck3.rrf.save;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.rrf.Contracts;
import org.xar.ck3.rrf.ExpectedSelection;
import org.xar.ck3.rrf.Json;
import org.xar.ck3.rrf.ReleaseBuilder;
import org.xar.ck3.rrf.acceptance.FixtureContracts;
import org.xar.ck3.rrf.acceptance.FixtureEmitter;
import org.xar.ck3.rrf.save.SaveContracts.*;

/** Actual emitter/public prepare/decoder child/typed consumer. World bytes and installed identity are authored. */
final class SavedCancelComparatorTest {
    @TempDir Path temporary;
    private Path repo,before,after,decoder,manifest,prepared;
    private static final NativeId ACTOR=new NativeId("900001");
    @BeforeEach void prepareActualBoundProducer() throws Exception {
        repo=Path.of(System.getProperty("rrf.source")).toAbsolutePath().normalize().getParent();
        var recipe=Json.read(Files.readAllBytes(repo.resolve("mod_religious_ritual_fusion/tools/src/main/resources/acceptance/requests/core-rite.json")),FixtureContracts.Request.class);
        var fixture=FixtureEmitter.emit(repo,temporary.resolve("fixture"),"authored-machine",recipe);manifest=fixture.manifest();
        var product=new ReleaseBuilder().build(repo.resolve("mod_religious_ritual_fusion"),temporary.resolve("product"),
                new Contracts.ReleaseIdentity("3826756673","authored-cancel-software","0".repeat(40)),new Contracts.Provenance(Contracts.ProvenanceKind.SYNTHETIC_FIXTURE,"authored-machine","2026-11-20T00:00:00Z"));
        String python="""
                import json,sys
                from pathlib import Path
                from unittest.mock import patch
                repo,manifest,product,output=map(Path,sys.argv[1:]);sys.path[:0]=[str(repo/'tools'),str(repo/'ck3_autonomous_player/src')]
                import ck3_mod_acceptance_prepare as p
                from ck3_mod_acceptance_cases import generic_product_adapter as a
                output.mkdir();r=output/'runtime.json';r.write_text(json.dumps({'machine_id':'authored-machine'}),encoding='utf-8')
                plain={}
                for i,n in enumerate(p.CONFIG_NAMES):
                    f=output/('plain-'+str(i));f.write_text('authored plain config',encoding='utf-8');plain[n]=p.pin(f)
                c={'product':'religious-ritual-fusion','case':'core','repo_root':str(repo),'runtime_manifest':p.pin(r),'output':str(output/'prepared'),'state_dir':str(output/'state'),
                    'case_contract':json.loads((repo/'tools/ck3_mod_acceptance_cases/religious_ritual_fusion_core.json').read_bytes()),
                    'case_inputs':{'product_dir':str(product),'plain_configuration':plain,'prebuilt_fixture_manifest':p.pin(manifest)}}
                (output/'prepared').mkdir()
                with patch.object(p,'_engine',return_value=(None,{'game_version':'authored-no-game','exe_sha256':'0'*64})):
                    result=a.prepare_case(c)
                assert result['business_pass'] is False and result['runtime_status']=='NOT_RUN'
                """;
        Process p=new ProcessBuilder(System.getProperty("dynastic.python","python"),"-B","-X","utf8","-c",python,repo.toString(),manifest.toString(),product.staging(),temporary.resolve("public").toString()).redirectErrorStream(true).start();
        assertTrue(p.waitFor(45,TimeUnit.SECONDS));assertEquals(0,p.exitValue(),new String(p.getInputStream().readAllBytes(),StandardCharsets.UTF_8));
        prepared=temporary.resolve("public/prepared/profile-preparation.json");
        decoder=Path.of(System.getProperty("java.home"),"bin",System.getProperty("os.name").startsWith("Windows")?"java.exe":"java").toRealPath();
        before=temporary.resolve("before-AUTHORED.ck3");after=temporary.resolve("after-AUTHORED.ck3");Files.writeString(before,world());Files.writeString(after,world());
    }
    private static Pin pin(Path p)throws IOException{return SaveInspector.pin(p);}
    private Request request()throws IOException {
        var tables=new ArrayList<org.xar.ck3.save.SaveContracts.TableSelection>();
        for(var e:List.of(new String[]{"ACTOR","living","900001"},new String[]{"RITE","rites/database","150,151,152"},new String[]{"FAITH","faiths/database","13,99"},new String[]{"RELIGION","religion/religions","8"},new String[]{"HOUSE","houses/database","174"},new String[]{"DYNASTY","dynasties/database","30"}))
            tables.add(new org.xar.ck3.save.SaveContracts.TableSelection(org.xar.ck3.save.SaveContracts.ScopeKind.valueOf(e[0]),List.of(e[1].split("/")),java.util.Arrays.stream(e[2].split(",")).map(org.xar.ck3.save.SaveContracts.NativeId::new).toList(),true));
        var selection=new org.xar.ck3.save.SaveContracts.Selection(tables,List.of(),true,false,List.of());
        return new Request(3,"authored-machine",repo.toString(),pin(after),pin(decoder),new Layout(List.of("living"),List.of("rites","database"),List.of("faiths","database"),List.of("religion","religions")),
                new Selection(ACTOR,ids("150","151","152"),ids("13","99"),ids("8")),new CancelUnchanged(pin(before),pin(manifest),pin(prepared),selection));
    }
    private static List<NativeId> ids(String...values){return java.util.Arrays.stream(values).map(NativeId::new).toList();}
    private SaveInspector.DecoderLauncher launcher(AtomicInteger calls){return (executable,save)->{calls.incrementAndGet();String classes;
        try { classes=Path.of(SavedCancelComparatorTest.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toAbsolutePath().toString(); }
        catch(java.net.URISyntaxException e){throw new IOException(e);}
        return new ProcessBuilder(executable.toString(),"-cp",classes,"melt",save.toString(),"-c","--format","ck3","--unknown-key","error").start();};}
    @Test void realBoundChainReadsFourCompleteStreamsAndTypedReportPreservesExactScope()throws Exception {
        var calls=new AtomicInteger();Request r=request();Report report=SaveInspector.inspect(r,launcher(calls));
        assertEquals(4,calls.get());assertEquals("rrf-save-cancel-inspection-v3",report.schema());assertEquals(report,Json.read(Json.write(report),Report.class));
        var result=assertInstanceOf(CancelVerified.class,report.assessment());assertTrue(result.noNewObject());assertEquals("1000.12500",result.before().actor().piety());
        assertEquals(ACTOR,result.after().actor().actorId());assertEquals(new StateValue(false,""),result.before().actor().state());
        assertEquals(List.of(new NativeId("160")),result.before().completeInventories().getFirst().tombstoneIds());
        assertEquals(new NativeId("174"),result.after().actor().houseId());assertEquals(new NativeId("30"),result.after().actor().dynastyId());assertTrue(result.reportedDraftDifferences().isEmpty());
        assertEquals(pin(before),result.before().save());assertEquals(pin(after),result.after().save());
        assertEquals(result.before().save().sha256(),result.after().save().sha256(),"distinct real saved files may legitimately have identical bytes");
        assertNotEquals(result.before().physical().fileKey(),result.after().physical().fileKey());
        assertTrue(report.producerSources().stream().anyMatch(p->p.path().endsWith("SavedCancelComparator.java")));
    }
    @Test void onlyExplicitEmptyDraftCachePresenceMayDifferAndStateIsNeverNormalized()throws Exception {
        for(String cache:List.of("rrf_candidate_tenets","rrf_family_converts")) {
            Files.writeString(after,world().replace("list={}","list={{name=\""+cache+"\" duration={1}}}"));
            var value=(CancelVerified)SaveInspector.inspect(request(),launcher(new AtomicInteger())).assessment();assertEquals(1,value.reportedDraftDifferences().size());
            Files.writeString(after,world().replace("list={}","list={{name=\""+cache+"\" item={type=character identity=900002}}}"));
            assertThrows(IOException.class,()->SaveInspector.inspect(request(),launcher(new AtomicInteger())),"nonempty draft cache never qualifies");
        }
        for(String state:List.of("editing","committing","unresolved","succeeded")) {
            Files.writeString(after,world().replace("data={"+variable("rrfa_seed_done",""),"data={"+variable("rrf_state","type=flag flag=\""+state+"\"")+variable("rrfa_seed_done","")));
            assertThrows(IOException.class,()->SaveInspector.inspect(request(),launcher(new AtomicInteger())),state);
        }
        Files.writeString(after,world().replace("data={"+variable("rrfa_seed_done",""),"data={"+variable("rrf_state","type=flag flag=\"idle\"")+variable("rrfa_seed_done","")));
        assertThrows(IOException.class,()->SaveInspector.inspect(request(),launcher(new AtomicInteger())),"absent is not idle");
    }
    @Test void persistentFieldChangesTypesAndDuplicateReferencesRefuse()throws Exception {
        List<String> wrong=List.of(world().replace("currency=1000.12500","currency=1000.12501"),world().replace("currency=1000.12500","currency=\"1000.12500\""),
                world().replace("currency=1000.12500","currency=1000 currency=1000"),world().replace("currency=1000.12500",""),world().replace("dynasty_house=174","dynasty_house=175"),world().replace("dynasty=30","dynasty=31"),
                world().replace("rite=150 dynasty_house","rite=151 dynasty_house"),world().replace("name=\"House\"","name=\"Changed House\""),
                world().replace("data={"+variable("rrfa_seed_done",""),"data={"+variable("rrf_fusion_cooldown","")+variable("rrfa_seed_done","")),
                world().replace("data={"+variable("rrfa_seed_done",""),"data={"+variable("rrf_last_result_rite","type=rite identity=999")+variable("rrfa_seed_done","")),
                world().replace(variable("rrfa_source_a","type=rite identity=150"),variable("rrfa_source_a","type=rite identity=150")+variable("rrfa_source_a","type=rite identity=150")),
                world().replace("dynasty_house=174","dynasty_house={174}"),world().replace("variables={","flags={rrf_fusion_cooldown=yes} variables={"),
                world().replace("1066.9.15","1066.9.16"),world().replace("authored-cancel-campaign","other-campaign"));
        for(int i=0;i<wrong.size();i++){Files.writeString(after,wrong.get(i));var calls=new AtomicInteger();assertThrows(IOException.class,()->SaveInspector.inspect(request(),launcher(calls)),"case "+i);assertTrue(calls.get()>=3,"negative reached the after-Save decode");}
    }
    @Test void completeInventoryDetectsSameCountReplacementResurrectionTombstonesAndMalformedSlots()throws Exception {
        for(String wrong:List.of(world().replace("0={faith=13}","777={faith=13}"),world().replace("160=none","160={faith=13}"),world().replace("160=none","161=none"),
                world().replace("160=none","160=garbage"),world().replace("160=none","160=\"none\""),world().replace("160=none","160=none 160=none"),world().replace("160=none","160=none 151={faith=13}"),
                world().replace("99={religion=8 main_rite=152}","98={religion=8 main_rite=152}"))) {
            Files.writeString(after,wrong);assertThrows(IOException.class,()->SaveInspector.inspect(request(),launcher(new AtomicInteger())));
        }
    }
    @Test void missingTableActorAndRecordNeverBecomeObservedEmptyAndOverflowRefuses()throws Exception {
        for(String wrong:List.of(world().replace("living=","unobserved_living="),world().replace("900001={","900002={"),world().replace("houses={","unknown_houses={"),world().replace("rites={","unknown_rites={"),world().replace("174={dynasty=30 name=\"House\"}","174=none"))){
            Files.writeString(after,wrong);assertThrows(IOException.class,()->SaveInspector.inspect(request(),launcher(new AtomicInteger())));
        }
        StringBuilder many=new StringBuilder();for(int i=1000;i<=201000;i++)many.append(i).append("={faith=13} ");
        Files.writeString(after,world().replace("160=none","160=none "+many));assertThrows(IOException.class,()->SaveInspector.inspect(request(),launcher(new AtomicInteger())));
    }
    @Test void schemaPinsPreparedActorAndImmutablePairAreStrict()throws Exception {
        Request r=request();assertEquals(r,Json.read(Json.write(r),Request.class));
        assertThrows(IllegalArgumentException.class,()->new Request(2,r.machineId(),r.repository(),r.save(),r.decoder(),r.layout(),r.selection(),r.expectation()));
        assertThrows(IllegalArgumentException.class,()->new Request(3,r.machineId(),r.repository(),r.save(),r.decoder(),r.layout(),r.selection(),new InspectOnly()));
        byte[] request=Json.write(r);assertThrows(IOException.class,()->Json.read(new String(request,StandardCharsets.UTF_8).replace("\"schemaVersion\" : 3","\"schemaVersion\" : 3, \"unknown\" : true").getBytes(StandardCharsets.UTF_8),Request.class));
        Files.writeString(after,world()+"#same physical name different content\n");assertThrows(IOException.class,()->SaveInspector.inspect(r,launcher(new AtomicInteger())));
        Files.writeString(after,world());Files.writeString(prepared,"{}");assertThrows(IOException.class,()->SaveInspector.inspect(request(),launcher(new AtomicInteger())));
    }
    @Test void hardlinkedPairAndSameHashReplacementAreNotIndependentPhysicalEvidence()throws Exception {
        Files.delete(after);Files.createLink(after,before);
        var calls=new AtomicInteger();assertThrows(IOException.class,()->SaveInspector.inspect(request(),launcher(calls)));assertEquals(0,calls.get());
        Files.delete(after);Files.writeString(after,world());Request r=request();calls.set(0);
        var normal=launcher(calls);
        assertThrows(IOException.class,()->SaveInspector.inspect(r,(executable,save)->{
            if(calls.get()==2){Files.move(before,temporary.resolve("before-retired-owned.ck3"));Files.writeString(before,world());}
            return normal.start(executable,save);
        }));
        assertEquals(4,calls.get());
    }
    @Test void modeStorageAndTypedAssessmentRemainClosedContracts()throws Exception {
        Files.writeString(after,world().replace("type=flag flag=\"rite\"","type=character flag=\"rite\""));
        var calls=new AtomicInteger();assertThrows(IOException.class,()->SaveInspector.inspect(request(),launcher(calls)));assertEquals(4,calls.get());
        Files.writeString(after,world());Report report=SaveInspector.inspect(request(),launcher(new AtomicInteger()));
        String raw=new String(Json.write(report),StandardCharsets.UTF_8);
        assertThrows(IOException.class,()->Json.read(raw.replace("\"noNewObject\" : true","\"noNewObject\" : false").getBytes(StandardCharsets.UTF_8),Report.class));
        var node=Json.read(Json.write(report),com.fasterxml.jackson.databind.JsonNode.class);
        ((com.fasterxml.jackson.databind.node.ObjectNode)node.path("assessment").path("before").path("actor")).put("actorId","900002");
        assertThrows(IOException.class,()->Json.read(Json.write(node),Report.class));
        ((com.fasterxml.jackson.databind.node.ObjectNode)node.path("assessment").path("after").path("actor")).put("actorId","900002");
        assertThrows(IOException.class,()->Json.read(Json.write(node),Report.class),"matching pair still must belong to the requested actor");
        var samePhysical=Json.read(Json.write(report),com.fasterxml.jackson.databind.node.ObjectNode.class);
        ((com.fasterxml.jackson.databind.node.ObjectNode)samePhysical.path("assessment").path("after")).set("physical",samePhysical.path("assessment").path("before").path("physical"));
        assertThrows(IOException.class,()->Json.read(Json.write(samePhysical),Report.class));
        for(String field:List.of("selectedRecords","objectIds")) {
            var incomplete=Json.read(Json.write(report),com.fasterxml.jackson.databind.node.ObjectNode.class);
            for(String side:List.of("before","after")) {
                var value=incomplete.path("assessment").path(side);
                if(field.equals("selectedRecords"))((com.fasterxml.jackson.databind.node.ObjectNode)value).putArray(field);
                else for(var inventory:value.path("completeInventories"))((com.fasterxml.jackson.databind.node.ObjectNode)inventory).putArray(field);
            }
            assertThrows(IOException.class,()->Json.read(Json.write(incomplete),Report.class),"equal incomplete pair is not a complete oracle");
        }
        var missingUnselected=Json.read(Json.write(report),com.fasterxml.jackson.databind.node.ObjectNode.class);
        for(String side:List.of("before","after")) {
            var ids=(com.fasterxml.jackson.databind.node.ArrayNode)missingUnselected.path("assessment").path(side).path("completeInventories").get(0).path("objectIds");
            assertEquals("0",ids.get(0).textValue());ids.remove(0);
        }
        assertThrows(IOException.class,()->Json.read(Json.write(missingUnselected),Report.class),"selected-only equality cannot omit an observed unselected live ID");
    }
    /** Maintenance-only packaged-CLI input/consumer driver; does not ship in any runtime artifact. */
    public static void main(String[] args)throws Exception {
        if(args.length!=2)throw new IllegalArgumentException("prepare/verify and owned path required");
        if(args[0].equals("prepare")) {
            var owned=new SavedCancelComparatorTest();owned.temporary=Path.of(args[1]);
            if(Files.exists(owned.temporary))throw new IOException("unused owned fixture output required");
            Files.createDirectories(owned.temporary);owned.prepareActualBoundProducer();
            Files.write(owned.temporary.resolve("request.json"),Json.write(owned.request()));
        } else if(args[0].equals("verify")) {
            Report report=Json.read(Files.readAllBytes(Path.of(args[1])),Report.class);
            if(!(report.assessment() instanceof CancelVerified result)||!result.noNewObject()||!report.schema().equals("rrf-save-cancel-inspection-v3"))throw new IOException("actual typed cancellation report required");
            if(!result.before().save().equals(((CancelUnchanged)report.request().expectation()).beforeSave())||!result.after().save().equals(report.request().save()))throw new IOException("typed report crossed actual request");
            System.out.println("ACTUAL_PACKAGED_CANCEL_TYPED_CONSUMER_PASS; input_world=AUTHORED_SOFTWARE_ONLY; game_started=false");
        } else throw new IllegalArgumentException("unknown owned fixture mode");
    }
    private static String variable(String name,String value){return "{flag=\""+name+"\" data={"+value+"}}";}
    private static String rite(String id,String faith,List<ExpectedSelection.TenetKey> cores){String direct=cores.stream().map(k->"tenet=\""+k.value()+"\" ").reduce("",String::concat);String rows=cores.stream().map(k->"{tenet=\""+k.value()+"\" status=core}").reduce("",String::concat);return id+"={faith="+faith+" data={"+direct+"tenets={"+rows+"}}} ";}
    static String world(){String vars=variable("rrfa_seed_done","")+variable("rrfa_source_a","type=rite identity=150")+variable("rrfa_source_b_rite","type=rite identity=151")+variable("rrfa_source_b_faith_rite","type=rite identity=152")+variable("rrfa_source_a_faith","type=faith identity=13")+variable("rrfa_source_b_faith","type=faith identity=99")+variable("rrfa_expected_b","type=rite identity=151")+variable("rrfa_mode","type=flag flag=\"rite\"");
        return "CK3txt # AUTHORED_CANCEL_SOFTWARE_ONLY\nmeta_data={version=\"1.21.0.3\"} playthrough_id=\"authored-cancel-campaign\" date=1066.9.15 "+
            "living={900001={rite=150 dynasty_house=174 alive_data={piety={currency=1000.12500} variables={data={"+vars+"} list={}}}}} "+
            "rites={database={0={faith=13} "+rite("150","13",FixtureContracts.SOURCE_A)+rite("151","13",FixtureContracts.SOURCE_B)+rite("152","99",FixtureContracts.SOURCE_B)+"160=none}} "+
            "faiths={database={13={religion=8 main_rite=0} 99={religion=8 main_rite=152} 100=none}} religion={religions={8={key=\"christianity\"}}} houses={database={174={dynasty=30 name=\"House\"}}} dynasties={database={30={name=\"Dynasty\"}}}";
    }
}
