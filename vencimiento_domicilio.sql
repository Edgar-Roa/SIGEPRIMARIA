-- Actualizar función de documentos faltantes para respetar los 3 meses
CREATE OR REPLACE FUNCTION obtener_documentos_faltantes(p_alumno_id INTEGER)
RETURNS TABLE(
    tipo_doc_id INTEGER, 
    codigo VARCHAR, 
    nombre VARCHAR,
    descripcion TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        td.tipo_doc_id, 
        td.codigo, 
        td.nombre,
        td.descripcion
    FROM tipos_documento td
    WHERE td.requerido = TRUE
      AND td.activo = TRUE
      AND NOT EXISTS (
          SELECT 1 
          FROM documento_alumno da 
          WHERE da.alumno_id = p_alumno_id
            AND da.tipo_doc_id = td.tipo_doc_id
            -- EL CAMBIO CLAVE:
            AND (td.codigo != 'comprobante_dom' OR da.fecha_subida >= (CURRENT_DATE - INTERVAL '3 months'))
      )
    ORDER BY td.nombre;
END;
$$ LANGUAGE plpgsql;