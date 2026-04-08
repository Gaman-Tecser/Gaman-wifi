# Gaman WiFi - Instructivo para el Administrador

**URL de acceso:** http://wifi.apps.grupogaman.com.ar
**Credenciales:** Las provistas por el equipo de TI

---

## 1. Conceptos generales

Gaman WiFi administra el acceso WiFi corporativo. Toda accion que realices en el panel (crear usuarios, grupos, puntos de acceso) **se sincroniza automaticamente con el servidor RADIUS** (FreeRADIUS). No necesitas ejecutar ningun proceso de sincronizacion manual, salvo para equipos importados desde Active Directory.

### Que se sincroniza automaticamente

| Accion en el panel | Efecto en RADIUS |
|---|---|
| Crear/editar/eliminar un **usuario WiFi** | Se crea/actualiza/elimina su credencial y grupo |
| Habilitar/deshabilitar un **usuario WiFi** | Se permite/bloquea su autenticacion |
| Crear/editar/eliminar un **grupo WiFi** | Se crea/actualiza/elimina la VLAN asignada |
| Crear/editar/eliminar un **punto de acceso** | Se registra/actualiza/elimina el equipo + se reinicia FreeRADIUS |

### Que requiere accion manual

| Accion | Cuando hacerlo |
|---|---|
| **Importar equipos desde AD** | Cuando se suman nuevas PCs al dominio |
| **Sincronizar equipos AD a RADIUS** | Despues de importar o cambiar grupos de equipos AD |

---

## 2. Configuracion inicial (primera vez)

Seguir este orden:

### Paso 1: Crear grupos WiFi

1. Ir a **Grupos** en el menu lateral
2. Click en **Nuevo Grupo**
3. Completar:
   - **Nombre**: nombre descriptivo (ej: "Administracion", "Produccion")
   - **VLAN ID**: numero de VLAN que el switch/AP asignara a los usuarios de este grupo
4. Guardar

> Crear al menos un grupo antes de crear usuarios.

### Paso 2: Registrar puntos de acceso

1. Ir a **Puntos de Acceso** en el menu lateral
2. Click en **Nuevo Punto de Acceso**
3. Completar:
   - **Nombre**: nombre identificatorio (ej: "AP-Oficina-1")
   - **IP**: direccion IP del equipo
   - **Secret**: clave compartida con FreeRADIUS (debe coincidir con la configurada en el AP)
4. Guardar

> Al guardar, FreeRADIUS se reinicia automaticamente para reconocer el nuevo equipo.

### Paso 3: Crear usuarios WiFi (manual)

1. Ir a **Usuarios** en el menu lateral
2. Click en **Nuevo Usuario**
3. Completar:
   - **Username**: nombre de usuario para conectarse al WiFi
   - **Password**: contrasena WiFi
   - **Grupo**: seleccionar el grupo (determina la VLAN)
4. Guardar

> El usuario ya puede conectarse al WiFi inmediatamente.

---

## 3. Operacion diaria

### Gestionar usuarios WiFi

- **Deshabilitar un usuario**: en la lista de Usuarios, click en el boton de toggle. El usuario no podra conectarse pero no se elimina.
- **Habilitar un usuario**: mismo boton de toggle para reactivar.
- **Cambiar grupo/VLAN**: editar el usuario y seleccionar otro grupo.
- **Cambiar contrasena**: editar el usuario e ingresar nueva contrasena.
- **Eliminar un usuario**: click en Eliminar. Se remueve de RADIUS inmediatamente.

### Gestionar grupos

- **Cambiar VLAN de un grupo**: editar el grupo y cambiar el VLAN ID. Aplica a todos los usuarios del grupo.
- **Eliminar un grupo**: solo si no tiene usuarios asignados.

### Reiniciar FreeRADIUS manualmente

Si por alguna razon necesitas forzar un reinicio de FreeRADIUS:

1. Ir a **Puntos de Acceso**
2. Click en el boton **Reiniciar RADIUS**

---

## 4. Importar equipos desde Active Directory

Este proceso trae las cuentas de computadora del dominio al sistema. Es necesario para autenticacion 802.1X por maquina.

### Cuando hacerlo

- Cuando se incorporan nuevas PCs al dominio
- Periodicamente (ej: una vez por semana) para mantener el listado actualizado

### Procedimiento

1. Ir a **Equipos AD** en el menu lateral
2. Click en **Importar desde AD**
   - El sistema se conecta al controlador de dominio via LDAP
   - Trae todas las cuentas de computadora habilitadas
   - Las PCs nuevas se agregan, las existentes se actualizan
3. Revisar la lista de equipos importados
4. (Opcional) Cambiar el grupo asignado a equipos individuales si es necesario
5. Click en **Sincronizar todos a RADIUS**
   - Esto registra los equipos en FreeRADIUS para que puedan autenticarse via 802.1X

> **Importante:** Si solo cambias el grupo de un equipo individual, ese cambio se sincroniza a RADIUS automaticamente. El boton "Sincronizar todos" es para aplicar cambios masivos despues de una importacion.

### Habilitar/Deshabilitar equipos AD

- **Deshabilitar**: el equipo se remueve de RADIUS y no podra conectarse al WiFi
- **Habilitar**: el equipo se vuelve a registrar en RADIUS

---

## 5. Configurar la GPO de WiFi (Politica de Grupo)

Para que las PCs del dominio se conecten automaticamente al WiFi corporativo via 802.1X, es necesario configurar una politica de grupo (GPO) en el controlador de dominio.

### Ruta en el editor de GPO

**Computer Configuration > Policies > Windows Settings > Security Settings > Wireless Network (IEEE 802.11) Policies**

### Pasos

1. Click derecho > **Create A New Wireless Network Policy for Windows Vista and Later Releases**
2. En la pestana **General**, ponerle un nombre (ej: "WiFi Corporativo Gaman")
3. Click en **Add > Infrastructure**
4. Configurar las siguientes pestanas:

#### Pestana Connection

| Campo | Valor |
|---|---|
| Network Name (SSID) | El nombre exacto del SSID corporativo |
| Connect automatically when in range | Tildar |

#### Pestana Security

| Campo | Valor |
|---|---|
| Authentication | WPA2-Enterprise |
| Encryption | AES |
| Network authentication method | Microsoft: Protected EAP (PEAP) |

5. Click en **Properties** (al lado de PEAP):

| Campo | Valor |
|---|---|
| Validate server certificate | Destildar (salvo que se tenga CA propia) |
| Authentication method | Secured password (EAP-MSCHAPv2) |

6. Click en **Configure** (al lado de EAP-MSCHAPv2):

| Campo | Valor |
|---|---|
| Automatically use my Windows logon name and password | **Destildar** |

7. Volver a la pestana **Security**, click en **Advanced**:

| Campo | Valor |
|---|---|
| Authentication mode | **Computer authentication** |

> **Importante:** Se usa "Computer authentication" (no User authentication) porque el sistema autentica la cuenta de maquina de la PC, no las credenciales del usuario de Windows. Esto permite que la PC se conecte al WiFi incluso antes de que un usuario inicie sesion.

### Como funciona la autenticacion

```
PC (cuenta de maquina) --> Access Point --> FreeRADIUS --> ntlm_auth/Winbind --> Active Directory
```

1. La PC envia sus credenciales de maquina via PEAP/MSCHAPv2
2. FreeRADIUS valida las credenciales contra Active Directory (via Winbind)
3. FreeRADIUS busca el equipo en su base de datos para asignarle la VLAN correcta
4. El AP conecta la PC a la VLAN correspondiente

> **Requisito previo:** El equipo debe estar importado y sincronizado a RADIUS desde el panel (ver seccion 4).

### Verificar que la GPO se aplico

En una PC del dominio, ejecutar en CMD:

```
gpresult /r
```

Buscar en la salida que aparezca el nombre de la politica WiFi configurada.

Tambien se puede verificar en:

```
Configuracion de Windows > Red e Internet > Wi-Fi > Administrar redes conocidas
```

El SSID corporativo deberia aparecer en la lista.

---

## 6. Portal de autoservicio (usuarios con Google)

Si esta configurado, los usuarios pueden registrarse solos al WiFi usando su cuenta de Google corporativa.

### Configuracion (una sola vez)

1. Ir a **Dominios** en el menu lateral
2. Click en **Nuevo Dominio**
3. Completar:
   - **Dominio**: el dominio de email permitido (ej: "grupogaman.com.ar")
   - **Grupo por defecto**: el grupo WiFi que se asignara a los usuarios de este dominio
4. Guardar

### Como funciona para el usuario final

1. El usuario accede al portal cautivo (se muestra al conectarse al SSID guest)
2. Click en "Iniciar sesion con Google"
3. Se autentica con su cuenta corporativa
4. El sistema le genera automaticamente credenciales WiFi
5. El usuario ve su nombre de usuario y contrasena en pantalla
6. Se conecta al WiFi corporativo con esas credenciales

### Gestion de usuarios del portal

En **Usuarios Portal** podes:

- Ver todos los usuarios registrados via portal
- **Cambiar grupo**: reasignar a otro grupo/VLAN
- **Resetear contrasena**: genera una nueva contrasena
- **Deshabilitar/Habilitar**: bloquear o permitir acceso
- **Eliminar**: remover completamente del sistema

---

## 7. Resumen de flujos

```
USUARIO WIFI MANUAL
  Panel > Crear usuario > [automatico] > RADIUS actualizado > Usuario conecta

EQUIPO AD (802.1X)
  Panel > Importar desde AD > Asignar grupos > Sincronizar a RADIUS
  GPO > PC recibe politica WiFi > Se conecta automaticamente

PORTAL AUTOSERVICIO
  Usuario > Google OAuth > [automatico] > RADIUS actualizado > Usuario conecta
```

---

## 8. Preguntas frecuentes

**Un usuario no puede conectarse al WiFi, que reviso?**

1. Verificar que el usuario este habilitado (no deshabilitado) en el panel
2. Verificar que el punto de acceso esta registrado en el sistema
3. Verificar que el grupo del usuario tiene una VLAN valida
4. Probar reiniciar RADIUS desde Puntos de Acceso > Reiniciar RADIUS

**Agregue un AP nuevo y no funciona**

- Verificar que la IP y el secret coinciden con la configuracion del equipo fisico
- El reinicio de RADIUS es automatico, pero puede intentar reiniciar manualmente

**Las PCs del dominio no se conectan al WiFi 802.1X**

1. Verificar que se importaron los equipos desde AD (seccion 4)
2. Verificar que se sincronizaron a RADIUS (boton "Sincronizar todos")
3. Verificar que la GPO de WiFi esta aplicada en las PCs (ejecutar `gpresult /r`)
4. Verificar que el equipo esta habilitado en la lista de Equipos AD
5. Verificar que el SSID en la GPO coincide exactamente con el configurado en el AP

**La GPO no se aplica en una PC**

1. Ejecutar `gpupdate /force` en la PC
2. Verificar que la PC esta en la OU correcta donde se aplica la GPO
3. Reiniciar la PC (algunas politicas de Computer requieren reinicio)

**Un equipo AD aparece como "no sincronizado"**

- Click en "Sincronizar todos a RADIUS" para forzar la sincronizacion de todos los equipos
