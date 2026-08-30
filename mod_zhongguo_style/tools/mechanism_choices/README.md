# 361 mechanism choice overrides

The three numbered JSON files in this directory are reviewed source data for
`gen_361_mechanisms.py`. Each mechanism must supply:

- `title_en`
- tailored `option_a_cn` / `option_a_en` for the evidence-rich, durable, but
  administratively or fiscally costly route
- tailored `option_b_cn` / `option_b_en` for the faster, more forceful, but
  politically or operationally risky route
- one ledger `profile` declared in `zg361_mechanism_data.py`
- `reference_choice` (`a`, `b`, or `c`) for the turnkey charter

The Chinese decision and consequence prose is parsed from the numbered design
document and is not duplicated here.
