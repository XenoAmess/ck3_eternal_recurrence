package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Clock;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionDoctrineDraftReads.Group;

/** Six readonly draft producers, installed through the same source-bound doctrine/draft runtime. */
public final class RootReligionReformDraft {
    private RootReligionReformDraft() { }
    public static RootReligionDoctrineData.Prepared ordinary(RootAdditionalDomains.ImplementationMetadata metadata){
        return RootReligionDoctrineData.ordinary(metadata,Group.DRAFT,RootReligionReformDraft.class);
    }
    public static RootReligionDoctrineData.Prepared prepare(RootRuntimeDefinitions.Inputs inputs,
            RootRuntimeSelectedSources selected,RootRuntimeNativeOriginals.Bound originals,Clock clock)throws IOException{
        return RootReligionDoctrineData.prepare(inputs,selected,originals,clock,Group.DRAFT,RootReligionReformDraft.class);
    }
}
