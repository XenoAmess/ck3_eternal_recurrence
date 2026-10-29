package org.xar.ck3.control.application.planning.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;

/** Complete original Release provenance verifier. Results are DATA, never a live read permission. */
public final class H2743StockPredicateAdmission {
    private H2743StockPredicateAdmission() { }
    public static final String EVIDENCE_SCHEMA="xar.ck3.h2743-stock-predicate-evidence.v1";
    public static final String PAIR_SCHEMA="xar.ck3.h2743.stock-predicate-source-pair.v1";
    public static final String PINS_SCHEMA="xar.ck3.h2743.stock-predicate-pins.v1";
    public static final String REUSE="reuse-actual-compile-run-receipts-no-rerun";
    public enum Profile { EXPLICIT_STOCK_RELEASE, HISTORICAL_BASELINE }
    public record Input(Path pairPath,Path pinsPath,Path nativeSourceCheckout) {
        public Input { absolute(pairPath);absolute(pinsPath);absolute(nativeSourceCheckout); }
    }
    public record FileFact(Path path,long bytes,String sha256) {
        public FileFact { absolute(path);need(bytes>=0,"negative file size");hash(sha256); }
    }
    /** Implementations supply actual originals. The application owns no filesystem or native IO. */
    public interface Files {
        FileFact measure(Path absolutePath)throws IOException;
        byte[] read(Path absolutePath,int maximumBytes)throws IOException;
    }
    public record Pins(String pairSha256,String sourceHead,String sourceManifestSha256,
            String routeReceiptSha256,String dllSha256,String injectorSha256) {
        public Pins { hash(pairSha256);head(sourceHead);hash(sourceManifestSha256);hash(routeReceiptSha256);hash(dllSha256);hash(injectorSha256); }
    }
    public record VerifiedData(Profile profile,RawJson sourceReceipt,List<FileFact> completeFiles) {
        public VerifiedData { Objects.requireNonNull(profile);Objects.requireNonNull(sourceReceipt);completeFiles=List.copyOf(completeFiles);need(!completeFiles.isEmpty(),"complete provenance originals required"); }
    }
    private static final String OLD_PAIR="183BF62461AE3C2B382F9367C657C923D5D412883ADE45FA7F24B7E31BC0E42C";
    private static final String OLD_HEAD="24c51a37d2facd2dcf24da2d54e5f0c4548833cb";
    private static final String OLD_MANIFEST="3CC643CD3F73B63AC576361C5E99B34592F83B4DB0AE9875D4061325AB6611B3";
    public static VerifiedData verifyStock(Input input,Files files)throws IOException {
        return new Check(input,files).stock();
    }
    /** Explicit historical knowledge only; this result cannot enter the stock issuer. */
    public static VerifiedData verifyHistoricalBaseline(Path pair,Path checkout,Files files)throws IOException {
        absolute(pair);absolute(checkout);return new Check(new Input(pair,pair,checkout),files).baseline();
    }
    public static Pins decodePins(byte[] raw) {
        ObjectNode p=json(raw);keys(p,"schema","pair_sha256","source_head","source_manifest_sha256","route_receipt_sha256","dll_sha256","injector_sha256");eq(p,"schema",PINS_SCHEMA);
        return new Pins(text(p,"pair_sha256"),text(p,"source_head"),text(p,"source_manifest_sha256"),text(p,"route_receipt_sha256"),text(p,"dll_sha256"),text(p,"injector_sha256"));
    }
    private static final class Check {
        final Input input;final Files files;final Map<Path,FileFact> observed=new LinkedHashMap<>();
        Check(Input input,Files files){this.input=Objects.requireNonNull(input);this.files=Objects.requireNonNull(files);}
        FileFact measure(Path p)throws IOException { absolute(p);FileFact f=Objects.requireNonNull(files.measure(p));need(p.normalize().equals(f.path().normalize()),"file port changed original path");FileFact prior=observed.putIfAbsent(p.normalize(),f);need(prior==null||prior.equals(f),"original changed during verification");return f; }
        void matches(Path p,String sha)throws IOException { hash(sha);need(measure(p).sha256().equals(sha),"original hash changed: "+p); }
        byte[] bytes(Path p)throws IOException {FileFact before=measure(p);need(before.bytes()<=16777216,"provenance JSON/text exceeds finite16MiB");byte[] raw=files.read(p,16777216);need(raw.length==before.bytes()&&digest(raw).equals(before.sha256()),"read differs from measured original");need(measure(p).equals(before),"original changed after read");return raw;}
        ObjectNode obj(Path p)throws IOException{return json(bytes(p));}
        Path asset(JsonNode row,boolean exact)throws IOException {
            ObjectNode a=object(row);if(exact)keys(a,"path","size_bytes","sha256");Path p=path(a,"path");FileFact f=measure(p);need(f.sha256().equals(text(a,"sha256")),"asset hash changed: "+p);
            if(exact||a.has("size_bytes"))need(f.bytes()==integer(a,"size_bytes"),"asset size changed");return p;
        }
        VerifiedData stock()throws IOException {
            Pins p=decodePins(bytes(input.pinsPath()));matches(input.pairPath(),p.pairSha256());ObjectNode pair=obj(input.pairPath());
            eq(pair,"schema",PAIR_SCHEMA);eq(pair,"head",p.sourceHead());eq(pair,"candidate_identity_proposed","h2743-stock-predicate-application-main-v1");eq(pair,"stock_predicate_protocol",EVIDENCE_SCHEMA);eq(pair,"shared_native_source_manifest_sha256",p.sourceManifestSha256());
            quartet(pair);ObjectNode routeAsset=object(get(pair,"route_receipt"));eq(routeAsset,"sha256",p.routeReceiptSha256());Path routePath=asset(routeAsset,false);ObjectNode route=obj(routePath);eq(route,"source_head",p.sourceHead());bool(route,"full_route_closed",true);bool(route,"game_launched",false);bool(route,"material_complete",false);nil(route,"action_literal");
            Set<String> stages=Set.of("parser","firstguard","handler","submit","permitted_callback","installed_callback","application_main_executor");need(stringSet(get(route,"closed_stages")).equals(stages),"full route closure incomplete");
            ObjectNode counts=JsonNodeFactory.instance.objectNode();ObjectNode manifest=null;
            for(String kind:List.of("dll","injector")) {ObjectNode binary=object(get(pair,kind));eq(binary,"sha256",kind.equals("dll")?p.dllSha256():p.injectorSha256());manifest=build(pair,kind,p.sourceHead(),p.sourceManifestSha256(),true,counts);}
            Path dllBuild=path(object(get(pair,"dll")),"build_result").getParent();
            if(pair.has("focused_fixture_policy")&&REUSE.equals(text(pair,"focused_fixture_policy")))reused(pair,route,Objects.requireNonNull(manifest));
            else ctest(dllBuild,false);
            return receipt(Profile.EXPLICIT_STOCK_RELEASE,pair,p.pairSha256(),p.sourceHead(),p.sourceManifestSha256(),counts,measure(input.pinsPath()).sha256());
        }
        VerifiedData baseline()throws IOException {
            matches(input.pairPath(),OLD_PAIR);ObjectNode pair=obj(input.pairPath());eq(pair,"head",OLD_HEAD);eq(pair,"candidate_identity_proposed","war-storage-candidate-v5-head24c51");eq(pair,"shared_native_source_manifest_sha256",OLD_MANIFEST);quartet(pair);
            ObjectNode counts=JsonNodeFactory.instance.objectNode();for(String k:List.of("dll","injector"))build(pair,k,OLD_HEAD,OLD_MANIFEST,false,counts);ctest(path(object(get(pair,"dll")),"build_result").getParent(),true);
            return receipt(Profile.HISTORICAL_BASELINE,pair,OLD_PAIR,OLD_HEAD,OLD_MANIFEST,counts,null);
        }
        void quartet(ObjectNode pair)throws IOException {ObjectNode q=object(get(pair,"source_quartet"));keys(q,"xar_checkpoint.ck3","driver-state.json","first-heir-marriage-formal-v1.json","xar_ck3_bridge.dll");for(JsonNode a:q)asset(a,false);}
        ObjectNode build(ObjectNode pair,String kind,String head,String manifestSha,boolean stock,ObjectNode counts)throws IOException {
            ObjectNode binary=object(get(pair,kind));asset(binary,false);Path resultPath=path(binary,"build_result"),postPath=path(binary,"postcheck");matches(resultPath,text(binary,"build_result_sha256"));matches(postPath,text(binary,"postcheck_sha256"));ObjectNode result=obj(resultPath),post=obj(postPath);
            eq(result,"head",head);bool(result,"source_inputs_unchanged",true);bool(result,"game_launched",false);bool(result,"go_executed",false);eq(post,"head",head);bool(post,"clean",true);bool(post,"source_file_lists_equal",true);eq(post,"source_before_sha256",manifestSha);eq(post,"source_after_sha256",manifestSha);
            Path dir=resultPath.getParent();for(String name:List.of("source-native-tracked-before.json","source-native-tracked-after.json"))matches(dir.resolve(name),manifestSha);
            ObjectNode manifest=obj(dir.resolve("source-native-tracked-before.json"));JsonNode rows=array(get(manifest,"files"));need(!rows.isEmpty(),"tracked sources empty");
            if(stock){eq(manifest,"schema","xar.ck3.h2743.native-source-tracked.v1");eq(manifest,"source_head",head);}
            Set<String> seen=new java.util.HashSet<>();
            for(JsonNode raw:rows){ObjectNode row=object(raw);if(stock){keys(row,"relative_path","path","size_bytes","sha256");absolute(path(row,"path"));String rel=text(row,"relative_path");need(seen.add(rel),"duplicate tracked source");Path actual=resolve(rel);matches(actual,text(row,"sha256"));need(measure(actual).bytes()==integer(row,"size_bytes"),"tracked source size changed");}
                else {String rel=text(row,"path");if(rel.contains("/src/")||rel.contains("/include/")||rel.endsWith("/CMakeLists.txt"))matches(Path.of(rel).isAbsolute()?Path.of(rel):resolve(rel),text(row,"sha256"));}}
            Path depsPath=dir.resolve("actual-dependencies.json");matches(depsPath,text(post,"deps_sha256"));ObjectNode deps=obj(depsPath);need(array(get(deps,"external_dependency_paths")).isEmpty(),"unexplained external build sources");JsonNode headers=array(get(deps,"project_source_headers"));for(JsonNode row:headers)matches(resolve(text(row,"path")),text(row,"sha256"));counts.put(kind,headers.size());
            String cache=new String(bytes(dir.resolve("build/CMakeCache.txt")),StandardCharsets.UTF_8);need(cache.contains("CMAKE_BUILD_TYPE:STRING=Release")&&(!stock||cache.contains("XAR_CK3_ENABLE_H2743_STOCK_PREDICATE_READER_V1:BOOL=ON")),"Release/stock opt-in differs");need(integer(obj(dir.resolve("build-result.json")),"exit_code")==0,"build failed");return manifest;
        }
        Path resolve(String relative){need(relative!=null&&!relative.isBlank()&&!relative.matches("^[A-Za-z]:.*")&&!relative.startsWith("/")&&!relative.startsWith("\\"),"source path is not relative");Path p=Path.of(relative.replace('\\','/'));for(Path part:p)need(!part.toString().equals(".."),"source path escapes checkout");Path result=input.nativeSourceCheckout().resolve(p).normalize();need(result.startsWith(input.nativeSourceCheckout().normalize()),"source escaped checkout");return result;}
        void ctest(Path dir,boolean old)throws IOException {need(integer(obj(dir.resolve("ctest-result.json")),"exit_code")==0,"focused CTest failed");String text=new String(bytes(dir.resolve("ctest-stdout.txt")),StandardCharsets.UTF_8);need(text.contains(old?"100% tests passed, 0 tests failed out of 1":"100% tests passed, 0 tests failed"),"focused CTest summary differs");}
        void reused(ObjectNode pair,ObjectNode route,ObjectNode manifest)throws IOException {
            ObjectNode refs=object(get(pair,"focused_fixture_receipts"));keys(refs,"core","route");eq(pair,"focused_fixture_policy",REUSE);need(get(refs,"core").equals(get(route,"core_actual_fixture"))&&get(refs,"route").equals(get(route,"route_actual_fixture")),"focused receipts differ from pinned route");
            Map<String,ObjectNode> nativeRows=new LinkedHashMap<>();for(JsonNode row:array(get(manifest,"files"))){String rel=text(row,"relative_path");need(nativeRows.putIfAbsent(rel,object(row))==null,"duplicate manifest row");}
            ObjectNode core=obj(asset(get(refs,"core"),true));eq(core,"schema","xar.h2743.stock-predicate-core-actual-fixture.v1");eq(core,"configuration","Release");bool(core,"ck3_launched",false);exactCounts(get(core,"fixture"),List.of("main_case_blocks","observed_checks","observed_failures","exit_code"),List.of(19L,53L,0L,0L));
            JsonNode sources=array(get(core,"compiled_sources"));need(sources.size()==2,"core source count differs");List<JsonNode> compiled=new ArrayList<>();sources.forEach(compiled::add);compiled.add(get(core,"header"));Set<String> observedInputs=new java.util.HashSet<>();
            for(JsonNode row:compiled){String[] pieces=text(row,"path").replace('\\','/').split("ck3_autonomous_player/native_bridge/",-1);need(pieces.length==2,"core compiled path differs");need(observedInputs.add(pieces[1]),"duplicate core input");inputMatches(row,"ck3_autonomous_player/native_bridge/"+pieces[1],nativeRows);}
            need(observedInputs.equals(Set.of("src/h2743_stock_predicate_reader_v1.cpp","src/h2743_stock_predicate_reader_v1_test.cpp","include/xar_bridge/h2743_stock_predicate_reader_v1.hpp")),"core input closure incomplete");
            ObjectNode before=obj(asset(get(core,"source_before"),true)),after=obj(asset(get(core,"source_after"),true));bool(after,"snapshot_bytes_unchanged",true);need(get(before,"files").equals(get(after,"files")),"core source changed");asset(get(core,"exe"),true);ObjectNode evidence=object(get(core,"evidence"));keys(evidence,"compile","fixture");for(JsonNode row:evidence)evidence(row);
            ObjectNode query=obj(asset(get(refs,"route"),true));eq(query,"schema","xar.h2743.stock-private-query-actual-route-fixture.v1");eq(query,"configuration","Release");bool(query,"ck3_launched",false);bool(query,"native_binding_enabled_offline",false);
            ObjectNode fixtures=object(get(query,"actual_fixtures"));exactCounts(get(fixtures,"on"),List.of("cases","checks","macro","failures","exit_code"),List.of(16L,271L,1L,0L,0L));exactCounts(get(fixtures,"off"),List.of("cases","checks","macro","failures","exit_code"),List.of(1L,3L,0L,0L,0L));
            before=obj(asset(get(query,"source_before"),true));after=obj(asset(get(query,"source_after"),true));bool(after,"snapshot_bytes_unchanged",true);need(integer(after,"file_count")==integer(before,"file_count")&&get(after,"source_before").equals(get(query,"source_before")),"route source snapshot changed");JsonNode beforeRows=array(get(before,"files"));need(!beforeRows.isEmpty(),"route source snapshot empty");for(JsonNode row:beforeRows)inputMatches(row,"ck3_autonomous_player/native_bridge/"+text(row,"relative_path"),nativeRows);
            evidence=object(get(query,"evidence"));keys(evidence,"compile-fixture-on","run-fixture-on","compile-fixture-off","run-fixture-off","compile-bridge-on","compile-bridge-off");for(JsonNode row:evidence)evidence(row);
            ObjectNode outputs=object(get(query,"outputs"));keys(outputs,"fixture-on","fixture-off","bridge-on-object","bridge-off-object");for(JsonNode row:outputs)asset(row,true);asset(get(query,"actual_query_evidence"),true);
        }
        void inputMatches(JsonNode row,String relative,Map<String,ObjectNode> nativeRows)throws IOException {ObjectNode original=nativeRows.get(relative);need(original!=null&&get(row,"sha256").equals(get(original,"sha256"))&&integer(row,"size_bytes")==integer(original,"size_bytes"),"compiled fixture source differs: "+relative);ObjectNode a=JsonNodeFactory.instance.objectNode();for(String k:List.of("path","size_bytes","sha256"))a.set(k,get(row,k));asset(a,true);}
        void evidence(JsonNode row)throws IOException {ObjectNode e=object(row);keys(e,"argv","result","stdout","stderr");for(JsonNode a:e)asset(a,true);need(integer(obj(path(object(get(e,"result")),"path")),"exit_code")==0,"reused compile/run failed");}
        VerifiedData receipt(Profile profile,ObjectNode pair,String pairSha,String head,String manifestSha,ObjectNode counts,String pinsSha)throws IOException {
            ObjectNode r=JsonNodeFactory.instance.objectNode();r.put("schema",profile==Profile.EXPLICIT_STOCK_RELEASE?"xar.ck3.h2743.admitted-stock-source-pair.v1":"xar.ck3.h2743.traceable-source-pair.v1");r.put("status","SOURCE_PAIR_VERIFIED_NO_LAUNCH");r.put("pair_path",input.pairPath().normalize().toString());r.put("pair_sha256",pairSha);r.put("build_source_head",head);r.put("source_manifest_sha256",manifestSha);if(pinsSha!=null)r.put("stock_predicate_pins_sha256",pinsSha);r.put("native_source_checkout",input.nativeSourceCheckout().normalize().toString());r.set("actual_dependency_hashes_equal",counts);for(String k:List.of("source_quartet","dll","injector"))r.set(k,get(pair,k));for(String k:List.of("compilation_performed","ctest_rerun","ck3_started","native_condition_observed","material_complete"))r.put(k,false);r.putNull("action_literal");
            for(FileFact original:List.copyOf(observed.values()))need(measure(original.path()).equals(original),"provenance original changed before completion");
            return new VerifiedData(profile,new RawJson(DriverJson.encodeNode(r)),List.copyOf(observed.values()));
        }
    }
    /** Strict DATA round trip: this returns a source receipt object and cannot mint a live admission. */
    public static RawJson validateSourceReceipt(RawJson raw,Profile profile) {
        Objects.requireNonNull(profile);ObjectNode r=json(raw.bytes());Set<String> fields=new java.util.HashSet<>(Set.of("schema","status","pair_path","pair_sha256","build_source_head","source_manifest_sha256","native_source_checkout","actual_dependency_hashes_equal","source_quartet","dll","injector","compilation_performed","ctest_rerun","ck3_started","native_condition_observed","material_complete","action_literal"));if(profile==Profile.EXPLICIT_STOCK_RELEASE)fields.add("stock_predicate_pins_sha256");keys(r,fields.toArray(String[]::new));eq(r,"schema",profile==Profile.EXPLICIT_STOCK_RELEASE?"xar.ck3.h2743.admitted-stock-source-pair.v1":"xar.ck3.h2743.traceable-source-pair.v1");eq(r,"status","SOURCE_PAIR_VERIFIED_NO_LAUNCH");if(profile==Profile.HISTORICAL_BASELINE){eq(r,"pair_sha256",OLD_PAIR);eq(r,"build_source_head",OLD_HEAD);eq(r,"source_manifest_sha256",OLD_MANIFEST);}absolute(path(r,"pair_path"));absolute(path(r,"native_source_checkout"));hash(text(r,"pair_sha256"));head(text(r,"build_source_head"));hash(text(r,"source_manifest_sha256"));if(profile==Profile.EXPLICIT_STOCK_RELEASE)hash(text(r,"stock_predicate_pins_sha256"));ObjectNode c=object(get(r,"actual_dependency_hashes_equal"));keys(c,"dll","injector");integer(c,"dll");integer(c,"injector");ObjectNode q=object(get(r,"source_quartet"));keys(q,"xar_checkpoint.ck3","driver-state.json","first-heir-marriage-formal-v1.json","xar_ck3_bridge.dll");for(JsonNode a:q)validateAsset(a);for(String k:List.of("dll","injector")){JsonNode a=get(r,k);validateAsset(a);path(a,"build_result");path(a,"postcheck");hash(text(a,"build_result_sha256"));hash(text(a,"postcheck_sha256"));}for(String k:List.of("compilation_performed","ctest_rerun","ck3_started","native_condition_observed","material_complete"))bool(r,k,false);nil(r,"action_literal");return new RawJson(DriverJson.encodeNode(r));
    }
    /** Portable DATA only; 64-bit byte extents use canonical decimal strings. */
    public static RawJson encodeData(VerifiedData data) {
        Objects.requireNonNull(data);ObjectNode n=JsonNodeFactory.instance.objectNode();n.put("schema","xar.java.h2743.stock-source-data/v1");n.put("profile",data.profile().name());n.set("source_receipt",json(validateSourceReceipt(data.sourceReceipt(),data.profile()).bytes()));var files=n.putArray("complete_files");Set<Path> seen=new java.util.HashSet<>();need(data.completeFiles().size()<=8192,"source DATA closure exceeds8192");for(FileFact f:data.completeFiles()){need(seen.add(f.path()),"duplicate DATA original");ObjectNode row=files.addObject();row.put("path",f.path().toString());row.put("size_bytes",Long.toString(f.bytes()));row.put("sha256",f.sha256());}return new RawJson(DriverJson.encodeNode(n));
    }
    public static VerifiedData decodeData(RawJson raw) {
        ObjectNode n=json(raw.bytes());keys(n,"schema","profile","source_receipt","complete_files");eq(n,"schema","xar.java.h2743.stock-source-data/v1");Profile profile;try{profile=Profile.valueOf(text(n,"profile"));}catch(RuntimeException bad){throw new IllegalArgumentException("H2743 unknown DATA profile",bad);}RawJson receipt=validateSourceReceipt(new RawJson(DriverJson.encodeNode(get(n,"source_receipt"))),profile);List<FileFact> files=new ArrayList<>();Set<Path> seen=new java.util.HashSet<>();JsonNode rows=array(get(n,"complete_files"));need(rows.size()>0&&rows.size()<=8192,"bounded nonempty DATA closure required");for(JsonNode rawRow:rows){ObjectNode row=object(rawRow);keys(row,"path","size_bytes","sha256");String extent=text(row,"size_bytes");need(extent.matches("0|[1-9][0-9]*"),"canonical decimal byte extent required");java.math.BigInteger bytes=new java.math.BigInteger(extent);need(bytes.bitLength()<=63,"byte extent exceeds signed long");Path path=path(row,"path");need(seen.add(path),"duplicate DATA original");files.add(new FileFact(path,bytes.longValueExact(),text(row,"sha256")));}return new VerifiedData(profile,receipt,files);
    }
    private static void validateAsset(JsonNode a){object(a);path(a,"path");hash(text(a,"sha256"));if(a.has("size_bytes"))integer(a,"size_bytes");}
    private static ObjectNode json(byte[] raw){int start=raw.length>=3&&(raw[0]&255)==239&&(raw[1]&255)==187&&(raw[2]&255)==191?3:0;byte[] bytes=start==0?raw:java.util.Arrays.copyOfRange(raw,start,raw.length);return object(DriverJson.toNode(DriverJson.object(bytes,16777216)));}
    private static ObjectNode object(JsonNode n){need(n!=null&&n.isObject(),"expected provenance object");return (ObjectNode)n;}
    private static JsonNode get(JsonNode n,String k){JsonNode v=object(n).get(k);need(v!=null,"missing field: "+k);return v;}
    private static JsonNode array(JsonNode n){need(n!=null&&n.isArray(),"expected array");return n;}
    private static String text(JsonNode n,String k){JsonNode v=get(n,k);need(v.isTextual()&&!v.textValue().isBlank(),"nonempty text required: "+k);return v.textValue();}
    private static long integer(JsonNode n,String k){JsonNode v=get(n,k);need(v.isIntegralNumber()&&v.canConvertToLong()&&v.longValue()>=0,"exact nonnegative integer required: "+k);return v.longValue();}
    private static void exactCounts(JsonNode n,List<String> keys,List<Long> values){for(int i=0;i<keys.size();i++)need(integer(n,keys.get(i))==values.get(i),"fixture count/result differs: "+keys.get(i));}
    private static void bool(JsonNode n,String k,boolean b){JsonNode v=get(n,k);need(v.isBoolean()&&v.booleanValue()==b,"boolean differs: "+k);}
    private static void nil(JsonNode n,String k){need(get(n,k).isNull(),"explicit null required: "+k);}
    private static void eq(JsonNode n,String k,String s){need(text(n,k).equals(s),"text differs: "+k);}
    private static void keys(ObjectNode n,String... names){Set<String> actual=new java.util.HashSet<>();n.fieldNames().forEachRemaining(actual::add);need(actual.equals(Set.of(names)),"field roster differs");}
    private static Set<String> stringSet(JsonNode n){Set<String> r=new java.util.HashSet<>();for(JsonNode v:array(n)){need(v.isTextual(),"stage must be string");r.add(v.textValue());}return Set.copyOf(r);}
    private static Path path(JsonNode n,String k){Path p=Path.of(text(n,k));absolute(p);return p;}
    private static void absolute(Path p){need(p!=null&&p.isAbsolute()&&p.normalize().equals(p),"absolute normalized path required");}
    private static void hash(String s){need(s!=null&&s.matches("[0-9A-F]{64}"),"uppercase exact SHA256 required");}
    private static void head(String s){need(s!=null&&s.matches("[0-9a-f]{40}"),"lowercase exact source head required");}
    private static String digest(byte[] raw){return DriverJson.sha256(raw).toUpperCase(java.util.Locale.ROOT);}
    private static void need(boolean ok,String why){if(!ok)throw new IllegalArgumentException("H2743 "+why);}
}
