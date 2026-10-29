package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.planning.army.H2743StockPredicateAdmission.Input;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Real Windows file custody regression only; these tiny documents cannot qualify stock content. */
final class RootArmyStockReadOriginalsTest {
    @TempDir Path temporary;

    @Test void sameConfiguredOriginalsSurviveStrictConfigurationAndNativeIdentityRoundTrips()throws Exception {
        var configuration=configuration(temporary.resolve("roundtrip"));
        var mapper=ControlBuild.strictMapper();
        byte[] wire=StrictJson.canonical(mapper.valueToTree(configuration),1<<20);
        var restored=mapper.readValue(wire,RootArmyStockReadRuntime.Configuration.class);
        assertEquals(configuration,restored);
        var originals=RootArmyStockReadRuntime.ConfiguredOriginals.retain(restored);
        originals.requireCurrent();originals.requireCurrent();
        // All actual wide native identities stay textual through the same strict JSON reader.
        var witness=SharedSourceFiles.observe(Path.of(configuration.pair().path()));
        byte[] witnessWire=StrictJson.canonical(mapper.valueToTree(witness),1<<20);
        var document=StrictJson.parse(witnessWire,1<<20);
        for(String field:List.of("volume_serial_decimal","file_id_decimal","creation_filetime_decimal")) {
            var value=document.path("native_file").get(field);
            assertTrue(value.isTextual());assertTrue(value.textValue().matches("0|[1-9][0-9]*"));
            for(int wrongType=0;wrongType<3;wrongType++) {
                var malformed=((ObjectNode)document).deepCopy();var identity=(ObjectNode)malformed.get("native_file");
                if(wrongType==0)identity.put(field,true);
                else if(wrongType==1)identity.put(field,1.0);
                else identity.put(field,1);
                assertThrows(IOException.class,()->mapper.readValue(StrictJson.canonical(malformed,1<<20),SharedSourceFiles.Witness.class));
            }
        }
        assertEquals(witness,mapper.readValue(witnessWire,SharedSourceFiles.Witness.class));
    }

    @Test void installedPairAndPinsRejectSameBytesNativeReplacementAndContentDrift()throws Exception {
        for(int role=0;role<2;role++)for(boolean replacement:List.of(false,true)) {
            var configuration=configuration(temporary.resolve("drift-"+role+"-"+replacement));
            var originals=RootArmyStockReadRuntime.ConfiguredOriginals.retain(configuration);
            Path path=Path.of((role==0?configuration.pair():configuration.pins()).path());
            var before=SharedSourceFiles.observe(path);byte[] bytes=Files.readAllBytes(path);
            var modified=Files.getLastModifiedTime(path);
            if(replacement) {
                // Keep the original alive so Windows cannot recycle its FileID for the replacement.
                Files.move(path,path.resolveSibling(path.getFileName()+".retained-original"));
                Files.write(path,bytes,StandardOpenOption.CREATE_NEW);Files.setLastModifiedTime(path,modified);
                var after=SharedSourceFiles.observe(path);
                assertEquals(before.source(),after.source());
                assertNotEquals(before.nativeFile().identityKey(),after.nativeFile().identityKey());
                // The retired implementation's fresh-basis check accepts this exact content.
                RootArmyStockReadRuntime.ConfiguredOriginals.retain(configuration).requireCurrent();
            } else {
                bytes[0]^=1;Files.write(path,bytes);Files.setLastModifiedTime(path,modified);
                var after=SharedSourceFiles.observe(path);
                assertEquals(before.nativeFile().identityKey(),after.nativeFile().identityKey());
                assertNotEquals(before.source().sha256(),after.source().sha256());
            }
            assertThrows(IOException.class,originals::requireCurrent);
        }
    }

    @Test void originalConfigurationReaderRejectsMissingNullAndWrongTypedSourcesBeforeRetention()throws Exception {
        var configuration=configuration(temporary.resolve("malformed"));var mapper=ControlBuild.strictMapper();
        ObjectNode valid=mapper.valueToTree(configuration);
        for(String field:List.of("input","limits","pair","pins")) {
            var missing=valid.deepCopy();missing.remove(field);
            assertThrows(IOException.class,()->mapper.readValue(StrictJson.canonical(missing,1<<20),RootArmyStockReadRuntime.Configuration.class));
            var nil=valid.deepCopy();nil.putNull(field);
            assertThrows(IOException.class,()->mapper.readValue(StrictJson.canonical(nil,1<<20),RootArmyStockReadRuntime.Configuration.class));
            var wrong=valid.deepCopy();wrong.put(field,true);
            assertThrows(IOException.class,()->mapper.readValue(StrictJson.canonical(wrong,1<<20),RootArmyStockReadRuntime.Configuration.class));
        }
        for(String field:List.of("pair","pins"))for(boolean floating:List.of(false,true)) {
            var wrong=valid.deepCopy();var ref=(ObjectNode)wrong.get(field);
            if(floating)ref.put("bytes",1.0);else ref.put("bytes",true);
            assertThrows(IOException.class,()->mapper.readValue(StrictJson.canonical(wrong,1<<20),RootArmyStockReadRuntime.Configuration.class));
        }
        Files.writeString(Path.of(configuration.pair().path()),"changed",StandardCharsets.UTF_8);
        assertThrows(IOException.class,()->RootArmyStockReadRuntime.ConfiguredOriginals.retain(configuration));
    }

    private static RootArmyStockReadRuntime.Configuration configuration(Path root)throws IOException {
        Files.createDirectories(root);Path pair=root.resolve("pair.json"),pins=root.resolve("pins.json");
        Files.writeString(pair,"{\"custody_only\":\"pair\"}\n",StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
        Files.writeString(pins,"{\"custody_only\":\"pins\"}\n",StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
        return new RootArmyStockReadRuntime.Configuration(new Input(pair,pins,root),
                new RootH2743StockPredicateAdmission.Limits(16,4096,4096,4096),exact(pair),exact(pins));
    }
    private static ExactRef exact(Path path)throws IOException {
        var source=SharedSourceFiles.observe(path).source();return new ExactRef(source.path(),source.bytes(),source.sha256());
    }
}
