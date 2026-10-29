package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Path;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;

/** Calls the actual factory with actual store constructors. No private Stage/SAVE/Root authority or physical IO is fabricated. */
final class RootM7CheckpointCaptureFactoryTest {
    @TempDir Path temporary;
    private record Stores(CheckpointCommitVerifier pairs,DriverCheckpointStore drivers,SavedAttachmentSourceStore sources) { }
    private static AssertionError noAuthority() { return new AssertionError("store construction/lookup must not access writer, archive, Driver, Native or Game"); }
    private RootM7CheckpointCaptureFactory factory() {
        var writer=new ContinuityStorePort() {
            public WriterContracts.Prepared preview(WriterContracts.Request request) { throw noAuthority(); }
            public WriterContracts.Receipt commit(WriterContracts.Prepared prepared) { throw noAuthority(); }
            public ExactRef persistedHead() { throw noAuthority(); }
            public <T>T locked(SessionWork<T> work) { throw noAuthority(); }
        };
        var actions=new ActionJournal() {
            public <T>T locked(Function<LockedJournal,T> operation) { throw noAuthority(); }
        };
        return new RootM7CheckpointCaptureFactory(writer,same->{throw noAuthority();},actions,new DenyArchive(),owner->{throw noAuthority();});
    }
    private Stores stores(String name) {
        var files=new NativeCheckpointFiles();Path root=temporary.resolve(name).toAbsolutePath();
        var drivers=new DriverCheckpointStore(files,root.resolve("driver.json"),"actual-software-constructor-pipe",new DriverCheckpointStore.SnapshotSupplier() {
            public <T>T withFrozen(DriverCheckpointStore.SnapshotWork<T> work) { throw noAuthority(); }
        });
        var pairs=new CheckpointCommitVerifier(files,drivers,(same,owner,semantic)->{throw noAuthority();},root.resolve("writer.lock"),
                same->{throw noAuthority();},(same,owner,pair,proof)->{throw noAuthority();});
        var sources=new SavedAttachmentSourceStore(files,drivers,pairs,()->{throw noAuthority();},root.resolve("materials"),
                (same,owner,proof)->{throw noAuthority();},(same,owner,proof,head)->{throw noAuthority();});
        return new Stores(pairs,drivers,sources);
    }
    @Test void actualFactoryRetainsDistinctStoreTripletsAcrossNewGameStagingWithoutReplacingTheFirst() throws Exception {
        var factory=factory();var first=stores("first");var next=stores("next");
        var firstCapture=factory.create(first.pairs(),first.drivers(),first.sources());
        var firstInputs=factory.requireInputs(first.pairs(),first.drivers(),first.sources());
        var nextCapture=factory.create(next.pairs(),next.drivers(),next.sources());
        var nextInputs=factory.requireInputs(next.pairs(),next.drivers(),next.sources());
        assertNotSame(firstCapture,nextCapture);assertNotSame(firstInputs,nextInputs);
        assertSame(firstCapture,factory.create(first.pairs(),first.drivers(),first.sources()));
        assertSame(nextCapture,factory.create(next.pairs(),next.drivers(),next.sources()));
        assertSame(firstInputs,factory.requireInputs(first.pairs(),first.drivers(),first.sources()));
        assertSame(nextInputs,factory.requireInputs(next.pairs(),next.drivers(),next.sources()));
        assertSame(firstCapture,factory.requireCapture(first.pairs(),first.drivers(),first.sources()));
        assertSame(nextCapture,factory.requireCapture(next.pairs(),next.drivers(),next.sources()));
    }
    @Test void missingOrMixedStoreObjectsCannotAcquireAnotherGamesOriginalConsumers() throws Exception {
        var factory=factory();var first=stores("first");var next=stores("next");
        assertThrows(IOException.class,()->factory.requireInputs(first.pairs(),first.drivers(),first.sources()));
        var original=factory.create(first.pairs(),first.drivers(),first.sources());
        assertThrows(IOException.class,()->factory.requireCapture(next.pairs(),next.drivers(),next.sources()));
        assertThrows(IllegalArgumentException.class,()->factory.create(first.pairs(),next.drivers(),next.sources()));
        assertThrows(IllegalArgumentException.class,()->factory.create(next.pairs(),first.drivers(),next.sources()));
        assertThrows(IllegalArgumentException.class,()->factory.create(next.pairs(),next.drivers(),first.sources()));
        assertThrows(IOException.class,()->factory.requireInputs(next.pairs(),next.drivers(),first.sources()));
        assertSame(original,factory.requireCapture(first.pairs(),first.drivers(),first.sources()));
    }
    private static final class DenyArchive implements ActionPorts.OutcomeArchive {
        public ExactRef preserve(NativeActionPort.DispatchOutcome original) { throw noAuthority(); }
        public NativeActionPort.DispatchOutcome load(ExactRef original) { throw noAuthority(); }
        public ExactRef preserveRequest(NativeRequest original) { throw noAuthority(); }
        public NativeRequest loadRequest(ExactRef original) { throw noAuthority(); }
        public ExactRef referenceOf(NativeActionPort.DispatchOutcome original) { throw noAuthority(); }
        public ExactRef requestReferenceOf(NativeRequest original) { throw noAuthority(); }
        public ExactRef preserveRead(PlanningReadReceipt original) { throw noAuthority(); }
        public PlanningReadReceipt loadRead(ExactRef original) { throw noAuthority(); }
        public ExactRef readReferenceOf(PlanningReadReceipt original) { throw noAuthority(); }
        public ExactRef preserveRecord(ActionRecord original) { throw noAuthority(); }
        public ActionRecord loadRecord(ExactRef original) { throw noAuthority(); }
        public ExactRef recordReferenceOf(ActionRecord original) { throw noAuthority(); }
        public ExactRef preserveReceipt(ActionReceipt original) { throw noAuthority(); }
        public ActionReceipt loadReceipt(ExactRef original) { throw noAuthority(); }
        public ExactRef receiptReferenceOf(ActionReceipt original) { throw noAuthority(); }
        public ExactRef preserveMaterial(RawJson original) { throw noAuthority(); }
        public RawJson loadMaterial(ExactRef original) { throw noAuthority(); }
        public ExactRef materialReferenceOf(RawJson original) { throw noAuthority(); }
        public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame original) { throw noAuthority(); }
        public byte[] loadNativeFrame(ExactRef original) { throw noAuthority(); }
    }
}
