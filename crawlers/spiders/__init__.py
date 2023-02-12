from pandas.io.excel._base import ExcelFile

from pandas.io.excel._xlrd import XlrdReader

class CustomXlrdReader(XlrdReader):

    def load_workbook(self, filepath_or_buffer):
        """Same as original, just uses ignore_workbook_corruption=True)"""
        from xlrd import open_workbook

        if hasattr(filepath_or_buffer, "read"):
            data = filepath_or_buffer.read()
            return open_workbook(file_contents=data, ignore_workbook_corruption=True)
        else:
            return open_workbook(filepath_or_buffer)


ExcelFile._engines['custom_xlrd'] = CustomXlrdReader