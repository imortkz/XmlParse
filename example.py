#!/usr/bin/python
from XmlParse import XmlParse, XmlParseTest
import unittest

# запускаем юнит-тесты класса xmlParse()
print ('\n Запускаем юнит-тесты класса xmlParse: ')
test = XmlParseTest()
unittest.main()

# создаём экземпляр класса
xml = XmlParse()
file = './testXmlParse/source.xml'
# разбираем предоставленный в тестовом задании XML документ
print ('Разбираем ' + file + ', результат: \n') 
print (xml.parse(file))


