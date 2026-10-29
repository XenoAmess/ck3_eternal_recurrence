package org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaUploads;
import org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaData;
import org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaCodec;
import org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaPostconditions;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaContract.*;

/** Explicit public field conversion; decimal uint64 values never traverse double. */
public final class FrontendCoaCodec {
    private FrontendCoaCodec() { }
    public static Request decode(Method method,RawJson original) {
        JsonNode tree=FullJsonTree.parse(original.bytes(),RawJson.MAXIMUM_BYTES);
        need(tree.isObject(),"CoA arguments must be an object");ObjectNode n=(ObjectNode)tree;
        return switch(method) {
            case RESOURCE_CATALOG,CONFIGURED_CATALOG -> {
                fields(n,"kind","query?","visible_only?","offset?","limit?",method==Method.CONFIGURED_CATALOG?"user_directory":"game_directory");
                yield new Catalog(method,path(n,method==Method.CONFIGURED_CATALOG?"user_directory":"game_directory"),Kind.parse(string(n,"kind")),nullable(n,"query"),bool(n,"visible_only",true),integer(n,"offset",0,0,Integer.MAX_VALUE),integer(n,"limit",50,1,200));
            }
            case DEFINITION_CATALOG -> {fields(n,"game_directory","query?","offset?","limit?");yield new Catalog(method,path(n,"game_directory"),null,nullable(n,"query"),true,integer(n,"offset",0,0,Integer.MAX_VALUE),integer(n,"limit",50,1,200));}
            case RESOURCE_ASSET,CONFIGURED_ASSET -> {boolean configured=method==Method.CONFIGURED_ASSET;String d=configured?"user_directory":"game_directory",key=configured?"candidate_id":"name";fields(n,d,"kind",key);yield new Asset(method,path(n,d),Kind.parse(string(n,"kind")),string(n,key));}
            case DEFINITION -> {fields(n,"game_directory","key");yield new Definition(method,path(n,"game_directory"),string(n,"key"));}
            case LOAD_CONFIGURATION,DLC,RENDER_SUPPORT -> {String d=method==Method.LOAD_CONFIGURATION?"user_directory":"game_directory";fields(n,d);yield new Directory(method,path(n,d));}
            case VFS -> {fields(n,"game_directory","logical_path");yield new Vfs(method,path(n,"game_directory"),string(n,"logical_path"));}
            case BEGIN -> {fields(n,"total_bytes","source_sha256","chunk_count","chunk_encoding","expected_revision","apply","expected_game_version","expected_executable_sha256");yield new Begin(method,new CoaUploads.Begin(integer(n,"total_bytes",null,1,512*1024),string(n,"source_sha256"),integer(n,"chunk_count",null,1,32),string(n,"chunk_encoding"),intent(n)));}
            case APPEND -> {fields(n,"upload_id","generation","chunk_index","chunk_count","chunk_encoding","chunk_bytes","chunk_sha256","chunk_base64","source_sha256","expected_revision","apply","expected_game_version","expected_executable_sha256");yield new Append(method,new CoaUploads.Append(commit(n),integer(n,"chunk_index",null,0,31),string(n,"chunk_encoding"),integer(n,"chunk_bytes",null,1,48*1024),string(n,"chunk_sha256"),string(n,"chunk_base64")));}
            case COMMIT -> {fields(n,"upload_id","generation","chunk_count","source_sha256","expected_revision","apply","expected_game_version","expected_executable_sha256");yield new Commit(method,commit(n));}
            case ABORT -> {fields(n,"upload_id","generation");yield new Abort(method,key(n));}
            case PROBE -> {fields(n,"source","expected_revision","apply");yield new Probe(method,string(n,"source"),u64(n,"expected_revision",false),bool(n,"apply",null));}
            case EXPORT -> {fields(n,"expected_revision");yield new Revision(method,u64(n,"expected_revision",false));}
            case CALIBRATE2,CALIBRATE3 -> {fields(n,"calibration_id","phase");yield new Calibration(method,string(n,"calibration_id"),string(n,"phase"));}
            case COMPARE1,COMPARE2,COMPARE3 -> {if(method==Method.COMPARE1)fields(n,"reference_png_base64","reference_png_sha256");else fields(n,"calibration_id","reference_png_base64","reference_png_sha256");yield new Compare(method,method==Method.COMPARE1?null:string(n,"calibration_id"),string(n,"reference_png_base64"),string(n,"reference_png_sha256"));}
            case CAPTURE -> {fields(n,"calibration_id","side?");yield new Capture(method,string(n,"calibration_id"),integer(n,"side",230,32,512));}
            case CUSTOM,ACTIVATE,COMMIT_DYNASTY,GRID,TREE,PREPARE -> {fields(n);yield new Empty(method);}
        };
    }
    private static CoaUploads.Intent intent(ObjectNode n){return new CoaUploads.Intent(u64(n,"expected_revision",false),bool(n,"apply",null),string(n,"expected_game_version"),string(n,"expected_executable_sha256"));}
    private static CoaUploads.SessionKey key(ObjectNode n){return new CoaUploads.SessionKey(string(n,"upload_id"),u64(n,"generation",true));}
    private static CoaUploads.Commit commit(ObjectNode n){return new CoaUploads.Commit(key(n),integer(n,"chunk_count",null,1,32),string(n,"source_sha256"),intent(n));}
    public static Response response(ObjectNode n){return new Response(raw(n));}
    public static RawJson raw(JsonNode n){return new RawJson(FullJsonTree.encode(n,RawJson.MAXIMUM_BYTES));}
    public static ObjectNode object(RawJson raw){JsonNode n=FullJsonTree.parse(raw.bytes(),RawJson.MAXIMUM_BYTES);need(n.isObject(),"CoA response must be object");return (ObjectNode)n;}
    public static RawJson encode(Response response){object(response.original());return response.original();}
    public static ObjectNode binding(CoaData.Binding b){ObjectNode n=empty().put("revision",PublicUnsigned64.canonical(b.revision(),PublicUnsigned64.Minimum.ZERO)).put("connection_generation",PublicUnsigned64.canonical(b.connectionGeneration(),PublicUnsigned64.Minimum.ONE)).put("bridge_pid",b.bridgePid());if(b instanceof CoaData.FrontendBinding)return n.put("mode","frontend");CoaData.SnapshotBinding s=(CoaData.SnapshotBinding)b;n.put("mode",s.mode()==CoaData.SnapshotMode.GAMEPLAY?"gameplay":"frontend_snapshot").put("snapshot_id",s.snapshotId()).put("native_revision",PublicUnsigned64.canonical(s.nativeRevision(),PublicUnsigned64.Minimum.ONE)).put("date_raw",Long.toString(s.dateRaw()));s.episodeRunId().ifPresent(v->n.put("episode_run_id",v));return n;}
    public static ObjectNode upload(CoaUploads.Receipt r){ObjectNode n=empty().put("schema",r.schema()).put("schema_version",r.schemaVersion()).put("status",r.status().name().toLowerCase(java.util.Locale.ROOT)).put("upload_id",r.key().uploadId()).put("generation",PublicUnsigned64.canonical(r.key().generation(),PublicUnsigned64.Minimum.ONE)).put("total_bytes",r.totalBytes()).put("source_sha256",r.sourceSha256()).put("chunk_count",r.chunkCount()).put("received_chunks",r.receivedChunks()).put("received_bytes",r.receivedBytes()).put("chunk_encoding",r.chunkEncoding()).put("max_chunk_bytes",r.maxChunkBytes()).put("timeout_seconds",r.timeoutSeconds()).put("expected_revision",PublicUnsigned64.canonical(r.intent().expectedRevision(),PublicUnsigned64.Minimum.ZERO)).put("apply",r.intent().apply()).put("expected_game_version",r.intent().expectedGameVersion()).put("expected_executable_sha256",r.intent().expectedExecutableSha256());n.set("binding",binding(r.binding()));return n;}
    public static ObjectNode probe(CoaData.ProbeResult r){ObjectNode n=empty().put("schema","coat-of-arms-source-probe-v1").put("schema_version",1).put("step",CoaData.PROBE_STEP).put("status",r.status().name().toLowerCase(java.util.Locale.ROOT)).put("detected",r.detected()).put("designer_observed",r.designerObserved()).put("clipboard_written",r.clipboardWritten()).put("clipboard_readback_matched",r.clipboardReadbackMatched()).put("apply_requested",r.applyRequested()).put("paste_invoked",r.pasteInvoked()).put("applied",r.applied()).put("candidate_index",r.candidateIndex()).put("preview_coat_of_arms_handle",r.previewCoatOfArmsHandle()).put("active_coat_of_arms_index",r.activeCoatOfArmsIndex()).put("source_sha256",r.source().sourceSha256()).put("source_bytes",r.source().sourceBytes());if(r.reason().isPresent())n.put("reason",r.reason().orElseThrow());else n.putNull("reason");n.set("binding",binding(r.binding()));return n;}
    public static ObjectNode exported(CoaData.ExportResult r){ObjectNode n=empty().put("schema","coat-of-arms-source-export-v1").put("schema_version",1).put("step",CoaData.EXPORT_STEP).put("status",r.status().name().toLowerCase(java.util.Locale.ROOT)).put("designer_observed",r.designerObserved()).put("copy_invoked",r.copyInvoked()).put("clipboard_read",r.clipboardRead()).put("source_bytes",r.sourceBytes());if(r.source().isPresent())n.put("source",r.source().orElseThrow());else n.putNull("source");if(r.sourceSha256().isPresent())n.put("source_sha256",r.sourceSha256().orElseThrow());else n.putNull("source_sha256");if(r.reason().isPresent())n.put("reason",r.reason().orElseThrow());else n.putNull("reason");n.set("binding",binding(r.binding()));return n;}
    /** Original normalized native census fields; public uint64 RVAs are canonical decimal strings. */
    public static ObjectNode tree(CoaData.Tree r){
        ObjectNode n=empty().put("schema","ck3-frontend-gui-tree-inspection-v1").put("schema_version",1)
                .put("step",r.step()).put("accepted",true).put("status",r.available()?"available":"unavailable")
                .put("scope_root_name",r.scopeRootName()).put("root_available",r.available()).put("truncated",r.truncated())
                .put("widget_count",r.widgets().size()).put("backend_id","native-headless")
                .put("read_only",true).put("uses_ocr",false).put("uses_keyboard",false).put("uses_mouse",false);
        var rows=n.putArray("widgets");
        for(CoaData.Widget w:r.widgets())rows.add(empty().put("runtime_name",w.runtimeName()).put("child_path",w.childPath())
                .put("depth",w.depth()).put("child_count",w.childCount())
                .put("vtable_rva",PublicUnsigned64.canonical(w.vtableRva(),PublicUnsigned64.Minimum.ZERO))
                .put("effective_visible",w.effectiveVisible()).put("enabled",w.enabled()));
        if(r.directChildCount().isPresent())n.put("direct_child_count",r.directChildCount().orElseThrow()).put("direct_children_complete",true);
        return n;
    }
    public static ObjectNode route(FrontendRulesData.ObservedRoute r){
        return empty().put("schema","ck3-frontend-gui-route-v1").put("schema_version",1)
                .put("step","query-frontend-gui-route-v1").put("accepted",true).put("route",r.route().wire()).put("backend_id","native-headless");
    }
    /** The original ACK stays complete; independent typed observations supply the verified UI result. */
    public static Response designer(CoaPostconditions.DesignerVerified result,RawJson originalAck){
        CoaCodec.ActivationAck decoded=CoaCodec.activationAck(originalAck,result.action().step());
        need(decoded.equals(result.acknowledgement()),"designer public ACK differs from verified original");
        ObjectNode ack=object(originalAck).deepCopy();ack.put("backend_id",decoded.backendId());
        canonicalNativeHeader(ack,"query_sequence",PublicUnsigned64.Minimum.ONE);
        canonicalNativeHeader(ack,"snapshot_revision",PublicUnsigned64.Minimum.ZERO);
        ObjectNode n=schema("ck3-frontend-gui-action-v1","verified").put("step",result.action().step())
                .put("accepted",true).put("action",result.action().action()).put("input_backend","native_gui_semantic_activation")
                .put("uses_ocr",false).put("uses_keyboard",false).put("uses_mouse",false)
                .put("postcondition_verified",true).put("backend_id",decoded.backendId());
        n.set("before",route(result.before().value()));n.set("before_inspection",tree(result.beforeInspection().value()));
        n.set("acknowledgement",ack);n.set("after",route(result.after().value()));
        if(result.action()==CoaPostconditions.DesignerAction.CUSTOM_MODE)
            n.set("after_inspection",tree(result.afterInspection().orElseThrow().value()));
        return response(n);
    }
    private static void canonicalNativeHeader(ObjectNode n,String field,PublicUnsigned64.Minimum minimum){
        JsonNode v=n.get(field);if(v==null)return;
        need(v.isIntegralNumber(),"native "+field+" must retain its exact integer type");
        n.put(field,PublicUnsigned64.canonical(v.bigIntegerValue(),minimum));
    }
    public static ObjectNode empty(){return JsonNodeFactory.instance.objectNode();}
    public static ObjectNode schema(String schema,String status){return empty().put("schema",schema).put("schema_version",1).put("status",status);}
    public static BigInteger u64(ObjectNode n,String field,boolean positive){return PublicUnsigned64.parse(n.get(field),positive?PublicUnsigned64.Minimum.ONE:PublicUnsigned64.Minimum.ZERO,PublicUnsigned64.NumericInput.SAFE_INTEGER_OR_DECIMAL);}
    public static String string(ObjectNode n,String field){JsonNode v=n.get(field);need(v!=null&&v.isTextual(),field+" must be a string");return v.textValue();}
    private static String nullable(ObjectNode n,String field){JsonNode v=n.get(field);return v==null||v.isNull()?null:string(n,field);}
    private static Path path(ObjectNode n,String field){return Path.of(text(string(n,field),32767)).toAbsolutePath().normalize();}
    public static int integer(ObjectNode n,String field,Integer fallback,int minimum,int maximum){JsonNode v=n.get(field);if(v==null){need(fallback!=null,"missing "+field);return fallback;}need(v.isIntegralNumber()&&v.canConvertToInt()&&v.intValue()>=minimum&&v.intValue()<=maximum,field+" must be an integer in range");return v.intValue();}
    public static boolean bool(ObjectNode n,String field,Boolean fallback){JsonNode v=n.get(field);if(v==null){need(fallback!=null,"missing "+field);return fallback;}need(v.isBoolean(),field+" must be boolean");return v.booleanValue();}
    private static void fields(ObjectNode n,String...spec){Set<String> allowed=new HashSet<>();for(String field:spec){boolean optional=field.endsWith("?");String key=optional?field.substring(0,field.length()-1):field;allowed.add(key);need(optional||n.has(key),"missing "+key);}n.fieldNames().forEachRemaining(key->need(allowed.contains(key),"unexpected CoA field "+key));}
}
