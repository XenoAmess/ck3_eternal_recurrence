package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.service.mcp.McpCancellation;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.Arguments;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.Presence;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.ToolCall;
import org.xar.ck3.control.wave2.events.catalog.VanillaEventCatalog;
import static org.xar.ck3.control.service.root.RootSaveArtifactInspector.*;

/** Real temporary files + independent original Python. Missing native/dependency/fixture environment fails, never skips. */
final class RootSaveArtifactInspectorTest {
    @TempDir Path temporary;
    private static final String ORIGINAL_SHA = "3cca37c11eb43778d195f7d818359bd4f73d18ede85262e344bf56bdd9305ad8";
    private static final String ORIGINAL = """
        import sys,os,hashlib,importlib.util,json,zipfile,struct,warnings,unicodedata
        from pathlib import Path
        warnings.simplefilter('ignore',UserWarning)
        root=Path(sys.argv[1]).resolve();source=root/'ck3_autonomous_player/src/xar_autoplayer/ck3_save_artifacts.py'
        raw=source.read_bytes()
        if len(raw)!=6247 or hashlib.sha256(raw).hexdigest()!=sys.argv[2]:raise RuntimeError('original save producer source drift')
        spec=importlib.util.spec_from_file_location('actual_ck3_save_artifacts',source)
        module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
        profile=Path(sys.argv[3]);profile.mkdir();saves=profile/'save games';saves.mkdir();mode=sys.argv[4]
        if mode=='all':
            (profile/'last_save.ck3').write_bytes(b'not a CK3 save')
            (saves/'raw.ck3').write_bytes(b'SAV0100\\nmeta_data={\\n}\\n')
            (saves/'binary.ck3').write_bytes(b'SAV0101e741a8ef0000864d\\nU1\\x01\\x00\\x03\\x00opaque')
            for method in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED,zipfile.ZIP_BZIP2,zipfile.ZIP_LZMA):
                with zipfile.ZipFile(saves/f'method{method}.ck3','w',compression=method) as z:
                    z.writestr('meta-ß-𐐀',b'meta');z.writestr('gamestate',b'whole canonical gamestate'*64)
            with zipfile.ZipFile(saves/'missing.ck3','w') as z:z.writestr('meta',b'no gamestate')
            with zipfile.ZipFile(saves/'zip64.ck3','w') as z:
                with z.open('gamestate','w',force_zip64=True) as out:out.write(b'zip64 body')
            for name in ('Straße','STRASSe2','I','ı','İ','𐐀'):(saves/(name+'.ck3')).write_bytes(b'SAVf\\r\\nmeta_data={')
        elif mode=='crc':
            with zipfile.ZipFile(saves/'late-crc.ck3','w') as z:
                z.writestr('gamestate',b'state')
                for i in range(130):z.writestr(f'member{i}',b'complete CRC body')
            p=saves/'late-crc.ck3'
            with zipfile.ZipFile(p) as z:entry=z.getinfo('member129')
            data=bytearray(p.read_bytes());at=entry.header_offset;n,e=struct.unpack_from('<HH',data,at+26);data[at+30+n+e]^=1;p.write_bytes(data)
        elif mode=='duplicate':
            with zipfile.ZipFile(saves/'duplicate.ck3','w') as z:
                z.writestr('gamestate',b'first original');z.writestr('gamestate',b'final original')
            p=saves/'duplicate.ck3'
            with zipfile.ZipFile(p) as z:entry=z.infolist()[0]
            data=bytearray(p.read_bytes());at=entry.header_offset;n,e=struct.unpack_from('<HH',data,at+26);data[at+30+n+e]^=1;p.write_bytes(data)
        elif mode=='overflow':
            for i in range(513):(saves/f'{i}.ck3').write_bytes(b'SAV0\\nmeta_data={')
        elif mode=='malformed':
            (saves/'bad.ck3').write_bytes(b'PK\\x03\\x04truncated')
            (saves/'native.ck3').write_bytes(b'SAV1\\nmeta_data={PK\\x03\\x04truncated')
        else:raise RuntimeError('unknown finite fixture scenario')
        try:
            result=module.Ck3ProfileArtifactInspector(profile).inspect_save_artifacts_v1();seedable=[]
            for item in result['artifacts']:
                try:module.require_seedable_ck3_save_v1(item);seedable.append(True)
                except module.SaveArtifactError:seedable.append(False)
            response={'response':result,'seedable':seedable,'unicode_version':unicodedata.unidata_version}
        except module.SaveArtifactError as error:response={'failure':type(error).__name__}
        if source.read_bytes()!=raw:raise RuntimeError('original save producer changed during continuation')
        print(json.dumps(response,ensure_ascii=False,separators=(',',':')))
        """;
    private record Oracle(Path profile, JsonNode value) { }
    private static String required(String name) {
        String value = System.getProperty(name);
        if (value == null || value.isBlank()) throw new IllegalStateException("save artifact original parity requires " + name + "; NOT_RUN cannot be a passing skip");
        return value;
    }
    private Oracle oracle(String mode) throws Exception {
        Path repository = Path.of(required("xar.repository.root")).toRealPath();
        Path source = repository.resolve("ck3_autonomous_player/src/xar_autoplayer/ck3_save_artifacts.py").toRealPath();
        assertTrue(source.startsWith(repository)); assertEquals(6247, Files.size(source));
        assertEquals(ORIGINAL_SHA, ControlBuild.FileRef.measure(source).sha256());
        Path profile = temporary.resolve("profile-" + mode);
        ProcessBuilder command = new ProcessBuilder(required("xar.python"), "-I", "-B", "-c", ORIGINAL,
                repository.toString(), ORIGINAL_SHA, profile.toString(), mode);
        // These are fixed before import/module execution; no frozen-path import precedes fixture setup.
        command.environment().put("PYTHONDONTWRITEBYTECODE", "1"); command.environment().put("PYTHONNOUSERSITE", "1"); command.environment().put("PYTHONUTF8", "1");
        command.redirectErrorStream(true); Process process = command.start();
        CompletableFuture<byte[]> output = CompletableFuture.supplyAsync(() -> {
            try { return process.getInputStream().readNBytes((1 << 20) + 1); }
            catch (IOException unavailable) { throw new java.io.UncheckedIOException(unavailable); }
        });
        try {
            process.getOutputStream().close(); assertTrue(process.waitFor(60, TimeUnit.SECONDS), "original SAVE producer process timed out");
            byte[] raw = output.get(5, TimeUnit.SECONDS); assertTrue(raw.length <= 1 << 20);
            assertEquals(0, process.exitValue(), new String(raw, StandardCharsets.UTF_8));
            assertEquals(ORIGINAL_SHA, ControlBuild.FileRef.measure(source).sha256());
            return new Oracle(profile, ControlBuild.strictMapper().readTree(raw));
        } finally { if (process.isAlive()) process.destroyForcibly(); }
    }
    private RootSaveArtifactInspector inspector(Path profile) throws IOException {
        return new RootSaveArtifactInspector(profile, VanillaEventCatalog.load().textRules());
    }
    private Response compare(Oracle oracle) throws Exception {
        var rules = VanillaEventCatalog.load().textRules();
        assertEquals(oracle.value().get("unicode_version").textValue(), rules.unicodeVersion(), "use the same captured original Unicode rules, never host-JDK lower");
        Response actual = new RootSaveArtifactInspector(oracle.profile(), rules).inspect(); RawJson wire = RootSaveArtifactCodec.encode(actual);
        assertEquals(oracle.value().get("response"), ControlBuild.strictMapper().readTree(wire.bytes()));
        assertEquals(actual, RootSaveArtifactCodec.decode(wire));
        for (int i = 0; i < actual.artifacts().size(); i++) {
            Artifact artifact = actual.artifacts().get(i);
            if (oracle.value().get("seedable").get(i).booleanValue()) assertDoesNotThrow(() -> RootSaveArtifactInspector.requireSeedable(artifact));
            else assertThrows(IOException.class, () -> RootSaveArtifactInspector.requireSeedable(artifact));
        }
        return actual;
    }
    @Test void originalProducerAllFormatsCodecsZip64AndFullUnicodeOrderRoundTrip() throws Exception { compare(oracle("all")); }
    @Test void crcOfUnreportedLateMemberIsStillChecked() throws Exception {
        var zip = (ZipArtifact) compare(oracle("crc")).artifacts().getFirst();
        assertEquals(131, zip.memberCount()); assertEquals(128, zip.members().size()); assertTrue(zip.membersTruncated());
        assertFalse(zip.zipValid()); assertEquals("member129", zip.badMember()); assertFalse(zip.integrityOk());
    }
    @Test void duplicateNamesFollowTheOriginalTestzipFinalNameLookup() throws Exception {
        var zip = (ZipArtifact) compare(oracle("duplicate")).artifacts().getFirst(); assertTrue(zip.zipValid()); assertEquals(2, zip.memberCount());
    }
    @Test void malformedZipDoesNotInventIntegrityForARecognizedRawHeader() throws Exception { compare(oracle("malformed")); }
    @Test void inventoryOverflowRefusesBothRealProducersWithoutPartialResults() throws Exception {
        Oracle original = oracle("overflow"); assertEquals("SaveArtifactError", original.value().get("failure").textValue());
        assertThrows(IOException.class, () -> inspector(original.profile()).inspect());
    }
    @Test void emptyConfiguredProfileAndNonDirectoryLastSaveFollowOriginalInventoryScope() throws Exception {
        Path profile = Files.createDirectory(temporary.resolve("empty")); Files.createDirectory(profile.resolve("last_save.ck3"));
        assertTrue(inspector(profile).inspect().artifacts().isEmpty());
    }
    @Test void sameBytesAtANewFileIdentityCannotMasqueradeAsTheSelectedOriginal() throws Exception {
        Path profile = Files.createDirectory(temporary.resolve("identity")), saves = Files.createDirectory(profile.resolve("save games"));
        Path file = saves.resolve("original.ck3"); byte[] raw = "SAV0\nmeta_data={".getBytes(StandardCharsets.US_ASCII);
        Files.write(file, raw, StandardOpenOption.CREATE_NEW); var before = SharedSourceFiles.observe(file); var actual = inspector(profile);
        Files.move(file, profile.resolve("retained.ck3")); Files.write(file, raw, StandardOpenOption.CREATE_NEW);
        assertNotEquals(before.nativeFile().fileIdDecimal(), SharedSourceFiles.nativeFile(file).fileIdDecimal());
        assertThrows(IOException.class, () -> actual.inspectSelected(file, before));
    }
    @Test void replacementProfileAtTheSamePathCannotBeInspected() throws Exception {
        Path profile = Files.createDirectory(temporary.resolve("profile")); var actual = inspector(profile);
        Files.move(profile, temporary.resolve("retained-profile")); Files.createDirectory(profile);
        assertThrows(IOException.class, actual::inspect);
    }
    @Test void exactPathlessRequestRejectsAllCallerPathAndWrongFieldShapes() {
        for (String invalid : List.of("{\"path\":\"C:/escape\"}", "{\"profile_dir\":null}", "{\"limit\":1}"))
            assertThrows(IllegalArgumentException.class, () -> RootSaveArtifactCodec.decodeRequest(arguments(invalid)));
        assertNotNull(RootSaveArtifactCodec.decodeRequest(arguments("{}")));
        assertNotNull(RootSaveArtifactCodec.decodeRequest(new Arguments(Presence.MISSING, Optional.empty())));
        assertNotNull(RootSaveArtifactCodec.decodeRequest(new Arguments(Presence.NULL, Optional.of(new RawJson("null".getBytes(StandardCharsets.UTF_8))))));
    }
    @Test void fullResponseCodecRejectsMissingUnknownBooleanIntegerAndNullDrift() throws Exception {
        Response actual = compare(oracle("malformed")); ObjectNode row = (ObjectNode) ControlBuild.strictMapper().readTree(RootSaveArtifactCodec.encode(actual).bytes());
        ObjectNode wrong = row.deepCopy(); wrong.put("artifact_count", true); reject(wrong);
        wrong = row.deepCopy(); wrong.put("artifact_count", 2.0); reject(wrong);
        wrong = row.deepCopy(); wrong.remove("read_only"); reject(wrong);
        wrong = row.deepCopy(); wrong.put("extra", false); reject(wrong);
        wrong = row.deepCopy(); ((ObjectNode) wrong.get("artifacts").get(0)).put("integrity_ok", false); reject(wrong);
    }
    @Test void actualFilesystemLeafFlowsThroughThePublicDecoderHandlerAndCompleteEnvelope() throws Exception {
        Oracle original = oracle("all"); var actual = inspector(original.profile());
        Path source = Path.of("src/main/java/org/xar/ck3/control/service/root/RootSaveArtifactPublicProducts.java").toAbsolutePath();
        var file = ControlBuild.FileRef.measure(source); ExactRef implementation = new ExactRef(file.path(), file.bytes(), file.sha256());
        var binding = RootSaveArtifactPublicProducts.binding(implementation, request -> {
            try { return actual.inspect(); } catch (IOException unavailable) { throw new java.io.UncheckedIOException(unavailable); }
        });
        var call = new ToolCall(RootSaveArtifactPublicProducts.NAME, arguments("{}"), Optional.empty(), new McpCancellation());
        var request = binding.decoder().decode(call); var result = binding.encoder().encode(binding.actual().invoke(request));
        JsonNode envelope = ControlBuild.strictMapper().readTree(result.bytes()); assertFalse(envelope.get("isError").booleanValue());
        assertEquals(original.value().get("response"), envelope.get("structuredContent"));
        assertThrows(IllegalArgumentException.class, () -> binding.decoder().decode(new ToolCall(RootSaveArtifactPublicProducts.NAME,
                arguments("{\"path\":\"C:/foreign\"}"), Optional.empty(), new McpCancellation())));
        // This actual filesystem/protocol regression creates no Core, NativeLaunchPlan, Game or restoration permission.
    }
    private static Arguments arguments(String json) { return new Arguments(Presence.VALUE, Optional.of(new RawJson(json.getBytes(StandardCharsets.UTF_8)))); }
    private static void reject(ObjectNode row) throws IOException {
        RawJson bytes = new RawJson(ControlBuild.strictMapper().writeValueAsBytes(row)); assertThrows(IllegalArgumentException.class, () -> RootSaveArtifactCodec.decode(bytes));
    }
}
