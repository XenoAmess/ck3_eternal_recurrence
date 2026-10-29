package org.xar.ck3.control.nativebridge.capabilities.frontendfixture;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual Java migration of the six source-bound external intro handlers. It never loads Python. */
public final class FixtureStartupCase implements FixtureStartupHandler {
    public static final String SCHEMA="xar.java.frontend-fixture-startup-case/v1";
    private static final String PARSER_SHA="2edca624e611e6f6be7c6147774b1fae8892cdc24de0ef5a96e36214d388b968";
    public enum Handler {
        ORIGINAL("xqol_adapter.py","ca4284d9c8f9742bf071f2d8714a93f3e82c74e49a5a4df0de41ed565f0ac59e","ZQD120QUAL",true),
        UI_TAIL("xqol_ui_tail_adapter.py","06cc56f8036db6a4d1973a9ce7ef7fcdbe8836a58038a9af89d9cf363164adfb","ZQAUITAIL",false),
        GUARDS("xqol_guards_focused_adapter.py","7f5c6f308f85f7fde37bbb0fb2fcf3bb724c60c5dc1d439b0fec712dc78cef91","ZQAGUARD",false),
        FOLLOWUP("xqol_followup_common.py","da2208f6b2379f9f667989695ede8045735a0cbe0423ea4ba70db978b6609cfa","ZQR120QUAL",false),
        RELIGION("xqol_religion_adapter.py","3fd9ec809ec1ba609eb6a5dce2763868be8613e895579b0cf00899027de18ed8","ZQREL",false),
        ORDINARY_ASYNC("xqol_ordinary_async_adapter.py","dde7ea52b94d30bc826428367612a554ae057a1d7f8a6e967d8ad4f00666abf1","ZQR120QUAL",false);
        final String file,sha,prefix;final boolean steppe;
        Handler(String file,String sha,String prefix,boolean steppe){this.file=file;this.sha=sha;this.prefix=prefix;this.steppe=steppe;}
    }
    private final ExactRef contract,implementation,originalHandler;
    private final List<ExactRef> dependencies,closure;
    private final Handler handler;
    private final PreparedFixture fixture;
    private final List<SharedSourceFiles.Witness> witnesses;
    private FixtureStartupCase(ExactRef contract,ExactRef implementation,ExactRef originalHandler,
            List<ExactRef> dependencies,Handler handler,PreparedFixture fixture)throws IOException {
        this.contract=contract;this.implementation=implementation;this.originalHandler=originalHandler;
        this.dependencies=List.copyOf(dependencies);this.handler=handler;this.fixture=fixture;
        var refs=new ArrayList<ExactRef>();refs.add(contract);refs.add(implementation);refs.add(originalHandler);refs.addAll(dependencies);closure=List.copyOf(refs);
        var held=new ArrayList<SharedSourceFiles.Witness>();for(ExactRef ref:closure){readExact(ref,16*1024*1024);held.add(SharedSourceFiles.observe(Path.of(ref.path())));}witnesses=List.copyOf(held);
    }
    public static FixtureStartupCase prepare(ExactRef source,PreparedFixture identical)throws IOException {
        Objects.requireNonNull(source);Objects.requireNonNull(identical);identical.verifySources();
        ObjectNode row=StrictJson.object(StrictJson.parse(readExact(source,1024*1024)),Set.of("schema","state_dir","handler","handler_source","original_handler","original_dependencies"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema")))&&Path.of(StrictJson.text(row.get("state_dir"))).toRealPath().equals(identical.stateDir()),
                "external startup case requires its exact Java schema and identical actual state root");
        Handler handler=Handler.valueOf(StrictJson.text(row.get("handler")));
        ExactRef implementation=ExactRef.fromJson(row.get("handler_source")),original=ExactRef.fromJson(row.get("original_handler"));
        StrictJson.require(Path.of(implementation.path()).getFileName().toString().equals("FixtureStartupCase.java")
                &&Path.of(original.path()).getFileName().toString().equals(handler.file)&&original.sha256().equals(handler.sha),
                "external handler changed its reviewed original or named Java producer");
        JsonNode input=row.get("original_dependencies");StrictJson.require(input.isArray()&&input.size()>=3&&input.size()<=16,"complete bounded original external dependency list required");
        var dependencies=new ArrayList<ExactRef>();for(JsonNode node:input)dependencies.add(ExactRef.fromJson(node));
        var names=dependencies.stream().map(ref->Path.of(ref.path()).getFileName().toString()).collect(java.util.stream.Collectors.toSet());
        Set<String> expected=new java.util.HashSet<>(Set.of("xqol_scope.py","ck3_mod_acceptance_prepare.py","__init__.py"));
        switch(handler) {
            case ORIGINAL->expected.add("xqol_original_plans.json");
            case UI_TAIL->expected.addAll(Set.of("xqol_adapter.py","xqol_ui.py","xqol_original_plans.json","xqol_defense_and_ui.json"));
            case ORDINARY_ASYNC->expected.addAll(Set.of("xqol_ordinary_async.json","xqol_ordinary_async.plan.json","xqol_ordinary_async.rules.json"));
            default->{ }
        }
        StrictJson.require(names.equals(expected)&&names.size()==dependencies.size(),"complete original external handler dependency set changed");
        StrictJson.require(dependencies.stream().map(ExactRef::path).distinct().count()==dependencies.size()
                &&dependencies.stream().anyMatch(ref->Path.of(ref.path()).getFileName().toString().equals("xqol_scope.py")&&ref.sha256().equals(PARSER_SHA))
                &&dependencies.stream().anyMatch(ref->Path.of(ref.path()).getFileName().toString().equals("ck3_mod_acceptance_prepare.py"))
                &&dependencies.stream().anyMatch(ref->Path.of(ref.path()).getFileName().toString().equals("__init__.py")),"original external handler dependency/source closure incomplete");
        var result=new FixtureStartupCase(source,implementation,original,dependencies,handler,identical);result.verifySources();return result;
    }
    public ExactRef implementationSource(){return implementation;}
    public ExactRef contractSource(){return contract;}
    public Handler handler(){return handler;}
    @Override public List<ExactRef> sourceClosure(){return closure;}
    public void requireReviewedSources(List<ExactRef> actualInstalledSources)throws IOException {
        verifySources();StrictJson.require(actualInstalledSources.contains(implementation),"external Java handler absent from actual reviewed runtime source closure");
    }
    @Override public void verifySources()throws IOException {
        fixture.verifySources();for(var witness:witnesses)SharedSourceFiles.assertUnchanged(witness);
    }
    @Override public SelectDisplayedOption decide(PreparedFixture same,OpportunityJson.Obj snapshot,OpportunityJson.Obj eventWindow)throws IOException {
        StrictJson.require(same==fixture,"external startup handler changed its sole prepared fixture");verifySources();
        Path path=fixture.profileDirectory().resolve("logs/debug.log");
        var witness=SharedSourceFiles.observe(path);byte[] raw=readBounded(path,64*1024*1024);SharedSourceFiles.assertUnchanged(witness);ExactRef log=reference(path,raw);
        StrictJson.require(log.sha256().equals(witness.source().sha256()),"external qualification log changed during read");
        var scopes=new ArrayList<ActorScope>();scopes.add(parseScope(raw,"xqol_startup_actor","han_8052",handler.prefix));
        if(handler.steppe)scopes.add(parseScope(raw,"xqol_steppe_startup_actor","194333","ZQD120STEPPEQUAL"));
        ActorScope actor=scopes.get(scopes.size()-1);
        validateIntro(DriverJson.toNode(snapshot),DriverJson.toNode(eventWindow),actor.runtimeCharacterId());
        return new SelectDisplayedOption(1,1,new ScopeEvidence(log,scopes,false),implementation);
    }
    /** Replays the identical original handler over immutable archived log/snapshot/window DATA. */
    public void verifyOriginal(byte[] raw,OpportunityJson.Obj snapshot,OpportunityJson.Obj window,SelectDisplayedOption decision)throws IOException {
        verifySources();StrictJson.require(implementation.equals(decision.implementationSource())&&decision.eventInstanceId()==1&&decision.optionNumber()==1
                &&decision.proof().actualLog().bytes()==raw.length&&decision.proof().actualLog().sha256().equals(sha(raw)),"external handler original source/log/selection changed");
        var scopes=new ArrayList<ActorScope>();scopes.add(parseScope(raw,"xqol_startup_actor","han_8052",handler.prefix));
        if(handler.steppe)scopes.add(parseScope(raw,"xqol_steppe_startup_actor","194333","ZQD120STEPPEQUAL"));
        StrictJson.require(scopes.equals(decision.proof().scopes()),"original unique current/saved actor scope proof changed");
        validateIntro(DriverJson.toNode(snapshot),DriverJson.toNode(window),scopes.getLast().runtimeCharacterId());
    }
    /** Exact byte-domain original scope parser; historical ID is parser input, never a live actor substitute. */
    static ActorScope parseScope(byte[] raw,String alias,String historical,String prefix)throws IOException {
        if(raw.length>64*1024*1024)throw new IOException("QOL scope log exceeds original 64MiB bound");
        boolean plain=prefix.equals("ZQAUITAIL")||prefix.equals("ZQAGUARD")||prefix.equals("ZQREL");
        String suffix=plain?"actual_song_actor":alias.contains("steppe")?"actual_steppe_actor_D0":"actual_song_actor_D0";
        String begin=prefix+": SCOPE BEGIN "+suffix,pass=prefix+(plain?": SCOPE PASS ":": TEST PASS ")+suffix,
                end=prefix+": SCOPE END "+suffix,fail=prefix+": TEST FAIL "+suffix;
        String all=new String(raw,StandardCharsets.ISO_8859_1);
        if(count(all,fail)>0||count(all,begin)!=1||count(all,pass)!=1||count(all,end)!=1)throw new IOException("actual unique passing external actor scope unavailable");
        // bytes.splitlines(keepends=True): preserve byte offsets, CR, LF and CRLF exactly.
        var starts=new ArrayList<Integer>();var ends=new ArrayList<Integer>();int position=0;
        while(position<all.length()){int start=position;while(position<all.length()&&all.charAt(position)!='\r'&&all.charAt(position)!='\n')position++;
            if(position<all.length()){char c=all.charAt(position++);if(c=='\r'&&position<all.length()&&all.charAt(position)=='\n')position++;}starts.add(start);ends.add(position);}
        int b=line(all,starts,ends,begin),p=line(all,starts,ends,pass),e=line(all,starts,ends,end);
        if(!(b<p&&p<e))throw new IOException("external scope marker order changed");
        String body=all.substring(ends.get(b),starts.get(p));
        String id="\\(Internal ID: ([1-9][0-9]*) - Historical ID "+Pattern.quote(historical)+"\\)";
        Matcher header=Pattern.compile("(?m)^Saved event targets:\\r?$").matcher(body);
        Matcher saved=Pattern.compile("(?m)^"+Pattern.quote(alias)+": [^\\r\\n]*?"+id+"[^\\r\\n]*\\r?$").matcher(body);
        Matcher current=Pattern.compile("(?m)^\\[\\d{2}:\\d{2}:\\d{2}\\]\\[D\\]\\[effectimpl\\.cpp:\\d+\\]: [^\\r\\n]*?"+id+"[^\\r\\n]*\\r?$").matcher(body);
        if(!current.find())throw new IOException("original current actor dump absent");int actor=positive(current.group(1)),currentEnd=current.end();if(current.find())throw new IOException("duplicate current actor dump");
        if(!header.find())throw new IOException("original saved section absent");int headerStart=header.start();if(header.find())throw new IOException("duplicate saved section");
        if(!saved.find())throw new IOException("original saved actor absent");int savedActor=positive(saved.group(1)),savedStart=saved.start();if(saved.find())throw new IOException("duplicate saved actor");
        Matcher labels=Pattern.compile("(?m)^"+Pattern.quote(alias)+":").matcher(body);int labelCount=0;while(labels.find())labelCount++;
        if(actor!=savedActor||labelCount!=1||!(currentEnd<headerStart&&headerStart<savedStart))throw new IOException("current and uniquely saved external actor identities disagree");
        int byteStart=starts.get(b),byteEnd=ends.get(e);return new ActorScope(actor,historical,alias,b+1,p+1,e+1,byteStart,byteEnd,sha(Arrays.copyOfRange(raw,byteStart,byteEnd)));
    }
    static void validateIntro(JsonNode snapshot,JsonNode packet,int actor) {
        JsonNode played=snapshot.path("played_character"),event=snapshot.path("active_event"),typed=packet.path("current_event_window_context"),identity=typed.path("root_scope").path("typed_identity");
        StrictJson.require(integer(played.get("character_id"))==actor&&truth(played.get("alive"))&&text(played,"source").equals("native"),"external intro differs from actual scope actor");
        StrictJson.require(event.isObject()&&text(event,"source").equals("native")&&integer(event.get("instance_id"))==1&&integer(event.get("option_count"))==1,"original sole first native intro changed");
        JsonNode options=event.path("options");StrictJson.require(options.isArray()&&options.size()==1&&truth(options.get(0).get("enabled"))&&integer(options.get(0).get("option_number"))==1&&integer(options.get(0).get("index"))==0,"original displayed intro option changed");
        StrictJson.require(text(packet,"status").equals("available")&&truth(packet.get("current_event_window_context_ready"))&&text(typed,"schema").equals("current-event-window-context-v1")
                &&integer(typed.get("schema_version"))==1&&text(typed,"status").equals("available")&&integer(typed.get("window_match_count"))==1&&integer(typed.get("current_event_instance_id"))==1
                &&integer(typed.get("snapshot_revision"))==integer(snapshot.get("native_revision"))&&integer(typed.get("date_raw"))==integer(snapshot.get("date_raw"))
                &&text(identity,"status").equals("available")&&text(identity,"kind").equals("character")&&integer(identity.get("character_id"))==actor,"typed external intro owner/revision/date changed");
        JsonNode shown=typed.path("options");StrictJson.require(shown.isArray()&&shown.size()==1,"typed sole option required");JsonNode option=shown.get(0);
        StrictJson.require(integer(option.get("rendered_index"))==0&&integer(option.get("native_option_index"))==0&&truth(option.get("shown"))&&truth(option.get("enabled"))&&!truth(option.get("fallback"))&&!truth(option.get("cancel")),"typed original option changed");
    }
    private static String text(JsonNode n,String field){return StrictJson.text(n.get(field));}
    private static long integer(JsonNode n){return StrictJson.integer(n,0,Long.MAX_VALUE);}
    private static boolean truth(JsonNode n){StrictJson.require(n!=null&&n.isBoolean(),"exact boolean required");return n.booleanValue();}
    private static int positive(String n)throws IOException {try{int i=Integer.parseInt(n);if(i>0)return i;}catch(NumberFormatException ignored){}throw new IOException("original actor ID outside signed32");}
    private static int line(String all,List<Integer> starts,List<Integer> ends,String marker){for(int i=0;i<starts.size();i++)if(all.substring(starts.get(i),ends.get(i)).contains(marker))return i;throw new IllegalArgumentException("scope marker absent");}
    private static int count(String haystack,String needle){int n=0,index=0;while((index=haystack.indexOf(needle,index))>=0){n++;index+=needle.length();}return n;}
    private static byte[] readExact(ExactRef ref,long limit)throws IOException {Path path=Path.of(ref.path());byte[] b=readBounded(path,limit);if(b.length!=ref.bytes()||!sha(b).equals(ref.sha256()))throw new IOException("external startup exact source changed: "+path);return b;}
    private static byte[] readBounded(Path path,long limit)throws IOException {long size=Files.size(path);if(size>limit)throw new IOException("external startup input exceeds bound");try(var in=Files.newInputStream(path)){byte[] b=in.readNBytes(Math.toIntExact(limit+1));if(b.length>limit||Files.size(path)!=size)throw new IOException("external startup input changed or exceeds bound");return b;}}
    private static ExactRef reference(Path path,byte[] raw)throws IOException {return new ExactRef(path.toRealPath().toString(),raw.length,sha(raw));}
    private static String sha(byte[] bytes){try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));}catch(NoSuchAlgorithmException impossible){throw new IllegalStateException(impossible);}}
}
