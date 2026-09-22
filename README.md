# Fuel Control

Жеңіл Streamlit қосымшасы: автокөліктердің кез келген кезеңдегі жанармай шығынын қазақша немесе орысша есептеу, production деректерін Supabase PostgreSQL-де қауіпсіз сақтау және Excel-ге экспорттау. SQLite жергілікті әзірлеу fallback-ы ретінде сақталған.

## Мүмкіндіктер

- бірнеше автокөлік және әрқайсысына жеке жазғы/қысқы норматив;
- бастапқы **Газель** нормативтері: жазда 26, қыста 29,12 л/100 км;
- жүрген қашықтық = соңғы одометр − бастапқы одометр;
- нормативтік шығын = жүрген қашықтық × норматив / 100;
- есептік қалдық = бастапқы қалдық + құйылған жанармай − нормативтік шығын;
- еркін күндер аралығы, опционалды нақты қалдық, үнем немесе артық шығын және Excel экспорт;
- Android және iPhone экрандарына бейімделетін Streamlit интерфейсі.
- Supabase email/password authentication және әр қолданушыға RLS арқылы оқшауланған деректер.

## Жергілікті іске қосу

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Деректер әдепкіде `data/fuel_control.db` файлында сақталады. Басқа жолды `FUEL_CONTROL_DB` орта айнымалысы арқылы беруге болады.

## Тесттер

```bash
pip install -r requirements-dev.txt
pytest
ruff check .
```

## Streamlit Community Cloud

Public deployment Supabase Auth және PostgreSQL қолданады; SQLite тек жергілікті әзірлеу fallback-ы болып қалады.

1. Supabase Free жобасын жасаңыз және **SQL Editor** ішінде `supabase/schema.sql` файлын орындаңыз.
2. **Authentication → Providers → Email** ішінде email/password authentication-ды қосыңыз. Email confirmation талабын жоба саясатына сай таңдаңыз.
3. Streamlit Community Cloud-та репозиторийді қосып, entry point ретінде `app.py` таңдаңыз.
4. Қолданбаның **Secrets** бөліміне тек public anon credentials енгізіңіз:

   ```toml
   SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
   SUPABASE_ANON_KEY = "YOUR_ANON_KEY"
   ```

Service-role key-ді Streamlit UI-ға немесе репозиторийге қоспаңыз. `.env` және `.streamlit/secrets.toml` Git арқылы еленбейді. Парольдер қолданба кестелеріне жазылмайды — оларды Supabase Auth басқарады. `schema.sql` барлық user data үшін RLS қосады.

### Бірінші admin

1. Қосымша арқылы кәдімгі қолданушы ретінде тіркеліңіз.
2. Supabase SQL Editor ішінде email-ды өз мәніңізге ауыстырып орындаңыз:

   ```sql
   update public.profiles set role = 'admin' where email = 'admin@example.com';
   ```

Admin барлық профильдерді, көліктерді және есептерді көре алады әрі профильді бұғаттай алады; парольдерге қол жеткізе алмайды.

### Жергілікті SQLite режимі

Supabase secrets жоқ жергілікті ортада қосымша SQLite fallback-қа автоматты өтеді. Оны мәжбүрлеу үшін `FUEL_CONTROL_LOCAL=1 streamlit run app.py` іске қосыңыз. Public deployment-та қате конфигурацияны жасырмау үшін `FUEL_CONTROL_BACKEND=supabase` орнатуға болады; secrets жоқ болса қолданба friendly configuration error көрсетеді.
