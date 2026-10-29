package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.finance.WarPaymentNodes.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;

/** Original compiled/synthetic producer evidence; SOFTWARE only, never runtime qualification. */
final class WarPaymentExtrasMigrationTest {
    private static final String J=WarPaymentExtrasCodec.JOURNAL_KEY,C=WarPaymentExtrasCodec.CONTROL_KEY;
    private static Path repo(){return Path.of(required("xar.repository.root"));}
    private static String required(String key){String s=System.getProperty(key);if(s==null||s.isBlank())throw new IllegalStateException("Mandatory original Python parity setting: "+key);return s;}
    private static byte[] pinned(String relative,String hash)throws Exception{
        byte[] raw=Files.readAllBytes(repo().resolve(relative));assertEquals(hash,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)),relative);return raw;
    }
    private static ArrayNode fixture(String name,String hash)throws Exception{
        return list(JSON.readTree(pinned("ck3_autonomous_player/tests/unit/fixtures/"+name,hash)),64);
    }
    private static List<ObjectNode> cases()throws Exception{
        List<ObjectNode> out=new ArrayList<>();
        for(JsonNode row:fixture("war_payment_compiled_12004_a06.json","af7a7d9d90072a457d2ffe180b9f3eb0e96fe5c5ecd46176c268bbde871f5c7d"))out.add(obj(row.get("value").has(J)?row.get("value").get(J):row.get("value")));
        for(JsonNode row:fixture("war_payment_generic_context_12004_a04.json","27214c3ccdf6aba2b9510f65fd50e29ff03539a80aecddd8ea42e051c75320d3"))out.add(obj(row.get("value").has(J)?row.get("value").get(J):row.get("value")));
        assertEquals(25,out.size());return out;
    }
    private static ObjectNode snapshot(JsonNode journal){
        JsonNode s=journal.get("current_session");ObjectNode frame=empty().put("paused",true).put("map_ready",true);
        frame.set("native_revision",s.get("snapshot_revision"));frame.put("date_raw",n(s,"native_date_raw").and(BigInteger.valueOf(0xffffffffL)).intValue());
        frame.set("played_character",empty().set("character_id",s.get("player_character_full_id")));
        ObjectNode diagnostics=empty();diagnostics.set("bridge_pid",s.get("pid"));diagnostics.set("connection_generation",s.get("connection_generation"));
        diagnostics.set("hello",empty().put("expected_ck3_version",WarPaymentExtrasCodec.VERSION).put("expected_ck3_sha256",WarPaymentExtrasCodec.SHA));frame.set("diagnostics",diagnostics);return frame;
    }
    private static ObjectNode call(String operation,ObjectNode journal){
        ObjectNode input=empty().put("operation",operation).put("machine",journal.get("machine_id").textValue());input.set("journal",journal);input.set("snapshot",snapshot(journal));input.putNull("mode");return input;
    }
    private static RawJson actual(ObjectNode input){
        String machine=input.get("machine").textValue();Optional<WarPaymentExtrasCodec.Mode> mode=input.get("mode").isNull()?Optional.empty():Optional.of(WarPaymentExtrasCodec.Mode.valueOf(input.get("mode").textValue().toUpperCase(java.util.Locale.ROOT)));
        return switch(input.get("operation").textValue()){
            case "normalize" -> WarPaymentExtrasCodec.normalize(raw(input.get("result")),raw(input.get("snapshot")),machine,mode);
            case "wallet" -> WarPaymentExtrasCodec.consumeResource4WalletContexts(raw(input.get("journal")),raw(input.get("snapshot")),machine);
            case "raw4" -> WarPaymentExtrasCodec.consumeRaw4GetterObservations(raw(input.get("journal")),raw(input.get("snapshot")),machine);
            case "request" -> WarPaymentExtrasCodec.requestFields(mode,input.has("window")&&!input.get("window").isNull()?Optional.of(input.get("window").textValue()):Optional.empty(),machine);
            default -> throw new IllegalArgumentException("test operation");
        };
    }
    private static ObjectNode normalization(ObjectNode journal){ObjectNode c=call("normalize",journal);c.set("result",empty().set(J,journal));return c;}
    @org.junit.jupiter.api.io.TempDir Path temporary;
    private JsonNode python(JsonNode inputs)throws Exception{
        pinned("ck3_autonomous_player/src/xar_autoplayer/bridge/war_payment_observations_v1.py","b4a49efbb6e409001050aaf9ff8208bc73e9c0608f7161f2840fdf70c786c11b");
        pinned("ck3_autonomous_player/src/xar_autoplayer/bridge/war_payment_resource4_wallet_v1.py","48be37aa5bd9621502f5879b3906f4058f52c6a88967d13401c19815807c37f8");
        pinned("ck3_autonomous_player/src/xar_autoplayer/bridge/war_payment_raw4_getter_v1.py","46fca7fd5b65432acadb2063e196b12504d2dc897d6e802a6819b43d8cee9706");
        pinned("ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py","9f7665ed680238f6904bc3ef22e1d67ef9b4ccd047e699542d5dbaff24b01086");
        pinned("ck3_autonomous_player/src/xar_autoplayer/bridge/nonwar_private_build.py","fe1a53ca0f01e60ae37231e3b1a566442454f3bb77afd33b616849b25f6d53e9");
        pinned("ck3_autonomous_player/tests/unit/test_war_payment_resource4_wallet.py","2bfc215f1525cfc18cb7b18fe9428431b414cd352d97e35d9a1944a8054cdbbb");
        pinned("ck3_autonomous_player/tests/unit/test_war_payment_raw4_getter.py","641be7edf1dca31c4bbbefbe12341d1832545ac90329f52856e3e123d8f805aa");
        pinned("ck3_autonomous_player/tests/unit/fixtures/war_payment_compiled_12004_a06.json","af7a7d9d90072a457d2ffe180b9f3eb0e96fe5c5ecd46176c268bbde871f5c7d");
        pinned("ck3_autonomous_player/tests/unit/fixtures/war_payment_generic_context_12004_a04.json","27214c3ccdf6aba2b9510f65fd50e29ff03539a80aecddd8ea42e051c75320d3");
        String script="""
import sys,json,importlib.util
from pathlib import Path
repo=Path(sys.argv[1])
sys.stdin.reconfigure(encoding='utf-8');sys.stdout.reconfigure(encoding='utf-8')
sys.path[:0]=[str(repo),str(repo/'tools'),str(repo/'ck3_autonomous_player/src')]
from xar_autoplayer.bridge import war_payment_observations_v1 as p
from xar_autoplayer.bridge import war_payment_resource4_wallet_v1 as wallet
from xar_autoplayer.bridge import war_payment_raw4_getter_v1 as raw4
from tools import ck3_live_run_id as runid
from xar_autoplayer.bridge.driver import BridgeUnavailableError
sys.modules['ck3_live_run_id']=runid
payload=json.loads(sys.stdin.read())
if isinstance(payload,dict):
    out=[]
    for name,fn in [('test_war_payment_resource4_wallet','producer_shaped_journal'),('test_war_payment_raw4_getter','make')]:
        source=repo/'ck3_autonomous_player/tests/unit'/(name+'.py')
        spec=importlib.util.spec_from_file_location(name,source)
        module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
        out.append(getattr(module,fn)()[0])
    print(json.dumps(out));sys.exit(0)
outputs=[]
for x in payload:
    runid.current_machine_id=lambda override=None:x['machine']
    try:
        op=x['operation']
        if op=='normalize':v=p.normalize_payment_extras(x['result'],snapshot=x['snapshot'],payment_sampling=x['mode'])
        elif op=='wallet':v=wallet.consume_resource4_wallet_contexts(x['journal'],snapshot=x['snapshot'],machine_id=x['machine'])
        elif op=='raw4':v=raw4.consume_raw4_getter_observations(x['journal'],snapshot=x['snapshot'],machine_id=x['machine'])
        elif op=='request':v=p.payment_request_fields(x['mode'],x.get('window')) or {}
        else:raise ValueError('operation')
        outputs.append(dict(ok=True,value=v))
    except (ValueError,TypeError,KeyError,BridgeUnavailableError) as error:outputs.append(dict(ok=False,error=type(error).__name__))
print(json.dumps(outputs))
""";
        Path output=temporary.resolve("parity-"+java.util.UUID.randomUUID()+".json");
        var builder=new ProcessBuilder(required("xar.python"),"-B","-I","-c",script,repo().toString());
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1");builder.redirectError(ProcessBuilder.Redirect.INHERIT);builder.redirectOutput(output.toFile());
        Process process=builder.start();try{
            try(var input=process.getOutputStream()){input.write(JSON.writeValueAsBytes(inputs));}
            if(!process.waitFor(30,TimeUnit.SECONDS)){process.destroyForcibly();fail("Original pure Python parity timed out");}
            assertEquals(0,process.exitValue());assertTrue(Files.size(output)<=8L*1024*1024);return JSON.readTree(Files.readAllBytes(output));
        }finally{if(process.isAlive())process.destroyForcibly();}
    }
    private void parity(ArrayNode calls)throws Exception{
        JsonNode expected=python(calls);assertEquals(calls.size(),expected.size());
        for(int i=0;i<calls.size();i++){
            ObjectNode input=obj(calls.get(i));JsonNode wanted=expected.get(i);
            if(wanted.get("ok").booleanValue())assertTrue(eq(wanted.get("value"),parse(actual(input))),"original Python value drift at "+i);
            else assertThrows(IllegalArgumentException.class,()->actual(input),"original Python rejected case "+i);
        }
    }
    @Test void everyCompiledProducerCaseReachesBothStrictConsumersAndLosslessPublicWire()throws Exception{
        ArrayNode inputs=array();
        for(ObjectNode j:cases()){
            inputs.add(normalization(j));inputs.add(call("wallet",j));inputs.add(call("raw4",j));
            ObjectNode normal=parse(actual(normalization(j)));RawJson publicValue=WarPaymentExtrasCodec.publicWire(raw(normal));
            assertTrue(eq(normal,parse(WarPaymentExtrasCodec.nativeWire(publicValue))));
            JsonNode wire=parse(publicValue).get(J);assertTrue(wire.get("current_session").get("process_create_time_100ns").isTextual());
            assertTrue(wire.get("current_session").get("pid").isIntegralNumber());
            assertEquals(j.get("records").size(),wire.get("records").size());
        }
        parity(inputs);
    }
    private static ObjectNode change(ObjectNode original,java.util.function.Consumer<ObjectNode> mutate){
        ObjectNode c=normalization(original.deepCopy());mutate.accept(obj(c.get("result").get(J)));return c;
    }
    @Test void completeRequiredFieldsWrongTypesFrameAndUnprovenClaimsMatchOriginalRejection()throws Exception{
        ObjectNode generic=cases().get(9),boarding=cases().get(7);ArrayNode inputs=array();
        List<String> fields=new ArrayList<>();generic.fieldNames().forEachRemaining(fields::add);
        for(String key:fields)inputs.add(change(generic,j->j.remove(key)));
        inputs.add(change(generic,j->j.put("invented",true)));
        JsonNode context=generic.get("records").get(0).get(WarPaymentExtrasCodec.GENERIC);
        for(String scope:List.of("context","before","after","parent_trace")){
            JsonNode node=scope.equals("context")?context:context.get(scope);List<String> keys=new ArrayList<>();node.fieldNames().forEachRemaining(keys::add);
            for(String key:keys){
                inputs.add(change(generic,j->{ObjectNode c=obj(j.get("records").get(0).get(WarPaymentExtrasCodec.GENERIC));obj(scope.equals("context")?c:c.get(scope)).remove(key);}));
                inputs.add(change(generic,j->{ObjectNode c=obj(j.get("records").get(0).get(WarPaymentExtrasCodec.GENERIC));ObjectNode target=obj(scope.equals("context")?c:c.get(scope));
                    JsonNode value=target.get(key);if(value.isBoolean())target.put(key,1);else if(value.isNumber()||value.isNull())target.put(key,true);else target.put(key,17);}));
            }
        }
        inputs.add(change(boarding,j->obj(j.get("records").get(0)).put("amount_raw",0)));
        inputs.add(change(boarding,j->obj(j.get("records").get(0).get("after")).put("wrapper_balance_bits",123)));
        inputs.add(change(boarding,j->obj(j.get("records").get(0).get("parent_gateway_entry")).put("sequence",999)));
        inputs.add(change(boarding,j->obj(j.get("records").get(0).get("session_return")).put("connection_generation",99)));
        inputs.add(change(boarding,j->j.put("overwritten",1)));
        inputs.add(change(boarding,j->j.put("publication_failures",1)));
        inputs.add(change(boarding,j->obj(j.get("current_session")).put("pid",999)));
        inputs.add(change(boarding,j->obj(j.get("current_session")).put("native_date_raw",1)));
        inputs.add(change(boarding,j->j.put("machine_id","wrong-machine")));
        inputs.add(change(boarding,j->obj(j.get("qualified_boarding_debits").get(0)).put("requested_amount_raw",true)));
        inputs.add(change(generic,j->obj(j.get("records").get(0).get(WarPaymentExtrasCodec.GENERIC).get("before")).put("value_2c0",BigInteger.ONE.shiftLeft(63))));
        inputs.add(change(generic,j->obj(j.get("records").get(0).get(WarPaymentExtrasCodec.GENERIC).get("parent_trace")).put("module_base",BigInteger.ONE.shiftLeft(64))));
        inputs.add(change(generic,j->obj(j.get("records").get(0)).putNull(WarPaymentExtrasCodec.GENERIC)));
        ObjectNode high=change(boarding,j->obj(j.get("current_session")).put("native_date_raw",n(j.get("current_session"),"native_date_raw").or(BigInteger.valueOf(7).shiftLeft(32))));inputs.add(high);
        parity(inputs);
    }
    @Test void originalTwoChildProducersPreservePhysicalAndDefaultZeroAndUnknownBranches()throws Exception{
        JsonNode produced=python(empty().put("operation","child_inputs"));assertEquals(2,produced.size());
        ObjectNode wallet=obj(produced.get(0)),getter=obj(produced.get(1));ArrayNode inputs=array();
        inputs.add(normalization(wallet));inputs.add(call("wallet",wallet));inputs.add(normalization(getter));inputs.add(call("raw4",getter));
        for(String variant:List.of("default_zero","physical_zero","return","changed_context","session","unreadable","external_pc","busy","wrong_selector","extra_field","clear")){
            ObjectNode j=getter.deepCopy(),v=obj(j.get(WarPaymentRaw4Codec.KEY)),r=obj(v.get("records").get(0));
            switch(variant){
                case "default_zero" -> {for(String phase:List.of("before","after"))obj(r.get(phase)).put("context",0).putNull("physical_4a0_bits");r.put("out64_bits",0);}
                case "physical_zero" -> {for(String phase:List.of("before","after"))obj(r.get(phase)).put("physical_4a0_bits",0);r.put("out64_bits",0);}
                case "return" -> r.put("raw_return_bits",n(r,"raw_return_bits").xor(BigInteger.valueOf(8)));
                case "changed_context" -> obj(r.get("after")).put("context",n(r.get("after"),"context").add(BigInteger.valueOf(8)));
                case "session" -> obj(r.get("session_return")).put("connection_generation",10);
                case "unreadable" -> r.putNull("out64_bits").put("output_failed_reads",1);
                case "external_pc" -> r.put("caller_return_absolute",1).putNull("caller_return_rva");
                case "busy" -> obj(j.get("sampling")).put("busy",true).put("active_captures",1);
                case "wrong_selector" -> r.put("raw_selector",0);
                case "extra_field" -> r.put("paid",true);
                case "clear" -> obj(j.get("sampling")).put("capture_enabled",false).put("clear_completed",true).put("retained_records",0);
                default -> throw new IllegalArgumentException(variant);
            }
            inputs.add(call("raw4",j));
            if(variant.equals("default_zero")||variant.equals("physical_zero")){
                JsonNode q=parse(actual(call("raw4",j))).get("qualified_raw4_reads").get(0);
                assertEquals(variant.equals("default_zero")?"default_zero_missing_extension_or_context":"physical_context_4a0",q.get("read_branch").textValue());
            }
        }
        ObjectNode zero=wallet.deepCopy();JsonNode record=zero.get("records").get(0);for(String phase:List.of("before","after"))obj(record.get(WarPaymentResource4Codec.KEY).get(phase)).put("physical_4a0_bits",0);
        inputs.add(call("wallet",zero));JsonNode boundary=parse(actual(call("wallet",zero))).get("qualified_resource4_boundaries").get(0);
        assertFalse(boundary.get("boundary_matches_requested_sub_mod64").booleanValue());assertTrue(boundary.get("military_paid_raw").isNull());
        for(String bad:List.of("kind","resource","currency","extra","missing_read")){
            ObjectNode j=wallet.deepCopy(),r=obj(j.get("records").get(0)),v=obj(r.get(WarPaymentResource4Codec.KEY));
            switch(bad){case "kind"->r.put("kind",3);case "resource"->r.put("resource_kind_raw",0);case "currency"->v.put("resource_name","gold");case "extra"->v.put("paid",true);case "missing_read"->obj(v.get("before")).putNull("physical_4a0_bits").put("failed_reads",1);default->throw new IllegalArgumentException(bad);}
            inputs.add(call("wallet",j));
        }
        parity(inputs);
    }
    @Test void controlAdmissionMissingEvidenceAndRequestFieldsMatchOriginalWithoutRetry()throws Exception{
        ObjectNode j=cases().get(9);ArrayNode inputs=array();
        for(String mode:List.of("enable","disable","query"))for(boolean window:List.of(false,true)){
            ObjectNode c=call("request",j).put("mode",mode);if(window)c.put("window",WarPaymentExtrasCodec.WINDOW_CONTRACT);inputs.add(c);
        }
        inputs.add(call("request",j));inputs.add(call("request",j).put("window",WarPaymentExtrasCodec.WINDOW_CONTRACT));
        ObjectNode missing=normalization(j);missing.set("result",empty());inputs.add(missing);inputs.add(missing.deepCopy().put("mode","query"));
        ObjectNode controlOnly=normalization(j);controlOnly.set("result",empty().set(C,empty().put("requested","query").put("accepted",false).put("reason","not_enabled")));controlOnly.put("mode","query");inputs.add(controlOnly);
        for(boolean accepted:List.of(false,true)){
            ObjectNode c=normalization(j).put("mode","enable");obj(c.get("result")).set(C,empty().put("requested","enable").put("accepted",accepted).put("reason",accepted?"enabled_controlled_no_load_window":"natural_phase_sampling_must_be_enabled"));inputs.add(c);
        }
        ObjectNode refusal=normalization(j).put("mode","enable");obj(refusal.get("result")).set(C,empty().put("requested","enable").put("accepted",false).put("reason","未知：未资格"));inputs.add(refusal);
        ObjectNode off=j.deepCopy();off.put("controlled_window_admitted",false).put("session_basis","unqualified");off.set("records",array());off.set("qualified_boarding_debits",array());
        obj(off.get("current_session")).put("controlled_window_id",0).put("same_owned_process_no_load_window",false);
        obj(off.get("sampling")).put("capture_enabled",false).put("clear_completed",true).put("retained_records",0);
        for(String mode:List.of("disable","query")){
            ObjectNode c=normalization(off).put("mode",mode);obj(c.get("result")).set(C,empty().put("requested",mode).put("accepted",true).put("reason",mode.equals("disable")?"disabled":"not_enabled"));inputs.add(c);
        }
        ObjectNode unsolicited=normalization(j);obj(unsolicited.get("result")).set(C,empty().put("requested","query").put("accepted",false).put("reason","not_enabled"));inputs.add(unsolicited);
        ObjectNode mislabeled=normalization(j).put("mode","query");obj(mislabeled.get("result")).set(C,empty().put("requested","unknown").put("accepted",false).put("reason","unknown"));inputs.add(mislabeled);
        ObjectNode nullExtra=normalization(j);obj(nullExtra.get("result")).putNull(J);inputs.add(nullExtra);
        ObjectNode wrongBuild=normalization(j);obj(wrongBuild.get("snapshot").get("diagnostics").get("hello")).put("expected_ck3_version","1.20.0.3");inputs.add(wrongBuild);
        ObjectNode explicitNull=normalization(j);obj(explicitNull.get("snapshot").get("diagnostics").get("hello")).putNull("expected_ck3_version").put("game_version","1.20.0.4");inputs.add(explicitNull);
        parity(inputs);
    }
    @Test void publicWideIntegersAreCanonicalAndNumericUnsafeValuesNeverRoundTrip()throws Exception{
        ObjectNode source=parse(actual(normalization(cases().get(9))));
        ObjectNode wire=parse(WarPaymentExtrasCodec.publicWire(raw(source)));
        for(String malformed:List.of("00","-0","+1","18446744073709551616","-1")){
            ObjectNode bad=wire.deepCopy();obj(bad.get(J).get("current_session")).put("process_create_time_100ns",malformed);
            assertThrows(IllegalArgumentException.class,()->WarPaymentExtrasCodec.nativeWire(raw(bad)));
        }
        ObjectNode unsafe=wire.deepCopy();obj(unsafe.get(J).get("current_session")).put("process_create_time_100ns",9007199254740992L);
        assertThrows(IllegalArgumentException.class,()->WarPaymentExtrasCodec.nativeWire(raw(unsafe)));
        ObjectNode altered=source.deepCopy();obj(altered.get(J).get("records").get(0)).put("invented_paid",true);
        assertThrows(IllegalArgumentException.class,()->WarPaymentExtrasCodec.publicWire(raw(altered)));
        assertTrue(eq(source,parse(WarPaymentExtrasCodec.nativeWire(raw(wire)))));
    }
}
