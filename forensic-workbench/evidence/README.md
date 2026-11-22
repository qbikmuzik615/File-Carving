# Evidence vault: PRIVATE and read-only

**Never put actual evidence bytes into this public repository.** This folder is documentation only.

Recommended structure OUTSIDE this Git working tree or inside a separate dedicated private, access-restricted Git repository:

    evidence-vault/
      originals/drive/Lost-folder/<minute>.mp4
      originals/disk-images/<physical-card>.img
      references/known-good/<reference>.mp4
      derivatives/reconstruction-candidates/
      reports/unredacted/
      logs/tool-output/
      manifests/sha256.csv

Record Google Drive file ID, original folder, retrieval time, byte length, SHA-256, acquisition method and read-only storage destination in the PRIVATE manifest. Never infer a physical sector address from a Drive filename. Do not allow cloud AI actions direct access to this tree by default.

Transfer complete media to a private encrypted volume or private artifact store only after access verification. Avoid standard git blobs for a 2 GB collection; use a private object store or Git LFS with encryption/access restrictions and verify retention limits/costs. Preserve all original files, do not overwrite or 'repair' in place.

Public GitHub Actions run on synthetic fixtures only. Keep private runner separate and prohibit untrusted PR code on evidence hosts.

Private evidence copies are available in the current analysis workspace but are NOT published to GitHub.
