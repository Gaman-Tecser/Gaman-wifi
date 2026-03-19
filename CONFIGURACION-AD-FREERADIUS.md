# Configuración FreeRADIUS + Active Directory

## Resumen

Un solo SSID (Gaman, WPA2-Enterprise) para todos los usuarios:
- **PCs del dominio** → auth automática via PEAP/MSCHAPv2 (ntlm_auth contra AD)
- **Usuarios manuales** → admin crea user/pass desde la app Flask
- **Portal autoservicio** → usuarios con Google generan credenciales en /portal/

FreeRADIUS intenta primero SQL (radcheck) y si no encuentra el usuario, usa ntlm_auth contra AD.

---

## Parte 1: FreeRADIUS + AD (servidor 192.168.38.3)

### 1.1 Instalar paquetes

```bash
sudo apt update
sudo apt install -y samba winbind libpam-winbind libnss-winbind krb5-user
```

Cuando pregunte realm de Kerberos: **GRUPOGAMAN.LOCAL** (en mayúsculas).

### 1.2 Configurar Samba

Editar `/etc/samba/smb.conf`:

```ini
[global]
    realm = GRUPOGAMAN.LOCAL
    workgroup = GRUPOGAMAN
    security = ads
    ntlm auth = mschapv2-and-ntlmv2-only
    winbind use default domain = yes
    winbind enum users = yes
    winbind enum groups = yes
    idmap config * : backend = tdb
    idmap config * : range = 10000-20000
```

### 1.3 Unir al dominio

```bash
sudo net ads join -U Administrator
# Ingresar password del admin de AD cuando lo pida
sudo net ads testjoin   # Debe decir "Join is OK"
```

### 1.4 Configurar nsswitch

Editar `/etc/nsswitch.conf`, agregar `winbind` a las líneas passwd y group:

```
passwd: files systemd winbind
group:  files systemd winbind
```

### 1.5 Iniciar servicios

```bash
sudo systemctl enable --now smbd nmbd winbind
```

### 1.6 Permisos para FreeRADIUS

FreeRADIUS necesita acceso al socket de winbind:

```bash
sudo usermod -aG winbindd_priv freerad
sudo chgrp freerad /var/lib/samba/winbindd_privileged
sudo chmod 750 /var/lib/samba/winbindd_privileged
```

### 1.7 Verificar ntlm_auth

Probar con un usuario de AD:

```bash
ntlm_auth --request-nt-key --domain=GRUPOGAMAN --username=usuario_test --password=clave_test
```

Debe devolver: `NT_STATUS_OK`

### 1.8 Configurar mschap en FreeRADIUS

Editar `/etc/freeradius/3.0/mods-available/mschap`, reemplazar el bloque `mschap {}`:

```
mschap {
    use_mppe = yes
    require_encryption = yes
    require_strong = yes

    ntlm_auth = "/usr/bin/ntlm_auth --allow-mschapv2 --request-nt-key --username=%{mschap:User-Name} --domain=GRUPOGAMAN --challenge=%{%{mschap:Challenge}:-00} --nt-response=%{%{mschap:NT-Response}:-00}"
}
```

### 1.9 Verificar EAP

En `/etc/freeradius/3.0/mods-available/eap`, verificar que PEAP esté habilitado:

```
eap {
    default_eap_type = peap

    tls-config tls-common {
        private_key_file = /etc/freeradius/3.0/certs/server.key
        certificate_file = /etc/freeradius/3.0/certs/server.pem
        ca_file = /etc/freeradius/3.0/certs/ca.pem
    }

    peap {
        default_eap_type = mschapv2
        virtual_server = "inner-tunnel"
    }

    mschapv2 {
    }
}
```

### 1.10 Configurar sites-enabled/default

En `/etc/freeradius/3.0/sites-available/default`:

```
authorize {
    preprocess
    eap {
        ok = return
    }
    sql
    if (!ok) {
        mschap
    }
}

authenticate {
    Auth-Type MS-CHAP {
        mschap
    }
    eap
}
```

### 1.11 Configurar inner-tunnel

En `/etc/freeradius/3.0/sites-available/inner-tunnel`:

```
authorize {
    mschap
    sql
}

authenticate {
    Auth-Type MS-CHAP {
        mschap
    }
}
```

### 1.12 Habilitar módulo mschap

```bash
cd /etc/freeradius/3.0/mods-enabled/
sudo ln -sf ../mods-available/mschap mschap
# eap y sql ya deberían estar habilitados
```

### 1.13 Reiniciar y probar

```bash
sudo systemctl restart freeradius

# Si falla, correr en modo debug para ver errores:
sudo systemctl stop freeradius
sudo freeradius -X
```

---

## Parte 2: GPO en Active Directory (en el DC)

### 2.1 Crear GPO

1. Abrir `gpmc.msc` en el Domain Controller
2. Crear nueva GPO: **"WiFi Gaman Enterprise"**
3. Vincular a la OU donde están las PCs

### 2.2 Configurar WiFi en la GPO

Navegar a:
`Computer Configuration > Windows Settings > Security Settings > Wireless Network (IEEE 802.11) Policies`

Crear nueva policy con estos valores:

| Campo | Valor |
|-------|-------|
| SSID | Gaman |
| Seguridad | WPA2-Enterprise |
| Cifrado | AES |
| Autenticación | PEAP |
| Inner auth | MSCHAPv2 |
| Authentication mode | Computer or User |

**"Computer or User"** hace que la PC se conecte automáticamente tanto antes como después del login de Windows.

### 2.3 Verificar en una PC de prueba

```cmd
gpupdate /force
netsh wlan show profiles
```

Debe aparecer el perfil "Gaman" y la PC debería conectarse automáticamente.

---

## Parte 3: Portal autoservicio (ya implementado en código)

El portal está en `http://wifi.apps.grupogaman.com.ar/portal/`

Flujo:
1. Usuario accede a la URL
2. Inicia sesión con Google (dominio autorizado)
3. Se generan credenciales WiFi automáticamente (email + password random)
4. Se registran en RADIUS (radcheck + radusergroup)
5. Se muestran las credenciales en pantalla con instrucciones
6. Si vuelve a acceder, recupera las credenciales existentes
7. Puede regenerar la contraseña si lo necesita

---

## Verificación final

- [ ] PC del dominio se conecta a SSID Gaman automáticamente (sin clave)
- [ ] Usuario creado desde admin Flask se conecta con user/pass
- [ ] Portal autoservicio: OAuth con Google → ver credenciales → conectar
- [ ] Recovery: acceder al portal de nuevo → ver credenciales existentes
- [ ] Regenerar: botón regenerar → nueva contraseña → funciona

---

## Prerequisitos pendientes

- [ ] Configurar Google OAuth credentials (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET) en Coolify
- [ ] Correr migración Alembic en servidor (tablas portal)
- [ ] Configurar SSID "Gaman" como WPA2-Enterprise en el AP apuntando a RADIUS 192.168.38.3
