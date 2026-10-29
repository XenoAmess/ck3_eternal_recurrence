package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import org.xar.ck3.control.contracts.ExactRef;

/** Test-only exact manifest-pinned calls to the existing Python normalizers, with no generated Python file. */
final class ArmyStrengthsMonthlyOriginal {
    record Manifest(ExactRef bundle,List<ExactRef> sources) { Manifest{sources=List.copyOf(sources);} }
    private ArmyStrengthsMonthlyOriginal(){}
    static Path property(String key,boolean directory)throws Exception{String value=System.getProperty(key);if(value==null||value.isBlank())throw new IllegalStateException("required original-producer property missing: "+key);Path requested=Path.of(value);if(!requested.isAbsolute())throw new IllegalStateException("absolute path required: "+key);Path actual=requested.toRealPath();if(directory?!Files.isDirectory(actual):!Files.isRegularFile(actual))throw new IllegalStateException("unavailable original producer: "+key);return actual;}
    static String sha(byte[] value)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value));}
    static Manifest manifest()throws Exception{
        Path path=property("xar.monthly.original.manifest",false);String expected=System.getProperty("xar.monthly.original.manifest.sha256");
        if(expected==null||!expected.matches("[0-9a-f]{64}")||Files.size(path)>65536)throw new IllegalStateException("required exact original manifest hash/bound missing");
        byte[] bytes=Files.readAllBytes(path);if(!sha(bytes).equals(expected))throw new IllegalStateException("original monthly manifest drift");
        ObjectNode n=closed(parse(bytes),"schema","machine_id","observed_at_utc","java_bundle_source","sources");
        equal(n.get("schema"),"xar.army-monthly-original-producers/v1");nonempty(n.get("machine_id"));nonempty(n.get("observed_at_utc"));
        List<ExactRef> sources=array(n.get("sources"),ExactRef::fromJson);if(sources.size()!=18||sources.stream().map(ExactRef::path).distinct().count()!=18)throw new IllegalStateException("complete original monthly producer graph required");
        Manifest result=new Manifest(ExactRef.fromJson(n.get("java_bundle_source")),sources);verify(result);return result;
    }
    static void verify(Manifest manifest)throws Exception{
        Path root=property("xar.repository.root",true);
        for(ExactRef source:manifest.sources()){Path path=Path.of(source.path()).toRealPath();if(!path.startsWith(root))throw new IllegalStateException("original source escaped repository");verify(source);}
        verify(manifest.bundle());
    }
    private static void verify(ExactRef ref)throws Exception{Path path=Path.of(ref.path()).toRealPath();if(!Files.isRegularFile(path)||Files.size(path)!=ref.bytes()||ref.bytes()>2*1024*1024||!sha(Files.readAllBytes(path)).equals(ref.sha256()))throw new IllegalStateException("actual original source changed: "+ref.path());}
    static JsonNode normalize(ArmyStrengthsFamilies.Key key,JsonNode input,List<Integer> regiments)throws Exception{
        String module,function;
        switch(key){
            case NATIVE_OWNER_RECALL_INPUTS_V1->{module="battle_native_owner_recall_inputs_contract";function="normalize_battle_native_owner_recall_inputs_v1";}
            case NATIVE_MAA_RECRUITMENT_INPUTS_V1->{module="native_maa_recruitment_inputs_contract";function="normalize_native_maa_recruitment_inputs_v1";}
            case OWNED_REGIMENTS_V1->{module="owned_regiments_v1";function="normalize_owned_regiments_v1";}
            case MONTHLY_CALLER_EFFECT_INPUTS_V1->{module="army_monthly_caller_effect_inputs_contract";function="normalize_monthly_caller_effect_inputs_v1";}
            case MONTHLY_FIRST_REMOVAL_CLEANUP_INPUTS_V1->{module="army_manager_cleanup_inputs_contract";function="normalize_monthly_first_removal_cleanup_inputs_v1";}
            case MONTHLY_CURRENT_HELPER_DOMAIN_INPUTS_V1->{module="army_current_helper_domain_inputs_contract";function="normalize_monthly_current_helper_domain_inputs_v1";}
            case MONTHLY_CURRENT_HELPER_POINT_STORE_INPUTS_V1->{module="army_current_helper_point_store_inputs_contract";function="normalize_monthly_current_helper_point_store_inputs_v1";}
            case CURRENT_MONTH_FIRST_REFILL_CALL_INPUTS_V1->{module="army_current_month_first_refill_call_inputs_contract";function="normalize_current_month_first_refill_call_inputs_v1";}
            case ACTUAL_LOSS_WRITER_OBSERVATIONS_V1->{module="army_actual_loss_writer_observations_contract";function="normalize_actual_loss_writer_observations_v1";}
            case BATTLE_CASUALTY_OBSERVATIONS_V1->{module="battle_casualty_observation_contract";function="normalize_battle_casualty_observations_v1";}
            default->throw new IllegalArgumentException("outside original monthly graph");
        }
        Manifest manifest=manifest();Path root=property("xar.repository.root",true),python=property("xar.python",false);
        String invocation="""
                import importlib,json,sys
                from pathlib import Path
                sys.dont_write_bytecode=True
                root=Path(sys.argv[1])
                sys.path.insert(0,str(root/'ck3_autonomous_player'/'src'))
                v=json.load(sys.stdin)
                fn=getattr(importlib.import_module('xar_autoplayer.bridge.'+v['module']),v['function'])
                kwargs={}
                if v['key']=='NATIVE_OWNER_RECALL_INPUTS_V1': kwargs['lifecycle_status']='available'
                if v['key']=='ACTUAL_LOSS_WRITER_OBSERVATIONS_V1': kwargs['current_regiment_ids']=v['regiments']
                print(json.dumps({'value':fn(v['input'],**kwargs)},allow_nan=False))
                """;
        ObjectNode request=empty().put("module",module).put("function",function).put("key",key.name());request.set("input",input);var ids=request.putArray("regiments");regiments.forEach(ids::add);
        ProcessBuilder builder=new ProcessBuilder(python.toString(),"-B","-I","-c",invocation,root.toString()).directory(root.toFile());builder.environment().put("PYTHONDONTWRITEBYTECODE","1");Process process=builder.start();
        FutureTask<byte[]> stdout=new FutureTask<>(()->process.getInputStream().readNBytes(8*1024*1024+1)),stderr=new FutureTask<>(()->process.getErrorStream().readNBytes(16385));Thread.ofVirtual().start(stdout);Thread.ofVirtual().start(stderr);
        try{byte[] body=bytes(request);if(body.length>8*1024*1024)throw new IllegalStateException("original input bound exceeded");try(var stream=process.getOutputStream()){stream.write(body);}if(!process.waitFor(60,TimeUnit.SECONDS))throw new IllegalStateException("original monthly producer timeout");byte[] out=stdout.get(5,TimeUnit.SECONDS),err=stderr.get(5,TimeUnit.SECONDS);if(out.length>8*1024*1024||err.length>16384||process.exitValue()!=0)throw new IllegalStateException("original monthly producer exit="+process.exitValue()+": "+new String(err,StandardCharsets.UTF_8));verify(manifest);return get(closed(parse(out),"value"),"value");}finally{if(process.isAlive()){process.destroyForcibly();process.waitFor(5,TimeUnit.SECONDS);}}
    }
}

