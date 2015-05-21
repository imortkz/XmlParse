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
                       104: 'параметру parent_tag передано недопустимое значение',
                       105: 'параметру parent_attr передано недопустимое значение',
                       106: 'параметру child_tag передано недопустимое значение',
                       107: 'параметру child_attr передано недопустимое значение',
                       200: 'документ не является валидным документом XML.',
                       201: 'размер документа превышает допустимый.',
                       202: 'у элемента отсутствует заданный атрибут',
                       203: 'есть элементы с дублирующимися значениями заданного атрибута',
                       }
        self.__max_size = 16384
        self.__parent_tag = ''
        self.__parent_attr = ''
        self.__child_tag = ''
        self.__child_attr = ''

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

    # свойство parent_tag - родительский тег для разбора
    @property
    def parent_tag(self):
        return self.__parent_tag

    @parent_tag.setter
    def parent_tag(self, tag_name):
        if not self.__check_str_input (tag_name):
            raise XmlParseException(self.__error(104, tag_name), 104)
        else:
            self.__parent_tag = tag_name

    # свойство parent_attr - родительский тег для разбора
    @property
    def parent_attr(self):
        return self.__parent_attr

    @parent_attr.setter
    def parent_attr(self, tag_name):
        if not self.__check_str_input (tag_name):
            raise XmlParseException(self.__error(105, tag_name), 105)
        else:
            self.__parent_attr = tag_name

    # свойство child_tag - тег потомка для разбора
    @property
    def child_tag(self):
        return self.__child_tag

    @child_tag.setter
    def child_tag(self, tag_name):
        if not self.__check_str_input (tag_name):
            raise XmlParseException(self.__error(106, tag_name), 106)
        else:
            self.__child_tag = tag_name

    # свойство parent_attr - родительский тег для разбора
    @property
    def child_attr(self):
        return self.__child_attr

    @child_attr.setter
    def child_attr(self, tag_name):
        if not self.__check_str_input (tag_name):
            raise XmlParseException(self.__error(107, tag_name), 107)
        else:
            self.__child_attr = tag_name

    # проверка строкового параметра на корректность
    def __check_str_input(self, tag_name):
        if not isinstance(tag_name, str):
            return False
        if (len(tag_name) == 0) or (len(tag_name) >= sys.maxsize):
            return False
        return True

    # формирование поясняющего сообщения об ошибке для исключения
    def __error(self, error_code, description):
        return str(error_code)+' - '+self.errors[error_code] + ' (' + str(description) + ')'

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

    # проверка XML файла на валидность и соответствие требованиям спецификации
    def __check_xml(self, xml_string):
        # если размер XML документа более 16 Кбайт
        if len(xml_string) > self.__max_size:
            raise XmlParseException(self.__error(201, len(xml_string)), 201)
        try:
            root = et.fromstring(xml_string)
        except:
            raise XmlParseException(self.__error(200, xml_string), 200)
        parent_attr_list = []
        if not self.__check_str_input (self.parent_tag):
            raise XmlParseException(self.__error(104, self.parent_tag), 104)
        if not self.__check_str_input (self.parent_attr):
            raise XmlParseException(self.__error(105, self.parent_tag), 105)
        if not self.__check_str_input (self.child_tag):
            raise XmlParseException(self.__error(106, self.parent_tag), 106)
        if not self.__check_str_input (self.child_attr):
            raise XmlParseException(self.__error(107, self.parent_tag), 107)
        # находим все элементы parent_tag
        for parent_tag in root.iter(self.parent_tag):
            # проверка на наличие атрибута parent_attr в элементе parent_tag
            if self.parent_attr not in parent_tag.attrib:
                raise XmlParseException(self.__error(202, str(self.parent_tag)+str(parent_tag.attrib)), 202)
            # проверка на уникальность атрибута parent_attr в ноде parent_tag
            if parent_tag.attrib[self.parent_attr] in parent_attr_list:
                raise XmlParseException(self.__error(203, str(parent_tag.attrib[self.parent_attr])), 203)
            parent_attr_list.append(parent_tag.attrib[self.parent_attr])
            for child in parent_tag:
                if child.tag == self.child_tag:
                    # проверка на наличие атрибута ID в ноде tuningSetup
                    if self.child_attr not in child.attrib:
                        raise XmlParseException(self.__error(202, str(child.attrib)), 202)
        return 0

    # разбор XML документа из строки
    def __parse_xml(self, xml_string):
        result = {}
        temp = []
        root = et.fromstring(xml_string)
        for parent_tag in root.iter(self.parent_tag):
            for child_tag in parent_tag:
                if child_tag.tag == self.child_tag:
                    temp.append(child_tag.attrib[self.child_attr])
            if len(temp) != 0: 
                result[parent_tag.attrib[self.child_attr]] = temp.copy()
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
        self.xmlParse.parent_tag = 'input'
        self.xmlParse.parent_attr = 'id'
        self.xmlParse.child_tag = 'tuningSetup'
        self.xmlParse.child_attr = 'id'

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
    # 2.1. Параметр user_input неверного типа
    # 2.1.1. Число
    # 2.1.2. Список
    # 2.1.3. Null
    # 2.1.4. Отрицательное число
    # 2.1.5. Пустой словарь
    # 2.1.6. Словарь с элементами
    # 2.2. Несуществующий файл, некорректный URL
    # 2.3. Несуществующий URL
    # 2.4. Слишком большой XML документ
    # 2.5. Слишком большой документ (при увеличении xmlParse.maxSize)
    # 2.6. Некорректное значение XmlParse.maxSize
    # 2.7. Некорректное значение XmlParse.parent_tag
    # 2.8. Некорректное значение XmlParse.parent_attr
    # 2.9. Некорректное значение XmlParse.child_tag
    # 2.10. Некорректное значение XmlParse.child_attr


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

    def test_2_7(self):
        test_data = [0, -42, '', []]
        for test_tag in test_data:
            with self.assertRaises(XmlParseException) as cm:
                self.xmlParse.parent_tag = test_tag
            exception = cm.exception
            self.assertEqual(exception.error_code, 104)

    def test_2_8(self):
        test_data = [0, -42, '', []]
        for test_attr in test_data:
            with self.assertRaises(XmlParseException) as cm:
                self.xmlParse.parent_attr = test_attr
            exception = cm.exception
            self.assertEqual(exception.error_code, 105)

    def test_2_9(self):
        test_data = [0, -42, '', []]
        for test_tag in test_data:
            with self.assertRaises(XmlParseException) as cm:
                self.xmlParse.child_tag = test_tag
            exception = cm.exception
            self.assertEqual(exception.error_code, 106)

    def test_2_10(self):
        test_data = [0, -42, '', []]
        for test_attr in test_data:
            with self.assertRaises(XmlParseException) as cm:
                self.xmlParse.child_attr = test_attr
            exception = cm.exception
            self.assertEqual(exception.error_code, 107)

    # 3. Тестирование разбора некорректного XML документа
    # 3.1. Невалидный XML документ
    # 3.2. Есть нода parent_tag без атрибута parent_attr
    # 3.3. Есть нода child_tag без атрибута child_attr
    # 3.4. Есть нода parent_tag с дублирующимся атрибутом parent_attr

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
        test_xml = 'test_3_4.xml'
        self.assertEqual(self.__test_input(self.localPrefix + test_xml), 202)
        self.assertEqual(self.__test_input(self.httpPrefix + test_xml), 202)

    def test_3_4(self):
        test_xml = 'test_3_6.xml'
        self.assertEqual(self.__test_input(self.localPrefix + test_xml), 203)
        self.assertEqual(self.__test_input(self.httpPrefix + test_xml), 203)

if __name__ == '__main__':
    unittest.main()