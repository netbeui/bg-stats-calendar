# BG Stats Calendar (NSI + BNB → iCalendar)

Автоматично извличане на публикационните календари на **НСИ** и **БНБ** и публикуване като **.ics** файлове, подходящи за добавяне в Google Calendar (абонамент по URL).

## Какво прави
- Скрейпва официалната страница на НСИ: https://www.nsi.bg/calendar и месечните подстраници.
- Скрейпва календара на БНБ (Пресцентър): https://www.bnb.bg/AboutUs/PressOffice/POCalendar/index.htm
- Нормализира записи и генерира три ICS файла в `dist/`:
  - `nsi.ics` — събития на НСИ (целодневни)
  - `bnb.ics` — събития на БНБ (с конкретни часове, таймзона Europe/Sofia)
  - `bg_stats.ics` — обединен поток (НСИ + БНБ)

## Локално стартиране
```bash
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m src.build_ics
ls dist/*.ics
```

## Добавяне в Google Calendar (абонамент по URL)
1. Качи `dist/` съдържанието на публичен хост (или ползвай GitHub Pages от workflow-а по-долу).
2. В Google Calendar → **Settings** → **Add calendar** → **From URL** → постави линка към `https://.../bg_stats.ics` (или `nsi.ics`, `bnb.ics`).

> Заб.: Google опреснява абонаментните календари периодично (cron на Google, не се контролира от нас).

## Публикуване чрез GitHub Pages (автоматично)
Workflow-ът по-долу:
- Пуска се **всеки ден в 03:00 UTC** (≈06:00 EET/08:00 EEST сезонно).
- Генерира `dist/*.ics` и ги публикува в **GitHub Pages**. URL ще е от вида `https://<user>.github.io/<repo>/bg_stats.ics`

### Настройка
1. Създай публично репо, напр. `bg-stats-calendar`.
2. Включи **Pages** → **Build and deployment** → *GitHub Actions*.
3. Къмни този код в репото (включително `.github/workflows/publish.yml`).

## Точност и устойчивост
- НСИ често не публикува час → записите са **целодневни**.
- БНБ публикува и час → събитията имат 1 час продължителност (може да се коригира).
- Парсването е **хибридно** (таблици + списъци), за да преживява дребни промени по HTML-а.
- ICS съдържа **VTIMEZONE** за Europe/Sofia (коректни DST преходи).
- Дедупликация по ключ (дата+заглавие).

## Лиценз
MIT
