# Configuración de Cognito, Flujo OIDC y Seguridad · VidalStore

En el Caso VidalStore, AWS Cognito actúa como el **IDaaS (Identity as a Service)** centralizado en la nube. Todo el resto de la aplicación corre localmente.

---

## 1. Configuración del User Pool en AWS

### A. Grupos de Usuarios (Roles)
Se deben definir tres grupos con sus responsabilidades de negocio:
1. **`jugadores`**: Rol por omisión. Puede consultar el catálogo, realizar compras de licencias y ver su propia biblioteca.
2. **`editores`**: Puede realizar todo lo de jugadores, más agregar nuevos juegos al catálogo y editar los existentes.
3. **`administradores`**: Rol con máximos privilegios. Puede revocar licencias (`DELETE /v1/licencias/:id`), ver la lista global de todas las licencias y consultar auditoría.

### B. Resource Server y Scopes Personalizados
Se crea un Resource Server con el identificador `vidalstore` y tres scopes:
* **`vidalstore/catalogo.leer`**: Permiso que otorga la aplicación para consultar el catálogo.
* **`vidalstore/catalogo.escribir`**: Permiso para operaciones de escritura en catálogo.
* **`vidalstore/biblioteca.leer`**: Permiso para leer la biblioteca de juegos.

> [!IMPORTANT]
> **Diferencia Crítica para la Defensa**:
> * **Scopes**: Dicen qué operaciones puede solicitar la **aplicación cliente**. No identifican al usuario humano.
> * **Grupos (`cognito:groups`)**: Dicen quién es la **persona** y cuál es su **rol**. Son los únicos que pueden autorizar operaciones administrativas como revocar una licencia.

### C. Aplicaciones Cliente (App Clients)
El encargo exige **dos App Clients** creados en el mismo User Pool:

1. **App Client Principal (`vidalstore-spa`)**:
   * **Tipo**: Cliente público para SPA (**SIN secreto de cliente** / *Generate client secret* desmarcado).
   * **Flujos de autenticación**: Authorization Code Grant con PKCE habilitado.
   * **Allowed callback URLs**: `http://localhost:4200/callback`
   * **Allowed sign-out URLs**: `http://localhost:4200/`
   * **OAuth Scopes**: `openid`, `email`, `profile` + los scopes del Resource Server (`vidalstore/catalogo.leer`, etc.).

2. **App Client Secundario (`vidal-test-client`)**:
   * Creado en el mismo User Pool para satisfacer la **Prueba N°3 del Gateway (IE10)**.
   * Al emitir un token con este cliente y enviarlo a la API de VidalStore, el Gateway debe rechazarlo con `401 Unauthorized` porque el claim `client_id` no coincide con el App Client autorizado.

---

## 2. Trigger Lambda Post-Confirmación (Grupo `jugadores` Automático)

El documento **`EP1-aclaraciones.pdf`** exige que cualquier usuario nuevo que se registre quede automáticamente en el grupo `jugadores` sin que nadie deba entrar a la consola de AWS a asignarlo a mano.

### Código de la función Lambda (Node.js)
```javascript
import { CognitoIdentityProviderClient, AdminAddUserToGroupCommand } from "@aws-sdk/client-cognito-identity-provider";

const client = new CognitoIdentityProviderClient({});

export const handler = async (event) => {
    // Se ejecuta al dispararse el trigger "Post confirmation"
    if (event.triggerSource === "PostConfirmation_ConfirmSignUp") {
        const groupParams = {
            GroupName: "jugadores",
            UserPoolId: event.userPoolId,
            Username: event.userName,
        };

        try {
            await client.send(new AdminAddUserToGroupCommand(groupParams));
            console.log(`Usuario ${event.userName} agregado exitosamente a 'jugadores'.`);
        } catch (error) {
            console.error("Error al agregar usuario al grupo jugadores:", error);
            throw error;
        }
    }
    return event;
};
```
* **Rol IAM de la Lambda**: Debe tener la política `cognito-idp:AdminAddUserToGroup` sobre el User Pool.

---

## 3. Almacenamiento del Token: `sessionStorage` vs `localStorage`

### Configuración Obligatoria en Angular (`main.ts`)
```typescript
import { Amplify } from 'aws-amplify';
import { cognitoUserPoolsTokenProvider } from 'aws-amplify/auth/cognito';
import { sessionStorage } from 'aws-amplify/utils';

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: 'us-east-1_XXXXX',
      userPoolClientId: 'XXXXXXXXXXXXXXXXXX',
      loginWith: {
        oauth: {
          domain: 'vidalstore-auth.auth.us-east-1.amazoncognito.com',
          scopes: ['openid', 'email', 'profile', 'vidalstore/catalogo.leer'],
          redirectSignIn: ['http://localhost:4200/callback'],
          redirectSignOut: ['http://localhost:4200/'],
          responseType: 'code', // Authorization Code Grant con PKCE
        }
      }
    }
  }
});

cognitoUserPoolsTokenProvider.setKeyValueStorage(sessionStorage);
```

### Argumentación Técnica para la Defensa
* **¿Por qué NO `localStorage`?**:
  `localStorage` persiste indefinidamente en el disco local del navegador, incluso después de cerrar la pestaña o reiniciar el equipo. Es el segundo hallazgo crítico del informe forense del caso VidalStore, ya que amplía drásticamente la ventana de exposición frente a malware o acceso no autorizado a la máquina.
* **¿Qué se gana con `sessionStorage`?**:
  `sessionStorage` se destruye automáticamente al cerrar la pestaña o ventana del navegador y no se comparte entre pestañas independientes. Esto reduce de forma significativa la ventana de tiempo en la que el token es vulnerable.
* **¿Qué problema sigue sin resolver `sessionStorage`?**:
  Si la aplicación sufre una vulnerabilidad de **XSS (Cross-Site Scripting)**, cualquier script malicioso inyectado en la página puede acceder a `sessionStorage` y exfiltrar el token mientras la pestaña permanezca abierta. La solución óptima contra XSS en arquitecturas web es delegar el almacenamiento a cookies seguras con atributo `HttpOnly`, `Secure` y `SameSite` gestionadas por un BFF.

---

## 4. Limpieza e Higiene de Secretos

El profesor revisa el historial completo de Git. Un secreto commiteado queda registrado en el log histórico aunque se elimine en un commit posterior.

* **Qué datos son públicos por diseño**:
  - `userPoolId` (identificador del user pool).
  - `userPoolClientId` (identificador de la app client pública).
  - URL del dominio de Cognito y endpoints JWKS.
* **Qué datos NUNCA deben commitearse**:
  - Archivos `.env` con credenciales reales.
  - Secretos de clientes (`client_secret`), API Keys privadas, contraseñas de usuarios o credenciales de AWS (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`).
* **Verificación de Seguridad Obligatoria**:
  Antes de cualquier entrega o merge a `main`, ejecutar en la raíz de cada repositorio:
  ```bash
  git grep -iE "password|secret|token|cookie"
  ```
  El resultado debe estar limpio de credenciales reales.
