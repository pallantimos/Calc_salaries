import argparse
import json
import re
from argparse import ArgumentParser
from contextlib import ExitStack
from enum import StrEnum


class ReportType(StrEnum):
    PAYOUT = 'payout'


class OutgoingFormatType(StrEnum):
    JSON = 'json'


def create_arg_parser() -> ArgumentParser:
    """
        Парсит аргументы терминала.
        Аргумент files - путь до файлов.
        Аргумент --report - вид отчета.
        Аргумент --outgoing_format - формат итогового файла.
    """
    parser = argparse.ArgumentParser(description="Employee report generator")
    parser.add_argument(
        "files",
        nargs="+",
        help="CSV files with employee data",
    )
    parser.add_argument(
        "--report",
        required=True,
        choices=[ReportType.PAYOUT],
        help="Report type to generate",
    )
    parser.add_argument(
        "--outgoing_format",
        required=False,
        default='json',
        choices=[OutgoingFormatType.JSON],
        help="Output type to generate",
    )

    return parser


class AbstractReportHandler:
    _file_names = []

    def generate_report(self, file_names: list = '') -> dict:
        pass


class AbstractReportSerializer:
    def serialize_to_file(self, data: dict, file_name: str) -> None:
        pass


class PayoutReportHandler(AbstractReportHandler):
    _payout_dict = {}
    _file_names = []

    def __init__(self, file_names: list = ''):
        self._payout_dict = {}
        self._file_names = file_names

    def generate_report(self) -> dict:
        """
            Создает отчет по общему количеству зарплат и часов каждого отдела.
            Записывает результат в словарь.
        """

        r_list = ['r'] * len(self._file_names)
        file_dict = []

        with ExitStack() as stack:
            files = [stack.enter_context(open(fn, mode))
                     for fn, mode in zip(self._file_names, r_list)]
            for file in files:
                file_list = file.readlines()
                file_dict = [line.split(',') for line in file_list]
                index_rate = 0
                index_hours_work = 0
                index_department = 0
                index_name = 0
                index_email = 0
                for i in range(0, len(file_dict[0])):
                    if re.search(r'hourly_rate|salary|rate', file_dict[0][i]):
                        index_rate = i
                    elif file_dict[0][i] == 'hours_worked':
                        index_hours_work = i
                    elif file_dict[0][i] == 'department':
                        index_department = i
                    elif file_dict[0][i] == 'name':
                        index_name = i
                    elif file_dict[0][i] == 'email':
                        index_email = i

                sum_hours_work = 0
                for i in range(1, len(file_dict)):
                    if file_dict[i][index_department] not in self._payout_dict:
                        self._payout_dict[file_dict[i][index_department]] = {}

                    self._payout_dict[file_dict[i][index_department]][file_dict[i][index_name]] = {
                        "hours": file_dict[i][index_hours_work],
                        'rate': file_dict[i][index_rate],
                        'payout': int(file_dict[i][index_hours_work]) * int(file_dict[i][index_rate]),
                    }
        for i in self._payout_dict:
            sum_payout = 0
            sum_hours = 0
            for department, employee in self._payout_dict[i].items():
                sum_payout += int(employee['payout'])
                sum_hours += int(employee['hours'])
            self._payout_dict[i]['total_payout'] = str(sum_payout)
            self._payout_dict[i]['total_hours'] = str(sum_hours)

        return self._payout_dict

    def get_payout(self) -> dict:
        return self._payout_dict


class JSONReportSerializer(AbstractReportSerializer):
    def serialize_to_file(self, data: dict, file_name: str) -> None:
        """
            Сериализует данные в JSON файл.

            Параметр data: Данные для сериализации (dict/list).
            Параметр file_name: Имя выходного файла (добавляет .json, если отсутствует).
        """
        try:
            # Добавляем расширение .json, если его нет
            if not file_name.lower().endswith('.json'):
                file_name += '.json'

            # Записываем данные с форматированием
            with open(file_name, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            print(f"Отчёт успешно сохранён в файл: {file_name}")

        except (TypeError, ValueError) as e:
            print(f"Ошибка сериализации данных: {str(e)}")
        except (IOError, PermissionError) as e:
            print(f"Ошибка записи в файл: {str(e)}")


def main() -> None:
    arg_parser = create_arg_parser()

    args = arg_parser.parse_args()

    report_type = args.report
    file_names = args.files
    outgoing_format = args.outgoing_format

    if report_type == ReportType.PAYOUT:
        report_handler = PayoutReportHandler(file_names=file_names)
    else:
        print(f"Unknown report type.")

    try:
        report_data = report_handler.generate_report()
    except FileNotFoundError:
        print('The file path is incorrect.')
        return

    if outgoing_format == OutgoingFormatType.JSON:
        report_serializer = JSONReportSerializer()
    else:
        print('Unknown outgoing format.')
        return

    report_serializer.serialize_to_file(data=report_data, file_name=report_type)


if __name__ == "__main__":
    main()
