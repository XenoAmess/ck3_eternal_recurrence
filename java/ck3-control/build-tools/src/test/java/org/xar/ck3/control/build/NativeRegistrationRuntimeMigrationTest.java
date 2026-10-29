package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Real request/codec/entrypoint regressions; fixture bytes grant no native execution authority. */
final class NativeRegistrationRuntimeMigrationTest {
    @TempDir Path temporary;

    @Test void explicitCurrentRuntimeRoundTripsThroughTheActualRequestReader() throws IOException {
        var runtime=current("inventory.json");
        var registration=request(NativeBridgeBuild.REGISTER_REQUEST_SCHEMA,NativeBridgeBuild.Stage.REGISTER,runtime);
        var pin=pin("current-register.json",RootNativePlanJson.mapper().writeValueAsString(registration));
        assertEquals(registration,NativeBridgeBuild.readRequest(pin));
        NativeBridgeBuild.requireCurrentRequest(registration);
        assertThrows(IOException.class,()->NativeBridgeBuild.readAccepted(pin,NativeBridgeBuild.Stage.REGISTER));
        assertThrows(IOException.class,()->NativeBridgeDefender.verifyHelperRuntime(temporary,runtime));
    }

    @Test void oldRuntimeRemainsExactHistoricalDataAndCannotIssueAnotherRegistration() throws IOException {
        var legacy=legacy();
        var request=request(NativeBridgeBuild.REQUEST_SCHEMA,NativeBridgeBuild.Stage.REGISTER,legacy);
        var pin=pin("historical-register.json",RootNativePlanJson.mapper().writeValueAsString(request));
        assertEquals(request,NativeBridgeBuild.readRequest(pin));
        String reason=assertThrows(IOException.class,()->NativeBridgeBuild.requireCurrentRequest(request)).getMessage();
        Path output=temporary.resolve("must-not-write.json");
        assertEquals(reason,assertThrows(IOException.class,()->NativeBridgeBuild.writeRequest(request,temporary,output)).getMessage());
        assertFalse(Files.exists(output));
        assertEquals(reason,assertThrows(IOException.class,()->NativeBridgeBuild.execute(pin,null)).getMessage());
        var limits=new NativeBridgeRootGate.Limits("/root",pin("unused-capacity.json","{}"),Instant.now().plusSeconds(30),64L<<20,32L<<20,20);
        assertEquals(reason,assertThrows(IOException.class,()->NativeBridgeRootGate.open(pin,limits)).getMessage());
        assertFalse(Files.exists(request.stageRoot()));
        assertFalse(Files.exists(request.scratchRoot().resolve("ROOT-NATIVE-BUILD.lock")));
    }

    @Test void onlyTheExplicitRegisterSuccessorMayLinkToV2EnvAndBuild() throws IOException {
        var env=request(NativeBridgeBuild.REQUEST_SCHEMA,NativeBridgeBuild.Stage.ENV,null);
        var build=request(NativeBridgeBuild.REQUEST_SCHEMA,NativeBridgeBuild.Stage.BUILD,null);
        var registration=request(NativeBridgeBuild.REGISTER_REQUEST_SCHEMA,NativeBridgeBuild.Stage.REGISTER,current("first.json"));
        assertTrue(NativeBridgeBuild.sameBuild(env,registration));
        assertTrue(NativeBridgeBuild.sameBuild(registration,build));
        assertFalse(NativeBridgeBuild.sameBuild(registration,request(NativeBridgeBuild.REGISTER_REQUEST_SCHEMA,NativeBridgeBuild.Stage.REGISTER,current("second.json"))));
        assertFalse(NativeBridgeBuild.sameBuild(registration,request(NativeBridgeBuild.LEGACY_REQUEST_SCHEMA,NativeBridgeBuild.Stage.ENV,legacy())));
        assertThrows(IllegalArgumentException.class,()->request(NativeBridgeBuild.REGISTER_REQUEST_SCHEMA,NativeBridgeBuild.Stage.ENV,null));
        assertThrows(IllegalArgumentException.class,()->request(NativeBridgeBuild.REGISTER_REQUEST_SCHEMA,NativeBridgeBuild.Stage.REGISTER,legacy()));
        assertThrows(IllegalArgumentException.class,()->request(NativeBridgeBuild.REQUEST_SCHEMA,NativeBridgeBuild.Stage.REGISTER,current("first.json")));
    }

    @Test void newRuntimeCodecRejectsAliasesMissingNullUnknownAndWrongTypes() throws IOException {
        var mapper=RootNativePlanJson.mapper();
        ObjectNode original=mapper.valueToTree(current("inventory.json"));
        assertEquals(6,original.size());
        assertEquals(current("inventory.json"),mapper.treeToValue(original,NativeBridgeDefender.Runtime.class));
        for(String field:List.of("schema","python_base_root","venv_root","python","helper","inventory_ref")){
            ObjectNode missing=original.deepCopy();missing.remove(field);
            assertThrows(IOException.class,()->mapper.treeToValue(missing,NativeBridgeDefender.Runtime.class));
            ObjectNode nullable=original.deepCopy();nullable.putNull(field);
            assertThrows(IOException.class,()->mapper.treeToValue(nullable,NativeBridgeDefender.Runtime.class));
        }
        ObjectNode extra=original.deepCopy();extra.put("complete_python_files",true);
        assertThrows(IOException.class,()->mapper.treeToValue(extra,NativeBridgeDefender.Runtime.class));
        ObjectNode wrong=original.deepCopy();wrong.put("schema",false);
        assertThrows(IOException.class,()->mapper.treeToValue(wrong,NativeBridgeDefender.Runtime.class));
        ObjectNode unknown=original.deepCopy();unknown.put("schema","xar.native-register-manifest-runtime/v3");
        assertThrows(IOException.class,()->mapper.treeToValue(unknown,NativeBridgeDefender.Runtime.class));
        assertThrows(IOException.class,()->mapper.readValue("{\"schema\":\"one\",\"schema\":\"two\"}",NativeBridgeDefender.Runtime.class));
    }

    @Test void legacySixFieldDecoderDoesNotSilentlyCreateTheNewBranch() throws IOException {
        var mapper=RootNativePlanJson.mapper();ObjectNode old=mapper.valueToTree(legacy());
        assertEquals(6,old.size());
        assertInstanceOf(NativeBridgeDefender.HelperRuntime.class,mapper.treeToValue(old,NativeBridgeDefender.Runtime.class));
        old.put("schema",NativeBridgeDefender.ManifestRuntime.SCHEMA);
        assertThrows(IOException.class,()->mapper.treeToValue(old,NativeBridgeDefender.Runtime.class));
    }

    @Test void v1RedirectorManifestRemainsReadableButCannotIssueNewRegistration()throws IOException {
        var old=new NativeBridgeDefender.ManifestRuntime(NativeBridgeDefender.ManifestRuntime.SCHEMA,
                temporary.resolve("base"),temporary.resolve("venv"),pin("venv/Scripts/python.exe","venv launcher"),
                pin("helper.py","fixture"),pin("old-inventory.json","historical fixture"));
        assertEquals(NativeBridgeDefender.HelperInterpreterRoute.HISTORICAL_VENV_REDIRECTOR,old.interpreterRoute());
        var request=request(NativeBridgeBuild.REGISTER_REQUEST_SCHEMA,NativeBridgeBuild.Stage.REGISTER,old);
        var pin=pin("v1-redirector-register.json",RootNativePlanJson.mapper().writeValueAsString(request));
        assertEquals(request,NativeBridgeBuild.readRequest(pin));
        assertThrows(IOException.class,()->NativeBridgeBuild.requireCurrentRequest(request));
        assertThrows(IOException.class,()->NativeBridgeBuild.execute(pin,null));
        assertFalse(Files.exists(request.stageRoot()));
    }
    @Test void directBaseRequestRejectsAVenvOrForeignInterpreterAndUnqualifiedInventory()throws IOException {
        var runtime=current("direct-inventory.json");
        assertEquals(NativeBridgeDefender.HelperInterpreterRoute.DIRECT_BASE,runtime.interpreterRoute());
        NativeBridgeDefender.requireDirectHelperRuntime(runtime);
        var mapper=RootNativePlanJson.mapper();ObjectNode original=mapper.valueToTree(runtime);
        for(String path:List.of("venv/Scripts/python.exe","foreign/python.exe")){
            ObjectNode wrong=original.deepCopy();wrong.set("python",mapper.valueToTree(pin(path,"wrong interpreter")));
            assertThrows(IOException.class,()->mapper.treeToValue(wrong,NativeBridgeDefender.Runtime.class));
        }
        assertThrows(IOException.class,()->NativeBridgeDefender.directBaseRuntime(temporary,pin("unqualified-inventory.json","{}")));
    }
    private NativeBridgeBuild.Request request(String schema,NativeBridgeBuild.Stage stage,NativeBridgeDefender.Runtime runtime)throws IOException {
        Path source=temporary.resolve("source");Files.createDirectories(source);
        if(!Files.exists(source.resolve("CMakeLists.txt")))Files.writeString(source.resolve("CMakeLists.txt"),"option(XAR_CK3_FIXTURE \"fixture\" OFF)\n");
        return new NativeBridgeBuild.Request(schema,"software-fixture",stage,temporary,source,NativeBridgeBuild.inventory(source),
                temporary.resolve("build"),temporary.resolve("scratch"),pin("tools.json","unqualified fixture"),
                new NativeBridgeBuild.Toolchain(pin("cmd.exe","fixture"),pin("vcvars64.bat","fixture"),pin("java.exe","fixture"),
                        pin("cmake.exe","fixture"),pin("ninja.exe","fixture"),pin("cl.exe","fixture"),pin("link.exe","fixture")),
                List.of(new NativeBridgeBuild.Definition("XAR_CK3_FIXTURE",NativeBridgeBuild.SwitchValue.OFF)),4,
                stage==NativeBridgeBuild.Stage.ENV?null:pin("env.json","unqualified"),
                stage==NativeBridgeBuild.Stage.REGISTER?pin("build.json","unqualified"):null,runtime);
    }
    private NativeBridgeDefender.ManifestRuntime current(String name)throws IOException {
        return new NativeBridgeDefender.ManifestRuntime(NativeBridgeDefender.ManifestRuntime.DIRECT_SCHEMA,
                temporary.resolve("base"),temporary.resolve("venv"),pin("base/python.exe","fixture"),pin("helper.py","fixture"),pin(name,"not an inventory"));
    }
    private NativeBridgeDefender.HelperRuntime legacy()throws IOException {
        var python=pin("python.exe","fixture");var helper=pin("helper.py","fixture");
        return new NativeBridgeDefender.HelperRuntime(temporary.resolve("base"),temporary.resolve("venv"),python,helper,List.of(python),List.of(helper));
    }
    private ControlBuild.FileRef pin(String name,String value)throws IOException {
        Path file=temporary.resolve(name);Files.createDirectories(file.getParent());if(!Files.exists(file))Files.writeString(file,value);return ControlBuild.FileRef.measure(file);
    }
}
