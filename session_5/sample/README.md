# 📑 Guía: Despliegue de AWS Lambda vía CLI
Esta guía detalla el proceso para crear, desplegar y exponer una función Lambda a la web utilizando exclusivamente la AWS CLI.

## 1. Preparación del Código
Crea un archivo llamado `lambda_function.py` con el siguiente contenido:  

```Python
def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': '¡Hola desde la CLI de AWS!'
    }
```

Luego, comprímelo en un archivo .zip (requisito de AWS):  
* En PowerShell: `Compress-Archive -Path lambda_function.py -DestinationPath function.zip`  
* En Bash/macOS: `zip function.zip lambda_function.py`

## 2. Configuración de Permisos (IAM Role)

Lambda necesita un "Rol de ejecución". Primero crea el archivo de política de confianza `trust-policy.json`:

```Json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Service": "lambda.amazonaws.com" },
    "Action": "sts:AssumeRole"
  }]
}
```
Crea el rol en AWS y **copia el ARN** resultante:

```PowerShell
aws iam create-role --role-name mi-rol-lambda --assume-role-policy-document file://trust-policy.json
```
## 3. Creación de la Función
### a. Utiliza el ARN del paso anterior para crear la función física en la nube:
```PowerShell
aws lambda create-function `
    --function-name MiPrimeraLambda `
    --runtime python3.12 `
    --zip-file fileb://function.zip `
    --handler lambda_function.lambda_handler `
    --role arn:aws:iam::TU_CUENTA_ID:role/mi-rol-lambda
```
> **NOTA**: Deben copiar el arn de la funcion lambda creada, la van a necesitar en los permisos.

### b. Probar la función (Invocación)
Para verificar que funciona, ejecuta:
```PowerShell
aws lambda invoke --function-name MiPrimeraLambda response.json
```

## 4. Exposición a la Web (Function URL)
Para que la función sea accesible vía navegador sin usar API Gateway:

### a. Crear la configuración de la URL
```PowerShell
aws lambda create-function-url-config `
    --function-name MiPrimeraLambda `
    --auth-type NONE
```

### b. Permitir acceso público a la URL (Primer Statement)
Este comando habilita el acceso anónimo validando que el tipo de autenticación sea NONE. Si no ejecutas este paso, recibirás un error `{"Message":"Forbidden"}`:

```PowerShell
aws lambda add-permission `
    --function-name MiPrimeraLambda `
    --action lambda:InvokeFunctionUrl `
    --principal "*" `
    --function-url-auth-type NONE `
    --statement-id PublicAccessForWeb
```

### c. Permitir la invocación vía URL (Segundo Statement)
Este comando asegura que la función pueda ser invocada específicamente cuando el origen es la Function URL.
```PowerShell
aws lambda add-permission `
    --function-name MiPrimeraLambda `
    --statement-id FunctionURLAllowInvokeAction `
    --action lambda:InvokeFunction `
    --principal "*" `
    --source-arn "ARN de la funcion lambda creada"
```

### d. Cómo verificar que se aplicaron correctamente
Una vez ejecutados, pueden ver el JSON resultante con este comando:
```PowerShell
aws lambda get-policy --function-name MiPrimeraLambda
```

> * Notas importantes: `--statement-id` (Sid): Debe ser único. He usado los mismos nombres que tienes en tu JSON (`FunctionURLAllowPublicAccess` y `FunctionURLAllowInvokeAction`).  
> * Región: Asegúrate de que tu CLI esté en `us-east-1` o añade `--region us-east-1` al final de los comandos, ya que el ARN especifica esa región.

## 5. Obtención y Prueba de la URL
Para obtener la dirección final que debes pegar en el navegador:
```PowerShell
aws lambda get-function-url-config --function-name MiPrimeraLambda --query "FunctionUrl" --output text
```

## 6. Comandos de Mantenimiento Rápidos

| Acción | Comando |
| :--- | :--- |
| **Actualizar el código** | `aws lambda update-function-code --function-name MiPrimeraLambda --zip-file fileb://function.zip` |
| **Ver logs en tiempo real** | `aws logs tail /aws/lambda/MiPrimeraLambda` |
| **Listar funciones creadas** | `aws lambda list-functions --output table` |
| **Eliminar la función** | `aws lambda delete-function --function-name MiPrimeraLambda` |
| **Eliminar configuración URL** | `aws lambda delete-function-url-config --function-name MiPrimeraLambda` |