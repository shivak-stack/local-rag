import re
from functools import lru_cache
from pathlib import Path


HEALTHCARE_NOTICE = "This assistant is restricted to healthcare-related topics and healthcare documents."
DOCUMENT_NOTICE = "Only healthcare-related documents are supported."

HEALTHCARE_TERMS = {
    "health", "healthcare", "medical", "medicine", "medicines", "clinical", "patient", "patients",
    "disease", "diseases", "symptom", "symptoms", "diagnosis", "diagnostic", "treatment", "therapy",
    "drug", "drugs", "medication", "medications", "pharma", "pharmaceutical", "hospital", "clinic",
    "doctor", "nurse", "surgery", "surgical", "anatomy", "physiology", "pathology", "epidemiology",
    "public health", "imaging", "radiology", "cancer", "diabetes", "pneumonia", "asthma", "infection",
    "vaccine", "vaccination", "blood", "heart", "lung", "brain", "kidney", "liver", "mental health",
    "healthcare analytics", "healthcare ai", "patient record", "medical report", "clinical research",
    "wellness", "wellbeing", "health condition", "patient care", "care plan", "side effect",
    "side effects", "dose", "dosage", "blood pressure", "hypertension", "health policy",
    "medical history", "lab test", "laboratory test", "clinical trial", "health outcome",
}
NON_HEALTHCARE_TERMS = {
    "resume", "curriculum vitae", "software manual", "programming", "sorting algorithm", "finance report",
    "financial statement", "legal contract", "lease agreement", "cricket", "java programming", "source code",
    "python program", "python code", "write code", "sorting algorithm", "software development",
}

HEART_DATASET_FIELDS = {
    "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg", "thalach",
    "exang", "oldpeak", "slope", "ca", "thal",
}
HEART_DATASET_OUTCOMES = {"target", "output", "num", "heartdisease", "diagnosis"}
MODERN_HEART_DATASET_FIELDS = {
    "age", "sex", "chestpaintype", "restingbp", "cholesterol", "fastingbs",
    "restingecg", "maxhr", "exerciseangina", "oldpeak", "stslope", "heartdisease",
}
HEART_FAILURE_FIELDS = {
    "anaemia", "creatinine", "phosphokinase", "ejection", "fraction", "high", "blood",
    "pressure", "platelets", "serum", "sodium", "smoking", "time", "death", "event",
}
VERBOSE_HEART_FIELDS = {
    "chest pain", "resting bp", "resting blood pressure", "cholesterol",
    "fasting blood sugar", "resting ecg", "maximum heart rate", "max heart rate",
    "exercise induced angina", "exercise angina", "st depression", "thalassemia",
    "number of major vessels", "heart disease",
}


def _tokens(text):
    return set(re.findall(r"[a-z][a-z0-9-]*", (text or "").lower()))


def is_healthcare_query(text):
    normalized = (text or "").lower()
    tokens = _tokens(normalized)
    if any(term in normalized for term in NON_HEALTHCARE_TERMS):
        return False
    if re.search(r"\b(java|python|javascript|typescript|c\+\+|rust|golang)\b", normalized):
        return False
    return any(term in normalized for term in HEALTHCARE_TERMS) or bool(tokens & {"diagnose", "prescription", "prognosis", "pathogen", "anatomical", "physiological"})


def is_document_overview_query(text):
    normalized = (text or "").lower()
    return bool(re.search(
        r"\b(document|pdf|paper|report|file)\b|\b(summarize|summary|overview)\b",
        normalized,
    ))


def is_healthcare_followup(text, history):
    normalized = (text or "").lower()
    if any(term in normalized for term in NON_HEALTHCARE_TERMS) or re.search(r"\b(java|python|javascript|typescript|c\+\+|rust|golang|cricket)\b", normalized):
        return False
    refers_back = bool(re.search(r"\b(it|its|they|them|their|this|that|these|those|more|further|elaborate|continue)\b", normalized))
    has_healthcare_history = any(
        is_healthcare_query(item["content"])
        for item in history[-6:]
        if item.get("role") == "user"
    )
    return refers_back and has_healthcare_history


def is_healthcare_document(pages, filename=None):
    text = " ".join(page.get("text", "") for page in pages)
    if not text.strip():
        return False

    file_stem = Path(filename).stem.lower() if filename else ""
    normalized_name = re.sub(r"[_-]+", " ", file_stem)
    normalized = text.lower()
    if any(term in normalized for term in NON_HEALTHCARE_TERMS):
        return False
    if filename:
        if any(term in normalized_name for term in NON_HEALTHCARE_TERMS):
            return False

    # Kaggle heart-disease CSV/XLSX files often contain abbreviated column names
    # instead of prose medical terms (for example cp, trestbps, chol, thalach).
    schema_text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text).lower()
    schema_text = re.sub(r"[_-]+", " ", schema_text)
    schema_tokens = _tokens(schema_text)
    # Also compare compact header forms. Kaggle's common UCI version uses
    # camel-case names such as ChestPainType and RestingBP.
    compact_tokens = {
        re.sub(r"[^a-z0-9]", "", token.lower())
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_]*", text)
    }
    heart_named = bool(re.search(r"\b(heart|cardio|cardiac|cardiovascular)\b", normalized_name))
    outcome_present = (
        bool(schema_tokens & HEART_DATASET_OUTCOMES)
        or bool(compact_tokens & HEART_DATASET_OUTCOMES)
        or "heart disease" in schema_text
    )
    abbreviated_field_count = len(schema_tokens & HEART_DATASET_FIELDS)
    modern_field_count = len(compact_tokens & MODERN_HEART_DATASET_FIELDS)
    heart_failure_field_count = len(schema_tokens & HEART_FAILURE_FIELDS)
    verbose_field_count = sum(field in schema_text for field in VERBOSE_HEART_FIELDS)
    if (
        # Kaggle's "heart-selected-columns" export may intentionally omit its
        # target column; the filename plus several known clinical fields still
        # identify it as a heart dataset.
        (heart_named and abbreviated_field_count >= 8)
        or (
            outcome_present
            and (
                (heart_named and abbreviated_field_count >= 5)
                or modern_field_count >= 8
                or (heart_named and heart_failure_field_count >= 8 and "death event" in schema_text)
                or (verbose_field_count >= 5 and (heart_named or "heart disease" in schema_text))
            )
        )
    ):
        return True

    # Score distinct medical terms across the extracted PDF and require multiple signals.
    hits = sum(1 for term in HEALTHCARE_TERMS if term in normalized)
    return hits >= 3


@lru_cache(maxsize=128)
def _is_healthcare_pdf_cached(path, modified_ns, size):
    # Import here to avoid coupling PDF extraction to the guard module at import time.
    from backend.document_processor import extract_pdf_text

    try:
        return is_healthcare_document(extract_pdf_text(path), Path(path).name)
    except Exception:
        return False


@lru_cache(maxsize=256)
def _is_healthcare_file_cached(path, modified_ns, size):
    from backend.document_processor import extract_document_text

    try:
        return is_healthcare_document(extract_document_text(path), Path(path).name)
    except Exception:
        return False


def is_healthcare_file(filename):
    from backend.document_processor import SUPPORTED_EXTENSIONS

    name = Path(filename or "").name
    if not name or name != filename or Path(name).suffix.lower() not in SUPPORTED_EXTENSIONS:
        return False

    path = Path("backend/uploads") / name
    try:
        stat = path.stat()
    except OSError:
        return False

    return _is_healthcare_file_cached(
        str(path.resolve()),
        stat.st_mtime_ns,
        stat.st_size,
    )


def is_healthcare_pdf(filename):
    """Backward-compatible alias for older PDF-only callers."""
    return is_healthcare_file(filename)
