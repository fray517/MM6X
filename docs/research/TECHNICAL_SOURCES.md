# Initial Technical Sources
План основан на community documentation по MMX modding и наличии
MMXL ModKit в локальной Ubisoft-установке.

MMXLegacy (https://github.com/Albeoris/MMXLegacy) исследован:
MIT, rewritten Managed DLLs, last push 2017. **Не** hard dependency
(ADR-008). В репозиторий не копировать. Заметки:
`docs/research/MMXLEGACY.md`.

MM6 lod layout (extract): OpenEnroth `LodReader` /
`LodFormats` (LodEntry_MM6, LodImageHeader_MM6 text flag 0x100).
VERIFIED_SOURCE; тела lod в git не копировать.

Важно: внешняя документация не заменяет аудит локальной версии.
Exact schemas/versions должны получить статус VERIFIED_LOCAL.
