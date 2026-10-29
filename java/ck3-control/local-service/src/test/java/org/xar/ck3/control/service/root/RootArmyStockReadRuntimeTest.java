package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.ServiceLoader;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarSupplementalReadCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarSupplementalReads;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarSupplementalReads.DefenderStock;

/** Mandatory actual Root inputs; absence is a failure, never a skipped or synthetic admission. */
public final class RootArmyStockReadRuntimeTest {
    @Test public void originalRootConfigurationSuppliesTheIdenticalPairPinsAndExplicitCheckout()throws Exception {
        var actual=RootDriverProductSourcesFactoryTest.actual();
        var prepared=actual.definitions().catalogFactory().sources().army();
        var configuration=prepared.stockConfiguration().orElseThrow(()->new IOException("MISSING_NOT_RUN: actual Root stock configuration original"));
        var sources=prepared.stockSources().orElseThrow(()->new IOException("MISSING_NOT_RUN: actual catalog stock sources"));
        assertSame(configuration.pair(),sources.pair());assertSame(configuration.pins(),sources.pins());
        assertEquals(configuration.input().nativeSourceCheckout(),sources.nativeSourceCheckout());
        assertEquals(Path.of(sources.pair().path()),configuration.input().pairPath());
        assertEquals(Path.of(sources.pins().path()),configuration.input().pinsPath());
        assertSame(prepared,actual.definitions().catalogFactory().sources().army());
        byte[] wire=StrictJson.canonical(ControlBuild.strictMapper().valueToTree(configuration),1<<20);
        var restored=ControlBuild.strictMapper().readValue(wire,RootArmyStockReadRuntime.Configuration.class);
        assertEquals(configuration,restored);
    }
    @Test public void actualConfiguredSourceFactsRejectCrossRoleAndAmbiguousSerializedInputs()throws Exception {
        var prepared=RootDriverProductSourcesFactoryTest.actual().definitions().catalogFactory().sources().army();
        var configured=prepared.stockConfiguration().orElseThrow(()->new IOException("MISSING_NOT_RUN: actual Root stock configuration original"));
        assertThrows(IllegalArgumentException.class,()->new RootArmyStockReadRuntime.Configuration(
                configured.input(),configured.limits(),configured.pins(),configured.pair()));
        var mapper=ControlBuild.strictMapper();
        var original=mapper.valueToTree(configured);
        for(String field:List.of("pair","pins","limits","input")) {
            var missing=original.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)missing).remove(field);
            assertThrows(IOException.class,()->mapper.readValue(StrictJson.canonical(missing,1<<20),RootArmyStockReadRuntime.Configuration.class));
            var wrong=original.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)wrong).put(field,true);
            assertThrows(IOException.class,()->mapper.readValue(StrictJson.canonical(wrong,1<<20),RootArmyStockReadRuntime.Configuration.class));
        }
        var extra=original.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)extra).put("stockEnabled",true);
        assertThrows(IOException.class,()->mapper.readValue(StrictJson.canonical(extra,1<<20),RootArmyStockReadRuntime.Configuration.class));
    }
    /** A whole-Root fixture must have already issued, decoded and preserved this real stock read once.
     * No test provider, fake Core, guessed frame or new Native submission is supplied by this class. */
    public interface ActualStockReads {void withDedicatedOriginal(Check test)throws Exception;}
    @FunctionalInterface public interface Check {
        void check(RootInstalledCatalog installed,Session same,ArmyWarSupplementalReads.Selection selected,
                PlanningReadResult.Known<ArmyWarSupplementalReads.Observation> original)throws Exception;
    }
    @Test public void actualLiveOriginalReplaysAfterRetirementWithoutOpeningAnotherMailboxOwner()throws Exception {
        var providers=ServiceLoader.load(ActualStockReads.class).stream().map(ServiceLoader.Provider::get).toList();
        if(providers.size()!=1)throw new IOException("MISSING_NOT_RUN: one actual matching Release/SavedGame stock-read Root fixture required");
        var called=new AtomicBoolean();
        providers.getFirst().withDedicatedOriginal((catalog,same,selected,known)->{
            if(!called.compareAndSet(false,true))throw new IOException("actual dedicated stock fixture invoked twice");
            var context=catalog.context();context.writer().requireSession(same);
            var army=catalog.army();var products=army.products();
            var runtime=products.stockReads().orElseThrow(()->new IOException("MISSING_NOT_RUN: installed actual stock runtime"));
            var value=assertInstanceOf(DefenderStock.class,known.value());
            var reads=products.supplementalWarReads();var issued=reads.issue(context.readCatalog(),selected);
            assertTrue(context.readCatalog().containsIdentity(issued.contract()));
            assertEquals(known.originalReceipt(),context.archive().withSession(same).readReferenceOf(known.receipt()));
            assertEquals(value.actualMailboxSequence(),value.evidence().mailboxSequence());
            byte[] expected=ArmyWarSupplementalReadCodec.fullDriverResult(value).bytes();
            for(int i=0;i<2;i++) {
                var replay=reads.replayArchived(context.readCatalog(),selected,known.originalReceipt(),context.archive().withSession(same));
                assertArrayEquals(expected,ArmyWarSupplementalReadCodec.fullDriverResult(replay).bytes());
                assertSame(runtime,army.products().stockReads().orElseThrow());
            }
            // The same live receipt is not a second admitted mailbox. Archive replay above does not advance it.
            assertThrows(RuntimeException.class,()->issued.contract().decode(known.receipt()));
            army.close();army.close();
            var cold=reads.replayArchived(context.readCatalog(),selected,known.originalReceipt(),context.archive().withSession(same));
            assertArrayEquals(expected,ArmyWarSupplementalReadCodec.fullDriverResult(cold).bytes());
            assertThrows(RuntimeException.class,()->issued.contract().decode(known.receipt()));
            assertEquals(DriverJson.object(expected,DriverJson.MAX_NATIVE_BYTES),
                    DriverJson.object(ArmyWarSupplementalReadCodec.fullDriverResult(cold).bytes(),DriverJson.MAX_NATIVE_BYTES));
        });
        if(!called.get())throw new IOException("MISSING_NOT_RUN: actual dedicated stock fixture did not supply its original read");
    }
}
