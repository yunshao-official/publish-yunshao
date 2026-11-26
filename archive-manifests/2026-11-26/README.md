# EFS encrypted archive metadata manifest — 2026-11-26

This manifest records metadata only; it does not contain plaintext or EFS ciphertext.

Archives:

- `Theory_20261107`: 31,805 files, 95,280,452,844 bytes, stored on D: HDD.
- `Theory_20261007`: 7,422 files, 56,203,218,541 bytes, raw-copied with Robocopy `/EFSRAW` to D: HDD.

All listed files remain EFS-encrypted. The original encrypted files are preserved on the D: mechanical HDD pending recovery of the matching EFS private key.

The manifest is intended for path, size, timestamp, and missing-file comparison. Content hashes cannot be computed without the EFS private key.
