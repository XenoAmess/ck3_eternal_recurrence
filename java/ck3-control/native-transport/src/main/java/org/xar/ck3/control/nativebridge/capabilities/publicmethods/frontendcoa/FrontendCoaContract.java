package org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa;

import java.math.BigInteger;
import java.nio.file.Path;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaUploads;

/** One argument contract for the original eighteen frontend and ten source tools. */
public final class FrontendCoaContract {
    private FrontendCoaContract() { }
    public enum Method {
        ABORT("ck3_abort_coat_of_arms_source_upload_v2"), CUSTOM("ck3_activate_frontend_coat_of_arms_custom_mode_v1"),
        ACTIVATE("ck3_activate_frontend_coat_of_arms_designer_v1"), APPEND("ck3_append_coat_of_arms_source_chunk_v2"),
        BEGIN("ck3_begin_coat_of_arms_source_upload_v2"), CALIBRATE2("ck3_calibrate_frontend_coat_of_arms_framebuffer_v2"),
        CALIBRATE3("ck3_calibrate_frontend_coat_of_arms_framebuffer_v3"), CAPTURE("ck3_capture_frontend_coat_of_arms_framebuffer_v1"),
        COMMIT("ck3_commit_coat_of_arms_source_upload_v2"), COMMIT_DYNASTY("ck3_commit_frontend_dynasty_coat_of_arms_v1"),
        COMPARE1("ck3_compare_frontend_coat_of_arms_framebuffer_v1"), COMPARE2("ck3_compare_frontend_coat_of_arms_framebuffer_v2"),
        COMPARE3("ck3_compare_frontend_coat_of_arms_framebuffer_v3"), EXPORT("ck3_export_coat_of_arms_source_v1"),
        GRID("ck3_inspect_frontend_coat_of_arms_pattern_grid_v1"), TREE("ck3_inspect_frontend_coat_of_arms_tree_v1"),
        PREPARE("ck3_prepare_frontend_coat_of_arms_framebuffer_v1"), PROBE("ck3_probe_coat_of_arms_source_v1"),
        VFS("ck3_project_coat_of_arms_vfs_asset_winner_v1"), CONFIGURED_CATALOG("ck3_query_coat_of_arms_configured_resource_catalog_v1"),
        DEFINITION_CATALOG("ck3_query_coat_of_arms_definition_catalog_v1"), DLC("ck3_query_coat_of_arms_installed_dlc_sources_v1"),
        LOAD_CONFIGURATION("ck3_query_coat_of_arms_load_configuration_v1"), RESOURCE_CATALOG("ck3_query_coat_of_arms_resource_catalog_v1"),
        CONFIGURED_ASSET("ck3_read_coat_of_arms_configured_resource_asset_v1"), DEFINITION("ck3_read_coat_of_arms_definition_v1"),
        RENDER_SUPPORT("ck3_read_coat_of_arms_render_support_v1"), RESOURCE_ASSET("ck3_read_coat_of_arms_resource_asset_v1");
        private final String publicName;
        Method(String publicName) { this.publicName=publicName; }
        public String publicName() { return publicName; }
        public boolean diskOnly() { return ordinal()>=CONFIGURED_CATALOG.ordinal(); }
        public static Method named(String name) { return List.of(values()).stream().filter(v->v.publicName.equals(name)).findFirst().orElseThrow(()->new IllegalArgumentException("unknown CoA method")); }
    }
    public enum Kind {
        PATTERN("pattern","gfx/coat_of_arms/patterns","50_coa_designer_patterns.txt","pattern_assets"),
        COLORED_EMBLEM("colored_emblem","gfx/coat_of_arms/colored_emblems","50_coa_designer_emblems.txt","colored_emblem_assets"),
        COLOR("color","gfx/coat_of_arms/color_palettes","50_coa_designer_palettes.txt","color_palette_definitions");
        private final String wire,directory,manifest,candidateKey;
        Kind(String wire,String directory,String manifest,String candidateKey){this.wire=wire;this.directory=directory;this.manifest=manifest;this.candidateKey=candidateKey;}
        public String wire(){return wire;} public String directory(){return directory;} public String manifest(){return manifest;} public String candidateKey(){return candidateKey;}
        public boolean hasAsset(){return this!=COLOR;}
        public static Kind parse(String wire){return List.of(values()).stream().filter(v->v.wire.equals(wire)).findFirst().orElseThrow(()->new IllegalArgumentException("kind must be pattern, colored_emblem, or color"));}
    }
    public sealed interface Request permits Catalog,Asset,Directory,Definition,Vfs,Begin,Append,Commit,Abort,Probe,Revision,Empty,Calibration,Compare,Capture { Method method(); }
    public record Catalog(Method method,Path directory,Kind kind,String query,boolean visibleOnly,int offset,int limit) implements Request {
        public Catalog { need(List.of(Method.RESOURCE_CATALOG,Method.CONFIGURED_CATALOG,Method.DEFINITION_CATALOG).contains(method),"invalid catalog method");Objects.requireNonNull(directory);need(method==Method.DEFINITION_CATALOG?kind==null:kind!=null,"resource kind required only for resource catalogs");need(query==null||query.codePointCount(0,query.length())<=128,"query exceeds 128 characters");need(offset>=0&&limit>=1&&limit<=200,"page outside original bounds"); }
    }
    public record Asset(Method method,Path directory,Kind kind,String name) implements Request {
        public Asset { need(method==Method.RESOURCE_ASSET||method==Method.CONFIGURED_ASSET,"invalid asset method");Objects.requireNonNull(directory);Objects.requireNonNull(kind);need(kind.hasAsset(),"asset kind must be pattern or colored_emblem");text(name,128);if(method==Method.CONFIGURED_ASSET)need(name.matches("[0-9A-F]{64}"),"candidate_id requires uppercase SHA256"); }
    }
    public record Directory(Method method,Path directory) implements Request { public Directory{need(List.of(Method.LOAD_CONFIGURATION,Method.DLC,Method.RENDER_SUPPORT).contains(method),"invalid directory method");Objects.requireNonNull(directory);} }
    public record Definition(Method method,Path directory,String key) implements Request {public Definition{need(method==Method.DEFINITION,"invalid definition method");Objects.requireNonNull(directory);need(key!=null&&key.matches("[A-Za-z0-9_.:-]{1,128}"),"invalid definition key");}}
    public record Vfs(Method method,Path directory,String logicalPath) implements Request {
        public Vfs {need(method==Method.VFS,"invalid VFS method");Objects.requireNonNull(directory);text(logicalPath,512);need(!logicalPath.contains("\\")&&!logicalPath.startsWith("/")&&!logicalPath.endsWith("/"),"relative POSIX logical_path required");for(String s:logicalPath.split("/",-1))need(!s.isEmpty()&&!s.equals(".")&&!s.equals(".."),"unsafe logical_path");String f=logicalPath.toLowerCase(java.util.Locale.ROOT);need(f.endsWith(".dds")&&(f.startsWith("gfx/coat_of_arms/patterns/")||f.startsWith("gfx/coat_of_arms/colored_emblems/")||f.startsWith("gfx/coat_of_arms/textured_emblems/")),"direct CoA DDS logical_path required");}
    }
    public record Begin(Method method,CoaUploads.Begin value) implements Request {public Begin{need(method==Method.BEGIN,"invalid begin method");Objects.requireNonNull(value);}}
    public record Append(Method method,CoaUploads.Append value) implements Request {public Append{need(method==Method.APPEND,"invalid append method");Objects.requireNonNull(value);}}
    public record Commit(Method method,CoaUploads.Commit value) implements Request {public Commit{need(method==Method.COMMIT,"invalid commit method");Objects.requireNonNull(value);}}
    public record Abort(Method method,CoaUploads.SessionKey key) implements Request {public Abort{need(method==Method.ABORT,"invalid abort method");Objects.requireNonNull(key);}}
    public record Probe(Method method,String source,BigInteger expectedRevision,boolean apply) implements Request {public Probe{need(method==Method.PROBE,"invalid probe method");Objects.requireNonNull(source);org.xar.ck3.control.contracts.PublicUnsigned64.canonical(expectedRevision,org.xar.ck3.control.contracts.PublicUnsigned64.Minimum.ZERO);}}
    public record Revision(Method method,BigInteger expectedRevision) implements Request {public Revision{need(method==Method.EXPORT,"invalid export method");org.xar.ck3.control.contracts.PublicUnsigned64.canonical(expectedRevision,org.xar.ck3.control.contracts.PublicUnsigned64.Minimum.ZERO);}}
    public record Empty(Method method) implements Request {public Empty{need(List.of(Method.CUSTOM,Method.ACTIVATE,Method.COMMIT_DYNASTY,Method.GRID,Method.TREE,Method.PREPARE).contains(method),"invalid empty method");}}
    public record Calibration(Method method,String calibrationId,String phase) implements Request {public Calibration{need(method==Method.CALIBRATE2||method==Method.CALIBRATE3,"invalid calibration method");org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaFramebuffer.identifier(calibrationId);Objects.requireNonNull(phase);need(method==Method.CALIBRATE2?List.of("begin","complete").contains(phase):List.of("begin","surface_complete","anchor_base","anchors_complete").contains(phase),"invalid calibration phase");}}
    public record Compare(Method method,String calibrationId,String referencePngBase64,String referencePngSha256) implements Request {public Compare{need(List.of(Method.COMPARE1,Method.COMPARE2,Method.COMPARE3).contains(method),"invalid comparison method");Objects.requireNonNull(referencePngBase64);need(referencePngBase64.length()<=4*1024*1024,"reference PNG exceeds bounded contract");need(referencePngSha256!=null&&referencePngSha256.matches("[0-9A-Fa-f]{64}"),"reference SHA256 required");if(method!=Method.COMPARE1)org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaFramebuffer.identifier(calibrationId);else need(calibrationId==null,"v1 comparison has no calibration ID");}}
    public record Capture(Method method,String calibrationId,int side) implements Request {public Capture{need(method==Method.CAPTURE,"invalid capture method");org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaFramebuffer.identifier(calibrationId);need(side>=32&&side<=512,"capture side outside original range");}}
    /** Public JSON is an explicit wire boundary; internal requests never carry arbitrary maps. */
    public record Response(RawJson original) {public Response{Objects.requireNonNull(original);}}
    public static void need(boolean condition,String message){if(!condition)throw new IllegalArgumentException(message);}
    public static String text(String value,int maximum){need(value!=null&&!value.isEmpty()&&value.codePointCount(0,value.length())<=maximum,"bounded nonempty text required");return value;}
}
