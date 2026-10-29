package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.finance.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;

/** Invokes the actual preCore registration and the identical install-time catalog. No Core/Game authority is minted. */
final class FinanceRuntimeDomainBoundsTest {
    private static ExactRef ref(String name) { return new ExactRef("D:/fixture/finance-source-"+name+".java",1,"a".repeat(64)); }
    private static FinanceReadContracts.Registration read(String name,String operation) {
        return new FinanceReadContracts.Registration(ref(name),new FinanceReadContracts.Permission(Optional.empty(),operation,
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP));
    }
    private static FinanceRuntimeInstaller.Prepared prepared() {
        var fixed=List.of(FinanceReadContracts.Query.ROOT,FinanceReadContracts.Query.CASH,FinanceReadContracts.Query.MERCENARIES,
                FinanceReadContracts.Query.CONSTRUCTION,FinanceReadContracts.Query.FACTION_GIFT,FinanceReadContracts.Query.FACTION_GIFT_RECEIPT)
                .stream().map(query->new FinanceRuntimeInstaller.ReadSource(query,read(query.name(),query.operation().value()))).toList();
        var sources=new FinanceRuntimeInstaller.Sources(new OrdinaryFinanceFactory.Sources(ref("policy"),ref("hireMaterial"),ref("giftMaterial"),ref("quote")),
                ref("readCodec"),ref("hireAck"),ref("mercenaryDomain"),ref("mercenaryReducer"),ref("warPriority"),ref("factionDefinition"),ref("factionCodec"),
                ref("giftDomain"),ref("giftBodyCodec"),ref("giftReducer"),fixed,List.of(),
                new FinanceRuntimeInstaller.GiftColdSources(read("coldNative",GiftColdReadService.OPERATION.value()),ref("coldCodec"),ref("coldClassifier"),
                        ref("coldClassifierCodec"),ref("coldProvider"),ref("coldProcessIdentity")));
        return new FinanceRuntimeInstaller.Prepared(sources);
    }

    @Test void bothScopedFinanceProducersUseTheExactImportRequestCanonicalInputDomain() {
        Obj original=OrdinaryFinanceCollector.obj("kind",new Text("actual_fresh_campaign_finance_body"),
                "initial_basis",OrdinaryFinanceCollector.obj("path",new Text("D:/original-basis.bin"),"bytes",new IntegerValue(java.math.BigInteger.valueOf(4969)),
                        "sha256",new Text("a".repeat(64))),"episode",new Text("actual-episode"),
                "initial_frame",OrdinaryFinanceCollector.obj("revision",new IntegerValue(java.math.BigInteger.valueOf(31)),
                        "player",new IntegerValue(java.math.BigInteger.valueOf(31254)),"date_raw",new IntegerValue(java.math.BigInteger.valueOf(53144328))),
                "explicit_null",Nil.INSTANCE,"ordered",new Arr(List.of(new Text("first"),new Text("second"))));
        var raw=new org.xar.ck3.control.application.action.RawJson(encode(original));
        for(DomainBodies.Slot slot:List.of(DomainBodies.Slot.MERCENARY,DomainBodies.Slot.FACTION)) {
            byte[] canonical=slot==DomainBodies.Slot.MERCENARY?MercenaryDomainSource.canonicalInput(raw):GiftDomainSource.canonicalInput(raw);
            var request=new DomainBodies.ImportRequest(slot,"fixture.finance-input/v1",ref("body"),raw.bytes(),List.of(ref("native-evidence")),"actual-input");
            assertFalse(java.util.Arrays.equals(raw.bytes(),request.producerInput()),"the raw inserted order reproduces worker18");
            assertArrayEquals(request.producerInput(),canonical);
            assertEquals(original,object(parse(canonical),"complete canonical finance input"));
            assertEquals(List.of(ref("native-evidence")),request.evidence());
            var reordered=new java.util.LinkedHashMap<String,Value>();
            original.members().entrySet().stream().sorted(java.util.Map.Entry.comparingByKey()).forEach(entry->reordered.put(entry.getKey(),entry.getValue()));
            assertArrayEquals(canonical,MercenaryDomainSource.canonicalInput(new org.xar.ck3.control.application.action.RawJson(encode(new Obj(reordered)))));
            for(Obj changed:List.of(original.with("explicit_null",new Bool(false)),
                    original.with("initial_frame",object(original.get("initial_frame"),"frame").with("revision",new Bool(true))),
                    original.with("ordered",new Arr(List.of(new Text("second"),new Text("first")))))) {
                var altered=new org.xar.ck3.control.application.action.RawJson(encode(changed));
                assertFalse(java.util.Arrays.equals(canonical,MercenaryDomainSource.canonicalInput(altered)));
                assertFalse(java.util.Arrays.equals(canonical,GiftDomainSource.canonicalInput(altered)));
            }
        }
        var nonObject=new org.xar.ck3.control.application.action.RawJson("[]".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        assertThrows(IllegalArgumentException.class,()->MercenaryDomainSource.canonicalInput(nonObject));
        assertThrows(IllegalArgumentException.class,()->GiftDomainSource.canonicalInput(nonObject));
    }

    @Test void actualPreparedRegistrationsAndInstallCatalogUseTheSameExistingDomainBound() {
        var actual=prepared();var registrations=actual.registrations();var bindings=actual.bodyBindings();
        assertEquals(2,registrations.size());assertEquals(2,bindings.size());
        for(var registered:registrations) {
            assertEquals(ContinuityJson.DOMAIN_MAX_BYTES,registered.maximumBodyBytes());
            var bound=bindings.stream().filter(binding->binding.slot()==registered.slot()).findFirst().orElseThrow();
            assertEquals(registered.contractSchema(),bound.contractSchema());
            assertEquals(registered.maximumBodyBytes(),bound.maximumBodyBytes());
            assertEquals(registered.producerSources(),bound.actualProducerSources());
        }
        assertSame(registrations.getFirst(),actual.registrations().getFirst());
        assertTrue(bindings.stream().filter(binding->binding.slot()==DomainBodies.Slot.FACTION).findFirst().orElseThrow()
                .actualProducerSources().contains(ref("coldProcessIdentity")));
    }

    @Test void actualRegisteredMercenaryReaderAcceptsTheBoundaryThroughSharedSerializationAndPreservesExtensions() {
        var binding=prepared().bodyBindings().stream().filter(value->value.slot()==DomainBodies.Slot.MERCENARY).findFirst().orElseThrow();
        Obj empty=OrdinaryFinanceCollector.obj("schema",new Text(MercenaryProcurement.SCHEMA),"pending",Nil.INSTANCE,"observed",new Arr(List.of()),
                "original_extension",new Text(""));
        int remaining=binding.maximumBodyBytes()-DriverJson.encode(empty).length;
        byte[] raw=DriverJson.encode(empty.with("original_extension",new Text("x".repeat(remaining))));
        assertEquals(binding.maximumBodyBytes(),raw.length);
        byte[] shared=ContinuityJson.canonical(ContinuityJson.parseObject(raw,binding.maximumBodyBytes()),binding.maximumBodyBytes());
        var decoded=MercenaryProcurement.decode(shared);assertTrue(decoded.pending().isEmpty());
        var original=new ExactRef("D:/fixture/actual-boundary-mercenary-body.json",shared.length,ActionCodec.sha256(shared));
        var document=new FinanceStatePort.Document(FinanceStatePort.Domain.MERCENARY,original,shared);
        assertEquals(FinanceStatePort.Pending.CLEAR,binding.decoder().reader().decode(document));
        assertTrue(CanonicalFinanceStateSource.sameOriginalBody(raw,shared,binding.maximumBodyBytes()));
        byte[] oversized=DriverJson.encode(empty.with("original_extension",new Text("x".repeat(remaining+1))));
        assertThrows(IllegalArgumentException.class,()->CanonicalFinanceStateSource.originalBody(oversized,binding.maximumBodyBytes()));
        assertThrows(IllegalArgumentException.class,()->ContinuityJson.parseObject(oversized,binding.maximumBodyBytes()));
    }

    @Test void freshMercenaryProducerHasNoInventoryTransitionAcrossReceivedFrameChanges() {
        var binding=prepared().bodyBindings().stream().filter(value->value.slot()==DomainBodies.Slot.MERCENARY).findFirst().orElseThrow();
        var fresh=MercenaryProcurement.emptyFreshEpisode();byte[] body=MercenaryProcurement.encode(fresh);
        assertTrue(fresh.pending().isEmpty());assertTrue(fresh.observed().isEmpty());
        var original=new ExactRef("D:/fixture/worker41-empty-mercenary-body.json",body.length,ActionCodec.sha256(body));
        assertEquals(FinanceStatePort.Pending.CLEAR,binding.decoder().reader().decode(new FinanceStatePort.Document(FinanceStatePort.Domain.MERCENARY,original,body)));
        for(int revision:List.of(102,103)) {
            Obj snapshot=OrdinaryFinanceCollector.obj("snapshot_id",new Text("native:"+revision),"revision",new IntegerValue(java.math.BigInteger.valueOf(revision-95)),
                    "native_revision",new IntegerValue(java.math.BigInteger.valueOf(revision)),"date_raw",new IntegerValue(java.math.BigInteger.valueOf(53144328)),
                    "episode_run_id",new Text("resume63_vanilla_game02_20261029"),"played_character",OrdinaryFinanceCollector.obj("character_id",new IntegerValue(java.math.BigInteger.valueOf(31254))),
                    "active_wars",new Arr(List.of()),"player_armies",new Arr(List.of()));
            assertArrayEquals(body,MercenaryProcurement.encode(MercenaryProcurement.refreshInventory(MercenaryProcurement.decode(body),snapshot)),
                    "an empty original ledger cannot gain employment, payment, army attribution or an inventory transition");
        }
    }

    @Test void aReadCatalogCannotAdvertiseALargerBodyThanTheActualWriterRegistrationSupports() {
        var actual=prepared().bodyBindings().getFirst();
        for(int wrong:new int[]{0,-1,ContinuityJson.DOMAIN_MAX_BYTES+1,4*1024*1024})
            assertThrows(IllegalArgumentException.class,()->new CanonicalFinanceStateSource.Binding(actual.decoder(),actual.slot(),actual.contractSchema(),wrong,actual.actualProducerSources()));
        assertDoesNotThrow(()->new CanonicalFinanceStateSource.Binding(actual.decoder(),actual.slot(),actual.contractSchema(),ContinuityJson.DOMAIN_MAX_BYTES,actual.actualProducerSources()));
    }
}
