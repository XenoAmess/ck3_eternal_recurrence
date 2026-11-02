import java.nio.file.Path;
import java.time.Instant;
import java.time.Duration;
import java.util.*;
import jdk.jfr.consumer.*;

/** Offline, bounded summary of one already closed recording. Never attaches to a JVM. */
public final class AnalyzeRecording276V2 {
    private static final Map<String,Long> counts=new TreeMap<>(),leaf=new HashMap<>(),inclusive=new HashMap<>(),stacks=new HashMap<>(),threads=new HashMap<>(),states=new HashMap<>();
    private static final Map<String,Long> allocations=new HashMap<>(),ioStacks=new HashMap<>(),waitStacks=new HashMap<>();
    private static final Map<String,DurationStat> durations=new TreeMap<>();
    private static final Map<String,NumberStat> numbers=new TreeMap<>();
    private static final Map<String,Map<String,Long>> buckets=new TreeMap<>();
    private static final Map<String,List<String>> fields=new TreeMap<>();
    private static final List<Object> config=new ArrayList<>(),gc=new ArrayList<>();
    private static Instant first,last;
    private static long read;
    private static final Map<String,Map<String,Long>> typedLeaves=new TreeMap<>(),typedInclusive=new TreeMap<>(),typedCategories=new TreeMap<>();
    private static final Map<String,Map<String,Long>> windowSamples=new TreeMap<>();
    private static final Map<String,Map<String,Object>> windowDurations=new TreeMap<>();
    private static final Map<Long,String> eventNames=new HashMap<>();
    private static final List<Map<String,Object>> settings=new ArrayList<>();
    private static long truncatedStacks;
    private static String window(Instant t) {
        if(t.isBefore(Instant.parse("2026-11-01T23:00:58.726077700Z")))return "pre_LOOP";
        if(t.isBefore(Instant.parse("2026-11-01T23:01:49.351855800Z")))return "first_SAVE_and_boundaries";
        if(t.isBefore(Instant.parse("2026-11-01T23:03:07.880677400Z")))return "batch6_before_HTTP_start_not_exact_PLANNING";
        if(t.isBefore(Instant.parse("2026-11-01T23:03:16.419677400Z")))return "HTTP_reported_interval_derived_end";
        return "after_HTTP_to_recording_end";
    }
    private static String category(List<String> s) {
        if(s.isEmpty())return "no_stack";String leaf=s.getFirst();String all=String.join(" ",s);
        if(all.contains("HttpClientImpl$SelectorManager"))return "http_selector_wait";
        if(all.contains("jdk.jfr.internal.periodic"))return "jfr_periodic";
        if(leaf.contains("force0"))return "native_file_force";
        if(all.contains("IdentityBearingFileAttributes")&&(leaf.contains("Native.")||leaf.contains("Dispatcher")))return "native_file_identity_or_metadata";
        if(leaf.contains(".read0")||leaf.contains(".ReadFile"))return "native_file_read";
        if(leaf.startsWith("com.fasterxml.jackson.")||leaf.contains("ContinuityJson")||leaf.contains("FullJsonTree")||leaf.contains("DriverJson"))return "java_JSON_leaf";
        return "other";
    }

    private AnalyzeRecording276V2() { }
    private static void inc(Map<String,Long> map,String key,long value) { map.merge(key,value,Long::sum); }
    private static String method(RecordedFrame f) {
        var m=f.getMethod();return m==null?"<unknown>":m.getType().getName()+"."+m.getName();
    }
    private static List<String> stack(RecordedEvent e) {
        var s=e.getStackTrace();if(s==null)return List.of();
        var out=new ArrayList<String>();for(var f:s.getFrames()) {if(out.size()==64)break;out.add(method(f));}return out;
    }
    private static String signature(List<String> s) {return String.join(" <- ",s.subList(0,Math.min(24,s.size())));}
    private static String thread(RecordedEvent e) {
        RecordedThread t=e.hasField("sampledThread")?e.getThread("sampledThread"):e.getThread();
        return t==null?"<none>":t.getJavaName()+"#"+t.getJavaThreadId();
    }
    private static Object optional(RecordedEvent e,String name) {return e.hasField(name)?e.getValue(name):null;}
    private static void number(String name,Object value) {
        if(value instanceof Number n)numbers.computeIfAbsent(name,k->new NumberStat()).add(n.doubleValue());
    }
    private static long longValue(Object value) {return value instanceof Number n?n.longValue():0;}
    private static Map<String,Object> row(Object... vals) {
        var m=new LinkedHashMap<String,Object>();for(int i=0;i<vals.length;i+=2)m.put((String)vals[i],vals[i+1]);return m;
    }
    private static void sample(RecordedEvent e,String name) {
        var s=stack(e);var thread=thread(e);String state=String.valueOf(optional(e,"state"));
        inc(threads,thread,1);inc(states,name+":"+state,1);
        String typed=name+":"+thread;
        if(!s.isEmpty()){
            inc(typedLeaves.computeIfAbsent(typed,k->new HashMap<>()),s.getFirst(),1);
            for(String method:new LinkedHashSet<>(s))inc(typedInclusive.computeIfAbsent(typed,k->new HashMap<>()),method,1);
        }
        inc(typedCategories.computeIfAbsent(typed,k->new TreeMap<>()),category(s),1);
        inc(windowSamples.computeIfAbsent(window(e.getStartTime()),k->new TreeMap<>()),typed+":"+category(s),1);
        if(e.getStackTrace()!=null&&e.getStackTrace().isTruncated())truncatedStacks++;

        if(!s.isEmpty()) {inc(leaf,s.getFirst(),1);inc(stacks,signature(s),1);for(var x:new LinkedHashSet<>(s))inc(inclusive,x,1);}
        long seconds=e.getStartTime().getEpochSecond();
        var bucket=buckets.computeIfAbsent(Instant.ofEpochSecond(seconds-seconds%10).toString(),k->new TreeMap<>());
        inc(bucket,name+":"+thread,1);
        if(!s.isEmpty())for(String x:s)if(x.startsWith("org.xar.")){inc(bucket,"first_application:"+x,1);break;}
    }
    private static void accept(RecordedEvent e) {
        String name=e.getEventType().getName();read++;inc(counts,name,1);
        eventNames.put(e.getEventType().getId(),name);
        if(name.equals("jdk.ActiveSetting"))settings.add(row("id",optional(e,"id"),"name",optional(e,"name"),"value",optional(e,"value")));

        var start=e.getStartTime();var end=e.getEndTime();
        if(first==null||start.isBefore(first))first=start;if(last==null||end.isAfter(last))last=end;
        fields.computeIfAbsent(name,k->e.getEventType().getFields().stream().map(f->f.getName()+":"+f.getTypeName()).toList());
        if(name.equals("jdk.ExecutionSample")||name.equals("jdk.NativeMethodSample"))sample(e,name);
        long nanos=e.getDuration().toNanos();
        if(nanos>0)durations.computeIfAbsent(name,k->new DurationStat()).add(nanos,start,thread(e));
        if(nanos>0&&(name.equals("jdk.FileForce")||name.equals("jdk.ThreadPark")||name.equals("jdk.GarbageCollection")||name.equals("jdk.ThreadSleep"))) {
            String key=window(start)+":"+name+":"+thread(e);
            var stat=windowDurations.computeIfAbsent(key,k->row("count",0L,"duration_nanos_sum",0L));
            stat.put("count",((Long)stat.get("count"))+1L);stat.put("duration_nanos_sum",((Long)stat.get("duration_nanos_sum"))+nanos);
        }

        if(name.equals("jdk.ThreadCPULoad")) {
            number(name+":"+thread(e)+":user",optional(e,"user"));number(name+":"+thread(e)+":system",optional(e,"system"));
        }
        if(name.equals("jdk.CPULoad")) for(String f:List.of("jvmUser","jvmSystem","machineTotal"))number(name+":"+f,optional(e,f));
        if(name.equals("jdk.FileRead")||name.equals("jdk.FileWrite")||name.equals("jdk.FileForce")) {
            var s=stack(e);inc(ioStacks,name+":"+String.valueOf(optional(e,"path"))+":"+signature(s),nanos);
            number(name+":bytesRead",optional(e,"bytesRead"));number(name+":bytesWritten",optional(e,"bytesWritten"));
        }
        if(name.equals("jdk.ThreadPark")||name.equals("jdk.JavaMonitorEnter")||name.equals("jdk.JavaMonitorWait")||name.equals("jdk.ThreadSleep"))
            inc(waitStacks,name+":"+thread(e)+":"+signature(stack(e)),nanos);
        if(name.equals("jdk.ObjectAllocationSample")) {
            inc(allocations,signature(stack(e)),longValue(optional(e,"weight")));
            number(name+":weight",optional(e,"weight"));
        }
        if(name.equals("jdk.ObjectAllocationInNewTLAB")||name.equals("jdk.ObjectAllocationOutsideTLAB")) {
            number(name+":allocationSize",optional(e,"allocationSize"));number(name+":tlabSize",optional(e,"tlabSize"));
        }
        if(name.equals("jdk.GarbageCollection")) {
            var m=row("at",start.toString(),"duration_seconds",nanos/1e9,"cause",optional(e,"cause"),"name",optional(e,"name"),"gcId",optional(e,"gcId"));
            for(String f:List.of("sumOfPauses","longestPause"))if(e.hasField(f))m.put(f+"_seconds",e.getDuration(f).toNanos()/1e9);
            gc.add(m);
        }
        if(name.equals("jdk.ActiveRecording")||name.equals("jdk.JVMInformation")||name.equals("jdk.CPUInformation")||name.equals("jdk.GCConfiguration")||name.equals("jdk.GCHeapConfiguration")) {
            var m=row("event",name,"at",start.toString());for(var f:e.getEventType().getFields())if(!List.of("startTime","duration","eventThread","stackTrace").contains(f.getName()))m.put(f.getName(),String.valueOf(optional(e,f.getName())));
            if(config.size()<50)config.add(m);
        }
    }
    private static List<Object> top(Map<String,Long> m,int n) {
        return m.entrySet().stream().sorted(Map.Entry.<String,Long>comparingByValue().reversed().thenComparing(Map.Entry::getKey)).limit(n)
            .map(e->(Object)row("key",e.getKey(),"value",e.getValue())).toList();
    }
    private static String json(Object value) {
        if(value==null)return "null";if(value instanceof Boolean||value instanceof Number)return value.toString();
        if(value instanceof Map<?,?> m){var items=new ArrayList<String>();for(var e:m.entrySet())items.add(json(e.getKey().toString())+":"+json(e.getValue()));return "{"+String.join(",",items)+"}";}
        if(value instanceof Iterable<?> xs){var items=new ArrayList<String>();for(var x:xs)items.add(json(x));return "["+String.join(",",items)+"]";}
        var s=value.toString();var b=new StringBuilder("\"");for(char c:s.toCharArray())switch(c){case '\\'->b.append("\\\\");case '"'->b.append("\\\"");case '\n'->b.append("\\n");case '\r'->b.append("\\r");case '\t'->b.append("\\t");default->{if(c<32)b.append(String.format("\\u%04x",(int)c));else b.append(c);}}return b.append('"').toString();
    }
    public static void main(String[] args)throws Exception {
        if(args.length!=1)throw new IllegalArgumentException("One closed local recording path required");
        try(var file=new RecordingFile(Path.of(args[0]))) {while(file.hasMoreEvents())accept(file.readEvent());}
        var ds=new TreeMap<String,Object>();durations.forEach((k,v)->ds.put(k,v.result()));
        var ns=new TreeMap<String,Object>();numbers.forEach((k,v)->ns.put(k,v.result()));
        var typedTopLeaves=new TreeMap<String,Object>();typedLeaves.forEach((k,v)->typedTopLeaves.put(k,top(v,60)));
        var typedTopInclusive=new TreeMap<String,Object>();typedInclusive.forEach((k,v)->typedTopInclusive.put(k,top(v,150)));
        var relevantSettings=new ArrayList<Object>();
        for(var setting:settings){var id=setting.get("id");String type=id instanceof Number n?eventNames.get(n.longValue()):null;
            if(type!=null&&List.of("jdk.ExecutionSample","jdk.NativeMethodSample","jdk.FileRead","jdk.FileWrite","jdk.FileForce","jdk.ThreadPark","jdk.GarbageCollection","jdk.ObjectAllocationSample").contains(type))
                relevantSettings.add(row("event_type",type,"setting",setting.get("name"),"value",setting.get("value")));}

        System.out.println(json(row("event_count",read,"first_event_start",first,"last_event_end",last,
          "typed_sample_leaf_top60",typedTopLeaves,"typed_sample_inclusive_top150",typedTopInclusive,
          "typed_sample_exclusive_categories",typedCategories,"window_samples",windowSamples,
          "window_duration_events_by_start_not_clipped",windowDurations,"sample_truncated_stack_count",truncatedStacks,
          "relevant_actual_settings",relevantSettings,

          "event_extent_seconds",first==null?null:Duration.between(first,last).toNanos()/1e9,
          "counts",counts,"event_fields",fields,"sample_leaf_top100",top(leaf,100),"sample_inclusive_top150",top(inclusive,150),
          "sample_stacks_top80",top(stacks,80),"sample_threads",threads,"sample_states",states,"samples_10s",buckets,
          "durations",ds,"numeric_fields",ns,"IO_stacks_top40_nanos",top(ioStacks,40),"wait_stacks_top40_nanos",top(waitStacks,40),
          "allocation_sample_top50_weighted_bytes",top(allocations,50),"GC_events",gc,"recorded_configuration",config,
          "limits",List.of("Execution samples and allocation sample weights are sampled estimates, not exact method wall time or exact allocation totals.",
           "Duration sums across threads/types can overlap; GC and pause phase events must not be added together.",
           "First/last event extent is not the recording header interval, nor the full worker/report interval.",
           "No attachment, live process query, Game access, raw-event export, source modification or deployment."))));
    }
    private static final class DurationStat {
        long count,total,max;Instant at;String thread;
        void add(long n,Instant a,String t){count++;total=Math.addExact(total,n);if(n>max){max=n;at=a;thread=t;}}
        Map<String,Object> result(){return row("count",count,"sum_seconds",total/1e9,"max_seconds",max/1e9,"max_at",at,"max_thread",thread);}
    }
    private static final class NumberStat {
        long count;double sum,max=-Double.MAX_VALUE,min=Double.MAX_VALUE;
        void add(double n){count++;sum+=n;max=Math.max(max,n);min=Math.min(min,n);}
        Map<String,Object> result(){return row("count",count,"sum",sum,"mean",sum/count,"min",min,"max",max);}
    }
}
