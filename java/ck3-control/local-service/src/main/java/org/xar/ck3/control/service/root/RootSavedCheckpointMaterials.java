package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.checkpoint.SavedFirstCheckpointMaterialStore;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Explicit original P37 and Java saved-material branches. Neither branch is a rollback, cold admission or replay permit. */
public final class RootSavedCheckpointMaterials {
    public sealed interface Source permits OriginalP37,JavaSavedMaterial,JavaFirstSavedMaterial { }
    public record OriginalP37(RootColdCheckpointValidator.Expected expected) implements Source {
        public OriginalP37 { Objects.requireNonNull(expected); }
    }
    /** The concrete sole source store reruns the original SAVE/SEM/cycle verifier; a manifest's shape is never sufficient. */
    public record JavaSavedMaterial(SavedAttachmentSourceStore store,CheckpointPair pair,FileWitness manifest,String pipeName,Path profileDir) implements Source {
        public JavaSavedMaterial { Objects.requireNonNull(store);Objects.requireNonNull(pair);Objects.requireNonNull(manifest);StrictJson.text(pipeName);
            Objects.requireNonNull(profileDir);StrictJson.require(profileDir.isAbsolute()&&profileDir.normalize().equals(profileDir),"actual Java profile required"); }
    }
    public record JavaFirstSavedMaterial(SavedFirstCheckpointMaterialStore store,CheckpointPair pair,FileWitness manifest,String pipeName,Path profileDir) implements Source {
        public JavaFirstSavedMaterial { Objects.requireNonNull(store);Objects.requireNonNull(pair);Objects.requireNonNull(manifest);StrictJson.text(pipeName);
            Objects.requireNonNull(profileDir);StrictJson.require(profileDir.isAbsolute()&&profileDir.normalize().equals(profileDir),"actual Java first SAVE profile required"); }
    }
    public enum Branch { ORIGINAL_P37,JAVA_SAVED_MATERIAL,JAVA_FIRST_SAVED_MATERIAL }
    public static final class Verified {
        private final RootSavedCheckpointMaterials issuer;
        private final Session session;
        private final Source source;
        private final RootColdCheckpointValidator.Verified physical;
        private final SavedAttachmentSourceStore.SavedMaterial saved;
        private final SavedFirstCheckpointMaterialStore.BaselinedMaterial first;
        private Verified(RootSavedCheckpointMaterials issuer,Session session,Source source,
                RootColdCheckpointValidator.Verified physical,SavedAttachmentSourceStore.SavedMaterial saved,SavedFirstCheckpointMaterialStore.BaselinedMaterial first) {
            this.issuer=issuer;this.session=session;this.source=source;this.physical=physical;this.saved=saved;this.first=first;
        }
        public Branch branch(){return switch(source){case JavaSavedMaterial ignored->Branch.JAVA_SAVED_MATERIAL;case JavaFirstSavedMaterial ignored->Branch.JAVA_FIRST_SAVED_MATERIAL;case OriginalP37 ignored->Branch.ORIGINAL_P37;};}
        public RootColdCheckpointValidator.Verified physical(){return physical;}
        public SavedAttachmentSourceStore.SavedMaterial requireJavaSavedMaterial()throws IOException {
            if(saved==null)throw new IOException("original P37 evidence is not Java SavedMaterial");return saved;
        }
        public SavedFirstCheckpointMaterialStore.BaselinedMaterial requireFirstJavaSavedMaterial()throws IOException {
            if(first==null)throw new IOException("this source is not an actual Java first SAVE BASELINE material");return first;
        }
    }
    private final ContinuityWriter writer;
    private final RootColdCheckpointValidator physical;
    public RootSavedCheckpointMaterials(ContinuityWriter writer) {
        this.writer=Objects.requireNonNull(writer);physical=new RootColdCheckpointValidator(writer);
    }
    public Verified verify(Session same,Source source)throws IOException {
        writer.requireSession(same);Objects.requireNonNull(source);
        if(source instanceof OriginalP37 original)
            return new Verified(this,same,source,physical.verifyLegacy(same,original.expected()),null,null);
        if(source instanceof JavaFirstSavedMaterial first) {
            String head=same.head().digest();
            var material=first.store().loadBaselinedOriginal(same,first.manifest(),first.pair());
            StrictJson.require(material.witness().equals(first.manifest())&&material.pair().equals(first.pair()),"first SAVE BASELINE material changed its original witness/pair");
            Obj driver=DriverJson.object(material.savedDriver().encode(),RootColdCheckpointValidator.MAXIMUM_DRIVER_BYTES);
            Obj raw=OpportunityJson.object(driver.get("last_checkpoint"),"original first SAVE raw checkpoint");
            Obj anchor=RootColdCheckpointValidator.normalizePayload(driver,first.pipeName(),first.profileDir(),first.pair().save());
            var expected=new RootColdCheckpointValidator.Expected(first.pair().driver().reference(),first.pair().driver().identity(),first.pair().save().reference(),first.pair().save().identity(),
                    first.pipeName(),first.profileDir(),raw,anchor,material.savedDriver().commandHistory().size());
            var ticket=physical.verify(same,expected);requirePairAnchor(first.pair(),ticket);
            material.requirePhysical(same);physical.requireCurrent(same,ticket);
            StrictJson.require(head.equals(same.head().digest()),"first SAVE material verification changed canonical head");
            return new Verified(this,same,source,ticket,null,material);
        }
        JavaSavedMaterial java=(JavaSavedMaterial)source;
        String head=same.head().digest();
        SavedAttachmentSourceStore.SavedMaterial material=java.store().loadOriginal(same,java.manifest(),java.pair());
        requireMaterial(java,material);
        // loadOriginal, unlike loadRetainedOriginal, invokes the original physical SAVE/Driver verifier
        // and retains the caller's original manifest FileWitness instead of reobserving a new identity.
        // The following full physical read adds the canonical profile binding and inode/ns recheck.
        var pair=material.pair();
        Obj driver=readDriver(pair.driver().reference());
        Obj raw=OpportunityJson.object(driver.get("last_checkpoint"),"actual Java saved raw checkpoint");
        Path profile=java.profileDir();
        Obj anchor=RootColdCheckpointValidator.normalizePayload(driver,java.pipeName(),profile,pair.save());
        var expected=new RootColdCheckpointValidator.Expected(pair.driver().reference(),pair.driver().identity(),pair.save().reference(),pair.save().identity(),
                java.pipeName(),profile,raw,anchor,((OpportunityJson.Arr)driver.get("command_history")).items().size());
        var ticket=physical.verify(same,expected);
        requirePairAnchor(pair,ticket);
        StrictJson.require(head.equals(same.head().digest()),"Java saved-material validation changed the original writer head");
        return new Verified(this,same,source,ticket,material,null);
    }
    public void requireCurrent(Session same,Verified verified)throws IOException {
        Objects.requireNonNull(verified);writer.requireSession(same);
        if(verified.issuer!=this||verified.session!=same)throw new IOException("saved checkpoint ticket belongs to another concrete owner or writer scope");
        if(verified.source instanceof OriginalP37)physical.requireCurrentLegacy(same,verified.physical);
        else physical.requireCurrent(same,verified.physical);
        if(verified.source instanceof JavaSavedMaterial java) {
            var reread=java.store().loadOriginal(same,java.manifest(),java.pair());requireMaterial(java,reread);
            StrictJson.require(reread.originalHeadDigest().equals(verified.saved.originalHeadDigest())
                    &&reread.checkpointDigest().equals(verified.saved.checkpointDigest()),"same-lock Java saved original authority changed");
        }
        if(verified.source instanceof JavaFirstSavedMaterial)verified.first.requirePhysical(same);
        physical.requireCurrent(same,verified.physical);
    }
    private static void requireMaterial(JavaSavedMaterial source,SavedAttachmentSourceStore.SavedMaterial material) {
        StrictJson.require(source.manifest().equals(material.witness())&&source.pair().equals(material.pair()),
                "Java SavedMaterial must come from the exact sole original source store and pair");
    }
    private static void requirePairAnchor(CheckpointPair pair,RootColdCheckpointValidator.Verified physical) {
        Obj anchor=physical.normalizedAnchor();
        StrictJson.require(OpportunityJson.integer(anchor.get("saved_date_raw"),"saved date").equals(pair.frame().frame().identity().dateRaw())
                &&OpportunityJson.integer(anchor.get("history_index"),"saved history index").longValueExact()==pair.historyIndex()
                &&OpportunityJson.integer(physical.driverPayload().get("episode_character_id"),"saved actor").equals(pair.frame().frame().identity().player())
                &&OpportunityJson.text(physical.driverPayload().get("episode_run_id"),"saved episode").equals(pair.frame().frame().episodeRunId()),
                "physical Java Driver/SAVE anchor differs from the sole SavedMaterial frame");
    }
    private static Obj readDriver(ExactRef ref)throws IOException {
        StrictJson.require(ref.bytes()>0&&ref.bytes()<=RootColdCheckpointValidator.MAXIMUM_DRIVER_BYTES,"bounded complete Java saved Driver required");
        byte[] bytes;
        try(var input=java.nio.file.Files.newInputStream(Path.of(ref.path()))) { bytes=input.readNBytes(Math.toIntExact(ref.bytes())+1); }
        StrictJson.require(bytes.length==ref.bytes()&&DriverJson.sha256(bytes).equals(ref.sha256()),"complete Java saved Driver differs from original pair");
        return DriverJson.object(bytes,RootColdCheckpointValidator.MAXIMUM_DRIVER_BYTES);
    }
}
