package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyDeclarationCollection.Scope;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyDeclarationCollection.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Data and producer regressions are synthetic; execution belongs to the actual whole CI step. */
final class ArmyDeclarationCollectionTest {
    private static final Instant TIME = Instant.parse("2026-10-24T00:00:00Z");
    private static final Instant DEADLINE = TIME.plusSeconds(60);
    private static final ExactRef SOURCE = new ExactRef("synthetic-no-game-source",1,"a".repeat(64));
    private static final String ID = "original-fixture";
    @Test void strictFourStatesRoundTripThroughActualPublicIntegerProjection() {
        var actual = complete(true,BigInteger.TWO,"session"); var before = ArmyDeclarationCollectionCodec.binding(actual);
        var current = new Scope(ID,before,before); var staleBinding = changed(before,false,BigInteger.valueOf(3));
        var stale = new Scope(ID,before,staleBinding);
        var successful = packet(true); var rejected = packet(false);
        var choices = org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract.normalize(successful.path("result").path("declarable_wars"));
        var normalized = ((ObjectNode)successful.path("result")).deepCopy();
        normalized.set("declarable_wars",org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract.encode(choices));
        var declarations = new ArmyWarReadCodec.Declarations(choices,UInt64.positive(BigInteger.valueOf(5)),DriverJson.object(ArmyJson.bytes(normalized),DriverJson.MAX_NATIVE_BYTES));
        List<Result> cases = List.of(new Pending(current),new Stale(stale,Optional.empty()),new Stale(stale,Optional.of(raw(successful))),
                new NativeRejected(current,raw(rejected)),new Available(current,raw(successful),declarations));
        var context = new Context(actual.identity(),actual.source(),actual.sessionId(),DEADLINE);
        for (Result value : cases) {
            var original = ArmyDeclarationCollectionCodec.encode(value);
            var held=value instanceof Stale?complete(false,BigInteger.valueOf(3),"session"):actual;
            var wire=ArmyWarReadService.encodeCollection(new Reply(held,DEADLINE,value));
            var decoded = ArmyDeclarationCollectionCodec.decode(ArmyPublicWire.decodeExactSourceBound(wire,context));
            assertEquals(value.status(),decoded.status()); assertEquals(original,ArmyDeclarationCollectionCodec.encode(decoded));
            var n = ArmyJson.parse(wire.bytes()); assertFalse(n.path("native_resubmitted").booleanValue());
            assertFalse(n.has("queried_snapshot_id"));assertFalse(n.has("queried_revision"));assertFalse(n.has("queried_native_revision"));
            assertEquals(value instanceof Available,n.path("cache_restored").booleanValue());
            assertTrue(n.path("original_binding").path("connection_generation").isTextual());
        }
        assertEquals("18446744073709551615",ArmyJson.parse(ArmyWarReadService.encodeCollection(new Reply(actual,DEADLINE,cases.getFirst())).bytes())
                .path("original_binding").path("connection_generation").textValue());
    }
    @Test void malformedStatesFieldsTypesOrOriginalFramesDoNotBecomeAvailable() {
        var complete = complete(true,BigInteger.TWO,"session"); var binding = ArmyDeclarationCollectionCodec.binding(complete);
        var original = ArmyJson.object(OpportunityJson.toNode(ArmyDeclarationCollectionCodec.encode(new Pending(new Scope(ID,binding,binding)))));
        for (String field : List.of("schema","request_id","status","original_binding","current_binding","native_resubmitted","cache_restored")) {
            var missing = original.deepCopy(); missing.remove(field); assertThrows(IllegalArgumentException.class,() -> decode(missing));
        }
        var invalid = original.deepCopy().put("status","complete"); assertThrows(IllegalArgumentException.class,() -> decode(invalid));
        var resubmitted = original.deepCopy().put("native_resubmitted",true); assertThrows(IllegalArgumentException.class,() -> decode(resubmitted));
        var fakeRestored = original.deepCopy().put("cache_restored",true); assertThrows(IllegalArgumentException.class,() -> decode(fakeRestored));
        var invented = original.deepCopy().put("result_frame","private-custody"); assertThrows(IllegalArgumentException.class,() -> decode(invented));
        var wrongType = original.deepCopy(); ((ObjectNode)wrongType.path("current_binding")).put("native_revision",true);
        assertThrows(IllegalArgumentException.class,() -> decode(wrongType));
        var rounded = original.deepCopy(); ((ObjectNode)rounded.path("current_binding")).put("connection_generation",18446744073709551615.0);
        assertThrows(IllegalArgumentException.class,() -> decode(rounded));
        var same = new Scope(ID,binding,binding);
        assertThrows(IllegalArgumentException.class,() -> new Stale(same,Optional.empty()));
        assertThrows(IllegalArgumentException.class,() -> new NativeRejected(same,raw(packet(true))));
        assertThrows(IllegalArgumentException.class,() -> new NativeRejected(same,raw(packet(false).put("request_id","other-original"))));
        assertThrows(IllegalArgumentException.class,() -> Status.fromWire("native_rejected"));
    }
    @Test void unpausedCompleteCanReportStaleAndNeverPretendsToBeAnOrdinaryPausedSelection() {
        var before = ArmyDeclarationCollectionCodec.binding(complete(true,BigInteger.TWO,"session"));
        var actual = complete(false,BigInteger.valueOf(3),"session"); var current = ArmyDeclarationCollectionCodec.binding(actual);
        var reply = new Reply(actual,DEADLINE,new Stale(new Scope(ID,before,current),Optional.empty()));
        assertEquals(reply.result(),ArmyDeclarationCollectionCodec.decode(ArmyPublicWire.decodeExactSourceBound(ArmyWarReadService.encodeCollection(reply),reply.context())));
        assertEquals(Status.STALE,reply.result().status());
        assertThrows(IllegalArgumentException.class,() -> new ArmyRetreatFrames.Current(actual,DEADLINE));
        assertThrows(IllegalArgumentException.class,() -> new Reply(complete(true,BigInteger.TWO,"session"),DEADLINE,reply.result()));
    }
    @Test void pinnedOriginalPythonCollectorRetainsPoppedMalformedFrameAndMatchesFourStateContract(@org.junit.jupiter.api.io.TempDir java.nio.file.Path temporary) throws Exception {
        var input=ArmyJson.empty();input.set("original",OpportunityJson.toNode(complete(true,BigInteger.TWO,"session").semantic()));
        var rows=input.putArray("rows");
        for(String mode:List.of("pending","stale","native-rejected","available","malformed")) {
            var row=rows.addObject().put("mode",mode);
            row.set("current",OpportunityJson.toNode(complete(!mode.equals("stale"),mode.equals("stale")?BigInteger.valueOf(3):BigInteger.TWO,"session").semantic()));
            if(!mode.equals("pending")) {
                var frame=packet(!mode.equals("native-rejected"));
                if(mode.equals("malformed"))((ObjectNode)frame.path("result")).put("query_sequence",true);
                row.set("frame",frame);
            }
        }
        String python=required("xar.native.producer.python"),source=required("xar.native.producer.source");
        for(String path:List.of(python,source))if(!java.nio.file.Path.of(path).isAbsolute())throw new IllegalArgumentException("original producer properties require absolute paths");
        var output=temporary.resolve("collection.json");var error=temporary.resolve("collection.stderr");
        var child=new ProcessBuilder(python,"-X","utf8","-c",ORIGINAL_COLLECT,source,java.util.Base64.getEncoder().encodeToString(ArmyJson.bytes(input)))
                .redirectOutput(output.toFile()).redirectError(error.toFile()).start();
        if(!child.waitFor(20,java.util.concurrent.TimeUnit.SECONDS)){child.destroyForcibly();throw new java.io.IOException("original collection process timeout");}
        if(child.exitValue()!=0)throw new java.io.IOException("original collection failed: "+java.nio.file.Files.readString(error));
        var actual=ArmyJson.parse(java.nio.file.Files.readAllBytes(output));
        for(String mode:List.of("pending","stale","native-rejected","available")) {
            var observed=ArmyJson.object(actual.get(mode));var response=ArmyJson.object(observed.get("response"));
            assertEquals(mode,response.path("status").textValue());assertFalse(response.path("native_resubmitted").booleanValue());
            assertEquals(mode.equals("available"),response.path("cache_restored").booleanValue());
            var decoded=decode(response);assertEquals(DriverJson.object(ArmyJson.bytes(response),DriverJson.MAX_NATIVE_BYTES),ArmyDeclarationCollectionCodec.encode(decoded));
            assertEquals(1,observed.path("polls").intValue());assertEquals(mode.equals("pending"),observed.path("pending").booleanValue());
        }
        assertTrue(actual.path("malformed").path("retained").booleanValue());assertEquals(1,actual.path("malformed").path("polls").intValue());
        assertEquals(2,actual.path("malformed").path("failures").intValue());
    }
    private static String required(String key) {
        String value=System.getProperty(key);if(value==null||value.isBlank())throw new IllegalStateException("NOT EXECUTED: required original collector property missing: "+key);return value;
    }
    private static final String ORIGINAL_COLLECT="""
        import ast,base64,copy,hashlib,json,sys,threading,types
        from pathlib import Path
        def pinned(path,sha):
            p=Path(path)
            raw=p.read_bytes()
            if len(raw)>2*1024*1024 or hashlib.sha256(raw).hexdigest()!=sha:raise RuntimeError('original source drift')
            parsed=ast.parse(raw.decode('utf-8-sig'))
            if p.read_bytes()!=raw:raise RuntimeError('original source changed while parsing')
            return parsed
        tree=pinned(sys.argv[1],'eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603')
        imported=next(x for x in tree.body if isinstance(x,ast.ImportFrom) and x.level==1 and x.module=='declaration_contract' and any(y.name=='normalize_declarable_wars' for y in x.names))
        declarations=pinned(Path(sys.argv[1]).parent/(imported.module+'.py'),'b5ed2eb40f8f52298886d764259501559a551b4096ecaa839e39fa45a12e151c')
        scope={'copy':copy,'BridgeUnavailableError':RuntimeError,'QUERY_DECLARABLE_WARS_STEP':'query-declarable-wars'}
        def load(node):
            node.decorator_list=[]
            exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),sys.argv[1],'exec'),scope)
            return scope[node.name]
        for node in declarations.body:
            if isinstance(node,ast.FunctionDef):load(node)
        load(next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='_validate_revision'))
        cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='NativeHeadlessGameplayDriver')
        methods={name:load(next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name==name)) for name in ('_declaration_result_binding','_publish_declarable_war_result','collect_declarable_wars_result_v1')}
        data=json.loads(base64.b64decode(sys.argv[2]));out={}
        for row in data['rows']:
            owner=types.SimpleNamespace(_driver_state_lock=threading.RLock())
            owner.take_snapshot_without_native_command_history=lambda:copy.deepcopy(row['current'])
            owner._declaration_result_binding=methods['_declaration_result_binding']
            owner._publish_declarable_war_result=types.MethodType(methods['_publish_declarable_war_result'],owner)
            owner._pending_declaration_query={'request_id':'original-fixture','step':'query-declarable-wars','binding':methods['_declaration_result_binding'](data['original'])}
            queue=[copy.deepcopy(row.get('frame'))];count=[0]
            def poll(request_id,timeout):
                if request_id!='original-fixture' or timeout!=0.0:raise RuntimeError('collector replayed or changed original request')
                count[0]+=1
                return queue.pop(0) if queue else None
            owner.state=types.SimpleNamespace(wait_for_command_result=poll)
            if row['mode']=='malformed':
                failures=0
                for _ in range(2):
                    try:methods['collect_declarable_wars_result_v1'](owner,'original-fixture',expected_revision=row['current']['revision'])
                    except RuntimeError:failures+=1
                out[row['mode']]={'retained':owner._pending_declaration_query.get('result_frame')==row['frame'],'polls':count[0],'failures':failures}
            else:
                response=methods['collect_declarable_wars_result_v1'](owner,'original-fixture',expected_revision=row['current']['revision'])
                out[row['mode']]={'response':response,'polls':count[0],'pending':owner._pending_declaration_query is not None}
        print(json.dumps(out,separators=(',',':')))
        """;
    private static Result decode(ObjectNode value) { return ArmyDeclarationCollectionCodec.decode(DriverJson.object(ArmyJson.bytes(value),DriverJson.MAX_NATIVE_BYTES)); }
    private static Binding changed(Binding before,boolean paused,BigInteger revision) {
        return new Binding(before.snapshotId(),revision,before.nativeRevision(),before.episode(),before.dateRaw(),paused,before.mapReady(),before.playerCharacterId(),before.bridgePid(),before.connectionGeneration());
    }
    private static RawJson raw(ObjectNode n) { return new RawJson(ArmyJson.bytes(n)); }
    private static ObjectNode packet(boolean ok) {
        ObjectNode n = ArmyJson.empty().put("type","command_result").put("protocol_version",1).put("request_id",ID).put("ok",ok);
        if (!ok) { n.put("error","native rejected original"); return n; }
        ObjectNode r = n.putObject("result").put("step","query-declarable-wars").put("accepted",true).put("status","available").put("query_sequence",5).put("snapshot_revision",3);
        ObjectNode choice = r.putArray("declarable_wars").addObject().put("declaration_id","202-0--1").put("target_character_id",202).put("casus_belli_index",0)
                .put("casus_belli_key","claim_cb").put("configuration_index",-1).put("claimant_character_id",-1);
        choice.putArray("target_title_ids").add(0).add(17); return n;
    }
    private static Complete complete(boolean paused,BigInteger revision,String session) {
        BigInteger connection = new BigInteger("18446744073709551615");
        var source = new G2Source("synthetic-no-game",TIME.toString(),"1.20.0.4",SOURCE);
        var key = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(101),BigInteger.valueOf(3),BigInteger.valueOf(77)),"native:3",revision,"collection-fixture");
        var identity = new ObservationIdentity(source.machineId(),new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),key,1);
        ObjectNode n = ArmyJson.empty().put("paused",paused).put("map_ready",true).put("snapshot_id","native:3").put("revision",revision).put("native_revision",3)
                .put("date_raw",77).put("episode_run_id","collection-fixture");
        n.putObject("played_character").put("character_id",101).put("alive",true);
        n.putObject("diagnostics").put("bridge_pid",42).put("connection_generation",connection);
        return new Complete(identity,source,session,connection,DriverJson.object(ArmyJson.bytes(n),DriverJson.MAX_NATIVE_BYTES),SOURCE,TIME,"b".repeat(64));
    }
}
