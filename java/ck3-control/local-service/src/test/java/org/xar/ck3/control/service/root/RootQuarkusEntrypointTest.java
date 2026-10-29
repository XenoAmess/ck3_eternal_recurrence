package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Optional;
import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilderFactory;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.runtime.RootStartupInvocation;

/** Real launch DATA producer/sole codec -> build-selected entry -> actual Root positional consumer. No process is launched. */
final class RootQuarkusEntrypointTest {
    @TempDir Path root;
    @Test void actualInvocationProducerAndPersistentCodecReachRootStartupWithoutDroppingSavedOriginals()throws Exception {
        Path startup=root.resolve("startup-data.json"),saved=root.resolve("saved-route-data.json");
        Files.write(startup,new byte[]{'{','}'});Files.write(saved,new byte[]{'{','}'});
        FileRef startupSource=FileRef.measure(startup),savedSource=FileRef.measure(saved);
        for(Optional<FileRef> actualSaved:java.util.List.of(Optional.<FileRef>empty(),Optional.of(savedSource))) {
            var produced=new RootStartupInvocation(startupSource,actualSaved);
            Path data=root.resolve(actualSaved.isPresent()?"saved-invocation.json":"new-invocation.json");Files.write(data,produced.encode());
            var decoded=RootStartupInvocation.decode(Files.readAllBytes(data));assertEquals(produced,decoded);
            String[] arguments=decoded.arguments().toArray(String[]::new);
            assertEquals(actualSaved.isPresent()?6:3,arguments.length);
            assertEquals(RootQuarkusEntrypoint.Application.ROOT_STARTUP,RootQuarkusEntrypoint.select(arguments));
            var actual=RootSavedNativeCoordinator.arguments(arguments);
            assertEquals(startupSource,actual.startup());assertEquals(actualSaved,actual.savedRoute());
        }
    }
    @Test void publicHostStillOwnsZeroAndOriginalUnsupportedCountsIncludingFour() {
        assertEquals(RootQuarkusEntrypoint.Application.PUBLIC_HOST,RootQuarkusEntrypoint.select(new String[0]));
        assertEquals(RootQuarkusEntrypoint.Application.PUBLIC_HOST,RootQuarkusEntrypoint.select(new String[4]));
        assertThrows(IllegalArgumentException.class,()->RootQuarkusEntrypoint.select(new String[]{root.resolve("startup").toString(),"01","a".repeat(64)}));
    }
    @Test void actualPostPackageConsumerRejectsAnUnacceptedManifestWithoutManufacturingAnImporter()throws Exception {
        Path manifest=root.resolve("unaccepted-package.json"),invocation=root.resolve("unused-invocation.json");
        Files.write(manifest,new byte[]{'{','}'});Files.write(invocation,new byte[]{'{','}'});
        assertThrows(java.io.IOException.class,()->RootRuntimeLaunchCommand.prepare(FileRef.measure(manifest),FileRef.measure(invocation)));
    }
    @Test void sharedRootEntryRequiresTheDistinctOriginalInvocationAndDoesNotPublishOnInvalidInput()throws Exception {
        Path invalid=root.resolve("not-a-root-entry.json");Files.writeString(invalid,"{}");
        FileRef source=FileRef.measure(invalid);
        assertThrows(java.io.IOException.class,()->RootRuntimeLaunchCommand.runShared(source));
        Path binding=root.resolve("never-binding.json"),spec=root.resolve("never-spec.json"),invocation=root.resolve("never-invocation.json");
        assertThrows(java.io.IOException.class,()->RootRuntimeLaunchCommand.publishShared(source,binding,spec,invocation));
        assertFalse(Files.exists(binding));assertFalse(Files.exists(spec));assertFalse(Files.exists(invocation));
    }
    @Test void sharedRootPreparerIsThePrivateNamedConcretePackageConsumer()throws Exception {
        Class<?> type=Class.forName(RootRuntimeLaunchCommand.class.getName()+"$PreparedRoot");
        assertTrue(java.lang.reflect.Modifier.isPrivate(type.getModifiers()));
        assertTrue(java.lang.reflect.Modifier.isStatic(type.getModifiers()));
        assertTrue(java.lang.reflect.Modifier.isFinal(type.getModifiers()));
        assertTrue(org.xar.ck3.control.build.SharedOwnedCommand.RootPreparer.class.isAssignableFrom(type));
        assertFalse(type.isAnonymousClass());assertFalse(type.isSynthetic());
        assertEquals(RootRuntimeLaunchCommand.class.getClassLoader(),type.getClassLoader());
    }
    @Test void actualModulePomSelectsTheConcreteEntrypointUsedByTheInvocationConsumer()throws Exception {
        Path module=Path.of(System.getProperty("basedir",System.getProperty("user.dir")));
        var factory=DocumentBuilderFactory.newInstance();factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl",true);
        factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_DTD,"");factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_SCHEMA,"");
        var document=factory.newDocumentBuilder().parse(module.resolve("pom.xml").toFile());
        var configured=document.getElementsByTagName("quarkus.package.main-class");assertEquals(1,configured.getLength());
        assertEquals(RootFiniteFirstLiveMain.class.getAnnotation(io.quarkus.runtime.annotations.QuarkusMain.class).name(),configured.item(0).getTextContent().strip());
    }
}
