package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.util.LinkedHashMap;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;

/** Configuration/source contracts only. No fabricated loaded role, FrozenRunProfile, Native call or Game admission. */
final class RootLoadedRunProfileContractTest {
    @TempDir Path root;
    private static final Clock CLOCK=Clock.systemUTC();
    private static FileRef write(Path path,byte[] bytes)throws IOException {
        Files.write(path,bytes,StandardOpenOption.CREATE_NEW);return SharedSourceFiles.observe(path).source();
    }
    private static ExactRef exact(FileRef ref) { return new ExactRef(ref.path(),ref.bytes(),ref.sha256()); }
    private RootFrozenRunProfile.LoadedRequest fixture(Path directory)throws IOException {
        Files.createDirectories(directory);
        ExactRef environment=exact(write(directory.resolve("environment.json"),new byte[]{'{','}'}));
        ExactRef owner=exact(write(directory.resolve("owner-descriptor.json"),new byte[]{'{','}'}));
        ExactRef control=exact(write(directory.resolve("parent-control.json"),new byte[]{'{','}'}));
        ExactRef generation=exact(write(directory.resolve("generation-claim.json"),new byte[]{'{','}'}));
        // Locator contents are DATA here; only the private-role consumer may compare a decoded actual pair.
        ExactRef pair=exact(write(directory.resolve("checkpoint-pair.json"),new byte[]{'{','}'}));
        Instant now=CLOCK.instant();
        var fresh=new RootFrozenRunProfile.Request(WindowsJobProcess.currentMachineId(),now.minusSeconds(1),now.plusSeconds(2700),
                "owner-plan-original-request","owner-plan-original-session",environment,RootFrozenRunProfile.LifecycleMode.NATIVE_CAMPAIGN,
                false,new RootFrozenRunProfile.EnabledNativeCampaign(directory.resolve("state")));
        return new RootFrozenRunProfile.LoadedRequest(fresh,owner,control,generation,pair);
    }
    private static ObjectValue object(Value value) { assertInstanceOf(ObjectValue.class,value);return (ObjectValue)value; }
    private static ObjectValue with(ObjectValue original,String key,Value value) {
        var fields=new LinkedHashMap<>(original.fields());fields.put(key,value);return new ObjectValue(fields);
    }
    private static byte[] encode(Value value) { return OriginalDriverJournal.canonical(value,RootFrozenRunProfile.MAXIMUM_REQUEST_BYTES).bytes(); }

    @Test void loadedEnvelopeAndProducerAreSeparateVersionsAndLegacyDecodersRemainClosed()throws Exception {
        var request=fixture(root.resolve("serde"));byte[] bytes=RootFrozenRunProfile.encodeLoaded(request);
        assertEquals(request,RootFrozenRunProfile.decodeLoaded(bytes));
        assertArrayEquals(bytes,RootFrozenRunProfile.encodeLoaded(RootFrozenRunProfile.decodeLoaded(bytes)));
        assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.decode(bytes));
        byte[] old=RootFrozenRunProfile.encode(request.freshProfile());
        assertEquals(request.freshProfile(),RootFrozenRunProfile.decode(old));
        assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.decodeLoaded(old));
        var producer=new RootOriginalDriverRunProfileProducer.LoadedRequest(request);
        byte[] prepared=RootOriginalDriverRunProfileProducer.encodeLoaded(producer);
        assertEquals(producer,RootOriginalDriverRunProfileProducer.decodeLoaded(prepared));
        assertThrows(IllegalArgumentException.class,()->RootOriginalDriverRunProfileProducer.decode(prepared));
        byte[] original=RootOriginalDriverRunProfileProducer.encode(new RootOriginalDriverRunProfileProducer.Request(request.freshProfile()));
        assertThrows(IllegalArgumentException.class,()->RootOriginalDriverRunProfileProducer.decodeLoaded(original));
    }

    @Test void missingAliasWrongTypesAndUnknownVersionsCannotBecomeLoadedConfiguration()throws Exception {
        var request=fixture(root.resolve("closed"));
        var row=object(OriginalDriverJournal.parse(RootFrozenRunProfile.encodeLoaded(request),RootFrozenRunProfile.MAXIMUM_REQUEST_BYTES));
        var missing=new LinkedHashMap<>(row.fields());missing.remove("generation_claim");
        assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.decodeLoaded(encode(new ObjectValue(missing))));
        assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.decodeLoaded(encode(with(row,"role_permitted",new BooleanValue(true)))));
        assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.decodeLoaded(encode(with(row,"schema",new StringValue("unknown")))));
        var ref=object(row.get("owner_descriptor"));
        assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.decodeLoaded(encode(with(row,"owner_descriptor",with(ref,"bytes",new BooleanValue(true))))));
        var nested=object(row.get("fresh_profile"));
        assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.decodeLoaded(encode(with(row,"fresh_profile",with(nested,"ordinary_campaign_no_pact",new StringValue("false"))))));
    }

    @Test void loadedWindowAndSavedModeDoNotRelaxTheExistingRequestContract()throws Exception {
        var request=fixture(root.resolve("window"));var original=request.freshProfile();
        var longer=new RootFrozenRunProfile.Request(original.machineId(),original.observedAt(),original.observedAt().plusSeconds(3601),
                original.requestId(),original.sessionId(),original.environmentManifest(),original.lifecycle(),false,original.legacyImport());
        assertEquals(longer,RootFrozenRunProfile.decode(RootFrozenRunProfile.encode(longer)),"legacy v4 DATA keeps its existing finite bound");
        assertThrows(IllegalArgumentException.class,()->new RootFrozenRunProfile.LoadedRequest(longer,request.ownerDescriptor(),request.parentControl(),request.generationClaim(),request.checkpointPair()));
        var fresh=new RootFrozenRunProfile.Request(original.machineId(),original.observedAt(),original.reviewAt(),original.requestId(),original.sessionId(),
                original.environmentManifest(),RootFrozenRunProfile.LifecycleMode.ROGUE_ONE_LIFE,false,new RootFrozenRunProfile.DisabledFreshRobert());
        assertThrows(IllegalArgumentException.class,()->new RootFrozenRunProfile.LoadedRequest(fresh,request.ownerDescriptor(),request.parentControl(),request.generationClaim(),request.checkpointPair()));
        assertEquals("owner-plan-original-request",original.requestId());assertEquals("owner-plan-original-session",original.sessionId());
    }

    @Test void existingMetadataPrepareDispatchFeedsTheSameGuardedBodyWithoutPublishingOrIssuingARole()throws Exception {
        var request=fixture(root.resolve("prepare"));
        var producer=new RootOriginalDriverRunProfileProducer.LoadedRequest(request);
        FileRef source=write(root.resolve("loaded-producer.json"),RootOriginalDriverRunProfileProducer.encodeLoaded(producer));
        Path target=root.resolve("loaded-profile.json");
        var prepared=RootOriginalDriverRunProfileProducer.prepare(source,target,CLOCK);
        assertFalse(Files.exists(target));prepared.verifyOriginals();
        assertEquals(request,RootFrozenRunProfile.decodeLoaded(prepared.bytes()));
        var body=RootProfileBootstrapInputs.originalDriverRunProfile(prepared);
        assertEquals(1,body.quote().size());
        assertEquals(RootBootstrapOutputContract.Kind.ORIGINAL_DRIVER_RUN_PROFILE,body.quote().getFirst().kind());
        assertFalse(Files.exists(target));assertThrows(IOException.class,prepared::verifyCreated);
        // Readback only. The existing bootstrap Guard remains the sole production writer.
        FileRef created=write(target,prepared.bytes());prepared.verifyCreated();
        assertEquals(request,RootFrozenRunProfile.readLoadedRequest(exact(created)));
        assertEquals(producer,RootOriginalDriverRunProfileProducer.readLoadedRequest(source));
        assertThrows(IOException.class,()->RootOriginalDriverRunProfileProducer.readRequest(source));
    }

    @Test void changedActualIdentitySourceInvalidatesPreparedMetadataAndDoesNotRewriteIt()throws Exception {
        var request=fixture(root.resolve("changed"));
        FileRef source=write(root.resolve("changed-producer.json"),RootOriginalDriverRunProfileProducer.encodeLoaded(new RootOriginalDriverRunProfileProducer.LoadedRequest(request)));
        Path target=root.resolve("unpublished-profile.json");
        var prepared=RootOriginalDriverRunProfileProducer.prepareLoaded(source,target,CLOCK);
        byte[] bytes=prepared.bytes();
        Files.writeString(Path.of(request.generationClaim().path()),"{\"changed\":true}");
        assertThrows(IOException.class,prepared::verifyOriginals);assertThrows(IOException.class,prepared::verifyCreated);
        assertFalse(Files.exists(target));assertArrayEquals(bytes,prepared.bytes());
        assertEquals("{\"changed\":true}",Files.readString(Path.of(request.generationClaim().path())));
    }
}
