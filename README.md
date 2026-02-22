# WoodFlow

Финальная архитектура системы управления складом и отгрузкой древесины.

## Технологии
- Backend: FastAPI + SQLAlchemy 2.0 + PostgreSQL + JWT + openpyxl
- Frontend: React + TypeScript + Ant Design + Recharts
- Infra: Docker Compose + Nginx

## Структура

```text
app/
  models/
  schemas/
  services/
  api/
  auth/
  excel/
frontend/src/
  pages/
  components/
  services/
  theme/
```

## Ключевые фичи
- Мультитенантность по `company_id`
- Ролевая модель: Global Admin / Company Admin / Manager / Warehouse
- Бизнес-процесс статусов пакетов: `warehouse -> formed -> shipped`
- Dashboard KPI + агрегаты для графиков
- Генерация Excel документов покупателя и таможни при отгрузке

## Локальный запуск backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Документация API: `http://localhost:8000/docs`

## Запуск в Docker

```bash
docker compose up --build
```

## Ежедневный backup PostgreSQL
Пример cron на VPS:

```bash
0 2 * * * docker exec <db_container> pg_dump -U woodflow woodflow > /opt/backups/woodflow_$(date +\%F).sql
```
