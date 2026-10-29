package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.StrictJson;

/** Synthetic manifest boundary tests. These are neither native packets nor a Person10 corpus qualification. */
final class Person10CorpusManifestTest {
    @TempDir Path temporary;
    private record Fixture(Path root,Path manifest,ObjectNode value,String sha) { }
    @Test void completeManifestReadsExactOriginalsAndDetectsAddedMissingAndModifiedJson() throws Exception {
        Fixture f=fixture();var observed=Person10CorpusManifest.require(f.root(),f.manifest(),f.sha());assertEquals(2,observed.files().size());
        for(var file:observed.files())assertEquals(file.bytes(),file.read().length);
        Files.writeString(f.root().resolve("added.json"),"{}");assertThrows(IllegalArgumentException.class,()->Person10CorpusManifest.verify(observed));
        Files.delete(f.root().resolve("added.json"));Person10CorpusManifest.verify(observed);
        Files.writeString(f.root().resolve("a.json"),"{}");assertThrows(IllegalArgumentException.class,()->Person10CorpusManifest.verify(observed));
        Files.writeString(f.root().resolve("a.json"),"[]");Files.delete(f.root().resolve("b.json"));
        assertThrows(IllegalArgumentException.class,()->Person10CorpusManifest.verify(observed));
    }
    @Test void strictManifestRejectsWrongHashTypesUnknownFieldsOrderAndEscapingPaths() throws Exception {
        Fixture f=fixture();assertThrows(IllegalArgumentException.class,()->Person10CorpusManifest.require(f.root(),f.manifest(),"0".repeat(64)));
        for(String field:new String[]{"schema","machine_id","observed_at_utc","corpus_root","files"}){
            ObjectNode missing=f.value().deepCopy();missing.remove(field);checkRejected(f,missing);
        }
        ObjectNode unknown=f.value().deepCopy();unknown.put("file_alias",true);checkRejected(f,unknown);
        ObjectNode booleanBytes=f.value().deepCopy();((ObjectNode)booleanBytes.get("files").get(0)).put("bytes",true);checkRejected(f,booleanBytes);
        ObjectNode floatBytes=f.value().deepCopy();((ObjectNode)floatBytes.get("files").get(0)).put("bytes",2.0);checkRejected(f,floatBytes);
        ObjectNode stringBytes=f.value().deepCopy();((ObjectNode)stringBytes.get("files").get(0)).put("bytes","2");checkRejected(f,stringBytes);
        ObjectNode escaping=f.value().deepCopy();((ObjectNode)escaping.get("files").get(0)).put("path",temporary.resolve("outside.json").toString());checkRejected(f,escaping);
        ObjectNode duplicate=f.value().deepCopy();((ArrayNode)duplicate.get("files")).set(1,duplicate.get("files").get(0));checkRejected(f,duplicate);
        ObjectNode order=f.value().deepCopy();ArrayNode entries=(ArrayNode)order.get("files");JsonNode first=entries.get(0),second=entries.get(1);entries.set(0,second);entries.set(1,first);checkRejected(f,order);
        ObjectNode byteDrift=f.value().deepCopy();((ObjectNode)byteDrift.get("files").get(0)).put("sha256","f".repeat(64));checkRejected(f,byteDrift);
    }
    private static void checkRejected(Fixture f,ObjectNode changed) throws Exception {
        byte[] raw=StrictJson.canonical(changed);Files.write(f.manifest(),raw);String sha=digest(raw);
        assertThrows(IllegalArgumentException.class,()->Person10CorpusManifest.require(f.root(),f.manifest(),sha));
    }
    private Fixture fixture() throws Exception {
        Path root=Files.createDirectory(temporary.resolve("corpus")).toRealPath(),manifest=temporary.resolve("person10-manifest.json");
        Files.writeString(root.resolve("a.json"),"[]");Files.writeString(root.resolve("b.json"),"{}");
        ObjectNode value=StrictJson.object().put("schema","xar.person10-native-corpus/v1").put("machine_id","synthetic-manifest-fixture-machine")
            .put("observed_at_utc","2026-10-23T00:00:00Z").put("corpus_root",root.toString());ArrayNode files=value.putArray("files");
        for(String name:new String[]{"a.json","b.json"}){Path path=root.resolve(name);byte[] raw=Files.readAllBytes(path);files.addObject().put("path",path.toString()).put("bytes",raw.length).put("sha256",digest(raw));}
        byte[] raw=StrictJson.canonical(value);Files.write(manifest,raw);return new Fixture(root,manifest,value,digest(raw));
    }
    private static String digest(byte[] raw) throws Exception {return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));}
}
