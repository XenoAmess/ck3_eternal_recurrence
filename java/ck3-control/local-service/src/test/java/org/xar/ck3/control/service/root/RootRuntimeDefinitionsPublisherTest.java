package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.util.ArrayList;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.*;

/** Required genuine first-original publication, not a generated template, fake Native/Core or permissive guard.
 * Root supplies the actual DATA request/target for this runtime consumer test. Missing actual inputs fail; no skip counts as a pass. */
class RootRuntimeDefinitionsPublisherTest {
    private static Fixture retained;
    private record Fixture(RootRuntimeDefinitionsPublisher.Request request,RootRuntimeDefinitionsPublisher.Published published,
            RootRuntimeDefinitions loaded) { }

    private static FileRef requestOriginal()throws IOException {
        String prefix="xar.root.runtime.definitions.publication.request";
        String path=System.getProperty(prefix+".path"),count=System.getProperty(prefix+".bytes"),sha=System.getProperty(prefix+".sha256");
        if(path==null||count==null||sha==null)throw new IOException("required actual ORIGINAL_ROOT_RUNTIME_DEFINITIONS_PUBLICATION_REQUEST FileRef missing; NOT_RUN, no template or skip");
        if(!count.matches("[1-9][0-9]{0,6}")||!sha.matches("[0-9a-f]{64}"))throw new IOException("exact publication fixture byte count/SHA required");
        long bytes=Long.parseLong(count);if(bytes>RootRuntimeDefinitionsPublisher.MAXIMUM_REQUEST_BYTES)throw new IOException("publication fixture exceeds explicit bound");
        return new FileRef(path,bytes,sha);
    }
    private static RootRuntimeDefinitionsPublisher.Request request()throws IOException {
        return RootRuntimeDefinitionsPublisher.decodeRequest(RootRuntimeDefinitions.read(requestOriginal(),RootRuntimeDefinitionsPublisher.MAXIMUM_REQUEST_BYTES));
    }
    private static synchronized Fixture actual()throws IOException {
        if(retained==null){
            var request=request();var produced=RootRuntimeDefinitionsPublisher.execute(requestOriginal(),Clock.systemUTC());
            // Real original exists and has a native witness before the actual Main/Primary/Secondary reader is called.
            var loaded=produced.readExact(Clock.systemUTC());retained=new Fixture(request,produced,loaded);
        }
        retained.published().requireCurrent(Clock.systemUTC());return retained;
    }
    @Test void actualTypedProducerCreatesTheOriginalBeforeTheRealDefinitionsConsumer()throws Exception {
        var actual=actual();var published=actual.published();var witness=published.actualWitness();
        assertEquals(Path.of(actual.request().target()),Path.of(published.original().path()));
        assertEquals(published.original(),actual.loaded().inputs().originalRef());
        assertEquals(actual.request().configuration(),actual.loaded().inputs().configuration());
        assertEquals(SharedSourceFiles.observe(Path.of(published.original().path())),witness);
        assertEquals(published.original().bytes(),witness.nativeFile().logicalBytes());
        assertEquals(1,witness.nativeFile().linkCount());
        assertArrayEquals(RootRuntimeDefinitions.encodeConfiguration(actual.request().configuration()),
                RootRuntimeDefinitions.read(published.original(),RootRuntimeDefinitions.MAXIMUM_BYTES));
        assertEquals(actual.request().configuration().originalData().size(),actual.loaded().inputs().configuration().originalData().size());
    }
    @Test void onlyTheUniqueConfigurationCodecOwnsNestedFieldsAndStrictPublicationWire()throws Exception {
        var actual=request();byte[] bytes=RootRuntimeDefinitionsPublisher.encodeRequest(actual);
        assertEquals(actual,RootRuntimeDefinitionsPublisher.decodeRequest(bytes));
        var mapper=ControlBuild.strictMapper();
        var missing=(ObjectNode)mapper.readTree(bytes);missing.remove("output_binding_ref");
        assertThrows(IOException.class,()->RootRuntimeDefinitionsPublisher.decodeRequest(mapper.writeValueAsBytes(missing)));
        var alias=(ObjectNode)mapper.readTree(bytes);alias.put("runtime_definitions_ref","invented preexisting template");
        assertThrows(IOException.class,()->RootRuntimeDefinitionsPublisher.decodeRequest(mapper.writeValueAsBytes(alias)));
        var bool=(ObjectNode)mapper.readTree(bytes);((ObjectNode)bool.get("output_binding_ref")).put("bytes",true);
        assertThrows(IOException.class,()->RootRuntimeDefinitionsPublisher.decodeRequest(mapper.writeValueAsBytes(bool)));
        var old=(ObjectNode)mapper.readTree(bytes);old.put("schema","xar.java-root-runtime-definitions-publication/v0");
        assertThrows(IOException.class,()->RootRuntimeDefinitionsPublisher.decodeRequest(mapper.writeValueAsBytes(old)));
        var nullConfig=(ObjectNode)mapper.readTree(bytes);nullConfig.putNull("configuration");
        assertThrows(IOException.class,()->RootRuntimeDefinitionsPublisher.decodeRequest(mapper.writeValueAsBytes(nullConfig)));
    }
    @Test void anExistingActualOriginalCannotBeOverwrittenOrImplicitlyReplayed()throws Exception {
        var actual=actual();var before=actual.published().actualWitness();
        assertThrows(IOException.class,()->RootRuntimeDefinitionsPublisher.execute(requestOriginal(),Clock.systemUTC()));
        SharedSourceFiles.assertUnchanged(before);actual.published().requireCurrent(Clock.systemUTC());
    }
    @Test void passiveDataPinsAreRetainedWithoutReopeningThemDuringPublicationPreparation()throws Exception {
        var request=request();var config=request.configuration();var rows=new ArrayList<>(config.originalData());
        int index=-1;for(int i=0;i<rows.size();i++)if(rows.get(i).role()==DataRole.LIFE_SETTINGS)index=i;
        assertTrue(index>=0);var original=rows.get(index);String wrong=original.originalRef().sha256().equals("0".repeat(64))?"1".repeat(64):"0".repeat(64);
        rows.set(index,new DataPin(original.role(),new FileRef(original.originalRef().path(),original.originalRef().bytes(),wrong)));
        var changed=RootRuntimeDefinitions.rebindInputs(config,config.applicationRef(),rows);
        var prepared=RootRuntimeDefinitionsPublisher.prepare(changed,null,null,Clock.systemUTC());
        assertEquals(changed,prepared.configuration());assertEquals(changed,RootRuntimeDefinitions.decodeConfiguration(prepared.bytes()));
        assertEquals(rows,prepared.configuration().originalData());
    }
    @Test void historicalReviewPeriodsDoNotQualifyConfigurationDataPreparation()throws Exception {
        var config=request().configuration();var clock=Clock.fixed(java.time.Instant.parse(config.reviewAtUtc()).plusSeconds(86400),java.time.ZoneOffset.UTC);
        var prepared=RootRuntimeDefinitionsPublisher.prepare(config,null,null,clock);
        prepared.requireCurrent(clock);assertEquals(config,prepared.configuration());
        assertArrayEquals(RootRuntimeDefinitions.encodeConfiguration(config),prepared.bytes());
    }
    @Test void everyMandatoryRoleIsStillCheckedByTheSingleConfigurationContract()throws Exception {
        var config=request().configuration();
        for(DataRole role:DataRole.values())if(role!=DataRole.ROLLBACK_PROOF){
            var rows=config.originalData().stream().filter(row->row.role()!=role).toList();
            assertThrows(IllegalArgumentException.class,()->RootRuntimeDefinitions.rebindInputs(config,config.applicationRef(),rows));
        }
    }
}
