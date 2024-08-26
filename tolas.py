import chardet
import os


def add_las_extension_and_save(input_path):
    # Проверяем, имеет ли файл уже расширение .las
    base, ext = os.path.splitext(input_path)
    if ext != '.las':
        new_path = base + ext + '.las'
    else:
        # new_path = input_path  # Файл уже имеет нужное расширение
        return True, None

    # Чтение содержимого файла с предполагаемой верной кодировкой (UTF-8)
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Запись содержимого в файл с расширением .las также с кодировкой UTF-8
        with open(new_path, 'w', encoding='utf-8') as f:
            f.write(content)
            return True, new_path

        # print(f"Файл успешно сохранен с расширением '.las' и кодировкой UTF-8: {new_path}")
    except Exception as e:
        # print(f"Произошла ошибка при обработке файла: {str(e)}")

        return False, f"Произошла ошибка при обработке файла: {str(e)}"


def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        rawdata = file.read()
    result = chardet.detect(rawdata)
    return result['encoding']


def encode_with_chardet(file_path, output_path):
    encoding = detect_encoding(file_path)
    # print(f"Detected encoding: {encoding}")

    with open(file_path, 'r', encoding=encoding, errors='replace') as f_in:
        with open(output_path, 'w', encoding='utf-8') as f_out:
            for line in f_in:
                f_out.write(line)
    # print(f"File saved with UTF-8 encoding: {output_path}")


def convert_and_filter_file(input_path):
    base, ext = os.path.splitext(input_path)
    output_path_1 = base + '_fixed_manual' + ext
    output_path_2 = base + '_fixed_charde' + ext

    # Применим оба метода изменения кодировки
    encode_with_chardet(input_path, output_path_2)

    # Попробуем переместить код encode_manual в эту функцию
    try:
        with open(input_path, 'r', encoding='cp1251', errors='replace') as f_in, \
                open(output_path_1, 'w', encoding='utf-8') as f_out:
            for line in f_in:
                f_out.write(line)
        print(f"File saved with UTF-8 encoding in manual mode: {output_path_1}")
    except UnicodeEncodeError as e:
        print(f"Encoding conversion failed in manual mode for {input_path}: {e}")

    # Проверка файлов и выбор корректного
    def file_contains_invalid_encoding(file_path):
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                if any(ord(char) > 127 and char not in allowed_characters for char in line):
                    return True
        return False

    # Набор допустимых символов
    allowed_characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz" + \
                         "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЬЫЪЭЮЯабвгдеёжзийклмнопрстуфхцчшщьыъэюя" + \
                         "0123456789 |/\\.,~#:-\n\t"

    # Удаление некорректного файла
    invalid_1 = file_contains_invalid_encoding(output_path_1)
    invalid_2 = file_contains_invalid_encoding(output_path_2)

    if invalid_1 ^ invalid_2:
        if invalid_1:
            os.remove(output_path_1)
            # print(f"File {output_path_1} contains invalid encoding and has been deleted.")
            return output_path_2
        if invalid_2:
            os.remove(output_path_2)
            # print(f"File {output_path_2} contains invalid encoding and has been deleted.")
            return output_path_1
        if not invalid_1:
            # print(f"File {output_path_1} is valid and retained.")
            return output_path_1
        if not invalid_2:
            # print(f"File {output_path_2} is valid and retained.")
            return output_path_2

    else:
        os.remove(output_path_2)
        return output_path_1

