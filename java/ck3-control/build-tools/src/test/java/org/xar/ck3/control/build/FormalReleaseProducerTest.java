package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Base64;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.NativeRunProfileManifest.ReleaseManifest;

final class FormalReleaseProducerTest {
    // Exact retained native-registry original: 3226B / SHA256 47ff303b...c2d90.
    // Its Git blob must independently be observed by production; this fixture grants no clean/HEAD authority.
    static final byte[] REGISTRY=Base64.getDecoder().decode("IiIiRGVyaXZlIENLMyBXb3Jrc2hvcCBjb21wYXRpYmlsaXR5IHRhZ3MgZnJvbSBhIHJlbGVhc2Ugc3RhZ2luZyBkZXNjcmlwdG9yLgoKVGhlc2UgYXJlIG9yZGluYXJ5IFN0ZWFtIFdvcmtzaG9wIHRhZ3MuIEEgZGVzY3JpcHRvciB2ZXJzaW9uIGlzIGEgbWV0YWRhdGEKY2xhaW07IHRoaXMgaGVscGVyIGRvZXMgbm90IGVzdGFibGlzaCBnYW1lcGxheSBhY2NlcHRhbmNlIG9yIGF1dGhvcml6ZSB1cGxvYWQuCkF1dG9tYXRpYyB0YWdnaW5nIHN0YXJ0cyBhdCBDSzMgMS4yMC4gT2xkZXIgdmVyc2lvbnMgcHJlc2VydmUgdGhlaXIgdGFncy4gQWRkCmZ1dHVyZSBsYWJlbHMgb25seSBhZnRlciBjb25maXJtaW5nIHRoZSBnYW1lJ3MgYWN0dWFsIFdvcmtzaG9wIGZpbHRlci4KIiIiCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgpmcm9tIHBhdGhsaWIgaW1wb3J0IFBhdGgKaW1wb3J0IHJlCmZyb20gdHlwaW5nIGltcG9ydCBTZXF1ZW5jZQoKCiMgU2luZ2xlIHJlZ2lzdHJ5IGZvciBib3RoIG5hdGl2ZSBwdWJsaWNhdGlvbiBhbmQgc3RhZ2luZyBkZXNjcmlwdG9yIHJlbmRlcmluZy4KIyBGdXR1cmUgY29uZmlybWVkIG1pbm9ycyBuZWVkIG9ubHkgYSBuZXcgZW50cnkgaGVyZTsgY29uc3VtZXJzIHJlbWFpbiB1bmNoYW5nZWQuCkNLM19XT1JLU0hPUF9WRVJTSU9OX1RBR1MgPSB7IjEuMjAiOiAiMS4yMCAnQ3JvemllcicifQpfU1VQUE9SVEVEX1ZFUlNJT04gPSByZS5jb21waWxlKAogICAgcideXHMqc3VwcG9ydGVkX3ZlcnNpb25ccyo9XHMqIihbXiJcclxuXSspIlxzKig/OiMuKik/JCcsCiAgICByZS5NVUxUSUxJTkUsCikKX1ZFUlNJT05fQVNTSUdOTUVOVCA9IHJlLmNvbXBpbGUociJeXHMqc3VwcG9ydGVkX3ZlcnNpb25ccyo9IiwgcmUuTVVMVElMSU5FKQpfVkVSU0lPTiA9IHJlLmNvbXBpbGUociIoWzAtOV0rKVwuKFswLTldKykoPzpcLig/OlswLTldK3xcKikpezAsMn0iKQpfQ09NUEFUSUJJTElUWV9UQUcgPSByZS5jb21waWxlKHIiWzAtOV0rXC5bMC05XSsoPzogJ1teJ1xyXG5dKycpPyIpCgoKZGVmIGNvbXBhdGliaWxpdHlfdGFnX2Zyb21fZGVzY3JpcHRvcihkZXNjcmlwdG9yOiBzdHIpIC0+IHN0ciB8IE5vbmU6CiAgICAiIiJSZXR1cm4gdGhlIGNvbmZpcm1lZCBXb3Jrc2hvcCB0YWcsIG9yIE5vbmUgZm9yIHZlcnNpb25zIGJlZm9yZSAxLjIwLgoKICAgIFRoZSB2ZXJzaW9uIG1heSBzcGVjaWZ5IGEgbWlub3IsIG51bWVyaWMgcGF0Y2gvYnVpbGQgb3IgQ0szIHdpbGRjYXJkLiBNaXNzaW5nLAogICAgZHVwbGljYXRlLCBtYWxmb3JtZWQgYW5kIHVubWFwcGVkIDEuMjArIHZhbHVlcyBmYWlsIGJlZm9yZSBhbnkgcmVtb3RlIG9wZXJhdGlvbi4KICAgICIiIgogICAgaWYgbm90IGlzaW5zdGFuY2UoZGVzY3JpcHRvciwgc3RyKToKICAgICAgICByYWlzZSBWYWx1ZUVycm9yKCJkZXNjcmlwdG9yIG11c3QgYmUgdGV4dCIpCiAgICBkZXNjcmlwdG9yID0gZGVzY3JpcHRvci5sc3RyaXAoIlx1ZmVmZiIpCiAgICB2ZXJzaW9ucyA9IF9TVVBQT1JURURfVkVSU0lPTi5maW5kYWxsKGRlc2NyaXB0b3IpCiAgICBpZiBsZW4odmVyc2lvbnMpICE9IDEgb3IgbGVuKF9WRVJTSU9OX0FTU0lHTk1FTlQuZmluZGFsbChkZXNjcmlwdG9yKSkgIT0gMToKICAgICAgICByYWlzZSBWYWx1ZUVycm9yKCJkZXNjcmlwdG9yIG11c3QgY29udGFpbiBleGFjdGx5IG9uZSBzdXBwb3J0ZWRfdmVyc2lvbiIpCiAgICB2ZXJzaW9uID0gX1ZFUlNJT04uZnVsbG1hdGNoKHZlcnNpb25zWzBdKQogICAgaWYgdmVyc2lvbiBpcyBOb25lOgogICAgICAgIHJhaXNlIFZhbHVlRXJyb3IoZiJpbnZhbGlkIHN1cHBvcnRlZF92ZXJzaW9uOiB7dmVyc2lvbnNbMF0hcn0iKQogICAgbWlub3JfdmVyc2lvbiA9IChpbnQodmVyc2lvbi5ncm91cCgxKSksIGludCh2ZXJzaW9uLmdyb3VwKDIpKSkKICAgIGlmIG1pbm9yX3ZlcnNpb24gPCAoMSwgMjApOgogICAgICAgIHJldHVybiBOb25lCiAgICBtaW5vciA9IGYie21pbm9yX3ZlcnNpb25bMF19LnttaW5vcl92ZXJzaW9uWzFdfSIKICAgIHRyeToKICAgICAgICByZXR1cm4gQ0szX1dPUktTSE9QX1ZFUlNJT05fVEFHU1ttaW5vcl0KICAgIGV4Y2VwdCBLZXlFcnJvcjoKICAgICAgICByYWlzZSBWYWx1ZUVycm9yKAogICAgICAgICAgICBmIm5vIGNvbmZpcm1lZCBDSzMgV29ya3Nob3AgY29tcGF0aWJpbGl0eSB0YWcgZm9yIHttaW5vcn07ICIKICAgICAgICAgICAgImNvbmZpcm0gdGhlIG9mZmljaWFsIHZlcnNpb24gbGFiZWwgYmVmb3JlIHB1Ymxpc2hpbmciCiAgICAgICAgKSBmcm9tIE5vbmUKCgpkZWYgY29tcGF0aWJpbGl0eV90YWdzX2Zvcl9zdGFnaW5nKAogICAgc3RhZ2luZ19kaXI6IFBhdGggfCBzdHIsIHRhZ3M6IFNlcXVlbmNlW3N0cl0KKSAtPiB0dXBsZVtzdHIsIC4uLl06CiAgICAiIiJSZXBsYWNlIHZlcnNpb24gdGFncyB3aGlsZSBwcmVzZXJ2aW5nIGV2ZXJ5IG90aGVyIHRhZyBhbmQgaXRzIG9yZGVyLgoKICAgIFJlYWQgb25seSB0aGUgYWN0dWFsIHN0YWdpbmcgZGVzY3JpcHRvci4gRG8gbm90IHVzZSB0aGUgZGV2ZWxvcG1lbnQgdHJlZSBvcgogICAgY2hhbmdlIGEgZGVzY3JpcHRvciwgY29udGVudCBmaWxlLCBkZXNjcmlwdGlvbiBvciBDaGFuZ2UgTm90ZXMuCiAgICAiIiIKICAgIGlmIGlzaW5zdGFuY2UodGFncywgKHN0ciwgYnl0ZXMpKSBvciBub3QgaXNpbnN0YW5jZSh0YWdzLCBTZXF1ZW5jZSk6CiAgICAgICAgcmFpc2UgVmFsdWVFcnJvcigidGFncyBtdXN0IGJlIGEgc2VxdWVuY2Ugb2Ygbm9uLWVtcHR5IHN0cmluZ3MiKQogICAgaWYgYW55KG5vdCBpc2luc3RhbmNlKHRhZywgc3RyKSBvciBub3QgdGFnIGZvciB0YWcgaW4gdGFncyk6CiAgICAgICAgcmFpc2UgVmFsdWVFcnJvcigidGFncyBtdXN0IGJlIGEgc2VxdWVuY2Ugb2Ygbm9uLWVtcHR5IHN0cmluZ3MiKQogICAgZGVzY3JpcHRvciA9IFBhdGgoc3RhZ2luZ19kaXIpIC8gImRlc2NyaXB0b3IubW9kIgogICAgbGFiZWwgPSBjb21wYXRpYmlsaXR5X3RhZ19mcm9tX2Rlc2NyaXB0b3IoZGVzY3JpcHRvci5yZWFkX3RleHQoZW5jb2Rpbmc9InV0Zi04LXNpZyIpKQogICAgaWYgbGFiZWwgaXMgTm9uZToKICAgICAgICByZXR1cm4gdHVwbGUodGFncykKICAgIHJldGFpbmVkID0gdHVwbGUodGFnIGZvciB0YWcgaW4gdGFncyBpZiBfQ09NUEFUSUJJTElUWV9UQUcuZnVsbG1hdGNoKHRhZykgaXMgTm9uZSkKICAgIHJldHVybiByZXRhaW5lZCArIChsYWJlbCwpCg==");
    private static byte[] bytes(String value){return value.getBytes(StandardCharsets.UTF_8);}
    private static String text(byte[] value)throws IOException{return FormalReleaseDescriptor.decode(value);}
    @Test void exactRegistryAndDescriptorProjectionPreserveNonVersionFieldsAndBom()throws Exception{
        FormalReleaseDescriptor.requireRegistry(REGISTRY);
        byte[] original=bytes("\ufeffversion=\"1.0.2\"\r\ntags={\r\n\t\"Gameplay\"\r\n\t# keep \"1.18\" comment\r\n\t\"1.19 'Basileus'\"\r\n}\r\nsupported_version=\"1.20.0.3\"\r\nname=\"琉焰卿\"\r\n");
        byte[] projected=FormalReleaseDescriptor.project(original,REGISTRY);
        assertTrue(FormalReleaseDescriptor.hasBom(projected));
        assertEquals("version=\"1.0.2\"\r\ntags={\r\n\t\"Gameplay\"\r\n\t# keep \"1.18\" comment\r\n\t\"1.20 'Crozier'\"\r\n}\r\nsupported_version=\"1.20.0.3\"\r\nname=\"琉焰卿\"\r\n",text(projected));
        assertArrayEquals(projected,FormalReleaseDescriptor.project(projected,REGISTRY));
        byte[] wrong=REGISTRY.clone();wrong[0]^=1;assertThrows(IOException.class,()->FormalReleaseDescriptor.project(original,wrong));
    }
    @Test void nativeRegistryLegacyAndUnknownVersionPoliciesStayDistinct()throws Exception{
        byte[] legacy=bytes("supported_version=\"1.19.*\"\ntags={ \"Gameplay\" \"1.18\" }\n");
        assertArrayEquals(legacy,FormalReleaseDescriptor.project(legacy,REGISTRY));
        assertEquals("1.20 'Crozier'",FormalReleaseDescriptor.compatibilityLabel("supported_version=\"01.020.*.*\" # confirmed minor\n"));
        for(String invalid:List.of("", "supported_version=\"1.21\"\n","supported_version=\"2.0\"\n",
                "supported_version=\"1.20.0.3.4\"\n","supported_version=\"1.20\"\nsupported_version=\"1.20\"\n",
                "supported_version=\"1.20\"\nsupported_version=bad\n"))
            assertThrows(IOException.class,()->FormalReleaseDescriptor.compatibilityLabel(invalid));
        assertThrows(IOException.class,()->FormalReleaseDescriptor.project(bytes("supported_version=\"1.20\"\ntags={} tags={}\n"),REGISTRY));
        assertThrows(IOException.class,()->FormalReleaseDescriptor.project(new byte[]{(byte)0xc3},REGISTRY));
    }
    @Test void productionStripPreservesBytesAndRemovesAllThreeAcceptanceMechanisms()throws Exception{
        byte[] source=bytes("\ufeffkeep = yes\r\n# XAR_ACCEPTANCE_ONLY_BEGIN\r\nxar_selftest = yes\r\n# XAR_ACCEPTANCE_ONLY_END\r\n  # XAR_RELEASE_ONLY actual = yes\r\nsetting_xar_selftest = yes\r\ntail = yes");
        byte[] expected=bytes("\ufeffkeep = yes\r\n  actual = yes\r\ntail = yes");
        assertArrayEquals(expected,FormalReleaseProducer.strip("events/real.txt",source));
        byte[] binary={(byte)0xff,0,3};assertArrayEquals(binary,FormalReleaseProducer.strip("gfx/actual.dds",binary));
        List<FormalReleaseProducer.Rendered> result=FormalReleaseProducer.project(List.of(
                new FormalReleaseProducer.SourceBytes("events/xar_acceptance_events.txt",bytes("xar_acceptance_bad = yes")),
                new FormalReleaseProducer.SourceBytes("events/real.txt",source)),REGISTRY);
        assertEquals(1,result.size());assertArrayEquals(expected,result.getFirst().bytes());
    }
    @Test void malformedMarkersLeaksAndPathsFailBeforeAnyPublication()throws Exception{
        for(String input:List.of(FormalReleaseProducer.BEGIN+"\n"+FormalReleaseProducer.BEGIN+"\n",
                FormalReleaseProducer.END+"\n",FormalReleaseProducer.BEGIN+"\n",
                FormalReleaseProducer.BEGIN+"\n"+FormalReleaseProducer.RELEASE_ONLY+"a=yes\n"+FormalReleaseProducer.END+"\n"))
            assertThrows(IOException.class,()->FormalReleaseProducer.strip("common/actual.txt",bytes(input)));
        assertThrows(IOException.class,()->FormalReleaseProducer.project(List.of(new FormalReleaseProducer.SourceBytes("common/real.txt",bytes("xar_balance_leak=yes"))),REGISTRY));
        assertThrows(IOException.class,()->FormalReleaseProducer.project(List.of(new FormalReleaseProducer.SourceBytes("common/real.py",bytes("bad"))),REGISTRY));
        assertThrows(IOException.class,()->FormalReleaseProducer.project(List.of(new FormalReleaseProducer.SourceBytes("descriptor.mod",
                bytes("version=\"1.0.2\"\nsupported_version=\"1.20\"\ntags={}\nremote_file_id=\"3784706360\"\n"))),REGISTRY));
        for(String invalid:List.of("../escape.txt","common//bad.txt","common\\bad.txt","/common/a.txt","C:/bad.txt"))
            assertThrows(IllegalArgumentException.class,()->new FormalReleaseProducer.SourceBytes(invalid,bytes("bad")));
    }
    @Test void actualSharedFormat2ModelRoundTripsAndRejectsMalformedScalars()throws Exception{
        var rows=FormalReleaseProducer.project(List.of(new FormalReleaseProducer.SourceBytes("events/real.txt",bytes("x=yes\n"))),REGISTRY);
        ReleaseManifest original=FormalReleaseProducer.manifest(rows,"a".repeat(40),"1.0.2","v1.0.2");
        var mapper=ControlBuild.strictMapper();byte[] wire=NativeRunProfileManifest.canonical(mapper.valueToTree(original));
        assertEquals(original,mapper.readValue(wire,ReleaseManifest.class));
        var bad=mapper.readTree(wire);((com.fasterxml.jackson.databind.node.ObjectNode)bad).put("format_version",true);
        assertThrows(IOException.class,()->mapper.treeToValue(bad,ReleaseManifest.class));
        var duplicate=List.of(rows.getFirst(),rows.getFirst());
        assertThrows(IllegalArgumentException.class,()->FormalReleaseProducer.manifest(duplicate,"a".repeat(40),"1.0.2","v1.0.2"));
    }
    @Test void fixedGitPlanUsesExistingJobOwnerAndOnlyExplicitReadCommands(){
        Path root=Path.of("D:/qualified-test/repository"),logs=Path.of("D:/qualified-test/git-capture");
        var execution=new FormalReleaseGit.Execution("fixture-machine","2099-01-01T00:00:00Z",root,
                new ControlBuild.FileRef("D:/qualified-test/bin/git.exe",1,"a".repeat(64)),logs,64L<<20);
        var quote=FormalReleaseGit.quote(execution);
        assertEquals(24,quote.size());assertEquals(48,quote.stream().flatMap(row->java.util.stream.Stream.of(row.stdout(),row.stderr())).distinct().count());
        assertEquals(3993600,quote.stream().mapToLong(FormalReleaseGit.CaptureOutput::maximumLogicalBytes).sum());
        var blob=FormalReleaseGit.arguments(root,FormalReleaseGit.Operation.REGISTRY_BLOB);
        assertTrue(blob.contains("--no-optional-locks"));assertTrue(blob.contains("core.fsmonitor=false"));
        assertEquals(List.of("cat-file","blob","HEAD:"+FormalReleaseDescriptor.REGISTRY_PATH),blob.subList(blob.size()-3,blob.size()));
    }
    @Test void typedImportLayoutKeepsManifestOutsideRetainedModContent(){
        Path repository=Path.of("D:/fixture/repository"),state=Path.of("D:/fixture/state"),source=repository.resolve("XenoAmess_s_Eternal_Recurrence");
        var imported=new FormalReleaseProducer.Request(FormalReleaseProducer.REQUEST_SCHEMA,"fixture-machine","2099-01-01T00:00:00Z",
                repository,source,state,state.resolve("profile/mod-content/xar-production"),state.resolve("xar-production.manifest.json"),
                FormalReleaseProducer.Mode.PROFILE_STAGING,FormalReleaseProducer.Layout.ISOLATED_PROFILE_IMPORT);
        assertEquals(state,imported.outputRoot());
        assertFalse(imported.manifestTarget().startsWith(state.resolve("profile/mod-content")));
        assertThrows(IllegalArgumentException.class,()->new FormalReleaseProducer.Request(imported.schema(),imported.machineId(),imported.reviewAtUtc(),
                repository,source,state,imported.productionRoot(),state.resolve("profile/mod-content/xar-production.manifest.json"),
                imported.mode(),imported.layout()));
        assertThrows(IllegalArgumentException.class,()->new FormalReleaseProducer.Request(imported.schema(),imported.machineId(),imported.reviewAtUtc(),
                repository,source,state,imported.productionRoot(),imported.manifestTarget(),imported.mode(),FormalReleaseProducer.Layout.DIRECT_STAGING));
    }
    @Test void managedGitRequiresExplicitStorageConfigurationWithoutRepositoryFallback()throws Exception{
        assertThrows(IOException.class,()->FormalReleaseGit.explicitStorage(key->null,key->null));
        var configured=java.util.Map.of(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK,"true",
                ProjectStoragePolicy.PROJECT_STORAGE_ROOT,"D:/approved-project-data");
        var policy=FormalReleaseGit.explicitStorage(configured::get,key->null);
        assertTrue(policy.forbidSystemVolumeBulk());assertEquals(Path.of("D:/approved-project-data"),policy.preferredBulkRoot().orElseThrow());
        assertThrows(IOException.class,()->FormalReleaseGit.explicitStorage(key->key.equals(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK)?"TRUE":null,key->null));
    }
}

