# AGENTS.md — odoo-transbank

Integración de Transbank (Chile) como proveedor de pago para Odoo.
Cada rama corresponde a una versión de Odoo (`19.0`, `18.0`, …); no existe `main`.

## Módulos

| Módulo | Rol |
|---|---|
| `payment_transbank` | Base: proveedor `transbank`, `const.py`, campos Transbank en `payment.transaction`, hooks de instalación. |
| `payment_transbank_webpay` | Webpay Plus: método `webpay`, credenciales, controlador de retorno, create/commit. |

Lo común va en la base; cada producto (Webpay Plus, Oneclick, Mall) en su propio
`payment_transbank_<producto>` que depende de la base.

## Skills obligatorias (en este orden)

1. **`odoo-workflow`**: antes de cualquier cambio de código. Trazar el core real, armar el
   Context Brief con `file:line` y cerrar con su definition of done.
2. **`odoo-<versión>`** según la rama (`git branch --show-current` o el prefijo de
   `version` en `__manifest__.py`): en `19.0` → `odoo-19.0`, en `18.0` → `odoo-18.0`, etc.
   No mezclar APIs entre versiones.
3. **`odoo-transbank`**: en todo lo que toque Transbank (flujos, códigos, SDK, refunds,
   Oneclick, salida a producción). Es la fuente de verdad del dominio: si algo no está ahí
   ni en la documentación oficial, se verifica, no se supone.

Opcionales: `security-review` antes de mergear cambios en controladores o credenciales;
`context7-mcp` para consultar APIs de librerías.

## Runtime (para `odoo-workflow`)

Cada desarrollador necesita, en su máquina:

- Un checkout del **core de Odoo** de la misma versión que la rama (community; enterprise
  solo si se trabaja algo que dependa de él).
- Un **entorno Python** de esa versión con las dependencias de Odoo, `transbank-sdk`
  (versión de `requirements.txt`), `ruff` y `pre-commit`.

Las rutas concretas **no se versionan**. Cada uno crea su `.claude/odoo.json` (gitignored):

```json
{
  "odoo_version": "19.0",
  "odoo_root": "<ruta al core de Odoo 19.0>",
  "python": "<ruta al python del venv 19.0>",
  "addons": ["."]
}
```

`"addons": ["."]` agrega los módulos de este repo (rutas relativas a la raíz). En lugar de
`addons` se puede indicar `"conf"` con un `odoo.conf` cuyo `addons_path` incluya el repo.

Si `odoo_trace env` responde `SETUP ERROR`, falta este archivo o la ruta del core no está
disponible (disco no montado, checkout movido): corregirlo antes de trazar, nunca trabajar
de memoria.

## Convenciones

- Versión del módulo `<odoo>.<major>.<minor>.<patch>`: se sube en cada cambio de modelo,
  datos o vistas.
- Python: ruff (`pyproject.toml`): línea de 126, comillas simples, imports
  `stdlib → third-party → odoo → odoo.addons → local`.
- XML: prettier + `@prettier/plugin-xml` (`prettier.config.cjs`), 4 espacios.
- Antes de commitear: `pre-commit run --all-files`.
- Textos visibles con `_()`; idioma base inglés, traducción al español en `i18n/`.
- Dependencia externa: `transbank-sdk` fijada en `requirements.txt`. Si cambia, actualizar
  también `README.rst` y revisar `odoo-transbank` → `references/sdk-python.md`.

## Pruebas

- Instalar en una base desechable con `--test-enable`, usando el runtime de
  `.claude/odoo.json`. Nunca `-i`/`-u` sobre una base con nombre (dev, staging).
- Pruebas manuales: provider en estado `test` con las credenciales públicas de integración
  del SDK (`IntegrationCommerceCodes` / `IntegrationApiKeys`); tarjetas en `odoo-transbank`
  → `references/testing.md`.
- Tests automáticos en `<módulo>/tests/`, con el SDK mockeado y sin red.

## Git

- **Conventional Commits** con la skill `git-commit`: `type(módulo): descripción`
  (ej. `fix(payment_transbank_webpay): ...`). **No** usar `odoo-commit` (`[TAG] module:`),
  aunque se autoactive en repos Odoo.
- Ramas de trabajo desde la rama de versión: `<versión>-<tema>` (ej. `19.0-support_refund`),
  mergeadas con merge commit.
- Commit o push solo cuando se pide.
