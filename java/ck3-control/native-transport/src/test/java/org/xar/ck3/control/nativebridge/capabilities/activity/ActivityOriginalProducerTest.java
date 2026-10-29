package org.xar.ck3.control.nativebridge.capabilities.activity;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.activity.ActivityJson.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.activity.ActivityConfigurationModels.Frame;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Executes all ten original Python producer modules and their original fixtures in a fresh process. */
final class ActivityOriginalProducerTest {
    private static final String ORACLE="""
        import hashlib,importlib,json,runpy,sys
        from pathlib import Path
        root=Path(sys.argv[1]); sys.dont_write_bytecode=True
        sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
        pins={
          'activity_feast_guest_candidate':('6ded1ff311c3103ce300b18c4dc98dfe42a9f21e14715bcac671a63397424b7a','543e799de9a071d5be601103ac8aabe0cc5bdf35b023acc1993452a8a63a225f'),
          'activity_feast_guest_opinion':('2dc8219a916de5c5d3332ab945302f97ae2b4238238dabfc52382d08122806b7','d29cc993bd79f3724b900b9e2fae47817c0590083fbe430329fcebad3136c75e'),
          'activity_feast_guest_route_proof':('54f6014d7bcd51c57626fe03b61ea470f5eae98cbe17de8e30c97bde1f42ced4','c0aa67f40c82eac38a6f47b417dab77c15ccc0c865cb5d37aebebed6b3bdc999'),
          'activity_feast_guest_rule':('3c5a0670eae7a98143ff518b1197a35c6a640e5dce934b291f3f1a31978a69c9','f0dd59612bb99b75afa8e079b895ee06545d98031466e485687b732d96a92a33'),
          'activity_feast_guest_rule_provenance':('bce5656019b0bfec90ec38c88c83b9cb48885f63508274be95a8b24444c9b2df','5a9076637c2f0e0bcc9b592c865d5454e73702642b95f205b85f24edb0b33c0d'),
          'activity_feast_guest_target':('7cd49556a9b43ae8c80e5e62875f7d162ca2dee61bd8d32139057ca37454e19b','f6bb268a113306422007ec9b0741479cb3b98f606816f729b153a1551650e3b5'),
          'activity_feast_stage5_start':('656b02666880395c1bc1e0e3de4d9ff9d1a0d30e1393fc69e1d930aef43b8f3f','c8b7816eb20d8503d9b53f5b3ffcf2fc2f1502c32af255e58f4fbdbb69d7ad39'),
          'activity_planner_diag':('200e8500ac18bef4a71fa6f885285d344a62ebb28837a54d45efddabf7d9e7e9','749509e9f16ae031e9af8838dd16c4e24caf398948c85ae89635ef7cd3d522d9'),
          'activity_stage5_feast_full_cost':('e8630a63c7ae5cc08f0413bf21e707a92b5eced42fd41a75fb0f686e99e8efe9','10232552d4fe37bec59047af269d1c5cc7dda180b6c3e71aef99f73f9df304e0'),
          'activity_stage5_gold':('8d51db13df2939f62a9134592f3677c5e77c6b37e88031b7f06fa3c3f3fc7c74','e94f90dbb6cae56c4c97651b868e3c8bbfae53b8019b136c3bea55d8d1f077a1')}
        modules={};fixtures={}
        for name,(production_pin,fixture_pin) in pins.items():
            source=root/'ck3_autonomous_player/src/xar_autoplayer/bridge'/f'{name}_private_transport.py'
            fixture=root/'ck3_autonomous_player/tests/unit'/f'test_{name}_private_transport.py'
            if hashlib.sha256(source.read_bytes()).hexdigest()!=production_pin or hashlib.sha256(fixture.read_bytes()).hexdigest()!=fixture_pin: raise RuntimeError('Activity original source/fixture pin drift: '+name)
            modules[name]=importlib.import_module('xar_autoplayer.bridge.'+name+'_private_transport')
            fixtures[name]=runpy.run_path(str(fixture))
        cases=[]
        def emit(query,payload,status='available',args=None):
            args={} if args is None else args
            common=dict(native_revision=payload['snapshot_revision'],date_raw=payload['date_raw'],actor_id=payload['actor_character_id'])
            if query=='DIAGNOSTIC':
                if not modules['activity_planner_diag']._valid_payload(payload,revision=common['native_revision'],date_raw=common['date_raw'],actor_id=common['actor_id']): raise RuntimeError('original diagnostic refused fixture')
            elif query=='GOLD': modules['activity_stage5_gold'].parse_activity_stage5_gold_payload_v1(payload,expected_native_revision=common['native_revision'],expected_date_raw=common['date_raw'],expected_actor_character_id=common['actor_id'])
            elif query=='FULL_COST': modules['activity_stage5_feast_full_cost'].parse_activity_stage5_feast_full_cost_payload_v1(payload,expected_native_revision=common['native_revision'],expected_date_raw=common['date_raw'],expected_actor_character_id=common['actor_id'])
            elif query in ('START_INPUTS','HOSTED'):
                m=modules['activity_feast_stage5_start']; m._parse_payload(payload,step=m.INPUT_STEP if query=='START_INPUTS' else m.POST_STEP,**common)
            elif query=='GUEST_CANDIDATE': modules['activity_feast_guest_candidate'].parse_activity_feast_guest_candidate_private_v1(payload,envelope_status=status,**common)
            elif query=='GUEST_OPINION': modules['activity_feast_guest_opinion'].parse_activity_feast_guest_opinion_private_v1(payload,guest_id=args['guest_character_id'],envelope_status=status,**common)
            elif query=='GUEST_TARGET': modules['activity_feast_guest_target'].parse_activity_feast_guest_target_private_v1(payload,target_character_id=args['target_character_id'],envelope_status=status,**common)
            elif query=='GUEST_ROUTE_PROOF': modules['activity_feast_guest_route_proof'].parse_activity_feast_guest_route_proof_private_v1(payload,envelope_status=status,**common)
            elif query=='GUEST_RULE':
                m=modules['activity_feast_guest_rule']; m._parse(payload,step=m.QUERY_STEP,envelope_status=status,**common)
            elif query=='GUEST_RULE_PROVENANCE': modules['activity_feast_guest_rule_provenance'].parse_activity_feast_guest_rule_provenance_private_v1(payload,expected_revision=common['native_revision'],expected_date_raw=common['date_raw'],expected_actor_id=common['actor_id'],authored_rule_key=args['authored_rule_key'],candidate_character_id=args['candidate_character_id'],envelope_status=status)
            else: raise RuntimeError('unimplemented original producer')
            cases.append(dict(query=query,payload=payload,status=status,arguments=args))
        emit('DIAGNOSTIC',fixtures['activity_planner_diag']['value']())
        emit('GOLD',fixtures['activity_stage5_gold']['payload']())
        extreme=fixtures['activity_stage5_gold']['payload'](); extreme['configured_cost']['raw']=2**63-1; extreme['resource_value']['raw']=-(2**63); emit('GOLD',extreme)
        emit('FULL_COST',fixtures['activity_stage5_feast_full_cost']['payload']())
        f=fixtures['activity_feast_stage5_start']; emit('START_INPUTS',f['inputs_payload']()); emit('HOSTED',f['common_payload'](modules['activity_feast_stage5_start'].POST_SCHEMA))
        for status in ('observed','no_qualified_candidate','no_normal_refresh'): emit('GUEST_CANDIDATE',fixtures['activity_feast_guest_candidate']['payload'](status), 'unavailable' if status=='no_normal_refresh' else 'available')
        for status in ('observed','opinion_unavailable'): emit('GUEST_OPINION',fixtures['activity_feast_guest_opinion']['payload'](status),'available' if status=='observed' else 'unavailable',{'guest_character_id':32000})
        for status in ('observed','target_not_filtered','no_normal_refresh'): emit('GUEST_TARGET',fixtures['activity_feast_guest_target']['payload'](status=status),'unavailable' if status=='no_normal_refresh' else 'available',{'target_character_id':43699})
        fixture=fixtures['activity_feast_guest_route_proof']['GuestRouteProofTransportTests'](); fixture.setUp(); emit('GUEST_ROUTE_PROOF',fixture.payload)
        for status in ('observed_inactive','observed_active','rule_unavailable'): emit('GUEST_RULE',fixtures['activity_feast_guest_rule']['payload'](status),{'observed_inactive':'available','observed_active':'already_active'}.get(status,'unavailable'),{'authored_rule_key':'activity_invite_rule_vassals'})
        for status in ('observed','no_normal_refresh'): emit('GUEST_RULE_PROVENANCE',fixtures['activity_feast_guest_rule_provenance']['payload'](status=status),'available' if status=='observed' else 'unavailable',{'authored_rule_key':'activity_invite_rule_vassals','candidate_character_id':32000})
        print(json.dumps({'cases':cases},ensure_ascii=True,separators=(',',':')))
        """;
    static JsonNode originalCases() throws Exception {
        String root=System.getProperty("xar.repository.root"),python=System.getProperty("xar.python"); assertNotNull(root,"required repository root; never skip"); assertNotNull(python,"required explicit absolute Windows-native Python; never skip"); assertTrue(Path.of(python).isAbsolute(),"explicit interpreter path required");
        Process process=new ProcessBuilder(python,"-B","-c",ORACLE,root).redirectErrorStream(true).start(); FutureTask<byte[]> capture=new FutureTask<>(()->process.getInputStream().readNBytes(1_048_577)); Thread reader=Thread.ofVirtual().start(capture);
        try { assertTrue(process.waitFor(45,TimeUnit.SECONDS),"original Activity producer timed out"); byte[] output=capture.get(5,TimeUnit.SECONDS); assertTrue(output.length<=1_048_576,"bounded producer stdout"); assertEquals(0,process.exitValue(),new String(output,StandardCharsets.UTF_8)); return StrictJson.parse(output).get("cases"); }
        finally { if(process.isAlive())process.destroyForcibly(); reader.interrupt(); }
    }
    private static Frame frame(JsonNode row) { return new Frame(row.get("snapshot_revision").bigIntegerValue(),row.get("date_raw").bigIntegerValue(),row.get("actor_character_id").bigIntegerValue()); }
    @Test void allOriginalProducerFamiliesRoundTripAndRejectIdentityTypeDrift() throws Exception {
        JsonNode cases=originalCases(); assertEquals(20,cases.size());
        for(JsonNode fixture:cases) {
            ActivityNativeContracts.Query query=ActivityNativeContracts.Query.valueOf(text(fixture,"query")); ObjectNode payload=(ObjectNode)fixture.get("payload"); var arguments=app(fixture.get("arguments")); Frame frame=frame(payload); String status=text(fixture,"status");
            ActivityPayload decoded=ActivityReadCodec.decode(query,raw(payload).bytes(),frame,arguments,status,null); assertEquals(payload,StrictJson.parse(ActivityReadCodec.encode(decoded)),query.name());
            for(String key:List.of("snapshot_revision","date_raw","actor_character_id")) { ObjectNode wrong=payload.deepCopy(); wrong.put(key,true); assertThrows(IllegalArgumentException.class,()->ActivityReadCodec.decode(query,raw(wrong).bytes(),frame,arguments,status,null)); ObjectNode floating=payload.deepCopy(); floating.put(key,payload.get(key).doubleValue()); assertThrows(IllegalArgumentException.class,()->ActivityReadCodec.decode(query,raw(floating).bytes(),frame,arguments,status,null)); }
            ObjectNode missing=payload.deepCopy(); missing.remove("schema"); assertThrows(IllegalArgumentException.class,()->ActivityReadCodec.decode(query,raw(missing).bytes(),frame,arguments,status,null)); ObjectNode extra=payload.deepCopy().put("unknown_field",true); assertThrows(IllegalArgumentException.class,()->ActivityReadCodec.decode(query,raw(extra).bytes(),frame,arguments,status,null));
        }
    }
    @Test void nativeMutationWireRejectsAddedMetadataAndForgedStartFlags() {
        String start="""
            {"expected_date_raw":10000,"expected_actor_character_id":31000,"expected_activity_key":"activity_feast","expected_option_key":"feast_type_generic","expected_planning_stage":5,"policy_positive":true,"previous_submit_pending":false,"reserve_gold_raw":0,"reserve_treasury_raw":0,"reserve_piety_raw":0,"reserve_barter_goods_raw":0}
            """;
        ObjectNode fields=parse(start.getBytes(StandardCharsets.UTF_8)); ActivityActionRoutes.Kind kind=ActivityActionRoutes.Kind.START;
        ActivityActionRoutes.validateWire(kind,new NativeRequest(kind.step(),java.util.Optional.empty(),raw(fields)));
        for(String key:List.of("policy_positive","previous_submit_pending")) { ObjectNode wrong=fields.deepCopy(); wrong.put(key,!bool(fields,key)); assertThrows(IllegalArgumentException.class,()->ActivityActionRoutes.validateWire(kind,new NativeRequest(kind.step(),java.util.Optional.empty(),raw(wrong)))); }
        fields.put("planner_observation","must never reach native wire"); assertThrows(IllegalArgumentException.class,()->ActivityActionRoutes.validateWire(kind,new NativeRequest(kind.step(),java.util.Optional.empty(),raw(fields))));
    }
    @Test void publicNumericBoundaryRejectsRoundedIdentityWhileInternalNativeRawStaysExact() {
        ObjectNode safe=StrictJson.object().put("native_revision",9_007_199_254_740_991L); ActivityNativeContracts.publicSafeNumbers(safe);
        ObjectNode unsafe=StrictJson.object().put("native_revision",new BigInteger("9007199254740993")); assertThrows(IllegalArgumentException.class,()->ActivityNativeContracts.publicSafeNumbers(unsafe));
        assertEquals(new BigInteger("9007199254740993"),StrictJson.parse(raw(unsafe).bytes()).get("native_revision").bigIntegerValue());
        ActivityNativeContracts.publicSafeNumbers(StrictJson.object().put("native_identity_u64","18446744073709551615"));
    }
}
