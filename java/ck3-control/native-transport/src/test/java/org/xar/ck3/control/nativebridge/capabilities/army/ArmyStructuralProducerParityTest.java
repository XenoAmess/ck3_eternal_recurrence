package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;

/** Executes the three unchanged original method branches in an independent Python process, test-only. */
final class ArmyStructuralProducerParityTest {
    @TempDir Path temporary;
    private static final String DRIVER_SHA="eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603";
    private static final String WAR_SHA="b1b14953f01d66c9f6720e4c92cb6b30c26eb1946b20e9b4ba932c9b5e1f7937";
    private static final String ORIGINAL="""
        import ast, copy, hashlib, json, pathlib, sys
        anchor=pathlib.Path(sys.argv[1]); expected=sys.argv[2]
        assert hashlib.sha256(anchor.read_bytes()).hexdigest()==expected
        sys.path.insert(0,str(anchor.parents[2]))
        from xar_autoplayer.bridge.war_contract import parse_halt_army_step, parse_split_army_half_step, parse_merge_armies_step, controllable_armies
        class BridgeUnavailableError(Exception): pass
        tree=ast.parse(anchor.read_text(encoding='utf-8-sig'),filename=str(anchor))
        helper_names={'_NativeCommandRejectedError','_date_raw','_army_by_id','_controllable_army_ids','_army_known_merge_blocked','_army_in_combat_or_retreat','_positive_native_id'}
        helpers=[node for node in tree.body if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name in helper_names]
        assert len(helpers)==len(helper_names)
        method=next(node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name=='_execute_native_war_step')
        branch_parsers={'parse_split_army_half_step','parse_merge_armies_step','parse_halt_army_step'}
        branches=[]
        for index,node in enumerate(method.body):
            if isinstance(node,ast.Assign) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id in branch_parsers:
                assert isinstance(method.body[index+1],ast.If)
                branches.extend([node,method.body[index+1]])
        assert len(branches)==6
        run=ast.parse('def run(self, step, starting, selected_revision): pass').body[0]
        run.body=branches+[ast.parse("raise ValueError('not one of the three original branches')").body[0]]
        module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)]+helpers+[run],type_ignores=[])
        scope=globals();scope['_MERGE_POSTCONDITION_WAIT_SECONDS']=3.0
        exec(compile(ast.fix_missing_locations(module),str(anchor),'exec'),scope)
        class Fixture:
            command_timeout_seconds=1.0
            def __init__(self,row): self.row=row; self.calls=0; self.snapshots=0
            def _execute_primitive_step(self,step,expected_revision):
                self.calls+=1
                assert step==self.row['step'] and expected_revision==self.row['before']['revision']
                if self.row['deferred']:
                    raise _NativeCommandRejectedError(self.row['response']['error'],native_request_id='original-request',native_request_frame=self.row['request'],native_command_result_frame=self.row['response'])
                return copy.deepcopy(self.row['primitive'])
            def take_snapshot(self): self.snapshots+=1; return copy.deepcopy(self.row['after'])
            def _wait_for_snapshot(self,observed,predicate,timeout_seconds):
                assert 0<timeout_seconds<=3.0
                return copy.deepcopy(self.row['after'])
        rows=json.loads(pathlib.Path(sys.argv[3]).read_bytes()); results=[]
        for row in rows:
            fixture=Fixture(row)
            try: results.append({'ok':True,'value':run(fixture,row['step'],copy.deepcopy(row['before']),row['before']['revision']),'primitive_calls':fixture.calls,'snapshot_calls':fixture.snapshots})
            except (BridgeUnavailableError,ValueError) as error: results.append({'ok':False,'error_type':type(error).__name__,'message':str(error),'primitive_calls':fixture.calls,'snapshot_calls':fixture.snapshots})
        assert hashlib.sha256(anchor.read_bytes()).hexdigest()==expected
        print(json.dumps(results,separators=(',',':'),ensure_ascii=True))
        """;
    private static Obj input(String step,Obj before,Obj after,boolean deferred,Obj response) {
        var call=ArmyStructuralActionsTest.call(step);
        return new Obj(Map.of("step",new Text(step),"before",before,"after",after,"deferred",new Bool(deferred),
                "primitive",DriverJson.object(ArmyStructuralActionsTest.primitive(call).bytes(),DriverJson.MAX_NATIVE_BYTES),
                "request",ArmyStructuralActionsTest.request(step),"response",response));
    }
    private Arr original(List<Obj> rows)throws Exception {
        Path python=Path.of(required("xar.native.producer.python")),anchor=Path.of(required("xar.native.producer.source"));
        assertTrue(python.isAbsolute()&&Files.isRegularFile(python),"mandatory original Python executable");
        assertTrue(anchor.isAbsolute()&&Files.isRegularFile(anchor),"mandatory original native producer source");
        assertEquals(DRIVER_SHA,required("xar.native.producer.sha256"));byte[] source=Files.readAllBytes(anchor);
        assertEquals(1658471,source.length);assertEquals(DRIVER_SHA,DriverJson.sha256(source));
        Path war=anchor.resolveSibling("war_contract.py");byte[] warBytes=Files.readAllBytes(war);assertEquals(WAR_SHA,DriverJson.sha256(warBytes));
        Path input=temporary.resolve("original-structural-input.json"),output=temporary.resolve("original-structural-output.json"),error=temporary.resolve("original-structural-error.txt");
        Files.write(input,DriverJson.encode(new Arr(new ArrayList<Value>(rows))));
        Process process=new ProcessBuilder(python.toString(),"-B","-X","utf8","-c",ORIGINAL,anchor.toString(),DRIVER_SHA,input.toString())
                .redirectOutput(output.toFile()).redirectError(error.toFile()).start();
        if(!process.waitFor(30,TimeUnit.SECONDS)){process.destroyForcibly();throw new IOException("original structural producer timed out; not skipped");}
        if(process.exitValue()!=0)throw new IOException("original structural producer failed: "+Files.readString(error,StandardCharsets.UTF_8));
        assertArrayEquals(source,Files.readAllBytes(anchor));assertArrayEquals(warBytes,Files.readAllBytes(war));
        byte[] bytes=Files.readAllBytes(output);assertTrue(bytes.length<=1_048_576,"bounded original fixture response");
        return new Arr(array(DriverJson.fromNode(org.xar.ck3.control.contracts.FullJsonTree.parse(bytes,1_048_576)),"original result rows"));
    }
    private void compare(List<Obj> rows)throws Exception {
        Arr expected=original(rows);assertEquals(rows.size(),expected.items().size());
        for(int index=0;index<rows.size();index++) {
            Obj input=rows.get(index),oracle=object(expected.items().get(index),"oracle");
            var call=ArmyStructuralActionsTest.call(text(input.get("step"),"step"));
            Obj before=object(input.get("before"),"before"),after=object(input.get("after"),"after");
            assertEquals(ArmyStructuralActionsTest.n(1),oracle.get("primitive_calls"),"one original primitive call, never replay");
            if(new Bool(false).equals(oracle.get("ok"))) {
                Obj request=object(input.get("request"),"request"),response=object(input.get("response"),"response");
                if(new Text("BridgeUnavailableError").equals(oracle.get("error_type"))) {
                    assertEquals(ArmyStructuralActionsTest.n(1),oracle.get("snapshot_calls"));
                    assertTrue(ArmyStructuralActions.matchesHaltRefusal((ArmyStructuralActions.Halt)call,before,request,response,"original-request"));
                    var fault=assertThrows(ArmyStructuralActions.DriverUnavailable.class,()->ArmyStructuralActions.haltDeferred(
                            (ArmyStructuralActions.Halt)call,before,after,request,response,"original-request"));
                    assertEquals(ArmyStructuralActions.DriverFailureReason.HALT_ROUTE_READBACK,fault.reason());
                    assertEquals(text(oracle.get("message"),"message"),fault.getMessage(),"exact original readback failure row "+index);
                } else {
                    assertEquals(new Text("_NativeCommandRejectedError"),oracle.get("error_type"));
                    assertEquals(ArmyStructuralActionsTest.n(0),oracle.get("snapshot_calls"),"original packet guard rejects before another snapshot");
                    assertFalse(ArmyStructuralActions.matchesHaltRefusal((ArmyStructuralActions.Halt)call,before,request,response,"original-request"));
                }
                continue;
            }
            RawJson actual=new Bool(true).equals(input.get("deferred"))
                    ?ArmyStructuralActions.haltDeferred((ArmyStructuralActions.Halt)call,before,after,object(input.get("request"),"request"),object(input.get("response"),"response"),"original-request")
                    :ArmyStructuralActions.format(call,before,after,new RawJson(DriverJson.encode(input.get("primitive"))));
            Obj data=DriverJson.object(actual.bytes(),DriverJson.MAX_NATIVE_BYTES);assertEquals(oracle.get("value"),data,"complete original output row "+index);
            assertEquals(data,ArmyPublicWire.decodeExactSourceBound(ArmyPublicWire.encodeExactSourceBound(data,ArmyStructuralActionsTest.context()),ArmyStructuralActionsTest.context()));
        }
    }
    @Test void actualThreeProducerBranchesFullOutputsAndStrictPostconditionsMatchAcrossIndependentProcess()throws Exception {
        var before=ArmyStructuralActionsTest.before();List<Obj> rows=new ArrayList<>();
        for(int[] ids:List.of(new int[]{0,7,8,9},new int[]{0,9},new int[]{0,7,8},new int[]{0,7,8,9,10},new int[]{7,8,9}))
            rows.add(input("split-army-half-0",before,ArmyStructuralActionsTest.after(ids),false,ArmyStructuralActionsTest.rejection()));
        for(Obj after:List.of(ArmyStructuralActionsTest.after(0,8),ArmyStructuralActionsTest.after(0,7,8),ArmyStructuralActionsTest.after(0),
                ArmyStructuralActionsTest.put(ArmyStructuralActionsTest.after(0,8),"revision",before.get("revision")),
                ArmyStructuralActionsTest.put(ArmyStructuralActionsTest.after(0,8),"native_revision",before.get("native_revision")),
                ArmyStructuralActionsTest.put(ArmyStructuralActionsTest.after(0,8),"paused",new Bool(false))))
            rows.add(input("merge-armies-0-with-7",before,after,false,ArmyStructuralActionsTest.rejection()));
        rows.add(input("halt-army-0",before,ArmyStructuralActionsTest.after(0,7,8),false,ArmyStructuralActionsTest.rejection()));compare(rows);
    }
    @Test void actualStockHaltRefusalAndWrongErrorRouteOwnerOrWindowAreNotReclassifiedAsGameplaySuccess()throws Exception {
        var before=ArmyStructuralActionsTest.before();List<Obj> rows=new ArrayList<>();Obj after=ArmyStructuralActionsTest.after(0,7,8),response=ArmyStructuralActionsTest.rejection();
        rows.add(input("halt-army-0",before,after,true,response));
        rows.add(input("halt-army-0",before,ArmyStructuralActionsTest.put(after,"date_raw",ArmyStructuralActionsTest.n(0)),true,response));
        rows.add(input("halt-army-0",before,ArmyStructuralActionsTest.put(after,"active_event",new Obj(Map.of())),true,response));
        rows.add(input("halt-army-0",before,ArmyStructuralActionsTest.put(after,"player_armies",new Arr(List.of(ArmyStructuralActionsTest.put(ArmyStructuralActionsTest.army(0),"owner_character_id",ArmyStructuralActionsTest.n(74))))),true,response));
        rows.add(input("halt-army-0",before,after,true,ArmyStructuralActionsTest.put(response,"error",new Text("other native error"))));compare(rows);
    }
    @Test void actualHaltReadbackFaultClassMessageAndPacketGuardOrderingMatchTheOriginalProducer()throws Exception {
        Obj before=ArmyStructuralActionsTest.put(ArmyStructuralActionsTest.before(),"revision",
                new IntegerValue(ArmyStructuralActionsTest.WIDE.subtract(java.math.BigInteger.TWO)));
        Obj after=ArmyStructuralActionsTest.after(0,7,8),response=ArmyStructuralActionsTest.rejection();
        List<Obj> rows=new ArrayList<>();
        for(Obj bad:List.of(ArmyStructuralActionsTest.after(7,8),ArmyStructuralActionsTest.put(after,"diagnostics",Nil.INSTANCE),
                ArmyStructuralActionsTest.put(after,"played_character",Nil.INSTANCE),
                ArmyStructuralActionsTest.put(after,"player_armies",new Arr(List.of(ArmyStructuralActionsTest.put(
                        ArmyStructuralActionsTest.army(0),"route_province_ids",new Text("not a route")))))))
            rows.add(input("halt-army-0",before,bad,true,response));
        for(Obj bad:List.of(ArmyStructuralActionsTest.put(before,"diagnostics",Nil.INSTANCE),
                ArmyStructuralActionsTest.put(before,"played_character",Nil.INSTANCE),
                ArmyStructuralActionsTest.put(before,"player_armies",new Arr(List.of(ArmyStructuralActionsTest.put(
                        ArmyStructuralActionsTest.army(0),"route_province_ids",Nil.INSTANCE))))))
            rows.add(input("halt-army-0",bad,after,true,response));
        for(Obj wrong:List.of(ArmyStructuralActionsTest.put(response,"request_id",new Text("other")),
                ArmyStructuralActionsTest.put(response,"protocol_version",ArmyStructuralActionsTest.n(2)),
                ArmyStructuralActionsTest.put(response,"result",new Obj(Map.of()))))
            rows.add(input("halt-army-0",before,after,true,wrong));
        Obj requestMismatch=input("halt-army-0",before,after,true,response);
        rows.add(ArmyStructuralActionsTest.put(requestMismatch,"request",ArmyStructuralActionsTest.put(
                object(requestMismatch.get("request"),"request"),"expected_revision",ArmyStructuralActionsTest.n(1))));
        compare(rows);
    }
    private record FailureCase(Obj input,int primitiveCalls) { }
    @Test void actualOriginalFailureClassMessageAndPrimitiveSubmissionTimingMatch()throws Exception {
        var before=ArmyStructuralActionsTest.before();var after=ArmyStructuralActionsTest.after(0,7,8);
        var failures=new ArrayList<FailureCase>();
        for(String step:List.of("halt-army-0","split-army-half-0","merge-armies-0-with-7"))
            failures.add(new FailureCase(input(step,ArmyStructuralActionsTest.after(8),after,false,ArmyStructuralActionsTest.rejection()),0));
        Obj blocked=ArmyStructuralActionsTest.put(before,"player_armies",new Arr(List.of(
                ArmyStructuralActionsTest.put(ArmyStructuralActionsTest.army(0),"in_combat",new Bool(true)),ArmyStructuralActionsTest.army(7))));
        failures.add(new FailureCase(input("merge-armies-0-with-7",blocked,after,false,ArmyStructuralActionsTest.rejection()),0));
        for(Value wrong:List.of(Nil.INSTANCE,new Bool(true),new DecimalValue("1.0"),new Text("1"))) {
            Obj badDate=ArmyStructuralActionsTest.put(before,"date_raw",wrong);
            for(String step:List.of("split-army-half-0","merge-armies-0-with-7","halt-army-0"))
                failures.add(new FailureCase(input(step,badDate,after,false,ArmyStructuralActionsTest.rejection()),step.startsWith("halt")?1:0));
        }
        Arr original=original(failures.stream().map(FailureCase::input).toList());
        for(int index=0;index<failures.size();index++) {
            FailureCase test=failures.get(index);Obj row=test.input(),oracle=object(original.items().get(index),"oracle");
            assertEquals(new Bool(false),oracle.get("ok"));assertEquals(new Text("BridgeUnavailableError"),oracle.get("error_type"));
            assertEquals(ArmyStructuralActionsTest.n(test.primitiveCalls()),oracle.get("primitive_calls"));
            var call=ArmyStructuralActionsTest.call(text(row.get("step"),"step"));
            Obj frame=object(row.get("before"),"before");
            ArmyStructuralActions.DriverUnavailable actual;
            if(test.primitiveCalls()==0)actual=assertThrows(ArmyStructuralActions.DriverUnavailable.class,()->ArmyStructuralActions.preflight(call,frame));
            else {
                assertDoesNotThrow(()->ArmyStructuralActions.preflight(call,frame));
                actual=assertThrows(ArmyStructuralActions.DriverUnavailable.class,()->ArmyStructuralActions.format(call,frame,
                        object(row.get("after"),"after"),new RawJson(DriverJson.encode(row.get("primitive")))));
            }
            assertEquals(text(oracle.get("message"),"message"),actual.getMessage(),"exact original failure "+index);
        }
    }
    private static String required(String key){String value=System.getProperty(key);if(value==null||value.isBlank())throw new IllegalStateException("NOT_EXECUTED: missing pinned original fixture "+key);return value;}
}
