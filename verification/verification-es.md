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

Ejecutar tras commits y periódicamente al revisar historial; este documento no instala automatizaciones. Un clon nuevo necesita configurar el hook porque Git no transfiere configuración local.

[English](verification-en.md)
