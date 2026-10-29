package org.xar.ck3.control.service.root;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.EnumSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts.ArtifactsContract.*;

/** Actual software writer/source pin and pending dispatcher; this never constructs a private Core or Managed permission. */
final class RootArtifactsActionAggregationTest {
    @TempDir Path temporary;
    @Test void actualFiniteProducerDeclarationsRemainDisjointAndOnlyTheirUnionIsExposed() {
        Set<Method> nav=RootArtifactsSourcesFactory.navigationMethods(),plain=RootArtifactsPrivateActions.supportedMethods();
        var all=RootArtifactsSourcesFactory.combinedMethods(nav,plain);
        assertEquals(8,all.size());assertTrue(all.stream().noneMatch(Method::readOnly));
        assertEquals(Set.of(Method.OPEN,Method.CLOSE,Method.PERSONAL_SUBMIT),plain);
        assertFalse(plain.stream().anyMatch(nav::contains));
        var missing=EnumSet.copyOf(plain);missing.remove(Method.PERSONAL_SUBMIT);
        assertThrows(IllegalArgumentException.class,()->RootArtifactsSourcesFactory.combinedMethods(nav,missing));
        var wrong=EnumSet.copyOf(nav);wrong.add(Method.OPEN);
        assertThrows(IllegalArgumentException.class,()->RootArtifactsSourcesFactory.combinedMethods(wrong,plain));
    }
    @Test void realWriterPendingDispatcherConsumesTheSameContributedCallableAndRetainsBothOwners()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("actual-aggregate-pending"),false)) {
            Path path=fixture.root.resolve("reviewed-fixture-source.txt");byte[] bytes=Files.readAllBytes(path);
            var source=new ExactRef(path.toAbsolutePath().normalize().toString(),bytes.length,ActionCodec.sha256(bytes));
            var command=fixture.command("actual-aggregate-once");var calls=new AtomicInteger();
            var nav=new RootDomainIntentPreparation.Binding("actual-nav-owner",source,
                    c->c.operation().equals(RootArtifactsSourcesFactory.NAVIGATE),(same,c)->fail("another operation cannot consume the Nav pending owner"));
            var plain=new RootDomainIntentPreparation.Binding("actual-private-owner",source,
                    c->c.operation().equals(command.operation()),(same,c)->{try{assertSame(same,fixture.writer.borrowedSession());}catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}assertSame(command,c);calls.incrementAndGet();});
            var navigation=installation("nav",List.of(nav),Set.of());
            var originalPrivate=installation("private",List.of(plain),Set.of(command.operation()));
            var all=RootArtifactsSourcesFactory.combinedInstallation(navigation,originalPrivate);
            assertSame(nav,all.pending().get(0));assertSame(plain,all.pending().get(1));
            assertTrue(all.actions().isEmpty(),"this focused pending test contributes no fake action implementation");
            var dispatcher=new RootDomainIntentPreparation(fixture.writer,all.pending(),all.requiredPending());
            fixture.writer.locked(same->{dispatcher.prepare(same,command);return null;});
            assertEquals(1,calls.get());assertEquals(originalPrivate.requiredPending(),all.requiredPending());
            assertTrue(all.domainRegistrations().isEmpty());
            var duplicated=installation("duplicate",List.of(plain),Set.of(command.operation()));
            assertThrows(IllegalArgumentException.class,()->RootArtifactsSourcesFactory.combinedInstallation(originalPrivate,duplicated));
        }
    }
    private static RootDomainInstallation installation(String name,List<RootDomainIntentPreparation.Binding> pending,Set<OperationKey> required) {
        return new RootDomainInstallation(name,List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),pending,required,List.of(),List.of(),List.of(),List.of(),List.of());
    }
}
