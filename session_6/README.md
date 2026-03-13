# Análisis y Deployment de Azure Function function_app.py

## Análisis Azure Function function_app.py

La carpeta contiene un proyecto de **Azure Functions** desarrollado en **Python**. Los archivos principales son:

- **`function_app.py`**: Define dos funciones HTTP:
  - `funcion_con_lista`: Recibe un número como parámetro, ordena una lista hardcodeada de números usando quicksort, y realiza una búsqueda binaria para encontrar el índice del número objetivo.
  - `funcion_con_archivo`: Similar, pero lee una lista de números desde un archivo CSV en **Azure Blob Storage** (usando variables de entorno para la conexión).
- **`host.json`**: Configuración estándar de Azure Functions v2, con extensiones para bundles.
- **`local.settings.json`**: Configuración local con placeholders para credenciales de Azure Storage (necesitan ser completadas).
- **`requirements.txt`**: Dependencias: `azure-functions` y `azure-storage-blob`.

La función requiere acceso a Azure Blob Storage para la segunda ruta, por lo que necesitarás una cuenta de almacenamiento en Azure con un contenedor y un blob llamado `data.csv` (con números enteros, uno por línea).

## Paso a Paso para Ejecutar la Azure Function en Azure

Basado en las mejores prácticas de Azure (usando Flex Consumption plan para escalabilidad serverless, Linux para Python, y AZD para deployment), aquí está el proceso completo. Asumimos que tienes una suscripción de Azure activa y permisos para crear recursos.

### 1. Preparación del Entorno Local
- **Instala Azure CLI**: Descárgalo desde [azure.microsoft.com](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) e instala en Windows.
- **Instala Azure Functions Core Tools**: Ejecuta `npm install -g azure-functions-core-tools@4` (requiere Node.js).
- **Instala Azure Developer CLI (AZD)**: Descárgalo desde [aka.ms/azd](https://aka.ms/azd) e instala.
- **Inicia sesión en Azure**: Ejecuta `az login` en la terminal para autenticarte.
- **Verifica Python**: Asegúrate de tener Python 3.8+ instalado. Crea un entorno virtual si es necesario: `python -m venv venv` y activa con `venv\Scripts\activate`.
- **Instala dependencias**: En el directorio `session_6`, ejecuta `pip install -r requirements.txt`.

### 2. Configura el Proyecto para Deployment
- Navega al directorio `session_6` en tu terminal.
- Inicializa AZD: Ejecuta `azd init`. Selecciona un template para "Azure Functions" (elige Python). Esto creará archivos como `azure.yaml` y carpetas `.azure` con infraestructura en Bicep.
  - Si el template no detecta automáticamente, especifica manualmente: Elige "Function App" y configura para Flex Consumption plan.
- Edita `local.settings.json` con valores reales (obtén de Azure Portal):
  - `AZURE_STORAGE_ACCOUNT_NAME`: Nombre de tu cuenta de Storage.
  - `AZURE_STORAGE_ACCOUNT_KEY`: Clave de acceso.
  - `AZURE_STORAGE_CONTAINER`: "datasets" (o el nombre de tu contenedor).
  - `AZURE_STORAGE_BLOB`: "data.csv" (o el nombre de tu blob).
- Sube el archivo `data.csv` a Blob Storage: Usa Azure Portal o CLI (`az storage blob upload`).

### 3. Genera y Valida la Infraestructura
- Usa AZD para generar Bicep: Ejecuta `azd infra synth`. Esto crea archivos en `.azure/infra` basados en el template.
- Valida errores: Revisa los archivos Bicep generados (ej. `main.bicep`) para asegurar que incluyan:
  - Function App con runtime Python, OS Linux, plan Flex Consumption (FC1).
  - Storage Account con contenedor.
  - Application Insights para monitoreo.
- Si hay errores, corrige manualmente (ej. agrega `functionAppConfig` para Flex Consumption).

### 4. Despliega a Azure
- Ejecuta `azd up` en el directorio `session_6`. Esto:
  - Provisiona recursos (Function App, Storage Account, etc.).
  - Despliega el código de la función.
  - Configura variables de entorno en la Function App.
- Monitorea el progreso: AZD mostrará logs. Si falla, ejecuta `azd down` para limpiar y reintenta.
- Verifica en Azure Portal: Ve a "Function Apps" y confirma que `session_6` esté creada y ejecutándose.

### 5. Prueba la Función
- Obtén la URL de la Function App desde Azure Portal (en "Functions" > tu función > "Get Function URL").
- Prueba `funcion_con_lista`: Llama a `https://<tu-app>.azurewebsites.net/api/funcion_con_lista?numero=42` (o vía POST con JSON `{"numero": 42}`).
- Prueba `funcion_con_archivo`: Llama a `https://<tu-app>.azurewebsites.net/api/funcion_con_archivo?numero=42` (asegúrate de que `data.csv` tenga datos).
- Verifica logs: En Azure Portal > Function App > "Logs" o usa `azd monitor`.

### 6. Monitoreo y Mejores Prácticas Aplicadas
- **Escalabilidad**: Usa Flex Consumption para auto-escalado serverless.
- **Seguridad**: Configura autenticación (ej. Function keys) en lugar de anonymous. Habilita VNET si es necesario.
- **Monitoreo**: Application Insights está habilitado por defecto; revisa excepciones y dependencias.
- **Limpieza**: Si pruebas, ejecuta `azd down` para eliminar recursos y evitar costos.
- **Errores Comunes**: Si deployment falla con errores de formato, usa `func azure functionapp publish <app-name>` como alternativa.

Si encuentras errores específicos, proporciona los logs para ayudar a depurar. Este proceso debería tomar 15-30 minutos una vez configurado.