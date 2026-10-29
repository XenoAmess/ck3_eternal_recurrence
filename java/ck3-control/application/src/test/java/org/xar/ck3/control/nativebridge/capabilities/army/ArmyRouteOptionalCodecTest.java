package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyRouteOptionalFixtures.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.Iterator;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual retained Python normalizers -> full immutable Java route boundary, including every optional child. */
final class ArmyRouteOptionalCodecTest {
    private static final int MAXIMUM_BYTES=8*1024*1024;
    private static final List<String> SOURCES=List.of("army_captured_target_land_supply_inputs_contract.py","army_county_entry_preview_condition_contract.py",
            "army_county_predicate_trace_contract.py","army_origin_adjacency_contract.py");
    private static final String ORACLE="""
            import hashlib,json,pathlib,sys
            root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player'/'src'))
            from xar_autoplayer.bridge.army_captured_target_land_supply_inputs_contract import normalize_target_land_supply_in_route_preview
            from xar_autoplayer.bridge.army_county_entry_preview_condition_contract import normalize_county_entry_condition_in_route_preview
            names=['army_captured_target_land_supply_inputs_contract.py','army_county_entry_preview_condition_contract.py',
                   'army_county_predicate_trace_contract.py','army_origin_adjacency_contract.py']
            base=root/'ck3_autonomous_player'/'src'/'xar_autoplayer'/'bridge'
            pins={name:hashlib.sha256((base/name).read_bytes()).hexdigest() for name in names}
            outputs=[]
            for item in json.load(sys.stdin)['cases']:
                try:
                    value=normalize_county_entry_condition_in_route_preview(normalize_target_land_supply_in_route_preview(item))
                    outputs.append({'accepted':True,'value':value})
                except (ValueError,TypeError,KeyError,OverflowError):
                    outputs.append({'accepted':False})
            if pins!={name:hashlib.sha256((base/name).read_bytes()).hexdigest() for name in names}:
                raise RuntimeError('actual original optional family sources changed')
            json.dump({'source_sha256':pins,'outputs':outputs},sys.stdout)
            """;
    @Test void allReadableUnavailablePartialTruncatedAndNullableFamiliesPreserveTheExactImmutableRoute() {
        for(ObjectNode fixture:validCases()) {
            var original=json(fixture);assertSame(original,ArmyRouteOptionalCodec.normalize(original));
            var roundtrip=(OpportunityJson.Obj)OpportunityJson.parse(OpportunityJson.encode(original));
            assertEquals(original,ArmyRouteOptionalCodec.normalize(roundtrip));
        }
        var absent=ArmyRouteOptionalCodec.decode(json(route()));assertInstanceOf(ArmyRouteOptionalCodec.Missing.class,absent.county());
        ObjectNode nil=route();nil.putNull("county_entry_condition_v1");
        assertInstanceOf(ArmyRouteOptionalCodec.ObservedNull.class,ArmyRouteOptionalCodec.decode(json(nil)).county());
    }
    @Test void fullWidthPointerIdentitiesNeverPassThroughFloatingPointAndTheFirstRemainingEdgeIsBound() {
        ObjectNode parent=county(true);var typed=ArmyRouteOptionalCodec.decode(json(attach(supply(),parent)));
        var value=((ArmyRouteOptionalCodec.Present<ArmyRouteOptionalCodec.County>)typed.county()).value();
        assertEquals("native:9007199254740993",value.sourceCounty().value());assertEquals("native:18446744073709551615",value.targetCounty().value());
        for(String invalid:List.of("native:01","native:0","native:18446744073709551616","native:9007199254740992.0","native:+1","native:١")) {
            ObjectNode mutation=county(false).put("source_county_identity",invalid);
            assertThrows(IllegalArgumentException.class,()->ArmyRouteOptionalCodec.normalize(json(attach(null,mutation))));
        }
        ObjectNode wrong=attach(null,county(false));wrong.withArray("route_province_ids").set(1,StrictJson.object().put("bad",1));
        assertThrows(IllegalArgumentException.class,()->ArmyRouteOptionalCodec.normalize(json(wrong)));
        ObjectNode noLeadingOrigin=attach(null,county(false));noLeadingOrigin.putArray("route_province_ids").add(13).add(14);
        assertDoesNotThrow(()->ArmyRouteOptionalCodec.normalize(json(noLeadingOrigin)));
        ObjectNode supplyWrong=attach(supply().put("subject_carmy_id",6),null);
        assertThrows(IllegalArgumentException.class,()->ArmyRouteOptionalCodec.normalize(json(supplyWrong)));
    }
    @Test void theFourActualOriginalProducersAgreeOnEveryOptionalFieldWrongTypeMissingFieldAndNestedBinding() throws Exception {
        List<ObjectNode> cases=new ArrayList<>(validCases());ObjectNode rich=rich();cases.add(rich);
        List<List<String>> paths=new ArrayList<>();collect(rich.path("county_entry_condition_v1"),List.of("county_entry_condition_v1"),paths);
        collect(rich.path("province_supply").path("target").path("captured_target_land_supply_inputs_v1"),
                List.of("province_supply","target","captured_target_land_supply_inputs_v1"),paths);
        for(List<String> path:paths) {
            JsonNode original=at(rich,path);
            if(original.isIntegralNumber()) {
                ObjectNode bool=rich.deepCopy();replace(bool,path,com.fasterxml.jackson.databind.node.BooleanNode.TRUE);cases.add(bool);
                ObjectNode fraction=rich.deepCopy();replace(fraction,path,new com.fasterxml.jackson.databind.node.DoubleNode(original.doubleValue()));cases.add(fraction);
            } else if(original.isBoolean()) { ObjectNode numeric=rich.deepCopy();replace(numeric,path,new com.fasterxml.jackson.databind.node.IntNode(0));cases.add(numeric); }
            else if(original.isNull()) { ObjectNode numeric=rich.deepCopy();replace(numeric,path,new com.fasterxml.jackson.databind.node.IntNode(0));cases.add(numeric); }
            else if(original.isTextual()) { ObjectNode unknown=rich.deepCopy();replace(unknown,path,new com.fasterxml.jackson.databind.node.TextNode("malformed"));cases.add(unknown); }
            if(!path.isEmpty()&&!isIndex(path.getLast())) {
                ObjectNode missing=rich.deepCopy();((ObjectNode)at(missing,path.subList(0,path.size()-1))).remove(path.getLast());cases.add(missing);
            }
            if(original.isObject()) {
                ObjectNode extra=rich.deepCopy();((ObjectNode)at(extra,path)).put("unrecognized_new_field",true);cases.add(extra);
            }
        }
        ObjectNode body=StrictJson.object();var input=body.putArray("cases");cases.forEach(input::add);
        Path repo=Path.of(required("xar.repository.root")).toAbsolutePath().normalize();Path source=repo.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge");
        ObjectNode pins=StrictJson.object();for(String name:SOURCES)pins.put(name,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(source.resolve(name)))));
        ProcessBuilder builder=new ProcessBuilder(required("xar.python"),"-B","-X","utf8","-c",ORACLE,repo.toString());
        builder.directory(repo.toFile());builder.environment().put("PYTHONDONTWRITEBYTECODE","1");Process process=builder.start();
        try(var readers=Executors.newVirtualThreadPerTaskExecutor()) {
            var stdout=readers.submit(()->read(process.getInputStream()));var stderr=readers.submit(()->read(process.getErrorStream()));
            try {
                try(var stdin=process.getOutputStream()) { stdin.write(StrictJson.canonical(body,MAXIMUM_BYTES)); }
                assertTrue(process.waitFor(45,TimeUnit.SECONDS),"complete optional-family original producer timeout; no skip");
                byte[] output=stdout.get(5,TimeUnit.SECONDS),errors=stderr.get(5,TimeUnit.SECONDS);
                assertEquals(0,process.exitValue(),new String(errors,StandardCharsets.UTF_8));
                JsonNode original=StrictJson.parse(output,MAXIMUM_BYTES);assertEquals(pins,original.get("source_sha256"));assertEquals(cases.size(),original.path("outputs").size());
                for(int index=0;index<cases.size();index++) {
                    boolean accepted;OpportunityJson.Obj actual=null;
                    try { actual=ArmyRouteOptionalCodec.normalize(json(cases.get(index)));accepted=true; }
                    catch(IllegalArgumentException rejected) { accepted=false; }
                    JsonNode expected=original.path("outputs").get(index);assertEquals(expected.path("accepted").booleanValue(),accepted,"original optional family case "+index);
                    if(accepted)assertEquals(OpportunityJson.parse(StrictJson.canonical(expected.get("value"),MAXIMUM_BYTES)),actual,"full preserved route case "+index);
                }
            } finally { if(process.isAlive())process.destroyForcibly(); }
        }
    }
    private static ObjectNode rich() {
        ObjectNode supply=supply();supply.set("loss_adjustment_operands_v1",loss());ObjectNode county=county(true),trace=trace(true,true,true,true);
        ((ObjectNode)trace.path("stages").get(0)).set("relation_inputs_v1",relation(true,17,true));county.set("predicate_trace_v1",trace);
        county.set("origin_adjacency_v1",adjacency(2));county.put("internal_subpredicates_observed",true);return attach(supply,county);
    }
    private static void collect(JsonNode n,List<String> path,List<List<String>> output) {
        output.add(List.copyOf(path));if(n.isObject()) {
            Iterator<String> names=n.fieldNames();while(names.hasNext()) { String name=names.next();List<String> child=new ArrayList<>(path);child.add(name);collect(n.get(name),child,output); }
        } else if(n.isArray())for(int index=0;index<n.size();index++) { List<String> child=new ArrayList<>(path);child.add("#"+index);collect(n.get(index),child,output); }
    }
    private static boolean isIndex(String part) { return part.startsWith("#"); }
    private static JsonNode at(JsonNode root,List<String> path) { JsonNode current=root;for(String part:path)current=isIndex(part)?current.get(Integer.parseInt(part.substring(1))):current.get(part);return current; }
    private static void replace(ObjectNode root,List<String> path,JsonNode value) {
        JsonNode parent=at(root,path.subList(0,path.size()-1));String key=path.getLast();
        if(isIndex(key))((com.fasterxml.jackson.databind.node.ArrayNode)parent).set(Integer.parseInt(key.substring(1)),value);else ((ObjectNode)parent).set(key,value);
    }
    private static byte[] read(InputStream source) throws IOException { byte[] bytes=source.readNBytes(MAXIMUM_BYTES+1);if(bytes.length>MAXIMUM_BYTES)throw new IOException("original optional producer output exceeds explicit bound");return bytes; }
    private static String required(String property) { String value=System.getProperty(property);assertNotNull(value,"missing complete original producer property "+property);assertFalse(value.isBlank(),"empty original producer property "+property);return value; }
}
