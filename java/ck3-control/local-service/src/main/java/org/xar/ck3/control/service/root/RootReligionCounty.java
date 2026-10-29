package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Clock;
import org.xar.ck3.control.nativebridge.capabilities.religion.ReligionConversionActions;

/** Original County task submission; assignment does not mean complete county conversion. */
public final class RootReligionCounty {
    private RootReligionCounty(){ }
    public static final class Prepared extends RootReligionConversionRuntime.Prepared {
        private Prepared(RootReligionConversionRuntime.Sources sources){super(ReligionConversionActions.Kind.COUNTY,sources);}
    }
    public static Prepared ordinary(RootAdditionalDomains.ImplementationMetadata metadata){
        return new Prepared(RootReligionConversionRuntime.ordinarySources(ReligionConversionActions.Kind.COUNTY,RootReligionCounty.class,metadata));
    }
    public static Prepared prepare(RootRuntimeDefinitions.Inputs inputs,RootRuntimeSelectedSources selected,RootRuntimeNativeOriginals.Bound originals,Clock clock)throws IOException {
        return new Prepared(RootReligionConversionRuntime.sources(ReligionConversionActions.Kind.COUNTY,RootReligionCounty.class,inputs,selected,originals,clock));
    }
}
