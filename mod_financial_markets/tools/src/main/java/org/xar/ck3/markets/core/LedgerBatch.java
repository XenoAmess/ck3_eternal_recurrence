package org.xar.ck3.markets.core;

import java.util.List;
import java.util.Objects;

/** A fully prepared, atomic movement of existing money. No operation imports cash. */
public record LedgerBatch(String id, List<CreateEscrow> escrows, List<Transfer> transfers,
                          List<Fee> fees, List<CoinTransfer> coinTransfers, List<CoinIssue> coinIssues) {
    public LedgerBatch {
        IdentifierRules.validate(id, "ledger batch ID");
        escrows = List.copyOf(escrows);
        transfers = List.copyOf(transfers);
        fees = List.copyOf(fees);
        coinTransfers = List.copyOf(coinTransfers);
        coinIssues = List.copyOf(coinIssues);
    }

    public LedgerBatch(String id, List<CreateEscrow> escrows, List<Transfer> transfers, List<Fee> fees) {
        this(id, escrows, transfers, fees, List.of(), List.of());
    }
    public LedgerBatch(String id, List<CreateEscrow> escrows, List<Transfer> transfers,
                       List<Fee> fees, List<CoinTransfer> coinTransfers) {
        this(id, escrows, transfers, fees, coinTransfers, List.of());
    }

    public record CoinTransfer(AccountId from, AccountId to, CoinId coin, long coins) {
        public CoinTransfer {
            Objects.requireNonNull(from); Objects.requireNonNull(to); Objects.requireNonNull(coin);
            if (coins <= 0) throw new IllegalArgumentException("coin transfer must be positive");
        }
    }
    public record CoinIssue(CoinId coin, AccountId issuer, long initialCoins, long maxSupplyCoins) {
        public CoinIssue {
            Objects.requireNonNull(coin); Objects.requireNonNull(issuer);
            if (initialCoins <= 0 || initialCoins > maxSupplyCoins)
                throw new IllegalArgumentException("finite issuance required");
        }
    }

    public record CreateEscrow(AccountId id, AccountId legalOwner) {
        public CreateEscrow {
            Objects.requireNonNull(id, "id");
            Objects.requireNonNull(legalOwner, "legalOwner");
            if (!id.value().startsWith("xfm.escrow.")) {
                throw new IllegalArgumentException("escrow ID must use xfm.escrow. namespace");
            }
        }
    }

    public record Transfer(AccountId from, AccountId to, long cents) {
        public Transfer {
            Objects.requireNonNull(from, "from");
            Objects.requireNonNull(to, "to");
            if (cents <= 0) {
                throw new IllegalArgumentException("transfer cents must be positive");
            }
        }
    }

    public record Fee(AccountId payer, long cents) {
        public Fee {
            Objects.requireNonNull(payer, "payer");
            if (cents <= 0) {
                throw new IllegalArgumentException("fee cents must be positive");
            }
        }
    }
}
