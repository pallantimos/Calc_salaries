import json
from argparse import ArgumentParser

import pytest

from src.main import create_arg_parser, PayoutReportHandler, ReportType, JSONReportSerializer


@pytest.fixture()
def data_file(request):
    return ["tests/data1.csv", "tests/data2.csv", "tests/data3.csv"]


@pytest.fixture
def parser() -> ArgumentParser:
    """Фикстура для создания парсера перед каждым тестом"""
    return create_arg_parser()


def test_valid_arguments(parser):
    """Тест корректных аргументов"""
    args = parser.parse_args([
        "file1.csv",
        "--report", "payout",
        "--outgoing_format", "json"
    ])

    assert args.files == ["file1.csv"]
    assert args.report == "payout"
    assert args.outgoing_format == "json"


def test_real_data_processing(data_file):
    """Тест создания отчета"""
    handler = PayoutReportHandler(file_names=data_file)
    report = handler.generate_report()

    assert isinstance(report, dict)
    assert len(report) > 0

    for department in report.values():
        assert "total_payout" in department
        assert "total_hours" in department


def test_serialize_to_file_success():
    """Тест успешной записи в JSON-файл"""
    test_data = {"department": "IT", "total": 5000}
    output_file = "test_report.json"
    serializer = JSONReportSerializer()

    serializer.serialize_to_file(test_data, str(output_file))

    with open(output_file) as f:
        content = json.load(f)
        assert content == test_data


def test_data_consistency(data_file):
    """Тест успешной записи в JSON-файл"""
    handler = PayoutReportHandler(file_names=data_file)
    report = handler.generate_report()

    for dept, data in report.items():
        if dept.startswith("total"):
            continue

        total_payout = 0
        total_hours = 0

        for emp, emp_data in data.items():
            if emp.startswith("total"):
                continue

            hours = int(emp_data["hours"])
            rate = int(emp_data["rate"])
            payout = int(emp_data["payout"])

            assert hours * rate == payout
            total_payout += payout
            total_hours += hours

        assert total_payout == int(data["total_payout"])
        assert total_hours == int(data["total_hours"])
