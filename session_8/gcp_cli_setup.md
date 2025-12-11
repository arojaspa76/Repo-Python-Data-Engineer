## Instalación y Configuración del CLI de Google Cloud (gcloud)

### 1. Instalar Google Cloud CLI

#### Windows:
1. Descargar el instalador desde:
   https://cloud.google.com/sdk/docs/install
2. Ejecutar el instalador y seguir instrucciones.
3. Reiniciar terminal (si es necesario) y verificar:
   ```bash
   gcloud --version
   ```

#### macOS:
```bash
curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-456.0.0-darwin-arm.tar.gz
tar -xf google-cloud-cli-456.0.0-darwin-arm.tar.gz
./google-cloud-sdk/install.sh
```

#### Linux:
```bash
curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-456.0.0-linux-x86_64.tar.gz
tar -xf google-cloud-cli-456.0.0-linux-x86_64.tar.gz
./google-cloud-sdk/install.sh
```

---

### 2. Inicializar CLI y Autenticarse

Ejecutar:
```bash
gcloud init
```

- Se abrirá el navegador para iniciar sesión con tu cuenta de Google.
- Luego seleccionarás el proyecto GCP (o crearás uno nuevo).
- El CLI quedará configurado con las credenciales y proyecto activos.

Verificar configuración:
```bash
gcloud config list
```

---

### 3. Obtener credenciales y variables importantes

#### Obtener ID del proyecto actual:
```bash
gcloud config get-value project
```

#### Cambiar o establecer un proyecto por defecto:
```bash
gcloud config set project [PROJECT_ID]
```

#### Autenticación para uso en librerías de Python:
Para que las librerías de Google en Python usen las credenciales:
```bash
gcloud auth application-default login
```
Esto creará un archivo de credenciales en:
```bash
~/.config/gcloud/application_default_credentials.json
```

Puedes exportarlo como variable de entorno en tu notebook o terminal:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="~/.config/gcloud/application_default_credentials.json"
```

---

### 4. Probar CLI de GCP

```bash
gcloud storage buckets list
```
O listar datasets de BigQuery:
```bash
gcloud bigquery datasets list
```

---

Tu CLI está listo para trabajar con GCS, BigQuery, Vertex AI y otros servicios de GCP desde Python o terminal.

