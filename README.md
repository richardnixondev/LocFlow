# LocFlow

**Open-source localization automation platform.**

LocFlow streamlines the management of software localization workflows. It provides a REST API for managing projects, resource files, and translations, with built-in support for change detection, validation, and common localization file formats.

---

## Quick Start

1. Clone the repository:

```bash
git clone https://github.com/your-org/locflow.git
cd locflow
```

2. Copy the environment file and adjust as needed:

```bash
cp .env.example .env
```

3. Build and start the services:

```bash
make build
make up
```

4. Run database migrations:

```bash
make migrate
```

5. Create a superuser:

```bash
make createsuperuser
```

6. Access the application:

- **API:** http://localhost:8000/api/v1/
- **Swagger Docs:** http://localhost:8000/api/docs/
- **Admin Panel:** http://localhost:8000/admin/

---

## API Overview

| Endpoint Prefix               | Description                          |
|-------------------------------|--------------------------------------|
| `/api/v1/projects/`           | Manage localization projects         |
| `/api/v1/resources/`          | Manage resource files (PO, XLIFF)    |
| `/api/v1/translations/`       | Manage translation entries           |
| `/api/schema/`                | OpenAPI 3.0 schema (JSON)            |
| `/api/docs/`                  | Swagger UI interactive documentation |

---

## Development

Run the test suite:

```bash
make test
```

Open a Django shell:

```bash
make shell
```

View logs:

```bash
make logs
```

---

## Roadmap

| Phase | Features | Status |
|-------|----------|--------|
| 1 -- MVP | Upload, parsing, REST API, change detection, validation, Docker | In progress |
| 2 -- Translation Memory | Elasticsearch, fuzzy search for similar strings | Planned |
| 3 -- Auth & Cache | JWT, roles (admin/translator/reviewer), Redis cache | Planned |
| 4 -- Dashboard | React/Vue frontend with language progress and quality | Planned |
| 5 -- Integrations | Webhooks, CLI tool, Git integration | Planned |
| 6 -- Advanced Pluralization | Full CLDR rules, ICU MessageFormat, advanced validation | Planned |

---

## License

This project is licensed under the [MIT License](LICENSE).
