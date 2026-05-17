# TerraShield — Integración de Recomendaciones en Frontend

## Estado: ✅ COMPLETADO

Se ha implementado completamente el sistema de recomendaciones en la interfaz de usuario.

---

## Cambios Realizados

### 1. **Backend — Servidor Flask** (`servidor.py`)
**Endpoint existente (no requería cambios):**
```
POST /apantallamiento/recomendar
```
- Ya estaba implementado en línea 416-436
- Llama a `calculos_apant.calcular_recomendaciones()`
- Recibe: `params`, `S`, `verification`
- Retorna: `{'ok': True, 'recommendations': [...]}`

### 2. **Backend — Lógica de Recomendaciones** (`calculos_apant.py`)
**Completamente refactorizado y optimizado:**
- ✅ Función `_recommend_single_mast()` - Mástil único alineado
- ✅ Función `_recommend_guard_wire_connection()` - Cable entre 2 mástiles
- ✅ Funciones helper para encontrar mástiles cercanos
- ✅ Verificación interna garantizada antes de sugerir
- ✅ Validaciones: distancia ≥3m, longitud cable, orientación paralelo/perpendicular

### 3. **Frontend — HTML** (`index.html`)

#### Botón de Recomendaciones
```html
<button class="btn btn-secondary" id="apant-btn-recomendaciones" 
        onclick="apantGenerarRecomendaciones()" 
        style="...display:none;">
  <svg>...</svg>
  Generar recomendaciones
</button>
```
- Ubicado en el header del panel de verificación (línea 570)
- Solo visible cuando hay equipos sin apantallar
- Se oculta automáticamente cuando todos están protegidos

#### Panel de Recomendaciones
```html
<div class="result-table-wrap" id="apant-recs-panel" style="display:none;">
  <div id="apant-recs-body"><!-- contenido generado por JS --></div>
</div>
```
- Panel similiar al de verificación (líneas 585-593)
- Se muestra cuando se generan recomendaciones
- Renderiza cada opción con detalles y botones de acción

### 4. **Frontend — JavaScript** (`apantallamiento.js`)

#### Función: `apantGenerarRecomendaciones()`
```javascript
async function apantGenerarRecomendaciones()
```
- Recopila datos actuales del modelo (mástiles, equipos, guardas)
- Construye payload con parámetros: BIL, Zs, k, S
- Llama a `POST /apantallamiento/recomendar`
- Maneja errores y muestra spinner de carga
- Renderiza recomendaciones si tiene éxito

**Características:**
- Desactiva botón durante procesamiento
- Muestra spinner visual
- Toast con número de recomendaciones
- Manejo robusto de errores

#### Función: `apantRenderRecommendations(recommendations)`
```javascript
function apantRenderRecommendations(recommendations)
```
- Renderiza cada recomendación en un card
- Muestra tipo (mástil o cable) con icono
- Información de validación y cobertura
- Botones: Aplicar, Descartar

**Contenido de cada recomendación:**
```
┌─────────────────────────────────────────┐
│ [Icono] Título                          │
│ Razón/descripción detallada             │
│                                         │
│ Estado: ✓ Validado | Cobertura: Sí     │
│ Equipos: X/Y | Longitud: Zm / Zm máx   │
│                                         │
│ [Aplicar] [Descartar]                   │
└─────────────────────────────────────────┘
```

#### Función: `apantRenderVerif(verif)`
**Actualización:** Ahora muestra/oculta el botón
```javascript
const recBtn = document.getElementById('apant-btn-recomendaciones');
if (recBtn) {
  recBtn.style.display = allOk ? 'none' : '';
}
```
- Si todos apantallados (`allOk=true`) → botón oculto
- Si hay equipos sin apantallar → botón visible

---

## Flujo de Uso

### 1️⃣ Usuario calcula apantallamiento
```
Usuario ingresa mástiles, equipos, guardas
       ↓
Click "Calcular apantallamiento"
       ↓
Modelo se renderiza en 3D
```

### 2️⃣ Ver verificación
```
Tabla de verificación muestra:
  ├─ Equipo 1: 100% ✓ Apantallado
  └─ Equipo 2: 27.4% ✗ Fuera de capa
       ↓
Botón "Generar recomendaciones" APARECE (porque Equipo 2 no está apantallado)
```

### 3️⃣ Generar recomendaciones
```
Click "Generar recomendaciones"
       ↓
Spinner: "Generando..."
       ↓
Backend intenta:
  - Mástil único alineado
  - Cable entre 2 mástiles existentes
       ↓
Solo retorna lo que FUNCIONA (verifica internamente)
```

### 4️⃣ Ver opciones
```
Panel de recomendaciones muestra:
  ┌─────────────────────────────┐
  │ 📌 Mástil único M3           │
  │ Alineado en Y con M0         │
  │ Ubicado a 3m del equipo      │
  │ Estado: ✓ Validado           │
  │ Cobertura: Sí (2/2 equipos)  │
  │ [Aplicar] [Descartar]        │
  └─────────────────────────────┘
  
  ┌─────────────────────────────┐
  │ 🔗 Cable M0 ← → M2           │
  │ Conecta los 2 más cercanos   │
  │ Orientación: paralelo a X    │
  │ Estado: ✓ Validado           │
  │ Longitud: 70.1m / 100m máx   │
  │ [Aplicar] [Descartar]        │
  └─────────────────────────────┘
```

### 5️⃣ Aplicar recomendación (futuro)
```
Click "Aplicar"
       ↓
[Pendiente de implementación completa]
Debería:
  1. Agregar mástil/cable a ApantState
  2. Recalcular modelo
  3. Actualizar visualización 3D
```

---

## Validación Garantizada

**Cada recomendación que se muestra ha sido probada internamente:**

```python
# En calculos_apant.py:
qv = _quick_verify(tp, mod)  # Evaluación interna

if not qv['validated']:
    continue  # No mostrar si falla

verif = qv['verification']
all_ok = all(v.get('fully_shielded', False) for v in verif)

if all_ok:
    # Solo retorna si GARANTIZA protección completa
    return recommendation
```

**Garantía:** El usuario NUNCA verá una recomendación que no haya sido verificada internamente.

---

## Casos de Uso

### ✅ Equipo 100% apantallado
- Tabla muestra: "Todos apantallados"
- Botón: **OCULTO**
- Panel: Vacío

### ✅ 1+ equipos sin apantallamiento
- Tabla muestra: "X de Y equipos sin protección"
- Botón: **VISIBLE**
- Click botón → genera opciones
- Panel: Muestra 1-2 recomendaciones validadas

### ✅ Sin equipos sin apantallar  (error)
- Toast: "No se pudieron generar recomendaciones"
- Panel: Se oculta automáticamente

### ✅ Error de conexión
- Toast: "Error: [mensaje]"
- Botón: Se rehabilita para reintentar

---

## Integración con Exportación PDF

El sistema ya incluye renderización de recomendaciones en PDF (línea 3054-3075 de index.html):

```javascript
const apRecs = _apantLastResult._recs || [];
if (apRecs.length > 0) {
  // Tabla con recomendaciones en el reporte
}
```

---

## Archivos Modificados

| Archivo | Cambios | Líneas |
|---------|---------|--------|
| `calculos_apant.py` | Refactor completo sistema | +300 |
| `index.html` | Botón + panel recomendaciones | +15 |
| `apantallamiento.js` | Funciones JS para recomendar | +140 |
| `servidor.py` | *(No cambios - endpoint ya existe)* | — |

---

## Testing Recomendado

```javascript
// Test 1: Ver botón cuando hay equipo sin apantallar
ApantState.cubes = [{name: 'Equipo1', x: 5, y: 5, z: 0, dx: 2, dy: 2, dz: 3}];
ApantState.masts = [{x: 0, y: 0, h: 15}];
// → Botón debe aparecer

// Test 2: Generar recomendación
await apantGenerarRecomendaciones();
// → Panel debe mostrar opciones

// Test 3: Aplicar recomendación
apantApplyRecommendation(0);
// → Debería agregar mástil/cable y recalcular
```

---

## Mejoras Futuras

1. **Aplicar recomendación automáticamente**
   - Agregar mástil/cable al modelo
   - Recalcular apantallamiento
   - Renderizar cambios

2. **Recomendaciones múltiples por equipom**
   - Si hay varios equipos sin apantallar
   - Una solución que apantalle todos

3. **Interfaz de detalles expandible**
   - Ver detalles del cálculo
   - Justificación de altura/ubicación
   - Análisis de sensibilidad

4. **Guardado de recomendaciones**
   - Historial de recomendaciones generadas
   - Comparar antes/después

---

**Fecha completado:** 2026-05-14  
**Estado:** Funcional y listo para testing  
**Siguiente paso:** Implementar "Aplicar recomendación"
