package org.xar.ck3.control.wave2.runtime.closedadoption;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.Base64;
import java.util.HashMap;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.RootSoftwareChildBootstrap;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;
import static org.junit.jupiter.api.Assertions.*;

/** Actual RAM transport producer and direct-entry installer. Source fixtures confer no SDK or Native authority. */
final class CompositionBundleTransportTest {
    @TempDir Path temporary;
    @Test void actualPythonProducerAndJavaCollectorPreserveEmptyAndMultiChunkFiles() throws Exception {
        Path repo=Path.of(required("xar.repository.root")).toRealPath();Path python=Path.of(required("xar.python"));
        Path continuity=Path.of(required("xar.recovery.transport"));Path prepare=Path.of(required("xar.recovery.prepare"));
        Path fixture=temporary.resolve("source-fixture");Path modules=fixture.resolve("tools/g2_saved_campaign");Files.createDirectories(modules);
        Files.writeString(fixture.resolve("tools/__init__.py"),"");Files.writeString(modules.resolve("__init__.py"),"");
        Path owner=modules.resolve("root_current_saved_campaign_cold_owner_v1.py");Files.writeString(owner,"SOURCE_FIXTURE_ONLY=True\n");
        Files.setLastModifiedTime(owner,java.nio.file.attribute.FileTime.fromMillis(1_700_000_000_000L));
        assertEquals(1_700_000_000_000L,Files.getLastModifiedTime(owner).toMillis());
        Path transport=modules.resolve("current_saved_continuity_v1.py");Files.writeString(transport,"# not executed\n");
        Path freeze=temporary.resolve("source-only.json");Files.writeString(freeze,"{}");
        var binding=new RootSoftwareChildBootstrap.SdkLineageBinding(RootSoftwareChildBootstrap.SdkLineageKind.ORIGINAL_SOURCE32,
                ControlBuild.FileRef.measure(freeze),null);
        var settings=new WindowsFileWriterSession.Settings(python,fixture,temporary.resolve("unused"),96L<<20,
                Duration.ofSeconds(20),Instant.now().plusSeconds(25),System.getenv(),exact(transport),exact(owner),()->{},Optional.of(binding));
        String prefix=WindowsFileWriterSession.entryInstallationPrefix(settings);
        var environment=new HashMap<>(System.getenv());environment.put("PYTHONDONTWRITEBYTECODE","1");
        environment.put("TMP",temporary.toString());environment.put("TEMP",temporary.toString());
        Path stdout=temporary.resolve("frames.jsonl"),stderr=temporary.resolve("stderr.log");
        var command=new WindowsJobProcess.CommandSpec(python,List.of("-I","-B","-X","utf8","-c",PROGRAM,
                repo.toString(),continuity.toString(),prepare.toString(),Base64.getEncoder().encodeToString(prefix.getBytes(java.nio.charset.StandardCharsets.UTF_8)),
                temporary.toString()),temporary,environment,stdout,stderr,96L<<20);
        try(var child=WindowsJobProcess.start(command)) {
            var exit=child.await(Duration.ofSeconds(20),Instant.now().plusSeconds(20),()->{});
            assertTrue(exit.passed(),()->read(stderr));assertEquals(0,exit.accounting().activeProcesses());
        }
        var chunks=new OriginalColdConsumerSession.CompositionChunks();var ref=reference();
        for(String line:Files.readAllLines(stdout))chunks.accept((ObjectNode)StrictJson.parse(line.getBytes(java.nio.charset.StandardCharsets.UTF_8)),"source-fixture",ref,ref);
        var files=chunks.complete();assertEquals(2,files.size());assertEquals(70_000,files.get(0).content().length);
        assertEquals(0,files.get(1).content().length);assertFalse(Files.exists(temporary.resolve("a.py")));
    }
    @Test void malformedChunksAndIncompleteFilesAreRejected() {
        var ref=reference();var good=frame(new byte[]{1,2,3},0,3);var collector=new OriginalColdConsumerSession.CompositionChunks();
        collector.accept(good,"source-fixture",ref,ref);assertEquals(3,collector.complete().get(0).content().length);
        for(String key:List.of("file_index","offset","bytes")) {
            var wrong=good.deepCopy();wrong.put(key,true);
            assertThrows(RuntimeException.class,()->new OriginalColdConsumerSession.CompositionChunks().accept(wrong,"source-fixture",ref,ref));
            var floating=good.deepCopy();floating.put(key,1.0);
            assertThrows(RuntimeException.class,()->new OriginalColdConsumerSession.CompositionChunks().accept(floating,"source-fixture",ref,ref));
        }
        for(var wrong:List.of(good.deepCopy().put("machine_id","other"),good.deepCopy().put("offset",1),
                good.deepCopy().put("sha256","f".repeat(64)),good.deepCopy().put("data_base64","AQID="))) {
            assertThrows(RuntimeException.class,()->new OriginalColdConsumerSession.CompositionChunks().accept(wrong,"source-fixture",ref,ref));
        }
        var partial=new OriginalColdConsumerSession.CompositionChunks();partial.accept(frame(new byte[]{1},0,2),"source-fixture",ref,ref);
        assertThrows(RuntimeException.class,partial::complete);
    }
    @Test void typedCommandAndWireRoundtripDoNotAcceptCallerInstallationCode() {
        var command=new OriginalColdConsumerSession.ComposeBundle(reference());
        assertInstanceOf(OriginalColdConsumerSession.ComposeBundle.class,OriginalColdConsumerSession.decodeOperation(
                StrictJson.object().put("kind",command.kind().name()).get("kind"),StrictJson.parse(StrictJson.canonical(command.arguments()))));
        var bad=command.arguments();bad.put("entry_installation_prefix","caller supplied code");
        assertThrows(RuntimeException.class,()->OriginalColdConsumerSession.decodeOperation(
                StrictJson.object().put("kind",command.kind().name()).get("kind"),bad));
    }
    private ExactRef reference() {return new ExactRef(temporary.resolve("metadata-only.json").toString(),1,"0".repeat(64));}
    private ObjectNode frame(byte[] content,long offset,long size) {
        var row=StrictJson.object();row.put("schema","xar.java-closed-composition-chunk/v1");row.put("machine_id","source-fixture");
        row.set("basis_ref",reference().toJson());row.set("validation_ref",reference().toJson());row.put("file_index",0);
        row.put("path",temporary.resolve("a.py").toString());row.put("offset",offset);row.put("bytes",size);
        row.put("sha256",RecoveryEvidence.sha256(content));row.put("data_base64",Base64.getEncoder().encodeToString(content));return row;
    }
    private static ExactRef exact(Path path) throws Exception {var pin=ControlBuild.FileRef.measure(path);return new ExactRef(pin.path(),pin.bytes(),pin.sha256());}
    private static String required(String key) {String value=System.getProperty(key);assertNotNull(value,"explicit selected source property "+key);return value;}
    private static String read(Path path) {try{return Files.readString(path);}catch(java.io.IOException error){return error.toString();}}
    private static final String PROGRAM="""
import ast,base64,hashlib,json,sys
from pathlib import Path
from typing import Iterator
repo,continuity,prepare,prefix,root=sys.argv[1:]
sys.path.insert(0,repo)
from tools.g2_saved_campaign.current_saved_basis_v1 import ExactRefV1,JsonObject,need
scope={'hashlib':hashlib,'ExactRefV1':ExactRefV1,'JsonObject':JsonObject,'Iterator':Iterator,'need':need}
tree=ast.parse(Path(continuity).read_text(encoding='utf-8'))
node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_java_closed_composition_frames_v1')
exec(compile(ast.Module(body=[node],type_ignores=[]),continuity,'exec'),scope)
entry_scope={'ast':ast,'need':need}
tree=ast.parse(Path(prepare).read_text(encoding='utf-8'))
node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='emit_java_root_sdk_installation_v1')
exec(compile(ast.Module(body=[node],type_ignores=[]),prepare,'exec'),entry_scope)
prefix=base64.b64decode(prefix).decode('utf-8')
entry=b'\"\"\"source fixture\"\"\"\\nfrom __future__ import annotations\\nassert __name__=="direct_mcp_source_fixture"\\n'
emitted=entry_scope['emit_java_root_sdk_installation_v1'](entry,prefix)
assert emitted.index(b'from __future__')<emitted.index(prefix.encode())<emitted.index(b'assert __name__')
exec(compile(emitted,'<actual direct MCP source installation fixture>','exec'),{'__name__':'direct_mcp_source_fixture'})
owner=sys.modules['tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1']
assert owner.SOURCE_FIXTURE_ONLY is True
ref=ExactRefV1(str(Path(root)/'metadata-only.json'),1,'0'*64)
files={str(Path(root)/'a.py'):b'a'*70000,str(Path(root)/'b-empty.py'):b''}
for frame in scope['_java_closed_composition_frames_v1'](files,machine_id='source-fixture',basis_ref=ref,validation_ref=ref):
    print(json.dumps(frame,separators=(',',':')))
""";
}
