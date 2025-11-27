# Instalación de Azure CLI, AWS CLI y Google Cloud CLI en Windows 11

Este documento describe cómo instalar las tres herramientas principales de línea de comandos para la nube en **Windows 11**:  
- **Azure CLI**  
- **AWS CLI**  
- **Google Cloud CLI (gcloud)**  

Incluye métodos vía **Winget**, instaladores gráficos MSI y comandos de validación.

---

# 1. Instalar Azure CLI en Windows 11

La Azure CLI permite administrar y automatizar recursos en Microsoft Azure desde la terminal.

## ✅ Método recomendado (Winget)

Ejecuta PowerShell *como Administrador*:

```powershell
winget install --id Microsoft.AzureCLI -e
```

## 🟦 Método alternativo: Instalador MSI

1. Descargar instalador oficial:  
   https://aka.ms/installazurecliwindows  
2. Ejecutar → **Next** → **Install** → **Finish**

## 🔍 Verificar instalación

```powershell
az version
```

## 🔑 Iniciar sesión en Azure

```powershell
az login
```

## Para listar suscripciones disponibles:
```powershell
az account list -o table
```

## Seleccionar una suscripción específica: 
```powershell
az account set --subscription "<ID o Nombre>"
```

---

# 2. Instalar AWS CLI en Windows 11

La AWS CLI permite gestionar servicios de Amazon Web Services desde la línea de comandos.

## ✅ Método recomendado (Winget)

```powershell
winget install --id Amazon.AWSCLI -e
```

## 🟧 Método alternativo: Instalador MSI

1. Descargar instalador oficial:  
   https://awscli.amazonaws.com/AWSCLIV2.msi  
2. Ejecutar → **Next** → **Install** → **Finish**

## 🔍 Verificar instalación

```powershell
aws --version
```

## 🔑 Configurar credenciales

```powershell
aws configure
```

---

# 3. Instalar Google Cloud CLI (gcloud) en Windows 11

Google Cloud CLI permite administrar recursos y servicios en GCP desde la terminal.

## ✅ Método recomendado (Winget)

```powershell
winget install --id Google.CloudSDK -e
```

## 🟨 Método alternativo: Instalador oficial

1. Descargar instalador:  
   https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe  
2. Ejecutarlo y marcar:
   - **Add gcloud to PATH**
   - **Install bundled Python**

## 🔍 Verificar instalación

```powershell
gcloud version
```

## 🔑 Inicializar sesión y configuración

```powershell
gcloud init
```

---

# 📌 Resumen rápido

| CLI | Instalación rápida | Validación |
|-----|--------------------|------------|
| **Azure CLI** | `winget install Microsoft.AzureCLI` | `az version` |
| **AWS CLI** | `winget install Amazon.AWSCLI` | `aws --version` |
| **gcloud CLI** | `winget install Google.CloudSDK` | `gcloud version` |

---

# ✔️ Fin del documento
