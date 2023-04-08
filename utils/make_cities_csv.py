""" Process xlsx file of cities and population into a
tidy csv."""

import openpyxl
import pandas as pd


def code_in_str(s):
    codes = ['CDFC', 'CDFS', 'CDJC', 'CDJS', 'SSDF',
             'SSDJ', 'ESDF', 'ESDJ']

    for code in codes:
        if code in s:
            return True
    return False


def main():
    cities = []
    # The xls is obtained from
    # https://unstats.un.org/unsd/demographic-social/products/dyb/dyb_2020/,
    # Then tranformed into xlsx for openpyxl
    # some columns manually removed
    in_file_path = '../data/input/table08.xlsx'
    wrkbk = openpyxl.load_workbook(in_file_path)
    sh = wrkbk.active
    for row in sh.iter_rows(min_row=5, min_col=1):
        cells = [cell for cell in row]
        values = [cell.value for cell in row if cell.value is not None]

        if len(values) == 0:
            continue
        if len(values) == 1:
            if cells[0].font.bold:
                continent = cells[0].value.split('-')[0].strip()
            elif code_in_str(values[0]):
                date, code = values[0].split('(')
                date = date.strip().strip('*')
                code = code.strip().strip(')')
            else:
                country = values[0].split('-')[0].strip()
                country = ''.join(c for c in country if not c.isdigit())
        else:
            assert len(values) == 9
            values = [v if v != '...' else None for v in values]
            cities.append(values + [continent, date, code, country])

    df = pd.DataFrame(cities,
                      columns=['city',
                               'city_both',
                               'city_male', 'city_female',
                               'city_area',
                               'urban_both',
                               'urban_male', 'urban_female',
                               'urban_area',
                               'continent', 'date', 'code', 'country'],
                      )
    df.to_csv('../data/output/cities.csv', index=False)


if __name__ == '__main__':
    main()
