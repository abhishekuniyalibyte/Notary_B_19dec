def map_acta_to_engine_input(acta_json: dict) -> dict:
    """
    Converts extracted Acta JSON into the input format
    expected by decision_engine.py
    """

    # 1. Certificate type (LEGAL choice)
    certificate_type = "certificado_hechos"

    # 2. Facts (presence-based, NOT validity)
    facts = {
        "objeto_del_certificado": True,
        "documento_fuente": True,
        "exhibicion_o_compulsa": True,

        "conocimiento_personal_del_escribano": False,

        "documentacion_verificada_por_escribano": True,

        "existencia_persona_juridica": bool(acta_json.get("denominacion")),

        "designacion_autoridades": bool(
            acta_json.get("other_fields", {}).get("presidente_asamblea")
        ),

        "cargo_vigente": bool(
            acta_json.get("other_fields", {}).get("presidente_asamblea")
        ),

        "cumplimiento_ley_18930": "18930" in str(
            acta_json.get("other_fields", {}).get("modificacion_legal", "")
        ),

        "cumplimiento_ley_17904": False,

        "beneficiario_final_declarado": False
    }

    # 3. Conditions
    conditions = {
        "otorgante_no_sabe_o_no_puede_firmar": False
    }

    # 4. Global fields (Art. 255)
    global_fields = {
        "nombre_solicitante": True,
        "destinatario": True,
        "lugar_expedicion": True,
        "fecha_expedicion": True,
        "firma_y_sello_escribano": True,
        "constancia_cumplimiento_legal": True
    }

    return {
        "certificate_type": certificate_type,
        "facts": facts,
        "conditions": conditions,
        "global_fields": global_fields
    }
