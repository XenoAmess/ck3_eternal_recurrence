package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.CombatProjectionJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.military.combatwire.phaseevent.StockPhaseManifest;
import org.xar.ck3.control.wave2.military.forecast.CombatObservationCache;
import org.xar.ck3.control.wave2.military.forecast.CurrentBattleConditionCodec;

/** Real original producer differentials over explicitly synthetic inputs. No test qualifies a physical Game. */
final class CombatPublicProjectionOriginalTest {
    @TempDir Path temporary;
    @Test void currentSpecialKnightCalculationMatchesTheActualOriginalServiceReturn()throws Exception {
        JsonNode result=original("special",obj());
        var base=immutable(object(result.get("base")));var provenance=immutable(object(result.get("provenance")));
        var actual=CombatPublicProjection.specialInitial(base,provenance);
        assertEquals(result.get("expected"),node(actual));
        assertEquals(actual,DriverJson.object(OpportunityJson.encode(actual),DriverJson.MAX_NATIVE_BYTES));
        assertTrue(node(actual).get("observed_member_count").intValue()>0);
        assertFalse(yes(node(actual).get("native_write_performed")));
    }
    @Test void signedMaximumMultiplyAndZeroMissingOperandsMatchOriginalKernel()throws Exception {
        var input=obj();var pairs=input.putArray("pairs");for(long[] p:new long[][]{{0,Long.MIN_VALUE},{-3037000500L,3037000500L},{Long.MIN_VALUE,Long.MAX_VALUE},{Long.MAX_VALUE,Long.MAX_VALUE},{-100001,200003},{3037000499L,-3037000499L}})pairs.addArray().add(p[0]).add(p[1]);
        var expected=original("multiply",input);for(int i=0;i<pairs.size();i++)assertEquals(integer(expected.get(i)),CombatKnightKernel.fixedMultiply(integer(pairs.get(i).get(0)),integer(pairs.get(i).get(1))));
        var zero=new CombatKnightKernel.Input(Optional.of(BigInteger.ONE),Optional.of(BigInteger.valueOf(-5)),"fixture",Optional.of(BigInteger.TWO),"fixture",new CombatKnightKernel.PropertyContainer(Optional.empty(),Optional.empty(),Optional.empty()),java.util.Collections.nCopies(9,Optional.of(BigInteger.ZERO)),Optional.of(BigInteger.valueOf(50)),Optional.of(BigInteger.TEN),immutable(obj()),immutable(obj()));
        var computed=CombatKnightKernel.compute(zero);assertTrue(computed.ready());assertEquals(BigInteger.valueOf(5000000),integer(node(computed.statCache().orElseThrow()).get("effective_damage_raw")));
        var missing=new CombatKnightKernel.Input(zero.linkedCharacter(),zero.prowess(),zero.linkedStage(),zero.selectedCharacter(),zero.selectedStage(),zero.context(),List.of(Optional.of(BigInteger.ONE)),zero.damageMultiplier(),zero.toughnessMultiplier(),zero.selectedSource(),zero.externalSource());
        assertFalse(CombatKnightKernel.compute(missing).ready());assertTrue(CombatKnightKernel.compute(missing).statCache().isEmpty());
    }
    @Test void retainedWholeKnightPacketMatchesOriginalConsumptionIncludingOwnedBranches()throws Exception {
        Path packet=Path.of(required("xar.combat.public.knight.packet"));assertTrue(packet.isAbsolute());byte[] raw=Files.readAllBytes(packet);assertTrue(raw.length>0&&raw.length<=4<<20);
        String sha=HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(raw));assertEquals(required("xar.combat.public.knight.packet.sha256"),sha);
        var input=obj().put("packet",packet.toString()).put("sha256",sha);var expected=original("consumption",input);
        var frame=FullJsonTree.parse(raw,4<<20);JsonNode leaf=frame.get("result").get("combat_simulation_inputs").get("knight_stat_consumption_v1");
        var actual=CombatKnightConsumption.project(leaf).orElseThrow();assertEquals(expected,node(actual));
        assertEquals(actual,DriverJson.object(OpportunityJson.encode(actual),DriverJson.MAX_NATIVE_BYTES));
    }
    @Test void actualOriginalManagedFilesProofMatchesAndTamperingCannotMintEvidence()throws Exception {
        JsonNode fixture=original("managed-fixture",obj().put("directory",temporary.resolve("proof").toString()));
        Complete complete=complete(object(fixture.get("snapshot")));var definition=definition(fixture.get("definition"));Path state=Path.of(text(fixture.get("state_dir")));
        var proof=CombatLoadedPlaysetProof.projectOriginalFiles(state,complete,definition);assertEquals(fixture.get("expected"),node(proof));
        assertEquals(proof,DriverJson.object(OpportunityJson.encode(proof),DriverJson.MAX_NATIVE_BYTES));
        Path stock=Path.of(text(fixture.get("first_stock_file")));Files.writeString(stock,"actual fixture corruption");
        assertThrows(IllegalArgumentException.class,()->CombatLoadedPlaysetProof.projectOriginalFiles(state,complete,definition));
        var checked=original("managed-check",object(fixture));assertTrue(yes(checked.get("rejected")));
        // The test-input seam returns JSON only; it has no constructor or conversion to private Evidence.
        for(var constructor:CombatLoadedPlaysetProof.Evidence.class.getDeclaredConstructors())assertTrue(java.lang.reflect.Modifier.isPrivate(constructor.getModifiers()));
    }
    @Test void originalPhysicalWriterRecordJoinsTheActualCurrentConditionAdapterWithoutReplacingStats()throws Exception {
        Path packet=Path.of(required("xar.combat.public.knight.packet"));byte[] raw=Files.readAllBytes(packet);String sha=HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(raw));assertEquals(required("xar.combat.public.knight.packet.sha256"),sha);
        JsonNode fixture=original("physical",obj().put("packet",packet.toString()).put("sha256",sha));
        var condition=CurrentBattleConditionCodec.adapt(fixture.get("control"));var projected=immutable(object(fixture.get("consumption")));
        var frame=new CombatObservationCache.Frame("synthetic-physical-source",BigInteger.ONE,integer(fixture.get("native_revision")),BigInteger.ONE,"synthetic-physical-episode",integer(fixture.get("date_raw")));
        var actual=CombatPublicProjection.physical(condition,Optional.of(projected),frame);assertEquals(fixture.get("expected"),node(actual));
        assertFalse(yes(node(actual).get("fresh_condition_modified")));assertEquals(actual,DriverJson.object(OpportunityJson.encode(actual),DriverJson.MAX_NATIVE_BYTES));
    }
    @Test void explicitNoManagedStateProofMatchesOriginalCanonicalDigestAndCannotClaimLoaded()throws Exception {
        var input=obj().put("episode","原始episode").put("reason","managed_state_dir_unavailable");var expected=original("unavailable",input);
        var actual=CombatLoadedPlaysetProof.negativeForEpisode(Optional.of(text(input.get("episode"))),text(input.get("reason")));
        assertEquals(expected,node(actual));assertFalse(yes(node(actual).path("claims").get("loaded_playset_verified")));
    }
    @Test void originalProofDigestsKeepRecursiveOrderUnicodeControlsAndAsciiEscapes()throws Exception {
        var value=obj().put("z",true).putNull("none").put("a","quote\" slash\\ \b\f\n\r\t\u0001\u001a é中😀");
        value.putObject("nested").put("z",BigInteger.ONE.shiftLeft(140)).put("a",false);
        value.putArray("array").add(2).addNull().addObject().put("z","é").put("a",false);
        var expected=original("proof-digests",obj().set("value",value));
        assertEquals(text(expected.get("unicode")),proofDigest(value,false));
        assertEquals(text(expected.get("ascii")),proofDigest(value,true));
        var reordered=obj();reordered.set("array",value.get("array"));
        reordered.putObject("nested").put("a",false).put("z",BigInteger.ONE.shiftLeft(140));
        reordered.put("a",text(value.get("a"))).putNull("none").put("z",true);
        assertEquals(proofDigest(value,false),proofDigest(reordered,false));
        assertEquals(proofDigest(value,true),proofDigest(reordered,true));
    }
    @Test void fullMaterialReaderAndDigestAcceptAggregateAboveTheReceiptLaneWithoutTruncation()throws Exception {
        var value=obj();var rows=value.putArray("entries");
        for(int i=0;i<48;i++)rows.add("x".repeat(24_000));
        byte[] raw=FullJsonTree.encode(value,FullJsonTree.MAXIMUM_BYTES);
        assertTrue(raw.length>StrictJson.EXPLICIT_MAX_BYTES&&raw.length<2<<20);
        Path originalPath=temporary.resolve("aggregate-proof-input.json");Files.write(originalPath,raw);
        assertArrayEquals(raw,FullJsonTree.encode(proofRead(originalPath),FullJsonTree.MAXIMUM_BYTES));
        var expected=original("proof-digests",obj().set("value",value));
        assertEquals(text(expected.get("unicode")),proofDigest(value,false));
        assertEquals(text(expected.get("ascii")),proofDigest(value,true));
    }
    @Test void fullMaterialLaneDoesNotWidenTheOriginalIntegerOnlyDigestContract()throws Exception {
        var value=obj();value.set("fraction",FullJsonTree.parse("1.0".getBytes(java.nio.charset.StandardCharsets.UTF_8),32));
        var thrown=assertThrows(java.lang.reflect.InvocationTargetException.class,()->proofDigest(value,false));
        assertInstanceOf(IllegalArgumentException.class,thrown.getCause());
    }
    // These calls exercise the actual private serializer/parser without minting Evidence or broadening its API.
    private static String proofDigest(ObjectNode value,boolean ascii)throws Exception {
        var method=CombatLoadedPlaysetProof.class.getDeclaredMethod("digest",ObjectNode.class,boolean.class);method.setAccessible(true);
        return assertInstanceOf(String.class,method.invoke(null,value,ascii));
    }
    private static ObjectNode proofRead(Path path)throws Exception {
        var method=CombatLoadedPlaysetProof.class.getDeclaredMethod("read",Path.class);method.setAccessible(true);
        return assertInstanceOf(ObjectNode.class,method.invoke(null,path));
    }
    private JsonNode original(String mode,ObjectNode input)throws Exception {
        Path repo=Path.of(required("xar.repository.root"));String python=required("xar.python");assertTrue(repo.isAbsolute()&&Path.of(python).isAbsolute());
        Path out=temporary.resolve(mode+".json"),err=temporary.resolve(mode+".stderr");var process=new ProcessBuilder(python,"-X","utf8","-c",ORIGINAL,repo.toString(),mode).redirectOutput(out.toFile()).redirectError(err.toFile()).start();
        try(var stdin=process.getOutputStream()){stdin.write(FullJsonTree.encode(input,4<<20));}
        if(!process.waitFor(30,TimeUnit.SECONDS)){process.destroyForcibly();throw new IOException("original public combat differential timeout");}
        if(process.exitValue()!=0)throw new IOException("original public combat producer failed: "+Files.readString(err));
        return FullJsonTree.parse(Files.readAllBytes(out),4<<20);
    }
    private static String required(String key){String value=System.getProperty(key);if(value==null||value.isBlank())throw new IllegalStateException("NOT_RUN: actual original combat input property missing: "+key);return value;}
    private static CombatLoadedPlaysetProof.Definition definition(JsonNode n){List<StockPhaseManifest.Source> files=new ArrayList<>(),feedback=new ArrayList<>();for(JsonNode row:n.get("files"))files.add(source(row));for(JsonNode row:n.get("feedback"))feedback.add(source(row));return new CombatLoadedPlaysetProof.Definition(text(n.get("sha")),text(n.get("version")),text(n.get("executable_sha")),files,feedback);}
    private static StockPhaseManifest.Source source(JsonNode n){return new StockPhaseManifest.Source(text(n.get("relative_path")),text(n.get("sha256")),integer(n.get("load_order")).intValueExact());}
    private static Complete complete(ObjectNode n){Instant now=Instant.parse("2026-10-24T00:00:00Z");var ref=new ExactRef("synthetic-proof-test-source",1,"a".repeat(64));var source=new G2Source("synthetic-no-game",now.toString(),"fixture",ref);var identity=new ObservationIdentity(source.machineId(),new GameGeneration(4343,new PythonOnlyUInt64(BigInteger.ONE)),new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(707),integer(n.get("native_revision")),BigInteger.ZERO),text(n.get("snapshot_id")),integer(n.get("revision")),text(n.get("episode_run_id"))),1);return new Complete(identity,source,"synthetic-proof-session",BigInteger.ONE,immutable(n),ref,now,"b".repeat(64));}
    private static final String ORIGINAL="""
        import sys,json,hashlib
        from pathlib import Path
        from dataclasses import asdict,replace
        root=Path(sys.argv[1]);src=root/'ck3_autonomous_player'/'src';tests=root/'ck3_autonomous_player'/'tests'/'unit'
        sys.path[:0]=[str(src),str(tests),str(tests.parent)]
        pins={'simulation/knight_stat_consumption_12004.py':'35971f35987406bb08ac7b2a28a17663b210133c72dbfb01f9de3cb373e1a17d','simulation/battle_current_special_knight_value_12003.py':'f73d8c2caf4aa70f1ec5f11ae03caebbd159e816c9ff360bef37f93505386578','simulation/battle_first_contact_final_stat_refresh_12003.py':'cbe2ce88600baea8285c004ece78edb7d9c2c5e00c05e50bb66dcc75eb33b279','simulation/battle_trait_numeric_inputs_12003.py':'ae974dd51678fec9f05ea40c4991de30678ca356d30df298b97b88bb92a1810a','simulation/loaded_playset_proof.py':'8104c44d1dab7fc865296fc97e013bfcd814e65ed88ce687143e0d4d17ea38c7','bridge/service.py':'a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e'}
        for name,sha in pins.items():
            if hashlib.sha256((src/'xar_autoplayer'/name).read_bytes()).hexdigest()!=sha:raise RuntimeError('actual original public combat source drift: '+name)
        q=json.load(sys.stdin);mode=sys.argv[2]
        if mode=='special':
            from test_combat_v3_special_knight_value_service import current_knight_service_source,ExactCurrentKnightDriver
            from xar_autoplayer.bridge.service import GameplayBridgeService
            result=GameplayBridgeService(ExactCurrentKnightDriver(current_knight_service_source())).query_combat_simulation_inputs_v3(2596,2597,[357,33554657],[83886341],expected_revision=4)
            expected=result['current_special_knight_initial_value'];value={'base':result['combat_simulation_inputs']['base_inputs'],'provenance':expected['source_provenance'],'expected':expected}
        elif mode=='multiply':
            from xar_autoplayer.simulation.battle_first_contact_final_stat_refresh_12003 import knight_effectiveness_fixed_mul_12003
            value=[knight_effectiveness_fixed_mul_12003(a,b) for a,b in q['pairs']]
        elif mode=='consumption':
            from xar_autoplayer.simulation.knight_stat_consumption_12004 import project_knight_stat_consumption_12004
            raw=Path(q['packet']).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=q['sha256']:raise RuntimeError('actual original knight packet drift')
            packet=json.loads(raw);value=project_knight_stat_consumption_12004(packet['result']['combat_simulation_inputs']['knight_stat_consumption_v1'])
        elif mode=='physical':
            from xar_autoplayer.simulation.knight_stat_consumption_12004 import project_knight_stat_consumption_12004
            from xar_autoplayer.simulation.battle_current_knight_entry_refresh import associate_current_physical_entry_writebacks_12004
            from test_current_physical_entry_writeback_join_12004 import _synthetic_current_context,NATIVE_REVISION,DATE_RAW
            raw=Path(q['packet']).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=q['sha256']:raise RuntimeError('original physical packet drift')
            packet=json.loads(raw);consumed=project_knight_stat_consumption_12004(packet['result']['combat_simulation_inputs']['knight_stat_consumption_v1']);physical=consumed['events'][0]['physical_entry_writeback']
            if physical is None:raise RuntimeError('NOT_RUN: the actual physical writer packet is required for this whole join')
            raw_control,control,refreshed=_synthetic_current_context(physical['entry_identity']);coordinates={'native_revision':NATIVE_REVISION,'date_raw':DATE_RAW}
            expected=associate_current_physical_entry_writebacks_12004(refreshed.condition,consumed,combat_query_source=coordinates,control_query_source=coordinates)
            value={'control':control,'consumption':consumed,'native_revision':NATIVE_REVISION,'date_raw':DATE_RAW,'expected':expected}
        elif mode=='managed-fixture':
            from test_loaded_playset_proof import _ManagedPlaysetFixture
            f=_ManagedPlaysetFixture(Path(q['directory']));proof=f.build();snapshot={**f.snapshot_binding,'episode_run_id':f.episode_run_id,'paused':True,'map_ready':True,'date_raw':0,'diagnostics':{'hello':f.hello,'connection_generation':1},'played_character':{'character_id':707,'alive':True}}
            definition={'sha':f.manifest.canonical_manifest_sha256,'version':f.manifest.game_version,'executable_sha':f.manifest.executable_sha256,'files':[asdict(s) for s in f.manifest.files],'feedback':[asdict(s) for s in f.accolade_sources]}
            value={'state_dir':str(f.state_dir),'snapshot':snapshot,'definition':definition,'expected':proof,'first_stock_file':str(f.game_dir/'game'/f.manifest.files[0].relative_path)}
        elif mode=='managed-check':
            from xar_autoplayer.simulation.phase_event_manifest import load_stock_phase_event_manifest,FrozenPhaseEventSource
            from xar_autoplayer.simulation.loaded_playset_proof import build_loaded_playset_proof,LoadedPlaysetProofError
            d=q['definition'];manifest=replace(load_stock_phase_event_manifest(),executable_sha256=d['executable_sha'],files=tuple(FrozenPhaseEventSource(**s) for s in d['files']));n=q['snapshot']
            try:build_loaded_playset_proof(q['state_dir'],episode_run_id=n['episode_run_id'],snapshot_binding={k:n[k] for k in ('snapshot_id','revision','native_revision')},native_hello=n['diagnostics']['hello'],_manifest=manifest,_accolade_sources=tuple(FrozenPhaseEventSource(**s) for s in d['feedback']));value={'rejected':False}
            except LoadedPlaysetProofError:value={'rejected':True}
        elif mode=='proof-digests':
            from xar_autoplayer.simulation.loaded_playset_proof import _proof_digest
            from xar_autoplayer.environment import snapshot_digest
            value={'unicode':_proof_digest(q['value']).lower(),'ascii':snapshot_digest(q['value'])}
        elif mode=='unavailable':
            from xar_autoplayer.simulation.loaded_playset_proof import unavailable_loaded_playset_proof
            value=unavailable_loaded_playset_proof(episode_run_id=q['episode'],reason=q['reason'])
        else:raise RuntimeError('unknown original combat test mode')
        print(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')))
        """;
}
