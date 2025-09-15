import json
import os
import re

import pandas as pd


# class GovernmentBusinessMap:
def rename_columns(df):
    col_map = {
        'OFFC_NM': '소관',
        'PGM_NM': '프로그램명',
        '프로그램': '프로그램명',
        'ACTV_NM': '단위사업명',
        '단위사업': '단위사업명',
        'SACTV_NM': '세부사업명',
        '세부사업': '세부사업명'
    }
    cols = set(df.columns)
    if inter_cols := cols.intersection(set(col_map.keys())):
        columns = {
            col: col_map[col]
            for col in inter_cols
        }
        df = df.rename(columns=columns)
    return df


def filter_business(df):
    CLEAN_FORMAT = r'[\·]|\(R&D\)|\(RnD\)|\s|사업$'

    df = rename_columns(df)
    df['단위사업명'] = df['단위사업명'].str.replace(CLEAN_FORMAT, '', regex=True)
    df['세부사업명'] = df['세부사업명'].str.replace(CLEAN_FORMAT, '', regex=True)
    
    df = df[~(df['프로그램명'].str.contains('간거래'))]
    df = df[~(df['세부사업명'].str.contains('기본경비') | df['세부사업명'].str.contains('인건비') | df['세부사업명'].str.contains('수입대체'))]
    df = df[~(df['단위사업명'].str.contains('기본경비') | df['단위사업명'].str.contains('인건비') | df['단위사업명'].str.contains('수입대체'))]
    return df


def transfer_business_df_format(df, office=None, cols=None):
    columns = ['프로그램명', '단위사업명', '세부사업명']
    if cols:
       columns.extend(cols) 

    if isinstance(office, str):
        office = [office]
        df = df[df['소관'].isin(office)][columns]

    df = filter_business(df)
    return df.drop_duplicates()


def get_business_timeseries() -> pd.DataFrame:
    return pd.read_csv('../government/예결산/사업별_예산_시계열_2007-2025.csv')


def get_business_list(ministry: str, year: int):
    df = get_business_timeseries()

    if isinstance(year, int):
        if not (2007 <= year <= 2025):
            raise

    df = df[(df['소관']==ministry) & (df[f'{year}년'] != '0')][['소관', '회계', '계정', '분야', '부문', '프로그램', '단위사업', '세부사업', '2022년']]
    df = filter_business(df)
    return df