# M0 — Prove the MMX Modding Pipeline

Цель — подтвердить работу именно на установленной версии MMX.

## A Read-only audit
Build/distribution clues, hashes, StreamingAssets, StaticData, Dialog, Localisation, Managed, ModdingKit.

## B Backup/restore
Manifest + originals только тех файлов, которые планируем менять + restore verification.

## C Localisation proof
Одна безобидная видимая строка → verify → restore.

## D StaticData proof
Один low-risk value → verify → restore.

## E Dialog proof
Одна правка/injection → verify → restore.

## F Map proof
Одна видимая reversible map modification → game load → restore.

## G Dependency decision
Vanilla StreamingAssets достаточно для M0 и старта M1.
MMXLegacy — не hard dependency (ADR-008). Custom C# — last resort.

## Exit
Мы умеем повторяемо создать, установить, проверить и удалить маленький MMX mod.
