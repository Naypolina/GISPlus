# Эта функция выполняет проверку и исправление LAS в нужном порядке

import checkLASfunctions


def preprocessing(file):
    new_list = []
    # проверка содержимого
    check, error = checkLASfunctions.format_v_section(file)
    if not check:
        new_list.append(error)

    # если есть ошибки в кривых, добавляем к списку ошибок
    l = checkLASfunctions.validate_curve_section(file)
    if len(l) != 0:
        for i in l:
            new_list.append(i)

    check, error = checkLASfunctions.validate_well_section(file)
    if not check:
        new_list.append(error)

    l = checkLASfunctions.validate_parameter_section(file)
    if len(l) != 0:
        for i in l:
            new_list.append(i)

    l = checkLASfunctions.validate_parameter_sectionO(file)
    if len(l) != 0:
        for i in l:
            new_list.append(i)

    # возврат словаря для конкретного файла во внешнюю функцию
    if len(new_list) != 0:
        return True, {file: new_list}
    else:
        return False, None
