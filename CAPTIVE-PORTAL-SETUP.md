# Captive Portal - Setup Completo

## Estado actual (2026-03-18)

### Componentes configurados

#### 1. App Flask (Gaman WiFi)
- **URL**: http://wifi.apps.grupogaman.com.ar
- **Portal**: http://wifi.apps.grupogaman.com.ar/portal
- **Dominio configurado en Coolify** (Traefik proxy → contenedor puerto 5000)
- **Google OAuth**: credentials configuradas como env vars en Coolify
  - `GOOGLE_CLIENT_ID`: (configurado en Coolify, ver memoria del proyecto)
  - `GOOGLE_CLIENT_SECRET`: (configurado en Coolify, ver memoria del proyecto)
  - `PORTAL_SESSION_HOURS`: 24
- **Redirect URI en Google Console**: http://wifi.apps.grupogaman.com.ar/portal/callback
- **Tipo OAuth**: Internal (Google Workspace)
- **Tablas creadas**: gaman_allowed_domain, gaman_portal_user, gaman_portal_session
- **Dependencia agregada**: `requests` en requirements.txt (requerida por authlib)

#### 2. FreeRADIUS (192.168.38.3)
- **Policy captive portal**: `/etc/freeradius/3.0/policy.d/captive_portal`
- **Lógica en site default**: `captive_portal_mac_auth` insertado después de `-sql` en sección `authorize`
- **Backup config original**: `/etc/freeradius/3.0/default.bak`

**Comportamiento RADIUS:**

| Escenario | Resultado |
|---|---|
| MAC desconocida (no está en radcheck) | Access-Accept + VLAN 60 + Session-Timeout 60s |
| MAC conocida con grupo (en radcheck + radusergroup) | Access-Accept + VLAN del grupo (ej: VLAN 10) |
| Usuario sin grupo | Access-Accept (sin VLAN) |

**Policy `/etc/freeradius/3.0/policy.d/captive_portal`:**
```
captive_portal_mac_auth {
    if (!control:Cleartext-Password) {
        update control {
            Auth-Type := Accept
        }
        update reply {
            Tunnel-Type := VLAN
            Tunnel-Medium-Type := IEEE-802
            Tunnel-Private-Group-Id := "60"
            Session-Timeout := 60
        }
    }
}
```

**En `sites-enabled/default`, sección authorize, después de `-sql`:**
```
	#  Captive portal: unknown MACs get VLAN 60 + Session-Timeout 60s
	captive_portal_mac_auth
```

#### 3. Coolify (192.168.38.4)
- **Dominio app**: http://wifi.apps.grupogaman.com.ar
- **Traefik**: corriendo, red Docker recreada sin IPv6 (fix error ParseAddr)
- **Puerto**: 5000 (interno), Traefik rutea puerto 80 → 5000

#### 4. Red / MikroTik
- **VLAN 60**: VLAN de registro (acceso restringido: solo portal + Google + DNS)
- **VLANs de internet**: asignadas por grupo en radgroupreply (ej: Notebooks → VLAN 10)

#### 5. Aruba Instant On AP25
- **SSID guest**: abierto, portal invitado externo
- **URL portal**: http://wifi.apps.grupogaman.com.ar/portal
- **Walled garden**: wifi.apps.grupogaman.com.ar, accounts.google.com, oauth2.googleapis.com, fonts.googleapis.com, cdn.jsdelivr.net
- **Pendiente verificar**: MAC Authentication con RADIUS habilitado, VLAN 60 como default

---

## Flujo esperado

1. Dispositivo se conecta al SSID guest
2. RADIUS no conoce la MAC → Accept + VLAN 60 + Session-Timeout 60s
3. AP pone al cliente en VLAN 60 (registro, sin internet)
4. AP redirige al portal externo (http://wifi.apps.grupogaman.com.ar/portal)
5. Usuario ve landing con botón "Iniciar sesión con Google"
6. OAuth con Google → portal verifica dominio permitido
7. Portal registra MAC en radcheck + radusergroup (con grupo/VLAN asignado)
8. Pantalla de éxito → usuario desconecta y reconecta WiFi (o espera ~60s al Session-Timeout)
9. AP re-autentica MAC contra RADIUS → MAC ahora conocida → Accept + VLAN de internet
10. Dispositivo obtiene acceso a internet en la VLAN del grupo

---

## Pendientes para testeo

- [ ] Verificar MAC Authentication habilitado en SSID de Instant On
- [ ] Verificar VLAN 60 como default en el SSID
- [ ] Probar flujo completo: conectar → portal → Google OAuth → reconectar → internet
- [ ] Verificar que el parámetro de MAC del AP sea `mac` (si no, editar `app/blueprints/portal/routes.py`)
- [ ] Crear dominio permitido en admin (Dominios → Nuevo Dominio → dominio Google Workspace del cliente)

## Troubleshooting

### RADIUS no responde
```bash
# En 192.168.38.3:
sudo systemctl status freeradius
sudo freeradius -X  # modo debug

# Test manual:
radtest AA-BB-CC-DD-EE-FF AA-BB-CC-DD-EE-FF localhost 0 testing123
```

### App no carga
```bash
# Ver logs del contenedor en Coolify UI o:
ssh tecser@192.168.38.4
sudo docker logs ks0k004o4ksowogkokcgs8kc-<id>
```

### Google OAuth falla
- Verificar redirect URI en Google Console: `http://wifi.apps.grupogaman.com.ar/portal/callback`
- Verificar env vars en Coolify: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
- Verificar dominio permitido creado en admin de la app
