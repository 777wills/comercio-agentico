"""N2: agente navegador en LangGraph (D12).

- ``fuentes``: registro de proveedores que el operador autoriza (plano de control).
- ``lectura``: trae el texto de cada fuente (crawl4ai, pypdf, FastMCP); sin LLM.
- ``extraccion``: convierte un fragmento de un tercero en ``[Oferta]`` con ``Procedencia``.
- ``interpretacion``: formaliza la consulta del comprador en una ``Necesidad``.
- ``grafo``: interpretar → planificar ⇄ herramientas → emparejar → proponer.
"""
