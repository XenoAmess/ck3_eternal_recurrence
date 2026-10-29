package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Physical original-reader adapter bound to the identical live writer. No ledger, Driver or game writes. */
public final class OriginalRollbackFiles {
    public record Document(ExactRef reference,WriterContracts.Pin pin,byte[] bytes) {
        public Document {Objects.requireNonNull(reference);Objects.requireNonNull(pin);bytes=bytes.clone();
            StrictJson.require(reference.equals(pin.reference())&&reference.bytes()==bytes.length&&reference.sha256().equals(DriverJson.sha256(bytes)),"complete physical original document required");}
        @Override public byte[] bytes(){return bytes.clone();}
        public Obj object(){return DriverJson.object(bytes,Math.toIntExact(reference.bytes()));}
    }
    private final ContinuityWriter writer;
    private final CheckpointFiles files;
    public OriginalRollbackFiles(ContinuityWriter actualWriter,CheckpointFiles actualFiles) {
        writer=Objects.requireNonNull(actualWriter);files=Objects.requireNonNull(actualFiles);
    }
    public Scope open(ContinuityStorePort.Session borrowed,WriterContracts.Head original) throws IOException {
        writer.requireSession(borrowed);Objects.requireNonNull(original);
        var retained=borrowed.requireHistoricalState(original.state().sequence(),original.digest());
        StrictJson.require(ContinuityJson.same(retained.toJson(),original.state().toJson()),"original rollback predecessor is not this writer's actual canonical ancestry");
        return new Scope(borrowed,original);
    }
    /** Minted only after the actual writer has proved original ancestry. A Scope is a reader, never qualification. */
    public final class Scope {
        private final ContinuityStorePort.Session borrowed;
        private final WriterContracts.Head original;
        private final Thread owner=Thread.currentThread();
        private final LinkedHashMap<ExactRef,Document> documents=new LinkedHashMap<>();
        private final LinkedHashMap<Path,List<Path>> directories=new LinkedHashMap<>();
        private final List<Path> absent=new ArrayList<>();
        private Scope(ContinuityStorePort.Session borrowed,WriterContracts.Head original){this.borrowed=borrowed;this.original=original;}
        public ContinuityStorePort.Session session(){return borrowed;}
        public WriterContracts.Head originalHead(){return original;}
        public void requireCanonicalLedger(Path snapshot)throws IOException {
            requireOwner();Path actual=absolute(snapshot);String name=actual.getFileName().toString();
            StrictJson.require(name.endsWith(".json")&&actual.resolveSibling(name.substring(0,name.length()-5)+".lock").equals(writer.originalLockPath()),
                    "rollback frontier belongs to another actual canonical ledger/writer lock");
        }
        public Document read(ExactRef reference,int maximum) throws IOException {
            requireOwner();Objects.requireNonNull(reference);Document existing=documents.get(reference);
            if(existing!=null){StrictJson.require(existing.reference().bytes()<=maximum,"original document exceeds consumer bound");borrowed.verifyPin(existing.pin());return existing;}
            StrictJson.require(documents.size()<240,"finite original rollback closure requires a smaller explicit source inventory");
            var actual=RootRestoreMaterials.readPinned(borrowed,files,reference,maximum);
            var result=new Document(reference,actual.pin(),actual.contents());documents.put(reference,result);return result;
        }
        public Obj object(ExactRef reference,int maximum) throws IOException {return read(reference,maximum).object();}
        public void requireAbsent(Path path) throws IOException {
            requireOwner();Path normalized=absolute(path);StrictJson.require(!Files.exists(normalized,LinkOption.NOFOLLOW_LINKS),"original unsubmitted slot has physical dispatch context");
            if(!absent.contains(normalized))absent.add(normalized);
        }
        public List<Path> jsonFiles(Path directory,int maximumEntries) throws IOException {
            requireOwner();Path normalized=absolute(directory);List<Path> actual=enumerate(normalized,maximumEntries);
            List<Path> before=directories.putIfAbsent(normalized,actual);
            StrictJson.require(before==null||before.equals(actual),"actual physical original request inventory changed");return actual;
        }
        public List<WriterContracts.Pin> pins(){return documents.values().stream().map(Document::pin).toList();}
        public void requireCurrent() throws IOException {
            requireOwner();for(Document document:documents.values())borrowed.verifyPin(document.pin());
            for(Path path:absent)StrictJson.require(!Files.exists(path,LinkOption.NOFOLLOW_LINKS),"original unsubmitted slot appeared during recovery verification");
            for(var entry:directories.entrySet())StrictJson.require(enumerate(entry.getKey(),4096).equals(entry.getValue()),"original physical inventory drifted after qualification");
        }
        private void requireOwner() throws IOException {
            StrictJson.require(Thread.currentThread()==owner,"original rollback reader escaped its owning thread");writer.requireSession(borrowed);
        }
    }
    private static Path absolute(Path path) {Objects.requireNonNull(path);StrictJson.require(path.isAbsolute()&&path.normalize().equals(path),"normalized absolute original evidence path required");return path;}
    private static List<Path> enumerate(Path directory,int maximum) throws IOException {
        StrictJson.require(maximum>0&&maximum<=4096&&Files.isDirectory(directory,LinkOption.NOFOLLOW_LINKS)&&!Files.isSymbolicLink(directory),"actual original bounded evidence directory required");
        var result=new ArrayList<Path>();
        try(var stream=Files.newDirectoryStream(directory,"*.json")) {
            for(Path entry:stream) {
                StrictJson.require(Files.isRegularFile(entry,LinkOption.NOFOLLOW_LINKS)&&!Files.isSymbolicLink(entry)&&result.size()<maximum,"original inventory includes an unsafe or excess entry");
                result.add(entry.toAbsolutePath().normalize());
            }
        }
        return result.stream().sorted().toList();
    }
}
