package org.xar.ck3.control.nativebridge.capabilities.frontend_coa;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaContract;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaPostconditions.*;

/** Original Python JSON -> actual Java native decoder/domain validator/shared public formatter. No live permission is issued. */
final class CoaDesignerParityTest {
    private static final BigInteger WIDE=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private static final Instant NOW=Instant.parse("2026-10-24T04:00:00Z");
    private static final ExactRef DATA=new ExactRef("D:/controlled-coa-parity/native-data.json",1,"a".repeat(64));
    private static final String ORACLE="""
        import json,pathlib,runpy,sys
        root=pathlib.Path(sys.argv[1]).resolve()
        m=runpy.run_path(str(root/'ck3_autonomous_player/src/xar_autoplayer/bridge/frontend_gui_route_contract.py'))
        x=json.load(sys.stdin)
        route=lambda key:m['normalize_frontend_gui_route_v1'](x[key])
        tree=lambda key:m['normalize_frontend_gui_tree_inspection_v1'](x[key])
        out={
          'tree':m['normalize_frontend_coat_of_arms_tree_inspection_v1'](x['coa']),
          'grid':m['normalize_frontend_coat_of_arms_pattern_grid_inspection_v1'](x['grid']),
          'open':m['normalize_frontend_open_coat_of_arms_designer_v1'](x['open_ack'],before=route('ruler_route'),before_inspection=tree('ruler'),after=route('coa_route')),
          'commit':m['normalize_frontend_commit_dynasty_coat_of_arms_v1'](x['commit_ack'],before=route('coa_route'),before_inspection=tree('finish'),after=route('ruler_route')),
          'custom':m['normalize_frontend_enter_coat_of_arms_custom_mode_v1'](x['custom_ack'],before=route('coa_route'),before_inspection=m['normalize_frontend_coat_of_arms_tree_inspection_v1'](x['coa']),after=route('coa_route'),after_inspection=m['normalize_frontend_coat_of_arms_tree_inspection_v1'](x['background']))
        }
        # Explicit migration of unsigned64 wire fields to canonical decimal strings; no float/Number roundtrip.
        def public(v):
          if isinstance(v,list):return [public(a) for a in v]
          if isinstance(v,dict):
            return {k:(str(a) if k in ('vtable_rva','query_sequence','snapshot_revision') and isinstance(a,int) and not isinstance(a,bool) else public(a)) for k,a in v.items()}
          return v
        print(json.dumps(public(out),ensure_ascii=False,separators=(',',':')))
        """;
    private static ObjectNode object(String json){return FrontendCoaCodec.object(new RawJson(json.getBytes(StandardCharsets.UTF_8)));}
    private static RawJson raw(ObjectNode node){return FrontendCoaCodec.raw(node);}
    private static ObjectNode widget(String path,String name,int children){
        var row=FrontendCoaCodec.empty().put("runtime_name",name).put("child_path",path).put("depth",path.isEmpty()?0:path.split("/").length)
                .put("child_count",children).put("vtable_rva",WIDE).put("effective_visible",true).put("enabled",true);return row;
    }
    private static ObjectNode tree(String step,String root,ObjectNode...widgets){
        var row=FrontendCoaCodec.empty().put("step",step).put("accepted",true).put("status","available").put("scope_root_name",root)
                .put("root_available",true).put("truncated",false).put("widget_count",widgets.length).put("backend_id","native-headless");
        var out=row.putArray("widgets");for(var widget:widgets)out.add(widget);return row;
    }
    private static ObjectNode ack(DesignerAction action){
        return FrontendCoaCodec.empty().put("step",action.step()).put("accepted",true).put("status","acknowledged_verification_pending")
                .put("backend_id","native-headless").put("query_sequence",WIDE).put("original_engine_note","preserved exact native field");
    }
    private static ObjectNode fixtures(){
        var row=FrontendCoaCodec.empty();
        row.set("ruler_route",object("{\"step\":\"query-frontend-gui-route-v1\",\"accepted\":true,\"status\":\"ruler_designer\",\"backend_id\":\"native-headless\"}"));
        row.set("coa_route",object("{\"step\":\"query-frontend-gui-route-v1\",\"accepted\":true,\"status\":\"coat_of_arms_designer\",\"backend_id\":\"native-headless\"}"));
        row.set("ruler",tree("inspect-frontend-gui-tree-v1","ruler_designer",widget("0/0/0/0/0/0/0/3/1/0","",2)));
        row.set("finish",tree("inspect-frontend-gui-tree-v1","ruler_designer",widget("0/2/1/1","dynasty_finish_button",0)));
        row.set("coa",tree("inspect-frontend-coat-of-arms-tree-v1","coat_of_arms_page",widget("0/3/0/2/1/0/0/1/1/0","button_custom_mode",0)));
        row.set("background",tree("inspect-frontend-coat-of-arms-tree-v1","coat_of_arms_page",
                widget("0/3/0/2/0","coa_designer_tabs",0),widget("0/3/0/2/1/1","background_panel",0),
                widget("0/3/0/2/1/1/2","patterns",0),widget("0/3/0/2/1/1/2/0/0","patterns_scrollbox",0)));
        row.set("grid",tree("inspect-frontend-coat-of-arms-pattern-grid-v1","coat_of_arms_pattern_grid",widget("","",2),widget("0","",0),widget("1","",0)));
        row.set("open_ack",ack(DesignerAction.OPEN));row.set("commit_ack",ack(DesignerAction.COMMIT));row.set("custom_ack",ack(DesignerAction.CUSTOM_MODE));return row;
    }
    private static ObjectNode original(ObjectNode input)throws Exception{
        String repository=System.getProperty("xar.repository.root"),python=System.getProperty("xar.python");
        assertNotNull(repository,"original workspace is mandatory; no skip");assertNotNull(python,"original Python interpreter is mandatory; no skip");
        assertFalse(repository.isBlank());assertFalse(python.isBlank());Path root=Path.of(repository).toRealPath();
        assertTrue(Files.isRegularFile(root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/frontend_gui_route_contract.py")));
        byte[] bytes=raw(input).bytes();assertTrue(bytes.length<32*1024,"oracle fixture stays below bounded pipe capacity");
        Process child=new ProcessBuilder(python,"-X","utf8","-c",ORACLE,root.toString()).redirectErrorStream(true).start();
        try {
            try(var stream=child.getOutputStream()){stream.write(bytes);}
            boolean ended=child.waitFor(30,TimeUnit.SECONDS);if(!ended)child.destroyForcibly();assertTrue(ended,"original CoA oracle timeout");
            byte[] output=child.getInputStream().readNBytes(65537);assertTrue(output.length<=65536,"original oracle output budget exceeded");
            assertEquals(0,child.exitValue(),new String(output,StandardCharsets.UTF_8));return FrontendCoaCodec.object(new RawJson(output));
        } finally {if(child.isAlive())child.destroyForcibly();}
    }
    private static FrontendRulesData.Source source(){return new FrontendRulesData.Source(new FrontendRulesData.Binding(123,WIDE),FrontendRulesData.Build.CK3_12004);}
    private static ReadEvidence<FrontendRulesData.ObservedRoute> route(FrontendRulesData.Route route,int sequence){
        return new ReadEvidence<>(new FrontendRulesData.ObservedRoute(route,source(),BigInteger.valueOf(sequence)),"route-"+sequence,NOW.plusMillis(sequence),DATA);
    }
    private static ReadEvidence<CoaData.Tree> inspected(CoaData.Tree tree,int sequence){return new ReadEvidence<>(tree,"tree-"+sequence,NOW.plusMillis(sequence),DATA);}
    private static DesignerVerified verify(DesignerAction action,ObjectNode fixtures){
        var before=route(action.beforeRoute(),1);var after=route(action.afterRoute(),5);
        String key=action==DesignerAction.OPEN?"ruler":action==DesignerAction.COMMIT?"finish":"coa";
        var nativeTree=(ObjectNode)fixtures.get(key);CoaData.Tree tree=action==DesignerAction.CUSTOM_MODE?CoaCodec.tree(raw(nativeTree),false):CoaCodec.rulerDesignerTree(raw(nativeTree));
        var ack=ack(action);return designer(action,before,inspected(tree,2),CoaCodec.activationAck(raw(ack),action.step()),"mutation-3",NOW.plusMillis(3),after,
                action==DesignerAction.CUSTOM_MODE?Optional.of(inspected(CoaCodec.tree(raw((ObjectNode)fixtures.get("background")),false),6)):Optional.empty());
    }
    @Test void allFiveOriginalPublicResultsMatchPythonIncludingCompleteOriginalAckAndUnsigned64WireFields()throws Exception{
        var fixture=fixtures();var expected=original(fixture);var actual=FrontendCoaCodec.empty();
        actual.set("tree",FrontendCoaCodec.tree(CoaCodec.tree(raw((ObjectNode)fixture.get("coa")),false)));
        actual.set("grid",FrontendCoaCodec.tree(CoaCodec.tree(raw((ObjectNode)fixture.get("grid")),true)));
        for(var action:DesignerAction.values())actual.set(action==DesignerAction.OPEN?"open":action==DesignerAction.COMMIT?"commit":"custom",
                FrontendCoaCodec.object(FrontendCoaCodec.encode(FrontendCoaCodec.designer(verify(action,fixture),raw(ack(action))))));
        assertEquals(expected,actual);
        assertEquals(actual,FullJsonTree.parse(FullJsonTree.encode(actual,65536),65536));
        assertTrue(actual.get("commit").get("postcondition_verified").booleanValue());
        assertFalse(actual.get("tree").has("available"),"old alias is not the original public contract");
    }
    @Test void wrongFieldsTypesCountsGridCompletenessAndAmbiguousTargetsRefuseBeforeAnyPermission(){
        var f=fixtures();for(var method:List.of(FrontendCoaContract.Method.ACTIVATE,FrontendCoaContract.Method.CUSTOM,FrontendCoaContract.Method.COMMIT_DYNASTY,FrontendCoaContract.Method.GRID,FrontendCoaContract.Method.TREE)){
            assertInstanceOf(FrontendCoaContract.Empty.class,FrontendCoaCodec.decode(method,raw(FrontendCoaCodec.empty())));
            assertThrows(IllegalArgumentException.class,()->FrontendCoaCodec.decode(method,raw(FrontendCoaCodec.empty().put("expected_revision",0))));
        }
        var wrong=(ObjectNode)f.get("coa").deepCopy();wrong.put("widget_count",true);assertThrows(IllegalArgumentException.class,()->CoaCodec.tree(raw(wrong),false));
        var wide=(ObjectNode)f.get("coa").deepCopy();((ObjectNode)wide.get("widgets").get(0)).put("vtable_rva",WIDE.add(BigInteger.ONE));assertThrows(IllegalArgumentException.class,()->CoaCodec.tree(raw(wide),false));
        var missing=(ObjectNode)f.get("grid").deepCopy();missing.withArray("widgets").remove(2);missing.put("widget_count",2);assertThrows(IllegalArgumentException.class,()->CoaCodec.tree(raw(missing),true));
        var duplicate=(ObjectNode)f.get("coa").deepCopy();duplicate.withArray("widgets").add(widget("0/3/0/2/1/0/0/2/1/0","button_custom_mode",0));duplicate.put("widget_count",2);
        assertThrows(IllegalArgumentException.class,()->designerReady(DesignerAction.CUSTOM_MODE,route(FrontendRulesData.Route.COAT_OF_ARMS_DESIGNER,1).value(),CoaCodec.tree(raw(duplicate),false)));
    }
    @Test void ackOrOldOrForeignPostReadsNeverBecomeADesignerUiPostcondition(){
        var f=fixtures();var before=route(FrontendRulesData.Route.COAT_OF_ARMS_DESIGNER,1);
        var tree=inspected(CoaCodec.rulerDesignerTree(raw((ObjectNode)f.get("finish"))),2);var ack=CoaCodec.activationAck(raw(ack(DesignerAction.COMMIT)),DesignerAction.COMMIT.step());
        assertThrows(IllegalArgumentException.class,()->designer(DesignerAction.COMMIT,before,tree,ack,"mutation",NOW.plusMillis(3),route(FrontendRulesData.Route.COAT_OF_ARMS_DESIGNER,5),Optional.empty()));
        var sameId=new ReadEvidence<>(route(FrontendRulesData.Route.RULER_DESIGNER,5).value(),"mutation",NOW.plusMillis(5),DATA);
        assertThrows(IllegalArgumentException.class,()->designer(DesignerAction.COMMIT,before,tree,ack,"mutation",NOW.plusMillis(3),sameId,Optional.empty()));
        assertThrows(IllegalArgumentException.class,()->designer(DesignerAction.COMMIT,before,tree,ack,"mutation",NOW.plusMillis(3),route(FrontendRulesData.Route.RULER_DESIGNER,1),Optional.empty()));
        var wrong=raw(ack(DesignerAction.OPEN));assertThrows(IllegalArgumentException.class,()->FrontendCoaCodec.designer(verify(DesignerAction.COMMIT,f),wrong));
        assertThrows(IllegalArgumentException.class,()->designer(DesignerAction.CUSTOM_MODE,route(FrontendRulesData.Route.COAT_OF_ARMS_DESIGNER,1),
                inspected(CoaCodec.tree(raw((ObjectNode)f.get("coa")),false),2),CoaCodec.activationAck(raw(ack(DesignerAction.CUSTOM_MODE)),DesignerAction.CUSTOM_MODE.step()),
                "mutation",NOW.plusMillis(3),route(FrontendRulesData.Route.COAT_OF_ARMS_DESIGNER,5),Optional.empty()));
    }
}
