package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.annotation.JsonInclude;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.channels.FileLock;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.SharedSourceFiles.Witness;
import org.xar.ck3.control.build.WindowsJobProcess;

/** One shared mechanical command caller. The child has a hard Job; the outer is a reservation. */
public final class SharedOwnedCommand {
    private static final int MAXIMUM_JAVA_EVIDENCE_BYTES=4<<20;
    private final SharedOwnedCommandBinding binding;
    private final FileRef bindingRef;
    private final Witness bindingBefore;
    private final Path SOURCE;
    private final String MACHINE;
    private final FileRef STANDING;
    private final FileRef DELIVERY;
    private static final ObjectMapper JSON = ControlBuild.strictMapper();
    private static final Set<String> SPEC_KEYS = Set.of("schema","machine_id","owner","coordinator","slot_id","borrowed_slot_id","run_id",
            "standing_ref","launcher_source_ref","executable","arguments","cwd","environment","inputs","output_root",
            "timeout_seconds","memory_limit_bytes","root_exit_drain_policy","operation_card_ref","temporary_policy");
    private static final Set<String> UTF8_SPEC_KEYS;
    static { var keys=new HashSet<>(SPEC_KEYS); keys.add("java_invocation"); UTF8_SPEC_KEYS=Set.copyOf(keys); }
    private static final Set<String> MSVC_SPEC_KEYS;
    static { var keys=new HashSet<>(SPEC_KEYS); keys.add("msvc_auxiliary_binding"); MSVC_SPEC_KEYS=Set.copyOf(keys); }
    private static final Set<String> ROOT_SPEC_KEYS;
    static { var keys=new HashSet<>(SPEC_KEYS);keys.add("prepared_root");ROOT_SPEC_KEYS=Set.copyOf(keys); }
    /** Three exact original inputs; no argv, environment or alternate invocation engine. */
    public record PreparedRootInputs(FileRef packageManifest,FileRef invocation,FileRef rootRuntimeAuthorizationRef) {
        public PreparedRootInputs {
            for(FileRef pin:List.of(packageManifest,invocation,rootRuntimeAuthorizationRef)) {
                java.util.Objects.requireNonNull(pin);
                if(pin.bytes()<1)throw new IllegalArgumentException("Nonempty exact prepared Root input required");
            }
            if(Set.of(packageManifest.path(),invocation.path(),rootRuntimeAuthorizationRef.path()).size()!=3)
                throw new IllegalArgumentException("Distinct prepared Root original paths required");
        }
    }
    /** The only accepted implementation is the fixed named private LS preparer, verified against actual authority. */
    public interface RootPreparer {
        org.xar.ck3.control.build.runtime.JavaRuntimeLaunch.PreparedLaunch prepare(PreparedRootInputs inputs)throws IOException;
    }
    public static PreparedRootInputs decodePreparedRoot(JsonNode value)throws IOException {
        exactKeys(value,Set.of("package_manifest","invocation","root_runtime_authorization_ref"));
        try { return new PreparedRootInputs(ref(object(value,"package_manifest")),ref(object(value,"invocation")),
                ref(object(value,"root_runtime_authorization_ref"))); }
        catch(IllegalArgumentException invalid) { throw new IOException("Invalid exact prepared Root inputs",invalid); }
    }
    /** An explicit sole-engine publication, never inferred from generic argv. */
    public record JavaInvocation(Witness envelope,List<String> asciiVmOptions) {
        public JavaInvocation {
            java.util.Objects.requireNonNull(envelope); asciiVmOptions=List.copyOf(asciiVmOptions);
            java.util.Objects.requireNonNull(envelope.source());java.util.Objects.requireNonNull(envelope.nativeFile());
            if(envelope.source().bytes()!=envelope.nativeFile().logicalBytes()) throw new IllegalArgumentException("Consistent actual envelope witness required");
            for(String option:asciiVmOptions) {
                if(option==null || option.isEmpty() || option.chars().anyMatch(c->c<32 || c>126))
                    throw new IllegalArgumentException("Explicit ASCII startup JVM options required");
            }
        }
        public CiBootstrap.JavaUtf8Invocation.Publication publication() throws IOException {
            SharedSourceFiles.assertUnchanged(envelope);
            return new CiBootstrap.JavaUtf8Invocation.Publication(CiBootstrap.JavaUtf8Invocation.captureFile(path(envelope.source().path())));
        }
        public FileRef fileRef() { return envelope.source(); }
    }
    public enum Status { PASS, RED, REJECTED }
    public record Outcome(Status status, FileRef terminalRef) {
        public Outcome { if(status==null || terminalRef==null) throw new IllegalArgumentException("Actual terminal outcome required"); }
        public int exitCode() { return status == Status.PASS ? 0 : 1; }
    }
    record BindingEvidence(String schema,String machineId,FileRef bindingRef) { }
    enum TemporaryPolicy { SLOT_PRIVATE, HOST_FIXTURE_32_MIB }
    enum Check { MATCH, FAILED, NOT_REACHED }
    record Request(String schema,String machineId,String owner,String coordinator,String slotId,String borrowedSlotId,String runId,
                   FileRef standingRef,FileRef launcherSourceRef,FileRef operationCardRef,TemporaryPolicy temporaryPolicy,FileRef executable,List<String> arguments,Path cwd,
                   Map<String,String> environment,List<FileRef> inputs,Path outputRoot,long timeoutSeconds,
                   long memoryLimitBytes,WindowsJobProcess.RootExitDrainPolicy rootExitDrainPolicy,JavaInvocation javaInvocation,
                   MsvcAuxiliaryPolicy.ExecutionBinding msvcAuxiliaryBinding,PreparedRootInputs preparedRoot) {
        Request(String schema,String machineId,String owner,String coordinator,String slotId,String borrowedSlotId,String runId,
                FileRef standingRef,FileRef launcherSourceRef,FileRef operationCardRef,TemporaryPolicy temporaryPolicy,FileRef executable,
                List<String> arguments,Path cwd,Map<String,String> environment,List<FileRef> inputs,Path outputRoot,long timeoutSeconds,
                long memoryLimitBytes,WindowsJobProcess.RootExitDrainPolicy policy,JavaInvocation javaInvocation,
                MsvcAuxiliaryPolicy.ExecutionBinding auxiliary) {
            this(schema,machineId,owner,coordinator,slotId,borrowedSlotId,runId,standingRef,launcherSourceRef,operationCardRef,
                    temporaryPolicy,executable,arguments,cwd,environment,inputs,outputRoot,timeoutSeconds,memoryLimitBytes,policy,
                    javaInvocation,auxiliary,null);
        }
        Request(String schema,String machineId,String owner,String coordinator,String slotId,String borrowedSlotId,String runId,
                FileRef standingRef,FileRef launcherSourceRef,FileRef operationCardRef,TemporaryPolicy temporaryPolicy,FileRef executable,
                List<String> arguments,Path cwd,Map<String,String> environment,List<FileRef> inputs,Path outputRoot,long timeoutSeconds,
                long memoryLimitBytes,WindowsJobProcess.RootExitDrainPolicy policy,JavaInvocation javaInvocation) {
            this(schema,machineId,owner,coordinator,slotId,borrowedSlotId,runId,standingRef,launcherSourceRef,operationCardRef,
                    temporaryPolicy,executable,arguments,cwd,environment,inputs,outputRoot,timeoutSeconds,memoryLimitBytes,policy,javaInvocation,null);
        }
        Request(String schema,String machineId,String owner,String coordinator,String slotId,String borrowedSlotId,String runId,
                FileRef standingRef,FileRef launcherSourceRef,FileRef operationCardRef,TemporaryPolicy temporaryPolicy,FileRef executable,
                List<String> arguments,Path cwd,Map<String,String> environment,List<FileRef> inputs,Path outputRoot,long timeoutSeconds,
                long memoryLimitBytes,WindowsJobProcess.RootExitDrainPolicy policy) {
            this(schema,machineId,owner,coordinator,slotId,borrowedSlotId,runId,standingRef,launcherSourceRef,operationCardRef,
                    temporaryPolicy,executable,arguments,cwd,environment,inputs,outputRoot,timeoutSeconds,memoryLimitBytes,policy,null);
        }
    }
    record Slot(String slotId,Path outputRoot,long outputCapBytes,long workerMemoryLimitBytes,
                long outerMemoryBudgetBytes,long timeoutSeconds) { }
    record Outer(String pidDecimal,long reservedMemoryBytes,boolean hardJobEnforced,String scope) { }
    record Terminal(String schema,String machineId,String observedAtUtc,Status status,String owner,String slotId,
                    String borrowedSlotId,FileRef requestRef,FileRef standingRef,FileRef launcherSourceRef,
                    List<FileRef> completeRuntime,Outer outer,boolean childStarted,WindowsJobProcess.CommandResult child,
                    WindowsJobProcess.JobDiagnosticOutcome diagnostic,Check inputPrecheck,Check inputPostcheck,Check runtimePostcheck,
                    String failure,List<Witness> inputBefore,List<String> effectiveArguments,FileRef stdoutRef,
                    FileRef stderrRef,long outputNativeBytesWithDirectoryGuard,int gameRpcCalls,
                    int actualDriverOrSaveBodyReads,
                     @JsonInclude(JsonInclude.Include.NON_NULL) FileRef javaInvocationEvidenceRef,
                     MsvcAuxiliaryPolicy.Outcome auxiliaryCleanup,
                      @JsonInclude(JsonInclude.Include.NON_NULL) FileRef rootInvocationEvidenceRef) {
        Terminal {
            if (schema.equals("xar.shared-owned-command-terminal/v3") != (auxiliaryCleanup!=null))
                throw new IllegalArgumentException("Only explicit v3 MSVC commands carry the mandatory auxiliary outcome");
            if(rootInvocationEvidenceRef!=null && !schema.equals("xar.shared-owned-command-terminal/v5")
                    || schema.equals("xar.shared-owned-command-terminal/v5") && status==Status.PASS && rootInvocationEvidenceRef==null)
                throw new IllegalArgumentException("Explicit Root v5 requires its original evidence");
            if(rootInvocationEvidenceRef!=null && (auxiliaryCleanup!=null || javaInvocationEvidenceRef!=null))
                throw new IllegalArgumentException("Root v5 is a distinct sole prepared route");
            if (auxiliaryCleanup!=null && javaInvocationEvidenceRef!=null)
                throw new IllegalArgumentException("MSVC v3 cannot carry a UTF8-child evidence field");
        }
        Terminal(String schema,String machineId,String observedAtUtc,Status status,String owner,String slotId,String borrowedSlotId,
                FileRef requestRef,FileRef standingRef,FileRef launcherSourceRef,List<FileRef> completeRuntime,Outer outer,boolean childStarted,
                WindowsJobProcess.CommandResult child,WindowsJobProcess.JobDiagnosticOutcome diagnostic,Check inputPrecheck,Check inputPostcheck,
                Check runtimePostcheck,String failure,List<Witness> inputBefore,List<String> effectiveArguments,FileRef stdoutRef,FileRef stderrRef,
                long outputNativeBytesWithDirectoryGuard,int gameRpcCalls,int actualDriverOrSaveBodyReads,FileRef javaInvocationEvidenceRef,
                MsvcAuxiliaryPolicy.Outcome auxiliaryCleanup) {
            this(schema,machineId,observedAtUtc,status,owner,slotId,borrowedSlotId,requestRef,standingRef,launcherSourceRef,completeRuntime,
                    outer,childStarted,child,diagnostic,inputPrecheck,inputPostcheck,runtimePostcheck,failure,inputBefore,effectiveArguments,
                    stdoutRef,stderrRef,outputNativeBytesWithDirectoryGuard,gameRpcCalls,actualDriverOrSaveBodyReads,
                    javaInvocationEvidenceRef,auxiliaryCleanup,null);
        }
        Terminal(String schema,String machineId,String observedAtUtc,Status status,String owner,String slotId,String borrowedSlotId,
                FileRef requestRef,FileRef standingRef,FileRef launcherSourceRef,List<FileRef> completeRuntime,Outer outer,boolean childStarted,
                WindowsJobProcess.CommandResult child,WindowsJobProcess.JobDiagnosticOutcome diagnostic,Check inputPrecheck,Check inputPostcheck,
                Check runtimePostcheck,String failure,List<Witness> inputBefore,List<String> effectiveArguments,FileRef stdoutRef,FileRef stderrRef,
                long outputNativeBytesWithDirectoryGuard,int gameRpcCalls,int actualDriverOrSaveBodyReads,FileRef javaInvocationEvidenceRef) {
            this(schema,machineId,observedAtUtc,status,owner,slotId,borrowedSlotId,requestRef,standingRef,launcherSourceRef,completeRuntime,
                    outer,childStarted,child,diagnostic,inputPrecheck,inputPostcheck,runtimePostcheck,failure,inputBefore,effectiveArguments,
                    stdoutRef,stderrRef,outputNativeBytesWithDirectoryGuard,gameRpcCalls,actualDriverOrSaveBodyReads,javaInvocationEvidenceRef,null);
        }
        Terminal(String schema,String machineId,String observedAtUtc,Status status,String owner,String slotId,String borrowedSlotId,
                FileRef requestRef,FileRef standingRef,FileRef launcherSourceRef,List<FileRef> completeRuntime,Outer outer,boolean childStarted,
                WindowsJobProcess.CommandResult child,WindowsJobProcess.JobDiagnosticOutcome diagnostic,Check inputPrecheck,Check inputPostcheck,
                Check runtimePostcheck,String failure,List<Witness> inputBefore,List<String> effectiveArguments,FileRef stdoutRef,FileRef stderrRef,
                long outputNativeBytesWithDirectoryGuard,int gameRpcCalls,int actualDriverOrSaveBodyReads) {
            this(schema,machineId,observedAtUtc,status,owner,slotId,borrowedSlotId,requestRef,standingRef,launcherSourceRef,completeRuntime,
                    outer,childStarted,child,diagnostic,inputPrecheck,inputPostcheck,runtimePostcheck,failure,inputBefore,effectiveArguments,
                    stdoutRef,stderrRef,outputNativeBytesWithDirectoryGuard,gameRpcCalls,actualDriverOrSaveBodyReads,null);
        }
    }
    record JavaInvocationEvidence(String schema,JavaInvocation invocation,List<FileRef> carrierRuntime,
                    List<String> physicalArguments,List<String> effectiveAsciiVmOptions,JavaPreparationState preparationState,
                    Witness preparationRef,FileRef nativeEvidenceRef) { }
    enum JavaPreparationState { PRE_LAUNCH, PREPARED }
    record RootInvocationEvidence(String schema,FileRef rootInvocationRef,PreparedRootInputs preparedRoot,
            SourceGraphCommandSpecProducer.RootRuntimeAuthorization authorization,
            WindowsJobProcess.CommandSpec managedCommand,List<Witness> retainedPackageSources,
            List<Witness> retainedOuterSources,Check packagePrecheck,Check packagePostcheck,
            Check outerPrecheck,Check outerPostcheck) {
        RootInvocationEvidence {
            if(!"xar.shared-owned-command-root-evidence/v1".equals(schema))
                throw new IllegalArgumentException("Exact Root evidence schema required");
            retainedPackageSources=List.copyOf(retainedPackageSources);retainedOuterSources=List.copyOf(retainedOuterSources);
        }
    }

    enum NativeTerminalVersion { V2_ORIGINAL_26_FIELDS, V2_EXPLICIT_OPTIONAL_FIELDS, V3_MSVC_AUXILIARY }
    enum NativeTerminalScope { OWNED_TOOL_PROCESS_OBSERVATION_NOT_JAVA_INVOCATION_CUSTODY }
    enum NativePathRelation { EXACT_RAW_REFERENCES, HISTORICAL_WINDOWS_SPELLING_NOT_FILE_ID_OR_CURRENT_SOURCE }
    record NativeOriginalReferences(FileRef requestStanding,FileRef terminalStanding,FileRef requestLauncher,
            FileRef terminalLauncher,NativePathRelation relation) { }
    record NativeTerminal(NativeTerminalVersion version, NativeTerminalScope scope, Terminal terminal, Request request,
            NativeOriginalReferences originalReferences) {
        NativeTerminal {
            java.util.Objects.requireNonNull(version); java.util.Objects.requireNonNull(scope);
            java.util.Objects.requireNonNull(terminal); java.util.Objects.requireNonNull(request);
            java.util.Objects.requireNonNull(originalReferences);
        }
    }
    // An internal decode view, never written over a historical terminal or used by a Java invocation reader.
    private record NativeTerminalWire(String schema,String machineId,String observedAtUtc,Status status,String owner,String slotId,
            String borrowedSlotId,FileRef requestRef,FileRef standingRef,FileRef launcherSourceRef,
            List<FileRef> completeRuntime,Outer outer,boolean childStarted,WindowsJobProcess.CommandResult child,
            WindowsJobProcess.JobDiagnosticOutcome diagnostic,Check inputPrecheck,Check inputPostcheck,Check runtimePostcheck,
            String failure,List<Witness> inputBefore,List<String> effectiveArguments,FileRef stdoutRef,FileRef stderrRef,
            long outputNativeBytesWithDirectoryGuard,int gameRpcCalls,int actualDriverOrSaveBodyReads,
            FileRef javaInvocationEvidenceRef,MsvcAuxiliaryPolicy.Outcome auxiliaryCleanup) {
        Terminal terminal() {
            return new Terminal(schema,machineId,observedAtUtc,status,owner,slotId,borrowedSlotId,requestRef,standingRef,
                    launcherSourceRef,completeRuntime,outer,childStarted,child,diagnostic,inputPrecheck,inputPostcheck,
                    runtimePostcheck,failure,inputBefore,effectiveArguments,stdoutRef,stderrRef,
                    outputNativeBytesWithDirectoryGuard,gameRpcCalls,actualDriverOrSaveBodyReads,javaInvocationEvidenceRef,auxiliaryCleanup);
        }
    }
    private static final Set<String> NATIVE_TERMINAL_BASE_KEYS=Set.of(
            "schema","machine_id","observed_at_utc","status","owner","slot_id","borrowed_slot_id",
            "request_ref","standing_ref","launcher_source_ref","complete_runtime","outer","child_started","child",
            "diagnostic","input_precheck","input_postcheck","runtime_postcheck","failure","input_before",
            "effective_arguments","stdout_ref","stderr_ref","output_native_bytes_with_directory_guard",
            "game_rpc_calls","actual_driver_or_save_body_reads");

    /** Exact physical native/tool terminal and original request; this API grants no Java invocation custody. */
    static NativeTerminal readNativeTerminal(FileRef terminalRef) throws IOException {
        return readNativeTerminal(terminalRef,4<<20);
    }
    static NativeTerminal readNativeTerminal(FileRef terminalRef,int requestMaximum) throws IOException {
        require(requestMaximum>0 && requestMaximum<=(4<<20),"Finite original native request bound required");
        byte[] terminalBytes=readNativeOriginal(terminalRef,2<<20);
        JsonNode original=JSON.readTree(terminalBytes);
        require(original!=null && original.isObject(),"Native terminal object required");
        FileRef requestRef=ref(object(original,"request_ref"));
        NativeTerminal decoded=decodeNativeTerminal(terminalBytes,readNativeOriginal(requestRef,requestMaximum));
        terminalRef.verify(); requestRef.verify(); return decoded;
    }

    /** Pure versioned wire decoding. Original request content is mandatory even for preserved historical bytes. */
    static NativeTerminal decodeNativeTerminal(byte[] terminalBytes,byte[] requestBytes) throws IOException {
        require(terminalBytes!=null && terminalBytes.length>0 && terminalBytes.length<=(2<<20)
                && requestBytes!=null && requestBytes.length>0 && requestBytes.length<=(4<<20),
                "Bounded original native terminal and original request bytes required");
        JsonNode original=JSON.readTree(terminalBytes);
        require(original!=null && original.isObject(),"Native terminal object required");
        Set<String> keys=new HashSet<>(); original.fieldNames().forEachRemaining(keys::add);
        Set<String> allowed=new HashSet<>(NATIVE_TERMINAL_BASE_KEYS);
        allowed.add("java_invocation_evidence_ref"); allowed.add("auxiliary_cleanup");
        require(keys.containsAll(NATIVE_TERMINAL_BASE_KEYS) && allowed.containsAll(keys),
                "Exact original native terminal field contract required");
        String schema=text(original,"schema");
        require(schema.equals("xar.shared-owned-command-terminal/v2") || schema.equals("xar.shared-owned-command-terminal/v3"),
                "Explicit native terminal v2 or MSVC v3 required");
        require(!original.has("java_invocation_evidence_ref") || original.get("java_invocation_evidence_ref").isNull(),
                "Native-only reader cannot consume current Java invocation evidence");
        FileRef requestRef=ref(object(original,"request_ref"));
        require(requestRef.bytes()==requestBytes.length && requestRef.sha256().equals(nativeRequestDigest(requestBytes)),
                "Native terminal must bind the exact original request bytes");
        JsonNode rawRequest=JSON.readTree(requestBytes);
        Request command=parseRequest(rawRequest);
        FileRef rawStanding=rawNativeReference(object(rawRequest,"standing_ref"));
        FileRef terminalStanding=rawNativeReference(object(original,"standing_ref"));
        FileRef rawLauncher=rawNativeReference(object(rawRequest,"launcher_source_ref"));
        FileRef terminalLauncher=rawNativeReference(object(original,"launcher_source_ref"));
        require(rawStanding.equals(terminalStanding),"Original native standing reference must match its literal original request");
        boolean sameRawLauncher=rawLauncher.equals(terminalLauncher);
        require(sameRawLauncher || keys.equals(NATIVE_TERMINAL_BASE_KEYS)
                && sameRef(rawLauncher,terminalLauncher),"Only original 26-field native history permits explicit Windows launcher spelling correspondence");
        require(command.javaInvocation()==null && !javaMainImage(command.executable().path()),
                "Native-only reader cannot grant Java invocation custody");
        boolean msvc=schema.equals("xar.shared-owned-command-terminal/v3");
        require(msvc ? original.has("auxiliary_cleanup") && !original.get("auxiliary_cleanup").isNull()
                        && command.msvcAuxiliaryBinding()!=null
                : (!original.has("auxiliary_cleanup") || original.get("auxiliary_cleanup").isNull())
                        && command.msvcAuxiliaryBinding()==null,
                "Native terminal and original MSVC scope differ");
        var view=((com.fasterxml.jackson.databind.node.ObjectNode)original).deepCopy();
        if(!view.has("java_invocation_evidence_ref")) view.putNull("java_invocation_evidence_ref");
        if(!view.has("auxiliary_cleanup")) view.putNull("auxiliary_cleanup");
        Terminal terminal=JSON.treeToValue(view,NativeTerminalWire.class).terminal();
        require(terminal.childStarted() && terminal.child()!=null
                && terminal.child().identity()!=null && terminal.child().identity().executable()!=null
                && terminal.machineId()!=null && terminal.owner()!=null && terminal.slotId()!=null
                && terminal.standingRef()!=null && terminal.launcherSourceRef()!=null
                && !javaMainImage(terminal.child().identity().executable())
                && path(terminal.child().identity().executable()).equals(path(command.executable().path()))
                && terminal.machineId().equals(command.machineId()) && terminal.owner().equals(command.owner())
                && terminal.slotId().equals(command.slotId()) && java.util.Objects.equals(terminal.borrowedSlotId(),command.borrowedSlotId())
                && terminal.standingRef().equals(terminalStanding) && terminal.launcherSourceRef().equals(terminalLauncher),
                "Native/tool child identity and original request context required");
        NativeTerminalVersion version=msvc ? NativeTerminalVersion.V3_MSVC_AUXILIARY
                : keys.equals(NATIVE_TERMINAL_BASE_KEYS) ? NativeTerminalVersion.V2_ORIGINAL_26_FIELDS
                : NativeTerminalVersion.V2_EXPLICIT_OPTIONAL_FIELDS;
        return new NativeTerminal(version,NativeTerminalScope.OWNED_TOOL_PROCESS_OBSERVATION_NOT_JAVA_INVOCATION_CUSTODY,
                terminal,command,new NativeOriginalReferences(rawStanding,terminalStanding,rawLauncher,terminalLauncher,
                        sameRawLauncher ? NativePathRelation.EXACT_RAW_REFERENCES
                                : NativePathRelation.HISTORICAL_WINDOWS_SPELLING_NOT_FILE_ID_OR_CURRENT_SOURCE));
    }
    private static FileRef rawNativeReference(JsonNode value) throws IOException {
        exactKeys(value,Set.of("path","bytes","sha256"));
        path(text(value,"path")); // Validate the representation without replacing the original string.
        return new FileRef(text(value,"path"),integer(value,"bytes"),text(value,"sha256"));
    }
    private static boolean javaMainImage(String image) {
        String name=Path.of(image).getFileName().toString();
        return name.equalsIgnoreCase("java.exe") || name.equalsIgnoreCase("javaw.exe");
    }
    private static String nativeRequestDigest(byte[] bytes) throws IOException {
        try { return java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch(java.security.NoSuchAlgorithmException unavailable) { throw new IOException("Required SHA-256 unavailable",unavailable); }
    }
    private static byte[] readNativeOriginal(FileRef reference,int maximum) throws IOException {
        require(reference!=null && reference.bytes()>0 && reference.bytes()<=maximum,"Bounded native original required");
        Path input=path(reference.path()); SharedSourceFiles.plainAncestors(input); reference.verify();
        byte[] bytes=Files.readAllBytes(input);
        require(bytes.length==reference.bytes() && bytes.length<=maximum,"Native original changed while reading");
        reference.verify(); return bytes;
    }
    private FileRef rootInvocationRef;
    private SourceGraphCommandSpecProducer.RootInvocation rootInvocation;
    private SourceGraphCommandSpecProducer.RootRuntimeAuthorization rootAuthorization;
    private RootPreparer rootPreparer;
    private org.xar.ck3.control.build.runtime.JavaRuntimeLaunch.PreparedLaunch rootPrepared;
    private final List<Witness> rootPackageSources=new ArrayList<>();
    private final List<Witness> rootOuterSources=new ArrayList<>();
    private Request request;
    private FileRef requestRef;
    private Slot primary;
    private Slot borrowed;
    private Instant deadline;
    private List<FileRef> runtime = List.of();
    private final List<Witness> inputBefore = new ArrayList<>();

    private SharedOwnedCommand(FileRef bindingRef,SharedOwnedCommandBinding binding,Witness bindingBefore) throws IOException {
        this.bindingRef=bindingRef; this.binding=binding; this.bindingBefore=bindingBefore; SOURCE=path(binding.launcherSourceRef().path());
        MACHINE=binding.machineId(); STANDING=binding.standingRef(); DELIVERY=binding.deliveryRef();
    }

    /** Runs one exact request in an independently scoped instance. This method never exits the caller JVM. */
    public static Outcome execute(FileRef bindingRef,FileRef requestRef) throws Exception {
        require(bindingRef!=null,"exact binding ref required");
        Witness before=SharedSourceFiles.observe(path(bindingRef.path()));
        SharedOwnedCommandBinding binding=SharedOwnedCommandBinding.read(bindingRef);
        SharedSourceFiles.assertUnchanged(before);
        return new SharedOwnedCommand(bindingRef,binding,before).invoke(requestRef);
    }

    /** Fixed LS outer enters this same admission/lock/start path, never a nested Job. */
    public static Outcome executePreparedRoot(FileRef exactInvocation,RootPreparer preparer)throws Exception {
        require(exactInvocation!=null && preparer!=null,"Actual Root invocation and fixed preparer required");
        require(preparer.getClass().getName().equals("org.xar.ck3.control.service.root.RootRuntimeLaunchCommand$PreparedRoot")
                && !preparer.getClass().isSynthetic() && !preparer.getClass().isAnonymousClass(),
                "Only the fixed named private LS Root preparer is admitted");
        var invocation=SourceGraphCommandSpecProducer.readRootInvocation(exactInvocation);
        var authority=SourceGraphCommandSpecProducer.readRootAuthorization(invocation);
        SourceGraphCommandSpecProducer.requireRootProvider(authority,SourceGraphCommandSpecProducer.RootProvider.ROOT_PREPARER,preparer.getClass());
        SourceGraphCommandSpecProducer.requireRootOuterRuntime(authority);
        Witness before=SharedSourceFiles.observe(path(invocation.bindingRef().path()));
        var binding=SharedOwnedCommandBinding.read(invocation.bindingRef());SharedSourceFiles.assertUnchanged(before);
        var caller=new SharedOwnedCommand(invocation.bindingRef(),binding,before);
        caller.rootInvocationRef=exactInvocation;caller.rootInvocation=invocation;
        caller.rootAuthorization=authority;caller.rootPreparer=preparer;
        return caller.invoke(invocation.specRef());
    }

    public static void main(String[] args) throws Exception {
        if(args.length!=7 || !args[0].equals("run"))
            throw new IOException("run BINDING_PATH EXACT_BYTES SHA256 SPEC_PATH EXACT_BYTES SHA256 required");
        FileRef bindingRef=cliRef(args[1],args[2],args[3]), requestRef=cliRef(args[4],args[5],args[6]);
        Outcome outcome=execute(bindingRef,requestRef);
        if(outcome.exitCode()!=0) System.exit(outcome.exitCode());
    }

    static FileRef cliRef(String pathText,String bytesText,String sha256) throws IOException {
        final long bytes;
        try { bytes=Long.parseLong(bytesText); } catch(NumberFormatException error) { throw new IOException("Exact reference byte count required",error); }
        require(Long.toString(bytes).equals(bytesText),"canonical reference bytes required");
        return new FileRef(path(pathText).toString(),bytes,sha256);
    }

    private Outcome invoke(FileRef exactRequestRef) throws Exception {
        require(exactRequestRef!=null,"exact request ref required");
        requestRef=exactRequestRef; requestRef.verify(); require(requestRef.bytes()<=1048576,"spec larger than1MiB");
        request=parseRequest(parse(path(requestRef.path())));
        require((request.preparedRoot()!=null)==(rootInvocationRef!=null),"Root v5 requires the fixed LS preparer entry");
        if(request.preparedRoot()!=null)require(request.preparedRoot().equals(rootInvocation.preparedRoot()),
                "Exact Root invocation/prepared request required");
        authorize();
        List<FileChannel> channels=new ArrayList<>(); List<FileLock> locks=new ArrayList<>();
        try {
            List<Slot> slots=new ArrayList<>(List.of(primary)); if(borrowed!=null) slots.add(borrowed);
            slots.sort(Comparator.comparing(Slot::slotId));
            for(Slot slot:slots) {
                SharedSourceFiles.plainAncestors(slot.outputRoot()); Files.createDirectories(slot.outputRoot());
                FileChannel channel=FileChannel.open(slot.outputRoot().resolve(".shared-owned-command.lock"),StandardOpenOption.CREATE,StandardOpenOption.WRITE);
                channels.add(channel); FileLock lock=channel.tryLock();
                require(lock!=null,"slot already claimed: "+slot.slotId()); locks.add(lock);
            }
            return run();
        } finally {
            for(int index=locks.size()-1;index>=0;index--) locks.get(index).close();
            for(int index=channels.size()-1;index>=0;index--) channels.get(index).close();
        }
    }

    static Request parseRequest(JsonNode value) throws IOException {
        String schema=text(value,"schema");
        boolean root=schema.equals("xar.shared-owned-command-spec/v5");
        boolean utf8=schema.equals("xar.shared-owned-command-spec/v4");
        boolean msvc=schema.equals("xar.shared-owned-command-spec/v3");
        require(root || utf8 || msvc || schema.equals("xar.shared-owned-command-spec/v2"),"spec schema mismatch");
        exactKeys(value,root?ROOT_SPEC_KEYS:utf8?UTF8_SPEC_KEYS:msvc?MSVC_SPEC_KEYS:SPEC_KEYS);
        JavaInvocation javaInvocation=utf8?JSON.treeToValue(object(value,"java_invocation"),JavaInvocation.class):null;
        List<FileRef> inputs=new ArrayList<>();
        for(JsonNode entry:array(value,"inputs")) inputs.add(ref(entry));
        require(inputs.size()<=2048,"at most 2048 explicit input refs");
        List<String> arguments=texts(array(value,"arguments"));
        require(arguments.size()<=4096,"at most 4096 argv entries");
        if(utf8) {
            require(arguments.isEmpty(),"Explicit UTF8 Java request cannot retain a second generic argv");
            FileRef envelope=javaInvocation.fileRef();
            int envelopeCount=0;for(FileRef pin:inputs) if(sameRef(pin,envelope)) envelopeCount++;
            require(envelopeCount==1,
                    "UTF8 publication must be one exact explicit witnessed input");
            require(path(ref(object(value,"executable")).path()).getFileName().toString().equalsIgnoreCase("java.exe"),
                    "UTF8 invocation requires the exact allowed Java executable");
        }
        Map<String,String> environment=new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        JsonNode environmentNode=object(value,"environment");
        for(var entry:environmentNode.properties()) {
            require(entry.getValue().isTextual(),"environment values must be strings");
            require(environment.put(entry.getKey(),entry.getValue().textValue())==null,"case-duplicate environment key");
        }
        PreparedRootInputs preparedRoot=root?decodePreparedRoot(object(value,"prepared_root")):null;
        if(root) {
            require(arguments.isEmpty() && environment.isEmpty(),"Root v5 has no alternate argv or environment");
            require(path(ref(object(value,"executable")).path()).getFileName().toString().equalsIgnoreCase("java.exe"),
                    "Root v5 requires the exact allowed Java executable");
            for(FileRef pin:List.of(preparedRoot.packageManifest(),preparedRoot.invocation(),preparedRoot.rootRuntimeAuthorizationRef())) {
                int count=0;for(FileRef input:inputs)if(input.equals(pin))count++;
                require(count==1,"Each Root original must be one exact explicit input");
            }
        }
        String borrowedId=nullableText(value,"borrowed_slot_id");
        WindowsJobProcess.RootExitDrainPolicy policy;
        try { policy=WindowsJobProcess.RootExitDrainPolicy.valueOf(text(value,"root_exit_drain_policy")); }
        catch(IllegalArgumentException error) { throw new IOException("unknown typed root exit drain policy",error); }
        MsvcAuxiliaryPolicy.ExecutionBinding auxiliary=null;
        if(msvc) {
            auxiliary=JSON.treeToValue(object(value,"msvc_auxiliary_binding"),MsvcAuxiliaryPolicy.ExecutionBinding.class);
            auxiliary.requireRequest(ref(object(value,"executable")),inputs);
            require(policy==WindowsJobProcess.RootExitDrainPolicy.DEFAULT_FIVE_SECONDS,
                    "v3 MSVC policy must explicitly replace the default drain, not combine two policies");
        }
        return new Request(text(value,"schema"),text(value,"machine_id"),text(value,"owner"),text(value,"coordinator"),
                text(value,"slot_id"),borrowedId,text(value,"run_id"),ref(object(value,"standing_ref")),ref(object(value,"launcher_source_ref")),
                nullableRef(value,"operation_card_ref"),temporaryPolicy(value),ref(object(value,"executable")),arguments,path(text(value,"cwd")),Map.copyOf(environment),List.copyOf(inputs),
                path(text(value,"output_root")),integer(value,"timeout_seconds"),integer(value,"memory_limit_bytes"),policy,javaInvocation,auxiliary,preparedRoot);
    }

    /** Mechanical layout only; the standing still independently grants the slot and execution. */
    public static Path commandOutputRoot(Path slotRoot,String owner,String runId) throws IOException {
        require(slotRoot!=null && slotRoot.isAbsolute(),"absolute exact slot root required");
        require(owner!=null && owner.matches("/root/[a-z0-9_/-]+"),"canonical Root task owner required");
        require(runId!=null && runId.matches("[a-z0-9][a-z0-9_-]{0,79}"),"canonical finite run_id required");
        Path slot=slotRoot.toAbsolutePath().normalize();
        Path output=slot.resolve(owner.substring(6).replace('/','_')).resolve(runId);
        requireCommandOutputRoot(output,slot,owner,runId);
        return output;
    }

    /** Exactly the output guard used by authorize, shared with typed source-graph spec production. */
    static void requireCommandOutputRoot(Path outputRoot,Path slotRoot,String owner,String runId) throws IOException {
        require(outputRoot!=null && slotRoot!=null && outputRoot.isAbsolute() && slotRoot.isAbsolute(),
                "absolute exact command and slot roots required");
        require(owner!=null && owner.matches("/root/[a-z0-9_/-]+"),"canonical Root task owner required");
        require(outputRoot.startsWith(slotRoot) && !outputRoot.equals(slotRoot),"output outside exact slot build root");
        Path relative=slotRoot.relativize(outputRoot);
        String ownerStem=owner.substring(6).replace('/','_');
        require(relative.getNameCount()==2 && relative.getName(0).toString().equals(ownerStem)
                && relative.getName(1).toString().equals(runId)
                && runId!=null && runId.matches("[a-z0-9][a-z0-9_-]{0,79}"),"output must be slot/owner/unique run_id");
    }

    private void authorize() throws Exception {
        bindingRef.verify();
        require(MACHINE.equals(request.machineId()) && MACHINE.equals(WindowsJobProcess.currentMachineId()),"native machine mismatch");
        equalRef(request.standingRef(),STANDING); STANDING.verify();
        require(path(request.launcherSourceRef().path()).equals(SOURCE),"single shared launcher source required");
        equalRef(request.launcherSourceRef(),binding.launcherSourceRef()); request.launcherSourceRef().verify();
        require(request.owner().matches("/root/[a-z0-9_/-]+"),"canonical Root task owner required");
        JsonNode standing=parse(path(STANDING.path()));
        SharedOwnedCommandBinding.verifyAuthority(standing,binding.standingExpectation(),MACHINE);
        StandingPreflight preflight=validateStanding(request,binding,standing);
        primary=preflight.primary(); borrowed=preflight.borrowed(); deadline=preflight.deadline();
        ref(object(standing,"qualified_tools_ref")).verify(); ref(object(standing,"qualified_own_readback_ref")).verify();
        DELIVERY.verify(); JsonNode delivery=parse(path(DELIVERY.path()));
        SharedOwnedCommandBinding.verifyAuthority(delivery,binding.deliveryExpectation(),MACHINE);
        verifyPackagedSource(ref(object(standing,"qualified_tools_ref")));
        List<FileRef> expected=new ArrayList<>();
        for(JsonNode entry:array(standing,"runtime_closure")) { FileRef pin=ref(entry); pin.verify(); expected.add(pin); }
        List<FileRef> delivered=new ArrayList<>();
        for(JsonNode entry:array(delivery,"complete_runtime")) delivered.add(ref(entry));
        expected.sort(Comparator.comparing(FileRef::path)); delivered.sort(Comparator.comparing(FileRef::path));
        require(expected.size()==6 && expected.equals(delivered) && expected.equals(ControlBuild.producerClosure()),"complete exact six-piece accepted runtime required");
        runtime=List.copyOf(expected);
        if(rootAuthorization!=null) {
            Instant rootDeadline=Instant.parse(rootAuthorization.reviewAtUtc());
            if(rootDeadline.isBefore(deadline))deadline=rootDeadline;
            require(Instant.now().isBefore(deadline),"Root runtime authorization expired");
        }
    }

    /** Historical build evidence identifies the archive; the exact fresh standing grants this execution window. */
    private void verifyPackagedSource(FileRef actualRef) throws Exception {
        actualRef.verify();
        Path own=Path.of(SharedOwnedCommand.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toAbsolutePath().normalize();
        Path api=Path.of(ControlBuild.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toAbsolutePath().normalize();
        Path config=Path.of(SharedOwnedCommandBinding.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toAbsolutePath().normalize();
        require(Files.isRegularFile(own) && own.equals(api) && own.equals(config),"shared caller and binding must be in the complete packaged tools runtime");
        // The shared completed reader below enforces its recorded profile: legacy 2 MiB or explicit R2 4 MiB.
        ControlBuild.BuildReceipt actual=ControlBuild.verifiedCompletedReceipt(actualRef);
        require(actual.machineId().equals(MACHINE),"qualified package must match bound machine");
        require(actual.targetKind()==ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME,"qualified build-tools runtime required");
        boolean sourceMatched=false;
        for(FileRef pin:actual.sourcePins()) if(sameRef(pin,binding.launcherSourceRef())) sourceMatched=true;
        require(sourceMatched,"bound launcher source must belong to the accepted complete build source graph");
        require(SOURCE.getFileName().toString().equals("SharedOwnedCommand.java"),"packaged shared source identity required");
        require(Set.copyOf(actual.completeDeployment()).equals(Set.copyOf(ControlBuild.producerClosure())),"accepted package must be this loaded complete runtime");
    }

    record StandingPreflight(Slot primary, Slot borrowed, Instant deadline) { }

    /** Pure pre-child metadata checks shared by authorization and typed whole-entry production. */
    static StandingPreflight validateStanding(Request request, SharedOwnedCommandBinding binding, JsonNode standing) throws Exception {
        SharedOwnedCommandBinding.verifyAuthority(standing,binding.standingExpectation(),binding.machineId());
        require(request.machineId().equals(binding.machineId()),"request/binding machine differs");
        equalRef(request.standingRef(),binding.standingRef());
        equalRef(request.launcherSourceRef(),binding.launcherSourceRef());
        require(request.owner().matches("/root/[a-z0-9_/-]+"),"canonical Root task owner required");
        require(path(text(standing,"native_tmp_root")).equals(binding.nativeTemporaryRoot()),"exact approved native tmp root required");
        require(path(text(standing,"private_temporary_aggregate_root")).equals(binding.privateTemporaryAggregateRoot()),"exact standing private temporary aggregate root required");
        Instant deadline=Instant.parse(text(standing,"review_at_utc")); require(Instant.now().isBefore(deadline),"standing runtime expired");
        ref(object(standing,"source_grant_ref")).verify(); ref(object(standing,"capacity_release_ref")).verify();
        require(request.operationCardRef()==null && request.temporaryPolicy()==TemporaryPolicy.SLOT_PRIVATE,
                "packaged ordinary caller requires null operation card and SLOT_PRIVATE");
        Slot primary=findSlot(standing,request.slotId());
        long allowedMemory=primary.workerMemoryLimitBytes();
        Slot borrowed=null;
        if(request.borrowedSlotId()!=null) {
            require(request.coordinator().equals("/root/g2_java_delivery"),"only delivery coordinates a common slot loan");
            require(request.borrowedSlotId().matches("common-[0-3]") && !request.borrowedSlotId().equals(request.slotId()),"one distinct common slot loan required");
            borrowed=findSlot(standing,request.borrowedSlotId());
            allowedMemory=Math.addExact(allowedMemory,Math.addExact(borrowed.workerMemoryLimitBytes(),borrowed.outerMemoryBudgetBytes()));
        }
        require(request.memoryLimitBytes()>0 && request.memoryLimitBytes()<=allowedMemory,"worker memory exceeds its standing slot(s)");
        require(request.timeoutSeconds()>0 && request.timeoutSeconds()<=primary.timeoutSeconds(),"finite timeout exceeds group allowance");
        require(primary.outerMemoryBudgetBytes()==(256L<<20),"expected 256MiB outer reservation");
        requireCommandOutputRoot(request.outputRoot(),primary.outputRoot(),request.owner(),request.runId());
        SharedSourceFiles.plainAncestors(request.cwd()); require(Files.isDirectory(request.cwd(),LinkOption.NOFOLLOW_LINKS),"ordinary existing cwd required");
        String executableName=path(request.executable().path()).getFileName().toString().toLowerCase(java.util.Locale.ROOT);
        require(!Set.of("powershell.exe","pwsh.exe","cmd.exe","bash.exe","sh.exe","wscript.exe","cscript.exe").contains(executableName),"shell launch is outside mechanical argv scope");
        boolean allowed=false;
        for(JsonNode entry:array(standing,"allowed_executables")) { FileRef pin=ref(entry); if(sameRef(request.executable(),pin)) { pin.verify(); allowed=true; } }
        require(allowed,"exact fresh standing executable required");
        return new StandingPreflight(primary,borrowed,deadline);
    }

    static FileRef strictFileRef(JsonNode value) throws IOException { return ref(value); }

    static CiBootstrap.JavaUtf8Invocation.ClassCarrier javaCarrier(List<FileRef> exactRuntime) throws IOException {
        require(exactRuntime.size()==6,"Original exact six-file runtime carrier required");
        var pins=new ArrayList<CiBootstrap.JavaUtf8Invocation.ClasspathPin>();
        for(FileRef pin:exactRuntime) { pin.verify(); pins.add(CiBootstrap.JavaUtf8Invocation.captureClasspath(path(pin.path()))); }
        return new CiBootstrap.JavaUtf8Invocation.ClassCarrier(List.copyOf(pins));
    }

    static Path javaEvidenceRoot(Path slotRoot,String owner,String runId,boolean outer) throws IOException {
        Path command=commandOutputRoot(slotRoot,owner,runId);
        return command.resolveSibling(runId+(outer?"-outer-java-utf8":"-child-java-utf8"));
    }

    static void requireJavaEvidenceRoot(CiBootstrap.JavaUtf8Invocation.Request logical,Path expected) throws IOException {
        require(path(logical.evidenceRoot().path()).equals(expected),"Exact separately admitted UTF8 evidence root required");
        require(Files.isDirectory(expected,LinkOption.NOFOLLOW_LINKS),"Issuer-prepared existing UTF8 evidence root required");
        SharedSourceFiles.plainAncestors(expected);
        require(logical.evidenceRoot().equals(CiBootstrap.JavaUtf8Invocation.captureOutputRoot(expected)),
                "UTF8 evidence root native identity differs");
    }

    static void requireLegacyAsciiJava(FileRef executable,List<String> arguments) throws IOException {
        if(path(executable.path()).getFileName().toString().equalsIgnoreCase("java.exe"))
            for(String argument:arguments) require(argument.chars().allMatch(c->c>=32 && c<=126),
                    "Non-ASCII Java argv requires explicit sole-engine UTF8 invocation");
    }

    static Slot findSlot(JsonNode standing,String id) throws IOException {
        Slot found=null;
        for(JsonNode value:array(standing,"slots")) if(text(value,"slot_id").equals(id)) {
            require(found==null && bool(value,"serial"),"unique serial slot required");
            found=new Slot(id,path(text(value,"output_root")),integer(value,"output_cap_bytes"),
                    integer(value,"worker_memory_limit_bytes"),integer(value,"outer_memory_budget_bytes"),integer(value,"timeout_seconds"));
        }
        require(found!=null,"unassigned slot id"); return found;
    }

    private Outcome run() throws Exception {
        Path out=request.outputRoot(); SharedSourceFiles.plainAncestors(out);
        require(!Files.exists(out,LinkOption.NOFOLLOW_LINKS),"fresh attempt output required; unknown/finished attempt cannot be replayed");
        Files.createDirectories(out.getParent()); Files.createDirectory(out);
        Path terminalReserve=out.resolve("terminal-reserve.bin"); writeNew(terminalReserve,new byte[65536]);
        writeNew(out.resolve("binding-ref.json"),JSON.writeValueAsBytes(new BindingEvidence("xar.shared-owned-command-binding-evidence/v1",MACHINE,bindingRef)));
        Path temporary=nativeTemporary(); SharedSourceFiles.plainAncestors(temporary); Files.createDirectories(temporary);
        WindowsJobProcess.CommandResult result=null; WindowsJobProcess.JobDiagnosticOutcome diagnostic=null;
        MsvcAuxiliaryPolicy.Outcome auxiliary=request.msvcAuxiliaryBinding()==null?null:
                MsvcAuxiliaryPolicy.notEntered(request.msvcAuxiliaryBinding(),"Compiler has not entered exact auxiliary completion");
        String failure=null; boolean started=false; Check inputPre=Check.NOT_REACHED,inputPost=Check.NOT_REACHED,runtimePost=Check.NOT_REACHED;
        List<String> effectiveArguments=List.of(); FileRef javaEvidenceRef=null,javaNativeEvidenceRef=null; JavaInvocationEvidence javaEvidence=null;
        FileRef rootEvidenceRef=null;WindowsJobProcess.CommandSpec rootCommand=null;
        Check rootPackagePre=Check.NOT_REACHED,rootPackagePost=Check.NOT_REACHED,rootOuterPre=Check.NOT_REACHED,rootOuterPost=Check.NOT_REACHED;
        Path stdout=out.resolve("stdout.log"),stderr=out.resolve("stderr.log");long javaPendingOutputBytes=0;
        try {
            SharedSourceFiles.assertUnchanged(bindingBefore); inputBefore.add(bindingBefore);
            request.executable().verify(); inputBefore.add(SharedSourceFiles.observe(path(request.executable().path())));
            Set<Path> seen=new HashSet<>(); seen.add(path(request.executable().path()));
            for(FileRef pin:request.inputs()) {
                Path input=path(pin.path()); require(!input.startsWith(out),"input cannot be written inside fresh output");
                require(seen.add(input),"duplicate input ref"); pin.verify(); inputBefore.add(SharedSourceFiles.observe(input));
            }
            inputPre=Check.MATCH; guard();
            if(request.preparedRoot()!=null) {
                retainRootOuter();rootOuterPre=Check.MATCH;
                rootPrepared=rootPreparer.prepare(request.preparedRoot());
                rootPrepared.requireFiniteInputs(request.preparedRoot().packageManifest(),request.preparedRoot().invocation());
                rootPrepared.requireManagedOuterRuntime(rootAuthorization.outerClasspath().effective());
                rootPackageSources.addAll(rootPrepared.retainManagedSources());rootPackagePre=Check.MATCH;
                var paths=new org.xar.ck3.control.build.runtime.JavaRuntimeLaunch.ManagedCommandPaths(
                        stdout,stderr,temporary,binding.nativeTemporaryRoot(),request.memoryLimitBytes());
                rootCommand=rootPrepared.managedCommand(request.preparedRoot().packageManifest(),request.preparedRoot().invocation(),paths);
                requirePreparedRootCommand(request,rootCommand,paths,rootPrepared.environment());
                // Slow preparation never extends the original window or bypasses the original guards.
                authorize();guard();verifyRootRetained();verifyRootOuterCurrent();guard();
                effectiveArguments=rootCommand.arguments();
            } else effectiveArguments=effectiveArguments(temporary);
            if(request.javaInvocation()!=null) {
                var carrier=javaCarrier(runtime); var options=effectiveVmOptions(temporary);
                var logical=CiBootstrap.JavaUtf8Invocation.inspect(effectiveArguments,carrier,options);
                requireJavaEvidenceRoot(logical,javaEvidenceRoot(primary.outputRoot(),request.owner(),request.runId(),false));
                var evidence=new JavaInvocationEvidence("xar.shared-owned-command-java-evidence/v2",request.javaInvocation(),runtime,
                        effectiveArguments,options,JavaPreparationState.PRE_LAUNCH,null,null);
                long currentEvidence=JSON.writeValueAsBytes(evidence).length;
                // The logical request and complete preparation stay in their sole binary codec, without duplicate JSON trees.
                // The preparation uses the existing shared native witness, while JDK metadata stays in the sole binary.
                long sidecars=Math.addExact(2L*currentEvidence,6L*CiBootstrap.JavaUtf8Invocation.preparationPath(logical).toString().getBytes(java.nio.charset.StandardCharsets.UTF_8).length+16384L);
                long pending=Math.addExact(CiBootstrap.JavaUtf8Invocation.maximumOutputBytes(logical),sidecars);
                javaPendingOutputBytes=pending;
                require(Math.addExact(slotAllocated(),Math.addExact(pending,65536L))<=primary.outputCapBytes(),
                        "UTF8 engine and bounded actual sidecars exceed admitted slot");
                javaEvidence=evidence;
                Path evidencePath=out.resolve("java-invocation.json");writeJavaEvidence(evidencePath,evidence);
                javaEvidenceRef=FileRef.measure(evidencePath);
                verifyJavaEvidence(javaEvidenceRef);
            }
            Map<String,String> environment=new TreeMap<>(String.CASE_INSENSITIVE_ORDER); environment.putAll(System.getenv());
            environment.remove("JAVA_TOOL_OPTIONS"); environment.remove("JDK_JAVA_OPTIONS"); environment.remove("_JAVA_OPTIONS"); environment.remove("JDK_JAVAC_OPTIONS");
            for(String key:request.environment().keySet()) require(!Set.of("JAVA_TOOL_OPTIONS","JDK_JAVA_OPTIONS","_JAVA_OPTIONS","JDK_JAVAC_OPTIONS").contains(key.toUpperCase(java.util.Locale.ROOT)),"JVM option environment is controlled by shared caller");
            environment.putAll(request.environment()); environment.put("TEMP",temporary.toString()); environment.put("TMP",temporary.toString());
            environment.put("PYTHONDONTWRITEBYTECODE","1");
            var command=rootCommand!=null?rootCommand:
                    new WindowsJobProcess.CommandSpec(path(request.executable().path()),effectiveArguments,request.cwd(),environment,stdout,stderr,request.memoryLimitBytes());
            var carrier=request.javaInvocation()==null?null:javaCarrier(runtime);
            var launch=request.javaInvocation()==null?null:CiBootstrap.JavaUtf8Invocation.launch(request.javaInvocation().publication(),carrier,effectiveVmOptions(temporary));
            if(launch!=null) require(launch.physicalArguments().equals(effectiveArguments),"Native custody must bind the original physical argv");
            try(var images=request.msvcAuxiliaryBinding()==null?null:
                        MsvcAuxiliaryPolicy.retain(request.msvcAuxiliaryBinding(),deadline,this::periodic);
                    var custody=launch==null?null:JavaUtf8NativeCustody.acquire(launch,carrier)) {
                if(custody!=null) {
                    long quoted=custody.maximumEvidenceBytes(path(request.executable().path()));
                    require(Math.addExact(slotAllocated(),Math.addExact(quoted,Math.addExact(javaPendingOutputBytes,65536L)))<=primary.outputCapBytes(),
                            "Actual native continuity evidence and engine output exceed original slot cap");
                }
                if(request.preparedRoot()!=null) {verifyRootRetained();guard();}
                try(var child=WindowsJobProcess.start(command)) {
                    started=true;if(custody!=null) custody.attach(child);
                    if(images==null) {
                        var awaited=child.await(Duration.ofSeconds(request.timeoutSeconds()),deadline,custody==null?this::periodic:custody.guard(this::periodic),
                                out.resolve("before-cleanup.json"),request.rootExitDrainPolicy());
                        result=awaited.commandResult(); diagnostic=awaited.diagnostic();
                    } else {
                        var awaited=child.awaitWithMsvcAuxiliaries(Duration.ofSeconds(request.timeoutSeconds()),deadline,
                                this::periodic,out.resolve("before-cleanup.json"),images);
                        result=awaited.original().commandResult(); diagnostic=awaited.original().diagnostic();
                        auxiliary=awaited.auxiliaryCleanup();
                    }
                    if(custody!=null) {
                        var sources=custody.verifyTerminal(result);
                        Path nativePath=out.resolve("java-native-source-continuity.json");
                        byte[] nativeBytes=JavaUtf8NativeCustody.encodeEvidence(sources.evidence());
                        require(Math.addExact(slotAllocated(),Math.addExact(roundAllocation(nativeBytes.length),65536L))<=primary.outputCapBytes(),"Native evidence exceeds original slot cap");
                        writeNew(nativePath,nativeBytes);javaNativeEvidenceRef=FileRef.measure(nativePath);
                        JavaUtf8NativeCustody.requireCurrent(sources.evidence(),launch,carrier);
                    }
                }
            }
        } catch(Exception error) { failure=describe(error); if(inputPre!=Check.MATCH) inputPre=Check.FAILED; }
        if(javaEvidence!=null && started) {
            try {
                var logical=CiBootstrap.JavaUtf8Invocation.read(javaEvidence.invocation().publication());
                Path preparation=CiBootstrap.JavaUtf8Invocation.preparationPath(logical);
                if(Files.exists(preparation,LinkOption.NOFOLLOW_LINKS)) {
                    require(javaNativeEvidenceRef!=null,"Original native custody terminal proof required before prepared evidence");
                    var pin=SharedSourceFiles.observe(preparation);
                    CiBootstrap.JavaUtf8Invocation.inspectPreparation(CiBootstrap.JavaUtf8Invocation.captureFile(preparation),request.javaInvocation().publication());
                    var completed=new JavaInvocationEvidence(javaEvidence.schema(),javaEvidence.invocation(),javaEvidence.carrierRuntime(),
                            javaEvidence.physicalArguments(),javaEvidence.effectiveAsciiVmOptions(),JavaPreparationState.PREPARED,pin,javaNativeEvidenceRef);
                    Path evidencePath=out.resolve("java-invocation-prepared.json");writeJavaEvidence(evidencePath,completed);
                    javaEvidenceRef=FileRef.measure(evidencePath);verifyJavaEvidence(javaEvidenceRef);
                } else require(result==null || !result.passed(),"Successful UTF8 child has no original engine preparation receipt");
            } catch(Exception error) { failure=append(failure,"java_preparation: "+describe(error)); }
        }
        try { if(inputPre==Check.MATCH) { for(Witness pin:inputBefore) SharedSourceFiles.assertUnchanged(pin); inputPost=Check.MATCH; } }
        catch(Exception error) { inputPost=Check.FAILED; failure=append(failure,"input_postcheck: "+describe(error)); }
        try {
            bindingRef.verify(); requestRef.verify(); request.launcherSourceRef().verify(); STANDING.verify(); DELIVERY.verify();
            if(javaEvidenceRef!=null) verifyJavaEvidence(javaEvidenceRef);
            for(FileRef pin:runtime) pin.verify(); runtimePost=Check.MATCH;
        } catch(Exception error) { runtimePost=Check.FAILED; failure=append(failure,"runtime_postcheck: "+describe(error)); }
        if(request.preparedRoot()!=null) {
            try {
                require(rootPrepared!=null && rootPackagePre==Check.MATCH,"Actual package preparation not reached");
                rootPrepared.verifyCurrent();verifyRootRetained();rootPackagePost=Check.MATCH;
            }catch(Exception error) {rootPackagePost=Check.FAILED;failure=append(failure,"root_package_postcheck: "+describe(error));}
            try {verifyRootOuterCurrent();verifyRootRetained();rootOuterPost=Check.MATCH;}
            catch(Exception error) {rootOuterPost=Check.FAILED;failure=append(failure,"root_outer_postcheck: "+describe(error));}
            try {
                var evidence=new RootInvocationEvidence("xar.shared-owned-command-root-evidence/v1",rootInvocationRef,
                        request.preparedRoot(),rootAuthorization,rootCommand,rootPackageSources,rootOuterSources,
                        rootPackagePre,rootPackagePost,rootOuterPre,rootOuterPost);
                byte[] body=JSON.writeValueAsBytes(evidence);
                require(body.length<=MAXIMUM_JAVA_EVIDENCE_BYTES,"Bounded Root evidence required");
                require(Math.addExact(slotAllocated(),Math.addExact(roundAllocation(body.length),65536L))<=primary.outputCapBytes(),
                        "Actual Root evidence exceeds admitted output");
                Path evidencePath=out.resolve("root-invocation.json");writeNew(evidencePath,body);rootEvidenceRef=FileRef.measure(evidencePath);
            }catch(Exception error) {failure=append(failure,"root_evidence: "+describe(error));}
        }
        long outputBytes=-1;
        try { outputBytes=slotAllocated(); require(outputBytes<=primary.outputCapBytes()-65536,"output cap/terminal reserve exceeded"); }
        catch(Exception error) { failure=append(failure,"output_postcheck: "+describe(error)); }
        FileRef stdoutRef=null,stderrRef=null;
        try { if(Files.isRegularFile(stdout)) stdoutRef=FileRef.measure(stdout); if(Files.isRegularFile(stderr)) stderrRef=FileRef.measure(stderr); }
        catch(Exception error) { failure=append(failure,"log_postcheck: "+describe(error)); }
        Instant completedAt=Instant.now();
        if(!completedAt.isBefore(deadline)) { runtimePost=Check.FAILED; failure=append(failure,"standing runtime expired at command completion"); }
        Status status=!started?Status.REJECTED:result!=null && result.passed()
                && (auxiliary==null || auxiliary.completed()) && failure==null?Status.PASS:Status.RED;
        Terminal terminal=new Terminal(request.preparedRoot()!=null?"xar.shared-owned-command-terminal/v5":auxiliary!=null?"xar.shared-owned-command-terminal/v3":request.javaInvocation()==null?
                "xar.shared-owned-command-terminal/v2":"xar.shared-owned-command-terminal/v4",MACHINE,completedAt.toString(),status,
                request.owner(),request.slotId(),request.borrowedSlotId(),requestRef,STANDING,request.launcherSourceRef(),runtime,
                new Outer(Long.toString(ProcessHandle.current().pid()),primary.outerMemoryBudgetBytes(),false,
                        "Packaged outer JVM is a conservative reservation; no outer hard Job is claimed. Child and descendants are in the hard Job."),
                started,result,diagnostic,inputPre,inputPost,runtimePost,failure,List.copyOf(inputBefore),effectiveArguments,
                stdoutRef,stderrRef,outputBytes,0,0,javaEvidenceRef,auxiliary,rootEvidenceRef);
        byte[] terminalBytes=encodeTerminal(terminal,true);
        long now=0; boolean censusOk=true;
        try { now=slotAllocated(); } catch(Exception error) { censusOk=false; failure=append(failure,"terminal_census: "+describe(error)); }
        long growth=roundAllocation(terminalBytes.length);
        if(!censusOk || now+growth>primary.outputCapBytes()) {
            terminal=new Terminal(terminal.schema(),terminal.machineId(),terminal.observedAtUtc(),Status.RED,terminal.owner(),terminal.slotId(),
                    terminal.borrowedSlotId(),terminal.requestRef(),terminal.standingRef(),terminal.launcherSourceRef(),terminal.completeRuntime(),
                    terminal.outer(),terminal.childStarted(),terminal.child(),terminal.diagnostic(),terminal.inputPrecheck(),terminal.inputPostcheck(),
                    terminal.runtimePostcheck(),append(terminal.failure(),"full terminal snapshot exceeds output cap; actual child retained in compact terminal"),
                    List.of(),List.of(),terminal.stdoutRef(),terminal.stderrRef(),censusOk?now:-1,0,0,terminal.javaInvocationEvidenceRef(),terminal.auxiliaryCleanup(),terminal.rootInvocationEvidenceRef());
            terminalBytes=encodeTerminal(terminal,false); status=Status.RED;
            require(terminalBytes.length<=65536,"compact actual-child terminal exceeds its preallocated64KiB reservation");
        }
        if(!censusOk || now+roundAllocation(terminalBytes.length)>primary.outputCapBytes()) {
            try(FileChannel channel=FileChannel.open(terminalReserve,StandardOpenOption.WRITE)) {
                ByteBuffer buffer=ByteBuffer.wrap(terminalBytes); while(buffer.hasRemaining()) channel.write(buffer);
                channel.truncate(terminalBytes.length); channel.force(true);
            }
            Files.move(terminalReserve,out.resolve("terminal.json"),java.nio.file.StandardCopyOption.ATOMIC_MOVE);
        } else { writeNew(out.resolve("terminal.json"),terminalBytes); }
        try { require(slotAllocated()<=primary.outputCapBytes(),"actual terminal allocation exceeds output cap"); }
        catch(IOException error) {
            status=Status.RED;
            if(Files.exists(terminalReserve,LinkOption.NOFOLLOW_LINKS)) {
                Terminal compact=new Terminal(terminal.schema(),terminal.machineId(),terminal.observedAtUtc(),Status.RED,terminal.owner(),terminal.slotId(),
                        terminal.borrowedSlotId(),terminal.requestRef(),terminal.standingRef(),terminal.launcherSourceRef(),terminal.completeRuntime(),
                        terminal.outer(),terminal.childStarted(),terminal.child(),terminal.diagnostic(),terminal.inputPrecheck(),terminal.inputPostcheck(),
                        terminal.runtimePostcheck(),append(terminal.failure(),"final_cap_observation: "+describe(error)),List.of(),List.of(),
                        terminal.stdoutRef(),terminal.stderrRef(),-1,0,0,terminal.javaInvocationEvidenceRef(),terminal.auxiliaryCleanup(),terminal.rootInvocationEvidenceRef());
                replaceFromTerminalReserve(terminalReserve,out.resolve("terminal.json"),encodeTerminal(compact,false));
            }
            System.err.println("FINAL_CAP_OBSERVATION_FAILED actual RED terminal retained: "+describe(error));
        }
        if(Files.exists(terminalReserve,LinkOption.NOFOLLOW_LINKS)) Files.delete(terminalReserve);
        System.out.println("SHARED_COMMAND "+status+" child="+(result==null?"UNAVAILABLE":result.exitCode())+" Job="+(result==null?"UNAVAILABLE":result.accounting().activeProcesses())+" terminal="+out.resolve("terminal.json"));
        return new Outcome(status,FileRef.measure(out.resolve("terminal.json")));
    }

    static byte[] encodeTerminal(Terminal terminal,boolean pretty) throws IOException {
        com.fasterxml.jackson.databind.node.ObjectNode wire=JSON.valueToTree(terminal);
        if(!terminal.schema().equals("xar.shared-owned-command-terminal/v3")) wire.remove("auxiliary_cleanup");
        if(!terminal.schema().equals("xar.shared-owned-command-terminal/v5"))wire.remove("root_invocation_evidence_ref");
        return pretty?JSON.writerWithDefaultPrettyPrinter().writeValueAsBytes(wire):JSON.writeValueAsBytes(wire);
    }

    static void requirePreparedRootCommand(Request request,WindowsJobProcess.CommandSpec command,
            org.xar.ck3.control.build.runtime.JavaRuntimeLaunch.ManagedCommandPaths paths,Map<String,String> preparedEnvironment)throws IOException {
        var expected=new TreeMap<String,String>(String.CASE_INSENSITIVE_ORDER);
        expected.putAll(preparedEnvironment);expected.put("PYTHONDONTWRITEBYTECODE","1");
        require(command.executable().equals(path(request.executable().path())) && command.cwd().equals(request.cwd())
                && command.stdout().equals(paths.stdout()) && command.stderr().equals(paths.stderr())
                && command.memoryLimitBytes()==request.memoryLimitBytes() && command.memoryLimitBytes()==paths.memoryLimitBytes()
                && command.environment().equals(expected),"Prepared Root CommandSpec differs from admitted executable/cwd/logs/environment/memory");
        require(paths.temporaryRoot().toString().equals(command.environment().get("TEMP"))
                && paths.temporaryRoot().toString().equals(command.environment().get("TMP"))
                && command.arguments().contains("-Djava.io.tmpdir="+paths.temporaryRoot())
                && command.arguments().contains("-Djna.tmpdir="+paths.nativeScratchRoot()),
                "Prepared Root temporary and native scratch paths differ from original admission");
    }
    private void retainRootOuter()throws Exception {
        verifyRootOuterCurrent();
        var all=new ArrayList<FileRef>(rootAuthorization.outerClasspath().effective());
        all.add(rootInvocationRef);all.add(request.preparedRoot().rootRuntimeAuthorizationRef());
        for(FileRef ref:all) {
            var witness=SharedSourceFiles.observe(path(ref.path()));
            require(witness.source().equals(ref),"Exact actual Root outer source required");rootOuterSources.add(witness);
        }
        verifyRootOuterCurrent();
    }
    private void verifyRootRetained()throws IOException {
        for(Witness witness:rootPackageSources)SharedSourceFiles.assertUnchanged(witness);
        for(Witness witness:rootOuterSources)SharedSourceFiles.assertUnchanged(witness);
    }
    private void verifyRootOuterCurrent()throws Exception {
        rootInvocationRef.verify();
        var actual=SourceGraphCommandSpecProducer.readRootAuthorization(rootInvocation);
        require(actual.equals(rootAuthorization),"Original Root runtime authorization changed");
        SourceGraphCommandSpecProducer.requireRootOuterRuntime(actual);
        var loader=SharedOwnedCommand.class.getClassLoader();
        SourceGraphCommandSpecProducer.requireRootProvider(actual,SourceGraphCommandSpecProducer.RootProvider.ROOT_LAUNCHER,
                Class.forName("org.xar.ck3.control.service.root.RootRuntimeLaunchCommand",false,loader));
        SourceGraphCommandSpecProducer.requireRootProvider(actual,SourceGraphCommandSpecProducer.RootProvider.ROOT_PREPARER,rootPreparer.getClass());
        SourceGraphCommandSpecProducer.requireRootProvider(actual,SourceGraphCommandSpecProducer.RootProvider.NATIVE_VERIFIER,
                Class.forName("org.xar.ck3.control.service.root.RootPackageNativeVerifier",false,loader));
    }

    private List<String> effectiveArguments(Path temporary) throws IOException {
        if(request.javaInvocation()!=null)
            return CiBootstrap.JavaUtf8Invocation.launch(request.javaInvocation().publication(),javaCarrier(runtime),effectiveVmOptions(temporary)).physicalArguments();
        requireLegacyAsciiJava(request.executable(),request.arguments());
        List<String> result=new ArrayList<>(boundVmOptions(temporary));
        for(String argument:request.arguments()) { requireCallerOption(argument); result.add(argument); }
        return List.copyOf(result);
    }
    private List<String> effectiveVmOptions(Path temporary) throws IOException {
        var options=new ArrayList<>(boundVmOptions(temporary));
        for(String option:request.javaInvocation().asciiVmOptions()) { requireCallerOption(option); options.add(option); }
        return List.copyOf(options);
    }
    private List<String> boundVmOptions(Path temporary) throws IOException {
        List<String> result=new ArrayList<>();
        String name=path(request.executable().path()).getFileName().toString().toLowerCase(java.util.Locale.ROOT);
        String prefix=name.equals("javac.exe")?"-J-":name.equals("java.exe")?"-":"";
        if(!prefix.isEmpty()) {
            result.add(prefix+"Djava.io.tmpdir="+temporary); result.add(prefix+"Djna.tmpdir="+binding.nativeTemporaryRoot());
            String xx=prefix+"XX:"; result.add(xx+"ErrorFile="+request.outputRoot().resolve("hs_err_pid%p.log"));
            result.add(xx+"ReplayDataFile="+request.outputRoot().resolve("replay_pid%p.log"));
            result.add(xx+"HeapDumpPath="+request.outputRoot());
        }
        return List.copyOf(result);
    }
    private static void requireCallerOption(String argument) throws IOException {
        require(argument.indexOf('\0')<0,"NUL in argv");
        require(!argument.startsWith("-Djava.io.tmpdir=") && !argument.startsWith("-Djna.tmpdir=")
                && !argument.startsWith("-J-Djava.io.tmpdir=") && !argument.startsWith("-J-Djna.tmpdir="),"temporary roots are bound by the shared caller");
        require(!argument.matches("-J?-?XX:(ErrorFile|ReplayDataFile|HeapDumpPath)=.*"),"JVM crash outputs are bound by the shared caller");
    }
    /** Reads only the new explicit evidence wire; old terminals have no UTF8 provenance to infer. */
    public static CiBootstrap.JavaUtf8Invocation.Request verifyJavaEvidence(FileRef exactEvidence) throws IOException {
        require(exactEvidence.bytes()<=MAXIMUM_JAVA_EVIDENCE_BYTES,"Bounded UTF8 command evidence required");exactEvidence.verify();
        byte[] bytes;try(var in=Files.newInputStream(path(exactEvidence.path()))) { bytes=in.readNBytes(Math.toIntExact(exactEvidence.bytes()+1)); }
        BoundedSourceInputGuard.verifyReadBytes(exactEvidence,bytes,MAXIMUM_JAVA_EVIDENCE_BYTES);
        JsonNode wire=JSON.readTree(bytes);
        exactKeys(wire,Set.of("schema","invocation","carrier_runtime","physical_arguments","effective_ascii_vm_options",
                "preparation_state","preparation_ref","native_evidence_ref"));
        require(text(wire,"schema").equals("xar.shared-owned-command-java-evidence/v2"),"Explicit UTF8 native-witness evidence version required");
        JavaInvocation invocation=JSON.treeToValue(object(wire,"invocation"),JavaInvocation.class);
        var carrierRefs=new ArrayList<FileRef>();for(JsonNode item:array(wire,"carrier_runtime")) carrierRefs.add(ref(item));
        var physical=texts(array(wire,"physical_arguments"));var options=texts(array(wire,"effective_ascii_vm_options"));
        var carrier=javaCarrier(carrierRefs);
        var launched=CiBootstrap.JavaUtf8Invocation.launch(invocation.publication(),carrier,options);
        require(launched.physicalArguments().equals(physical),"Recorded UTF8 publication/physical argv differs");
        var logical=CiBootstrap.JavaUtf8Invocation.inspect(physical,carrier,options);
        String state=text(wire,"preparation_state");
        if(state.equals(JavaPreparationState.PREPARED.name())) {
            var preparation=JSON.treeToValue(object(wire,"preparation_ref"),Witness.class);
            SharedSourceFiles.assertUnchanged(preparation);
            require(path(preparation.source().path()).equals(CiBootstrap.JavaUtf8Invocation.preparationPath(logical)),"Original preparation path differs");
            CiBootstrap.JavaUtf8Invocation.inspectPreparation(CiBootstrap.JavaUtf8Invocation.captureFile(path(preparation.source().path())),invocation.publication());
            JavaUtf8NativeCustody.requireCurrent(readNativeEvidence(ref(object(wire,"native_evidence_ref"))),launched,carrier);
        } else {
            require(state.equals(JavaPreparationState.PRE_LAUNCH.name()) && field(wire,"preparation_ref").isNull() && field(wire,"native_evidence_ref").isNull(),
                    "Explicit pre-launch or actual prepared evidence required");
        }
        exactEvidence.verify();return logical;
    }
    static JavaUtf8NativeCustody.Evidence readNativeEvidence(FileRef exact) throws IOException {
        require(exact.bytes()<=JavaUtf8NativeCustody.MAXIMUM_EVIDENCE_BYTES,"Bounded actual native continuity evidence required");exact.verify();
        byte[] body;try(var in=Files.newInputStream(path(exact.path()))) { body=in.readNBytes(Math.toIntExact(exact.bytes()+1)); }
        BoundedSourceInputGuard.verifyReadBytes(exact,body,JavaUtf8NativeCustody.MAXIMUM_EVIDENCE_BYTES);
        var value=JavaUtf8NativeCustody.decodeEvidence(body);exact.verify();return value;
    }
    private void writeJavaEvidence(Path path,JavaInvocationEvidence evidence) throws IOException {
        byte[] bytes=JSON.writeValueAsBytes(evidence);
        require(bytes.length<=MAXIMUM_JAVA_EVIDENCE_BYTES,"Finite UTF8 evidence wire exceeded");
        require(Math.addExact(slotAllocated(),Math.addExact(roundAllocation(bytes.length),65536L))<=primary.outputCapBytes(),
                "Original slot cannot cover exact UTF8 evidence and terminal reserve");
        writeNew(path,bytes);
    }
    private void guard() throws Exception {
        require(Instant.now().isBefore(deadline),"standing runtime expired"); bindingRef.verify(); requestRef.verify(); request.launcherSourceRef().verify(); STANDING.verify(); DELIVERY.verify();
        for(Witness pin:inputBefore) SharedSourceFiles.assertUnchanged(pin);
        if(request.preparedRoot()!=null)verifyRootRetained();
        require(slotAllocated()<=primary.outputCapBytes()-65536,"slot output cap or terminal reserve exceeded");
    }
    private void periodic() { try { guard(); } catch(Exception error) { throw new IllegalStateException(describe(error),error); } }
    private Path nativeTemporary() { return binding.privateTemporaryAggregateRoot().resolve(request.slotId().replace('/','_')).resolve(request.owner().substring(6).replace('/','_')).resolve(request.runId()); }
    private long slotAllocated() throws IOException { return Math.addExact(allocated(primary.outputRoot()),allocated(binding.privateTemporaryAggregateRoot().resolve(request.slotId().replace('/','_')))); }
    static long allocated(Path root) throws IOException {
        if(Files.notExists(root,LinkOption.NOFOLLOW_LINKS)) return 0;
        require(Files.exists(root,LinkOption.NOFOLLOW_LINKS),"owned output root existence unavailable: "+root);
        final long[] measured={0};
        Files.walkFileTree(root,new java.nio.file.SimpleFileVisitor<Path>() {
            @Override public java.nio.file.FileVisitResult preVisitDirectory(Path dir,java.nio.file.attribute.BasicFileAttributes attrs) throws IOException {
                try {
                    if(!plainMutableAncestors(dir)) return java.nio.file.FileVisitResult.SKIP_SUBTREE; require(!attrs.isSymbolicLink() && !attrs.isOther(),"plain owned output directory required: "+dir);
                } catch(IOException error) {
                    if(!dir.equals(root) && Files.notExists(dir,LinkOption.NOFOLLOW_LINKS)) return java.nio.file.FileVisitResult.SKIP_SUBTREE;
                    throw new IOException("owned mutable-output directory metadata failed: "+dir,error);
                }
                measured[0]=Math.addExact(measured[0],4096); return java.nio.file.FileVisitResult.CONTINUE;
            }
            @Override public java.nio.file.FileVisitResult visitFile(Path file,java.nio.file.attribute.BasicFileAttributes attrs) throws IOException {
                try {
                    require(attrs.isRegularFile() && !attrs.isSymbolicLink() && !attrs.isOther(),"plain owned output file required: "+file);
                    measured[0]=Math.addExact(measured[0],mutableFileAllocation(file));
                } catch(IOException error) {
                    if(!Files.notExists(file,LinkOption.NOFOLLOW_LINKS)) throw new IOException("owned mutable-output metadata failed: "+file,error);
                }
                return java.nio.file.FileVisitResult.CONTINUE;
            }
            @Override public java.nio.file.FileVisitResult visitFileFailed(Path file,IOException error) throws IOException {
                if(!file.equals(root) && error instanceof java.nio.file.NoSuchFileException) return java.nio.file.FileVisitResult.CONTINUE;
                throw new IOException("owned output walk failed: "+file,error);
            }
            @Override public java.nio.file.FileVisitResult postVisitDirectory(Path dir,IOException error) throws IOException {
                if(error!=null && (dir.equals(root) || !(error instanceof java.nio.file.NoSuchFileException))) throw new IOException("owned directory walk failed: "+dir,error);
                return java.nio.file.FileVisitResult.CONTINUE;
            }
        });
        return measured[0];
    }
    private static JsonNode parse(Path path) throws IOException { JsonNode value=JSON.readTree(Files.readAllBytes(path)); require(value!=null && value.isObject(),"JSON object required"); return value; }
    private static JsonNode field(JsonNode value,String key) throws IOException { require(value.isObject() && value.has(key),"missing field: "+key); return value.get(key); }
    private static JsonNode object(JsonNode value,String key) throws IOException { JsonNode result=field(value,key); require(result.isObject(),"object required: "+key); return result; }
    private static JsonNode array(JsonNode value,String key) throws IOException { JsonNode result=field(value,key); require(result.isArray(),"array required: "+key); return result; }
    private static String text(JsonNode value,String key) throws IOException { JsonNode result=field(value,key); require(result.isTextual(),"string required: "+key); return result.textValue(); }
    private static String nullableText(JsonNode value,String key) throws IOException { JsonNode result=field(value,key); require(result.isNull() || result.isTextual(),"explicit null/string required: "+key); return result.isNull()?null:result.textValue(); }
    private static long integer(JsonNode value,String key) throws IOException { JsonNode result=field(value,key); require(result.isIntegralNumber() && result.canConvertToLong(),"exact integer required: "+key); return result.longValue(); }
    private static boolean bool(JsonNode value,String key) throws IOException { JsonNode result=field(value,key); require(result.isBoolean(),"boolean required: "+key); return result.booleanValue(); }
    private static List<String> texts(JsonNode array) throws IOException { List<String> result=new ArrayList<>(); for(JsonNode value:array) { require(value.isTextual(),"string argv required"); result.add(value.textValue()); } return List.copyOf(result); }
    private static FileRef ref(JsonNode value) throws IOException { exactKeys(value,Set.of("path","bytes","sha256")); return new FileRef(path(text(value,"path")).toString(),integer(value,"bytes"),text(value,"sha256")); }
    private static Path path(String value) throws IOException { Path path=Path.of(value); require(path.isAbsolute(),"absolute path required"); return path.toAbsolutePath().normalize(); }
    private static void equalRef(FileRef left,FileRef right) throws IOException { require(path(left.path()).equals(path(right.path())) && left.bytes()==right.bytes() && left.sha256().equals(right.sha256()),"exact reference mismatch"); }
    private static void exactKeys(JsonNode value,Set<String> keys) throws IOException { require(value!=null && value.isObject() && value.size()==keys.size(),"exact object fields required"); for(var item:value.properties()) require(keys.contains(item.getKey()),"unknown field: "+item.getKey()); }
    private static void writeNew(Path target,byte[] data) throws IOException { SharedSourceFiles.plainAncestors(target); try(FileChannel out=FileChannel.open(target,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE)) { ByteBuffer bytes=ByteBuffer.wrap(data); while(bytes.hasRemaining()) out.write(bytes); out.force(true); } }
    private static long roundAllocation(long bytes) { return Math.multiplyExact(Math.addExact(bytes,4095)/4096,4096); }
    private static String describe(Exception error) { return error.getClass().getSimpleName()+": "+error.getMessage(); }
    private static String append(String first,String next) { return first==null?next:first+"; "+next; }
    private static void require(boolean condition,String message) throws IOException { if(!condition) throw new IOException(message); }

    private static FileRef nullableRef(JsonNode value,String key) throws IOException { JsonNode item=field(value,key); return item.isNull()?null:ref(item); }
    private static TemporaryPolicy temporaryPolicy(JsonNode value) throws IOException { try { return TemporaryPolicy.valueOf(text(value,"temporary_policy")); } catch(IllegalArgumentException error) { throw new IOException("unknown typed temporary policy",error); } }
    private static boolean sameRef(FileRef a,FileRef b) throws IOException { return path(a.path()).equals(path(b.path())) && a.bytes()==b.bytes() && a.sha256().equals(b.sha256()); }

    /** Mutable output only: native missing2/3 can race CREATE_NEW/replace; reparse and access failures remain fatal. */
    private static boolean plainMutableAncestors(Path path) throws IOException {
        Path current=path.toAbsolutePath().normalize();
        while(current!=null) {
            int attrs=com.sun.jna.platform.win32.Kernel32.INSTANCE.GetFileAttributes(extendedWindowsPath(current));
            if(attrs==-1) {
                int error=com.sun.jna.Native.getLastError();
                if(error==2 || error==3) return false;
                throw new IOException("mutable path attribute Win32="+error+" path="+current);
            }
            require((attrs&0x400)==0,"mutable output reparse path rejected: "+current);
            current=current.getParent();
        }
        return true;
    }
    private static long mutableFileAllocation(Path file) throws IOException {
        IOException last=null;
        for(int attempt=0;attempt<4;attempt++) {
            if(!plainMutableAncestors(file)) return 0;
            try { return nativeMutableAllocation(file); }
            catch(IOException error) { last=error; if(!plainMutableAncestors(file)) return 0; }
        }
        throw new IOException("bounded mutable metadata retries exhausted: "+file,last);
    }


    private static final class MutableApi {
        private static final SharedSourceFiles.AttributeApi VALUE=com.sun.jna.Native.load("kernel32",SharedSourceFiles.AttributeApi.class);
    }
    private static String extendedWindowsPath(Path path) throws IOException {
        require(path.isAbsolute(),"absolute mutable Windows path required"); String value=path.toAbsolutePath().normalize().toString();
        if(value.startsWith("\\\\?\\")) return value;
        if(value.startsWith("\\\\")) return "\\\\?\\UNC\\"+value.substring(2);
        require(value.matches("[A-Za-z]:\\\\.*"),"canonical Windows drive or UNC path required");
        return "\\\\?\\"+value;
    }
    private static long nativeMutableAllocation(Path file) throws IOException {
        var handle=com.sun.jna.platform.win32.Kernel32.INSTANCE.CreateFile(extendedWindowsPath(file),0x80,7,null,3,0x00200000,null);
        if(com.sun.jna.platform.win32.WinBase.INVALID_HANDLE_VALUE.equals(handle)) {
            int error=com.sun.jna.Native.getLastError(); if(error==2 || error==3) return 0;
            throw new IOException("mutable extended metadata open Win32="+error+" path="+file);
        }
        try(com.sun.jna.Memory basic=new com.sun.jna.Memory(40); com.sun.jna.Memory standard=new com.sun.jna.Memory(24)) {
            require(MutableApi.VALUE.GetFileInformationByHandleEx(handle,0,basic,40)
                    && MutableApi.VALUE.GetFileInformationByHandleEx(handle,1,standard,24),"mutable extended metadata query failed: "+file);
            require((basic.getInt(32)&0x400)==0 && standard.getByte(21)==0,"mutable native regular non-reparse file required: "+file);
            long allocated=standard.getLong(0); require(allocated>=0,"nonnegative native allocation required: "+file); return allocated;
        } finally { require(com.sun.jna.platform.win32.Kernel32.INSTANCE.CloseHandle(handle),"mutable metadata handle close failed: "+file); }
    }


    private static void replaceFromTerminalReserve(Path reserve,Path target,byte[] bytes) throws IOException {
        require(bytes.length<=65536,"compact actual terminal exceeds preallocated64KiB");
        try(FileChannel channel=FileChannel.open(reserve,StandardOpenOption.WRITE)) {
            ByteBuffer buffer=ByteBuffer.wrap(bytes); while(buffer.hasRemaining()) channel.write(buffer);
            channel.truncate(bytes.length); channel.force(true);
        }
        Files.move(reserve,target,java.nio.file.StandardCopyOption.ATOMIC_MOVE,java.nio.file.StandardCopyOption.REPLACE_EXISTING);
    }

}
