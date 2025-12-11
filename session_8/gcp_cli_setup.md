## Instalación y Configuración del CLI de Google Cloud (gcloud)

### 1. Instalar Google Cloud CLI

#### Windows:
1. Descargar el .zip desde:  
   https://storage.googleapis.com/cloud-sdk-release/google-cloud-sdk-540.0.0-windows-x86_64.zip
2. Extraer en:
   C:\Program Files (x86)\Google\Cloud SDK\  
3. Ejecutar en un Command Prompt como administrador:   
   C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\install.bat  
4. Acepta el uso de Python embebido.  
5. Añade manualmente la ruta indicada al PATH del sistema de las variables de ambiente una vez la instalcion haya concluido.  
5. Reiniciar terminal (si es necesario) y verificar:
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

Puedes exportarlo, en linux, como variable de entorno en tu notebook o terminal:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="~/.config/gcloud/application_default_credentials.json"
```
**_En windows, se debe crear la variable de entorno a nivel de sistema con la ruta que genera el instalador_**

---

### 4. Probar CLI de GCP

```bash
gcloud storage buckets list
```
O listar datasets de BigQuery:
```bash
bq ls
```

---

Tu CLI está listo para trabajar con GCS, BigQuery, Vertex AI y otros servicios de GCP desde Python o terminal.

