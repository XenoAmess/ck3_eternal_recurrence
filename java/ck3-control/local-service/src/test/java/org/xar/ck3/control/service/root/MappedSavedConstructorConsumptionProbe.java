package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.Arrays;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.driver.DriverBootstrap;
import org.xar.ck3.control.application.driver.DriverCapabilityRuntime;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.NativeSavedGameClone;

/**
 * Owner-executable consumer probe requiring an existing genuine adopted graph and joined Full.
 * Never creates an Admission, token, Received, writer, Game, SAVE or current physical permission.
 * Invoke from the existing Runtime/Java integration callback, not as a standalone Game launcher.
 */
public final class MappedSavedConstructorConsumptionProbe {
    private MappedSavedConstructorConsumptionProbe(){ }
    public static ObjectNode capture(String sampleLabel,RootRuntimeContext context,RootInstalledCatalog catalog,
            DriverBootstrap.Adopted actual,DriverCapabilityRuntime capabilities,
            RootFrozenRunProfile.FrozenRunProfile frozen,CheckpointPair unchangedOriginalPair,
            DriverObservationAssembler.FullSnapshot actualFull,DriverSnapshotFacts.Known actualKnown)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(catalog);Objects.requireNonNull(actual);
        Objects.requireNonNull(capabilities);Objects.requireNonNull(frozen);Objects.requireNonNull(unchangedOriginalPair);
        Objects.requireNonNull(actualFull);Objects.requireNonNull(actualKnown);StrictJson.text(sampleLabel);
        byte[] originalPair=CheckpointPairCodec.encode(unchangedOriginalPair);
        return context.withSession(same->{
            String before=same.head().digest();
            StrictJson.require(context.adopted()==actual&&frozen.initialPolicy().isMaterializedSaved(),"probe requires the actual mapped adopted graph");
            frozen.initialPolicy().requireSavedHistory(context.game().launchPlan());
            catalog.planningInputs(actual,capabilities);
            var source=capabilities.actualPublicPlanningLifecycleSource(same);
            var facts=source.capture(same,actualFull,actualKnown);
            source.requireCurrent(same,actualFull,actualKnown,facts);
            StrictJson.require(facts.constructor()==DriverCapabilityRuntime.NativeCampaignConstructor.SAVED
                    &&facts.game().equals(context.game().generation())&&facts.sessionId().equals(context.game().sessionId())
                    &&facts.policySource().equals(frozen.initialPolicy().source())&&facts.source().equals(context.source()),
                    "actual constructor facts differ from their installed private source");
            String mutableClone=NativeSavedGameClone.actualPath(context.game().launchPlan()).toString();
            StrictJson.require(facts.sourceClosure().stream().noneMatch(ref->ref.path().equals(mutableClone)),
                    "mutable initial clone cannot enter immutable planning source closure");
            var lookalike=new DriverCapabilityRuntime.NativeCampaignConstructorFacts(facts.constructor(),facts.game(),facts.sessionId(),
                    facts.source(),facts.policySource(),facts.environmentSource(),facts.sourceClosure(),facts.headDigest());
            boolean refused=false;
            try{source.requireCurrent(same,actualFull,actualKnown,lookalike);}
            catch(IllegalArgumentException expected){refused=true;}
            StrictJson.require(refused,"public constructor DATA impersonated the actual private captured facts");
            source.requireCurrent(same,actualFull,actualKnown,facts);
            StrictJson.require(before.equals(same.head().digest())&&Arrays.equals(originalPair,CheckpointPairCodec.encode(unchangedOriginalPair)),
                    "read-only constructor consumption changed canonical head or original Pair metadata");
            var row=StrictJson.object().put("schema","xar.mapped-saved-constructor-consumption-probe/v1");
            row.put("sample_label",sampleLabel);row.put("consumer_returned",true);row.put("live_phase_inferred",false);
            row.put("original_pair_unchanged",true);row.put("canonical_head_unchanged",true);row.put("lookalike_facts_refused",true);
            row.put("head_digest",before);row.put("observation_version",actualFull.facts().observationVersion());
            row.set("policy_source",facts.policySource().toJson());row.set("original_save",unchangedOriginalPair.save().reference().toJson());
            return row;
        });
    }
}
