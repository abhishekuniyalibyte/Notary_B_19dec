from __future__ import annotations
 
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
 
 
@dataclass
class Finding:
    kind: str  # "missing" | "expired"
    rule_id: str
    description_es: str
    article: Optional[int]
    literal: Optional[str]
    cross_ref_article: Optional[int]
    message_es: str
 
 
 
# JSON loading
def load_legal_rules(json_path: str | Path) -> Dict[str, Any]:
    """
    Loads the Spanish legal rule model (legal_rules.json).
 
    Args:
        json_path: Path to the JSON rules file.
 
    Returns:
        Parsed JSON as a Python dict.
    """
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"Legal rules file not found: {path.resolve()}")
 
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
 
# Value normalization helpers
def _is_present(value: Any) -> bool:
    """
    Normalize "presence" checks.
 
    Accepts:
      - bool (True/False)
      - dict with {"presente": True/False}
      - dict with {"present": True/False} (fallback)
    """
    if isinstance(value, bool):
        return value
 
    if isinstance(value, dict):
        if "presente" in value:
            return bool(value["presente"])
        if "present" in value:
            return bool(value["present"])
 
    # If caller sends None or missing, this becomes False for mandatory checks
    return bool(value)
 
 
def _is_expired(value: Any) -> Optional[bool]:
    """
    Extract expiration state (if provided).
 
    Accepts:
      - dict with {"vencido": True/False}
      - dict with {"expired": True/False} (fallback)
 
    Returns:
      True/False if provided, else None.
    """
    if isinstance(value, dict):
        if "vencido" in value:
            return bool(value["vencido"])
        if "expired" in value:
            return bool(value["expired"])
    return None
 
# Legal source extraction
def _legal_source(rule: Dict[str, Any]) -> Tuple[Optional[int], Optional[str], Optional[int]]:
    """
    Returns:
      (article, literal, cross_reference_article)
    """
    source = rule.get("fuente_legal") or {}
    article = source.get("articulo")
    literal = source.get("literal")
 
    cross_ref = source.get("referencia_cruzada") or {}
    cross_ref_article = cross_ref.get("articulo")
 
    return article, literal, cross_ref_article
 
 
def _format_basis(article: Optional[int], literal: Optional[str]) -> Optional[str]:
    if article is None:
        return None
    if literal:
        return f"Art. {article} lit. {literal}"
    return f"Art. {article}"
 
 
 
# Message builders (Spanish, safe, deterministic)
def _missing_message_es(description_es: str,
                        article: Optional[int],
                        literal: Optional[str],
                        cross_ref_article: Optional[int]) -> str:
    if article is None:
        return f"Falta '{description_es}'."
 
    basis = _format_basis(article, literal) or f"Art. {article}"
    if cross_ref_article:
        return f"Falta '{description_es}', exigido por {basis} en relación con Art. {cross_ref_article}."
    return f"Falta '{description_es}', exigido por {basis}."
 
 
def _expired_message_es(description_es: str,
                        article: Optional[int],
                        literal: Optional[str],
                        cross_ref_article: Optional[int]) -> str:
    if article is None:
        return f"'{description_es}' se encuentra vencido."
 
    basis = _format_basis(article, literal) or f"Art. {article}"
    if cross_ref_article:
        return f"'{description_es}' se encuentra vencido, incumpliendo {basis} en relación con Art. {cross_ref_article}."
    return f"'{description_es}' se encuentra vencido, incumpliendo {basis}."
 
 
 
# Public API: evaluate certificate
def evaluate_certificate(
    legal_rules: Dict[str, Any],
    certificate_type: str,
    facts: Dict[str, Any],
    conditions: Optional[Dict[str, Any]] = None,
    global_fields: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Deterministically evaluates legality for a certificate instance.
 
    Args:
        legal_rules: Loaded dict from legal_rules.json
        certificate_type: e.g. "certificado_firmas"
        facts: Fact map keyed by Spanish legal requirement IDs (from JSON)
        conditions: Conditional flags keyed by Spanish condition IDs
        global_fields: Presence map for "requisitos_globales_certificado.campos"
 
    Returns:
        {
          "status": "VALID" | "INVALID",
          "errors": [...],
          "warnings": [...],
          "legal_basis": ["Art. ...", ...]
        }
    """
    if conditions is None:
        conditions = {}
    if global_fields is None:
        global_fields = {}
 
    if certificate_type not in legal_rules:
        available = [k for k in legal_rules.keys() if k != "requisitos_globales_certificado"]
        raise KeyError(
            f"certificate_type '{certificate_type}' not found in legal_rules. "
            f"Available: {', '.join(sorted(available))}"
        )
 
    cfg = legal_rules[certificate_type]
    requirements = cfg.get("requisitos", [])
    conditional_blocks = cfg.get("requisitos_condicionales", [])
 
    findings: List[Finding] = []
    legal_basis: List[str] = []
 
    # 1) Base legal for the certificate type itself (Art. 248 literal ...)
    base_legal = cfg.get("base_legal") or {}
    base_article = base_legal.get("articulo_principal")
    base_literal = base_legal.get("literal")
    base_str = _format_basis(base_article, base_literal)
    if base_str:
        legal_basis.append(base_str)
 
    # 2) Evaluate normal requirements
    for req in requirements:
        req_id = req.get("id")
        description_es = req.get("descripcion", req_id)
        mandatory = bool(req.get("obligatorio", False))
        can_expire = bool(req.get("puede_vencer", False))
 
        article, literal, cross_ref_article = _legal_source(req)
        basis_str = _format_basis(article, literal)
        if basis_str:
            legal_basis.append(basis_str)
 
        value = facts.get(req_id)
 
        if mandatory and not _is_present(value):
            findings.append(
                Finding(
                    kind="missing",
                    rule_id=req_id,
                    description_es=description_es,
                    article=article,
                    literal=literal,
                    cross_ref_article=cross_ref_article,
                    message_es=_missing_message_es(description_es, article, literal, cross_ref_article),
                )
            )
            continue
 
        if can_expire and value is not None:
            expired = _is_expired(value)
            if expired is True:
                findings.append(
                    Finding(
                        kind="expired",
                        rule_id=req_id,
                        description_es=description_es,
                        article=article,
                        literal=literal,
                        cross_ref_article=cross_ref_article,
                        message_es=_expired_message_es(description_es, article, literal, cross_ref_article),
                    )
                )
 
    # 3) Evaluate conditional requirements
    for block in conditional_blocks:
        condition_id = block.get("condicion")
        if not condition_id:
            continue
 
        if not bool(conditions.get(condition_id, False)):
            continue  # condition not active → skip
 
        for req in block.get("requisitos", []):
            req_id = req.get("id")
            description_es = req.get("descripcion", req_id)
            mandatory = bool(req.get("obligatorio", False))
            can_expire = bool(req.get("puede_vencer", False))
 
            article, literal, cross_ref_article = _legal_source(req)
            basis_str = _format_basis(article, literal)
            if basis_str:
                legal_basis.append(basis_str)
 
            value = facts.get(req_id)
 
            if mandatory and not _is_present(value):
                findings.append(
                    Finding(
                        kind="missing",
                        rule_id=req_id,
                        description_es=description_es,
                        article=article,
                        literal=literal,
                        cross_ref_article=cross_ref_article,
                        message_es=_missing_message_es(description_es, article, literal, cross_ref_article),
                    )
                )
                continue
 
            if can_expire and value is not None:
                expired = _is_expired(value)
                if expired is True:
                    findings.append(
                        Finding(
                            kind="expired",
                            rule_id=req_id,
                            description_es=description_es,
                            article=article,
                            literal=literal,
                            cross_ref_article=cross_ref_article,
                            message_es=_expired_message_es(description_es, article, literal, cross_ref_article),
                        )
                    )
 
    # 4) Evaluate global certificate requirements (Art. 255)
    global_cfg = legal_rules.get("requisitos_globales_certificado") or {}
    global_base = global_cfg.get("base_legal") or {}
    global_article = global_base.get("articulo")
    if global_article:
        legal_basis.append(f"Art. {global_article}")
 
    for field in global_cfg.get("campos", []):
        field_id = field.get("id")
        field_desc = field.get("descripcion", field_id)
 
        # Global fields are mandatory by definition (Art. 255: "todo certificado contendrá")
        if not _is_present(global_fields.get(field_id)):
            findings.append(
                Finding(
                    kind="missing",
                    rule_id=field_id,
                    description_es=field_desc,
                    article=255,
                    literal=None,
                    cross_ref_article=None,
                    message_es=f"Falta '{field_desc}', exigido por Art. 255.",
                )
            )
 
    # Deduplicate legal_basis while keeping order
    deduped_basis: List[str] = []
    seen = set()
    for b in legal_basis:
        if b and b not in seen:
            deduped_basis.append(b)
            seen.add(b)
 
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
 
    for f in findings:
        errors.append(
            {
                "kind": f.kind,
                "id": f.rule_id,
                "description_es": f.description_es,
                "article": f.article,
                "literal": f.literal,
                "cross_reference_article": f.cross_ref_article,
                "message_es": f.message_es,
            }
        )
 
    status = "INVALID" if errors else "VALID"
 
    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "legal_basis": deduped_basis,
    }
 
def main() -> None:
   
    rules = load_legal_rules(Path(__file__).resolve().parents[0] / "legal" / "legal_rules.json")
 
    # demo_input = {
    # "certificate_type": "certificado_firmas",
 
    # "facts": {
    #     "firma_en_presencia": True,
    #     "lectura_del_documento": True,
    #     "ratificacion_contenido_y_firma": True,
 
    #     "individualizacion_otorgantes": True,
 
    #     "identificacion_otorgantes": {
    #     "presente": True,
    #     "vencido": False
    #     },
 
    #     "requerimiento_expreso": True,
 
    #     "documento_fuente": True,
    #     "exhibicion_o_compulsa": True,
 
    #     "persona_juridica_vigente": True,
 
    #     "representacion_acreditada": True,
    #     "cargo_vigente": True,
 
    #     "cumplimiento_ley_17904": True,
    #     "cumplimiento_ley_18930": True,
    #     "cumplimiento_ley_19484": True,
 
    #     "documentacion_verificada": True
    # },
 
    # "conditions": {
    #     "otorgante_no_sabe_o_no_puede_firmar": False
    # },
 
    # "global_fields": {
    #     "nombre_solicitante": True,
    #     "destinatario": True,
    #     "lugar_expedicion": True,
    #     "fecha_expedicion": True,
    #     "firma_y_sello_escribano": True,
    #     "constancia_cumplimiento_legal": True
    # }
    # }
    demo_input = {
        "certificate_type": "certificado_firmas",
 
        "facts": {
            "individualizacion_otorgantes": True,
            "identificacion_otorgantes": True,
 
            "firma_en_presencia": True,
            "lectura_del_documento": True,
 
            "existencia_persona_juridica": True,
            "estatuto_vigente": True,
 
            "designacion_autoridades": True,
            "cargo_vigente": True,
            "facultades_representacion_validas": True,
 
            "cumplimiento_ley_17904": True,
            "cumplimiento_ley_18930": True,
            "beneficiario_final_declarado": True,
 
            "requerimiento_expreso": True,
            "documentacion_verificada_por_escribano": True
        },
 
        "conditions": {
            "otorgante_no_sabe_o_no_puede_firmar": False
        },
 
        "global_fields": {
            "nombre_solicitante": True,
            "destinatario": True,
            "lugar_expedicion": True,
            "fecha_expedicion": True,
            "firma_y_sello_escribano": True,
            "constancia_cumplimiento_legal": True
        }
    }
 
 
 
    result = evaluate_certificate(
        legal_rules=rules,
        certificate_type=demo_input["certificate_type"],
        facts=demo_input["facts"],
        conditions=demo_input["conditions"],
        global_fields=demo_input["global_fields"],
    )
 
    print(json.dumps(result, ensure_ascii=False, indent=2))
 
 
if __name__ == "__main__":
    main()
 