package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.writer.StorageWriteGuardTestSupport;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.service.root.RootDriverRegistryPublicProducts.Kind;
import org.xar.ck3.control.service.root.RootDriverRegistryPublicProducts.PreparedProduct;
import org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.SelectedSource;

/** Uses the sole actual pre-Core fixture; no source-only index, copied metadata or fake Core grants admission. */
final class RootDriverPreparedSourceRolesPrimaryTest {
    @TempDir Path temporary;

    private record Role(Kind kind,Class<? extends PreparedProduct> type) { }
    private static final List<Role> ROLES=List.of(
            new Role(Kind.GOVERNANCE,RootDriverGovernancePublicSupplier.Prepared.class),
            new Role(Kind.FACTION,RootDriverFactionPublicSupplier.Prepared.class),
            new Role(Kind.HEIR,RootDriverHeirPublicSupplier.Prepared.class),
            new Role(Kind.LIFECYCLE,RootDriverLifecycleRuntimeInstaller.Prepared.class),
            new Role(Kind.TRANSPORT,RootDriverTransportRuntimeFactory.Prepared.class),
            new Role(Kind.FAMILY,RootDriverFamilyPublicProduct.Prepared.class));

    @Test void sixPrimarySlotsRetainTheirActualTypesSourcesAndIdenticalPreparedProducts()throws IOException {
        var actual=RootDriverProductSourcesFactoryTest.actual();
        assertSame(actual.factory(),actual.definitions().driverProductSources());
        assertSame(actual.prepared(),actual.factory().prepare());
        assertSame(actual.sources(),actual.factory().sources());
        for(var role:ROLES) {
            PreparedProduct product=actual.prepared().prepared(role.kind(),role.type());
            assertSame(product,actual.prepared().prepared(role.kind(),role.type()));
            assertSame(product,actual.prepared().products().ordered().get(role.kind().ordinal()));
            assertSame(role.type(),product.getClass());
            assertSame(role.type().getEnclosingClass(),product.source().implementation());
            assertEquals(javaSource(actual.sources().javaProducts(),role.kind()),product.source().selectedSource());
            assertEquals(product.source().selectedSource(),actual.factory().retainedInput().selected().javaSourceAt(
                    product.source().targetRelative(),product.source().implementation()));
        }
        actual.factory().requireDefinitions(actual.definitions().catalogFactory().sources());
    }

    @Test void eachMissingPrimarySourceIsRejectedByTheActualFactoryBeforeAnySecondPreparation()throws IOException {
        var actual=RootDriverProductSourcesFactoryTest.actual();var input=actual.factory().retainedInput();
        for(var role:ROLES) {
            var product=actual.prepared().prepared(role.kind(),role.type());
            var rows=new ArrayList<>(input.inputs().sourceIndex());
            assertTrue(rows.removeIf(source->source.targetRelative().equals(product.source().targetRelative())),role.kind().name());
            rejectUnadmittedSelection(input,new RootRuntimeSelectedSources(rows));
        }
        assertSame(actual.prepared(),actual.factory().prepare());
    }

    @Test void eachForeignPrimarySourceRefIsRejectedEvenWhenTheOtherSourceIsGenuine()throws IOException {
        var actual=RootDriverProductSourcesFactoryTest.actual();var input=actual.factory().retainedInput();
        for(int index=0;index<ROLES.size();index++) {
            var role=ROLES.get(index);var foreignRole=ROLES.get((index+1)%ROLES.size());
            var product=actual.prepared().prepared(role.kind(),role.type());
            ExactRef foreign=javaSource(actual.sources().javaProducts(),foreignRole.kind());
            assertNotEquals(product.source().selectedSource(),foreign);
            var rows=new ArrayList<>(input.inputs().sourceIndex());boolean replaced=false;
            for(int row=0;row<rows.size();row++)if(rows.get(row).targetRelative().equals(product.source().targetRelative())) {
                rows.set(row,new SelectedSource(product.source().targetRelative(),foreign));replaced=true;
            }
            assertTrue(replaced,role.kind().name());
            rejectUnadmittedSelection(input,new RootRuntimeSelectedSources(rows));
        }
        assertSame(actual.prepared(),actual.factory().prepare());
    }

    @Test void eachWrongPrimaryExpectedDigestIsRejectedWithoutTouchingItsActualSource()throws IOException {
        var actual=RootDriverProductSourcesFactoryTest.actual();var input=actual.factory().retainedInput();
        for(var role:ROLES) {
            var product=actual.prepared().prepared(role.kind(),role.type());ExactRef original=product.source().selectedSource();
            var physical=new FileRef(original.path(),original.bytes(),original.sha256());physical.verify();
            String different=original.sha256().equals("0".repeat(64))?"1".repeat(64):"0".repeat(64);
            var wrong=new ExactRef(original.path(),original.bytes(),different);
            var rows=new ArrayList<>(input.inputs().sourceIndex());boolean replaced=false;
            for(int row=0;row<rows.size();row++)if(rows.get(row).targetRelative().equals(product.source().targetRelative())) {
                rows.set(row,new SelectedSource(product.source().targetRelative(),wrong));replaced=true;
            }
            assertTrue(replaced,role.kind().name());rejectUnadmittedSelection(input,new RootRuntimeSelectedSources(rows));
            physical.verify();
        }
        assertSame(actual.prepared(),actual.factory().prepare());
    }

    @Test void actualConfigurationSourceDriftInvalidatesBothTheRetainedFactoryAndStartupEntry()throws IOException {
        var original=RootDriverProductSourcesFactoryTest.actual().definitions().inputs().originalRef();
        byte[] bytes=RootRuntimeDefinitions.read(original,RootRuntimeDefinitions.MAXIMUM_BYTES);
        // This software issuer requires one existing original lock. Configuration IO receives its finite card first.
        Path originalLock=Files.createFile(temporary.resolve("configuration-fixture.lock"));
        try(var storage=StorageWriteGuardTestSupport.create(temporary,originalLock,8L<<20)) {
          storage.requireInitialization(originalLock,List.of(temporary));
          for(boolean replacement:List.of(false,true)) {
            Path copy=temporary.resolve("actual-runtime-definitions-"+replacement+".json");
            StorageWriteGuardTestSupport.atomic(copy,bytes,false);FileRef reference=FileRef.measure(copy);
            // The normal full reader must succeed before a currentness refusal is meaningful.
            var definitions=RootRuntimeDefinitions.readExact(reference,Clock.systemUTC());
            var factory=definitions.driverProductSources();var prepared=factory.prepare();
            factory.requireDefinitions(definitions.catalogFactory().sources());
            assertSame(prepared,factory.prepare());factory.requireCurrent();
            var nativeBefore=SharedSourceFiles.nativeFile(copy);
            if(replacement) {
                // The sole guarded atomic writer creates/pins the new file while the old target still exists,
                // then renames that same native file: the old target's FileID cannot be recycled into it.
                StorageWriteGuardTestSupport.atomic(copy,bytes,true);
                assertEquals(reference,FileRef.measure(copy));
                assertNotEquals(nativeBefore.identityKey(),SharedSourceFiles.nativeFile(copy).identityKey());
            } else {
                byte[] changed=bytes.clone();changed[0]^=1;
                StorageWriteGuardTestSupport.atomic(copy,changed,true);
                assertEquals(reference.bytes(),Files.size(copy));
                assertNotEquals(reference.sha256(),FileRef.measure(copy).sha256());
            }
            assertThrows(IOException.class,factory::requireCurrent);
            assertThrows(IOException.class,factory::prepare);
            assertThrows(IOException.class,factory::sources);
            assertThrows(IOException.class,definitions::driverProductSources);
          }
        }
    }

    private static void rejectUnadmittedSelection(RootDriverProductSourcesFactory.Input actual,
            RootRuntimeSelectedSources unadmitted)throws IOException {
        // Every retained domain, plan, permission provider and Inputs object is genuine and unchanged.
        // Only this candidate selection lacks the private actual-Inputs affiliation. It must never prepare.
        var derived=new RootDriverProductSourcesFactory.Input(
                actual.inputs(),unadmitted,actual.originals(),actual.settings(),actual.registration(),actual.plan(),
                actual.storage(),actual.frontend(),actual.finance(),actual.construction(),actual.family(),actual.governance(),
                actual.retry(),actual.lifecycle(),actual.ports(),actual.nativeGovernance(),actual.grantStore(),actual.clock(),actual.queryHistory(),actual.operatorAuthority());
        assertSame(actual.queryHistory(),derived.queryHistory());assertSame(actual.operatorAuthority(),derived.operatorAuthority());
        var candidate=new RootDriverProductSourcesFactory(derived);
        assertThrows(IOException.class,candidate::prepare);
        assertThrows(IOException.class,candidate::prepare);
        assertThrows(IOException.class,candidate::sources);
    }

    private static ExactRef javaSource(RootDriverProductSourcesFactory.JavaProducts sources,Kind role) {
        return switch(role) {
            case GOVERNANCE->sources.governance();case FACTION->sources.faction();case HEIR->sources.heir();
            case LIFECYCLE->sources.lifecycle();case TRANSPORT->sources.transport();case FAMILY->sources.family();
            default->throw new IllegalArgumentException("not a primary Driver product role: "+role);
        };
    }
}
