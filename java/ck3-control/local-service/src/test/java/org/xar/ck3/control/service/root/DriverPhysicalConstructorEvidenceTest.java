package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.capabilities.DynamicCapabilities;
import org.xar.ck3.control.application.driver.DriverCapabilityStateProducer;
import org.xar.ck3.control.application.driver.DriverCapabilityStateProducer.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.NativeColdAdoptionProjection;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual production physical reader -> strict input metadata codec. DATA here never creates a live scope or Game. */
public final class DriverPhysicalConstructorEvidenceTest {
    @TempDir Path directory;
    private ExactRef original(String name,byte[] bytes)throws Exception {
        Path path=directory.resolve(name);Files.write(path,bytes,StandardOpenOption.CREATE_NEW);
        var file=FileRef.measure(path);return new ExactRef(file.path(),file.bytes(),file.sha256());
    }
    private static NativeColdAdoptionProjection.Lifecycle lifecycle(){
        return new NativeColdAdoptionProjection.Lifecycle("rogue_one_life",Optional.of("xar_on"),
                "terminal_settlement_required","legacy-driver-default",Optional.empty());
    }
    private static PublicTerminalLifecycleData data(ExactRef policy,ExactRef environment,ExactRef nativeSource,List<ExactRef> closure){
        return new PublicTerminalLifecycleData(PublicTerminalLifecycleMode.NATIVE_CAMPAIGN_SAVED_NULL_CONSTRUCTOR,
                DeclaredLifecyclePresence.NULL,Nil.INSTANCE,lifecycle(),Optional.of(policy),Optional.of(environment),Optional.of(nativeSource),closure);
    }
    private PublicTerminalWire wire(ExactRef metadata,PublicTerminalLifecycleData lifecycle){
        return new PublicTerminalWire(metadata.sha256(),metadata,metadata,metadata,BigInteger.ZERO,
                new DynamicCapabilities.Configuration(Optional.of(directory.toAbsolutePath()),Optional.empty(),1,1,false,false),
                Optional.empty(),Optional.empty(),Optional.empty(),lifecycle);
    }
    @Test void realEmptyAndLargerThanTransactionalPinOriginalsRoundTripWithoutPayloadMaterialization()throws Exception {
        var empty=original("empty-original",new byte[0]);Path save=directory.resolve("large-save.ck3");
        try(var file=FileChannel.open(save,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE)){
            file.position(WriterContracts.MAX_PIN_BYTES);var last=ByteBuffer.wrap(new byte[]{1});
            while(last.hasRemaining())file.write(last);
        }
        var measured=FileRef.measure(save);var large=new ExactRef(measured.path(),measured.bytes(),measured.sha256());
        assertTrue(large.bytes()>WriterContracts.MAX_PIN_BYTES);
        var zeroWitness=RootFrozenRunProfile.retainOriginalEvidence(empty);
        var largeWitness=RootFrozenRunProfile.retainOriginalEvidence(large);
        assertEquals(0,zeroWitness.nativeFile().logicalBytes());assertEquals(large.bytes(),largeWitness.nativeFile().logicalBytes());
        var policy=original("policy-metadata",new byte[]{1});var environment=original("environment-metadata",new byte[]{2});
        var nativeSource=original("native-metadata",new byte[]{3});var closure=List.of(policy,environment,nativeSource,empty,large);
        var actual=wire(policy,data(policy,environment,nativeSource,closure));byte[] encoded=DriverJson.encode(actual.toJson());
        assertTrue(encoded.length<65536);var decoded=DriverCapabilityStateProducer.decodePublicTerminalWire(encoded);
        assertEquals(actual,decoded);assertEquals(closure,decoded.lifecycleInputs().sourceClosure());
        assertArrayEquals(encoded,DriverJson.encode(decoded.toJson()));
        SharedSourceFiles.assertUnchanged(zeroWitness);SharedSourceFiles.assertUnchanged(largeWitness);
    }
    @Test void emptyEvidenceNeverFillsNamedPositiveSourcesAndWrongReferenceTypesStayRejected()throws Exception {
        var empty=original("empty",new byte[0]);var positive=original("positive",new byte[]{1});
        assertThrows(IllegalArgumentException.class,()->data(empty,positive,positive,List.of(empty,positive)));
        assertThrows(IllegalArgumentException.class,()->data(positive,empty,positive,List.of(empty,positive)));
        assertThrows(IllegalArgumentException.class,()->data(positive,positive,empty,List.of(empty,positive)));
        var actual=wire(positive,data(positive,positive,positive,List.of(positive,empty))).toJson();
        Obj lifecycle=(Obj)actual.get("lifecycle_inputs");Arr sources=(Arr)lifecycle.get("source_closure");
        Obj reference=(Obj)sources.items().get(1);
        for(Value invalid:List.of(new Bool(true),new Text("0"),new IntegerValue(BigInteger.valueOf(-1)))){
            var fields=new LinkedHashMap<String,Value>(reference.members());fields.put("bytes",invalid);
            var changed=new Arr(List.of(sources.items().get(0),new Obj(fields)));
            var inner=new LinkedHashMap<String,Value>(lifecycle.members());inner.put("source_closure",changed);
            var outer=new LinkedHashMap<String,Value>(actual.members());outer.put("lifecycle_inputs",new Obj(inner));
            assertThrows(IllegalArgumentException.class,()->DriverCapabilityStateProducer.decodePublicTerminalWire(DriverJson.encode(new Obj(outer))));
        }
        var missing=new LinkedHashMap<String,Value>(lifecycle.members());missing.remove("source_closure");
        var outer=new LinkedHashMap<String,Value>(actual.members());outer.put("lifecycle_inputs",new Obj(missing));
        assertThrows(IllegalArgumentException.class,()->DriverCapabilityStateProducer.decodePublicTerminalWire(DriverJson.encode(new Obj(outer))));
    }
}
