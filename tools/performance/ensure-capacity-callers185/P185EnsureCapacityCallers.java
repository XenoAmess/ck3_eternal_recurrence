import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import jdk.jfr.consumer.RecordedClass;
import jdk.jfr.consumer.RecordedEvent;
import jdk.jfr.consumer.RecordedFrame;
import jdk.jfr.consumer.RecordedMethod;
import jdk.jfr.consumer.RecordedStackTrace;
import jdk.jfr.consumer.RecordedThread;
import jdk.jfr.consumer.RecordingFile;

/** One fixed successful raw, complete EOF, exact leaf filter; no app CP, source attribution or live operation. */
public final class P185EnsureCapacityCallers {
    private static final Path INPUT=Path.of("D:/ck3-state/resume91-native-integration/p182-current-integration-profile01/raw/current-integration182.jfr");
    private static final long INPUT_BYTES=8_340_560L,EXPECTED_EVENTS=26_253L;
    private static final String INPUT_SHA="442632bf590a2c79bc473dbb7f2d0ddc8e9e81ff9ad56dada7159790d3fe1d0f";
    private static final String CLASS="java.lang.AbstractStringBuilder",METHOD="ensureCapacityInternal",DESCRIPTOR="(I)V";
    private static final int MAX_SAMPLES=64,MAX_FRAMES=64,MAX_METADATA_CHARS=4096,MAX_EVENT_TYPES=128,MAX_OUTPUT_BYTES=1_048_576;
    private static final long EXPECTED_MATCHES=41;

    public static void main(String[] args)throws Exception {
        if(args.length!=2)throw new IllegalArgumentException("exact input and new output paths required");
        Path input=Path.of(args[0]).toRealPath();require(input.equals(INPUT.toRealPath()),"only the fixed successful P182 input is allowed");
        Path requested=Path.of(args[1]).toAbsolutePath().normalize(),parent=requested.getParent();require(parent!=null,"existing output parent required");
        Path output=parent.toRealPath().resolve(requested.getFileName());require(!output.equals(input),"output must differ from input");require(!Files.exists(output,LinkOption.NOFOLLOW_LINKS),"CREATE_NEW output must not exist");
        long started=System.nanoTime();Instant toolStarted=Instant.now();BasicFileAttributes before=Files.readAttributes(input,BasicFileAttributes.class,LinkOption.NOFOLLOW_LINKS);require(before.isRegularFile()&&before.size()==INPUT_BYTES,"fixed regular input size required");String shaBefore=sha(input);require(INPUT_SHA.equals(shaBefore),"fixed input SHA mismatch");
        var types=new TreeMap<String,Long>();var samples=new ArrayList<Map<String,Object>>();long total=0,execution=0,missingStack=0,emptyStack=0,unknownLeaf=0,missingSampledThread=0,targetLeafSeen=0,targetMissingThread=0,sameNameOtherDescriptor=0;boolean EOF=false;
        try(RecordingFile file=new RecordingFile(input)) {
            while(file.hasMoreEvents()) {
                RecordedEvent event=file.readEvent();total=Math.addExact(total,1);String type=bounded(event.getEventType().getName(),"event type",512);require(type!=null,"event type missing");if(!types.containsKey(type))require(types.size()<MAX_EVENT_TYPES,"event type cap exceeded");types.put(type,Math.addExact(types.getOrDefault(type,0L),1));
                if(!type.equals("jdk.ExecutionSample"))continue;execution=Math.addExact(execution,1);
                Object threadField=event.hasField("sampledThread")?event.getValue("sampledThread"):null;RecordedThread thread=threadField instanceof RecordedThread held?held:null;if(thread==null)missingSampledThread=Math.addExact(missingSampledThread,1);
                RecordedStackTrace trace=event.getStackTrace();if(trace==null){missingStack=Math.addExact(missingStack,1);continue;}List<RecordedFrame> frames=trace.getFrames();if(frames.isEmpty()){emptyStack=Math.addExact(emptyStack,1);continue;}
                RecordedFrame leaf=frames.getFirst();RecordedMethod method=leaf==null?null:leaf.getMethod();RecordedClass owner=method==null?null:method.getType();String ownerName=owner==null?null:owner.getName(),name=method==null?null:method.getName(),descriptor=method==null?null:method.getDescriptor();
                if(ownerName==null||name==null||descriptor==null){unknownLeaf=Math.addExact(unknownLeaf,1);continue;}
                if(!CLASS.equals(ownerName)||!METHOD.equals(name))continue;if(!DESCRIPTOR.equals(descriptor)){sameNameOtherDescriptor=Math.addExact(sameNameOtherDescriptor,1);continue;}
                targetLeafSeen=Math.addExact(targetLeafSeen,1);if(thread==null){targetMissingThread=Math.addExact(targetMissingThread,1);continue;}
                require(samples.size()<MAX_SAMPLES,"matched sample cap exceeded; no successful truncation");require(frames.size()<=MAX_FRAMES,"matched recorded frame cap exceeded; no successful truncation");
                var row=new LinkedHashMap<String,Object>();row.put("match_index",samples.size());row.put("event_ordinal_1based",total);row.put("event_type",type);row.put("start",text(event.getStartTime()));row.put("end",text(event.getEndTime()));row.put("duration_ns",event.getDuration().toNanos());row.put("sampled_thread",thread(thread));row.put("state",state(event));row.put("recorded_truncated",trace.isTruncated());row.put("recorded_frame_count",frames.size());
                var chain=new ArrayList<List<Object>>(frames.size());for(RecordedFrame frame:frames)chain.add(frame(frame));row.put("frames",chain);samples.add(row);
            }
            EOF=true;
        }
        BasicFileAttributes after=Files.readAttributes(input,BasicFileAttributes.class,LinkOption.NOFOLLOW_LINKS);String shaAfter=sha(input);require(after.isRegularFile()&&after.size()==INPUT_BYTES&&before.size()==after.size()&&before.lastModifiedTime().equals(after.lastModifiedTime())&&INPUT_SHA.equals(shaAfter)&&shaBefore.equals(shaAfter),"input size/modified/SHA drift");
        long typeSum=0;for(long count:types.values())typeSum=Math.addExact(typeSum,count);require(EOF&&total==typeSum&&total==EXPECTED_EVENTS,"EOF total/type partition differs from original26253");
        require(types.equals(expectedTypes()),"observed event type counts differ from the successful original report");require(execution==752,"ExecutionSample total differs from original752");
        require(targetLeafSeen==EXPECTED_MATCHES&&samples.size()==EXPECTED_MATCHES&&targetMissingThread==0,"post-EOF target41/thread reconciliation failed: seen="+targetLeafSeen+",retained="+samples.size()+",missingThread="+targetMissingThread);
        var report=new LinkedHashMap<String,Object>();report.put("schema","ck3.p185.fixed-ensureCapacity-execution-callers/v1");report.put("completed",true);report.put("read_to_EOF",EOF);report.put("tool_started_utc",toolStarted.toString());report.put("input",input.toString());report.put("input_bytes_before",before.size());report.put("input_bytes_after",after.size());report.put("input_modified_before",before.lastModifiedTime().toString());report.put("input_modified_after",after.lastModifiedTime().toString());report.put("input_sha256_before",shaBefore);report.put("input_sha256_after",shaAfter);report.put("input_unchanged",true);report.put("retained_OS_handle_identity_proof",false);
        report.put("all_events",total);report.put("event_type_counts",types);report.put("event_type_sum",typeSum);report.put("original_event_count_crosscheck",EXPECTED_EVENTS);report.put("execution_samples",execution);report.put("execution_missing_stack",missingStack);report.put("execution_empty_stack",emptyStack);report.put("execution_unknown_leaf_metadata",unknownLeaf);report.put("execution_missing_sampledThread",missingSampledThread);report.put("target_leaf_seen",targetLeafSeen);report.put("target_missing_sampledThread",targetMissingThread);report.put("same_class_name_other_descriptor",sameNameOtherDescriptor);report.put("target_matches",samples.size());report.put("target_expected_postcheck",EXPECTED_MATCHES);
        report.put("filter",List.of("jdk.ExecutionSample",CLASS,METHOD,DESCRIPTOR,"actual sampledThread and stack required; original frame zero is leaf"));report.put("frame_columns",List.of("class_jfr_id","class","method","descriptor","line","BCI","frame_type","java_frame","hidden_method"));report.put("frame_values","One ordered array per original recorded frame, leaf first. Null frame/metadata explicitnull; negative line/BCI preserved as original unknown values. No frame dropped, dictionary substitution, root reconstruction or classification.");report.put("samples",samples);
        report.put("caps",Map.of("samples",MAX_SAMPLES,"recorded_frames_per_sample",MAX_FRAMES,"each_metadata_chars",MAX_METADATA_CHARS,"event_types",MAX_EVENT_TYPES,"output_bytes",MAX_OUTPUT_BYTES));report.put("limits","Recorded-truncated is original JFR status, never a complete logical root. Count is not CPU time/call count/frequency. FQName/classJFRid is not loaded class SHA or source authority. SHA/size/modified checks are not retained OS HANDLE identity. This only re-reads the successful P182 raw; no new recording/app/Main/SDK/Test/Runtime/Game/P100 operation. Allcaps fail, never partial success; unexpected41/typecounts fail after EOF, never filter to fit expected counts.");report.put("main_before_report_ns",System.nanoTime()-started);
        StringBuilder json=new StringBuilder(65_536);json(report,json,0);byte[] bytes=json.toString().getBytes(StandardCharsets.UTF_8);require(bytes.length<=MAX_OUTPUT_BYTES,"output byte cap exceeded");Files.write(output,bytes,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);System.out.println("P185 PASS EOF events="+total+" target="+samples.size()+" outputBytes="+bytes.length);
    }

    private static Map<String,Long> expectedTypes() {
        var out=new TreeMap<String,Long>();out.put("jdk.ActiveRecording",1L);out.put("jdk.ActiveSetting",372L);out.put("jdk.Compilation",6L);out.put("jdk.ExecutionSample",752L);out.put("jdk.GCPhasePause",485L);out.put("jdk.GarbageCollection",485L);out.put("jdk.NativeMethodSample",4325L);out.put("jdk.ObjectAllocationSample",19817L);out.put("org.junit.EngineDiscovery",3L);out.put("org.junit.LauncherDiscovery",1L);out.put("org.junit.TestExecution",5L);out.put("org.junit.TestPlanExecution",1L);return out;
    }
    private static Map<String,Object> thread(RecordedThread thread)throws IOException {
        var out=new LinkedHashMap<String,Object>();out.put("source_field","sampledThread");out.put("jfr_id",thread.getId());out.put("java_thread_id",thread.getJavaThreadId());out.put("OS_thread_id",thread.getOSThreadId());out.put("java_name",bounded(thread.getJavaName(),"Java thread name",MAX_METADATA_CHARS));out.put("OS_name",bounded(thread.getOSName(),"OS thread name",MAX_METADATA_CHARS));out.put("virtual",thread.isVirtual());return out;
    }
    private static Map<String,Object> state(RecordedEvent event)throws IOException {
        boolean present=event.hasField("state");Object value=present?event.getValue("state"):null;boolean scalar=value instanceof String||value instanceof Byte||value instanceof Short||value instanceof Integer||value instanceof Long;
        if(value instanceof String text)bounded(text,"sample state",MAX_METADATA_CHARS);var out=new LinkedHashMap<String,Object>();out.put("field_present",present);out.put("available",scalar);out.put("original_value",scalar?value:null);out.put("raw_java_type",value==null?null:bounded(value.getClass().getName(),"state type",MAX_METADATA_CHARS));out.put("unknown_reason",scalar?null:(!present?"missing_state_field":"null_or_non_scalar_state"));return out;
    }
    private static List<Object> frame(RecordedFrame frame)throws IOException {
        if(frame==null)return Arrays.asList(null,null,null,null,null,null,null,null,null);RecordedMethod method=frame.getMethod();RecordedClass owner=method==null?null:method.getType();
        return Arrays.asList(owner==null?null:owner.getId(),bounded(owner==null?null:owner.getName(),"frame class",MAX_METADATA_CHARS),bounded(method==null?null:method.getName(),"frame method",MAX_METADATA_CHARS),bounded(method==null?null:method.getDescriptor(),"frame descriptor",MAX_METADATA_CHARS),frame.getLineNumber(),frame.getBytecodeIndex(),bounded(frame.getType(),"frame type",MAX_METADATA_CHARS),frame.isJavaFrame(),method==null?null:method.isHidden());
    }
    private static String text(Instant value)throws IOException{return value==null?null:bounded(value.toString(),"event timestamp",128);}
    private static String bounded(String value,String role,int maximum)throws IOException {require(value==null||value.length()<=maximum,role+" metadata cap exceeded");return value;}
    private static String sha(Path input)throws Exception {MessageDigest digest=MessageDigest.getInstance("SHA-256");try(InputStream stream=Files.newInputStream(input)){byte[] buffer=new byte[65_536];int count;while((count=stream.read(buffer))!=-1)digest.update(buffer,0,count);}return HexFormat.of().formatHex(digest.digest());}
    private static void require(boolean value,String message)throws IOException {if(!value)throw new IOException(message);}
    private static void json(Object value,StringBuilder out,int depth)throws IOException {
        require(depth<=16,"JSON nesting cap exceeded");if(value==null)out.append("null");else if(value instanceof String text)quote(text,out);else if(value instanceof Boolean||value instanceof Byte||value instanceof Short||value instanceof Integer||value instanceof Long)out.append(value);
        else if(value instanceof Map<?,?> map){out.append('{');boolean comma=false;for(var entry:map.entrySet()){if(comma)out.append(',');require(entry.getKey() instanceof String,"JSON string key required");quote((String)entry.getKey(),out);out.append(':');json(entry.getValue(),out,depth+1);comma=true;}out.append('}');}
        else if(value instanceof List<?> list){out.append('[');boolean comma=false;for(Object item:list){if(comma)out.append(',');json(item,out,depth+1);comma=true;}out.append(']');}
        else throw new IOException("unsupported explicit JSON field type");require(out.length()<=MAX_OUTPUT_BYTES,"ASCII JSON output cap exceeded");
    }
    private static void quote(String text,StringBuilder out)throws IOException {
        require(text.length()<=MAX_METADATA_CHARS,"JSON string metadata cap exceeded");String hex="0123456789abcdef";out.append('"');for(int i=0;i<text.length();i++){char c=text.charAt(i);if(c=='"')out.append("\\\"");else if(c=='\\')out.append("\\\\");else if(c>=32&&c<=126)out.append(c);else{out.append("\\u");for(int shift=12;shift>=0;shift-=4)out.append(hex.charAt((c>>>shift)&15));}require(out.length()<=MAX_OUTPUT_BYTES,"ASCII JSON output cap exceeded");}out.append('"');
    }
}
