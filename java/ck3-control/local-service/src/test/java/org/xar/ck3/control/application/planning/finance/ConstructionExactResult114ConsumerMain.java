package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.*;
import java.lang.management.ManagementFactory;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Clock;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.NativeConstructionEffects;
import org.xar.ck3.control.continuity.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction.NativeQuote;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec.ObservedRequest;

/** Finite manual consumer DATA benchmark, never Policy.evaluate/revalidate or a Native READ.
 * Real production entries: full factories, compose, fixed finalizer/cache, Source.preserve/resolveCommand,
 * sameQuote, package-private Lifecycle.intent and its existing canonical-body codec. Args/action assembly
 * below is explicitly DATA adaptation of the Policy fields, not execution of that complete policy.
 * PREP creates a separate SOFTWARE mutable store once; four JVMs reopen identical absolute input/source/CAS.
 * The old captured command is decoded as a DATA prototype, never rewritten, registered or executed.
 */
public final class ConstructionExactResult114ConsumerMain {
    private static final int FULL=FullJsonTree.MAXIMUM_BYTES;
    private static final long BUDGET=64L*1024*1024;
    private static final ObjectMapper JSON=new ObjectMapper();
    private static final Method GETTER=findGetter();
    private static final java.lang.management.ThreadMXBean CPU=ManagementFactory.getThreadMXBean();
    private static final com.sun.management.ThreadMXBean ALLOC=CPU instanceof com.sun.management.ThreadMXBean value?value:null;
    // Phases are disjoint, including actual writer acquisition/release; whole spans the complete held-session call.
    private ConstructionExactResult114ConsumerMain() { }

    /** prepare ROOT ORIGINAL_FULL_PLAN ORIGINAL_RECEIPT OUT; run ROOT LABEL OUT. */
    public static void main(String[] args)throws Throwable {
        long mainStart=System.nanoTime();enableMetrics();
        Map<String,Object> report=new LinkedHashMap<>();report.put("schema","ck3.p114.complete-consumer-data/v1");
        report.put("actual_policy_evaluate_or_revalidate",false);report.put("Native_Game_HTTP_SAVE",0);
        report.put("new_cache_api_present",GETTER!=null);report.put("cohort","all-warm-existing-CAS; mutable real preserve, no cold/warm mixing");
        report.put("boundary","factory+compose+DATA extraction/args+real same-writer preserve/readback/resolve+distinct fixed-DATA Q2+pure intent; excludes Native/physical SEM/owning publication admission");
        Throwable failed=null;
        Path output=Path.of(args[args.length-1]).toAbsolutePath().normalize();
        try {
            if(args[0].equals("prepare")) {
                check(args.length==5,"prepare args");prepare(Path.of(args[1]).toAbsolutePath().normalize(),Path.of(args[2]),Path.of(args[3]),report);
            } else {
                check(args.length==4&&args[0].equals("run"),"run args");
                Path root=Path.of(args[1]).toAbsolutePath().normalize();String label=args[2];
                check(label.equals("A0")||label.equals("B0")||label.equals("B1")||label.equals("A1"),"fixed ABBA label");
                check(label.startsWith("B")== (GETTER!=null),"only classpath determines actual new API presence");
                report.put("label",label);run(root,report);
            }
        } catch(Throwable failure) {failed=failure;report.put("failure_class",failure.getClass().getName());report.put("failure_message",String.valueOf(failure.getMessage()));}
        report.put("main_ns_before_output",System.nanoTime()-mainStart);
        Files.createDirectories(output.getParent());Files.write(output,FullJsonTree.encode(JSON.valueToTree(report),1_048_576));
        if(failed!=null)throw failed;
        System.out.println("P114 consumer DATA complete "+output);
    }
    private static void prepare(Path root,Path originalPlan,Path originalReceipt,Map<String,Object> report)throws Exception {
        check(!Files.exists(root),"PREP requires a new independent root; never reset an existing store");Files.createDirectories(root);
        byte[] captured=Files.readAllBytes(originalPlan),receipt=Files.readAllBytes(originalReceipt);
        ObjectNode q1=(ObjectNode)FullJsonTree.parse(captured,FULL),small=q1.deepCopy();
        ObjectNode nested=query(q1),smallQuery=query(small);
        JsonNode history=pureHistory139();check(history.isArray()&&history.size()==139,"qualified first139 DATA rows");
        for(String key:List.of("starting_snapshot","ending_snapshot")) {
            ObjectNode before=(ObjectNode)nested.get(key),control=(ObjectNode)smallQuery.get(key);
            check(before.get("opaque_unconsumed_extension").isTextual()&&before.get("opaque_unconsumed_extension").textValue().length()==3_400_000,"captured public SOFTWARE extension");
            before.remove("opaque_unconsumed_extension");before.set("native_command_history",history.deepCopy());
            control.remove("opaque_unconsumed_extension");
        }
        ObjectNode q2=q1.deepCopy(),second=query(q2),envelope=(ObjectNode)second.get("native_envelope");
        String refreshed=second.get("native_query_request_id").textValue()+"-p114-fixed-data-second";
        second.put("native_query_request_id",refreshed);envelope.put("request_id",refreshed);
        ObjectNode probe=(ObjectNode)envelope.get("result").get("private_probe");probe.put("proof_epoch",probe.get("proof_epoch").bigIntegerValue().add(java.math.BigInteger.ONE));
        byte[] full=FullJsonTree.encode(q1,FULL),fresh=FullJsonTree.encode(q2,FULL),control=FullJsonTree.encode(small,FULL);
        check(full.length>6_000_000&&control.length<OrdinaryWartimeConstructionCodec.MAX_BYTES,"large139/control dimensions");
        ObjectNode original=(ObjectNode)FullJsonTree.parse(receipt,FULL);
        byte[] command=FullJsonTree.encode(original.get("command"),ActionCodec.MAX_COMMAND_BYTES);
        ActionCommand prototype=ActionCodec.decodeCommand(command);
        check(Arrays.equals(command,ActionCodec.encodeCommand(prototype)),"captured canonical command bytes");
        write(root,"input-q1.json",full);write(root,"input-q2.json",fresh);write(root,"input-small.json",control);write(root,"prototype-command.json",command);
        write(root,"anchor.json",initial(prototype));write(root,"ROOT-CONTINUITY-WINDOW.json",initial(prototype));write(root,"ROOT-CONTINUITY-WINDOW.lock",new byte[0]);
        Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));Files.createDirectory(root.resolve("objects"));
        ObjectNode manifest=StrictJson.object();manifest.put("captured_public_plan_sha256",ActionCodec.sha256(captured));manifest.put("captured_public_plan_bytes",captured.length);
        manifest.put("derivation","DATA reconstruction: replace only both unconsumed3.4M strings with qualified139history; keep every other captured member. Control removes only those two strings. Q2 fixed DATA request/probe refresh, never a new READ.");
        manifest.put("q1_sha256",ActionCodec.sha256(full));manifest.put("q2_sha256",ActionCodec.sha256(fresh));manifest.put("small_sha256",ActionCodec.sha256(control));manifest.put("prototype_sha256",ActionCodec.sha256(command));
        manifest.set("source",prototype.source().sourceRef().toJson());write(root,"DATA.json",FullJsonTree.encode(manifest,1_048_576));
        var data=new Data(root);
        try(var env=new Environment(root,data.prototype)) {
            report.put("software_allocation_cards",env.cards);
            Trace smallTrace=new Trace("setup_small_control",0);
            try {perform(env,data,data.small,data.small,smallTrace);check(!smallTrace.cached,"old public-small fallback control");}
            finally {report.put("small_control",smallTrace.map());}
            Trace prep=new Trace("PREP_first_durable_publish",0);
            try {perform(env,data,data.q1,data.q2,prep);check(!prep.casExisted,"PREP records the first creation, outside both measured variants");}
            finally {report.put("first_publish",prep.map());}
            ObjectNode expected=JSON.valueToTree(prep.markers);write(root,"EXPECTED.json",FullJsonTree.encode(expected,1_048_576));
            check(env.writer.locked(same->same.head().state().sequence())==0,"DATA benchmark never publishes an action/domain event");
        }
        check(Arrays.equals(captured,Files.readAllBytes(originalPlan))&&Arrays.equals(receipt,Files.readAllBytes(originalReceipt)),"captured originals unchanged");
        report.put("root",root.toString());report.put("data_manifest",manifest);report.put("setup_only",true);
    }
    private static void run(Path root,Map<String,Object> report)throws IOException {
        long setup=System.nanoTime();var data=new Data(root);report.put("root",root.toString());report.put("data_manifest",FullJsonTree.parse(Files.readAllBytes(root.resolve("DATA.json")),1_048_576));
        report.put("prototype_deadline_descriptor_only_never_executed",data.prototype.deadline().toString());
        ObjectNode expected=(ObjectNode)FullJsonTree.parse(Files.readAllBytes(root.resolve("EXPECTED.json")),1_048_576);
        List<Map<String,Object>> samples=new ArrayList<>();report.put("all_calls",samples);
        try(var env=new Environment(root,data.prototype)) {
            report.put("software_allocation_cards",env.cards);report.put("setup_ns",System.nanoTime()-setup);
            for(int i=0;i<6;i++) {
                Trace trace=new Trace(i<2?"warmup":"measured",i<2?i:i-2);
                try {perform(env,data,data.q1,data.q2,trace);
                    check(trace.casExisted,"all ABBA calls must be warm-existing same CAS, including first warmup");
                    check(expected.equals(JSON.valueToTree(trace.markers)),"full scalar/hash marker set differs from PREP successful baseline");
                }catch(Throwable failure){trace.failure=failure.getClass().getName()+":"+failure.getMessage();throw failure;}
                finally{samples.add(trace.map());}
            }
            check(env.writer.locked(same->same.head().state().sequence())==0,"no actions/domain events");
        }
    }
    private static void perform(Environment env,Data data,byte[] q1,byte[] q2,Trace trace)throws IOException {
        trace.callStart=point();
        try {env.writer.locked(same->{operation(env,data,q1,q2,same,trace);return null;});}
        catch(Throwable failure){trace.failure=failure.getClass().getName()+":"+failure.getMessage();throw failure;}
        finally {Point end=point();if(trace.innerEnd!=null)trace.phases.put("writer_release",delta(trace.innerEnd,end));trace.whole=delta(trace.callStart,end);}
    }
    private static void operation(Environment env,Data data,byte[] q1,byte[] q2,Session same,Trace t)throws IOException {
        Point begin=point(),last=begin;t.phases.put("writer_acquire",delta(t.callStart,begin));
        ObservedRequest first=observed(q1);NativeQuote quote=first.input().quoted().orElseThrow().nativeQuote();
        last=t.phase("construct",last);
        var result=OrdinaryWartimeConstruction.compose(first.input());check(result.disposition()==OrdinaryWartimeConstruction.Disposition.QUOTED_CANDIDATE,"SELECTED/QUOTED before timing comparison");
        last=t.phase("compose",last);
        byte[] finalized=finalized(quote,t);Obj selected=object(parse(finalized),"existing fixed finalized quote");
        ExactRef source=data.prototype.source().sourceRef();exactFile(source);
        last=t.phase("extract_and_metadata_source",last);
        String inputSha=ActionCodec.sha256(q1);t.casExisted=Files.exists(env.root.resolve("objects").resolve(inputSha+".bin"));
        Obj supplied=new ConstructionOriginalSource(env.archive,env.writer::borrowedSession).preserve(first);
        last=t.phase("preserve_readback",last);
        // DATA assembly of the actual Policy fields; the full Policy and its live collectors are not executed.
        Obj args=obj("candidate",selected.get("candidate"),"pre_proof_epoch",selected.get("proof_epoch"),"ordinary_cash_request",supplied,
                "ordinary_cash_result",DriverJson.object(OrdinaryWartimeConstructionCodec.encode(result),OrdinaryWartimeConstructionCodec.MAX_BYTES),
                ConstructionFundingEvidence.FIELD,data.prototype.arguments().get(ConstructionFundingEvidence.FIELD));
        String id=ActionIds.forDecision(data.prototype.sessionId(),data.prototype.before(),OrdinaryConstructionPolicy.OPERATION.value()+":"+ActionCodec.sha256(encode(args)));
        ActionCommand command=new ActionCommand(id,data.prototype.before(),data.prototype.source(),data.prototype.sessionId(),OrdinaryConstructionPolicy.OPERATION,args,
                NativeConstructionEffects.expected(data.prototype.before(),data.prototype.source(),args),data.prototype.claims(),data.prototype.deadline());
        check(!id.equals(data.prototype.actionId()),"distinct unexecuted DATA command, never mutate/reissue original");
        byte[] canonicalCommand=ActionCodec.encodeCommand(command);ConstructionFundingEvidence.command(command);
        last=t.phase("args_command_data",last);
        // Reopen the canonical command representation, just as the actual cold consumer does.
        var decodedCommand=ActionCodec.decodeCommand(canonicalCommand);
        var loaded=ConstructionOriginalSource.resolveCommand(same,env.archive,decodedCommand);
        if(new Text(ConstructionOriginalSource.SCHEMA).equals(supplied.get("schema")))
            check(Arrays.equals(first.original(),loaded.observed().original()),"physical full reread exact bytes");
        else {
            // The historical inline loader reencodes canonical decoded args with its original encoder/ctor.
            // Only this small setup control uses that existing representation, never the full-CAS oracle.
            byte[] expectedOld=new ObservedRequest(encode(object(decodedCommand.arguments().get("ordinary_cash_request"),"canonical inline original"))).original();
            check(Arrays.equals(expectedOld,loaded.observed().original()),"old inline canonical-command representation");
        }
        last=t.phase("resolve_full",last);
        ObservedRequest second=observed(q2);check(first!=second&&quote!=second.input().quoted().orElseThrow().nativeQuote(),"new distinct DATA quote, never a cross-call cached object");
        var current=OrdinaryWartimeConstruction.compose(second.input());check(current.disposition()==OrdinaryWartimeConstruction.Disposition.QUOTED_CANDIDATE,"DATA Q2 positive");
        check(OrdinaryConstructionPolicy.sameQuote(result.candidate().orElseThrow().original().bytes(),current.candidate().orElseThrow().original().bytes()),"existing fresh-quote identity comparison");
        last=t.phase("distinct_q2_compose_compare",last);
        Obj empty=obj("schema",new Text(ConstructionLedgerCodec.SCHEMA),"pending",Nil.INSTANCE,"applied",Nil.INSTANCE,"applied_prior",new Arr(List.of()));
        var body=ConstructionDomainLifecycle.intent(ConstructionLedgerCodec.decodeLedger(DriverJson.encode(empty)),command,loaded);
        byte[] canonicalBody=ConstructionDomainLifecycle.Prepared.canonicalBody(body);check(ConstructionLedgerCodec.decodeLedger(canonicalBody).pending().isPresent(),"actual pure intent typed body");
        last=t.phase("pure_intent_canonical",last);
        t.markers.put("input_sha256",inputSha);t.markers.put("input_bytes",String.valueOf(q1.length));t.markers.put("q2_sha256",ActionCodec.sha256(q2));
        t.markers.put("result_sha256",ActionCodec.sha256(OrdinaryWartimeConstructionCodec.encode(result)));t.markers.put("finalized_sha256",ActionCodec.sha256(finalized));
        t.markers.put("args_sha256",ActionCodec.sha256(encode(args)));t.markers.put("command_sha256",ActionCodec.sha256(canonicalCommand));t.markers.put("action_id",id);
        t.markers.put("body_sha256",ActionCodec.sha256(canonicalBody));t.markers.put("body_bytes",String.valueOf(canonicalBody.length));
        t.markers.put("source_path",source.path());t.markers.put("source_sha256",source.sha256());t.markers.put("source_bytes",String.valueOf(source.bytes()));
        t.markers.put("prototype_sha256",ActionCodec.sha256(ActionCodec.encodeCommand(data.prototype)));
        if(new Text(ConstructionOriginalSource.SCHEMA).equals(supplied.get("schema"))) {
            var ref=ExactRef.fromJson(StrictJson.parse(DriverJson.encode(object(supplied.get("input_ref"),"full reference"))));
            check(ref.bytes()==q1.length&&ref.sha256().equals(inputSha),"actual CAS ref/length/SHA");t.markers.put("CAS_path",ref.path());t.markers.put("CAS_sha256",ref.sha256());
        }else t.markers.put("CAS_path","old-small-inline-control");
        check(Arrays.equals(q1,first.original())&&Arrays.equals(q2,second.original()),"original input array identity unchanged");
        if(q1.length>OrdinaryWartimeConstructionCodec.MAX_BYTES)check(t.cached==(GETTER!=null),"every large call uses the actual B cache or A fixed fallback");
        else check(!t.cached,"old-small control never adopts full-only cache");
        if(data.expected!=null&&q1==data.q1)check(data.expected.equals(JSON.valueToTree(t.markers)),"full scalar/hash markers equal successful baseline PREP");
        last=t.phase("marker_and_input_validation",last);t.innerEnd=last;
    }
    private static ObservedRequest observed(byte[] raw){return raw.length>OrdinaryWartimeConstructionCodec.MAX_BYTES?ObservedRequest.fromFullMaterial(raw):new ObservedRequest(raw);}
    private static Method findGetter(){try{return NativeQuote.class.getMethod("exactFullFinalizedBytes");}catch(NoSuchMethodException old){return null;}}
    private static byte[] finalized(NativeQuote quote,Trace t){
        if(GETTER!=null)try{Object value=GETTER.invoke(quote);check(value instanceof Optional<?>,"actual Optional<byte[]> API");var item=(Optional<?>)value;
            if(item.isPresent()){check(item.orElseThrow() instanceof byte[],"cache bytes");t.cached=true;return (byte[])item.orElseThrow();}
        }catch(ReflectiveOperationException failure){throw new IllegalStateException("actual cache accessor failed",failure);}
        return ConstructionOriginalSource.finalizeQuery(quote.original());
    }
    private static final class Data {
        final byte[] q1,q2,small;final ActionCommand prototype;final JsonNode expected;
        Data(Path root)throws IOException {
            q1=Files.readAllBytes(root.resolve("input-q1.json"));q2=Files.readAllBytes(root.resolve("input-q2.json"));small=Files.readAllBytes(root.resolve("input-small.json"));
            byte[] raw=Files.readAllBytes(root.resolve("prototype-command.json"));prototype=ActionCodec.decodeCommand(raw);check(Arrays.equals(raw,ActionCodec.encodeCommand(prototype)),"prototype canonical exact");
            expected=Files.exists(root.resolve("EXPECTED.json"))?FullJsonTree.parse(Files.readAllBytes(root.resolve("EXPECTED.json")),1_048_576):null;
            JsonNode data=FullJsonTree.parse(Files.readAllBytes(root.resolve("DATA.json")),1_048_576);
            check(data.get("q1_sha256").textValue().equals(ActionCodec.sha256(q1))&&data.get("q2_sha256").textValue().equals(ActionCodec.sha256(q2))
                    &&data.get("small_sha256").textValue().equals(ActionCodec.sha256(small))&&data.get("prototype_sha256").textValue().equals(ActionCodec.sha256(raw)),"fixed PREP input hashes");
        }
    }
    private static final class Environment implements AutoCloseable {
        final Path root;final StorageWriteGuardTestSupport guard;final ContinuityWriter writer;final NativeOutcomeArchive archive;final List<String> cards;
        Environment(Path root,ActionCommand prototype)throws IOException {
            this.root=root;var oldCards=cardNames(root);Path snapshot=root.resolve("ROOT-CONTINUITY-WINDOW.json");var layout=new Layout(snapshot,exact(root.resolve("anchor.json")),prototype.source().machineId());
            guard=StorageWriteGuardTestSupport.create(root,layout.lock(),BUDGET);
            var store=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("objects"),layout.lock(),BUDGET),guard);
            writer=new ContinuityWriter(layout,List.of(prototype.source().sourceRef()),new TransitionAuthority(){
                public String revalidate(ContinuityState state,Request request){throw new AssertionError("DATA consumer never publishes actions/domain events");}
                public ContinuityState reduce(ContinuityState state,Request request){throw new AssertionError("DATA consumer never mutates continuity");}
            },Clock.systemUTC(),new ContinuityWriter.Extensions(List.of(),Optional.of(store),Optional.empty()),guard);
            archive=new NativeOutcomeArchive(store,writer);cards=new ArrayList<>(cardNames(root));cards.removeAll(oldCards);
            check(cards.size()==1,"record distinct per-process software allocation card, not identical whole filesystem");
        }
        public void close()throws IOException{guard.close();}
    }
    private record Point(long wall,Long cpu,Long alloc) { }
    private record Metric(long wall_ns,Long cpu_ns,Long thread_allocated_bytes) { }
    private static Point point(){long id=Thread.currentThread().threadId();return new Point(System.nanoTime(),CPU.isCurrentThreadCpuTimeSupported()?CPU.getCurrentThreadCpuTime():null,
            ALLOC!=null&&ALLOC.isThreadAllocatedMemorySupported()&&ALLOC.isThreadAllocatedMemoryEnabled()?ALLOC.getThreadAllocatedBytes(id):null);}
    private static Metric delta(Point a,Point b){return new Metric(b.wall-a.wall,a.cpu==null||b.cpu==null?null:b.cpu-a.cpu,a.alloc==null||b.alloc==null?null:b.alloc-a.alloc);}
    private static void enableMetrics(){if(CPU.isThreadCpuTimeSupported()&&!CPU.isThreadCpuTimeEnabled())CPU.setThreadCpuTimeEnabled(true);
        if(ALLOC!=null&&ALLOC.isThreadAllocatedMemorySupported()&&!ALLOC.isThreadAllocatedMemoryEnabled())ALLOC.setThreadAllocatedMemoryEnabled(true);}
    private static final class Trace {
        final String kind;final int index;final Map<String,Metric> phases=new LinkedHashMap<>();final Map<String,String> markers=new LinkedHashMap<>();
        Metric whole;Point callStart,innerEnd;boolean cached,casExisted;String failure;
        Trace(String kind,int index){this.kind=kind;this.index=index;}
        Point phase(String name,Point previous){Point now=point();phases.put(name,delta(previous,now));return now;}
        Map<String,Object> map(){var row=new LinkedHashMap<String,Object>();row.put("kind",kind);row.put("index",index);row.put("whole",whole);row.put("phases",phases);
            row.put("markers",markers);row.put("cache_api_used",cached);row.put("cas_existed_before_preserve",casExisted);row.put("failure",failure);return row;}
    }
    private static ObjectNode query(ObjectNode input){return (ObjectNode)input.get("quoted_outlay").get("query_observation");}
    private static JsonNode pureHistory139()throws Exception {
        Class<?> type=Class.forName("org.xar.ck3.control.wave3.development.wartimesequencing.ConstructionFullOriginal113SdkTest");
        var method=type.getDeclaredMethod("retainedHistory139");method.setAccessible(true);return (JsonNode)method.invoke(null);
    }
    private static byte[] initial(ActionCommand prototype){
        var state=StrictJson.object();state.put("schema","root.ck3.continuity-window/v1").put("machine_id",prototype.source().machineId()).put("sequence",0).put("window_id",1).put("status","running")
                .put("target_days",10958).put("target_years",30).put("calendar_year_days",365.25).put("start_date_raw",1000).put("target_date_raw",263992)
                .put("last_settled_date_raw",1000).put("last_settled_cycles",1).put("manual_repair_count",1).put("automatic_recovery_count",0).put("binding_lineage_count",0).put("NEXT",2);
        state.putObject("game_binding").put("pid",123).put("creation_date","2026-10-23T01:00:00Z");state.putNull("latest_binding");state.putObject("pending_cycle").put("stage","auto_unsettled").put("auto_sequence",1);
        return ContinuityJson.canonical(state);
    }
    private static List<String> cardNames(Path root)throws IOException {try(var files=Files.list(root)){return files.filter(p->p.getFileName().toString().startsWith("software-storage-card-")).map(p->p.toAbsolutePath().normalize().toString()).sorted().toList();}}
    private static void exactFile(ExactRef ref)throws IOException {byte[] raw=Files.readAllBytes(Path.of(ref.path()));check(raw.length==ref.bytes()&&ActionCodec.sha256(raw).equals(ref.sha256()),"actual metadata source file exact bytes");}
    private static ExactRef exact(Path path)throws IOException{byte[] raw=Files.readAllBytes(path);return new ExactRef(path.toAbsolutePath().normalize().toString(),raw.length,ActionCodec.sha256(raw));}
    private static void write(Path root,String name,byte[] bytes)throws IOException{Files.write(root.resolve(name),bytes,StandardOpenOption.CREATE_NEW);}
    private static void check(boolean value,String why){if(!value)throw new IllegalArgumentException(why);}
}
