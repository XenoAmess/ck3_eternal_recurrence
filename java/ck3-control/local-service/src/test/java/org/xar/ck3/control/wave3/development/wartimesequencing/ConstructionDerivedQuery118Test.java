package org.xar.ck3.control.wave3.development.wartimesequencing;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.*;
import java.math.BigInteger;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.function.Supplier;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.application.planning.finance.ConstructionOriginalSource;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryCodec;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec.ObservedRequest;

/** New SDK derived-node DATA only; no writer/Guard issuer/Native/Runtime authority.
 * Existing complete/history methods are pure fixture builders, never old @Test methods.
 * Every positive public-node input is normalized by the existing FullJsonTree raw parser.
 */
final class ConstructionDerivedQuery118Test {
    private static final int FULL=FullJsonTree.MAXIMUM_BYTES;
    private static final JsonNodeFactory N=JsonNodeFactory.instance;

    @Test void full139InputKeepsExactQuerySdkFinalizerAndTypedResult()throws Exception {
        ObjectNode root=standardOuter();JsonNode history=fixture("retainedHistory139");assertEquals(139,history.size());
        for(String field:List.of("starting_snapshot","ending_snapshot"))((ObjectNode)query(root).get(field)).set("native_command_history",history.deepCopy());
        ObjectNode world=world(query(root));
        world.set("opaque_derived118",parse("{\"z\":1.00,\"a\":-0.0,\"fraction\":0.123456789012345678901,\"exp\":1e+0,\"nested\":{\"last\":2,\"first\":1},\"rows\":[null,false,{},[]]}"));
        byte[] original=wire(root),caller=original.clone();assertTrue(original.length>6_000_000);
        ObjectNode owned=(ObjectNode)FullJsonTree.parse(original,FULL);ObjectNode q=query(owned);byte[] oldRaw=wire(q);
        var derived=ConstructionQueryCodec.deriveFullMaterialQuery(q);assertArrayEquals(oldRaw,derived.originalQueryBytes());
        assertArrayEquals(ConstructionQueryCodec.projectFullMaterialInput(oldRaw),derived.sdkRoleBytes());
        NativeQuote oldQuote=NativeQuote.fromFullMaterial(oldRaw);assertTrue(oldQuote.selected().isPresent());
        var actual=ObservedRequest.fromFullMaterial(caller);caller[0]='[';var current=actual.input().quoted().orElseThrow();
        assertNativeValue(oldQuote,current.nativeQuote());assertArrayEquals(oldRaw,current.nativeQuote().original());
        byte[] fixed=ConstructionOriginalSource.finalizeQuery(oldRaw);
        assertArrayEquals(fixed,current.nativeQuote().exactFullFinalizedBytes().orElseThrow());
        assertTrue(new String(fixed,StandardCharsets.UTF_8).contains("0.123456789012345678901"));
        var oldTyped=new Request(actual.input().selection(),actual.input().stage(),actual.input().current(),
                Optional.of(new QuotedOutlay(oldQuote,current.currentCash())),actual.input().financing());
        Result before=compose(oldTyped),after=compose(actual.input());assertEquals(Disposition.QUOTED_CANDIDATE,before.disposition());
        assertEquals(Disposition.QUOTED_CANDIDATE,after.disposition());assertArrayEquals(OrdinaryWartimeConstructionCodec.encode(before),OrdinaryWartimeConstructionCodec.encode(after));
        byte[] exposed=actual.original();exposed[0]='!';assertArrayEquals(original,actual.original());assertArrayEquals(original,wire(root));
    }
    @Test void closedCarrierOwnsSnapshotGetterBytesAndIndependentInstances()throws Exception {
        ObjectNode q=standardQuery();byte[] raw=wire(q);var first=ConstructionQueryCodec.deriveFullMaterialQuery(q);
        byte[] sdk=ConstructionQueryCodec.projectFullMaterialInput(raw);NativeQuote firstQuote=NativeQuote.fromDerivedProjection(first);
        assertTrue(firstQuote.selected().isPresent());byte[] fixed=ConstructionOriginalSource.finalizeQuery(raw);
        ((ObjectNode)q.path("native_envelope").path("result").path("private_probe")).set("proof_epoch",N.numberNode(BigInteger.TWO));
        ((ObjectNode)q.get("starting_snapshot")).set("new_caller_mutation",N.textNode("later"));
        byte[] rawGetter=first.originalQueryBytes(),sdkGetter=first.sdkRoleBytes();rawGetter[0]='[';sdkGetter[0]='!';
        assertArrayEquals(raw,first.originalQueryBytes());assertArrayEquals(sdk,first.sdkRoleBytes());
        assertArrayEquals(raw,firstQuote.original());assertArrayEquals(fixed,firstQuote.exactFullFinalizedBytes().orElseThrow());
        var second=ConstructionQueryCodec.deriveFullMaterialQuery(q);NativeQuote secondQuote=NativeQuote.fromDerivedProjection(second);
        assertFalse(Arrays.equals(first.originalQueryBytes(),second.originalQueryBytes()));
        assertFalse(Arrays.equals(firstQuote.exactFullFinalizedBytes().orElseThrow(),secondQuote.exactFullFinalizedBytes().orElseThrow()));
        byte[] other=second.originalQueryBytes();other[0]='!';assertArrayEquals(raw,first.originalQueryBytes());
        assertArrayEquals(wire(q),secondQuote.original());
    }
    // Only the deliberately rejected Jackson container subclass fixtures inherit unchecked deepCopy bridges.
    @SuppressWarnings("unchecked")
    @Test void newNodeDomainRejectsCustomAndNullPayloadsButPreservesOpaqueText()throws Exception {
        List<Supplier<JsonNode>> rejected=List.of(
                ()->new ObjectNode(N){},()->new ArrayNode(N){},()->new TextNode("custom"){},
                ()->new TextNode(null),()->new BigIntegerNode((BigInteger)null),
                ()->new BigIntegerNode(new BigInteger("7"){}),()->IntNode.valueOf(7),()->LongNode.valueOf(7),
                ()->DoubleNode.valueOf(1.0),()->DoubleNode.valueOf(Double.NaN),()->DecimalNode.valueOf(new BigDecimal("1.00")),
                ConstructionDerivedQuery118Test::nullChildObject,ConstructionDerivedQuery118Test::nullKeyObject);
        int count=0;
        for(var factory:rejected){ObjectNode q=standardQuery();((ObjectNode)q.get("starting_snapshot")).set("opaque_rejected118",factory.get());
            assertThrows(RuntimeException.class,()->ConstructionQueryCodec.deriveFullMaterialQuery(q));count++;}
        assertThrows(RuntimeException.class,()->ConstructionQueryCodec.deriveFullMaterialQuery(null));
        ObjectNode q=standardQuery(),snapshot=(ObjectNode)q.get("starting_snapshot");
        snapshot.set("",N.textNode(""));snapshot.set("k".repeat(40_000),N.textNode(""));snapshot.set("opaque_long_text118",N.textNode("v".repeat(40_000)));
        snapshot.set("escaped_and_nonbmp118",parse("\"\\u6c49\\u5b57\\ud83d\\ude80\\n\\\"\\\\\""));assertDerivedValue(q);
        snapshot.set("opaque_surrogate118",parse("\"\\ud800\""));
        boolean oldEncoded=true;byte[] old=null;
        try{old=wire(q);}catch(RuntimeException refused){oldEncoded=false;}
        if(oldEncoded){var derived=ConstructionQueryCodec.deriveFullMaterialQuery(q);assertArrayEquals(old,derived.originalQueryBytes());assertArrayEquals(ConstructionQueryCodec.projectFullMaterialInput(old),derived.sdkRoleBytes());}
        else assertThrows(RuntimeException.class,()->ConstructionQueryCodec.deriveFullMaterialQuery(q));
        System.out.println("P118 restrictedNodeRefusals="+count+" escapedSurrogateOldDerivedAccepted="+oldEncoded);
    }
    @Test void depthScalarEmptyAndNonemptyContainersMatchActualOldByteParser()throws Exception {
        record Row(int wrappers,String leaf,boolean accepted){}
        List<Row> rows=List.of(new Row(62,"0",true),new Row(63,"0",false),new Row(61,"{}",true),new Row(62,"{}",false),
                new Row(61,"{\"leaf\":0}",true),new Row(62,"{\"leaf\":0}",false));int checked=0;
        for(boolean array:List.of(false,true))for(Row row:rows) {
            ObjectNode template=standardQuery();((ObjectNode)template.get("starting_snapshot")).set("depth_slot118",N.textNode("DEPTH-MARKER-118"));
            String base=new String(wire(template),StandardCharsets.UTF_8);String marker="\"DEPTH-MARKER-118\"";
            assertEquals(base.indexOf(marker),base.lastIndexOf(marker));assertTrue(base.contains(marker));
            String prefix=array?"[":"{\"n\":",suffix=array?"]":"}";
            String literal=prefix.repeat(row.wrappers())+row.leaf()+suffix.repeat(row.wrappers());
            byte[] raw=base.replace(marker,literal).getBytes(StandardCharsets.UTF_8);
            JsonNode child=parse(row.leaf());for(int i=0;i<row.wrappers();i++){if(array){ArrayNode parent=N.arrayNode();parent.add(child);child=parent;}else{ObjectNode parent=N.objectNode();parent.set("n",child);child=parent;}}
            ((ObjectNode)template.get("starting_snapshot")).set("depth_slot118",child);
            boolean oldAccepted=true;try{FullJsonTree.parse(raw,FULL);}catch(RuntimeException refused){oldAccepted=false;}
            assertEquals(row.accepted(),oldAccepted,"actual old byte parser: array="+array+" row="+row);
            if(oldAccepted){var derived=ConstructionQueryCodec.deriveFullMaterialQuery(template);assertArrayEquals(raw,derived.originalQueryBytes());assertArrayEquals(ConstructionQueryCodec.projectFullMaterialInput(raw),derived.sdkRoleBytes());}
            else assertThrows(RuntimeException.class,()->ConstructionQueryCodec.deriveFullMaterialQuery(template));checked++;
        }
        System.out.println("P118 actualOldByteDepthBoundaryRows="+checked);
    }
    @Test void closedRootsConsumedBudgetsAndOldSmallBytePathRemainUnchanged()throws Exception {
        ObjectNode baseline=standardQuery();assertTrue(NativeQuote.fromFullMaterial(wire(baseline)).selected().isPresent());
        List<Consumer<ObjectNode>> malformed=List.of(q->q.put("unknown_root",true),q->q.remove("expected_revision"),q->q.put("schema","wrong"),
                q->q.putNull("starting_snapshot"),q->q.put("material_receipt",1),
                q->((ObjectNode)q.get("native_envelope")).put("opaque_large118","x".repeat(ConstructionQueryCodec.MAX_BYTES)),
                q->((ObjectNode)q.path("starting_snapshot").path("played_character")).put("opaque_large118","x".repeat(ConstructionQueryCodec.MAX_BYTES)));
        for(var mutate:malformed){ObjectNode q=standardQuery();mutate.accept(q);ObjectNode canonical=(ObjectNode)FullJsonTree.parse(wire(q),FULL);
            assertThrows(RuntimeException.class,()->NativeQuote.fromFullMaterial(wire(canonical)));
            assertThrows(RuntimeException.class,()->NativeQuote.fromDerivedProjection(ConstructionQueryCodec.deriveFullMaterialQuery(canonical)));}
        ObjectNode q=standardQuery();((ObjectNode)q.get("starting_snapshot")).set("native_command_history",N.textNode("x".repeat(ConstructionQueryCodec.MAX_BYTES)));
        assertDerivedValue(q);
        byte[] small=wire(standardQuery());assertTrue(small.length<ConstructionQueryCodec.MAX_BYTES);NativeQuote oldSmall=new NativeQuote(small);
        NativeQuote derived=NativeQuote.fromDerivedProjection(ConstructionQueryCodec.deriveFullMaterialQuery((ObjectNode)FullJsonTree.parse(small,FULL)));
        assertTrue(oldSmall.exactFullFinalizedBytes().isEmpty());assertNativeValue(oldSmall,derived);
        assertArrayEquals(ConstructionOriginalSource.finalizeQuery(small),derived.exactFullFinalizedBytes().orElseThrow());
    }
    @Test void derivedQueryOutputKeepsExisting64MiBBudgetWhileOldLiteralByteEntryKeepsItsDomain()throws Exception {
        ObjectNode q=standardQuery();ObjectNode opaque=N.objectNode();opaque.set("large",N.textNode("P118-LARGE-NUMBER"));opaque.set("unicode",N.textNode("P118-LITERAL-EMOJI"));
        ((ObjectNode)q.get("starting_snapshot")).set("opaque_expansion118",opaque);
        byte[] raw=nearLimitLiteralQuery(wire(q));assertEquals(FULL-1,raw.length);
        assertOldStandaloneBytePositive(raw);
        int expanded=expandedLength(raw);assertTrue(expanded>FULL);
        assertOldDerivedEncodeRefused(raw);
        RuntimeException rejected=assertThrows(RuntimeException.class,()->ConstructionQueryCodec.deriveFullMaterialQuery(FullJsonTree.parse(raw,FULL)));
        assertTrue(rejected.getMessage().contains("explicit lease"));
        System.out.println("P118 queryLiteralRaw="+raw.length+" derivedEncoding="+expanded+" oldByteSelected=true oldDerived64Rejected=true newDerived64Rejected=true");
    }
    private static void assertOldStandaloneBytePositive(byte[] raw){NativeQuote old=NativeQuote.fromFullMaterial(raw);assertTrue(old.selected().isPresent());assertArrayEquals(raw,old.original());}
    private static int expandedLength(byte[] raw){return FullJsonTree.encode(FullJsonTree.parse(raw,FULL),FullJsonTree.MAXIMUM_DRIVER_BYTES).length;}
    private static void assertOldDerivedEncodeRefused(byte[] raw){RuntimeException rejected=assertThrows(RuntimeException.class,()->wire(FullJsonTree.parse(raw,FULL)));assertTrue(rejected.getMessage().contains("explicit lease"));}
    private static byte[] nearLimitLiteralQuery(byte[] base){
        byte[] number="\"P118-LARGE-NUMBER\"".getBytes(StandardCharsets.US_ASCII),unicode="\"P118-LITERAL-EMOJI\"".getBytes(StandardCharsets.US_ASCII);
        int n=indexOf(base,number),u=indexOf(base,unicode);assertTrue(n>=0&&u>n);
        byte[] literal=("\""+new String(Character.toChars(0x1F600)).repeat(6000)+"\"").getBytes(StandardCharsets.UTF_8);
        int target=FULL-1,numLength=target-(base.length-number.length-unicode.length+literal.length);assertTrue(numLength>60_000_000);
        byte[] raw=new byte[target];int offset=0;System.arraycopy(base,0,raw,0,n);offset+=n;raw[offset++]='1';raw[offset++]='e';raw[offset++]='+';
        Arrays.fill(raw,offset,offset+numLength-3,(byte)'0');offset+=numLength-3;int middle=n+number.length;
        System.arraycopy(base,middle,raw,offset,u-middle);offset+=u-middle;System.arraycopy(literal,0,raw,offset,literal.length);offset+=literal.length;
        int tail=u+unicode.length;System.arraycopy(base,tail,raw,offset,base.length-tail);offset+=base.length-tail;assertEquals(raw.length,offset);return raw;
    }
    private static int indexOf(byte[] source,byte[] target){outer:for(int s=0;s<=source.length-target.length;s++){for(int i=0;i<target.length;i++)if(source[s+i]!=target[i])continue outer;return s;}return -1;}
    private static JsonNode nullChildObject(){Map<String,JsonNode> map=new LinkedHashMap<>();map.put("bad",null);return new ObjectNode(N,map);}
    private static JsonNode nullKeyObject(){Map<String,JsonNode> map=new LinkedHashMap<>();map.put(null,NullNode.instance);return new ObjectNode(N,map);}
    private static void assertDerivedValue(ObjectNode q){byte[] raw=wire(q);var derived=ConstructionQueryCodec.deriveFullMaterialQuery(q);assertArrayEquals(raw,derived.originalQueryBytes());
        assertArrayEquals(ConstructionQueryCodec.projectFullMaterialInput(raw),derived.sdkRoleBytes());NativeQuote before=NativeQuote.fromFullMaterial(raw),after=NativeQuote.fromDerivedProjection(derived);assertNativeValue(before,after);
        assertEquals(before.exactFullFinalizedBytes().isPresent(),after.exactFullFinalizedBytes().isPresent());before.exactFullFinalizedBytes().ifPresent(bytes->assertArrayEquals(bytes,after.exactFullFinalizedBytes().orElseThrow()));}
    private static void assertNativeValue(NativeQuote before,NativeQuote after){assertEquals(before.observation(),after.observation());assertEquals(before.constructionKind(),after.constructionKind());assertEquals(before.selected().isPresent(),after.selected().isPresent());
        if(before.selected().isPresent()){assertEquals(before.selected().orElseThrow().candidate(),after.selected().orElseThrow().candidate());assertEquals(before.selected().orElseThrow().sourceFrame(),after.selected().orElseThrow().sourceFrame());assertArrayEquals(before.selected().orElseThrow().original().bytes(),after.selected().orElseThrow().original().bytes());}}
    private static ObjectNode query(ObjectNode outer){return (ObjectNode)outer.get("quoted_outlay").get("query_observation");}
    private static ObjectNode world(ObjectNode q){return (ObjectNode)q.path("native_envelope").path("result").path("private_probe").path("player_world_building_sources");}
    private static ObjectNode standardOuter()throws Exception{return (ObjectNode)FullJsonTree.parse(wire(fixture("complete")),FULL);}
    private static ObjectNode standardQuery()throws Exception{return query(standardOuter());}
    private static JsonNode fixture(String name)throws Exception{Class<?> type=Class.forName("org.xar.ck3.control.wave3.development.wartimesequencing.ConstructionFullOriginal113SdkTest");var method=type.getDeclaredMethod(name);method.setAccessible(true);return (JsonNode)method.invoke(null);}
    private static JsonNode parse(String json){return FullJsonTree.parse(json.getBytes(StandardCharsets.UTF_8),FULL);}
    private static byte[] wire(JsonNode value){return FullJsonTree.encode(value,FULL);}
}
