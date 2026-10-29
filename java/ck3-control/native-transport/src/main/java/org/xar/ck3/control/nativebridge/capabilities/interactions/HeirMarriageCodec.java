package org.xar.ck3.control.nativebridge.capabilities.interactions;

import java.util.OptionalLong;
import org.xar.ck3.control.application.action.RawJson;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

/** Existing public typed consumer delegates to the single complete native codec. */
public final class HeirMarriageCodec {
    public static final String STEP=FamilyHeirLegality.STEP;
    private HeirMarriageCodec() { }
    public static HeirMarriageLegality decode(RawJson raw,Context context,HeirSubject subject) {
        var binding=new FamilyHeirLegality.Binding(context,subject.rootQuerySequence(),
                OptionalLong.of(subject.firstHeir().value()),subject.originalCampaignRoot());
        var value=FamilyHeirLegality.decode(raw,binding);
        var d=value.diagnostics();
        return new HeirMarriageLegality(new Frame(context.revision(),context.date(),context.actor(),context.build(),value.querySequence()),
                subject,value.availability(),value.candidates(),d.slotsScanned(),d.storageCapacity(),value.subjectRoleMismatches());
    }
}
