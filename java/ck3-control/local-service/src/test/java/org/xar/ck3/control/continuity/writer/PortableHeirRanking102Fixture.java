package org.xar.ck3.control.continuity.writer;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Relocates naturally produced heir Ranking102 DATA; no source qualification, lease, Game or lineage is constructed. */
final class PortableHeirRanking102Fixture {
    private static final int MAXIMUM=ContinuityJson.DOMAIN_MAX_BYTES;
    private static final int TEMPLATE_MAXIMUM=4*1024*1024;
    private PortableHeirRanking102Fixture() { }
    record Originals(ExactRef root,ExactRef legality,ExactRef projection) { }
    static Originals materialize(Path temporary)throws IOException {
        ObjectNode bundle;
        try(var original=PortableHeirRanking102Fixture.class.getResourceAsStream("/heirranking102/original-root-template.json.gz")) {
            if(original==null)throw new IOException("required heir Ranking102 fixture resource absent");
            try(var gzip=new GZIPInputStream(original)) {
                byte[] raw=gzip.readNBytes(TEMPLATE_MAXIMUM+1);if(raw.length>TEMPLATE_MAXIMUM)throw new IOException("bounded heir Ranking102 fixture required");
                bundle=ObjectNode.class.cast(org.xar.ck3.control.contracts.FullJsonTree.parse(raw,TEMPLATE_MAXIMUM));
            }
        }
        StrictJson.require("xar.family-ranking102-software-fixture/v1".equals(bundle.path("schema").textValue()),"exact heir Ranking102 fixture schema required");
        Path root=Files.createTempDirectory(temporary,"family-ranking102-software-").toAbsolutePath().normalize();
        var originals=new Materializer(root,(ObjectNode)bundle.get("files"));
        return new Originals(originals.reference(bundle.path("root_receipt").textValue()),originals.reference(bundle.path("legality_receipt").textValue()),originals.reference(bundle.path("projection_receipt").textValue()));
    }
    private static final class Materializer {
        private final Path root;private final ObjectNode templates;
        private final Map<String,byte[]> bytes=new HashMap<>();private final Map<String,ExactRef> refs=new HashMap<>();
        private final Set<String> active=new HashSet<>();
        Materializer(Path root,ObjectNode templates){this.root=root;this.templates=templates;}
        ExactRef reference(String key)throws IOException {
            if(refs.containsKey(key))return refs.get(key);
            StrictJson.require(active.add(key),"cyclic family heir Ranking102 fixture dependency: "+key);
            try {
                var template=templates.get(key);StrictJson.require(template instanceof ObjectNode,"missing family heir Ranking102 fixture dependency: "+key);
                String format=StrictJson.text(template.get("format"));JsonNode value=transform(template.get("value"));
                byte[] raw=DriverJson.encodeNode(value);
                if(format.equals("driver"))raw=DriverStateSnapshot.decodeComplete(raw).encode();
                else if(format.equals("framed"))raw=ByteBuffer.allocate(raw.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(raw.length).put(raw).array();
                else StrictJson.require(format.equals("full-json"),"unknown family heir Ranking102 fixture format");
                Path path=root.resolve(key+".bin");Files.write(path,raw);bytes.put(key,raw);
                var reference=new ExactRef(path.toString(),raw.length,DriverJson.sha256(raw));refs.put(key,reference);return reference;
            }finally{active.remove(key);}
        }
        private JsonNode transform(JsonNode value)throws IOException {
            if(value.isObject()) {
                if(value.size()==1) {
                    if(value.has("$decimal"))return new org.xar.ck3.control.contracts.DecimalTokenNode(StrictJson.text(value.get("$decimal")));
                    if(value.has("$ref"))return reference(StrictJson.text(value.get("$ref"))).toJson();
                    if(value.has("$hash"))return StrictJson.object().put("v",reference(StrictJson.text(value.get("$hash"))).sha256()).get("v");
                    if(value.has("$length")) {String key=StrictJson.text(value.get("$length"));reference(key);return StrictJson.object().put("v",bytes.get(key).length).get("v");}
                    if(value.has("$path")) {
                        Path path=root.resolve(StrictJson.text(value.get("$path"))).normalize();StrictJson.require(path.startsWith(root),"family heir Ranking102 fixture path escaped its root");
                        return StrictJson.object().put("v",path.toString()).get("v");
                    }
                }
                var result=StrictJson.object();var fields=value.fieldNames();
                while(fields.hasNext()){String field=fields.next();result.set(field,transform(value.get(field)));}return result;
            }
            if(value.isArray()){var result=StrictJson.object().putArray("v");for(var child:value)result.add(transform(child));return result;}
            return value.deepCopy();
        }
    }
}
