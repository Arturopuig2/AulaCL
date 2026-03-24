---
description: Genera y ejecuta pruebas unitarias con Jest para validar la lógica principal del proyecto (funciones y reglas de negocio), informando errores y proponiendo soluciones cuando alguna prueba falla.
---

Content_Workflow: Generar todas las pruebas unitarias básicas para la lógica del proyecto.
Pasos:
1. Analizar el proyecto en busca de funciones lógicas relevantes (p. ej., createItem, updateItem, deleteItem, processX, validateY) y módulos con reglas de negocio.
2. Para cada función/módulo identificado, definir casos de prueba mínimos (casos “happy path”, límites y errores esperados) y generar sus pruebas unitarias con Jest.
3. Crear un archivo de test por función o módulo, siguiendo una convención genérica de nombres (p. ej., tests/<modulo>.<funcion>.test.js o __tests__/<modulo>.test.js).
4. Ejecutar el conjunto de pruebas y reportar resultados (tests pasados/fallidos, mensajes de error relevantes y el contexto del fallo).
5. Si alguna prueba falla, diagnosticar la causa probable y proponer soluciones (cambios en la implementación, ajuste del test, corrección de mocks/fixtures o manejo de edge cases), indicando los siguientes pasos para validar el arreglo.