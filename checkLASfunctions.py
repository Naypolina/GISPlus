# Здесь собраны функции, проверяющие и исправляющие файлы

import re
import os
import shutil
import tempfile


def format_v_section(input_file):
    temp_file = input_file.replace(os.path.basename(input_file), 'temporary.las')

    with open(input_file, 'r') as file:
        lines = file.readlines()

    # Переменные для хранения информации о секциях
    version_section_lines = []
    other_section_lines = []
    ascii_data_lines = []
    version_section_found = False
    version_section_should_be_first = (len(lines) > 0 and lines[0].strip().upper().startswith("~V"))
    ascii_section_index = None

    vers_found = False
    wrap_found = False

    current_section_lines = []
    current_section_id = ""

    # Проходим по всем строкам входного файла
    for i, line in enumerate(lines):
        if line.strip() == '':
            continue

        # Идентификация секций по строкам, содержащим тильды
        if line.startswith("~"):
            if current_section_id:
                # Сохраняем предыдущую секцию
                if current_section_id.startswith("~V"):
                    version_section_lines.extend(current_section_lines)
                elif current_section_id.startswith("~A"):
                    ascii_data_lines.extend(current_section_lines)
                else:
                    other_section_lines.append("".join(current_section_lines))

            # Переключаемся на новую секцию
            current_section_id = line.strip().upper()
            current_section_lines = [line]

            if current_section_id.startswith("~V"):
                if version_section_found:
                    # print('В файле LAS 2.0 должна быть только одна секция ~V.')
                    return False, 'В файле LAS 2.0 должна быть только одна секция ~V.'
                version_section_found = True

            elif current_section_id.startswith("~A"):
                ascii_section_index = len(lines) - len(current_section_lines)
        else:
            current_section_lines.append(line)

    # Не забываем добавить последнюю прочитанную секцию
    if current_section_id.startswith("~V"):
        version_section_lines.extend(current_section_lines)
    elif current_section_id.startswith("~A"):
        ascii_data_lines.extend(current_section_lines)
    else:
        other_section_lines.append("".join(current_section_lines))

    # Проверка обязательности секции и ее позиции
    if not version_section_found:
        # print('Секция ~V является обязательной в LAS-файле.')
        return False, 'Секция ~V является обязательной в LAS-файле.'
    if not version_section_should_be_first:
        # print('Секция ~V должна быть первой в LAS-файле.')
        return False, 'Секция ~V должна быть первой в LAS-файле.'

    # Проверка наличия необходимых мнемоник в секции ~V
    for line in version_section_lines:
        if line.strip().startswith("VERS"):
            vers_found = True
            # Дополнительно можно проверить корректность версии
            if not any(v in line for v in ["1.1", "1.2", "2.0"]):
                # print('Мнемоника VERS должна содержать корректную версию: 1.1, 1.2 или 2.0.')
                return False, 'Мнемоника VERS должна содержать корректную версию: 1.1, 1.2 или 2.0.'
        elif line.strip().startswith("WRAP"):
            wrap_found = True

    if not vers_found:
        # print('Секция ~V должна содержать мнемонику VERS.')
        return False, 'Секция ~V должна содержать мнемонику VERS.'
    if not wrap_found:
        # print('Секция ~V должна содержать мнемонику WRAP.')
        return False, 'Секция ~V должна содержать мнемонику WRAP.'

    # Проверка длины строк в секции ~A и настройка WRAP
    max_ascii_length = max(len(l.strip()) for l in ascii_data_lines[1:] if not l.startswith("~"))

    if max_ascii_length > 256:
        wrap_required = True
        for idx, line in enumerate(version_section_lines):
            if line.strip().startswith("WRAP"):
                version_section_lines[idx] = "WRAP . YES : Multiple lines per depth step\n"
    else:
        wrap_required = False
        for idx, line in enumerate(version_section_lines):
            if line.strip().startswith("WRAP"):
                version_section_lines[idx] = "WRAP . NO : One line per depth step\n"

    # Применяем обрезку строк в секции ~A если wrap_required = True
    formatted_ascii_data_lines = []
    for line in ascii_data_lines:
        if wrap_required and not line.startswith("~"):
            # Разбиваем строку на части по 80 символов
            line = line.strip()
            if line:
                for i in range(0, len(line), 80):
                    formatted_ascii_data_lines.append(line[i:i + 80] + "\n")
        else:
            formatted_ascii_data_lines.append(line)

    # Составляем итоговый файл
    formatted_lines = []
    formatted_lines.extend(version_section_lines)
    formatted_lines.extend(other_section_lines)
    formatted_lines.extend(formatted_ascii_data_lines)

    # Записываем изменения во временный файл
    with open(temp_file, 'w') as file:
        file.writelines(formatted_lines)

    # Заменяем оригинальный файл временным
    os.replace(temp_file, input_file)
    return True, None


def validate_curve_section(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    curve_section_started = False
    ascii_data_section_started = False
    curve_mnemonics = []
    ascii_data_mnemonics = []
    curve_section_count = 0
    errors = []

    depth_aliases = ['DEPT', 'DEPTH', 'TIME', 'INDEX']
    first_mnemonic_depth = False

    for line in lines:
        line = line.strip()
        if '~C' in line:
            curve_section_started = True
            curve_section_count += 1
            if curve_section_count > 1:
                errors.append("Т-24: В файле должна быть только одна секция '~C'.")
            continue
        if '~A' in line:
            ascii_data_section_started = True
            curve_section_started = False
            continue

        if curve_section_started and (':' in line and '.' in line):
            mnemonic, description = line.split(':', 1)
            mnemonic = mnemonic.strip().split('.')[0]
            if not curve_mnemonics:
                first_mnemonic_depth = mnemonic in depth_aliases
            curve_mnemonics.append(mnemonic)

        if ascii_data_section_started and ':' not in line and '.' not in line and line:
            # Первая строка после '~A', содержащая данные
            ascii_data_mnemonics = line.split()
            break  # Только первая строка после '~A' нужна для сравнения

    if curve_section_count == 0:
        errors.append("Т-23: Секция '~C' является обязательной, но отсутствует.")


    if not first_mnemonic_depth:
        errors.append("Т-27: Первая мнемоника в секции '~C' должна быть DEPT, DEPTH, TIME или INDEX.")

    return errors


# проверяем на одну секцию W
def validate_well_section(file_path):
    k = 0
    with open(file_path, 'r') as f:
        line = f.readlines()
        for i in range(len(line)):
            if line[i].startswith("~W"):
                k = k+1

    if k == 0:
        return False, 'В LAS файле нет секции WELL'
    elif k == 1:
        return True, None
    else:
        return False, 'В LAS файле больше одной секции WELL'


# Проверка секции ~P
def validate_parameter_section(file_path):

    with open(file_path, 'r') as file:
        lines = file.readlines()

    param_section_started = False
    param_section_count = 0
    errors = []
    param_mnemonic_pattern = re.compile(r'^\s*(\S+)\.\s*(\S+)\s+(-|\d+)\s*:\s*(.*)$')

    for line in lines:
        line = line.strip()
        if '~P' in line:
            param_section_started = True
            param_section_count += 1
            if param_section_count > 1:
                errors.append("Т-29: В файле должна быть только одна секция '~P'.")
            continue
        if line.startswith('~') and '~P' not in line:
            param_section_started = False  # Завершаем разбор секции '~P' при нахождении новой секции
            continue

    return errors

# Проверка секции ~O
def validate_parameter_sectionO(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    param_section_started = False
    param_section_count = 0
    errors = []

    for line in lines:
        line = line.strip()
        if '~O' in line:
            param_section_started = True
            param_section_count += 1
            if param_section_count > 1:
                errors.append("Т-29: В файле должна быть только одна секция '~O'.")
            continue
        if line.startswith('~') and '~O' not in line:
            param_section_started = False  # Завершаем разбор секции '~P' при нахождении новой секции
            continue

    return errors


def fix_mnemonic_format(line):
    # Используем регулярное выражение для разбивки на части
    parts = re.split(r'\s+', line.strip(), 3)

    # Если в строке только имя мнемоники и нет точки, добавим точку и двоеточие
    if len(parts) == 1:
        fixed_line = f"{parts[0]}. :"
        return fixed_line, "Добавлены точка и пробел с двоеточием после имени мнемоники."

    # Если отсутствует точка после имени мнемоники, добавим её
    if not parts[0].endswith('.'):
        parts[0] = f"{parts[0]}."

    # Проверка, чтобы между точкой и двоеточием был хотя бы один пробел
    if len(parts) == 2 and not line.endswith(':'):
        if not parts[1].startswith(':'):
            parts[1] = f' :'
        return ' '.join(parts), "Добавлен пробел перед двоеточием."

    if len(parts) > 2:
        # Если отсутствует двоеточие, добавим его с пробелом
        if ':' not in parts[2]:
            parts[2] = f"{parts[2]} :"
        else:
            # Добавляем пробел перед двоеточием, если его нет
            parts[2] = re.sub(r'(?<!\s):', ' :', parts[2])

    # Воссоздаем исправленную строку
    fixed_line = ' '.join(filter(None, parts))
    return fixed_line.strip(), "Были внесены исправления в формате мнемоники."


def check_and_fix_mnemonic_format(line):
    # Основное регулярное выражение для проверки формата
    pattern = r'^\s*([\w]+)\.(\S*)\s+(\S*)\s*:\s*(.*)$'

    # Проверяем соответствие строки шаблону
    match = re.match(pattern, line)
    if not match:
        fixed_line, message = fix_mnemonic_format(line)
        if fixed_line:
            return False, fixed_line, message
        else:
            return False, line, message

    mnemonic, units, data, description = match.groups()

    # Проверка на использование пробелов или двоеточий в имени мнемоники
    if ' ' in mnemonic or ':' in mnemonic:
        return False, line, "Имя мнемоники содержит недопустимые символы пробела или двоеточия."

    # Проверка на использование двоеточий и внутренних пробелов в единицах измерения (если они есть)
    if ':' in units or ' ' in units:
        return False, line, "Единицы измерения содержат недопустимые символы пробела или двоеточия."

    # Если все проверки выполнены успешно, возвращаем True
    return True, line, "Строка соответствует требованиям."


def validate_las_file(input_file_path):
    # Создание временного файла
    temp_file_descriptor, temp_file_path = tempfile.mkstemp()

    with os.fdopen(temp_file_descriptor, 'w', encoding='utf-8') as temp_file:
        with open(input_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        check_lines = True
        for line in lines:
            trimmed_line = line.strip()
            if trimmed_line.startswith('~'):
                # Пишем в временный файл секционные строки как есть
                temp_file.write(line)
                # Если это секция ~ASCII log data, перестаем проверять дальше
                if (trimmed_line.lower().startswith('~ascii log data') or trimmed_line.lower().startswith(
                        '~ascii data')):
                    check_lines = False
                continue

            if check_lines:
                is_valid, checked_line, _ = check_and_fix_mnemonic_format(trimmed_line)
                # Записываем исправленную или проверенную строку в временный файл
                temp_file.write(checked_line + '\n')
            else:
                # Записываем оригинальные строки после завершения проверяемых секций
                temp_file.write(line)

    # Перемещаем временный файл на место исходного
    shutil.move(temp_file_path, input_file_path)
