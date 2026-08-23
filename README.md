# Open-Editor Bot
> A.k.a **copy-editor-ai** (coined name from last semester team)  

Flask web app for reviewing JUTLP `.docx` manuscripts.

The app accepts a Word document, runs JUTLP/template checks, reference checks,
Australian spelling/style corrections, and OpenAI-assisted editorial review. It
returns a reviewed `.docx` file with Word comments and tracked changes.

## Features

- Upload `.docx` manuscripts through the web interface
- Validate JUTLP structure, front page, headings, tables, figures, references, and appendices
- Check citation/reference consistency and CrossRef metadata where available
- Add Word comments for issues that need author attention
- Apply tracked changes for supported copy-editing fixes
- Generate output filenames like:

```text
FirstAuthorLastName_JUTLP_Year_CopyEdit1.docx
```

## Local Setup
### Windows

```shell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

### Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Add your OpenAI key to `.env`:

```text
OPENAI_API_KEY=your-key-here
```

Run locally:

```bash
python -m app.main 
```

Open:

```text
http://127.0.0.1:5009
```

## Railway Deployment

Railway uses the `Procfile`:

```text
web: gunicorn --workers 1 --threads 8 --timeout 120 --bind 0.0.0.0:$PORT app.main:app
```

Set these variables in Railway:

| Variable | Required | Purpose |
|---|---:|---|
| `OPENAI_API_KEY` | Yes | Enables OpenAI editorial review |
| `APP_PASSWORD` | Yes | Shared password for accessing the app |
| `SECRET_KEY` | Yes | Flask session signing key |
| `OPENAI_MODEL` | No | Defaults to `gpt-5.4-mini` |
| `OPENAI_TEMPERATURE` | No | Defaults to `0.2` |
| `OPENAI_MAX_TOKENS` | No | Defaults to `16384` |
| `MAX_UPLOAD_MB` | No | Defaults to `16` |
| `RATE_LIMIT_DEFAULT` | No | Defaults to `200 per day; 60 per hour` |
| `RATE_LIMIT_UPLOAD` | No | Defaults to `10 per hour` |
| `CORS_ALLOWED_ORIGINS` | No | Comma-separated origins allowed to call `/api/*` |
| `ACRONYM_ADMIN_PASSWORD` | No | Extra password for editing acronym rules |
| `ACRONYM_DB_PATH` | No | Path for persistent acronym storage on a Railway volume |

Generate a `SECRET_KEY` with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Changing the app password

The password gate uses the `APP_PASSWORD` variable in Railway.

To change it:

1. Open the Railway project.
2. Go to **Variables**.
3. Update `APP_PASSWORD` to the new shared access password.
4. Save/apply the change.
5. Wait for Railway to restart/redeploy the app.
6. Share the new password with authorised users.

If you also want to force all existing browser sessions to sign in again,
rotate `SECRET_KEY` at the same time. Changing only `APP_PASSWORD` changes
future login attempts, but already signed-in users may remain signed in until
their session expires or they log out.

## Using The App

1. Sign in using the shared app password.
2. Upload a `.docx` manuscript.
3. Wait for processing to finish.
4. Review the issue summary in the browser.
5. Download the reviewed Word document.

Acronym settings are available at:

```text
/settings/acronyms
```

API docs are available at:

```text
/apidocs/
```

## API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/upload` | `POST` | Upload and process a `.docx` file |
| `/api/results/<session_id>` | `GET` | Poll analysis status/results |
| `/api/download/<session_id>` | `GET` | Download the reviewed `.docx` |
| `/api/cancel/<session_id>` | `POST` | Cancel a running analysis |
| `/api/acronyms` | `GET` | List stored acronym rules |
| `/api/acronyms` | `POST` | Add acronym rule |
| `/api/acronyms/<key>` | `DELETE` | Delete acronym rule |

## Project Structure

| Path | Purpose |
|---|---|
| `app/main.py` | Flask app, auth, routes, uploads, downloads |
| `app/pipelines/feedback_gen_pipeline.py` | Main document-processing pipeline |
| `app/services/` | Validation, reference checks, corrections, output generation |
| `app/services/ai/` | OpenAI client, prompts, editorial review |
| `app/domain/` | JUTLP template, guideline, and editorial reference data |
| `app/templates/` | HTML templates |
| `app/static/` | CSS, JavaScript, logo |
| `requirements.txt` | Python dependencies |
| `Procfile` | Railway/gunicorn startup command |

## Tests

Run the test suite with:

```bash
.venv/bin/python -m pytest
```

## Troubleshooting

If uploads fail, check `MAX_UPLOAD_MB`.

If users cannot sign in, check `APP_PASSWORD` and Railway deployment logs.

If OpenAI review fails, check `OPENAI_API_KEY`, `OPENAI_MODEL`, and account access.

If acronym changes disappear after deploys, configure `ACRONYM_DB_PATH` with a Railway volume.

## Security Notes

Never commit `.env`.

Set `APP_PASSWORD` and `SECRET_KEY` in Railway before giving the app to users.

Rotate any API key that was previously shared or committed by mistake.
