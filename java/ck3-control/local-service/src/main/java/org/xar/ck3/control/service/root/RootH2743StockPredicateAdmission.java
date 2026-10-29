package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.sun.jna.Native;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.planning.army.H2743StockPredicateAdmission;
import org.xar.ck3.control.application.planning.army.H2743StockPredicateAdmission.FileFact;
import org.xar.ck3.control.application.planning.army.H2743StockPredicateAdmission.Input;
import org.xar.ck3.control.application.planning.army.H2743StockPredicateAdmission.VerifiedData;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.SharedSourceFiles.NativeFile;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.platform.NativeLaunchPlan;

/** Actual Root source issuer. DATA decoding cannot construct Admission or extend its thread scope. */
public final class RootH2743StockPredicateAdmission implements AutoCloseable {
    public record Limits(int maximumFiles,long maximumSourceBytes,int maximumDocumentBytes,long maximumReadBytes) {
        public Limits {if(maximumFiles<1||maximumFiles>8192||maximumSourceBytes<1||maximumDocumentBytes<1||maximumDocumentBytes>16777216||maximumReadBytes<1)throw new IllegalArgumentException("explicit finite H2743 custody limits required");}
    }
    private final RootRuntimeContext context;
    private final RootManagedSessionScope managed;
    private final Custody files;
    private final Input input;
    private final VerifiedData data;
    private final ThreadLocal<Admission> active=new ThreadLocal<>();
    private BigInteger lastMailbox=BigInteger.ZERO;
    private boolean closed;
    private RootH2743StockPredicateAdmission(RootRuntimeContext actual,RootManagedSessionScope physical,Input input,Limits limits)throws IOException {
        context=Objects.requireNonNull(actual);managed=Objects.requireNonNull(physical);this.input=Objects.requireNonNull(input);files=new Custody(limits);
        try {
            managed.requireCurrent();context.game().launchPlan().sources().requireLoadedClass(RootH2743StockPredicateAdmission.class);context.game().launchPlan().sources().requireLoadedClass(H2743StockPredicateAdmission.class);
            data=H2743StockPredicateAdmission.verifyStock(input,files);requireOwner();
        } catch(IOException|RuntimeException error){try{files.close();}catch(IOException cleanup){error.addSuppressed(cleanup);}throw error;}
    }
    /** Actual files to pure verifier, for offline provenance checks only. Never returns Admission. */
    public static VerifiedData verifyDataOnly(Input input,Limits limits)throws IOException {
        try(Custody originals=new Custody(limits)) {
            VerifiedData result=H2743StockPredicateAdmission.verifyStock(input,originals);originals.verify();return result;
        }
    }
    /** Only actual Root installation may retain this sole owner; no historical DATA overload exists. */
    public static RootH2743StockPredicateAdmission bind(RootRuntimeContext actual,RootManagedSessionScope physical,Input input,Limits limits)throws IOException {
        return new RootH2743StockPredicateAdmission(actual,physical,input,limits);
    }
    private void requireOwner()throws IOException {
        need(!closed,"stock source custody closed");managed.requireCurrent();context.game().verify();files.verify();
        var review=context.game().launchPlan().sources().review();
        Path checkout=input.nativeSourceCheckout().toRealPath(),nativeRoot=review.nativeSourceRoot().toRealPath();
        // Original manifests resolve repo-relative ck3_autonomous_player/native_bridge paths.
        // A reviewed launch may retain that exact physical subtree, not just the repository root.
        need(nativeRoot.equals(checkout)||nativeRoot.equals(checkout.resolve("ck3_autonomous_player/native_bridge").normalize()),"stock source root is outside its explicit original checkout/native subtree");
        for(var actualSource:context.game().launchPlan().sources().nativeProof().expected().completeSources()) {
            Path actualPath=Path.of(actualSource.path()).toRealPath();
            need(actualPath.startsWith(nativeRoot),"reviewed native source escaped its original root");
            FileFact original=null;for(FileFact f:data.completeFiles())if(f.path().toRealPath().equals(actualPath)){original=f;break;}
            need(original!=null&&original.bytes()==actualSource.bytes()&&original.sha256().equalsIgnoreCase(actualSource.sha256()),"actual complete launch source is missing or differs from the admitted compiled closure");
        }
        JsonNode receipt=DriverJson.toNode(DriverJson.object(data.sourceReceipt().bytes(),16777216));
        requireBinary(receipt.get("dll"),review.bridgeDll().path(),review.bridgeDll().bytes(),review.bridgeDll().sha256());
        requireBinary(receipt.get("injector"),review.injector().path(),review.injector().bytes(),review.injector().sha256());
        need(context.game().launchPlan().load() instanceof NativeLaunchPlan.SavedGame,"H2743 stock baseline requires the actual original saved-game launch");
        NativeLaunchPlan.SavedGame saved=(NativeLaunchPlan.SavedGame)context.game().launchPlan().load();
        JsonNode seed=receipt.get("source_quartet").get("xar_checkpoint.ck3");
        requireBinary(seed,saved.save().path(),saved.save().bytes(),saved.save().sha256());
    }
    private void requireBinary(JsonNode original,String actualPath,long actualBytes,String actualSha)throws IOException {
        need(original!=null&&original.isObject()&&original.path("path").isTextual()&&original.path("sha256").isTextual(),"missing admitted binary/seed original");
        Path p=Path.of(original.get("path").textValue());FileFact fact=files.measure(p);
        need(p.toRealPath().equals(Path.of(actualPath).toRealPath())&&fact.bytes()==actualBytes&&fact.sha256().equalsIgnoreCase(actualSha)&&fact.sha256().equals(original.get("sha256").textValue()),"admitted artifact differs from actual retained launch source");
    }
    public final class Admission {
        private final Thread owner=Thread.currentThread();private final Session same;private final Complete frame;private boolean ended;
        private Admission(Session same,Complete frame){this.same=same;this.frame=frame;}
        public void requireCurrent(Session actualSame,Complete actualFrame)throws IOException {
            need(!ended&&active.get()==this&&Thread.currentThread()==owner&&same==actualSame&&frame==actualFrame,"stock admission escaped its actual original frame/session/thread scope");
            context.writer().requireSession(same);managed.requireFrame(same,frame);requireOwner();
        }
        /** This receipt is DATA; retaining it does not retain this private live capability. */
        public VerifiedData data(Session actualSame,Complete actualFrame)throws IOException {requireCurrent(actualSame,actualFrame);return data;}
    }
    @FunctionalInterface public interface Work<T> {T run(Admission actual)throws IOException,InterruptedException;}
    public synchronized <T>T withAdmission(Session same,Complete actual,Work<T> work)throws IOException,InterruptedException {
        Objects.requireNonNull(work);need(active.get()==null,"recursive stock scope refused");requireOwner();context.writer().requireSession(same);managed.requireFrame(same,actual);
        Admission admission=new Admission(same,actual);active.set(admission);
        try {admission.requireCurrent(same,actual);T result=work.run(admission);admission.requireCurrent(same,actual);return result;}
        finally {admission.ended=true;active.remove();}
    }
    /** Live decoder calls this only after the entire stock envelope has passed its source-owned parser.
     * Archive pure replay does not advance this once-per-original-owner mailbox gate. */
    public synchronized void acceptMailbox(Admission original,Session same,Complete frame,BigInteger actualSequence)throws IOException {
        Objects.requireNonNull(original);original.requireCurrent(same,frame);need(actualSequence!=null&&actualSequence.signum()>0&&actualSequence.bitLength()<=64&&actualSequence.compareTo(lastMailbox)>0,"stock mailbox replay or invalid exact sequence");lastMailbox=actualSequence;
    }
    @Override public synchronized void close()throws IOException {need(active.get()==null,"cannot close active stock scope");if(closed)return;files.close();closed=true;}
    private static void need(boolean ok,String why)throws IOException {if(!ok)throw new IOException("H2743 "+why);}
    private record Held(Path path,HANDLE handle,NativeFile original,boolean directory) { }
    private static final class Custody implements H2743StockPredicateAdmission.Files,AutoCloseable {
        final Limits limits;final Map<Path,Held> held=new LinkedHashMap<>();final Map<Path,FileFact> facts=new LinkedHashMap<>();long sourceBytes,readBytes;boolean closed;
        Custody(Limits limits){this.limits=Objects.requireNonNull(limits);}
        // Preserve the original Win32 spelling without exposing the build package helper.
        private static String heldNativePath(Path path) throws IOException {
            if (path == null || !path.isAbsolute()) throw new IOException("absolute native source path required");
            return heldNativePathValue(path.toAbsolutePath().normalize().toString());
        }
        /** A Path can hide its extended spelling; keep this mechanical conversion independently testable. */
        private static String heldNativePathValue(String value) throws IOException {
            if (value == null || value.indexOf('\0') >= 0) throw new IOException("ordinary absolute Windows spelling required");
            if (value.startsWith("\\\\?\\")) return value;
            if (value.startsWith("\\\\")) return "\\\\?\\UNC\\" + value.substring(2);
            if (!value.matches("[A-Za-z]:\\\\.*")) throw new IOException("canonical Windows drive or UNC path required");
            return "\\\\?\\" + value;
        }
        private Held open(Path path,boolean directory)throws IOException {
            need(!closed,"source custody closed");Path p=path.toAbsolutePath().normalize();Held existing=held.get(p);if(existing!=null){need(existing.directory()==directory,"file/directory role changed");return existing;}
            SharedSourceFiles.plainAncestors(p);need(held.size()<65536,"source handle closure exceeds finite65536");
            HANDLE handle=Kernel32.INSTANCE.CreateFile(heldNativePath(p),directory?0x80:0x80000000,directory?3:1,null,3,0x00200000|(directory?0x02000000:0),null);
            need(handle!=null&&!WinBase.INVALID_HANDLE_VALUE.equals(handle),"held source open failed Win32="+Native.getLastError()+" path="+p);
            try {NativeFile original=directory?SharedSourceFiles.nativeHeldDirectory(handle):SharedSourceFiles.nativeHeldFile(handle);Held result=new Held(p,handle,original,directory);held.put(p,result);return result;}
            catch(IOException|RuntimeException error){Kernel32.INSTANCE.CloseHandle(handle);throw error;}
        }
        private void parents(Path path)throws IOException {List<Path> parents=new ArrayList<>();for(Path p=path.getParent();p!=null;p=p.getParent()){need(parents.size()<64,"source path exceeds64 ancestors");parents.add(p);}for(int i=parents.size()-1;i>=0;i--)open(parents.get(i),true);}
        @Override public FileFact measure(Path original)throws IOException {
            need(original!=null&&original.isAbsolute()&&original.normalize().equals(original),"absolute normalized original source required");Path p=original.normalize();FileFact prior=facts.get(p);if(prior!=null){verifyHeld(held.get(p));return prior;}
            need(facts.size()<limits.maximumFiles(),"source closure exceeds admitted file count");parents(p);Held h=open(p,false);need(h.original().logicalBytes()<=limits.maximumSourceBytes()-sourceBytes,"source bytes exceed finite aggregate limit");
            SharedSourceFiles.Witness witness=SharedSourceFiles.observe(p);need(witness.nativeFile().equals(h.original()),"path and held original differ");FileFact f=new FileFact(p,witness.source().bytes(),witness.source().sha256().toUpperCase(java.util.Locale.ROOT));facts.put(p,f);sourceBytes=Math.addExact(sourceBytes,f.bytes());verifyHeld(h);return f;
        }
        @Override public byte[] read(Path p,int requestedMaximum)throws IOException {
            FileFact f=measure(p);int maximum=Math.min(requestedMaximum,limits.maximumDocumentBytes());need(f.bytes()<=maximum&&f.bytes()<=limits.maximumReadBytes()-readBytes,"provenance read exceeds finite aggregate/document limits");
            byte[] bytes;try(var stream=java.nio.file.Files.newInputStream(p)){bytes=stream.readNBytes(maximum+1);}readBytes=Math.addExact(readBytes,bytes.length);need(bytes.length==f.bytes()&&DriverJson.sha256(bytes).equalsIgnoreCase(f.sha256()),"held document bytes changed");verifyHeld(held.get(p));return bytes;
        }
        private void verifyHeld(Held h)throws IOException {
            need(h!=null,"source has no original held custody");NativeFile actual=h.directory()?SharedSourceFiles.nativeHeldDirectory(h.handle()):SharedSourceFiles.nativeHeldFile(h.handle());need(h.directory()?actual.identityKey().equals(h.original().identityKey()):actual.equals(h.original()),"held original native identity/times/extent changed");
            if(h.directory()){need(SharedSourceFiles.nativeDirectory(h.path()).equals(new SharedSourceFiles.DirectoryIdentity(actual.volumeSerialDecimal(),actual.fileIdDecimal(),actual.creationFiletimeDecimal())),"held parent and path identity changed");}
            else need(SharedSourceFiles.nativeFile(h.path()).equals(actual),"held source and path no longer match");
        }
        void verify()throws IOException {need(!closed,"source custody closed");for(Held h:held.values())verifyHeld(h);}
        @Override public void close()throws IOException {
            if(closed)return;IOException error=null;List<Held> reverse=new ArrayList<>(held.values());for(int i=reverse.size()-1;i>=0;i--){Held h=reverse.get(i);if(!Kernel32.INSTANCE.CloseHandle(h.handle())){IOException e=new IOException("H2743 original custody close failed Win32="+Native.getLastError());if(error==null)error=e;else error.addSuppressed(e);}}closed=true;if(error!=null)throw error;
        }
    }
}
