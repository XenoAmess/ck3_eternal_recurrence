package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Clock;
import org.xar.ck3.control.nativebridge.capabilities.religion.ReligionConversionActions;

/** Original five conversion reads and the original paid conversion action. */
public final class RootReligionConversion {
    private RootReligionConversion(){ }
    public static final class Prepared extends RootReligionConversionRuntime.Prepared {
        private Prepared(RootReligionConversionRuntime.Sources sources){super(ReligionConversionActions.Kind.CONVERSION,sources);}
    }
    public static Prepared ordinary(RootAdditionalDomains.ImplementationMetadata metadata){
        return new Prepared(RootReligionConversionRuntime.ordinarySources(ReligionConversionActions.Kind.CONVERSION,RootReligionConversion.class,metadata));
    }
    public static Prepared prepare(RootRuntimeDefinitions.Inputs inputs,RootRuntimeSelectedSources selected,RootRuntimeNativeOriginals.Bound originals,Clock clock)throws IOException {
        return new Prepared(RootReligionConversionRuntime.sources(ReligionConversionActions.Kind.CONVERSION,RootReligionConversion.class,inputs,selected,originals,clock));
    }
}
