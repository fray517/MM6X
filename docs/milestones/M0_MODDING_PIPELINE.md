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
Определить, достаточно ли vanilla data/modding kit, нужен ли MMXLegacy или custom patch.

## Exit
Мы умеем повторяемо создать, установить, проверить и удалить маленький MMX mod.
