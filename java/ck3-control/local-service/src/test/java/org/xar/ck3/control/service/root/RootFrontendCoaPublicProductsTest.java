package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaData;
import org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaUploads;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaContract;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaService;
import org.xar.ck3.control.service.mcp.McpCancellation;
import org.xar.ck3.control.service.mcp.McpExecutableDirectory;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaCodec.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaContract.*;
import static org.junit.jupiter.api.Assertions.*;

/** Actual typed public binding, complete original SDK descriptors, and original Python response oracles. */
final class RootFrontendCoaPublicProductsTest {
    @TempDir Path temporary;
    @BeforeAll static void completeOriginalDescriptorsAreMandatory()throws Exception{
        var descriptors=RootOriginalPublicTestInputs.tools();Set<String> names=new HashSet<>();for(var descriptor:descriptors)assertTrue(names.add(descriptor.name()));
        for(Method method:Method.values())assertTrue(names.contains(method.publicName()),"full original SDK capture lacks "+method.publicName());
        assertEquals(28,Method.values().length);
    }
    private static FrontendCoaService disk(){return new FrontendCoaService(request->{throw new AssertionError("disk call entered native provider");},()->{throw new AssertionError("disk call queried current Game");});}
    private static McpExecutableDirectory.DirectBinding<?,?> binding(Method method){return RootFrontendCoaPublicProducts.diskMethods(disk(),new ExactRef("fixture/source",1,"a".repeat(64))).stream().filter(b->b.name().equals(method.publicName())).findFirst().orElseThrow();}
    private static <Q,R> JsonNode invoke(McpExecutableDirectory.DirectBinding<Q,R> binding,ObjectNode args)throws Exception{
        ToolCall call=new ToolCall(binding.name(),new Arguments(Presence.VALUE,Optional.of(raw(args))),Optional.empty(),new McpCancellation());
        Q request=binding.decoder().decode(call);R result=binding.actual().invoke(request);
        return FullJsonTree.parse(binding.encoder().encode(result).bytes(),RawJson.MAXIMUM_BYTES).get("structuredContent");
    }
    private Path configured(boolean archive)throws Exception{
        Path user=temporary.resolve(archive?"archive-user":"directory-user"),content=temporary.resolve(archive?"archive-content":"directory-content");Files.createDirectories(user.resolve("mod"));
        String manifest="plain.dds = { colors = 2 visible = yes category = common }\nhidden.dds = { visible = no }\n";
        if(archive){Path zip=content.resolveSibling("resources.zip");try(var output=new ZipOutputStream(Files.newOutputStream(zip))){for(String member:List.of("gfx/coat_of_arms/patterns/a.txt","gfx/coat_of_arms/patterns/plain.dds")){output.putNextEntry(new ZipEntry(member));output.write(member.endsWith(".txt")?manifest.getBytes(StandardCharsets.UTF_8):dds());output.closeEntry();}}Files.writeString(user.resolve("mod/test.mod"),"name = \"Archive\"\narchive = \""+zip.toString().replace('\\','/')+"\"\n");}
        else{Path directory=content.resolve("gfx/coat_of_arms/patterns");Files.createDirectories(directory);Files.writeString(directory.resolve("a.txt"),manifest);Files.write(directory.resolve("plain.dds"),dds());Files.writeString(user.resolve("mod/test.mod"),"name = \"Directory\"\npath = \""+content.toString().replace('\\','/')+"\"\n");}
        ObjectNode load=empty();load.putArray("enabled_mods").add("mod/test.mod");load.putArray("disabled_dlcs").add("dlc_ignored");Files.write(user.resolve("dlc_load.json"),raw(load).bytes());return user;
    }
    private static byte[] dds(){byte[] bytes=new byte[128];ByteBuffer b=ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN);b.put(new byte[]{68,68,83,32}).putInt(124);b.putInt(12,8).putInt(16,8);bytes[84]='D';bytes[85]='X';bytes[86]='T';bytes[87]='1';return bytes;}
    @Test void actualDirectoryAndArchiveProducersReachPublicCatalogOpaqueCandidateAssetAndWire()throws Exception{
        for(boolean archive:List.of(false,true)){Path user=configured(archive);ObjectNode args=empty().put("user_directory",user.toString()).put("kind","pattern");JsonNode catalog=invoke(binding(Method.CONFIGURED_CATALOG),args);assertEquals(1,catalog.get("total").intValue());JsonNode candidate=catalog.get("items").get(0);assertEquals(2,candidate.get("colors").intValue());assertFalse(catalog.get("provenance").get("load_order_precedence_applied").booleanValue());String id=candidate.get("candidate_id").textValue();assertTrue(id.matches("[A-F0-9]{64}"));
            JsonNode asset=invoke(binding(Method.CONFIGURED_ASSET),empty().put("user_directory",user.toString()).put("kind","pattern").put("candidate_id",id));assertEquals("plain.dds",asset.get("name").textValue());assertArrayEquals(dds(),java.util.Base64.getDecoder().decode(asset.get("asset_base64").textValue()));assertEquals("DXT1",asset.get("dds").get("format").textValue());assertEquals(8,asset.get("dds").get("width").intValue());
            byte[] original=raw((ObjectNode)asset).bytes();assertArrayEquals(original,encode(new Response(new RawJson(original))).bytes());
        }
    }
    @Test void configuredHiddenPaginationAndDuplicateCandidatesRemainCandidatesWithoutInventedWinner()throws Exception{
        Path user=configured(false);ObjectNode args=empty().put("user_directory",user.toString()).put("kind","pattern").put("visible_only",false).put("limit",1);
        JsonNode first=invoke(binding(Method.CONFIGURED_CATALOG),args);assertEquals(2,first.get("total").intValue());assertTrue(first.get("has_more").booleanValue());assertEquals(1,first.get("next_offset").intValue());args.put("offset",1);JsonNode second=invoke(binding(Method.CONFIGURED_CATALOG),args);assertFalse(second.get("items").get(0).get("visible").booleanValue());assertTrue(second.get("next_offset").isNull());
        ObjectNode load=empty();load.putArray("enabled_mods").add("mod/test.mod").add("mod/test.mod");Files.write(user.resolve("dlc_load.json"),raw(load).bytes());args.remove(List.of("limit","offset"));args.put("visible_only",true);JsonNode repeated=invoke(binding(Method.CONFIGURED_CATALOG),args);assertEquals(2,repeated.get("total").intValue());assertNotEquals(repeated.get("items").get(0).get("candidate_id"),repeated.get("items").get(1).get("candidate_id"));assertTrue(repeated.get("items").get(0).get("potential_configured_name_conflict").booleanValue());
    }
    @Test void actualConfigurationMutationInvalidatesOldCandidateAndMissingDiffersFromNull()throws Exception{
        Path user=configured(false);JsonNode catalog=invoke(binding(Method.CONFIGURED_CATALOG),empty().put("user_directory",user.toString()).put("kind","pattern"));String id=catalog.get("items").get(0).get("candidate_id").textValue();Path manifest=temporary.resolve("directory-content/gfx/coat_of_arms/patterns/a.txt");Files.writeString(manifest,"plain.dds = { colors = 3 }\n");assertThrows(Exception.class,()->invoke(binding(Method.CONFIGURED_ASSET),empty().put("user_directory",user.toString()).put("kind","pattern").put("candidate_id",id)));
        ObjectNode load=empty();load.putArray("enabled_mods").add("mod/test.mod");Files.write(user.resolve("dlc_load.json"),raw(load).bytes());JsonNode current=invoke(binding(Method.LOAD_CONFIGURATION),empty().put("user_directory",user.toString()));assertTrue(current.get("disabled_dlcs").isArray());assertEquals(0,current.get("disabled_dlcs").size());load.putNull("disabled_dlcs");Files.write(user.resolve("dlc_load.json"),raw(load).bytes());assertThrows(Exception.class,()->invoke(binding(Method.LOAD_CONFIGURATION),empty().put("user_directory",user.toString())));
    }
    @Test void originalExactBuildGuardRejectsUnrelatedInstallationWithoutTouchingNativeProvider()throws Exception{
        Path game=temporary.resolve("wrong-game");Files.createDirectories(game.resolve("binaries"));Files.writeString(game.resolve("binaries/ck3.exe"),"unrelated fixture");
        for(Method method:List.of(Method.RESOURCE_CATALOG,Method.DEFINITION_CATALOG,Method.DLC,Method.RENDER_SUPPORT,Method.RESOURCE_ASSET,Method.DEFINITION)){ObjectNode args=empty().put("game_directory",game.toString());if(method==Method.RESOURCE_CATALOG||method==Method.RESOURCE_ASSET)args.put("kind","pattern");if(method==Method.RESOURCE_ASSET)args.put("name","plain.dds");if(method==Method.DEFINITION)args.put("key","test");assertThrows(Exception.class,()->invoke(binding(method),args));}
    }
    @Test void publicUnsigned64AndUploadLibraryPreserveMaximumWithoutUnsafeNumericOrFloatAlias()throws Exception{
        String maximum="18446744073709551615";var revision=(Revision)decode(Method.EXPORT,raw(empty().put("expected_revision",maximum)));assertEquals(maximum,revision.expectedRevision().toString());
        for(JsonNode wrong:List.of(empty().booleanNode(true),empty().numberNode(1.0),empty().nullNode(),empty().numberNode(new java.math.BigInteger(maximum)))){ObjectNode n=empty();n.set("expected_revision",wrong);assertThrows(IllegalArgumentException.class,()->decode(Method.EXPORT,raw(n)));}
        var binding=new CoaData.FrontendBinding(new java.math.BigInteger(maximum),17);var upload=new CoaUploads.Receipt(CoaUploads.Status.RECEIVING,new CoaUploads.SessionKey("a".repeat(32),new java.math.BigInteger(maximum)),4,"b".repeat(64),1,0,0,new CoaUploads.Intent(java.math.BigInteger.ZERO,false,CoaData.GAME_VERSION,CoaData.EXE_SHA256),binding);ObjectNode encoded=upload(upload);assertEquals(maximum,encoded.get("generation").textValue());assertEquals(maximum,encoded.get("binding").get("connection_generation").textValue());assertEquals("0",encoded.get("expected_revision").textValue());assertEquals(encoded,object(raw(encoded)));
    }
    @Test void everyArgumentBoundaryRejectsExtraMissingNullBooleanAndFloatIDsBeforeProvider()throws Exception{
        for(String value:List.of("{}","{\"user_directory\":null}","{\"user_directory\":true}","{\"user_directory\":1.0}","{\"user_directory\":\"x\",\"alias\":1}"))assertThrows(IllegalArgumentException.class,()->decode(Method.LOAD_CONFIGURATION,new RawJson(value.getBytes(StandardCharsets.UTF_8))));
        ObjectNode base=empty().put("user_directory","x").put("kind","pattern");for(String field:List.of("offset","limit","visible_only")){ObjectNode wrong=base.deepCopy();wrong.putNull(field);assertThrows(IllegalArgumentException.class,()->decode(Method.CONFIGURED_CATALOG,raw(wrong)));}
        assertThrows(IllegalArgumentException.class,()->decode(Method.CAPTURE,raw(empty().put("calibration_id","good").put("side",32.0))));
        assertEquals(32,((Capture)decode(Method.CAPTURE,raw(empty().put("calibration_id","good").put("side",32)))).side());assertEquals(512,((Capture)decode(Method.CAPTURE,raw(empty().put("calibration_id","good").put("side",512)))).side());
        assertThrows(IllegalArgumentException.class,()->new Catalog(Method.EXPORT,Path.of("x"),Kind.PATTERN,null,true,0,50));
    }
    @Test void unavailableNativeNineteenAreAbsentFromActualExecutableBindings(){List<String> names=RootFrontendCoaPublicProducts.diskMethods(disk(),new ExactRef("fixture/source",1,"a".repeat(64))).stream().map(McpExecutableDirectory.DirectBinding::name).toList();assertEquals(9,names.size());for(Method method:Method.values())assertEquals(RootFrontendCoaPublicProducts.DISK_METHODS.contains(method),names.contains(method.publicName()));}
    @Test void completeOriginalPythonStaticOraclesMustReachEveryActualDiskConsumer()throws Exception{
        String path=required("xar.public.coa.original.oracles.path"),bytes=required("xar.public.coa.original.oracles.bytes"),sha=required("xar.public.coa.original.oracles.sha256");FileRef ref=new FileRef(path,Long.parseLong(bytes),sha);ref.verify();var witness=SharedSourceFiles.observe(Path.of(path));byte[] raw=Files.readAllBytes(Path.of(path));assertEquals(ref.bytes(),raw.length);JsonNode cases=FullJsonTree.parse(raw,RawJson.MAXIMUM_BYTES);assertTrue(cases.isArray()&&!cases.isEmpty());Set<Method> covered=new HashSet<>();for(JsonNode item:cases){assertTrue(item.isObject()&&item.get("name").isTextual()&&item.get("arguments").isObject()&&item.get("expected").isObject());Method method=Method.named(item.get("name").textValue());assertTrue(RootFrontendCoaPublicProducts.DISK_METHODS.contains(method));assertEquals(item.get("expected"),invoke(binding(method),(ObjectNode)item.get("arguments")));covered.add(method);}assertEquals(RootFrontendCoaPublicProducts.DISK_METHODS,covered,"a partial oracle capture cannot count as all-consumer parity");SharedSourceFiles.assertUnchanged(witness);ref.verify();
    }
    @Test void originalAsciiScriptWhitespaceKeepsUnicodeSpaceInsideActualConfiguredResourceNameAndAsset()throws Exception{
        Path user=configured(false),directory=temporary.resolve("directory-content/gfx/coat_of_arms/patterns");
        String name="uni\u2003name.dds";
        Files.writeString(directory.resolve("a.txt"),name+" = { colors = 2 visible = yes }\n");Files.write(directory.resolve(name),dds());
        JsonNode catalog=invoke(binding(Method.CONFIGURED_CATALOG),empty().put("user_directory",user.toString()).put("kind","pattern"));
        assertEquals(1,catalog.get("total").intValue());assertEquals(name,catalog.get("items").get(0).get("name").textValue());
        String candidate=catalog.get("items").get(0).get("candidate_id").textValue();
        JsonNode asset=invoke(binding(Method.CONFIGURED_ASSET),empty().put("user_directory",user.toString()).put("kind","pattern").put("candidate_id",candidate));
        assertEquals(name,asset.get("name").textValue());assertArrayEquals(dds(),java.util.Base64.getDecoder().decode(asset.get("asset_base64").textValue()));
    }
    @Test void originalCodePointStringBoundsAndPythonTrimReachActualPublicConfiguredConsumer()throws Exception{
        Path user=configured(false);ObjectNode args=empty().put("user_directory",user.toString()).put("kind","pattern");
        assertEquals(1,invoke(binding(Method.CONFIGURED_CATALOG),args.deepCopy().put("query","\u00a0PLAIN\u00a0")).get("total").intValue());
        String face="\ud83d\ude00";
        assertEquals(0,invoke(binding(Method.CONFIGURED_CATALOG),args.deepCopy().put("query",face.repeat(128))).get("total").intValue());
        assertThrows(IllegalArgumentException.class,()->invoke(binding(Method.CONFIGURED_CATALOG),args.deepCopy().put("query",face.repeat(129))));
        ObjectNode asset=empty().put("game_directory",user.toString()).put("kind","pattern").put("name",face.repeat(124)+".dds");
        assertEquals(face.repeat(124)+".dds",((Asset)decode(Method.RESOURCE_ASSET,raw(asset))).name());
        assertThrows(IllegalArgumentException.class,()->decode(Method.RESOURCE_ASSET,raw(asset.deepCopy().put("name",face.repeat(125)+".dds"))));
    }
    @Test void originalCaseFoldCodePointOrderingDrivesConfiguredManifestProducerAndOpaqueAssetWire()throws Exception{
        Path user=configured(false),directory=temporary.resolve("directory-content/gfx/coat_of_arms/patterns");
        Files.writeString(directory.resolve("a.txt"),"# no resources in this original manifest\n");
        Files.writeString(directory.resolve("\ue000.txt"),"bmp.dds = { colors = 1 }\n");
        Files.writeString(directory.resolve("\ud83d\ude00.txt"),"supplementary.dds = { colors = 2 }\n");
        Files.write(directory.resolve("bmp.dds"),dds());Files.write(directory.resolve("supplementary.dds"),dds());
        JsonNode catalog=invoke(binding(Method.CONFIGURED_CATALOG),empty().put("user_directory",user.toString()).put("kind","pattern"));
        assertEquals(2,catalog.get("total").intValue());assertEquals("bmp.dds",catalog.get("items").get(0).get("name").textValue());
        assertEquals("supplementary.dds",catalog.get("items").get(1).get("name").textValue());
        for(JsonNode candidate:catalog.get("items")){
            JsonNode asset=invoke(binding(Method.CONFIGURED_ASSET),empty().put("user_directory",user.toString()).put("kind","pattern").put("candidate_id",candidate.get("candidate_id").textValue()));
            assertEquals(candidate.get("name"),asset.get("name"));assertArrayEquals(dds(),java.util.Base64.getDecoder().decode(asset.get("asset_base64").textValue()));
        }
    }
    private static String required(String name){String value=System.getProperty(name);if(value==null||value.isBlank())throw new IllegalStateException("NOT_RUN_REQUIRED_ACTUAL_ORIGINAL_COA_ORACLES: missing -D"+name);return value;}
}
