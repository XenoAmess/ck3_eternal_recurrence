// Included inside xar::game; sealed minimum balance/classifier schema precedes code.
struct ContextSourceFollowing2bca620BalanceV1 {
  std::optional<bool> component_present;
  std::optional<std::int64_t> balance_raw_q64;
  std::optional<std::int64_t> numeric_balance_q64;
  std::string reason;
  friend bool operator==(const ContextSourceFollowing2bca620BalanceV1 &, const ContextSourceFollowing2bca620BalanceV1 &) = default;
};
struct ContextSourceFollowing2bca620ClassifierV1 {
  std::string status = "partial";
  bool ready = false;
  std::optional<std::string> selection;
  std::optional<std::int32_t> index_raw_i32;
  std::string reason;
  friend bool operator==(const ContextSourceFollowing2bca620ClassifierV1 &, const ContextSourceFollowing2bca620ClassifierV1 &) = default;
};
struct ContextSourceFollowing2bca620ProviderV1 {
  std::string status = "partial";
  bool ready = false;
  std::optional<bool> provider_loaded;
  std::optional<std::int32_t> count_raw;
  std::optional<std::string> selection;
  std::optional<std::string> definition_identity;
  std::optional<std::uint32_t> definition_magic_u32;
  std::optional<bool> admitted;
  ContextSourceAfterPcV1 pc{};
  std::string reason;
  friend bool operator==(const ContextSourceFollowing2bca620ProviderV1 &, const ContextSourceFollowing2bca620ProviderV1 &) = default;
};
struct ContextSourceFollowing2bca620InputsV1 {
  std::string status = "partial";
  bool ready = false;
  std::int32_t character_id = -1;
  ContextSourceFollowing2bca620BalanceV1 balance_source{};
  ContextSourceFollowing2bca620ClassifierV1 classifier{};
  ContextSourceFollowing2bca620ProviderV1 provider_selection{};
  std::string reason;
  friend bool operator==(const ContextSourceFollowing2bca620InputsV1 &, const ContextSourceFollowing2bca620InputsV1 &) = default;
};
