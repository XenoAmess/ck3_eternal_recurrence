package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.ZoneOffset;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceCodec;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceGrant;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceRole;
import org.xar.ck3.control.service.root.RootEventSourceContextProducer;
import org.xar.ck3.control.service.root.RootJavaBootstrapInputs;
import org.xar.ck3.control.service.root.RootRuntimeDefinitions;
import org.xar.ck3.control.wave2.events.sourcecatalog.EvidenceGrantManifestPublisher;

/** Real offline publisher and exact stock fixture through the new producer and existing Definitions codec.
 * This creates no signed output authority, Core, real native capture or Game qualification. */
final class RootEventSourceContextProducerTest {
    @TempDir Path directory;
    private static final Clock CLOCK=Clock.fixed(OfflineInteractionCorpus.NOW,ZoneOffset.UTC);
    private RootEventSourceContextProducer.Request request(OfflineInteractionCorpus f,FileRef manifest) {
        return new RootEventSourceContextProducer.Request(RootEventSourceContextProducer.SCHEMA,WindowsJobProcess.currentMachineId(),
                CLOCK.instant().toString(),CLOCK.instant().plusSeconds(60).toString(),RootJavaBootstrapInputs.Mode.QUOTE,null,
                f.state.toString(),f.game.toString(),manifest,directory.resolve("event-context.json").toString().replace('\\','/'));
    }
    @Test void solePublisherEmptyInitializationRoundtripsThroughActualContextProducerAndDefinitions()throws Exception {
        var f=new OfflineInteractionCorpus(directory.resolve("empty"));Files.createDirectories(f.grants.getParent());var host=f.host(false);
        assertEquals(0,host.initialization().orElseThrow().grants());
        FileRef manifest=FileRef.measure(f.grants);byte[] original=Files.readAllBytes(f.grants);
        var fromManifest=RootEventSourceContextProducer.prepare(request(f,manifest),CLOCK);
        var explicitFresh=RootEventSourceContextProducer.prepare(request(f,null),CLOCK);
        assertArrayEquals(fromManifest.bytes(),explicitFresh.bytes());
        var actual=RootRuntimeDefinitions.decodeEventSources(fromManifest.bytes());
        assertEquals(List.of(),actual.evidenceGrants());assertEquals(f.state,actual.stateRoot());assertEquals(f.game,actual.stockGameRoot());
        assertArrayEquals(fromManifest.bytes(),RootRuntimeDefinitions.encodeEventSources(actual));
        assertEquals(1,fromManifest.quote().size());
        assertEquals(Path.of(request(f,manifest).target()).toString(),fromManifest.expected().path());
        assertFalse(Files.exists(Path.of(fromManifest.expected().path())));
        assertThrows(IOException.class,()->fromManifest.createNew(CLOCK));assertArrayEquals(original,Files.readAllBytes(f.grants));
    }
    @Test void actualNonemptyPinsKeepUnknownOriginAndChangesAreRejectedBeforeAnyOutput()throws Exception {
        var f=new OfflineInteractionCorpus(directory.resolve("pins"));Files.createDirectories(f.grants.getParent());
        Path fact=directory.resolve("historical-facts.json");Files.writeString(fact,"{}\n");FileRef pin=FileRef.measure(fact);
        var grant=new ProjectionEvidenceGrant(fact,pin.bytes(),pin.sha256(),"unknown",ProjectionEvidenceRole.EVENT_SOURCE_FACTS);
        EvidenceGrantManifestPublisher.publish(f.grants,List.of(grant));
        var prepared=RootEventSourceContextProducer.prepare(request(f,FileRef.measure(f.grants)),CLOCK);
        assertEquals(List.of(grant),RootRuntimeDefinitions.decodeEventSources(prepared.bytes()).evidenceGrants());
        assertEquals("unknown",prepared.context().evidenceGrants().getFirst().originMachineId());
        Files.writeString(fact,"{\"changed\":true}\n");assertThrows(IOException.class,()->prepared.requireCurrent(CLOCK));
        assertFalse(Files.exists(Path.of(prepared.expected().path())));
    }
    @Test void explicitEmptyDoesNotAdmitMissingNullOrMistypedGrantCollections()throws Exception {
        var f=new OfflineInteractionCorpus(directory.resolve("strict"));Files.createDirectories(f.grants.getParent());f.host(false);
        byte[] bytes=RootEventSourceContextProducer.prepare(request(f,FileRef.measure(f.grants)),CLOCK).bytes();
        var root=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(bytes,ProjectionEvidenceCodec.MAX_BYTES);
        var missing=root.deepCopy();missing.remove("evidence_grants");
        assertThrows(IllegalArgumentException.class,()->RootRuntimeDefinitions.decodeEventSources(StrictJson.canonical(missing,1<<20)));
        var nil=root.deepCopy();nil.putNull("evidence_grants");
        assertThrows(IllegalArgumentException.class,()->RootRuntimeDefinitions.decodeEventSources(StrictJson.canonical(nil,1<<20)));
        for(var value:List.of("null","{}","true","0")){
            var wrong=root.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)wrong.get("evidence_grants")).set("grants",StrictJson.parse(value.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class,()->RootRuntimeDefinitions.decodeEventSources(StrictJson.canonical(wrong,1<<20)));
        }
        var request=request(f,null);assertEquals(request,RootEventSourceContextProducer.decode(RootEventSourceContextProducer.encode(request)));
        var missingManifest=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(RootEventSourceContextProducer.encode(request));missingManifest.remove("evidence_manifest_ref");
        assertThrows(IOException.class,()->RootEventSourceContextProducer.decode(StrictJson.canonical(missingManifest)));
    }
}
