package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;

/** Genuine configured sources and actual installed Root callbacks only. No ACK, private Source,
 * writer membership, Game or fixture is manufactured. Missing actual inputs fail or remain NOT_RUN. */
public final class RootOperatorNonRebindMaterialTest {
    @Test void genuineConfigurationRetainsTheFixedOperatorOwnerAndStrictSourceWire()throws IOException {
        var actual=RootDriverProductSourcesFactoryTest.actual();var input=actual.factory().retainedInput();
        var owner=input.operatorAuthority();owner.requireInputs(input.inputs(),input.selected());
        assertFalse(owner.sources().isEmpty());
        assertTrue(input.inputs().application().writerSources().containsAll(owner.sources()));
        assertTrue(input.selected().retainedSources().containsAll(owner.sources()));
        input.plan().sources().requireLoadedClass(RootOperatorCharacterAuthority.class);
        input.plan().sources().requireLoadedClass(RootActionHistoryMaterialSourceFactory.class);
        byte[] wire=ControlBuild.strictMapper().writeValueAsBytes(owner.sources());
        var type=ControlBuild.strictMapper().getTypeFactory().constructCollectionType(List.class,ExactRef.class);
        List<ExactRef> restored=ControlBuild.strictMapper().readValue(wire,type);
        assertEquals(owner.sources(),restored);
        assertArrayEquals(wire,ControlBuild.strictMapper().writeValueAsBytes(restored));
        var wrong=ControlBuild.strictMapper().readTree(wire);((ObjectNode)wrong.get(0)).put("bytes",true);
        assertThrows(IOException.class,()->ControlBuild.strictMapper().readValue(ControlBuild.strictMapper().writeValueAsBytes(wrong),type));
        var missing=ControlBuild.strictMapper().readTree(wire);((ObjectNode)missing.get(0)).remove("sha256");
        assertThrows(IOException.class,()->ControlBuild.strictMapper().readValue(ControlBuild.strictMapper().writeValueAsBytes(missing),type));
        var renamed=ControlBuild.strictMapper().readTree(wire);var first=(ObjectNode)renamed.get(0);first.set("digest",first.remove("sha256"));
        assertThrows(IOException.class,()->ControlBuild.strictMapper().readValue(ControlBuild.strictMapper().writeValueAsBytes(renamed),type));
        input.selected().requireInputs(input.inputs());input.selected().requireLoadedClasses(input.plan());actual.factory().requireCurrent();
    }

    /** Invoke for a genuine known-code rejection and again for genuine BEFORE_WRITE zero-dispatch.
     * These retain native_driver.py's finite known-code exception and no-write distinctions. */
    public static void assertActualCanonicalNonRebind(RootActionHistoryMaterialSourceFactory.Prepared prepared,
            RootInstalledCatalog catalog,Session same,DriverActionHistoryPublisher publisher,ActionReceipt actual)throws Exception {
        var context=catalog.context();context.writer().requireSession(same);
        var products=prepared.install(context,catalog);assertSame(products,prepared.install(context,catalog));
        var materials=products.materials();var authority=context.adopted().authority();
        materials.requireOwner(authority,context.core().journal(),context.archive());
        publisher.requireOwner(authority,context.core().journal(),context.archive());
        assertTrue(DriverOperatorNonRebindOriginals.isRecordedNonRebound(actual));
        if(actual.state() instanceof ActionState.Settled settled){
            var rejected=assertInstanceOf(ActionState.Rejected.class,settled.settlement());
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,settled.dispatch());
            assertEquals(rejected.reason(),OperatorPlayerSwitch.knownRejection(ack).orElseThrow().wire());
        }else{
            var zero=assertInstanceOf(ActionState.RejectedBeforeDispatch.class,actual.state());
            assertEquals(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,zero.dispatch().proof().stage());
            assertEquals(0,zero.dispatch().proof().requestBytesWritten());
        }
        assertTrue(materials.sources().containsAll(context.core().operatorAuthority().sources()));
        var originals=context.archive().withSession(same);var before=known(authority,same);String head=same.head().digest();
        var actions=List.copyOf(catalog.bindings().actionBindings());var replays=List.copyOf(catalog.bindings().archivedBindings());
        ExactRef record=ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),actual,originals);
        assertEquals(actual,originals.loadRecord(record).receipt());
        byte[] wire=ActionReceiptCodec.encodeReceipt(actual,originals);
        var decoded=ActionReceiptCodec.decodeReceipt(wire,originals);assertEquals(actual,decoded);
        assertArrayEquals(wire,ActionReceiptCodec.encodeReceipt(decoded,originals));
        context.core().operatorAuthority().requireOperatorWithoutRebind(context,same,decoded,originals);
        materials.requireOperatorWithoutRebind(same,decoded,originals);
        for(int repeat=0;repeat<2;repeat++){
            var disposition=assertInstanceOf(DriverActionHistoryPublisher.Unchanged.class,publisher.completed(same,decoded));
            assertEquals(DriverActionHistoryPublisher.Reason.OPERATOR_NO_REBIND_RECEIPT_VERIFIED,disposition.reason());
        }
        assertFalse(publisher.hasPending(same));assertEquals(actions,catalog.bindings().actionBindings());
        assertEquals(replays,catalog.bindings().archivedBindings());
        sameDriver(before,known(authority,same));assertEquals(head,same.head().digest());
        assertEquals(record,ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),decoded,originals));
        malformedReceiptWire(wire,originals);assertEquals(head,same.head().digest());
    }

    /** Cold context must already be genuinely installed. Reading this historical receipt never
     * resolves or issues its target family. */
    public static void assertActualColdCanonicalNonRebind(RootActionHistoryMaterialSourceFactory.Prepared prepared,
            RootInstalledCatalog actualColdCatalog,Session same,DriverActionHistoryPublisher publisher,ActionReceipt original)throws Exception {
        assertTrue(actualColdCatalog.bindings().actualActionBinding(original.command().operation()).isEmpty());
        assertTrue(actualColdCatalog.bindings().actualArchivedVerifier(original.command().operation()).isEmpty());
        assertActualCanonicalNonRebind(prepared,actualColdCatalog,same,publisher,original);
        assertTrue(actualColdCatalog.bindings().actualActionBinding(original.command().operation()).isEmpty());
        assertTrue(actualColdCatalog.bindings().actualArchivedVerifier(original.command().operation()).isEmpty());
    }

    /** A real canonical UNKNOWN stays unresolved and is never replayed or turned into a rejection. */
    public static void assertActualUnknownNotQualified(RootActionHistoryMaterialSourceFactory.Prepared prepared,
            RootInstalledCatalog catalog,Session same,DriverActionHistoryPublisher publisher,ActionReceipt originalUnknown)throws Exception {
        var context=catalog.context();context.writer().requireSession(same);
        assertInstanceOf(ActionState.Unknown.class,originalUnknown.state());
        assertInstanceOf(CommandExpectation.OperatorRebind.class,originalUnknown.command().expectation());
        var originals=context.archive().withSession(same);
        ExactRef record=ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),originalUnknown,originals);
        var before=known(context.adopted().authority(),same);String head=same.head().digest();
        var materials=prepared.install(context,catalog).materials();
        assertThrows(Exception.class,()->materials.requireOperatorWithoutRebind(same,originalUnknown,originals));
        assertThrows(Exception.class,()->context.core().operatorAuthority().requireOperatorWithoutRebind(context,same,originalUnknown,originals));
        var unchanged=assertInstanceOf(DriverActionHistoryPublisher.Unchanged.class,publisher.completed(same,originalUnknown));
        assertEquals(DriverActionHistoryPublisher.Reason.UNRESOLVED,unchanged.reason());
        assertEquals(originalUnknown,originals.loadRecord(record).receipt());
        sameDriver(before,known(context.adopted().authority(),same));assertEquals(head,same.head().digest());
    }

    /** Both owners must be independently genuine. An uninstalled owner cannot borrow another
     * owner's history even when its source DATA has equal bytes. */
    public static void assertActualUninstalledOwnerRejected(RootOperatorCharacterAuthority.Prepared foreignOwner,
            RootInstalledCatalog actualCatalog,Session same,ActionReceipt actual)throws Exception {
        var context=actualCatalog.context();assertNotSame(foreignOwner,context.core().operatorAuthority());
        String head=same.head().digest();
        assertThrows(IOException.class,()->foreignOwner.requireOperatorWithoutRebind(context,same,actual,context.archive().withSession(same)));
        assertEquals(head,same.head().digest());
    }

    private static void malformedReceiptWire(byte[] actual,ActionPorts.OutcomeArchive archive)throws IOException {
        ObjectNode missing=wire(actual);missing.remove("sequence");
        assertThrows(RuntimeException.class,()->ActionReceiptCodec.decodeReceipt(bytes(missing),archive));
        ObjectNode renamed=wire(actual);renamed.set("body_hash",renamed.remove("body_sha256"));
        assertThrows(RuntimeException.class,()->ActionReceiptCodec.decodeReceipt(bytes(renamed),archive));
        ObjectNode bool=wire(actual);bool.put("sequence",true);
        assertThrows(RuntimeException.class,()->ActionReceiptCodec.decodeReceipt(bytes(bool),archive));
        ObjectNode fraction=wire(actual);fraction.put("sequence",1.0);
        assertThrows(RuntimeException.class,()->ActionReceiptCodec.decodeReceipt(bytes(fraction),archive));
        ObjectNode unknown=wire(actual);unknown.put("operator_policy",true);
        assertThrows(RuntimeException.class,()->ActionReceiptCodec.decodeReceipt(bytes(unknown),archive));
    }
    private static ObjectNode wire(byte[] actual)throws IOException{return ControlBuild.strictMapper().readValue(actual,ObjectNode.class);}
    private static byte[] bytes(ObjectNode row)throws IOException{return ControlBuild.strictMapper().writeValueAsBytes(row);}
    private static DriverSnapshotFacts.Known known(DriverStateAssembler authority,Session same)throws IOException {
        return authority.withFrozenFacts(same,frozen->assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state()));
    }
    private static void sameDriver(DriverSnapshotFacts.Known before,DriverSnapshotFacts.Known after){
        assertSame(before,after);assertEquals(before.stamp(),after.stamp());assertArrayEquals(before.driver().encode(),after.driver().encode());
        assertEquals(before.actionRows(),after.actionRows());assertEquals(before.observation(),after.observation());assertEquals(before.auxiliary(),after.auxiliary());
    }
}
