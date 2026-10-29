package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.DataPin;
import org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.DataRole;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.BooleanValue;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.ObjectValue;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.StringValue;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.Value;

/** Small DATA/serde regression. The ordinary bootstrap Guard integration is in its owning command test;
 * no test here issues a launch plan, FrozenRunProfile, Game observation, or runtime admission. */
class RootOriginalDriverRunProfileProducerTest {
    @TempDir Path root;
    static final Instant NOW=Instant.parse("2026-10-25T20:00:00Z");
    static final Clock CLOCK=Clock.fixed(NOW,ZoneOffset.UTC);

    @Test void configurationRoundTripsEveryExistingImportModeThroughTheSingleProfileCodec()throws IOException {
        ExactRef environment=exact(write(root.resolve("environment.json"),"{}".getBytes(StandardCharsets.UTF_8)));
        ExactRef policy=exact(write(root.resolve("fixture-policy.json"),"{}".getBytes(StandardCharsets.UTF_8)));
        var modes=List.<RootFrozenRunProfile.ImportMode>of(new RootFrozenRunProfile.DisabledFreshRobert(),
                new RootFrozenRunProfile.Enabled(root.resolve("saved-state")),
                new RootFrozenRunProfile.DisabledFreshFixture(policy,Optional.empty()),
                new RootFrozenRunProfile.EnabledNativeCampaign(root.resolve("native-saved-state")));
        for(var mode:modes) {
            var lifecycle=(mode instanceof RootFrozenRunProfile.DisabledFreshFixture
                    ||mode instanceof RootFrozenRunProfile.EnabledNativeCampaign)
                    ?RootFrozenRunProfile.LifecycleMode.NATIVE_CAMPAIGN:RootFrozenRunProfile.LifecycleMode.ROGUE_ONE_LIFE;
            var profile=profile(environment,lifecycle,mode);
            var request=new RootOriginalDriverRunProfileProducer.Request(profile);
            byte[] bytes=RootOriginalDriverRunProfileProducer.encode(request);
            assertEquals(request,RootOriginalDriverRunProfileProducer.decode(bytes));
            assertArrayEquals(bytes,RootOriginalDriverRunProfileProducer.encode(RootOriginalDriverRunProfileProducer.decode(bytes)));
            assertTrue(bytes.length<=RootOriginalDriverRunProfileProducer.MAXIMUM_REQUEST_BYTES);
            FileRef original=write(root.resolve("request-"+mode.getClass().getSimpleName()+".json"),bytes);
            assertEquals(request,RootOriginalDriverRunProfileProducer.readRequest(original));
        }
    }

    @Test void strictEnvelopeAndNestedProfileRejectMissingExtraWrongTypesAndExistingProfileAsProducerRequest()throws IOException {
        var profile=profile(exact(write(root.resolve("environment.json"),"{}".getBytes(StandardCharsets.UTF_8))),
                RootFrozenRunProfile.LifecycleMode.ROGUE_ONE_LIFE,new RootFrozenRunProfile.DisabledFreshRobert());
        byte[] profileBytes=RootFrozenRunProfile.encode(profile);
        byte[] requestBytes=RootOriginalDriverRunProfileProducer.encode(new RootOriginalDriverRunProfileProducer.Request(profile));
        var envelope=object(OriginalDriverJournal.parse(requestBytes,RootOriginalDriverRunProfileProducer.MAXIMUM_REQUEST_BYTES));
        assertThrows(IllegalArgumentException.class,()->RootOriginalDriverRunProfileProducer.decode(profileBytes));
        assertInvalid(with(envelope,"schema",new StringValue("wrong")));
        var missing=new LinkedHashMap<>(envelope.fields());missing.remove("profile");assertInvalid(new ObjectValue(missing));
        assertInvalid(with(envelope,"unexpected",new BooleanValue(true)));
        var nested=object(envelope.get("profile"));
        assertInvalid(with(envelope,"profile",with(nested,"ordinary_campaign_no_pact",new StringValue("false"))));
        var missingMode=new LinkedHashMap<>(nested.fields());missingMode.remove("legacy_import");
        assertInvalid(with(envelope,"profile",new ObjectValue(missingMode)));
        var reference=object(nested.get("environment_manifest"));
        assertInvalid(with(envelope,"profile",with(nested,"environment_manifest",with(reference,"bytes",new BooleanValue(true)))));
        var invalid=write(root.resolve("bad-request.json"),OriginalDriverJournal.canonical(
                with(envelope,"schema",new StringValue("wrong")),RootOriginalDriverRunProfileProducer.MAXIMUM_REQUEST_BYTES).bytes());
        assertThrows(IOException.class,()->RootOriginalDriverRunProfileProducer.readRequest(invalid));
    }

    @Test void preparationDoesNotWriteAndActuallyCreatedProfileReopensThroughTheProductionDataConsumer()throws IOException {
        FileRef environment=write(root.resolve("environment.json"),"{\"actual_software_environment_input\":true}".getBytes(StandardCharsets.UTF_8));
        var profile=profile(exact(environment),RootFrozenRunProfile.LifecycleMode.ROGUE_ONE_LIFE,
                new RootFrozenRunProfile.DisabledFreshRobert());
        FileRef request=write(root.resolve("producer-request.json"),RootOriginalDriverRunProfileProducer.encode(
                new RootOriginalDriverRunProfileProducer.Request(profile)));
        Path target=root.resolve("original-driver-run-profile.json");
        var prepared=RootOriginalDriverRunProfileProducer.prepare(request,target,CLOCK);
        assertEquals(target,prepared.target());assertFalse(Files.exists(target));prepared.verifyOriginals();
        assertThrows(IOException.class,prepared::verifyCreated);
        byte[] expected=RootFrozenRunProfile.encode(profile),copy=prepared.bytes();copy[0]^=1;
        assertArrayEquals(expected,prepared.bytes());
        // Only test readback here. The unique bootstrap command test invokes the real Body/Guard publisher.
        FileRef actual=write(target,prepared.bytes());prepared.verifyCreated();
        var pin=new DataPin(DataRole.ORIGINAL_DRIVER_RUN_PROFILE,actual);
        byte[] consumed=RootRuntimeDefinitions.readData(pin);
        assertArrayEquals(expected,consumed);assertEquals(profile,RootFrozenRunProfile.decode(consumed));
        assertArrayEquals(expected,RootFrozenRunProfile.encode(RootFrozenRunProfile.decode(consumed)));
        assertNotEquals(request.sha256(),actual.sha256());
    }

    @Test void actualMissingEnvironmentAndExpiredConfigurationCannotBePrepared()throws IOException {
        var missing=new ExactRef(root.resolve("missing-environment.json").toString(),2,OriginalDriverJournal.sha256("{}".getBytes(StandardCharsets.UTF_8)));
        var profile=profile(missing,RootFrozenRunProfile.LifecycleMode.ROGUE_ONE_LIFE,new RootFrozenRunProfile.DisabledFreshRobert());
        FileRef request=write(root.resolve("missing-request.json"),RootOriginalDriverRunProfileProducer.encode(
                new RootOriginalDriverRunProfileProducer.Request(profile)));
        assertThrows(IOException.class,()->RootOriginalDriverRunProfileProducer.prepare(request,root.resolve("missing-output.json"),CLOCK));
        FileRef environment=write(root.resolve("environment.json"),"{}".getBytes(StandardCharsets.UTF_8));
        var valid=profile(exact(environment),RootFrozenRunProfile.LifecycleMode.ROGUE_ONE_LIFE,new RootFrozenRunProfile.DisabledFreshRobert());
        FileRef validRequest=write(root.resolve("expired-request.json"),RootOriginalDriverRunProfileProducer.encode(
                new RootOriginalDriverRunProfileProducer.Request(valid)));
        assertThrows(IOException.class,()->RootOriginalDriverRunProfileProducer.prepare(validRequest,root.resolve("expired-output.json"),
                Clock.fixed(NOW.plusSeconds(3600),ZoneOffset.UTC)));
        assertFalse(Files.exists(root.resolve("expired-output.json")));
    }

    @Test void changedProducerRequestIsRejectedBeforeAnyProfileCanBePublished()throws IOException {
        FileRef environment=write(root.resolve("environment.json"),"{}".getBytes(StandardCharsets.UTF_8));
        var profile=profile(exact(environment),RootFrozenRunProfile.LifecycleMode.ROGUE_ONE_LIFE,
                new RootFrozenRunProfile.DisabledFreshRobert());
        byte[] bytes=RootOriginalDriverRunProfileProducer.encode(new RootOriginalDriverRunProfileProducer.Request(profile));
        FileRef request=write(root.resolve("request.json"),bytes);Path target=root.resolve("profile.json");
        var prepared=RootOriginalDriverRunProfileProducer.prepare(request,target,CLOCK);
        // Whitespace preserves the JSON value but changes the exact original, which cannot be silently accepted.
        Files.writeString(Path.of(request.path()),new String(bytes,StandardCharsets.UTF_8)+" ",StandardCharsets.UTF_8);
        assertThrows(IOException.class,prepared::verifyOriginals);
        assertThrows(IOException.class,prepared::verifyCreated);
        assertFalse(Files.exists(target));
    }

    @Test void changedActualEnvironmentInvalidatesPreparedBytesWithoutPublishingOrRepairingIt()throws IOException {
        FileRef environment=write(root.resolve("environment.json"),"{}".getBytes(StandardCharsets.UTF_8));
        var profile=profile(exact(environment),RootFrozenRunProfile.LifecycleMode.ROGUE_ONE_LIFE,
                new RootFrozenRunProfile.DisabledFreshRobert());
        FileRef request=write(root.resolve("request.json"),RootOriginalDriverRunProfileProducer.encode(
                new RootOriginalDriverRunProfileProducer.Request(profile)));
        Path target=root.resolve("profile.json");
        var prepared=RootOriginalDriverRunProfileProducer.prepare(request,target,CLOCK);
        Files.writeString(Path.of(environment.path()),"{\"changed\":true}",StandardCharsets.UTF_8);
        assertThrows(IOException.class,prepared::verifyOriginals);
        assertThrows(IOException.class,prepared::verifyCreated);
        assertFalse(Files.exists(target));
        assertEquals("{\"changed\":true}",Files.readString(Path.of(environment.path()),StandardCharsets.UTF_8));
    }

    @Test void changedCreatedProfileFailsActualReadbackAndIsNeverRewrittenByVerification()throws IOException {
        FileRef environment=write(root.resolve("environment.json"),"{}".getBytes(StandardCharsets.UTF_8));
        var profile=profile(exact(environment),RootFrozenRunProfile.LifecycleMode.ROGUE_ONE_LIFE,
                new RootFrozenRunProfile.DisabledFreshRobert());
        FileRef request=write(root.resolve("request.json"),RootOriginalDriverRunProfileProducer.encode(
                new RootOriginalDriverRunProfileProducer.Request(profile)));
        Path target=root.resolve("profile.json");
        var prepared=RootOriginalDriverRunProfileProducer.prepare(request,target,CLOCK);
        write(target,prepared.bytes());prepared.verifyCreated();
        byte[] changed=prepared.bytes();changed[0]^=1;Files.write(target,changed);
        assertThrows(IOException.class,prepared::verifyCreated);
        assertArrayEquals(changed,Files.readAllBytes(target));
        prepared.verifyOriginals();
    }

    static RootFrozenRunProfile.Request profile(Path actualEnvironment)throws IOException {
        return profile(exact(SharedSourceFiles.observe(actualEnvironment).source()),RootFrozenRunProfile.LifecycleMode.ROGUE_ONE_LIFE,
                new RootFrozenRunProfile.DisabledFreshRobert());
    }
    private static RootFrozenRunProfile.Request profile(ExactRef environment,RootFrozenRunProfile.LifecycleMode lifecycle,
            RootFrozenRunProfile.ImportMode mode) {
        return new RootFrozenRunProfile.Request(WindowsJobProcess.currentMachineId(),NOW.minusSeconds(1),NOW.plusSeconds(3600),
                "first-robert-request","first-robert-session",environment,lifecycle,false,mode);
    }
    private static FileRef write(Path path,byte[] bytes)throws IOException {
        Files.write(path,bytes,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);return SharedSourceFiles.observe(path).source();
    }
    private static ExactRef exact(FileRef ref){return new ExactRef(ref.path(),ref.bytes(),ref.sha256());}
    private static ObjectValue object(Value value){assertInstanceOf(ObjectValue.class,value);return (ObjectValue)value;}
    private static ObjectValue with(ObjectValue original,String key,Value value) {
        var fields=new LinkedHashMap<>(original.fields());fields.put(key,value);return new ObjectValue(fields);
    }
    private static void assertInvalid(ObjectValue value) {
        byte[] bytes=OriginalDriverJournal.canonical(value,RootOriginalDriverRunProfileProducer.MAXIMUM_REQUEST_BYTES).bytes();
        assertThrows(IllegalArgumentException.class,()->RootOriginalDriverRunProfileProducer.decode(bytes));
    }
}
