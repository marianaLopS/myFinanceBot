# myFinanceBot

Asistente financiero con IA que registra gastos e ingresos desde Telegram y los guarda en Google Sheets.

> Estado: en construcción (Etapa 2, preparación del proyecto). Aún no hay bot funcional.

## Requisitos

- Python 3.11 o superior
- Cuenta de Google (para tu copia de la hoja)
- Cuenta de Telegram
- Clave de API del proveedor de IA elegido

## Instalación rápida (desarrollo)

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # y completa tus valores
```

## Estructura

```
src/finance_bot/   código del bot
  config.py        lectura y validación de .env
tests/             pruebas
.env.example       plantilla de configuración (sin secretos)
requirements.txt   dependencias
```

## Seguridad

- `.env`, `credentials.json` y la base de datos local están en `.gitignore`. Nunca los subas al repositorio.
- El bot responde solo al `TELEGRAM_OWNER_ID` configurado.
- Cada usuario usa su propio bot, su propia hoja y sus propias credenciales.

## Próximos pasos

Ver el plan de etapas en la documentación del proyecto. La guía de instalación para no programadores llegará en la Etapa 8.
