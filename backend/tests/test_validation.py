"""Tests for validation and abnormality classification"""
import pytest
from app.services.validation.service import ValidationService, ReferenceRangeDB
from app.schemas.report import TestResultStatus


def test_classify_numeric_normal():
    service = ValidationService()
    assert service._classify_numeric(14.0, 13.5, 17.5, "hemoglobin") == TestResultStatus.NORMAL.value


def test_classify_numeric_low():
    service = ValidationService()
    assert service._classify_numeric(10.0, 13.5, 17.5, "hemoglobin") == TestResultStatus.LOW.value


def test_classify_numeric_high():
    service = ValidationService()
    assert service._classify_numeric(20.0, 13.5, 17.5, "hemoglobin") == TestResultStatus.HIGH.value


def test_classify_numeric_critical():
    service = ValidationService()
    assert service._classify_numeric(6.0, 13.5, 17.5, "hemoglobin") == TestResultStatus.CRITICALLY_LOW.value


def test_reference_range_db():
    low, high, text = ReferenceRangeDB.get_range("hemoglobin", "male")
    assert low == 13.5
    assert high == 17.5
