# Update Signing Key Rotation Design

## Goal

Allow the launcher to trust more than one Ed25519 update-signing public key so release signing keys can be rotated without breaking update compatibility during a transition window.

## Scope

- Keep `update-signature.json` unchanged: it still contains `algorithm`, `keyId`, and `signature`.
- Add a trusted public key map keyed by `keyId`.
- Verification selects the public key by the signature document's `keyId`.
- Keep existing single-key arguments as a compatibility path for tests and any existing call sites.
- Do not add remote key fetching, key revocation lists, or automatic key rotation in this pass.

## Data Flow

1. Release tooling signs `update-manifest.json` with a private key and writes its `keyId`.
2. The launcher reads `update-signature.json`.
3. The launcher checks that `algorithm` is `Ed25519`.
4. The launcher finds `keyId` in the trusted public key map.
5. The launcher verifies the manifest bytes with the selected public key.
6. Only after signature verification succeeds does the existing manifest validation and replacement flow continue.

## Testing

- A signature using a secondary trusted `keyId` must verify successfully.
- A signature using an unknown `keyId` must fail before manifest validation.
- Local update import must accept packages signed by a secondary trusted key when that key is configured.
