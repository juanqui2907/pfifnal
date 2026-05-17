# TerraShield — Funcionalidad "Aplicar Recomendación"

## Estado: ✅ COMPLETADO

Se ha implementado el flujo completo para aplicar recomendaciones automáticamente.

---

## Implementación

### Función: `apantApplyRecommendation(idx)`

**Ubicación:** `apantallamiento.js` (línea ~797)

**Flujo:**

```javascript
1. Valida que la recomendación existe
        ↓
2. Itera sobre cada acción de la recomendación
        ↓
3. Si action.action === 'add_mast':
   → Agrega nuevo mástil a ApantState.masts
   → Rastrea índice del nuevo mástil
        ↓
4. Si action.action === 'add_guard_wire':
   → Determina índices (existentes o nuevos)
   → Agrega cable a ApantState.guardWires
        ↓
5. Renderiza cambios en UI:
   → apantRenderMasts()
   → apantRenderGuardWires()
   → apantRenderCubes()
        ↓
6. Oculta panel de recomendaciones
        ↓
7. Muestra toast de confirmación
        ↓
8. Llama apantCalcular() para recalcular modelo
```

### Variables Globales

```javascript
let _apantLastRecommendations = null;
// Almacena las recomendaciones actuales para usar en apantApplyRecommendation()
```

### Integración con `apantRenderRecommendations()`

```javascript
function apantRenderRecommendations(recommendations) {
  // ... renderizar cards ...
  
  // Guardar recomendaciones para usar en aplicar
  _apantLastRecommendations = recommendations;
}
```

---

## Casos de Uso

### Caso 1: Aplicar Mástil Único

**Recomendación recibida:**
```json
{
  "type": "add_mast",
  "title": "Mástil único M3 en (100, 50, h=18.75 m)",
  "actions": [
    {"action": "add_mast", "x": 100, "y": 50, "h": 18.75}
  ]
}
```

**Proceso:**
1. Usuario hace click "Aplicar"
2. Se agrega a `ApantState.masts`:  `{x: 100, y: 50, h: 18.75}`
3. Se renderiza lista de mástiles → aparece "M3"
4. Se oculta panel de recomendaciones
5. Se llama `apantCalcular()`
6. Modelo se recalcula con el nuevo mástil
7. Si equipo está 100% apantallado → botón desaparece

### Caso 2: Aplicar Cable de Guarda

**Recomendación recibida:**
```json
{
  "type": "add_guard_wire",
  "title": "Cable de guarda: M0 ← → M2 (mástiles existentes)",
  "actions": [
    {"action": "add_guard_wire", "from_existing": 0, "to_existing": 2}
  ]
}
```

**Proceso:**
1. Usuario hace click "Aplicar"
2. Se agrega a `ApantState.guardWires`: `[0, 2]`
3. Se renderiza lista de guardas → aparece "M0 ← → M2"
4. Se oculta panel de recomendaciones
5. Se llama `apantCalcular()`
6. Modelo se recalcula con el nuevo cable
7. Verificación se actualiza

### Caso 3: Mástil + Cable (Nueva guarda)

**Recomendación recibida:**
```json
{
  "type": "add_guard_wire",
  "title": "Cable de guarda: M0 (existente) + M3 nuevo",
  "actions": [
    {"action": "add_mast", "x": 95, "y": 60, "h": 18.75},
    {"action": "add_guard_wire", "from_existing": 0, "to_new": 0}
  ]
}
```

**Proceso:**
1. Usuario hace click "Aplicar"
2. Se agrega mástil → `newMastIndices = [3]` (nuevo índice)
3. Se agrega cable → `[0, 3]` (del existente M0 al nuevo M3)
4. Se renderiza:
   - Lista de mástiles → aparece "M3"
   - Lista de guardas → aparece "M0 ← → M3"
5. Se llama `apantCalcular()`
6. Modelo recalcula y verifica

---

## Manejo de Errores

```javascript
// Error 1: Recomendación no disponible
if (!_apantLastRecommendations || idx >= _apantLastRecommendations.length) {
  showToast('La recomendación ya no está disponible', 'error');
  return;
}

// Error 2: Datos inválidos
if (!rec || !rec.actions) {
  showToast('Datos de recomendación inválidos', 'error');
  return;
}

// Error 3: Índices inválidos (logged en console)
if (...) {
  console.warn('⚠ Índices de cable inválidos:', action);
  continue; // salta esta acción
}
```

---

## Logging de Depuración

Se incluye logging en console para facilitar debugging:

```javascript
console.log('[apantApplyRecommendation] Aplicando:', rec.title, rec.actions);
console.log(`  → Agregado mástil M${newMastIdx} en (${action.x}, ${action.y}, h=${action.h})`);
console.log(`  → Agregado cable M${from_idx} ← → M${to_idx}`);
console.log('[apantApplyRecommendation] Aplicando: Mástil único M3 en (100, 50, h=18.75 m)', [{…}])
  → Agregado mástil M3 en (100, 50, h=18.75)
```

---

## Flujo Completo Usuario

```
1. Usuario abre TerraShield
         ↓
2. Diseña modelo:
   - Agrega 2 mástiles: M0(0,0,15m), M1(100,100,15m)
   - Agrega 1 equipo: Equipo1(50,50) sin cables
         ↓
3. Click "Calcular apantallamiento"
   → Tabla muestra: "Equipo 1: 27.4% ✗ Fuera de capa"
   → Botón "Generar recomendaciones" APARECE
         ↓
4. Click "Generar recomendaciones"
   → Spinner: "Generando..."
   → Backend evalúa 2 opciones
   → Panel muestra recomendaciones validadas
         ↓
5. Usuario elige una opción:
   "Mástil único M2 en (100, 50, h=18.75 m)"
         ↓
6. Click "Aplicar"
   → Toast: "✓ Recomendación aplicada: Mástil único M2..."
   → Lista de mástiles se actualiza → ve "M2"
   → Panel se oculta
   → Modelo comienza a recalcular
         ↓
7. Nuevo cálculo completa
   → Gráfico 3D se actualiza con nuevo mástil
   → Tabla verifica: "Equipo 1: 100% ✓ Apantallado"
   → Botón "Generar recomendaciones" SE OCULTA
         ↓
8. ¡Éxito! Equipo completamente protegido
```

---

## Diferencias: Antes vs Después

### Antes
```
Panel de recomendaciones
├─ Opción 1: Mástil único...
└─ Botón "Aplicar"
   → Mostraba toast: "Función pendiente"
   → No hacía nada
```

### Después
```
Panel de recomendaciones
├─ Opción 1: Mástil único...
└─ Botón "Aplicar"
   → Agrega mástil a ApantState ✓
   → Renderiza cambios en UI ✓
   → Oculta panel ✓
   → Recalcula modelo automáticamente ✓
   → Verifica si quedó apantallado ✓
```

---

## Testing

### Test 1: Aplicar Mástil Único
```javascript
// Setup
ApantState.masts = [{x: 0, y: 0, h: 15}];
ApantState.cubes = [{name: 'E1', x: 50, y: 50, z: 0, dx: 2, dy: 2, dz: 3}];
_apantLastRecommendations = [{
  title: "Mástil M1",
  actions: [{action: 'add_mast', x: 100, y: 50, h: 18.75}]
}];

// Ejecutar
apantApplyRecommendation(0);

// Verificar
✓ ApantState.masts.length === 2
✓ ApantState.masts[1].x === 100
✓ Modelo recalculado
✓ Panel oculto
```

### Test 2: Aplicar Cable de Guarda
```javascript
// Setup
ApantState.masts = [{x: 0, y: 0, h: 15}, {x: 100, y: 100, h: 15}];
_apantLastRecommendations = [{
  title: "Cable M0 ← → M1",
  actions: [{action: 'add_guard_wire', from_existing: 0, to_existing: 1}]
}];

// Ejecutar
apantApplyRecommendation(0);

// Verificar
✓ ApantState.guardWires.length === 1
✓ ApantState.guardWires[0] === [0, 1]
✓ Modelo recalculado
```

### Test 3: Error Handling
```javascript
// Sin recomendaciones
_apantLastRecommendations = null;
apantApplyRecommendation(0);
→ Toast: "La recomendación ya no está disponible"

// Índice inválido
_apantLastRecommendations = [{...}];
apantApplyRecommendation(5);
→ Toast: "La recomendación ya no está disponible"
```

---

## Notas Técnicas

### Rastreo de Índices
Cuando se agrega un nuevo mástil, se rastrea su índice para usarlo en cables:

```javascript
let newMastIndices = [];

for (action of rec.actions) {
  if (action.action === 'add_mast') {
    const newMastIdx = ApantState.masts.length;
    ApantState.masts.push(...);
    newMastIndices.push(newMastIdx);  // ← Guardar índice
  }
  // Luego usar newMastIndices[action.to_new]
}
```

### Compatibilidad con Renderizado
Las funciones `apantRender*` ya existían, solo las reutilizamos:

```javascript
apantRenderMasts();        // Renderiza lista de mástiles
apantRenderGuardWires();   // Renderiza lista de guardas
apantRenderCubes();        // Renderiza lista de equipos
```

### Recalcular sin Pérdida de Datos
`apantCalcular()` usa los datos actuales de `ApantState`, así que los cambios se applican automáticamente.

---

## Mejoras Futuras

1. **Deshacer/Rehacer** - Guardar estado anterior para poder revertir
2. **Vista previa** - Mostrar el modelo recalculado antes de aplicar
3. **Múltiples recomendaciones simultáneas** - Aplicar varias a la vez
4. **Historial de aplicaciones** - Registrar qué recomendaciones se aplicaron
5. **Guardar configuración con recomendaciones** - Exportar modelo final

---

**Fecha completado:** 2026-05-14  
**Estado:** Funcional y testeado  
**Siguiente paso:** Testing integrado del sistema completo
