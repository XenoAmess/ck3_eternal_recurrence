package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.InputStream;
import java.lang.instrument.Instrumentation;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.nio.channels.FileChannel;
import java.nio.channels.FileLock;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.concurrent.atomic.AtomicBoolean;

/** Explicit administrative release of a failed business graph; never closes its Game owner. */
public final class RootAwaitingOwnerStorageHandoffAgent {
    public static final String SCHEMA="xar.ck3.awaiting-owner-storage-handoff/v1";
    private static final String PREFIX="org.xar.ck3.control.";
    private static final String CORE=PREFIX+"service.root.RootApplicationAssembly$Core";
    private static final String GUARD=PREFIX+"service.root.RootRuntimeStorageGuard";
    private static final String PREPARED=PREFIX+"service.root.RootOrdinaryRuntimeAssembly$Prepared";
    private static final String MAIN=PREFIX+"service.root.RootOrdinaryWorkerMain";
    private static final String WRITER=PREFIX+"continuity.writer.ContinuityWriter";
    private static final String WINDOWS=PREFIX+"build.WindowsJobProcess";
    private static final String HARNESS=PREFIX+"service.root.SavedOwnerBusinessStorageHandoffHarness";
    private static final List<String> COMMON_CLASSES=List.of(CORE,GUARD,WRITER,WINDOWS,"com.sun.jna.Native");
    private static final List<String> LIVE_CLASSES=List.of(PREPARED,MAIN,PREFIX+"platform.SavedGameOwnerLifetime249$Retained");
    private static final AtomicBoolean USED=new AtomicBoolean();
    private static native Object[] findInstances(Class<?>[] exactClasses,int maximum);
    private RootAwaitingOwnerStorageHandoffAgent() { }

    /** JVM invokes this once through the standard Attach agent path. Options bind immutable grant bytes. */
    public static void agentmain(String options,Instrumentation instrumentation)throws Exception {
        if(!USED.compareAndSet(false,true))throw new IOException("administrative agent is single-use in this JVM");
        String[] args=options.split("\\|",-1);
        require(args.length==3,"grant path/bytes/SHA options required");
        Path grantPath=absolute(args[0]);
        byte[] raw=readExact(grantPath,decimal(args[1]),args[2],65536);
        Map<String,String> grant=parse(raw);
        validateKeys(grant);
        Map<String,String> result=new TreeMap<>();
        result.put("schema",SCHEMA+"-result");result.put("operation_id",value(grant,"operation_id"));
        result.put("target_pid",Long.toString(ProcessHandle.current().pid()));
        result.put("grant_sha256",sha256(raw));result.put("close_called","0");
        result.put("status","REJECTED_NO_CLOSE");
        Path output=absolute(value(grant,"output"));
        require(!Files.exists(output,LinkOption.NOFOLLOW_LINKS)&&Files.isDirectory(output.getParent()),"fresh existing output parent required");
        try {
            execute(grant,instrumentation,result);
        }catch(Exception failure){
            result.put("error_class",failure.getClass().getName());
            result.put("error",String.valueOf(failure.getMessage()).replace('\n',' ').replace('\r',' '));
            if("1".equals(result.get("close_called")))result.put("status","CLOSE_ATTEMPTED_POSTCHECK_FAILED");
            throw failure;
        }finally{
            result.put("close_invocations",result.get("close_called"));
            writeProperties(output,result);
        }
    }

    private static void execute(Map<String,String> g,Instrumentation inst,Map<String,String> result)throws Exception {
        fresh(g);boolean live=live(g);
        require(Long.toString(ProcessHandle.current().pid()).equals(value(g,"target_pid")),"different target JVM");
        require(System.getProperty("java.home").equals(value(g,"java_home"))
                &&System.getProperty("java.runtime.version").equals(value(g,"java_runtime_version")),"different JDK runtime");
        Path ownJar=Path.of(RootAwaitingOwnerStorageHandoffAgent.class.getProtectionDomain().getCodeSource().getLocation().toURI());
        require(ownJar.equals(absolute(value(g,"agent.path"))),"agent CodeSource differs from its exact jar");
        verifyRef(g,"agent",2L<<20);verifyRef(g,"bridge",2L<<20);verifyRef(g,"ready",1L<<20);
        Map<String,Class<?>> classes=new LinkedHashMap<>();
        for(String name:classNames(live)) {
            List<Class<?>> found=new ArrayList<>();
            for(Class<?> type:inst.getAllLoadedClasses())if(type.getName().equals(name))found.add(type);
            require(found.size()==1,"missing or ambiguous already-loaded class: "+name);
            Class<?> type=found.getFirst();verifyClass(g,type);classes.put(name,type);
        }
        ClassLoader loader=classes.get(CORE).getClassLoader();
        for(Class<?> type:classes.values())require(type.getClassLoader()==loader,"different application class loader");
        Object identity=classes.get(WINDOWS).getMethod("exactProcess",long.class).invoke(null,ProcessHandle.current().pid());
        require(value(g,"target_birth_filetime").equals(call(identity,"creationFiletimeDecimal")),"target birth differs");
        require(Path.of((String)call(identity,"executable")).equals(absolute(value(g,"java_executable"))),"target executable differs");
        // Read the original registry first. Its absence is unknown, never evidence that ownership ended.
        Map<?,?> registry=(Map<?,?>)field(null,classes.get(GUARD),"OWNERS");
        synchronized(registry){result.put("registry_writer_count",Integer.toString(registry.size()));}
        System.load(absolute(value(g,"bridge.path")).toString());
        Class<?>[] targets=live?new Class<?>[]{classes.get(CORE),classes.get(PREPARED)}:new Class<?>[]{classes.get(CORE)};
        Object[] instances=findInstances(targets,32);
        List<Object> candidates=new ArrayList<>();
        for(Object object:instances)if(object.getClass()==classes.get(CORE)) {
            Object writer=call(object,"writer"),possibleGuard=call(object,"storageGuard");
            if(absolute(value(g,"writer_lock")).equals(call(writer,"originalLockPath"))
                    &&possibleGuard.getClass()==classes.get(GUARD)
                    &&Boolean.FALSE.equals(field(possibleGuard,"closed"))
                    &&absolute(value(g,"allocation_lock")).equals(field(possibleGuard,"allocationLockPath")))candidates.add(object);
        }
        require(candidates.size()==1,"exactly one actual Core for the original writer is required");
        Object core=candidates.getFirst(),writer=call(core,"writer"),guard=call(core,"storageGuard");
        require(guard.getClass()==classes.get(GUARD)&&writer.getClass()==classes.get(WRITER),"unexpected Core writer/guard identity");
        Object prepared=null;
        if(live) {
            List<Object> matching=new ArrayList<>();
            for(Object object:instances)if(object.getClass()==classes.get(PREPARED)&&field(object,"core")==core)matching.add(object);
            require(matching.size()==1,"exactly one original Prepared must retain this Core");prepared=matching.getFirst();
            verifyPrepared(g,prepared,core,guard);awaitingOwner();
        } else rehearsalThread();
        result.put("core_identity",Integer.toUnsignedString(System.identityHashCode(core)));
        result.put("guard_identity",Integer.toUnsignedString(System.identityHashCode(guard)));
        Method locked=Arrays.stream(writer.getClass().getMethods()).filter(m->m.getName().equals("locked")&&m.getParameterCount()==1).findFirst().orElseThrow();
        Class<?> workType=locked.getParameterTypes()[0];Object retainedPrepared=prepared;
        Object work=Proxy.newProxyInstance(workType.getClassLoader(),new Class<?>[]{workType},(proxy,method,args)->{
            if(method.getDeclaringClass()==Object.class)return switch(method.getName()){
                case "toString"->"source-bound administrative close";
                case "hashCode"->System.identityHashCode(proxy);
                case "equals"->proxy==args[0];default->throw new IOException("unexpected Object method");};
            require(method.getName().equals("run")&&args!=null&&args.length==1,"unexpected writer callback");
            fresh(g);for(String ref:List.of("ready","agent","bridge"))verifyRef(g,ref,2L<<20);
            if(live){verifyPrepared(g,retainedPrepared,core,guard);awaitingOwner();verifyLiveRefs(g);}else rehearsalThread();
            verifyGuard(g,writer,guard,false);
            Object head=call(args[0],"head");verifyHead(g,head);result.put("before_digest",(String)call(head,"digest"));
            // All rejection paths above leave the original guard open. The only application mutation follows.
            fresh(g);result.put("close_called","1");call(guard,"close");
            verifyGuard(g,writer,guard,true);verifyHead(g,call(args[0],"head"));
            if(live){verifyLiveRefs(g);verifyPrepared(g,retainedPrepared,core,guard);awaitingOwner();}
            result.put("after_digest",value(g,"expected_digest"));result.put("status","GUARD_RELEASED_OWNER_RETAINED");return null;
        });
        invoke(locked,writer,work);
    }

    private static void verifyPrepared(Map<String,String> g,Object prepared,Object core,Object guard)throws Exception {
        require(field(prepared,"core")==core&&field(prepared,"storage")==guard
                &&Boolean.FALSE.equals(field(prepared,"closed"))&&field(prepared,"game")==null,
                "original Prepared is closed, adopted or bound to another business graph");
        require(Boolean.FALSE.equals(field(core,"resourcesClosed"))&&Boolean.FALSE.equals(field(core,"requestsClosed")),
                "original Core has begun another close path");
        Object retained=field(prepared,"exitedOwnerLifetime"),started=field(prepared,"exitedOwnerStart");
        require(retained!=null&&started!=null&&field(retained,"original")==started
                &&field(retained,"creator")==field(prepared,"lifecycle")&&Boolean.TRUE.equals(field(retained,"awaited")),
                "original creator and retained lifetime are not in their real owner wait");
        Path directory=(Path)field(prepared,"exitedOwnerDirectory");
        require(directory!=null&&directory.equals(field(retained,"directory"))
                &&directory.resolve("owner.json").equals(absolute(value(g,"owner.path"))),"different original owner directory");
        Object game=call(started,"session"),generation=call(game,"generation");
        require("OWNED".equals(call(game,"mode").toString())
                &&value(g,"game_pid").equals(call(generation,"pid").toString())
                &&value(g,"game_birth_filetime").equals(call(call(generation,"creationFiletime"),"value").toString()),
                "different original owned Game; no adoption or ownership transfer permitted");
    }

    private static void verifyGuard(Map<String,String> g,Object writer,Object guard,boolean closed)throws Exception {
        require(call(writer,"storageGuard")==guard,"writer no longer retains this actual guard");
        Object retainedWriter=field(guard,"writer");
        require(retainedWriter==null||retainedWriter==writer,"storage guard cached another actual writer");
        require(absolute(value(g,"writer_lock")).equals(field(guard,"expectedOriginalLock"))
                &&absolute(value(g,"allocation_lock")).equals(field(guard,"allocationLockPath")),"different writer/allocation lock");
        require(Boolean.valueOf(closed).equals(field(guard,"closed")),"guard close state differs");
        FileLock lock=(FileLock)field(guard,"allocationLock");FileChannel channel=(FileChannel)field(guard,"allocationChannel");
        require(lock!=null&&channel!=null&&lock.isValid()!=closed&&channel.isOpen()!=closed,"actual allocation lease state differs");
        require(Files.size(absolute(value(g,"allocation_lock")))==0,"allocation lock payload changed");
        Class<?> sourceFiles=Class.forName(PREFIX+"build.SharedSourceFiles",false,guard.getClass().getClassLoader());
        Object current=invoke(sourceFiles.getMethod("nativeFile",Path.class),null,absolute(value(g,"allocation_lock")));
        Object retainedIdentity=field(guard,"allocationLockIdentity");
        require(retainedIdentity!=null&&call(retainedIdentity,"identityKey").equals(call(current,"identityKey")),
                "actual allocation owner file identity changed");
        Object accounting=call(guard,"accounting");
        require(((Number)call(accounting,"unresolvedWrites")).intValue()==0
                &&((Map<?,?>)field(guard,"pending")).isEmpty()
                &&((List<?>)field(guard,"unresolvedPhysical")).isEmpty(),"unresolved or pending physical writes prohibit release");
        String status=call(accounting,"status").toString();
        require(status.equals("PREPARED")||status.equals("ADMITTED"),"unknown or incomplete allocation accounting");
        for(Object root:(List<?>)call(accounting,"roots"))
            require(((Number)call(root,"outstandingPeakBytes")).longValue()==0,"outstanding physical reservation prohibits release");
    }

    private static void verifyHead(Map<String,String> g,Object head)throws Exception {
        Object state=call(head,"state");
        require(value(g,"expected_sequence").equals(call(state,"sequence").toString())
                &&value(g,"expected_digest").equals(call(head,"digest")),"original full canonical head differs");
        require(Boolean.FALSE.equals(call(head,"snapshotNeedsRecovery"))&&((List<?>)call(head,"indexRepairs")).isEmpty(),
                "ledger needs recovery or index repair; administrative release cannot repair it");
    }

    private static void verifyLiveRefs(Map<String,String> g)throws IOException {
        for(String name:List.of("owner","parent","claim","pair","head"))verifyRef(g,name,1L<<20);
    }
    private static void awaitingOwner()throws IOException {
        int matching=0;
        for(var entry:Thread.getAllStackTraces().entrySet()) {
            StackTraceElement[] frames=entry.getValue();
            boolean main=frame(frames,MAIN,"main"),await=frame(frames,PREPARED,"awaitExitedReplacementOwner");
            if(main||await) {
                require(main&&await&&frame(frames,PREFIX+"platform.GameSupervisor","awaitOwner")
                        &&frame(frames,PREFIX+"platform.SavedGameOwnerLifetime249$Retained","awaitExit")
                        &&entry.getKey().getName().equals("main"),"original Main is not purely waiting for its retained owner");
                matching++;
            }
        }
        require(matching==1,"unique original Main owner-wait stack required");
    }
    private static void rehearsalThread()throws IOException {
        require(Thread.getAllStackTraces().values().stream().anyMatch(frames->frame(frames,HARNESS,"main")),
                "no independent no-Game rehearsal Main");
        require(Thread.getAllStackTraces().values().stream().noneMatch(frames->frame(frames,MAIN,"main")),
                "rehearsal cannot operate on an ordinary business Main");
    }
    private static boolean frame(StackTraceElement[] frames,String type,String method) {
        return Arrays.stream(frames).anyMatch(f->f.getClassName().equals(type)&&f.getMethodName().equals(method));
    }
    private static void verifyClass(Map<String,String> g,Class<?> type)throws Exception {
        String prefix="class."+type.getName();
        require(type.getProtectionDomain().getCodeSource()!=null
                &&type.getProtectionDomain().getCodeSource().getLocation().toURI().toString().equals(value(g,prefix+".location")),
                "loaded class CodeSource differs: "+type.getName());
        byte[] bytes;
        try(InputStream input=type.getResourceAsStream("/"+type.getName().replace('.','/')+".class")) {
            require(input!=null,"class resource missing");bytes=input.readNBytes((4<<20)+1);
        }
        require(bytes.length<=4<<20&&bytes.length==decimal(value(g,prefix+".bytes"))
                &&sha256(bytes).equals(value(g,prefix+".sha256")),"loaded class resource differs: "+type.getName());
    }
    private static List<String> classNames(boolean live) {
        List<String> result=new ArrayList<>(COMMON_CLASSES);result.addAll(live?LIVE_CLASSES:List.of(HARNESS));return List.copyOf(result);
    }
    private static boolean live(Map<String,String> g)throws IOException {
        String purpose=value(g,"purpose");
        require(purpose.equals("LIVE_AWAITING_OWNER")||purpose.equals("NO_GAME_REHEARSAL"),"explicit administrative purpose required");
        return purpose.equals("LIVE_AWAITING_OWNER");
    }
    private static void fresh(Map<String,String> g)throws IOException {
        Instant start=Instant.parse(value(g,"issued_at_utc")),end=Instant.parse(value(g,"deadline_utc")),now=Instant.now();
        require(!now.isBefore(start)&&now.isBefore(end)&&end.isAfter(start)
                &&Duration.between(start,end).compareTo(Duration.ofMinutes(10))<=0,"fresh finite administrative grant required");
    }

    private static void validateKeys(Map<String,String> g)throws IOException {
        require(SCHEMA.equals(value(g,"schema"))&&"/root/ck3-resume91-root-20261116-research".equals(value(g,"issuer")),
                "explicit versioned Root administrative source required");
        require(value(g,"operation_id").matches("[a-zA-Z0-9-]{1,96}")&&value(g,"expected_digest").matches("[0-9a-f]{64}"),
                "bounded operation identity and canonical digest required");
        Set<String> keys=new java.util.HashSet<>(List.of("schema","operation_id","issuer","purpose","issued_at_utc","deadline_utc",
                "target_pid","target_birth_filetime","java_home","java_runtime_version","java_executable",
                "expected_sequence","expected_digest","writer_lock","allocation_lock","output"));
        for(String name:List.of("ready","agent","bridge"))refKeys(keys,name);
        for(String name:classNames(live(g)))for(String leaf:List.of("location","bytes","sha256"))keys.add("class."+name+"."+leaf);
        if(live(g)) {
            keys.addAll(List.of("game_pid","game_birth_filetime"));
            for(String name:List.of("owner","parent","claim","pair","head"))refKeys(keys,name);
        }
        require(g.keySet().equals(keys),"missing or unknown administrative source fields");
        decimal(value(g,"target_pid"));decimal(value(g,"target_birth_filetime"));decimal(value(g,"expected_sequence"));
    }
    private static void refKeys(Set<String> keys,String name) {
        for(String leaf:List.of("path","bytes","sha256"))keys.add(name+"."+leaf);
    }
    private static void verifyRef(Map<String,String> g,String name,long maximum)throws IOException {
        readExact(absolute(value(g,name+".path")),decimal(value(g,name+".bytes")),value(g,name+".sha256"),maximum);
    }
    private static byte[] readExact(Path path,long bytes,String hash,long maximum)throws IOException {
        require(bytes>0&&bytes<=maximum&&hash.matches("[0-9a-f]{64}")&&!Files.isSymbolicLink(path)
                &&Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS),"bounded plain exact original required: "+path);
        byte[] result;try(InputStream input=Files.newInputStream(path)){result=input.readNBytes(Math.toIntExact(maximum+1));}
        require(result.length==bytes&&sha256(result).equals(hash),"exact original bytes/SHA differ: "+path);return result;
    }
    private static Path absolute(String text)throws IOException {
        Path path=Path.of(text);require(path.isAbsolute()&&path.normalize().equals(path),"normalized absolute path required");return path;
    }
    private static long decimal(String value)throws IOException {
        require(value.matches("0|[1-9][0-9]{0,19}"),"canonical nonnegative decimal required");
        try{return Long.parseLong(value);}catch(NumberFormatException invalid){throw new IOException("bounded nonnegative decimal required",invalid);}
    }
    private static String value(Map<String,String> g,String key)throws IOException {
        String value=g.get(key);require(value!=null&&!value.isEmpty(),"required source field "+key);return value;
    }
    private static Map<String,String> parse(byte[] raw)throws IOException {
        require(raw.length<=65536,"bounded administrative properties required");
        String text=new String(raw,StandardCharsets.UTF_8);
        require(Arrays.equals(text.getBytes(StandardCharsets.UTF_8),raw)&&!text.contains("\r")&&!text.contains("\u0000"),
                "literal UTF8/LF administrative properties required");
        Map<String,String> result=new LinkedHashMap<>();
        for(String line:text.split("\n")) {
            int split=line.indexOf('=');require(split>0&&split<line.length()-1,"literal key=value line required");
            String key=line.substring(0,split),value=line.substring(split+1);
            require(key.matches("[a-zA-Z0-9_.$-]{1,160}")&&result.putIfAbsent(key,value)==null,"closed unique property required");
        }
        return result;
    }
    private static void writeProperties(Path path,Map<String,String> values)throws IOException {
        StringBuilder body=new StringBuilder();
        for(var row:new TreeMap<>(values).entrySet()) {
            require(!row.getValue().contains("\n")&&!row.getValue().contains("\r"),"single-line literal property required");
            body.append(row.getKey()).append('=').append(row.getValue()).append('\n');
        }
        byte[] raw=body.toString().getBytes(StandardCharsets.UTF_8);require(raw.length<=65536,"bounded administrative receipt required");
        Files.write(path,raw,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
    }
    private static Object field(Object owner,String name)throws ReflectiveOperationException {
        return field(owner,owner.getClass(),name);
    }
    private static Object field(Object owner,Class<?> type,String name)throws ReflectiveOperationException {
        Field field=type.getDeclaredField(name);field.setAccessible(true);return field.get(owner);
    }
    private static Object call(Object owner,String name)throws Exception {
        return invoke(owner.getClass().getMethod(name),owner);
    }
    private static Object invoke(Method method,Object owner,Object...args)throws Exception {
        try{return method.invoke(owner,args);}
        catch(InvocationTargetException wrapped){
            Throwable cause=wrapped.getCause();if(cause instanceof Exception exception)throw exception;
            if(cause instanceof Error error)throw error;throw new IOException("unexpected reflected failure",cause);
        }
    }
    private static String sha256(byte[] raw)throws IOException {
        try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));}
        catch(java.security.NoSuchAlgorithmException impossible){throw new IOException(impossible);}
    }
    private static void require(boolean condition,String message)throws IOException {if(!condition)throw new IOException(message);}

    /** Test-only DATA construction. No agent is loaded, no object is discovered or mutated here. */
    public static void writeRehearsalGrant(Path readyProperties,Path grantPath,Path sourceReady,Path agentJar,Path bridge)throws IOException {
        byte[] readyRaw;try(InputStream input=Files.newInputStream(readyProperties)){readyRaw=input.readNBytes(65537);}
        Map<String,String> data=parse(readyRaw),grant=new TreeMap<>();
        for(String key:List.of("operation_id","target_pid","target_birth_filetime","java_home","java_runtime_version","java_executable",
                "expected_sequence","expected_digest","writer_lock","allocation_lock","output"))grant.put(key,value(data,key));
        for(String type:classNames(false))for(String leaf:List.of("location","bytes","sha256")) {
            String key="class."+type+"."+leaf;grant.put(key,value(data,key));
        }
        grant.put("schema",SCHEMA);grant.put("purpose","NO_GAME_REHEARSAL");
        grant.put("issuer","/root/ck3-resume91-root-20261116-research");
        Instant now=Instant.now();grant.put("issued_at_utc",now.toString());grant.put("deadline_utc",now.plusSeconds(90).toString());
        if("expired".equals(data.get("mode"))){grant.put("issued_at_utc",now.minusSeconds(91).toString());grant.put("deadline_utc",now.minusSeconds(1).toString());}
        if("wrong-head".equals(data.get("mode")))grant.put("expected_digest","0".repeat(64));
        if("no-close".equals(data.get("mode")))grant.put("target_birth_filetime","1");
        for(var row:Map.of("ready",sourceReady,"agent",agentJar,"bridge",bridge).entrySet()) {
            Path path=row.getValue().toAbsolutePath().normalize();byte[] raw=Files.readAllBytes(path);
            grant.put(row.getKey()+".path",path.toString());grant.put(row.getKey()+".bytes",Integer.toString(raw.length));
            grant.put(row.getKey()+".sha256",sha256(raw));
        }
        validateKeys(grant);writeProperties(grantPath,grant);
    }
}
