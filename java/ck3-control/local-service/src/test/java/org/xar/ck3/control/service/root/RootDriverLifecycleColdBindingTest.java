package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.service.root.RootDriverLifecycleResumeCodec.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;

/** Original Python cold DATA producer and public codec consumers; no private pending ledger or cold ticket. */
final class RootDriverLifecycleColdBindingTest {
    private static final BigInteger MAX=new BigInteger("18446744073709551615");
    private static final List<String> COUNTERS=List.of("connection_generation","revision","native_revision");
    private static final List<String> PROOF=List.of("status","predecessor_character_id","successor_character_id",
            "source_episode_run_id","episode_run_id","same_campaign_frame","ck3_command_submitted","process_restarted",
            "succession_lifecycle","reconciliation","predecessor_binding","successor_episode_binding");
    private static TransitionMaterial transition(){return RootDriverLifecycleResumeCodecTest.transition(Qualification.VERIFIED,Optional.empty());}
    private static Obj tree(RawJson actual){return DriverJson.object(actual.bytes(),RawJson.MAXIMUM_BYTES);}
    private static RawJson json(Obj actual){return PublicDataJson.encodeFullMaterial(actual);}
    private static IntegerValue number(long value){return new IntegerValue(BigInteger.valueOf(value));}
    private static ColdFrame retained(){return new ColdFrame(7,MAX,"snapshot",MAX,MAX,4,12,"new");}
    private static ColdFrame resumed(){return new ColdFrame(7,BigInteger.ONE,"new-connection",BigInteger.ONE,MAX,4,12,"new");}
    private static ColdGame game(){return new ColdGame(7,"2026-10-24T19:00:00.000000Z","D:/游戏/\uE000/\uD800\uDC00/ck3.exe");}
    private static ExactRef ledger(){byte[] data="software-only actual Java pending-domain body".getBytes(StandardCharsets.UTF_8);return new ExactRef("software-data:canonical-natural-clock-originals",data.length,DriverJson.sha256(data));}
    private static ColdBindingMaterial material(Optional<RawJson> observation,ColdFrame current){
        return new ColdBindingMaterial(transition(),observation,retained(),current,"xenoamess-full-tower-eb9d2c1186","a".repeat(64),game(),ledger(),!current.connectionGeneration().equals(MAX));
    }
    private static Obj frame(ColdFrame value){return new Obj(Map.of("bridge_pid",number(value.bridgePid()),"connection_generation",new IntegerValue(value.connectionGeneration()),
            "snapshot_id",new Text(value.snapshotId()),"revision",new IntegerValue(value.revision()),"native_revision",new IntegerValue(value.nativeRevision()),
            "date_raw",number(value.dateRaw()),"actor_character_id",number(value.actorCharacterId()),"episode_run_id",new Text(value.episodeRunId())));}
    private static RawJson currentSnapshot(ColdFrame current){
        Obj snapshot=tree(RootDriverLifecycleResumeCodecTest.snapshot()),diagnostics=object(snapshot.get("diagnostics"),"diagnostics");
        return json(snapshot.with("snapshot_id",new Text(current.snapshotId())).with("revision",new IntegerValue(current.revision()))
                .with("native_revision",new IntegerValue(current.nativeRevision())).with("date_raw",number(current.dateRaw()))
                .with("diagnostics",diagnostics.with("connection_generation",new IntegerValue(current.connectionGeneration()))));
    }
    private static RawJson observation(){
        Obj actualFrame=frame(retained());var fields=new LinkedHashMap<>(actualFrame.members());
        fields.remove("actor_character_id");fields.put("played_character_id",number(12));
        // These are DATA-only extensions used to verify Python key order and ensure_ascii, not Native predicates.
        Obj timeline=new Obj(Map.of("snapshot_revision",new IntegerValue(MAX),"\uE000",new Text("中文\n\"\\"),"\uD800\uDC00",new Text("\uD83D\uDE00")));
        var result=new LinkedHashMap<String,Value>();result.put("schema",new Text("xar.ck3.successor-ui-observation/v1"));result.put("frame",new Obj(fields));
        result.put("exact_ck3_build",new Text("1.20.0.4"));result.put("exe_sha256",new Text("b".repeat(64)));result.put("ui_clearance",new Text("unresolved"));result.put("timeline",timeline);
        result.put("event_instance_id",Nil.INSTANCE);result.put("event_context_status",new Text("not_observed"));result.put("event_definition_key",Nil.INSTANCE);result.put("event_root_scope",Nil.INSTANCE);result.put("event_semantic_decision_ready",Nil.INSTANCE);
        result.put("fresh_timeline_read_after_event_required",new Bool(false));result.put("ordinary_event_policy_unchanged",new Bool(true));result.put("caller_owned_process_and_query_source_proof_required",new Bool(true));
        result.put("authorizes_close_or_save",new Bool(false));result.put("authorizes_event_selection",new Bool(false));result.put("business_cycle_credit",number(0));result.put("action_replay_authorized",new Bool(false));return json(new Obj(result));
    }
    private static ResumeResult result(ColdBindingMaterial actual,ColdBinding binding){
        return new ResumeResult(Status.CLOSE_REQUIRED,true,false,false,currentSnapshot(actual.resumedFrame()),Optional.of(actual.actualTransition()),Optional.of(binding),Optional.empty());
    }

    @Test void originalNoObservationProducerKeepsTheCompleteFourteenFieldBindingAndCanonicalDigest()throws Exception {
        ColdBindingMaterial actual=material(Optional.empty(),resumed());ColdBinding binding=formatColdBinding(actual);Obj numeric=tree(binding.originalNumeric());
        assertEquals(tree(actual.actualTransition().successorEpisodeBinding()),numeric.get("retained_frame"));
        assertEquals(14,object(numeric.get("retained_frame"),"retained frame").members().size());
        assertEquals(new Text(ledger().sha256()),numeric.get("ledger_sha256"));assertEquals(new Bool(true),numeric.get("connection_rebound"));
        assertEquals(originalProducer(actual),numeric);
        RawJson wire=encode(result(actual,binding));Data decoded=decode(wire);
        assertEquals(tree(wire),tree(encode(decoded)));assertEquals(tree(currentSnapshot(resumed())),tree(decoded.originalNumericSnapshot()));
        Obj retained=object(object(tree(wire).get("cold_resume_binding"),"binding").get("retained_frame"),"retained frame");
        assertEquals(Nil.INSTANCE,retained.get("one_life_terminal_reason"));assertTrue(retained.members().containsKey("driver_state_restore_kind"));
        for(String name:COUNTERS)assertInstanceOf(Text.class,retained.get(name));
    }

    @Test void originalObservationProducerKeepsPlayedActorFrameUnicodeAndNullAcrossPublicRoundtrip()throws Exception {
        ColdBindingMaterial actual=material(Optional.of(observation()),resumed());ColdBinding binding=formatColdBinding(actual);
        assertEquals(originalProducer(actual),tree(binding.originalNumeric()));
        Obj retained=object(tree(binding.originalNumeric()).get("retained_frame"),"retained frame");
        assertEquals(8,retained.members().size());assertTrue(retained.members().containsKey("played_character_id"));assertFalse(retained.members().containsKey("actor_character_id"));
        RawJson wire=encode(result(actual,binding));assertEquals(tree(wire),tree(encode(decode(wire))));
        assertEquals(tree(currentSnapshot(resumed())),tree(decode(wire).originalNumericSnapshot()));
        var decimal=tree(observation()).with("timeline",object(tree(observation()).get("timeline"),"timeline").with("unknown_decimal",new DecimalValue("1.0")));
        assertThrows(IllegalArgumentException.class,()->formatColdBinding(material(Optional.of(json(decimal)),resumed())));
    }

    @Test void originalProofUsesRetainedBindingWhileNewConnectionSnapshotHasAnIndependentRevision() {
        var first=material(Optional.empty(),resumed());var laterFrame=new ColdFrame(7,BigInteger.ONE,"newer-frame",BigInteger.TWO,MAX,4,12,"new");
        var second=material(Optional.empty(),laterFrame);Obj original=tree(formatColdBinding(first).originalNumeric()),later=tree(formatColdBinding(second).originalNumeric());
        assertEquals(original.get("transition_sha256"),later.get("transition_sha256"));assertEquals(original.get("retained_frame"),later.get("retained_frame"));
        assertNotEquals(original.get("binding_sha256"),later.get("binding_sha256"));
        var same=material(Optional.empty(),retained());assertEquals(new Bool(false),tree(formatColdBinding(same).originalNumeric()).get("connection_rebound"));
        var wrong=new ColdFrame(7,MAX,"different-retained-frame",MAX,MAX,4,12,"new");
        assertThrows(IllegalArgumentException.class,()->formatColdBinding(new ColdBindingMaterial(transition(),Optional.empty(),wrong,resumed(),first.machineId(),first.sourceEpoch(),game(),ledger(),true)));
    }

    @Test void missingNullWrongTypeNoncanonicalAndDigestChangesCannotBecomeValidPublicColdData() {
        var actual=material(Optional.empty(),resumed());var binding=formatColdBinding(actual);Obj numeric=tree(binding.originalNumeric());
        assertThrows(IllegalArgumentException.class,()->new ColdBinding(json(numeric.with("binding_sha256",new Text("0".repeat(64))))));
        var projected=assertThrows(IllegalArgumentException.class,()->new ColdBinding(json(numeric.with("retained_frame",frame(retained())))));
        assertEquals("original retained cold frame must be a complete successor binding or observation frame",projected.getMessage());
        Obj wire=tree(encode(result(actual,binding))),cold=object(wire.get("cold_resume_binding"),"cold binding");
        Obj originalRetained=object(cold.get("retained_frame"),"retained frame");
        for(Value bad:List.<Value>of(Nil.INSTANCE,new Bool(true),new DecimalValue("1.0"),new Text("01"),new IntegerValue(MAX))) {
            Obj wrong=cold.with("retained_frame",originalRetained.with("revision",bad));
            assertThrows(IllegalArgumentException.class,()->decode(json(wire.with("cold_resume_binding",wrong))));
        }
        var missing=new LinkedHashMap<>(originalRetained.members());missing.remove("one_life_terminal_reason");
        assertThrows(IllegalArgumentException.class,()->decode(json(wire.with("cold_resume_binding",cold.with("retained_frame",new Obj(missing))))));
        assertThrows(IllegalArgumentException.class,()->new ColdFrame(0,MAX,"s",MAX,MAX,4,12,"new"));
        assertThrows(IllegalArgumentException.class,()->new ColdFrame(7,MAX,"s",MAX,BigInteger.ZERO,4,12,"new"));
        assertThrows(IllegalArgumentException.class,()->new ColdFrame(7,MAX,"s",MAX,MAX,-1,12,"new"));
        assertThrows(IllegalArgumentException.class,()->new ColdFrame(7,MAX,"s",MAX,MAX,4,0,"new"));
        assertThrows(IllegalArgumentException.class,()->formatColdBinding(material(Optional.of(RootDriverLifecycleResumeCodecTest.raw("{}")),resumed())));
    }

    /** Exact original pure producer statements are executed after their private ledger gates; only DATA is compared. */
    private static Obj originalProducer(ColdBindingMaterial actual)throws Exception {
        String repository=required("xar.repository.root"),python=required("xar.python");Path root=Path.of(repository);
        Path journal=root.resolve("ck3_autonomous_player/src/xar_autoplayer/successor_ui_pending_ledger_v1.py");
        Path service=root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/verified_successor_ui_service_v1.py");
        var pins=List.of(SharedSourceFiles.observe(journal),SharedSourceFiles.observe(service));
        assertEquals("a448b2d0d2c8ef65ed90aa6059f852e848819dfcdc8c55dbbd5ad7bc0abc1311",pins.get(0).source().sha256());assertEquals("8a5cee33bb36e08e3c0bed68b3a3228235637269a5c57ccc22cb47e161412dd3",pins.get(1).source().sha256());
        var proof=new LinkedHashMap<String,Value>();TransitionMaterial transition=actual.actualTransition();
        proof.put("status",new Text(transition.qualification().wire()));proof.put("predecessor_character_id",number(transition.predecessorCharacterId()));proof.put("successor_character_id",number(transition.successorCharacterId()));
        proof.put("source_episode_run_id",new Text(transition.sourceEpisodeRunId()));proof.put("episode_run_id",new Text(transition.episodeRunId()));proof.put("same_campaign_frame",new Bool(true));proof.put("ck3_command_submitted",new Bool(false));proof.put("process_restarted",new Bool(false));
        proof.put("succession_lifecycle",tree(transition.successionLifecycle()));proof.put("reconciliation",tree(transition.reconciliation()));proof.put("predecessor_binding",tree(transition.predecessorBinding()));proof.put("successor_episode_binding",tree(transition.successorEpisodeBinding()));assertEquals(java.util.Set.copyOf(PROOF),proof.keySet());
        actual.originalObservation().ifPresent(value->proof.put("successor_ui_observation",tree(value)));
        Obj input=new Obj(Map.of("transition",new Obj(proof),"current",frame(actual.resumedFrame()),"old",frame(actual.retainedFrame()),"machine",new Text(actual.machineId()),"epoch",new Text(actual.sourceEpoch().orElseThrow()),
                "game",new Obj(Map.of("pid",number(actual.game().pid()),"creation_date",new Text(actual.game().creationDate()),"executable",new Text(actual.game().executable()))),"pin",new Text(actual.canonicalPendingLedger().sha256())));
        String program="""
            import ast,copy,hashlib,json,pathlib,sys,types
            sys.dont_write_bytecode=True
            root=pathlib.Path(sys.argv[1]);data=json.load(sys.stdin)
            journal=root/'ck3_autonomous_player/src/xar_autoplayer/successor_ui_pending_ledger_v1.py'
            service=root/'ck3_autonomous_player/src/xar_autoplayer/bridge/verified_successor_ui_service_v1.py'
            tree=ast.parse(journal.read_text(encoding='utf-8-sig'));st=ast.parse(service.read_text(encoding='utf-8-sig'))
            proof=next(n for n in st.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PROOF' for t in n.targets))
            scope=dict(hashlib=hashlib,json=json,deepcopy=copy.deepcopy,COLD='xar.ck3.successor-ui-cold-binding/v1')
            exec(compile(ast.Module(body=[proof],type_ignores=[]),str(service),'exec'),scope)
            functions=[copy.deepcopy(n) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('digest','transition_digest')]
            assert len(functions)==2
            for function in functions:
                if function.name=='transition_digest':
                    dependency=[n for n in function.body if isinstance(n,ast.ImportFrom)]
                    assert len(dependency)==1 and dependency[0].module=='bridge.verified_successor_ui_service_v1'
                    function.body=[n for n in function.body if not isinstance(n,ast.ImportFrom)]
            exec(compile(ast.fix_missing_locations(ast.Module(body=functions,type_ignores=[])),str(journal),'exec'),scope)
            owner=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='SuccessorUIPendingLedger')
            load=next(n for n in owner.body if isinstance(n,ast.FunctionDef) and n.name=='load')
            assignments=[]
            for node in load.body:
                if not isinstance(node,ast.Assign):continue
                target=node.targets[0]
                if isinstance(target,ast.Name) and target.id in ('previous','retained','cold'):assignments.append(node)
                elif isinstance(target,ast.Subscript) and isinstance(target.value,ast.Name) and target.value.id=='cold' and isinstance(target.slice,ast.Constant) and target.slice.value=='binding_sha256':assignments.append(node)
            assert len(assignments)==4
            scope.update(transition=data['transition'],current=data['current'],old=data['old'],pin=data['pin'],self=types.SimpleNamespace(machine_id=data['machine'],epoch=data['epoch'],game=data['game']))
            scope['value']={'transition_sha256':scope['transition_digest'](data['transition'])}
            exec(compile(ast.Module(body=assignments,type_ignores=[]),str(journal),'exec'),scope)
            print(json.dumps(scope['cold'],sort_keys=True,separators=(',',':'),allow_nan=False))
            """;
        var builder=new ProcessBuilder(python,"-I","-B","-X","utf8","-c",program,repository).directory(root.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1");Process child=builder.start();
        var output=CompletableFuture.supplyAsync(()->read(child.getInputStream(),1_048_577));var error=CompletableFuture.supplyAsync(()->read(child.getErrorStream(),16_385));
        try {
            try(var stream=child.getOutputStream()){stream.write(DriverJson.encode(input));}
            assertTrue(child.waitFor(30,TimeUnit.SECONDS),"original cold DATA producer timed out");
            byte[] out=output.get(5,TimeUnit.SECONDS),err=error.get(5,TimeUnit.SECONDS);assertTrue(out.length<=1_048_576&&err.length<=16_384);
            assertEquals(0,child.exitValue(),new String(err,StandardCharsets.UTF_8));return DriverJson.object(out,1_048_576);
        }finally{if(child.isAlive()){child.destroyForcibly();child.waitFor(5,TimeUnit.SECONDS);}for(var pin:pins)SharedSourceFiles.assertUnchanged(pin);}
    }
    private static byte[] read(java.io.InputStream stream,int bound){try{return stream.readNBytes(bound);}catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}}
    private static String required(String property){String value=System.getProperty(property);if(value==null||value.isBlank())throw new IllegalStateException("NOT_RUN_REQUIRED_ORIGINAL_INPUT: "+property);return value;}
}
