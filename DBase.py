import sqlite3
import lasio
from pathlib import Path
import pandas as pd


def table_gis(x, file_path):
    las = lasio.read(file_path, ignore_header_errors=True)
    well_mnem = []
    out = []

    for item in las.well:
        well_mnem.append(item.mnemonic)

    for i in x:
        if i in well_mnem:
            out.append(las.well[i].value)
        else:
            out.append('')

    return out


def database(file_path, ftype):
    # данные из ГИС
    t_g = table_gis(['STRT', 'STOP', 'SRVC', 'DATE', 'WELL', 'FLD'], file_path)

    conn = sqlite3.connect("GIS_database.db3", check_same_thread=False)
    cursor = conn.cursor()

    with conn:
        data = conn.execute("select count(*) from sqlite_master where type='table' and name='subsoil_user'")
        for row in data:
            if row[0] == 0:
                with conn:
                    cursor.execute('''CREATE TABLE subsoil_user (
                                    id_subsoil_user INTEGER PRIMARY KEY AUTOINCREMENT,
                                    username TEXT NOT NULL)
                                    ''')

    with conn:
        data = conn.execute("select count(*) from sqlite_master where type='table' and name='field'")
        for row in data:
            if row[0] == 0:
                with conn:
                    cursor.execute('''CREATE TABLE field (id_field INTEGER PRIMARY KEY AUTOINCREMENT,
                                      name_field TEXT, 
                                      id_subsoil_user INTEGER REFERENCES subsoil_user (id_subsoil_user))
                                      ''')

    with conn:
        data = conn.execute("select count(*) from sqlite_master where type='table' and name='borehole'")
        for row in data:
            if row[0] == 0:
                with conn:
                    cursor.execute('''CREATE TABLE borehole (id_borehole INTEGER PRIMARY KEY AUTOINCREMENT,
                                      name_borehole TEXT,
                                      id_field INTEGER REFERENCES field (id_field))
                                      ''')

    with conn:
        data = conn.execute("select count(*) from sqlite_master where type='table' and name='gis'")
        for row in data:
            if row[0] == 0:
                with conn:
                    cursor.execute('''CREATE TABLE gis (id_gis INTEGER PRIMARY KEY AUTOINCREMENT,
                                      name_file TEXT,
                                      type_file TEXT,
                                      path_file TEXT,
                                      methods_gis TEXT,
                                      name_field TEXT,
                                      begin_method REAL,
                                      end_method REAL,
                                      data_gis TEXT,
                                      id_borehole INTEGER REFERENCES borehole (id_borehole))
                                      ''')

    # запрос для загрузки данных по недропользователю
    sqlite_insert_with_param_subsoil = """INSERT INTO subsoil_user(username) VALUES (?);"""
    cursor.execute(sqlite_insert_with_param_subsoil, [t_g[2]])

    # запрос для загрузки данных по месторождению
    sqlite_insert_with_param_field = """INSERT INTO field(name_field, id_subsoil_user) VALUES (?, LAST_INSERT_ROWID());"""
    cursor.execute(sqlite_insert_with_param_field, [t_g[5]])

    # запрос для загрузки данных по скважинам
    sqlite_insert_with_param_borehole = """INSERT INTO borehole(name_borehole, id_field) VALUES (?, LAST_INSERT_ROWID());"""
    cursor.execute(sqlite_insert_with_param_borehole, [str(t_g[4])])

    # запрос для загрузки данных по gis
    sqlite_insert_with_param_gis = """INSERT INTO gis(name_file, type_file, path_file, methods_gis, name_field,
                                    begin_method, end_method, data_gis, id_borehole) 
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, LAST_INSERT_ROWID());"""
    name_file = Path(file_path).stem
    type_file = ftype
    path_file = file_path
    method_gis = 'ГК'
    params = [[name_file, type_file, path_file, method_gis, t_g[5], t_g[0], t_g[1], t_g[3]]]
    cursor.executemany(sqlite_insert_with_param_gis, params)

    sql_zapros = """DELETE FROM gis
                        WHERE rowid NOT IN (
                        SELECT MIN(rowid)
                        FROM gis
                        GROUP BY name_file, type_file, path_file, 
                        methods_gis, name_field, begin_method, end_method, data_gis
                        );"""
    cursor.execute(sql_zapros)
    res_1 = cursor.fetchall()

    # запрос для вывода таблицы ГИС
    sqlite_gis = """SELECT name_file, type_file, path_file, methods_gis, name_field, begin_method, end_method, data_gis, name_borehole
                    FROM gis INNER JOIN borehole ON gis.id_borehole=borehole.id_borehole;"""
    cursor.execute(sqlite_gis)
    res = cursor.fetchall()
    conn.commit()
    return pd.DataFrame(res,
                        columns=['Название файла', 'Тип файла', 'Путь файла', 'Методы ГИС', 'Название месторождения', 'Начало интервала',
                                 'Конец интервала', 'Дата проведения ГИС', 'Номер скважины'])


def display_database():
    conn = sqlite3.connect("GIS_database.db3", check_same_thread=False)
    cursor = conn.cursor()
    sqlite_gis = """SELECT name_file, type_file, path_file, methods_gis, name_field, begin_method, end_method, data_gis, name_borehole
                        FROM gis INNER JOIN borehole ON gis.id_borehole=borehole.id_borehole;"""
    cursor.execute(sqlite_gis)
    res = cursor.fetchall()
    conn.commit()
    return pd.DataFrame(res,
                        columns=['Название файла', 'Тип файла', 'Путь файла', 'Методы ГИС', 'Название месторождения', 'Начало интервала',
                                 'Конец интервала', 'Дата проведения ГИС', 'Номер скважины'])
