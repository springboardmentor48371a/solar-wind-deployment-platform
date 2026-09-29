import pytest
from app.services.report_service import report_service


def test_pdf_report_generation():
    data = {
        "site_name": "Test Site Alpha",
        "technology": "Solar",
        "overall_score": 88.5,
        "category": "Highly Suitable",
        "resource_score": 89.0,
        "geographic_score": 92.0,
        "infrastructure_score": 85.0,
        "environmental_score": 87.0,
        "economic_score": 86.0,
        "expected_mwh_year": 85000.0,
        "capex_usd": 42500000.0,
        "npv_usd": 22000000.0,
        "irr_pct": 11.5,
        "payback_years": 6.8,
        "recommendation": "Highly Recommended"
    }
    pdf_bytes = report_service.generate_pdf_report("Site_Assessment", data)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")


def test_excel_report_generation():
    data = {
        "site_name": "Test Site Alpha",
        "technology": "Solar",
        "overall_score": 88.5,
        "category": "Highly Suitable",
        "resource_score": 89.0,
        "geographic_score": 92.0,
        "infrastructure_score": 85.0,
        "environmental_score": 87.0,
        "economic_score": 86.0,
        "expected_mwh_year": 85000.0,
        "capex_usd": 42500000.0,
        "annual_revenue_usd": 6375000.0,
        "opex_per_year_usd": 637500.0
    }
    excel_bytes = report_service.generate_excel_report("Site_Assessment", data)
    assert len(excel_bytes) > 2000
    # ZIP/Office open XML signature
    assert excel_bytes.startswith(b"PK")
