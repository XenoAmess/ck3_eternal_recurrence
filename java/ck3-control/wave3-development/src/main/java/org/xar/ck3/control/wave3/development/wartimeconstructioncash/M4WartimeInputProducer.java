package org.xar.ck3.control.wave3.development.wartimeconstructioncash;

import com.fasterxml.jackson.databind.node.TextNode;
import java.io.ByteArrayOutputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionModel.Input;

/** The existing local read context becomes one validated request; this producer performs no reads or actions. */
public final class M4WartimeInputProducer {
    private M4WartimeInputProducer() { }

    /** Original copied SDK object. Validation never replaces its integer/floating token categories or bytes. */
    public static final class CopiedObject {
        private final byte[] originalUtf8;

        public CopiedObject(byte[] originalUtf8) {
            this.originalUtf8 = Objects.requireNonNull(originalUtf8, "original SDK object").clone();
            StrictJson.require(StrictJson.parse(this.originalUtf8, WartimeConstructionCodec.MAX_BYTES).isObject(),
                    "copied SDK context must be an object");
        }

        public byte[] originalUtf8() { return originalUtf8.clone(); }
    }

    /** Empty means observed input unavailable/null; it is never a fabricated empty object or empty market. */
    public record Context(CopiedObject snapshot, Optional<CopiedObject> root, Optional<CopiedObject> spending,
            Optional<CopiedObject> market, Optional<CopiedObject> marketSourceFrame,
            Optional<CopiedObject> mercenaryLedger, Optional<CopiedObject> procurementDecision) {
        public Context {
            Objects.requireNonNull(snapshot, "snapshot"); Objects.requireNonNull(root, "root observation");
            Objects.requireNonNull(spending, "spending observation"); Objects.requireNonNull(market, "market observation");
            Objects.requireNonNull(marketSourceFrame, "market source observation");
            Objects.requireNonNull(mercenaryLedger, "mercenary ledger observation");
            Objects.requireNonNull(procurementDecision, "procurement observation");
        }
    }

    /** Whole actual quoted outlay. Zero is used only by the existing prequote stage; unknown remains null. */
    public record Outlay(String kind, Optional<BigInteger> constructionGoldRaw) {
        public Outlay {
            Objects.requireNonNull(kind, "construction kind");
            if (!kind.isEmpty()) { StrictJson.text(kind); }
            Objects.requireNonNull(constructionGoldRaw, "construction quote observation");
        }
    }

    /** Only produce can construct this value, after the original full codec has validated the whole envelope. */
    public static final class ProducedRequest {
        private final byte[] originalUtf8;
        private final Input input;

        private ProducedRequest(byte[] originalUtf8, Input input) {
            this.originalUtf8 = originalUtf8.clone(); this.input = Objects.requireNonNull(input);
        }

        public byte[] utf8() { return originalUtf8.clone(); }
        public Input input() { return input; }
    }

    public static ProducedRequest produce(Context context, Outlay outlay) {
        Objects.requireNonNull(context, "current local context"); Objects.requireNonNull(outlay, "whole quoted outlay");
        ByteArrayOutputStream wire = new ByteArrayOutputStream();
        ascii(wire, "{\"schema\":\"" + WartimeConstructionCodec.SCHEMA + "\",\"snapshot\":");
        wire.writeBytes(context.snapshot().originalUtf8());
        ascii(wire, ",\"kind\":");
        wire.writeBytes(StrictJson.canonical(TextNode.valueOf(outlay.kind())));
        ascii(wire, ",\"construction_gold_raw\":");
        ascii(wire, outlay.constructionGoldRaw().map(BigInteger::toString).orElse("null"));
        nullableObject(wire, "root", context.root());
        nullableObject(wire, "spending", context.spending());
        nullableObject(wire, "market", context.market());
        nullableObject(wire, "market_source_frame", context.marketSourceFrame());
        nullableObject(wire, "mercenary_ledger", context.mercenaryLedger());
        nullableObject(wire, "procurement_decision", context.procurementDecision());
        ascii(wire, "}");
        byte[] original = wire.toByteArray();
        // The complete original codec owns every field/type/source guard. Never reencode SDK subtrees first.
        Input input = WartimeConstructionCodec.decode(original);
        return new ProducedRequest(original, input);
    }

    private static void nullableObject(ByteArrayOutputStream wire, String field, Optional<CopiedObject> value) {
        ascii(wire, ",\"" + field + "\":");
        if (value.isPresent()) { wire.writeBytes(value.orElseThrow().originalUtf8()); }
        else { ascii(wire, "null"); }
    }

    private static void ascii(ByteArrayOutputStream wire, String value) {
        wire.writeBytes(value.getBytes(StandardCharsets.US_ASCII));
    }
}
