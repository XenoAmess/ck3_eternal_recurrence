package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Locale;
import java.util.ServiceLoader;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.planning.army.H2743StockPredicateAdmission;
import org.xar.ck3.control.application.planning.army.H2743StockPredicateAdmission.Input;
import org.xar.ck3.control.application.planning.army.H2743StockPredicateAdmission.Profile;

/** Software source files exercise the original producer and real held verifier. They are not Native qualification. */
public final class RootH2743StockPredicateAdmissionTest {
    @TempDir Path temporary;
    private static final RootH2743StockPredicateAdmission.Limits LIMITS=new RootH2743StockPredicateAdmission.Limits(128,8388608,1048576,8388608);
    private record Vector(Input input,JsonNode expected) { }
    @Test public void originalSoftwareProducerToHeldVerifierAndStrictDataRoundTrip()throws Exception {
        Vector v=vector(false);var data=RootH2743StockPredicateAdmission.verifyDataOnly(v.input(),LIMITS);
        assertEquals(Profile.EXPLICIT_STOCK_RELEASE,data.profile());assertEquals(v.expected(),node(data.sourceReceipt()));
        assertEquals(node(data.sourceReceipt()),node(H2743StockPredicateAdmission.validateSourceReceipt(data.sourceReceipt(),data.profile())));
        assertThrows(IllegalArgumentException.class,()->H2743StockPredicateAdmission.validateSourceReceipt(data.sourceReceipt(),Profile.HISTORICAL_BASELINE));
        assertFalse(v.expected().get("native_condition_observed").booleanValue());assertFalse(v.expected().get("ck3_started").booleanValue());
        var decoded=H2743StockPredicateAdmission.decodeData(H2743StockPredicateAdmission.encodeData(data));assertEquals(data.profile(),decoded.profile());assertEquals(data.completeFiles(),decoded.completeFiles());assertEquals(node(data.sourceReceipt()),node(decoded.sourceReceipt()));
        ObjectNode corrupted=(ObjectNode)node(H2743StockPredicateAdmission.encodeData(data));((ObjectNode)corrupted.get("complete_files").get(0)).put("size_bytes",true);assertThrows(IllegalArgumentException.class,()->H2743StockPredicateAdmission.decodeData(new RawJson(DriverJson.encodeNode(corrupted))));
        assertTrue(data.completeFiles().size()>20);assertTrue(data.completeFiles().stream().allMatch(f->f.sha256().matches("[0-9A-F]{64}")));
    }
    @Test public void changedCompiledSourceCannotBorrowUnchangedPins()throws Exception {Vector v=vector(false);Files.writeString(v.input().nativeSourceCheckout().resolve("native.cpp"),"changed");assertThrows(IllegalArgumentException.class,()->RootH2743StockPredicateAdmission.verifyDataOnly(v.input(),LIMITS));}
    @Test public void nullFrozenSourceIdentityIsRejectedByTheActualProducerPath()throws Exception {Vector v=vector(true);assertThrows(IllegalArgumentException.class,()->RootH2743StockPredicateAdmission.verifyDataOnly(v.input(),LIMITS));}
    @Test public void booleanExitCodeDoesNotEqualIntegerZero()throws Exception {Vector v=vector(false);Files.writeString(temporary.resolve("fixture/dll/build-result.json"),"{\"exit_code\":false}");assertThrows(IllegalArgumentException.class,()->RootH2743StockPredicateAdmission.verifyDataOnly(v.input(),LIMITS));}
    @Test public void missingReleaseOptInAndChangedRouteAreUnavailable()throws Exception {
        Vector v=vector(false);Path cache=temporary.resolve("fixture/dll/build/CMakeCache.txt");Files.writeString(cache,"CMAKE_BUILD_TYPE:STRING=Release\n");assertThrows(IllegalArgumentException.class,()->RootH2743StockPredicateAdmission.verifyDataOnly(v.input(),LIMITS));
        Files.writeString(cache,"CMAKE_BUILD_TYPE:STRING=Release\nXAR_CK3_ENABLE_H2743_STOCK_PREDICATE_READER_V1:BOOL=ON\n");Files.writeString(temporary.resolve("fixture/route.json"),"{}");assertThrows(IllegalArgumentException.class,()->RootH2743StockPredicateAdmission.verifyDataOnly(v.input(),LIMITS));
    }
    @Test public void explicitFileAndByteLimitsStopBeforeAnUnboundedClosure()throws Exception {Vector v=vector(false);assertThrows(IOException.class,()->RootH2743StockPredicateAdmission.verifyDataOnly(v.input(),new RootH2743StockPredicateAdmission.Limits(2,8388608,1048576,8388608)));}
    /** Genuine original startup scope only; no implementation is supplied here. */
    public interface ActualReleaseInputs {void withActualInputs(ActualCheck mandatory)throws Exception;}
    @FunctionalInterface public interface ActualCheck {
        void require(RootRuntimeContext actual,RootManagedSessionScope physical,Input sources,
                RootH2743StockPredicateAdmission.Limits limits,
                org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
                org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete held)throws Exception;
    }
    @Test public void actualReleasePairAndManagedScopeAreMandatory()throws Exception {
        List<ActualReleaseInputs> actual=ServiceLoader.load(ActualReleaseInputs.class).stream().map(ServiceLoader.Provider::get).toList();
        if(actual.size()!=1)throw new IOException("MISSING_NOT_RUN: actual reviewed Release pair, independent pins, retained Managed Root and stock runtime input provider");
        var called=new java.util.concurrent.atomic.AtomicBoolean();
        actual.getFirst().withActualInputs((context,physical,input,limits,same,held)->{
            if(called.get())throw new IOException("actual H2743 inputs invoked twice");
            try(var issuer=RootH2743StockPredicateAdmission.bind(context,physical,input,limits)){
                var escaped=new java.util.concurrent.atomic.AtomicReference<RootH2743StockPredicateAdmission.Admission>();
                issuer.withAdmission(same,held,proof->{assertEquals(Profile.EXPLICIT_STOCK_RELEASE,proof.data(same,held).profile());escaped.set(proof);return null;});
                assertThrows(IOException.class,()->escaped.get().requireCurrent(same,held));
            }
            called.set(true);
        });
        if(!called.get())throw new IOException("MISSING_NOT_RUN: actual H2743 input provider did not exercise original Root source issuer");
    }
    private Vector vector(boolean invalid)throws Exception {
        String raw=System.getProperty("xar.native.producer.source");if(raw==null||raw.isBlank())throw new IOException("MISSING_NOT_RUN: actual original native producer source input");
        String python=System.getProperty("xar.native.producer.python");if(python==null||python.isBlank())throw new IOException("MISSING_NOT_RUN: actual original native producer Python input");
        Path producer=Path.of(raw).toAbsolutePath().normalize();Path pkg=producer.getParent().getParent();
        Path baseline=pkg.resolve("h2743_exit_source_pair.py"),stock=pkg.resolve("h2743_stock_predicate_admission.py");Path fixture=pkg.getParent().getParent().resolve("tests/unit/test_h2743_stock_predicate_consumer.py");
        exact(baseline,"06ce121f6747eca71f38e6d53af5c88c25f91fca056714c68c879b1bb0ac7ae3");exact(stock,"de9816f26acdc5e76899fa87bdaefb4d5c7c16b49e626bf1daeecf531f7b3bb8");exact(fixture,"6fed5fdf2dce4af272f0a6b89c3e1a1296eaa6c2017763bf551c3ae3550854b8");
        Path output=temporary.resolve("fixture");Files.createDirectories(output);
        Process p=new ProcessBuilder(python,"-c",SCRIPT,pkg.toString(),fixture.toString(),output.toString(),invalid?"1":"0").redirectError(ProcessBuilder.Redirect.INHERIT).start();
        if(!p.waitFor(30,TimeUnit.SECONDS)){p.destroyForcibly();throw new IOException("original source producer timeout");}byte[] stdout=p.getInputStream().readNBytes(65537);assertEquals(0,p.exitValue());assertTrue(stdout.length<=65536);
        exact(baseline,"06ce121f6747eca71f38e6d53af5c88c25f91fca056714c68c879b1bb0ac7ae3");exact(stock,"de9816f26acdc5e76899fa87bdaefb4d5c7c16b49e626bf1daeecf531f7b3bb8");exact(fixture,"6fed5fdf2dce4af272f0a6b89c3e1a1296eaa6c2017763bf551c3ae3550854b8");
        JsonNode result=node(new RawJson(stdout));return new Vector(new Input(Path.of(result.get("pair").textValue()),Path.of(result.get("pins").textValue()),Path.of(result.get("checkout").textValue())),result.get("expected"));
    }
    private static JsonNode node(RawJson raw){return DriverJson.toNode(DriverJson.object(raw.bytes(),1048576));}
    private static void exact(Path path,String sha)throws IOException {if(!Files.isRegularFile(path)||Files.size(path)>1048576||!DriverJson.sha256(Files.readAllBytes(path)).equals(sha))throw new IOException("MISSING_OR_CHANGED_ORIGINAL_SOURCE: "+path);}
    private static final String SCRIPT="""
        import ast,hashlib,importlib.util,json,sys,types
        from pathlib import Path
        pkg,fixture,root=map(Path,sys.argv[1:4])
        parent=types.ModuleType('h2743_original'); parent.__path__=[str(pkg)]
        sys.modules['h2743_original']=parent
        for name in ('h2743_exit_source_pair','h2743_stock_predicate_admission'):
            spec=importlib.util.spec_from_file_location('h2743_original.'+name,pkg/(name+'.py'))
            module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
        stock=sys.modules['h2743_original.h2743_stock_predicate_admission']
        source=ast.parse(fixture.read_text(encoding='utf-8'))
        selected=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in ('write','fixture_pair')]
        assert len(selected)==2
        namespace={'Path':Path,'hashlib':hashlib,'json':json,'EVIDENCE_SCHEMA':stock.EVIDENCE_SCHEMA,'PAIR_SCHEMA':stock.PAIR_SCHEMA,'PINS_SCHEMA':stock.PINS_SCHEMA}
        exec(compile(ast.Module(body=selected,type_ignores=[]),str(fixture),'exec'),namespace)
        pair,pins,checkout=namespace['fixture_pair'](root,invalid_source_identity=sys.argv[4]=='1')
        expected=None
        if sys.argv[4]!='1':expected,_=stock.verify_admitted_stock_predicate_pair(pair,pins_path=pins,native_source_checkout=checkout)
        print(json.dumps({'pair':str(pair),'pins':str(pins),'checkout':str(checkout),'expected':expected}))
        """;
}
