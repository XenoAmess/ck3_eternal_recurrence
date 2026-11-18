package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure native-identity DATA consumer. No current file, allocation, Game, lease or admission is manufactured. */
final class MappedSavedNativeIdentityTest {
    private static ObjectNode identity(String volume,String file,String created) {
        return StrictJson.object().put("volume_serial_decimal",volume).put("file_id_decimal",file).put("creation_filetime_decimal",created);
    }
    @Test void actualR11ProducerVolumeIsUnsigned64AndCannotBeTruncatedToLegacyVolume32() {
        // Retained R11 postexit metadata only: device=6505083400996699863, original FileID=281474994429586.
        var actual=identity("6505083400996699863","281474994429586","134388874028640137");
        var decoded=InitialEpisodePolicy.mappedNativeIdentity(actual);
        assertEquals("6505083400996699863",decoded.volumeSerialDecimal());
        assertEquals("281474994429586",decoded.fileIdDecimal());
        assertEquals("134388874028640137",decoded.creationFiletimeDecimal());
        assertTrue(new BigInteger(decoded.volumeSerialDecimal()).bitLength()>32);
    }
    @Test void fullUnsignedDomainsAndValuesAboveBinary64PrecisionRemainDecimalStrings() {
        for(String volume:List.of("0","4294967296","9007199254740993","18446744073709551615")) {
            var decoded=InitialEpisodePolicy.mappedNativeIdentity(identity(volume,"340282366920938463463374607431768211455","18446744073709551615"));
            assertEquals(volume,decoded.volumeSerialDecimal());
            assertEquals("340282366920938463463374607431768211455",decoded.fileIdDecimal());
            assertEquals("18446744073709551615",decoded.creationFiletimeDecimal());
        }
    }
    @Test void outOfDomainNoncanonicalAndNumericAliasesRemainRejected() {
        for(String field:List.of("volume_serial_decimal","file_id_decimal","creation_filetime_decimal")) {
            for(String value:List.of("-1","01","+1","1.0","1e3"," 1","")) {
                var wrong=identity("1","2","3");wrong.put(field,value);
                assertThrows(IllegalArgumentException.class,()->InitialEpisodePolicy.mappedNativeIdentity(wrong));
            }
            var numeric=identity("1","2","3");numeric.put(field,new BigInteger("9007199254740993"));
            assertThrows(IllegalArgumentException.class,()->InitialEpisodePolicy.mappedNativeIdentity(numeric));
            var missing=identity("1","2","3");missing.remove(field);
            assertThrows(IllegalArgumentException.class,()->InitialEpisodePolicy.mappedNativeIdentity(missing));
            var nul=identity("1","2","3");nul.putNull(field);
            assertThrows(IllegalArgumentException.class,()->InitialEpisodePolicy.mappedNativeIdentity(nul));
        }
        var volume=identity("18446744073709551616","2","3");
        assertThrows(IllegalArgumentException.class,()->InitialEpisodePolicy.mappedNativeIdentity(volume));
        var file=identity("1","340282366920938463463374607431768211456","3");
        assertThrows(IllegalArgumentException.class,()->InitialEpisodePolicy.mappedNativeIdentity(file));
        var time=identity("1","2","18446744073709551616");
        assertThrows(IllegalArgumentException.class,()->InitialEpisodePolicy.mappedNativeIdentity(time));
        var extra=identity("1","2","3");extra.put("available",true);
        assertThrows(IllegalArgumentException.class,()->InitialEpisodePolicy.mappedNativeIdentity(extra));
    }
}
