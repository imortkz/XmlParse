#!/usr/bin/python
#
# test XML parse class
# Copyright © 2015 Valentin Kim
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import sys
import os
import subprocess
import platform

import urllib.request as ur
import xml.etree.ElementTree as et
import re

import unittest


# класс реализующий разбор XML документа согласно спецификации, см. README
class XmlParse:
    # инициализация класса, создание словаря с кодами и описанием ошибок, и констант
    def __init__(self):
        self.errors = {100: 'в качестве параметра передана не строка или параметр пустой.',
                       101: 'не удаётся открыть HTTP ссылку.',
                       102: 'не удаётся открыть файл.',
                       103: 'параметру max_size передано недопустимое значение',
                       200: 'документ не является валидным документом XML.',
                       201: 'размер документа более допустимого.',
                       202: 'у элемента <input> отсутствует атрибут id.',
                       203: 'у элемента <input> атрибут id имеет недопустимое значение (не целочисленное \
                             положительное или равное нулю).',
                       204: 'у элемента <tuningSetup> отсутствует атрибут id.',
                       205: 'у элемента <tuningSetup> атрибут id имеет недопустимое значение (не целочисленное \
                             положительное или равное нулю).',
                       206: 'есть элементы <input> с дублирующимися атрибутами id.',
                       }
        self.__max_size = 16384

    # свойство max_size - максимальный размер XML документа для обработки
    @property
    def max_size(self):
        return self.__max_size

    @max_size.setter
    def max_size(self, size):
        if not isinstance(size, int):
            raise XmlParseException(self.__error(103, size), 103)
        if size == 0 or size < 0 or size >= sys.maxsize:
            raise XmlParseException(self.__error(103, size), 103)
        self.__max_size = int(size)

    # проверяем входящие данные на базовую корректность в случае локального файла
    def __check_file(self, filename):
        # содержит ли входной параметр данные
        if len(filename) != 0:
            # существует ли файл по указанному пути, есть ли права его открыть на чтение
            try:
                xmlfile = open(filename, 'rt')
                xmlfile.close()
            except:
                raise XmlParseException(self.__error(102, filename), 102)
            # укладывается ли размер файла в разрешённый диапазон
            if os.path.getsize(filename) > self.__max_size:
                raise XmlParseException(self.__error(201, str(os.path.getsize(filename))+' > ' +
                                                     str(self.__max_size)), 201)
            # базовая проверка XML документа на валидность
            try:
                xmlfile = open(filename, 'rt')
                xmldata = xmlfile.read()
                xmlfile.close()
                root = et.fromstring(xmldata)
            except:
                raise XmlParseException(self.__error(200, filename), 200)
        else:
            raise XmlParseException(self.__error(100, filename), 100)
        return 0

    # проверяем входящие данные на базовую корректность в случае HTTP ссылки
    def __check_address(self, address):
        if len(address) != 0:
            # проверяем URL на корректность
            try:
                conn = ur.urlopen(address)
            except:
                raise XmlParseException(self.__error(101, address), 101)
            # проверим код ответа на HTTP запрос, если он отличается от 200 OK, возвращаем исключение
            if conn.getcode() != 200:
                raise XmlParseException(self.__error(101, address), 101)
            # проверим размер HTTP документа
            headers = conn.info()
            if int(headers.get('Content-Length')) > self.__max_size:
                raise XmlParseException(self.__error(201, headers.get('Content-Length')), 201)
        else: 
            raise XmlParseException(self.__error(100, address), 100)
        return 0

    # формирование поясняющего сообщения об ошибке для исключения
    def __error(self, error_code, description):
        return str(error_code)+' - '+self.errors[error_code] + ' (' + str(description) + ')'

    # проверка атрибута id на корректное значение
    def __is_valid_id(self, test_id):
        try:
            test_id = int(test_id)
        except:
            return False
        if (test_id < 0) or (test_id is None) or (test_id >= sys.maxsize):
            return False
        else:
            return True

    # проверка XML файла на валидность и соответствие требованиям спецификации, проверка на ошибки 200,202-206
    def __check_xml(self, xml_string):
        # если размер XML документа более 16 Кбайт
        if len(xml_string) > self.__max_size:
            raise XmlParseException(self.__error(201, len(xml_string)), 201)
        try:
            root = et.fromstring(xml_string)
        except:
            raise XmlParseException(self.__error(200, xml_string), 200)
        input_id_list = []
        # находим все элементы <input>
        for input_tag in root.iter('input'):
            # проверка на наличие атрибута id в ноде input
            if 'id' not in input_tag.attrib:
                raise XmlParseException(self.__error(202, '<input "name"='+input_tag.attrib['name']+'>'), 202)
            # проверка на валидность значения атрибута id в ноде input
            if not self.__is_valid_id(input_tag.attrib['id']):
                raise XmlParseException(self.__error(203, '<input "name"='+input_tag.attrib['name']+'>'), 203)
            # проверка на уникальность атрибута id в ноде input
            if input_tag.attrib['id'] in input_id_list:
                raise XmlParseException(self.__error(206, '<input "name"='+input_tag.attrib['name']+'>'), 206)
            input_id_list.append(input_tag.attrib['id'])
            for child in input_tag:
                if child.tag == 'tuningSetup': 
                    # проверка на наличие атрибута ID в ноде tuningSetup
                    if 'id' not in child.attrib:
                        raise XmlParseException(self.__error(204, '<tuningSetup "name"='+child.attrib['name']+'>'), 204)
                    # проверка на валидность атрибута id в ноде tuningSetup
                    if not self.__is_valid_id(child.attrib['id']):
                        raise XmlParseException(self.__error(203, '<tuningSetup "name"='+child.attrib['name']+'>'), 205)
        return 0        

    # разбор XML документа из строки
    def __parse_xml(self, xml_string):
        result = {}
        temp = []
        root = et.fromstring(xml_string)
        for input_tag in root.iter('input'):
            for child in input_tag:
                if child.tag == 'tuningSetup': 
                    temp.append(child.attrib['id'])
            if len(temp) != 0: 
                result[input_tag.attrib['id']] = temp.copy()
            temp.clear()
        return result

    # публичный метод разбора XML документа согласно спецификации. На входе: URL или локальный путь к файлу.
    def parse(self, user_input):
        # это строка?
        if not isinstance(user_input, str):
            raise XmlParseException(self.__error(100, user_input), 100)
        # это URL?
        parsed_input = re.findall('^http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                                  user_input)
        if len(parsed_input) == 1:
            # в качестве параметра передан URL
            # проверяем входящие данные на базовую корректность
            startup_check = self.__check_address(parsed_input[0])
            conn = ur.urlopen(parsed_input[0])
            xml_string = conn.read()
            # проверяем XML на ошибки семантики
            semantic_check = self.__check_xml(xml_string)
            # извлекаем данные
            return self.__parse_xml(xml_string)
        else:
            # в качестве параметра передан путь к локальному файлу
            # проверяем входящие данные на базовую корректность
            self.__check_file(user_input)
            xml_file = open(user_input, 'rt')
            xml_string = xml_file.read()
            xml_file.close()
            # проверяем XML на ошибки семантики
            self.__check_xml(xml_string)
            # извлекаем данные
            return self.__parse_xml(xml_string)


# класс исключения для xmlParse()
class XmlParseException(Exception):
    def __init__(self, message, error):
        self.message = message
        self.error_code = error


# класс юнит-тестов для xmlParse()        
class XmlParseTest (unittest.TestCase):
    def setUp(self):
        # запускаем локальный web сервер (для каждого теста он стартует и завершает работу)
        self.xmlParse = XmlParse()
        self.httpd = subprocess.Popen(["python", "-m", "http.server"], stdin=subprocess.DEVNULL,
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).pid
        self.localPrefix = './XmlParseTest/'
        self.httpPrefix = 'http://localhost:8000/XmlParseTest/'

    def tearDown(self):
        if platform.system() == 'Windows':
            subprocess.Popen("taskkill /F /T /PID "+str(self.httpd), shell=True, stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if platform.system() == 'Linux':
            os.system('kill -9 ' + str(self.httpd))

    def __test_input(self, xml_string):
        with self.assertRaises(XmlParseException) as cm:
            self.xmlParse.parse(xml_string)
        exception = cm.exception
        return exception.error_code    

    # 1. Тестирование разбора корректного XML документа
    # 1.1. Предоставленный исходный текст
    # 1.2. Документ с несколькими нодами <input> без вложенных нод <tuningSetup>
    # 1.3. Документ с несколькими нодами <input>, одна из которых вложена в другую, и содержит в себе ноду <tuningSetup>
    # 1.4. Документ с нодой <tuningSetup> вложенной в другую ноду <tuningSetup> 
    # 1.5. Документ с нодой <input> и вложенной нодой <tuningSetup>, вложенные произвольно глубоко.

    def test_1_1(self):
        test_xml = 'source.xml'
        self.assertEqual(self.xmlParse.parse(self.localPrefix + test_xml),
                         {'100': ['0'], '1': ['1', '2', '3'], '2': ['1']})
        self.assertEqual(self.xmlParse.parse(self.httpPrefix + test_xml),
                         {'100': ['0'], '1': ['1', '2', '3'], '2': ['1']})

    def test_1_2(self):
        test_xml = 'test_1_2.xml'
        self.assertEqual(self.xmlParse.parse(self.localPrefix + test_xml), {})
        self.assertEqual(self.xmlParse.parse(self.httpPrefix + test_xml), {})

    def test_1_3(self):
        test_xml = 'test_1_3.xml'
        self.assertEqual(self.xmlParse.parse(self.localPrefix + test_xml), {'1': ['1'], '2': ['2']})
        self.assertEqual(self.xmlParse.parse(self.httpPrefix + test_xml), {'1': ['1'], '2': ['2']})

    def test_1_4(self):
        test_xml = 'test_1_4.xml'
        self.assertEqual(self.xmlParse.parse(self.localPrefix + test_xml), {'2': ['2'], '1': ['1']})
        self.assertEqual(self.xmlParse.parse(self.httpPrefix + test_xml), {'2': ['2'], '1': ['1']})

    def test_1_5(self):
        test_xml = 'test_1_5.xml'
        self.assertEqual(self.xmlParse.parse(self.localPrefix + test_xml), {'1': ['1', '4'], '2': ['2'], '3': ['1']})
        self.assertEqual(self.xmlParse.parse(self.httpPrefix + test_xml), {'1': ['1', '4'], '2': ['2'], '3': ['1']})

    # 2. Тестирование входных параметров
    # 2.1. Параметр неверного типа
    # 2.1.1. Число
    # 2.1.2. Список
    # 2.1.3. Null
    # 2.1.4. Отрицательное число
    # 2.1.5. Пустой словарь
    # 2.1.6. Словарь с элементами
    # 2.2. Несуществующий файл, некорректный URL
    # 2.3. Несуществующий URL
    # 2.4. Слишком большой XML документ
    # 2.5. Слишком большой документ (при увеличении xmlParse.max_size)
    # 2.6. Некорректное значение xmlParse.max_size

    def test_2_1(self):
        test_data = [42, ['1', '2'], '', -1, {}, {'1': '2'}]
        for test_input in test_data:
            self.assertEqual(self.__test_input(test_input), 100)
            self.assertEqual(self.__test_input(test_input), 100)

    def test_2_2(self):
        self.assertEqual(self.__test_input('./XmlParseTest/nonexisted.file'), 102)
        self.assertEqual(self.__test_input('www.google.com'), 102)

    def test_2_3(self):
        self.assertEqual(self.__test_input('http://nonexist.url'), 101)

    def test_2_4(self):
        test_xml = 'test_2_4.xml'
        self.assertEqual(self.__test_input(self.localPrefix + test_xml), 201)
        self.assertEqual(self.__test_input(self.httpPrefix + test_xml), 201)

    def test_2_5(self):
        self.xmlParse.max_size = 32768
        test_files = ['test_2_4.xml', 'test_2_5.xml']
        self.assertEqual(self.xmlParse.parse(self.localPrefix + test_files[0]), {})
        self.assertEqual(self.xmlParse.parse(self.httpPrefix + test_files[0]), {})
        self.assertEqual(self.__test_input(self.localPrefix + test_files[1]), 201)
        self.assertEqual(self.__test_input(self.httpPrefix + test_files[1]), 201)

    def test_2_6(self):
        test_data = [0, -42, 'test', []]
        for test_size in test_data:
            with self.assertRaises(XmlParseException) as cm:
                self.xmlParse.max_size = test_size
            exception = cm.exception
            self.assertEqual(exception.error_code, 103)

    # 3. Тестирование разбора некорректного XML документа
    # 3.1. Невалидный XML документ
    # 3.2. Есть нода <input> без атрибута id
    # 3.3. Есть нода <input> с недопустимым значением атрибута id
    # 3.4. Есть нода <tuningSetup> без атрибута id
    # 3.5. Есть нода <tuningSetup> с недопустимым значением атрибута id
    # 3.6. Есть нода <input> с дублирующимся атрибутом id

    def test_3_1(self):
        test_files = ['test_3_1_1.xml', 'test_3_1_2.xml', 'test_3_1_3.xml']
        for test_xml in test_files:
            self.assertEqual(self.__test_input(self.localPrefix + test_xml), 200)
            self.assertEqual(self.__test_input(self.httpPrefix + test_xml), 200)

    def test_3_2(self):
        test_xml = 'test_3_2.xml'
        self.assertEqual(self.__test_input(self.localPrefix + test_xml), 202)
        self.assertEqual(self.__test_input(self.httpPrefix + test_xml), 202)

    def test_3_3(self):
        test_files = ['test_3_3_1.xml', 'test_3_3_2.xml', 'test_3_3_3.xml']
        for test_xml in test_files:
            self.assertEqual(self.__test_input(self.localPrefix + test_xml), 203)
            self.assertEqual(self.__test_input(self.httpPrefix + test_xml), 203)

    def test_3_4(self):
        test_xml = 'test_3_4.xml'
        self.assertEqual(self.__test_input(self.localPrefix + test_xml), 204)
        self.assertEqual(self.__test_input(self.httpPrefix + test_xml), 204)

    def test_3_5(self):
        test_files = ['test_3_5_1.xml', 'test_3_5_2.xml', 'test_3_5_3.xml']
        for test_xml in test_files:
            self.assertEqual(self.__test_input(self.localPrefix + test_xml), 205)
            self.assertEqual(self.__test_input(self.httpPrefix + test_xml), 205)

    def test_3_6(self):
        test_xml = 'test_3_6.xml'
        self.assertEqual(self.__test_input(self.localPrefix + test_xml), 206)
        self.assertEqual(self.__test_input(self.httpPrefix + test_xml), 206)

if __name__ == '__main__':
    unittest.main()
