import gspread
import re
import os

"""
Google Spreadsheets Datasource: returns given columns from google spreadsheets if the row with given key is found
"""

class GspreadReader:
    reader = None
    config = {}
    sources = {}

    def __init__(self, config):
        if config:
            self.config = config

        if 'gsa_file' not in config:
            raise Exception('Не указан путь к файлу сервисного аккаунта Google для gspread')
        elif not os.path.exists(config['gsa_file']):
            raise Exception(f"Файл сервисного аккаунта Google не найден: {config['gsa_file']}")

        self.reader = gspread.service_account(filename=config['gsa_file'])

    async def get_info(self, location, key, seek, columns, sheet = 1):
        """Find row by key in seek column and return requested columns.

        Args:
            location: Google Spreadsheet URL
            key: value to search in seek column
            seek: 1-based column index to search for the key
            columns: list of 1-based column indexes to return
            sheet: 1-based worksheet index (default: 1)

        Returns:
            dict of {header: value} for requested columns if found, otherwise {}
        """
        # Normalize types
        # Basic input validation
        if not location:
            raise Exception('Требуется URL таблицы Google')
        if key is None:
            raise Exception('Требуется значение ключа')
        try:
            seek_col_index = int(str(seek).strip())
        except Exception:
            raise Exception('Некорректный номер колонки для поиска (seek)')
        if seek_col_index <= 0:
            raise Exception('Номер колонки для поиска должен быть положительным числом')

        if isinstance(columns, str):
            columns = [c for c in columns.split(',') if c != '']
        try:
            requested_columns = [int(str(c).strip()) for c in columns]
        except Exception:
            raise Exception('Некорректный список колонок')
        if not requested_columns:
            raise Exception('Список колонок не должен быть пустым')
        if not all(c > 0 for c in requested_columns):
            raise Exception('Номера колонок должны быть положительными числами')

        # Cache worksheets by URL and sheet index key
        cache_key = f"{location}::sheet:{sheet}"
        if cache_key not in self.sources:
            spreadsheet = self.reader.open_by_url(location)
            # gspread uses 0-based worksheet index
            worksheet = spreadsheet.get_worksheet(int(sheet) - 1)
            if worksheet is None:
                raise Exception('Лист с указанным номером не найден')
            self.sources[cache_key] = worksheet

        worksheet = self.sources[cache_key]

        # Fetch all data
        values = worksheet.get_all_values()
        if not values or len(values) < 2:
            return {}

        headers = values[0]
        # Ensure headers list is at least as long as the largest requested column
        max_col = max(max(requested_columns), seek_col_index)
        if len(headers) < max_col:
            # pad headers to avoid index errors; unnamed columns will use default names later
            headers = headers + [''] * (max_col - len(headers))

        # Convert 1-based indices to 0-based
        seek_idx0 = seek_col_index - 1

        # Find the row where the seek column equals the key
        target_row = None
        for row in values[1:]:
            if seek_idx0 < len(row) and str(row[seek_idx0]) == str(key):
                target_row = row
                break

        if target_row is None:
            return {}

        result = {}
        for col in requested_columns:
            idx0 = col - 1
            header = str.capitalize(headers[idx0]) if idx0 < len(headers) and headers[idx0] != '' else f"Column {col}"
            value = target_row[idx0] if idx0 < len(target_row) else ''
            result[header] = value

        return result
