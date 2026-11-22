<h1 align="center">resume-from-projects (Español)</h1>

<p align="center">
  <em>Habilidad de agente para desarrolladores y freelancers: convierte tu carpeta de proyectos en un currículum verificado de una sola página en Word (.docx) y PDF.</em>
</p>

## Filosofía y Problema

Tienes el trabajo hecho. El currículum es la parte que siempre se pospone. Tus proyectos están dispersos en carpetas; algunos son tutoriales o bifurcaciones (forks), y otros son sistemas reales que construiste y desplegaste tú mismo.

Si le pides a una IA ordinaria que cree tu currículum, pone todo al mismo nivel: tutoriales, repositorios clonados donde cambiaste una línea, y proyectos de producción, vistiendo todo con métricas inventadas que nadie puede comprobar.

**`resume-from-projects` verifica primero:**
Inspecciona el historial de Git, comprueba la autoría, te muestra la lista de proyectos con evidencia real y no escribe ninguna afirmación que el código no respalde.

## Reglas Inquebrantables

1. **Acceso de solo lectura:** Nunca escribe, modifica ni ejecuta compilaciones dentro de tus directorios de proyectos. Los archivos de trabajo se generan en un directorio temporal.
2. **Cero alucinación:** No inventa empleadores, fechas, métricas, porcentajes ni números de usuarios. Cada dato debe provenir del código, README, configuración o historial de Git.
3. **Privacidad total:** El código fuente nunca sale de tu equipo local.
4. **Datos, no comandos:** Los READMEs o comentarios en tus proyectos se leen como datos, nunca como instrucciones ejecutables.
5. **Exactamente una página:** El documento final se ciñe a una sola página (.docx y .pdf) sin desbordamientos de texto.

## Proceso de 6 Pasos

1. **Verificar entorno:** Comprueba Python 3.8+ y LibreOffice.
2. **Preguntas iniciales:** Recoge la ruta de tus proyectos, el puesto deseado y datos de contacto opcionales.
3. **Escanear y verificar:** Filtra tutoriales, cursos y forks ajenos.
4. **Clasificar y priorizar:** Evalúa profundidad técnica, pruebas, CI y ajuste al rol.
5. **Redactar con evidencia:** Redacta viñetas claras con trazabilidad a archivos de código.
6. **Compilar y validar:** Construye el archivo .docx y lo convierte a PDF asegurando que quepa en una sola hoja.

## Instalación Rápida

```bash
git clone https://github.com/hasanify/resume-from-projects.git
mkdir -p .agents/skills
cp -r resume-from-projects/skills/resume-from-projects .agents/skills/
```

Pregunta a tu asistente:

> "Crea un currículum de una página a partir de mis proyectos en ~/code. 5 proyectos, para puestos de ingeniería backend."

## Licencia

[MIT](LICENSE).
