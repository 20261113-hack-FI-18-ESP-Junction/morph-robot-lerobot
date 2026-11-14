---
id: verification-es
lang: es
type: verification
owner: repository
status: verified
sources: ["local-verification"]
---

# Verificación local de secretos

El repositorio usa Gitleaks 8.30.1 para cambios preparados y un contenedor fijado por digest para historial confirmado. Instalar Gitleaks y Docker y activar el hook versionado en un clon nuevo:

```sh
git config core.hooksPath .githooks
```

El hook analiza el área de preparación y rechaza hallazgos o ausencia del analizador. Ejecutar la comprobación local independiente desde este repositorio:

```sh
./tools/scan-secrets.sh
```

El contenedor es temporal, sin red, con lectura del repositorio, oculta valores detectados y devuelve fallo ante filtraciones. La imagen fijada debe existir localmente; obtener `ghcr.io/gitleaks/gitleaks:v8.30.1` antes de ejecutar sin conexión. Es verificación local, no despliegue de producción. No requiere variables de entorno de servicio.

El flujo de GitHub Actions ejecuta el análisis del historial en cada push a `main`, los lunes a las 04:17 UTC y bajo ejecución manual. Descarga todo el historial con permiso de solo lectura y sin conservar la credencial del checkout. La imagen y la acción de checkout están fijadas a versiones inmutables. Revisar periódicamente las actualizaciones del analizador para incorporar nuevas reglas de detección. Las comprobaciones locales han pasado; el registro de entrega indica si se observó una ejecución alojada. Un clon nuevo necesita configurar el hook porque Git no transfiere configuración local.

[English](verification-en.md)
