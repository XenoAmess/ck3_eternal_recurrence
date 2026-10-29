package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Objects;
import java.util.concurrent.TimeUnit;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.army.H2743StockPredicateAdmission.Input;

/** Test-only original producer/transport capture. Synthetic software files never authorize a Native read. */
public final class StockConsumerOriginalInputs {
    private StockConsumerOriginalInputs() { }
    public record Vector(Input input,RawJson before,RawJson after,RawJson nativeResult,
            RawJson expectedResult,RawJson expectedSource) {
        public Vector {Objects.requireNonNull(input);Objects.requireNonNull(before);Objects.requireNonNull(after);Objects.requireNonNull(nativeResult);Objects.requireNonNull(expectedResult);Objects.requireNonNull(expectedSource);}
    }
    private record Original(String relative,String sha256) { }
    private static final List<Original> ORIGINALS=List.of(
        new Original("h2743_exit_source_pair.py","06ce121f6747eca71f38e6d53af5c88c25f91fca056714c68c879b1bb0ac7ae3"),
        new Original("h2743_stock_predicate_admission.py","de9816f26acdc5e76899fa87bdaefb4d5c7c16b49e626bf1daeecf531f7b3bb8"),
        new Original("bridge/defender_dejure_exit_terms_v1.py","fdb5155ed55d5c1c700cdeb4fe8235f9e6317515d70341fe58a6860f5ec6dc0a"),
        new Original("bridge/h2743_exit_readonly_transport.py","1e69bf57ba441e0ba2d9a19f39ce8570dafed5644329ee3336ac6b21cf9ee92e"),
        new Original("bridge/driver.py","eed449063debf1a84216a350f0178d64a9a6602bbfcc266298a810a9bb736fb6"));
    public static Vector capture(Path outputRoot)throws IOException,InterruptedException {
        Objects.requireNonNull(outputRoot);if(!outputRoot.isAbsolute()||!outputRoot.normalize().equals(outputRoot))throw new IOException("absolute normalized software fixture root required");
        String producer=required("xar.native.producer.source"),python=required("xar.native.producer.python");
        Path pkg=Path.of(producer).toAbsolutePath().normalize().getParent().getParent();
        Path originalFixture=pkg.getParent().getParent().resolve("tests/unit/test_h2743_stock_predicate_consumer.py");
        verify(pkg,originalFixture);Files.createDirectories(outputRoot);
        Process process=new ProcessBuilder(python,"-c",SCRIPT,pkg.toString(),originalFixture.toString(),outputRoot.toString()).redirectError(ProcessBuilder.Redirect.INHERIT).start();
        boolean finished=false;
        try {
            finished=process.waitFor(30,TimeUnit.SECONDS);if(!finished)throw new IOException("original stock software producer timeout");
            byte[] stdout=process.getInputStream().readNBytes(131073);if(stdout.length>131072||process.exitValue()!=0)throw new IOException("original stock producer failed/oversized exit="+process.exitValue());
            verify(pkg,originalFixture);JsonNode result=DriverJson.toNode(DriverJson.object(stdout,131072));
            var names=new java.util.HashSet<String>();result.fieldNames().forEachRemaining(names::add);if(!names.equals(java.util.Set.of("pair","pins","checkout","before","after","native_result","expected_result","expected_source")))throw new IOException("original stock producer output roster changed");
            Input input=new Input(path(result,"pair"),path(result,"pins"),path(result,"checkout"));
            return new Vector(input,raw(result,"before"),raw(result,"after"),raw(result,"native_result"),raw(result,"expected_result"),raw(result,"expected_source"));
        } finally {if(!finished)process.destroyForcibly();}
    }
    private static String required(String name)throws IOException {String value=System.getProperty(name);if(value==null||value.isBlank())throw new IOException("MISSING_NOT_RUN: original producer input "+name);return value;}
    private static Path path(JsonNode n,String name)throws IOException {JsonNode v=n.get(name);if(v==null||!v.isTextual())throw new IOException("missing original path "+name);return Path.of(v.textValue());}
    private static RawJson raw(JsonNode n,String name)throws IOException {JsonNode v=n.get(name);if(v==null||!v.isObject())throw new IOException("missing original object "+name);return new RawJson(DriverJson.encodeNode(v));}
    private static void verify(Path pkg,Path fixture)throws IOException {
        for(Original original:ORIGINALS)exact(pkg.resolve(original.relative()),original.sha256());
        exact(fixture,"6fed5fdf2dce4af272f0a6b89c3e1a1296eaa6c2017763bf551c3ae3550854b8");
    }
    private static void exact(Path path,String expected)throws IOException {if(!Files.isRegularFile(path)||Files.size(path)>1048576)throw new IOException("MISSING_OR_OVERSIZE_ORIGINAL_SOURCE: "+path);byte[] bytes;try(var input=Files.newInputStream(path)){bytes=input.readNBytes(1048577);}if(bytes.length>1048576||!DriverJson.sha256(bytes).equals(expected))throw new IOException("CHANGED_ORIGINAL_SOURCE: "+path);}
    private static final String SCRIPT="""
        import ast,copy,hashlib,importlib.util,json,sys,types
        from pathlib import Path
        pkg,fixture,root=map(Path,sys.argv[1:4])
        parent=types.ModuleType('h2743_original');parent.__path__=[str(pkg)];sys.modules[parent.__name__]=parent
        bridge=types.ModuleType('h2743_original.bridge');bridge.__path__=[str(pkg/'bridge')];sys.modules[bridge.__name__]=bridge
        def original(name,path):
            spec=importlib.util.spec_from_file_location('h2743_original.'+name,path)
            module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module);return module
        baseline_source=original('h2743_exit_source_pair',pkg/'h2743_exit_source_pair.py')
        stock=original('h2743_stock_predicate_admission',pkg/'h2743_stock_predicate_admission.py')
        driver_source=ast.parse((pkg/'bridge/driver.py').read_text(encoding='utf-8'))
        exceptions=[n for n in driver_source.body if isinstance(n,ast.ClassDef) and n.name=='BridgeUnavailableError']
        assert len(exceptions)==1
        driver_module=types.ModuleType('h2743_original.bridge.driver')
        exec(compile(ast.Module(body=exceptions,type_ignores=[]),str(pkg/'bridge/driver.py'),'exec'),driver_module.__dict__)
        sys.modules[driver_module.__name__]=driver_module
        normalizer=original('bridge.defender_dejure_exit_terms_v1',pkg/'bridge/defender_dejure_exit_terms_v1.py')
        transport=original('bridge.h2743_exit_readonly_transport',pkg/'bridge/h2743_exit_readonly_transport.py')
        test=ast.parse(fixture.read_text(encoding='utf-8'))
        functions=[n for n in test.body if isinstance(n,ast.FunctionDef) and n.name in ('write','fixture_pair','baseline')]
        assert len(functions)==3
        ns={'Path':Path,'hashlib':hashlib,'json':json,'deepcopy':copy.deepcopy,
            'EVIDENCE_SCHEMA':stock.EVIDENCE_SCHEMA,'PAIR_SCHEMA':stock.PAIR_SCHEMA,'PINS_SCHEMA':stock.PINS_SCHEMA,
            'RESOURCES':normalizer.RESOURCES,'SCHEMA':normalizer.SCHEMA,'UNAVAILABLE_REASONS':normalizer.UNAVAILABLE_REASONS,
            'BASELINE_STEP':transport.BASELINE_STEP}
        exec(compile(ast.Module(body=functions,type_ignores=[]),str(fixture),'exec'),ns)
        cls=next(n for n in test.body if isinstance(n,ast.ClassDef) and n.name=='StockPredicateConsumerTest')
        method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='test_production_transport_native_frame_and_replay_guards')
        frame_nodes=[n.value for n in ast.walk(method) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='frame' for t in n.targets)]
        assert len(frame_nodes)==1
        frame=ast.literal_eval(frame_nodes[0]);ns['frame']=frame
        classes=[n for n in ast.walk(method) if isinstance(n,ast.ClassDef) and n.name=='Driver'];assert len(classes)==1
        exec(compile(ast.Module(body=classes,type_ignores=[]),str(fixture),'exec'),ns)
        pair,pins,checkout=ns['fixture_pair'](root)
        expected_source,admission=stock.verify_admitted_stock_predicate_pair(pair,pins_path=pins,native_source_checkout=checkout)
        class RecordingDriver(ns['Driver']):
            def __init__(self):super().__init__();self.original_results=[]
            def _execute_primitive_step(self,step,**kwargs):
                actual=super()._execute_primitive_step(step,**kwargs);self.original_results.append(copy.deepcopy(actual));return actual
        actual=RecordingDriver();before=copy.deepcopy(actual.frames[0]);after=copy.deepcopy(actual.frames[1])
        transport.bind_admitted_stock_predicates(actual,admission)
        expected=transport.query_h2743_exit_baseline(actual,expected_frame=before)
        assert len(actual.original_results)==1 and actual.frames==[]
        assert actual._h2743_stock_last_mailbox_sequence==9
        print(json.dumps(dict(pair=str(pair),pins=str(pins),checkout=str(checkout),before=before,after=after,
            native_result=actual.original_results[0],expected_result=expected,expected_source=expected_source),allow_nan=False))
        """;
}
