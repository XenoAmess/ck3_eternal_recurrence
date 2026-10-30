package org.xar.ck3.control.application.session;

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
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Materializes a small derived software fixture under JUnit's temporary directory.
 * Symbolic references are rebuilt from their actual bytes after relocation. No
 * original machine path, physical Native custody or historical qualification exists.
 */
final class PortableSettledFixture {
    private static final String RESOURCE="/settledrecovery/settled35-template.json.gz";
    private static final int MAXIMUM=ContinuityJson.DOMAIN_MAX_BYTES;
    private PortableSettledFixture() { }

    static Path materialize(Path temporary) throws IOException {
        return materialize(temporary,35);
    }
    static Path materialize38(Path temporary) throws IOException {
        return materialize(temporary,38);
    }
    static Path materialize42(Path temporary) throws IOException {
        return materialize(temporary,42);
    }
    static Path materialize(Path temporary,int lastSequence) throws IOException {
        StrictJson.require(lastSequence==35||lastSequence==38||lastSequence==42,"supported portable settled frontier required");
        Path root=Files.createTempDirectory(temporary,"settled-software-").toAbsolutePath().normalize();
        ObjectNode bundle;
        try(var original=PortableSettledFixture.class.getResourceAsStream(RESOURCE)) {
            if(original==null)throw new IOException("required settled recovery fixture resource is absent");
            try(var gzip=new GZIPInputStream(original)) {
                byte[] bytes=gzip.readNBytes(MAXIMUM+1);
                if(bytes.length>MAXIMUM)throw new IOException("settled fixture resource exceeds its finite bound");
                bundle=ContinuityJson.parseObject(bytes,MAXIMUM);
            }
        }
        StrictJson.require("xar.settled-recovery-software-fixture-template/v1".equals(bundle.path("schema").textValue()),
                "exact portable fixture template required");
        var materializer=new Materializer(root,(ObjectNode)bundle.get("files"),lastSequence);
        materializer.bytes("state-000");
        for(int sequence=1;sequence<=lastSequence;sequence++)materializer.bytes(String.format(java.util.Locale.ROOT,"event-%03d",sequence));
        materializer.bytes(String.format(java.util.Locale.ROOT,"state-%03d",lastSequence));
        return root;
    }

    private static final class Materializer {
        private final Path root;
        private final ObjectNode templates;
        private final int lastSequence;
        private final Map<String,byte[]> originals=new HashMap<>();
        private final Map<String,ExactRef> references=new HashMap<>();
        private final Set<String> active=new HashSet<>();
        Materializer(Path root,ObjectNode templates,int lastSequence) {this.root=root;this.templates=templates;this.lastSequence=lastSequence;}

        private Path path(String key) {
            if(key.equals("state-000"))return root.resolve("genesis-anchor.json");
            if(key.equals(String.format(java.util.Locale.ROOT,"state-%03d",lastSequence)))return root.resolve("continuity.json");
            if(key.matches("event-[0-9]{3}"))return root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS")
                    .resolve(String.format(java.util.Locale.ROOT,"%08d.json",Integer.parseInt(key.substring(6))));
            return root.resolve("artifacts").resolve(key+".bin");
        }
        byte[] bytes(String key) throws IOException {
            byte[] existing=originals.get(key);if(existing!=null)return existing.clone();
            StrictJson.require(active.add(key),"portable fixture dependency cycle: "+key);
            try {
                JsonNode value=templates.get(key);StrictJson.require(value instanceof ObjectNode,"unknown portable fixture dependency: "+key);
                var template=(ObjectNode)value;String format=StrictJson.text(template.get("format"));
                JsonNode transformed=transform(template.get("value"));byte[] result;
                if(format.equals("event")) {
                    int sequence=(int)StrictJson.integer(template.get("sequence"),1,lastSequence);
                    var event=StrictJson.object();event.put("kind",StrictJson.text(template.get("kind")));event.put("sequence",sequence);
                    event.set("details",transformed);event.put("identity",reference(String.format(java.util.Locale.ROOT,"event-identity-%03d",sequence)).sha256());
                    event.set("after",ContinuityJson.parseObject(bytes(StrictJson.text(template.get("state"))),MAXIMUM));
                    result=ContinuityJson.canonical(event,MAXIMUM);
                } else if(format.equals("event-identity")) {
                    var request=StrictJson.object();request.put("kind",StrictJson.text(template.get("kind")));request.set("details",transformed);
                    result=ContinuityJson.canonical(request,MAXIMUM);
                } else if(format.equals("command")) {
                    result=ActionCodec.encodeCommand(ActionCodec.decodeCommand(ContinuityJson.canonical(transformed,MAXIMUM)));
                } else if(format.equals("driver")) {
                    result=org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.decodeComplete(ContinuityJson.canonical(transformed,MAXIMUM)).encode();
                } else {
                    result=ContinuityJson.canonical(transformed,MAXIMUM);
                    if(format.equals("framed"))result=ByteBuffer.allocate(result.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(result.length).put(result).array();
                    else StrictJson.require(format.equals("json"),"unknown portable fixture encoding");
                }
                Path target=path(key);Files.createDirectories(target.getParent());Files.write(target,result);
                originals.put(key,result);references.put(key,new ExactRef(target.toString(),result.length,ActionCodec.sha256(result)));
                return result.clone();
            } finally {active.remove(key);}
        }
        private ExactRef reference(String key) throws IOException {bytes(key);return references.get(key);}
        private JsonNode transform(JsonNode value) throws IOException {
            if(value.isObject()) {
                if(value.size()==1) {
                    if(value.has("$path")) {
                        Path target=root.resolve(StrictJson.text(value.get("$path"))).toAbsolutePath().normalize();
                        StrictJson.require(target.startsWith(root),"fixture path escaped temporary root");
                        return StrictJson.object().put("value",target.toString()).get("value");
                    }
                    if(value.has("$ref"))return reference(StrictJson.text(value.get("$ref"))).toJson();
                    if(value.has("$hash"))return StrictJson.object().put("value",reference(StrictJson.text(value.get("$hash"))).sha256()).get("value");
                    if(value.has("$length"))return StrictJson.object().put("value",bytes(StrictJson.text(value.get("$length"))).length).get("value");
                    if(value.has("$body"))return StrictJson.object().put("value",ActionCodec.bodySha256(ActionCodec.decodeCommand(bytes(StrictJson.text(value.get("$body")))))).get("value");
                }
                ObjectNode result=StrictJson.object();var fields=value.fieldNames();
                while(fields.hasNext()){String field=fields.next();result.set(field,transform(value.get(field)));}
                return result;
            }
            if(value.isArray()) {
                var result=StrictJson.object().putArray("items");for(JsonNode child:value)result.add(transform(child));return result;
            }
            return value.deepCopy();
        }
    }
}
