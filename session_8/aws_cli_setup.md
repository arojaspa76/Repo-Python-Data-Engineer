## Instalación y Configuración del AWS CLI

### 1. Instalar AWS CLI (versión 2)

#### Windows:
1. Descargar el instalador desde:
   https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-windows.html
2. Ejecutar el instalador como administrador.
3. Verificar:
   ```bash
   aws --version
   ```

#### macOS:
```bash
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /
```

#### Linux (x86_64):
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

Verifica la instalación:
```bash
aws --version
```

---

### 2. Crear Access Key y Secret Key en AWS

1. Inicia sesión en la consola de AWS: https://console.aws.amazon.com/
2. Ir a **IAM** (Identity and Access Management).
3. Selecciona **Users** (Usuarios) en el panel izquierdo.
4. Haz clic sobre tu nombre de usuario.
5. Ve a la pestaña **Security credentials**.
6. En la sección **Access keys**, haz clic en **Create access key**.
7. Guarda la **Access key ID** y la **Secret access key**.

**Nota:** Las claves se muestran solo una vez. Guarda en lugar seguro.

---

### 3. Configurar AWS CLI

En terminal o consola:
```bash
aws configure
```
Te solicitará:
- **AWS Access Key ID**: tu access key
- **AWS Secret Access Key**: tu secret key
- **Default region name**: ej. `us-east-1`, `us-west-2`, etc.
- **Default output format**: `json` (opcionalmente `table` o `text`)

Ejemplo:
```bash
AWS Access Key ID [None]: AKIA...
AWS Secret Access Key [None]: abc123...
Default region name [None]: us-east-1
Default output format [None]: json
```

---

### 4. Probar autenticación

```bash
aws s3 ls
```
Deberías ver tus buckets de S3 si todo está correctamente configurado.

